#!/bin/bash
# Phase 2自動セットアップ開始

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🚀 エラー智能判断システム Phase 2 セットアップ開始"
echo ""
echo "📊 Phase 2の実装内容:"
echo "  - AutoFixExecutor: エラー自動修正エンジン"
echo "  - RetryOrchestrator: 修正後のリトライ管理"
echo "  - 安全性チェックとロールバック機能"
echo "  - 修正履歴の学習機能"
echo ""

# セットアップ実行
python3 scripts/setup_error_intelligence_phase2.py
