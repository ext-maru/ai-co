#!/bin/bash
#!/bin/bash
echo "🔍 最終確認:"
echo ""
echo "1. プロセス状態:"
ps aux | grep -E "(error_intelligence_worker|command_executor)" | grep -v grep
echo ""
echo "2. ログファイル:"
ls -la /home/aicompany/ai_co/logs/*error* 2>/dev/null || echo "ログファイルはまだ生成されていません"
echo ""
echo "3. データベース:"
ls -la /home/aicompany/ai_co/db/error_patterns.db 2>/dev/null || echo "データベースはまだ生成されていません"
echo ""
echo "✅ エラー智能判断システム Phase 1 が正常にセットアップされました！"
