"""占位页面：M1+ 实现。"""

from __future__ import annotations

from nicegui import ui

from app.ui.layout import page_frame


def placeholder_page(route: str, title: str, note: str):
    def render() -> None:
        with page_frame(title):
            ui.label(title).classes("text-2xl font-bold")
            ui.label(note).classes("text-gray-500")

    return ui.page(route)(render)


placeholder_page("/assets", "资产", "M1 实现：目录扫描与资产列表")
placeholder_page("/search", "搜索", "M4/M5 实现：全文 + 向量搜索")
placeholder_page("/tasks", "任务", "M7 实现：任务中心")
placeholder_page("/settings", "设置", "M7 实现：配置管理")
