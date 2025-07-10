#!/usr/bin/env python3
"""
Google Drive連携サービス
"""

import os
import io
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleDriveService:
    """Google Drive 連携サービス"""
    
    def __init__(self, credentials_path: str = None, folder_id: str = None):
        # Dockerとローカル環境の両方に対応
        if credentials_path:
            self.credentials_path = credentials_path
        elif os.path.exists('/app/config/google_credentials.json'):
            self.credentials_path = '/app/config/google_credentials.json'
        else:
            # ローカル環境のパス
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.credentials_path = os.path.join(base_dir, 'config', 'google_credentials.json')
        
        self.folder_id = folder_id or os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        self.enabled = os.getenv('GOOGLE_DRIVE_ENABLED', 'false').lower() == 'true'
        self.service = None
        
        if self.enabled:
            self._initialize_service()
    
    def _initialize_service(self) -> bool:
        """Google Drive サービスを初期化"""
        try:
            if not os.path.exists(self.credentials_path):
                logger.error(f"認証情報ファイルが見つかりません: {self.credentials_path}")
                self.enabled = False
                return False
            
            # 認証情報の読み込み
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            # Drive APIクライアント作成
            self.service = build('drive', 'v3', credentials=credentials)
            
            # 接続テスト
            self._test_connection()
            
            logger.info("Google Drive サービスの初期化が完了しました")
            return True
            
        except Exception as e:
            logger.error(f"Google Drive サービスの初期化に失敗: {e}")
            self.enabled = False
            return False
    
    def _test_connection(self):
        """接続テスト"""
        try:
            # 簡単なAPIコールでテスト
            about = self.service.about().get(fields='user').execute()
            user_email = about.get('user', {}).get('emailAddress', 'Unknown')
            logger.info(f"Google Drive 接続成功: {user_email}")
            
            # フォルダの存在確認
            if self.folder_id:
                self._verify_folder()
                
        except HttpError as e:
            logger.error(f"Google Drive 接続テストに失敗: {e}")
            raise
    
    def _verify_folder(self):
        """フォルダの存在確認"""
        try:
            folder = self.service.files().get(fileId=self.folder_id).execute()
            logger.info(f"アップロード先フォルダ確認: {folder.get('name', 'Unknown')}")
        except HttpError as e:
            if e.resp.status == 404:
                logger.error(f"指定されたフォルダが見つかりません: {self.folder_id}")
            else:
                logger.error(f"フォルダの確認に失敗: {e}")
            raise
    
    def upload_image(self, image_path: str, customer_name: str, image_type: str, 
                    original_filename: str) -> Optional[Dict[str, Any]]:
        """画像をGoogle Driveにアップロード"""
        
        if not self.enabled:
            logger.warning("Google Drive 連携が無効です")
            return None
        
        if not self.service:
            logger.error("Google Drive サービスが初期化されていません")
            return None
        
        try:
            # ファイルの存在確認
            if not os.path.exists(image_path):
                logger.error(f"アップロードファイルが見つかりません: {image_path}")
                return None
            
            # ファイルサイズ確認
            file_size = os.path.getsize(image_path)
            if file_size > 10 * 1024 * 1024:  # 10MB制限
                logger.error(f"ファイルサイズが大きすぎます: {file_size} bytes")
                return None
            
            # アップロード先フォルダ作成（顧客別）
            customer_folder_id = self._create_customer_folder(customer_name)
            
            # ファイル名生成
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            clean_image_type = image_type.replace('_', ' ').title()
            drive_filename = f"{clean_image_type}_{timestamp}_{original_filename}"
            
            # ファイルメタデータ
            file_metadata = {
                'name': drive_filename,
                'parents': [customer_folder_id],
                'description': f"画像種類: {clean_image_type}\n顧客: {customer_name}\nアップロード日時: {datetime.now().isoformat()}"
            }
            
            # ファイルの読み込み
            with open(image_path, 'rb') as file_data:
                media = MediaIoBaseUpload(
                    io.BytesIO(file_data.read()),
                    mimetype='image/jpeg',
                    resumable=True
                )
            
            # アップロード実行
            logger.info(f"Google Drive アップロード開始: {drive_filename}")
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,webContentLink'
            ).execute()
            
            # 結果
            result = {
                'file_id': file.get('id'),
                'filename': file.get('name'),
                'web_view_link': file.get('webViewLink'),
                'web_content_link': file.get('webContentLink'),
                'folder_id': customer_folder_id,
                'upload_time': datetime.now().isoformat()
            }
            
            logger.info(f"Google Drive アップロード完了: {file.get('id')}")
            return result
            
        except HttpError as e:
            logger.error(f"Google Drive アップロードエラー (HTTP): {e}")
            return None
        except Exception as e:
            logger.error(f"Google Drive アップロードエラー: {e}")
            return None
    
    def _create_customer_folder(self, customer_name: str) -> str:
        """顧客別フォルダを作成（既存の場合は取得）"""
        try:
            # 既存フォルダの検索
            query = f"name='{customer_name}' and parents in '{self.folder_id}' and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(q=query).execute()
            
            existing_folders = results.get('files', [])
            if existing_folders:
                folder_id = existing_folders[0]['id']
                logger.info(f"既存の顧客フォルダを使用: {customer_name} ({folder_id})")
                return folder_id
            
            # 新規フォルダ作成
            current_date = datetime.now().strftime('%Y年%m月')
            folder_metadata = {
                'name': customer_name,
                'parents': [self.folder_id],
                'mimeType': 'application/vnd.google-apps.folder',
                'description': f"顧客: {customer_name}\n作成日: {current_date}"
            }
            
            folder = self.service.files().create(body=folder_metadata).execute()
            folder_id = folder.get('id')
            
            logger.info(f"新規顧客フォルダを作成: {customer_name} ({folder_id})")
            return folder_id
            
        except Exception as e:
            logger.error(f"顧客フォルダの作成に失敗: {e}")
            # エラーの場合は親フォルダを返す
            return self.folder_id
    
    def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
        """フォルダを作成"""
        if not self.enabled or not self.service:
            return None
            
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_folder_id or self.folder_id:
            file_metadata['parents'] = [parent_folder_id or self.folder_id]
        
        try:
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            return folder.get('id')
        except Exception as e:
            logger.error(f"フォルダ作成エラー: {e}")
            return None
    
    def upload_file(self, file_path: str, filename: str, folder_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """ファイルをアップロード（upload_imageのエイリアス）"""
        if not self.enabled or not self.service:
            return None
            
        if not os.path.exists(file_path):
            logger.error(f"ファイルが見つかりません: {file_path}")
            return None
        
        try:
            # MIMEタイプを推定
            mime_type = 'image/jpeg'
            if file_path.lower().endswith('.png'):
                mime_type = 'image/png'
            elif file_path.lower().endswith('.gif'):
                mime_type = 'image/gif'
                
            media = MediaFileUpload(file_path, mimetype=mime_type)
            
            file_metadata = {
                'name': filename,
                'parents': [folder_id] if folder_id else ([self.folder_id] if self.folder_id else [])
            }
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink'
            ).execute()
            
            return {
                'id': file.get('id'),
                'webViewLink': file.get('webViewLink')
            }
        except Exception as e:
            logger.error(f"ファイルアップロードエラー: {e}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """ファイルを削除"""
        if not self.enabled or not self.service:
            return False
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Google Drive ファイル削除完了: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Google Drive ファイル削除エラー: {e}")
            return False
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """ファイル情報を取得"""
        if not self.enabled or not self.service:
            return None
        
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields='id,name,size,createdTime,modifiedTime,webViewLink'
            ).execute()
            
            return file_info
        except Exception as e:
            logger.error(f"Google Drive ファイル情報取得エラー: {e}")
            return None
    
    def list_customer_files(self, customer_name: str) -> list:
        """顧客のファイル一覧を取得"""
        if not self.enabled or not self.service:
            return []
        
        try:
            # 顧客フォルダ検索
            folder_query = f"name='{customer_name}' and parents in '{self.folder_id}' and mimeType='application/vnd.google-apps.folder'"
            folder_results = self.service.files().list(q=folder_query).execute()
            
            customer_folders = folder_results.get('files', [])
            if not customer_folders:
                return []
            
            customer_folder_id = customer_folders[0]['id']
            
            # フォルダ内のファイル一覧
            files_query = f"parents in '{customer_folder_id}'"
            files_results = self.service.files().list(
                q=files_query,
                fields='files(id,name,size,createdTime,webViewLink)'
            ).execute()
            
            return files_results.get('files', [])
            
        except Exception as e:
            logger.error(f"顧客ファイル一覧取得エラー: {e}")
            return []
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """ストレージ使用量を取得"""
        if not self.enabled or not self.service:
            return {}
        
        try:
            about = self.service.about().get(fields='storageQuota').execute()
            storage_quota = about.get('storageQuota', {})
            
            return {
                'limit': int(storage_quota.get('limit', 0)),
                'usage': int(storage_quota.get('usage', 0)),
                'usage_in_drive': int(storage_quota.get('usageInDrive', 0)),
                'usage_in_drive_trash': int(storage_quota.get('usageInDriveTrash', 0))
            }
        except Exception as e:
            logger.error(f"ストレージ使用量取得エラー: {e}")
            return {}


# シングルトンインスタンス
_drive_service_instance = None


def get_drive_service() -> GoogleDriveService:
    """Google Drive サービスのシングルトンインスタンスを取得"""
    global _drive_service_instance
    
    if _drive_service_instance is None:
        _drive_service_instance = GoogleDriveService()
    
    return _drive_service_instance


def upload_approved_image(image_path: str, customer_name: str, image_type: str, 
                         original_filename: str) -> Optional[Dict[str, Any]]:
    """承認済み画像をGoogle Driveにアップロード（便利関数）"""
    service = get_drive_service()
    
    if not service.enabled:
        return None
    
    try:
        # 顧客フォルダ作成または取得
        folder_id = service.create_folder(customer_name)
        if not folder_id:
            return None
        
        # ファイル名作成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{customer_name}_{image_type}_{timestamp}_{original_filename}"
        
        # アップロード実行
        result = service.upload_file(image_path, filename, folder_id)
        
        if result:
            return {
                'file_id': result.get('id'),
                'web_view_link': result.get('webViewLink'),
                'folder_id': folder_id
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Google Drive アップロードエラー: {e}")
        return None