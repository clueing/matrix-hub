import os
import asyncio
from pathlib import Path
from typing import Tuple, Optional
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from playwright_stealth import Stealth
from app.core.config import settings
from app.drivers.base import BaseDriver

class PlaywrightDriver(BaseDriver):
    """
    Playwright 隔离浏览器驱动实现
    每个账号独享独立的 user_data_dir 目录，物理隔离所有 Cookie、缓存与 LocalStorage，
    集成反指纹补丁与并发信号量控制，防止触发平台风控。
    """

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        # 控制全局浏览器并发数，防止本地电脑内存与 CPU 负载过高
        self._semaphore = asyncio.Semaphore(settings.MAX_BROWSER_CONCURRENCY)
        self._active_contexts = {}

    async def _ensure_playwright(self):
        """确保 Playwright 引擎已初始化"""
        if self._playwright is None:
            self._playwright = await async_playwright().start()

    async def get_context_and_page(
        self,
        account_id: str,
        headless: bool = True,
        proxy_url: Optional[str] = None
    ) -> Tuple[BrowserContext, Page]:
        """
        启动并获取指定账号的独立持久化浏览器上下文及主页面
        """
        await self._ensure_playwright()

        # 为该账号创建独立的用户数据存储目录 (持久化隔离)
        account_dir = settings.SESSIONS_DIR / account_id
        user_data_dir = account_dir / "user_data"
        user_data_dir.mkdir(parents=True, exist_ok=True)

        # 启动参数：消除自动化特征、伪装真实中文系统
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--lang=zh-CN,zh;q=0.9",
            "--window-size=1280,800",
            "--start-maximized"
        ]

        proxy_config = None
        if proxy_url:
            proxy_config = {"server": proxy_url}

        # 真实主流 Windows Chrome User-Agent
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )

        # 启动持久化上下文 (自动读取与回写所有 Cookie 和缓存)
        context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=headless,
            args=args,
            user_agent=user_agent,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            viewport={"width": 1280, "height": 800},
            proxy=proxy_config,
            slow_mo=settings.BROWSER_SLOW_MO,
            accept_downloads=True
        )

        # 获取或创建初始页面
        if len(context.pages) > 0:
            page = context.pages[0]
        else:
            page = await context.new_page()

        # 注入 stealth 补丁，伪造 navigator 属性以规避风控特征检测
        try:
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
        except Exception:
            # 兼容处理
            pass

        self._active_contexts[account_id] = context
        return context, page

    async def close_context(self, context: BrowserContext, page: Optional[Page] = None):
        """关闭上下文并释放资源"""
        try:
            if page and not page.is_closed():
                await page.close()
            await context.close()
        except Exception:
            pass

    async def stop(self):
        """关闭整个 Playwright 引擎"""
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

# 单例驱动实例
playwright_driver = PlaywrightDriver()
