"""任务中心页：任务列表、详情对话框、失败重试、自动刷新。"""

from __future__ import annotations

from nicegui import run, ui

from app.database import get_conn
from app.repositories.task_repository import get_task, list_tasks
from app.state import get_db_path, state
from app.ui.layout import page_frame
from app.utils import notify_error

STATUS_COLORS = {
    "pending": "grey",
    "running": "blue",
    "success": "green",
    "failed": "red",
    "cancelled": "orange",
}

STATUS_LABELS = {
    "pending": "等待中",
    "running": "运行中",
    "success": "成功",
    "failed": "失败",
    "cancelled": "已取消",
}

TYPE_LABELS = {
    "transcription": "转录",
    "summarization": "总结",
}


@ui.page("/tasks")
def tasks_page() -> None:
    with page_frame("任务中心", active_nav="/tasks"):
        if state.library_root is None:
            ui.label("未打开知识库").classes("text-xl")
            ui.link("去打开知识库", "/").classes("text-blue-600")
            return

        ui.label("任务中心").classes("text-2xl font-bold")
        ui.label(str(state.library_root)).classes("text-sm text-gray-500")

        with ui.row().classes("items-center gap-3 mt-3"):
            ui.button("刷新", icon="refresh", on_click=lambda: load_tasks())
            ui.label("每 5 秒自动刷新").classes("text-xs text-gray-500")

        container = ui.column().classes("w-full mt-4")

        def load_tasks():
            container.clear()

            conn = get_conn(get_db_path())

            try:
                tasks = list_tasks(conn, limit=200)
            finally:
                conn.close()

            with container:
                if not tasks:
                    ui.label("暂无任务。").classes("text-gray-600")
                    return

                with ui.row().classes(
                    "w-full bg-gray-100 p-2 font-semibold rounded"
                ):
                    ui.label("创建时间").classes("w-48")
                    ui.label("类型").classes("w-20")
                    ui.label("资产").classes("w-48")
                    ui.label("状态").classes("w-20")
                    ui.label("输出 / 错误").classes("flex-1")
                    ui.label("操作").classes("w-28")

                for task in tasks:
                    with ui.row().classes(
                        "w-full border-b p-2 items-center hover:bg-gray-50 rounded"
                    ):
                        ui.label(task["created_at"] or "").classes(
                            "w-48 truncate"
                        ).tooltip(task["created_at"] or "")

                        ui.label(
                            TYPE_LABELS.get(task["type"], task["type"])
                        ).classes("w-20")

                        if task["asset_id"]:
                            ui.link(
                                task["asset_title"] or "-",
                                f"/assets/{task['asset_id']}",
                            ).classes("w-48 truncate text-blue-600").tooltip(
                                task["asset_title"] or ""
                            )
                        else:
                            ui.label("-").classes("w-48")

                        status = task["status"]

                        ui.badge(
                            STATUS_LABELS.get(status, status),
                            color=STATUS_COLORS.get(status, "grey"),
                        ).classes("w-20")

                        if status == "failed":
                            message = task["error"] or "失败"
                        else:
                            message = task["output_path"] or ""

                        ui.label(message).classes(
                            "flex-1 truncate"
                        ).tooltip(message)

                        with ui.row().classes("w-28 gap-1"):
                            ui.button(
                                "详情",
                                on_click=make_detail_handler(task["id"]),
                            ).props("dense size=sm flat")

                            if status == "failed":
                                ui.button(
                                    "重试",
                                    on_click=make_retry_handler(task),
                                ).props("dense size=sm flat color=orange")

        def make_detail_handler(task_id: str):
            async def handler():
                conn = get_conn(get_db_path())

                try:
                    task = get_task(conn, task_id)
                finally:
                    conn.close()

                if task is None:
                    ui.notify("任务不存在", type="negative")
                    return

                with ui.dialog() as dialog, ui.card().classes(
                    "w-[640px] max-h-[80vh] overflow-y-auto"
                ):
                    ui.label(f"任务详情：{task_id[:8]}").classes(
                        "text-lg font-semibold"
                    )
                    ui.separator()

                    ui.label(f"类型：{TYPE_LABELS.get(task['type'], task['type'])}")
                    ui.label(f"状态：{STATUS_LABELS.get(task['status'], task['status'])}")
                    ui.label(f"创建时间：{task['created_at']}")
                    ui.label(f"开始时间：{task['started_at'] or '-'}")
                    ui.label(f"结束时间：{task['finished_at'] or '-'}")
                    ui.label(f"输出路径：{task['output_path'] or '-'}")

                    if task["command"]:
                        ui.label("命令：").classes("font-semibold mt-2")
                        ui.code(task["command"]).classes("w-full")

                    if task["params_json"]:
                        ui.label("参数：").classes("font-semibold mt-2")
                        ui.code(task["params_json"], language="json").classes(
                            "w-full"
                        )

                    if task["error"]:
                        ui.label("错误信息：").classes(
                            "font-semibold mt-2 text-red-600"
                        )
                        ui.code(task["error"]).classes(
                            "w-full max-h-48 overflow-y-auto"
                        )

                    with ui.row().classes("mt-3"):
                        ui.button("关闭", on_click=dialog.close)

                dialog.open()

            return handler

        def make_retry_handler(task: dict):
            async def handler():
                try:
                    if task["type"] == "transcription" and task["asset_id"]:
                        from app.services.transcription_service import (
                            start_transcription,
                        )

                        new_task_id = await run.io_bound(
                            start_transcription,
                            task["asset_id"],
                        )

                        ui.notify(
                            f"已创建新转录任务：{new_task_id[:8]}",
                            type="positive",
                        )

                    elif task["type"] == "summarization" and task["asset_id"]:
                        from app.services.summarization_service import (
                            start_summarization,
                        )

                        new_task_id = await run.io_bound(
                            start_summarization,
                            task["asset_id"],
                        )

                        ui.notify(
                            f"已创建新总结任务：{new_task_id[:8]}",
                            type="positive",
                        )

                    else:
                        ui.notify("该任务类型暂不支持重试", type="warning")
                        return

                    load_tasks()

                except Exception as exc:
                    notify_error(exc)

            return handler

        load_tasks()

        # 每 5 秒自动刷新一次任务状态
        ui.timer(5.0, load_tasks)
