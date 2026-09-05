import asyncio
import base64
import re
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
        """访问抖音创作者后台，校验当前会话 Cookie 是否有效并同步创作者信息"""
        try:
            await page.goto(self.creator_url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(2.5)

            # 抖音若未登录会重定向至根域登录页或包含 passport/login
            if "passport" in page.url or page.url.rstrip("/") == "https://creator.douyin.com":
                login_btn = await page.query_selector(".login-button, div:has-text('登录')")
                if login_btn and await login_btn.is_visible():
                    return False, None

            # 检查是否处于创作者后台或检测到登录要素
            is_logged = "creator-micro" in page.url or "home" in page.url
            if not is_logged:
                indicator = await page.query_selector("img[src*='aweme-avatar'], .semi-avatar, .header-user-info")
                if indicator and await indicator.is_visible():
                    is_logged = True

            if not is_logged:
                return False, None

            info = await self._extract_user_info_from_page(page)
            return True, info
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

        # 获取页面纯文本用于正则匹配
        page_text = ""
        try:
            page_text = await page.evaluate("() => (document.body ? document.body.innerText : '')")
        except Exception:
            pass

        # 1. 提取抖音号/UID (如 "抖音号：614542688")
        if page_text:
            uid_match = re.search(r"抖音号[：:\s]*([a-zA-Z0-9_\-\.]+)", page_text)
            if uid_match:
                uid = uid_match.group(1).strip()

        # 兜底：若未从文本匹配到，尝试从 localStorage 提取 user_unique_id
        if not uid:
            try:
                ls_uid = await page.evaluate(r"""() => {
                    try {
                        const v = localStorage.getItem('SLARDARdouyin_creator');
                        if (v) {
                            const parsed = JSON.parse(decodeURIComponent(v));
                            return parsed.userId || null;
                        }
                    } catch(e) {}
                    return null;
                }""")
                if ls_uid:
                    uid = str(ls_uid).strip()
            except Exception:
                pass

        # 2. 提取创作者昵称
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
                    if text and len(text) < 30 and "创作者" not in text:
                        account_name = text
                        break
            except Exception:
                pass

        if account_name == "抖音创作者" and page_text:
            # 尝试通过正则在 "抖音号" 前一行匹配创作者昵称
            name_match = re.search(r"([^\n\r]+)\n+抖音号", page_text)
            if name_match:
                found_name = name_match.group(1).strip()
                if found_name and len(found_name) < 30 and "AI" not in found_name:
                    account_name = found_name

        # 3. 提取创作者头像 (抖音真实 CDN 包含 aweme-avatar 或 douyinpic.com)
        avatar_selectors = [
            "img[src*='aweme-avatar']",
            "img[src*='douyinpic.com']",
            ".img-PeynF_",
            ".semi-avatar img", 
            ".header-user-info img", 
            "img[class*='avatar']", 
            ".avatar img"
        ]
        for sel in avatar_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    src = await el.get_attribute("src")
                    if src and not src.startswith("data:image/svg") and not src.startswith("data:image/"):
                        avatar = src
                        break
            except Exception:
                pass

        # 4. 从页面提取粉丝、获赞、关注数
        try:
            stats = await page.evaluate(r"""() => {
                const res = { fans: 0, likes: 0, follows: 0 };
                const text = document.body ? document.body.innerText : '';
                
                const parseNum = (match) => {
                    if (!match) return 0;
                    let v = match[1];
                    if (v.includes('万') || v.toLowerCase().includes('w')) return Math.round(parseFloat(v) * 10000);
                    if (v.toLowerCase().includes('k')) return Math.round(parseFloat(v) * 1000);
                    return parseInt(v, 10) || 0;
                };

                const fansMatch = text.match(/粉丝[^\d]*(\d+[\.\d]*[wW万kK]?)/);
                res.fans = parseNum(fansMatch);

                const likeMatch = text.match(/(?:获赞|点赞)[^\d]*(\d+[\.\d]*[wW万kK]?)/);
                res.likes = parseNum(likeMatch);

                const followMatch = text.match(/关注[^\d]*(\d+[\.\d]*[wW万kK]?)/);
                res.follows = parseNum(followMatch);

                return res;
            }""")
            if stats:
                fans_count = stats.get("fans", 0)
                likes_count = stats.get("likes", 0)
                following_count = stats.get("follows", 0)
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
        on_progress: Optional[Callable[[str, str], Any]] = None,
        on_verify_required: Optional[Callable[[Dict[str, Any]], Any]] = None
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

            # 轮询等待视频上传并服务端解析就绪 (最长等待 180 秒)
            log("正在上传视频并等待服务端转码解析...")
            upload_finished = False
            for wait_idx in range(90):
                await asyncio.sleep(2)

                # 检测并关闭新功能遮罩或引导气泡 (如 "视频预览功能 [我知道了]")
                try:
                    got_it = await page.query_selector("button:has-text('我知道了'), div:has-text('我知道了')")
                    if got_it and await got_it.is_visible():
                        await got_it.click()
                        await asyncio.sleep(0.3)
                except Exception:
                    pass

                # 探测视频是否上传解析完毕 (右侧面板出现重新上传按钮或手机播放预览)
                reupload = await page.query_selector("div:has-text('重新上传'), span:has-text('重新上传'), button:has-text('重新上传')")
                if reupload and await reupload.is_visible():
                    upload_finished = True
                    log("视频文件上传解析完毕！")
                    break

                # 提取上传进度并在每 10 秒输出一次进度
                if wait_idx % 5 == 0:
                    try:
                        progress_text = await page.evaluate(r"""() => {
                            const match = document.body ? document.body.innerText.match(/(\d+[\.\d]*%|\d+MB\/\d+MB)/) : null;
                            return match ? match[0] : null;
                        }""")
                        if progress_text:
                            log(f"视频上传进度: {progress_text}...")
                    except Exception:
                        pass
            else:
                log("视频上传等待超时，尝试继续填写元数据...", level="WARNING")

            # 1. 填写独立作品标题 (抖音官方标题上限 30 字)
            title = subtask_data.get("title", "")
            title_30 = title[:30] if len(title) > 30 else title
            if title_30:
                log(f"正在填写作品标题: {title_30}")
                title_input = await page.query_selector("input[placeholder*='填写作品标题'], input.semi-input")
                if title_input and await title_input.is_visible():
                    await title_input.click()
                    await title_input.fill(title_30)
                    await asyncio.sleep(0.3)

            # 2. 填写作品描述与话题标签 (转换为官方蓝色话题实体)
            description = subtask_data.get("description", "")
            tags = subtask_data.get("tags") or []
            log(f"正在填写作品描述 (包含 {len(tags)} 个话题标签)...")

            desc_box = await page.query_selector("div[contenteditable='true'], .zone-container")
            if desc_box:
                await desc_box.click()
                if description:
                    await page.keyboard.type(description, delay=20)
                    await asyncio.sleep(0.3)

                # 逐个注入抖音官方话题标签
                if tags:
                    log(f"正在将 {len(tags)} 个话题标签转换为平台官方话题节点...")
                    for tag in tags:
                        tag_clean = str(tag).strip().lstrip("#").strip()
                        if not tag_clean:
                            continue

                        # 优先点击编辑框下方的“#添加话题”按钮以拉起话题推荐
                        topic_btn = await page.query_selector("div[class*='toolbar-button']:has-text('添加话题'), span:has-text('添加话题')")
                        if topic_btn and await topic_btn.is_visible():
                            await topic_btn.click()
                        else:
                            await page.keyboard.type(" #")

                        await asyncio.sleep(0.3)
                        await page.keyboard.type(tag_clean, delay=40)
                        await asyncio.sleep(0.6)

                        # 敲击回车选中联想话题
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(0.4)

            # 3. 封面图设置 (如果有自定义封面)
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

            # 4. 平台原生定时发布
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

            # 5. 滚动到页面底部定位真实的表单提交【发布】按钮 (严苛排除导航栏按钮)
            log("正在检测并定位表单提交【发布】按钮...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)

            # 严苛排除左侧导航栏的菜单按钮 (如 .header-button-KP2xn1 '作品发布')
            publish_btn = await page.query_selector(
                "button.primary-cECiOJ:has-text('发布'), button.button-dhlUZE:has-text('发布'), button.fixed-J9O8Yw:has-text('发布')"
            )
            if not publish_btn:
                btns = await page.query_selector_all("button")
                for b in btns:
                    txt = (await b.inner_text()).strip()
                    cls = (await b.get_attribute("class")) or ""
                    if txt == "发布" and "header-button" not in cls and "master-button" not in cls:
                        publish_btn = b
                        break

            if not publish_btn:
                raise Exception("未找到抖音表单底部的【发布】提交按钮")

            await publish_btn.scroll_into_view_if_needed()
            log("正在点击提交【发布】按钮...")
            await publish_btn.click()
            await asyncio.sleep(2)

            # 6. 校验发布结果与安全验证感知 (彻底杜绝以 'content' 为依据的假阳性判断)
            upload_url = self.publish_url
            for sec in range(60):
                await asyncio.sleep(1)
                curr_url = page.url
                page_text = await page.evaluate("() => document.body ? document.body.innerText : ''")

                # 自动关闭功能引导气泡（如“视频预览功能：我知道了”）
                know_btn = await page.query_selector("button:has-text('我知道了'), div:has-text('我知道了')")
                if know_btn and await know_btn.is_visible():
                    try:
                        await know_btn.click()
                    except Exception:
                        pass

                # 1) 检测是否弹出短信验证码弹窗 (文本包含 '接收短信验证码' 或页面已挂载验证码输入框)
                code_input = await page.query_selector("input[placeholder*='验证码']")
                is_sms_verify = ("接收短信验证码" in page_text or "当前手机号" in page_text) or (code_input is not None and await code_input.is_visible())
                if is_sms_verify:
                    log("检测到抖音触发二次安全短信验证码...", level="WARNING")
                    phone_match = re.search(r"当前手机号[：:\s]*([0-9\*]+)", page_text)
                    phone_str = phone_match.group(1) if phone_match else ""

                    # 自动触发点击【获取验证码】 (抖音创作者中心中为 .uc-ui-input_right 或 p.uc-ui-typography_description)
                    for click_try in range(5):
                        get_code_btn = await page.query_selector(".uc-ui-input_right p, .uc-ui-input_right, p:has-text('获取验证码')")
                        if get_code_btn and await get_code_btn.is_visible():
                            btn_text = (await get_code_btn.inner_text()).strip()
                            if "获取验证码" in btn_text and "重新" not in btn_text and "秒" not in btn_text and "s" not in btn_text.lower():
                                log(f"正在自动点击【获取验证码】向手机 {phone_str} 发送短信验证码...")
                                try:
                                    await get_code_btn.click()
                                    await asyncio.sleep(0.8)
                                    after_text = (await get_code_btn.inner_text()).strip()
                                    if "秒" in after_text or "s" in after_text.lower():
                                        log("短信验证码获取指令已成功触发 (已进入倒计时状态)", level="SUCCESS")
                                        break
                                except Exception as click_err:
                                    log(f"点击获取验证码按钮异常: {click_err}", level="WARNING")
                        await asyncio.sleep(0.5)

                    if on_verify_required:
                        log(f"已唤起 Web 端内二次验证通道，等待用户输入收到的短信验证码 (目标手机: {phone_str})...", level="WARNING")
                        verify_queue: asyncio.Queue = await on_verify_required({
                            "type": "sms",
                            "phone": phone_str,
                            "timeout": 120
                        })

                        # 循环等待前端网页输入验证码或重发/取消指令
                        verify_start = asyncio.get_event_loop().time()
                        verification_passed = False
                        while asyncio.get_event_loop().time() - verify_start < 120:
                            time_left = max(1.0, 120 - (asyncio.get_event_loop().time() - verify_start))
                            try:
                                action_data = await asyncio.wait_for(verify_queue.get(), timeout=time_left)
                            except asyncio.TimeoutError:
                                log("等待用户输入短信验证码超时 (120秒)，发布终止", level="ERROR")
                                return {"success": False, "error": "短信验证码输入超时"}

                            action = action_data.get("action")
                            if action == "cancel":
                                log("用户在网页端取消了短信验证，终止发布", level="WARNING")
                                cancel_btn = await page.query_selector("div.uc-ui-verify_sms-verify_button:has-text('取消'), button:has-text('取消')")
                                if cancel_btn and await cancel_btn.is_visible():
                                    try:
                                        await cancel_btn.click()
                                    except Exception:
                                        pass
                                return {"success": False, "error": "用户取消短信验证"}

                            elif action == "resend":
                                log("用户请求重新获取短信验证码，正在触发页面点击...", level="INFO")
                                resend_btn = await page.query_selector(".uc-ui-input_right p, .uc-ui-input_right, p:has-text('获取验证码'), p:has-text('重新获取')")
                                if resend_btn and await resend_btn.is_visible():
                                    try:
                                        await resend_btn.click()
                                        log("已在后台成功点击重新发送验证码", level="SUCCESS")
                                    except Exception as e:
                                        log(f"重新点击发送验证码失败: {e}", level="WARNING")
                                else:
                                    log("当前无法重新获取验证码，可能尚未到重发间隔", level="WARNING")

                            elif action == "submit":
                                code = str(action_data.get("code", "")).strip()
                                if not code:
                                    continue
                                log(f"收到网页端输入的验证码 [{code}]，正在自动填入并提交校验...")
                                code_input = await page.query_selector("input[placeholder*='验证码']")
                                if code_input:
                                    await code_input.click()
                                    await code_input.fill("")
                                    await code_input.fill(code)
                                    await asyncio.sleep(0.3)
                                else:
                                    log("未在页面中找到验证码输入框", level="ERROR")
                                    continue

                                confirm_btn = await page.query_selector("div.uc-ui-verify_sms-verify_button:has-text('验证'), div.uc-ui-button:has-text('验证')")
                                if confirm_btn and await confirm_btn.is_visible():
                                    await confirm_btn.click()
                                    log("已点击【验证】按钮，正在校验...")
                                    await asyncio.sleep(2)

                                # 检查页面是否提示错误
                                error_tip = await page.query_selector(".semi-toast, .semi-form-item-explain, div[class*='error'], div[class*='feedback'], .uc-ui-typography_danger")
                                err_text = ""
                                if error_tip and await error_tip.is_visible():
                                    err_text = (await error_tip.inner_text()).strip()

                                curr_modal_text = ""
                                try:
                                    curr_modal_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
                                except Exception:
                                    pass

                                if any(w in err_text or w in curr_modal_text for w in ["错误", "失效", "不正确", "过期", "重新输入"]):
                                    fail_reason = err_text or "验证码错误或已失效"
                                    log(f"短信验证码校验未通过: {fail_reason}，等待重新输入...", level="ERROR")
                                    from app.core.event_bus import event_bus
                                    await event_bus.broadcast("verification_failed", {
                                        "subtask_id": subtask_data.get("id"),
                                        "error": fail_reason
                                    })
                                    continue
                                else:
                                    # 检查验证码输入框是否已经从页面消失，说明通过并关闭了弹窗
                                    check_input = await page.query_selector("input[placeholder*='验证码']")
                                    if check_input is None or not (await check_input.is_visible()):
                                        log("短信验证码已通过，验证弹窗已关闭！", level="SUCCESS")
                                        from app.core.event_bus import event_bus
                                        await event_bus.broadcast("verification_success", {
                                            "subtask_id": subtask_data.get("id")
                                        })
                                        verification_passed = True
                                        await asyncio.sleep(2)
                                        break
                                    else:
                                        await asyncio.sleep(1)
                                        check_input2 = await page.query_selector("input[placeholder*='验证码']")
                                        if check_input2 is None or not (await check_input2.is_visible()):
                                            log("短信验证码已通过，验证弹窗已关闭！", level="SUCCESS")
                                            from app.core.event_bus import event_bus
                                            await event_bus.broadcast("verification_success", {
                                                "subtask_id": subtask_data.get("id")
                                            })
                                            verification_passed = True
                                            await asyncio.sleep(2)
                                            break

                        if not verification_passed:
                            return {"success": False, "error": "短信验证码校验未通过"}
                    else:
                        # 未注入交互通道时的降级方案
                        log("未提供端内验证交互通道，请在实时视窗中手动输入短信验证码...", level="WARNING")
                        if sec > 45:
                            return {"success": False, "error": "抖音发布触发安全短信验证码，等待超时未完成"}
                        continue

                # 2) 检测是否弹出人机验证/滑动验证
                elif "人机验证" in page_text or "滑动验证" in page_text:
                    log("检测到抖音触发人机滑块验证，请打开实时视窗完成滑块验证...", level="WARNING")
                    if sec > 45:
                        return {"success": False, "error": "抖音发布触发人机滑块验证，等待超时未完成"}
                    continue

                # 3) 检测是否成功跳转至内容管理列表
                if "manage" in curr_url or "发布成功" in page_text or "已发布" in page_text or "作品已提交" in page_text:
                    log("抖音作品已成功发布！", level="SUCCESS")
                    return {"success": True, "error": None}

                # 4) 检查 URL 发生跳转且脱离了上传发布编辑页
                if "upload" not in curr_url and "post" not in curr_url and "creator-micro" in curr_url:
                    log("抖音作品已成功发布！", level="SUCCESS")
                    return {"success": True, "error": None}

            log("抖音发布等待超时，未能确认发布成功", level="ERROR")
            return {"success": False, "error": "发布提交后未检测到成功标志，可能处于审核或需要人工验证"}

        except Exception as e:
            err_msg = str(e)
            log(f"抖音发布流程出现异常: {err_msg}", level="ERROR")
            return {"success": False, "error": err_msg}
