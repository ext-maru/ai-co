#!/usr/bin/env python3
"""
データベースモデル定義
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import func

db = SQLAlchemy()

class ImageStatus(Enum):
    PENDING = "pending"      # 未アップロード
    UPLOADED = "uploaded"    # アップロード済み（承認待ち）
    APPROVED = "approved"    # 承認済み
    REJECTED = "rejected"    # 却下

class ImageType(Enum):
    # とりあえず版：一般的な書類種類
    IDENTITY_CARD = "identity_card"        # 身分証明書
    RESIDENCE_CERT = "residence_cert"      # 住民票
    INCOME_PROOF = "income_proof"          # 収入証明書
    CONTRACT = "contract"                  # 契約書
    BANK_STATEMENT = "bank_statement"      # 銀行明細
    OTHER_DOCUMENT = "other_document"      # その他書類

class Customer(db.Model):
    """顧客テーブル"""
    __tablename__ = 'customers'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # リレーション
    images = db.relationship('CustomerImage', backref='customer', lazy=True)
    
    def __repr__(self):
        return f"<Customer {self.id}: {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class CustomerImage(db.Model):
    """顧客画像テーブル"""
    __tablename__ = 'customer_images'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    image_type = db.Column(db.Enum(ImageType), nullable=False)
    filename = db.Column(db.String(255))
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    status = db.Column(db.Enum(ImageStatus), default=ImageStatus.PENDING)
    uploaded_at = db.Column(db.DateTime)
    reviewed_at = db.Column(db.DateTime)
    reviewer_notes = db.Column(db.Text)
    google_drive_file_id = db.Column(db.String(100))
    google_drive_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<CustomerImage {self.customer_id}: {self.image_type.value}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'image_type': self.image_type.value,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'status': self.status.value,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewer_notes': self.reviewer_notes,
            'google_drive_url': self.google_drive_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class SystemConfig(db.Model):
    """システム設定テーブル"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemConfig {self.key}: {self.value}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# ヘルパー関数
def get_image_type_display_name(image_type):
    """画像タイプの表示名を取得"""
    display_names = {
        ImageType.IDENTITY_CARD: "身分証明書",
        ImageType.RESIDENCE_CERT: "住民票",
        ImageType.INCOME_PROOF: "収入証明書",
        ImageType.CONTRACT: "契約書",
        ImageType.BANK_STATEMENT: "銀行明細",
        ImageType.OTHER_DOCUMENT: "その他書類"
    }
    return display_names.get(image_type, image_type.value)

def get_status_display_name(status):
    """ステータスの表示名を取得"""
    display_names = {
        ImageStatus.PENDING: "未アップロード",
        ImageStatus.UPLOADED: "アップロード済み",
        ImageStatus.APPROVED: "承認済み",
        ImageStatus.REJECTED: "却下"
    }
    return display_names.get(status, status.value)

def get_status_symbol(status):
    """ステータスの記号を取得"""
    symbols = {
        ImageStatus.PENDING: "×",
        ImageStatus.UPLOADED: "📤",
        ImageStatus.APPROVED: "○",
        ImageStatus.REJECTED: "×"
    }
    return symbols.get(status, "?")