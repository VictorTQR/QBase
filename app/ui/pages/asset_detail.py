"""资产详情页：原始文件信息、派生文件列表、文本预览/分段、转录与总结操作。"""

from __future__ import annotations

from nicegui import run, ui
from pathlib import Path

from app.database import get_conn
from app.repositories.artifact_repository import list_artifacts_by_asset
from app.repositories.asset_repository import get_asset_by_id
from app.services import (
    config_service,
    summarization_service,
    transcription_service,
)
from app.services.parse_service import PARSEABLE_EXTENSIONS, start_parsing
from app.services.parsers import get_parser_for_extension
from app.state import get_db_path, state
from app.ui.components import render_derived_badges
from app.ui.layout import breadcrumb, page_frame, require_library
from app.ui.tokens import C
from app.utils import (
    human_size,
    human_time,
    notify_error,
    open_file,
    open_folder,
    read_text_full,
    read_text_preview,
)

KIND_LABELS = {
    "transcript": "转录",
    "transcript_meta": "转录元数据",
    "summary": "总结",
    "note": "笔记",
    "parsed": "解析结果",
    "meta": "元数据",
}

TEXT_ARTIFACT_KINDS = {"transcript", "summary", "note", "parsed"}

# 大文本分段阈值
SEGMENT_SIZE = 10000
FULL_TEXT_THRESHOLD = 50000


def is_text_artifact(artifact: dict) -> bool:
    if artifact["kind"] not in TEXT_ARTIFACT_KINDS:
        return False
    path = artifact["relative_path"].lower()
    return (
        path.endswith(".txt")
        or path.endswith(".md")
        or path.endswith(".transcript.json")
    )


def _make_open_handler(fn, path: str):
    async def handler():
        try:
            await run.io_bound(fn, path)
        except Exception as exc:
            notify_error(exc)

    return handler


def _render_text_section(artifact: dict):
    """渲染文本预览区域，支持展开全文与分段翻页。"""
    abs_path = artifact["absolute_path"]

    preview_container = ui.column().classes("w-full mt-2")
    full_container = ui.column().classes("w-full mt-2")
    full_container.set_visibility(False)

    try:
        preview_text, _ = read_text_preview(abs_path, max_chars=2000)
    except Exception:
        preview_text = "（无法读取预览）"

    with preview_container:
        ui.label(preview_text).classes(
            "text-sm whitespace-pre-wrap text-gray-700 bg-gray-50 p-3 rounded "
            "max-h-[40vh] overflow-y-auto"
        )
        ui.label("预览已截断").classes("text-xs text-gray-600 mt-1")

    expand_btn = ui.button("展开全文").props("flat size=sm color=blue").classes("mt-1")
    collapse_btn = ui.button("收起").props("flat size=sm color=grey").classes("mt-1")
    collapse_btn.set_visibility(False)

    segment_state = {"offset": 0, "total_len": 0, "full_text": ""}

    async def handle_expand():
        try:
            text = await run.io_bound(read_text_full, abs_path)
        except Exception as exc:
            notify_error(exc)
            return

        segment_state["full_text"] = text
        segment_state["total_len"] = len(text)

        preview_container.set_visibility(False)
        full_container.set_visibility(True)
        expand_btn.set_visibility(False)
        collapse_btn.set_visibility(True)

        if len(text) <= FULL_TEXT_THRESHOLD:
            with full_container:
                ui.label(text).classes(
                    "text-sm whitespace-pre-wrap text-gray-700 bg-gray-50 p-3 rounded "
                    "max-h-[70vh] overflow-y-auto"
                )
        else:
            _render_segment(full_container, segment_state)

    def handle_collapse():
        preview_container.set_visibility(True)
        full_container.set_visibility(False)
        expand_btn.set_visibility(True)
        collapse_btn.set_visibility(False)

    expand_btn.on_click(handle_expand)
    collapse_btn.on_click(handle_collapse)


