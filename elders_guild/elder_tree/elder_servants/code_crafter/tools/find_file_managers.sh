#!/bin/bash
# ファイル管理関連のコンポーネントを検索

echo "🔍 ファイル管理関連コンポーネントの検索"
echo "=================================================="

# 1. ファイル名検索
echo ""
echo "📁 'file' を含むPythonファイル:"
echo "------------------------"
find . -name "*.py" -type f | grep -i file | grep -v __pycache__ | grep -v ".bak" | sort

# 2. manager を含むファイル
echo ""
echo "📁 'manager' を含むPythonファイル:"
echo "------------------------"
find . -name "*manager*.py" -type f | grep -v __pycache__ | grep -v ".bak" | sort

# 3. outputディレクトリの詳細
echo ""
echo "📁 output/code ディレクトリの最新ファイル（詳細）:"
echo "------------------------"
ls -la output/code/*/  2>/dev/null | head -20 || echo "なし"

# 4. 自己進化システムが配置した可能性のあるファイル
echo ""
echo "📁 最近作成されたワーカー/マネージャー:"
echo "------------------------"
echo "Workers:"
find workers -name "*.py" -type f -mtime -7 | grep -v __pycache__ | sort
echo ""
echo "Libs:"
find libs -name "*.py" -type f -mtime -7 | grep -v __pycache__ | sort

# 5. ファイル管理タスクの検索
echo ""
echo "📋 ファイル管理関連のタスク履歴:"
echo "------------------------"
if [ -f "db/task_history.db" ]; then
    sqlite3 db/task_history.db "SELECT task_id, prompt, created_at FROM task_history WHERE prompt LIKE '%file%manag%' OR prompt LIKE '%ファイル%管理%' ORDER BY created_at DESC LIMIT 5;" 2>/dev/null || echo "データベースアクセスエラー"
else
    echo "task_history.db が見つかりません"
fi

echo ""
echo "=================================================="
echo "💡 ヒント:"
echo "  - 自己進化システムは output/ にファイルを生成します"
echo "  - その後 PMWorker が適切な場所に配置します"
echo "  - もし file_manager.py を作成したタスクがあれば、"
echo "    output/code/タスクID/ 内に存在するはずです"
