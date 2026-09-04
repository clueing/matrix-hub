import random
from datetime import datetime, timedelta
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import settings
from app.core.event_bus import event_bus
from app.services.publisher_service import publisher_service

class SchedulerService:
    """
    任务调度与错峰排队管理服务
    基于 APScheduler，实现多账号阶梯错峰发布与平台原生定时计划编排
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()

    async def schedule_batch_subtasks(
        self, 
        subtasks_data: List[dict],
        base_interval_seconds: int = 300,
        jitter_seconds: int = 60
    ):
        """
        对一批子任务进行阶梯错峰排队调度
        :param subtasks_data: 包含 subtask_id, schedule_mode, scheduled_at 等信息的字典列表
        :param base_interval_seconds: 账号之间的基础错峰间隔秒数 (默认5分钟)
        :param jitter_seconds: 随机上下扰动秒数 (默认1分钟)
        """
        now = datetime.now()

        for idx, item in enumerate(subtasks_data):
            subtask_id = item["id"]
            mode = item.get("schedule_mode", "immediate")
            target_time = item.get("scheduled_at")

            # 阶梯累加错峰时间
            delay_seconds = idx * base_interval_seconds
            if jitter_seconds > 0:
                delay_seconds += random.randint(-jitter_seconds, jitter_seconds)
            delay_seconds = max(0, delay_seconds)

            if mode == "immediate":
                # 立即排队依次错峰执行
                run_time = now + timedelta(seconds=delay_seconds)
                self.scheduler.add_job(
                    publisher_service.execute_subtask,
                    "date",
                    run_date=run_time,
                    args=[subtask_id],
                    id=f"subtask_{subtask_id}",
                    replace_existing=True
                )
                await event_bus.emit_log(
                    f"子任务已加入错峰执行队列，预计执行时间: {run_time.strftime('%H:%M:%S')}"
                )

            elif mode == "platform_native":
                # 平台原生定时：任务直接在当前依次排队上传，向平台提交指定的定时时刻
                run_time = now + timedelta(seconds=delay_seconds)
                self.scheduler.add_job(
                    publisher_service.execute_subtask,
                    "date",
                    run_date=run_time,
                    args=[subtask_id],
                    id=f"subtask_{subtask_id}",
                    replace_existing=True
                )
                await event_bus.emit_log(
                    f"子任务将在本地错峰提交 ({run_time.strftime('%H:%M:%S')})，并设定平台于 {target_time} 正式公开"
                )

            elif mode == "local_staggered":
                # 本地定时唤醒发布
                if isinstance(target_time, str):
                    target_dt = datetime.fromisoformat(target_time.replace("Z", ""))
                else:
                    target_dt = target_time or now

                run_time = target_dt + timedelta(seconds=delay_seconds)
                self.scheduler.add_job(
                    publisher_service.execute_subtask,
                    "date",
                    run_date=run_time,
                    args=[subtask_id],
                    id=f"subtask_{subtask_id}",
                    replace_existing=True
                )
                await event_bus.emit_log(
                    f"子任务已预约在指定时间错峰触发: {run_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )

scheduler_service = SchedulerService()
