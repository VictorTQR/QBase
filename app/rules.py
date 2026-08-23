"""文件类型与忽略规则。"""

from pathlib import Path

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
    ".pptx",
    ".ppt",
    ".xlsx",
    ".xls",
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


def is_transcript_json_name(filename: str) -> bool:
    """判断文件名是否为 QVoice JSON 转录（m12 统一判定）。

    平铺形态 <stem>.transcript.json（后缀匹配）与 sidecar 目录内固定名
    transcript.json（无 stem 前缀）均命中。平铺库中独立存在的 transcript.json
    不命中任何资产/产物规则，精确匹配收紧无副作用。
    """
    lower = filename.lower()
    return lower == "transcript.json" or lower.endswith(TRANSCRIPT_JSON_SUFFIX)


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
    """文档解析策略。

    audio / video：不需要文档解析，需要转录。
    .md / .txt：可直接读取文本，不需要额外解析。
    .html / .htm：内容提取未实现，不入内容索引（仅文件名搜索），
      状态为 not_required（2026-08-23 前误标 pending，无解析入口造成误导）。
    其他 document（pdf/office/epub）：等待文档解析（pending）。
    """
    if asset_type in {"audio", "video"}:
        return "not_required"

    ext = ext.lower()

    if ext in {".md", ".txt", ".html", ".htm"}:
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


# ── sidecar 目录（m11）─────────────────────────────────────────────────────
# <原始文件完整文件名>.kb/ 目录：内部派生文件用固定文件名（无 stem 前缀），
# 目录名即绑定键，按 relative_path 精确绑定资产，天然无歧义。
SIDECAR_DIR_SUFFIX = ".kb"

# sidecar 目录内文件名 -> kind（精确匹配；未列出的文件忽略）。
SIDECAR_FILE_KINDS = {
    "transcript.json": "transcript",
    "transcript.txt": "transcript",
    "summary.md": "summary",
    "notes.md": "note",
    "parsed.md": "parsed",
    "meta.json": "meta",
}


def is_sidecar_dir(dir_name: str) -> bool:
    """判断目录名是否为 <原始文件名>.kb 形式的 sidecar 目录（裸 ".kb" 不算）。"""
    return (
        dir_name.lower().endswith(SIDECAR_DIR_SUFFIX)
        and len(dir_name) > len(SIDECAR_DIR_SUFFIX)
    )


def sidecar_asset_filename(dir_name: str) -> str:
    """episode-001.mp3.kb -> episode-001.mp3（去掉 .kb 即原始文件完整文件名）。"""
    return dir_name[: -len(SIDECAR_DIR_SUFFIX)]


def sidecar_file_kind(filename: str) -> str | None:
    """sidecar 目录内文件名 -> kind；未识别命名返回 None。"""
    return SIDECAR_FILE_KINDS.get(filename.lower())


def sidecar_dir_of(asset_path) -> Path:
    """资产路径 -> 对应 sidecar 目录路径（episode.mp3 -> episode.mp3.kb）。"""
    asset_path = Path(asset_path)
    return asset_path.parent / (asset_path.name + SIDECAR_DIR_SUFFIX)


def derived_output_path(asset_path, filename: str) -> Path:
    """应用生成派生产物的写入路径（m11 跟随现状策略）。

    资产旁已存在 <完整文件名>.kb/ 目录时写入其中（filename 原名，如 summary.md）；
    否则与资产同目录平铺（stem.filename，如 episode-001.summary.md）。
    """
    asset_path = Path(asset_path)

    sidecar_dir = sidecar_dir_of(asset_path)

    if sidecar_dir.is_dir():
        return sidecar_dir / filename

    return asset_path.with_name(f"{asset_path.stem}.{filename}")
