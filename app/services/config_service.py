"""库级配置读取与写回（.knowledge/config.toml）。

读取类函数（get_embedding_config / get_summary_llm_config 等）供服务层使用；
写回类函数（save_config / test_connection 等）供设置页与 Settings API 使用。
配置的唯一真相来源是 .knowledge/config.toml，严禁写入 SQLite。
"""

from __future__ import annotations

import httpx
import os
import tomllib
import tomli_w
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.state import state


class ConfigError(ValueError):
    """配置读取、校验或保存失败。"""


def get_config_path() -> Path:
    if state.library_root is None:
        raise ConfigError("未打开知识库")

    return state.library_root / ".knowledge" / "config.toml"


def load_config() -> dict:
    """读取 .knowledge/config.toml。"""
    path = get_config_path()

    if not path.exists():
        return {}

    with open(path, "rb") as f:
        return tomllib.load(f)


def get_secrets_path() -> Path:
    """返回知识库目录下的本地密钥文件路径 .knowledge/secrets.toml。"""
    if state.library_root is None:
        raise ConfigError("未打开知识库")

    return Path(state.library_root) / ".knowledge" / "secrets.toml"


def load_secrets() -> dict[str, str]:
    """读取 .knowledge/secrets.toml 的 [keys] 段，返回 {键名: 密钥}。

    文件不存在或段缺失时返回空字典。该文件存放真实密钥，不应提交 Git。
    """
    path = get_secrets_path()

    if not path.exists():
        return {}

    with path.open("rb") as f:
        data = tomllib.load(f)

    keys = data.get("keys", {})

    return {str(k): str(v) for k, v in keys.items() if v}


def get_api_key(key_name: str) -> str:
    """根据密钥名解析真实 API Key。

    读取优先级（见 M7 设计 §19.2）：
    1. 当前进程环境变量
    2. .knowledge/secrets.toml 中的 [keys]
    """
    if not key_name:
        return ""

    env_value = os.getenv(key_name, "")
    if env_value:
        return env_value

    return load_secrets().get(key_name, "")


def _resolve_cli_cwd(raw: str | None) -> str | None:
    """解析 transcribe_cwd。

    支持三种写法：绝对路径；~ 开头（用户主目录）；相对路径（相对 QBase 应用根目录，
    即本文件上两级，便于 QVoice 与 QBase 同级仓库时写 "../QVoice"）。
    """
    if not raw:
        return None

    path = Path(raw).expanduser()

    if not path.is_absolute():
        base = Path(__file__).resolve().parents[2]
        path = base / path

    return str(path.resolve())


def get_transcribe_cli_config() -> dict:
    """读取转录 CLI 配置。"""
    config = load_config()
    cli_config = config.get("cli", {})

    command = cli_config.get("transcribe_command")

    if not command or not isinstance(command, list):
        raise ValueError(
            "未配置 transcribe_command。"
            "请在 .knowledge/config.toml 的 [cli] 中以数组格式配置。"
        )

    cwd = _resolve_cli_cwd(cli_config.get("transcribe_cwd"))

    if cwd is not None and not Path(cwd).is_dir():
        raise ValueError(f"transcribe_cwd 目录不存在：{cwd}")

    timeout = int(cli_config.get("transcribe_timeout_seconds", 14400))

    return {
        "command": command,
        "cwd": cwd,
        "timeout": timeout,
    }


def get_embedding_config() -> dict:
    """读取 Embedding 配置（enabled=false 时返回未启用状态，不校验）。"""
    config = load_config()
    embedding_config = config.get("embedding", {})

    enabled = bool(embedding_config.get("enabled", False))

    base_url = str(embedding_config.get("base_url", "")).strip()
    api_key_env = str(embedding_config.get("api_key_env", "")).strip()
    api_key = str(embedding_config.get("api_key", "")).strip()

    if api_key_env:
        resolved = get_api_key(api_key_env)
        api_key = resolved if resolved else api_key

    model = str(embedding_config.get("model", "")).strip()
    dimension = int(embedding_config.get("dimension", 0) or 0)
    batch_size = int(embedding_config.get("batch_size", 16) or 16)
    timeout = int(embedding_config.get("timeout", 120) or 120)

    result = {
        "enabled": enabled,
        "provider": str(embedding_config.get("provider", "openai_compatible")),
        "base_url": base_url,
        "api_key_env": api_key_env,
        "api_key": api_key,
        "model": model,
        "dimension": dimension,
        "batch_size": batch_size,
        "timeout": timeout,
    }

    if enabled:
        if not base_url:
            raise ValueError("Embedding 配置缺少 base_url")

        if not model:
            raise ValueError("Embedding 配置缺少 model")

        if dimension <= 0:
            raise ValueError("Embedding 配置缺少有效的 dimension")

        if not api_key:
            if api_key_env:
                raise ValueError(
                    "未获取到 Embedding API Key。"
                    f"已检查进程环境变量与 .knowledge/secrets.toml，均未找到 {api_key_env}。"
                    "请设置该环境变量名，或在 .knowledge/secrets.toml 的 [keys] 下配置。"
                )
            raise ValueError(
                "未获取到 Embedding API Key，请配置 api_key_env 或 api_key"
            )

    return result


