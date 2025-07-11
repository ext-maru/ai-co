from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models import SubmissionSession
from app.schemas.session import SessionResponse, SessionListResponse

router = APIRouter()


@router.get("/admin/sessions", response_model=SessionListResponse)
async def get_all_sessions(
    db: Session = Depends(get_db)
):
    """管理者用: 全セッション一覧を取得"""
    sessions = db.query(SubmissionSession).order_by(
        SubmissionSession.created_at.desc()
    ).all()

    session_list = []
    for session in sessions:
        # アップロードされたファイル情報を整形
        uploaded_files = []
        for file in session.uploaded_files:
            uploaded_files.append({
                "filename": file.filename,
                "size": file.file_size,
                "uploaded_at": file.uploaded_at.isoformat()
            })

        session_list.append(SessionResponse(
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
        ))

    return SessionListResponse(sessions=session_list)
