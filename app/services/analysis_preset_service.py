"""深度分析模板（m18）：.knowledge/presets/*.md，frontmatter + 提示词正文。

模板 id = 文件名 stem（限 [a-z0-9][a-z0-9_-]*，与 rules.py 的分析产物
文件名反解规则一致）。正文即提示词模板，占位符 {title} 会被替换为资产
标题（str.replace 实现，提示词正文可自由使用花括号）。
内置 teaching / interview 两个模板，开库时生成，已存在一律不覆盖。
"""

from __future__ import annotations

import re
from pathlib import Path

from loguru import logger

from app.state import state

PRESET_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

PRESETS_DIR_NAME = "presets"

VALID_ASSET_TYPES = {"audio", "video", "document"}

BUILTIN_PRESETS: dict[str, str] = {
    "teaching": """---
name: 授课分析
description: 拆解授课音视频：讲了什么、怎么讲的、哪些手法可以化用到自己的课
types: audio, video
---
你是一位资深教学设计顾问。请根据下面这堂课的带时间戳转录，输出一份「授课分析」，
帮助一位准备讲同类课程的老师看懂这堂课的结构与讲法，并把可用的技巧带回自己的课堂。
课程标题：{title}

转录格式说明：每行开头 [MM:SS] 为该段开始时间（超过 1 小时为 [H:MM:SS]）；
行内「说话人:」前缀存在时表示说话人，缺失时请根据内容自行推断并在概览中注明。

请严格按以下 Markdown 骨架输出（分段数量按内容实际情况，不强行凑数）：

# 授课分析：{title}

## 一、课程概览
- 主题与范围：这节课讲了什么，需要什么前置知识
- 整体结构：大纲式列出各环节，每项带时间锚点（如 [12:30]）
- 受众与难度推断

## 二、逐段拆解
（按内容逻辑分成 5-12 段，每段用如下格式）

### [起始时间–结束时间] 段落小标题
- **内容要点**：本段讲了什么（2-4 条）
- **引入方式**：这段是怎么开场或从上一段过渡的（问题、悬念、例子、回顾旧知识、直接切入…）
- **讲解手法**：用了哪些手法（类比 / 图示 / 公式推导 / 代码演示 / 提问互动 / 举例 / 讲故事 / 幽默…），各自怎么用的
- **亮点**：特别有效的地方，以及为什么有效（没有可省略此行）

## 三、可迁移的教学手法清单
（把逐段发现的手法去重汇总成表格）

| 手法 | 出现时间 | 用法要点 | 迁移提示 |
| --- | --- | --- | --- |

## 四、化用建议
（3-5 条针对备课的具体建议：结构安排、概念引入、节奏控制等）

要求：
1. 不要编造转录中不存在的信息；不确定的地方明确标注「转录未提及」。
2. 所有时间引用一律带时间戳（[MM:SS] 或 [H:MM:SS]），便于回看定位。
3. 使用简体中文、Markdown 格式，不要输出与骨架无关的开场白。
""",
    "interview": """---
name: 访谈分析
description: 拆解访谈/播客：话题脉络、逐段观点、主持技巧与可引用摘录
types: audio, video
---
你是一位资深访谈研究员。请根据下面这期访谈节目（1 对 1 或 1 对 N）的带时间戳
转录，输出一份「访谈分析」，帮助读者深入使用这期内容：既看懂观点，也看懂问法。
节目标题：{title}

转录格式说明：每行开头 [MM:SS] 为该段开始时间（超过 1 小时为 [H:MM:SS]）；
行内「说话人:」前缀存在时表示说话人，缺失时请根据内容区分主持人/嘉宾并自行
推断命名，在概览中注明是推断。

请严格按以下 Markdown 骨架输出（分段数量按内容实际情况，不强行凑数）：

# 访谈分析：{title}

## 一、节目概览
- 主题与脉络：这期围绕什么展开，如何推进
- 嘉宾与角色：1 对 1 还是 1 对 N；各嘉宾的身份背景（转录可推断时）
- 话题块结构：话题序列，每项带时间锚点（如 [18:20]）

## 二、逐段分析
（按话题分成 4-10 段，每段用如下格式）

### [起始时间–结束时间] 话题小标题
- **核心观点**：本段的主要论点（注明是谁说的）
- **关键问答**：主持人怎么问的（问法、铺垫、追问），嘉宾怎么答的
- **金句 / 数据 / 案例**：值得引用的原话或事实（带时间戳）
- **分歧与碰撞**：多位嘉宾观点的差异（仅 1 对 N 且存在时输出）

## 三、主持技巧拆解
- 提问策略：开放式 / 封闭式 / 假设式…（各附实例与时间戳）
- 追问与转折：怎么深挖、怎么换话题
- 控场与节奏：怎么收住跑题、怎么分配发言

## 四、观点摘录
（按主题归类，每条带时间戳与说话人，便于回听）

要求：
1. 不要编造转录中不存在的信息；不确定的地方明确标注「转录未提及」。
2. 所有时间引用一律带时间戳（[MM:SS] 或 [H:MM:SS]）。
3. 使用简体中文、Markdown 格式，不要输出与骨架无关的开场白。
""",
}


