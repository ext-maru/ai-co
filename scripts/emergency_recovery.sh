#!/bin/bash
# 🚨 緊急ワーカー復旧システム - インシデント賢者実装
# 4賢者会議決定事項

set -e

PROJECT_ROOT="/home/aicompany/ai_co"
LOG_FILE="$PROJECT_ROOT/logs/emergency_recovery.log"

# ログ関数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [EMERGENCY] $1" | tee -a "$LOG_FILE"
}

# エラーハンドリング
handle_error() {
    log "❌ エラー発生: $1"
    exit 1
}

# メイン復旧処理
main() {
    log "🚨 緊急ワーカー復旧システム開始"
    
    cd "$PROJECT_ROOT" || handle_error "プロジェクトディレクトリに移動できません"
    
    # 1. 実装検証
    log "🔍 実装検証実行中..."
    if python3 scripts/validate_implementations.py; then
        log "✅ 実装検証完了"
    else
        log "⚠️ 実装検証で問題発見 - 継続します"
    fi
    
    # 2. ワーカープロセス状況確認
    log "📊 ワーカープロセス状況確認..."
    WORKER_COUNT=$(ps aux | grep -E "(worker|python)" | grep -v grep | grep -c -E "(pm|task)" || echo "0")
    log "現在のワーカー数: $WORKER_COUNT"
    
    # 3. RabbitMQ状況確認
    log "🐰 RabbitMQ状況確認..."
    if ! rabbitmqctl status > /dev/null 2>&1; then
        log "❌ RabbitMQ未稼働 - 手動確認が必要"
        handle_error "RabbitMQ接続失敗"
    fi
    
    # 4. キューバックログ確認
    log "📋 キューバックログ確認..."
    PM_QUEUE_MSG=$(rabbitmqctl list_queues name messages | grep ai_pm | awk '{print $2}' || echo "0")
    TASK_QUEUE_MSG=$(rabbitmqctl list_queues name messages | grep ai_tasks | awk '{print $2}' || echo "0")
    
    log "ai_pm キュー: $PM_QUEUE_MSG 件"
    log "ai_tasks キュー: $TASK_QUEUE_MSG 件"
    
    # 5. 緊急復旧判定
    NEED_RECOVERY=false
    
    if [ "$WORKER_COUNT" -lt 2 ]; then
        log "⚠️ ワーカー不足検出"
        NEED_RECOVERY=true
    fi
    
    if [ "$PM_QUEUE_MSG" -gt 10 ]; then
        log "⚠️ PM キューバックログ検出"
        NEED_RECOVERY=true
    fi
    
    if [ "$TASK_QUEUE_MSG" -gt 20 ]; then
        log "⚠️ Task キューバックログ検出" 
        NEED_RECOVERY=true
    fi
    
    # 6. 復旧実行
    if [ "$NEED_RECOVERY" = true ]; then
        log "🔄 緊急復旧実行中..."
        
        # PM Worker復旧
        if [ "$PM_QUEUE_MSG" -gt 0 ]; then
            log "🚀 PM Worker緊急起動..."
            nohup python3 workers/async_pm_worker_simple.py --worker-id emergency-pm > /dev/null 2>&1 &
            log "✅ PM Worker起動: PID $!"
        fi
        
        # Task Worker復旧
        if [ "$TASK_QUEUE_MSG" -gt 0 ]; then
            log "🚀 Task Worker緊急起動..."
            nohup python3 workers/simple_task_worker.py --worker-id emergency-task > /dev/null 2>&1 &
            log "✅ Task Worker起動: PID $!"
        fi
        
        # 復旧後待機
        log "⏳ 復旧処理安定化待機..."
        sleep 10
        
        # 復旧確認
        NEW_WORKER_COUNT=$(ps aux | grep -E "(worker|python)" | grep -v grep | grep -c -E "(pm|task)" || echo "0")
        log "復旧後ワーカー数: $NEW_WORKER_COUNT"
        
        if [ "$NEW_WORKER_COUNT" -gt "$WORKER_COUNT" ]; then
            log "✅ 緊急復旧成功"
        else
            log "⚠️ 復旧が不完全 - 手動確認推奨"
        fi
        
    else
        log "✅ システム正常 - 復旧不要"
    fi
    
    # 7. Slack通知（可能であれば）
    if command -v curl > /dev/null 2>&1; then
        log "📢 Slack通知送信試行..."
        # Slack Webhookがあれば通知
        # curl -X POST ... (実装略)
    fi
    
    log "🎯 緊急復旧システム完了"
}

# スクリプト実行
main "$@"