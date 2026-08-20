"""通用工具：大小/时间格式化，系统打开文件/目录。"""

from __future__ import annotations

import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

from app.rules import TRANSCRIPT_JSON_SUFFIX


def escape_like(value: str) -> str:
    """转义 LIKE 查询中的特殊字符。"""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def human_size(size: int | None) -> str:
    if size is None:
        return ""

    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    index = 0

    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1

    return f"{value:.1f} {units[index]}"


def human_time(ts: int | float | None) -> str:
    if not ts:
        return ""

    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""


def open_file(path_str: str) -> None:
    """用系统默认程序打开文件。"""
    path = Path(path_str)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{path}")

    if sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def open_folder(path_str: str) -> None:
    """打开文件所在目录。Windows 下若目标是文件，在资源管理器中选中它。"""
    path = Path(path_str)

    if not path.exists():
        raise FileNotFoundError(f"路径不存在：{path}")

    target_dir = path if path.is_dir() else path.parent

    if sys.platform.startswith("win"):
        if path.is_file():
            subprocess.Popen(["explorer", f"/select,{path}"])
        else:
            os.startfile(str(target_dir))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        if path.is_file():
            subprocess.Popen(["open", "-R", str(path)])
        else:
            subprocess.Popen(["open", str(target_dir)])
    else:
        subprocess.Popen(["xdg-open", str(target_dir)])


def _is_transcript_json(path: Path) -> bool:
    """判断文件是否是 QVoice JSON 转录（.transcript.json）。"""
    return path.name.lower().endswith(TRANSCRIPT_JSON_SUFFIX)


def extract_transcript_json_text(path_str: str | Path) -> str:
    """提取 QVoice JSON 转录中的纯文本。

    优先取顶层 text 字段（含标点的完整全文）；为空时回退按行拼接 segments[].text。
    解析失败抛 ValueError，由调用方决定跳过或报错。
    """
    path = Path(path_str)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法解析转录 JSON：{path}（{exc}）") from exc

    if not isinstance(data, dict):
        raise ValueError(f"转录 JSON 结构不符合预期：{path}")

    text = str(data.get("text") or "").strip()

    if text:
        return text

    segments = data.get("segments") or []
    return "\n".join(
        str(seg.get("text", "")).strip()
        for seg in segments
        if isinstance(seg, dict) and str(seg.get("text", "")).strip()
    )


def read_text_for_index(path_str: str, max_chars: int = 500_000) -> str:
    """读取文本文件用于建立索引。

    .transcript.json 提取纯文本；其余依次尝试 UTF-8 / UTF-8-SIG / GBK。
    """
    path = Path(path_str)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{path}")

    if _is_transcript_json(path):
        return extract_transcript_json_text(path)[:max_chars]

    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read(max_chars)
        except UnicodeDecodeError:
            continue

    raise ValueError(f"无法识别文本编码：{path}")


def read_text_preview(path_str: str, max_chars: int = 3000) -> tuple[str, bool]:
    """读取文本文件预览，返回 (文本, 是否截断)。

    .transcript.json 提取纯文本；其余依次尝试 UTF-8 / UTF-8-SIG / GBK。
    """
    path = Path(path_str)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{path}")

    if _is_transcript_json(path):
        text = extract_transcript_json_text(path)
        truncated = len(text) > max_chars
        return text[:max_chars], truncated

    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            with open(path, "r", encoding=encoding) as f:
                text = f.read(max_chars + 1)

            truncated = len(text) > max_chars
            return text[:max_chars], truncated
        except UnicodeDecodeError:
            continue

    raise ValueError(f"无法识别文本编码：{path}")


# ──────────────────────────────────────────────
# 错误提示统一层
# ──────────────────────────────────────────────

# 已知异常的中文映射（key 为异常类名字符串，value 为提示模板）
_ERROR_MESSAGES = {
    "FileNotFoundError": "文件不存在：{detail}",
    "PermissionError": "权限不足：{detail}",
    "ValueError": "{detail}",
    "ConnectionError": "网络连接失败，请检查服务是否启动：{detail}",
    "TimeoutError": "操作超时，请稍后重试：{detail}",
}


def notify_error(exc: Exception) -> str:
    """统一错误处理：记录完整堆栈到日志，对用户显示友好的中文提示。

    返回用户友好的消息字符串（供调用方需要时复用）。
    """
    from nicegui import ui

    logger.exception(f"操作失败：{type(exc).__name__}: {exc}")

    exc_name = type(exc).__name__
    detail = str(exc)

    if exc_name == "OperationalError" and "no such table" in detail.lower():
        message = "索引可能未建立，请前往设置页重建索引。"
    elif exc_name in _ERROR_MESSAGES:
        message = _ERROR_MESSAGES[exc_name].format(detail=detail)
    else:
        message = f"操作失败：{detail}。详见日志。"

    ui.notify(message, type="negative", multi_line=True)
    return message


# ──────────────────────────────────────────────
# 搜索高亮
# ──────────────────────────────────────────────


def highlight_snippet(snippet: str, words: list[str]) -> str:
    """对 snippet 中的命中词进行高亮，返回安全的 HTML 字符串。

    1. 先 HTML 转义
    2. 对每个 word 做大小写不敏感替换，包裹 <mark>
    """
    if not words:
        return html.escape(snippet)

    escaped = html.escape(snippet)
    for word in words:
        if not word:
            continue
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        escaped = pattern.sub(
            lambda m: f'<mark class="bg-yellow-200 px-0.5 rounded">{m.group()}</mark>',
            escaped,
        )
    return escaped


# ──────────────────────────────────────────────
# 大文本读取
# ──────────────────────────────────────────────


def read_text_full(path_str: str | Path) -> str:
    """读取完整文本文件，UTF-8 → UTF-8-SIG → GBK 兜底。"""
    p = Path(path_str)

    if _is_transcript_json(p):
        return extract_transcript_json_text(p)

    raw = p.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError("无法识别文本编码")


def read_text_segment(path_str: str | Path, offset: int = 0, length: int = 10000) -> str:
    """读取文本文件的指定片段（用于大文本分段显示）。"""
    full_text = read_text_full(path_str)
    return full_text[offset : offset + length]
