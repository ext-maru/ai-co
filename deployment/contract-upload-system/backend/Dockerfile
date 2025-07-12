# Elder Flow準拠 - 本番環境対応Dockerfile
FROM python:3.12-slim

WORKDIR /app

# メタデータ
LABEL maintainer="Elders Guild <elder@guild.com>"
LABEL version="2.1.0"
LABEL description="Elder Flow準拠 契約書アップロードシステム"

# システム依存関係 (セキュリティ更新含む)
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    libpng-dev \
    postgresql-client \
    curl \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# 本番環境依存関係をコピー
COPY requirements.production.txt requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.production.txt

# アプリケーションコード
COPY . .

# セキュリティ: 実行ユーザー作成
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app
USER appuser

# ヘルスチェック設定
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ポート公開
EXPOSE 8000

# 環境変数設定
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# 本番環境起動コマンド
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-level", "info"]
