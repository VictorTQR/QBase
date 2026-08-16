"""目录扫描服务：把受支持的文件写入 assets 表。"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from loguru import logger

from app.database import get_conn
from app.repositories.asset_repository import delete_missing_assets, upsert_asset
from app.rules import classify_extension, get_parse_status, should_ignore_dir
from app.state import get_db_path, state


def scan_current_library() -> dict:
    """扫描当前知识库，将支持的文件写入 assets 表，清理失效记录。"""
    if state.library_root is None:
        raise ValueError("未打开知识库")

    root: Path = state.library_root
    conn = get_conn(get_db_path())

    seen_paths: set[str] = set()
    stats = {
        "added_or_updated": 0,
        "skipped": 0,
        "removed": 0,
        "total_assets": 0,
    }

    try:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]

            for filename in filenames:
                if filename.startswith("."):
                    continue

                full_path = Path(dirpath) / filename

                try:
                    stat_result = full_path.stat()
                except OSError:
                    stats["skipped"] += 1
                    continue

                ext = full_path.suffix.lower()
                asset_type = classify_extension(ext)

                if not asset_type:
                    continue

                relative_path = full_path.relative_to(root).as_posix()
                seen_paths.add(relative_path)

                upsert_asset(
                    conn,
                    {
                        "title": full_path.stem,
                        "type": asset_type,
                        "relative_path": relative_path,
                        "absolute_path": str(full_path),
                        "mime_type": None,
                        "size": stat_result.st_size,
                        "mtime": int(stat_result.st_mtime),
                        "parse_status": get_parse_status(asset_type, ext),
                    },
                )
                stats["added_or_updated"] += 1

        stats["removed"] = delete_missing_assets(conn, seen_paths)
        stats["total_assets"] = len(seen_paths)

        conn.commit()
    finally:
        conn.close()

    logger.info("扫描完成：{}", stats)
    return stats
