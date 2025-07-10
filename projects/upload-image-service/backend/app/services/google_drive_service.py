"""Google Drive統合サービス

専用ページ発行時に自動でフォルダ作成
ファイルアップロード時にGoogle Driveに保存
"""

import io
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleDriveService:
    """Google Drive操作サービス"""
    
    def __init__(self, credentials_path: str, root_folder_id: Optional[str] = None):
        """
        Args:
            credentials_path: サービスアカウントキーファイルのパス
            root_folder_id: ルートフォルダID（省略時はマイドライブ）
        """
        self.credentials_path = credentials_path
        self.root_folder_id = root_folder_id
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Google Drive APIの認証"""
        try:
            # サービスアカウント認証
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive API認証成功")
            
        except Exception as e:
            logger.error(f"Google Drive API認証失敗: {e}")
            raise
    
    def create_contract_folder(self, contract_upload_id: str, user_name: str) -> str:
        """契約アップロード用フォルダ作成
        
        Args:
            contract_upload_id: 契約アップロードID
            user_name: ユーザー名
            
        Returns:
            作成されたフォルダのID
        """
        try:
            folder_name = f"{contract_upload_id}_{user_name}"
            
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [self.root_folder_id] if self.root_folder_id else []
            }
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"Google Driveフォルダ作成成功: {folder_name} (ID: {folder_id})")
            
            return folder_id
            
        except HttpError as e:
            logger.error(f"Google Driveフォルダ作成失敗: {e}")
            raise
    
    def upload_file(self, file_data: bytes, filename: str, folder_id: str, 
                   content_type: str = 'application/octet-stream') -> str:
        """ファイルをGoogle Driveにアップロード
        
        Args:
            file_data: ファイルのバイナリデータ
            filename: ファイル名
            folder_id: アップロード先フォルダID
            content_type: ファイルのMIMEタイプ
            
        Returns:
            アップロードされたファイルのID
        """
        try:
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            
            media = MediaIoBaseUpload(
                io.BytesIO(file_data),
                mimetype=content_type,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"Google Driveファイルアップロード成功: {filename} (ID: {file_id})")
            
            return file_id
            
        except HttpError as e:
            logger.error(f"Google Driveファイルアップロード失敗: {e}")
            raise
    
    def get_folder_url(self, folder_id: str) -> str:
        """フォルダのURL取得
        
        Args:
            folder_id: フォルダID
            
        Returns:
            フォルダのWebURL
        """
        return f"https://drive.google.com/drive/folders/{folder_id}"
    
    def get_file_url(self, file_id: str) -> str:
        """ファイルのURL取得
        
        Args:
            file_id: ファイルID
            
        Returns:
            ファイルのWebURL
        """
        return f"https://drive.google.com/file/d/{file_id}/view"
    
    def list_folder_files(self, folder_id: str) -> list:
        """フォルダ内のファイル一覧取得
        
        Args:
            folder_id: フォルダID
            
        Returns:
            ファイル情報のリスト
        """
        try:
            query = f"parents in '{folder_id}'"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, createdTime, size)"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"フォルダ内ファイル取得: {len(files)}件")
            
            return files
            
        except HttpError as e:
            logger.error(f"フォルダ内ファイル取得失敗: {e}")
            raise
    
    def delete_file(self, file_id: str) -> bool:
        """ファイル削除
        
        Args:
            file_id: 削除するファイルID
            
        Returns:
            削除成功時True
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Google Driveファイル削除成功: {file_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Google Driveファイル削除失敗: {e}")
            return False
    
    def move_file_to_folder(self, file_id: str, new_folder_id: str) -> bool:
        """ファイルを別フォルダに移動
        
        Args:
            file_id: 移動するファイルID
            new_folder_id: 移動先フォルダID
            
        Returns:
            移動成功時True
        """
        try:
            # 現在の親フォルダを取得
            file = self.service.files().get(
                fileId=file_id,
                fields='parents'
            ).execute()
            
            previous_parents = ",".join(file.get('parents'))
            
            # 新しいフォルダに移動
            self.service.files().update(
                fileId=file_id,
                addParents=new_folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            
            logger.info(f"ファイル移動成功: {file_id} -> {new_folder_id}")
            return True
            
        except HttpError as e:
            logger.error(f"ファイル移動失敗: {e}")
            return False
    
    def create_subfolder(self, parent_folder_id: str, subfolder_name: str) -> str:
        """サブフォルダ作成
        
        Args:
            parent_folder_id: 親フォルダID
            subfolder_name: サブフォルダ名
            
        Returns:
            作成されたサブフォルダのID
        """
        try:
            folder_metadata = {
                'name': subfolder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"サブフォルダ作成成功: {subfolder_name} (ID: {folder_id})")
            
            return folder_id
            
        except HttpError as e:
            logger.error(f"サブフォルダ作成失敗: {e}")
            raise
    
    def set_folder_permissions(self, folder_id: str, email: str, role: str = 'reader'):
        """フォルダの共有権限設定
        
        Args:
            folder_id: フォルダID
            email: 共有先メールアドレス
            role: 権限レベル ('reader', 'writer', 'commenter')
        """
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            self.service.permissions().create(
                fileId=folder_id,
                body=permission
            ).execute()
            
            logger.info(f"フォルダ権限設定成功: {folder_id} -> {email} ({role})")
            
        except HttpError as e:
            logger.error(f"フォルダ権限設定失敗: {e}")
            raise


# シングルトンインスタンス用
_drive_service: Optional[GoogleDriveService] = None


def get_drive_service(credentials_path: str = None, root_folder_id: str = None) -> GoogleDriveService:
    """Google Drive サービスのシングルトンインスタンス取得"""
    global _drive_service
    
    if _drive_service is None:
        if not credentials_path:
            # 環境変数やデフォルトパスから取得
            credentials_path = "/app/config/google-drive-credentials.json"
        
        _drive_service = GoogleDriveService(credentials_path, root_folder_id)
    
    return _drive_service


# 便利関数
def create_user_contract_folder(contract_upload_id: str, user_name: str) -> Dict[str, str]:
    """ユーザーの契約用フォルダ作成（高レベル関数）
    
    Returns:
        {
            'folder_id': 'フォルダID',
            'folder_url': 'フォルダURL',
            'documents_folder_id': '書類フォルダID'
        }
    """
    drive_service = get_drive_service()
    
    # メインフォルダ作成
    main_folder_id = drive_service.create_contract_folder(contract_upload_id, user_name)
    
    # 書類用サブフォルダ作成
    documents_folder_id = drive_service.create_subfolder(main_folder_id, "書類")
    
    return {
        'folder_id': main_folder_id,
        'folder_url': drive_service.get_folder_url(main_folder_id),
        'documents_folder_id': documents_folder_id
    }


def upload_contract_document(file_data: bytes, filename: str, 
                           documents_folder_id: str, content_type: str) -> Dict[str, str]:
    """契約書類アップロード（高レベル関数）
    
    Returns:
        {
            'file_id': 'ファイルID',
            'file_url': 'ファイルURL'
        }
    """
    drive_service = get_drive_service()
    
    file_id = drive_service.upload_file(file_data, filename, documents_folder_id, content_type)
    
    return {
        'file_id': file_id,
        'file_url': drive_service.get_file_url(file_id)
    }