"""任务仓库：tasks 表 CRUD。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_task_id() -> str:
    return str(uuid.uuid4())


def create_task(
    conn,
    *,
    asset_id: str | None,
    task_type: str,
    params: dict | None = None,
    command: list | None = None,
    output_path: str | None = None,
) -> str:
    """创建任务。"""
    task_id = make_task_id()
    now = utcnow_iso()

    conn.execute(
        """
        INSERT INTO tasks (
          id,
          asset_id,
          type,
          status,
          command,
          params_json,
          output_path,
          error,
          pid,
          created_at,
          started_at,
          finished_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            asset_id,
            task_type,
            "pending",
            json.dumps(command, ensure_ascii=False) if command else None,
            json.dumps(params, ensure_ascii=False) if params else None,
            output_path,
            None,
            None,
            now,
            None,
            None,
        ),
    )

    return task_id


def update_task(conn, task_id: str, **fields) -> None:
    """更新任务字段。"""
    allowed_fields = {
        "status",
        "command",
        "params_json",
        "output_path",
        "error",
        "pid",
        "started_at",
        "finished_at",
    }

    sets = []
    args = []

    for key, value in fields.items():
        if key in allowed_fields:
            sets.append(f"{key} = ?")
            args.append(value)

    if not sets:
        return

    args.append(task_id)

    conn.execute(
        f"""
        UPDATE tasks
        SET {", ".join(sets)}
        WHERE id = ?
        """,
        args,
    )


def get_task(conn, task_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT
          id,
          asset_id,
          type,
          status,
          command,
          params_json,
          output_path,
          error,
          pid,
          created_at,
          started_at,
          finished_at
        FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    ).fetchone()

    if row is None:
        return None

    return dict(row)


def list_tasks(conn, limit: int = 200) -> list[dict]:
    """任务中心列表。"""
    rows = conn.execute(
        """
        SELECT
          t.id,
          t.asset_id,
          t.type,
          t.status,
          t.command,
          t.params_json,
          t.output_path,
          t.error,
          t.created_at,
          t.started_at,
          t.finished_at,
          a.title AS asset_title
        FROM tasks t
        LEFT JOIN assets a ON t.asset_id = a.id
        ORDER BY t.created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    return [dict(row) for row in rows]


def count_running_tasks(
    conn,
    asset_id: str | None = None,
    task_type: str | None = None,
) -> int:
    """统计正在运行或等待中的任务。"""
    sql = """
        SELECT COUNT(*) AS cnt
        FROM tasks
        WHERE status IN ('pending', 'running')
    """

    args = []

    if asset_id is not None:
        sql += " AND asset_id = ?"
        args.append(asset_id)

    if task_type is not None:
        sql += " AND type = ?"
        args.append(task_type)

    row = conn.execute(sql, args).fetchone()

    return row["cnt"] if row else 0
