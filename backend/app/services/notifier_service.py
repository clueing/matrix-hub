import httpx
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.setting import SystemSetting

class NotifierService:
    """
    Webhook 机器人消息告警服务
    支持飞书、钉钉、企业微信群机器人的富文本卡片通知
    """

    async def get_setting(self, db: AsyncSession, key: str, default: Optional[str] = None) -> Optional[str]:
        res = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
        setting = res.scalar_one_or_none()
        return setting.value if setting else default

    async def send_notification(self, title: str, content: str, level: str = "INFO", db: Optional[AsyncSession] = None):
        """发送告警通知到配置好的 Webhook 机器人"""
        webhook_url = None
        channel = "feishu"

        try:
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                webhook_url = await self.get_setting(session, "webhook_url")
                channel = (await self.get_setting(session, "webhook_channel")) or "feishu"
        except Exception:
            return

        if not webhook_url:
            return  # 未配置 webhook 则静默跳过

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                if channel == "feishu":
                    # 飞书文本/卡片消息
                    payload = {
                        "msg_type": "text",
                        "content": {
                            "text": f"【matrix-hub 通知】\n标 题: {title}\n级 别: {level}\n内 容: {content}"
                        }
                    }
                    await client.post(webhook_url, json=payload)
                elif channel == "dingtalk":
                    # 钉钉机器人消息
                    payload = {
                        "msg_type": "text",
                        "text": {
                            "content": f"【matrix-hub】{title}\n[{level}] {content}"
                        }
                    }
                    await client.post(webhook_url, json=payload)
                elif channel == "wecom":
                    # 企业微信机器人消息
                    payload = {
                        "msgtype": "text",
                        "text": {
                            "content": f"【matrix-hub】{title}\n[{level}] {content}"
                        }
                    }
                    await client.post(webhook_url, json=payload)
            except Exception:
                pass  # 告警失败不阻断主流程

notifier_service = NotifierService()
