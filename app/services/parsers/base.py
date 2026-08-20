"""文档解析器抽象：submit → poll → fetch 三阶段。

HTTP API 与本地 CLI 均可实现同一接口：
CLI 解析器的 submit = 起子进程、poll = 查输出文件、fetch = 读产物。
行为复用一律走组合（轮询循环/超时/持久化在 parse_service 编排），
基类只做接口声明，不携带任何共享实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParseSubmission:
    """一次解析提交的远端状态。

    持久化进任务的 params_json（见 parse_service），
    应用重启后凭它恢复轮询（结果接口幂等）。
    """

    batch_id: str
    files: list[dict] = field(default_factory=list)


@dataclass
class ParseFileState:
    """单个文件的解析状态。"""

    name: str
    state: str  # waiting_file / running / done / failed（沿用 MinerU v4 枚举）
    err_msg: str | None = None
    full_zip_url: str | None = None


class DocumentParser(ABC):
    """解析器接口。注册表见 parsers/__init__.py。"""

    name: str = ""

    @abstractmethod
    def submit(self, paths: list[Path]) -> ParseSubmission:
        """提交解析（含文件上传），返回可轮询的远端状态。"""

    @abstractmethod
    def poll(self, submission: ParseSubmission) -> list[ParseFileState]:
        """查询各文件状态。结果接口幂等，可反复调用。"""

    @abstractmethod
    def fetch(self, state: ParseFileState) -> bytes:
        """取回产物原始字节（MinerU 为 zip 字节流）。"""
