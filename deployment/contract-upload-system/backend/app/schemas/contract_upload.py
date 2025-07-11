from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from app.models.contract_type import ContractType
from app.models.contract_type import DocumentType
from app.models.upload import UploadStatus
from pydantic import BaseModel
from pydantic import Field


class DocumentUploadStatus(BaseModel):
    """個別書類のアップロード状況"""

    document_type: DocumentType
    display_name: str
    description: str
    required: bool
    uploaded: bool = False
    file_count: int = 0
    max_files: int = 1
    files: List[Dict[str, Any]] = []
    status: UploadStatus = UploadStatus.NOT_UPLOADED
    expiry_date: Optional[datetime] = None
    allowed_formats: List[str] = [".pdf", ".jpg", ".jpeg", ".png"]
    max_size_mb: int = 10


class ContractUploadCreate(BaseModel):
    """契約書類アップロード作成"""

    contract_type: ContractType
    metadata: Optional[Dict[str, Any]] = {}


class ContractUploadResponse(BaseModel):
    """契約書類アップロード応答"""

    id: str
    user_id: str
    contract_type: ContractType
    status: UploadStatus
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_orm(cls, obj):
        """ORMオブジェクトからスキーマオブジェクトを作成"""
        data = {
            'id': obj.id,
            'user_id': obj.user_id,
            'contract_type': obj.contract_type,
            'status': obj.status,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at,
            'submitted_at': obj.submitted_at,
            'reviewed_at': obj.reviewed_at,
            'reviewed_by': obj.reviewed_by,
            'review_notes': obj.review_notes,
            'metadata': obj.meta_data if hasattr(obj, 'meta_data') else {}
        }
        return cls(**data)

    class Config:
        from_attributes = True


class ContractUploadDetail(ContractUploadResponse):
    """契約書類アップロード詳細"""

    document_statuses: List[DocumentUploadStatus]
    completion_rate: float = Field(description="完了率（0-100）")
    missing_documents: List[str] = Field(description="不足書類リスト")
    expired_documents: List[str] = Field(description="期限切れ書類リスト")


class FileUploadRequest(BaseModel):
    """ファイルアップロードリクエスト"""

    contract_upload_id: str
    document_type: DocumentType


class FileUploadResponse(BaseModel):
    """ファイルアップロード応答"""

    id: str
    filename: str
    original_filename: str
    size: int
    content_type: str
    document_type: DocumentType
    status: UploadStatus
    created_at: datetime
    thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True


class ContractUploadListResponse(BaseModel):
    """契約書類アップロード一覧応答"""

    items: List[ContractUploadResponse]
    total: int
    skip: int
    limit: int


class DocumentValidationResult(BaseModel):
    """書類検証結果"""

    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class ContractReviewRequest(BaseModel):
    """契約書類レビューリクエスト"""

    action: str = Field(description="approve or reject")
    notes: Optional[str] = Field(description="レビューコメント")
    document_notes: Optional[Dict[str, str]] = Field(
        description="個別書類へのコメント", example={"resident_card": "有効期限が近いです"}
    )
