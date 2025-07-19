#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🚀 AI Company ai-send拡張実装を開始..."
echo "=================================="
date

# 実装スクリプトの実行
if [ -f implement_ai_send_extension.sh ]; then
    chmod +x implement_ai_send_extension.sh
    echo "📝 実装スクリプトを実行中..."
    ./implement_ai_send_extension.sh
    echo ""
    echo "✅ 実装スクリプトの実行完了"
else
    echo "❌ implement_ai_send_extension.sh が見つかりません"
    exit 1
fi

# 結果確認
echo ""
echo "🔍 実装結果:"
echo "============"

# タスクタイプ設定ファイル
if [ -f config/task_types.json ]; then
    echo "✅ タスクタイプ設定ファイル: 作成成功"
    echo ""
    echo "📋 登録されたタスクタイプ:"
    python3 -c "import json; data=json.load(open('config/task_types.json')); [print(f'  - {k}: {v[\"description\"]}') for k,v in data['task_types'].items()]"
else
    echo "❌ タスクタイプ設定ファイル: 作成失敗"
fi

# テンプレート確認
echo ""
if [ -d templates/task_types ]; then
    count=$(ls templates/task_types/*.yaml 2>/dev/null | wc -l)
    echo "✅ タスクテンプレート: $count 個作成"
else
    echo "❌ タスクテンプレートディレクトリが見つかりません"
fi

# ドキュメント確認
if [ -f docs/AI_SEND_EXTENDED_GUIDE.md ]; then
    echo "✅ 拡張ガイド: 作成済み"
else
    echo "❌ 拡張ガイド: 未作成"
fi

# Slack通知
echo ""
echo "📢 Slack通知を送信..."
python3 -c "
try:
    from libs.slack_notifier import SlackNotifier
    notifier = SlackNotifier()
    message = '''🎉 ai-send拡張版の実装が完了しました！

📋 追加されたタスクタイプ:
• test - テスト作成・実行
• fix - バグ修正・問題解決
• deploy - デプロイ・リリース
• review - コードレビュー
• docs - ドキュメント生成
• optimize - パフォーマンス最適化
• security - セキュリティ監査
• monitor - システム監視
• backup - バックアップ作業

🚀 使用例:
\`\`\`
ai-send 'テストを作成' test
ai-send 'バグを修正' fix --priority 9
ai-send --list-types
\`\`\`
'''
    notifier.send_message(message)
    print('✅ Slack通知を送信しました')
except Exception as e:
    print(f'⚠️ Slack通知エラー: {e}')
"

echo ""
echo "🎉 実装プロセス完了！"
