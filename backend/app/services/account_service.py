import io
import os
import json
import zipfile
import asyncio
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.event_bus import event_bus
from app.models.account import Account
from app.drivers.playwright_driver import playwright_driver
from app.adapters import get_adapter

class AccountService:
    """
    账号管理服务
    负责账号授权流程（扫码推流、会话保存）、健康监测、人工辅助弹窗以及账号凭证的导出与导入
    """

    def __init__(self):
        self._active_tasks: Dict[str, asyncio.Task] = {}

    @staticmethod
    def _apply_user_info(acc: Account, user_info: Optional[Dict[str, Any]]):
        """同步创作者基本信息、头像、UID及互动统计"""
        if not user_info:
            return
        if user_info.get("name"):
            acc.account_name = user_info["name"]
        if user_info.get("uid"):
            acc.uid = str(user_info["uid"])
        if user_info.get("avatar"):
            acc.avatar_url = user_info["avatar"]
        if "followers_count" in user_info:
            acc.followers_count = user_info["followers_count"] or 0
        if "likes_count" in user_info:
            acc.likes_count = user_info["likes_count"] or 0
        if "following_count" in user_info:
            acc.following_count = user_info["following_count"] or 0

    async def start_login_session(
        self, 
        db: AsyncSession, 
        platform: str, 
        group_name: str = "默认分组",
        proxy_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        开启扫码登录会话：拉起独立浏览器上下文，获取二维码并通过 WebSocket 实时广播
        """
        adapter = get_adapter(platform)
        if not adapter:
            raise ValueError(f"不支持的平台: {platform}")

        # 1. 在数据库中创建临时未授权账号记录
        account = Account(
            platform=platform,
            account_name=f"{adapter.platform_name}待登录账号",
            group_name=group_name,
            status="unauthorized",
            storage_path="",
            proxy_url=proxy_url
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)

        account.storage_path = str(settings.SESSIONS_DIR / account.id)
        await db.commit()
        await event_bus.broadcast("account_status_changed", account.to_dict())

        # 2. 中止该账号可能存在的历史残留任务并释放文件锁
        old_task = self._active_tasks.pop(account.id, None)
        if old_task and not old_task.done():
            old_task.cancel()
        await playwright_driver.close_account_context(account.id)

        # 3. 异步启动扫码流程
        task = asyncio.create_task(self._run_login_pipeline(account.id, platform, proxy_url))
        self._active_tasks[account.id] = task

        return {
            "account_id": account.id,
            "platform": platform,
            "status": "waiting_qrcode"
        }

    async def _run_login_pipeline(self, account_id: str, platform: str, proxy_url: Optional[str] = None):
        """后台执行扫码与登录态捕获管线"""
        adapter = get_adapter(platform)
        context = None
        page = None
        try:
            await event_bus.emit_log(f"正在拉起【{adapter.platform_name}】独立环境以获取登录二维码...", account_id=account_id)
            context, page = await playwright_driver.get_context_and_page(
                account_id=account_id,
                headless=settings.DEFAULT_HEADLESS,
                proxy_url=proxy_url
            )

            # 挂载 CDP Screencast 实时屏幕推流 (Manus 风格视窗)
            await playwright_driver.start_screencast(page, account_id=account_id)

            # 获取二维码并推流到前端 (耗时约 1~2 秒)
            qrcode_b64 = await adapter.get_login_qrcode(page)
            if qrcode_b64:
                await event_bus.broadcast("qrcode_updated", {
                    "account_id": account_id,
                    "platform": platform,
                    "qrcode_base64": qrcode_b64
                })
                await event_bus.emit_log(f"【{adapter.platform_name}】登录二维码获取成功，请使用手机 App 扫码！", account_id=account_id)
            else:
                await event_bus.emit_log(f"获取二维码超时或需要人机验证，请尝试使用【人工辅助】窗口登录", level="WARNING", account_id=account_id)

            # 等待扫码确认 (仅静默检测 URL 跳转，绝不打断页面)
            logged_in, user_info = await adapter.wait_for_login(page, timeout=120)

            if logged_in:
                # 只有确认成功登录，才持久化会话凭证
                account_dir = settings.SESSIONS_DIR / account_id
                account_dir.mkdir(parents=True, exist_ok=True)
                storage_file = account_dir / "storage_state.json"
                await context.storage_state(path=str(storage_file))

                from app.core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as session:
                    res = await session.execute(select(Account).where(Account.id == account_id))
                    acc = res.scalar_one_or_none()
                    if acc:
                        acc.status = "active"
                        acc.last_login_at = datetime.utcnow()
                        acc.last_check_at = datetime.utcnow()
                        self._apply_user_info(acc, user_info)
                        await session.commit()
                        await event_bus.emit_log(f"恭喜！【{acc.account_name}】授权登录成功！", level="SUCCESS", account_id=account_id)
                        await event_bus.broadcast("account_status_changed", acc.to_dict())
            else:
                # 超时未扫码：先查询当前账号是否已经被人工辅助窗口登录激活过，避免错误覆盖有效状态
                from app.core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as session:
                    res = await session.execute(select(Account).where(Account.id == account_id))
                    acc = res.scalar_one_or_none()
                    if acc and acc.status != "active":
                        acc.status = "unauthorized"
                        await session.commit()
                        await event_bus.emit_log(f"扫码超时或取消，请重试登录", level="WARNING", account_id=account_id)
                        await event_bus.broadcast("account_status_changed", acc.to_dict())

        except asyncio.CancelledError:
            pass  # 任务被正常取消（如切换到人工辅助）
        except Exception as e:
            await event_bus.emit_log(f"登录流程发生异常: {str(e)}", level="ERROR", account_id=account_id)
        finally:
            self._active_tasks.pop(account_id, None)
            if page:
                await playwright_driver.stop_screencast(page)
            if context:
                await playwright_driver.close_context(context, page)
            await event_bus.broadcast("screencast_stopped", {"account_id": account_id})

    async def check_account_health(self, db: AsyncSession, account_id: str) -> Dict[str, Any]:
        """对单个账号触发轻量级心跳测试，判断 Cookie 是否仍然有效"""
        res = await db.execute(select(Account).where(Account.id == account_id))
        account = res.scalar_one_or_none()
        if not account:
            raise ValueError("账号不存在")

        adapter = get_adapter(account.platform)
        if not adapter:
            raise ValueError("未知的平台类型")

        context, page = await playwright_driver.get_context_and_page(
            account_id=account.id,
            headless=True,
            proxy_url=account.proxy_url
        )
        try:
            is_valid, user_info = await adapter.check_login_status(page)
            account.last_check_at = datetime.utcnow()
            if is_valid:
                account.status = "active"
                self._apply_user_info(account, user_info)
            else:
                account.status = "expired"

            await db.commit()
            await db.refresh(account)
            await event_bus.broadcast("account_status_changed", account.to_dict())
            return account.to_dict()
        finally:
            await playwright_driver.close_context(context, page)

    async def launch_visible_assist(self, account_id: str):
        """
        在宿主机桌面唤起有头浏览器窗口，供人工滑动验证码或短信/扫码登录，
        并在检测到登录完成后自动保存会话、同步状态到前端并关闭窗口。
        """
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(Account).where(Account.id == account_id))
            account = res.scalar_one_or_none()
            if not account:
                raise ValueError("账号不存在")
            platform = account.platform
            proxy_url = account.proxy_url
            account_status = account.status
            account_name = account.account_name

        # 1. 优先中断该账号可能在后台排队的无头扫码任务并释放文件锁
        old_task = self._active_tasks.pop(account_id, None)
        if old_task and not old_task.done():
            old_task.cancel()
        await playwright_driver.close_account_context(account_id)
        await asyncio.sleep(1)

        adapter = get_adapter(platform)
        await event_bus.emit_log("正在本地桌面唤起独立辅助浏览器窗口，请在弹窗中操作...", account_id=account_id)
        
        context, page = await playwright_driver.get_context_and_page(
            account_id=account_id,
            headless=False,
            proxy_url=proxy_url
        )
        try:
            # 访问登录页（未登录）或创作者首页
            target_url = adapter.login_url if account_status != "active" else adapter.creator_url
            await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")

            login_detected = False
            for _ in range(150):  # 最多等待 300 秒
                await asyncio.sleep(2)
                if page.is_closed():
                    break
                
                # 监听页面 URL：若跳转进入后台，则说明扫码/过滑块成功
                curr_url = page.url
                if "login" not in curr_url and any(k in curr_url for k in ["creator", "home", "micro", "platform"]):
                    login_detected = True
                    await asyncio.sleep(1.5)
                    break

                # 探测页面是否已出现创作者主页元素
                try:
                    success_indicator = await page.query_selector(".user-info, .header-avatar, .con-name, .name-box, [class*='avatar']")
                    if success_indicator and await success_indicator.is_visible():
                        login_detected = True
                        await asyncio.sleep(1.5)
                        break
                except Exception:
                    pass

            # 即使页面被关闭，也检查 cookies 兜底识别
            try:
                cookies = await context.cookies()
                has_session = any(
                    any(term in c["name"].lower() for term in ["session", "token", "a1", "sso", "passport", "login", "auth"])
                    for c in cookies
                )
                if has_session:
                    login_detected = True
            except Exception:
                pass

            if login_detected:
                # 导出并持久化 StorageState
                account_dir = settings.SESSIONS_DIR / account_id
                account_dir.mkdir(parents=True, exist_ok=True)
                storage_file = account_dir / "storage_state.json"
                try:
                    await context.storage_state(path=str(storage_file))
                except Exception:
                    pass

                async with AsyncSessionLocal() as session:
                    acc_res = await session.execute(select(Account).where(Account.id == account_id))
                    acc = acc_res.scalar_one_or_none()
                    if acc:
                        acc.status = "active"
                        acc.last_login_at = datetime.utcnow()
                        acc.last_check_at = datetime.utcnow()
                        if not page.is_closed():
                            try:
                                info = await adapter._extract_user_info_from_page(page)
                                self._apply_user_info(acc, info)
                            except Exception:
                                pass
                        await session.commit()
                        await event_bus.emit_log(f"人工辅助验证通过，【{acc.account_name}】状态已自动同步！", level="SUCCESS", account_id=account_id)
                        await event_bus.broadcast("account_status_changed", acc.to_dict())
                        await asyncio.sleep(2)
        finally:
            await playwright_driver.close_context(context, page)

    async def export_single_account(self, db: AsyncSession, account_id: str) -> io.BytesIO:
        """
        将单账号的元数据和 storage_state 打包为 ZIP 字节流供前端下载
        """
        res = await db.execute(select(Account).where(Account.id == account_id))
        account = res.scalar_one_or_none()
        if not account:
            raise ValueError("账号不存在")

        mem_zip = io.BytesIO()
        with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # 写入账号元数据描述
            meta = {
                "version": "1.0",
                "export_time": datetime.utcnow().isoformat(),
                "account": account.to_dict()
            }
            zf.writestr("meta.json", json.dumps(meta, ensure_ascii=False, indent=2))

            # 写入 StorageState (如果存在)
            storage_file = settings.SESSIONS_DIR / account.id / "storage_state.json"
            if storage_file.exists():
                zf.write(str(storage_file), arcname="storage_state.json")

        mem_zip.seek(0)
        return mem_zip

    async def import_account_archive(self, db: AsyncSession, file_bytes: bytes, overwrite: bool = True) -> Dict[str, Any]:
        """
        解析上传的 ZIP 账号备份包，还原会话并注册到数据库
        """
        imported_accounts = []
        with zipfile.ZipFile(io.BytesIO(file_bytes), mode="r") as zf:
            namelist = zf.namelist()
            if "meta.json" not in namelist:
                raise ValueError("无效的账号凭证包，缺少 meta.json")

            meta_data = json.loads(zf.read("meta.json").decode("utf-8"))
            acc_info = meta_data.get("account", {})
            platform = acc_info.get("platform")
            if not platform:
                raise ValueError("凭证包中未指定平台类型")

            # 查询是否已有同名或相同 UID 账号
            existing_account = None
            if acc_info.get("uid"):
                stmt = select(Account).where(Account.platform == platform, Account.uid == acc_info["uid"])
                existing_account = (await db.execute(stmt)).scalar_one_or_none()

            if existing_account and not overwrite:
                return {"message": "账号已存在且未开启覆盖模式", "account": existing_account.to_dict()}

            target_account = existing_account or Account(
                platform=platform,
                account_name=acc_info.get("account_name", "导入的账号"),
                uid=acc_info.get("uid"),
                avatar_url=acc_info.get("avatar_url"),
                group_name=acc_info.get("group_name", "导入分组"),
                status="active",
                storage_path="",
                proxy_url=acc_info.get("proxy_url")
            )
            if not existing_account:
                db.add(target_account)
                await db.commit()
                await db.refresh(target_account)

            target_account.storage_path = str(settings.SESSIONS_DIR / target_account.id)
            await db.commit()

            # 解压还原 storage_state.json
            acc_dir = settings.SESSIONS_DIR / target_account.id
            acc_dir.mkdir(parents=True, exist_ok=True)
            if "storage_state.json" in namelist:
                with open(acc_dir / "storage_state.json", "wb") as f:
                    f.write(zf.read("storage_state.json"))

            # 异步触发一次健康心跳检测更新状态
            asyncio.create_task(self.check_account_health(db, target_account.id))
            imported_accounts.append(target_account.to_dict())

        return {
            "imported_count": len(imported_accounts),
            "accounts": imported_accounts
        }

account_service = AccountService()
