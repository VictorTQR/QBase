"""搜索服务：文件名搜索 + 全文搜索（FTS5 + LIKE 兜底）+ 向量语义搜索（m5）+ 综合搜索（m14，RRF 融合）。

m15 起四种模式均支持标签过滤（tag_names，多选 OR：资产带任一所选标签即保留）。
"""

from __future__ import annotations

import re
import sqlite3

from app.database import get_conn
from app.state import get_db_path
from app.utils import escape_like


def _tag_filter_sql(
    assets_ref: str, tag_names: list[str] | None
) -> tuple[str, list]:
    """构造标签过滤 EXISTS 片段，供各搜索模式复用。

    assets_ref 为 assets 表在当前查询中的引用（别名或表名）；
    未选标签时返回 ("", [])。
    """
    if not tag_names:
        return "", []

    placeholders = ", ".join("?" * len(tag_names))
    clause = (
        "EXISTS("
        "SELECT 1 FROM asset_tags at "
        "JOIN tags t ON t.id = at.tag_id "
        f"WHERE at.asset_id = {assets_ref}.id AND t.name IN ({placeholders})"
        ")"
    )
    return clause, list(tag_names)


def _asset_ids_with_any_tag(
    conn: sqlite3.Connection, asset_ids: list[str], tag_names: list[str] | None
) -> set[str]:
    """筛选出带任一所选标签的资产 ID 集合（供向量路回表后过滤）。"""
    if not tag_names:
        return set(asset_ids)

    if not asset_ids:
        return set()

    asset_ph = ", ".join("?" * len(asset_ids))
    tag_ph = ", ".join("?" * len(tag_names))
    rows = conn.execute(
        f"""
        SELECT DISTINCT at.asset_id
        FROM asset_tags at
        JOIN tags t ON t.id = at.tag_id
        WHERE at.asset_id IN ({asset_ph}) AND t.name IN ({tag_ph})
        """,
        asset_ids + list(tag_names),
    ).fetchall()

    return {str(row["asset_id"]) for row in rows}


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


def _extract_highlight_words(query: str) -> list[str]:
    """从查询字符串提取高亮词列表（与 build_fts_query 拆词逻辑一致）。"""
    words = query.strip().split()
    return [w for w in words if w not in ("AND", "OR", "NOT", "*")]


def _get_derived_badges(conn, asset_id: str | None) -> dict:
    """查询某资产的派生完成度（转录/总结/笔记/已解析/元数据/分析）。"""
    if not asset_id:
        return {}

    sql = """
        SELECT
            CASE WHEN EXISTS(
                SELECT 1 FROM artifacts WHERE asset_id = ? AND kind = 'transcript'
                AND status = 'active'
            ) THEN 1 ELSE 0 END AS has_transcript,
            CASE WHEN EXISTS(
                SELECT 1 FROM artifacts WHERE asset_id = ? AND kind = 'summary'
                AND status = 'active'
            ) THEN 1 ELSE 0 END AS has_summary,
            CASE WHEN EXISTS(
                SELECT 1 FROM artifacts WHERE asset_id = ? AND kind = 'note'
                AND status = 'active'
            ) THEN 1 ELSE 0 END AS has_note,
            CASE WHEN EXISTS(
                SELECT 1 FROM artifacts WHERE asset_id = ? AND kind = 'parsed'
                AND status = 'active'
            ) THEN 1 ELSE 0 END AS has_parsed,
            CASE WHEN EXISTS(
                SELECT 1 FROM artifacts WHERE asset_id = ? AND kind = 'meta'
                AND status = 'active'
            ) THEN 1 ELSE 0 END AS has_meta,
            CASE WHEN EXISTS(
                SELECT 1 FROM artifacts WHERE asset_id = ? AND kind = 'analysis'
                AND status = 'active'
            ) THEN 1 ELSE 0 END AS has_analysis
    """
    row = conn.execute(
        sql,
        (asset_id, asset_id, asset_id, asset_id, asset_id, asset_id),
    ).fetchone()
    return dict(row) if row else {}


