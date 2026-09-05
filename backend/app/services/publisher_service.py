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

    def __init__(self):
        # 维护处于等待二次安全验证的子任务队列通道: subtask_id -> asyncio.Queue
        self._verification_queues: Dict[str, asyncio.Queue] = {}

    def has_active_verification(self, subtask_id: str) -> bool:
        """检查指定子任务是否处于活跃等待验证状态"""
        return subtask_id in self._verification_queues

    async def submit_verification(self, subtask_id: str, code: Optional[str] = None, action: str = "submit") -> bool:
        """向后台自动化适配器下发前端用户输入的验证码或操作动作"""
        queue = self._verification_queues.get(subtask_id)
        if not queue:
            return False
        await queue.put({"action": action, "code": code})
        return True

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

            # 初始化该子任务的异步验证通信通道
            verify_queue = asyncio.Queue()
            self._verification_queues[subtask.id] = verify_queue

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

                # 挂载 CDP Screencast 实时屏幕推流 (Manus 风格视窗)
                await playwright_driver.start_screencast(
                    page,
                    task_id=subtask.task_id,
                    account_id=account.id
                )

                def log_callback(level: str, msg: str):
                    asyncio.create_task(event_bus.emit_log(
                        msg,
                        level=level,
                        task_id=subtask.task_id,
                        subtask_id=subtask.id,
                        account_id=account.id
                    ))

                subtask_dict = {
                    "id": subtask.id,
                    "task_id": subtask.task_id,
                    "video_path": subtask.video_path,
                    "cover_path": subtask.cover_path,
                    "title": subtask.title,
                    "description": subtask.description,
                    "tags": subtask.tags or [],
                    "schedule_mode": subtask.schedule_mode,
                    "scheduled_at": subtask.scheduled_at
                }

                async def handle_verify_required(verify_info: dict) -> asyncio.Queue:
                    """当底层适配器检测到需要二次验证时触发，将任务切至 waiting_manual 并广播全局通知"""
                    subtask.status = "waiting_manual"
                    await db.commit()
                    await self._update_parent_task_stats(db, subtask.task_id)
                    await event_bus.broadcast("subtask_status_changed", subtask.to_dict())
                    await event_bus.broadcast("verification_required", {
                        "subtask_id": subtask.id,
                        "task_id": subtask.task_id,
                        "account_id": account.id,
                        "account_name": account.account_name,
                        "platform": subtask.platform,
                        "phone": verify_info.get("phone", ""),
                        "title": subtask.title,
                        "timeout": verify_info.get("timeout", 120)
                    })
                    await event_bus.emit_log(
                        f"【{account.account_name}】作品《{subtask.title}》触发二次短信验证，已发送验证码至手机 {verify_info.get('phone', '')}，等待网页端输入...",
                        level="WARNING",
                        task_id=subtask.task_id,
                        subtask_id=subtask.id,
                        account_id=account.id
                    )
                    return verify_queue

                # 执行平台发布逻辑并注入交互通道
                result = await adapter.publish_video(
                    page, 
                    subtask_dict, 
                    on_progress=log_callback,
                    on_verify_required=handle_verify_required
                )

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
                        subtask_id=subtask.id,
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
                        subtask_id=subtask.id,
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
                    subtask_id=subtask.id,
                    account_id=account.id
                )
            finally:
                self._verification_queues.pop(subtask_id, None)
                if page:
                    await playwright_driver.stop_screencast(page)
                if context:
                    await playwright_driver.close_context(context, page)
                await event_bus.broadcast("screencast_stopped", {
                    "task_id": subtask.task_id,
                    "account_id": account.id
                })
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
