"""全文索引服务：分块写入 chunks 表并重建 FTS5。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from loguru import logger

from app.database import get_conn
from app.state import get_db_path
from app.utils import read_text_for_index


CHUNK_MAX_CHARS = 800

INDEX_ARTIFACT_KINDS = ("transcript", "summary", "note", "parsed")


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def chunk_text(text: str, max_chars: int = CHUNK_MAX_CHARS) -> list[str]:
    """简单分块：优先按段落聚合，段落过长时按字符切。"""
    text = text.strip()

    if not text:
        return []

    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 1 <= max_chars:
            current = f"{current}\n{paragraph}" if current else paragraph
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            start = 0
            while start < len(paragraph):
                end = min(start + max_chars, len(paragraph))
                chunks.append(paragraph[start:end])
                start = end

    if current:
        chunks.append(current)

    return chunks


def insert_chunks(
    conn,
    *,
    asset_id: str,
    artifact_id: str | None,
    kind: str,
    relative_path: str,
    text: str,
) -> int:
    """将一段文本分块后写入 chunks 表。"""
    chunks = chunk_text(text)

    if not chunks:
        return 0

    now = utcnow_iso()

    for index, chunk in enumerate(chunks):
        conn.execute(
            """
            INSERT INTO chunks (
              id, asset_id, artifact_id, kind, relative_path,
              chunk_index, content, content_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                asset_id,
                artifact_id,
                kind,
                relative_path,
                index,
                chunk,
                None,
                now,
            ),
        )

    return len(chunks)


def rebuild_fulltext_index() -> dict:
    """重建全文索引：清空 chunks → 索引派生文件 → 索引文档资产 → 重建 FTS5。"""
    db_path = get_db_path()
    conn = get_conn(db_path)

    stats = {"sources": 0, "chunks": 0}

    try:
        conn.execute("DELETE FROM chunks")

        # 索引派生文件：transcript / summary / note / parsed
        artifact_rows = conn.execute(
            """
            SELECT id, asset_id, kind, relative_path, absolute_path
            FROM artifacts
            WHERE status = 'active' AND kind IN (?, ?, ?, ?)
            """,
            INDEX_ARTIFACT_KINDS,
        ).fetchall()

        for row in artifact_rows:
            try:
                text = read_text_for_index(row["absolute_path"])
            except Exception:
                continue

            if not text.strip():
                continue

            count = insert_chunks(
                conn,
                asset_id=row["asset_id"],
                artifact_id=row["id"],
                kind=row["kind"],
                relative_path=row["relative_path"],
                text=text,
            )

            if count > 0:
                stats["sources"] += 1
                stats["chunks"] += count

        # 索引可直接读取的文档资产：.md / .txt
        document_rows = conn.execute(
            """
            SELECT id, relative_path, absolute_path
            FROM assets
            WHERE type = 'document'
              AND parse_status = 'not_required'
              AND (lower(relative_path) LIKE '%.md' OR lower(relative_path) LIKE '%.txt')
            """
        ).fetchall()

        for row in document_rows:
            try:
                text = read_text_for_index(row["absolute_path"])
            except Exception:
                continue

            if not text.strip():
                continue

            count = insert_chunks(
                conn,
                asset_id=row["id"],
                artifact_id=None,
                kind="document",
                relative_path=row["relative_path"],
                text=text,
            )

            if count > 0:
                stats["sources"] += 1
                stats["chunks"] += count

        # 重建 FTS5。FTS5 对中文分词有限，搜索服务同时使用 LIKE 兜底。
        try:
            conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('rebuild')")
        except Exception as exc:
            logger.warning("FTS5 重建失败（不影响 LIKE 搜索）：{}", exc)

        conn.commit()
    finally:
        conn.close()

    logger.info("全文索引重建完成：{} 来源 / {} 片段", stats["sources"], stats["chunks"])
    return stats
