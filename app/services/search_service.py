"""搜索服务：文件名搜索 + 全文搜索（FTS5 + LIKE 兜底）。"""

from __future__ import annotations

import sqlite3

from app.database import get_conn
from app.state import get_db_path


def escape_like(value: str) -> str:
    """转义 LIKE 查询中的特殊字符。"""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def build_fts_query(query: str) -> str | None:
    """构造简单的 FTS5 查询：'本地 知识 管理' → '"本地" OR "知识" OR "管理"'。"""
    terms = [t.replace('"', "").strip() for t in query.split() if t.strip()]

    if not terms:
        return None

    return " OR ".join(f'"{term}"' for term in terms)


def make_snippet(content: str, query: str, radius: int = 80) -> str:
    """生成搜索结果片段。"""
    if not content:
        return ""

    query_lower = query.lower()
    content_lower = content.lower()
    index = content_lower.find(query_lower)

    if index < 0:
        return content[:160].replace("\n", " ")

    start = max(0, index - radius)
    end = min(len(content), index + len(query) + radius)

    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(content) else ""

    return prefix + content[start:end].replace("\n", " ") + suffix


def search_filename(conn, query: str, limit: int = 50) -> list[dict]:
    """文件名搜索：命中标题或相对路径。"""
    like_pattern = f"%{escape_like(query)}%"

    rows = conn.execute(
        """
        SELECT
          id AS asset_id, title AS asset_title,
          type AS asset_type, relative_path
        FROM assets
        WHERE title LIKE ? ESCAPE '\\'
           OR relative_path LIKE ? ESCAPE '\\'
        ORDER BY title
        LIMIT ?
        """,
        (like_pattern, like_pattern, limit),
    ).fetchall()

    return [
        {
            "asset_id": row["asset_id"],
            "asset_title": row["asset_title"],
            "asset_type": row["asset_type"],
            "kind": "asset",
            "relative_path": row["relative_path"],
            "snippet": row["relative_path"],
        }
        for row in rows
    ]


def search_fulltext(conn, query: str, limit: int = 50) -> list[dict]:
    """全文内容搜索：先 FTS5，再 LIKE 兜底（中文子串更可靠）。"""
    results: list[dict] = []
    seen_chunk_ids: set[str] = set()

    fts_query = build_fts_query(query)

    if fts_query:
        try:
            rows = conn.execute(
                """
                SELECT
                  c.id AS chunk_id, c.asset_id AS asset_id, c.kind AS kind,
                  c.relative_path AS relative_path, c.content AS content,
                  a.title AS asset_title, a.type AS asset_type
                FROM chunks_fts f
                JOIN chunks c ON c.rowid = f.rowid
                LEFT JOIN assets a ON a.id = c.asset_id
                WHERE chunks_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (fts_query, limit),
            ).fetchall()

            for row in rows:
                if len(results) >= limit:
                    break

                if row["chunk_id"] in seen_chunk_ids:
                    continue

                seen_chunk_ids.add(row["chunk_id"])
                results.append(
                    {
                        "asset_id": row["asset_id"],
                        "asset_title": row["asset_title"] or row["relative_path"],
                        "asset_type": row["asset_type"],
                        "kind": row["kind"],
                        "relative_path": row["relative_path"],
                        "snippet": make_snippet(row["content"], query),
                    }
                )
        except sqlite3.OperationalError:
            pass

    like_pattern = f"%{escape_like(query)}%"

    rows = conn.execute(
        """
        SELECT
          c.id AS chunk_id, c.asset_id AS asset_id, c.kind AS kind,
          c.relative_path AS relative_path, c.content AS content,
          a.title AS asset_title, a.type AS asset_type
        FROM chunks c
        LEFT JOIN assets a ON a.id = c.asset_id
        WHERE c.content LIKE ? ESCAPE '\\'
        ORDER BY c.id
        LIMIT ?
        """,
        (like_pattern, limit),
    ).fetchall()

    for row in rows:
        if len(results) >= limit:
            break

        if row["chunk_id"] in seen_chunk_ids:
            continue

        seen_chunk_ids.add(row["chunk_id"])
        results.append(
            {
                "asset_id": row["asset_id"],
                "asset_title": row["asset_title"] or row["relative_path"],
                "asset_type": row["asset_type"],
                "kind": row["kind"],
                "relative_path": row["relative_path"],
                "snippet": make_snippet(row["content"], query),
            }
        )

    return results


def search(query: str, mode: str, limit: int = 50) -> list[dict]:
    """统一搜索入口。mode: filename / fulltext。"""
    query = query.strip()

    if not query:
        return []

    conn = get_conn(get_db_path())

    try:
        if mode == "filename":
            return search_filename(conn, query, limit=limit)

        return search_fulltext(conn, query, limit=limit)
    finally:
        conn.close()
