import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 将 backend 根目录加入 sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import uvicorn
from app.core.config import settings

def main():
    """
    matrix-hub 后端快捷启动入口
    """
    print("=" * 60)
    print(f"  matrix-hub 自媒体矩阵分发平台服务启动中...")
    print(f"  本地访问地址: http://{settings.HOST}:{settings.PORT}")
    print(f"  接口文档地址: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

if __name__ == "__main__":
    main()
