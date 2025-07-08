#!/bin/bash
#!/bin/bash
echo "=== AI Script Execution ===" | tee /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132237_implement_ai_send_extension.log
echo "Task: implement_ai_send_extension" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132237_implement_ai_send_extension.log
echo "Description: ai-send拡張の実装" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132237_implement_ai_send_extension.log
echo "Started: $(date)" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132237_implement_ai_send_extension.log
echo "============================" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132237_implement_ai_send_extension.log

/home/aicompany/ai_co/ai_programs/inbox/implement_ai_send_extension.sh 2>&1 | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132237_implement_ai_send_extension.log
EXIT_CODE=${PIPESTATUS[0]}

echo "============================" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132237_implement_ai_send_extension.log
echo "Completed: $(date)" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132237_implement_ai_send_extension.log
echo "Exit Code: $EXIT_CODE" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132237_implement_ai_send_extension.log

# アーカイブまたは失敗フォルダへ移動
if [ $EXIT_CODE -eq 0 ]; then
    ARCHIVE_DIR="/home/aicompany/ai_co/ai_programs/archive/$(date +%Y-%m-%d)"
    mkdir -p "$ARCHIVE_DIR"
    mv /home/aicompany/ai_co/ai_programs/inbox/implement_ai_send_extension.sh "$ARCHIVE_DIR/implement_ai_send_extension_20250703_132237.sh"
    echo "Archived to: $ARCHIVE_DIR" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132237_implement_ai_send_extension.log
else
    mv /home/aicompany/ai_co/ai_programs/inbox/implement_ai_send_extension.sh "/home/aicompany/ai_co/ai_programs/failed/implement_ai_send_extension_20250703_132237.sh"
    echo "Moved to failed directory" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_132237_implement_ai_send_extension.log
fi

exit $EXIT_CODE
