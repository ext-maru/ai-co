import enum
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UploadStatus(str, enum.Enum):
    """アップロードステータス（3段階シンプル版）"""

    NOT_UPLOADED = "not_uploaded"  # アップしてない
    NEEDS_REUPLOAD = "needs_reupload"  # アップしたがNG出て再度アップ必要
    APPROVED = "approved"  # アップしてOKでた


class ContractUpload(Base):
    """契約書類アップロード"""

    __tablename__ = "contract_uploads"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    contract_type = Column(String, nullable=False)  # individual or corporate
    status = Column(SQLEnum(UploadStatus), default=UploadStatus.NOT_UPLOADED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(String)
    review_notes = Column(String)
    meta_data = Column(JSON)  # 追加情報を格納

    # リレーション
    documents = relationship("Upload", back_populates="contract_upload")


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(String, primary_key=True)
    contract_upload_id = Column(String, ForeignKey("contract_uploads.id"))
    document_type = Column(String, nullable=False)  # DocumentTypeのvalue
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    status = Column(SQLEnum(UploadStatus), default=UploadStatus.NOT_UPLOADED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    storage_path = Column(String)
    thumbnail_path = Column(String)
    approval_notes = Column(String)
    approved_by = Column(String)
    approved_at = Column(DateTime)
    expiry_date = Column(DateTime)  # 書類の有効期限

    # リレーション
    contract_upload = relationship("ContractUpload", back_populates="documents")
