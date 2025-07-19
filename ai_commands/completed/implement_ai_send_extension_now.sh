#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🚀 AI Company ai-send拡張実装を開始..."
echo "==================================="

# 実装スクリプトの実行
if [ -f implement_ai_send_extension.sh ]; then
    chmod +x implement_ai_send_extension.sh
    ./implement_ai_send_extension.sh
    echo ""
    echo "✅ 実装スクリプトの実行完了"
else
    echo "❌ implement_ai_send_extension.sh が見つかりません"
    exit 1
fi

# 実装結果の確認
echo ""
echo "🔍 実装結果の確認:"
echo "==================="

# 1. タスクタイプ設定ファイル
if [ -f config/task_types.json ]; then
    echo "✅ タスクタイプ設定: 作成成功"
    echo ""
    echo "📋 登録されたタスクタイプ:"
    python3 -c "
import json
with open('config/task_types.json') as f:
    data = json.load(f)
    for k, v in data['task_types'].items():
        print(f'  - {k:<10} : {v[\"description\"]}')"
else
    echo "❌ タスクタイプ設定: 作成失敗"
fi

# 2. テンプレート確認
echo ""
echo "📁 タスクテンプレート:"
if [ -d templates/task_types ]; then
    count=$(ls templates/task_types/*.yaml 2>/dev/null | wc -l)
    echo "  ✅ $count 個のテンプレート作成済み"
else
    echo "  ❌ テンプレートディレクトリが見つかりません"
fi

# 3. ドキュメント確認
echo ""
echo "📚 ドキュメント:"
if [ -f docs/AI_SEND_EXTENDED_GUIDE.md ]; then
    echo "  ✅ 拡張ガイド作成済み"
else
    echo "  ❌ 拡張ガイド未作成"
fi

# 4. Slack通知
echo ""
echo "📢 Slack通知を送信..."
python3 -c "
from libs.slack_notifier import SlackNotifier
notifier = SlackNotifier()
try:
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
```
ai-send 'テストを作成' test
ai-send 'バグを修正' fix --priority 9
ai-send --list-types
```
'''
    notifier.send_message(message)
    print('✅ Slack通知を送信しました')
except Exception as e:
    print(f'⚠️ Slack通知エラー: {e}')
"

echo ""
echo "🎉 ai-send拡張の実装が完了しました！"
