#!/bin/bash
# Setup daily cron job for unit progress tracking
# 騎士団、ウィザーズ、ドワーフ工房の日次進捗レポート自動生成

PROJECT_DIR="/home/aicompany/ai_co"
SCRIPT_PATH="$PROJECT_DIR/scripts/track-unit-progress"

echo "🔧 Setting up daily unit progress tracking..."

# Create cron job that runs at 23:59 every day
CRON_COMMAND="59 23 * * * cd $PROJECT_DIR && /usr/bin/python3 $SCRIPT_PATH >> $PROJECT_DIR/logs/unit_progress_cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "track-unit-progress"; then
    echo "⚠️  Cron job already exists. Updating..."
    # Remove old job
    (crontab -l 2>/dev/null | grep -v "track-unit-progress") | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

echo "✅ Daily unit progress tracking scheduled for 23:59 every day"
echo "📁 Reports will be saved to: $PROJECT_DIR/knowledge_base/unit_progress/"
echo "📊 Logs will be saved to: $PROJECT_DIR/logs/unit_progress_cron.log"

# Create initial report for today
echo ""
echo "📊 Generating initial report for today..."
cd "$PROJECT_DIR" && python3 "$SCRIPT_PATH"
