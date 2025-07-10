from sqlalchemy import Column, String, DateTime, Integer, Boolean, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class UploadStatus(str, enum.Enum):
    """アップロードステータス"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"  # 期限切れ

class ContractUpload(Base):
    """契約書類アップロード"""
    __tablename__ = "contract_uploads"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    contract_type = Column(String, nullable=False)  # individual or corporate
    status = Column(SQLEnum(UploadStatus), default=UploadStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(String)
    review_notes = Column(String)
    metadata = Column(JSON)  # 追加情報を格納
    
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
    status = Column(SQLEnum(UploadStatus), default=UploadStatus.PENDING)
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