def get_presets_dir() -> Path:
    if state.library_root is None:
        raise ValueError("未打开知识库")

    return state.library_root / ".knowledge" / PRESETS_DIR_NAME


def parse_preset_content(content: str, preset_id: str) -> dict:
    """解析模板文件：frontmatter（--- 分隔的 key: value 行）+ 提示词正文。

    返回 {id, name, description, types, prompt}；frontmatter 缺失时
    name 回退为 preset_id，types 回退为 {audio, video}。
    """
    name = preset_id
    description = ""
    types = {"audio", "video"}
    prompt = content

    lines = content.splitlines()

    if lines and lines[0].strip() == "---":
        try:
            end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
        except StopIteration:
            end = -1

        if end > 0:
            meta: dict[str, str] = {}

            for line in lines[1:end]:
                if ":" not in line:
                    continue
                key, _, value = line.partition(":")
                meta[key.strip().lower()] = value.strip()

            if meta.get("name"):
                name = meta["name"]

            description = meta.get("description", "")

            if meta.get("types"):
                parsed_types = {
                    t.strip().lower()
                    for t in meta["types"].split(",")
                    if t.strip()
                }
                if parsed_types:
                    types = parsed_types

            prompt = "\n".join(lines[end + 1 :]).strip()

    return {
        "id": preset_id,
        "name": name,
        "description": description,
        "types": types,
        "prompt": prompt,
    }


def ensure_builtin_presets() -> None:
    """确保 .knowledge/presets/ 目录与内置模板存在；已存在一律不覆盖。"""
    if state.library_root is None:
        return

    presets_dir = get_presets_dir()
    presets_dir.mkdir(parents=True, exist_ok=True)

    for preset_id, content in BUILTIN_PRESETS.items():
        preset_path = presets_dir / f"{preset_id}.md"

        if preset_path.exists():
            continue

        preset_path.write_text(content, encoding="utf-8")
        logger.info("已生成内置分析模板：{}", preset_path)


def list_analysis_presets() -> list[dict]:
    """列出全部可用模板，按 id 排序；无效文件跳过并记日志。"""
    presets_dir = get_presets_dir()
    presets: list[dict] = []

    if not presets_dir.is_dir():
        return presets

    for path in sorted(presets_dir.glob("*.md")):
        preset_id = path.stem.lower()

        if not PRESET_ID_RE.match(preset_id):
            logger.warning("跳过非法分析模板文件名（需 [a-z0-9][a-z0-9_-]*）：{}", path)
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("无法读取分析模板 {}：{}", path, exc)
            continue

        preset = parse_preset_content(content, preset_id)

        if not preset["prompt"].strip():
            logger.warning("分析模板正文为空，跳过：{}", path)
            continue

        preset["path"] = str(path)
        presets.append(preset)

    return presets


def get_analysis_preset(preset_id: str) -> dict:
    """按 id 取单个模板；不存在或非法抛 ValueError（中文）。"""
    preset_id = (preset_id or "").strip().lower()

    if not PRESET_ID_RE.match(preset_id):
        raise ValueError(f"分析模板 id 非法：{preset_id}")

    for preset in list_analysis_presets():
        if preset["id"] == preset_id:
            return preset

    raise ValueError(f"分析模板不存在：{preset_id}（.knowledge/presets/ 目录）")


def format_analysis_prompt(preset: dict, title: str) -> str:
    """模板正文替换 {title} 占位符。str.replace 实现，正文可含其他花括号。"""
    return preset["prompt"].replace("{title}", title)
