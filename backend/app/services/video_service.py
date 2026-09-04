import os
from pathlib import Path
from typing import List, Dict, Any, Optional

class VideoService:
    """
    原始视频素材管理服务
    负责本地视频路径校验、目录扫描及素材有效性校验
    """

    SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".flv", ".avi", ".webm"}

    def scan_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """
        扫描指定本地磁盘文件夹，检索所有支持格式的视频素材文件
        """
        p = Path(folder_path)
        if not p.exists() or not p.is_dir():
            raise ValueError(f"指定的目录不存在或不是文件夹: {folder_path}")

        video_files = []
        for file in p.rglob("*"):
            if file.is_file() and file.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                stat = file.stat()
                video_files.append({
                    "name": file.name,
                    "stem": file.stem,  # 不含后缀的文件名 (可作为默认标题)
                    "path": str(file.resolve()),
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified_time": stat.st_mtime,
                    "extension": file.suffix.lower()
                })
        
        # 按修改时间倒序排列
        video_files.sort(key=lambda x: x["modified_time"], reverse=True)
        return video_files

    def verify_video(self, video_path: str) -> Dict[str, Any]:
        """
        校验单个视频文件的存在性与可读性
        """
        p = Path(video_path)
        if not p.exists() or not p.is_file():
            return {"valid": False, "error": "视频文件不存在"}

        if p.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return {"valid": False, "error": f"暂不支持的文件格式: {p.suffix}"}

        size = p.stat().st_size
        if size == 0:
            return {"valid": False, "error": "视频文件大小为0字节"}

        return {
            "valid": True,
            "name": p.name,
            "stem": p.stem,
            "size": size,
            "size_mb": round(size / (1024 * 1024), 2),
            "path": str(p.resolve())
        }

video_service = VideoService()
