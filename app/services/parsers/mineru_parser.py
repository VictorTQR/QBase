"""MinerU 精准解析 API v4（https://mineru.net/apiManage/docs）。

本地文件的唯一上传入口是批量接口（2026-08-21 接真实 API 核对）：
1. POST /api/v4/file-urls/batch   申请 OSS 上传链接（≤50 文件/批）。
   请求体只传 files=[{name}] + model_version；
   响应 data = {batch_id, file_urls}，file_urls 是纯 URL 字符串列表，
   按请求 files 顺序一一对应
2. PUT  {upload_url}              上传文件（不能带 Content-Type 头）
3. 上传完成后系统自动提交解析任务，无需再调提交接口
4. GET  /api/v4/extract-results/batch/{batch_id}  轮询：
   data.extract_result[] = {file_name, state, full_zip_url, err_msg}
限制：单文件 ≤200MB、≤200 页；上传链接 24h 有效。
"""

from __future__ import annotations

import httpx
from pathlib import Path

from app.services.config_service import get_api_key
from app.services.parsers.base import (
    DocumentParser,
    ParseFileState,
    ParseSubmission,
)

DEFAULT_BASE_URL = "https://mineru.net"
DEFAULT_MODEL_VERSION = "vlm"
DEFAULT_TOKEN_ENV = "MINERU_API_TOKEN"
MAX_FILE_BYTES = 200 * 1024 * 1024


class MineruParser(DocumentParser):
    name = "mineru"

    def __init__(self, config: dict):
        self.base_url = (
            str(config.get("base_url") or DEFAULT_BASE_URL).strip().rstrip("/")
        )
        self.model_version = (
            str(config.get("model_version") or DEFAULT_MODEL_VERSION).strip()
        )
        self.token_env = str(config.get("token_env") or DEFAULT_TOKEN_ENV).strip()
        self.timeout = int(config.get("timeout", 30) or 30)
        self.token = get_api_key(self.token_env)

        if not self.token:
            raise ValueError(
                f"未配置 MinerU token：请设置环境变量 {self.token_env}，"
                "或写入 .knowledge/secrets.toml 的 [keys]"
            )

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def submit(self, paths: list[Path]) -> ParseSubmission:
        # 申请上传链接（QBase 一资产一任务，固定 batch-of-1）。
        # 请求体按官方示例只传 files + model_version。
        resp = httpx.post(
            f"{self.base_url}/api/v4/file-urls/batch",
            headers=self._headers(),
            json={
                "files": [{"name": p.name} for p in paths],
                "model_version": self.model_version,
            },
            timeout=self.timeout,
        )

        data = self._unwrap(resp, "申请上传链接")

        # file_urls 是纯 URL 字符串列表，按请求 files 顺序一一对应（官方示例
        # requests.put(urls[i])），不是对象列表
        urls = data.get("file_urls")

        if not isinstance(urls, list) or len(urls) != len(paths):
            raise ValueError(
                f"MinerU 返回的上传链接数量与文件数不一致：{urls!r}"
            )

        files = [
            {"name": path.name, "upload_url": url}
            for path, url in zip(paths, urls)
        ]

        # 上传。注意：不能带 Content-Type 头，否则 OSS 签名校验失败
        for file_info, path in zip(files, paths):
            up = httpx.put(
                file_info["upload_url"],
                content=path.read_bytes(),
                timeout=600,
            )

            if up.status_code != 200:
                raise ValueError(
                    f"上传 {file_info['name']} 失败：HTTP {up.status_code}"
                )

        # 上传完成即自动提交解析
        return ParseSubmission(batch_id=data["batch_id"], files=files)

    def poll(self, submission: ParseSubmission) -> list[ParseFileState]:
        resp = httpx.get(
            f"{self.base_url}/api/v4/extract-results/batch/{submission.batch_id}",
            headers=self._headers(),
            timeout=self.timeout,
        )

        data = self._unwrap(resp, "查询解析结果")

        return [
            ParseFileState(
                name=str(item.get("file_name", "")),
                state=str(item.get("state", "running")),
                err_msg=item.get("err_msg"),
                full_zip_url=item.get("full_zip_url"),
            )
            for item in data["extract_result"]
        ]

    def fetch(self, state: ParseFileState) -> bytes:
        if not state.full_zip_url:
            raise ValueError("该文件没有可下载的解析结果")

        resp = httpx.get(state.full_zip_url, timeout=600, follow_redirects=True)

        if resp.status_code != 200:
            raise ValueError(f"下载解析结果失败：HTTP {resp.status_code}")

        return resp.content

    def _unwrap(self, resp: httpx.Response, action: str) -> dict:
        """校验响应状态与业务码，返回 data 段。"""
        if resp.status_code in (401, 403):
            raise ValueError(f"MinerU {action}失败：token 无效（HTTP {resp.status_code}）")

        if resp.status_code != 200:
            raise ValueError(
                f"MinerU {action}失败：HTTP {resp.status_code} {resp.text[:200]}"
            )

        try:
            body = resp.json()
        except Exception as exc:
            raise ValueError(f"MinerU {action}返回非 JSON：{exc}") from exc

        if body.get("code") != 0:
            raise ValueError(f"MinerU {action}失败：{body.get('msg') or body}")

        data = body.get("data")

        if not isinstance(data, dict):
            raise ValueError(f"MinerU {action}返回缺少 data 段")

        return data
