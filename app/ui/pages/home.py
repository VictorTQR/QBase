"""首页：M0 占位，显示应用状态与里程碑进度。"""

from __future__ import annotations

from nicegui import ui

from app import __version__
from app.config import get_config
from app.ui.layout import page_frame

MILESTONES = [
    ("M0", "项目骨架", True),
    ("M1", "知识库与扫描", False),
    ("M2", "派生文件识别", False),
    ("M3", "转录任务", False),
    ("M4", "全文搜索", False),
    ("M5", "向量搜索", False),
    ("M6", "AI 总结", False),
    ("M7", "设置与任务中心", False),
    ("M8", "体验优化", False),
]


@ui.page("/")
def home_page() -> None:
    cfg = get_config()
    with page_frame("首页"):
        ui.label("本地知识管理中心").classes("text-2xl font-bold")
        ui.label("管理播客、视频、文档，配套转录 / 总结 / 三层搜索。").classes("text-gray-500")

        with ui.card().classes("w-full"):
            ui.label("运行状态").classes("font-semibold")
            with ui.grid(columns=2).classes("gap-2 w-full"):
                ui.label("版本").classes("text-gray-500")
                ui.label(f"v{__version__}")
                ui.label("监听地址").classes("text-gray-500")
                ui.label(f"http://{cfg.host}:{cfg.port}")
                ui.label("日志级别").classes("text-gray-500")
                ui.label(cfg.log_level)

        with ui.card().classes("w-full"):
            ui.label("里程碑").classes("font-semibold")
            for tag, name, done in MILESTONES:
                with ui.row().classes("items-center gap-2"):
                    icon = "✅" if done else "⬜"
                    ui.label(f"{icon} {tag} {name}").classes(
                        "text-sm" + (" line-through text-gray-400" if done else "")
                    )
