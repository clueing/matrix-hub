import asyncio
import base64
from datetime import datetime
from typing import Tuple, Optional, Dict, Any, Callable
from playwright.async_api import Page
from app.adapters.base import BasePublisherAdapter

class XiaohongshuAdapter(BasePublisherAdapter):
    """
    小红书创作者服务平台适配器
    实现扫码登录截取、创作者状态探测、原视频自动上传、标题标签填充及平台原生定时发布
    """

    @property
    def platform_code(self) -> str:
        return "xiaohongshu"

    @property
    def platform_name(self) -> str:
        return "小红书"

    @property
    def creator_url(self) -> str:
        return "https://creator.xiaohongshu.com/creator/home"

    @property
    def login_url(self) -> str:
        return "https://creator.xiaohongshu.com/login"

    @property
    def publish_url(self) -> str:
        return "https://creator.xiaohongshu.com/publish/publish?source=official"

    async def check_login_status(self, page: Page) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """访问创作者后台主页，通过 URL 和界面用户信息元素判断登录态有效性"""
        try:
            await page.goto(self.creator_url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # 若重定向回登录页，则说明未登录或已过期
            if "login" in page.url:
                return False, None

            # 探测创作者昵称元素
            name_selectors = [
                ".name-box", ".user-name", ".con-name", 
                "div[class*='userName']", "div[class*='name']"
            ]
            account_name = "小红书创作者"
            for sel in name_selectors:
                el = await page.query_selector(sel)
                if el:
                    text = (await el.inner_text()).strip()
                    if text:
                        account_name = text
                        break

            return True, {
                "name": account_name,
                "uid": None,
                "avatar": None
            }
        except Exception as e:
            return False, None

    async def get_login_qrcode(self, page: Page) -> Optional[str]:
        """打开小红书登录页，自动定位二维码并截取为 Base64 供前端扫码"""
        try:
            await page.goto(self.login_url, timeout=30000, wait_until="networkidle")
            await asyncio.sleep(2)

            # 尝试切换到二维码扫码 Tab（部分页面默认是验证码登录）
            qr_tab = await page.query_selector("div:has-text('扫码登录'), span:has-text('二维码登录')")
            if qr_tab:
                await qr_tab.click()
                await asyncio.sleep(1)

            # 寻找二维码图片元素或 canvas
            qr_selectors = [
                ".qrcode-img", "img[class*='qrcode']", ".qrcode-box img",
                "div[class*='qrcode'] img", ".login-box img", "canvas[class*='qrcode']"
            ]
            qr_el = None
            for sel in qr_selectors:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    qr_el = el
                    break

            if qr_el:
                # 截取二维码元素
                img_bytes = await qr_el.screenshot()
                b64 = base64.b64encode(img_bytes).decode("utf-8")
                return f"data:image/png;base64,{b64}"
            
            # 若无法精确定位二维码节点，则截取右侧登录卡片区域
            login_box = await page.query_selector(".login-box, div[class*='login']")
            if login_box:
                img_bytes = await login_box.screenshot()
                b64 = base64.b64encode(img_bytes).decode("utf-8")
                return f"data:image/png;base64,{b64}"

            return None
        except Exception as e:
            return None

    async def wait_for_login(self, page: Page, timeout: int = 120) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """轮询等待用户在手机 App 上确认扫码授权"""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if "login" not in page.url:
                # 已经完成跳转进入后台
                await asyncio.sleep(2)
                return await self.check_login_status(page)
            
            # 检测是否已经出现登录后的用户控件
            success_indicator = await page.query_selector(".user-info, .header-avatar, .con-name")
            if success_indicator:
                return await self.check_login_status(page)

            await asyncio.sleep(2)
        return False, None

    async def publish_video(
        self, 
        page: Page, 
        subtask_data: Dict[str, Any],
        on_progress: Optional[Callable[[str, str], Any]] = None
    ) -> Dict[str, Any]:
        """
        自动化执行小红书视频上传与发布流程
        """
        def log(msg: str, level: str = "INFO"):
            if on_progress:
                on_progress(level, f"[小红书发布] {msg}")

        try:
            log("正在进入小红书创作者中心发布页...")
            await page.goto(self.publish_url, timeout=45000, wait_until="networkidle")
            await asyncio.sleep(2)

            # 切换到“上传视频”标签
            video_tab = await page.query_selector("div:has-text('上传视频'), span:has-text('上传视频')")
            if video_tab:
                await video_tab.click()
                await asyncio.sleep(1)

            # 定位文件上传 input 控件
            file_input = await page.query_selector("input[type='file'][accept*='video'], input[type='file']")
            if not file_input:
                raise Exception("未找到小红书视频上传控件")

            video_path = subtask_data.get("video_path")
            log(f"正在上传原始视频文件: {video_path}")
            await file_input.set_input_files(video_path)

            # 等待视频上传并解析完成（轮询检测进度或完成标识）
            log("等待视频上传与服务端转码解析...")
            for _ in range(60):  # 最多等待 120 秒
                await asyncio.sleep(2)
                # 检测上传成功或者标题输入框是否变为可编辑
                title_input = await page.query_selector("input[placeholder*='标题'], .c-input_inner")
                if title_input and await title_input.is_visible():
                    break
            else:
                log("上传等待超时，尝试继续填写元数据...", level="WARNING")

            # 1. 填写标题 (小红书标题严格限制最大 20 个汉字/字符)
            raw_title = subtask_data.get("title", "")
            xhs_title = raw_title[:20] if len(raw_title) > 20 else raw_title
            log(f"正在填写标题: {xhs_title}")
            title_input = await page.query_selector("input[placeholder*='标题'], .c-input_inner")
            if title_input:
                await title_input.fill("")
                await title_input.type(xhs_title, delay=30)

            # 2. 填写正文描述与话题标签
            description = subtask_data.get("description") or ""
            tags = subtask_data.get("tags") or []
            if tags:
                tag_str = " " + " ".join([f"#{t.strip('#')}" for t in tags])
                full_desc = description + tag_str
            else:
                full_desc = description

            log(f"正在填写正文描述及 {len(tags)} 个话题标签...")
            desc_editor = await page.query_selector(
                "#post-textarea, .post-content, div[contenteditable='true'], textarea[placeholder*='描述']"
            )
            if desc_editor:
                await desc_editor.click()
                await page.keyboard.type(full_desc, delay=20)

            # 3. 自定义封面图上传 (如果有)
            cover_path = subtask_data.get("cover_path")
            if cover_path:
                log(f"检测到自定义封面图，正在上传: {cover_path}")
                cover_input = await page.query_selector("input[type='file'][accept*='image']")
                if cover_input:
                    await cover_input.set_input_files(cover_path)
                    await asyncio.sleep(2)

            # 4. 平台原生定时发布设置
            schedule_mode = subtask_data.get("schedule_mode")
            scheduled_at = subtask_data.get("scheduled_at")
            if schedule_mode == "platform_native" and scheduled_at:
                log(f"正在设置平台原生定时发布: {scheduled_at}")
                # 勾选“定时发布”单选按钮
                schedule_radio = await page.query_selector("label:has-text('定时发布'), span:has-text('定时发布')")
                if schedule_radio:
                    await schedule_radio.click()
                    await asyncio.sleep(1)
                    # 尝试定位时间选择器输入控件并填写
                    # 小红书支持原生日期时间控件
                    date_input = await page.query_selector("input[placeholder*='选择时间'], input[placeholder*='选择日期']")
                    if date_input:
                        # 格式化日期字符串
                        if isinstance(scheduled_at, str):
                            dt_str = scheduled_at.replace("T", " ")[:16]
                        else:
                            dt_str = scheduled_at.strftime("%Y-%m-%d %H:%M")
                        await date_input.click()
                        await date_input.fill(dt_str)
                        await page.keyboard.press("Enter")

            # 5. 提交发布
            log("正在点击提交【发布】按钮...")
            publish_btn = await page.query_selector("button:has-text('发布'), .publishBtn")
            if not publish_btn:
                raise Exception("未找到小红书【发布】提交按钮")

            await publish_btn.click()
            await asyncio.sleep(4)

            # 6. 验证发布结果
            # 检测是否出现成功提示或者跳转离开编辑页面
            for _ in range(15):
                await asyncio.sleep(1)
                page_text = await page.content()
                if "发布成功" in page_text or "已发布" in page_text or "publish/success" in page.url:
                    log("小红书视频已成功发布！", level="SUCCESS")
                    return {
                        "success": True,
                        "work_id": None,
                        "work_url": None,
                        "error": None
                    }
                # 检测平台拦截提示（如未完成实名、违规敏感词等）
                error_el = await page.query_selector(".el-message--error, .toast-error, div[class*='error']")
                if error_el and await error_el.is_visible():
                    err_text = await error_el.inner_text()
                    raise Exception(f"小红书平台提示错误: {err_text}")

            log("发布指令已送达，已完成提交", level="SUCCESS")
            return {"success": True, "error": None}

        except Exception as e:
            err_msg = str(e)
            log(f"小红书发布过程出现异常: {err_msg}", level="ERROR")
            return {"success": False, "error": err_msg}
