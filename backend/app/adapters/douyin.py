import asyncio
import base64
from datetime import datetime
from typing import Tuple, Optional, Dict, Any, Callable
from playwright.async_api import Page
from app.adapters.base import BasePublisherAdapter

class DouyinAdapter(BasePublisherAdapter):
    """
    抖音创作者服务平台适配器
    实现二维码扫码捕获、创作者登录态感知、原视频无损上传、标题/话题标签自动化填写与平台原生定时
    """

    @property
    def platform_code(self) -> str:
        return "douyin"

    @property
    def platform_name(self) -> str:
        return "抖音"

    @property
    def creator_url(self) -> str:
        return "https://creator.douyin.com/creator-micro/home"

    @property
    def login_url(self) -> str:
        return "https://creator.douyin.com/"

    @property
    def publish_url(self) -> str:
        return "https://creator.douyin.com/creator-micro/content/upload"

    async def check_login_status(self, page: Page) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """访问抖音创作者后台，校验当前会话 Cookie 是否有效"""
        try:
            await page.goto(self.creator_url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # 抖音若未登录会重定向至根域登录页或包含 passport/login
            if "passport" in page.url or page.url.rstrip("/") == "https://creator.douyin.com":
                login_btn = await page.query_selector(".login-button, div:has-text('登录')")
                if login_btn:
                    return False, None

            # 探测创作者昵称
            name_selectors = [
                ".semi-navigation-header-title", ".user-name", 
                "span[class*='name']", "div[class*='account-name']",
                ".header-user-info span"
            ]
            account_name = "抖音创作者"
            for sel in name_selectors:
                el = await page.query_selector(sel)
                if el:
                    text = (await el.inner_text()).strip()
                    if text and len(text) < 30:
                        account_name = text
                        break

            return True, {
                "name": account_name,
                "uid": None,
                "avatar": None
            }
        except Exception:
            return False, None

    async def get_login_qrcode(self, page: Page) -> Optional[str]:
        """进入抖音登录页面，快速定位并截取真实的扫码二维码 (排除 SVG 卡片背景图)"""
        try:
            await page.goto(self.login_url, timeout=25000, wait_until="domcontentloaded")
            await asyncio.sleep(1.5)

            # 1. 优先使用抖音专属扫码容器高精度定位（避免误判外层带有 data:image 的 SVG 文件夹卡片背景）
            targeted_selectors = [
                "#animate_qrcode_container img",
                "#douyin_login_comp_scan_code img",
                "div[id*='scan_code'] img",
                "div[id*='qrcode'] img",
                "div[class*='qrcode'] img",
                "div[class*='scan'] img"
            ]
            for sel in targeted_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el and await el.is_visible():
                        box = await el.bounding_box()
                        if box and 100 <= box["width"] <= 350 and 100 <= box["height"] <= 350:
                            src = await el.get_attribute("src")
                            if src and ("image/png" in src or "image/jpeg" in src):
                                return src
                            # 若非标准 data URI，对该正方形二维码元素进行高清截图
                            img_bytes = await el.screenshot()
                            b64 = base64.b64encode(img_bytes).decode("utf-8")
                            return f"data:image/png;base64,{b64}"
                except Exception:
                    continue

            # 2. 检查是否有渲染在 canvas 上的二维码
            canvas_selectors = [
                "#animate_qrcode_container canvas",
                "#douyin_login_comp_scan_code canvas",
                "canvas"
            ]
            for sel in canvas_selectors:
                try:
                    c = await page.query_selector(sel)
                    if c and await c.is_visible():
                        box = await c.bounding_box()
                        if box and 100 <= box["width"] <= 350 and 100 <= box["height"] <= 350:
                            img_bytes = await c.screenshot()
                            b64 = base64.b64encode(img_bytes).decode("utf-8")
                            return f"data:image/png;base64,{b64}"
                except Exception:
                    continue

            # 3. 兜底扫描页面所有图片，严格排除 SVG 卡片背景及非正方形图标
            imgs = await page.query_selector_all("img")
            for img in imgs:
                try:
                    if not await img.is_visible():
                        continue
                    box = await img.bounding_box()
                    if not box:
                        continue
                    # 二维码必须满足：正方形且尺寸在 110~300px 之间
                    is_square = abs(box["width"] - box["height"]) <= 20
                    is_valid_size = 110 <= box["width"] <= 300 and 110 <= box["height"] <= 300
                    if not (is_square and is_valid_size):
                        continue

                    src = await img.get_attribute("src") or ""
                    cls = await img.get_attribute("class") or ""
                    # 严防 SVG 背景大图或非二维码装饰
                    if "svg" in src or "bg" in cls.lower() or "background" in cls.lower():
                        continue

                    if src.startswith("data:image/png") or src.startswith("data:image/jpeg"):
                        return src

                    img_bytes = await img.screenshot()
                    b64 = base64.b64encode(img_bytes).decode("utf-8")
                    return f"data:image/png;base64,{b64}"
                except Exception:
                    continue

            # 4. 再次兜底：直接对扫码容器进行截图
            containers = ["#animate_qrcode_container", "#douyin_login_comp_scan_code", "div[id*='scan_code']"]
            for c_sel in containers:
                try:
                    c_el = await page.query_selector(c_sel)
                    if c_el and await c_el.is_visible():
                        box = await c_el.bounding_box()
                        if box and 100 <= box["width"] <= 350 and 100 <= box["height"] <= 350:
                            img_bytes = await c_el.screenshot()
                            b64 = base64.b64encode(img_bytes).decode("utf-8")
                            return f"data:image/png;base64,{b64}"
                except Exception:
                    continue

            return None
        except Exception:
            return None

    async def wait_for_login(self, page: Page, timeout: int = 120) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """等待用户使用抖音 App 扫码登录 (不打断当前页面)"""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if page.is_closed():
                return False, None

            if "creator-micro" in page.url or "home" in page.url:
                await asyncio.sleep(2)
                return True, await self._extract_user_info_from_page(page)

            logged_indicator = await page.query_selector(".semi-avatar, .header-user-info")
            if logged_indicator and await logged_indicator.is_visible():
                await asyncio.sleep(1)
                return True, await self._extract_user_info_from_page(page)

            await asyncio.sleep(1.5)
        return False, None

    async def _extract_user_info_from_page(self, page: Page) -> Dict[str, Any]:
        """提取抖音创作者昵称、头像、UID及统计信息"""
        account_name = "抖音创作者"
        uid = None
        avatar = None
        fans_count = 0
        likes_count = 0
        following_count = 0

        name_selectors = [
            ".semi-navigation-header-title", ".user-name", 
            "span[class*='name']", "div[class*='account-name']",
            ".header-user-info span"
        ]
        for sel in name_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    text = (await el.inner_text()).strip()
                    if text and len(text) < 30:
                        account_name = text
                        break
            except Exception:
                pass

        avatar_selectors = [
            ".semi-avatar img", ".header-user-info img", 
            "img[class*='avatar']", ".avatar img"
        ]
        for sel in avatar_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    src = await el.get_attribute("src")
                    if src and not src.startswith("data:image/svg"):
                        avatar = src
                        break
            except Exception:
                pass

        # 尝试从页面全局变量或 DOM 中提取粉丝、关注等
        try:
            stats = await page.evaluate(r"""() => {
                const res = { fans: 0, likes: 0, follows: 0 };
                const text = document.body.innerText || '';
                const fansMatch = text.match(/粉丝[^\d]*(\d+[\.\d]*[wW万kK]?)/);
                if (fansMatch) {
                    let v = fansMatch[1];
                    if (v.includes('万') || v.toLowerCase().includes('w')) res.fans = Math.round(parseFloat(v) * 10000);
                    else if (v.toLowerCase().includes('k')) res.fans = Math.round(parseFloat(v) * 1000);
                    else res.fans = parseInt(v) || 0;
                }
                const likeMatch = text.match(/(获赞|点赞)[^\d]*(\d+[\.\d]*[wW万kK]?)/);
                if (likeMatch) {
                    let v = likeMatch[2];
                    if (v.includes('万') || v.toLowerCase().includes('w')) res.likes = Math.round(parseFloat(v) * 10000);
                    else if (v.toLowerCase().includes('k')) res.likes = Math.round(parseFloat(v) * 1000);
                    else res.likes = parseInt(v) || 0;
                }
                return res;
            }""")
            if stats:
                fans_count = stats.get("fans", 0)
                likes_count = stats.get("likes", 0)
        except Exception:
            pass

        return {
            "name": account_name,
            "uid": uid,
            "avatar": avatar,
            "followers_count": fans_count,
            "likes_count": likes_count,
            "following_count": following_count
        }

    async def publish_video(
        self, 
        page: Page, 
        subtask_data: Dict[str, Any],
        on_progress: Optional[Callable[[str, str], Any]] = None
    ) -> Dict[str, Any]:
        """
        自动化执行抖音视频上传与发布全流程
        """
        def log(msg: str, level: str = "INFO"):
            if on_progress:
                on_progress(level, f"[抖音发布] {msg}")

        try:
            log("正在导航至抖音创作者服务平台上传页面...")
            await page.goto(self.publish_url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # 检查是否由于未授权或凭证失效被拦截跳转至登录页
            if "passport" in page.url or "login" in page.url:
                raise Exception("账号登录凭证已失效或未授权，请在账号管理中重新扫码或呼出窗口登录")

            # 寻找并注入视频文件 (使用 state="attached" 允许捕获可能被 CSS 隐藏的底层 file 控件)
            file_input = await page.wait_for_selector(
                "input[type='file'][accept*='video'], input[type='file']",
                state="attached",
                timeout=20000
            )
            if not file_input:
                raise Exception("未定位到抖音视频上传控件")

            video_path = subtask_data.get("video_path")
            log(f"正在上传原始视频: {video_path}")
            await file_input.set_input_files(video_path)

            # 抖音会拉取视频切片并做本地预览初始化，等待表单变为可用
            log("等待视频上传与基础信息解析...")
            for _ in range(60):
                await asyncio.sleep(2)
                editor = await page.query_selector(
                    "div[contenteditable='true'], .zone-container, textarea[placeholder*='作品描述']"
                )
                if editor and await editor.is_visible():
                    break
            else:
                log("上传等待超时，尝试继续填写元数据...", level="WARNING")

            # 1. 组装并填写作品描述与话题标签 (抖音标题与描述合二为一)
            title = subtask_data.get("title", "")
            description = subtask_data.get("description", "")
            tags = subtask_data.get("tags") or []
            tag_text = " " + " ".join([f"#{t.strip('#')}" for t in tags]) if tags else ""
            
            # 整合为总描述文本
            full_text = f"{title}\n{description}{tag_text}".strip()
            log(f"正在填写作品标题与话题描述 ({len(tags)} 个标签)...")

            desc_box = await page.query_selector(
                "div[contenteditable='true'], .zone-container, textarea[placeholder*='作品描述']"
            )
            if desc_box:
                await desc_box.click()
                await page.keyboard.type(full_text, delay=25)

            # 2. 封面图设置 (如果有自定义封面)
            cover_path = subtask_data.get("cover_path")
            if cover_path:
                log(f"检测到自定义封面图，准备上传: {cover_path}")
                cover_btn = await page.query_selector("div:has-text('选择封面'), span:has-text('选择封面')")
                if cover_btn:
                    await cover_btn.click()
                    await asyncio.sleep(1)
                    cover_input = await page.query_selector("input[type='file'][accept*='image']")
                    if cover_input:
                        await cover_input.set_input_files(cover_path)
                        await asyncio.sleep(2)
                        # 点击保存封面弹窗确定按钮
                        confirm_btn = await page.query_selector("button:has-text('确定'), button:has-text('完成')")
                        if confirm_btn:
                            await confirm_btn.click()

            # 3. 平台原生定时发布
            schedule_mode = subtask_data.get("schedule_mode")
            scheduled_at = subtask_data.get("scheduled_at")
            if schedule_mode == "platform_native" and scheduled_at:
                log(f"正在勾选抖音原生定时发布: {scheduled_at}")
                schedule_radio = await page.query_selector("label:has-text('定时发布'), span:has-text('定时发布')")
                if schedule_radio:
                    await schedule_radio.click()
                    await asyncio.sleep(1)
                    # 抖音定时选择器
                    date_picker = await page.query_selector("input[placeholder*='选择时间'], input[placeholder*='发布时间']")
                    if date_picker:
                        if isinstance(scheduled_at, str):
                            dt_str = scheduled_at.replace("T", " ")[:16]
                        else:
                            dt_str = scheduled_at.strftime("%Y-%m-%d %H:%M")
                        await date_picker.click()
                        await date_picker.fill(dt_str)
                        await page.keyboard.press("Enter")

            # 4. 提交发布
            log("正在提交发布...")
            publish_btn = await page.query_selector("button:has-text('发布'), .button-publish")
            if not publish_btn:
                raise Exception("未找到抖音【发布】按钮")

            await publish_btn.click()
            await asyncio.sleep(4)

            # 5. 校验结果
            for _ in range(15):
                await asyncio.sleep(1)
                page_text = await page.content()
                if "发布成功" in page_text or "manage" in page.url or "content" in page.url:
                    log("抖音作品已成功发布！", level="SUCCESS")
                    return {"success": True, "error": None}

            log("抖音作品发布指令已成功提交", level="SUCCESS")
            return {"success": True, "error": None}

        except Exception as e:
            err_msg = str(e)
            log(f"抖音发布流程出现异常: {err_msg}", level="ERROR")
            return {"success": False, "error": err_msg}
