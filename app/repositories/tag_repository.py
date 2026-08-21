"""tags / asset_tags 表数据访问（m15 标签系统）。"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_tag_id(name: str) -> str:
    """使用标签名生成稳定 ID（同名重建得到同 ID）。"""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"tag:{name}"))


def list_tags(conn: sqlite3.Connection) -> list[dict]:
    """全部标签 + 使用数（绑定资产数），使用数降序、名称升序。"""
    rows = conn.execute(
        """
        SELECT t.id, t.name, COUNT(at.asset_id) AS usage
        FROM tags t
        LEFT JOIN asset_tags at ON at.tag_id = t.id
        GROUP BY t.id, t.name
        ORDER BY usage DESC, t.name COLLATE NOCASE ASC
        """
    ).fetchall()

    return [dict(row) for row in rows]


def get_tags_for_asset(conn: sqlite3.Connection, asset_id: str) -> list[str]:
    """获取某资产的标签名列表，名称升序。"""
    rows = conn.execute(
        """
        SELECT t.name
        FROM asset_tags at
        JOIN tags t ON t.id = at.tag_id
        WHERE at.asset_id = ?
        ORDER BY t.name COLLATE NOCASE ASC
        """,
        (asset_id,),
    ).fetchall()

    return [str(row["name"]) for row in rows]


def set_asset_tags(
    conn: sqlite3.Connection, asset_id: str, tag_names: list[str]
) -> list[str]:
    """全量替换某资产的标签绑定。

    缺失的 tags 行先创建（按名取稳定 ID），删除该资产既有绑定后重插；
    随后清理零引用标签。调用方负责 commit。
    """
    now = utcnow_iso()

    for name in tag_names:
        conn.execute(
            """
            INSERT OR IGNORE INTO tags (id, name, created_at)
            VALUES (?, ?, ?)
            """,
            (make_tag_id(name), name, now),
        )

    conn.execute("DELETE FROM asset_tags WHERE asset_id = ?", (asset_id,))

    tag_ids = [
        str(row["id"])
        for row in conn.execute(
            "SELECT id FROM tags WHERE name IN (%s)"
            % ",".join("?" * len(tag_names)),
            tag_names,
        ).fetchall()
    ] if tag_names else []

    if tag_ids:
        conn.executemany(
            "INSERT OR IGNORE INTO asset_tags (asset_id, tag_id, created_at)"
            " VALUES (?, ?, ?)",
            [(asset_id, tag_id, now) for tag_id in tag_ids],
        )

    delete_orphan_tags(conn)

    return list(tag_names)


def delete_orphan_tags(conn: sqlite3.Connection) -> int:
    """删除零引用标签，返回删除数量。"""
    cursor = conn.execute(
        "DELETE FROM tags WHERE id NOT IN (SELECT tag_id FROM asset_tags)"
    )
    return cursor.rowcount
