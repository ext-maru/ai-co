# Elders Guild Project Web Portal - Next.js Frontend
# RAGエルダー推奨Docker環境

FROM node:18-alpine AS base

# メタデータ
LABEL maintainer="Claude Elder <claude@eldersguild.ai>"
LABEL description="Elders Guild Project Web Portal - Next.js 14 Frontend"
LABEL version="1.0.0"

# 依存関係インストールステージ
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# package.json と package-lock.json をコピー
COPY package*.json ./
RUN npm ci --only=production

# ビルドステージ
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js のテレメトリを無効化
ENV NEXT_TELEMETRY_DISABLED 1

# アプリケーションビルド
RUN npm run build

# 実行ステージ
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# 非rootユーザー作成
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 必要なファイルをコピー
COPY --from=builder /app/public ./public

# ビルド出力を適切な権限でコピー
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# ユーザー切り替え
USER nextjs

# ポート公開
EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# アプリケーション起動
CMD ["node", "server.js"]
