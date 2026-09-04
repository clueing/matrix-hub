from typing import Dict, Optional
from app.adapters.base import BasePublisherAdapter
from app.adapters.xiaohongshu import XiaohongshuAdapter
from app.adapters.douyin import DouyinAdapter
from app.adapters.kuaishou import KuaishouAdapter
from app.adapters.channels import ChannelsAdapter

# 平台适配器单例注册注册表
_adapters: Dict[str, BasePublisherAdapter] = {
    "xiaohongshu": XiaohongshuAdapter(),
    "douyin": DouyinAdapter(),
    "kuaishou": KuaishouAdapter(),
    "channels": ChannelsAdapter()
}

def get_adapter(platform: str) -> Optional[BasePublisherAdapter]:
    """
    根据平台标识获取对应自动化适配器实例
    :param platform: 'xiaohongshu', 'douyin', 'kuaishou', 'channels'
    """
    return _adapters.get(platform.lower())

def list_supported_platforms():
    """获取系统已支持及预留的全部平台列表"""
    return [
        {"code": "xiaohongshu", "name": "小红书", "status": "active"},
        {"code": "douyin", "name": "抖音", "status": "active"},
        {"code": "kuaishou", "name": "快手", "status": "beta"},
        {"code": "channels", "name": "微信视频号", "status": "beta"}
    ]

__all__ = ["BasePublisherAdapter", "get_adapter", "list_supported_platforms"]
