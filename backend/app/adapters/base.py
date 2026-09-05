from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any, Callable
from playwright.async_api import Page

class BasePublisherAdapter(ABC):
    """
    平台自动化适配器抽象基类
    统一各社交平台（小红书、抖音、快手、视频号等）的登录识别、扫码推流及自动化发布流程
    """

    @property
    @abstractmethod
    def platform_code(self) -> str:
        """平台代码标识，如 'xiaohongshu', 'douyin'"""
        pass

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """平台中文名，如 '小红书', '抖音'"""
        pass

    @property
    @abstractmethod
    def creator_url(self) -> str:
        """创作者平台主页入口"""
        pass

    @property
    @abstractmethod
    def login_url(self) -> str:
        """创作者平台登录页入口"""
        pass

    @abstractmethod
    async def check_login_status(self, page: Page) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        检查当前页面或会话是否处于登录有效状态
        :param page: Playwright 页面对象
        :return: (是否已登录, 创作者信息字典 {'uid': ..., 'name': ..., 'avatar': ...})
        """
        pass

    @abstractmethod
    async def get_login_qrcode(self, page: Page) -> Optional[str]:
        """
        打开登录页面并提取登录二维码的 Base64 图片数据 URL (data:image/png;base64,...)
        :param page: Playwright 页面对象
        :return: 二维码图片的 Base64 字符串
        """
        pass

    @abstractmethod
    async def wait_for_login(self, page: Page, timeout: int = 120) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        等待用户在手机 App 上扫码并确认登录
        :param page: Playwright 页面对象
        :param timeout: 等待超时时间 (秒)
        :return: (是否成功登录, 创作者信息字典)
        """
        pass

    @abstractmethod
    async def publish_video(
        self, 
        page: Page, 
        subtask_data: Dict[str, Any],
        on_progress: Optional[Callable[[str, str], Any]] = None,
        on_verify_required: Optional[Callable[[Dict[str, Any]], Any]] = None
    ) -> Dict[str, Any]:
        """
        执行自动化发布视频核心流程
        :param page: Playwright 页面对象
        :param subtask_data: 子任务详情 (包含视频路径、标题、描述、标签、定时信息等)
        :param on_progress: 进度实时回调函数 (log_level, log_message)
        :param on_verify_required: 二次安全验证回调函数 (接收验证信息字典，返回用户交互异步通道队列)
        :return: 执行结果字典 {'success': bool, 'work_id': ..., 'work_url': ..., 'error': ...}
        """
        pass

    async def fetch_metrics(self, page: Page) -> Dict[str, Any]:
        """
        获取该账号的最新主页大盘与作品列表指标
        :param page: Playwright 页面对象
        :return: 包含 account 与 works 列表的字典
        格式:
        {
            "account": {
                "followers_count": int,
                "likes_count": int,
                "total_views_count": int,
                "works_count": int
            },
            "works": [
                {
                    "work_id": str,
                    "title": str,
                    "view_count": int,
                    "like_count": int,
                    "comment_count": int,
                    "share_count": int,
                    "collect_count": int,
                    "work_url": str,
                    "publish_time": str
                }
            ]
        }
        """
        return {"account": {}, "works": []}

