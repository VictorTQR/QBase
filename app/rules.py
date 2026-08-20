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

IGNORE_FILE_NAMES = {
    "qvoice_manifest.json",
}

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

# QVoice JSON 转录文件后缀（读取时需提取纯文本，见 utils.extract_transcript_json_text）。
TRANSCRIPT_JSON_SUFFIX = ".transcript.json"

# 派生文件 sidecar 后缀 -> kind（顺序重要：长后缀优先匹配）。
# .transcript.txt / .transcript.json 均为 QVoice 产物（-f txt / -f json）。
ARTIFACT_SUFFIXES = [
    (".transcript.txt", "transcript"),
    (".transcript.json", "transcript"),
    (".summary.md", "summary"),
    (".notes.md", "note"),
    (".parsed.md", "parsed"),
    (".meta.json", "meta"),
]


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


def explicit_artifact_kind(filename: str) -> str | None:
    """判断文件名是否是明确命名的派生文件，返回 kind。

    例：episode-001.summary.md -> "summary"
    """
    lower_name = filename.lower()

    for suffix, kind in ARTIFACT_SUFFIXES:
        if lower_name.endswith(suffix):
            return kind

    return None


def explicit_artifact_stem(filename: str) -> str:
    """获取派生文件对应的原始文件名 stem。

    例：episode-001.transcript.txt -> "episode-001"
    """
    lower_name = filename.lower()

    for suffix, _ in ARTIFACT_SUFFIXES:
        if lower_name.endswith(suffix):
            return filename[: -len(suffix)]

    return filename
