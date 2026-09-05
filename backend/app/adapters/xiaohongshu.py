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
        """访问创作者后台主页，通过 Cookie 与页面重定向判断登录态有效性"""
        try:
            # 1. 先探测 context 中是否存在小红书核心鉴权 Cookie
            cookies = await page.context.cookies()
            cookie_names = [c["name"].lower() for c in cookies]
            if not any(k in cookie_names for k in ["web_session", "a1", "webid"]):
                return False, None

            # 2. 访问创作者主页
            await page.goto(self.creator_url, timeout=25000, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            # 若重定向回登录页或携带 401 提示，则说明未登录或已过期
            curr_url = page.url
            if "login" in curr_url or "401" in curr_url:
                return False, None

            info = await self._extract_user_info_from_page(page)
            return True, info
        except Exception:
            return False, None

    async def get_login_qrcode(self, page: Page) -> Optional[str]:
        """打开小红书登录页，自动切换至扫码模式并精准提取真实 160x160 登录二维码"""
        try:
            await page.goto(self.login_url, timeout=20000, wait_until="domcontentloaded")
            await asyncio.sleep(1.5)

            # 1. 优先检查当前是否已经展示真实二维码 (尺寸需 >= 100x100，排除 64x64 的右上角角标图标)
            imgs = await page.query_selector_all("img")
            for img in imgs:
                try:
                    box = await img.bounding_box()
                    src = await img.get_attribute("src")
                    if box and box["width"] >= 100 and box["height"] >= 100 and src and src.startswith("data:image"):
                        return src
                except Exception:
                    continue

            # 2. 若未展示真实二维码，说明默认停留在手机号/验证码登录态，需点击右上角角标切换为扫码登录
            toggle_selectors = [
                "img.css-wemwzq", 
                ".css-jjnw1w", 
                "div[class*='login-box'] img",
                ".login-box-container img",
                "img[class*='wemwzq']"
            ]
            for sel in toggle_selectors:
                toggle = await page.query_selector(sel)
                if toggle:
                    try:
                        await toggle.click()
                        break
                    except Exception:
                        continue

            # 3. 点击切换后，轮询等待真实二维码生成 (寻找 width >= 100 的 data:image 图片)
            for _ in range(12):  # 最多等待 6 秒
                await asyncio.sleep(0.5)
                imgs = await page.query_selector_all("img")
                for img in imgs:
                    try:
                        box = await img.bounding_box()
                        src = await img.get_attribute("src")
                        if box and box["width"] >= 100 and box["height"] >= 100 and src and src.startswith("data:image"):
                            return src
                    except Exception:
                        continue

            # 4. 备用：按专有类名精准查找或截图
            qr_el = await page.query_selector("img.css-1lhmg90, div.css-1d81qt0 img, .qrcode-img")
            if qr_el:
                src = await qr_el.get_attribute("src")
                if src and src.startswith("data:image"):
                    return src
                img_bytes = await qr_el.screenshot()
                b64 = base64.b64encode(img_bytes).decode("utf-8")
                return f"data:image/png;base64,{b64}"

            return None
        except Exception:
            return None

    async def wait_for_login(self, page: Page, timeout: int = 120) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """轮询等待用户在手机 App 上确认扫码授权 (不主动调用 page.goto，绝不打断用户操作)"""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if page.is_closed():
                return False, None

            # 1. 检查页面 URL 是否已跳转离开登录页
            if "login" not in page.url:
                await asyncio.sleep(2)
                info = await self._extract_user_info_from_page(page)
                return True, info

            # 2. 检查是否出现已登录用户标识元素
            success_indicator = await page.query_selector(".user-info, .header-avatar, .con-name, .name-box")
            if success_indicator and await success_indicator.is_visible():
                await asyncio.sleep(1)
                info = await self._extract_user_info_from_page(page)
                return True, info

            await asyncio.sleep(1.5)
        return False, None

    async def _extract_user_info_from_page(self, page: Page) -> Dict[str, Any]:
        """从当前已登录页面中提取创作者昵称等基本信息"""
        account_name = "小红书创作者"
        name_selectors = [
            ".name-box", ".user-name", ".con-name", 
            "div[class*='userName']", "div[class*='name']",
            ".author-name", ".user-info span"
        ]
        for sel in name_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    text = (await el.inner_text()).strip()
                    if text and len(text) < 40:
                        account_name = text
                        break
            except Exception:
                pass
        return {"name": account_name, "uid": None, "avatar": None}

    async def _safe_input_text(
        self, 
        page: Page, 
        selectors: list, 
        text: str, 
        log_fn: Optional[Callable] = None
    ) -> bool:
        """
        智能安全输入：
        1. 依次匹配候选选择器，自动判断是否为真实 input/textarea 或 contenteditable；
        2. 若匹配到的是外层容器 div，自动向下钻取真正的输入控件；
        3. 优先执行 click 聚焦，并结合 Control+A + Backspace 与 fill("") 彻底清空；
        4. 采用 keyboard.type 模拟真实人工键入，确保触发前端数据双向绑定与字数统计响应。
        """
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if not el:
                    continue
                
                # 检查当前节点是否可编辑
                tag_name = await el.evaluate("el => el.tagName ? el.tagName.toLowerCase() : ''")
                is_editable = await el.evaluate(
                    "el => el.isContentEditable || ['input', 'textarea'].includes((el.tagName || '').toLowerCase())"
                )
                
                target_el = el
                if not is_editable:
                    # 向下查找真实输入控件
                    child = await el.query_selector("input, textarea, [contenteditable='true']")
                    if child:
                        target_el = child
                        tag_name = await target_el.evaluate("el => el.tagName ? el.tagName.toLowerCase() : ''")
                    else:
                        continue

                # 聚焦目标输入元素
                await target_el.click()
                await asyncio.sleep(0.1)

                # 清空现有内容（优先 fill("")，兼容 Control+A + Backspace）
                try:
                    if tag_name in ['input', 'textarea']:
                        await target_el.fill("")
                    else:
                        await page.keyboard.press("Control+A")
                        await page.keyboard.press("Backspace")
                except Exception:
                    await page.keyboard.press("Control+A")
                    await page.keyboard.press("Backspace")

                await asyncio.sleep(0.1)
                if text:
                    await page.keyboard.type(text, delay=25)
                return True
            except Exception as ex:
                continue
        return False

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
            # 注入 Shadow DOM Hook，将 Web Component 内部的 Closed Shadow DOM 转换为 Open，以便获取内部真实【发布】按钮
            try:
                await page.add_init_script("""
                    const origAttachShadow = Element.prototype.attachShadow;
                    Element.prototype.attachShadow = function(init) {
                        return origAttachShadow.call(this, { ...init, mode: 'open' });
                    };
                """)
            except Exception:
                pass

            log("正在进入小红书创作者中心发布页...")
            await page.goto(self.publish_url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # 检查是否由于未授权或凭证失效被拦截跳转至登录页
            if "login" in page.url or "401" in page.url:
                raise Exception("账号登录凭证已失效或未授权，请在账号管理中重新扫码或呼出窗口登录")

            # 切换到“上传视频”标签（若存在图文/视频切换标签）
            try:
                video_tab = await page.wait_for_selector(
                    "div:has-text('上传视频'), span:has-text('上传视频'), .tab:has-text('视频')",
                    timeout=5000
                )
                if video_tab and await video_tab.is_visible():
                    await video_tab.click()
                    await asyncio.sleep(1)
            except Exception:
                pass

            # 定位文件上传 input 控件 (小红书前端 input.upload-input 设置了隐藏样式，必须使用 state='attached' 捕获)
            file_input = await page.wait_for_selector(
                "input.upload-input, input[type='file'][accept*='video'], input[type='file']",
                state="attached",
                timeout=20000
            )
            if not file_input:
                raise Exception("未找到小红书视频上传控件")

            video_path = subtask_data.get("video_path")
            log(f"正在上传原始视频文件: {video_path}")
            await file_input.set_input_files(video_path)

            # 等待视频上传并解析完成（轮询检测进度或完成标识）
            log("等待视频上传与服务端转码解析...")
            for _ in range(60):  # 最多等待 120 秒
                await asyncio.sleep(2)
                # 检测上传成功或者标题/正文输入框是否变为可用
                ready_el = await page.query_selector(
                    ".c-input_inner input, input[placeholder*='标题'], input[maxlength='20'], #post-textarea, .post-content"
                )
                if ready_el and await ready_el.is_visible():
                    break
            else:
                log("上传等待超时，尝试继续填写元数据...", level="WARNING")

            # 1. 填写标题 (小红书标题严格限制最大 20 个汉字/字符)
            raw_title = subtask_data.get("title", "")
            xhs_title = raw_title[:20] if len(raw_title) > 20 else raw_title
            log(f"正在填写标题: {xhs_title}")
            title_selectors = [
                ".c-input_inner input",
                "input[placeholder*='标题']",
                "div[class*='title'] input",
                ".title-input input",
                ".c-input input",
                "input.c-input_inner",
                "input[maxlength='20']",
                "input[placeholder*='填写标题']",
                ".c-input_inner",
                "div[class*='title']",
            ]
            title_ok = await self._safe_input_text(page, title_selectors, xhs_title, log_fn=log)
            if not title_ok:
                log("未通过选择器直接匹配到标题输入框，尝试向当前焦点直接键入标题...", level="WARNING")
                await page.keyboard.type(xhs_title, delay=25)

            # 2. 填写正文描述与话题标签
            description = subtask_data.get("description") or ""
            tags = subtask_data.get("tags") or []
            if tags:
                tag_str = " " + " ".join([f"#{t.strip('#')}" for t in tags])
                full_desc = description + tag_str
            else:
                full_desc = description

            log(f"正在填写正文描述及 {len(tags)} 个话题标签...")
            desc_selectors = [
                "#post-textarea",
                ".post-content",
                "div[contenteditable='true']",
                "textarea[placeholder*='描述']",
                ".ql-editor",
                "div[class*='editor']",
            ]
            desc_ok = await self._safe_input_text(page, desc_selectors, full_desc, log_fn=log)
            if not desc_ok:
                log("未通过选择器直接匹配到描述区域，尝试向当前焦点直接键入描述...", level="WARNING")
                await page.keyboard.type(full_desc, delay=20)

            # 关闭可能弹出的联想话题下拉菜单，避免阻挡后续点击
            try:
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.5)
            except Exception:
                pass

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

            # 5. 等待发布按钮就绪并提交发布
            log("正在检测并等待【发布】按钮就绪...")
            for i in range(30):
                is_ready = await page.evaluate("""() => {
                    const host = document.querySelector('xhs-publish-btn');
                    if (host) {
                        const disabled = host.getAttribute('submit-disabled');
                        if (disabled === 'false') return true;
                        if (host.shadowRoot) {
                            const btn = host.shadowRoot.querySelector('button.bg-red, button:not(.white)');
                            if (btn && !btn.disabled) return true;
                        }
                    }
                    const normalBtn = document.querySelector('button.publishBtn, .ce-btn.bg-red, .publish-page-publish-btn button');
                    if (normalBtn && !normalBtn.disabled) return true;
                    for (const b of document.querySelectorAll('button')) {
                        if ((b.innerText || '').trim() === '发布' && !b.disabled) return true;
                    }
                    return false;
                }""")
                if is_ready:
                    break
                await asyncio.sleep(1)

            log("正在点击提交【发布】按钮...")
            clicked = False

            # 策略 1: 通过 Shadow DOM 内部红色按钮触发点击
            clicked = await page.evaluate("""() => {
                const host = document.querySelector('xhs-publish-btn');
                if (host && host.shadowRoot) {
                    const btn = host.shadowRoot.querySelector('button.bg-red, button:not(.white)');
                    if (btn) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            }""")

            # 策略 2: 使用 Playwright Shadow Piercing 选择器定位并点击
            if not clicked:
                try:
                    red_btn = page.locator("xhs-publish-btn button.bg-red, xhs-publish-btn >> button.bg-red, xhs-publish-btn >> button:has-text('发布')")
                    if await red_btn.count() > 0:
                        await red_btn.first.click()
                        clicked = True
                except Exception:
                    pass

            # 策略 3: 常规 DOM 选择器探测点击
            if not clicked:
                for sel in ["button:has-text('发布')", ".publishBtn", "button.ce-btn.bg-red", "div.publish-btn"]:
                    btn = await page.query_selector(sel)
                    if btn and await btn.is_visible():
                        await btn.click()
                        clicked = True
                        break

            # 策略 4: 基于 <xhs-publish-btn> 宿主容器坐标计算偏移模拟真实鼠标点击
            # 按钮栏中“发布”按钮位于容器中心偏右 +72px 处
            if not clicked:
                host_el = await page.query_selector("xhs-publish-btn")
                if host_el:
                    box = await host_el.bounding_box()
                    if box:
                        target_x = box["x"] + box["width"] / 2 + 72
                        target_y = box["y"] + box["height"] / 2
                        log(f"通过组件坐标辅助模拟物理点击【发布】: ({target_x}, {target_y})")
                        await page.mouse.click(target_x, target_y)
                        clicked = True

            if not clicked:
                raise Exception("未找到小红书【发布】提交按钮")

            # 6. 验证发布结果
            # 紧跟点击后持续监测平台 Toast 拦截报错（如未绑定手机号、违规限制）或跳转成功页面
            for sec in range(20):
                await asyncio.sleep(0.8)

                # 优先检测平台错误拦截提示（小红书原生为 .d-new-toast / .d-toast-content / .d-toast-icon-danger）
                toast_err = await page.evaluate("""() => {
                    const dangerToast = document.querySelector(
                        '.d-toast-icon-danger, .d-toast-content, .d-new-toast, .el-message--error, .toast-error'
                    );
                    if (dangerToast) {
                        const parent = dangerToast.closest('.d-new-toast, .d-toast-notice, .el-message') || dangerToast;
                        const t = (parent.innerText || '').trim();
                        if (t) return t;
                    }
                    return null;
                }""")
                if toast_err:
                    raise Exception(f"小红书平台拦截提示: {toast_err}")

                # 检测是否跳转离开编辑页面
                curr_url = page.url
                if "publish/success" in curr_url or "creator/notes" in curr_url:
                    log("小红书视频已成功发布！", level="SUCCESS")
                    return {"success": True, "work_id": None, "work_url": None, "error": None}

                page_text = await page.content()
                if "发布成功" in page_text or "已发布" in page_text:
                    log("小红书视频已成功发布！", level="SUCCESS")
                    return {"success": True, "work_id": None, "work_url": None, "error": None}

            # 如果 16 秒后仍在发布页面，且没有任何成功标识，说明平台未放行
            if "publish/publish" in page.url:
                raise Exception("小红书发布未能确认成功（仍停留在发布页面），平台可能存在未提示的资质校验或风控拦截")

            log("页面已跳转，发布已完成", level="SUCCESS")
            return {"success": True, "error": None}

        except Exception as e:
            err_msg = str(e)
            log(f"小红书发布过程出现异常: {err_msg}", level="ERROR")
            return {"success": False, "error": err_msg}
