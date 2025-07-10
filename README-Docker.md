# 🐳 Elders Guild Project Web Portal - Docker統合環境

RAGエルダー推奨による完全なDocker統合開発・本番環境

## 🎯 概要

完全にコンテナ化されたElders Guild Project Web Portalシステム：

- **PostgreSQL + pgvector**: ベクトル検索対応データベース
- **Redis**: キャッシュ・バックグラウンドタスク
- **FastAPI**: Python バックエンドAPI
- **Next.js 14**: React フロントエンド
- **Nginx**: リバースプロキシ・ロードバランサー

## 🏗️ アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx (Port 80)                     │
│                 リバースプロキシ                          │
└─────────────────────┬───────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
┌─────────▼──────────┐   ┌────────▼──────────┐
│   Next.js Frontend │   │  FastAPI Backend  │
│    (Port 3000)     │   │    (Port 8000)    │
└────────────────────┘   └───────────┬───────┘
                                     │
                     ┌───────────────┴───────────────┐
                     │                               │
           ┌─────────▼──────────┐         ┌─────────▼──────────┐
           │ PostgreSQL+pgvector │         │      Redis        │
           │    (Port 5432)     │         │   (Port 6379)     │
           └────────────────────┘         └───────────────────┘
```

## 🚀 クイックスタート

### 前提条件

- Docker 20.10+
- Docker Compose 2.0+
- OpenAI API キー

### 1. リポジトリクローン

```bash
git clone <repository-url>
cd ai_co
```

### 2. 環境変数設定

```bash
# 環境変数ファイル作成
cp .env.example .env

# OpenAI API キーを設定
nano .env
# OPENAI_API_KEY=sk-proj-your-api-key-here
```

### 3. 自動起動（推奨）

```bash
# 自動起動スクリプト実行
./scripts/docker_start.sh
```

### 4. 手動起動

```bash
# 段階的起動
docker-compose up -d postgres redis
sleep 10
docker-compose up -d backend
sleep 15
docker-compose up -d frontend nginx
```

### 5. 動作確認

- **メインアプリ**: http://localhost
- **フロントエンド**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📋 サービス詳細

### PostgreSQL + pgvector

```yaml
service: postgres
image: pgvector/pgvector:pg16
port: 5432
database: elders_guild
user: elder_admin
password: sage_wisdom_2025
```

**機能**:
- ベクトル類似検索（HNSW インデックス）
- プロジェクトメタデータ保存
- 自動資料生成データ
- システムメトリクス

### Redis

```yaml
service: redis
image: redis:7-alpine
port: 6379
```

**機能**:
- APIレスポンスキャッシュ
- バックグラウンドタスクキュー
- セッション管理
- リアルタイム通信

### FastAPI Backend

```yaml
service: backend
build: Dockerfile.backend
port: 8000
```

**機能**:
- RESTful API エンドポイント
- プロジェクト分析エンジン
- 自動資料生成
- WebSocket リアルタイム通信
- OpenAI API 統合

### Next.js Frontend

```yaml
service: frontend
build: frontend/Dockerfile
port: 3000
```

**機能**:
- React 18 + TypeScript
- Tailwind CSS スタイリング
- SWR データフェッチ
- Framer Motion アニメーション
- Mermaid 図表描画

### Nginx

```yaml
service: nginx
image: nginx:alpine
port: 80
```

**機能**:
- リバースプロキシ
- 静的ファイル配信
- ロードバランシング
- SSL/TLS 終端
- レート制限

## 🛠️ 開発環境

### ホットリロード開発

```bash
# 開発モードで起動
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 個別サービス再起動
docker-compose restart backend
docker-compose restart frontend
```

### ログ確認

```bash
# 全サービスログ
docker-compose logs -f

# 個別サービスログ
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### データベース接続

```bash
# PostgreSQL接続
docker-compose exec postgres psql -U elder_admin -d elders_guild

# Redis接続
docker-compose exec redis redis-cli
```

