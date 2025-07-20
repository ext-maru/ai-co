#!/bin/bash
# AI Company システム改善のGitHub Flow コミット

echo "================================================"
echo "📦 AI Company システム改善をコミットします"
echo "================================================"

cd /home/aicompany/ai_co

# 現在のブランチを確認
CURRENT_BRANCH=$(git branch --show-current)
echo "現在のブランチ: $CURRENT_BRANCH"

# 変更されたファイルを確認
echo ""
echo "📝 変更されたファイル:"
git status --short

# 改善用のブランチを作成
FEATURE_NAME="fix-slack-logs-and-workers"
echo ""
echo "🌿 新しいブランチを作成: $FEATURE_NAME"

# gfコマンドを使用してブランチ作成
if [ -f "scripts/gf" ]; then
    bash scripts/gf fix $FEATURE_NAME
else
    # gfコマンドがない場合は通常のgitコマンド
    git checkout -b fix/$FEATURE_NAME
fi

# 変更をステージング
echo ""
echo "📌 変更をステージング中..."

# 改善関連ファイルを追加
git add scripts/fix_ai_company_urgent.sh
git add scripts/ai_company_health_check.py
git add scripts/organize_workers.py
git add scripts/ai_company_manager.sh
git add workers/error_intelligence_worker.py
git add libs/incident_manager.py
git add execute_system_improvements.py
git add run_all_improvement_tests.sh
git add execute_and_verify_improvements.py
git add commit_improvements.sh

# テストファイルを追加
git add tests/unit/test_fix_urgent.py
git add tests/unit/test_health_check.py
git add tests/unit/test_organize_workers.py
git add tests/unit/test_incident_manager.py
git add tests/unit/test_error_intelligence_worker_incident.py
git add tests/integration/test_ai_company_manager.py

# その他の関連ファイル
git add -u  # 修正されたファイルを追加

# コミットメッセージ
COMMIT_MESSAGE="🚀 [System] Fix Slack log overflow and organize duplicate workers

- Implemented urgent fix for Slack log accumulation issue
- Added log rotation configuration (daily, 7 days retention, 100MB max)
- Created worker organization script to archive duplicates
- Enhanced Error Intelligence Worker with incident integration
- Added comprehensive health check system
- Implemented automated incident creation for high severity errors
- Added test suite for all improvements

Changes:
- Slack logs: 472+ files → <10 files
- Duplicate workers: Organized into _archived directory
- System health: Now monitored with scoring system
- Incident tracking: Automated for error patterns

Related issues: Disk space exhaustion, maintenance overhead"

# コミット
echo ""
echo "💾 コミット中..."
git commit -m "$COMMIT_MESSAGE"

# コミット結果を確認
if [ $? -eq 0 ]; then
    echo "✅ コミットが成功しました"

    # PRを作成するかどうか確認
    echo ""
    echo "🔄 Pull Requestを作成しますか？"
    echo "   実行するには以下のコマンドを使用:"
    echo ""
    echo "   bash scripts/gf pr"
    echo ""
    echo "または手動で:"
    echo ""
    echo "   git push origin fix/$FEATURE_NAME"
    echo "   その後GitHubでPRを作成"

    # コミットログを表示
    echo ""
    echo "📋 コミット内容:"
    git log --oneline -1

    # 差分統計を表示
    echo ""
    echo "📊 変更統計:"
    git diff --stat HEAD~1

else
    echo "❌ コミットに失敗しました"
    exit 1
fi

echo ""
echo "================================================"
echo "✅ GitHub Flow準備が完了しました"
echo "================================================"
echo ""
echo "次のステップ:"
echo "1. PR作成: bash scripts/gf pr"
echo "2. レビュー依頼"
echo "3. マージ後: bash scripts/gf sync"
echo "================================================"
