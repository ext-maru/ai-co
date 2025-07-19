#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🎯 ベストプラクティス統合の最終確認"
echo "=====================================\n"

echo "1️⃣ CommitMessageGenerator"
if [ -f "libs/commit_message_generator.py" ]; then
    echo "   ✅ 存在確認OK"
    python3 -c "from libs.commit_message_generator import CommitMessageGenerator; print('   ✅ インポート可能')" 2>/dev/null || echo "   ❌ インポートエラー"
else
    echo "   ❌ ファイルが見つかりません"
fi

echo ""
echo "2️⃣ GitFlowManager統合"
if grep -q "use_best_practices" libs/git_flow_manager.py 2>/dev/null; then
    echo "   ✅ use_best_practicesパラメータ実装済み"
else
    echo "   ❌ use_best_practicesパラメータ未実装"
fi

echo ""
echo "3️⃣ ai-gitコマンド新機能"
for cmd in "preview" "analyze" "changelog" "best-practices"; do
    if grep -q "$cmd" scripts/ai-git 2>/dev/null; then
        echo "   ✅ ai-git $cmd"
    else
        echo "   ❌ ai-git $cmd"
    fi
done

echo ""
echo "4️⃣ 設定ファイル"
if [ -f "config/commit_best_practices.json" ]; then
    echo "   ✅ commit_best_practices.json"
fi
if [ -f ".gitmessage" ]; then
    echo "   ✅ .gitmessageテンプレート"
fi

echo ""
echo "5️⃣ PMWorker統合 (最重要)"
if grep -q "use_best_practices=True" workers/pm_worker.py 2>/dev/null; then
    echo "   ✅ PMWorkerがベストプラクティスを使用"
    echo "   場所: $(grep -n 'use_best_practices=True' workers/pm_worker.py | head -1)"
else
    echo "   ❌ PMWorkerが未対応"
    echo "   現在: $(grep -n 'commit_changes(commit_message, new_files)' workers/pm_worker.py | head -1)"
fi

echo ""
echo "====================================="
echo "📊 統合サマリー:"

if grep -q "use_best_practices=True" workers/pm_worker.py 2>/dev/null; then
    echo ""
    echo "🎉 すべてのコンポーネントが統合されました！"
    echo ""
    echo "📝 利用可能なコマンド:"
    echo "   • ai-git commit --preview  # プレビュー"
    echo "   • ai-git analyze          # 変更分析"
    echo "   • ai-git best-practices   # ガイドライン表示"
    echo "   • ai-git changelog        # CHANGELOG生成"
    echo ""
    echo "🚀 次のステップ: ai-restart でシステム再起動"
else
    echo ""
    echo "⚠️  PMWorkerがまだ未対応です"
    echo "   → final_pm_fix_simpleコマンドを実行してください"
fi
