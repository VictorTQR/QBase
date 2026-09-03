"""LLM Batch 批处理客户端（m21）：OpenAI 风格 files + batches 三段式。

智谱（…/api/paas/v4）与硅基流动（…/v1）路径结构一致：
上传 JSONL（POST {base_url}/files，purpose=batch）→ 创建批任务
（POST {base_url}/batches）→ 轮询（GET {base_url}/batches/{id}）→
下载结果（GET {base_url}/files/{file_id}/content）。
endpoint 参数值从 base_url 末段推导（/v4/chat/completions、
/v1/chat/completions），不硬编码域名，网关代理同样可用。
Batch 模式五折计费、不受在线限流约束，预计 24 小时内完成。
"""

from __future__ import annotations

import json

import httpx

from app.services.llm_service import _build_payload, _extract_content

# 单个输入文件的最大请求数（按硅基流动较严限制取安全值，智谱上限 5 万）
MAX_REQUESTS_PER_FILE = 4000

# 终态：completed 正常完成；failed / expired / cancelled 时已完成请求
# 仍会写入输出文件（expired 未完成请求才进错误文件），一律先回收再判失败
BATCH_TERMINAL_STATUSES = {"completed", "failed", "expired", "cancelled"}

# 硅基流动 in_queue、智谱 validating / finalizing 等中间态一律继续轮询


class BatchError(RuntimeError):
    """Batch API 调用失败。"""


class BatchAuthError(BatchError):
    """认证失败（401/403），密钥问题应早失败。"""


class BatchMissingError(BatchError):
    """批任务不存在（404），轮询没有意义。"""


class BatchUnsupportedError(BatchError):
    """当前提供商不支持 Batch 接口（提交 404/405）。"""


def derive_batch_endpoint(config: dict) -> str:
    """从 base_url 末段推导 Batch 请求的 endpoint 参数值。

    智谱 …/api/paas/v4 → /v4/chat/completions；硅基流动 …/v1 →
    /v1/chat/completions。
    """
    last_segment = config["base_url"].rstrip("/").rsplit("/", 1)[-1]
    return f"/{last_segment}/chat/completions"


def _headers(config: dict) -> dict:
    return {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }


def build_jsonl_lines(
    requests: list[tuple[str, list[dict]]], config: dict
) -> str:
    """把 (custom_id, messages) 列表序列化为 Batch 输入 JSONL 文本。

    每行 body 复用 _build_payload（model / temperature / max_tokens /
    thinking 与 sync/async 模式含义一致）。
    """
    endpoint = derive_batch_endpoint(config)
    lines = [
        json.dumps(
            {
                "custom_id": custom_id,
                "method": "POST",
                "url": endpoint,
                "body": _build_payload(messages, config),
            },
            ensure_ascii=False,
        )
        for custom_id, messages in requests
    ]

    return "\n".join(lines) + "\n"


def upload_input_file(config: dict, jsonl_text: str) -> str:
    """上传 Batch 输入 JSONL（purpose=batch），返回 input_file_id。"""
    base = config["base_url"].rstrip("/")

    with httpx.Client(timeout=config.get("timeout", 180)) as client:
        response = client.post(
            f"{base}/files",
            headers={"Authorization": f"Bearer {config['api_key']}"},
            files={
                "file": (
                    "batch_input.jsonl",
                    jsonl_text.encode("utf-8"),
                    "application/jsonl",
                )
            },
            data={"purpose": "batch"},
        )

    if response.status_code in (404, 405):
        raise BatchUnsupportedError(
            f"当前提供商不支持 Batch 文件接口（{response.status_code} "
            f"{base}/files），请将该功能的 mode 改回 sync / async"
        )

    if response.status_code in (401, 403):
        raise BatchAuthError(
            f"Batch 文件上传被拒绝（{response.status_code}），请检查 API Key"
        )

    if response.status_code != 200:
        raise BatchError(
            f"Batch 文件上传错误：{response.status_code} {response.text[:500]}"
        )

    file_id = (response.json() or {}).get("id")

    if not file_id:
        raise BatchError(
            f"Batch 文件上传未返回文件 id：{response.text[:300]}"
        )

    return file_id


