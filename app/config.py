"""应用级配置加载。

优先级：环境变量 > config.toml > 默认值。
库级配置（.knowledge/config.toml）在 M1 引入。
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.toml"


@dataclass(frozen=True)
class AppConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    open_browser: bool = True
    log_level: str = "INFO"


def load_config(path: Path = CONFIG_FILE) -> AppConfig:
    data: dict = {}
    if path.exists():
        with path.open("rb") as f:
            data = tomllib.load(f)
    section = data.get("app", {})

    return AppConfig(
        host=os.getenv("QBASE_HOST", section.get("host", AppConfig.host)),
        port=int(os.getenv("QBASE_PORT", section.get("port", AppConfig.port))),
        open_browser=str(
            os.getenv("QBASE_OPEN_BROWSER", section.get("open_browser", True))
        ).lower()
        in ("1", "true", "yes"),
        log_level=os.getenv("QBASE_LOG_LEVEL", section.get("log_level", AppConfig.log_level)),
    )


_config: AppConfig | None = None


def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = load_config()
    return _config
