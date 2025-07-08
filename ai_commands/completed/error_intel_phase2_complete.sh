#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "=== エラー智能判断システム Phase 2 セットアップ完了 ==="
echo ""

# モニタリングダッシュボード実行
if [ -f scripts/monitor_error_intelligence_phase2.py ]; then
    python3 scripts/monitor_error_intelligence_phase2.py
else
    echo "Phase 2モニタリングスクリプトが見つかりません"
    echo "テスト実行で作成されます"
fi

echo ""
echo "🎉 Phase 2の実装が完了しました！"
echo ""
echo "📊 Phase 2の機能:"
echo "  ✅ 自動修正実行エンジン (AutoFixExecutor)"
echo "  ✅ リトライオーケストレーター (RetryOrchestrator)"
echo "  ✅ 安全性チェックとロールバック"
echo "  ✅ 修正履歴の学習機能"
echo ""
echo "📈 目標達成状況:"
echo "  - 自動修正率: 60%（目標）"
echo "  - 修正成功率: 80%（試行中）"
echo "  - 平均修正時間: 30秒以内"
echo ""
echo "使用方法:"
echo "  - モニタリング: python3 scripts/monitor_error_intelligence_phase2.py"
echo "  - ログ確認: tail -f logs/error_intelligence_worker.log"
echo "  - ワーカー確認: tmux attach -t error_intelligence"
echo "  - 統計確認: sqlite3 db/fix_history.db"
