#!/bin/bash
# AI Company コマンドインストールスクリプト

echo "🔧 AI Company コマンドをインストール中..."

# スクリプトに実行権限を付与
chmod +x /home/aicompany/ai_co/scripts/ai_restart_new.sh
chmod +x /home/aicompany/ai_co/scripts/ai_start_new.sh
chmod +x /home/aicompany/ai_co/scripts/ai_stop_new.sh
chmod +x /home/aicompany/ai_co/scripts/start_company.sh

# /usr/local/binにコピー
sudo cp /home/aicompany/ai_co/scripts/ai_restart_new.sh /usr/local/bin/ai-restart
sudo cp /home/aicompany/ai_co/scripts/ai_start_new.sh /usr/local/bin/ai-start
sudo cp /home/aicompany/ai_co/scripts/ai_stop_new.sh /usr/local/bin/ai-stop

# 実行権限を再度確認
sudo chmod +x /usr/local/bin/ai-restart
sudo chmod +x /usr/local/bin/ai-start
sudo chmod +x /usr/local/bin/ai-stop

echo "✅ インストール完了！"
echo ""
echo "システムを再起動します..."
ai-restart
