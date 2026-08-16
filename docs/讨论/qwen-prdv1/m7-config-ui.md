下面给你一份类似 `m7.md` 的实施文档，建议保存为：

```text
docs/讨论/m7-config-ui.md
```

这份文档承接 M7 的“设置页只读展示 + 索引重建”，目标是把知识库配置升级为**可在界面中安全修改的配置 UI**。

---

# M7 补完（m7-config-ui）：配置 UI 化实施文档

> 前置条件：M7 已完成，设置页可以只读展示 CLI / Embedding / LLM 配置，并支持重建全文索引和向量索引。
>
> 本阶段目标：
>
> 1. 设置页支持修改部分核心配置。
> 2. 修改结果写回 `.knowledge/config.toml`。
> 3. 保持“文件即真相”：UI 只是 TOML 的可视化编辑器，不把配置存进 SQLite。
> 4. 支持环境变量状态检测。
> 5. 支持 LLM / Embedding API 连通性测试。
> 6. 修改 Embedding 模型或维度时提示需要重建向量索引。

---

## 1. 本阶段目标

本阶段（M7 配置 UI 化补完）的核心目标是：

```text
设置页从“只读展示配置”
升级为
“部分配置可视化编辑 + 安全保存 + API 测试 + 索引重建提醒”
```

具体包括：

1. LLM 总结配置可视化编辑。
2. Embedding 配置可视化编辑。
3. 索引分块配置可视化编辑。
4. 任务配置可视化编辑。
5. 知识库扫描基础配置可视化编辑。
6. CLI 配置保持只读展示，提供打开 `config.toml` 的入口。
7. 保存配置时写回 `.knowledge/config.toml`。
8. 保存前做基础校验。
9. 检测 API Key 环境变量是否已设置。
10. 提供 LLM / Embedding API 测试按钮。
11. 修改 Embedding model 或 dimension 后提示重建向量索引。

---

## 2. 本阶段明确不做

为了控制复杂度，本阶段不做全量配置 UI 化。

以下配置暂不提供完整 UI 编辑：

1. `cli.transcribe_command`
2. `cli.parse_command`
3. `library.ignore` 完整列表编辑
4. `app.host`
5. `app.port`
6. `app.open_browser`
7. `provider` 复杂切换
8. 明文 API Key 输入
9. Prompt 模板复杂编辑器
10. 多知识库配置管理

其中：

- CLI 命令模板较复杂，直接在 UI 中编辑容易出错。
- `app.host` / `app.port` 修改后需要重启服务，第一阶段只展示。
- API Key 继续只通过环境变量读取，UI 不提供明文输入框。

---

## 3. 配置 UI 化原则

### 3.1 UI 只是 config.toml 的可视化编辑器

所有 UI 修改最终都必须写回：

```text
<知识库目录>/.knowledge/config.toml
```

不允许：

```text
UI 修改配置 → 写入 SQLite
```

必须保持：

```text
UI 表单
  ↓
patch dict
  ↓
读取原 config.toml
  ↓
deep merge
  ↓
校验
  ↓
写回 config.toml
```

这样可以保证用户仍然可以直接编辑 `config.toml`，不会被 UI 锁死。

---

### 3.2 部分支持，而不是全量支持

配置分为两类：

#### 高频表单区

这些配置适合 UI 编辑：

```text
[llm.summary]
enabled
base_url
model
api_key_env
temperature
max_tokens
timeout
max_input_chars
chunk_chars

[embedding]
enabled
base_url
model
api_key_env
dimension
batch_size
timeout

[index]
chunk_max_chars
chunk_overlap
rebuild_batch_size

[task]
max_workers
task_timeout_seconds

[library]
scan_on_startup
```

#### 极客直编区

这些配置只在 UI 中展示，不提供完整编辑：

```text
[app]
host
port
open_browser
log_level

[cli]
transcribe_command
parse_command

[library]
ignore

[embedding]
api_key，如果存在则只警告，不编辑

[llm.summary]
api_key，如果存在则只警告，不编辑
```

UI 中提供：

```text
打开 config.toml
```

按钮，让用户用系统默认编辑器修改。

---

### 3.3 API Key 安全原则

UI 不提供明文 API Key 输入框。

配置中只允许修改：

```toml
api_key_env = "OPENAI_API_KEY"
```

实际 Key 从系统环境变量读取：

```text
OPENAI_API_KEY
```

如果检测到配置里已经有明文：

```toml
api_key = "sk-xxx"
```

UI 应提示：

