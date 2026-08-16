"""QBase 入口。

启动方式：
    python -m app.main
    uvicorn app.main:app --host 127.0.0.1 --port 8765
"""

from __future__ import annotations

import threading
import webbrowser

import uvicorn
from fastapi import FastAPI
from loguru import logger

from app import __version__
from app.config import AppConfig, get_config
from app.logging_conf import setup_logging


def create_app(cfg: AppConfig | None = None) -> FastAPI:
    cfg = cfg or get_config()
    fastapi_app = FastAPI(title="QBase", version=__version__)

    @fastapi_app.get("/api/health")
    async def health() -> dict:
        return {"status": "ok", "version": __version__}

    # 注册 NiceGUI 页面（导入即注册 @ui.page 路由）
    from nicegui import ui

    from app.ui import pages  # noqa: F401

    ui.run_with(
        fastapi_app,
        title="QBase",
        storage_secret="qbase-local",
    )
    return fastapi_app


def _open_browser_later(url: str, delay: float = 1.5) -> None:
    threading.Timer(delay, lambda: webbrowser.open(url)).start()


def main() -> None:
    cfg = get_config()
    setup_logging(cfg.log_level)

    app = create_app(cfg)
    url = f"http://{cfg.host}:{cfg.port}"
    logger.info("QBase v{} 启动于 {}", __version__, url)

    if cfg.open_browser:
        _open_browser_later(url)

    uvicorn.run(app, host=cfg.host, port=cfg.port, log_config=None)


app = create_app()

if __name__ == "__main__":
    main()
