"""提出セッション管理モデル"""

import enum
import secrets
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Text, Enum as SQLEnum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class SubmissionType(str, enum.Enum):
    """提出タイプ"""
    INDIVIDUAL = "individual"  # 個人契約者用
    CORPORATE = "corporate"    # 法人契約者用


class SessionStatus(str, enum.Enum):
    """セッション状態"""
    CREATED = "created"           # 作成済み・未送付
    SENT = "sent"                # 提出者に送付済み
    IN_PROGRESS = "in_progress"   # 提出中
    COMPLETED = "completed"       # 提出完了
    EXPIRED = "expired"           # 期限切れ
    CANCELLED = "cancelled"       # キャンセル


class SubmissionSession(Base):
    """提出セッション"""
    
    __tablename__ = "submission_sessions"
    
    id = Column(String, primary_key=True)
    session_url_key = Column(String, unique=True, nullable=False, index=True)  # 短縮URL用キー
    
    # 管理者情報
    creator_admin_id = Column(String, nullable=False)
    creator_admin_name = Column(String, nullable=False)
    
    # 提出者情報
    submitter_name = Column(String, nullable=False)
    submitter_email = Column(String)
    submitter_phone = Column(String)
    submitter_organization = Column(String)  # 所属組織
    
    # セッション設定
    submission_type = Column(SQLEnum(SubmissionType), nullable=False)
    title = Column(String, nullable=False)  # セッションタイトル
    description = Column(Text)  # 提出依頼の説明
    admin_notes = Column(Text)  # 管理者用メモ
    
    # 期限・制限
    due_date = Column(DateTime)
    max_file_size_mb = Column(String, default="50")
    allowed_file_types = Column(String, default=".pdf,.jpg,.jpeg,.png,.doc,.docx")
    
    # 状態管理
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.CREATED)
    is_active = Column(Boolean, default=True)
    
    # アクセス制限
    access_ip_whitelist = Column(String)  # カンマ区切りIP
    access_password = Column(String)      # アクセスパスワード（オプション）
    
    # タイムスタンプ
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_at = Column(DateTime)        # 提出者に送付した日時
    first_access_at = Column(DateTime)  # 提出者が初回アクセスした日時
    completed_at = Column(DateTime)   # 提出完了日時
    
    # リレーション
    uploads = relationship("SubmissionUpload", back_populates="session")
    
    @classmethod
    def generate_url_key(cls, length: int = 12) -> str:
        """セッションURL用の短縮キーを生成"""
        return secrets.token_urlsafe(length)
    
    @property
    def submission_url(self) -> str:
        """提出用URL"""
        return f"/submit/{self.session_url_key}"
    
    @property
    def is_expired(self) -> bool:
        """期限切れチェック"""
        if not self.due_date:
            return False
        return datetime.utcnow() > self.due_date
    
    @property
    def days_until_due(self) -> int:
        """期限までの日数"""
        if not self.due_date:
            return 999
        delta = self.due_date - datetime.utcnow()
        return max(0, delta.days)


class SubmissionUpload(Base):
    """提出セッション内のファイルアップロード"""
    
    __tablename__ = "submission_uploads"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("submission_sessions.id"), nullable=False)
    
    # ファイル情報
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    file_size = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    thumbnail_path = Column(String)
    
    # 分類・説明
    document_category = Column(String)  # 書類カテゴリ（住民票、契約書等）
    submitter_comment = Column(Text)    # 提出者コメント
    
    # 管理者レビュー
    admin_status = Column(String, default="pending")  # pending/approved/rejected
    admin_comment = Column(Text)
    reviewed_by = Column(String)
    reviewed_at = Column(DateTime)
    
    # タイムスタンプ
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # リレーション
    session = relationship("SubmissionSession", back_populates="uploads")


class CustomDocumentTemplate(Base):
    """カスタム書類テンプレート（管理者が自由に作成）"""
    
    __tablename__ = "custom_document_templates"
    
    id = Column(String, primary_key=True)
    created_by = Column(String, nullable=False)  # 作成者管理者ID
    
    template_name = Column(String, nullable=False)
    description = Column(Text)
    
    # 必要書類定義（JSON形式）
    required_documents = Column(Text)  # JSON: [{"name": "住民票", "required": true, "max_files": 1}]
    
    # 使用統計
    usage_count = Column(String, default="0")
    last_used_at = Column(DateTime)
    
    # タイムスタンプ
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)