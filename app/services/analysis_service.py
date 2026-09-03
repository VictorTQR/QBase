"""深度分析服务（m18）：模板驱动的分析产物 analysis.<preset_id>.md。

一个资产 × 一个分析模板 = 一份分析文件（区别于快速浏览的总结：
长输出、结构化、带时间锚点）。输入从 transcript.json 的 segments 构造
带时间戳文本（时间戳信息不丢，说话人缺失时由模型推断）。
任务形态完全复用 tasks 系统 + batch_runner（单条 / 批量 / 重启恢复）；
mode=batch 时打包为厂商 Batch 批任务（m21，由 batch_job_service 轮询回填）。
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from app.database import get_conn
from app.repositories import task_repository
from app.repositories.artifact_repository import list_artifacts_by_asset
from app.repositories.asset_repository import get_asset_by_id
from app.rules import (
    derived_output_path,
    flat_analysis_artifact,
    is_transcript_json_name,
    sidecar_analysis_preset,
)
from app.services import batch_runner, llm_service
from app.services.analysis_preset_service import (
    format_analysis_prompt,
    get_analysis_preset,
)
from app.services.config_service import get_analysis_llm_config
from app.services.index_service import rebuild_fulltext_index
from app.services.scanner_service import scan_current_library
from app.state import get_db_path, state
from app.utils import format_clock, load_transcript_segments


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def analysis_output_filename(preset_id: str) -> str:
    """分析产物的文件名（sidecar 目录内 / 平铺共用，m11 跟随现状）。"""
    return f"analysis.{preset_id}.md"


def get_active_transcript_artifact(conn, asset_id: str) -> dict | None:
    for artifact in list_artifacts_by_asset(conn, asset_id):
        if artifact["kind"] == "transcript" and artifact["status"] == "active":
            return artifact

    return None


def build_timestamped_input(conn, asset: dict) -> str:
    """构造带时间戳的分析输入：[MM:SS] 说话人: 文本（每 segment 一行）。

    仅支持音视频 + JSON 转录（有 segments 才有分段分析的时间锚点）；
    纯文本转录（-f txt / 普通 txt）没有时间分段，明确报错引导重转录。
    """
    if asset["type"] not in {"audio", "video"}:
        raise ValueError("深度分析目前仅支持音频 / 视频资产（需要带时间戳的转录）")

    transcript = get_active_transcript_artifact(conn, asset["id"])

    if transcript is None:
        raise ValueError("该音视频没有转录文件，请先生成转录")

    transcript_path = Path(transcript["absolute_path"])

    if not is_transcript_json_name(transcript_path.name):
        raise ValueError(
            "当前转录不是 JSON 格式（无时间分段），无法做分段分析。"
            "请把 [cli] transcribe_command 改为 -f json 重新生成转录"
        )

    data = load_transcript_segments(transcript_path)

    if not data["segments"]:
        raise ValueError("转录 JSON 中没有可用的分段（segments 为空），无法做分段分析")

    lines: list[str] = []

    for seg in data["segments"]:
        timestamp = format_clock(seg["start"])
        prefix = f"[{timestamp}]" if timestamp else ""
        speaker = f"{seg['speaker']}: " if seg["speaker"] else ""
        lines.append(f"{prefix} {speaker}{seg['text']}".strip())

    return "\n".join(lines)


def build_analysis_frontmatter(asset: dict, preset: dict, config: dict) -> str:
    """分析文件的 frontmatter（preset / preset_name 供 UI 展示模板名）。"""
    return (
        "---\n"
        "type: analysis\n"
        f"preset: {preset['id']}\n"
        f"preset_name: {preset['name']}\n"
        f"source: {asset['relative_path']}\n"
        "generator: openai_compatible\n"
        f"model: {config['model']}\n"
        f"created_at: {datetime.now(timezone.utc).isoformat()}\n"
        "---\n\n"
    )


def backup_existing_analysis(analysis_path: Path) -> Path | None:
    """覆盖前备份旧分析到 <library_root>/.knowledge/backups/，返回备份路径。"""
    if not analysis_path.exists():
        return None

    if state.library_root is None:
        raise RuntimeError("未打开知识库")

    backup_dir = state.library_root / ".knowledge" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{analysis_path.stem}.{timestamp}{analysis_path.suffix}"

    shutil.copy2(analysis_path, backup_path)
    logger.info("已备份旧分析：{} -> {}", analysis_path, backup_path)

    return backup_path


def analysis_preset_name(artifact: dict) -> str | None:
    """从分析产物文件名反解 preset_id（用于 UI 标注模板）。"""
    name = Path(artifact["relative_path"]).name

    sidecar_preset = sidecar_analysis_preset(name)

    if sidecar_preset is not None:
        return sidecar_preset

    parts = flat_analysis_artifact(name)

    if parts is not None:
        return parts[1]

    return None


def has_active_analysis(conn, asset_id: str, preset_id: str) -> bool:
    """资产是否已有该模板的 active 分析。

    按文件名反解 preset（平铺 / sidecar 均可），与输出路径无关——
    中途创建 .kb 目录不改变「已有该模板分析」的判定（m11 跟随现状
    只影响新文件的写入位置）。
    """
    for artifact in list_artifacts_by_asset(conn, asset_id):
        if artifact["kind"] != "analysis" or artifact["status"] != "active":
            continue

        if analysis_preset_name(artifact) == preset_id:
            return True

    return False


def _create_analysis_task(
    conn, asset_id: str, preset_id: str
) -> tuple[str | None, str | None]:
    """校验并创建 pending 分析任务；不通过时返回 (None, 中文原因)，不报错。"""
    asset = get_asset_by_id(conn, asset_id)

    if asset is None:
        return None, "资产不存在"

    if task_repository.count_running_tasks(
        conn, asset_id=asset_id, task_type="analysis"
    ) > 0:
        return None, "该资产已有分析任务正在运行"

    llm_config = get_analysis_llm_config()

    if not llm_config["enabled"]:
        return None, "AI 分析未启用，请检查 [llm.analysis] enabled"

    try:
        preset = get_analysis_preset(preset_id)
    except ValueError as exc:
        return None, str(exc)

    if asset["type"] not in preset["types"]:
        return None, f"模板「{preset['name']}」不适用于 {asset['type']} 资产"

    # 前置校验输入（无转录 / 非 JSON 转录在这里就报错，不创建任务）
    try:
        input_text = build_timestamped_input(conn, asset)
    except ValueError as exc:
        return None, str(exc)

    if not input_text.strip():
        return None, "输入文本为空，无法生成分析"

    output_path = str(
        derived_output_path(
            asset["absolute_path"], analysis_output_filename(preset["id"])
        )
    )

    task_id = task_repository.create_task(
        conn,
        asset_id=asset_id,
        task_type="analysis",
        params={
            "asset_id": asset_id,
            "preset_id": preset["id"],
            "preset_name": preset["name"],
            "input_length": len(input_text),
            "output_path": output_path,
        },
        command=None,
        output_path=output_path,
    )

    return task_id, None


def _dispatch_created_tasks(task_ids: list[str]) -> None:
    """按 [llm.analysis] mode 分流（m21）：batch 打包为厂商批任务，其余本地消费。"""
    from app.services import batch_job_service

    if batch_job_service.is_batch_mode(get_analysis_llm_config()):
        batch_job_service.submit_batch_jobs("analysis", task_ids)
    else:
        batch_runner.execute_tasks(task_ids, run_analysis_task)


def start_analysis(asset_id: str, preset_id: str) -> str:
    """创建并启动单条分析任务（并发去重 + 前置校验）。"""
    conn = get_conn(get_db_path())

    try:
        task_id, reason = _create_analysis_task(conn, asset_id, preset_id)

        if task_id is None:
            raise ValueError(reason)

        conn.commit()
    finally:
        conn.close()

    _dispatch_created_tasks([task_id])

    logger.info("分析任务已创建：{}（asset {}，preset {}）", task_id, asset_id, preset_id)

    return task_id


def start_batch_analysis(
    asset_ids: list[str], preset_id: str, overwrite: bool = False
) -> dict:
    """批量分析（m18）：逐资产预检建任务，不合规项跳过并记录原因。

    overwrite=False 时该资产该模板已有 active 分析的跳过；True 时全部
    重新生成（执行体覆盖前自动备份到 .knowledge/backups/）。
    """
    if not asset_ids:
        raise ValueError("未选择任何资产")

    preset = get_analysis_preset(preset_id)

    llm_config = get_analysis_llm_config()

    if not llm_config["enabled"]:
        raise ValueError("AI 分析未启用，请检查 [llm.analysis] enabled")

    created: list[str] = []
    skipped: list[dict] = []

    conn = get_conn(get_db_path())

    try:
        for asset_id in asset_ids:
            asset = get_asset_by_id(conn, asset_id)

            if asset is None:
                skipped.append(
                    {"asset_id": asset_id, "title": None, "reason": "资产不存在"}
                )
                continue

            if not overwrite and has_active_analysis(conn, asset_id, preset["id"]):
                skipped.append(
                    {
                        "asset_id": asset_id,
                        "title": asset["title"],
                        "reason": f"已有「{preset['name']}」分析",
                    }
                )
                continue

            task_id, reason = _create_analysis_task(conn, asset_id, preset_id)

            if task_id is None:
                skipped.append(
                    {"asset_id": asset_id, "title": asset["title"], "reason": reason}
                )
            else:
                created.append(task_id)

        conn.commit()
    finally:
        conn.close()

    if created:
        _dispatch_created_tasks(created)

    logger.info(
        "批量分析（{}）：创建 {} 个任务，跳过 {} 项",
        preset_id,
        len(created),
        len(skipped),
    )

    return {
        "created": len(created),
        "task_ids": created,
        "skipped": skipped,
        "mode": llm_config.get("mode", "sync"),
    }


def resume_pending_analysis_tasks() -> None:
    """打开知识库时恢复未完结的分析任务（重跑幂等；in-flight 去重见 batch_runner）。

    params_json 带 batch_task_id 的任务由 batch_job_service 轮询回填，
    这里跳过（m21），避免与厂商批任务重复计费。
    """
    conn = get_conn(get_db_path())

    try:
        rows = conn.execute(
            """
            SELECT id, params_json FROM tasks
            WHERE type = 'analysis' AND status IN ('pending', 'running')
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

    logger.info("恢复未完结的分析任务：{} 个", len(task_ids))
    batch_runner.execute_tasks(task_ids, run_analysis_task)