def get_summary_llm_config() -> dict:
    """读取 LLM 总结配置（enabled=false 时返回未启用状态，不校验）。"""
    config = load_config()
    summary_config = config.get("llm", {}).get("summary", {})

    enabled = bool(summary_config.get("enabled", False))

    base_url = str(summary_config.get("base_url", "")).strip()
    api_key_env = str(summary_config.get("api_key_env", "")).strip()
    api_key = str(summary_config.get("api_key", "")).strip()

    if api_key_env:
        resolved = get_api_key(api_key_env)
        api_key = resolved if resolved else api_key

    model = str(summary_config.get("model", "")).strip()
    temperature = float(summary_config.get("temperature", 0.2))
    max_tokens = int(summary_config.get("max_tokens", 2000) or 2000)
    timeout = int(summary_config.get("timeout", 180) or 180)
    max_input_chars = int(summary_config.get("max_input_chars", 24000) or 24000)
    chunk_chars = int(summary_config.get("chunk_chars", 6000) or 6000)

    result = {
        "enabled": enabled,
        "provider": str(summary_config.get("provider", "openai_compatible")),
        "base_url": base_url,
        "api_key_env": api_key_env,
        "api_key": api_key,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout": timeout,
        "max_input_chars": max_input_chars,
        "chunk_chars": chunk_chars,
    }

    if enabled:
        if not base_url:
            raise ValueError("LLM 总结配置缺少 base_url")

        if not model:
            raise ValueError("LLM 总结配置缺少 model")

        if not api_key:
            if api_key_env:
                raise ValueError(
                    "未获取到 LLM API Key。"
                    f"已检查进程环境变量与 .knowledge/secrets.toml，均未找到 {api_key_env}。"
                    "请设置该环境变量名，或在 .knowledge/secrets.toml 的 [keys] 下配置。"
                )
            raise ValueError("未获取到 LLM API Key，请配置 api_key_env 或 api_key")

    return result


def get_tagging_llm_config() -> dict:
    """读取 AI 打标配置（[llm.tagging]，m16；enabled=false 时返回未启用状态，不校验）。"""
    config = load_config()
    tagging_config = config.get("llm", {}).get("tagging", {})

    enabled = bool(tagging_config.get("enabled", False))

    base_url = str(tagging_config.get("base_url", "")).strip()
    api_key_env = str(tagging_config.get("api_key_env", "")).strip()
    api_key = str(tagging_config.get("api_key", "")).strip()

    if api_key_env:
        resolved = get_api_key(api_key_env)
        api_key = resolved if resolved else api_key

    result = {
        "enabled": enabled,
        "provider": str(tagging_config.get("provider", "openai_compatible")),
        "base_url": base_url,
        "api_key_env": api_key_env,
        "api_key": api_key,
        "model": str(tagging_config.get("model", "")).strip(),
        "temperature": float(tagging_config.get("temperature", 0.1)),
        "max_tokens": int(tagging_config.get("max_tokens", 300) or 300),
        "timeout": int(tagging_config.get("timeout", 60) or 60),
        "max_input_chars": int(
            tagging_config.get("max_input_chars", 4000) or 4000
        ),
    }

    if enabled:
        if not base_url:
            raise ValueError("AI 打标配置缺少 base_url")

        if not result["model"]:
            raise ValueError("AI 打标配置缺少 model")

        if not api_key:
            if api_key_env:
                raise ValueError(
                    "未获取到 AI 打标 API Key。"
                    f"已检查进程环境变量与 .knowledge/secrets.toml，均未找到 {api_key_env}。"
                    "请设置该环境变量名，或在 .knowledge/secrets.toml 的 [keys] 下配置。"
                )
            raise ValueError("未获取到 AI 打标 API Key，请配置 api_key_env 或 api_key")

    return result


