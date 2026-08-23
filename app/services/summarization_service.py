"""总结服务：LLM 生成 {stem}.summary.md，后台任务 + 覆盖备份 + 自动刷新索引（m6）；
批量总结与重启恢复（m17）经 batch_runner 消费。"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from app.database import get_conn
from app.repositories import task_repository
from app.repositories.artifact_repository import (
    has_active_artifact,
    list_artifacts_by_asset,
)
from app.repositories.asset_repository import get_asset_by_id
from app.rules import derived_output_path
from app.services import batch_runner
from app.services.config_service import get_summary_llm_config
from app.services.index_service import rebuild_fulltext_index
from app.services.llm_service import summarize_text
from app.services.parse_service import PARSEABLE_EXTENSIONS
from app.services.scanner_service import scan_current_library
from app.state import get_db_path, state
from app.utils import read_text_for_index


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_summary_input_text(conn, asset: dict) -> str:
    """获取总结输入文本：音视频取转录；.md/.txt 文档取原文；白名单文档取解析结果。"""
    asset_type = asset["type"]
    asset_path = Path(asset["absolute_path"])

    if asset_type in {"audio", "video"}:
        transcript_artifact = None

        for artifact in list_artifacts_by_asset(conn, asset["id"]):
            if artifact["kind"] == "transcript" and artifact["status"] == "active":
                transcript_artifact = artifact
                break

        if transcript_artifact is None:
            raise ValueError("该音视频没有转录文件，请先生成转录")

        return read_text_for_index(transcript_artifact["absolute_path"])

    if asset_type == "document":
        ext = asset_path.suffix.lower()

        if ext in {".md", ".txt"}:
            return read_text_for_index(str(asset_path))

        if ext in PARSEABLE_EXTENSIONS:
            parsed_artifact = None

            for artifact in list_artifacts_by_asset(conn, asset["id"]):
                if artifact["kind"] == "parsed" and artifact["status"] == "active":
                    parsed_artifact = artifact
                    break

            if parsed_artifact is None:
                raise ValueError("该文档尚未解析，请先在详情页生成解析")

            return read_text_for_index(parsed_artifact["absolute_path"])

        raise ValueError(f"当前不支持对 {ext} 文件生成总结")

    raise ValueError(f"不支持对 {asset_type} 类型生成总结")


def build_summary_frontmatter(asset: dict, config: dict) -> str:
    """总结文件的 frontmatter。"""
    return (
        "---\n"
        "type: summary\n"
        f"source: {asset['relative_path']}\n"
        "generator: openai_compatible\n"
        f"model: {config['model']}\n"
        f"created_at: {datetime.now(timezone.utc).isoformat()}\n"
        "---\n\n"
    )


def backup_existing_summary(summary_path: Path) -> Path | None:
    """覆盖前备份旧总结到 <library_root>/.knowledge/backups/，返回备份路径。"""
    if not summary_path.exists():
        return None

    if state.library_root is None:
        raise RuntimeError("未打开知识库")

    backup_dir = state.library_root / ".knowledge" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{summary_path.stem}.{timestamp}{summary_path.suffix}"

    shutil.copy2(summary_path, backup_path)
    logger.info("已备份旧总结：{} -> {}", summary_path, backup_path)

    return backup_path


def _create_summarization_task(
    conn, asset_id: str
) -> tuple[str | None, str | None]:
    """校验并创建 pending 总结任务；不通过时返回 (None, 中文原因)，不报错。"""
    asset = get_asset_by_id(conn, asset_id)

    if asset is None:
        return None, "资产不存在"

    if task_repository.count_running_tasks(
        conn, asset_id=asset_id, task_type="summarization"
    ) > 0:
        return None, "该资产已有总结任务正在运行"

    llm_config = get_summary_llm_config()

    if not llm_config["enabled"]:
        return None, "LLM 总结未启用，请检查 [llm.summary] enabled"

    # 前置校验输入文本（无转录 / 不支持的类型在这里就报错，不创建任务）
    input_text = get_summary_input_text(conn, asset)

    if not input_text.strip():
        return None, "输入文本为空，无法生成总结"

    # m11 跟随现状：资产旁存在 <name>.kb/ 目录时写入其中，否则平铺
    summary_path = str(derived_output_path(asset["absolute_path"], "summary.md"))

    task_id = task_repository.create_task(
        conn,
        asset_id=asset_id,
        task_type="summarization",
        params={
            "asset_id": asset_id,
            "input_length": len(input_text),
            "output_path": summary_path,
        },
        command=None,
        output_path=summary_path,
    )

    return task_id, None


def start_summarization(asset_id: str) -> str:
    """创建并启动总结任务（并发去重 + 前置校验）。"""
    conn = get_conn(get_db_path())

    try:
        task_id, reason = _create_summarization_task(conn, asset_id)

        if task_id is None:
            raise ValueError(reason)

        conn.commit()
    finally:
        conn.close()

    batch_runner.execute_tasks([task_id], run_summarization_task)

    logger.info("总结任务已创建：{}（asset {}）", task_id, asset_id)

    return task_id


def start_batch_summarization(
    asset_ids: list[str], overwrite: bool = False
) -> dict:
    """批量总结（m17）：逐资产预检建任务，不合规项跳过并记录原因。

    overwrite=False 时已有 active 总结的资产跳过；True 时全部重新生成
    （执行体覆盖前自动备份到 .knowledge/backups/）。
    """
    if not asset_ids:
        raise ValueError("未选择任何资产")

    llm_config = get_summary_llm_config()

    if not llm_config["enabled"]:
        raise ValueError("LLM 总结未启用，请检查 [llm.summary] enabled")

    created: list[str] = []
    skipped: list[dict] = []

    conn = get_conn(get_db_path())

    try:
        for asset_id in asset_ids:
            asset = get_asset_by_id(conn, asset_id)

            if asset is None:
                skipped.append(
                    {
                        "asset_id": asset_id,
                        "title": None,
                        "reason": "资产不存在",
                    }
                )
                continue

            if not overwrite and has_active_artifact(conn, asset_id, "summary"):
                skipped.append(
                    {
                        "asset_id": asset_id,
                        "title": asset["title"],
                        "reason": "已有总结",
                    }
                )
                continue

            task_id, reason = _create_summarization_task(conn, asset_id)

            if task_id is None:
                skipped.append(
                    {
                        "asset_id": asset_id,
                        "title": asset["title"],
                        "reason": reason,
                    }
                )
            else:
                created.append(task_id)

        conn.commit()
    finally:
        conn.close()

    if created:
        batch_runner.execute_tasks(created, run_summarization_task)

    logger.info(
        "批量总结：创建 {} 个任务，跳过 {} 项", len(created), len(skipped)
    )

    return {
        "created": len(created),
        "task_ids": created,
        "skipped": skipped,
    }


def resume_pending_summarization_tasks() -> None:
    """打开知识库时恢复未完结的总结任务（重跑幂等；in-flight 去重见 batch_runner）。"""
    conn = get_conn(get_db_path())

    try:
        rows = conn.execute(
            """
            SELECT id FROM tasks
            WHERE type = 'summarization' AND status IN ('pending', 'running')
            """
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return

    task_ids = [row["id"] for row in rows]
    logger.info("恢复未完结的总结任务：{} 个", len(task_ids))
    batch_runner.execute_tasks(task_ids, run_summarization_task)


def run_summarization_task(task_id: str) -> None:
    """后台执行总结任务。"""
    conn = get_conn(get_db_path())

    try:
        task = task_repository.get_task(conn, task_id)

        if task is None:
            return

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

        llm_config = get_summary_llm_config()

        task_repository.update_task(
            conn, task_id, status="running", started_at=utcnow_iso()
        )
        conn.commit()

        input_text = get_summary_input_text(conn, asset)
        summary_content = summarize_text(input_text, llm_config)

        summary_path = derived_output_path(asset["absolute_path"], "summary.md")

        backup_existing_summary(summary_path)

        summary_path.write_text(
            build_summary_frontmatter(asset, llm_config) + summary_content,
            encoding="utf-8",
        )

        # 刷新扫描和全文索引（失败不影响任务结果）
        warning = None

        try:
            scan_current_library()
            rebuild_fulltext_index()
        except Exception as scan_exc:
            warning = f"总结生成成功，但刷新索引失败：{scan_exc}"

        task_repository.update_task(
            conn,
            task_id,
            status="success",
            output_path=str(summary_path),
            error=warning,
            finished_at=utcnow_iso(),
        )
        conn.commit()

        logger.info("总结任务完成：{} -> {}", task_id, summary_path)
    except Exception as exc:
        logger.error("总结任务失败：{} - {}", task_id, exc)

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
