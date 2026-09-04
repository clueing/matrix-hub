from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.task import PublishTask, PublishSubtask
from app.models.account import Account
from app.services.scheduler_service import scheduler_service
from app.services.publisher_service import publisher_service

router = APIRouter(prefix="/tasks", tags=["发布任务"])

class SubtaskItemRequest(BaseModel):
    account_id: str
    video_path: str
    cover_path: Optional[str] = None
    # 差异化覆盖字段 (若不填则自动继承母版配置)
    title_override: Optional[str] = None
    description_override: Optional[str] = None
    tags_override: Optional[List[str]] = None
    scheduled_at_override: Optional[datetime] = None

class CreateTaskRequest(BaseModel):
    name: str = Field(..., description="任务名称/主题")
    task_type: str = Field("one_to_many", description="分发模式: one_to_many 或 many_to_many")
    # 统一母版配置
    master_title: str
    master_description: Optional[str] = ""
    master_tags: List[str] = []
    schedule_mode: str = Field("immediate", description="immediate(立即错峰), platform_native(平台原生定时), local_staggered(本地定时)")
    scheduled_at: Optional[datetime] = None
    # 错峰参数
    stagger_interval: int = Field(300, description="账号间错峰间隔秒数")
    stagger_jitter: int = Field(60, description="随机扰动秒数")
    # 具体分发目标列表
    items: List[SubtaskItemRequest]

@router.get("", summary="获取发布任务主表列表")
async def list_tasks(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PublishTask).order_by(PublishTask.created_at.desc())
    if status:
        stmt = stmt.where(PublishTask.status == status)
    res = await db.execute(stmt)
    tasks = res.scalars().all()
    return {"code": 0, "data": [t.to_dict() for t in tasks]}

@router.get("/{task_id}", summary="获取任务详情及所有子任务进度")
async def get_task_details(task_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(PublishTask).where(PublishTask.id == task_id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"code": 0, "data": task.to_dict(include_subtasks=True)}

@router.post("", summary="创建并启动矩阵分发任务")
async def create_task(payload: CreateTaskRequest, db: AsyncSession = Depends(get_db)):
    """
    创建主任务及多个子任务，自动合并母版与差异化配置，并提交给错峰调度器排队
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="至少需要选择一个发布账号与视频")

    # 1. 创建任务主记录
    task = PublishTask(
        name=payload.name,
        task_type=payload.task_type,
        status="pending",
        total_count=len(payload.items),
        success_count=0,
        fail_count=0
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 2. 批量生成并保存子任务
    subtasks_to_schedule = []
    for item in payload.items:
        # 查询账号信息获取所属平台
        acc_res = await db.execute(select(Account).where(Account.id == item.account_id))
        acc = acc_res.scalar_one_or_none()
        if not acc:
            continue

        # 合并差异化覆盖逻辑：有独立配置则优先用独立配置，否则继承母版
        final_title = item.title_override if item.title_override else payload.master_title
        final_desc = item.description_override if item.description_override is not None else payload.master_description
        final_tags = item.tags_override if item.tags_override is not None else payload.master_tags
        final_time = item.scheduled_at_override if item.scheduled_at_override else payload.scheduled_at

        subtask = PublishSubtask(
            task_id=task.id,
            account_id=acc.id,
            platform=acc.platform,
            video_path=item.video_path,
            cover_path=item.cover_path,
            title=final_title,
            description=final_desc,
            tags=final_tags,
            schedule_mode=payload.schedule_mode,
            scheduled_at=final_time,
            status="pending"
        )
        db.add(subtask)
        await db.commit()
        await db.refresh(subtask)

        subtasks_to_schedule.append({
            "id": subtask.id,
            "schedule_mode": payload.schedule_mode,
            "scheduled_at": final_time
        })

    # 3. 提交到错峰调度器进行阶梯时间编排
    await scheduler_service.schedule_batch_subtasks(
        subtasks_data=subtasks_to_schedule,
        base_interval_seconds=payload.stagger_interval,
        jitter_seconds=payload.stagger_jitter
    )

    task.status = "processing"
    await db.commit()
    return {"code": 0, "message": "分发任务创建成功并已加入错峰排期", "data": {"task_id": task.id}}

@router.post("/{task_id}/retry", summary="一键重试失败的子任务")
async def retry_failed_subtasks(task_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(PublishSubtask).where(PublishSubtask.task_id == task_id, PublishSubtask.status == "failed")
    res = await db.execute(stmt)
    failed_subtasks = res.scalars().all()
    if not failed_subtasks:
        return {"code": 0, "message": "当前没有失败的子任务需要重试"}

    retry_list = []
    for s in failed_subtasks:
        s.status = "pending"
        s.retry_count += 1
        s.error_message = None
        retry_list.append({"id": s.id, "schedule_mode": "immediate", "scheduled_at": None})

    await db.commit()
    await scheduler_service.schedule_batch_subtasks(retry_list, base_interval_seconds=60)
    return {"code": 0, "message": f"已将 {len(retry_list)} 个失败子任务重新加入重试队列"}