```text
检测到配置中存在明文 API Key。
建议删除 api_key，改为使用 api_key_env 引用环境变量。
```

但 UI 不主动展示、编辑或保存明文 Key。

---

## 4. 新增依赖

Python 3.11+ 内置 `tomllib`，可以读取 TOML。

但写入 TOML 需要额外依赖：

```bash
uv add tomli-w
```

如果项目还没有 `httpx`，也安装：

```bash
uv add httpx
```

---

## 5. 新增后端服务：config_service

新增文件：

```text
app/services/config_service.py
```

职责：

1. 读取 `.knowledge/config.toml`
2. 合并 UI 提交的配置 patch
3. 校验配置
4. 写回 `.knowledge/config.toml`
5. 检测环境变量是否存在
6. 测试 LLM / Embedding API 连通性

---

### 5.1 config_service 基础代码

```python
# app/services/config_service.py

from __future__ import annotations

import os
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any

import httpx
import tomli_w

from app.state import state


class ConfigError(ValueError):
    """配置读取、校验或保存失败。"""


def get_config_path() -> Path:
    """
    获取当前知识库配置文件路径。
    """
    if state.library_root is None:
        raise ConfigError("未打开知识库")

    return Path(state.library_root) / ".knowledge" / "config.toml"


def load_config() -> dict[str, Any]:
    """
    读取当前知识库配置。
    如果配置文件不存在，返回空 dict。
    """
    path = get_config_path()

    if not path.exists():
        return {}

    with path.open("rb") as f:
        return tomllib.load(f)


def get_settings_view() -> dict[str, Any]:
    """
    返回设置页需要的数据。
    """
    config = load_config()

    return {
        "config": config,
        "env_status": get_env_status(config),
        "config_path": str(get_config_path()),
    }


def save_config(patch: dict[str, Any]) -> dict[str, Any]:
    """
    将 UI 提交的 patch 合并到原配置中，并写回 config.toml。
    """
    current_config = load_config()
    merged_config = _deep_merge(current_config, patch)
    cleaned_config = _clean_none(merged_config)
    validated_config = validate_config(cleaned_config)

    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("wb") as f:
        tomli_w.dump(validated_config, f)

    return validated_config


def _deep_merge(
    base: dict[str, Any],
    patch: dict[str, Any],
) -> dict[str, Any]:
    """
    递归合并配置。
    patch 中的值优先，但保留 base 中未被编辑的字段。
    """
    result = deepcopy(base)

    for key, value in patch.items():
        if (
            isinstance(value, dict)
            and isinstance(result.get(key), dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result


def _clean_none(value: Any) -> Any:
    """
    tomli_w 不支持 None。
    保存前删除 None 值。
    """
    if isinstance(value, dict):
        return {
            k: _clean_none(v)
            for k, v in value.items()
            if v is not None
        }

    if isinstance(value, list):
        return [
            _clean_none(item)
            for item in value
            if item is not None
        ]

    return value
```

---

### 5.2 配置校验代码

继续写在 `config_service.py`：

