import os
import shutil
import asyncio
import subprocess
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.core.config import settings
from app.services.video_service import video_service

router = APIRouter(prefix="/videos", tags=["视频素材管理"])

class ScanFolderRequest(BaseModel):
    folder_path: str

class VerifyVideoRequest(BaseModel):
    video_path: str

def _pick_file() -> Optional[str]:
    """在宿主机桌面唤起系统原生文件选择窗口"""
    # 优先方案：Tkinter 标准库原生文件对话框
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        filetypes = [
            ("视频素材 (*.mp4, *.mov, *.flv, *.mkv)", "*.mp4;*.mov;*.flv;*.mkv;*.avi;*.wmv;*.webm"),
            ("所有文件 (*.*)", "*.*")
        ]
        file_path = filedialog.askopenfilename(
            title="请选择要分发的视频文件",
            filetypes=filetypes
        )
        root.destroy()
        if file_path:
            return os.path.normpath(file_path)
    except Exception:
        pass

    # 备用方案：通过 PowerShell 调用 System.Windows.Forms.OpenFileDialog
    try:
        ps_cmd = (
            'Add-Type -AssemblyName System.Windows.Forms; '
            '$f = New-Object System.Windows.Forms.OpenFileDialog; '
            '$f.Filter = "视频素材 (*.mp4;*.mov;*.flv;*.mkv;*.avi)|*.mp4;*.mov;*.flv;*.mkv;*.avi|所有文件 (*.*)|*.*"; '
            '$f.Title = "请选择要分发的视频文件"; '
            'if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $f.FileName }'
        )
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=180
        )
        out = res.stdout.strip()
        if out:
            return os.path.normpath(out)
    except Exception:
        pass

    return None

def _pick_folder() -> Optional[str]:
    """在宿主机桌面唤起系统原生文件夹选择窗口"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder_path = filedialog.askdirectory(title="请选择包含视频素材的本地文件夹")
        root.destroy()
        if folder_path:
            return os.path.normpath(folder_path)
    except Exception:
        pass

    try:
        ps_cmd = (
            'Add-Type -AssemblyName System.Windows.Forms; '
            '$f = New-Object System.Windows.Forms.FolderBrowserDialog; '
            '$f.Description = "请选择包含视频素材的本地文件夹"; '
            'if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $f.SelectedPath }'
        )
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=180
        )
        out = res.stdout.strip()
        if out:
            return os.path.normpath(out)
    except Exception:
        pass

    return None

@router.post("/pick-file", summary="调起本地系统原生文件选择窗口")
async def pick_file_dialog():
    """在用户桌面弹出系统原生文件选择对话框，直接获取视频真实本地绝对路径"""
    try:
        file_path = await asyncio.to_thread(_pick_file)
        if not file_path:
            return {"code": 0, "data": None, "message": "用户取消了选择"}
            
        verify_res = video_service.verify_video(file_path)
        return {
            "code": 0,
            "data": {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "size_mb": verify_res.get("size_mb", 0),
                "valid": verify_res.get("valid", False)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调起系统文件选择框失败: {str(e)}")

@router.post("/pick-folder", summary="调起本地系统原生文件夹选择窗口")
async def pick_folder_dialog():
    """在用户桌面弹出系统原生文件夹选择对话框，直接获取文件夹绝对路径并自动扫描"""
    try:
        folder_path = await asyncio.to_thread(_pick_folder)
        if not folder_path:
            return {"code": 0, "data": None, "message": "用户取消了选择"}
            
        videos = video_service.scan_folder(folder_path)
        return {
            "code": 0,
            "data": {
                "folder_path": folder_path,
                "videos": videos
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调起系统文件夹选择框失败: {str(e)}")

@router.post("/upload", summary="上传视频素材文件至本地缓存库")
async def upload_video(file: UploadFile = File(...)):
    """支持前端直接拖拽或浏览器文件选择上传，保存到本地 uploads 目录并返回绝对路径"""
    try:
        upload_dir = settings.DATA_DIR / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        if file_path.exists():
            import time
            stem = Path(file.filename).stem
            suffix = Path(file.filename).suffix
            file_path = upload_dir / f"{stem}_{int(time.time())}{suffix}"
            
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_size = file_path.stat().st_size
        size_mb = round(file_size / (1024 * 1024), 2)
        return {
            "code": 0,
            "data": {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "size_mb": size_mb,
                "valid": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传视频文件失败: {str(e)}")

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
