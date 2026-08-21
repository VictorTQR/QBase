"""assets 表数据访问。"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone

from app.utils import escape_like


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
  ) AS has_note,
  EXISTS(
    SELECT 1 FROM artifacts b
    WHERE b.asset_id = a.id AND b.kind = 'parsed' AND b.status = 'active'
  ) AS has_parsed,
  EXISTS(
    SELECT 1 FROM artifacts b
    WHERE b.asset_id = a.id AND b.kind = 'meta' AND b.status = 'active'
  ) AS has_meta
"""

# 排序白名单，防止 SQL 注入
_ALLOWED_ORDER_COLUMNS = {"title", "mtime", "size", "type"}


def _build_asset_filters(
    asset_type: str | None,
    keyword: str | None,
    tag_names: list[str] | None = None,
) -> tuple[str, list]:
    """构造类型、文件名（标题/相对路径）与标签筛选条件。

    标签为多选 OR 语义：资产带任一所选标签即保留。
    """
    clauses: list[str] = []
    params: list = []

    if asset_type:
        clauses.append("a.type = ?")
        params.append(asset_type)

    if keyword:
        like_pattern = f"%{escape_like(keyword)}%"
        clauses.append(
            "(a.title LIKE ? ESCAPE '\\' OR a.relative_path LIKE ? ESCAPE '\\')"
        )
        params.extend([like_pattern, like_pattern])

    if tag_names:
        placeholders = ", ".join("?" * len(tag_names))
        clauses.append(
            "EXISTS("
            "SELECT 1 FROM asset_tags at "
            "JOIN tags t ON t.id = at.tag_id "
            f"WHERE at.asset_id = a.id AND t.name IN ({placeholders})"
            ")"
        )
        params.extend(tag_names)

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_clause, params


def list_assets(
    conn: sqlite3.Connection,
    limit: int = 50,
    offset: int = 0,
    asset_type: str | None = None,
    order_by: str = "mtime",
    order_dir: str = "DESC",
    keyword: str | None = None,
    tag_names: list[str] | None = None,
) -> list[dict]:
    """获取资产列表，附带派生文件状态（徽章）与标签，支持筛选、排序与分页。

    order_by: "title" / "mtime" / "size" / "type"
    order_dir: "ASC" / "DESC"
    keyword: 文件名关键词，命中标题或相对路径
    tag_names: 标签多选（OR）；行内 tags 为标签名列表，展示顺序由 UI 排序
    """
    if order_by not in _ALLOWED_ORDER_COLUMNS:
        order_by = "mtime"
    if order_dir.upper() not in ("ASC", "DESC"):
        order_dir = "DESC"

    base_columns = """
      a.id, a.title, a.type, a.relative_path, a.absolute_path,
      a.size, a.mtime, a.parse_status, a.created_at, a.updated_at,
      (SELECT group_concat(t.name, ',')
         FROM asset_tags at
         JOIN tags t ON t.id = at.tag_id
        WHERE at.asset_id = a.id) AS tags_csv
    """

    where_clause, params = _build_asset_filters(asset_type, keyword, tag_names)

    rows = conn.execute(
        f"""
        SELECT {base_columns}, {_HAS_BADGE_COLUMNS}
        FROM assets a
        {where_clause}
        ORDER BY a.{order_by} {order_dir}
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset],
    ).fetchall()

    assets = []
    for row in rows:
        asset = dict(row)
        tags_csv = asset.pop("tags_csv", None) or ""
        asset["tags"] = [name for name in tags_csv.split(",") if name]
        assets.append(asset)

    return assets


def count_assets(
    conn: sqlite3.Connection,
    asset_type: str | None = None,
    keyword: str | None = None,
    tag_names: list[str] | None = None,
) -> int:
    where_clause, params = _build_asset_filters(asset_type, keyword, tag_names)
    row = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM assets a {where_clause}",
        params,
    ).fetchone()
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
    """删除已不存在文件的 asset 记录，返回删除数量。

    同步清理 asset_tags 绑定与零引用标签（全库无外键，清理走显式 SQL）。
    """
    rows = conn.execute("SELECT id, relative_path FROM assets").fetchall()

    missing_ids = [
        row["id"] for row in rows if row["relative_path"] not in seen_paths
    ]

    if missing_ids:
        conn.executemany(
            "DELETE FROM assets WHERE id = ?",
            [(asset_id,) for asset_id in missing_ids],
        )
        conn.executemany(
            "DELETE FROM asset_tags WHERE asset_id = ?",
            [(asset_id,) for asset_id in missing_ids],
        )
        conn.execute(
            "DELETE FROM tags WHERE id NOT IN (SELECT tag_id FROM asset_tags)"
        )

    return len(missing_ids)
