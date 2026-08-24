"""共享 UI 组件：消除各页面重复的徽章渲染逻辑。

之前 search.py / assets.py / asset_detail.py 各自重复或内联了一份
派生文件徽章渲染，现统一于此，颜色引用 app.ui.tokens.C。
"""

from __future__ import annotations

from nicegui import ui

from app.ui.tokens import C


def render_derived_badges(item: dict) -> None:
    """渲染派生文件完成度徽章：转录 / 总结 / 笔记 / 已解析 / 元数据 / 待解析。

    item 兼容两种结构：
    - 含 derived_badges 子字典（搜索结果）
    - 含顶层 has_transcript 等字段 + parse_status（资产 / 详情）
    """
    badges = item.get("derived_badges") or item
    if badges.get("has_transcript"):
        ui.badge("转录", color=C.TRANSCRIPT).classes("text-xs")
    if badges.get("has_summary"):
        ui.badge("总结", color=C.SUMMARY).classes("text-xs")
    if badges.get("has_note"):
        ui.badge("笔记", color=C.NOTE).classes("text-xs")
    if badges.get("has_parsed"):
        ui.badge("已解析", color=C.PARSED).classes("text-xs")
    if badges.get("has_meta"):
        ui.badge("元数据", color=C.META).classes("text-xs")
    if badges.get("has_analysis"):
        ui.badge("分析", color=C.ANALYSIS).classes("text-xs")
    if item.get("parse_status") == "pending":
        # parse_status 是扫描时的静态策略值（pdf/office 恒为 pending，不随
        # 解析产物翻转），已解析时须抑制待解析徽章，避免二者并排
        if not badges.get("has_parsed"):
            ui.badge("待解析", color=C.PENDING).classes("text-xs")