def get_parse_config() -> dict:
    """读取文档解析配置（[parse] + provider 子表展平，enabled=false 不校验）。"""
    config = load_config()
    parse = config.get("parse")

    if not isinstance(parse, dict):
        parse = {}

    provider = str(parse.get("provider", "mineru")).strip() or "mineru"
    provider_config = parse.get(provider)

    if not isinstance(provider_config, dict):
        provider_config = {}

    return {
        "enabled": bool(parse.get("enabled", False)),
        "provider": provider,
        "timeout_seconds": int(provider_config.get("timeout_seconds", 1800) or 1800),
        "poll_interval_seconds": int(
            provider_config.get("poll_interval_seconds", 10) or 10
        ),
        **provider_config,
    }


# ──────────────────────────────────────────────────────────────────────────
# 配置写回 / 校验 / 环境检测 / 连通性测试（m7-config-ui）
# ──────────────────────────────────────────────────────────────────────────


def _mask_api_keys(config: dict[str, Any]) -> dict[str, Any]:
    """返回配置的副本，明文 api_key 字段统一替换为 '***'。

    避免明文 Key 经 GET /api/settings 回传到前端展示层。
    """
    masked = deepcopy(config)

    for section in ("embedding", ("llm", "summary"), ("llm", "tagging")):
        node = masked
        for key in section if isinstance(section, tuple) else (section,):
            node = node.get(key, {}) if isinstance(node, dict) else {}
        if isinstance(node, dict) and node.get("api_key"):
            node["api_key"] = "***"

    return masked


def get_settings_view() -> dict[str, Any]:
    """返回设置页所需数据：配置（明文 Key 已打码）、密钥状态、配置文件路径。"""
    config = load_config()

    return {
        "config": _mask_api_keys(config),
        "key_status": get_key_status(config),
        "has_plain_api_key": has_plain_api_key(config),
        "config_path": str(get_config_path()),
    }


def save_config(patch: dict[str, Any]) -> dict[str, Any]:
    """将 UI 提交的 patch 合并到原配置，校验后写回 config.toml。

    原则：UI 只是 TOML 的可视化编辑器，不把配置存进 SQLite。
    """
    current_config = load_config()
    merged_config = _deep_merge(current_config, patch)
    cleaned_config = _clean_none(merged_config)
    validated_config = validate_config(cleaned_config)

    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("wb") as f:
        tomli_w.dump(validated_config, f)

    return _mask_api_keys(validated_config)


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """递归合并配置。patch 值优先，保留 base 中未被编辑的字段。"""
    result = deepcopy(base)

    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result


def _clean_none(value: Any) -> Any:
    """tomli_w 不支持 None，保存前删除 None 值。"""
    if isinstance(value, dict):
        return {k: _clean_none(v) for k, v in value.items() if v is not None}

    if isinstance(value, list):
        return [_clean_none(item) for item in value if item is not None]

    return value


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    """对配置做基础校验，校验失败时抛出 ConfigError。"""
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

    # ── llm.tagging（m16 AI 打标）──
    tagging = llm.get("tagging", {})

    if tagging.get("enabled"):
        if not str(tagging.get("base_url", "")).strip():
            raise ConfigError("AI 打标已启用，但 base_url 为空")

        if not str(tagging.get("model", "")).strip():
            raise ConfigError("AI 打标已启用，但 model 为空")

        tagging_max_tokens = int(tagging.get("max_tokens", 300))
        if tagging_max_tokens <= 0:
            raise ConfigError("AI 打标 max_tokens 必须大于 0")

        tagging_timeout = int(tagging.get("timeout", 60))
        if tagging_timeout <= 0:
            raise ConfigError("AI 打标 timeout 必须大于 0")

        tagging_max_input = int(tagging.get("max_input_chars", 4000))
        if tagging_max_input <= 0:
            raise ConfigError("AI 打标 max_input_chars 必须大于 0")

    # ── parse ──
    parse = cfg.get("parse", {})

    if parse.get("enabled"):
        # 惰性导入避免与 parsers 包循环依赖（mineru_parser 导入本模块的 get_api_key）
        from app.services.parsers import PARSERS

        provider = str(parse.get("provider", "")).strip() or "mineru"

        if provider not in PARSERS:
            raise ConfigError(
                f"解析器未注册：{provider}（可用：{'、'.join(sorted(PARSERS))}）"
            )

        provider_cfg = parse.get(provider)

        if not isinstance(provider_cfg, dict):
            provider_cfg = {}

        if provider == "mineru":
            model_version = str(provider_cfg.get("model_version", "vlm")).strip()

            if model_version not in {"pipeline", "vlm"}:
                raise ConfigError(
                    "parse model_version 仅支持 pipeline / vlm"
                )

        timeout_seconds = int(provider_cfg.get("timeout_seconds", 1800))

        if timeout_seconds < 1:
            raise ConfigError("parse timeout_seconds 必须大于等于 1")

        poll_interval_seconds = int(provider_cfg.get("poll_interval_seconds", 10))

        if poll_interval_seconds < 1:
            raise ConfigError("parse poll_interval_seconds 必须大于等于 1")

    return cfg


