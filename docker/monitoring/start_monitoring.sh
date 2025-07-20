#!/bin/bash
# Elder Tree 監視システム起動スクリプト
# Grand Elder maru統治下の完璧な監視体制

echo "🏛️ Elder Tree Monitoring System Startup"
echo "Under the governance of Grand Elder maru"
echo "========================================"

# 環境変数設定
export PYTHONPATH="/home/aicompany/ai_co:$PYTHONPATH"
export MONITORING_HOME="/home/aicompany/ai_co/monitoring"

# ログディレクトリ作成
mkdir -p $MONITORING_HOME/logs/audit
mkdir -p $MONITORING_HOME/logs/dashboard
mkdir -p $MONITORING_HOME/backups/audit
mkdir -p $MONITORING_HOME/reports/generated
mkdir -p $MONITORING_HOME/dashboards

echo "📁 Directory structure created"

# 監視ダッシュボード起動
echo "🖥️ Starting monitoring dashboard..."
python3 $MONITORING_HOME/dashboards/elder_tree_dashboard.py > $MONITORING_HOME/logs/dashboard/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "   Dashboard PID: $DASHBOARD_PID"

# アラートシステム起動
echo "🚨 Starting alert system..."
python3 $MONITORING_HOME/alerts/alert_system.py > $MONITORING_HOME/logs/alerts.log 2>&1 &
ALERT_PID=$!
echo "   Alert system PID: $ALERT_PID"

# 監査ログシステム起動
echo "📝 Starting audit logger..."
python3 $MONITORING_HOME/logs/audit_logger.py > $MONITORING_HOME/logs/audit_system.log 2>&1 &
AUDIT_PID=$!
echo "   Audit logger PID: $AUDIT_PID"

# PIDファイル保存
echo $DASHBOARD_PID > $MONITORING_HOME/dashboard.pid
echo $ALERT_PID > $MONITORING_HOME/alert.pid
echo $AUDIT_PID > $MONITORING_HOME/audit.pid

echo ""
echo "✅ All monitoring systems started successfully!"
echo ""
echo "📊 Dashboard URL: http://localhost:8080/monitoring/dashboard"
echo "📋 Logs location: $MONITORING_HOME/logs/"
echo "🔍 To check status: ps aux | grep -E 'dashboard|alert|audit'"
echo ""
echo "🏛️ Elder Tree monitoring is now active under Grand Elder maru"
echo ""
echo "To stop monitoring:"
echo "  ./stop_monitoring.sh"
