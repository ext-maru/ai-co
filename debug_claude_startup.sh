#!/bin/bash
# Claude 起動のデバッグスクリプト

echo "🔍 Claude 起動デバッグ"
echo "===================="

echo -e "\n1. 環境変数:"
env | grep -E "(CLAUDE|ANTHROPIC)" | grep -v API_KEY

echo -e "\n2. Claude 実行ファイル:"
which claude
ls -la $(which claude)

echo -e "\n3. 実行中の Claude プロセス:"
ps aux | grep claude | grep -v grep | wc -l

echo -e "\n4. Claude を直接実行（引数なし）:"
echo "実行コマンド: claude"

# 環境変数をクリアして実行
echo -e "\n5. 環境変数をクリアして実行:"
echo "実行コマンド: env -i PATH=$PATH HOME=$HOME claude"

echo -e "\n💡 解決案:"
echo "- CLAUDE_CODE_ENTRYPOINT 環境変数が問題の可能性"
echo "- または別の Claude プロセスが干渉している可能性"