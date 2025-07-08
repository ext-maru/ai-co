#!/bin/bash
#!/bin/bash
echo "=== AI Script Execution ===" | tee /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_worker_health_check.log
echo "Task: worker_health_check" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_worker_health_check.log
echo "Description: AI Companyワーカー健全性チェック" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_worker_health_check.log
echo "Started: $(date)" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_worker_health_check.log
echo "============================" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_worker_health_check.log

/home/aicompany/ai_co/ai_programs/inbox/worker_health_check.sh 2>&1 | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_worker_health_check.log
EXIT_CODE=${PIPESTATUS[0]}

echo "============================" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_worker_health_check.log
echo "Completed: $(date)" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_worker_health_check.log
echo "Exit Code: $EXIT_CODE" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_worker_health_check.log

# アーカイブまたは失敗フォルダへ移動
if [ $EXIT_CODE -eq 0 ]; then
    ARCHIVE_DIR="/home/aicompany/ai_co/ai_programs/archive/$(date +%Y-%m-%d)"
    mkdir -p "$ARCHIVE_DIR"
    mv /home/aicompany/ai_co/ai_programs/inbox/worker_health_check.sh "$ARCHIVE_DIR/worker_health_check_20250703_003142.sh"
    echo "Archived to: $ARCHIVE_DIR" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_worker_health_check.log
else
    mv /home/aicompany/ai_co/ai_programs/inbox/worker_health_check.sh "/home/aicompany/ai_co/ai_programs/failed/worker_health_check_20250703_003142.sh"
    echo "Moved to failed directory" | tee -a /home/aicompany/ai_co/ai_programs/ai_logs/exec_20250703_003142_worker_health_check.log
fi

exit $EXIT_CODE
