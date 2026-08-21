"""文档解析任务服务：submit → poll 循环 → fetch 产物 → to_markdown
→ 写 {stem}.parsed.md → 自动重扫 + 重建全文索引（成功后动作对齐转录/总结）。

与转录任务的模型差异：远端解析（MinerU）是分钟级异步任务，batch_id 持久化
进任务 params_json，应用重启后 resume_running_parse_tasks() 恢复轮询
（MinerU 结果接口幂等），不产生孤儿任务；本地解析（epub，m10）秒级无状态，
fetch 现算，重启后重算即可。解析器按扩展名路由（.epub → 内置本地解析器，
其余 → [parse].provider）。
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path

from loguru import logger

from app.database import get_conn
from app.repositories import task_repository
from app.repositories.asset_repository import get_asset_by_id
from app.rules import derived_output_path
from app.services.config_service import get_parse_config
from app.services.index_service import rebuild_fulltext_index
from app.services.parsers import get_parser_for_extension
from app.services.parsers.base import ParseSubmission
from app.services.scanner_service import scan_current_library
from app.state import get_db_path, state

# 可解析后缀白名单（.epub 走内置本地解析器、图片留给未来 provider）
PARSEABLE_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
    ".xlsx",
    ".xls",
    ".epub",
}
PARSED_SUFFIX = ".parsed.md"

# 正在执行的解析任务守卫：防止 resume 与新任务对同一 task 重复起线程
_live_task_ids: set[str] = set()
_live_lock = threading.Lock()


def _parsed_path(asset_path: str) -> Path:
    """paper.pdf -> paper.parsed.md；m11 跟随现状：存在 <name>.kb/ 目录时写
    入其中（parsed.md 原名），平铺时与 rules.ARTIFACT_SUFFIXES 的绑定键一致。"""
    return derived_output_path(asset_path, "parsed.md")


def _backup_dir() -> Path:
    if state.library_root is None:
        raise RuntimeError("未打开知识库")

    backup_dir = state.library_root / ".knowledge" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def start_parsing(asset_id: str) -> str:
    """创建并启动解析任务（前置校验 + 并发去重，对齐 start_transcription）。"""
    conn = get_conn(get_db_path())

    try:
        asset = get_asset_by_id(conn, asset_id)

        if asset is None:
            raise ValueError("资产不存在")

        ext = Path(asset["absolute_path"]).suffix.lower()

        if ext not in PARSEABLE_EXTENSIONS:
            raise ValueError(f"当前不支持解析 {ext} 文件")

        if task_repository.count_running_tasks(
            conn, asset_id=asset_id, task_type="parse"
        ) > 0:
            raise ValueError("该资产已有解析任务正在运行")

        config = get_parse_config()

        if not config.get("enabled"):
            raise ValueError("文档解析未启用，请在设置页开启 [parse]")

        # 按扩展名路由（.epub 本地免 token；其余 provider 未注册/token 缺失在此即抛）
        parser = get_parser_for_extension(config, ext)

        size = Path(asset["absolute_path"]).stat().st_size

        if parser.max_file_bytes and size > parser.max_file_bytes:
            raise ValueError(
                f"文件超过 {parser.name} 单文件 "
                f"{parser.max_file_bytes // (1024 * 1024)}MB 上限，无法解析"
            )

        parsed = _parsed_path(asset["absolute_path"])
        params = {
            "asset_id": asset_id,
            "input": asset["absolute_path"],
            "provider": parser.name,  # 实际使用的解析器（epub 固定本地）
            # submission 字段提交成功后回写，重启恢复轮询的凭据
        }

        task_id = task_repository.create_task(
            conn,
            asset_id=asset_id,
            task_type="parse",
            params=params,
            command=None,
            output_path=str(parsed),
        )

        conn.commit()
    finally:
        conn.close()

    _spawn_task_thread(task_id)

    logger.info("解析任务已创建：{} ({})", task_id[:8], asset["title"])

    return task_id


def _spawn_task_thread(task_id: str) -> None:
    with _live_lock:
        if task_id in _live_task_ids:
            return
        _live_task_ids.add(task_id)

    threading.Thread(target=run_parse_task, args=(task_id,), daemon=True).start()


def run_parse_task(task_id: str) -> None:
    """后台执行解析任务：提交 → 轮询 → 取回产物 → 写 parsed.md → 刷新索引。"""
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

        config = get_parse_config()
        asset_ext = Path(asset["absolute_path"]).suffix.lower()
        parser = get_parser_for_extension(config, asset_ext)
        params = json.loads(task["params_json"]) if task["params_json"] else {}

        task_repository.update_task(
            conn,
            task_id,
            status="running",
            started_at=task_repository.utcnow_iso(),
        )
        conn.commit()

        # ── 阶段 1：提交（params 已含 submission 则跳过——重启恢复场景）──
        if params.get("submission"):
            submission = ParseSubmission(**params["submission"])
        else:
            submission = parser.submit([Path(asset["absolute_path"])])
            params["submission"] = {
                "batch_id": submission.batch_id,
                "files": submission.files,
            }
            task_repository.update_task(
                conn,
                task_id,
                params_json=json.dumps(params, ensure_ascii=False),
            )
            conn.commit()

        # ── 阶段 2：轮询（结果接口幂等）──
        deadline = time.monotonic() + config.get("timeout_seconds", 1800)
        interval = max(1, config.get("poll_interval_seconds", 10))
        state_obj = None

        while True:
            states = parser.poll(submission)
            state_obj = states[0] if states else None

            if state_obj is None:
                raise ValueError("解析结果为空：远端未返回该文件的状态")

            if state_obj.state == "done":
                if state_obj.full_zip_url:
                    break

                raise ValueError("解析已完成，但远端未返回结果下载地址")

            if state_obj.state == "failed":
                raise ValueError(
                    f"{parser.name} 解析失败：{state_obj.err_msg or '未给出原因'}"
                )

            if time.monotonic() > deadline:
                raise ValueError(
                    f"解析超时（超过 {config.get('timeout_seconds', 1800)} 秒），"
                    "可在任务中心重试"
                )

            time.sleep(interval)

        # ── 阶段 3：取回产物 + 落盘 ──
        raw = parser.fetch(state_obj)
        md_text = parser.to_markdown(raw)

        parsed = _parsed_path(asset["absolute_path"])
        backup_dir = _backup_dir()
        # 留档命名基座用资产 stem：.kb 模式下 parsed.stem 恒为 "parsed"，会跨资产撞名
        asset_stem = Path(asset["absolute_path"]).stem

        if parsed.exists():
            # 覆盖重解析前，旧 parsed.md 一并留档（对齐总结覆盖备份策略）
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_md = backup_dir / f"{asset_stem}.{timestamp}.bak.md"
            backup_md.write_text(parsed.read_text(encoding="utf-8"), encoding="utf-8")

        if parser.PRODUCT_BACKUP_SUFFIX:
            # 产物留档（MinerU 结果 zip；本地解析产物即 md 文本，不留档）；
            # 用平铺产物名，两种写入模式的留档名保持一致
            product = backup_dir / (
                f"{asset_stem}{PARSED_SUFFIX}{parser.PRODUCT_BACKUP_SUFFIX}"
            )
            product.write_bytes(raw)

        parsed.write_text(md_text, encoding="utf-8")

        # ── 阶段 4：刷新索引（对齐转录/总结）──
        warning = None

        try:
            scan_current_library()
            rebuild_fulltext_index()
        except Exception as scan_exc:
            warning = f"解析成功，但刷新索引失败：{scan_exc}"

        task_repository.update_task(
            conn,
            task_id,
            status="success",
            output_path=str(parsed),
            error=warning,
            finished_at=task_repository.utcnow_iso(),
        )
        conn.commit()
        logger.info("解析任务成功：{}", asset["title"])

    except Exception as exc:
        logger.exception("解析任务异常：{}", task_id)

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
        with _live_lock:
            _live_task_ids.discard(task_id)
        conn.close()


def resume_running_parse_tasks() -> None:
    """打开知识库时，恢复未完结的解析任务。

    - params_json 已含 submission：直接续轮询（幂等）
    - 尚未提交：从 submit 重新开始
    _live_task_ids 保证同一任务不会重复起线程。
    """
    conn = get_conn(get_db_path())

    try:
        rows = conn.execute(
            """
            SELECT id FROM tasks
            WHERE type = 'parse' AND status IN ('pending', 'running')
            """
        ).fetchall()
    finally:
        conn.close()

    for row in rows:
        logger.info("恢复未完结的解析任务：{}", row["id"][:8])
        _spawn_task_thread(row["id"])
