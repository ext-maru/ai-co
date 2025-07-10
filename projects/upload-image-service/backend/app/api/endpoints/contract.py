from typing import Optional

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.contract_type import ContractType
from app.models.contract_type import DocumentType
from app.models.contract_type import get_document_categories
from app.models.upload import UploadStatus
from app.schemas.contract_upload import ContractReviewRequest
from app.schemas.contract_upload import ContractUploadCreate
from app.schemas.contract_upload import ContractUploadDetail
from app.schemas.contract_upload import ContractUploadListResponse
from app.schemas.contract_upload import ContractUploadResponse
from app.schemas.contract_upload import FileUploadResponse
from app.services.contract_upload_service import ContractUploadService
from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/requirements/{contract_type}")
async def get_contract_requirements(contract_type: ContractType):
    """契約タイプ別の必要書類一覧取得"""
    categories = get_document_categories(contract_type)
    return {
        "contract_type": contract_type,
        "categories": [
            {
                "name": cat.name,
                "documents": [
                    {
                        "document_type": doc.document_type.value,
                        "display_name": doc.display_name,
                        "description": doc.description,
                        "required": doc.required,
                        "max_files": doc.max_files,
                        "allowed_formats": doc.allowed_formats,
                        "max_size_mb": doc.max_size_mb,
                        "expiry_days": doc.expiry_days,
                    }
                    for doc in cat.documents
                ],
            }
            for cat in categories
        ],
    }


@router.post("/", response_model=ContractUploadResponse)
async def create_contract_upload(
    data: ContractUploadCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """新規契約書類アップロードセッション作成"""
    service = ContractUploadService(db)
    try:
        return await service.create_contract_upload(user_id=current_user["id"], data=data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{contract_upload_id}", response_model=ContractUploadDetail)
async def get_contract_upload_detail(
    contract_upload_id: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """契約書類アップロード詳細取得"""
    service = ContractUploadService(db)
    try:
        return await service.get_contract_upload_detail(
            contract_upload_id=contract_upload_id, user_id=current_user["id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{contract_upload_id}/upload", response_model=FileUploadResponse)
async def upload_contract_document(
    contract_upload_id: str,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """契約書類ファイルアップロード"""
    service = ContractUploadService(db)

    # ファイル読み込み
    file_data = await file.read()

    try:
        return await service.upload_document(
            contract_upload_id=contract_upload_id,
            document_type=document_type,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type,
            user_id=current_user["id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{contract_upload_id}/submit", response_model=ContractUploadResponse)
async def submit_contract_upload(
    contract_upload_id: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """契約書類提出"""
    service = ContractUploadService(db)
    try:
        return await service.submit_contract_upload(contract_upload_id=contract_upload_id, user_id=current_user["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=ContractUploadListResponse)
async def list_contract_uploads(
    status: Optional[UploadStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """契約書類アップロード一覧取得"""
    service = ContractUploadService(db)

    uploads = await service.list_contract_uploads(user_id=current_user["id"], status=status, skip=skip, limit=limit)

    total = len(uploads)  # TODO: 実際のカウントクエリ実装

    return ContractUploadListResponse(items=uploads, total=total, skip=skip, limit=limit)


# 管理者用エンドポイント
@router.get("/admin/list", response_model=ContractUploadListResponse)
async def list_all_contract_uploads(
    status: Optional[UploadStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),  # TODO: 管理者権限チェック
    db: Session = Depends(get_db),
):
    """全契約書類アップロード一覧取得（管理者用）"""
    service = ContractUploadService(db)

    uploads = await service.list_contract_uploads(user_id=None, status=status, skip=skip, limit=limit)  # 全ユーザー対象

    total = len(uploads)

    return ContractUploadListResponse(items=uploads, total=total, skip=skip, limit=limit)


@router.get("/admin/{contract_upload_id}", response_model=ContractUploadDetail)
async def get_contract_upload_detail_admin(
    contract_upload_id: str,
    current_user=Depends(get_current_user),  # TODO: 管理者権限チェック
    db: Session = Depends(get_db),
):
    """契約書類アップロード詳細取得（管理者用）"""
    service = ContractUploadService(db)
    try:
        return await service.get_contract_upload_detail(
            contract_upload_id=contract_upload_id, user_id=None  # ユーザーIDチェックなし
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/{contract_upload_id}/review")
async def review_contract_upload(
    contract_upload_id: str,
    review_data: ContractReviewRequest,
    current_user=Depends(get_current_user),  # TODO: 管理者権限チェック
    db: Session = Depends(get_db),
):
    """契約書類レビュー（承認/却下）"""
    # TODO: レビュー処理の実装
    return {
        "message": "レビュー処理は実装準備中です",
        "contract_upload_id": contract_upload_id,
        "action": review_data.action,
    }


@router.get("/admin/pending", response_model=ContractUploadListResponse)
async def get_pending_contracts(
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),  # TODO: 管理者権限チェック
    db: Session = Depends(get_db),
):
    """作業中案件一括取得（アップしてない + NG出て再アップ必要）"""
    service = ContractUploadService(db)
    
    # 作業中ステータス: NOT_UPLOADED と NEEDS_REUPLOAD
    pending_statuses = [UploadStatus.NOT_UPLOADED, UploadStatus.NEEDS_REUPLOAD]
    
    uploads = await service.list_contract_uploads_by_statuses(
        statuses=pending_statuses,
        skip=skip,
        limit=limit
    )
    
    total = len(uploads)  # TODO: 実際のカウントクエリ実装
    
    return ContractUploadListResponse(items=uploads, total=total, skip=skip, limit=limit)


@router.patch("/admin/{contract_upload_id}/status")
async def update_contract_status(
    contract_upload_id: str,
    status: UploadStatus,
    admin_notes: Optional[str] = None,
    current_user=Depends(get_current_user),  # TODO: 管理者権限チェック
    db: Session = Depends(get_db),
):
    """契約ステータス更新（簡易版）"""
    service = ContractUploadService(db)
    
    try:
        updated_contract = await service.update_contract_status(
            contract_upload_id=contract_upload_id,
            status=status,
            admin_notes=admin_notes,
            admin_user_id=current_user["id"]
        )
        
        return {
            "success": True,
            "message": f"ステータスを{status.value}に更新しました",
            "contract_upload": updated_contract
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