```python
def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    对配置做基础校验。
    校验失败时抛出 ConfigError。
    """
    cfg = deepcopy(config)

    # ── task ──
    task = cfg.get("task", {})
    if task:
        max_workers = int(task.get("max_workers", 1))
        if max_workers < 1:
            raise ConfigError("task.max_workers 必须大于等于 1")

        task_timeout_seconds = int(task.get("task_timeout_seconds", 7200))
        if task_timeout_seconds < 1:
            raise ConfigError("task.task_timeout_seconds 必须大于等于 1")

    # ── index ──
    index = cfg.get("index", {})
    if index:
        chunk_max_chars = int(index.get("chunk_max_chars", 800))
        chunk_overlap = int(index.get("chunk_overlap", 100))

        if chunk_max_chars <= 0:
            raise ConfigError("index.chunk_max_chars 必须大于 0")

        if chunk_overlap < 0:
            raise ConfigError("index.chunk_overlap 不能小于 0")

        if chunk_overlap >= chunk_max_chars:
            raise ConfigError("index.chunk_overlap 必须小于 chunk_max_chars")

        rebuild_batch_size = int(index.get("rebuild_batch_size", 100))
        if rebuild_batch_size <= 0:
            raise ConfigError("index.rebuild_batch_size 必须大于 0")

    # ── embedding ──
    embedding = cfg.get("embedding", {})
    if embedding.get("enabled"):
        if not str(embedding.get("base_url", "")).strip():
            raise ConfigError("Embedding 已启用，但 base_url 为空")

        if not str(embedding.get("model", "")).strip():
            raise ConfigError("Embedding 已启用，但 model 为空")

        dimension = int(embedding.get("dimension", 0))
        if dimension <= 0:
            raise ConfigError("Embedding dimension 必须大于 0")

        batch_size = int(embedding.get("batch_size", 32))
        if batch_size <= 0:
            raise ConfigError("Embedding batch_size 必须大于 0")

        timeout = int(embedding.get("timeout", 120))
        if timeout <= 0:
            raise ConfigError("Embedding timeout 必须大于 0")

    # ── llm.summary ──
    llm = cfg.get("llm", {})
    summary = llm.get("summary", {})

    if summary.get("enabled"):
        if not str(summary.get("base_url", "")).strip():
            raise ConfigError("LLM 总结已启用，但 base_url 为空")

        if not str(summary.get("model", "")).strip():
            raise ConfigError("LLM 总结已启用，但 model 为空")

        max_tokens = int(summary.get("max_tokens", 2000))
        if max_tokens <= 0:
            raise ConfigError("LLM max_tokens 必须大于 0")

        timeout = int(summary.get("timeout", 180))
        if timeout <= 0:
            raise ConfigError("LLM timeout 必须大于 0")

        max_input_chars = int(summary.get("max_input_chars", 24000))
        chunk_chars = int(summary.get("chunk_chars", 6000))

        if max_input_chars <= 0:
            raise ConfigError("LLM max_input_chars 必须大于 0")

        if chunk_chars <= 0:
            raise ConfigError("LLM chunk_chars 必须大于 0")

        if chunk_chars > max_input_chars:
            raise ConfigError("LLM chunk_chars 不应大于 max_input_chars")

    return cfg
```

---

### 5.3 环境变量状态检测

继续写在 `config_service.py`：

```python
def get_env_status(config: dict[str, Any] | None = None) -> dict[str, bool]:
    """
    检测配置中引用的环境变量是否存在。
    例如：
    {
        "OPENAI_API_KEY": True
    }
    """
    if config is None:
        config = load_config()

    env_names: set[str] = set()

    embedding = config.get("embedding", {})
    if embedding.get("api_key_env"):
        env_names.add(str(embedding["api_key_env"]))

    llm_summary = config.get("llm", {}).get("summary", {})
    if llm_summary.get("api_key_env"):
        env_names.add(str(llm_summary["api_key_env"]))

    result: dict[str, bool] = {}

    for env_name in env_names:
        result[env_name] = bool(os.getenv(env_name))

    return result


def has_plain_api_key(config: dict[str, Any] | None = None) -> bool:
    """
    检测配置中是否存在明文 api_key。
    UI 不编辑明文 Key，只做警告。
    """
    if config is None:
        config = load_config()

    embedding_key = config.get("embedding", {}).get("api_key")
    llm_key = config.get("llm", {}).get("summary", {}).get("api_key")

    return bool(embedding_key or llm_key)
```

---

## 6. API 连通性测试

继续写在 `config_service.py`。

这里的测试逻辑：

- Embedding：调用 `/embeddings`
- LLM：优先调用 `/models`
  - 如果 `/models` 不支持，再尝试 `/chat/completions`

