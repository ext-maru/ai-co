#!/usr/bin/env python3
"""
画像アップロード管理システム - メインアプリケーション
"""

import os
import uuid
import secrets
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from PIL import Image
import json

from models import db, Customer, CustomerImage, ImageType, ImageStatus, SystemConfig
from models import get_image_type_display_name, get_status_display_name, get_status_symbol
from google_drive_service import upload_approved_image, get_drive_service

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///image_upload.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# データベース初期化
db.init_app(app)

# アップロードフォルダ作成
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 許可される拡張子
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    """許可されたファイル拡張子かチェック"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image_path, max_size=(1920, 1080)):
    """画像リサイズ（容量削減）"""
    try:
        with Image.open(image_path) as img:
            # EXIF情報に基づく回転修正（新API使用）
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
            
            # サイズ調整
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # JPEGで保存（品質調整）
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            img.save(image_path, 'JPEG', quality=85, optimize=True)
            return True
    except Exception as e:
        print(f"画像リサイズエラー: {e}")
        return False

@app.route('/')
def index():
    """トップページ"""
    return render_template('index.html')

@app.route('/customer/<customer_id>')
def customer_page(customer_id):
    """顧客ページ"""
    customer = Customer.query.get_or_404(customer_id)
    
    # 画像タイプ別の状況を取得
    image_status = {}
    for image_type in ImageType:
        image = CustomerImage.query.filter_by(
            customer_id=customer_id,
            image_type=image_type
        ).first()
        
        if image:
            image_status[image_type.value] = {
                'status': image.status.value,
                'symbol': get_status_symbol(image.status),
                'display_name': get_image_type_display_name(image_type),
                'uploaded_at': image.uploaded_at.strftime('%Y-%m-%d %H:%M') if image.uploaded_at else None,
                'reviewer_notes': image.reviewer_notes
            }
        else:
            image_status[image_type.value] = {
                'status': ImageStatus.PENDING.value,
                'symbol': get_status_symbol(ImageStatus.PENDING),
                'display_name': get_image_type_display_name(image_type),
                'uploaded_at': None,
                'reviewer_notes': None
            }
    
    return render_template('customer.html', customer=customer, image_status=image_status)

@app.route('/customer/<customer_id>/upload', methods=['POST'])
def upload_image(customer_id):
    """画像アップロード"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        if 'file' not in request.files:
            return jsonify({'error': 'ファイルが選択されていません'}), 400
        
        file = request.files['file']
        image_type_str = request.form.get('image_type')
        
        if file.filename == '':
            return jsonify({'error': 'ファイルが選択されていません'}), 400
        
        if not image_type_str:
            return jsonify({'error': '画像タイプが指定されていません'}), 400
        
        try:
            image_type = ImageType(image_type_str)
        except ValueError:
            return jsonify({'error': '無効な画像タイプです'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '許可されていないファイル形式です（JPG、PNG、GIFのみ）'}), 400
        
        # ファイル名生成
        filename = secure_filename(file.filename)
        unique_filename = f"{customer_id}_{image_type.value}_{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # ファイル保存
        file.save(file_path)
        
        # 画像リサイズ
        if not resize_image(file_path):
            os.remove(file_path)
            return jsonify({'error': '画像処理に失敗しました'}), 400
        
        # ファイル情報取得
        file_size = os.path.getsize(file_path)
        
        # 既存の画像レコードをチェック
        existing_image = CustomerImage.query.filter_by(
            customer_id=customer_id,
            image_type=image_type
        ).first()
        
        if existing_image:
            # 既存ファイルを削除
            if existing_image.file_path and os.path.exists(existing_image.file_path):
                os.remove(existing_image.file_path)
            
            # レコード更新
            existing_image.filename = unique_filename
            existing_image.original_filename = filename
            existing_image.file_path = file_path
            existing_image.file_size = file_size
            existing_image.mime_type = file.content_type
            existing_image.status = ImageStatus.UPLOADED
            existing_image.uploaded_at = datetime.now(timezone.utc)
            existing_image.reviewed_at = None
            existing_image.reviewer_notes = None
            
        else:
            # 新規レコード作成
            image = CustomerImage(
                customer_id=customer_id,
                image_type=image_type,
                filename=unique_filename,
                original_filename=filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=file.content_type,
                status=ImageStatus.UPLOADED,
                uploaded_at=datetime.now(timezone.utc)
            )
            db.session.add(image)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'アップロードが完了しました',
            'image_type': image_type.value,
            'status': ImageStatus.UPLOADED.value,
            'symbol': get_status_symbol(ImageStatus.UPLOADED)
        })
        
    except RequestEntityTooLarge:
        return jsonify({'error': 'ファイルサイズが大きすぎます（最大16MB）'}), 413
    except Exception as e:
        print(f"アップロードエラー: {e}")
        return jsonify({'error': '内部エラーが発生しました'}), 500

