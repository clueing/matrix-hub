@chcp 65001 >nul
@echo off
title MatrixHub 自媒体多账号矩阵分发平台

echo ========================================================
echo   MatrixHub 自媒体多账号矩阵分发平台正在启动...
echo ========================================================

REM 1. 检查 Python 虚拟环境
if exist ".venv" goto CHECK_FRONTEND
echo [INFO] 正在初始化 Python 虚拟环境...
python -m venv .venv
call .venv\Scripts\activate.bat
echo [INFO] 正在安装 Python 依赖库...
pip install -r backend/requirements.txt
playwright install chromium

:CHECK_FRONTEND
REM 2. 检查前端静态产物
if exist "frontend\dist" goto START_APP
echo [INFO] 检测到前端尚未构建，正在使用 pnpm 构建前端产物...
cd frontend
call pnpm install --ignore-scripts
call pnpm build
cd ..

:START_APP
REM 3. 自动在系统默认浏览器中打开控制台
start http://127.0.0.1:8000

REM 4. 启动后端核心服务
echo [OK] 正在启动核心服务，请保持本窗口运行...
.venv\Scripts\python.exe backend\run.py

pause