```python
def test_connection(
    kind: str,
    override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    测试 LLM 或 Embedding API 连通性。

    kind:
        - llm
        - embedding

    override:
        前端当前表单内容。
        测试时优先使用表单值，而不是已保存配置。
    """
    config = load_config()

    if override:
        config = _deep_merge(config, override)

    if kind == "embedding":
        return _test_embedding_connection(config)

    if kind == "llm":
        return _test_llm_connection(config)

    return {
        "ok": False,
        "message": f"不支持的测试类型：{kind}",
    }


def _get_api_key(section: dict[str, Any]) -> tuple[str, str]:
    """
    根据 api_key_env 获取环境变量中的 API Key。
    返回：
        env_name, api_key
    """
    env_name = str(section.get("api_key_env", "")).strip()

    if not env_name:
        return "", ""

    return env_name, os.getenv(env_name, "")


def _test_embedding_connection(config: dict[str, Any]) -> dict[str, Any]:
    embedding = config.get("embedding", {})

    if not embedding.get("enabled"):
        return {
            "ok": False,
            "message": "Embedding 未启用",
        }

    base_url = str(embedding.get("base_url", "")).strip().rstrip("/")
    model = str(embedding.get("model", "")).strip()

    if not base_url:
        return {
            "ok": False,
            "message": "Embedding base_url 为空",
        }

    if not model:
        return {
            "ok": False,
            "message": "Embedding model 为空",
        }

    env_name, api_key = _get_api_key(embedding)

    if env_name and not api_key:
        return {
            "ok": False,
            "message": f"环境变量 {env_name} 未设置",
        }

    headers = {}

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    url = f"{base_url}/embeddings"

    payload = {
        "model": model,
        "input": ["ping"],
    }

    try:
        response = httpx.post(
            url,
            headers=headers,
            json=payload,
            timeout=15,
        )

        if response.status_code == 200:
            return {
                "ok": True,
                "message": f"Embedding API 连接成功：{model}",
            }

        return {
            "ok": False,
            "message": (
                f"Embedding API 返回 HTTP {response.status_code}："
                f"{response.text[:200]}"
            ),
        }

    except Exception as exc:
        return {
            "ok": False,
            "message": f"Embedding API 请求失败：{exc}",
        }


def _test_llm_connection(config: dict[str, Any]) -> dict[str, Any]:
    summary = config.get("llm", {}).get("summary", {})

    if not summary.get("enabled"):
        return {
            "ok": False,
            "message": "LLM 总结未启用",
        }

    base_url = str(summary.get("base_url", "")).strip().rstrip("/")
    model = str(summary.get("model", "")).strip()

    if not base_url:
        return {
            "ok": False,
            "message": "LLM base_url 为空",
        }

    if not model:
        return {
            "ok": False,
            "message": "LLM model 为空",
        }

    env_name, api_key = _get_api_key(summary)

    if env_name and not api_key:
        return {
            "ok": False,
            "message": f"环境变量 {env_name} 未设置",
        }

    headers = {}

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # 优先尝试 /models
    try:
        response = httpx.get(
            f"{base_url}/models",
            headers=headers,
            timeout=15,
        )

        if response.status_code == 200:
            return {
                "ok": True,
                "message": "LLM API 连接成功",
            }

        if response.status_code in {401, 403}:
            return {
                "ok": False,
                "message": (
                    f"LLM API 认证失败：HTTP {response.status_code}"
                ),
            }

    except Exception:
        pass

    # 如果 /models 不支持，尝试 chat/completions
    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "ping",
                    }
                ],
                "max_tokens": 1,
            },
            timeout=15,
        )

        if response.status_code == 200:
            return {
                "ok": True,
                "message": f"LLM API 连接成功：{model}",
            }

        return {
            "ok": False,
            "message": (
                f"LLM API 返回 HTTP {response.status_code}："
                f"{response.text[:200]}"
            ),
        }

    except Exception as exc:
        return {
            "ok": False,
            "message": f"LLM API 请求失败：{exc}",
        }
```

---

## 7. 新增 Settings API

修改或新增：

```text
app/api/settings.py
```

如果项目已有该文件，则替换为下面内容。

```python
# app/api/settings.py

from fastapi import APIRouter, FastAPI, HTTPException

from app.services import config_service


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings():
    """
    获取当前配置、环境变量状态和配置文件路径。
    """
    return config_service.get_settings_view()


@router.put("")
def put_settings(payload: dict):
    """
    保存配置。
    payload 是前端提交的配置 patch。
    """
    try:
        return config_service.save_config(payload)
    except config_service.ConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/test-connection")
def test_connection(payload: dict):
    """
    测试 LLM 或 Embedding API 连通性。

    请求体示例：
    {
        "kind": "embedding",
        "override": {
            "embedding": {
                "base_url": "...",
                "model": "...",
                "api_key_env": "OPENAI_API_KEY"
            }
        }
    }
    """
    kind = payload.get("kind")
    override = payload.get("override", {})

    if kind not in {"llm", "embedding"}:
        raise HTTPException(
            status_code=400,
            detail="kind 必须是 llm 或 embedding",
        )

    return config_service.test_connection(kind, override)


def register_settings_api(app: FastAPI) -> None:
    """
    注册设置 API。
    """
    app.include_router(router)
```

---

## 8. 更新 main.py

在 `main.py` 中注册 Settings API。

```python
# app/main.py

from nicegui import ui

from app.api.library import register_library_api
from app.api.settings import register_settings_api
from app.ui.pages import (
    asset_detail_page,
    assets_page,
    home_page,
    search_page,
    settings_page,
    tasks_page,
)  # noqa: F401

from nicegui import app

register_library_api(app)
register_settings_api(app)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Local Knowledge Hub",
        host="127.0.0.1",
        port=8765,
        show=False,
        reload=False,
    )
```

---

## 9. 替换设置页

替换：

```text
app/ui/pages/settings.py
```

这一版设置页包括：

