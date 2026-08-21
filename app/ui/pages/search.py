"""搜索页：文件名 + 全文 + 语义 + 综合（RRF 融合）搜索，命中高亮，派生徽章，统一错误提示。"""

from __future__ import annotations

from nicegui import run, ui

from app.database import get_conn
from app.services import index_service, search_service, vector_service
from app.state import get_db_path, state
from app.ui.components import render_derived_badges
from app.ui.layout import page_frame, require_library
from app.ui.tokens import C
from app.utils import highlight_snippet, notify_error


@ui.page("/search")
def search_page():
    with page_frame("搜索", active_nav="search"):
        if not require_library():
            return

        with ui.row().classes("items-center gap-3 mt-3 w-full"):
            query_input = ui.input(
                label="搜索关键词", placeholder="输入搜索关键词…"
            ).classes("flex-1")
            hybrid_btn = ui.button("综合搜索")
            fulltext_btn = ui.button("全文搜索").props("outline")
            filename_btn = ui.button("文件名搜索").props("outline")
            vector_btn = ui.button("语义搜索").props("outline color=teal")

        with ui.row().classes("items-center gap-3 mt-2"):
            rebuild_button = ui.button("重建全文索引", icon="refresh")
            rebuild_vector_button = ui.button("重建向量索引", icon="bubble_chart")
            ui.label(
                "首次使用全文搜索前先重建全文索引；首次语义搜索前先重建向量索引。"
            ).classes("text-xs text-gray-600")
            ui.label("重建向量索引会调用 Embedding API，可能产生费用。").classes(
                "text-xs text-orange-600"
            )

        results_container = ui.column().classes("w-full mt-4")

        def render_results(
            results: list[dict], mode: str, degraded_reason: str | None = None
        ):
            results_container.clear()
            with results_container:
                if degraded_reason:
                    ui.label(degraded_reason).classes(
                        "text-xs text-orange-600 mb-2"
                    )
                if not results:
                    ui.label("未找到相关结果。").classes("text-gray-600 mt-4")
                    return
                ui.label(f"共 {len(results)} 条结果").classes(
                    "text-sm text-gray-600 mb-2"
                )
                for result in results:
                    with ui.card().classes("w-full p-3 mb-2"):
                        with ui.row().classes("items-center gap-2"):
                            if result.get("asset_id"):
                                ui.link(
                                    result["asset_title"],
                                    f"/assets/{result['asset_id']}",
                                ).classes("text-blue-600 font-medium")
                            else:
                                ui.label(result["asset_title"]).classes("font-medium")
                            ui.badge(result["kind"], color=C.NEUTRAL).classes("text-xs")
                            if mode == "hybrid":
                                sources = result.get("sources") or []
                                if len(sources) >= 2:
                                    ui.badge("双命中", color=C.SUCCESS).classes(
                                        "text-xs"
                                    )
                                elif "vector" in sources:
                                    ui.badge("语义", color=C.PARSED).classes("text-xs")
                                else:
                                    ui.badge("全文", color=C.INFO).classes("text-xs")
                            if result.get("asset_type"):
                                ui.badge(
                                    result["asset_type"], color=C.ASSET_TYPE
                                ).classes("text-xs")
                            render_derived_badges(result)

                        snippet = result.get("snippet", "")
                        words = result.get("highlight_words", [])
                        if words and snippet:
                            highlighted = highlight_snippet(snippet, words)
                            ui.html(
                                f'<p class="text-sm mt-2 whitespace-pre-wrap">{highlighted}</p>'
                            ).classes("w-full")
                        else:
                            ui.label(snippet).classes(
                                "text-sm mt-2 whitespace-pre-wrap text-gray-600"
                            )

                        if (
                            result.get("rrf_score") is not None
                            or result.get("distance") is not None
                        ):
                            with ui.row().classes("gap-3"):
                                if result.get("rrf_score") is not None:
                                    ui.label(
                                        f"rrf_score: {result['rrf_score']:.4f}"
                                    ).classes("text-xs text-gray-600")
                                if result.get("distance") is not None:
                                    ui.label(
                                        f"distance: {result['distance']:.4f}"
                                    ).classes("text-xs text-gray-600")
                        ui.label(result.get("relative_path", "")).classes(
                            "text-xs text-gray-600 mt-1"
                        )

        async def handle_hybrid():
            query = query_input.value.strip()
            if not query:
                ui.notify("请输入搜索关键词", type="warning")
                return
            try:
                conn = get_conn(get_db_path())
                try:
                    results, degraded_reason = search_service.search_hybrid(
                        conn, query
                    )
                finally:
                    conn.close()
                render_results(results, "hybrid", degraded_reason=degraded_reason)
            except Exception as exc:
                notify_error(exc)

        async def handle_fulltext():
            query = query_input.value.strip()
            if not query:
                ui.notify("请输入搜索关键词", type="warning")
                return
            try:
                conn = get_conn(get_db_path())
                try:
                    results = search_service.search_fulltext(conn, query)
                finally:
                    conn.close()
                render_results(results, "fulltext")
            except Exception as exc:
                notify_error(exc)

        async def handle_filename():
            query = query_input.value.strip()
            if not query:
                ui.notify("请输入搜索关键词", type="warning")
                return
            try:
                conn = get_conn(get_db_path())
                try:
                    results = search_service.search_filename(conn, query)
                finally:
                    conn.close()
                render_results(results, "filename")
            except Exception as exc:
                notify_error(exc)

        async def handle_vector():
            query = query_input.value.strip()
            if not query:
                ui.notify("请输入搜索关键词", type="warning")
                return
            try:
                conn = get_conn(get_db_path())
                try:
                    results = search_service.search_vector(conn, query)
                finally:
                    conn.close()
                render_results(results, "vector")
            except Exception as exc:
                notify_error(exc)

        async def handle_rebuild():
            rebuild_button.disable()
            try:
                stats = await run.io_bound(index_service.rebuild_fulltext_index)
                ui.notify(
                    "全文索引重建完成："
                    f"{stats['sources']} 个来源，{stats['chunks']} 个片段",
                    type="positive",
                )
            except Exception as exc:
                notify_error(exc)
            finally:
                rebuild_button.enable()

        async def handle_rebuild_vector():
            rebuild_vector_button.disable()
            try:
                stats = await run.io_bound(vector_service.rebuild_vector_index)
                ui.notify(
                    "向量索引重建完成："
                    f"总片段 {stats['total_chunks']}，"
                    f"缓存命中 {stats['cache_hits']}，新调用 {stats['embedded']}",
                    type="positive",
                )
            except Exception as exc:
                notify_error(exc)
            finally:
                rebuild_vector_button.enable()

        hybrid_btn.on_click(handle_hybrid)
        fulltext_btn.on_click(handle_fulltext)
        filename_btn.on_click(handle_filename)
        vector_btn.on_click(handle_vector)
        rebuild_button.on_click(handle_rebuild)
        rebuild_vector_button.on_click(handle_rebuild_vector)
        query_input.on("keydown.enter", handle_hybrid)
