#!/bin/bash
# Elder Tree 監視システム停止スクリプト

echo "🛑 Stopping Elder Tree Monitoring System..."

MONITORING_HOME="/home/aicompany/ai_co/monitoring"

# PIDファイルから読み込み
if [ -f "$MONITORING_HOME/dashboard.pid" ]; then
    DASHBOARD_PID=$(cat $MONITORING_HOME/dashboard.pid)
    kill $DASHBOARD_PID 2>/dev/null
    echo "   Dashboard stopped (PID: $DASHBOARD_PID)"
    rm $MONITORING_HOME/dashboard.pid
fi

if [ -f "$MONITORING_HOME/alert.pid" ]; then
    ALERT_PID=$(cat $MONITORING_HOME/alert.pid)
    kill $ALERT_PID 2>/dev/null
    echo "   Alert system stopped (PID: $ALERT_PID)"
    rm $MONITORING_HOME/alert.pid
fi

if [ -f "$MONITORING_HOME/audit.pid" ]; then
    AUDIT_PID=$(cat $MONITORING_HOME/audit.pid)
    kill $AUDIT_PID 2>/dev/null
    echo "   Audit logger stopped (PID: $AUDIT_PID)"
    rm $MONITORING_HOME/audit.pid
fi

echo ""
echo "✅ All monitoring systems stopped"
echo "📝 Logs are preserved in: $MONITORING_HOME/logs/"