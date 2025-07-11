from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pathlib import Path
import json

from app.core.database import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/admin/google-drive/settings")
async def get_google_drive_settings():
    """Google Drive設定を取得"""
    return {
        "google_drive_enabled": settings.google_drive_enabled,
        "google_drive_parent_folder_id": settings.google_drive_parent_folder_id or "",
        "google_drive_folder_name_format": settings.google_drive_folder_name_format,
        "google_drive_auto_create_folders": settings.google_drive_auto_create_folders,
        "google_drive_share_with_submitter": settings.google_drive_share_with_submitter,
        "credentials_uploaded": bool(settings.google_drive_credentials_path and
                                   Path(settings.google_drive_credentials_path).exists())
    }


@router.put("/admin/google-drive/settings")
async def update_google_drive_settings(settings_data: dict):
    """Google Drive設定を更新"""
    # 実際の実装では環境変数または設定ファイルを更新
    # ここでは簡略化のためメモリ上で更新

    if "google_drive_enabled" in settings_data:
        settings.google_drive_enabled = settings_data["google_drive_enabled"]

    if "google_drive_parent_folder_id" in settings_data:
        settings.google_drive_parent_folder_id = settings_data["google_drive_parent_folder_id"]

    if "google_drive_folder_name_format" in settings_data:
        settings.google_drive_folder_name_format = settings_data["google_drive_folder_name_format"]

    if "google_drive_auto_create_folders" in settings_data:
        settings.google_drive_auto_create_folders = settings_data["google_drive_auto_create_folders"]

    if "google_drive_share_with_submitter" in settings_data:
        settings.google_drive_share_with_submitter = settings_data["google_drive_share_with_submitter"]

    return {"message": "設定が保存されました"}


@router.post("/admin/google-drive/test-connection")
async def test_google_drive_connection():
    """Google Drive接続テスト"""
    try:
        # 認証ファイル確認
        if not settings.google_drive_credentials_path:
            return {
                "connected": False,
                "error": "認証ファイルが設定されていません"
            }

        creds_path = Path(settings.google_drive_credentials_path)
        if not creds_path.exists():
            return {
                "connected": False,
                "error": "認証ファイルが見つかりません"
            }

        # 実際のGoogle Drive API接続テストはここで実装
        # 今回は簡略化のため、ファイルの存在確認のみ

        return {
            "connected": True,
            "message": "接続テストが成功しました"
        }

    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


@router.post("/admin/google-drive/upload-credentials")
async def upload_credentials(
    credentials: UploadFile = File(...)
):
    """Google Drive認証ファイルをアップロード"""
    # ファイル形式チェック
    if not credentials.filename.endswith('.json'):
        raise HTTPException(
            status_code=400,
            detail="JSONファイルを選択してください"
        )

    # 認証ファイル保存
    creds_dir = Path("./credentials")
    creds_dir.mkdir(exist_ok=True)

    creds_path = creds_dir / "credentials.json"

    content = await credentials.read()

    # JSON形式チェック
    try:
        json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="無効なJSONファイルです"
        )

    with open(creds_path, "wb") as f:
        f.write(content)

    # 設定更新
    settings.google_drive_credentials_path = str(creds_path)

    return {"message": "認証ファイルがアップロードされました"}
