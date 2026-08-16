"""任务中心页：任务列表、状态徽章、错误摘要、自动刷新。"""

from __future__ import annotations

from nicegui import ui

from app.database import get_conn
from app.repositories.task_repository import list_tasks
from app.state import get_db_path, state
from app.ui.layout import page_frame

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


@ui.page("/tasks")
def tasks_page() -> None:
    with page_frame("任务中心"):
        if state.library_root is None:
            ui.label("未打开知识库").classes("text-xl")
            ui.link("去打开知识库", "/").classes("text-blue-600")
            return

        ui.label("任务中心").classes("text-2xl font-bold")
        ui.label(str(state.library_root)).classes("text-sm text-gray-500")

        with ui.row().classes("items-center gap-3 mt-3"):
            ui.button("刷新", on_click=lambda: load_tasks())
            ui.link("资产列表", "/assets").classes("text-blue-600")

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
                    ui.label("类型").classes("w-28")
                    ui.label("资产").classes("w-56")
                    ui.label("状态").classes("w-24")
                    ui.label("输出 / 错误").classes("flex-1")

                for task in tasks:
                    with ui.row().classes(
                        "w-full border-b p-2 items-center hover:bg-gray-50 rounded"
                    ):
                        ui.label(task["created_at"] or "").classes("w-48 truncate")

                        ui.label(task["type"]).classes("w-28")

                        if task["asset_id"]:
                            ui.link(
                                task["asset_title"] or "-",
                                f"/assets/{task['asset_id']}",
                            ).classes("w-56 truncate text-blue-600")
                        else:
                            ui.label("-").classes("w-56")

                        status = task["status"]

                        ui.badge(
                            STATUS_LABELS.get(status, status),
                            color=STATUS_COLORS.get(status, "grey"),
                        ).classes("w-24")

                        if status == "failed":
                            message = task["error"] or "失败"
                        else:
                            message = task["output_path"] or ""

                        ui.label(message).classes(
                            "flex-1 truncate"
                        ).tooltip(message)

        load_tasks()

        # 每 5 秒自动刷新一次任务状态
        ui.timer(5.0, load_tasks)