def _task_params(task: dict) -> dict:
    try:
        return json.loads(task["params_json"] or "{}")
    except json.JSONDecodeError:
        return {}


def write_analysis_artifact(
    asset: dict, preset: dict, analysis_content: str, llm_config: dict
) -> str:
    """分析落盘（m21 抽取）：覆盖前备份 + frontmatter，返回输出路径。

    只写文件不刷索引，索引刷新由调用方负责（batch 批量回填时统一刷一次）。
    """
    analysis_path = derived_output_path(
        asset["absolute_path"], analysis_output_filename(preset["id"])
    )

    backup_existing_analysis(analysis_path)

    analysis_path.write_text(
        build_analysis_frontmatter(asset, preset, llm_config) + analysis_content,
        encoding="utf-8",
    )

    return str(analysis_path)


def refresh_analysis_indexes() -> str | None:
    """刷新扫描与全文索引，失败返回警告文本不抛错（sync/batch 共用）。"""
    try:
        scan_current_library()
        rebuild_fulltext_index()
    except Exception as scan_exc:
        return f"分析生成成功，但刷新索引失败：{scan_exc}"

    return None


def build_batch_request(conn, task_id: str) -> dict:
    """构建 batch 模式叶子请求（m21）：短文 1 条，长文按时间窗 N 条。

    返回 {"requests": [...], "window_labels": [...]}，标签供合并时
    标注各窗时间范围。
    """
    task = task_repository.get_task(conn, task_id)

    if task is None:
        raise ValueError("任务不存在")

    asset = get_asset_by_id(conn, task["asset_id"]) if task["asset_id"] else None

    if asset is None:
        raise ValueError("资产不存在")

    preset = get_analysis_preset(_task_params(task).get("preset_id") or "")
    llm_config = get_analysis_llm_config()

    system_prompt = format_analysis_prompt(preset, asset["title"])
    input_text = build_timestamped_input(conn, asset)

    messages_list, window_labels = llm_service.build_analysis_leaf_messages(
        system_prompt, input_text, llm_config
    )

    return {"requests": messages_list, "window_labels": window_labels}


