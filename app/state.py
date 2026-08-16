"""全局运行时状态（单用户本地应用，进程内单例）。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppState:
    library_root: Path | None = None


state = AppState()


def get_db_path() -> Path:
    if state.library_root is None:
        raise RuntimeError("未打开知识库")

    return state.library_root / ".knowledge" / "db.sqlite"
