#!/bin/bash
# 品質進化システム管理用スクリプト

PROJECT_ROOT="/home/aicompany/ai_co"

case "$1" in
    status)
        echo "🔍 品質進化システム状態確認"
        sudo systemctl status quality-evolution --no-pager
        ;;
    start)
        echo "🚀 品質進化システム開始"
        sudo systemctl start quality-evolution
        ;;
    stop)
        echo "⏹️ 品質進化システム停止"
        sudo systemctl stop quality-evolution
        ;;
    restart)
        echo "🔄 品質進化システム再起動"
        sudo systemctl restart quality-evolution
        ;;
    logs)
        echo "📋 品質進化システムログ表示"
        sudo journalctl -u quality-evolution -f
        ;;
    check)
        echo "🔍 手動品質チェック実行"
        python3 "$PROJECT_ROOT/scripts/manual_quality_check.py"
        ;;
    *)
        echo "使用方法: $0 {status|start|stop|restart|logs|check}"
        exit 1
        ;;
esac