def apply_batch_results(
    conn,
    task_id: str,
    contents: list[str],
    window_labels: list[str] | None,
    llm_config: dict,
) -> dict:
    """batch 结果落盘（m21）：多窗结果先本地合并再写文件。

    返回合并进任务 params 的附加字段（output_path）；失败抛异常。
    """
    task = task_repository.get_task(conn, task_id)

    if task is None:
        raise ValueError("任务不存在")

    asset = get_asset_by_id(conn, task["asset_id"]) if task["asset_id"] else None

    if asset is None:
        raise ValueError("资产不存在")

    preset = get_analysis_preset(_task_params(task).get("preset_id") or "")

    if len(contents) == 1:
        analysis_content = contents[0]
    else:
        system_prompt = format_analysis_prompt(preset, asset["title"])
        analysis_content = llm_service.merge_analysis_partials(
            system_prompt, contents, window_labels or [], llm_config
        )

    output_path = write_analysis_artifact(asset, preset, analysis_content, llm_config)

    return {"output_path": output_path}


def run_analysis_task(task_id: str) -> None:
    """后台执行分析任务（task_id 自包含：preset_id 取自 params_json）。"""
    conn = get_conn(get_db_path())

    try:
        task = task_repository.get_task(conn, task_id)

        if task is None:
            return

        params = _task_params(task)

        if params.get("batch_task_id"):
            return  # batch 托管任务由 batch_job_service 轮询回填

        asset = get_asset_by_id(conn, task["asset_id"]) if task["asset_id"] else None

        if asset is None:
            task_repository.update_task(
                conn,
                task_id,
                status="failed",
                error="资产不存在",
                finished_at=utcnow_iso(),
            )
            conn.commit()
            return

        preset_id = str(params.get("preset_id") or "")

        try:
            preset = get_analysis_preset(preset_id)
        except ValueError as exc:
            task_repository.update_task(
                conn,
                task_id,
                status="failed",
                error=str(exc),
                finished_at=utcnow_iso(),
            )
            conn.commit()
            return

        llm_config = get_analysis_llm_config()

        task_repository.update_task(
            conn, task_id, status="running", started_at=utcnow_iso()
        )
        conn.commit()

        input_text = build_timestamped_input(conn, asset)

        system_prompt = format_analysis_prompt(preset, asset["title"])
        analysis_content = llm_service.analyze_text(system_prompt, input_text, llm_config)

        analysis_path = write_analysis_artifact(asset, preset, analysis_content, llm_config)
        warning = refresh_analysis_indexes()

        task_repository.update_task(
            conn,
            task_id,
            status="success",
            output_path=analysis_path,
            error=warning,
            finished_at=utcnow_iso(),
        )
        conn.commit()

        logger.info("分析任务完成：{} -> {}", task_id, analysis_path)
    except Exception as exc:
        logger.error("分析任务失败：{} - {}", task_id, exc)

        try:
            task_repository.update_task(
                conn,
                task_id,
                status="failed",
                error=str(exc),
                finished_at=utcnow_iso(),
            )
            conn.commit()
        except Exception:
            pass
    finally:
        conn.close()
