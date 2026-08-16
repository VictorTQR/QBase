"""向量服务：chunks 向量化 + LanceDB 语义搜索 + embedding 缓存（m5）。

数据来源是 SQLite chunks 表；向量写入 <library_root>/.knowledge/vector/lancedb。
重建向量索引会调用 Embedding API，可能产生费用或额度消耗。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
from loguru import logger

from app.database import get_conn
from app.services.config_service import get_embedding_config
from app.state import get_db_path, state

TABLE_NAME = "chunks"


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cache_key(model: str, text: str, prefix: str = "chunk") -> str:
    """embedding 缓存 key：chunk:model:sha256 / query:model:sha256。"""
    return f"{prefix}:{model}:{sha256_text(text)}"


def vector_dir() -> Path:
    if state.library_root is None:
        raise RuntimeError("未打开知识库")

    return state.library_root / ".knowledge" / "vector" / "lancedb"


def connect_lancedb():
    import lancedb

    path = vector_dir()
    path.mkdir(parents=True, exist_ok=True)

    return lancedb.connect(str(path))


def table_exists(db) -> bool:
    return TABLE_NAME in db.table_names()


def get_cached_vector(conn, key: str) -> list[float] | None:
    row = conn.execute(
        "SELECT vector FROM embedding_cache WHERE content_hash = ?",
        (key,),
    ).fetchone()

    if row is None:
        return None

    raw = row["vector"]

    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")

    try:
        return json.loads(raw)
    except Exception:
        return None


def set_cached_vector(conn, key: str, model: str, vector: list[float]) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO embedding_cache (
          content_hash, model, vector, dimension, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (key, model, json.dumps(vector).encode("utf-8"), len(vector), utcnow_iso()),
    )


def embed_texts(texts: list[str], config: dict) -> list[list[float]]:
    """调用 OpenAI 兼容 /embeddings API，按 batch_size 分批。"""
    if not texts:
        return []

    url = config["base_url"].rstrip("/") + "/embeddings"

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    all_vectors: list[list[float]] = []
    batch_size = max(1, int(config.get("batch_size", 16)))

    with httpx.Client(timeout=config.get("timeout", 120)) as client:
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]

            response = client.post(
                url,
                headers=headers,
                json={"model": config["model"], "input": batch},
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Embedding API 错误：{response.status_code} {response.text[:500]}"
                )

            data = response.json().get("data", [])
            data.sort(key=lambda item: item.get("index", 0))
            vectors = [item["embedding"] for item in data]

            if len(vectors) != len(batch):
                raise RuntimeError("Embedding API 返回数量与请求数量不一致")

            all_vectors.extend(vectors)

    return all_vectors


def embed_query(query: str, config: dict) -> list[float]:
    """对搜索语句生成 embedding，优先命中缓存。"""
    conn = get_conn(get_db_path())

    key = cache_key(config["model"], query, prefix="query")

    try:
        cached = get_cached_vector(conn, key)

        if cached is not None and len(cached) == config["dimension"]:
            return cached

        vector = embed_texts([query], config)[0]

        if len(vector) != config["dimension"]:
            raise ValueError(
                f"Embedding 维度不匹配：配置为 {config['dimension']}，"
                f"实际返回 {len(vector)}"
            )

        set_cached_vector(conn, key, config["model"], vector)
        conn.commit()

        return vector
    finally:
        conn.close()


def rebuild_vector_index() -> dict:
    """重建 LanceDB 向量索引：SQLite chunks → embedding → LanceDB 全量重建。

    embedding 结果写入 embedding_cache，重复内容不再调 API。
    返回 {total_chunks, cache_hits, embedded}。
    """
    config = get_embedding_config()

    if not config["enabled"]:
        raise ValueError("向量搜索未启用，请检查 [embedding] enabled")

    conn = get_conn(get_db_path())

    records: list[dict | None] = []
    pending: list[dict] = []

    stats = {"total_chunks": 0, "cache_hits": 0, "embedded": 0}

    try:
        rows = conn.execute(
            """
            SELECT id, asset_id, artifact_id, kind,
                   relative_path, chunk_index, content
            FROM chunks
            ORDER BY rowid
            """
        ).fetchall()

        now = utcnow_iso()

        for row in rows:
            content = row["content"] or ""

            if not content.strip():
                continue

            key = cache_key(config["model"], content, prefix="chunk")

            record = {
                "id": row["id"],
                "asset_id": row["asset_id"],
                "artifact_id": row["artifact_id"] or "",
                "kind": row["kind"],
                "relative_path": row["relative_path"],
                "chunk_index": row["chunk_index"],
                "content": content,
                "content_hash": sha256_text(content),
                "embedding_model": config["model"],
                "updated_at": now,
            }

            cached_vector = get_cached_vector(conn, key)

            if cached_vector is not None and len(cached_vector) == config["dimension"]:
                record["vector"] = cached_vector
                records.append(record)
                stats["cache_hits"] += 1
                continue

            placeholder_index = len(records)
            records.append(None)

            pending.append(
                {
                    "index": placeholder_index,
                    "content": content,
                    "key": key,
                    "record": record,
                }
            )

        # 批量调用 embedding API。
        batch_size = max(1, config["batch_size"])

        for start in range(0, len(pending), batch_size):
            batch = pending[start : start + batch_size]

            texts = [item["content"] for item in batch]
            vectors = embed_texts(texts, config)

            if len(vectors) != len(batch):
                raise RuntimeError("Embedding API 返回数量异常")

            for item, vector in zip(batch, vectors):
                if len(vector) != config["dimension"]:
                    raise ValueError(
                        f"Embedding 维度不匹配：配置为 {config['dimension']}，"
                        f"实际返回 {len(vector)}"
                    )

                record = item["record"]
                record["vector"] = vector
                records[item["index"]] = record

                set_cached_vector(conn, item["key"], config["model"], vector)
                stats["embedded"] += 1

        conn.commit()
    finally:
        conn.close()

    final_records = [record for record in records if record is not None]
    stats["total_chunks"] = len(final_records)

    db = connect_lancedb()

    if table_exists(db):
        db.drop_table(TABLE_NAME)

    if final_records:
        db.create_table(TABLE_NAME, data=final_records)

    logger.info(
        "向量索引重建完成：总片段 {}，缓存命中 {}，新调用 {}",
        stats["total_chunks"],
        stats["cache_hits"],
        stats["embedded"],
    )

    return stats


def search_vectors(query: str, limit: int = 20) -> list[dict]:
    """LanceDB 向量搜索。"""
    query = query.strip()

    if not query:
        return []

    config = get_embedding_config()

    if not config["enabled"]:
        raise ValueError("向量搜索未启用，请检查 [embedding] enabled")

    db = connect_lancedb()

    if not table_exists(db):
        return []

    table = db.open_table(TABLE_NAME)

    query_vector = embed_query(query, config)

    rows = table.search(query_vector).limit(limit).to_list()

    return [
        {
            "asset_id": row.get("asset_id"),
            "artifact_id": row.get("artifact_id"),
            "kind": row.get("kind"),
            "relative_path": row.get("relative_path"),
            "content": row.get("content"),
            "distance": row.get("_distance"),
        }
        for row in rows
    ]
