#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "=== AI Program Execution ===" | tee /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_test_runner.log
echo "Task: test_runner" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_test_runner.log
echo "Description: AI Program Runnerの動作テスト" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_test_runner.log
echo "Started: $(date)" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_test_runner.log
echo "============================" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_test_runner.log

python3 /home/aicompany/ai_co/ai_programs/inbox/test_runner.py 2>&1 | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_test_runner.log
EXIT_CODE=${PIPESTATUS[0]}

echo "============================" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_test_runner.log
echo "Completed: $(date)" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_test_runner.log
echo "Exit Code: $EXIT_CODE" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_test_runner.log

# アーカイブまたは失敗フォルダへ移動
if [ $EXIT_CODE -eq 0 ]; then
    ARCHIVE_DIR="/home/aicompany/ai_co/ai_programs/archive/$(date +%Y-%m-%d)"
    mkdir -p "$ARCHIVE_DIR"
    mv /home/aicompany/ai_co/ai_programs/inbox/test_runner.py "$ARCHIVE_DIR/test_runner_20250703_003142.py"
    echo "Archived to: $ARCHIVE_DIR" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_test_runner.log
else
    mv /home/aicompany/ai_co/ai_programs/inbox/test_runner.py "/home/aicompany/ai_co/ai_programs/failed/test_runner_20250703_003142.py"
    echo "Moved to failed directory" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_test_runner.log
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

task_name = "test_runner"
exit_code = $EXIT_CODE
status = "$STATUS"
emoji = "$EMOJI"

try:
    notifier = SlackNotifier()
    message = f"{emoji} AIプログラム実行{status}: {task_name}\nDescription: AI Program Runnerの動作テスト\nExit Code: {exit_code}"
    notifier.send_message(message)
except Exception as e:
    print(f"Slack notification failed: {e}")
EOF

python3 /tmp/notify_program_result.py
rm -f /tmp/notify_program_result.py

exit $EXIT_CODE
