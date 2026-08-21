"""UI 设计 token：集中定义颜色与样式类，作为单一来源。

消除 Tailwind 类（.classes()）与 Quasar color= 调色板名的散落混用：
- C    ：语义颜色，供 badge / button 的 color= 参数（Quasar 调色板名）
- CLS  ：Tailwind 类串，供 .classes() 使用

次要文字统一为 text-gray-600（在白底约 5.3:1，满足 WCAG AA 正文对比度），
不再使用 text-gray-400 / text-gray-500（约 2.85 / 4.0:1，不达标）。
"""

from __future__ import annotations


class C:
    """语义颜色：Quasar 调色板名，用于组件 color= 参数。"""

    PRIMARY = "primary"

    # 派生文件徽章
    TRANSCRIPT = "green"
    SUMMARY = "blue"
    NOTE = "purple"
    PARSED = "teal"
    META = "grey-6"
    PENDING = "orange"

    # 标签徽章（m15）
    TAG = "indigo"

    # 通用状态
    SUCCESS = "green"
    ERROR = "red"
    WARNING = "orange"
    INFO = "blue"
    NEUTRAL = "grey"
    NEUTRAL_4 = "grey-4"
    ASSET_TYPE = "blue-grey"


# Tailwind 类串：供 .classes() 使用（单一来源）
CLS = {
    # 顶栏
    "top_bar": "items-center justify-between px-6 py-3 bg-gray-800 text-white",
    "nav_on": "text-white font-semibold no-underline bg-white/20 px-2 py-0.5 rounded",
    "nav_off": "text-white/80 hover:text-white no-underline",
    # 标题行（与内容区同 max-w-5xl mx-auto 对齐）
    "title_row": "w-full max-w-5xl mx-auto px-6 py-3 items-center gap-3",
    "title": "text-2xl font-bold",
    # 内容区与页脚
    "content": "w-full max-w-5xl mx-auto p-6 gap-4 min-h-screen",
    "footer": "w-full items-center py-2",
    "footer_text": "text-xs text-gray-600",
    # 链接与次要文字（统一为达标对比度 text-gray-600）
    "link": "text-blue-600 hover:underline",
    "muted": "text-gray-600",
    # 面包屑（已处于 content 容器内，不再自带左右 padding）
    "breadcrumb": "py-1 items-center gap-1 text-sm text-gray-600",
    "breadcrumb_sep": "text-gray-400",
    "breadcrumb_current": "text-gray-700 font-medium truncate",
    # 卡片
    "card": "w-full p-4",
    "card_title": "text-lg font-semibold",
    # 表格表头 / 行
    "table_head": "w-full bg-gray-100 p-2 font-semibold items-center rounded",
    "table_row": "w-full border-b p-2 items-center hover:bg-gray-50 rounded",
}
