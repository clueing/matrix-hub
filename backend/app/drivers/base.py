from abc import ABC, abstractmethod
from typing import Tuple, Any

class BaseDriver(ABC):
    """
    浏览器驱动抽象基类
    定义启动、环境上下文创建与关闭的标准生命周期接口
    """

    @abstractmethod
    async def get_context_and_page(
        self, 
        account_id: str, 
        headless: bool = True,
        proxy_url: str = None
    ) -> Tuple[Any, Any]:
        """
        获取指定账号的隔离浏览器上下文及初始页面
        :param account_id: 账号ID（用于指定持久化存储路径）
        :param headless: 是否为无头静默模式（人工辅助时设为 False）
        :param proxy_url: 独立代理地址 (可选)
        :return: (BrowserContext, Page)
        """
        pass

    @abstractmethod
    async def close_context(self, context: Any, page: Any = None):
        """
        安全释放和关闭浏览器上下文与页面资源
        """
        pass
