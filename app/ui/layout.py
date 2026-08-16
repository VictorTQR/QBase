"""共享页面框架：顶部导航 + 内容区。

所有页面共用同一套顶部栏（品牌 QBase + 导航高亮），保证视觉一致。
"""

from __future__ import annotations

from contextlib import contextmanager

from nicegui import ui

from app.state import state

# (path, label, key) — 导航项，key 用于高亮，path 用于链接
NAV_ITEMS = [
    ("/", "首页", "home"),
    ("/assets", "资产", "assets"),
    ("/search", "搜索", "search"),
    ("/tasks", "任务", "tasks"),
    ("/settings", "设置", "settings"),
]

# path -> key 映射，供 page_frame 传入的路径型 active_nav 归一化
_PATH_TO_KEY = {path: key for path, _label, key in NAV_ITEMS}


def _render_top_bar(active_key: str) -> None:
    """渲染统一的顶部导航栏（品牌 + 导航链接）。"""
    with ui.header().classes("items-center justify-between px-6 py-3 bg-gray-800 text-white"):
        ui.label("QBase").classes("text-lg font-bold")
        with ui.row().classes("gap-4"):
            for _path, label, key in NAV_ITEMS:
                if key == active_key:
                    ui.link(label, _path).classes(
                        "text-white font-semibold no-underline bg-white/20 px-2 py-0.5 rounded"
                    )
                else:
                    ui.link(label, _path).classes(
                        "text-white/80 hover:text-white no-underline"
                    )


def _render_title_row(title: str) -> None:
    """渲染标题行（页面标题 + 当前知识库路径徽章）。"""
    with ui.row().classes("w-full max-w-5xl mx-auto px-6 py-3 items-center gap-3"):
        ui.label(title).classes("text-2xl font-bold")
        if state.library_root:
            ui.badge(str(state.library_root), color="grey-4").classes("text-xs")
        else:
            ui.badge("未打开知识库", color="orange").classes("text-xs")


@contextmanager
def page_frame(title: str, active_nav: str = ""):
    """所有页面共用的布局骨架（首页/任务/设置）。

    active_nav: 可为导航路径（如 "/assets"）或 key（如 "assets"），用于高亮。
    """
    ui.page_title(f"{title} - QBase")

    # active_nav 归一化为 key
    active_key = _PATH_TO_KEY.get(active_nav, active_nav)

    _render_top_bar(active_key)
    _render_title_row(title)

    with ui.column().classes("w-full max-w-5xl mx-auto p-6 gap-4 min-h-screen"):
        yield
    with ui.column().classes("w-full items-center py-2"):
        ui.label("QBase · 本地知识管理中心").classes("text-xs text-gray-400")


def page_header(title: str, active_nav: str = ""):
    """页面顶部：统一导航栏 + 标题行（当前项高亮）。

    与 page_frame 共用同一套顶部栏样式，保证视觉一致。
    active_nav: "home" / "assets" / "search" / "tasks" / "settings"
    """
    ui.page_title(f"{title} - QBase")
    _render_top_bar(active_nav)
    _render_title_row(title)


def breadcrumb(items: list[tuple[str, str | None]]):
    """面包屑导航。

    items: [(显示文字, 链接路径), ...]，最后一项路径为 None 表示当前页。
    示例：breadcrumb([("首页", "/"), ("资产列表", "/assets"), ("某文件", None)])
    """
    with ui.row().classes("px-6 py-1 items-center gap-1 text-sm text-gray-500"):
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
