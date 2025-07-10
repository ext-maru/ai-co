# 画像アップロード管理システム

## 概要
顧客が複数の画像をアップロードし、管理者が承認・管理できるWebアプリケーション

## 機能
- 📸 顧客: 5-10種類の画像アップロード
- ✅ 顧客: アップロード状況確認（〇×表示）
- 👨‍💼 管理者: アップロード画像の承認・却下
- ☁️ 管理者: GoogleDriveへの自動アップロード

## 技術スタック
- **Backend**: Flask (Python)
- **Frontend**: HTML/CSS/JavaScript
- **Database**: SQLite
- **Cloud**: Google Drive API
- **Container**: Docker

## 起動方法
```bash
# Docker起動
docker-compose up -d

# 顧客用URL
http://localhost:5000/customer/{customer_id}

# 管理者用URL
http://localhost:5000/admin
```

## 構成
```
├── app/
│   ├── app.py              # メインアプリケーション
│   ├── models.py           # データベースモデル
│   ├── templates/          # HTMLテンプレート
│   └── static/             # CSS/JS
├── uploads/                # アップロード画像保存
├── config/                 # 設定ファイル
├── Dockerfile
└── docker-compose.yml
```