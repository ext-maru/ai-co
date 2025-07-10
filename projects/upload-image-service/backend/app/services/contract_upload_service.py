import os
import uuid
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import List
from typing import Optional

from app.core.config import settings
from app.services.google_drive_service import create_user_contract_folder
from app.models.contract_type import ContractType
from app.models.contract_type import DOCUMENT_REQUIREMENTS
from app.models.contract_type import DocumentType
from app.models.upload import ContractUpload
from app.models.upload import Upload
from app.models.upload import UploadStatus
from app.schemas.contract_upload import ContractUploadCreate
from app.schemas.contract_upload import ContractUploadDetail
from app.schemas.contract_upload import ContractUploadResponse
from app.schemas.contract_upload import DocumentUploadStatus
from app.schemas.contract_upload import DocumentValidationResult
from app.schemas.contract_upload import FileUploadResponse
from sqlalchemy.orm import Session


class ContractUploadService:
    """契約書類アップロードサービス"""

    def __init__(self, db: Session):
        self.db = db

    async def create_contract_upload(self, user_id: str, user_name: str, data: ContractUploadCreate) -> ContractUploadResponse:
        """契約書類アップロードセッション作成（Google Driveフォルダ自動作成）"""
        contract_upload_id = str(uuid.uuid4())
        
        # Google Driveフォルダ自動作成
        try:
            drive_info = create_user_contract_folder(contract_upload_id, user_name)
            
            # メタデータにGoogle Drive情報を追加
            metadata = data.metadata or {}
            metadata.update({
                'google_drive_folder_id': drive_info['folder_id'],
                'google_drive_folder_url': drive_info['folder_url'],
                'google_drive_documents_folder_id': drive_info['documents_folder_id']
            })
            
        except Exception as e:
            # Google Drive連携エラーでも続行（ログに記録）
            print(f"Google Drive フォルダ作成エラー: {e}")
            metadata = data.metadata or {}
        
        contract_upload = ContractUpload(
            id=contract_upload_id,
            user_id=user_id,
            contract_type=data.contract_type.value,
            metadata=metadata
        )

        self.db.add(contract_upload)
        self.db.commit()
        self.db.refresh(contract_upload)

        return ContractUploadResponse.from_orm(contract_upload)

    async def get_contract_upload_detail(
        self, contract_upload_id: str, user_id: Optional[str] = None
    ) -> ContractUploadDetail:
        """契約書類アップロード詳細取得"""
        query = self.db.query(ContractUpload).filter(ContractUpload.id == contract_upload_id)

        if user_id:
            query = query.filter(ContractUpload.user_id == user_id)

        contract_upload = query.first()
        if not contract_upload:
            raise ValueError("契約書類アップロードが見つかりません")

        # 書類要件取得
        contract_type = ContractType(contract_upload.contract_type)
        requirements = DOCUMENT_REQUIREMENTS[contract_type]

        # アップロード済み書類取得
        uploaded_docs = self.db.query(Upload).filter(Upload.contract_upload_id == contract_upload_id).all()

        # 書類ごとの状態を構築
        doc_status_map = {}
        for req in requirements:
            doc_status = DocumentUploadStatus(
                document_type=req.document_type,
                display_name=req.display_name,
                description=req.description,
                required=req.required,
                uploaded=False,
                file_count=0,
                max_files=req.max_files,
                files=[],
                status=UploadStatus.PENDING,
                allowed_formats=req.allowed_formats,
                max_size_mb=req.max_size_mb,
            )
            doc_status_map[req.document_type] = doc_status

        # アップロード済みファイル情報を追加
        for upload in uploaded_docs:
            doc_type = DocumentType(upload.document_type)
            if doc_type in doc_status_map:
                file_info = {
                    "id": upload.id,
                    "filename": upload.original_filename,
                    "size": upload.size,
                    "uploaded_at": upload.created_at.isoformat(),
                    "status": upload.status.value,
                    "thumbnail_url": f"/api/v1/upload/thumbnail/{upload.id}" if upload.thumbnail_path else None,
                }
                doc_status_map[doc_type].files.append(file_info)
                doc_status_map[doc_type].file_count += 1
                doc_status_map[doc_type].uploaded = True
                doc_status_map[doc_type].status = upload.status
                if upload.expiry_date:
                    doc_status_map[doc_type].expiry_date = upload.expiry_date

        # 詳細情報構築
        document_statuses = list(doc_status_map.values())

        # 完了率計算
        required_docs = [ds for ds in document_statuses if ds.required]
        uploaded_required = [ds for ds in required_docs if ds.uploaded]
        completion_rate = (len(uploaded_required) / len(required_docs) * 100) if required_docs else 0

        # 不足書類
        missing_documents = [ds.display_name for ds in required_docs if not ds.uploaded]

        # 期限切れ書類
        expired_documents = []
        now = datetime.utcnow()
        for ds in document_statuses:
            if ds.expiry_date and ds.expiry_date < now:
                expired_documents.append(ds.display_name)

        return ContractUploadDetail(
            **contract_upload.__dict__,
            document_statuses=document_statuses,
            completion_rate=completion_rate,
            missing_documents=missing_documents,
            expired_documents=expired_documents,
        )

    async def upload_document(
        self,
        contract_upload_id: str,
        document_type: DocumentType,
        file_data: bytes,
        filename: str,
        content_type: str,
        user_id: str,
    ) -> FileUploadResponse:
        """書類アップロード"""
        # 契約アップロード確認
        contract_upload = (
            self.db.query(ContractUpload)
            .filter(ContractUpload.id == contract_upload_id, ContractUpload.user_id == user_id)
            .first()
        )

        if not contract_upload:
            raise ValueError("契約書類アップロードが見つかりません")

        # 書類要件確認
        contract_type = ContractType(contract_upload.contract_type)
        requirements = DOCUMENT_REQUIREMENTS[contract_type]

        requirement = None
        for req in requirements:
            if req.document_type == document_type:
                requirement = req
                break

        if not requirement:
            raise ValueError("無効な書類タイプです")

        # ファイル検証
        validation = await self._validate_file(file_data, filename, content_type, requirement)
        if not validation.is_valid:
            raise ValueError(f"ファイル検証エラー: {', '.join(validation.errors)}")

        # 既存ファイル数確認
        existing_count = (
            self.db.query(Upload)
            .filter(Upload.contract_upload_id == contract_upload_id, Upload.document_type == document_type.value)
            .count()
        )

        if existing_count >= requirement.max_files:
            raise ValueError(f"最大ファイル数（{requirement.max_files}）を超えています")

        # ファイル保存
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(filename)[1]
        stored_filename = f"{file_id}{file_ext}"
        storage_path = os.path.join(settings.UPLOAD_PATH, stored_filename)

        os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
        with open(storage_path, "wb") as f:
            f.write(file_data)

        # 有効期限計算
        expiry_date = None
        if requirement.expiry_days > 0:
            expiry_date = datetime.utcnow() + timedelta(days=requirement.expiry_days)

        # DB登録
        upload = Upload(
            id=file_id,
            contract_upload_id=contract_upload_id,
            document_type=document_type.value,
            filename=stored_filename,
            original_filename=filename,
            content_type=content_type,
            size=len(file_data),
            storage_path=storage_path,
            expiry_date=expiry_date,
        )

        self.db.add(upload)
        self.db.commit()
        self.db.refresh(upload)

        return FileUploadResponse.from_orm(upload)

    async def _validate_file(
        self, file_data: bytes, filename: str, content_type: str, requirement: Any
    ) -> DocumentValidationResult:
        """ファイル検証"""
        errors = []
        warnings = []

        # ファイル拡張子チェック
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in requirement.allowed_formats:
            errors.append(f"許可されていないファイル形式です。" f"許可: {', '.join(requirement.allowed_formats)}")

        # ファイルサイズチェック
        size_mb = len(file_data) / (1024 * 1024)
        if size_mb > requirement.max_size_mb:
            errors.append(f"ファイルサイズが大きすぎます。" f"最大: {requirement.max_size_mb}MB")

        # コンテンツタイプチェック
        if content_type.startswith("image/"):
            if file_ext not in [".jpg", ".jpeg", ".png"]:
                warnings.append("画像ファイルの形式を確認してください")
        elif content_type == "application/pdf":
            if file_ext != ".pdf":
                errors.append("PDFファイルの拡張子が正しくありません")

        # TODO: より詳細なファイル内容検証
        # - マジックナンバーチェック
        # - ウイルススキャン
        # - PDFの有効性チェック

        return DocumentValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    async def submit_contract_upload(self, contract_upload_id: str, user_id: str) -> ContractUploadResponse:
        """契約書類提出"""
        contract_upload = (
            self.db.query(ContractUpload)
            .filter(ContractUpload.id == contract_upload_id, ContractUpload.user_id == user_id)
            .first()
        )

        if not contract_upload:
            raise ValueError("契約書類アップロードが見つかりません")

        # 詳細情報取得して完了率確認
        detail = await self.get_contract_upload_detail(contract_upload_id, user_id)

        if detail.completion_rate < 100:
            raise ValueError(f"必要書類が不足しています。" f"不足: {', '.join(detail.missing_documents)}")

        if detail.expired_documents:
            raise ValueError(f"期限切れの書類があります。" f"期限切れ: {', '.join(detail.expired_documents)}")

        # ステータス更新
        contract_upload.submitted_at = datetime.utcnow()
        contract_upload.status = UploadStatus.PENDING

        self.db.commit()
        self.db.refresh(contract_upload)

        return ContractUploadResponse.from_orm(contract_upload)

    async def list_contract_uploads(
        self, user_id: Optional[str] = None, status: Optional[UploadStatus] = None, skip: int = 0, limit: int = 100
    ) -> List[ContractUploadResponse]:
        """契約書類アップロード一覧取得"""
        query = self.db.query(ContractUpload)

        if user_id:
            query = query.filter(ContractUpload.user_id == user_id)

        if status:
            query = query.filter(ContractUpload.status == status)

        query = query.order_by(ContractUpload.created_at.desc())
        query = query.offset(skip).limit(limit)

        uploads = query.all()

        return [ContractUploadResponse.from_orm(u) for u in uploads]
