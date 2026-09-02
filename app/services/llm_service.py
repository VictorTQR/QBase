"""LLM 服务：OpenAI 兼容 chat completions + 长文本分段摘要合并（m6）+ AI 建议标签（m16）
+ 深度分析（m18，模板提示词 + 时间窗切块合并）。"""

from __future__ import annotations

import httpx
import json
import re

SYSTEM_PROMPT = """你是一个知识管理助手。
请根据用户提供的内容生成中文总结。

要求：
1. 先给出 3-5 句核心总结。
2. 再列出 5-15 个关键点，使用 Markdown 无序列表。
3. 如果内容包含行动项或待办事项，请单独列出。
4. 不要编造不存在的信息。
5. 使用 Markdown 格式输出。
6. 不要输出与内容无关的开场白。"""

CHUNK_SUMMARY_PROMPT = """请总结下面这段内容，保留关键信息，输出简洁中文摘要。
不要编造不存在的信息。

内容：
{chunk}"""

MERGE_SUMMARY_PROMPT = """下面是一篇长内容的多段摘要。
请根据这些摘要生成最终的中文总结。

要求：
1. 先给出 3-5 句核心总结。
2. 再列出 5-15 个关键点，使用 Markdown 无序列表。
3. 如果内容包含行动项或待办事项，请单独列出。
4. 不要编造不存在的信息。
5. 使用 Markdown 格式输出。

分段摘要：
{partial_summaries}"""

TAGGING_SYSTEM_PROMPT = """你是一个知识管理打标助手。
根据提供的资产标题与内容，为主题打标签。

要求：
1. 输出 3-8 个标签，中文为主，专有名词可用英文。
2. 每个标签不超过 10 个字符，不要包含逗号。
3. 优先从「已有标签」中选用语义匹配的，再补充必要的新标签。
4. 只输出 JSON 字符串数组（如 ["AI", "播客"]），不要输出任何其他内容。"""

# 深度分析（m18）：长内容超出 max_input_chars 时按时间窗逐窗分析后合并。
# 时间戳行格式 [MM:SS] 或 [H:MM:SS]（由 analysis_service 构造输入时生成）。
TIMESTAMP_LINE_RE = re.compile(r"^\[(\d{1,3}):(\d{2})(?::(\d{2}))?\]")

ANALYSIS_WINDOW_PROMPT = """这是完整内容的一个时间窗（第 {index} / {total} 窗，覆盖 [{start} – {end}]）。
请只针对这个时间窗输出分析，保持既定的 Markdown 结构与章节层次；
不要臆测未出现在本窗中的内容。

内容：
{window_text}"""

ANALYSIS_MERGE_PROMPT = """下面是一份长内容按时间窗分段生成的分析结果。
请把它们合并成一份完整的最终分析：
1. 保持既定的 Markdown 结构（合并同主题段落，重排章节编号）。
2. 保留所有时间戳引用，不要丢弃或改写时间。
3. 「手法清单 / 摘录」类汇总章节需跨窗去重合并，按时间排序。
4. 不要编造分段分析中不存在的信息。

分段分析：
{partial_analyses}"""


def chat_completion(messages: list[dict], config: dict) -> str:
    """调用 OpenAI 兼容 /chat/completions API。"""
    url = config["base_url"].rstrip("/") + "/chat/completions"

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    max_tokens = config.get("max_tokens", 2000)

    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": config.get("temperature", 0.2),
        "max_tokens": max_tokens,
    }

    with httpx.Client(timeout=config.get("timeout", 180)) as client:
        response = client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise RuntimeError(
                f"LLM API 错误：{response.status_code} {response.text[:500]}"
            )

        data = response.json()

    choices = data.get("choices", [])

    if not choices:
        raise RuntimeError("LLM API 返回空结果")

    choice = choices[0]
    content = (choice.get("message") or {}).get("content") or ""
    finish_reason = choice.get("finish_reason")

    if finish_reason == "length":
        reasoning_tokens = (
            (data.get("usage") or {}).get("completion_tokens_details") or {}
        ).get("reasoning_tokens")
        reasoning_part = (
            f"，其中思考消耗 {reasoning_tokens} token"
            if reasoning_tokens is not None
            else ""
        )
        raise RuntimeError(
            f"LLM 输出在 max_tokens={max_tokens} 处被截断（finish_reason=length"
            f"{reasoning_part}）。思考型模型的推理 token 计入 max_tokens，"
            "请在配置中调大后重试"
        )

    if not content.strip():
        raise RuntimeError(
            f"LLM 返回空内容（finish_reason={finish_reason}），请重试或检查模型配置"
        )

    return content


