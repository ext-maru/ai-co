# 🌐 Elders Guild Project Web Portal - 更新版アクセス情報

**RAGエルダー推奨Docker統合環境（ポート分離版）**

## 📍 サーバーIPアドレス

### 🖥️ メインサーバーIP
- **プライマリIP**: `172.29.65.239`
- **Tailscale VPN**: `100.76.169.124`

## 🚪 ポート分離版アクセス情報

### 🎯 **メインアクセス（推奨）**

#### **Nginxプロキシ経由（統合アクセス）**
```
http://172.29.65.239:8080        # メインアプリケーション
http://100.76.169.124:8080       # Tailscale VPN経由
```

### 🔧 **開発者向け直接アクセス**

#### **Next.js フロントエンド**
```
http://172.29.65.239:8002
http://100.76.169.124:8002
```

#### **FastAPI バックエンド**
```
http://172.29.65.239:8001        # API
http://172.29.65.239:8001/docs   # Swagger UI
http://172.29.65.239:8001/redoc  # ReDoc
```

#### **データベース**
```
PostgreSQL: 172.29.65.239:8003
Redis:      172.29.65.239:8004
```

## 🎯 ポート割り当て表

| サービス | 外部ポート | 内部ポート | 説明 |
|---------|-----------|-----------|------|
| **Nginx** | 8080 | 80 | メインプロキシ |
| **FastAPI** | 8001 | 8000 | バックエンドAPI |
| **Next.js** | 8002 | 3000 | フロントエンド |
| **PostgreSQL** | 8003 | 5432 | データベース |
| **Redis** | 8004 | 6379 | キャッシュ |

## 🚀 起動方法

### 📋 自動起動スクリプト
```bash
cd /home/aicompany/ai_co
./scripts/docker_start.sh
```

### ⚡ 手動起動
```bash
# 環境変数設定
cp .env.example .env
# .env の OPENAI_API_KEY を設定

# Docker起動
docker-compose up -d
```

## 🔍 動作確認

### 📊 ヘルスチェック
```bash
# メインアプリ（Nginx）
curl http://172.29.65.239:8080/health

# バックエンドAPI
curl http://172.29.65.239:8001/health

# フロントエンド
curl http://172.29.65.239:8002
```

### 📈 サービス状態確認
```bash
# コンテナ状態
docker-compose ps

# 全サービスログ
docker-compose logs -f
```

## 🌍 ブラウザアクセス

### 🎯 **推奨アクセス方法**
```
メインアプリ: http://172.29.65.239:8080
```

### 🔧 **開発者用アクセス**
```
フロントエンド: http://172.29.65.239:8002
API:          http://172.29.65.239:8001
API Docs:     http://172.29.65.239:8001/docs
```

### 📱 **Tailscale VPN ユーザー**
```
メインアプリ: http://100.76.169.124:8080
```

## 🔌 API エンドポイント例

### 🎯 主要API
```bash
# プロジェクト一覧
curl http://172.29.65.239:8001/api/projects

# プロジェクト詳細
curl http://172.29.65.239:8001/api/projects/{id}

# プロジェクトスキャン
curl -X POST http://172.29.65.239:8001/api/projects/scan \
  -H "Content-Type: application/json" \
  -d '{"root_path": "/home/aicompany/ai_co", "force_refresh": false}'

# 統計情報
curl http://172.29.65.239:8001/api/stats

# 検索
curl "http://172.29.65.239:8001/api/search?q=python&limit=10"
```

### 🔄 WebSocket
```javascript
// リアルタイム通信
const ws = new WebSocket('ws://172.29.65.239:8001/ws');
```

## 🗄️ データベース接続

### 📊 PostgreSQL
```bash
# Docker経由
docker-compose exec postgres psql -U elder_admin -d elders_guild

# 外部クライアント
psql -h 172.29.65.239 -p 8003 -U elder_admin -d elders_guild
```

### 🔧 Redis
```bash
# Docker経由
docker-compose exec redis redis-cli

# 外部クライアント
redis-cli -h 172.29.65.239 -p 8004
```

## 🛠️ 管理コマンド

### 📋 基本操作
```bash
# サービス起動
docker-compose up -d

# サービス停止
docker-compose down

# 個別サービス再起動
docker-compose restart backend

# ログ確認
docker-compose logs -f [service_name]
```

### 📊 監視
```bash
# リソース使用量
docker stats

# サービス状態
docker-compose ps

# システムリソース
htop
```

## 🔒 ポート競合回避

### ✅ **他アプリとの競合回避**
- **80番ポート**: 8080番に変更（他のWebサーバーと競合回避）
- **3000番ポート**: 8002番に変更（他のNext.jsアプリと競合回避）
- **8000番ポート**: 8001番に変更（他のFastAPIアプリと競合回避）
- **5432番ポート**: 8003番に変更（他のPostgreSQLと競合回避）
- **6379番ポート**: 8004番に変更（他のRedisと競合回避）

### 🔍 **ポート使用状況確認**
```bash
# 使用中ポート確認
netstat -tlnp | grep -E ":(80|3000|8000|8001|8002|8003|8004|5432|6379)"

# 特定ポート確認
lsof -i :8080
```

## 🚨 トラブルシューティング

### ❗ よくある問題

#### 1. **ポート競合エラー**
```bash
# エラー例: "bind: address already in use"
# 解決: 競合ポートを確認・停止
sudo lsof -i :8080
sudo kill -9 <PID>
```

#### 2. **フロントエンドAPI接続エラー**
```bash
# 環境変数確認
docker-compose exec frontend env | grep NEXT_PUBLIC

# 正しい設定:
# NEXT_PUBLIC_API_URL=http://localhost:8001
```

#### 3. **データベース接続エラー**
```bash
# PostgreSQL起動確認
docker-compose logs postgres

# 接続テスト
docker-compose exec postgres pg_isready -U elder_admin
```

## 🎯 テスト手順

### 1️⃣ **基本接続テスト**
```bash
curl -I http://172.29.65.239:8080/health
curl -I http://172.29.65.239:8001/health
curl -I http://172.29.65.239:8002
```

### 2️⃣ **機能テスト**
1. ブラウザで `http://172.29.65.239:8080` にアクセス
2. プロジェクト一覧が表示されることを確認
3. プロジェクトスキャンを実行
4. プロジェクト詳細ページを確認
5. 自動資料生成をテスト

### 3️⃣ **API テスト**
```bash
# プロジェクト一覧
curl http://172.29.65.239:8001/api/projects

# 統計情報
curl http://172.29.65.239:8001/api/stats
```

## 🎊 利点・特徴

### ✅ **ポート分離の利点**
- **他アプリとの競合回避**: 標準ポートを避けて安全
- **複数環境共存**: 他の開発環境と同時稼働可能
- **明確な分離**: 各サービスが独立したポートで稼働
- **開発効率向上**: ポート競合によるダウンタイム削減

### 🎯 **推奨運用方法**
- **一般ユーザー**: `http://172.29.65.239:8080` （Nginx経由）
- **開発者**: 必要に応じて直接ポートアクセス
- **管理者**: すべてのポートでシステム監視

---

## 🌟 まとめ

**ポート分離版Elders Guild Project Web Portal**により、他のアプリケーションとの競合を完全に回避した安全な運用環境を実現しました。

### 🎯 **メインアクセス**
```
http://172.29.65.239:8080
```

**🎉 ポート競合の心配なく、RAGエルダー推奨の最先端プロジェクト管理システムをお楽しみください！**
