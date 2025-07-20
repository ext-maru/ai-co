#!/bin/bash
# AI Company 徹底クリーンアップ＆Git最適化スクリプト

cd /root/ai_co

echo "🧹 AI Company 徹底クリーンアップ開始..."
echo "======================================="

# 1. まず.gitignoreを最適化
echo "📝 .gitignore を更新..."
cat << 'GITIGNORE' > .gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
venv/
.env

# Logs - 完全に無視
logs/
*.log

# Database
*.db
*.sqlite3

# IDE
.vscode/
.idea/

# Output files - 完全に無視
output/

# Credentials
credentials/
*.json

# Temporary files
*.tmp
*.bak
*.swp
*~
.DS_Store

# Backup files
*.backup_*
*.backup
*.orig

# Config with secrets
config/slack.conf
config/github.conf

# Test files
test_*.py
test_*.sh

# Session files
*.session
GITIGNORE

echo "✅ .gitignore 更新完了"

# 2. バックアップファイルを徹底削除
echo "💾 全バックアップファイルを検索・削除..."
find . -type f \( \
    -name "*.backup_*" -o \
    -name "*.backup" -o \
    -name "*.bak" -o \
    -name "*.orig" -o \
    -name "*~" -o \
    -name "*.old" \
\) -print -delete 2>/dev/null || true
echo "✅ バックアップファイル削除完了"

# 3. Git から output と logs を完全に削除
echo "🔧 Git から output/logs を削除..."
git rm -r --cached output/ 2>/dev/null || true
git rm -r --cached logs/ 2>/dev/null || true
git rm --cached *.log 2>/dev/null || true
echo "✅ Git追跡から削除"

# 4. output/logs の中身をクリア
echo "📁 output/logs ディレクトリをクリア..."
rm -rf output/*
rm -rf logs/*
# ディレクトリは残す
mkdir -p output/code output/general
mkdir -p logs
touch logs/.gitkeep
touch output/.gitkeep
echo "✅ ディレクトリクリア完了"

# 5. Python キャッシュを削除
echo "🐍 Python キャッシュを削除..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
echo "✅ Python キャッシュ削除完了"

# 6. 一時ファイルとテストファイルを削除
echo "🗑️ 一時ファイル・テストファイルを削除..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.swp" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true
# ルートディレクトリのtest_*.pyを削除（scripts/内は残す）
find . -maxdepth 1 -name "test_*.py" -delete 2>/dev/null || true
echo "✅ 一時ファイル削除完了"

# 7. 重複・不要なワーカーバックアップを確認
echo "🔍 重複ファイルを確認..."
echo "workers/内のバックアップ:"
ls -la workers/*.backup* 2>/dev/null | wc -l | xargs echo "  件"
echo "libs/内のバックアップ:"
ls -la libs/*.backup* 2>/dev/null | wc -l | xargs echo "  件"

# 8. Git ステータス確認
echo ""
echo "📊 現在のGit状態:"
git status --short

# 9. コミット作成
echo ""
echo "💾 クリーンアップをコミット..."
git add .gitignore
git add -A
git commit -m "🧹 大規模クリーンアップ: バックアップ削除、.gitignore最適化、output/logs除外" || echo "変更なし"

# 10. ディスク使用量確認
echo ""
echo "💽 クリーンアップ後のディスク使用量:"
echo "--------------------------------"
du -sh . | awk '{print "合計: " $1}'
du -sh workers/ libs/ scripts/ config/ 2>/dev/null | sort -h

# 11. Git で追跡されているファイル数
echo ""
echo "📈 統計:"
echo "Git追跡ファイル数: $(git ls-files | wc -l)"
echo "Pythonファイル数: $(find . -name "*.py" -not -path "./venv/*" -not -path "./__pycache__/*" | wc -l)"
echo "シェルスクリプト数: $(find . -name "*.sh" | wc -l)"

# 12. 最終確認
echo ""
echo "🎯 追加の推奨アクション:"
echo "--------------------------------"
echo "1. データベースも初期化: rm -f *.db && python3 scripts/setup_database.sh"
echo "2. 設定ファイルバックアップ: tar -czf config_backup.tar.gz config/"
echo "3. Git履歴の最適化: git gc --aggressive"
echo "4. 大きなファイル確認: find . -size +1M -type f"

echo ""
echo "🎉 徹底クリーンアップ完了！"
echo ""
echo "⚠️ 注意: output/とlogs/はGitから除外されました"
echo "今後これらのディレクトリ内のファイルはGitに含まれません"
