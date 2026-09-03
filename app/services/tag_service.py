"""标签服务（m15）：标签名校验、查询与整体替换；AI 建议标签（m16）；
任务化批量 AI 打标——建议清洗后自动追加写库（m17）；mode=batch 时
打包为厂商 Batch 批任务（m21，由 batch_job_service 轮询回填）。"""

from __future__ import annotations

import json

from loguru import logger

from app.database import get_conn
from app.repositories import task_repository
from app.repositories.artifact_repository import list_artifacts_by_asset
from app.repositories.asset_repository import get_asset_by_id
from app.repositories.tag_repository import (
    get_tags_for_asset,
    list_tags,
    set_asset_tags as repo_set_asset_tags,
)
from app.services import (
    batch_runner,
    config_service,
    llm_service,
    summarization_service,
)
from app.state import get_db_path
from app.utils import read_text_for_index

MAX_TAG_LENGTH = 30
MAX_TAGS_PER_ASSET = 20


def normalize_tag_names(names: list[str]) -> list[str]:
    """trim、去空、去重保序并逐条校验，违规抛 ValueError（中文报错）。"""
    normalized: list[str] = []

    for raw in names:
        if not isinstance(raw, str):
            raise ValueError("标签名必须是字符串")

        name = raw.strip()

        if not name:
            raise ValueError("标签名不能为空")

        if "," in name:
            raise ValueError(f"标签名不能包含半角逗号：{name}")

        if len(name) > MAX_TAG_LENGTH:
            raise ValueError(
                f"标签名不能超过 {MAX_TAG_LENGTH} 个字符：{name[:MAX_TAG_LENGTH]}…"
            )

        if name not in normalized:
            normalized.append(name)

    if len(normalized) > MAX_TAGS_PER_ASSET:
        raise ValueError(f"单个资产最多 {MAX_TAGS_PER_ASSET} 个标签")

    return normalized


def get_all_tags() -> list[dict]:
    """全部标签 + 使用数（绑定资产数）。"""
    conn = get_conn(get_db_path())
    try:
        return list_tags(conn)
    finally:
        conn.close()


def get_asset_tags(asset_id: str) -> list[str]:
    """某资产的标签名列表；资产不存在抛 ValueError。"""
    conn = get_conn(get_db_path())
    try:
        if get_asset_by_id(conn, asset_id) is None:
            raise ValueError("资产不存在")

        return get_tags_for_asset(conn, asset_id)
    finally:
        conn.close()


def set_asset_tags(asset_id: str, names: list[str]) -> list[str]:
    """整体替换某资产的标签，返回最终标签名列表。"""
    normalized = normalize_tag_names(names)

    conn = get_conn(get_db_path())
    try:
        if get_asset_by_id(conn, asset_id) is None:
            raise ValueError("资产不存在")

        result = repo_set_asset_tags(conn, asset_id, normalized)
        conn.commit()
        return result
    finally:
        conn.close()


def _clean_suggestions(names: list[str]) -> list[str]:
    """宽松清洗 AI 建议的标签：不合规条目直接丢弃而非报错。"""
    cleaned: list[str] = []

    for raw in names:
        if not isinstance(raw, str):
            continue

        name = raw.strip()

        if not name or "," in name or len(name) > MAX_TAG_LENGTH:
            continue

        if name not in cleaned:
            cleaned.append(name)

    return cleaned[:MAX_TAGS_PER_ASSET]


def _get_tagging_input_text(conn, asset: dict) -> str:
    """打标输入：优先取 active 总结（浓缩全文，长内容截断只伤覆盖度）；
    无总结时沿用总结的来源选择（音频/视频取转录、文档取解析/原文）。
    """
    for artifact in list_artifacts_by_asset(conn, asset["id"]):
        if artifact["kind"] == "summary" and artifact["status"] == "active":
            text = read_text_for_index(artifact["absolute_path"])
            if text.strip():
                return text
            break  # 总结为空文件，退回全文来源

    return summarization_service.get_summary_input_text(conn, asset)


def suggest_asset_tags(asset_id: str) -> list[str]:
    """AI 建议标签（m16）：只返回建议，不写库；由用户在编辑器确认后保存。

    输入优先用 active 总结，无则取转录/解析/原文（复用总结来源选择）。
    """
    conn = get_conn(get_db_path())
    try:
        asset = get_asset_by_id(conn, asset_id)

        if asset is None:
            raise ValueError("资产不存在")

        llm_config = config_service.get_tagging_llm_config()

        if not llm_config.get("enabled"):
            raise ValueError("AI 打标未启用，请前往设置页开启")

        input_text = _get_tagging_input_text(conn, asset)
        existing = [tag["name"] for tag in list_tags(conn)]
    finally:
        conn.close()

    suggestions = llm_service.suggest_tags(
        asset["title"], input_text, existing, llm_config
    )

    return _clean_suggestions(suggestions)


