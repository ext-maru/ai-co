#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "📊 PMWorkerベストプラクティス対応状況確認"
echo "=====================================\n"

echo "1. マーカー確認:"
if grep -q "BEST_PRACTICES_PATCH_APPLIED" workers/pm_worker.py; then
    echo "   ✅ BEST_PRACTICES_PATCH_APPLIED マーカー存在"
else
    echo "   ❌ BEST_PRACTICES_PATCH_APPLIED マーカーなし"
fi

echo ""
echo "2. commit_changes呼び出し確認:"
echo "   現在の実装:"
grep -B2 -A2 "commit_changes" workers/pm_worker.py | grep -v "^--$"

echo ""
echo "3. use_best_practices確認:"
if grep -q "use_best_practices=True" workers/pm_worker.py; then
    echo "   ✅ use_best_practices=True が設定されています"
    echo "   場所:"
    grep -n "use_best_practices=True" workers/pm_worker.py
else
    echo "   ❌ use_best_practices=True が設定されていません"
fi

echo ""
echo "=====================================" 
echo "📝 今後のコミットメッセージ:"
echo "   - Conventional Commits形式"
echo "   - 詳細な説明付き"
echo "   - Breaking changes記載"
echo "   - タスクID参照"
echo ""
echo "🚀 完全なベストプラクティス対応のためには:"
echo "   1. ai-restart でワーカー再起動"
echo "   2. 新しいタスクでテスト"