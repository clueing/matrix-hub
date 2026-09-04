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

        # 2. 异步启动扫码流程
        asyncio.create_task(self._run_login_pipeline(account.id, platform, proxy_url))

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

            # 获取二维码并推流到前端
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

            # 等待扫码确认
            logged_in, user_info = await adapter.wait_for_login(page, timeout=120)

            # 无论成功与否，持久化 session 凭证
            account_dir = settings.SESSIONS_DIR / account_id
            account_dir.mkdir(parents=True, exist_ok=True)
            storage_file = account_dir / "storage_state.json"
            await context.storage_state(path=str(storage_file))

            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(Account).where(Account.id == account_id))
                acc = res.scalar_one_or_none()
                if acc:
                    if logged_in:
                        acc.status = "active"
                        acc.last_login_at = datetime.utcnow()
                        acc.last_check_at = datetime.utcnow()
                        if user_info and user_info.get("name"):
                            acc.account_name = user_info["name"]
                        if user_info and user_info.get("uid"):
                            acc.uid = user_info["uid"]
                        await session.commit()
                        await event_bus.emit_log(f"恭喜！【{acc.account_name}】授权登录成功！", level="SUCCESS", account_id=account_id)
                        await event_bus.broadcast("account_status_changed", acc.to_dict())
                    else:
                        acc.status = "unauthorized"
                        await session.commit()
                        await event_bus.emit_log(f"扫码超时或取消，请重试登录", level="WARNING", account_id=account_id)

        except Exception as e:
            await event_bus.emit_log(f"登录流程发生异常: {str(e)}", level="ERROR", account_id=account_id)
        finally:
            if context:
                await playwright_driver.close_context(context, page)

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
                if user_info and user_info.get("name"):
                    account.account_name = user_info["name"]
            else:
                account.status = "expired"

            await db.commit()
            await db.refresh(account)
            await event_bus.broadcast("account_status_changed", account.to_dict())
            return account.to_dict()
        finally:
            await playwright_driver.close_context(context, page)

    async def launch_visible_assist(self, db: AsyncSession, account_id: str):
        """
        在宿主机桌面唤起有头浏览器窗口，方便人工滑动滑块或输入短信验证码
        """
        res = await db.execute(select(Account).where(Account.id == account_id))
        account = res.scalar_one_or_none()
        if not account:
            raise ValueError("账号不存在")

        adapter = get_adapter(account.platform)
        await event_bus.emit_log("正在本地桌面唤起独立辅助浏览器窗口，请在弹出的窗口中操作...", account_id=account_id)
        
        # 启动非无头 (有头) 浏览器窗口
        context, page = await playwright_driver.get_context_and_page(
            account_id=account.id,
            headless=False,
            proxy_url=account.proxy_url
        )
        try:
            await page.goto(adapter.creator_url)
            # 等待用户在可见窗口中操作完成 (最多保持 300 秒或检测到成功登录)
            for _ in range(60):
                await asyncio.sleep(5)
                if page.is_closed():
                    break
                is_valid, user_info = await adapter.check_login_status(page)
                if is_valid:
                    account.status = "active"
                    account.last_login_at = datetime.utcnow()
                    account.last_check_at = datetime.utcnow()
                    if user_info and user_info.get("name"):
                        account.account_name = user_info["name"]
                    await db.commit()
                    # 导出持久化凭证
                    storage_file = settings.SESSIONS_DIR / account.id / "storage_state.json"
                    await context.storage_state(path=str(storage_file))
                    await event_bus.emit_log(f"人工辅助验证通过，【{account.account_name}】状态已更新！", level="SUCCESS", account_id=account_id)
                    break
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
