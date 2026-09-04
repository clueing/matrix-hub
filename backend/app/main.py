import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.database import init_db
from app.api import api_router, ws_router
from app.services.scheduler_service import scheduler_service
from app.drivers.playwright_driver import playwright_driver

import sys
import asyncio
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        # 必须使用 Proactor 事件循环策略以支持 Playwright 异步子进程
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用全局生命周期管理
    初始化数据库表结构、启动后台错峰定时调度器，退出时优雅释放资源
    """
    print(f"[INFO] [{settings.APP_NAME}] 正在初始化核心服务与本地数据库...")
    await init_db()
    scheduler_service.start()
    print(f"[READY] [{settings.APP_NAME}] 定时调度服务启动成功")
    
    yield
    
    print(f"[SHUTDOWN] [{settings.APP_NAME}] 正在关闭服务与释放浏览器资源...")
    scheduler_service.shutdown()
    await playwright_driver.stop()
    print(f"[EXIT] [{settings.APP_NAME}] 服务已安全退出")

app = FastAPI(
    title="matrix-hub API",
    description="自媒体多账号矩阵分发平台核心后端",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# 允许跨域（方便前端在开发模式如 :5173 下调试）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册核心 REST API 与 WebSocket 路由
app.include_router(api_router)
app.include_router(ws_router)

@app.get("/api/health", summary="健康检查接口")
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

# 静态资源托管：如果前端已构建 (dist 目录存在)，直接由 FastAPI 托管，实现纯本地一键启动
if settings.FRONTEND_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=settings.FRONTEND_DIST_DIR / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # 排除 API 请求
        if full_path.startswith("api/") or full_path == "ws":
            return None
        file_path = settings.FRONTEND_DIST_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(settings.FRONTEND_DIST_DIR / "index.html")
