import asyncio
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.metrics_service import metrics_service

router = APIRouter(prefix="/metrics", tags=["数据资产与监控"])

class SyncMetricsRequest(BaseModel):
    account_id: Optional[str] = None

@router.get("/overview", summary="获取全矩阵数据大盘资产概览与爆款排行榜")
async def get_overview(db: AsyncSession = Depends(get_db)):
    """
    返回全矩阵总粉丝量、总播放量、总获赞量、各平台数据分布及 Top 10 爆款作品
    """
    data = await metrics_service.get_matrix_overview(db)
    return {"code": 0, "data": data}

@router.post("/sync", summary="触发全矩阵或单账号指标数据回流同步")
async def sync_metrics(payload: Optional[SyncMetricsRequest] = None):
    """
    触发指标同步，单账号即时返回结果，全矩阵在后台执行并通过 WebSocket 广播进度
    """
    if payload and payload.account_id:
        res = await metrics_service.sync_account_metrics(payload.account_id)
        if not res.get("success"):
            raise HTTPException(status_code=400, detail=res.get("error") or res.get("message") or "同步失败")
        return {"code": 0, "message": "账号数据同步成功", "data": res}

    if metrics_service.is_syncing:
        return {"code": 0, "message": "全矩阵数据同步已在进行中，请查看日志推流"}

    asyncio.create_task(metrics_service.sync_all_metrics())
    return {"code": 0, "message": "全矩阵指标巡检已在后台启动，系统将自动同步各平台数据"}

@router.post("/sync/{account_id}", summary="即时同步单个账号数据指标")
async def sync_single_account_metrics(account_id: str):
    """
    立即同步指定账号的创作者中心数据
    """
    res = await metrics_service.sync_account_metrics(account_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error") or res.get("message") or "同步失败")
    return {"code": 0, "message": "账号指标同步成功", "data": res}
