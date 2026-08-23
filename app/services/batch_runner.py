"""批量任务消费器（m17）：消费 [task] max_workers 配置，串行/并发执行已建任务。

批量总结与批量打标的编排器只负责「预检 + 建一批 pending 任务」，
实际执行交给本模块起的 worker 线程；单条入口（含任务中心重试）与
重启恢复（open_library）同样经 execute_tasks，_inflight_task_ids
保证同一任务不会被重复起线程。
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from loguru import logger

from app.services import config_service

# 正在被 worker 消费的任务 ID（进程内）；防重启恢复与在跑任务重复执行
_inflight_task_ids: set[str] = set()
_inflight_lock = threading.Lock()


def get_max_workers() -> int:
    """读 [task] max_workers，默认 1；配置异常时回退 1 不阻断批量。"""
    try:
        task_config = config_service.load_config().get("task", {})
        max_workers = int(task_config.get("max_workers", 1))
    except Exception:
        return 1

    return max_workers if max_workers >= 1 else 1


def execute_tasks(task_ids: list[str], run_task: Callable[[str], None]) -> None:
    """起 daemon 线程消费任务：max_workers<=1 串行，否则线程池并发。

    已在消费中的任务自动跳过；run_task 内部需自行处理单任务失败
    （置 failed），不让异常中断整批。
    """
    with _inflight_lock:
        pending_ids = [
            task_id for task_id in task_ids if task_id not in _inflight_task_ids
        ]
        _inflight_task_ids.update(pending_ids)

    if not pending_ids:
        return

    max_workers = get_max_workers()

    def _worker() -> None:
        try:
            if max_workers <= 1:
                for task_id in pending_ids:
                    run_task(task_id)
            else:
                with ThreadPoolExecutor(max_workers=max_workers) as pool:
                    list(pool.map(run_task, pending_ids))
        finally:
            with _inflight_lock:
                for task_id in pending_ids:
                    _inflight_task_ids.discard(task_id)

    threading.Thread(target=_worker, daemon=True).start()
    logger.info(
        "批量消费线程已启动：{} 个任务（max_workers={}）",
        len(pending_ids),
        max_workers,
    )
