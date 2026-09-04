from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from app.core.database import Base

class SystemSetting(Base):
    """系统全局配置表，以键值对形式存储运行参数与 Webhook 配置"""
    __tablename__ = "system_settings"

    key = Column(String(64), primary_key=True, comment="配置键名")
    value = Column(Text, nullable=False, comment="配置值 (支持纯文本或 JSON 字符串)")
    description = Column(String(255), nullable=True, comment="配置项功能描述")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="最后更新时间")

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
