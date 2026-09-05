import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer
from app.core.database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    platform = Column(String(32), nullable=False, index=True)  # xiaohongshu, douyin, kuaishou, channels
    account_name = Column(String(128), default="未命名账号")
    uid = Column(String(128), nullable=True, index=True)
    avatar_url = Column(Text, nullable=True)
    group_name = Column(String(64), default="默认分组", index=True)
    status = Column(String(32), default="unauthorized", index=True)  # unauthorized, active, expired, banned
    storage_path = Column(Text, nullable=False)
    proxy_url = Column(String(255), nullable=True)
    followers_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    last_login_at = Column(DateTime, nullable=True)
    last_check_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "platform": self.platform,
            "account_name": self.account_name,
            "uid": self.uid,
            "avatar_url": self.avatar_url,
            "group_name": self.group_name,
            "status": self.status,
            "proxy_url": self.proxy_url,
            "followers_count": self.followers_count or 0,
            "likes_count": self.likes_count or 0,
            "following_count": self.following_count or 0,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "last_check_at": self.last_check_at.isoformat() if self.last_check_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

