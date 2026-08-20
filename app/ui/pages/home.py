"""首页：打开知识库 + 最近打开 + 运行状态 + 里程碑进度。"""

from __future__ import annotations

import os
from pathlib import Path

from nicegui import run, ui

from app import __version__
from app.config import get_config
from app.services import recent_library_service
from app.services.library_service import get_library_status, open_library
from app.ui.layout import page_frame
from app.utils import notify_error

MILESTONES = [
    ("M0", "项目骨架", True),
    ("M1", "知识库与扫描", True),
    ("M2", "派生文件识别", True),
    ("M3", "转录任务", True),
    ("M4", "全文搜索", True),
    ("M5", "向量搜索", True),
    ("M6", "AI 总结", True),
    ("M7", "设置与任务中心", True),
    ("M8", "体验优化", True),
]


@ui.page("/")
def home_page() -> None:
    cfg = get_config()
    recents = recent_library_service.get_recent_libraries()
    latest_recent = recents[0]["path"] if recents else ""

    with page_frame("首页", active_nav="/"):
        ui.label("本地知识管理中心").classes("text-2xl font-bold")
        ui.label("管理播客、视频、文档，配套转录 / 总结 / 三层搜索。").classes(
            "text-gray-600"
        )

        # 打开知识库
        with ui.card().classes("w-full"):
            ui.label("打开知识库").classes("font-semibold")
            ui.label("输入一个本地目录，应用会在该目录下创建 .knowledge 文件夹。").classes(
                "text-sm text-gray-600"
            )

            path_input = ui.input(
                label="知识库目录",
                placeholder="例如：D:/Knowledge",
                value=latest_recent,
            ).classes("w-full mt-2")

            status_label = ui.label("当前未打开知识库").classes(
                "text-sm text-gray-600 mt-2"
            )

            def refresh_status():
                status = get_library_status()
                if status.get("opened"):
                    status_label.text = f"当前知识库：{status['library_root']}"
                else:
                    status_label.text = "当前未打开知识库"

            async def do_open(raw_path: str):
                raw_path = (raw_path or "").strip().strip('"').strip("'")
                if not raw_path:
                    ui.notify("请输入知识库目录路径", type="warning")
                    return

                try:
                    target = Path(raw_path).expanduser().resolve()
                except Exception:
                    ui.notify(f"路径无法解析：{raw_path}", type="negative")
                    return

                if not target.exists():
                    ui.notify(f"目录不存在：{target}", type="negative")
                    return
                if not target.is_dir():
                    ui.notify(f"路径不是目录：{target}", type="negative")
                    return
                if not os.access(target, os.W_OK):
                    ui.notify(f"目录不可写：{target}", type="negative")
                    return
                if ".knowledge" in target.parts:
                    ui.notify(
                        "不能选择 .knowledge 目录内的子目录作为知识库",
                        type="negative",
                    )
                    return

                try:
                    result = await run.io_bound(open_library, str(target))
                    ui.notify(f"已打开：{result['library_root']}", type="positive")
                    refresh_status()
                except Exception as exc:
                    notify_error(exc)

            def make_open_handler(path_str: str):
                async def handler():
                    await do_open(path_str)

                return handler

            with ui.row().classes("mt-3 gap-3"):
                ui.button("打开知识库", icon="folder_open", color="primary", on_click=lambda: do_open(path_input.value))
                ui.link("进入资产列表 →", "/assets").classes(
                    "flex items-center text-blue-600"
                )

            refresh_status()

        # 最近打开
        if recents:
            with ui.card().classes("w-full"):
                ui.label("最近打开").classes("font-semibold")
                ui.label("点击可快速切换知识库。").classes("text-sm text-gray-600")
                for item in recents[:5]:
                    with ui.row().classes("items-center gap-2 w-full"):
                        ui.label(item["path"]).classes(
                            "flex-1 truncate text-sm"
                        ).tooltip(item["path"])
                        ui.button(
                            "打开",
                            icon="folder_open",
                            on_click=make_open_handler(item["path"]),
                        ).props("dense size=sm")

        # 运行状态
        with ui.card().classes("w-full"):
            ui.label("运行状态").classes("font-semibold")
            with ui.grid(columns=2).classes("gap-2 w-full"):
                ui.label("版本").classes("text-gray-600")
                ui.label(f"v{__version__}")
                ui.label("监听地址").classes("text-gray-600")
                ui.label(f"http://{cfg.host}:{cfg.port}")
                ui.label("日志级别").classes("text-gray-600")
                ui.label(cfg.log_level)

        # 里程碑
        with ui.card().classes("w-full"):
            ui.label("里程碑").classes("font-semibold")
            for tag, name, done in MILESTONES:
                icon = "✅" if done else "⬜"
                ui.label(f"{icon} {tag} {name}").classes(
                    "text-sm" + (" line-through text-gray-600" if done else "")
                )
