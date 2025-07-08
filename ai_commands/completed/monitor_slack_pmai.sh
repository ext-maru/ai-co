#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

# モニタリングをバックグラウンドで10秒間実行
timeout 10 python3 monitor_slack_pmai.py > monitor_result.txt 2>&1 &

# 5秒待機
sleep 5

# 結果表示
echo "=== モニタリング結果 ==="
cat monitor_result.txt | head -30
