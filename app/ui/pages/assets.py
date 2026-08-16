"""资产列表页：扫描 / 刷新、类型过滤、打开文件与所在目录。"""

from __future__ import annotations

from nicegui import run, ui

from app.database import get_conn
from app.repositories.asset_repository import count_assets, list_assets
from app.services.scanner_service import scan_current_library
from app.state import get_db_path, state
from app.ui.layout import page_frame
from app.utils import human_size, human_time, open_file, open_folder

TYPE_FILTERS = [("全部", None), ("音频", "audio"), ("视频", "video"), ("文档", "document")]


@ui.page("/assets")
def assets_page() -> None:
    if state.library_root is None:
        with page_frame("资产"):
            ui.label("未打开知识库").classes("text-xl")
            ui.link("去打开知识库", "/").classes("text-blue-600")
        return

    with page_frame("资产"):
        ui.label("资产列表").classes("text-2xl font-bold")
        ui.label(str(state.library_root)).classes("text-sm text-gray-500")

        with ui.row().classes("items-center gap-3 mt-3"):
            scan_button = ui.button("扫描 / 刷新", icon="refresh")
            type_select = ui.select(
                {key: label for label, key in TYPE_FILTERS},
                value=None,
                label="类型",
            ).props("dense outlined")
            count_label = ui.label("").classes("text-sm text-gray-600")

        list_container = ui.column().classes("w-full mt-4")

        def make_open_handler(fn, path: str):
            async def handler():
                try:
                    await run.io_bound(fn, path)
                except Exception as exc:
                    ui.notify(str(exc), type="negative")

            return handler

        def load_assets():
            list_container.clear()

            conn = get_conn(get_db_path())
            try:
                selected = type_select.value
                total = count_assets(conn, selected)
                assets = list_assets(conn, limit=1000, asset_type=selected)
            finally:
                conn.close()

            count_label.text = f"总计 {total} 个资产，当前显示 {len(assets)} 个"

            with list_container:
                if not assets:
                    ui.label("暂无资产。请点击「扫描 / 刷新」。").classes("text-gray-600")
                    return

                with ui.row().classes("w-full bg-gray-100 p-2 font-semibold rounded"):
                    ui.label("标题").classes("w-56 truncate")
                    ui.label("类型").classes("w-16")
                    ui.label("路径").classes("flex-1")
                    ui.label("大小").classes("w-20 text-right")
                    ui.label("修改时间").classes("w-32")
                    ui.label("操作").classes("w-28")

                for asset in assets:
                    with ui.row().classes(
                        "w-full border-b p-2 items-center hover:bg-gray-50 rounded"
                    ):
                        ui.label(asset["title"]).classes("w-56 truncate").tooltip(
                            asset["title"]
                        )
                        ui.label(asset["type"]).classes("w-16")
                        ui.label(asset["relative_path"]).classes(
                            "flex-1 truncate"
                        ).tooltip(asset["relative_path"])
                        ui.label(human_size(asset["size"])).classes("w-20 text-right")
                        ui.label(human_time(asset["mtime"])).classes("w-32")

                        with ui.row().classes("w-28 gap-1"):
                            ui.button(
                                "文件",
                                on_click=make_open_handler(open_file, asset["absolute_path"]),
                            ).props("dense size=sm")
                            ui.button(
                                "目录",
                                on_click=make_open_handler(open_folder, asset["absolute_path"]),
                            ).props("dense size=sm")

        async def handle_scan():
            scan_button.disable()
            try:
                stats = await run.io_bound(scan_current_library)
                ui.notify(
                    f"扫描完成：新增/更新 {stats['added_or_updated']}，"
                    f"删除 {stats['removed']}",
                    type="positive",
                )
                load_assets()
            except Exception as exc:
                ui.notify(str(exc), type="negative")
            finally:
                scan_button.enable()

        scan_button.on_click(handle_scan)
        type_select.on_value_change(lambda _: load_assets())
        load_assets()
