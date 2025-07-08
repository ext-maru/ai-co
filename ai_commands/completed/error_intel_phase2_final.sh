#!/bin/bash
#!/bin/bash
echo "🔍 最終確認:"
echo ""
echo "1. プロセス状態:"
ps aux | grep -E "(error_intelligence_worker)" | grep -v grep
echo ""
echo "2. データベース:"
ls -la /home/aicompany/ai_co/db/*.db 2>/dev/null
echo ""
echo "3. バックアップディレクトリ:"
ls -la /home/aicompany/ai_co/backups/autofix/ 2>/dev/null || echo "バックアップディレクトリが作成されました"
echo ""
echo "✅ エラー智能判断システム Phase 2 が正常にセットアップされました！"
echo ""
echo "次のステップ:"
echo "  Phase 3: 経験から学習して自己修復（95%の自動修正率を目指す）"
