"""文档解析器抽象：submit → poll → fetch 三阶段 + to_markdown 产物转换。

HTTP API 与本地解析器均可实现同一接口：远端的 submit = 上传、poll = 查
状态、fetch = 下载；本地的 submit = 校验、poll = 查源文件、fetch = 现算
（见 epub_parser）。行为复用一律走组合（轮询循环/超时/持久化在
parse_service 编排），基类只做接口声明，不携带任何共享实现。
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
    """解析器接口。注册表见 parsers/__init__.py。

    按扩展名路由：.epub 固定走内置 epub 解析器，其余走 [parse].provider。
    """

    name: str = ""

    # 产物留档后缀（backups/ 下）：MinerU 为 ".zip"；
    # None = 产物不单独留档（epub 产物即 markdown 文本，覆盖时已有 .bak.md）
    PRODUCT_BACKUP_SUFFIX: str | None = None

    # 单文件大小上限：None = 不限制（200MB 是 MinerU 的限制，不是解析层的）
    max_file_bytes: int | None = None

    @abstractmethod
    def submit(self, paths: list[Path]) -> ParseSubmission:
        """提交解析（含文件上传），返回可轮询的远端状态。"""

    @abstractmethod
    def poll(self, submission: ParseSubmission) -> list[ParseFileState]:
        """查询各文件状态。结果接口幂等，可反复调用。"""

    @abstractmethod
    def fetch(self, state: ParseFileState) -> bytes:
        """取回产物原始字节（MinerU 为 zip 字节流，本地解析器为现算产物）。"""

    @abstractmethod
    def to_markdown(self, raw: bytes) -> str:
        """产物原始字节 → markdown 文本（MinerU 从 zip 提 full.md）。"""