def _create_tagging_task(conn, asset_id: str) -> tuple[str | None, str | None]:
    """校验并创建 pending AI 打标任务（m17）；不通过时返回 (None, 中文原因)。

    输入可总结性（有无转录/解析）不在创建期校验——留到执行期以任务
    failed 形式呈现，用户可在任务中心看到具体原因。
    """
    asset = get_asset_by_id(conn, asset_id)

    if asset is None:
        return None, "资产不存在"

    if task_repository.count_running_tasks(
        conn, asset_id=asset_id, task_type="tagging"
    ) > 0:
        return None, "该资产已有打标任务正在运行"

    llm_config = config_service.get_tagging_llm_config()

    if not llm_config.get("enabled"):
        return None, "AI 打标未启用，请前往设置页开启"

    task_id = task_repository.create_task(
        conn,
        asset_id=asset_id,
        task_type="tagging",
        params={"asset_id": asset_id},
        command=None,
        output_path=None,
    )

    return task_id, None


def run_tagging_task(task_id: str) -> None:
    """后台执行 AI 打标任务（m17）：生成建议 → 清洗 → 追加写库（不删已有标签）。

    实际写入的新标签记入任务 params_json 的 applied 字段（任务详情可审计）。
    """
    conn = get_conn(get_db_path())

    try:
        task = task_repository.get_task(conn, task_id)

        if task is None:
            return

        try:
            params = json.loads(task["params_json"] or "{}")
        except json.JSONDecodeError:
            params = {}

        if params.get("batch_task_id"):
            return  # batch 托管任务由 batch_job_service 轮询回填

        asset = get_asset_by_id(conn, task["asset_id"]) if task["asset_id"] else None

        if asset is None:
            task_repository.update_task(
                conn,
                task_id,
                status="failed",
                error="资产不存在",
                finished_at=task_repository.utcnow_iso(),
            )
            conn.commit()
            return

        llm_config = config_service.get_tagging_llm_config()

        if not llm_config.get("enabled"):
            task_repository.update_task(
                conn,
                task_id,
                status="failed",
                error="AI 打标未启用，请前往设置页开启",
                finished_at=task_repository.utcnow_iso(),
            )
            conn.commit()
            return

        task_repository.update_task(
            conn, task_id, status="running", started_at=task_repository.utcnow_iso()
        )
        conn.commit()

        input_text = _get_tagging_input_text(conn, asset)
        existing = [tag["name"] for tag in list_tags(conn)]

        suggestions = _clean_suggestions(
            llm_service.suggest_tags(asset["title"], input_text, existing, llm_config)
        )

        applied = _apply_suggestions(conn, asset, suggestions)

        task_repository.update_task(
            conn,
            task_id,
            status="success",
            params_json=json.dumps(
                {"asset_id": asset["id"], "applied": applied},
                ensure_ascii=False,
            ),
            finished_at=task_repository.utcnow_iso(),
        )
        conn.commit()

        logger.info(
            "AI 打标任务完成：{}（asset {}，追加 {}）",
            task_id,
            asset["id"],
            applied,
        )
    except Exception as exc:
        logger.error("AI 打标任务失败：{} - {}", task_id, exc)

        try:
            task_repository.update_task(
                conn,
                task_id,
                status="failed",
                error=str(exc),
                finished_at=task_repository.utcnow_iso(),
            )
            conn.commit()
        except Exception:
            pass
    finally:
        conn.close()


def _apply_suggestions(conn, asset: dict, suggestions: list[str]) -> list[str]:
    """清洗后的建议追加写库（不删已有标签，m21 抽取 sync/batch 共用）。

    无可用标签抛 ValueError；返回实际写入的标签。
    """
    if not suggestions:
        raise ValueError("AI 未返回可用标签")

    current = get_tags_for_asset(conn, asset["id"])
    merged = (current + [s for s in suggestions if s not in current])[
        :MAX_TAGS_PER_ASSET
    ]

    repo_set_asset_tags(conn, asset["id"], merged)
    conn.commit()

    return [s for s in suggestions if s in merged]


