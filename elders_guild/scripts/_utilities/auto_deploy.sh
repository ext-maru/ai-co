#!/bin/bash
echo "🚀 Starting automatic deployment..."

# 品質ゲート実行
python3 scripts/quality_gate.py
if [ $? -ne 0 ]; then
    echo "❌ Quality gates failed. Deployment aborted."
    exit 1
fi

# デプロイ実行（本番では実際のデプロイコマンドに置換）
echo "✅ Quality gates passed. Deploying to production..."
echo "🎉 Deployment completed successfully!"
