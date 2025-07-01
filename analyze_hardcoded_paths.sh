#!/bin/bash
# ハードコーディングされたパスを分析

cd /root/ai_co

echo "🔍 ハードコーディングされたパスを分析中..."
echo "==========================================="

# 1. /root/ai_co を含むファイルを検索
echo ""
echo "📋 /root/ai_co を含むファイル:"
echo "--------------------------------"
grep -r "/root/ai_co" . \
    --exclude-dir=.git \
    --exclude-dir=venv \
    --exclude-dir=__pycache__ \
    --exclude="*.log" \
    --exclude="*.pyc" | \
    cut -d: -f1 | sort | uniq | while read file; do
    count=$(grep -c "/root/ai_co" "$file")
    echo "  $file ($count箇所)"
done

# 2. 種類別に分類
echo ""
echo "📊 ファイルタイプ別統計:"
echo "------------------------"
echo "Pythonファイル:"
grep -l "/root/ai_co" workers/*.py libs/*.py scripts/*.py 2>/dev/null | wc -l

echo "シェルスクリプト:"
grep -l "/root/ai_co" scripts/*.sh 2>/dev/null | wc -l

echo "設定ファイル:"
grep -l "/root/ai_co" config/*.conf 2>/dev/null | wc -l

# 3. 詳細分析
echo ""
echo "📝 詳細な使用パターン:"
echo "----------------------"

# Pythonでの使用
echo ""
echo "【Python内での使用】"
grep -h "import sys" -A1 workers/*.py libs/*.py | grep "/root/ai_co" | head -3

# logging設定
echo ""
echo "【ログファイルパス】"
grep -h "FileHandler.*/" workers/*.py libs/*.py 2>/dev/null | head -3

# その他の絶対パス
echo ""
echo "【その他の絶対パス】"
grep -h "Path.*/" workers/*.py libs/*.py | grep -v "__file__" | head -3

