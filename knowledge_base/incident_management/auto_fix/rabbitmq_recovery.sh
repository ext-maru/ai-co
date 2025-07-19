#!/bin/bash
# RabbitMQ 自動復旧スクリプト
# インシデント賢者の RabbitMQ 専用治癒術

LOG_FILE="/home/aicompany/ai_co/logs/rabbitmq_recovery.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_rabbitmq_status() {
    log_message "🔍 RabbitMQ status check starting..."

    # サービス状態確認
    if systemctl is-active --quiet rabbitmq-server; then
        log_message "✅ RabbitMQ service is running"
        return 0
    else
        log_message "❌ RabbitMQ service is not running"
        return 1
    fi
}

restart_rabbitmq() {
    log_message "🔄 Restarting RabbitMQ service..."

    # サービス停止
    sudo systemctl stop rabbitmq-server
    sleep 3

    # プロセス確認と強制終了
    if pgrep -f rabbitmq > /dev/null; then
        log_message "⚠️ RabbitMQ processes still running, force killing..."
        sudo pkill -f rabbitmq
        sleep 2
    fi

    # サービス開始
    sudo systemctl start rabbitmq-server
    sleep 5

    # 状態確認
    if check_rabbitmq_status; then
        log_message "✅ RabbitMQ restart successful"
        return 0
    else
        log_message "❌ RabbitMQ restart failed"
        return 1
    fi
}

reset_rabbitmq_queues() {
    log_message "🧹 Resetting RabbitMQ queues..."

    # AI Company の主要キュー
    queues=("task_queue" "result_queue" "pm_queue" "dialog_queue")

    for queue in "${queues[@]}"; do
        log_message "Purging queue: $queue"
        sudo rabbitmqctl purge_queue "$queue" 2>/dev/null || log_message "⚠️ Queue $queue not found or already empty"
    done

    log_message "✅ Queue reset completed"
    return 0
}

check_rabbitmq_connections() {
    log_message "🔌 Checking RabbitMQ connections..."

    # 接続数確認
    connections=$(sudo rabbitmqctl list_connections -q 2>/dev/null | wc -l)
    log_message "Active connections: $connections"

    # ポート確認
    if netstat -an | grep -q ":5672.*LISTEN"; then
        log_message "✅ RabbitMQ port 5672 is listening"
        return 0
    else
        log_message "❌ RabbitMQ port 5672 is not listening"
        return 1
    fi
}

fix_rabbitmq_permissions() {
    log_message "🔐 Fixing RabbitMQ permissions..."

    # データディレクトリ権限修正
    sudo chown -R rabbitmq:rabbitmq /var/lib/rabbitmq/
    sudo chmod -R 755 /var/lib/rabbitmq/

    # ログディレクトリ権限修正
    sudo chown -R rabbitmq:rabbitmq /var/log/rabbitmq/
    sudo chmod -R 755 /var/log/rabbitmq/

    log_message "✅ RabbitMQ permissions fixed"
    return 0
}

comprehensive_rabbitmq_recovery() {
    log_message "🚨 Starting comprehensive RabbitMQ recovery..."

    local recovery_steps=0
    local successful_steps=0

    # Step 1: 基本状態確認
    recovery_steps=$((recovery_steps + 1))
    if check_rabbitmq_status; then
        log_message "ℹ️ RabbitMQ is running, checking deeper issues..."
        successful_steps=$((successful_steps + 1))
    fi

    # Step 2: 接続確認
    recovery_steps=$((recovery_steps + 1))
    if check_rabbitmq_connections; then
        successful_steps=$((successful_steps + 1))
    else
        log_message "🔄 Connection issues detected, attempting restart..."

        # Step 3: サービス再起動
        recovery_steps=$((recovery_steps + 1))
        if restart_rabbitmq; then
            successful_steps=$((successful_steps + 1))
        fi
    fi

    # Step 4: 権限修正
    recovery_steps=$((recovery_steps + 1))
    if fix_rabbitmq_permissions; then
        successful_steps=$((successful_steps + 1))
    fi

    # Step 5: キューリセット
    recovery_steps=$((recovery_steps + 1))
    if reset_rabbitmq_queues; then
        successful_steps=$((successful_steps + 1))
    fi

    # Step 6: 最終確認
    recovery_steps=$((recovery_steps + 1))
    if check_rabbitmq_status && check_rabbitmq_connections; then
        successful_steps=$((successful_steps + 1))
        log_message "🎉 RabbitMQ recovery completed successfully!"

        # AI Company ワーカーの再起動推奨
        log_message "💡 Recommendation: Restart AI Company workers to reconnect"
        echo "cd /home/aicompany/ai_co && python commands/ai_restart.py" >> "$LOG_FILE"

        return 0
    else
        log_message "❌ RabbitMQ recovery failed. Manual intervention required."
        log_message "📊 Recovery statistics: $successful_steps/$recovery_steps steps successful"
        return 1
    fi
}

# メイン実行
case "${1:-full}" in
    "status")
        check_rabbitmq_status
        ;;
    "restart")
        restart_rabbitmq
        ;;
    "reset_queues")
        reset_rabbitmq_queues
        ;;
    "fix_permissions")
        fix_rabbitmq_permissions
        ;;
    "full"|*)
        comprehensive_rabbitmq_recovery
        ;;
esac

exit $?