def split_text_for_summary(text: str, chunk_chars: int) -> list[str]:
    """长文本按段落切分（段落优先，超长段落硬切），用于分段摘要。"""
    text = text.strip()

    if not text:
        return []

    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 1 <= chunk_chars:
            current = f"{current}\n{paragraph}" if current else paragraph
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) <= chunk_chars:
            current = paragraph
        else:
            start = 0
            while start < len(paragraph):
                end = min(start + chunk_chars, len(paragraph))
                chunks.append(paragraph[start:end])
                start = end

    if current:
        chunks.append(current)

    return chunks


def summarize_text(text: str, config: dict) -> str:
    """生成总结：短文本直接总结；超过 max_input_chars 分段摘要后合并。"""
    text = text.strip()

    if not text:
        raise ValueError("输入文本为空，无法生成总结")

    max_input_chars = config.get("max_input_chars", 24000)
    chunk_chars = config.get("chunk_chars", 6000)

    if len(text) <= max_input_chars:
        return chat_completion(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            config,
        )

    chunks = split_text_for_summary(text, chunk_chars)

    if not chunks:
        raise ValueError("文本切分后为空")

    if len(chunks) == 1:
        return chat_completion(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": chunks[0]},
            ],
            config,
        )

    partial_summaries: list[str] = []

    for chunk in chunks:
        partial = chat_completion(
            [
                {
                    "role": "system",
                    "content": "你是一个文本摘要助手。请输出简洁中文摘要。",
                },
                {
                    "role": "user",
                    "content": CHUNK_SUMMARY_PROMPT.format(chunk=chunk),
                },
            ],
            config,
        )
        partial_summaries.append(partial.strip())

    combined = "\n\n---\n\n".join(
        f"【第 {i + 1} 段摘要】\n{summary}"
        for i, summary in enumerate(partial_summaries)
    )

    return chat_completion(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": MERGE_SUMMARY_PROMPT.format(partial_summaries=combined),
            },
        ],
        config,
    )


def _line_start_seconds(line: str) -> float | None:
    """解析行首时间戳 [MM:SS] / [H:MM:SS] 为秒；无时间戳返回 None。"""
    match = TIMESTAMP_LINE_RE.match(line.strip())

    if match is None:
        return None

    first, minute, second = match.group(1), match.group(2), match.group(3)

    if second is None:
        return int(first) * 60 + int(minute)

    return int(first) * 3600 + int(minute) * 60 + int(second)