1. 当前配置文件路径展示。
2. 明文 API Key 警告。
3. LLM 总结配置表单。
4. Embedding 配置表单。
5. 索引配置表单。
6. 任务配置表单。
7. 扫描配置表单。
8. CLI 配置只读展示。
9. 应用配置只读展示。
10. 重建全文索引。
11. 重建向量索引。
12. 打开 `config.toml`。

---

### 9.1 settings.py 完整示例

```python
# app/ui/pages/settings.py

from nicegui import run, ui

from app.services import config_service
from app.services.config_service import ConfigError
from app.state import state
from app.ui.layout import page_header, require_library
from app.utils import open_file


@ui.page("/settings")
def settings_page():
    page_header("设置")

    if not require_library():
        return

    try:
        config = config_service.load_config()
        config_path = config_service.get_config_path()
        env_status = config_service.get_env_status(config)
    except ConfigError as exc:
        ui.label(str(exc)).classes("text-red-600 mt-4")
        return

    # ── 顶部信息 ──
    with ui.card().classes("w-full p-4 mt-4"):
        ui.label("配置文件").classes("text-lg font-semibold")
        ui.label(str(config_path)).classes("text-sm text-gray-600 mt-2")

        with ui.row().classes("gap-3 mt-3"):
            ui.button(
                "打开 config.toml",
                on_click=lambda: open_file(str(config_path)),
            )

            ui.button(
                "重新加载配置",
                on_click=lambda: ui.navigate.to("/settings"),
            )

        if config_service.has_plain_api_key(config):
            ui.label(
                "检测到配置中存在明文 api_key。"
                "建议删除 api_key，改为使用 api_key_env 引用环境变量。"
            ).classes("text-orange-600 text-sm mt-3")

    # ── 默认值准备 ──
    llm_config = config.get("llm", {}).get("summary", {})
    embedding_config = config.get("embedding", {})
    index_config = config.get("index", {})
    task_config = config.get("task", {})
    library_config = config.get("library", {})
    cli_config = config.get("cli", {})
    app_config = config.get("app", {})

    # 原始 Embedding 配置，用于判断是否需要重建向量索引
    original_embedding_model = str(embedding_config.get("model", ""))
    original_embedding_dimension = int(embedding_config.get("dimension", 0))

    # ── LLM 总结配置 ──
    with ui.card().classes("w-full p-4 mt-4"):
        ui.label("LLM 总结配置").classes("text-lg font-semibold")

        llm_enabled = ui.switch(
            "启用 LLM 总结",
            value=bool(llm_config.get("enabled", False)),
        )

        llm_base_url = ui.input(
            "Base URL",
            value=str(llm_config.get("base_url", "")),
        ).classes("w-full")

        llm_model = ui.input(
            "Model",
            value=str(llm_config.get("model", "")),
        ).classes("w-full")

        llm_api_key_env = ui.input(
            "API Key 环境变量名",
            value=str(llm_config.get("api_key_env", "")),
        ).classes("w-full")

        _render_env_status(
            env_status,
            str(llm_config.get("api_key_env", "")),
        )

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
            test_llm_button = ui.button("测试 LLM API")

    # ── Embedding 配置 ──
    with ui.card().classes("w-full p-4 mt-4"):
        ui.label("Embedding 配置").classes("text-lg font-semibold")

        embedding_enabled = ui.switch(
            "启用 Embedding",
            value=bool(embedding_config.get("enabled", False)),
        )

        embedding_base_url = ui.input(
            "Base URL",
            value=str(embedding_config.get("base_url", "")),
        ).classes("w-full")

        embedding_model = ui.input(
            "Model",
            value=str(embedding_config.get("model", "")),
        ).classes("w-full")

        embedding_api_key_env = ui.input(
            "API Key 环境变量名",
            value=str(embedding_config.get("api_key_env", "")),
        ).classes("w-full")

        _render_env_status(
            env_status,
            str(embedding_config.get("api_key_env", "")),
        )

        with ui.row().classes("w-full gap-3"):
            embedding_dimension = ui.number(
                "dimension",
                value=int(embedding_config.get("dimension", 0)),
                min=1,
                step=1,
            ).classes("w-40")

            embedding_batch_size = ui.number(
                "batch_size",
                value=int(embedding_config.get("batch_size", 32)),
                min=1,
                step=1,
            ).classes("w-40")

            embedding_timeout = ui.number(
                "timeout 秒",
                value=int(embedding_config.get("timeout", 120)),
                min=1,
                step=1,
            ).classes("w-40")

        ui.label(
            "注意：修改 Embedding model 或 dimension 后，"
            "需要重建向量索引。"
        ).classes("text-orange-600 text-sm mt-2")

        with ui.row().classes("mt-3 gap-3"):
            test_embedding_button = ui.button("测试 Embedding API")

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

        ui.label(
            "chunk_overlap 必须小于 chunk_max_chars。"
        ).classes("text-xs text-gray-500 mt-2")

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
            "忽略目录列表较复杂，当前版本请通过 config.toml 修改。"
        ).classes("text-xs text-gray-500 mt-2")

    # ── CLI 配置，只读展示 ──
    with ui.card().classes("w-full p-4 mt-4"):
        ui.label("CLI 配置").classes("text-lg font-semibold")

        transcribe_command = cli_config.get("transcribe_command", "")
        parse_command = cli_config.get("parse_command", "")

        ui.label("transcribe_command").classes("text-sm font-semibold mt-3")

        if transcribe_command:
            ui.code(str(transcribe_command)).classes("w-full")
        else:
            ui.label("未配置").classes("text-sm text-gray-600")

        ui.label("parse_command").classes("text-sm font-semibold mt-3")

        if parse_command:
            ui.code(str(parse_command)).classes("w-full")
        else:
            ui.label("未配置").classes("text-sm text-gray-600")

        ui.label(
            "CLI 命令模板涉及路径和参数格式，"
            "当前版本请通过 config.toml 修改。"
        ).classes("text-xs text-gray-500 mt-2")

    # ── 应用配置，只读展示 ──
    with ui.card().classes("w-full p-4 mt-4"):
        ui.label("应用配置").classes("text-lg font-semibold")

        ui.label(
            f"host: {app_config.get('host', '127.0.0.1')}"
        ).classes("text-sm mt-2")

        ui.label(
            f"port: {app_config.get('port', 8765)}"
        ).classes("text-sm")

        ui.label(
            f"log_level: {app_config.get('log_level', 'INFO')}"
        ).classes("text-sm")

        ui.label(
            "host / port 修改后需要重启应用，"
            "当前版本请通过 config.toml 修改。"
        ).classes("text-xs text-gray-500 mt-2")

    # ── 保存按钮 ──
    with ui.card().classes("w-full p-4 mt-4"):
        ui.label("保存配置").classes("text-lg font-semibold")

        ui.label(
            "保存后会写回 config.toml。"
        ).classes("text-sm text-gray-600 mt-2")

        with ui.row().classes("mt-3 gap-3"):
            save_button = ui.button("保存配置").props("color=primary")

    # ── 索引管理，延续 M7 ──
    with ui.card().classes("w-full p-4 mt-4"):
        ui.label("索引管理").classes("text-lg font-semibold")

        ui.label(
            "重建全文索引会重新处理所有已识别的文本内容。"
        ).classes("text-sm text-gray-600 mt-2")

        ui.label(
            "重建向量索引会调用 Embedding API，可能产生费用。"
        ).classes("text-sm text-orange-600 mt-1")

        with ui.row().classes("gap-3 mt-3"):
            rebuild_fts_button = ui.button("重建全文索引")
            rebuild_vector_button = ui.button("重建向量索引")

    # ── 工具函数 ──

    def build_patch() -> dict:
        """
        收集当前表单值，生成配置 patch。
        """
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
                "batch_size": int(embedding_batch_size.value or 32),
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
        """
        判断 Embedding model 或 dimension 是否发生变化。
        """
        new_model = str(patch["embedding"]["model"])
        new_dimension = int(patch["embedding"]["dimension"])

        return (
            new_model != original_embedding_model
            or new_dimension != original_embedding_dimension
        )

    async def handle_save():
        save_button.disable()

        patch = build_patch()
        need_rebuild_vector = embedding_index_changed(patch)

        try:
            await run.io_bound(
                config_service.save_config,
                patch,
            )

            ui.notify(
                "配置已保存到 config.toml",
                type="positive",
            )

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
            patch = build_patch()

            result = await run.io_bound(
                config_service.test_connection,
                "llm",
                patch,
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
            patch = build_patch()

            result = await run.io_bound(
                config_service.test_connection,
                "embedding",
                patch,
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
                f"缓存命中 {stats['cache_hits']}，"
                f"新调用 {stats['embedded']}",
                type="positive",
            )

        except Exception as exc:
            ui.notify(str(exc), type="negative")

        finally:
            rebuild_vector_button.enable()

    # ── 绑定事件 ──
    save_button.on_click(handle_save)
    test_llm_button.on_click(handle_test_llm)
    test_embedding_button.on_click(handle_test_embedding)
    rebuild_fts_button.on_click(handle_rebuild_fts)
    rebuild_vector_button.on_click(handle_rebuild_vector)


def _render_env_status(env_status: dict[str, bool], env_name: str):
    """
    展示环境变量是否存在。
    """
    if not env_name:
        ui.label("未配置 API Key 环境变量名").classes(
            "text-xs text-gray-500 mt-1"
        )
        return

    if env_status.get(env_name):
        ui.label(f"✓ 环境变量 {env_name} 已设置").classes(
            "text-green-600 text-xs mt-1"
        )
    else:
        ui.label(f"✗ 环境变量 {env_name} 未设置").classes(
            "text-red-600 text-xs mt-1"
        )
```