def search_filename(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 50,
    tag_names: list[str] | None = None,
) -> list[dict]:
    """文件名搜索：命中标题或相对路径，可按标签过滤（OR）。"""
    like_pattern = f"%{escape_like(query)}%"
    tag_clause, tag_params = _tag_filter_sql("assets", tag_names)

    tag_and = f" AND {tag_clause}" if tag_clause else ""

    rows = conn.execute(
        f"""
        SELECT
          id AS asset_id, title AS asset_title,
          type AS asset_type, relative_path
        FROM assets
        WHERE (title LIKE ? ESCAPE '\\'
           OR relative_path LIKE ? ESCAPE '\\'){tag_and}
        ORDER BY title
        LIMIT ?
        """,
        (like_pattern, like_pattern, *tag_params, limit),
    ).fetchall()

    return [
                {
                    "asset_id": row["asset_id"],
                    "asset_title": row["asset_title"],
                    "asset_type": row["asset_type"],
                    "kind": "asset",
                    "relative_path": row["relative_path"],
                    "snippet": row["relative_path"],
                    "highlight_words": _extract_highlight_words(query),
                    "derived_badges": _get_derived_badges(conn, row["asset_id"]),
                }
        for row in rows
    ]


def search_fulltext(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 50,
    tag_names: list[str] | None = None,
) -> list[dict]:
    """全文内容搜索：先 FTS5，再 LIKE 兜底（中文子串更可靠），可按标签过滤（OR）。"""
    results: list[dict] = []
    seen_chunk_ids: set[str] = set()

    fts_query = build_fts_query(query)
    tag_clause, tag_params = _tag_filter_sql("a", tag_names)
    tag_and = f" AND {tag_clause}" if tag_clause else ""

    if fts_query:
        try:
            rows = conn.execute(
                f"""
                SELECT
                  c.id AS chunk_id, c.asset_id AS asset_id, c.kind AS kind,
                  c.relative_path AS relative_path, c.content AS content,
                  a.title AS asset_title, a.type AS asset_type
                FROM chunks_fts f
                JOIN chunks c ON c.rowid = f.rowid
                LEFT JOIN assets a ON a.id = c.asset_id
                WHERE chunks_fts MATCH ?{tag_and}
                ORDER BY rank
                LIMIT ?
                """,
                (fts_query, *tag_params, limit),
            ).fetchall()

            for row in rows:
                if len(results) >= limit:
                    break

                if row["chunk_id"] in seen_chunk_ids:
                    continue

                seen_chunk_ids.add(row["chunk_id"])
                results.append(
                    {
                        "chunk_id": row["chunk_id"],
                        "asset_id": row["asset_id"],
                        "asset_title": row["asset_title"] or row["relative_path"],
                        "asset_type": row["asset_type"],
                        "kind": row["kind"],
                        "relative_path": row["relative_path"],
                        "snippet": make_snippet(row["content"], query),
                        "highlight_words": _extract_highlight_words(query),
                        "derived_badges": _get_derived_badges(conn, row["asset_id"]),
                    }
                )
        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                raise RuntimeError(
                    "全文索引尚未建立，请前往「设置」页面点击「重建全文索引」。"
                ) from e
            raise

    like_pattern = f"%{escape_like(query)}%"

    rows = conn.execute(
        f"""
        SELECT
          c.id AS chunk_id, c.asset_id AS asset_id, c.kind AS kind,
          c.relative_path AS relative_path, c.content AS content,
          a.title AS asset_title, a.type AS asset_type
        FROM chunks c
        LEFT JOIN assets a ON a.id = c.asset_id
        WHERE c.content LIKE ? ESCAPE '\\'{tag_and}
        ORDER BY c.id
        LIMIT ?
        """,
        (like_pattern, *tag_params, limit),
    ).fetchall()

    for row in rows:
        if len(results) >= limit:
            break

        if row["chunk_id"] in seen_chunk_ids:
            continue

        seen_chunk_ids.add(row["chunk_id"])
        results.append(
            {
                "chunk_id": row["chunk_id"],
                "asset_id": row["asset_id"],
                "asset_title": row["asset_title"] or row["relative_path"],
                "asset_type": row["asset_type"],
                "kind": row["kind"],
                "relative_path": row["relative_path"],
                "snippet": make_snippet(row["content"], query),
            }
        )

    return results


