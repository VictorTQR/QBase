from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger


class QBaseError(Exception):
    """QBase 基础错误类"""

    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class FileNotFoundError(QBaseError):
    """文件未找到错误"""

    def __init__(self, message: str = "文件未找到", details: dict = None):
        super().__init__(message, status_code=404, details=details)


class WorkspaceNotInitializedError(QBaseError):
    """工作区未初始化错误"""

    def __init__(self, message: str = "工作区未初始化", details: dict = None):
        super().__init__(message, status_code=400, details=details)


async def qbase_error_handler(request: Request, exc: QBaseError):
    """QBase 错误处理器"""
    logger.error(f"[{exc.status_code}] {exc.message}: {exc.details}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "details": exc.details,
        },
    )


async def general_error_handler(request: Request, exc: Exception):
    """通用错误处理器"""
    logger.exception(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "内部服务器错误",
            "details": {"type": type(exc).__name__},
        },
    )


def setup_error_handlers(app):
    """设置错误处理器"""
    app.add_exception_handler(QBaseError, qbase_error_handler)
    app.add_exception_handler(Exception, general_error_handler)
