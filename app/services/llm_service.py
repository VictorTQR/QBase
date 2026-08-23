"""LLM 服务：OpenAI 兼容 chat completions + 长文本分段摘要合并（m6）+ AI 建议标签（m16）。"""

from __future__ import annotations

import httpx
import json

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


def chat_completion(messages: list[dict], config: dict) -> str:
    """调用 OpenAI 兼容 /chat/completions API。"""
    url = config["base_url"].rstrip("/") + "/chat/completions"

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": config.get("temperature", 0.2),
        "max_tokens": config.get("max_tokens", 2000),
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

    return choices[0].get("message", {}).get("content", "")


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