---

## 10. 保存流程说明

用户点击“保存配置”后，流程如下：

```text
1. 前端收集表单值，生成 patch
2. 判断 Embedding model / dimension 是否变化
3. 调用 config_service.save_config(patch)
4. 后端读取当前 config.toml
5. deep merge patch
6. 删除 None
7. 校验配置
8. 写回 config.toml
9. 前端提示保存成功
10. 如果 Embedding model / dimension 变化，提示重建向量索引
```

示例：

```text
原配置：

[embedding]
enabled = true
base_url = "https://api.example.com/v1"
model = "text-embedding-3-small"
dimension = 1536
api_key_env = "OPENAI_API_KEY"
some_future_field = "keep me"
```

UI 只修改：

```text
dimension = 1024
```

保存后：

```text
some_future_field 仍然保留
```

这是 deep merge 的目的。

---

## 11. 环境变量检测说明

设置页加载时调用：

```python
config_service.get_env_status(config)
```

返回示例：

```json
{
  "OPENAI_API_KEY": true,
  "SILICONFLOW_API_KEY": false
}
```

UI 展示：

```text
✓ 环境变量 OPENAI_API_KEY 已设置
✗ 环境变量 SILICONFLOW_API_KEY 未设置
```

注意：

- 不读取 API Key 明文。
- 不展示 API Key 内容。
- 只判断环境变量是否存在且非空。

