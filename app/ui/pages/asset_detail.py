"""资产详情页：原始文件信息、派生文件列表、文本预览。"""

from __future__ import annotations

from nicegui import run, ui

from app.database import get_conn
from app.repositories.artifact_repository import list_artifacts_by_asset
from app.repositories.asset_repository import get_asset_by_id
from app.services import summarization_service, transcription_service
from app.state import get_db_path, state
from app.ui.layout import page_frame
from app.utils import (
    human_size,
    human_time,
    open_file,
    open_folder,
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


def is_text_artifact(artifact: dict) -> bool:
    if artifact["kind"] not in TEXT_ARTIFACT_KINDS:
        return False

    path = artifact["relative_path"].lower()
    return path.endswith(".txt") or path.endswith(".md")


def make_open_handler(fn, path: str):
    async def handler():
        try:
            await run.io_bound(fn, path)
        except Exception as exc:
            ui.notify(str(exc), type="negative")

    return handler


@ui.page("/assets/{asset_id}")
def asset_detail_page(asset_id: str) -> None:
    with page_frame("资产详情"):
        if state.library_root is None:
            ui.label("未打开知识库").classes("text-xl")
            ui.link("去打开知识库", "/").classes("text-blue-600")
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

        ui.link("< 返回资产列表", "/assets").classes("text-blue-600")

        ui.label(asset["title"]).classes("text-3xl font-bold mt-2")

        with ui.row().classes("gap-2 mt-2"):
            ui.badge(asset["type"], color="grey")

            kinds = {artifact["kind"] for artifact in artifacts}
            has_transcript = "transcript" in kinds
            has_summary = "summary" in kinds

            if has_transcript:
                ui.badge("转录", color="green")
            if has_summary:
                ui.badge("总结", color="blue")
            if "note" in kinds:
                ui.badge("笔记", color="purple")
            if "parsed" in kinds:
                ui.badge("已解析", color="teal")

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
                    ui.notify(str(exc), type="negative")

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
                    ui.label("当前未检测到转录文件。").classes(
                        "text-sm text-gray-600"
                    )

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

        # AI 总结卡片（音视频基于转录；.md/.txt 基于原文）
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
                ui.notify(str(exc), type="negative")

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

                ui.link("任务中心", "/tasks").classes(
                    "flex items-center text-blue-600"
                )

        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("文件信息").classes("text-lg font-semibold")

            ui.label(f"类型：{asset['type']}")
            ui.label(f"相对路径：{asset['relative_path']}")
            ui.label(f"绝对路径：{asset['absolute_path']}")
            ui.label(f"大小：{human_size(asset['size'])}")
            ui.label(f"修改时间：{human_time(asset['mtime'])}")
            ui.label(f"解析状态：{asset['parse_status']}")

            with ui.row().classes("gap-2 mt-3"):
                ui.button(
                    "打开文件",
                    on_click=make_open_handler(open_file, asset["absolute_path"]),
                ).props("dense")
                ui.button(
                    "打开目录",
                    on_click=make_open_handler(open_folder, asset["absolute_path"]),
                ).props("dense")

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

                    ui.button(
                        "文件",
                        on_click=make_open_handler(open_file, artifact["absolute_path"]),
                    ).props("dense size=sm")
                    ui.button(
                        "目录",
                        on_click=make_open_handler(open_folder, artifact["absolute_path"]),
                    ).props("dense size=sm")

                if is_text_artifact(artifact):
                    try:
                        text, truncated = read_text_preview(
                            artifact["absolute_path"],
                            max_chars=2000,
                        )

                        with ui.expansion("预览", icon="visibility").classes(
                            "w-full mt-2"
                        ):
                            ui.label(text).classes("whitespace-pre-wrap text-sm")

                            if truncated:
                                ui.label("预览已截断。").classes(
                                    "text-xs text-gray-500 mt-2"
                                )
                    except Exception as exc:
                        ui.label(f"预览失败：{exc}").classes(
                            "text-sm text-red-600 mt-2"
                        )
