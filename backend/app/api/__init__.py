from fastapi import APIRouter
from app.api.accounts import router as accounts_router
from app.api.tasks import router as tasks_router
from app.api.videos import router as videos_router
from app.api.settings import router as settings_router
from app.api.ws import router as ws_router

api_router = APIRouter(prefix="/api")
api_router.include_router(accounts_router)
api_router.include_router(tasks_router)
api_router.include_router(videos_router)
api_router.include_router(settings_router)

__all__ = ["api_router", "ws_router"]
