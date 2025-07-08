#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "📊 ai-send拡張の最終確認を実行..."
echo "=================================="

# 最終確認スクリプトを実行
python3 check_ai_send_final_results.py

# AI Command Executorのログも確認
echo ""
echo "📝 最新のAI Command Executorログ:"
echo "==================================="
if [ -d ai_commands/logs ]; then
    # 最新5個のログファイル名を表示
    ls -t ai_commands/logs/*.log 2>/dev/null | head -5 | while read log; do
        echo "  - $(basename $log)"
    done
    
    # ai_send関連のログを探す
    echo ""
    echo "🔍 ai-send関連のログ:"
    ls ai_commands/logs/*ai_send*.log ai_commands/logs/*implement*.log 2>/dev/null | while read log; do
        echo "  ✅ $(basename $log)"
    done || echo "  ❌ 関連ログが見つかりません"
fi

echo ""
echo "✅ 確認完了"