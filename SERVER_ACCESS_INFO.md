# 🌐 Elders Guild Project Web Portal - サーバーアクセス情報

**RAGエルダー推奨Docker統合環境**のアクセス情報

## 📍 サーバーIPアドレス

### 🖥️ メインサーバーIP
- **プライマリIP**: `172.29.65.239`
- **Tailscale VPN**: `100.76.169.124`

## 🚪 アクセスポート一覧

### 🌐 Webアプリケーション

#### **メインアクセス（Nginx経由）**
```
http://172.29.65.239        # HTTP（推奨）
http://100.76.169.124       # Tailscale VPN経由
```

#### **直接アクセス**
```
# Next.js フロントエンド
http://172.29.65.239:3000
http://100.76.169.124:3000

# FastAPI バックエンド
http://172.29.65.239:8000
http://100.76.169.124:8000

# FastAPI ドキュメント
http://172.29.65.239:8000/docs
http://100.76.169.124:8000/docs
```

### 🗄️ データベース

#### **PostgreSQL + pgvector**
```
Host: 172.29.65.239
Port: 5432
Database: elders_guild
User: elder_admin
Password: sage_wisdom_2025

# 接続文字列
postgresql://elder_admin:sage_wisdom_2025@172.29.65.239:5432/elders_guild
```

#### **Redis**
```
Host: 172.29.65.239
Port: 6379
Database: 0

# 接続文字列
redis://172.29.65.239:6379/0
```

## 🚀 Docker起動コマンド

### 📋 起動手順

```bash
# 1. サーバーにSSH接続
ssh user@172.29.65.239

# 2. プロジェクトディレクトリに移動
cd /home/aicompany/ai_co

# 3. 環境変数設定
cp .env.example .env
nano .env  # OPENAI_API_KEY を設定

# 4. Docker起動
./scripts/docker_start.sh
```

### ⚡ 個別サービス起動

```bash
# 段階的起動
docker-compose up -d postgres redis    # データベース
docker-compose up -d backend           # API
docker-compose up -d frontend          # UI
docker-compose up -d nginx             # プロキシ

# 一括起動
docker-compose up -d
```

## 🔍 サービス確認

### 📊 ヘルスチェック

```bash
# メインアプリ
curl http://172.29.65.239/health

# バックエンドAPI
curl http://172.29.65.239:8000/health

# フロントエンド
curl http://172.29.65.239:3000
```

### 📈 ステータス確認

```bash
# コンテナ状態
docker-compose ps

# ログ確認
docker-compose logs -f

# リソース使用量
docker stats
```

## 🌍 外部アクセス設定

### 🔓 ファイアウォール（必要に応じて）

```bash
# 必要ポート開放
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS
sudo ufw allow 3000    # Next.js（開発用）
sudo ufw allow 8000    # FastAPI（開発用）
```

### 🔒 セキュリティ設定

```bash
# 本番環境では直接ポートアクセスを制限
sudo ufw deny 3000     # Next.js 直接アクセス拒否
sudo ufw deny 8000     # FastAPI 直接アクセス拒否
sudo ufw deny 5432     # PostgreSQL 外部アクセス拒否
sudo ufw deny 6379     # Redis 外部アクセス拒否
```

## 📱 アクセス方法

### 🖥️ デスクトップブラウザ

```
メインアプリ:    http://172.29.65.239
API ドキュメント: http://172.29.65.239:8000/docs
```

### 📱 モバイル・タブレット

```
メインアプリ:    http://172.29.65.239
```

### 🔧 開発者用

```
フロントエンド:   http://172.29.65.239:3000
バックエンド:    http://172.29.65.239:8000
API Docs:      http://172.29.65.239:8000/docs
ReDoc:         http://172.29.65.239:8000/redoc
```

## 🔌 API エンドポイント

### 🎯 主要API

```bash
# プロジェクト一覧
GET http://172.29.65.239:8000/api/projects

# プロジェクト詳細
GET http://172.29.65.239:8000/api/projects/{id}

# プロジェクトスキャン
POST http://172.29.65.239:8000/api/projects/scan

# 自動資料生成
POST http://172.29.65.239:8000/api/projects/{id}/documentation

# 統計情報
GET http://172.29.65.239:8000/api/stats

# 検索
GET http://172.29.65.239:8000/api/search?q=python
```

### 🔄 WebSocket

```javascript
// リアルタイム通信
const ws = new WebSocket('ws://172.29.65.239:8000/ws');
```

## 📊 監視・デバッグ

### 🔍 ログ確認

```bash
# 全サービスログ
ssh user@172.29.65.239 "cd /home/aicompany/ai_co && docker-compose logs -f"

# 個別サービス
ssh user@172.29.65.239 "cd /home/aicompany/ai_co && docker-compose logs -f backend"
```

### 📈 メトリクス

```bash
# コンテナリソース
ssh user@172.29.65.239 "docker stats --no-stream"

# システムリソース
ssh user@172.29.65.239 "top"
```

## 🎯 テスト手順

### 1️⃣ 基本接続テスト

```bash
# メインアプリ
curl -I http://172.29.65.239

# API ヘルス
curl http://172.29.65.239:8000/health
```

### 2️⃣ 機能テスト

```bash
# プロジェクト一覧
curl http://172.29.65.239:8000/api/projects

# 統計情報
curl http://172.29.65.239:8000/api/stats
```

### 3️⃣ フロントエンドテスト

1. ブラウザで `http://172.29.65.239` にアクセス
2. プロジェクト一覧が表示されることを確認
3. プロジェクトスキャンを実行
4. プロジェクト詳細ページを確認

## 🎊 まとめ

### 🌟 推奨アクセス方法

**🎯 一般ユーザー**:
```
http://172.29.65.239
```

**🔧 開発者**:
```
フロントエンド: http://172.29.65.239:3000
API:          http://172.29.65.239:8000
API Docs:     http://172.29.65.239:8000/docs
```

**📱 Tailscale VPN ユーザー**:
```
http://100.76.169.124
```

---

**🎉 Elders Guild Project Web Portal へようこそ！**  
**RAGエルダー推奨の最先端プロジェクト管理システムをお楽しみください！**