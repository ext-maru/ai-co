import hashlib
import os
import uuid
from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional

import aiofiles
from app.core.config import settings
from app.models.upload import Upload
from app.services.storage_service import StorageService
from PIL import Image


class UploadService:
    def __init__(self):
        self.storage = StorageService()
        self.upload_path = settings.UPLOAD_PATH
        os.makedirs(self.upload_path, exist_ok=True)

    async def process_upload(self, file_data: bytes, filename: str, content_type: str, user_id: str) -> Dict:
        """ファイルアップロード処理"""
        # ファイルID生成
        file_id = str(uuid.uuid4())
        hashlib.sha256(file_data).hexdigest()

        # ファイル保存
        file_path = os.path.join(self.upload_path, f"{file_id}_{filename}")
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_data)

        # サムネイル生成（画像の場合）
        thumbnail_path = None
        if content_type.startswith("image/"):
            thumbnail_path = await self.create_thumbnail(file_path, file_id)

        # データベース記録
        upload_record = Upload(
            id=file_id,
            filename=filename,
            content_type=content_type,
            size=len(file_data),
            user_id=user_id,
            storage_path=file_path,
            thumbnail_path=thumbnail_path,
            status="pending",
        )

        # クラウドストレージへのアップロード（設定による）
        if settings.CLOUD_STORAGE_ENABLED:
            cloud_url = await self.storage.upload_to_cloud(file_path, filename)
            upload_record.cloud_url = cloud_url

        return {
            "file_id": file_id,
            "filename": filename,
            "size": len(file_data),
            "status": "success",
            "thumbnail_url": f"/api/v1/upload/thumbnail/{file_id}" if thumbnail_path else None,
        }

    async def create_thumbnail(self, file_path: str, file_id: str) -> Optional[str]:
        """サムネイル生成"""
        try:
            with Image.open(file_path) as img:
                # EXIF情報に基づいて回転補正
                img = self.correct_image_orientation(img)

                # サムネイルサイズ
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)

                # 保存
                thumbnail_path = os.path.join(self.upload_path, f"thumb_{file_id}.jpg")
                img.save(thumbnail_path, "JPEG", quality=85)

                return thumbnail_path
        except Exception as e:
            print(f"サムネイル生成エラー: {e}")
            return None

    def correct_image_orientation(self, img):
        """画像の向き補正"""
        try:
            exif = img._getexif()
            if exif:
                orientation = exif.get(274)  # Orientation tag
                if orientation:
                    rotations = {3: 180, 6: 270, 8: 90}
                    if orientation in rotations:
                        img = img.rotate(rotations[orientation], expand=True)
        except:
            pass
        return img

    async def get_upload_status(self, file_id: str) -> Optional[Dict]:
        """アップロードステータス取得"""
        # TODO: データベースから取得
        return {"file_id": file_id, "status": "pending", "created_at": datetime.now().isoformat()}

    async def list_user_uploads(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        """ユーザーのアップロード一覧"""
        # TODO: データベースから取得
        return []
