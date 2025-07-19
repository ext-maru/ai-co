#!/bin/bash
#!/bin/bash
# Slack通知改善の簡単な動作確認

cd /home/aicompany/ai_co

echo "=== Slack通知フォーマット改善 動作確認 ==="
echo

# SlackNotifierの変更確認
echo "1. SlackNotifierの確認:"
if grep -q "send_task_completion_simple" libs/slack_notifier.py; then
    echo "  ✅ send_task_completion_simple メソッドが追加されています"
else
    echo "  ❌ send_task_completion_simple メソッドが見つかりません"
fi

# 脳みそ絵文字の確認
echo
echo "2. 脳みそ絵文字の確認:"
if grep -q "🧠" libs/slack_notifier.py; then
    echo "  ⚠️  脳みそ絵文字がまだ残っています"
else
    echo "  ✅ 脳みそ絵文字は削除されています"
fi

# ResultWorkerの確認
echo
echo "3. ResultWorkerの確認:"
if grep -q "1000" workers/result_worker.py; then
    echo "  ✅ 応答表示が拡張されています（1000文字）"
else
    echo "  ⚠️  応答表示の拡張が確認できません"
fi

# ワーカープロセスの確認
echo
echo "4. 現在のワーカー状態:"
ps aux | grep -E "(task_worker|result_worker)" | grep -v grep || echo "  ワーカーが実行されていません"

# ドキュメントの確認
echo
echo "5. ドキュメント:"
if [ -f "docs/SLACK_FORMAT_IMPROVEMENT.md" ]; then
    echo "  ✅ 改善ガイドが作成されています"
    echo "  📄 docs/SLACK_FORMAT_IMPROVEMENT.md"
else
    echo "  ❌ 改善ガイドが見つかりません"
fi

echo
echo "=== 確認完了 ==="
echo
echo "次のステップ:"
echo "1. ワーカーを再起動（restart_slack_workers.json が自動実行されます）"
echo "2. テスト通知を送信（test_slack_format.json が自動実行されます）"
echo "3. 実際のタスクで動作を確認"
echo
echo "[$(date)] Slack通知フォーマット改善確認完了" >> logs/command_executor.log
