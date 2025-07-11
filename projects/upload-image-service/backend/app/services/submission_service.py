"""提出セッション管理サービス"""

import uuid
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, UploadFile
from app.models.submission import (
    SubmissionSession, SubmissionUpload, CustomDocumentTemplate,
    SubmissionType, SessionStatus
)
from app.schemas.submission import (
    SubmissionSessionCreate, SubmissionSessionResponse, SubmissionSessionDetail,
    SubmissionUploadCreate, SubmissionUploadResponse,
    SubmissionStatistics, SessionStatusUpdate, FileReviewUpdate,
    CustomDocumentTemplateCreate, CustomDocumentTemplateResponse
)


class SubmissionService:
    """提出セッション管理サービス"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_session(
        self, 
        admin_id: str, 
        admin_name: str, 
        data: SubmissionSessionCreate
    ) -> SubmissionSessionResponse:
        """新規提出セッション作成"""
        
        session_id = str(uuid.uuid4())
        url_key = SubmissionSession.generate_url_key()
        
        # URL重複チェック
        while self.db.query(SubmissionSession).filter(
            SubmissionSession.session_url_key == url_key
        ).first():
            url_key = SubmissionSession.generate_url_key()
        
        session = SubmissionSession(
            id=session_id,
            session_url_key=url_key,
            creator_admin_id=admin_id,
            creator_admin_name=admin_name,
            submitter_name=data.submitter_name,
            submitter_email=data.submitter_email,
            submitter_phone=data.submitter_phone,
            submitter_organization=data.submitter_organization,
            submission_type=data.submission_type,
            title=data.title,
            description=data.description,
            admin_notes=data.admin_notes,
            due_date=data.due_date,
            max_file_size_mb=str(data.max_file_size_mb),
            allowed_file_types=data.allowed_file_types,
            access_password=data.access_password,
            access_ip_whitelist=data.access_ip_whitelist
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return self._to_response(session)
    
    async def get_session_by_url_key(self, url_key: str) -> Optional[SubmissionSessionDetail]:
        """URLキーでセッション取得（提出者用）"""
        
        session = self.db.query(SubmissionSession).filter(
            and_(
                SubmissionSession.session_url_key == url_key,
                SubmissionSession.is_active == True
            )
        ).first()
        
        if not session:
            return None
        
        # 初回アクセス記録
        if not session.first_access_at:
            session.first_access_at = datetime.utcnow()
            if session.status == SessionStatus.CREATED:
                session.status = SessionStatus.IN_PROGRESS
            self.db.commit()
        
        return self._to_detail(session)
    
    async def get_session_detail(self, session_id: str, admin_id: str) -> SubmissionSessionDetail:
        """セッション詳細取得（管理者用）"""
        
        session = self.db.query(SubmissionSession).filter(
            and_(
                SubmissionSession.id == session_id,
                SubmissionSession.creator_admin_id == admin_id
            )
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        return self._to_detail(session)
    
    async def list_sessions(
        self, 
        admin_id: str, 
        status: Optional[SessionStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """セッション一覧取得"""
        
        query = self.db.query(SubmissionSession).filter(
            SubmissionSession.creator_admin_id == admin_id
        )
        
        if status:
            query = query.filter(SubmissionSession.status == status)
        
        total = query.count()
        sessions = query.order_by(desc(SubmissionSession.created_at)).offset(skip).limit(limit).all()
        
        # ステータス別カウント
        status_counts = {}
        for status_value in SessionStatus:
            count = self.db.query(SubmissionSession).filter(
                and_(
                    SubmissionSession.creator_admin_id == admin_id,
                    SubmissionSession.status == status_value
                )
            ).count()
            status_counts[status_value.value] = count
        
        return {
            "items": [self._to_response(session) for session in sessions],
            "total": total,
            "skip": skip,
            "limit": limit,
            "status_counts": status_counts
        }
    
    async def upload_file(
        self, 
        session_url_key: str, 
        file: UploadFile,
        upload_data: SubmissionUploadCreate
    ) -> SubmissionUploadResponse:
        """ファイルアップロード（提出者用）"""
        
        session = self.db.query(SubmissionSession).filter(
            and_(
                SubmissionSession.session_url_key == session_url_key,
                SubmissionSession.is_active == True
            )
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        if session.is_expired:
            raise HTTPException(status_code=400, detail="提出期限が過ぎています")
        
        # ファイルサイズチェック
        file_size = len(await file.read())
        await file.seek(0)  # ファイルポインタをリセット
        
        max_size = int(session.max_file_size_mb) * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=400, 
                detail=f"ファイルサイズが上限（{session.max_file_size_mb}MB）を超えています"
            )
        
        # ファイル形式チェック
        allowed_types = session.allowed_file_types.split(',')
        file_ext = '.' + file.filename.split('.')[-1].lower()
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"対応していないファイル形式です（対応形式: {session.allowed_file_types}）"
            )
        
        upload_id = str(uuid.uuid4())
        storage_path = f"uploads/sessions/{session.id}/{upload_id}_{file.filename}"
        
        # TODO: 実際のファイル保存処理を実装
        # await save_file_to_storage(file, storage_path)
        
        upload = SubmissionUpload(
            id=upload_id,
            session_id=session.id,
            filename=f"{upload_id}_{file.filename}",
            original_filename=file.filename,
            content_type=file.content_type,
            file_size=str(file_size),
            storage_path=storage_path,
            document_category=upload_data.document_category,
            submitter_comment=upload_data.submitter_comment
        )
        
        self.db.add(upload)
        
        # セッションステータス更新
        if session.status == SessionStatus.CREATED:
            session.status = SessionStatus.IN_PROGRESS
        
        self.db.commit()
        self.db.refresh(upload)
        
        return SubmissionUploadResponse.from_orm(upload)
    
    async def update_session_status(
        self, 
        session_id: str, 
        admin_id: str,
        status_update: SessionStatusUpdate
    ) -> SubmissionSessionResponse:
        """セッションステータス更新"""
        
        session = self.db.query(SubmissionSession).filter(
            and_(
                SubmissionSession.id == session_id,
                SubmissionSession.creator_admin_id == admin_id
            )
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        session.status = status_update.status
        if status_update.admin_notes:
            session.admin_notes = status_update.admin_notes
        
        if status_update.status == SessionStatus.COMPLETED:
            session.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(session)
        
        return self._to_response(session)
    
    async def review_file(
        self, 
        upload_id: str, 
        admin_id: str,
        review_data: FileReviewUpdate
    ) -> SubmissionUploadResponse:
        """ファイルレビュー"""
        
        upload = self.db.query(SubmissionUpload).join(SubmissionSession).filter(
            and_(
                SubmissionUpload.id == upload_id,
                SubmissionSession.creator_admin_id == admin_id
            )
        ).first()
        
        if not upload:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
        upload.admin_status = review_data.admin_status
        upload.admin_comment = review_data.admin_comment
        upload.reviewed_by = admin_id
        upload.reviewed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(upload)
        
        return SubmissionUploadResponse.from_orm(upload)
    
    async def get_statistics(self, admin_id: str) -> SubmissionStatistics:
        """統計情報取得"""
        
        # 基本統計
        total_sessions = self.db.query(SubmissionSession).filter(
            SubmissionSession.creator_admin_id == admin_id
        ).count()
        
        active_sessions = self.db.query(SubmissionSession).filter(
            and_(
                SubmissionSession.creator_admin_id == admin_id,
                SubmissionSession.status.in_([SessionStatus.CREATED, SessionStatus.IN_PROGRESS])
            )
        ).count()
        
        completed_sessions = self.db.query(SubmissionSession).filter(
            and_(
                SubmissionSession.creator_admin_id == admin_id,
                SubmissionSession.status == SessionStatus.COMPLETED
            )
        ).count()
        
        # ファイル統計
        upload_stats = self.db.query(
            func.count(SubmissionUpload.id).label('total_uploads'),
            func.sum(func.cast(SubmissionUpload.file_size, func.Integer)).label('total_size')
        ).join(SubmissionSession).filter(
            SubmissionSession.creator_admin_id == admin_id
        ).first()
        
        return SubmissionStatistics(
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            completed_sessions=completed_sessions,
            total_uploads=upload_stats.total_uploads or 0,
            total_file_size_gb=round((upload_stats.total_size or 0) / (1024**3), 2)
        )
    
    def _to_response(self, session: SubmissionSession) -> SubmissionSessionResponse:
        """ORMオブジェクトをレスポンススキーマに変換"""
        return SubmissionSessionResponse(
            id=session.id,
            session_url_key=session.session_url_key,
            submission_url=session.submission_url,
            creator_admin_id=session.creator_admin_id,
            creator_admin_name=session.creator_admin_name,
            submitter_name=session.submitter_name,
            submitter_email=session.submitter_email,
            submitter_phone=session.submitter_phone,
            submitter_organization=session.submitter_organization,
            submission_type=session.submission_type,
            title=session.title,
            description=session.description,
            admin_notes=session.admin_notes,
            due_date=session.due_date,
            max_file_size_mb=session.max_file_size_mb,
            allowed_file_types=session.allowed_file_types,
            status=session.status,
            is_active=session.is_active,
            created_at=session.created_at,
            updated_at=session.updated_at,
            sent_at=session.sent_at,
            first_access_at=session.first_access_at,
            completed_at=session.completed_at,
            is_expired=session.is_expired,
            days_until_due=session.days_until_due,
            upload_count=len(session.uploads) if session.uploads else 0
        )
    
    def _to_detail(self, session: SubmissionSession) -> SubmissionSessionDetail:
        """詳細レスポンス変換"""
        response = self._to_response(session)
        
        return SubmissionSessionDetail(
            **response.dict(),
            uploads=[SubmissionUploadResponse.from_orm(upload) for upload in session.uploads or []],
            total_file_size=str(sum(int(upload.file_size) for upload in session.uploads or [])),
            completion_percentage=self._calculate_completion_percentage(session)
        )
    
    def _calculate_completion_percentage(self, session: SubmissionSession) -> float:
        """完了率計算"""
        if not session.uploads:
            return 0.0
        
        # 簡易計算：アップロードがあれば50%、承認済みファイルがあれば100%
        approved_count = len([
            upload for upload in session.uploads 
            if upload.admin_status == "approved"
        ])
        
        if approved_count > 0:
            return 100.0
        elif len(session.uploads) > 0:
            return 50.0
        else:
            return 0.0