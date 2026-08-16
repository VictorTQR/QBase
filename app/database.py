"""SQLite 连接与建表。

库级数据库位于 <library_root>/.knowledge/db.sqlite。
文件系统是唯一数据源，数据库只是索引缓存——删掉 .knowledge 可重建。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  type TEXT NOT NULL,
  relative_path TEXT NOT NULL UNIQUE,
  absolute_path TEXT NOT NULL,
  mime_type TEXT,
  size INTEGER,
  mtime INTEGER,
  file_hash TEXT,
  duration_seconds REAL,
  parse_status TEXT DEFAULT 'unknown',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


def get_conn(db_path: Path) -> sqlite3.Connection:
    """打开连接，行以 dict 形式返回。调用方负责 close。"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path) -> None:
    """初始化库级数据库（幂等）。"""
    conn = get_conn(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
