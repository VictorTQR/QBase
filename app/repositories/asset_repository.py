"""assets 表数据访问。"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_asset_id(relative_path: str) -> str:
    """使用相对路径生成稳定 ID（相对路径不变则 ID 不变）。"""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, relative_path))


def upsert_asset(conn: sqlite3.Connection, asset: dict) -> str:
    """新增或更新 asset，返回资产 ID。"""
    now = utcnow_iso()

    existing = conn.execute(
        "SELECT id FROM assets WHERE relative_path = ?",
        (asset["relative_path"],),
    ).fetchone()

    if existing:
        conn.execute(
            """
            UPDATE assets
            SET
              title = ?,
              type = ?,
              absolute_path = ?,
              mime_type = ?,
              size = ?,
              mtime = ?,
              parse_status = ?,
              updated_at = ?
            WHERE relative_path = ?
            """,
            (
                asset["title"],
                asset["type"],
                asset["absolute_path"],
                asset.get("mime_type"),
                asset["size"],
                asset["mtime"],
                asset["parse_status"],
                now,
                asset["relative_path"],
            ),
        )
        return str(existing["id"])

    asset_id = make_asset_id(asset["relative_path"])

    conn.execute(
        """
        INSERT INTO assets (
          id, title, type, relative_path, absolute_path, mime_type,
          size, mtime, file_hash, duration_seconds, parse_status,
          created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            asset_id,
            asset["title"],
            asset["type"],
            asset["relative_path"],
            asset["absolute_path"],
            asset.get("mime_type"),
            asset["size"],
            asset["mtime"],
            None,
            None,
            asset["parse_status"],
            now,
            now,
        ),
    )

    return asset_id


def list_assets(
    conn: sqlite3.Connection,
    limit: int = 1000,
    asset_type: str | None = None,
) -> list[dict]:
    """获取资产列表。"""
    if asset_type:
        rows = conn.execute(
            """
            SELECT id, title, type, relative_path, absolute_path,
                   size, mtime, parse_status, created_at, updated_at
            FROM assets
            WHERE type = ?
            ORDER BY type, title
            LIMIT ?
            """,
            (asset_type, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id, title, type, relative_path, absolute_path,
                   size, mtime, parse_status, created_at, updated_at
            FROM assets
            ORDER BY type, title
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def count_assets(conn: sqlite3.Connection, asset_type: str | None = None) -> int:
    if asset_type:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM assets WHERE type = ?", (asset_type,)
        ).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM assets").fetchone()
    return int(row["cnt"]) if row else 0


def delete_missing_assets(conn: sqlite3.Connection, seen_paths: set[str]) -> int:
    """删除已不存在文件的 asset 记录，返回删除数量。"""
    rows = conn.execute("SELECT id, relative_path FROM assets").fetchall()

    missing_ids = [
        row["id"] for row in rows if row["relative_path"] not in seen_paths
    ]

    if missing_ids:
        conn.executemany(
            "DELETE FROM assets WHERE id = ?",
            [(asset_id,) for asset_id in missing_ids],
        )

    return len(missing_ids)
