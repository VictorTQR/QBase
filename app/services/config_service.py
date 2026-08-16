"""库级配置读取（.knowledge/config.toml）。"""

from __future__ import annotations

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
