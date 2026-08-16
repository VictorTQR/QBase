"""转录任务服务：创建任务 → 后台线程执行 CLI → 完成后重扫描。"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from loguru import logger

from app.database import get_conn
from app.repositories import task_repository
from app.repositories.asset_repository import get_asset_by_id
from app.services.cli_runner import build_command, run_cli_command, tail
from app.services.config_service import get_transcribe_cli_config
from app.services.index_service import rebuild_fulltext_index
from app.services.scanner_service import scan_current_library
from app.state import get_db_path


def start_transcription(asset_id: str) -> str:
    """创建并启动转录任务，返回 task_id。"""
    conn = get_conn(get_db_path())

    try:
        asset = get_asset_by_id(conn, asset_id)

        if asset is None:
            raise ValueError("资产不存在")

        if asset["type"] not in {"audio", "video"}:
            raise ValueError("只有音频或视频可以生成转录")

        running_count = task_repository.count_running_tasks(
            conn,
            asset_id=asset_id,
            task_type="transcription",
        )

        if running_count > 0:
            raise ValueError("该资产已有转录任务正在运行")

        cli_config = get_transcribe_cli_config()

        expected_output = Path(asset["absolute_path"]).with_suffix(".txt")

        command = build_command(
            cli_config["command"],
            {
                "input": asset["absolute_path"],
            },
        )

        params = {
            "asset_id": asset_id,
            "input": asset["absolute_path"],
            "expected_output": str(expected_output),
            "cwd": cli_config.get("cwd"),
        }

        task_id = task_repository.create_task(
            conn,
            asset_id=asset_id,
            task_type="transcription",
            params=params,
            command=command,
            output_path=str(expected_output),
        )

        conn.commit()
    finally:
        conn.close()

    thread = threading.Thread(
        target=run_transcription_task,
        args=(task_id,),
        daemon=True,
    )
    thread.start()

    logger.info("转录任务已创建：{} ({})", task_id[:8], asset["title"])

    return task_id


def run_transcription_task(task_id: str) -> None:
    """后台执行转录任务。"""
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
                finished_at=task_repository.utcnow_iso(),
            )
            conn.commit()
            return

        cli_config = get_transcribe_cli_config()

        command = build_command(
            cli_config["command"],
            {
                "input": asset["absolute_path"],
            },
        )

        task_repository.update_task(
            conn,
            task_id,
            status="running",
            command=json.dumps(command, ensure_ascii=False),
            started_at=task_repository.utcnow_iso(),
        )
        conn.commit()

        result = run_cli_command(
            command,
            cwd=cli_config.get("cwd"),
            timeout=cli_config.get("timeout", 14400),
        )

        expected_output = Path(asset["absolute_path"]).with_suffix(".txt")

        if result.returncode == 0:
            if expected_output.exists():
                warning = None

                try:
                    scan_current_library()
                    rebuild_fulltext_index()
                except Exception as scan_exc:
                    warning = f"转录成功，但刷新索引失败：{scan_exc}"

                task_repository.update_task(
                    conn,
                    task_id,
                    status="success",
                    output_path=str(expected_output),
                    error=warning,
                    finished_at=task_repository.utcnow_iso(),
                )
                conn.commit()
                logger.info("转录任务成功：{}", asset["title"])
            else:
                error_text = (
                    "CLI 执行成功，但没有找到输出文件。\n"
                    f"期望输出：{expected_output}\n\n"
                    f"stdout:\n{tail(result.stdout)}\n\n"
                    f"stderr:\n{tail(result.stderr)}"
                )

                task_repository.update_task(
                    conn,
                    task_id,
                    status="failed",
                    error=error_text,
                    finished_at=task_repository.utcnow_iso(),
                )
                conn.commit()
        else:
            if result.returncode == 124:
                error_text = (
                    "转录任务超时。\n\n"
                    f"stdout:\n{tail(result.stdout)}\n\n"
                    f"stderr:\n{tail(result.stderr)}"
                )
            elif result.returncode == 127:
                error_text = (
                    "无法启动 CLI 命令。请检查 uv 是否可用，以及配置是否正确。\n\n"
                    f"stderr:\n{tail(result.stderr)}"
                )
            else:
                error_text = (
                    f"CLI 退出码：{result.returncode}\n\n"
                    f"stdout:\n{tail(result.stdout)}\n\n"
                    f"stderr:\n{tail(result.stderr)}"
                )

            task_repository.update_task(
                conn,
                task_id,
                status="failed",
                error=error_text,
                finished_at=task_repository.utcnow_iso(),
            )
            conn.commit()
            logger.warning("转录任务失败（{}）：{}", result.returncode, asset["title"])

    except Exception as exc:
        logger.exception("转录任务异常：{}", task_id)

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
