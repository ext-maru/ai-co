# Docker Best Practices for Elders Guild
# エルダーズギルド Docker ベストプラクティス

**策定者**: RAGエルダー (Search Mystic)
**承認**: エルダー評議会
**適用開始**: 2025-07-10

## 🏛️ エルダーズギルド Docker 運用原則

### 1. 階層遵守原則
```yaml
# グランドエルダーmaru → クロードエルダー → 4賢者 の階層をコンテナ設計に反映
services:
  grand-elder-maru:
    image: elders/grand-elder:latest
    depends_on:
      - claude-elder

  claude-elder:
    image: elders/claude-elder:latest
    depends_on:
      - knowledge-sage
      - task-oracle
      - crisis-sage
      - rag-elder
```

### 2. 賢者独立性原則
- 各賢者は独立したコンテナとして動作
- 賢者間通信は明確なAPIで定義
- 知識ベースは共有ボリュームで管理

### 3. TDD統合原則
```dockerfile
# すべてのコンテナにテスト環境を統合
FROM python:3.11-slim AS test
COPY requirements-test.txt .
RUN pip install -r requirements-test.txt
COPY . .
RUN pytest tests/

FROM python:3.11-slim AS production
# テスト済みコードのみを本番環境に
```

## 🔐 セキュリティベストプラクティス

### コンテナセキュリティ
```dockerfile
# 非rootユーザー実行
RUN adduser --disabled-password --gecos '' elderuser
USER elderuser

# 最小権限原則
USER 1001
WORKDIR /app
```

### シークレット管理
```yaml
# Docker Secrets使用
secrets:
  elder_council_key:
    external: true
  database_password:
    external: true

services:
  knowledge-sage:
    secrets:
      - elder_council_key
```

## ⚡ パフォーマンス最適化

### イメージサイズ最適化
```dockerfile
# Alpine Linux ベース使用
FROM python:3.11-alpine

# Multi-stage build
FROM node:18-alpine AS build
# ビルド処理
FROM nginx:alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
```

### リソース制限
```yaml
services:
  rag-elder:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
```

## 🔄 開発ワークフロー統合

### 開発環境コンテナ
```yaml
# docker-compose.dev.yml
services:
  claude-elder-dev:
    build:
      context: .
      target: development
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
    ports:
      - "3000:3000"
      - "9229:9229"  # デバッグポート
```

### CI/CD 統合
```yaml
# GitHub Actions 統合例
- name: Build and test
  run: |
    docker build --target test .
    docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📊 監視・ロギング

### ヘルスチェック標準
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### ログ管理
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    labels: "service,environment"
```

## 🚀 デプロイメント戦略

### ブルーグリーンデプロイ
```bash
# 新バージョンデプロイ
docker compose -f docker-compose.blue.yml up -d
# ヘルスチェック後
docker compose -f docker-compose.green.yml down
```

### ローリングアップデート
```yaml
deploy:
  replicas: 3
  update_config:
    parallelism: 1
    delay: 10s
    order: start-first
```

---
**策定完了**: 2025-07-10
**適用範囲**: エルダーズギルド全プロジェクト
**更新周期**: 月次レビュー
**責任者**: RAGエルダー + クロードエルダー
