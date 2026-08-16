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


_HAS_BADGE_COLUMNS = """
  EXISTS(
    SELECT 1 FROM artifacts b
    WHERE b.asset_id = a.id AND b.kind = 'transcript' AND b.status = 'active'
  ) AS has_transcript,
  EXISTS(
    SELECT 1 FROM artifacts b
    WHERE b.asset_id = a.id AND b.kind = 'summary' AND b.status = 'active'
  ) AS has_summary,
  EXISTS(
    SELECT 1 FROM artifacts b
    WHERE b.asset_id = a.id AND b.kind = 'note' AND b.status = 'active'
  ) AS has_note
"""


def list_assets(
    conn: sqlite3.Connection,
    limit: int = 1000,
    asset_type: str | None = None,
) -> list[dict]:
    """获取资产列表，附带派生文件状态（转录/总结/笔记徽章）。"""
    base_columns = """
      a.id, a.title, a.type, a.relative_path, a.absolute_path,
      a.size, a.mtime, a.parse_status, a.created_at, a.updated_at
    """

    if asset_type:
        rows = conn.execute(
            f"""
            SELECT {base_columns}, {_HAS_BADGE_COLUMNS}
            FROM assets a
            WHERE a.type = ?
            ORDER BY a.type, a.title
            LIMIT ?
            """,
            (asset_type, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            f"""
            SELECT {base_columns}, {_HAS_BADGE_COLUMNS}
            FROM assets a
            ORDER BY a.type, a.title
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


def get_asset_by_id(conn: sqlite3.Connection, asset_id: str) -> dict | None:
    """按 ID 获取单个资产。"""
    row = conn.execute(
        """
        SELECT id, title, type, relative_path, absolute_path, mime_type,
               size, mtime, file_hash, duration_seconds, parse_status,
               created_at, updated_at
        FROM assets
        WHERE id = ?
        """,
        (asset_id,),
    ).fetchone()

    return dict(row) if row else None


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
