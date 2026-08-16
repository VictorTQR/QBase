"""共享页面框架：顶部导航 + 内容区。"""

from __future__ import annotations

from contextlib import contextmanager

from nicegui import ui

from app.state import state

# (path, label) — 供 page_frame 使用
NAV_ITEMS = [
    ("/", "首页"),
    ("/assets", "资产"),
    ("/search", "搜索"),
    ("/tasks", "任务"),
    ("/settings", "设置"),
]

# (label, path, key) — 供 page_header 使用
NAV_ITEMS_KEYED = [
    ("首页", "/", "home"),
    ("资产", "/assets", "assets"),
    ("搜索", "/search", "search"),
    ("任务", "/tasks", "tasks"),
    ("设置", "/settings", "settings"),
]


@contextmanager
def page_frame(title: str, active_nav: str = ""):
    """所有页面共用的布局骨架。active_nav 传路径（如 "/assets"）用于高亮。"""
    ui.page_title(f"{title} - QBase")
    with ui.header().classes("items-center justify-between px-6 py-3"):
        ui.label("QBase").classes("text-lg font-bold")
        with ui.row().classes("gap-4"):
            for path, label in NAV_ITEMS:
                if path == active_nav:
                    ui.link(label, path).classes(
                        "text-white font-semibold no-underline bg-white/20 px-2 py-0.5 rounded"
                    )
                else:
                    ui.link(label, path).classes(
                        "text-white/80 hover:text-white no-underline"
                    )
    with ui.column().classes("w-full max-w-5xl mx-auto p-6 gap-4 min-h-screen"):
        yield
    with ui.column().classes("w-full items-center py-2"):
        ui.label("QBase · 本地知识管理中心").classes("text-xs text-gray-400")


def page_header(title: str, active_nav: str = ""):
    """页面顶部：标题 + 导航栏（当前项高亮）。

    active_nav: "home" / "assets" / "search" / "tasks" / "settings"
    """
    with ui.header().classes(
        "items-center justify-between px-4 py-2 bg-gray-800 text-white"
    ):
        ui.label("Local Knowledge Hub").classes("font-bold text-lg")
        with ui.row().classes("gap-4 items-center"):
            for label, path, key in NAV_ITEMS_KEYED:
                if key == active_nav:
                    ui.link(label, path).classes(
                        "bg-white/20 text-white font-semibold px-2 py-0.5 rounded"
                    )
                else:
                    ui.link(label, path).classes(
                        "text-white/80 hover:text-white px-2 py-0.5 rounded"
                    )
    with ui.row().classes("w-full px-4 py-3 items-center gap-3"):
        ui.label(title).classes("text-2xl font-bold")
        if state.library_root:
            ui.badge(str(state.library_root), color="grey-4").classes("text-xs")
        else:
            ui.badge("未打开知识库", color="orange").classes("text-xs")


def breadcrumb(items: list[tuple[str, str | None]]):
    """面包屑导航。

    items: [(显示文字, 链接路径), ...]，最后一项路径为 None 表示当前页。
    示例：breadcrumb([("首页", "/"), ("资产列表", "/assets"), ("某文件", None)])
    """
    with ui.row().classes("px-4 py-1 items-center gap-1 text-sm text-gray-500"):
        for i, (text, path) in enumerate(items):
            if i > 0:
                ui.label("/").classes("text-gray-400")
            if path is not None:
                ui.link(text, path).classes("text-blue-600 hover:underline")
            else:
                ui.label(text).classes("text-gray-700 font-medium truncate").props(
                    "style='max-width: 200px'"
                )


def require_library() -> bool:
    """检查是否已打开知识库；未打开时显示提示并返回 False。"""
    if state.library_root is None:
        ui.label("未打开知识库").classes("text-xl mt-6")
        ui.link("去打开知识库", "/").classes("text-blue-600 mt-2")
        return False
    return True
