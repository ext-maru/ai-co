from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from pathlib import Path

from app.core.database import get_db
from app.core.config import settings
from app.models import SubmissionSession, UploadedFile
from app.schemas.file import FileResponse

router = APIRouter()


@router.post("/sessions/{session_id}/upload")
async def upload_files(
    session_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """ファイルをアップロード"""
    # セッション確認
    session = db.query(SubmissionSession).filter(
        SubmissionSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    # アップロードディレクトリ作成
    upload_dir = Path(settings.upload_dir) / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    uploaded_files = []

    for file in files:
        # ファイルサイズチェック
        content = await file.read()
        file_size = len(content)

        if file_size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"ファイルサイズが大きすぎます: {file.filename}"
            )

        # 拡張子チェック
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"許可されていないファイル形式です: {file.filename}"
            )

        # ファイル保存
        file_id = str(uuid.uuid4())
        file_path = upload_dir / f"{file_id}{file_ext}"

        with open(file_path, "wb") as f:
            f.write(content)

        # データベース登録
        db_file = UploadedFile(
            id=file_id,
            session_id=session_id,
            filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            mime_type=file.content_type
        )

        db.add(db_file)
        uploaded_files.append({
            "filename": file.filename,
            "size": file_size,
            "uploaded_at": db_file.uploaded_at.isoformat()
        })

    # セッションステータス更新
    from app.models import SubmissionStatus
    if session.status == SubmissionStatus.NOT_UPLOADED:
        session.status = SubmissionStatus.NEEDS_REUPLOAD

    db.commit()

    return {
        "message": "ファイルのアップロードが完了しました",
        "uploaded_files": uploaded_files
    }


@router.get("/sessions/{session_id}/files", response_model=List[FileResponse])
async def get_session_files(
    session_id: str,
    db: Session = Depends(get_db)
):
    """セッションのファイル一覧を取得"""
    files = db.query(UploadedFile).filter(
        UploadedFile.session_id == session_id
    ).all()

    return files
