"""解析器注册表。[parse] provider 配置值 -> 解析器类。

新增解析器：实现 DocumentParser 三阶段接口，注册进 PARSERS 即可，
配置端把 [parse].provider 切到对应键（provider 专属配置挂同名子表）。
"""

from __future__ import annotations

from app.services.parsers.base import DocumentParser, ParseFileState, ParseSubmission
from app.services.parsers.mineru_parser import MineruParser

PARSERS: dict[str, type[DocumentParser]] = {
    MineruParser.name: MineruParser,
}


def get_parser(config: dict) -> DocumentParser:
    """按配置实例化解析器。provider 未注册 / token 缺失时抛 ValueError。"""
    provider = str(config.get("provider") or "mineru").strip() or "mineru"
    cls = PARSERS.get(provider)

    if cls is None:
        raise ValueError(
            f"未注册的解析器：{provider}（可用：{'、'.join(sorted(PARSERS))}）"
        )

    provider_config = config.get(provider)

    if not isinstance(provider_config, dict):
        provider_config = {}

    return cls(provider_config)
