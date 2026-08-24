"""资产列表页：扫描 / 刷新、类型与文件名与标签过滤、排序、分页、派生状态徽章、
标签列、打开文件与目录、多选与批量总结 / 批量打标（m17）、
按文件夹层级浏览——面包屑 + 子文件夹导航 + 当前层直接文件（m19）。"""

from __future__ import annotations

import asyncio
from pathlib import Path

from nicegui import run, ui

from app.ui.tokens import C, CLS
from app.database import get_conn
from app.repositories.artifact_repository import has_active_artifact
from app.repositories.asset_repository import (
    count_assets,
    list_assets,
    list_child_folders,
)
from app.services.analysis_preset_service import list_analysis_presets
from app.services.analysis_service import (
    has_active_analysis,
    start_batch_analysis,
)
from app.services.scanner_service import scan_current_library
from app.services.summarization_service import start_batch_summarization
from app.services.tag_service import get_all_tags, start_batch_tagging
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
            tag_filter = ui.select(
                options=[],
                label="标签",
                multiple=True,
                clearable=True,
            ).classes("w-56")
            sort_select = ui.select(
                list(SORT_OPTIONS.keys()),
                value="修改时间 ↓",
                label="排序",
            ).classes("w-36")
            view_toggle = ui.toggle(
                {"folder": "按文件夹", "flat": "平铺"},
                value="folder",
            ).props('no-caps dense').classes("text-sm")
            count_label = ui.label("").classes("text-sm text-gray-600")

        # 批量操作栏（m17）：勾选数 > 0 时可用；选择集按 asset_id 跨页保留
        selection: dict = {"ids": set()}

        with ui.row().classes("items-center gap-3 mt-2"):
            selection_label = ui.label("已选 0 项").classes("text-sm text-gray-600")
            batch_summarize_btn = ui.button("批量总结", icon="notes").props(
                "outline size=sm"
            )
            batch_tag_btn = ui.button("批量打标", icon="sell").props(
                "outline size=sm"
            )
            batch_analyze_btn = ui.button("批量分析", icon="query_stats").props(
                "outline size=sm"
            )
            clear_selection_btn = ui.button("清除选择").props(
                "flat size=sm"
            )

        batch_summarize_btn.disable()
        batch_tag_btn.disable()
        batch_analyze_btn.disable()
        clear_selection_btn.disable()

        def update_selection_ui():
            count = len(selection["ids"])
            selection_label.text = f"已选 {count} 项"
            batch_summarize_btn.enabled = count > 0
            batch_tag_btn.enabled = count > 0
            batch_analyze_btn.enabled = count > 0
            clear_selection_btn.enabled = count > 0

        # 批量确认对话框须在页面层级定义，避免被 list_container.clear() 销毁
        with ui.dialog() as batch_summarize_dialog:
            with ui.card():
                batch_summarize_content = ui.column()

        with ui.dialog() as batch_tag_dialog:
            with ui.card():
                batch_tag_content = ui.column()

        with ui.dialog() as batch_analyze_dialog:
            with ui.card():
                batch_analyze_content = ui.column()

        list_container = ui.column().classes("w-full mt-4 overflow-x-auto")

        with ui.row().classes("items-center gap-3 mt-4 justify-center"):
            prev_btn = ui.button("← 上一页").props("outline size=sm")
            page_label = ui.label("").classes("text-sm text-gray-600")
            next_btn = ui.button("下一页 →").props("outline size=sm")

        current_page = {"value": 0}
        current_folder = {"value": ""}  # 当前浏览的文件夹（POSIX 相对路径，"" 为根）

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

        def make_enter_folder_handler(folder_path: str):
            async def handler():
                current_folder["value"] = folder_path
                current_page["value"] = 0
                await load_assets()

            return handler

        def make_open_folder_row_handler(folder_path: str):
            async def handler():
                try:
                    absolute_dir = Path(state.library_root) / folder_path
                    await run.io_bound(open_folder, str(absolute_dir))
                except Exception as exc:
                    notify_error(exc)

            return handler

        def render_folder_breadcrumb():
            """文件夹模式下的路径面包屑：祖先可点击返回，当前层加粗。"""
            with ui.row().classes(CLS["breadcrumb"]):
                if current_folder["value"]:
                    ui.button(
                        "全部", on_click=make_enter_folder_handler("")
                    ).props("flat dense size=sm no-caps").classes(CLS["link"])
                else:
                    ui.label("全部").classes(CLS["breadcrumb_current"])

                prefix = ""
                segments = current_folder["value"].split("/")
                for i, segment in enumerate(segments):
                    prefix = f"{prefix}/{segment}" if prefix else segment
                    ui.label("/").classes(CLS["breadcrumb_sep"])
                    if i < len(segments) - 1:
                        ui.button(
                            segment,
                            on_click=make_enter_folder_handler(prefix),
                        ).props("flat dense size=sm no-caps").classes(CLS["link"])
                    else:
                        ui.label(segment).classes(CLS["breadcrumb_current"])

        def render_folder_row(child: dict):
            """子文件夹行：名称点击进入，「打开」在资源管理器中定位。"""
            child_path = (
                f"{current_folder['value']}/{child['name']}"
                if current_folder["value"]
                else child["name"]
            )
            with ui.row().classes(CLS["table_row"]).style("min-width: 1080px"):
                ui.icon("folder", color="amber").classes("w-10")
                ui.button(
                    child["name"],
                    on_click=make_enter_folder_handler(child_path),
                ).props("flat dense no-caps align=left").classes(
                    "flex-1 truncate text-blue-600"
                ).tooltip(child_path)
                ui.badge(f"{child['count']} 个资产", color=C.NEUTRAL).classes(
                    "text-xs"
                )
                with ui.row().classes("w-36 gap-1 justify-end"):
                    ui.button(
                        "打开",
                        on_click=make_open_folder_row_handler(child_path),
                    ).props("dense size=sm")

        async def load_tag_options():
            """加载全部标签名作为筛选项（库未建标签表等异常时静默为空）。"""
            def _load():
                return [tag["name"] for tag in get_all_tags()]

            try:
                names = await run.io_bound(_load)
            except Exception:
                names = []

            # 修改 options 后需 update() 才会同步到客户端
            tag_filter.options = names
            tag_filter.update()

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
            tag_names = [t for t in (tag_filter.value or []) if t] or None

            # 文件夹浏览 = 按文件夹视图且无关键词；全库搜索与平铺模式不按文件夹过滤
            folder_browsing = view_toggle.value == "folder" and not keyword
            # None = 不过滤（搜索 / 平铺）；"" = 根层直接文件
            folder = current_folder["value"] if folder_browsing else None

            def _load():
                conn = get_conn(get_db_path())
                try:
                    folders = (
                        list_child_folders(
                            conn,
                            folder=folder,
                            asset_type=asset_type,
                            tag_names=tag_names,
                        )
                        if folder_browsing
                        else []
                    )
                    total = count_assets(
                        conn,
                        asset_type,
                        keyword=keyword,
                        tag_names=tag_names,
                        folder=folder,
                    )
                    rows = list_assets(
                        conn,
                        limit=PAGE_SIZE,
                        offset=offset,
                        asset_type=asset_type,
                        order_by=order_by,
                        order_dir=order_dir,
                        keyword=keyword,
                        tag_names=tag_names,
                        folder=folder,
                    )
                finally:
                    conn.close()
                return folders, total, rows

            folders, total, assets = await run.io_bound(_load)

            total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            if keyword:
                count_label.text = f"全库搜索：{total} 个结果"
            elif folder_browsing:
                count_label.text = (
                    f"当前层 {total} 个文件 · {len(folders)} 个子文件夹"
                )
            else:
                count_label.text = f"共 {total} 个资产"
            page_label.text = f"第 {page + 1} / {total_pages} 页"
            prev_btn.disabled = page <= 0
            next_btn.disabled = page >= total_pages - 1

            list_container.clear()
            with list_container:
                if folder_browsing:
                    render_folder_breadcrumb()
                    for child in folders:
                        render_folder_row(child)

                if not assets:
                    if folder_browsing and folders:
                        ui.label("此文件夹内暂无直接资产。").classes(
                            "text-gray-600"
                        )
                    elif folder_browsing and current_folder["value"]:
                        if asset_type or tag_names:
                            ui.label("没有匹配的资产。").classes("text-gray-600")
                        else:
                            ui.label("此文件夹内暂无资产。").classes("text-gray-600")
                    elif keyword or asset_type or tag_names:
                        ui.label("没有匹配的资产。").classes("text-gray-600")
                    else:
                        ui.label("暂无资产。请点击「扫描 / 刷新」。").classes(
                            "text-gray-600"
                        )
                    return

                def make_select_handler(asset_id: str):
                    def handler(e):
                        if e.value:
                            selection["ids"].add(asset_id)
                        else:
                            selection["ids"].discard(asset_id)
                        update_selection_ui()

                    return handler

                page_asset_ids = [asset["id"] for asset in assets]

                def make_select_all_handler():
                    async def handler(e):
                        if e.value:
                            selection["ids"].update(page_asset_ids)
                        else:
                            selection["ids"].difference_update(page_asset_ids)
                        update_selection_ui()
                        # 重新渲染本页各行勾选状态
                        await load_assets()

                    return handler

                # 文件夹浏览时标题即文件名、路径列冗余（标题列加宽）；
                # 搜索 / 平铺模式保留完整路径列便于定位
                show_path = not folder_browsing

                with ui.row().classes(CLS["table_head"]).style("min-width: 1080px"):
                    ui.checkbox(
                        "",
                        value=all(
                            asset_id in selection["ids"]
                            for asset_id in page_asset_ids
                        ),
                        on_change=make_select_all_handler(),
                    ).classes("w-10").tooltip("全选本页")
                    ui.label("标题").classes(
                        "w-56" if show_path else "flex-1"
                    )
                    ui.label("类型").classes("w-16")
                    if show_path:
                        ui.label("路径").classes("flex-1")
                    ui.label("标签").classes("w-40")
                    ui.label("状态").classes("w-48")
                    ui.label("大小").classes("w-20 text-right")
                    ui.label("修改时间").classes("w-32")
                    ui.label("操作").classes("w-36")

                for asset in assets:
                    with ui.row().classes(CLS["table_row"]).style(
                        "min-width: 1080px"
                    ):
                        ui.checkbox(
                            "",
                            value=asset["id"] in selection["ids"],
                            on_change=make_select_handler(asset["id"]),
                        ).classes("w-10")

                        ui.link(
                            asset["title"],
                            f"/assets/{asset['id']}",
                        ).classes(
                            "w-56 truncate text-blue-600"
                            if show_path
                            else "flex-1 truncate text-blue-600"
                        ).tooltip(asset["title"])

                        ui.label(asset["type"]).classes("w-16")

                        if show_path:
                            ui.label(asset["relative_path"]).classes(
                                "flex-1 truncate"
                            ).tooltip(asset["relative_path"])

                        tags = sorted(asset.get("tags") or [])
                        with ui.row().classes("w-40 gap-1 flex-wrap"):
                            for name in tags[:3]:
                                ui.badge(name, color=C.TAG).classes("text-xs")
                            if len(tags) > 3:
                                ui.badge(
                                    f"+{len(tags) - 3}", color=C.NEUTRAL
                                ).classes("text-xs")

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
                # 扫描可能删除文件夹，回到根目录避免停留在已消失的路径
                current_folder["value"] = ""
                await load_assets()
                # 扫描会清理已删资产及其标签绑定，筛选项随之刷新
                await load_tag_options()
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

        def count_selected_with_summary(asset_ids: list[str]) -> int:
            conn = get_conn(get_db_path())
            try:
                return sum(
                    1
                    for asset_id in asset_ids
                    if has_active_artifact(conn, asset_id, "summary")
                )
            finally:
                conn.close()

        async def run_batch_summarize(overwrite: bool):
            asset_ids = sorted(selection["ids"])
            batch_summarize_dialog.close()

            if not asset_ids:
                return

            try:
                report = await run.io_bound(
                    start_batch_summarization, asset_ids, overwrite
                )
            except Exception as exc:
                notify_error(exc)
                return

            message = f"已创建 {report['created']} 个总结任务，进度见任务中心"

            if report["skipped"]:
                message += f"；跳过 {len(report['skipped'])} 项"

            ui.notify(message, type="positive")

        async def open_batch_summarize_dialog():
            asset_ids = sorted(selection["ids"])

            if not asset_ids:
                return

            try:
                existing_count = await run.io_bound(
                    count_selected_with_summary, asset_ids
                )
            except Exception as exc:
                notify_error(exc)
                return

            batch_summarize_content.clear()
            with batch_summarize_content:
                ui.label("批量 AI 总结").classes("text-lg font-bold")

                if existing_count > 0:
                    ui.label(
                        f"已选 {len(asset_ids)} 项，"
                        f"其中 {existing_count} 项已有总结。"
                    ).classes("mt-1")
                else:
                    ui.label(f"将为 {len(asset_ids)} 个资产生成 AI 总结。").classes(
                        "mt-1"
                    )

                with ui.row().classes("mt-3 gap-2"):
                    if existing_count > 0:
                        ui.button(
                            "跳过已有，总结其余",
                            on_click=lambda: run_batch_summarize(False),
                        ).props("color=primary")
                        ui.button(
                            "全部重新生成（旧文件自动备份）",
                            on_click=lambda: run_batch_summarize(True),
                        ).props("outline")
                    else:
                        ui.button(
                            "开始总结",
                            on_click=lambda: run_batch_summarize(False),
                        ).props("color=primary")

                    ui.button("取消", on_click=batch_summarize_dialog.close).props(
                        "flat"
                    )

            batch_summarize_dialog.open()

        async def run_batch_tag():
            asset_ids = sorted(selection["ids"])
            batch_tag_dialog.close()

            if not asset_ids:
                return

            try:
                report = await run.io_bound(start_batch_tagging, asset_ids)
            except Exception as exc:
                notify_error(exc)
                return

            message = f"已创建 {report['created']} 个打标任务，进度见任务中心"

            if report["skipped"]:
                message += f"；跳过 {len(report['skipped'])} 项"

            ui.notify(message, type="positive")

        def open_batch_tag_dialog():
            asset_ids = sorted(selection["ids"])

            if not asset_ids:
                return

            batch_tag_content.clear()
            with batch_tag_content:
                ui.label("批量 AI 打标").classes("text-lg font-bold")
                ui.label(
                    f"将对 {len(asset_ids)} 个资产生成 AI 标签并自动追加保存"
                    "（不删除已有标签），任务可在任务中心查看。"
                ).classes("mt-1")

                with ui.row().classes("mt-3 gap-2"):
                    ui.button("开始打标", on_click=run_batch_tag).props(
                        "color=primary"
                    )
                    ui.button("取消", on_click=batch_tag_dialog.close).props("flat")

            batch_tag_dialog.open()

        async def run_batch_analyze(overwrite: bool, preset_id: str | None):
            asset_ids = sorted(selection["ids"])
            batch_analyze_dialog.close()

            if not asset_ids or not preset_id:
                return

            try:
                report = await run.io_bound(
                    start_batch_analysis, asset_ids, preset_id, overwrite
                )
            except Exception as exc:
                notify_error(exc)
                return

            message = f"已创建 {report['created']} 个分析任务，进度见任务中心"

            if report["skipped"]:
                message += f"；跳过 {len(report['skipped'])} 项"

            ui.notify(message, type="positive")

        def count_selected_with_analysis(asset_ids: list[str], preset_id: str) -> int:
            conn = get_conn(get_db_path())
            try:
                return sum(
                    1
                    for asset_id in asset_ids
                    if has_active_analysis(conn, asset_id, preset_id)
                )
            finally:
                conn.close()

        async def open_batch_analyze_dialog():
            asset_ids = sorted(selection["ids"])

            if not asset_ids:
                return

            try:
                presets = await run.io_bound(list_analysis_presets)
            except Exception as exc:
                notify_error(exc)
                return

            if not presets:
                ui.notify(
                    "未找到分析模板。模板位于 .knowledge/presets/，"
                    "加文件即加新分析类型。",
                    type="warning",
                )
                return

            batch_analyze_content.clear()

            with batch_analyze_content:
                ui.label("批量 AI 分析").classes("text-lg font-bold")

                analyze_preset_select = ui.select(
                    options={p["id"]: p["name"] for p in presets},
                    value=presets[0]["id"],
                    label="分析模板",
                ).classes("w-64")

                preset_desc_label = ui.label(
                    presets[0]["description"] or ""
                ).classes("text-xs text-gray-600 mt-1")

                analyze_existing_label = ui.label().classes("text-sm mt-2")
                ui.label(
                    "仅音频 / 视频且已有 JSON 转录的资产会创建任务，"
                    "其余跳过并记录原因。"
                ).classes("text-xs text-gray-600 mt-1")

                with ui.row().classes("mt-3 gap-2"):
                    ui.button(
                        "跳过已有，分析其余",
                        on_click=lambda: run_batch_analyze(
                            False, analyze_preset_select.value
                        ),
                    ).props("color=primary")
                    ui.button(
                        "全部重新生成（旧文件自动备份）",
                        on_click=lambda: run_batch_analyze(
                            True, analyze_preset_select.value
                        ),
                    ).props("outline")
                    ui.button(
                        "取消", on_click=batch_analyze_dialog.close
                    ).props("flat")

            async def refresh_existing_count():
                preset_id = analyze_preset_select.value

                try:
                    existing_count = await run.io_bound(
                        count_selected_with_analysis, asset_ids, preset_id
                    )
                except Exception:
                    existing_count = 0

                analyze_existing_label.set_text(
                    f"已选 {len(asset_ids)} 项，"
                    f"其中 {existing_count} 项已有此模板的分析。"
                )

            def handle_preset_change():
                preset_id = analyze_preset_select.value
                preset_desc_label.set_text(
                    next(
                        (p["description"] for p in presets if p["id"] == preset_id),
                        "",
                    )
                    or ""
                )
                # async 刷新计数交给事件循环，避免阻塞 on_change 回调
                asyncio.create_task(refresh_existing_count())

            analyze_preset_select.on_value_change(
                lambda: handle_preset_change()
            )
            await refresh_existing_count()

            batch_analyze_dialog.open()

        async def handle_clear_selection():
            selection["ids"].clear()
            update_selection_ui()
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
        tag_filter.on_value_change(handle_filter_or_sort_change)
        sort_select.on_value_change(handle_filter_or_sort_change)
        view_toggle.on_value_change(handle_filter_or_sort_change)
        name_filter.on_value_change(lambda: schedule_name_filter_reload())
        prev_btn.on_click(handle_prev)
        next_btn.on_click(handle_next)
        batch_summarize_btn.on_click(open_batch_summarize_dialog)
        batch_tag_btn.on_click(open_batch_tag_dialog)
        batch_analyze_btn.on_click(open_batch_analyze_dialog)
        clear_selection_btn.on_click(handle_clear_selection)

        await load_tag_options()
        await load_assets()
