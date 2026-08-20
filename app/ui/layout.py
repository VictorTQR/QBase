"""共享页面框架：顶部导航 + 标题行 + 内容区 + 页脚。

所有页面共用同一套顶部栏（品牌 QBase + 导航高亮）与统一内容容器，
保证视觉一致。样式类串与颜色统一引用 app.ui.tokens（单一来源）。
"""

from __future__ import annotations

from contextlib import contextmanager

from nicegui import ui

from app.state import state
from app.ui.tokens import C, CLS

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
    with ui.header().classes(CLS["top_bar"]):
        ui.label("QBase").classes("text-lg font-bold")
        with ui.row().classes("gap-4"):
            for _path, label, key in NAV_ITEMS:
                if key == active_key:
                    ui.link(label, _path).classes(CLS["nav_on"])
                else:
                    ui.link(label, _path).classes(CLS["nav_off"])


def _render_title_row(title: str) -> None:
    """渲染标题行（页面标题 + 当前知识库路径徽章）。"""
    with ui.row().classes(CLS["title_row"]):
        ui.label(title).classes(CLS["title"])
        if state.library_root:
            ui.badge(str(state.library_root), color=C.NEUTRAL_4).classes("text-xs")
        else:
            ui.badge("未打开知识库", color=C.WARNING).classes("text-xs")


def _render_footer() -> None:
    """渲染统一页脚。"""
    with ui.column().classes(CLS["footer"]):
        ui.label("QBase · 本地知识管理中心").classes(CLS["footer_text"])


def breadcrumb(items: list[tuple[str, str | None]]):
    """面包屑导航。

    items: [(显示文字, 链接路径), ...]，最后一项路径为 None 表示当前页。
    示例：breadcrumb([("首页", "/"), ("资产列表", "/assets"), ("某文件", None)])
    """
    with ui.row().classes(CLS["breadcrumb"]):
        for i, (text, path) in enumerate(items):
            if i > 0:
                ui.label("/").classes(CLS["breadcrumb_sep"])
            if path is not None:
                ui.link(text, path).classes(CLS["link"])
            else:
                ui.label(text).classes(CLS["breadcrumb_current"]).props(
                    "style='max-width: 200px'"
                )


def require_library() -> bool:
    """检查是否已打开知识库；未打开时显示提示并返回 False。"""
    if state.library_root is None:
        ui.label("未打开知识库").classes("text-xl mt-6")
        ui.link("去打开知识库", "/").classes(CLS["link"] + " mt-2")
        return False
    return True


@contextmanager
def page_frame(title: str, active_nav: str = ""):
    """所有页面共用的布局骨架（首页 / 任务 / 设置 / 搜索 / 资产 / 详情）。

    active_nav: 可为导航路径（如 "/assets"）或 key（如 "assets"），用于高亮。
    """
    ui.page_title(f"{title} - QBase")

    # active_nav 归一化为 key
    active_key = _PATH_TO_KEY.get(active_nav, active_nav)

    _render_top_bar(active_key)
    _render_title_row(title)

    with ui.column().classes(CLS["content"]):
        yield
    _render_footer()
