"""设置相关 API：读取/写回配置、测试 LLM/Embedding 连通性。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services import config_service
from app.services.config_service import ConfigError


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings() -> dict:
    """获取当前配置（明文 Key 已打码）、环境变量状态和配置文件路径。"""
    if not config_service.get_config_path().exists():
        raise HTTPException(status_code=400, detail="未打开知识库或未生成配置")

    return config_service.get_settings_view()


@router.put("")
def put_settings(payload: dict) -> dict:
    """保存配置。payload 是前端提交的配置 patch，校验后写回 config.toml。"""
    try:
        return config_service.save_config(payload)
    except ConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/test-connection")
def test_connection(payload: dict) -> dict:
    """测试 LLM 或 Embedding API 连通性。

    请求体示例：
    {
        "kind": "embedding",
        "override": {
            "embedding": {"base_url": "...", "model": "...", "api_key_env": "..."}
        }
    }
    """
    kind = payload.get("kind")
    override = payload.get("override", {})

    if kind not in {"llm", "embedding"}:
        raise HTTPException(
            status_code=400, detail="kind 必须是 llm 或 embedding"
        )

    try:
        return config_service.test_connection(kind, override)
    except ConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
