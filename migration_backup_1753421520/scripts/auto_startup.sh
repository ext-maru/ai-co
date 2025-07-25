#!/bin/bash
# WSL自動起動スクリプト
# AI Company システム復旧用

PROJECT_ROOT="/home/aicompany/ai_co"
LOG_FILE="$PROJECT_ROOT/logs/auto_startup.log"

echo "[$(date)] WSL自動起動スクリプト実行開始" >> "$LOG_FILE"

# Python環境の復旧
cd "$PROJECT_ROOT"
python3 scripts/wsl_sleep_recovery_system.py >> "$LOG_FILE" 2>&1

echo "[$(date)] WSL自動起動スクリプト実行完了" >> "$LOG_FILE"
