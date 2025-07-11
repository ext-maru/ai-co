from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models import SubmissionSession, SubmissionStatus
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionListResponse,
    SessionUpdate,
    SubmissionStatusEnum
)

router = APIRouter()


@router.post("/sessions", response_model=dict)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """新しい提出セッションを作成"""
    # セッションID生成
    session_id = f"session_{str(uuid.uuid4())[:8]}"

    # データベースモデル作成
    db_session = SubmissionSession(
        id=session_id,
        submitter_name=session_data.submitter_name,
        submitter_email=session_data.submitter_email,
        submission_type=session_data.submission_type,
        description=session_data.description,
        status=SubmissionStatus.NOT_UPLOADED
    )

    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return {
        "session_id": session_id,
        "message": "セッションが作成されました",
        "url": f"/submission/{session_id}"
    }


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """特定のセッション情報を取得"""
    session = db.query(SubmissionSession).filter(
        SubmissionSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    # アップロードされたファイル情報を整形
    uploaded_files = []
    for file in session.uploaded_files:
        uploaded_files.append({
            "filename": file.filename,
            "size": file.file_size,
            "uploaded_at": file.uploaded_at.isoformat()
        })

    return SessionResponse(
        id=session.id,
        submitter_name=session.submitter_name,
        submitter_email=session.submitter_email,
        submission_type=session.submission_type,
        status=session.status,
        description=session.description,
        google_drive_folder_id=session.google_drive_folder_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        uploaded_files=uploaded_files
    )


@router.put("/sessions/{session_id}/status")
async def update_session_status(
    session_id: str,
    status_update: dict,
    db: Session = Depends(get_db)
):
    """セッションのステータスを更新"""
    session = db.query(SubmissionSession).filter(
        SubmissionSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    # ステータス更新
    new_status = status_update.get("status")
    if new_status:
        try:
            session.status = SubmissionStatus(new_status)
        except ValueError:
            raise HTTPException(status_code=400, detail="無効なステータス")

    session.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "ステータスが更新されました"}
