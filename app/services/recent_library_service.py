"""最近打开知识库记录（本地持久化，文件即数据）。

存储位置：<项目根>/data/recent_libraries.json
格式：[{ "path": "...", "opened_at": "ISO8601" }, ...]（最新在前，最多 MAX_RECENTS 条）
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.config import PROJECT_ROOT

MAX_RECENTS = 5
RECENTS_FILE = PROJECT_ROOT / "data" / "recent_libraries.json"


def _normalize(path_str: str) -> str:
    """规范化路径为绝对、解析符号链接的形式。"""
    return str(Path(path_str).expanduser().resolve())


def _read() -> list[dict]:
    if not RECENTS_FILE.exists():
        return []
    try:
        with RECENTS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return [d for d in data if isinstance(d, dict) and d.get("path")]
    except (json.JSONDecodeError, OSError):
        return []


def _write(items: list[dict]) -> None:
    RECENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with RECENTS_FILE.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def add_recent_library(path_str: str) -> None:
    """记录一个最近打开的知识库（去重、最新在前、超量截断）。"""
    norm = _normalize(path_str)

    items = _read()
    # 去重：移除已有的同路径记录
    items = [it for it in items if _normalize(it["path"]) != norm]
    items.insert(0, {"path": norm, "opened_at": datetime.now().isoformat(timespec="seconds")})
    items = items[:MAX_RECENTS]
    _write(items)


def get_recent_libraries() -> list[dict]:
    """返回最近打开且当前仍然存在的知识库列表（最新在前）。

    读取时剔除目录已不存在的条目，并回写清理后的列表。
    """
    items = _read()
    kept = []
    for it in items:
        path = it.get("path", "")
        if path and Path(path).expanduser().is_dir():
            kept.append(it)
    if len(kept) != len(items):
        _write(kept)
    return kept


def clear_recents() -> None:
    """清空最近记录。"""
    if RECENTS_FILE.exists():
        RECENTS_FILE.unlink()