def _render_segment(container, segment_state: dict):
    """渲染分段文本 + 翻页控件。"""
    container.clear()
    text = segment_state["full_text"]
    offset = segment_state["offset"]
    total_len = segment_state["total_len"]

    segment = text[offset : offset + SEGMENT_SIZE]
    current_page = offset // SEGMENT_SIZE + 1
    total_pages = (total_len + SEGMENT_SIZE - 1) // SEGMENT_SIZE

    with container:
        ui.label(segment).classes(
            "text-sm whitespace-pre-wrap text-gray-700 bg-gray-50 p-3 rounded "
            "max-h-[60vh] overflow-y-auto"
        )
        with ui.row().classes("items-center gap-3 mt-2"):
            seg_prev = ui.button("← 上一段").props("outline size=sm")
            ui.label(f"第 {current_page} / {total_pages} 段").classes(
                "text-sm text-gray-600"
            )
            seg_next = ui.button("下一段 →").props("outline size=sm")

            seg_prev.disabled = offset <= 0
            seg_next.disabled = offset + SEGMENT_SIZE >= total_len

            def go_prev():
                segment_state["offset"] = max(0, offset - SEGMENT_SIZE)
                _render_segment(container, segment_state)

            def go_next():
                segment_state["offset"] = offset + SEGMENT_SIZE
                _render_segment(container, segment_state)

            seg_prev.on_click(go_prev)
            seg_next.on_click(go_next)


