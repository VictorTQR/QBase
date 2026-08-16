"""库级配置读取（.knowledge/config.toml）。"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from app.state import state


def get_config_path() -> Path:
    if state.library_root is None:
        raise RuntimeError("未打开知识库")

    return state.library_root / ".knowledge" / "config.toml"


def load_config() -> dict:
    """读取 .knowledge/config.toml。"""
    path = get_config_path()

    if not path.exists():
        return {}

    with open(path, "rb") as f:
        return tomllib.load(f)


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

    cwd = cli_config.get("transcribe_cwd") or None
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
        api_key = os.environ.get(api_key_env, api_key)

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
                    f"未获取到 Embedding API Key，请设置环境变量：{api_key_env}"
                )
            raise ValueError(
                "未获取到 Embedding API Key，请配置 api_key_env 或 api_key"
            )

    return result
