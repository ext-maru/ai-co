#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "📊 AI Command Executor実行確認"
echo "=============================="

# 実装スクリプトの実行
echo "🚀 implement_ai_send_extension.sh を実行中..."
chmod +x implement_ai_send_extension.sh
./implement_ai_send_extension.sh

# 実行結果の確認
echo ""
echo "🔍 実行結果:"
if [ -f config/task_types.json ]; then
    echo "✅ タスクタイプ設定ファイル作成成功！"
    echo ""
    echo "📋 登録されたタスクタイプ:"
    python3 -c "import json; data=json.load(open('config/task_types.json')); print('\n'.join(f'{k}: {v[\"description\"]}' for k,v in data['task_types'].items()))"

    # Slack通知
    echo ""
    echo "📢 Slack通知送信中..."
    python3 -c "from libs.slack_notifier import SlackNotifier; notifier=SlackNotifier(); notifier.send_message('🎉 ai-send拡張の実装が完了しました！\n\n追加されたタスクタイプ: test, fix, deploy, review, docs, optimize, security, monitor, backup\n\n使用例: ai-send \'テストを作成\' test')"
    echo "✅ 完了！"
else
    echo "❌ タスクタイプ設定ファイルの作成に失敗しました"
fi
