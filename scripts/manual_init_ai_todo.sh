#!/bin/bash
# AI Todoシステムの手動初期化と結果確認

echo "🚀 AI Todoシステムを手動で初期化します"

cd /home/aicompany/ai_co
source venv/bin/activate

# 初期化スクリプトを直接実行
echo "実行中: init_ai_todo_system.py"
python3 scripts/init_ai_todo_system.py

# 少し待機
sleep 2

# 結果確認
echo -e "\n📊 実行結果確認:"

# ai_todoディレクトリ確認
if [ -d "ai_todo" ]; then
    echo "✅ ai_todoディレクトリが作成されました:"
    ls -la ai_todo/
fi

# 知識ベース確認
if [ -d "knowledge_base/ai_learning" ]; then
    echo -e "\n✅ 知識ベースディレクトリが作成されました:"
    ls -la knowledge_base/ai_learning/
fi

# ログ確認
echo -e "\n📋 AI Growth Todoログ:"
if [ -f "logs/ai_growth_todo.log" ]; then
    tail -10 logs/ai_growth_todo.log
else
    echo "ログファイルはまだありません"
fi

# pendingコマンド確認
echo -e "\n📁 Pending状態のAI Todoコマンド:"
ls -la ai_commands/pending/*ai*todo* 2>/dev/null || echo "なし"

echo -e "\n✨ 初期化プロセス完了！"
