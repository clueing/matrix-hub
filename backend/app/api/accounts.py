import io
import shutil
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.core.config import settings
from app.core.event_bus import event_bus
from app.models.account import Account
from app.services.account_service import account_service

router = APIRouter(prefix="/accounts", tags=["账号管理"])

class StartLoginRequest(BaseModel):
    platform: str
    group_name: str = "默认分组"
    proxy_url: Optional[str] = None

class UpdateAccountRequest(BaseModel):
    account_name: Optional[str] = None
    group_name: Optional[str] = None
    proxy_url: Optional[str] = None

@router.get("", summary="获取所有账号列表")
async def list_accounts(
    platform: Optional[str] = None,
    group_name: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Account).order_by(Account.created_at.desc())
    if platform:
        stmt = stmt.where(Account.platform == platform)
    if group_name:
        stmt = stmt.where(Account.group_name == group_name)
    if status:
        stmt = stmt.where(Account.status == status)

    res = await db.execute(stmt)
    accounts = res.scalars().all()
    return {"code": 0, "data": [a.to_dict() for a in accounts]}

@router.post("/login/start", summary="发起扫码登录流程")
async def start_login(payload: StartLoginRequest, db: AsyncSession = Depends(get_db)):
    """拉起独立会话并开始捕获二维码，前端通过 WebSocket 接收二维码数据"""
    try:
        data = await account_service.start_login_session(
            db=db,
            platform=payload.platform,
            group_name=payload.group_name,
            proxy_url=payload.proxy_url
        )
        return {"code": 0, "message": "扫码登录流程已开启", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{account_id}/check", summary="健康检查与状态刷新")
async def check_account(account_id: str, db: AsyncSession = Depends(get_db)):
    """主动测试账号当前登录凭证是否依然有效"""
    try:
        data = await account_service.check_account_health(db, account_id)
        return {"code": 0, "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{account_id}/assist", summary="唤起本地窗口人工辅助 (过滑块/短信)")
async def launch_assist(account_id: str):
    """在宿主机桌面弹出可见的 Chrome 窗口供人工滑动验证码"""
    import asyncio
    asyncio.create_task(account_service.launch_visible_assist(account_id))
    return {"code": 0, "message": "桌面辅助窗口已成功拉起，请在弹窗中操作"}

@router.patch("/{account_id}", summary="修改账号信息 (分组/代理/备注名)")
async def update_account(account_id: str, payload: UpdateAccountRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Account).where(Account.id == account_id))
    acc = res.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="账号不存在")

    if payload.account_name is not None:
        acc.account_name = payload.account_name
    if payload.group_name is not None:
        acc.group_name = payload.group_name
    if payload.proxy_url is not None:
        acc.proxy_url = payload.proxy_url

    await db.commit()
    await db.refresh(acc)
    return {"code": 0, "data": acc.to_dict()}

@router.delete("/{account_id}", summary="删除账号及本地会话缓存")
async def delete_account(account_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Account).where(Account.id == account_id))
    acc = res.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 清理物理存储文件
    acc_dir = settings.SESSIONS_DIR / account_id
    if acc_dir.exists():
        shutil.rmtree(acc_dir, ignore_errors=True)

    await db.delete(acc)
    await db.commit()
    await event_bus.broadcast("account_deleted", {"account_id": account_id})
    return {"code": 0, "message": "账号及本地会话已彻底删除"}

@router.get("/{account_id}/export", summary="导出单账号凭证包 (.zip)")
async def export_account(account_id: str, db: AsyncSession = Depends(get_db)):
    """将账号信息与完整的 storage_state.json 打包供备份与多机迁移"""
    try:
        mem_zip = await account_service.export_single_account(db, account_id)
        filename = f"account_backup_{account_id[:8]}.zip"
        return StreamingResponse(
            mem_zip,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/import", summary="导入账号凭证包 (.zip)")
async def import_account(
    file: UploadFile = File(...),
    overwrite: bool = Query(True, description="若账号已存在是否覆盖"),
    db: AsyncSession = Depends(get_db)
):
    """解析上传的 ZIP 账号归档，一键恢复登录态到当前系统"""
    try:
        content = await file.read()
        res = await account_service.import_account_archive(db, content, overwrite=overwrite)
        return {"code": 0, "message": "账号凭证导入成功", "data": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")
