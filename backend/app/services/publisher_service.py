import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.event_bus import event_bus
from app.models.task import PublishTask, PublishSubtask
from app.models.account import Account
from app.drivers.playwright_driver import playwright_driver
from app.adapters import get_adapter
from app.services.notifier_service import notifier_service

class PublisherService:
    """
    分发任务执行核心服务
    按队列串行/控并发调度各个账号的发布子任务，处理重试、状态流转与告警通知
    """

    async def execute_subtask(self, subtask_id: str):
        """执行具体的单个发布子任务"""
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(PublishSubtask).where(PublishSubtask.id == subtask_id))
            subtask = res.scalar_one_or_none()
            if not subtask:
                return

            if subtask.status in ["published", "cancelled"]:
                return

            # 获取关联账号信息
            acc_res = await db.execute(select(Account).where(Account.id == subtask.account_id))
            account = acc_res.scalar_one_or_none()
            if not account:
                subtask.status = "failed"
                subtask.error_message = "关联账号不存在"
                await db.commit()
                return

            adapter = get_adapter(subtask.platform)
            if not adapter:
                subtask.status = "failed"
                subtask.error_message = f"不支持的平台: {subtask.platform}"
                await db.commit()
                return

            # 标记为上传执行中
            subtask.status = "uploading"
            subtask.executed_at = datetime.utcnow()
            await db.commit()
            await event_bus.broadcast("subtask_status_changed", subtask.to_dict())
            await event_bus.emit_log(
                f"开始向【{adapter.platform_name}】账号【{account.account_name}】分发作品: {subtask.title}",
                task_id=subtask.task_id,
                account_id=account.id
            )

            # 启动受控浏览器
            context = None
            page = None
            try:
                context, page = await playwright_driver.get_context_and_page(
                    account_id=account.id,
                    headless=True,
                    proxy_url=account.proxy_url
                )

                def log_callback(level: str, msg: str):
                    asyncio.create_task(event_bus.emit_log(msg, level=level, task_id=subtask.task_id, account_id=account.id))

                subtask_dict = {
                    "video_path": subtask.video_path,
                    "cover_path": subtask.cover_path,
                    "title": subtask.title,
                    "description": subtask.description,
                    "tags": subtask.tags or [],
                    "schedule_mode": subtask.schedule_mode,
                    "scheduled_at": subtask.scheduled_at
                }

                # 执行平台发布逻辑
                result = await adapter.publish_video(page, subtask_dict, on_progress=log_callback)

                if result.get("success"):
                    subtask.status = "published"
                    subtask.finished_at = datetime.utcnow()
                    subtask.error_message = None
                    subtask.platform_work_id = result.get("work_id")
                    subtask.platform_work_url = result.get("work_url")
                    await db.commit()
                    await self._update_parent_task_stats(db, subtask.task_id)
                    await event_bus.emit_log(
                        f"【{account.account_name}】作品《{subtask.title}》发布成功！",
                        level="SUCCESS",
                        task_id=subtask.task_id,
                        account_id=account.id
                    )
                else:
                    err = result.get("error", "未知发布错误")
                    subtask.status = "failed"
                    subtask.error_message = err
                    subtask.finished_at = datetime.utcnow()
                    await db.commit()
                    await self._update_parent_task_stats(db, subtask.task_id)
                    await event_bus.emit_log(
                        f"【{account.account_name}】作品《{subtask.title}》发布失败: {err}",
                        level="ERROR",
                        task_id=subtask.task_id,
                        account_id=account.id
                    )

            except Exception as e:
                err_msg = str(e)
                subtask.status = "failed"
                subtask.error_message = err_msg
                subtask.finished_at = datetime.utcnow()
                await db.commit()
                await self._update_parent_task_stats(db, subtask.task_id)
                await event_bus.emit_log(
                    f"【{account.account_name}】执行发布异常中断: {err_msg}",
                    level="ERROR",
                    task_id=subtask.task_id,
                    account_id=account.id
                )
            finally:
                if context:
                    await playwright_driver.close_context(context, page)
                await event_bus.broadcast("subtask_status_changed", subtask.to_dict())

    async def _update_parent_task_stats(self, db: AsyncSession, task_id: str):
        """汇总更新主任务的执行进度与状态"""
        res = await db.execute(select(PublishTask).where(PublishTask.id == task_id))
        task = res.scalar_one_or_none()
        if not task:
            return

        subtasks_res = await db.execute(select(PublishSubtask).where(PublishSubtask.task_id == task_id))
        subtasks = subtasks_res.scalars().all()

        total = len(subtasks)
        success = sum(1 for s in subtasks if s.status == "published")
        failed = sum(1 for s in subtasks if s.status == "failed")
        processing = sum(1 for s in subtasks if s.status in ["uploading", "waiting_manual"])

        task.total_count = total
        task.success_count = success
        task.fail_count = failed

        if processing > 0:
            task.status = "processing"
        elif total > 0 and (success + failed == total):
            if failed == 0:
                task.status = "completed"
                # 发送飞书/钉钉通知
                asyncio.create_task(notifier_service.send_notification(
                    title="矩阵发布任务全部完成",
                    content=f"任务《{task.name}》全部 {success} 个子任务均已成功发布！",
                    level="SUCCESS",
                    db=db
                ))
            elif success > 0:
                task.status = "partial_failed"
                asyncio.create_task(notifier_service.send_notification(
                    title="矩阵发布任务部分完成",
                    content=f"任务《{task.name}》执行结束: 成功 {success} 个，失败 {failed} 个。",
                    level="WARNING",
                    db=db
                ))
            else:
                task.status = "failed"
                asyncio.create_task(notifier_service.send_notification(
                    title="矩阵发布任务失败",
                    content=f"任务《{task.name}》所有子任务发布均失败，请在控制台排查！",
                    level="ERROR",
                    db=db
                ))

        await db.commit()
        await event_bus.broadcast("task_status_changed", task.to_dict())

publisher_service = PublisherService()