def search_vector(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 20,
    tag_names: list[str] | None = None,
) -> list[dict]:
    """向量语义搜索：LanceDB 命中后回查资产标题，可按标签过滤（OR）。

    标签过滤发生在 top-K 候选回表之后，过滤后结果可能少于 limit
    （候选集本身有限，属预期行为，不算降级）。
    """
    from app.services import vector_service

    hits = vector_service.search_vectors(query, limit=limit)

    asset_ids = [str(hit["asset_id"]) for hit in hits if hit.get("asset_id")]
    kept_asset_ids = _asset_ids_with_any_tag(conn, asset_ids, tag_names)

    results = []

    for hit in hits:
        # 标签过滤与 SQL 路径的 EXISTS 语义一致：无资产绑定的命中在有
        # 过滤时一并排除
        if tag_names:
            if not hit.get("asset_id") or str(hit["asset_id"]) not in kept_asset_ids:
                continue

        asset_title = hit["relative_path"]
        asset_type = None

        if hit["asset_id"]:
            asset_row = conn.execute(
                "SELECT title, type FROM assets WHERE id = ?",
                (hit["asset_id"],),
            ).fetchone()

            if asset_row is not None:
                asset_title = asset_row["title"]
                asset_type = asset_row["type"]

        results.append(
            {
                "chunk_id": hit.get("chunk_id"),
                "asset_id": hit["asset_id"],
                "asset_title": asset_title,
                "asset_type": asset_type,
                "kind": hit.get("kind") or "vector",
                "relative_path": hit.get("relative_path"),
                "snippet": make_snippet(hit.get("content") or "", query),
                "distance": hit.get("distance"),
                "highlight_words": [],
                "derived_badges": _get_derived_badges(conn, hit.get("asset_id")),
            }
        )

    return results


RRF_K = 60


def _rrf_fuse(
    fulltext_results: list[dict], vector_results: list[dict], limit: int = 50
) -> list[dict]:
    """RRF 融合全文+向量结果：score = Σ 1/(RRF_K + rank)，同 chunk 去重合并。

    双命中条目保留全文路的片段与高亮词（有字面命中信息），distance 取向量路。
    """
    merged: dict[object, dict] = {}

    def entry_key(item: dict, prefix: str, rank: int):
        chunk_id = item.get("chunk_id")
        return chunk_id if chunk_id else f"{prefix}-{rank}"

    for rank, item in enumerate(fulltext_results, start=1):
        key = entry_key(item, "fulltext", rank)
        entry = merged.get(key)

        if entry is None:
            entry = {**item, "sources": []}
            merged[key] = entry

        entry["rrf_score"] = entry.get("rrf_score", 0.0) + 1.0 / (RRF_K + rank)

        if "fulltext" not in entry["sources"]:
            entry["sources"].append("fulltext")

    for rank, item in enumerate(vector_results, start=1):
        key = entry_key(item, "vector", rank)
        entry = merged.get(key)

        if entry is None:
            entry = {**item, "sources": []}
            merged[key] = entry
        elif item.get("distance") is not None:
            entry["distance"] = item["distance"]

        entry["rrf_score"] = entry.get("rrf_score", 0.0) + 1.0 / (RRF_K + rank)

        if "vector" not in entry["sources"]:
            entry["sources"].append("vector")

    ranked = sorted(
        merged.values(), key=lambda e: e["rrf_score"], reverse=True
    )
    return ranked[:limit]


def search_hybrid(
    conn,
    query: str,
    limit: int = 50,
    tag_names: list[str] | None = None,
) -> tuple[list[dict], str | None]:
    """综合搜索：全文 + 向量 RRF 融合（m14），可按标签过滤（m15）。

    单路不可用（索引缺失 / Embedding 未启用或调用失败）时降级为另一路，
    返回 (结果, 降级原因)；两路都参与时原因为 None。
    """
    candidate_limit = max(limit, 50)
    fulltext_results: list[dict] = []
    vector_results: list[dict] = []
    reasons: list[str] = []

    try:
        fulltext_results = search_fulltext(
            conn, query, limit=candidate_limit, tag_names=tag_names
        )
    except RuntimeError as exc:
        reasons.append(f"全文搜索未参与本次融合：{exc}")

    try:
        vector_results = search_vector(
            conn, query, limit=candidate_limit, tag_names=tag_names
        )
    except Exception as exc:
        reasons.append(f"向量搜索未参与本次融合：{exc}")

    results = _rrf_fuse(fulltext_results, vector_results, limit=limit)
    return results, "；".join(reasons) if reasons else None


def search(
    query: str,
    mode: str,
    limit: int = 50,
    tag_names: list[str] | None = None,
) -> list[dict]:
    """统一搜索入口。mode: filename / fulltext / vector / hybrid。"""
    query = query.strip()

    if not query:
        return []

    conn = get_conn(get_db_path())

    try:
        if mode == "filename":
            return search_filename(conn, query, limit=limit, tag_names=tag_names)

        if mode == "vector":
            return search_vector(conn, query, limit=limit, tag_names=tag_names)

        if mode == "hybrid":
            results, _ = search_hybrid(
                conn, query, limit=limit, tag_names=tag_names
            )
            return results

        return search_fulltext(conn, query, limit=limit, tag_names=tag_names)
    finally:
        conn.close()
