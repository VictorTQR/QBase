"""日志初始化：loguru 统一接管，标准 logging 转发进来。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from loguru import logger

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


class InterceptHandler(logging.Handler):
    """把标准 logging 的记录转发给 loguru。"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = None, 0
        if sys.version_info >= (3, 12):
            while True:
                if frame is None:
                    frame = logging.currentframe()
                else:
                    frame = frame.f_back
                depth += 1
                if frame and frame.f_code.co_filename == logging.__file__:
                    continue
                break
        else:  # pragma: no cover
            if sys.version_info < (3, 8):
                depth = 0
            else:
                depth = 2

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(level: str = "INFO") -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | {name}:{line} - {message}",
    )
    LOG_DIR.mkdir(exist_ok=True)
    logger.add(
        LOG_DIR / "qbase.log",
        level=level,
        rotation="10 MB",
        retention=5,
        encoding="utf-8",
        enqueue=True,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "nicegui", "fastapi"):
        std_logger = logging.getLogger(name)
        std_logger.handlers = []
        std_logger.propagate = True
