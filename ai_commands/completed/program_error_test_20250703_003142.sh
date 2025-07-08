#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "=== AI Program Execution ===" | tee /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_error_test.log
echo "Task: error_test" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_error_test.log
echo "Description: 失敗時の動作確認" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_error_test.log
echo "Started: $(date)" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_error_test.log
echo "============================" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_error_test.log

python3 /home/aicompany/ai_co/ai_programs/inbox/error_test.py 2>&1 | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_error_test.log
EXIT_CODE=${PIPESTATUS[0]}

echo "============================" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_error_test.log
echo "Completed: $(date)" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_error_test.log
echo "Exit Code: $EXIT_CODE" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_error_test.log

# アーカイブまたは失敗フォルダへ移動
if [ $EXIT_CODE -eq 0 ]; then
    ARCHIVE_DIR="/home/aicompany/ai_co/ai_programs/archive/$(date +%Y-%m-%d)"
    mkdir -p "$ARCHIVE_DIR"
    mv /home/aicompany/ai_co/ai_programs/inbox/error_test.py "$ARCHIVE_DIR/error_test_20250703_003142.py"
    echo "Archived to: $ARCHIVE_DIR" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_error_test.log
else
    mv /home/aicompany/ai_co/ai_programs/inbox/error_test.py "/home/aicompany/ai_co/ai_programs/failed/error_test_20250703_003142.py"
    echo "Moved to failed directory" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_error_test.log
fi

# Slack通知
if [ $EXIT_CODE -eq 0 ]; then
    EMOJI="✅"
    STATUS="成功"
else
    EMOJI="❌"
    STATUS="失敗"
fi

# Slack通知用のPythonスクリプト作成
cat > /tmp/notify_program_result.py << 'EOF'
import sys
sys.path.insert(0, "/home/aicompany/ai_co")
from libs.slack_notifier import SlackNotifier

task_name = "error_test"
exit_code = $EXIT_CODE
status = "$STATUS"
emoji = "$EMOJI"

try:
    notifier = SlackNotifier()
    message = f"{emoji} AIプログラム実行{status}: {task_name}\nDescription: 失敗時の動作確認\nExit Code: {exit_code}"
    notifier.send_message(message)
except Exception as e:
    print(f"Slack notification failed: {e}")
EOF

python3 /tmp/notify_program_result.py
rm -f /tmp/notify_program_result.py

exit $EXIT_CODE
