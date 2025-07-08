#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "=== エラー智能判断システム セットアップ完了 ==="
echo ""
echo "📊 初期モニタリング結果:"
python3 scripts/monitor_error_intelligence.py
echo ""
echo "🎉 Phase 1の実装が完了しました！"
echo ""
echo "使用方法:"
echo "  - モニタリング: python3 scripts/monitor_error_intelligence.py"
echo "  - ログ確認: tail -f logs/error_intelligence_worker.log"
echo "  - ワーカー確認: tmux attach -t error_intelligence"
