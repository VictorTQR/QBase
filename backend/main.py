import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config import settings
from api.mineru import router as mineru_router
from api.audio import router as audio_router
from api.vector import router as vector_router
from api.websocket import router as websocket_router
from api.papers import router as papers_router
from api.workspace import router as workspace_router
from api.files import router as files_router
from api import derivatives

app = FastAPI(title="QBase Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mineru_router)
app.include_router(audio_router)
app.include_router(vector_router)
app.include_router(websocket_router)
app.include_router(papers_router)
app.include_router(workspace_router)
app.include_router(files_router)
app.include_router(derivatives.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    logger.info(f"Storage directory created at: {settings.STORAGE_DIR}")

    # 初始化数据库
    from database import init_db

    await init_db()
    logger.info("Database initialized")

    import subprocess

    logger.info("=" * 50)
    logger.info("执行启动健康检查...")

    try:
        subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
        logger.info("✓ ffprobe 检查通过")
    except Exception as e:
        logger.error(f"✗ ffprobe 未安装或不可用: {e}")
        logger.error("  请安装 ffmpeg: https://ffmpeg.org/download.html")

    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
        logger.info("✓ ffmpeg 检查通过")
    except Exception as e:
        logger.error(f"✗ ffmpeg 未安装或不可用: {e}")
        logger.error("  请安装 ffmpeg: https://ffmpeg.org/download.html")

    if settings.SILICONFLOW_API_KEY:
        logger.info("✓ SILICONFLOW_API_KEY 已配置")
    else:
        logger.warning("⚠ SILICONFLOW_API_KEY 未配置，音频转录功能可能不可用")

    if settings.MINERU_API_KEY:
        logger.info("✓ MINERU_API_KEY 已配置")
    else:
        logger.warning("⚠ MINERU_API_KEY 未配置，文档解析功能可能不可用")

    # 初始化 LanceDB
    from vector.lancedb_service import lancedb_service

    lancedb_service.initialize()
    logger.info("✓ LanceDB initialized")

    logger.info("=" * 50)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
