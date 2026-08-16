@echo off
REM 快速启动 QBase（依赖仓库根 .venv）
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到 .venv，请先执行 uv sync 创建虚拟环境。
    pause
    exit /b 1
)

echo 正在启动 QBase ...
.venv\Scripts\python.exe -m app.main

endlocal
