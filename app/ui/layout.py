"""共享页面框架：顶部导航 + 内容区。"""

from __future__ import annotations

from contextlib import contextmanager

from nicegui import ui

NAV_ITEMS = [
    ("/", "首页"),
    ("/assets", "资产"),
    ("/search", "搜索"),
    ("/tasks", "任务"),
    ("/settings", "设置"),
]


@contextmanager
def page_frame(title: str):
    """所有页面共用的布局骨架。"""
    ui.page_title(f"{title} - QBase")
    with ui.header().classes("items-center justify-between px-6 py-3"):
        ui.label("QBase").classes("text-lg font-bold")
        with ui.row().classes("gap-4"):
            for path, label in NAV_ITEMS:
                ui.link(label, path).classes("text-white/80 hover:text-white no-underline")
    with ui.column().classes("w-full max-w-5xl mx-auto p-6 gap-4 min-h-screen"):
        yield
    with ui.column().classes("w-full items-center py-2"):
        ui.label("QBase · 本地知识管理中心").classes("text-xs text-gray-400")
