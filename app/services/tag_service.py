"""标签服务（m15）：标签名校验、查询与整体替换。"""

from __future__ import annotations

from app.database import get_conn
from app.repositories.asset_repository import get_asset_by_id
from app.repositories.tag_repository import (
    get_tags_for_asset,
    list_tags,
    set_asset_tags as repo_set_asset_tags,
)
from app.state import get_db_path

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
