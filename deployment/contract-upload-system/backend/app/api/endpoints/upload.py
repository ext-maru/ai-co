from typing import List

from app.core.auth import get_current_user
from app.schemas.upload import UploadResponse
from app.schemas.upload import UploadStatus
from app.services.upload_service import UploadService
from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile

router = APIRouter()
upload_service = UploadService()


@router.post("/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...), user=Depends(get_current_user)):
    """ファイルアップロード"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="画像ファイルのみ対応しています")

    result = await upload_service.process_upload(
        await file.read(),
        file.filename,
        file.content_type,
        user_id=user.id
    )

    return result


@router.post("/multiple", response_model=List[UploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    user=Depends(get_current_user)
):
    """複数ファイルアップロード"""
    results = []
    for file in files:
        if file.content_type.startswith("image/"):
            result = await upload_service.process_upload(
                await file.read(), file.filename, file.content_type, user_id=user.id
            )
            results.append(result)

    return results


@router.get("/status/{file_id}", response_model=UploadStatus)
async def get_upload_status(file_id: str):
    """アップロードステータス取得"""
    status = await upload_service.get_upload_status(file_id)
    if not status:
        raise HTTPException(status_code=404, detail="File not found")
    return status


@router.get("/list", response_model=List[UploadStatus])
async def list_uploads(skip: int = 0, limit: int = 100, user=Depends(get_current_user)):
    """アップロード一覧取得"""
    return await upload_service.list_user_uploads(user.id, skip, limit)