def get_key_status(config: dict[str, Any] | None = None) -> dict[str, dict]:
    """检测配置中引用的密钥名称是否可解析，并标明来源。

    返回：{key_name: {"found": bool, "source": "环境变量" | "secrets.toml" | ""}}
    source 为空字符串表示未找到。
    """
    if config is None:
        config = load_config()

    key_names: set[str] = set()

    embedding = config.get("embedding", {})
    if embedding.get("api_key_env"):
        key_names.add(str(embedding["api_key_env"]))

    llm_summary = config.get("llm", {}).get("summary", {})
    if llm_summary.get("api_key_env"):
        key_names.add(str(llm_summary["api_key_env"]))

    llm_tagging = config.get("llm", {}).get("tagging", {})
    if llm_tagging.get("api_key_env"):
        key_names.add(str(llm_tagging["api_key_env"]))

    parse = config.get("parse", {})

    if isinstance(parse, dict):
        parse_provider = str(parse.get("provider", "mineru") or "mineru")
        provider_cfg = parse.get(parse_provider)

        if isinstance(provider_cfg, dict) and provider_cfg.get("token_env"):
            key_names.add(str(provider_cfg["token_env"]))

    secrets = load_secrets()

    result: dict[str, dict] = {}
    for name in key_names:
        if os.getenv(name):
            result[name] = {"found": True, "source": "环境变量"}
        elif name in secrets:
            result[name] = {"found": True, "source": "secrets.toml"}
        else:
            result[name] = {"found": False, "source": ""}

    return result


def has_plain_api_key(config: dict[str, Any] | None = None) -> bool:
    """检测配置中是否存在明文 api_key（UI 不编辑，只做警告）。"""
    if config is None:
        config = load_config()

    embedding_key = config.get("embedding", {}).get("api_key")
    llm = config.get("llm", {})
    llm_key = llm.get("summary", {}).get("api_key") or llm.get(
        "tagging", {}
    ).get("api_key")

    return bool(embedding_key or llm_key)


def get_vector_last_rebuilt() -> str | None:
    """读取 config.toml [vector] last_rebuilt（ISO8601），未设置或尚未打开知识库返回 None。"""
    try:
        return load_config().get("vector", {}).get("last_rebuilt")
    except ConfigError:
        return None


def set_vector_last_rebuilt(iso: str | None = None) -> None:
    """记录向量索引最后重建时间到 config.toml 的 [vector] last_rebuilt。

    iso 为 None 时写入当前 UTC 时间（ISO8601）。重建向量索引成功后调用。
    只更新 [vector] 段，其余配置保持不变。
    """
    from datetime import datetime, timezone

    if iso is None:
        iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    config = load_config()
    vector_section = dict(config.get("vector", {}))
    vector_section["last_rebuilt"] = iso
    config["vector"] = vector_section

    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        tomli_w.dump(config, f)


