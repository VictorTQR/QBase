"""LLM 服务：OpenAI 兼容 chat completions + 长文本分段摘要合并（m6）。"""

from __future__ import annotations

import httpx

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
3. 如果有行动项或待办事项，请单独列出。
4. 不要编造不存在的信息。
5. 使用 Markdown 格式输出。

分段摘要：
{partial_summaries}"""


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
