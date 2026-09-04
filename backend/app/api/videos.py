from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.video_service import video_service

router = APIRouter(prefix="/videos", tags=["视频素材管理"])

class ScanFolderRequest(BaseModel):
    folder_path: str

class VerifyVideoRequest(BaseModel):
    video_path: str

@router.post("/scan-folder", summary="扫描本地文件夹获取视频列表")
async def scan_folder(payload: ScanFolderRequest):
    """递归检索用户本地指定文件夹中的所有 MP4/MOV 等常见格式视频"""
    try:
        videos = video_service.scan_folder(payload.folder_path)
        return {"code": 0, "data": videos}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify", summary="校验单个视频文件可用性")
async def verify_video(payload: VerifyVideoRequest):
    """检查视频路径是否存在、大小是否正常"""
    res = video_service.verify_video(payload.video_path)
    if not res.get("valid"):
        raise HTTPException(status_code=400, detail=res.get("error", "视频文件无效"))
    return {"code": 0, "data": res}
