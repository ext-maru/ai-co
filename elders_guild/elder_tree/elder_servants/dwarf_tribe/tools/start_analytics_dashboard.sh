#!/bin/bash
echo "🚀 エルダーズギルド データアナリティクスダッシュボード起動"
echo "=============================================="
echo ""
echo "📊 以下の機能が利用可能です:"
echo "  - リアルタイムデータ分析"
echo "  - 予測アナリティクス"
echo "  - インタラクティブレポート"
echo "  - システムヘルス監視"
echo ""
echo "🌐 ダッシュボードを起動中..."
echo ""

cd /home/aicompany/ai_co
python3 projects/web-monitoring-dashboard/dashboard_server.py