def _format_seconds(total_seconds: int) -> str:
    hours, rem = divmod(total_seconds, 3600)
    minutes, secs = divmod(rem, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"


def split_by_time_windows(text: str, window_minutes: int) -> list[dict]:
    """按行首时间戳把带时间戳文本聚成时间窗（时间感知版切块，m18）。

    每窗 {start, end, text}：start/end 为窗内首/末时间戳（秒），
    无时间戳的行归入当前窗；输入完全无时间戳时返回单窗原文。
    """
    window_seconds = max(60, int(window_minutes) * 60)
    windows: list[dict] = []
    current: dict | None = None
    current_index = -1

    for line in text.splitlines():
        if not line.strip():
            continue

        seconds = _line_start_seconds(line)

        if seconds is None:
            if current is None:
                current = {"start": None, "end": None, "lines": []}
                windows.append(current)
                current_index = -1
        else:
            index = int(seconds // window_seconds)

            if index != current_index:
                current = {"start": seconds, "end": seconds, "lines": []}
                windows.append(current)
                current_index = index
            else:
                current["end"] = seconds

        current["lines"].append(line)

    result: list[dict] = []

    for window in windows:
        if not window["lines"]:
            continue

        start = window["start"] if window["start"] is not None else 0
        end = window["end"] if window["end"] is not None else start

        result.append(
            {
                "start": start,
                "end": end,
                "text": "\n".join(window["lines"]),
            }
        )

    return result


def analyze_text(system_prompt: str, text: str, config: dict) -> str:
    """深度分析（m18）：模板提示词为 system，带时间戳全文为 user。

    短输入单次调用；超过 max_input_chars 时按时间窗切块：逐窗调用
    （附「只分析该时间窗」指令）再用 ANALYSIS_MERGE_PROMPT 合并成
    完整分析，合并要求保留时间戳与模板结构。
    """
    text = text.strip()

    if not text:
        raise ValueError("输入文本为空，无法生成分析")

    max_input_chars = config.get("max_input_chars", 100000)

    if len(text) <= max_input_chars:
        return chat_completion(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            config,
        )

    window_minutes = config.get("window_minutes", 15)
    windows = split_by_time_windows(text, window_minutes)

    if len(windows) <= 1:
        raise ValueError(
            "输入过长且无法按时间戳分窗（转录缺少时间分段），"
            "请在 [llm.analysis] 中调大 max_input_chars 或改用长上下文模型"
        )

    partial_analyses: list[str] = []

    for index, window in enumerate(windows):
        user_content = (
            f"{system_prompt.strip()}\n\n"
            + ANALYSIS_WINDOW_PROMPT.format(
                index=index + 1,
                total=len(windows),
                start=_format_seconds(window["start"]),
                end=_format_seconds(window["end"]),
                window_text=window["text"],
            )
        )

        partial = chat_completion(
            [
                {"role": "system", "content": "你是一个内容分析助手，输出简体中文 Markdown。"},
                {"role": "user", "content": user_content},
            ],
            config,
        )
        partial_analyses.append(partial.strip())

    combined = "\n\n---\n\n".join(
        f"【第 {i + 1} 窗 · {_format_seconds(w['start'])} – {_format_seconds(w['end'])}】\n{partial}"
        for i, (w, partial) in enumerate(zip(windows, partial_analyses))
    )

    return chat_completion(
        [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": ANALYSIS_MERGE_PROMPT.format(partial_analyses=combined),
            },
        ],
        config,
    )


def _parse_tag_list(raw: str) -> list[str]:
    """宽容解析 LLM 返回的标签 JSON 数组。

    剥离 markdown code fence 与前后废话，截取首个 [ 到末个 ] 后
    json.loads；非数组或解析失败抛 RuntimeError。
    """
    text = raw.strip()

    if text.startswith("```"):
        lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()

    start = text.find("[")
    end = text.rfind("]")

    if start < 0 or end <= start:
        raise RuntimeError("AI 返回格式异常，请重试")

    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise RuntimeError("AI 返回格式异常，请重试") from exc

    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise RuntimeError("AI 返回格式异常，请重试")

    return data


def suggest_tags(
    title: str,
    text: str,
    existing_tags: list[str],
    config: dict,
) -> list[str]:
    """AI 建议标签：标题 + 内容（截断）+ 已有标签 → JSON 数组（m16）。"""
    max_input_chars = config.get("max_input_chars", 4000)
    content = text.strip()[:max_input_chars]

    if not content:
        raise ValueError("没有可用于打标的内容")

    existing = "、".join(existing_tags) if existing_tags else "（暂无）"

    user_content = (
        f"资产标题：{title}\n\n"
        f"已有标签：{existing}\n\n"
        f"内容：\n{content}"
    )

    raw = chat_completion(
        [
            {"role": "system", "content": TAGGING_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        config,
    )

    return _parse_tag_list(raw)
