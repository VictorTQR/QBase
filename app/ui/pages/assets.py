"""资产列表页：扫描 / 刷新、类型与文件名过滤、排序、分页、派生状态徽章、打开文件与目录。"""

from __future__ import annotations

import asyncio

from nicegui import run, ui

from app.ui.tokens import CLS
from app.database import get_conn
from app.repositories.asset_repository import count_assets, list_assets
from app.services.scanner_service import scan_current_library
from app.state import get_db_path, state
from app.ui.components import render_derived_badges
from app.ui.layout import page_frame, require_library
from app.utils import (
    human_size,
    human_time,
    notify_error,
    open_file,
    open_folder,
)

PAGE_SIZE = 50

SORT_OPTIONS = {
    "修改时间 ↓": ("mtime", "DESC"),
    "修改时间 ↑": ("mtime", "ASC"),
    "名称 A→Z": ("title", "ASC"),
    "名称 Z→A": ("title", "DESC"),
    "大小 ↓": ("size", "DESC"),
    "大小 ↑": ("size", "ASC"),
    "类型": ("type", "ASC"),
}


@ui.page("/assets")
async def assets_page():
    with page_frame("资产列表", active_nav="assets"):
        if not require_library():
            return

        with ui.row().classes("items-center gap-3 mt-3"):
            scan_button = ui.button("扫描 / 刷新", color="primary")
            name_filter = ui.input(
                label="文件名", placeholder="按标题或路径筛选…"
            ).classes("w-64").props("clearable")
            type_filter = ui.select(
                ["全部", "audio", "video", "document"],
                value="全部",
                label="类型",
            ).classes("w-32")
            sort_select = ui.select(
                list(SORT_OPTIONS.keys()),
                value="修改时间 ↓",
                label="排序",
            ).classes("w-36")
            count_label = ui.label("").classes("text-sm text-gray-600")

        list_container = ui.column().classes("w-full mt-4 overflow-x-auto")

        with ui.row().classes("items-center gap-3 mt-4 justify-center"):
            prev_btn = ui.button("← 上一页").props("outline size=sm")
            page_label = ui.label("").classes("text-sm text-gray-600")
            next_btn = ui.button("下一页 →").props("outline size=sm")

        current_page = {"value": 0}

        def make_open_file_handler(asset: dict):
            async def handler():
                try:
                    await run.io_bound(open_file, asset["absolute_path"])
                except Exception as exc:
                    notify_error(exc)

            return handler

        def make_open_folder_handler(asset: dict):
            async def handler():
                try:
                    await run.io_bound(open_folder, asset["absolute_path"])
                except Exception as exc:
                    notify_error(exc)

            return handler

        async def load_assets():
            list_container.clear()
            with list_container:
                ui.spinner(size="md")
            await asyncio.sleep(0)

            page = current_page["value"]
            offset = page * PAGE_SIZE

            sort_key = sort_select.value or "修改时间 ↓"
            order_by, order_dir = SORT_OPTIONS.get(sort_key, ("mtime", "DESC"))

            selected_type = type_filter.value
            asset_type = selected_type if selected_type != "全部" else None
            keyword = (name_filter.value or "").strip() or None

            def _load():
                conn = get_conn(get_db_path())
                try:
                    total = count_assets(conn, asset_type, keyword=keyword)
                    rows = list_assets(
                        conn,
                        limit=PAGE_SIZE,
                        offset=offset,
                        asset_type=asset_type,
                        order_by=order_by,
                        order_dir=order_dir,
                        keyword=keyword,
                    )
                finally:
                    conn.close()
                return total, rows

            total, assets = await run.io_bound(_load)

            total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            count_label.text = f"共 {total} 个资产"
            page_label.text = f"第 {page + 1} / {total_pages} 页"
            prev_btn.disabled = page <= 0
            next_btn.disabled = page >= total_pages - 1

            list_container.clear()
            with list_container:
                if not assets:
                    if keyword or asset_type:
                        ui.label("没有匹配的资产。").classes("text-gray-600")
                    else:
                        ui.label("暂无资产。请点击「扫描 / 刷新」。").classes(
                            "text-gray-600"
                        )
                    return

                with ui.row().classes(CLS["table_head"]).style("min-width: 900px"):
                    ui.label("标题").classes("w-56")
                    ui.label("类型").classes("w-16")
                    ui.label("路径").classes("flex-1")
                    ui.label("状态").classes("w-48")
                    ui.label("大小").classes("w-20 text-right")
                    ui.label("修改时间").classes("w-32")
                    ui.label("操作").classes("w-36")

                for asset in assets:
                    with ui.row().classes(CLS["table_row"]).style("min-width: 900px"):
                        ui.link(
                            asset["title"],
                            f"/assets/{asset['id']}",
                        ).classes("w-56 truncate text-blue-600").tooltip(asset["title"])

                        ui.label(asset["type"]).classes("w-16")
                        ui.label(asset["relative_path"]).classes(
                            "flex-1 truncate"
                        ).tooltip(asset["relative_path"])

                        with ui.row().classes("w-48 gap-1 flex-wrap"):
                            render_derived_badges(asset)

                        ui.label(human_size(asset["size"])).classes("w-20 text-right")
                        ui.label(human_time(asset["mtime"])).classes("w-32")

                        with ui.row().classes("w-36 gap-1"):
                            ui.button(
                                "文件",
                                on_click=make_open_file_handler(asset),
                            ).props("dense size=sm")
                            ui.button(
                                "目录",
                                on_click=make_open_folder_handler(asset),
                            ).props("dense size=sm")

        async def handle_scan():
            scan_button.disable()
            try:
                stats = await run.io_bound(scan_current_library)
                message = (
                    "扫描完成："
                    f"资产新增/更新 {stats['assets_added_or_updated']}，"
                    f"删除 {stats['assets_removed']}；"
                    f"派生文件 {stats['artifacts_added_or_updated']} 个"
                )
                ui.notify(message, type="positive")

                if stats["ambiguous_artifacts"] > 0:
                    ui.notify(
                        f"有 {stats['ambiguous_artifacts']} 个派生文件存在歧义，未自动绑定",
                        type="warning",
                    )

                if stats["orphan_artifacts"] > 0:
                    ui.notify(
                        f"有 {stats['orphan_artifacts']} 个派生文件未找到对应资产",
                        type="warning",
                    )

                current_page["value"] = 0
                await load_assets()
            except Exception as exc:
                notify_error(exc)
            finally:
                scan_button.enable()

        async def handle_prev():
            if current_page["value"] > 0:
                current_page["value"] -= 1
                await load_assets()

        async def handle_next():
            current_page["value"] += 1
            await load_assets()

        async def handle_filter_or_sort_change():
            current_page["value"] = 0
            await load_assets()

        name_debounce: dict = {"handle": None, "task": None}

        def fire_name_filter_reload():
            name_debounce["handle"] = None
            # 持有 task 引用，避免任务被垃圾回收
            name_debounce["task"] = asyncio.create_task(
                handle_filter_or_sort_change()
            )

        def schedule_name_filter_reload():
            # 输入防抖：停止输入 0.3 秒后再查询，避免每个按键都触发加载
            # （当前 NiceGUI 的 Timer 无 restart()，用事件循环句柄实现）
            if name_debounce["handle"] is not None:
                name_debounce["handle"].cancel()
            name_debounce["handle"] = asyncio.get_running_loop().call_later(
                0.3, fire_name_filter_reload
            )

        scan_button.on_click(handle_scan)
        type_filter.on_value_change(handle_filter_or_sort_change)
        sort_select.on_value_change(handle_filter_or_sort_change)
        name_filter.on_value_change(lambda: schedule_name_filter_reload())
        prev_btn.on_click(handle_prev)
        next_btn.on_click(handle_next)

        await load_assets()
