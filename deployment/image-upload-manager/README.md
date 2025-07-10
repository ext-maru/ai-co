# エルダーズギルド Image Upload Manager デプロイ

## 📋 デプロイ手順

### 1. サーバにファイル転送
```bash
scp -i server-private.pem -r image-upload-manager ubuntu@57.181.4.111:/tmp/
```

### 2. デプロイ実行
```bash
ssh -i server-private.pem ubuntu@57.181.4.111
cd /tmp/image-upload-manager
./deploy.sh
```

### 3. 動作確認
```bash
curl http://57.181.4.111/
```

## 🛠️ 管理コマンド

### アプリケーション管理
```bash
cd /opt/elders-guild/image-upload-manager

# 停止
docker compose -f docker-compose.production.yml down

# 起動
docker compose -f docker-compose.production.yml up -d

# ログ確認
docker compose -f docker-compose.production.yml logs -f

# 再起動
docker compose -f docker-compose.production.yml restart
```

### システム監視
```bash
# コンテナ状態確認
docker ps

# リソース使用量
docker stats

# ログ確認
tail -f /var/log/nginx/elders-guild-image-upload.access.log
```

## 🔧 トラブルシューティング

### コンテナ起動失敗
```bash
docker compose -f docker-compose.production.yml logs
docker system prune -f
```

### Nginx設定エラー
```bash
sudo nginx -t
sudo systemctl status nginx
```

### ポート競合
```bash
sudo netstat -tulpn | grep :5000
sudo netstat -tulpn | grep :80
```

## 📊 監視・メンテナンス

- **アクセスログ**: `/var/log/nginx/elders-guild-image-upload.access.log`
- **エラーログ**: `/var/log/nginx/elders-guild-image-upload.error.log`
- **アプリログ**: `docker compose logs -f`
- **データ**: `/opt/elders-guild/image-upload-manager/data/`
- **アップロード**: `/opt/elders-guild/image-upload-manager/uploads/`
