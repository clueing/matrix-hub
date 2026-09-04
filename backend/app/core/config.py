from pathlib import Path
from pydantic_settings import BaseSettings

# Root directory of matrix-hub
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
DATA_DIR = PROJECT_ROOT / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
UPLOADS_DIR = DATA_DIR / "uploads"
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"

# Ensure data directories exist
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    APP_NAME: str = "matrix-hub"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Paths
    PROJECT_ROOT: Path = PROJECT_ROOT
    DATA_DIR: Path = DATA_DIR
    SESSIONS_DIR: Path = SESSIONS_DIR
    UPLOADS_DIR: Path = UPLOADS_DIR
    FRONTEND_DIST_DIR: Path = FRONTEND_DIST_DIR
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR}/matrix.db"
    
    # Automation & Concurrency
    MAX_BROWSER_CONCURRENCY: int = 1
    DEFAULT_HEADLESS: bool = True
    BROWSER_SLOW_MO: int = 50  # ms delay between operations for natural human-like typing
    
    # Staggered Scheduling Defaults
    DEFAULT_STAGGER_INTERVAL: int = 300  # 5 minutes
    DEFAULT_STAGGER_JITTER: int = 120    # +- 2 minutes

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