@app.route('/admin')
def admin_page():
    """管理者ページ"""
    customers = Customer.query.all()
    
    customer_data = []
    for customer in customers:
        images = CustomerImage.query.filter_by(customer_id=customer.id).all()
        
        upload_status = {}
        for image_type in ImageType:
            image = next((img for img in images if img.image_type == image_type), None)
            if image:
                upload_status[image_type.value] = {
                    'status': image.status.value,
                    'symbol': get_status_symbol(image.status),
                    'uploaded_at': image.uploaded_at.strftime('%Y-%m-%d %H:%M') if image.uploaded_at else None
                }
            else:
                upload_status[image_type.value] = {
                    'status': ImageStatus.PENDING.value,
                    'symbol': get_status_symbol(ImageStatus.PENDING),
                    'uploaded_at': None
                }
        
        customer_data.append({
            'customer': customer,
            'upload_status': upload_status
        })
    
    return render_template('admin.html', customer_data=customer_data, image_types=ImageType)

@app.route('/admin/customer/<customer_id>/images')
def admin_customer_images(customer_id):
    """管理者：顧客画像詳細"""
    customer = Customer.query.get_or_404(customer_id)
    images = CustomerImage.query.filter_by(customer_id=customer_id).all()
    
    return render_template('admin_customer_images.html', customer=customer, images=images)

@app.route('/admin/image/<int:image_id>/review', methods=['POST'])
def review_image(image_id):
    """管理者：画像レビュー"""
    try:
        image = db.session.get(CustomerImage, image_id)
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        action = request.form.get('action')
        notes = request.form.get('notes', '')
        
        if action == 'approve':
            image.status = ImageStatus.APPROVED
        elif action == 'reject':
            image.status = ImageStatus.REJECTED
        else:
            return jsonify({'error': '無効なアクションです'}), 400
        
        image.reviewed_at = datetime.now(timezone.utc)
        image.reviewer_notes = notes
        
        # 承認の場合、Google Driveにアップロード
        if action == 'approve' and image.file_path and os.path.exists(image.file_path):
            try:
                customer = db.session.get(Customer, image.customer_id)
                drive_result = upload_approved_image(
                    image_path=image.file_path,
                    customer_name=customer.name,
                    image_type=image.image_type.value,
                    original_filename=image.original_filename
                )
                
                if drive_result:
                    image.google_drive_file_id = drive_result.get('file_id')
                    image.google_drive_url = drive_result.get('web_view_link')
                    print(f"Google Drive アップロード成功: {drive_result.get('file_id')}")
                else:
                    print("Google Drive アップロードに失敗しました")
                    
            except Exception as e:
                print(f"Google Drive アップロードエラー: {e}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'レビューが完了しました',
            'status': image.status.value,
            'symbol': get_status_symbol(image.status)
        })
        
    except Exception as e:
        print(f"レビューエラー: {e}")
        return jsonify({'error': '内部エラーが発生しました'}), 500

