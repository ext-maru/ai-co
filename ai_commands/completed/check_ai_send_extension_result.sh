#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "📊 ai-send拡張実装結果の確認"
echo "=============================="
echo ""

# 1. タスクタイプ設定ファイルの確認
echo "📋 タスクタイプ設定ファイル:"
if [ -f config/task_types.json ]; then
    echo "  ✅ 存在します"
    echo ""
    echo "  登録されたタスクタイプ:"
    python3 -c "
import json
with open('config/task_types.json') as f:
    data = json.load(f)
    for k, v in data['task_types'].items():
        print(f'    - {k:<10} : {v[\"description\"]} (優先度: {v[\"default_priority\"]})')"
else
    echo "  ❌ まだ作成されていません"
fi

# 2. ai_send.pyの確認
echo ""
echo "📝 ai_send.pyの状態:"
if grep -q 'test.*fix.*deploy' commands/ai_send.py 2>/dev/null; then
    echo "  ✅ 拡張済み（新しいタスクタイプが含まれています）"
else
    echo "  ⚠️ まだ拡張されていません"
    echo "  現在のタスクタイプ:"
    grep "choices=" commands/ai_send.py | head -1
fi

# 3. テンプレートの確認
echo ""
echo "📁 タスクテンプレート:"
if [ -d templates/task_types ]; then
    count=$(ls templates/task_types/*.yaml 2>/dev/null | wc -l)
    echo "  ✅ $count 個のテンプレート作成済み"
    ls templates/task_types/*.yaml 2>/dev/null | while read file; do
        echo "    - $(basename $file)"
    done
else
    echo "  ❌ テンプレートディレクトリが見つかりません"
fi

# 4. ドキュメントの確認
echo ""
echo "📚 ドキュメント:"
if [ -f docs/AI_SEND_EXTENDED_GUIDE.md ]; then
    echo "  ✅ AI_SEND_EXTENDED_GUIDE.md: 作成済み"
else
    echo "  ❌ 拡張ガイド: 未作成"
fi

# 5. 使用方法の表示
echo ""
echo "🚀 使用方法:"
echo "  ai-send 'タスクの説明' [タスクタイプ]"
echo ""
echo "📋 タスクタイプ一覧:"
echo "  ai-send --list-types"
echo ""
echo "🎯 使用例:"
echo "  ai-send 'テストを作成' test"
echo "  ai-send 'バグを修正' fix --priority 9"
echo "  ai-send 'セキュリティチェック' security"
