"""artifacts 表数据访问。"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_artifact_id(relative_path: str) -> str:
    """使用相对路径生成稳定 Artifact ID。"""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, relative_path))


def upsert_artifact(conn: sqlite3.Connection, artifact: dict) -> str:
    """新增或更新 artifact，返回 ID。"""
    now = utcnow_iso()

    existing = conn.execute(
        "SELECT id FROM artifacts WHERE relative_path = ?",
        (artifact["relative_path"],),
    ).fetchone()

    if existing:
        conn.execute(
            """
            UPDATE artifacts
            SET
              asset_id = ?,
              kind = ?,
              absolute_path = ?,
              mtime = ?,
              source = ?,
              generator = ?,
              model = ?,
              status = ?,
              updated_at = ?
            WHERE relative_path = ?
            """,
            (
                artifact["asset_id"],
                artifact["kind"],
                artifact["absolute_path"],
                artifact["mtime"],
                artifact.get("source"),
                artifact.get("generator"),
                artifact.get("model"),
                artifact.get("status", "active"),
                now,
                artifact["relative_path"],
            ),
        )
        return str(existing["id"])

    artifact_id = make_artifact_id(artifact["relative_path"])

    conn.execute(
        """
        INSERT INTO artifacts (
          id, asset_id, kind, relative_path, absolute_path, file_hash,
          mtime, source, generator, model, status, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            artifact_id,
            artifact["asset_id"],
            artifact["kind"],
            artifact["relative_path"],
            artifact["absolute_path"],
            None,
            artifact["mtime"],
            artifact.get("source"),
            artifact.get("generator"),
            artifact.get("model"),
            artifact.get("status", "active"),
            now,
            now,
        ),
    )

    return artifact_id


def list_artifacts_by_asset(conn: sqlite3.Connection, asset_id: str) -> list[dict]:
    """获取某个资产的所有派生文件。"""
    rows = conn.execute(
        """
        SELECT id, asset_id, kind, relative_path, absolute_path, mtime,
               source, generator, model, status, created_at, updated_at
        FROM artifacts
        WHERE asset_id = ?
        ORDER BY kind, relative_path
        """,
        (asset_id,),
    ).fetchall()

    return [dict(row) for row in rows]


def delete_missing_artifacts(conn: sqlite3.Connection, seen_paths: set[str]) -> int:
    """删除已不存在文件的 artifact 记录，返回删除数量。"""
    rows = conn.execute("SELECT id, relative_path FROM artifacts").fetchall()

    missing_ids = [
        row["id"] for row in rows if row["relative_path"] not in seen_paths
    ]

    if missing_ids:
        conn.executemany(
            "DELETE FROM artifacts WHERE id = ?",
            [(artifact_id,) for artifact_id in missing_ids],
        )

    return len(missing_ids)
