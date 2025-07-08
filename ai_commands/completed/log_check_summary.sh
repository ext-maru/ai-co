#!/bin/bash
# ログ確認実行状況サマリー
cd /home/aicompany/ai_co

echo "📊 ログ確認実行状況"
echo "=================="
echo "時刻: $(date)"
echo ""

# 実行中のコマンド数
echo "AI Command Executor:"
ls -1 ai_commands/pending/*.sh 2>/dev/null | wc -l | xargs -I {} echo "  保留中: {}件"
ls -1 ai_commands/running/*.sh 2>/dev/null | wc -l | xargs -I {} echo "  実行中: {}件"

echo ""
echo "最新実行コマンド:"
ls -lt ai_commands/logs/*.log | head -5 | awk '{print "  " $9}'

echo ""
echo "詳細はログファイルを確認してください"
