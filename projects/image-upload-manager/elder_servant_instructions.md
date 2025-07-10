# 🧝‍♂️ エルダーサーバント作業指示書

## 📋 タスク情報
- **タスクID**: image_upload_test_fix_20250710
- **優先度**: HIGH
- **期限**: 即時対応
- **承認者**: クロードエルダー

## 🎯 作業目標
画像アップロード管理システムの19個の失敗テストを修正し、カバレッジ67%を維持する。

## 📝 詳細作業手順

### Step 1: 環境準備（5分）
```bash
cd /home/aicompany/ai_co/projects/image-upload-manager
pip install pytest-mock --break-system-packages
```

### Step 2: conftest.py改善（5分）
`tests/conftest.py`に以下を追加：
```python
@pytest.fixture(autouse=True)
def reset_google_drive_singleton():
    """Google Driveサービスのシングルトンをリセット"""
    from google_drive_service import GoogleDriveService
    if hasattr(GoogleDriveService, '_instance'):
        delattr(GoogleDriveService, '_instance')
```

### Step 3: models.py修正（10分）
以下の変更を`app/models.py`に適用：

1. インポート追加：
```python
from sqlalchemy import func
```

2. 各モデルクラスの修正：
```python
# Customerクラス
created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

def __repr__(self):
    return f"<Customer {self.id}: {self.name}>"

# CustomerImageクラス  
created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

def __repr__(self):
    return f"<CustomerImage {self.customer_id}: {self.image_type.value}>"

# SystemConfigクラス
created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

def __repr__(self):
    return f"<SystemConfig {self.key}: {self.value}>"
```

3. 表示名の修正：
```python
# IMAGE_TYPE_DISPLAY_NAMESの修正
ImageType.BANK_STATEMENT: '銀行明細',  # '銀行取引明細'から変更
```

### Step 4: google_drive_service.py修正（15分）

1. インポート追加：
```python
from googleapiclient.http import MediaFileUpload
```

2. メソッド追加（GoogleDriveServiceクラス内）：
```python
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
        print(f"フォルダ作成エラー: {e}")
        return None

def upload_file(self, file_path: str, filename: str, folder_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """ファイルをアップロード（upload_imageのエイリアス）"""
    if not self.enabled or not self.service:
        return None
        
    if not os.path.exists(file_path):
        print(f"ファイルが見つかりません: {file_path}")
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
        print(f"ファイルアップロードエラー: {e}")
        return None
```

3. upload_approved_image関数の修正：
```python
def upload_approved_image(image_path: str, customer_name: str, image_type: str, original_filename: str) -> Optional[Dict[str, Any]]:
    """承認済み画像をGoogle Driveにアップロード"""
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
        print(f"Google Drive アップロードエラー: {e}")
        return None
```

### Step 5: app.py修正（10分）

1. resize_image関数の修正：
```python
def resize_image(image_path, max_size=(1920, 1080)):
    """画像リサイズ（容量削減）"""
    try:
        with Image.open(image_path) as img:
            # EXIF情報に基づく回転修正（新しいAPI使用）
            try:
                exif = img.getexif()
                if exif:
                    orientation = exif.get(0x0112)
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
            except:
                pass  # EXIF情報がない場合は無視
            
            # 以下既存のコード...
```

2. review_imageルートの修正：
```python
@app.route('/admin/image/<int:image_id>/review', methods=['POST'])
def review_image(image_id):
    """管理者：画像レビュー"""
    try:
        image = CustomerImage.query.get(image_id)
        if not image:
            return jsonify({'error': 'Image not found'}), 404
            
        # 既存のコード...
```

### Step 6: テスト実行と確認（10分）

```bash
# テスト実行
python3 -m pytest tests/ -v --cov=app --cov-report=term-missing

# 成功確認
# - 19個の失敗テストが0になること
# - カバレッジが67%以上であること
```

### Step 7: 報告（5分）

作業完了後、以下の情報を記録：
- 修正したファイル一覧
- テスト結果（成功数/全体数）
- 最終カバレッジ率
- 発生した問題と解決方法

## ⚠️ 注意事項

1. **データベーススキーマ変更**がある場合は、既存のデータベースファイルをバックアップ
2. **Dockerコンテナ**で動作している場合は、コンテナ内でも動作確認
3. **エラーが発生**した場合は、即座に報告し、4賢者会議を要請

## 📊 成功基準

- ✅ 全テストがPASS（64/64）
- ✅ カバレッジ67%以上
- ✅ 新たなエラーが発生しない
- ✅ コードの可読性維持

エルダーサーバントよ、この指示に従い作業を実行せよ。
進捗は30分ごとに報告すること。

---
承認：クロードエルダー
日時：2025-07-10 02:55