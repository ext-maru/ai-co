#!/bin/bash
#!/bin/bash
echo "📊 ai-send拡張実装状況"
echo "======================="
echo ""
if [ -f /home/aicompany/ai_co/config/task_types.json ]; then
    echo "✅ 実装完了！"
    echo ""
    echo "📋 登録されたタスクタイプ:"
    cd /home/aicompany/ai_co
    python3 -c "import json; data=json.load(open('config/task_types.json')); print('\n'.join(f'  - {k}: {v[\"description\"]}' for k,v in data['task_types'].items()))"
    echo ""
    echo "🚀 使用例:"
    echo "  ai-send 'テストを作成' test"
    echo "  ai-send 'バグを修正' fix"
    echo "  ai-send --list-types"
else
    echo "❌ まだ実装されていません"
    echo ""
    echo "📝 以下のコマンドで手動実装してください:"
    echo "  cd /home/aicompany/ai_co"
    echo "  chmod +x implement_ai_send_extension.sh"
    echo "  ./implement_ai_send_extension.sh"
fi
