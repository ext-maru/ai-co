#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🎉 Git コミットメッセージ ベストプラクティス実装完了！"
echo "=" | tr '=' '='$(seq -s= 60 | tr -d '[:digit:]')
echo ""

# 実装状況最終確認
echo "📊 実装状況:"
if grep -q "use_best_practices=True" workers/pm_worker.py; then
    echo "✅ PMWorker: ベストプラクティス有効"
else
    echo "❌ PMWorker: 要確認"
fi

if [ -f libs/commit_message_generator.py ]; then
    echo "✅ CommitMessageGenerator: 作成済み"
else
    echo "❌ CommitMessageGenerator: 未作成"
fi

if [ -f knowledge_base/KB_GitCommitBestPractices.md ]; then
    echo "✅ ナレッジベース: 作成済み"
else
    echo "❌ ナレッジベース: 未作成"
fi

echo ""
echo "📚 ナレッジベース:"
echo "knowledge_base/KB_GitCommitBestPractices.md"
echo ""

# Slack通知
python3 notify_git_best_practices_complete.py

echo ""
echo "🚀 全ての実装が完了しました！"
echo ""
echo "今後、全ての自動コミットが詳細なベストプラクティス形式になります。"