---

## 12. API 测试说明

### 12.1 LLM 测试

测试逻辑：

```text
1. 读取当前表单中的 LLM 配置
2. 读取 api_key_env 对应的环境变量
3. GET {base_url}/models
4. 如果 /models 返回 200，认为连接成功
5. 如果 /models 不支持，尝试 POST {base_url}/chat/completions
6. 返回成功或失败信息
```

### 12.2 Embedding 测试

测试逻辑：

```text
1. 读取当前表单中的 Embedding 配置
2. 读取 api_key_env 对应的环境变量
3. POST {base_url}/embeddings
4. payload：
   {
     "model": "...",
     "input": ["ping"]
   }
5. 返回成功或失败信息
```

---

## 13. 危险操作提醒

以下配置变化时，需要提醒用户：

### 13.1 Embedding model 变化

```text
原 model：text-embedding-3-small
新 model：bge-m3
```

提示：

```text
Embedding model 已变化，请重建向量索引。
```

### 13.2 Embedding dimension 变化

```text
原 dimension：1536
新 dimension：1024
```

提示：

```text
Embedding dimension 已变化，请重建向量索引。
```

### 13.3 保存成功后

如果检测到变化：

```text
配置已保存到 config.toml。
Embedding model 或 dimension 已变化，请重建向量索引。
```

用户可以直接点击设置页中的“重建向量索引”。

---

## 14. 运行测试

安装依赖：

```bash
uv add tomli-w
uv add httpx
```

启动：

```bash
python -m app.main
```

打开：

```text
http://127.0.0.1:8765/settings
```

---

### 14.1 测试配置展示

确认设置页展示：

```text
配置文件路径
LLM 总结配置
Embedding 配置
索引配置
任务配置
扫描配置
CLI 配置
应用配置
索引管理
```

---

### 14.2 测试保存配置

测试步骤：

1. 修改 LLM model。
2. 修改 Embedding batch_size。
3. 修改 index.chunk_max_chars。
4. 点击“保存配置”。
5. 打开 `.knowledge/config.toml`。
6. 确认修改已经写入。

预期：

```text
UI 修改的字段已更新。
未编辑的字段保留。
config.toml 语法合法。
```

---

### 14.3 测试未知字段保留

手动在 `config.toml` 中加入：

```toml
[embedding]
future_test_field = "keep"
```

然后在 UI 中修改 Embedding 任意字段并保存。