def create_batch(config: dict, input_file_id: str, metadata: dict) -> dict:
    """创建批任务，返回 batch 对象（含 id / status）。

    completion_window 留空时不发送（智谱已废弃该参数，按负载调度）；
    硅基流动支持 24h - 336h。
    """
    base = config["base_url"].rstrip("/")
    payload: dict = {
        "input_file_id": input_file_id,
        "endpoint": derive_batch_endpoint(config),
        "metadata": metadata,
    }

    completion_window = str(config.get("completion_window") or "").strip()

    if completion_window:
        payload["completion_window"] = completion_window

    with httpx.Client(timeout=config.get("timeout", 180)) as client:
        response = client.post(
            f"{base}/batches", headers=_headers(config), json=payload
        )

    if response.status_code in (404, 405):
        raise BatchUnsupportedError(
            f"当前提供商不支持 Batch 批处理接口（{response.status_code} "
            f"{base}/batches），请将该功能的 mode 改回 sync / async"
        )

    if response.status_code in (401, 403):
        raise BatchAuthError(
            f"Batch 任务创建被拒绝（{response.status_code}），请检查 API Key"
        )

    if response.status_code != 200:
        raise BatchError(
            f"Batch 任务创建错误：{response.status_code} {response.text[:500]}"
        )

    batch = response.json() or {}

    if not batch.get("id"):
        raise BatchError(f"Batch 任务创建未返回 id：{response.text[:300]}")

    return batch


def retrieve_batch(config: dict, batch_id: str) -> dict:
    """查询批任务状态（status / request_counts / output_file_id 等）。"""
    base = config["base_url"].rstrip("/")

    try:
        response = httpx.get(
            f"{base}/batches/{batch_id}",
            headers=_headers(config),
            timeout=config.get("timeout", 180),
        )
    except httpx.HTTPError as exc:
        raise BatchError(f"Batch 状态查询网络异常：{exc}") from exc

    if response.status_code == 404:
        raise BatchMissingError(f"Batch 任务不存在（batch_id={batch_id}）")

    if response.status_code in (401, 403):
        raise BatchAuthError(
            f"Batch 状态查询被拒绝（{response.status_code}），请检查 API Key"
        )

    if response.status_code != 200:
        raise BatchError(
            f"Batch 状态查询错误：{response.status_code} {response.text[:300]}"
        )

    return response.json() or {}


def download_results(config: dict, file_id: str) -> list[dict]:
    """下载并解析结果 JSONL 文件（输出/错误文件通用），返回行对象列表。"""
    base = config["base_url"].rstrip("/")

    with httpx.Client(timeout=config.get("timeout", 180)) as client:
        response = client.get(
            f"{base}/files/{file_id}/content",
            headers={"Authorization": f"Bearer {config['api_key']}"},
        )

    if response.status_code == 404:
        raise BatchMissingError(f"Batch 结果文件不存在（file_id={file_id}）")

    if response.status_code in (401, 403):
        raise BatchAuthError(
            f"Batch 结果下载被拒绝（{response.status_code}），请检查 API Key"
        )

    if response.status_code != 200:
        raise BatchError(
            f"Batch 结果下载错误：{response.status_code} {response.text[:300]}"
        )

    lines: list[dict] = []

    for line in response.text.splitlines():
        line = line.strip()

        if not line:
            continue

        lines.append(json.loads(line))

    return lines


def extract_result(line: dict, max_tokens: int) -> tuple[str | None, str | None]:
    """从结果行提取 (正文, 错误信息)，二选一。

    成功行（response.status_code==200）复用 _extract_content，含
    max_tokens 截断与空内容检测；失败行优先取顶层 error 字段
    （如硅基流动 batch_expired），其次 response.body.error。
    """
    error = line.get("error")

    if isinstance(error, dict) and (error.get("code") or error.get("message")):
        detail = " ".join(
            str(part) for part in (error.get("code"), error.get("message")) if part
        )
        return None, detail

    response = line.get("response") or {}
    status_code = response.get("status_code")
    body = response.get("body")

    if status_code == 200:
        try:
            return _extract_content(body if isinstance(body, dict) else {}, max_tokens), None
        except RuntimeError as exc:
            return None, str(exc)

    body_error = body.get("error") if isinstance(body, dict) else None

    if isinstance(body_error, dict) and (
        body_error.get("code") or body_error.get("message")
    ):
        detail = " ".join(
            str(part)
            for part in (body_error.get("code"), body_error.get("message"))
            if part
        )
    else:
        detail = json.dumps(body, ensure_ascii=False)[:200] if body else "请求失败"

    if status_code:
        return None, f"HTTP {status_code}：{detail}"

    return None, detail


def split_requests_chunks(
    requests: list[tuple[str, list[dict]]],
) -> list[list[tuple[str, list[dict]]]]:
    """按单文件请求上限拆分输入（保持顺序），每段 ≤ MAX_REQUESTS_PER_FILE。"""
    return [
        requests[start : start + MAX_REQUESTS_PER_FILE]
        for start in range(0, len(requests), MAX_REQUESTS_PER_FILE)
    ]
