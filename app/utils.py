"""通用工具：大小/时间格式化，系统打开文件/目录。"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


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


def read_text_preview(path_str: str, max_chars: int = 3000) -> tuple[str, bool]:
    """读取文本文件预览，返回 (文本, 是否截断)。

    依次尝试 UTF-8 / UTF-8-SIG / GBK。
    """
    path = Path(path_str)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{path}")

    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            with open(path, "r", encoding=encoding) as f:
                text = f.read(max_chars + 1)

            truncated = len(text) > max_chars
            return text[:max_chars], truncated
        except UnicodeDecodeError:
            continue

    raise ValueError(f"无法识别文本编码：{path}")
