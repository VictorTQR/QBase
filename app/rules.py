"""文件类型与忽略规则。"""

AUDIO_EXTENSIONS = {
    ".mp3",
    ".m4a",
    ".wav",
    ".flac",
    ".aac",
    ".ogg",
    ".opus",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".mov",
    ".webm",
    ".avi",
}

DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".md",
    ".txt",
    ".html",
    ".htm",
    ".epub",
}

SUPPORTED_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS | DOCUMENT_EXTENSIONS

IGNORE_DIR_NAMES = {
    ".knowledge",
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "$recycle.bin",
    "system volume information",
    ".trash",
}


def classify_extension(ext: str) -> str | None:
    """根据扩展名判断资产类型。"""
    ext = ext.lower()

    if ext in AUDIO_EXTENSIONS:
        return "audio"

    if ext in VIDEO_EXTENSIONS:
        return "video"

    if ext in DOCUMENT_EXTENSIONS:
        return "document"

    return None


def should_ignore_dir(name: str) -> bool:
    """判断目录是否应该忽略。隐藏目录一律忽略。"""
    if name.startswith("."):
        return True

    return name.lower() in IGNORE_DIR_NAMES


def get_parse_status(asset_type: str, ext: str) -> str:
    """第一阶段文档解析策略。

    audio / video：不需要文档解析，需要转录。
    .md / .txt：可直接读取文本，不需要额外解析。
    其他 document：等待文档解析模块（pending）。
    """
    if asset_type in {"audio", "video"}:
        return "not_required"

    ext = ext.lower()

    if ext in {".md", ".txt"}:
        return "not_required"

    return "pending"
