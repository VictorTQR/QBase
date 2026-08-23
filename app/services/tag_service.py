"""标签服务（m15）：标签名校验、查询与整体替换；AI 建议标签（m16）。"""

from __future__ import annotations

from app.database import get_conn
from app.repositories.artifact_repository import list_artifacts_by_asset
from app.repositories.asset_repository import get_asset_by_id
from app.repositories.tag_repository import (
    get_tags_for_asset,
    list_tags,
    set_asset_tags as repo_set_asset_tags,
)
from app.services import config_service, llm_service, summarization_service
from app.state import get_db_path
from app.utils import read_text_for_index

MAX_TAG_LENGTH = 30
MAX_TAGS_PER_ASSET = 20


def normalize_tag_names(names: list[str]) -> list[str]:
    """trim、去空、去重保序并逐条校验，违规抛 ValueError（中文报错）。"""
    normalized: list[str] = []

    for raw in names:
        if not isinstance(raw, str):
            raise ValueError("标签名必须是字符串")

        name = raw.strip()

        if not name:
            raise ValueError("标签名不能为空")

        if "," in name:
            raise ValueError(f"标签名不能包含半角逗号：{name}")

        if len(name) > MAX_TAG_LENGTH:
            raise ValueError(
                f"标签名不能超过 {MAX_TAG_LENGTH} 个字符：{name[:MAX_TAG_LENGTH]}…"
            )

        if name not in normalized:
            normalized.append(name)

    if len(normalized) > MAX_TAGS_PER_ASSET:
        raise ValueError(f"单个资产最多 {MAX_TAGS_PER_ASSET} 个标签")

    return normalized


def get_all_tags() -> list[dict]:
    """全部标签 + 使用数（绑定资产数）。"""
    conn = get_conn(get_db_path())
    try:
        return list_tags(conn)
    finally:
        conn.close()


def get_asset_tags(asset_id: str) -> list[str]:
    """某资产的标签名列表；资产不存在抛 ValueError。"""
    conn = get_conn(get_db_path())
    try:
        if get_asset_by_id(conn, asset_id) is None:
            raise ValueError("资产不存在")

        return get_tags_for_asset(conn, asset_id)
    finally:
        conn.close()


def set_asset_tags(asset_id: str, names: list[str]) -> list[str]:
    """整体替换某资产的标签，返回最终标签名列表。"""
    normalized = normalize_tag_names(names)

    conn = get_conn(get_db_path())
    try:
        if get_asset_by_id(conn, asset_id) is None:
            raise ValueError("资产不存在")

        result = repo_set_asset_tags(conn, asset_id, normalized)
        conn.commit()
        return result
    finally:
        conn.close()


def _clean_suggestions(names: list[str]) -> list[str]:
    """宽松清洗 AI 建议的标签：不合规条目直接丢弃而非报错。"""
    cleaned: list[str] = []

    for raw in names:
        if not isinstance(raw, str):
            continue

        name = raw.strip()

        if not name or "," in name or len(name) > MAX_TAG_LENGTH:
            continue

        if name not in cleaned:
            cleaned.append(name)

    return cleaned[:MAX_TAGS_PER_ASSET]


def _get_tagging_input_text(conn, asset: dict) -> str:
    """打标输入：优先取 active 总结（浓缩全文，长内容截断只伤覆盖度）；
    无总结时沿用总结的来源选择（音频/视频取转录、文档取解析/原文）。
    """
    for artifact in list_artifacts_by_asset(conn, asset["id"]):
        if artifact["kind"] == "summary" and artifact["status"] == "active":
            text = read_text_for_index(artifact["absolute_path"])
            if text.strip():
                return text
            break  # 总结为空文件，退回全文来源

    return summarization_service.get_summary_input_text(conn, asset)


def suggest_asset_tags(asset_id: str) -> list[str]:
    """AI 建议标签（m16）：只返回建议，不写库；由用户在编辑器确认后保存。

    输入优先用 active 总结，无则取转录/解析/原文（复用总结来源选择）。
    """
    conn = get_conn(get_db_path())
    try:
        asset = get_asset_by_id(conn, asset_id)

        if asset is None:
            raise ValueError("资产不存在")

        llm_config = config_service.get_tagging_llm_config()

        if not llm_config.get("enabled"):
            raise ValueError("AI 打标未启用，请前往设置页开启")

        input_text = _get_tagging_input_text(conn, asset)
        existing = [tag["name"] for tag in list_tags(conn)]
    finally:
        conn.close()

    suggestions = llm_service.suggest_tags(
        asset["title"], input_text, existing, llm_config
    )

    return _clean_suggestions(suggestions)