@ui.page("/assets/{asset_id}")
def asset_detail_page(asset_id: str) -> None:
    with page_frame("资产详情", active_nav="assets"):
        if not require_library():
            return

        conn = get_conn(get_db_path())
        try:
            asset = get_asset_by_id(conn, asset_id)
            artifacts = list_artifacts_by_asset(conn, asset_id) if asset else []
        finally:
            conn.close()

        if asset is None:
            ui.label("资产不存在").classes("text-xl")
            ui.link("返回资产列表", "/assets").classes("text-blue-600")
            return

        breadcrumb([
            ("首页", "/"),
            ("资产列表", "/assets"),
            (asset["title"], None),
        ])

        kinds = {artifact["kind"] for artifact in artifacts}
        has_transcript = "transcript" in kinds
        has_summary = "summary" in kinds
        has_parsed = "parsed" in kinds

        # 基本信息卡片
        with ui.card().classes("w-full p-4 mt-3"):
            with ui.row().classes("items-center gap-3"):
                ui.label(asset["title"]).classes("text-3xl font-bold")
                ui.badge(asset["type"], color=C.NEUTRAL)
                render_derived_badges(asset)

            ui.label(f"类型：{asset['type']}").classes("text-sm text-gray-600 mt-2")
            ui.label(f"相对路径：{asset['relative_path']}").classes("text-sm text-gray-600")
            ui.label(f"绝对路径：{asset['absolute_path']}").classes("text-sm text-gray-600")
            ui.label(f"大小：{human_size(asset['size'])}").classes("text-sm text-gray-600")
            ui.label(f"修改时间：{human_time(asset['mtime'])}").classes("text-sm text-gray-600")
            # parse_status 是静态策略值（pdf/office 恒 pending），按解析产物显示有效状态
            if has_parsed:
                parse_status_label = "已解析"
            elif asset["parse_status"] == "pending":
                parse_status_label = "待解析"
            elif asset["parse_status"] == "not_required":
                parse_status_label = "无需解析"
            else:
                parse_status_label = asset["parse_status"]
            ui.label(f"解析状态：{parse_status_label}").classes("text-sm text-gray-600")

            with ui.row().classes("gap-2 mt-3"):
                ui.button(
                    "打开文件",
                    on_click=_make_open_handler(open_file, asset["absolute_path"]),
                ).props("dense")
                ui.button(
                    "打开目录",
                    on_click=_make_open_handler(open_folder, asset["absolute_path"]),
                ).props("dense")

        # 文档解析卡片（仅白名单文档类型，m9）
        asset_ext = Path(asset["relative_path"]).suffix.lower()
        can_parse = asset["type"] == "document" and asset_ext in PARSEABLE_EXTENSIONS

        if can_parse:
            parse_ready = False
            parse_hint = ""

            try:
                parse_config = config_service.get_parse_config()

                if not parse_config.get("enabled"):
                    parse_hint = "文档解析未启用，请前往设置页开启。"
                else:
                    # 按扩展名路由实例化（.epub 本地免 token；mineru 缺 token 抛
                    # ValueError，文案直接展示）
                    get_parser_for_extension(parse_config, asset_ext)
                    parse_ready = True
            except ValueError as exc:
                parse_hint = f"{exc}，请前往设置页检查。"
            except Exception:
                parse_hint = "无法读取解析配置，请前往设置页检查。"

            parse_is_local = asset_ext == ".epub"

            async def start_parsing_task():
                try:
                    task_id = await run.io_bound(start_parsing, asset["id"])
                    ui.notify(
                        f"解析任务已创建：{task_id[:8]}。请查看任务中心。",
                        type="positive",
                    )
                    parse_button.disable()
                except Exception as exc:
                    notify_error(exc)

            with ui.dialog() as overwrite_parse_dialog:
                with ui.card():
                    ui.label("已存在解析结果，是否重新解析？（旧结果会自动备份）")
                    with ui.row().classes("gap-2 mt-3"):
                        ui.button("取消", on_click=overwrite_parse_dialog.close)

                        async def confirm_overwrite_parse():
                            overwrite_parse_dialog.close()
                            await start_parsing_task()

                        ui.button("覆盖并解析", on_click=confirm_overwrite_parse)

            with ui.card().classes("w-full p-4 mt-4"):
                ui.label("文档解析").classes("text-lg font-semibold")

                if has_parsed:
                    ui.label(
                        "当前已检测到解析结果。重新解析会覆盖（旧结果自动备份）。"
                    ).classes("text-sm text-gray-600")
                elif parse_ready and parse_is_local:
                    ui.label(
                        "本地解析为 Markdown（内置 EPUB 解析器，无需远端服务，"
                        "通常数秒完成）。"
                    ).classes("text-sm text-gray-600")
                elif parse_ready:
                    ui.label(
                        "调用 MinerU 解析为 Markdown（远端异步任务，约需 1-5 分钟）。"
                    ).classes("text-sm text-gray-600")
                else:
                    ui.label(parse_hint).classes("text-sm text-orange-600")

                with ui.row().classes("gap-3 mt-3"):
                    if parse_ready:
                        parse_button = ui.button(
                            "重新解析" if has_parsed else "生成解析",
                            icon="description",
                            on_click=lambda: (
                                overwrite_parse_dialog.open()
                                if has_parsed
                                else start_parsing_task()
                            ),
                        )
                    else:
                        ui.button("生成解析", icon="description").props("disable")
                    ui.link("任务中心", "/tasks").classes(
                        "flex items-center text-blue-600"
                    )

        # 转录操作卡片（仅音频/视频）
        if asset["type"] in {"audio", "video"}:
            async def start_transcription():
                try:
                    task_id = await run.io_bound(
                        transcription_service.start_transcription,
                        asset["id"],
                    )
                    ui.notify(
                        f"转录任务已创建：{task_id[:8]}。请查看任务中心。",
                        type="positive",
                    )
                    transcribe_button.disable()
                except Exception as exc:
                    notify_error(exc)

            with ui.dialog() as overwrite_dialog:
                with ui.card():
                    ui.label("已存在转录文件，是否覆盖？")
                    with ui.row().classes("gap-2 mt-3"):
                        ui.button("取消", on_click=overwrite_dialog.close)

                        async def confirm_overwrite():
                            overwrite_dialog.close()
                            await start_transcription()

                        ui.button("覆盖并转录", on_click=confirm_overwrite)

            with ui.card().classes("w-full p-4 mt-4"):
                ui.label("转录").classes("text-lg font-semibold")
                if has_transcript:
                    ui.label(
                        "当前已检测到转录文件。重新生成可能会覆盖已有文件。"
                    ).classes("text-sm text-gray-600")
                else:
                    ui.label("当前未检测到转录文件。").classes("text-sm text-gray-600")
                with ui.row().classes("gap-3 mt-3"):
                    transcribe_button = ui.button(
                        "重新生成转录" if has_transcript else "生成转录",
                        on_click=lambda: (
                            overwrite_dialog.open()
                            if has_transcript
                            else start_transcription()
                        ),
                    )
                    ui.link("任务中心", "/tasks").classes(
                        "flex items-center text-blue-600"
                    )

        # AI 总结卡片
        async def start_summarization():
            try:
                task_id = await run.io_bound(
                    summarization_service.start_summarization,
                    asset["id"],
                )
                ui.notify(
                    f"总结任务已创建：{task_id[:8]}。请查看任务中心。",
                    type="positive",
                )
                summarize_button.disable()
            except Exception as exc:
                notify_error(exc)

        with ui.dialog() as overwrite_summary_dialog:
            with ui.card():
                ui.label("已存在总结文件，是否覆盖？（旧文件会自动备份）")
                with ui.row().classes("gap-2 mt-3"):
                    ui.button("取消", on_click=overwrite_summary_dialog.close)

                    async def confirm_overwrite_summary():
                        overwrite_summary_dialog.close()
                        await start_summarization()

                    ui.button("覆盖并生成", on_click=confirm_overwrite_summary)

        can_summarize = False
        summarize_hint = ""

        if asset["type"] in {"audio", "video"}:
            if has_transcript:
                can_summarize = True
                summarize_hint = "将基于转录文本生成总结。"
            else:
                summarize_hint = "需要先生成转录，才能生成总结。"
        elif asset["type"] == "document":
            if asset_ext in {".md", ".txt"}:
                can_summarize = True
                summarize_hint = "将基于文档原文生成总结。"
            elif asset_ext in PARSEABLE_EXTENSIONS:
                if has_parsed:
                    can_summarize = True
                    summarize_hint = "将基于解析结果生成总结。"
                else:
                    summarize_hint = "需要先生成解析，才能生成总结。"
            else:
                summarize_hint = "当前文档格式暂不支持总结。"

        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("AI 总结").classes("text-lg font-semibold")
            ui.label(summarize_hint).classes("text-sm text-gray-600")
            if has_summary:
                ui.label(
                    "当前已存在总结文件。重新生成会覆盖（旧文件自动备份）。"
                ).classes("text-sm text-orange-600 mt-1")
            with ui.row().classes("gap-3 mt-3"):
                if can_summarize:
                    summarize_button = ui.button(
                        "重新生成总结" if has_summary else "生成总结",
                        icon="auto_awesome",
                        on_click=lambda: (
                            overwrite_summary_dialog.open()
                            if has_summary
                            else start_summarization()
                        ),
                    )
                else:
                    ui.button("生成总结", icon="auto_awesome").props("disable")
                ui.link("任务中心", "/tasks").classes("flex items-center text-blue-600")

        # 派生文件（多 tab 展示：每个派生文件一个 tab）
        ui.label("派生文件").classes("text-xl font-semibold mt-6")

        if not artifacts:
            ui.label("暂无派生文件。").classes("text-gray-600")
        else:
            # 计算 tab 标签：kind 标签为主，同 kind 重复时追加序号区分
            seen: dict[str, int] = {}
            tab_names: list[str] = []
            for artifact in artifacts:
                base = KIND_LABELS.get(artifact["kind"], artifact["kind"])
                if base in seen:
                    seen[base] += 1
                    tab_names.append(f"{base} ({seen[base]})")
                else:
                    seen[base] = 1
                    tab_names.append(base)

            with ui.tabs().classes("w-full") as derived_tabs:
                for name in tab_names:
                    ui.tab(name, label=name)

            with ui.tab_panels(derived_tabs, value=tab_names[0]).classes("w-full"):
                for idx, artifact in enumerate(artifacts):
                    with ui.tab_panel(tab_names[idx]):
                        with ui.card().classes("w-full p-3"):
                            with ui.row().classes("w-full items-center gap-2"):
                                ui.badge(
                                    KIND_LABELS.get(artifact["kind"], artifact["kind"]),
                                    color=C.NEUTRAL,
                                )
                                ui.label(artifact["relative_path"]).classes(
                                    "flex-1 truncate"
                                ).tooltip(artifact["relative_path"])
                                if artifact.get("status"):
                                    ui.badge(
                                        artifact["status"], color=C.WARNING
                                    ).classes("text-xs")
                                if artifact.get("generator"):
                                    ui.label(f"by {artifact['generator']}").classes(
                                        "text-xs text-gray-600"
                                    )
                                ui.button(
                                    "文件",
                                    on_click=_make_open_handler(
                                        open_file, artifact["absolute_path"]
                                    ),
                                ).props("dense size=sm")
                                ui.button(
                                    "目录",
                                    on_click=_make_open_handler(
                                        open_folder, artifact["absolute_path"]
                                    ),
                                ).props("dense size=sm")

                            if is_text_artifact(artifact):
                                _render_text_section(artifact)
