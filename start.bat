@echo off
chcp 65001 >nul
title matrix-hub 自媒体矩阵分发平台

echo ========================================================
echo    🚀 matrix-hub 自媒体多账号矩阵分发平台正在启动...
echo ========================================================

:: 1. 检查 Python 虚拟环境
if not exist ".venv" (
    echo [提示] 正在初始化 Python 虚拟环境...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [提示] 正在安装 Python 依赖库...
    pip install -r backend/requirements.txt
    playwright install chromium
)

:: 2. 检查前端静态产物
if not exist "frontend\dist" (
    echo [提示] 检测到前端尚未构建，正在使用 pnpm 构建前端产物...
    cd frontend
    call pnpm install --ignore-scripts
    call pnpm build
    cd ..
)

:: 3. 自动在系统默认浏览器中打开控制台
start http://127.0.0.1:8000

:: 4. 启动后端核心服务
echo [OK] 正在启动核心服务，请不要关闭本窗口...
.venv\Scripts\python.exe backend\run.py

pause
