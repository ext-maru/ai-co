"""提出セッション関連スキーマ"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from app.models.submission import SubmissionType, SessionStatus


class SubmissionSessionCreate(BaseModel):
    """提出セッション作成"""
    
    submitter_name: str = Field(..., min_length=1, max_length=100)
    submitter_email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    submitter_phone: Optional[str] = None
    submitter_organization: Optional[str] = None
    
    submission_type: SubmissionType
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    admin_notes: Optional[str] = None
    
    due_date: Optional[datetime] = None
    max_file_size_mb: int = Field(default=50, ge=1, le=500)
    allowed_file_types: str = Field(default=".pdf,.jpg,.jpeg,.png,.doc,.docx")
    
    access_password: Optional[str] = None
    access_ip_whitelist: Optional[str] = None
    
    @validator('due_date')
    def validate_due_date(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('期限は未来の日時を指定してください')
        return v


class SubmissionSessionResponse(BaseModel):
    """提出セッション応答"""
    
    id: str
    session_url_key: str
    submission_url: str
    
    creator_admin_id: str
    creator_admin_name: str
    
    submitter_name: str
    submitter_email: Optional[str] = None
    submitter_phone: Optional[str] = None
    submitter_organization: Optional[str] = None
    
    submission_type: SubmissionType
    title: str
    description: Optional[str] = None
    admin_notes: Optional[str] = None
    
    due_date: Optional[datetime] = None
    max_file_size_mb: str
    allowed_file_types: str
    
    status: SessionStatus
    is_active: bool
    
    created_at: datetime
    updated_at: datetime
    sent_at: Optional[datetime] = None
    first_access_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 計算プロパティ
    is_expired: bool = False
    days_until_due: int = 999
    upload_count: int = 0
    
    class Config:
        from_attributes = True


class SubmissionUploadCreate(BaseModel):
    """ファイルアップロード作成"""
    
    document_category: Optional[str] = None
    submitter_comment: Optional[str] = None


class SubmissionUploadResponse(BaseModel):
    """ファイルアップロード応答"""
    
    id: str
    session_id: str
    
    filename: str
    original_filename: str
    content_type: str
    file_size: str
    thumbnail_path: Optional[str] = None
    
    document_category: Optional[str] = None
    submitter_comment: Optional[str] = None
    
    admin_status: str
    admin_comment: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class SubmissionSessionDetail(SubmissionSessionResponse):
    """提出セッション詳細（ファイル・メッセージ含む）"""
    
    uploads: List[SubmissionUploadResponse] = []
    
    # 統計情報
    total_file_size: str = "0"
    completion_percentage: float = 0.0


class SubmissionSessionList(BaseModel):
    """提出セッション一覧"""
    
    items: List[SubmissionSessionResponse]
    total: int
    skip: int
    limit: int
    
    # 統計情報
    status_counts: Dict[str, int] = {}
    total_file_size: str = "0"


class SessionStatusUpdate(BaseModel):
    """セッションステータス更新"""
    
    status: SessionStatus
    admin_notes: Optional[str] = None


class FileReviewUpdate(BaseModel):
    """ファイルレビュー更新"""
    
    admin_status: str = Field(..., regex='^(pending|approved|rejected)$')
    admin_comment: Optional[str] = None


class CustomDocumentTemplateCreate(BaseModel):
    """カスタム書類テンプレート作成"""
    
    template_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    required_documents: List[Dict[str, Any]] = Field(
        ..., 
        example=[
            {"name": "住民票", "required": True, "max_files": 1, "description": "発行から3か月以内"},
            {"name": "契約書", "required": True, "max_files": 1, "description": "署名済みのもの"}
        ]
    )


class CustomDocumentTemplateResponse(BaseModel):
    """カスタム書類テンプレート応答"""
    
    id: str
    created_by: str
    
    template_name: str
    description: Optional[str] = None
    required_documents: str  # JSON文字列
    
    usage_count: str
    last_used_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SubmissionStatistics(BaseModel):
    """提出統計情報"""
    
    total_sessions: int = 0
    active_sessions: int = 0
    completed_sessions: int = 0
    expired_sessions: int = 0
    
    total_uploads: int = 0
    pending_reviews: int = 0
    approved_files: int = 0
    rejected_files: int = 0
    
    avg_completion_time_hours: float = 0.0
    total_file_size_gb: float = 0.0
    
    # 月別統計
    monthly_stats: List[Dict[str, Any]] = []
    
    # 提出タイプ別統計
    type_stats: Dict[str, int] = {}


class SubmissionNotification(BaseModel):
    """提出通知設定"""
    
    session_id: str
    notification_type: str = Field(..., regex='^(email|sms|slack)$')
    recipient: str
    message_template: Optional[str] = None
    send_at: Optional[datetime] = None  # 予約送信
    is_recurring: bool = False  # 定期送信（催促）
    recurring_interval_hours: Optional[int] = None