预期：

```toml
future_test_field = "keep"
```

仍然存在。

---

### 14.4 测试环境变量状态

设置环境变量：

```bash
set OPENAI_API_KEY=test-key
```

Windows CMD 下测试。

或者 PowerShell：

```powershell
$env:OPENAI_API_KEY="test-key"
```

然后刷新设置页。

预期：

```text
✓ 环境变量 OPENAI_API_KEY 已设置
```

删除环境变量后刷新：

```text
✗ 环境变量 OPENAI_API_KEY 未设置
```

---

### 14.5 测试 LLM API

配置真实 API 后点击：

```text
测试 LLM API
```

预期成功：

```text
LLM API 连接成功
```

如果 Key 错误，预期：

```text
LLM API 认证失败：HTTP 401
```

或类似错误。

---

### 14.6 测试 Embedding API

配置真实 Embedding API 后点击：

```text
测试 Embedding API
```

预期成功：

```text
Embedding API 连接成功：text-embedding-3-small
```

如果模型不存在，预期：

```text
Embedding API 返回 HTTP 404
```

或类似错误。

---

### 14.7 测试向量索引提醒

测试步骤：

1. 修改 Embedding dimension。
2. 点击保存。
3. 观察通知。

预期：

```text
配置已保存到 config.toml
Embedding model 或 dimension 已变化，请重建向量索引。
```

---

### 14.8 测试 CLI 配置不被破坏

测试步骤：

1. 不在 UI 中编辑 CLI。
2. 修改其他配置并保存。
3. 检查 `config.toml` 中的 `[cli]`。

预期：

```text
[cli] 配置保持不变。
```

---

## 15. 本阶段验收标准

本阶段完成后，需要满足：

1. 设置页可以展示当前 `.knowledge/config.toml` 路径。
2. 设置页可以打开 `config.toml`。
3. 设置页可以编辑 LLM 总结配置。
4. 设置页可以编辑 Embedding 配置。
5. 设置页可以编辑索引分块配置。
6. 设置页可以编辑任务配置。
7. 设置页可以编辑 `library.scan_on_startup`。
8. CLI 配置只读展示，不被 UI 误改。
9. 应用配置只读展示，修改需通过 TOML。
10. 点击保存后配置写回 `config.toml`。
11. 保存时不会破坏未编辑字段。
12. 保存时不会破坏未来新增字段。
13. 配置校验失败时显示错误。
14. UI 不提供明文 API Key 输入框。
15. 如果配置中存在明文 `api_key`，UI 显示警告。
16. UI 能显示 API Key 环境变量是否已设置。
17. LLM API 测试按钮可用。
18. Embedding API 测试按钮可用。
19. 修改 Embedding model 或 dimension 后提示重建向量索引。
20. 重建全文索引和重建向量索引功能仍然可用。

---

## 16. 当前项目完成度更新

本阶段完成后，项目进度可更新为：

```text
✅ M0：项目骨架
✅ M1：扫描和资产列表
✅ M2：派生文件识别 + 资产详情页
✅ M3：转录任务
✅ M4：全文搜索
✅ M5：LanceDB 向量搜索
✅ M6：AI 总结生成
✅ M7：统一导航 + 设置页 + 任务中心增强 + 配置 UI 化（本阶段）
⬜ M8：体验优化（PRD §28 既定，尚未开始）
```

---

## 17. 后续阶段建议

本阶段是 M7 的配置 UI 化补完。PRD §28 中 M8 仍为「体验优化」，尚未开始。以下为 qwen 提出的后续阶段设想（编号从 M9 起，与 PRD 的整数里程碑体系后续再对齐）：

```text
M9：watchdog 文件监听自动同步
M10：文档解析 CLI 接入
M11：PDF / DOCX / EPUB 内容索引
M12：sidecar .kb 目录结构
M13：应用内笔记编辑
M14：Prompt 模板 UI 编辑
M15：ignore 列表 UI 编辑
M16：CLI 命令模板 UI 编辑
M17：多 Provider 配置支持
M18：混合搜索排序优化
M19：标签系统
M20：打包分发
```

---

## 18. 推荐实施顺序

建议按下面顺序实施：

```text
1. 安装 tomli-w
2. 新增 config_service.py
3. 新增 Settings API
4. main.py 注册 Settings API
5. 替换 settings.py
6. 测试保存 config.toml
7. 测试未知字段保留
8. 测试环境变量状态
9. 测试 LLM / Embedding API 连通性
10. 测试 Embedding 变化提醒
11. 更新本阶段验收结果
```