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

CREATE TABLE IF NOT EXISTS artifacts (
  id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  relative_path TEXT NOT NULL UNIQUE,
  absolute_path TEXT NOT NULL,
  file_hash TEXT,
  mtime INTEGER,
  source TEXT,
  generator TEXT,
  model TEXT,
  status TEXT DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  asset_id TEXT,
  type TEXT NOT NULL,
  status TEXT NOT NULL,
  command TEXT,
  params_json TEXT,
  output_path TEXT,
  error TEXT,
  pid INTEGER,
  created_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL,
  artifact_id TEXT,
  kind TEXT NOT NULL,
  relative_path TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  content_hash TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS embedding_cache (
  content_hash TEXT PRIMARY KEY,
  model TEXT NOT NULL,
  vector BLOB NOT NULL,
  dimension INTEGER NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS asset_tags (
  asset_id TEXT NOT NULL,
  tag_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (asset_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_artifacts_asset_id ON artifacts(asset_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_kind ON artifacts(kind);
CREATE INDEX IF NOT EXISTS idx_asset_tags_tag_id ON asset_tags(tag_id);
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
    """初始化库级数据库（幂等）。建表 + FTS5 虚拟表。"""
    conn = get_conn(db_path)
    try:
        conn.executescript(SCHEMA)

        try:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                  content,
                  content='chunks',
                  content_rowid='rowid'
                );
                """
            )
        except sqlite3.OperationalError:
            pass

        conn.commit()
    finally:
        conn.close()
