"""知识库打开 / 状态管理（m1.md 未覆盖，按 PRD §20/§22.1 补齐）。"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from app.database import init_db
from app.services.recent_library_service import add_recent_library
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
# transcribe_cwd 支持绝对路径 / ~ 开头（用户主目录）/ 相对路径（相对 QBase 应用根目录）
transcribe_cwd = "../QVoice"
transcribe_timeout_seconds = 14400
parse_command = []

[llm.summary]
# AI 总结（m6）。使用前填好 base_url / model，再把 enabled 改为 true。
# max_input_chars：超过则分段摘要后合并；chunk_chars：分段每段最大字符数。
enabled = false
provider = "openai_compatible"
base_url = "https://api.siliconflow.cn/v1"
api_key_env = "SILICONFLOW_API_KEY"
model = "Qwen/Qwen2.5-72B-Instruct"
temperature = 0.2
max_tokens = 2000
timeout = 180
max_input_chars = 24000
chunk_chars = 6000

[embedding]
# 向量语义搜索（m5）。使用前先填好 base_url / model / dimension，
# 再把 enabled 改为 true。dimension 必须与模型实际输出维度一致：
#   BAAI/bge-m3 -> 1024，text-embedding-3-small -> 1536
enabled = false
provider = "openai_compatible"
base_url = "https://api.siliconflow.cn/v1"
api_key_env = "SILICONFLOW_API_KEY"
model = "BAAI/bge-m3"
dimension = 1024
batch_size = 16
timeout = 120

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
    add_recent_library(str(root))
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
