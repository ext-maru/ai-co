#!/bin/bash
# AI Company プロジェクトクリーンアップスクリプト

cd /root/ai_co

echo "🧹 AI Company クリーンアップ開始..."
echo "================================"

# 1. output ディレクトリの中身を削除（ディレクトリ自体は残す）
echo "📁 output ディレクトリをクリーンアップ..."
if [ -d "output" ]; then
    find output -mindepth 1 -delete 2>/dev/null || true
    echo "✅ output ディレクトリをクリア"
else
    mkdir -p output
    echo "✅ output ディレクトリを作成"
fi

# 2. logs ディレクトリの中身を削除（ディレクトリ自体は残す）
echo "📋 logs ディレクトリをクリーンアップ..."
if [ -d "logs" ]; then
    find logs -name "*.log" -delete 2>/dev/null || true
    echo "✅ ログファイルを削除"
else
    mkdir -p logs
    echo "✅ logs ディレクトリを作成"
fi

# 3. バックアップファイルを削除
echo "💾 バックアップファイルを削除..."
find . -name "*.backup_*" -type f -delete 2>/dev/null || true
find . -name "*.bak" -type f -delete 2>/dev/null || true
echo "✅ バックアップファイルを削除"

# 4. Python キャッシュを削除
echo "🐍 Python キャッシュを削除..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
echo "✅ Python キャッシュを削除"

# 5. 一時ファイルを削除
echo "🗑️ 一時ファイルを削除..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.swp" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true
echo "✅ 一時ファイルを削除"

# 6. Git から削除されたファイルを反映
echo "🔧 Git クリーンアップ..."
# Gitで追跡されているが削除されたファイルをステージング
git add -u 2>/dev/null || true

# 削除されたファイルがある場合はコミット
if git diff --cached --exit-code > /dev/null 2>&1; then
    echo "✅ Git: 変更なし"
else
    git commit -m "🧹 プロジェクトクリーンアップ: 不要ファイル削除" 2>/dev/null || true
    echo "✅ Git: クリーンアップコミット作成"
fi

# 7. Git で追跡されていない不要ファイルを表示（削除はしない）
echo ""
echo "📌 Git で追跡されていないファイル:"
git status --porcelain 2>/dev/null | grep '^??' | cut -c4- | head -10 || true

# 8. ディスク使用量を表示
echo ""
echo "💾 ディスク使用量:"
du -sh . 2>/dev/null || true
du -sh output logs 2>/dev/null || true

# 9. .gitignore の確認
echo ""
echo "📝 .gitignore 推奨追加項目:"
echo "================================"
cat << 'GITIGNORE'
# 追加推奨（もし含まれていない場合）
credentials/
*.sqlite3
.env
.vscode/
.idea/
test_*.py
GITIGNORE

echo ""
echo "🎉 クリーンアップ完了！"
echo ""
echo "追加オプション:"
echo "- 強制的にGit未追跡ファイルも削除: git clean -fd"
echo "- データベースも削除: rm -f *.db"
echo "- 設定ファイルのバックアップ: cp -r config config.backup"

