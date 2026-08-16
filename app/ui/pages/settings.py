"""设置页：配置 UI 化（m7-config-ui）。

渐进式分层：高频配置用表单编辑并写回 .knowledge/config.toml；
CLI / App 等复杂配置只读展示，提供「打开 config.toml」按钮交由系统编辑器处理。
配置唯一真相来源始终是 config.toml，UI 只是其可视化编辑器。
"""

from __future__ import annotations

from nicegui import run, ui
from pathlib import Path

from app.services import config_service
from app.services.config_service import ConfigError
from app.state import state
from app.ui.layout import page_frame
from app.utils import open_file


@ui.page("/settings")
def settings_page() -> None:
    with page_frame("设置"):

        def handle_open_secrets() -> None:
            """打开 .knowledge/secrets.toml；不存在则创建含 [keys] 模板的文件。"""
            try:
                secrets_file = config_service.get_secrets_path()
            except ConfigError as exc:
                ui.notify(str(exc), type="negative")
                return

            if not secrets_file.exists():
                secrets_file.parent.mkdir(parents=True, exist_ok=True)
                secrets_file.write_text(
                    "# 本地密钥文件，请勿提交 Git\n"
                    "[keys]\n"
                    "# OPENAI_API_KEY = \"sk-xxxx\"\n",
                    encoding="utf-8",
                )
            open_file(str(secrets_file))
        if state.library_root is None:
            ui.label("未打开知识库").classes("text-xl")
            ui.link("去打开知识库", "/").classes("text-blue-600")
            return

        try:
            config = config_service.load_config()
            config_path = config_service.get_config_path()
            key_status = config_service.get_key_status(config)
        except ConfigError as exc:
            ui.label(str(exc)).classes("text-red-600 mt-4")
            return

        ui.label("设置").classes("text-2xl font-bold")
        ui.label(str(state.library_root)).classes("text-sm text-gray-500")

        # ── 配置文件信息 ──
        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("配置文件").classes("text-lg font-semibold")
            ui.label(str(config_path)).classes("text-sm text-gray-600 mt-2")

            with ui.row().classes("gap-3 mt-3"):
                ui.button(
                    "打开 config.toml",
                    icon="edit_document",
                    on_click=lambda: open_file(str(config_path)),
                )
                ui.button(
                    "编辑 secrets.toml",
                    icon="key",
                    on_click=handle_open_secrets,
                )
                ui.button(
                    "重新加载",
                    icon="refresh",
                    on_click=lambda: ui.navigate.to("/settings"),
                )

            ui.label(
                "API Key 也可放在 .knowledge/secrets.toml 的 [keys] 中，"
                "由 api_key_env 引用的名称查找，无需设置系统环境变量。"
            ).classes("text-xs text-gray-500 mt-3")

            if config_service.has_plain_api_key(config):
                ui.label(
                    "⚠ 检测到配置中存在明文 api_key。"
                    "建议删除 api_key，改用 api_key_env 引用环境变量。"
                ).classes("text-orange-600 text-sm mt-3")

        # 原始 Embedding 配置，用于判断是否需要重建向量索引
        original_embedding = config.get("embedding", {})
        original_model = str(original_embedding.get("model", ""))
        original_dimension = int(original_embedding.get("dimension", 0) or 0)

        llm_config = config.get("llm", {}).get("summary", {})
        embedding_config = original_embedding
        index_config = config.get("index", {})
        task_config = config.get("task", {})
        library_config = config.get("library", {})
        cli_config = config.get("cli", {})
        app_config = config.get("app", {})

        # ── LLM 总结配置 ──
        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("LLM 总结配置").classes("text-lg font-semibold")

            llm_enabled = ui.switch(
                "启用 LLM 总结", value=bool(llm_config.get("enabled", False))
            )
            llm_base_url = ui.input(
                "Base URL", value=str(llm_config.get("base_url", ""))
            ).classes("w-full")
            llm_model = ui.input(
                "Model", value=str(llm_config.get("model", ""))
            ).classes("w-full")
            llm_api_key_env = ui.input(
                "API Key 密钥名（api_key_env）",
                value=str(llm_config.get("api_key_env", "")),
            ).classes("w-full")
            _render_key_status(key_status, str(llm_config.get("api_key_env", "")))

            with ui.row().classes("w-full gap-3"):
                llm_temperature = ui.number(
                    "temperature",
                    value=float(llm_config.get("temperature", 0.2)),
                    min=0,
                    max=2,
                    step=0.1,
                ).classes("w-40")
                llm_max_tokens = ui.number(
                    "max_tokens",
                    value=int(llm_config.get("max_tokens", 2000)),
                    min=1,
                    step=1,
                ).classes("w-40")
                llm_timeout = ui.number(
                    "timeout 秒",
                    value=int(llm_config.get("timeout", 180)),
                    min=1,
                    step=1,
                ).classes("w-40")

            with ui.row().classes("w-full gap-3"):
                llm_max_input_chars = ui.number(
                    "max_input_chars",
                    value=int(llm_config.get("max_input_chars", 24000)),
                    min=1,
                    step=1000,
                ).classes("w-52")
                llm_chunk_chars = ui.number(
                    "chunk_chars",
                    value=int(llm_config.get("chunk_chars", 6000)),
                    min=1,
                    step=500,
                ).classes("w-52")

            with ui.row().classes("mt-3 gap-3"):
                test_llm_button = ui.button("测试 LLM API", icon="cable")

        # ── Embedding 配置 ──
        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("Embedding 配置").classes("text-lg font-semibold")

            embedding_enabled = ui.switch(
                "启用 Embedding", value=bool(embedding_config.get("enabled", False))
            )
            embedding_base_url = ui.input(
                "Base URL", value=str(embedding_config.get("base_url", ""))
            ).classes("w-full")
            embedding_model = ui.input(
                "Model", value=str(embedding_config.get("model", ""))
            ).classes("w-full")
            embedding_api_key_env = ui.input(
                "API Key 密钥名（api_key_env）",
                value=str(embedding_config.get("api_key_env", "")),
            ).classes("w-full")
            _render_key_status(
                key_status, str(embedding_config.get("api_key_env", ""))
            )

            with ui.row().classes("w-full gap-3"):
                embedding_dimension = ui.number(
                    "dimension",
                    value=int(embedding_config.get("dimension", 0) or 0),
                    min=1,
                    step=1,
                ).classes("w-40")
                embedding_batch_size = ui.number(
                    "batch_size",
                    value=int(embedding_config.get("batch_size", 16) or 16),
                    min=1,
                    step=1,
                ).classes("w-40")
                embedding_timeout = ui.number(
                    "timeout 秒",
                    value=int(embedding_config.get("timeout", 120) or 120),
                    min=1,
                    step=1,
                ).classes("w-40")

            ui.label(
                "注意：修改 Embedding model 或 dimension 后需要重建向量索引。"
            ).classes("text-orange-600 text-sm mt-2")

            with ui.row().classes("mt-3 gap-3"):
                test_embedding_button = ui.button(
                    "测试 Embedding API", icon="cable"
                )

        # ── 索引配置 ──
        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("索引配置").classes("text-lg font-semibold")

            with ui.row().classes("w-full gap-3"):
                chunk_max_chars = ui.number(
                    "chunk_max_chars",
                    value=int(index_config.get("chunk_max_chars", 800)),
                    min=100,
                    step=100,
                ).classes("w-48")
                chunk_overlap = ui.number(
                    "chunk_overlap",
                    value=int(index_config.get("chunk_overlap", 100)),
                    min=0,
                    step=10,
                ).classes("w-48")
                rebuild_batch_size = ui.number(
                    "rebuild_batch_size",
                    value=int(index_config.get("rebuild_batch_size", 100)),
                    min=1,
                    step=10,
                ).classes("w-48")

            ui.label("chunk_overlap 必须小于 chunk_max_chars。").classes(
                "text-xs text-gray-500 mt-2"
            )

        # ── 任务配置 ──
        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("任务配置").classes("text-lg font-semibold")

            with ui.row().classes("w-full gap-3"):
                max_workers = ui.number(
                    "max_workers",
                    value=int(task_config.get("max_workers", 1)),
                    min=1,
                    max=8,
                    step=1,
                ).classes("w-40")
                task_timeout_seconds = ui.number(
                    "task_timeout_seconds",
                    value=int(task_config.get("task_timeout_seconds", 7200)),
                    min=1,
                    step=60,
                ).classes("w-56")

        # ── 扫描配置 ──
        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("扫描配置").classes("text-lg font-semibold")
            scan_on_startup = ui.switch(
                "启动时扫描",
                value=bool(library_config.get("scan_on_startup", True)),
            )

            ignore_list = library_config.get("ignore", [])
            ui.label("当前忽略目录").classes("text-sm font-semibold mt-3")
            if ignore_list:
                ui.code("\n".join(ignore_list)).classes("w-full")
            else:
                ui.label("未配置忽略目录").classes("text-sm text-gray-600")
            ui.label(
                "忽略目录列表较复杂，请通过 config.toml 修改。"
            ).classes("text-xs text-gray-500 mt-2")

        # ── 极客直编区：CLI / App 只读展示 ──
        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("转录 CLI 配置（只读）").classes("text-lg font-semibold")
            transcribe_command = cli_config.get("transcribe_command", [])
            if transcribe_command:
                ui.code(str(transcribe_command)).classes("w-full")
            else:
                ui.label("未配置").classes("text-sm text-gray-600")
            ui.label(
                "CLI 命令模板涉及路径与参数格式，请通过 config.toml 修改。"
            ).classes("text-xs text-gray-500 mt-2")

        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("应用配置（只读）").classes("text-lg font-semibold")
            ui.label(
                f"host: {app_config.get('host', '127.0.0.1')}"
            ).classes("text-sm mt-2")
            ui.label(f"port: {app_config.get('port', 8765)}").classes("text-sm")
            ui.label(
                f"log_level: {app_config.get('log_level', 'INFO')}"
            ).classes("text-sm")
            ui.label(
                "host / port 修改后需重启应用，请通过 config.toml 修改。"
            ).classes("text-xs text-gray-500 mt-2")

        # ── 保存 ──
        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("保存配置").classes("text-lg font-semibold")
            ui.label("保存后会写回 config.toml，未编辑的字段保持不变。").classes(
                "text-sm text-gray-600 mt-2"
            )
            with ui.row().classes("mt-3 gap-3"):
                save_button = ui.button("保存配置", icon="save").props(
                    "color=primary"
                )

        # ── 索引管理 ──
        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("索引管理").classes("text-lg font-semibold")
            ui.label("重建全文索引会重新处理所有已识别的文本内容。").classes(
                "text-sm text-gray-600 mt-2"
            )
            ui.label(
                "重建向量索引会调用 Embedding API，已缓存的片段不会重复计费。"
            ).classes("text-sm text-orange-600 mt-1")
            with ui.row().classes("gap-3 mt-3"):
                rebuild_fts_button = ui.button(
                    "重建全文索引", icon="refresh"
                )
                rebuild_vector_button = ui.button(
                    "重建向量索引", icon="hub"
                )

        # ── 表单值收集 ──
        def build_patch() -> dict:
            return {
                "llm": {
                    "summary": {
                        "enabled": bool(llm_enabled.value),
                        "base_url": str(llm_base_url.value or "").strip(),
                        "model": str(llm_model.value or "").strip(),
                        "api_key_env": str(llm_api_key_env.value or "").strip(),
                        "temperature": float(llm_temperature.value or 0.2),
                        "max_tokens": int(llm_max_tokens.value or 2000),
                        "timeout": int(llm_timeout.value or 180),
                        "max_input_chars": int(llm_max_input_chars.value or 24000),
                        "chunk_chars": int(llm_chunk_chars.value or 6000),
                    }
                },
                "embedding": {
                    "enabled": bool(embedding_enabled.value),
                    "base_url": str(embedding_base_url.value or "").strip(),
                    "model": str(embedding_model.value or "").strip(),
                    "api_key_env": str(embedding_api_key_env.value or "").strip(),
                    "dimension": int(embedding_dimension.value or 0),
                    "batch_size": int(embedding_batch_size.value or 16),
                    "timeout": int(embedding_timeout.value or 120),
                },
                "index": {
                    "chunk_max_chars": int(chunk_max_chars.value or 800),
                    "chunk_overlap": int(chunk_overlap.value or 100),
                    "rebuild_batch_size": int(rebuild_batch_size.value or 100),
                },
                "task": {
                    "max_workers": int(max_workers.value or 1),
                    "task_timeout_seconds": int(task_timeout_seconds.value or 7200),
                },
                "library": {
                    "scan_on_startup": bool(scan_on_startup.value),
                },
            }

        def embedding_index_changed(patch: dict) -> bool:
            new_model = str(patch["embedding"]["model"])
            new_dimension = int(patch["embedding"]["dimension"])
            return (
                new_model != original_model
                or new_dimension != original_dimension
            )

        async def handle_save():
            save_button.disable()
            patch = build_patch()
            need_rebuild_vector = embedding_index_changed(patch)

            try:
                await run.io_bound(config_service.save_config, patch)
                ui.notify("配置已保存到 config.toml", type="positive")

                if need_rebuild_vector:
                    ui.notify(
                        "Embedding model 或 dimension 已变化，请重建向量索引。",
                        type="warning",
                        timeout=8000,
                    )
            except Exception as exc:
                ui.notify(str(exc), type="negative")
            finally:
                save_button.enable()

        async def handle_test_llm():
            test_llm_button.disable()
            try:
                result = await run.io_bound(
                    config_service.test_connection, "llm", build_patch()
                )
                if result.get("ok"):
                    ui.notify(result.get("message", "连接成功"), type="positive")
                else:
                    ui.notify(result.get("message", "连接失败"), type="negative")
            except Exception as exc:
                ui.notify(str(exc), type="negative")
            finally:
                test_llm_button.enable()

        async def handle_test_embedding():
            test_embedding_button.disable()
            try:
                result = await run.io_bound(
                    config_service.test_connection,
                    "embedding",
                    build_patch(),
                )
                if result.get("ok"):
                    ui.notify(result.get("message", "连接成功"), type="positive")
                else:
                    ui.notify(result.get("message", "连接失败"), type="negative")
            except Exception as exc:
                ui.notify(str(exc), type="negative")
            finally:
                test_embedding_button.enable()

        async def handle_rebuild_fts():
            rebuild_fts_button.disable()
            try:
                from app.services.index_service import rebuild_fulltext_index

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
                from app.services.vector_service import rebuild_vector_index

                stats = await run.io_bound(rebuild_vector_index)
                ui.notify(
                    f"向量索引重建完成：总片段 {stats['total_chunks']}，"
                    f"缓存命中 {stats['cache_hits']}，新调用 {stats['embedded']}",
                    type="positive",
                )
            except Exception as exc:
                ui.notify(str(exc), type="negative")
            finally:
                rebuild_vector_button.enable()

        save_button.on_click(handle_save)
        test_llm_button.on_click(handle_test_llm)
        test_embedding_button.on_click(handle_test_embedding)
        rebuild_fts_button.on_click(handle_rebuild_fts)
        rebuild_vector_button.on_click(handle_rebuild_vector)


def _render_key_status(key_status: dict[str, dict], key_name: str) -> None:
    """展示密钥名称是否已解析，以及来源（环境变量 / secrets.toml）。"""
    if not key_name:
        ui.label("未配置密钥名称（api_key_env）").classes(
            "text-xs text-gray-500 mt-1"
        )
        return

    info = key_status.get(key_name, {"found": False, "source": ""})

    if info.get("found"):
        source = info.get("source", "")
        ui.label(f"✓ {key_name} 已设置，来源：{source}").classes(
            "text-green-600 text-xs mt-1"
        )
    else:
        ui.label(
            f"✗ {key_name} 未设置（请设置环境变量，"
            "或在 .knowledge/secrets.toml 的 [keys] 中配置）"
        ).classes("text-red-600 text-xs mt-1")