@app.route('/admin/image/<int:image_id>/view')
def view_image(image_id):
    """管理者：画像表示"""
    image = CustomerImage.query.get_or_404(image_id)
    
    if not image.file_path or not os.path.exists(image.file_path):
        return "画像ファイルが見つかりません", 404
    
    return send_file(image.file_path)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    """管理者：システム設定"""
    if request.method == 'POST':
        try:
            # 認証ファイルのアップロード処理
            if 'google_credentials_file' in request.files:
                credentials_file = request.files['google_credentials_file']
                if credentials_file and credentials_file.filename.endswith('.json'):
                    # 設定ディレクトリのパス
                    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
                    os.makedirs(config_dir, exist_ok=True)
                    
                    # ファイル保存
                    credentials_path = os.path.join(config_dir, 'google_credentials.json')
                    credentials_file.save(credentials_path)
                    
                    flash('認証ファイルをアップロードしました', 'success')
                elif credentials_file and credentials_file.filename:
                    flash('JSONファイルを選択してください', 'error')
            
            # Google Drive設定
            google_drive_enabled = request.form.get('google_drive_enabled') == 'on'
            google_drive_folder_id = request.form.get('google_drive_folder_id', '').strip()
            
            # 環境変数を更新（実際の本番環境では設定ファイルに保存すべき）
            os.environ['GOOGLE_DRIVE_ENABLED'] = 'true' if google_drive_enabled else 'false'
            if google_drive_folder_id:
                os.environ['GOOGLE_DRIVE_FOLDER_ID'] = google_drive_folder_id
            
            # システム設定をデータベースに保存
            settings = {
                'google_drive_enabled': google_drive_enabled,
                'google_drive_folder_id': google_drive_folder_id,
                'max_file_size': request.form.get('max_file_size', '16'),
                'allowed_extensions': request.form.get('allowed_extensions', 'jpg,jpeg,png,gif'),
            }
            
            for key, value in settings.items():
                config = SystemConfig.query.filter_by(key=key).first()
                if config:
                    config.value = str(value)
                else:
                    config = SystemConfig(
                        key=key,
                        value=str(value),
                        description=f"System setting: {key}"
                    )
                    db.session.add(config)
            
            db.session.commit()
            
            # Google Drive サービスの再初期化
            drive_service = get_drive_service()
            drive_service.enabled = google_drive_enabled
            if google_drive_enabled:
                drive_service.folder_id = google_drive_folder_id
                drive_service._initialize_service()
            
            flash('設定を保存しました', 'success')
            return redirect(url_for('admin_settings'))
            
        except Exception as e:
            print(f"設定保存エラー: {e}")
            flash('設定の保存に失敗しました', 'error')
            return redirect(url_for('admin_settings'))
    
    # 現在の設定を取得
    settings = {}
    for key in ['google_drive_enabled', 'google_drive_folder_id', 'max_file_size', 'allowed_extensions']:
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            settings[key] = config.value
        else:
            # デフォルト値
            if key == 'google_drive_enabled':
                settings[key] = os.getenv('GOOGLE_DRIVE_ENABLED', 'false').lower() == 'true'
            elif key == 'google_drive_folder_id':
                settings[key] = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')
            elif key == 'max_file_size':
                settings[key] = '16'
            elif key == 'allowed_extensions':
                settings[key] = 'jpg,jpeg,png,gif'
    
    # Google Drive接続状態確認
    drive_service = get_drive_service()
    google_drive_status = {
        'enabled': drive_service.enabled,
        'connected': False,
        'error': None
    }
    
    if drive_service.enabled and drive_service.service:
        try:
            # 接続テスト
            about = drive_service.service.about().get(fields='user').execute()
            google_drive_status['connected'] = True
            google_drive_status['user'] = about.get('user', {}).get('emailAddress', 'Unknown')
        except Exception as e:
            google_drive_status['error'] = str(e)
    
    # 認証ファイルの存在確認
    # Dockerとローカル環境の両方に対応
    if os.path.exists('/app/config/google_credentials.json'):
        credentials_path = '/app/config/google_credentials.json'
        google_drive_status['credentials_exists'] = True
    elif os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'config', 'google_credentials.json')):
        credentials_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'google_credentials.json')
        google_drive_status['credentials_exists'] = True
    else:
        google_drive_status['credentials_exists'] = False
        google_drive_status['credentials_path'] = 'config/google_credentials.json'
    
    return render_template('admin_settings.html', settings=settings, google_drive_status=google_drive_status, os=os)

@app.route('/admin/settings/google-drive-guide')
def google_drive_guide():
    """Google Drive設定ガイド表示"""
    return render_template('admin_settings_guide.html')

@app.route('/admin/settings/google-drive-guide-content')
def google_drive_guide_content():
    """Google Drive設定ガイド内容（AJAX用）"""
    return render_template('admin_settings_guide.html')

@app.route('/admin/customer/create', methods=['GET', 'POST'])
def create_customer():
    """管理者：顧客作成"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            
            if not name:
                flash('顧客名は必須です', 'error')
                return redirect(url_for('create_customer'))
            
            # より長い安全なランダムIDを生成（URLトークンとして使用）
            # 32文字のランダム文字列（推測困難）
            customer_id = secrets.token_urlsafe(24)  # URLセーフな32文字程度のトークン
            
            customer = Customer(
                id=customer_id,
                name=name,
                email=email,
                phone=phone
            )
            
            db.session.add(customer)
            db.session.commit()
            
            flash(f'顧客「{name}」を作成しました', 'success')
            return redirect(url_for('admin_page'))
            
        except Exception as e:
            print(f"顧客作成エラー: {e}")
            flash('顧客作成に失敗しました', 'error')
            return redirect(url_for('create_customer'))
    
    return render_template('create_customer.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

def init_db():
    """データベース初期化"""
    with app.app_context():
        db.create_all()
        
        # サンプルデータ作成
        if Customer.query.count() == 0:
            # テスト用顧客（推測困難なID）
            test_customer_id = secrets.token_urlsafe(24)
            test_customer = Customer(
                id=test_customer_id,
                name='テスト太郎',
                email='test@example.com',
                phone='090-1234-5678'
            )
            db.session.add(test_customer)
            db.session.commit()
            print(f"テスト顧客を作成しました: {test_customer_id}")
            print(f"テスト顧客URL: /customer/{test_customer_id}")

if __name__ == '__main__':
    init_db()
    # use_reloader=Falseで不要な再起動を防ぐ
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)