def build_batch_request(conn, task_id: str) -> list[list[dict]]:
    """构建 batch 模式叶子请求（m21）：打标恒为单请求（输入短、截断）。"""
    task = task_repository.get_task(conn, task_id)
    asset = get_asset_by_id(conn, task["asset_id"]) if task and task["asset_id"] else None

    if asset is None:
        raise ValueError("资产不存在")

    llm_config = config_service.get_tagging_llm_config()

    if not llm_config.get("enabled"):
        raise ValueError("AI 打标未启用，请前往设置页开启")

    input_text = _get_tagging_input_text(conn, asset)
    existing = [tag["name"] for tag in list_tags(conn)]

    return [
        llm_service.build_tagging_messages(asset["title"], input_text, existing, llm_config)
    ]


def apply_batch_results(conn, task_id: str, contents: list[str]) -> dict:
    """batch 结果落库（m21）：解析各行原始输出 → 清洗 → 追加写库。

    返回合并进任务 params 的附加字段（applied 审计）；失败抛异常。
    """
    task = task_repository.get_task(conn, task_id)
    asset = get_asset_by_id(conn, task["asset_id"]) if task and task["asset_id"] else None

    if asset is None:
        raise ValueError("资产不存在")

    suggestions: list[str] = []

    for raw in contents:
        suggestions.extend(llm_service._parse_tag_list(raw))

    applied = _apply_suggestions(conn, asset, _clean_suggestions(suggestions))

    return {"applied": applied}


def _dispatch_created_tasks(task_ids: list[str]) -> None:
    """按 [llm.tagging] mode 分流（m21）：batch 打包为厂商批任务，其余本地消费。"""
    from app.services import batch_job_service

    if batch_job_service.is_batch_mode(config_service.get_tagging_llm_config()):
        batch_job_service.submit_batch_jobs("tagging", task_ids)
    else:
        batch_runner.execute_tasks(task_ids, run_tagging_task)


def start_tagging(asset_id: str) -> str:
    """创建并启动单个 AI 打标任务（任务中心失败重试入口）。"""
    conn = get_conn(get_db_path())

    try:
        task_id, reason = _create_tagging_task(conn, asset_id)

        if task_id is None:
            raise ValueError(reason)

        conn.commit()
    finally:
        conn.close()

    _dispatch_created_tasks([task_id])

    logger.info("AI 打标任务已创建：{}（asset {}）", task_id, asset_id)

    return task_id


def start_batch_tagging(asset_ids: list[str]) -> dict:
    """批量 AI 打标（m17）：追加语义全量跑，逐资产预检，不合规项跳过记原因。"""
    if not asset_ids:
        raise ValueError("未选择任何资产")

    llm_config = config_service.get_tagging_llm_config()

    if not llm_config.get("enabled"):
        raise ValueError("AI 打标未启用，请前往设置页开启")

    created: list[str] = []
    skipped: list[dict] = []

    conn = get_conn(get_db_path())

    try:
        for asset_id in asset_ids:
            asset = get_asset_by_id(conn, asset_id)

            task_id, reason = _create_tagging_task(conn, asset_id)

            if task_id is None:
                skipped.append(
                    {
                        "asset_id": asset_id,
                        "title": asset["title"] if asset else None,
                        "reason": reason,
                    }
                )
            else:
                created.append(task_id)

        conn.commit()
    finally:
        conn.close()

    if created:
        _dispatch_created_tasks(created)

    logger.info(
        "批量 AI 打标：创建 {} 个任务，跳过 {} 项", len(created), len(skipped)
    )

    return {
        "created": len(created),
        "task_ids": created,
        "skipped": skipped,
        "mode": llm_config.get("mode", "sync"),
    }


def resume_pending_tagging_tasks() -> None:
    """打开知识库时恢复未完结的 AI 打标任务（重跑幂等；in-flight 去重见 batch_runner）。

    params_json 带 batch_task_id 的任务由 batch_job_service 轮询回填，
    这里跳过（m21），避免与厂商批任务重复计费。
    """
    conn = get_conn(get_db_path())

    try:
        rows = conn.execute(
            """
            SELECT id, params_json FROM tasks
            WHERE type = 'tagging' AND status IN ('pending', 'running')
            """
        ).fetchall()
    finally:
        conn.close()

    task_ids: list[str] = []

    for row in rows:
        try:
            params = json.loads(row["params_json"] or "{}")
        except json.JSONDecodeError:
            params = {}

        if params.get("batch_task_id"):
            continue

        task_ids.append(row["id"])

    if not task_ids:
        return

    logger.info("恢复未完结的 AI 打标任务：{} 个", len(task_ids))
    batch_runner.execute_tasks(task_ids, run_tagging_task)
