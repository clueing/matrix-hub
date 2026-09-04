from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.setting import SystemSetting
from app.services.notifier_service import notifier_service

router = APIRouter(prefix="/settings", tags=["系统设置"])

class UpdateSettingsRequest(BaseModel):
    settings: Dict[str, str]

class TestWebhookRequest(BaseModel):
    webhook_url: str
    channel: str = "feishu"

@router.get("", summary="获取全部系统配置")
async def get_settings(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SystemSetting))
    items = res.scalars().all()
    data = {item.key: item.value for item in items}
    # 默认值兜底
    defaults = {
        "stagger_interval": "300",
        "stagger_jitter": "60",
        "max_concurrency": "1",
        "webhook_url": "",
        "webhook_channel": "feishu"
    }
    for k, v in defaults.items():
        if k not in data:
            data[k] = v
    return {"code": 0, "data": data}

@router.put("", summary="更新系统配置")
async def update_settings(payload: UpdateSettingsRequest, db: AsyncSession = Depends(get_db)):
    for k, v in payload.settings.items():
        res = await db.execute(select(SystemSetting).where(SystemSetting.key == k))
        item = res.scalar_one_or_none()
        if item:
            item.value = str(v)
        else:
            item = SystemSetting(key=k, value=str(v), description="用户自定义配置")
            db.add(item)
    await db.commit()
    return {"code": 0, "message": "系统设置已更新"}

@router.post("/test-webhook", summary="测试 Webhook 机器人告警连通性")
async def test_webhook(payload: TestWebhookRequest):
    try:
        import httpx
        async with httpx.AsyncClient(timeout=8) as client:
            if payload.channel == "feishu":
                body = {
                    "msg_type": "text",
                    "content": {"text": "【matrix-hub】恭喜！飞书机器人告警通知测试成功！"}
                }
            elif payload.channel == "dingtalk":
                body = {
                    "msg_type": "text",
                    "text": {"content": "【matrix-hub】恭喜！钉钉机器人告警通知测试成功！"}
                }
            else:
                body = {
                    "msgtype": "text",
                    "text": {"content": "【matrix-hub】恭喜！企业微信机器人告警通知测试成功！"}
                }
            resp = await client.post(payload.webhook_url, json=body)
            if resp.status_code >= 400:
                raise HTTPException(status_code=400, detail=f"机器人接口返回错误: {resp.text}")
        return {"code": 0, "message": "测试通知已发送，请检查群聊消息"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"发送失败: {str(e)}")
