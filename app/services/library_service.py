"""知识库打开 / 状态管理（m1.md 未覆盖，按 PRD §20/§22.1 补齐）。"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from app.database import init_db
from app.state import state

DEFAULT_LIBRARY_CONFIG = """# 知识库级配置（打开知识库时生成，可在设置页修改）

[library]
scan_on_startup = false
ignore = [
  ".knowledge",
  ".git",
  "__pycache__",
  "node_modules",
  ".venv",
  "venv",
  "$RECYCLE.BIN",
  "System Volume Information",
]

[task]
max_workers = 1
task_timeout_seconds = 7200

[cli]
transcribe_command = [
  "uv",
  "run",
  "qvoice",
  "transcribe",
  "{input}",
]
transcribe_cwd = "E:/Code/00Code/GitBank/QVoice"
transcribe_timeout_seconds = 14400
parse_command = []

[llm.summary]
enabled = true
provider = "openai_compatible"
base_url = "https://api.example.com/v1"
api_key_env = "OPENAI_API_KEY"
model = "gpt-4o-mini"

[embedding]
enabled = true
provider = "openai_compatible"
base_url = "https://api.example.com/v1"
api_key_env = "OPENAI_API_KEY"
model = "text-embedding-3-small"

[index]
chunk_max_chars = 800
chunk_overlap = 100
"""


def open_library(path_str: str) -> dict:
    """打开（或初始化）知识库目录。

    - 目录必须已存在且为文件夹
    - 自动创建 .knowledge/，写入默认库级配置
    - 初始化 SQLite
    """
    path_str = (path_str or "").strip().strip('"').strip("'")

    if not path_str:
        raise ValueError("请输入知识库目录")

    root = Path(path_str).expanduser().resolve()

    if not root.exists():
        raise FileNotFoundError(f"目录不存在：{root}")

    if not root.is_dir():
        raise NotADirectoryError(f"不是目录：{root}")

    kb_dir = root / ".knowledge"
    kb_dir.mkdir(exist_ok=True)

    config_path = kb_dir / "config.toml"
    if not config_path.exists():
        config_path.write_text(DEFAULT_LIBRARY_CONFIG, encoding="utf-8")

    db_path = kb_dir / "db.sqlite"
    init_db(db_path)

    state.library_root = root
    logger.info("已打开知识库：{}", root)

    return {
        "library_root": str(root),
        "db_path": str(db_path),
    }


def close_library() -> None:
    state.library_root = None


def get_library_status() -> dict:
    """当前知识库状态。"""
    if state.library_root is None:
        return {"opened": False}

    root: Path = state.library_root
    return {
        "opened": True,
        "library_root": str(root),
        "db_exists": (root / ".knowledge" / "db.sqlite").exists(),
    }
