"""提出セッション管理API"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.submission import SessionStatus
from app.schemas.submission import (
    SubmissionSessionCreate, SubmissionSessionResponse, SubmissionSessionDetail,
    SubmissionUploadCreate, SubmissionUploadResponse,
    SubmissionStatistics, SessionStatusUpdate, FileReviewUpdate
)
from app.services.submission_service import SubmissionService

router = APIRouter()


@router.post("/sessions", response_model=SubmissionSessionResponse)
async def create_submission_session(
    data: SubmissionSessionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """新規提出セッション作成（管理者用）"""
    service = SubmissionService(db)
    return await service.create_session(
        admin_id=current_user["id"],
        admin_name=current_user.get("name", "管理者"),
        data=data
    )


@router.get("/sessions", response_model=dict)
async def list_submission_sessions(
    status: Optional[SessionStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提出セッション一覧取得（管理者用）"""
    service = SubmissionService(db)
    return await service.list_sessions(
        admin_id=current_user["id"],
        status=status,
        skip=skip,
        limit=limit
    )


@router.get("/sessions/{session_id}", response_model=SubmissionSessionDetail)
async def get_submission_session_detail(
    session_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提出セッション詳細取得（管理者用）"""
    service = SubmissionService(db)
    return await service.get_session_detail(session_id, current_user["id"])


@router.patch("/sessions/{session_id}/status", response_model=SubmissionSessionResponse)
async def update_session_status(
    session_id: str,
    status_update: SessionStatusUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """セッションステータス更新（管理者用）"""
    service = SubmissionService(db)
    return await service.update_session_status(
        session_id=session_id,
        admin_id=current_user["id"],
        status_update=status_update
    )


@router.patch("/uploads/{upload_id}/review", response_model=SubmissionUploadResponse)
async def review_upload(
    upload_id: str,
    review_data: FileReviewUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """アップロードファイルレビュー（管理者用）"""
    service = SubmissionService(db)
    return await service.review_file(
        upload_id=upload_id,
        admin_id=current_user["id"],
        review_data=review_data
    )


@router.get("/statistics", response_model=SubmissionStatistics)
async def get_submission_statistics(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提出統計情報取得（管理者用）"""
    service = SubmissionService(db)
    return await service.get_statistics(current_user["id"])


# === 提出者用エンドポイント ===

@router.get("/submit/{url_key}", response_model=SubmissionSessionDetail)
async def get_submission_page(
    url_key: str,
    db: Session = Depends(get_db)
):
    """提出ページ取得（提出者用・認証不要）"""
    service = SubmissionService(db)
    session = await service.get_session_by_url_key(url_key)
    
    if not session:
        raise HTTPException(status_code=404, detail="指定されたURLは無効です")
    
    return session


@router.post("/submit/{url_key}/upload", response_model=SubmissionUploadResponse)
async def submit_file(
    url_key: str,
    file: UploadFile = File(...),
    document_category: Optional[str] = Form(None),
    submitter_comment: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """ファイル提出（提出者用・認証不要）"""
    service = SubmissionService(db)
    
    upload_data = SubmissionUploadCreate(
        document_category=document_category,
        submitter_comment=submitter_comment
    )
    
    return await service.upload_file(
        session_url_key=url_key,
        file=file,
        upload_data=upload_data
    )


# === 短縮URL機能 ===

@router.get("/s/{url_key}")
async def redirect_to_submission(
    url_key: str,
    db: Session = Depends(get_db)
):
    """短縮URL経由でのリダイレクト"""
    service = SubmissionService(db)
    
    session = await service.get_session_by_url_key(url_key)
    if not session:
        raise HTTPException(status_code=404, detail="指定されたURLは無効です")
    
    # フロントエンドの提出ページにリダイレクト
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/submit/{url_key}", status_code=302)


# === QRコード生成 ===

@router.get("/sessions/{session_id}/qr")
async def generate_qr_code(
    session_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """セッション用QRコード生成（管理者用）"""
    service = SubmissionService(db)
    session_detail = await service.get_session_detail(session_id, current_user["id"])
    
    import qrcode
    from io import BytesIO
    import base64
    
    # QRコード生成
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"https://yourdomain.com/submit/{session_detail.session_url_key}")
    qr.make(fit=True)
    
    # 画像生成
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Base64エンコード
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        "session_id": session_id,
        "submission_url": f"/submit/{session_detail.session_url_key}",
        "qr_code_base64": qr_base64,
        "qr_code_data_url": f"data:image/png;base64,{qr_base64}"
    }