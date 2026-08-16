"""外部 CLI 执行器：命令模板替换 + 子进程运行 + 超时处理。"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class CliResult:
    returncode: int
    stdout: str
    stderr: str


def build_command(template: list[str], variables: dict) -> list[str]:
    """将命令模板中的变量替换掉。

    例如 template = ["uv", "run", "qvoice", "transcribe", "{input}"]
    返回 ["uv", "run", "qvoice", "transcribe", "D:/Knowledge/test.mp3"]
    """
    if not isinstance(template, list):
        raise ValueError("CLI 命令必须是数组格式")

    return [str(item).format(**variables) for item in template]


def tail(text: str | None, max_chars: int = 4000) -> str:
    """截取日志尾部，避免数据库存太多内容。"""
    if not text:
        return ""

    text = text.strip()

    if len(text) <= max_chars:
        return text

    return "...\n" + text[-max_chars:]


def run_cli_command(
    command: list[str],
    cwd: str | None = None,
    timeout: int = 14400,
) -> CliResult:
    """同步执行外部 CLI。适合放进 run.io_bound 或后台线程中运行。"""
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

        return CliResult(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )

    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout
        stderr = exc.stderr

        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")

        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")

        return CliResult(
            returncode=124,
            stdout=stdout or "",
            stderr=stderr or "",
        )

    except FileNotFoundError as exc:
        return CliResult(
            returncode=127,
            stdout="",
            stderr=str(exc),
        )
