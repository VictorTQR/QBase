"""搜索页：文件名 + 全文 + 语义搜索，手动重建全文/向量索引。"""

from __future__ import annotations

from nicegui import run, ui

from app.services import index_service, search_service, vector_service
from app.state import state
from app.ui.layout import page_frame


KIND_LABELS = {
    "asset": "文件名",
    "document": "文档",
    "transcript": "转录",
    "summary": "总结",
    "note": "笔记",
    "parsed": "解析结果",
    "transcript_meta": "转录元数据",
    "meta": "元数据",
    "vector": "向量",
}

MODE_MAP = {"全文": "fulltext", "文件名": "filename", "语义": "vector"}


@ui.page("/search")
def search_page():
    with page_frame("搜索"):
        if state.library_root is None:
            ui.label("未打开知识库").classes("text-xl")
            ui.link("去打开知识库", "/").classes("text-blue-600")
            return

        ui.label("搜索").classes("text-2xl font-bold")
        ui.label(str(state.library_root)).classes("text-sm text-gray-500")

        with ui.row().classes("items-end gap-3 mt-3"):
            query_input = ui.input("搜索关键词").classes("w-96")

            mode_select = ui.select(
                list(MODE_MAP.keys()),
                value="全文",
                label="搜索模式",
            )

            search_button = ui.button("搜索", icon="search")
            rebuild_button = ui.button("重建全文索引", icon="refresh")
            rebuild_vector_button = ui.button("重建向量索引", icon="bubble_chart")

        ui.label(
            "首次使用全文搜索前，先重建全文索引；首次使用语义搜索前，先重建向量索引。"
        ).classes("text-sm text-gray-600 mt-2")

        ui.label("重建向量索引会调用 Embedding API，可能产生费用或额度消耗。").classes(
            "text-sm text-orange-600 mt-1"
        )

        results_container = ui.column().classes("w-full mt-4")

        def render_results(results: list[dict]):
            results_container.clear()

            with results_container:
                if not results:
                    ui.label("没有搜索结果。").classes("text-gray-600")
                    return

                for result in results:
                    with ui.card().classes("w-full p-3"):
                        with ui.row().classes("w-full items-center gap-2"):
                            if result["asset_id"]:
                                ui.link(
                                    result["asset_title"],
                                    f"/assets/{result['asset_id']}",
                                ).classes("text-blue-600 font-semibold no-underline")
                            else:
                                ui.label(result["asset_title"]).classes("font-semibold")

                            ui.badge(
                                KIND_LABELS.get(result["kind"], result["kind"]),
                                color="grey",
                            )

                            if result.get("asset_type"):
                                ui.badge(result["asset_type"], color="blue-grey")

                            if result.get("distance") is not None:
                                ui.label(f"distance: {result['distance']:.4f}").classes(
                                    "text-xs text-gray-500"
                                )

                        ui.label(result["relative_path"]).classes(
                            "text-xs text-gray-500 mt-1 truncate"
                        )

                        ui.label(result["snippet"]).classes(
                            "text-sm mt-2 whitespace-pre-wrap"
                        )

        async def handle_search():
            query = query_input.value

            if not query or not query.strip():
                ui.notify("请输入搜索关键词", type="warning")
                return

            mode = MODE_MAP.get(mode_select.value, "fulltext")

            search_button.disable()

            try:
                results = await run.io_bound(
                    search_service.search,
                    query,
                    mode,
                )

                render_results(results)
            except Exception as exc:
                ui.notify(str(exc), type="negative")
            finally:
                search_button.enable()

        async def handle_rebuild():
            rebuild_button.disable()

            try:
                stats = await run.io_bound(index_service.rebuild_fulltext_index)

                ui.notify(
                    "全文索引重建完成："
                    f"{stats['sources']} 个来源，"
                    f"{stats['chunks']} 个片段",
                    type="positive",
                )
            except Exception as exc:
                ui.notify(str(exc), type="negative")
            finally:
                rebuild_button.enable()

        async def handle_rebuild_vector():
            rebuild_vector_button.disable()

            try:
                stats = await run.io_bound(vector_service.rebuild_vector_index)

                ui.notify(
                    "向量索引重建完成："
                    f"总片段 {stats['total_chunks']}，"
                    f"缓存命中 {stats['cache_hits']}，"
                    f"新调用 {stats['embedded']}",
                    type="positive",
                )
            except Exception as exc:
                ui.notify(str(exc), type="negative")
            finally:
                rebuild_vector_button.enable()

        search_button.on_click(handle_search)
        rebuild_button.on_click(handle_rebuild)
        rebuild_vector_button.on_click(handle_rebuild_vector)

        query_input.on("keydown.enter", handle_search)
