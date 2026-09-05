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
            # 每日定时凌晨 03:30 自动执行一次全矩阵数据资产巡检
            try:
                from app.services.metrics_service import metrics_service
                self.scheduler.add_job(
                    metrics_service.sync_all_metrics,
                    "cron",
                    hour=3,
                    minute=30,
                    id="daily_metrics_sync",
                    replace_existing=True
                )
            except Exception as e:
                print(f"[Scheduler] 注册每日指标巡检任务失败: {e}")


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
            task_id = item.get("task_id")
            mode = item.get("schedule_mode", "immediate")
            target_time = item.get("scheduled_at")

            # 阶梯累加错峰时间：若基础间隔为0，则全部零延迟即时触发
            if base_interval_seconds == 0:
                delay_seconds = 0
            else:
                delay_seconds = idx * base_interval_seconds
                if jitter_seconds > 0:
                    delay_seconds += random.randint(-jitter_seconds, jitter_seconds)
                delay_seconds = max(0, delay_seconds)

            if mode == "immediate":
                # 立即执行或依次错峰执行
                run_time = now + timedelta(seconds=delay_seconds)
                self.scheduler.add_job(
                    publisher_service.execute_subtask,
                    "date",
                    run_date=run_time,
                    args=[subtask_id],
                    id=f"subtask_{subtask_id}",
                    replace_existing=True
                )
                if delay_seconds == 0:
                    msg = "子任务已加入即时执行队列，立即启动发布流程"
                else:
                    msg = f"子任务已加入错峰执行队列，预计执行时间: {run_time.strftime('%H:%M:%S')}"
                await event_bus.emit_log(msg, task_id=task_id, subtask_id=subtask_id)

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
                if delay_seconds == 0:
                    msg = f"子任务将立即在本地提交发布，并设定平台于 {target_time} 正式公开"
                else:
                    msg = f"子任务将在本地错峰提交 ({run_time.strftime('%H:%M:%S')})，并设定平台于 {target_time} 正式公开"
                await event_bus.emit_log(msg, task_id=task_id, subtask_id=subtask_id)

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
                if delay_seconds == 0:
                    msg = f"子任务已预约在指定时间准点触发: {run_time.strftime('%Y-%m-%d %H:%M:%S')}"
                else:
                    msg = f"子任务已预约在指定时间错峰触发: {run_time.strftime('%Y-%m-%d %H:%M:%S')}"
                await event_bus.emit_log(msg, task_id=task_id, subtask_id=subtask_id)

    def cancel_subtask_job(self, subtask_id: str) -> bool:
        """从 APScheduler 队列中安全移除指定子任务的作业"""
        job_id = f"subtask_{subtask_id}"
        if self.scheduler.get_job(job_id):
            try:
                self.scheduler.remove_job(job_id)
                return True
            except Exception:
                pass
        return False

    async def schedule_single_subtask(
        self, 
        subtask_id: str, 
        schedule_mode: str = "immediate", 
        scheduled_at=None, 
        delay_seconds: int = 0
    ):
        """重新编排/调度单个子任务"""
        self.cancel_subtask_job(subtask_id)
        now = datetime.now()
        if schedule_mode in ["immediate", "platform_native"]:
            run_time = now + timedelta(seconds=delay_seconds)
        else:
            if isinstance(scheduled_at, str):
                target_dt = datetime.fromisoformat(scheduled_at.replace("Z", ""))
            else:
                target_dt = scheduled_at or now
            run_time = target_dt + timedelta(seconds=delay_seconds)

        self.scheduler.add_job(
            publisher_service.execute_subtask,
            "date",
            run_date=run_time,
            args=[subtask_id],
            id=f"subtask_{subtask_id}",
            replace_existing=True
        )

scheduler_service = SchedulerService()