def test_connection(
    kind: str,
    override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """测试 LLM 或 Embedding API 连通性。

    override 为前端当前表单内容（部分 patch），优先于已保存配置使用。
    """
    config = load_config()

    if override:
        config = _deep_merge(config, override)

    if kind == "embedding":
        return _test_embedding_connection(config)

    if kind == "llm":
        return _test_llm_connection(config.get("llm", {}).get("summary", {}), "LLM 总结")

    if kind == "llm_tagging":
        return _test_llm_connection(
            config.get("llm", {}).get("tagging", {}), "AI 打标"
        )

    if kind == "parse":
        return _test_parse_connection(config)

    return {"ok": False, "message": f"不支持的测试类型：{kind}"}


def _get_api_key(section: dict[str, Any]) -> tuple[str, str]:
    """根据 api_key_env 解析真实 API Key，返回 (key_name, api_key)。

    解析走 get_api_key：先查进程环境变量，再查 .knowledge/secrets.toml；
    未解析到时回退配置中的明文 api_key（与运行时读取逻辑一致）。
    """
    env_name = str(section.get("api_key_env", "")).strip()

    api_key = get_api_key(env_name) if env_name else ""

    if not api_key:
        api_key = str(section.get("api_key", "")).strip()

    return env_name, api_key


def _test_embedding_connection(config: dict[str, Any]) -> dict[str, Any]:
    embedding = config.get("embedding", {})

    if not embedding.get("enabled"):
        return {"ok": False, "message": "Embedding 未启用"}

    base_url = str(embedding.get("base_url", "")).strip().rstrip("/")
    model = str(embedding.get("model", "")).strip()

    if not base_url:
        return {"ok": False, "message": "Embedding base_url 为空"}

    if not model:
        return {"ok": False, "message": "Embedding model 为空"}

    env_name, api_key = _get_api_key(embedding)

    if env_name and not api_key:
        return {"ok": False, "message": f"环境变量 {env_name} 未设置"}

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = httpx.post(
            f"{base_url}/embeddings",
            headers=headers,
            json={"model": model, "input": ["ping"]},
            timeout=15,
        )

        if response.status_code == 200:
            return {"ok": True, "message": f"Embedding API 连接成功：{model}"}

        return {
            "ok": False,
            "message": (
                f"Embedding API 返回 HTTP {response.status_code}："
                f"{response.text[:200]}"
            ),
        }

    except Exception as exc:
        return {"ok": False, "message": f"Embedding API 请求失败：{exc}"}


def _test_llm_connection(section: dict[str, Any], label: str) -> dict[str, Any]:
    """测试 OpenAI 兼容 LLM 端点连通性（section 为 [llm.summary] / [llm.tagging]）。"""
    if not section.get("enabled"):
        return {"ok": False, "message": f"{label}未启用"}

    base_url = str(section.get("base_url", "")).strip().rstrip("/")
    model = str(section.get("model", "")).strip()

    if not base_url:
        return {"ok": False, "message": f"{label} base_url 为空"}

    if not model:
        return {"ok": False, "message": f"{label} model 为空"}

    env_name, api_key = _get_api_key(section)

    if env_name and not api_key:
        return {"ok": False, "message": f"环境变量 {env_name} 未设置"}

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = httpx.get(
            f"{base_url}/models",
            headers=headers,
            timeout=15,
        )

        if response.status_code == 200:
            return {"ok": True, "message": f"{label} API 连接成功"}

        if response.status_code in {401, 403}:
            return {
                "ok": False,
                "message": f"{label} API 认证失败：HTTP {response.status_code}",
            }

    except Exception:
        pass

    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
            },
            timeout=15,
        )

        if response.status_code == 200:
            return {"ok": True, "message": f"{label} API 连接成功：{model}"}

        return {
            "ok": False,
            "message": (
                f"{label} API 返回 HTTP {response.status_code}："
                f"{response.text[:200]}"
            ),
        }

    except Exception as exc:
        return {"ok": False, "message": f"{label} API 请求失败：{exc}"}


def _test_parse_connection(config: dict[str, Any]) -> dict[str, Any]:
    """测试 MinerU 连通性：用一个不存在的 batch_id 查结果接口。

    401/403 = token 无效；其余（通常 404 或 code!=0）说明服务可达且 token 通过认证。
    不提交真实解析任务，不消耗页数额度。
    """
    parse = config.get("parse", {})

    if not parse.get("enabled"):
        return {"ok": False, "message": "文档解析未启用"}

    provider = str(parse.get("provider", "mineru") or "mineru")
    provider_cfg = parse.get(provider)

    if not isinstance(provider_cfg, dict):
        provider_cfg = {}

    base_url = (
        str(provider_cfg.get("base_url", "")).strip().rstrip("/")
        or "https://mineru.net"
    )
    token_env = str(provider_cfg.get("token_env", "")).strip()
    token = get_api_key(token_env) if token_env else ""

    if token_env and not token:
        return {"ok": False, "message": f"环境变量 {token_env} 未设置"}

    if not token:
        return {"ok": False, "message": "未配置解析 token（token_env）"}

    try:
        response = httpx.get(
            f"{base_url}/api/v4/extract-results/batch/qbase-connectivity-test",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )

        if response.status_code in (401, 403):
            return {
                "ok": False,
                "message": f"MinerU token 无效或已过期：HTTP {response.status_code}",
            }

        return {"ok": True, "message": "MinerU API 连接成功（token 有效）"}

    except Exception as exc:
        return {"ok": False, "message": f"MinerU API 请求失败：{exc}"}
