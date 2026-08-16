"""设置页：配置总览（CLI / Embedding / LLM）+ 索引管理。"""

from __future__ import annotations

from nicegui import run, ui

from app.services.config_service import get_config_path, load_config
from app.services.index_service import rebuild_fulltext_index
from app.services.vector_service import rebuild_vector_index
from app.state import state
from app.ui.layout import page_frame


@ui.page("/settings")
def settings_page() -> None:
    with page_frame("设置"):
        if state.library_root is None:
            ui.label("未打开知识库").classes("text-xl")
            ui.link("去打开知识库", "/").classes("text-blue-600")
            return

        ui.label("设置").classes("text-2xl font-bold")
        ui.label(str(state.library_root)).classes("text-sm text-gray-500")

        config_path = get_config_path()
        ui.label(f"配置文件：{config_path}").classes("text-sm text-gray-500")

        config = load_config()

        # ── 当前配置展示 ──

        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("当前配置").classes("text-lg font-semibold")

            if not config:
                ui.label("配置文件为空或不存在。").classes("text-gray-600")
            else:
                ui.code(_format_config(config), language="toml").classes("w-full")

        # ── CLI 配置 ──

        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("转录 CLI 配置").classes("text-lg font-semibold")

            cli_config = config.get("cli", {})

            command = cli_config.get("transcribe_command", [])
            cwd = cli_config.get("transcribe_cwd", "")
            timeout = cli_config.get("transcribe_timeout_seconds", 14400)

            ui.label(
                f"命令：{' '.join(command) if command else '未配置'}"
            ).classes("text-sm mt-2")
            ui.label(f"工作目录：{cwd or '未配置'}").classes("text-sm")
            ui.label(f"超时：{timeout} 秒").classes("text-sm")

            if command:
                ui.label("✓ 转录 CLI 已配置").classes("text-green-600 text-sm mt-2")
            else:
                ui.label("✗ 转录 CLI 未配置").classes("text-red-600 text-sm mt-2")

        # ── Embedding 配置 ──

        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("Embedding 配置").classes("text-lg font-semibold")

            emb_config = config.get("embedding", {})

            emb_enabled = emb_config.get("enabled", False)
            emb_base_url = emb_config.get("base_url", "")
            emb_model = emb_config.get("model", "")
            emb_dimension = emb_config.get("dimension", 0)
            emb_api_key_env = emb_config.get("api_key_env", "")

            ui.label(f"启用：{'是' if emb_enabled else '否'}").classes("text-sm mt-2")
            ui.label(f"Base URL：{emb_base_url or '未配置'}").classes("text-sm")
            ui.label(f"模型：{emb_model or '未配置'}").classes("text-sm")
            ui.label(f"维度：{emb_dimension or '未配置'}").classes("text-sm")
            ui.label(
                f"API Key 环境变量：{emb_api_key_env or '未配置'}"
            ).classes("text-sm")

            if emb_enabled and emb_base_url and emb_model:
                ui.label("✓ Embedding 已配置").classes(
                    "text-green-600 text-sm mt-2"
                )
            else:
                ui.label("✗ Embedding 未配置或未启用").classes(
                    "text-orange-600 text-sm mt-2"
                )

        # ── LLM 总结配置 ──

        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("LLM 总结配置").classes("text-lg font-semibold")

            llm_config = config.get("llm", {}).get("summary", {})

            llm_enabled = llm_config.get("enabled", False)
            llm_base_url = llm_config.get("base_url", "")
            llm_model = llm_config.get("model", "")
            llm_api_key_env = llm_config.get("api_key_env", "")
            llm_max_input = llm_config.get("max_input_chars", 24000)
            llm_chunk = llm_config.get("chunk_chars", 6000)

            ui.label(f"启用：{'是' if llm_enabled else '否'}").classes("text-sm mt-2")
            ui.label(f"Base URL：{llm_base_url or '未配置'}").classes("text-sm")
            ui.label(f"模型：{llm_model or '未配置'}").classes("text-sm")
            ui.label(
                f"API Key 环境变量：{llm_api_key_env or '未配置'}"
            ).classes("text-sm")
            ui.label(f"最大输入字符：{llm_max_input}").classes("text-sm")
            ui.label(f"分段字符数：{llm_chunk}").classes("text-sm")

            if llm_enabled and llm_base_url and llm_model:
                ui.label("✓ LLM 总结已配置").classes("text-green-600 text-sm mt-2")
            else:
                ui.label("✗ LLM 总结未配置或未启用").classes(
                    "text-orange-600 text-sm mt-2"
                )

        # ── 索引管理 ──

        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("索引管理").classes("text-lg font-semibold")

            ui.label("重建索引会重新处理所有已识别的文本内容。").classes(
                "text-sm text-gray-600 mt-2"
            )
            ui.label(
                "重建向量索引会调用 Embedding API，已缓存的片段不会重复计费。"
            ).classes("text-sm text-orange-600 mt-1")

            with ui.row().classes("gap-3 mt-3"):
                rebuild_fts_button = ui.button("重建全文索引", icon="refresh")
                rebuild_vector_button = ui.button("重建向量索引", icon="hub")

        async def handle_rebuild_fts():
            rebuild_fts_button.disable()

            try:
                stats = await run.io_bound(rebuild_fulltext_index)

                ui.notify(
                    f"全文索引重建完成：{stats['sources']} 个来源，"
                    f"{stats['chunks']} 个片段",
                    type="positive",
                )
            except Exception as exc:
                ui.notify(str(exc), type="negative")
            finally:
                rebuild_fts_button.enable()

        async def handle_rebuild_vector():
            rebuild_vector_button.disable()

            try:
                stats = await run.io_bound(rebuild_vector_index)

                ui.notify(
                    f"向量索引重建完成：总片段 {stats['total_chunks']}，"
                    f"缓存命中 {stats['cache_hits']}，"
                    f"新调用 {stats['embedded']}",
                    type="positive",
                )
            except Exception as exc:
                ui.notify(str(exc), type="negative")
            finally:
                rebuild_vector_button.enable()

        rebuild_fts_button.on_click(handle_rebuild_fts)
        rebuild_vector_button.on_click(handle_rebuild_vector)


def _format_config(config: dict, parent: str = "") -> str:
    """将配置字典格式化为 TOML 风格文本（隐藏明文 API Key）。"""
    lines = []

    for key, value in config.items():
        if isinstance(value, dict):
            section = f"{parent}.{key}" if parent else key
            scalar_lines = _format_config(value, parent=section)

            if scalar_lines:
                lines.append(f"[{section}]")
                lines.append(scalar_lines)
        elif isinstance(value, list):
            lines.append(f"{key} = {value}")
        else:
            if "api_key" in key.lower() and "env" not in key.lower():
                lines.append(f"{key} = '***'")
            else:
                lines.append(f"{key} = {value!r}")

    return "\n".join(line for line in lines if line)
