# Upload Image Service - サーバーアップロードコマンド

## 🚀 クイックデプロイコマンド

### 1. プロジェクトをサーバーにアップロード
```bash
# ローカルマシンから実行（プロジェクトルートで）
rsync -avz --exclude 'node_modules' --exclude 'venv' --exclude '__pycache__' \
  --exclude '*.db' --exclude '.env' --exclude 'server.log' --exclude 'frontend.log' \
  ./ ubuntu@172.29.65.239:/var/www/upload-image-service/
```

### 2. サーバーにSSH接続してデプロイ
```bash
# SSH接続
ssh ubuntu@172.29.65.239

# デプロイディレクトリに移動
cd /var/www/upload-image-service

# デプロイスクリプト実行
chmod +x deploy.sh
./deploy.sh
```

## 📝 サーバー接続情報メモ

- **ホスト**: 172.29.65.239
- **ユーザー**: ubuntu
- **デプロイ先**: /var/www/upload-image-service/
- **アプリケーションポート**: 9001
- **APIポート**: 8001

## 🔍 デプロイ後の確認

```bash
# ブラウザでアクセス
http://172.29.65.239:9001/        # メインアプリ
http://172.29.65.239:9001/admin   # 管理画面

# サーバー上でログ確認
tail -f /var/www/upload-image-service/backend/app.log
```

## 🛠️ トラブルシューティング

### ポート9001が使用中の場合
```bash
# 使用中のポート確認
sudo lsof -i :9001

# 別のポートに変更（例：9002）
# deploy.shとNginx設定を編集してポート番号を変更
```

### 権限エラーの場合
```bash
# ディレクトリ権限の修正
sudo chown -R ubuntu:ubuntu /var/www/upload-image-service
```
