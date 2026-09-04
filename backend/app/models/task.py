import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class PublishTask(Base):
    __tablename__ = "publish_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    task_type = Column(String(32), nullable=False, default="one_to_many")  # one_to_many, many_to_many
    status = Column(String(32), default="pending", index=True)  # pending, processing, completed, partial_failed, failed, cancelled
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subtasks = relationship("PublishSubtask", back_populates="task", cascade="all, delete-orphan", lazy="selectin")

    def to_dict(self, include_subtasks: bool = False):
        res = {
            "id": self.id,
            "name": self.name,
            "task_type": self.task_type,
            "status": self.status,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_subtasks and self.subtasks:
            res["subtasks"] = [s.to_dict() for s in self.subtasks]
        return res


class PublishSubtask(Base):
    __tablename__ = "publish_subtasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("publish_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(32), nullable=False)
    
    # Media & Content
    video_path = Column(Text, nullable=False)
    cover_path = Column(Text, nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)  # list of tags e.g. ["#搞笑", "#日常"]

    # Scheduling
    schedule_mode = Column(String(32), default="immediate")  # immediate, platform_native, local_staggered
    scheduled_at = Column(DateTime, nullable=True, index=True)
    stagger_delay_seconds = Column(Integer, default=0)

    # Execution State
    status = Column(String(32), default="pending", index=True)  # pending, scheduled, waiting_manual, uploading, published, failed, cancelled
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=2)
    error_message = Column(Text, nullable=True)
    platform_work_id = Column(String(128), nullable=True)
    platform_work_url = Column(Text, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = relationship("PublishTask", back_populates="subtasks")
    account = relationship("Account", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "account_id": self.account_id,
            "account_name": self.account.account_name if self.account else "未知账号",
            "platform": self.platform,
            "video_path": self.video_path,
            "cover_path": self.cover_path,
            "title": self.title,
            "description": self.description,
            "tags": self.tags or [],
            "schedule_mode": self.schedule_mode,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "stagger_delay_seconds": self.stagger_delay_seconds,
            "status": self.status,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "platform_work_id": self.platform_work_id,
            "platform_work_url": self.platform_work_url,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
