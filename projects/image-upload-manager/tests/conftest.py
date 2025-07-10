import pytest
import os
import sys
import tempfile
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app import app, db, init_db
from models import Customer, CustomerImage, ImageType, ImageStatus

@pytest.fixture
def client():
    """テスト用のFlaskクライアント"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

@pytest.fixture
def sample_customer():
    """サンプル顧客データ"""
    customer = Customer(
        id='test_customer_123',
        name='テスト太郎',
        email='test@example.com',
        phone='090-1234-5678'
    )
    db.session.add(customer)
    db.session.commit()
    return customer

@pytest.fixture
def temp_upload_dir():
    """一時的なアップロードディレクトリ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_upload_folder = app.config['UPLOAD_FOLDER']
        app.config['UPLOAD_FOLDER'] = temp_dir
        yield temp_dir
        app.config['UPLOAD_FOLDER'] = original_upload_folder

@pytest.fixture
def sample_image_file():
    """サンプル画像ファイル"""
    from PIL import Image
    import io
    
    # 100x100の赤い画像を作成
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes

@pytest.fixture(autouse=True)
def reset_google_drive_singleton():
    """Google Driveサービスのシングルトンをリセット"""
    from google_drive_service import GoogleDriveService
    if hasattr(GoogleDriveService, '_instance'):
        delattr(GoogleDriveService, '_instance')