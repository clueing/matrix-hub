import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import AsyncSessionLocal
from app.core.event_bus import event_bus
from app.models.account import Account
from app.models.task import PublishSubtask, PublishTask
from app.drivers.playwright_driver import playwright_driver
from app.adapters import get_adapter

class MetricsService:
    """
    全矩阵数据资产与指标监控服务
    负责各平台创作者中心后台数据爬取、作品级指标回流匹配与矩阵大盘统计
    """

    def __init__(self):
        self._syncing = False

    @property
    def is_syncing(self) -> bool:
        return self._syncing

    async def sync_account_metrics(self, account_id: str) -> Dict[str, Any]:
        """
        拉取并同步单个账号的大盘指标与作品明细
        """
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Account).where(Account.id == account_id))
            account = res.scalar_one_or_none()
            if not account:
                raise ValueError("账号不存在")

            if account.status != "active":
                return {"success": False, "message": f"账号【{account.account_name}】未激活或已失效，跳过同步"}

            adapter = get_adapter(account.platform)
            if not adapter:
                return {"success": False, "message": f"不支持的平台: {account.platform}"}

            await event_bus.emit_log(f"开始同步【{adapter.platform_name}】账号【{account.account_name}】的最新数据指标...", account_id=account.id)

            context = None
            page = None
            try:
                context, page = await playwright_driver.get_context_and_page(
                    account_id=account.id,
                    headless=True,
                    proxy_url=account.proxy_url
                )

                metrics_data = await adapter.fetch_metrics(page)
                acc_metrics = metrics_data.get("account", {})
                works_metrics = metrics_data.get("works", [])

                # 1. 更新账号大盘属性
                if acc_metrics.get("followers_count"):
                    account.followers_count = acc_metrics["followers_count"]
                if acc_metrics.get("likes_count"):
                    account.likes_count = acc_metrics["likes_count"]
                if acc_metrics.get("total_views_count"):
                    account.total_views_count = acc_metrics["total_views_count"]
                if acc_metrics.get("works_count"):
                    account.works_count = acc_metrics["works_count"]

                account.last_metrics_at = datetime.utcnow()

                # 2. 查询该账号已在 MatrixHub 发布的子作品
                subs_res = await db.execute(
                    select(PublishSubtask).where(
                        PublishSubtask.account_id == account.id,
                        PublishSubtask.status == "published"
                    )
                )
                published_subs = subs_res.scalars().all()

                matched_count = 0
                for work in works_metrics:
                    work_id = str(work.get("work_id", "")).strip()
                    work_title = str(work.get("title", "")).strip()

                    # 优先级匹配：1) platform_work_id 精准对齐；2) 标题包含或相等
                    matched_sub = None
                    if work_id:
                        for s in published_subs:
                            if s.platform_work_id == work_id:
                                matched_sub = s
                                break

                    if not matched_sub and work_title:
                        for s in published_subs:
                            if s.title and (s.title in work_title or work_title in s.title):
                                matched_sub = s
                                break

                    if matched_sub:
                        matched_sub.view_count = work.get("view_count", 0)
                        matched_sub.like_count = work.get("like_count", 0)
                        matched_sub.comment_count = work.get("comment_count", 0)
                        matched_sub.share_count = work.get("share_count", 0)
                        matched_sub.collect_count = work.get("collect_count", 0)
                        matched_sub.last_metrics_at = datetime.utcnow()

                        if not matched_sub.platform_work_id and work_id:
                            matched_sub.platform_work_id = work_id
                        if not matched_sub.platform_work_url and work.get("work_url"):
                            matched_sub.platform_work_url = work.get("work_url")

                        matched_count += 1

                await db.commit()

                # 广播账号状态更新
                await event_bus.broadcast("account_status_changed", account.to_dict())
                await event_bus.broadcast("metrics_updated", {
                    "account_id": account.id,
                    "matched_works": matched_count,
                    "total_fetched": len(works_metrics)
                })

                await event_bus.emit_log(
                    f"【{account.account_name}】指标同步完成：粉丝 {account.followers_count}，总获赞 {account.likes_count}，匹配更新了 {matched_count} 篇作品指标！",
                    level="SUCCESS",
                    account_id=account.id
                )

                return {
                    "success": True,
                    "account_id": account.id,
                    "followers_count": account.followers_count,
                    "likes_count": account.likes_count,
                    "total_views_count": account.total_views_count,
                    "matched_works": matched_count,
                    "fetched_works_count": len(works_metrics)
                }

            except Exception as e:
                err = str(e)
                await event_bus.emit_log(f"同步【{account.account_name}】指标异常: {err}", level="ERROR", account_id=account.id)
                return {"success": False, "error": err}
            finally:
                if context:
                    await playwright_driver.close_context(account.id)

    async def sync_all_metrics(self) -> Dict[str, Any]:
        """
        全量同步所有活跃账号的数据资产
        """
        if self._syncing:
            return {"success": False, "message": "正在执行数据同步中，请稍候"}

        self._syncing = True
        try:
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(Account).where(Account.status == "active"))
                accounts = res.scalars().all()

            total = len(accounts)
            if total == 0:
                return {"success": True, "message": "暂无活跃账号需要同步", "synced_count": 0}

            await event_bus.emit_log(f"开始执行全矩阵资产数据回流，共发现 {total} 个活跃账号待巡检...")

            results = []
            for acc in accounts:
                res = await self.sync_account_metrics(acc.id)
                results.append(res)
                await asyncio.sleep(2)  # 间隔 2 秒避免密集并发

            await event_bus.emit_log(f"全矩阵数据回流巡检完成！已成功同步 {total} 个账号的最新表现", level="SUCCESS")
            return {
                "success": True,
                "total": total,
                "results": results
            }
        finally:
            self._syncing = False

    async def get_matrix_overview(self, db: AsyncSession) -> Dict[str, Any]:
        """
        获取全矩阵核心资产总览与爆款内容排行榜
        """
        # 1. 账号概览
        acc_res = await db.execute(select(Account))
        accounts = acc_res.scalars().all()

        total_accounts = len(accounts)
        active_accounts = sum(1 for a in accounts if a.status == "active")
        total_followers = sum(a.followers_count or 0 for a in accounts)
        total_account_likes = sum(a.likes_count or 0 for a in accounts)
        total_account_views = sum(a.total_views_count or 0 for a in accounts)

        # 平台分布统计
        platform_stats: Dict[str, Any] = {
            "douyin": {"accounts": 0, "followers": 0, "likes": 0, "views": 0, "works": 0},
            "xiaohongshu": {"accounts": 0, "followers": 0, "likes": 0, "views": 0, "works": 0},
            "kuaishou": {"accounts": 0, "followers": 0, "likes": 0, "views": 0, "works": 0},
            "channels": {"accounts": 0, "followers": 0, "likes": 0, "views": 0, "works": 0}
        }

        for a in accounts:
            p = a.platform
            if p not in platform_stats:
                platform_stats[p] = {"accounts": 0, "followers": 0, "likes": 0, "views": 0, "works": 0}
            platform_stats[p]["accounts"] += 1
            platform_stats[p]["followers"] += (a.followers_count or 0)
            platform_stats[p]["likes"] += (a.likes_count or 0)
            platform_stats[p]["views"] += (a.total_views_count or 0)

        # 2. 作品数据
        sub_res = await db.execute(
            select(PublishSubtask).where(PublishSubtask.status == "published")
        )
        published_subs = sub_res.scalars().all()

        total_published_works = len(published_subs)
        sub_total_views = sum(s.view_count or 0 for s in published_subs)
        sub_total_likes = sum(s.like_count or 0 for s in published_subs)
        sub_total_comments = sum(s.comment_count or 0 for s in published_subs)
        sub_total_shares = sum(s.share_count or 0 for s in published_subs)
        sub_total_collects = sum(s.collect_count or 0 for s in published_subs)

        # 累计播放量取两者较大值（账号大盘汇总 vs 作品明细汇总）
        total_views = max(total_account_views, sub_total_views)
        total_likes = max(total_account_likes, sub_total_likes)

        for s in published_subs:
            p = s.platform
            if p in platform_stats:
                platform_stats[p]["works"] += 1

        # 3. 爆款作品排行榜 Top 10
        top_works_res = await db.execute(
            select(PublishSubtask)
            .where(PublishSubtask.status == "published")
            .order_by(desc(PublishSubtask.view_count), desc(PublishSubtask.like_count))
            .limit(10)
        )
        top_subs = top_works_res.scalars().all()

        top_works = []
        for s in top_subs:
            top_works.append({
                "id": s.id,
                "title": s.title,
                "cover_path": s.cover_path,
                "platform": s.platform,
                "account_name": s.account.account_name if s.account else "未知账号",
                "account_avatar": s.account.avatar_url if s.account else None,
                "view_count": s.view_count or 0,
                "like_count": s.like_count or 0,
                "comment_count": s.comment_count or 0,
                "share_count": s.share_count or 0,
                "collect_count": s.collect_count or 0,
                "platform_work_url": s.platform_work_url,
                "executed_at": s.executed_at.isoformat() if s.executed_at else None,
                "last_metrics_at": s.last_metrics_at.isoformat() if s.last_metrics_at else None
            })

        # 最近一次同步时间
        metric_times = [a.last_metrics_at for a in accounts if a.last_metrics_at]
        last_sync_at = max(metric_times).isoformat() if metric_times else None

        return {
            "overview": {
                "total_accounts": total_accounts,
                "active_accounts": active_accounts,
                "total_followers": total_followers,
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": sub_total_comments,
                "total_shares": sub_total_shares,
                "total_collects": sub_total_collects,
                "total_published_works": total_published_works,
                "last_sync_at": last_sync_at,
                "is_syncing": self._syncing
            },
            "platform_stats": platform_stats,
            "top_works": top_works
        }

metrics_service = MetricsService()