## 🔧 運用コマンド

### 基本操作

```bash
# サービス起動
docker-compose up -d

# サービス停止
docker-compose down

# サービス再起動
docker-compose restart

# サービス状態確認
docker-compose ps
```

### データ管理

```bash
# データベースバックアップ
docker-compose exec postgres pg_dump -U elder_admin elders_guild > backup.sql

# データベースリストア
docker-compose exec -T postgres psql -U elder_admin elders_guild < backup.sql

# ボリューム削除（データ完全削除）
docker-compose down -v
```

### システム更新

```bash
# イメージ更新
docker-compose pull

# 再ビルド
docker-compose build --no-cache

# 更新適用
docker-compose up -d --force-recreate
```

## 📊 監視・メトリクス

### ヘルスチェック

```bash
# 全サービス確認
curl http://localhost/health

# 個別サービス確認
curl http://localhost:8000/health
curl http://localhost:3000
```

### リソース監視

```bash
# コンテナリソース使用量
docker stats

# 詳細監視
docker-compose exec backend htop
```

## 🔒 セキュリティ

### 本番環境設定

1. **環境変数の更新**:
   ```bash
   # .env ファイル更新
   SECRET_KEY=production-secret-key
   JWT_SECRET=production-jwt-secret
   POSTGRES_PASSWORD=secure-password
   ```

2. **SSL証明書設定**:
   ```bash
   # SSL証明書配置
   mkdir -p nginx/ssl
   cp cert.pem nginx/ssl/
   cp key.pem nginx/ssl/
   ```

3. **ファイアウォール設定**:
   ```bash
   # 必要ポートのみ開放
   ufw allow 80
   ufw allow 443
   ufw deny 3000
   ufw deny 8000
   ```

## 🚨 トラブルシューティング

### よくある問題

#### 1. ポート競合

```bash
# ポート使用確認
netstat -tlnp | grep :80
netstat -tlnp | grep :3000

# Docker Composeポート変更
# docker-compose.yml のportsセクションを編集
```

#### 2. メモリ不足

```bash
# メモリ使用量確認
docker stats --no-stream

# 不要コンテナ・イメージ削除
docker system prune -a
```

#### 3. データベース接続エラー

```bash
# PostgreSQL起動確認
docker-compose logs postgres

# 接続テスト
docker-compose exec postgres pg_isready -U elder_admin
```

#### 4. フロントエンドビルドエラー

```bash
# Node.js依存関係確認
docker-compose exec frontend npm list

# 再ビルド
docker-compose build frontend --no-cache
```

### デバッグモード

```bash
# 詳細ログ有効化
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose up --build

# コンテナ内部確認
docker-compose exec backend bash
docker-compose exec frontend sh
```

## 📈 パフォーマンス最適化

### 本番環境最適化

1. **イメージサイズ削減**:
   - マルチステージビルド使用
   - 不要ファイル除外
   - Alpine ベースイメージ

2. **キャッシュ戦略**:
   - Nginx 静的ファイルキャッシュ
   - Redis API レスポンスキャッシュ
   - Docker レイヤーキャッシュ

3. **リソース制限**:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 512M
         cpus: '0.5'
   ```

## 🎯 次のステップ

1. **監視システム統合**:
   - Prometheus + Grafana
   - ELK Stack ログ集約
   - Jaeger 分散トレーシング

2. **CI/CD パイプライン**:
   - GitHub Actions
   - 自動テスト実行
   - 段階的デプロイ

3. **スケールアウト**:
   - Docker Swarm クラスタ
   - Kubernetes 移行
   - マイクロサービス分割

---

## 🎊 結語

**Elders Guild Project Web Portal** のDocker統合環境により、開発から本番まで一貫した高品質なコンテナ基盤を実現しました。

RAGエルダーの叡智により、最新のコンテナ技術とAI技術が完璧に融合した、次世代のプロジェクト管理システムをお楽しみください！

**🚀 Happy Dockerizing with Elders Guild! 🚀**