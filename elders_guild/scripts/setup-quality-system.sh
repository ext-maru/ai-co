#!/bin/bash
# 品質管理システムのセットアップ

set -e

echo "🔧 品質管理システムのセットアップ..."

PROJECT_DIR="/home/aicompany/ai_co"
cd "$PROJECT_DIR"

# スクリプトに実行権限を付与
echo "📝 実行権限を付与..."
chmod +x scripts/start-quality-system.sh
chmod +x scripts/test-quality-system.sh
chmod +x scripts/ai-quality-stats
chmod +x workers/quality_pm_worker.py
chmod +x workers/quality_task_worker.py

# シンボリックリンク作成（コマンドとして使えるように）
echo "🔗 コマンドリンクを作成..."
if [ -d "bin" ]; then
    ln -sf ../scripts/ai-quality-stats bin/ai-quality-stats 2>/dev/null || true
fi

echo ""
echo "✅ セットアップ完了！"
echo ""
echo "📚 使用方法:"
echo ""
echo "1. システム起動:"
echo "   ./scripts/start-quality-system.sh"
echo ""
echo "2. テスト実行:"
echo "   ./scripts/test-quality-system.sh"
echo ""
echo "3. 品質統計確認:"
echo "   ai-quality-stats              # 過去24時間の統計"
echo "   ai-quality-stats --hours 48   # 過去48時間の統計"
echo "   ai-quality-stats --watch      # リアルタイム監視"
echo ""
echo "4. 通常使用:"
echo "   ai-send \"要件\" code          # PMが品質チェックして必要なら再実行"
echo ""
echo "📊 品質基準の概要:"
echo "  - シェバング、インポート設定"
echo "  - エラーハンドリング実装"
echo "  - ログ出力の実装"
echo "  - Slack通知（ワーカーの場合）"
echo "  - docstring/コメント"
echo "  - 品質スコア 0.7以上で合格"
echo ""
echo "🎯 これでPMが納得するまで自動で品質改善される仕組みが完成しました！"
