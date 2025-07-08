#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "=== AI Program Execution ===" | tee /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132248_process_todo_ai_self_growth.log
echo "Task: process_todo_ai_self_growth" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132248_process_todo_ai_self_growth.log
echo "Description: ToDoリスト 'ai_self_growth' の自律処理" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132248_process_todo_ai_self_growth.log
echo "Started: $(date)" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132248_process_todo_ai_self_growth.log
echo "============================" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132248_process_todo_ai_self_growth.log

python3 /home/aicompany/ai_co/ai_programs/inbox/process_todo_ai_self_growth.py 2>&1 | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132248_process_todo_ai_self_growth.log
EXIT_CODE=${PIPESTATUS[0]}

echo "============================" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132248_process_todo_ai_self_growth.log
echo "Completed: $(date)" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132248_process_todo_ai_self_growth.log
echo "Exit Code: $EXIT_CODE" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132248_process_todo_ai_self_growth.log

# アーカイブまたは失敗フォルダへ移動
if [ $EXIT_CODE -eq 0 ]; then
    ARCHIVE_DIR="/home/aicompany/ai_co/ai_programs/archive/$(date +%Y-%m-%d)"
    mkdir -p "$ARCHIVE_DIR"
    mv /home/aicompany/ai_co/ai_programs/inbox/process_todo_ai_self_growth.py "$ARCHIVE_DIR/process_todo_ai_self_growth_20250703_132248.py"
    echo "Archived to: $ARCHIVE_DIR" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132248_process_todo_ai_self_growth.log
else
    mv /home/aicompany/ai_co/ai_programs/inbox/process_todo_ai_self_growth.py "/home/aicompany/ai_co/ai_programs/failed/process_todo_ai_self_growth_20250703_132248.py"
    echo "Moved to failed directory" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132248_process_todo_ai_self_growth.log
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

task_name = "process_todo_ai_self_growth"
exit_code = $EXIT_CODE
status = "$STATUS"
emoji = "$EMOJI"

try:
    notifier = SlackNotifier()
    message = f"{emoji} AIプログラム実行{status}: {task_name}\nDescription: ToDoリスト 'ai_self_growth' の自律処理\nExit Code: {exit_code}"
    notifier.send_message(message)
except Exception as e:
    print(f"Slack notification failed: {e}")
EOF

python3 /tmp/notify_program_result.py
rm -f /tmp/notify_program_result.py

exit $EXIT_CODE
