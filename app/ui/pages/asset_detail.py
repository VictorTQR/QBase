"""资产详情页：原始文件信息、派生文件列表、文本预览/分段、转录与总结操作。"""

from __future__ import annotations

from nicegui import run, ui

from app.database import get_conn
from app.repositories.artifact_repository import list_artifacts_by_asset
from app.repositories.asset_repository import get_asset_by_id
from app.services import summarization_service, transcription_service
from app.state import get_db_path, state
from app.ui.layout import breadcrumb, page_header, require_library
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
    return path.endswith(".txt") or path.endswith(".md")


def _render_asset_badges(asset: dict):
    """渲染资产派生完成度 + 待解析状态徽章。"""
    if asset.get("has_transcript"):
        ui.badge("转录", color="green").classes("text-xs")
    if asset.get("has_summary"):
        ui.badge("总结", color="blue").classes("text-xs")
    if asset.get("has_note"):
        ui.badge("笔记", color="purple").classes("text-xs")
    if asset.get("has_parsed"):
        ui.badge("已解析", color="teal").classes("text-xs")
    if asset.get("has_meta"):
        ui.badge("元数据", color="grey-6").classes("text-xs")
    if asset.get("parse_status") == "pending":
        ui.badge("待解析", color="orange").classes("text-xs")


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
            "text-sm whitespace-pre-wrap text-gray-700 bg-gray-50 p-3 rounded"
        )
        ui.label("预览已截断").classes("text-xs text-gray-400 mt-1")

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
                "text-sm text-gray-500"
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
    page_header("资产详情", active_nav="assets")
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

    # 基本信息卡片
    with ui.card().classes("w-full p-4 mt-3"):
        with ui.row().classes("items-center gap-3"):
            ui.label(asset["title"]).classes("text-3xl font-bold")
            ui.badge(asset["type"], color="grey")
            _render_asset_badges(asset)

        ui.label(f"类型：{asset['type']}").classes("text-sm text-gray-600 mt-2")
        ui.label(f"相对路径：{asset['relative_path']}").classes("text-sm text-gray-600")
        ui.label(f"绝对路径：{asset['absolute_path']}").classes("text-sm text-gray-600")
        ui.label(f"大小：{human_size(asset['size'])}").classes("text-sm text-gray-600")
        ui.label(f"修改时间：{human_time(asset['mtime'])}").classes("text-sm text-gray-600")
        ui.label(f"解析状态：{asset['parse_status']}").classes("text-sm text-gray-600")

        with ui.row().classes("gap-2 mt-3"):
            ui.button(
                "打开文件",
                on_click=_make_open_handler(open_file, asset["absolute_path"]),
            ).props("dense")
            ui.button(
                "打开目录",
                on_click=_make_open_handler(open_folder, asset["absolute_path"]),
            ).props("dense")

    kinds = {artifact["kind"] for artifact in artifacts}
    has_transcript = "transcript" in kinds
    has_summary = "summary" in kinds

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
        ext = asset["relative_path"].lower()
        if ext.endswith(".md") or ext.endswith(".txt"):
            can_summarize = True
            summarize_hint = "将基于文档原文生成总结。"
        else:
            summarize_hint = "当前文档格式暂不支持总结，需要文档解析模块。"

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

    # 派生文件列表
    ui.label("派生文件").classes("text-xl font-semibold mt-6")

    if not artifacts:
        ui.label("暂无派生文件。").classes("text-gray-600")

    for artifact in artifacts:
        with ui.card().classes("w-full p-3 mt-2"):
            with ui.row().classes("w-full items-center gap-2"):
                ui.badge(
                    KIND_LABELS.get(artifact["kind"], artifact["kind"]),
                    color="grey",
                )
                ui.label(artifact["relative_path"]).classes(
                    "flex-1 truncate"
                ).tooltip(artifact["relative_path"])
                if artifact.get("status"):
                    ui.badge(artifact["status"], color="orange").classes("text-xs")
                if artifact.get("generator"):
                    ui.label(f"by {artifact['generator']}").classes(
                        "text-xs text-gray-400"
                    )
                ui.button(
                    "文件",
                    on_click=_make_open_handler(open_file, artifact["absolute_path"]),
                ).props("dense size=sm")
                ui.button(
                    "目录",
                    on_click=_make_open_handler(open_folder, artifact["absolute_path"]),
                ).props("dense size=sm")

            if is_text_artifact(artifact):
                _render_text_section(artifact)
