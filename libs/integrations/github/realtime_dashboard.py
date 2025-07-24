#!/usr/bin/env python3
"""
🚀 自動イシュー処理システム - リアルタイム監視ダッシュボード
Phase 2実装: リアルタイム処理状況表示・成功率・エラー率の可視化

エルダーズギルド評議会承認 - リアルタイム監視システム
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import sqlite3
from flask import Flask, jsonify, render_template_string
from flask_socketio import SocketIO, emit
import threading
import time

# Project root
project_root = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from libs.integrations.github.monitoring_dashboard import MetricsDatabase, ProcessingMetrics, SystemHealthMetrics

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RealtimeDashboard")

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'elder_guild_realtime_monitoring'
socketio = SocketIO(app, cors_allowed_origins="*")


class RealtimeDashboard:
    """リアルタイム監視ダッシュボード"""
    
    def __init__(self):
        """初期化メソッド"""
        self.metrics_db = MetricsDatabase()
        self.is_running = False
        self.update_interval = 5  # 5秒間隔で更新
        
    def start(self):
        """ダッシュボード開始"""
        self.is_running = True
        
        # バックグラウンドでメトリクス更新
        thread = threading.Thread(target=self._metrics_update_loop)
        thread.daemon = True
        thread.start()
        
        logger.info("🚀 Realtime Dashboard started")
        
    def stop(self):
        """ダッシュボード停止"""
        self.is_running = False
        logger.info("⏹️ Realtime Dashboard stopped")
        
    def _metrics_update_loop(self):
        """メトリクス更新ループ"""
        while self.is_running:
            try:
                # 最新のメトリクスを取得してブロードキャスト
                current_metrics = self.get_current_metrics()
                socketio.emit('metrics_update', current_metrics)
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Metrics update error: {e}")
                time.sleep(self.update_interval)
                
    def get_current_metrics(self) -> Dict[str, Any]:
        """現在のメトリクスを取得"""
        try:
            with sqlite3connect(self.metrics_db.db_path) as conn:
                cursor = conn.cursor()
                
                # 過去24時間の処理統計
                yesterday = (datetime.now() - timedelta(days=1)).isoformat()
                
                # 成功率計算
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN processing_status = 'completed' THEN 1 ELSE 0 END) as successful
                    FROM processing_metrics 
                    WHERE timestamp > ?
                """, (yesterday,))
                
                total_count, successful_count = cursor.fetchone()
                success_rate = (successful_count / total_count * 100) if total_count > 0 else 0
                
                # 平均処理時間
                cursor.execute("""
                    SELECT AVG(processing_time_seconds)
                    FROM processing_metrics 
                    WHERE timestamp > ? AND processing_status = 'completed'
                """, (yesterday,))
                
                avg_time_result = cursor.fetchone()
                avg_processing_time = avg_time_result[0] if avg_time_result[0] else 0
                
                # 優先度別統計
                cursor.execute("""
                    SELECT priority, COUNT(*) as count
                    FROM processing_metrics 
                    WHERE timestamp > ?
                    GROUP BY priority
                """, (yesterday,))
                
                priority_stats = dict(cursor.fetchall())
                
                # 最近の処理
                cursor.execute("""
                    SELECT issue_number, issue_title, priority, processing_status, 
                           timestamp, pr_url
                    FROM processing_metrics 
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                """, (yesterday,))
                
                recent_processes = []
                for row in cursor.fetchall():
                    recent_processes.append({
                        'issue_number': row[0],
                        'issue_title': row[1],
                        'priority': row[2],
                        'status': row[3],
                        'timestamp': row[4],
                        'pr_url': row[5]
                    })
                
                # エラー統計
                cursor.execute("""
                    SELECT COUNT(*) as error_count
                    FROM processing_metrics 
                    WHERE timestamp > ? AND processing_status = 'failed'
                """, (yesterday,))
                
                error_count = cursor.fetchone()[0]
                error_rate = (error_count / total_count * 100) if total_count > 0 else 0
                
                # 時間別統計（過去24時間）
                cursor.execute("""
                    SELECT 
                        strftime('%H', timestamp) as hour,
                        COUNT(*) as total,
                        SUM(CASE WHEN processing_status = 'completed' THEN 1 ELSE 0 END) as successful
                    FROM processing_metrics 
                    WHERE timestamp > ?
                    GROUP BY strftime('%H', timestamp)
                    ORDER BY hour
                """, (yesterday,))
                
                hourly_stats = {}
                for row in cursor.fetchall():
                    hour, total, successful = row
                    hourly_stats[hour] = {
                        'total': total,
                        'successful': successful,
                        'success_rate': (successful / total * 100) if total > 0 else 0
                    }
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'summary': {
                        'total_processed_24h': total_count,
                        'successful_count': successful_count,
                        'success_rate': round(success_rate, 2),
                        'error_count': error_count,
                        'error_rate': round(error_rate, 2),
                        'avg_processing_time': round(avg_processing_time, 2),
                    },
                    'priority_stats': priority_stats,
                    'recent_processes': recent_processes,
                    'hourly_stats': hourly_stats,
                    'system_status': self._get_system_status()
                }
                
        except Exception as e:
            logger.error(f"Error getting current metrics: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'summary': {},
                'priority_stats': {},
                'recent_processes': [],
                'hourly_stats': {},
                'system_status': {'status': 'error', 'message': str(e)}
            }
    
    def _get_system_status(self) -> Dict[str, Any]:
        """システム状態を取得"""
        try:
            # Auto Issue Processorの稼働状況確認
            from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
            
            # 簡単なヘルスチェック
            processor = AutoIssueProcessor()
            capabilities = processor.get_capabilities()
            
            return {
                'status': 'healthy',
                'auto_processor': 'active',
                'github_api': 'connected',
                'four_sages': 'available',
                'capabilities': capabilities
            }
        except Exception as e:
            return {
                'status': 'degraded',
                'error': str(e),
                'message': 'Some components may not be available'
            }


# Global dashboard instance
dashboard = RealtimeDashboard()


@app.route('/')
def index():
    """ダッシュボードメインページ"""
    return render_template_string(DASHBOARD_HTML_TEMPLATE)


@app.route('/api/metrics')
def get_metrics():
    """メトリクスAPI"""
    return jsonify(dashboard.get_current_metrics())


@app.route('/api/status')
def get_status():
    """システム状態API"""
    return jsonify(dashboard._get_system_status())


@socketio.on('connect')
def handle_connect():
    """WebSocket接続時"""
    logger.info("Client connected to dashboard")
    emit('metrics_update', dashboard.get_current_metrics())


@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket切断時"""
    logger.info("Client disconnected from dashboard")


@socketio.on('request_metrics')
def handle_request_metrics():
    """メトリクス要求"""
    emit('metrics_update', dashboard.get_current_metrics())


# HTML Template for Dashboard
DASHBOARD_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Auto Issue Processor - Realtime Dashboard</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
            margin: 10px 0;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .card h3 {
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.3em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            padding: 10px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }
        
        .metric-value {
            font-weight: bold;
            font-size: 1.2em;
        }
        
        .success { color: #4CAF50; }
        .error { color: #f44336; }
        .warning { color: #ff9800; }
        .info { color: #2196F3; }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-healthy { background-color: #4CAF50; }
        .status-degraded { background-color: #ff9800; }
        .status-error { background-color: #f44336; }
        
        .recent-item {
            padding: 10px;
            margin: 5px 0;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        .recent-item.completed { border-left-color: #4CAF50; }
        .recent-item.failed { border-left-color: #f44336; }
        .recent-item.started { border-left-color: #2196F3; }
        .recent-item.skipped { border-left-color: #ff9800; }
        
        .timestamp {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .priority-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .priority-critical { background-color: #f44336; }
        .priority-high { background-color: #ff9800; }
        .priority-medium { background-color: #2196F3; }
        .priority-low { background-color: #4CAF50; }
        
        #last-update {
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.7);
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.9em;
        }
        
        .chart-container {
            position: relative;
            height: 200px;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div id="last-update">⏰ 更新中...</div>
    
    <div class="header">
        <h1>🤖 Auto Issue Processor</h1>
        <p>🏛️ エルダーズギルド リアルタイム監視ダッシュボード</p>
        <p id="status-indicator">
            <span class="status-indicator status-healthy"></span>
            システム稼働中
        </p>
    </div>
    
    <div class="dashboard-grid">
        <!-- Summary Stats -->
        <div class="card">
            <h3>"📊" 処理統計 (24時間)</h3>
            <div class="metric">
                <span>総処理数</span>
                <span class="metric-value info" id="total-processed">-</span>
            </div>
            <div class="metric">
                <span>成功数</span>
                <span class="metric-value success" id="successful-count">-</span>
            </div>
            <div class="metric">
                <span>成功率</span>
                <span class="metric-value success" id="success-rate">-</span>
            </div>
            <div class="metric">
                <span>エラー数</span>
                <span class="metric-value error" id="error-count">-</span>
            </div>
            <div class="metric">
                <span>エラー率</span>
                <span class="metric-value error" id="error-rate">-</span>
            </div>
            <div class="metric">
                <span>平均処理時間</span>
                <span class="metric-value info" id="avg-time">-</span>
            </div>
        </div>
        
        <!-- Priority Distribution -->
        <div class="card">
            <h3>🎯 優先度別統計</h3>
            <div id="priority-stats">
                <div class="metric">
                    <span>Critical</span>
                    <span class="metric-value priority-critical" id="priority-critical">-</span>
                </div>
                <div class="metric">
                    <span>High</span>
                    <span class="metric-value priority-high" id="priority-high">-</span>
                </div>
                <div class="metric">
                    <span>Medium</span>
                    <span class="metric-value priority-medium" id="priority-medium">-</span>
                </div>
                <div class="metric">
                    <span>Low</span>
                    <span class="metric-value priority-low" id="priority-low">-</span>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="priorityChart"></canvas>
            </div>
        </div>
        
        <!-- System Status -->
        <div class="card">
            <h3>⚡ システム状況</h3>
            <div id="system-status">
                <div class="metric">
                    <span>Auto Processor</span>
                    <span class="metric-value" id="auto-processor-status">-</span>
                </div>
                <div class="metric">
                    <span>GitHub API</span>
                    <span class="metric-value" id="github-api-status">-</span>
                </div>
                <div class="metric">
                    <span>4賢者システム</span>
                    <span class="metric-value" id="four-sages-status">-</span>
                </div>
            </div>
        </div>
        
        <!-- Hourly Performance -->
        <div class="card">
            <h3>"📈" 時間別パフォーマンス</h3>
            <div class="chart-container">
                <canvas id="hourlyChart"></canvas>
            </div>
        </div>
        
        <!-- Recent Processes -->
        <div class="card" style="grid-column: 1 / -1;">
            <h3>🔄 最近の処理</h3>
            <div id="recent-processes">
                <!-- Dynamic content -->
            </div>
        </div>
    </div>
    
    <script>
        // Socket.IO connection
        const socket = io();
        
        // Chart instances
        let priorityChart, hourlyChart;
        
        // Initialize charts
        function initCharts() {
            // Priority Chart
            const priorityCtx = document.getElementById('priorityChart').getContext('2d');
            priorityChart = new Chart(priorityCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Critical', 'High', 'Medium', 'Low'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: [
                            '#f44336',
                            '#ff9800',
                            '#2196F3',
                            '#4CAF50'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
            
            // Hourly Chart
            const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
            hourlyChart = new Chart(hourlyCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: '成功率 (%)',
                        data: [],
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
        
        // Update dashboard with new data
        function updateDashboard(data) {
            if (data.error) {
                console.error('Dashboard error:', data.error);
                return;
            }
            
            const summary = data.summary || {};
            const priorityStats = data.priority_stats || {};
            const recentProcesses = data.recent_processes || [];
            const hourlyStats = data.hourly_stats || {};
            const systemStatus = data.system_status || {};
            
            // Update summary
            document.getElementById('total-processed').textContent = summary.total_processed_24h || 0;
            document.getElementById('successful-count').textContent = summary.successful_count || 0;
            document.getElementById('success-rate').textContent = (summary.success_rate || 0) + '%';
            document.getElementById('error-count').textContent = summary.error_count || 0;
            document.getElementById('error-rate').textContent = (summary.error_rate || 0) + '%';
            document.getElementById('avg-time').textContent = (summary.avg_processing_time || 0) + 's';
            
            // Update priority stats
            document.getElementById('priority-critical').textContent = priorityStats.critical || 0;
            document.getElementById('priority-high').textContent = priorityStats.high || 0;
            document.getElementById('priority-medium').textContent = priorityStats.medium || 0;
            document.getElementById('priority-low').textContent = priorityStats.low || 0;
            
            // Update priority chart
            if (priorityChart) {
                priorityChart.data.datasets[0].data = [
                    priorityStats.critical || 0,
                    priorityStats.high || 0,
                    priorityStats.medium || 0,
                    priorityStats.low || 0
                ];
                priorityChart.update();
            }
            
            // Update system status
            const statusColors = {
                'healthy': 'success',
                'active': 'success',
                'connected': 'success',
                'available': 'success',
                'degraded': 'warning',
                'error': 'error'
            };
            
            document.getElementById('auto-processor-status').textContent = systemStatus.auto_processor || 'unknown';
            document.getElementById('auto-processor-status').className = 'metric-value ' + \
                (statusColors[systemStatus.auto_processor] || 'info');
            
            document.getElementById('github-api-status').textContent = systemStatus.github_api || 'unknown';
            document.getElementById('github-api-status').className = 'metric-value ' + \
                (statusColors[systemStatus.github_api] || 'info');
            
            document.getElementById('four-sages-status').textContent = systemStatus.four_sages || 'unknown';
            document.getElementById('four-sages-status').className = 'metric-value ' + \
                (statusColors[systemStatus.four_sages] || 'info');
            
            // Update hourly chart
            if (hourlyChart && Object.keys(hourlyStats).length > 0) {
                const hours = Object.keys(hourlyStats).sort();
                const successRates = hours.map(hour => hourlyStats[hour].success_rate || 0);
                
                hourlyChart.data.labels = hours.map(h => h + ':00');
                hourlyChart.data.datasets[0].data = successRates;
                hourlyChart.update();
            }
            
            // Update recent processes
            const recentContainer = document.getElementById('recent-processes');
            recentContainer.innerHTML = '';
            
            recentProcesses.forEach(process => {
                const div = document.createElement('div');
                div.className = `recent-item ${process.status}`;
                div.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center;" \
                        "display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>#${process.issue_number}</strong>
                            <span class="priority-badge priority-${process.priority}">${process.priority}</span>
                            ${process.issue_title}
                        </div>
                        <div>
                            ${process.pr_url ? `<a href="${process.pr_url}" target="_blank" style= \
                                "color: #4CAF50;">PR</a>` : ''}
                            <span class="timestamp">${new Date(process.timestamp).toLocaleString()}</span>
                        </div>
                    </div>
                `;
                recentContainer.appendChild(div);
            });
            
            // Update timestamp
            document.getElementById('last-update').textContent = 
                '⏰ ' + new Date(data.timestamp).toLocaleString();
        }
        
        // Socket event handlers
        socket.on('connect', function() {
            console.log('Connected to dashboard');
            socket.emit('request_metrics');
        });
        
        socket.on('metrics_update', function(data) {
            updateDashboard(data);
        });
        
        socket.on('disconnect', function() {
            console.log('Disconnected from dashboard');
        });
        
        // Initialize on load
        window.addEventListener('load', function() {
            initCharts();
            
            // Request initial metrics
            setTimeout(() => {
                socket.emit('request_metrics');
            }, 1000);
        });
        
        // Manual refresh button
        document.addEventListener('keydown', function(e) {
            if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
                e.preventDefault();
                socket.emit('request_metrics');
            }
        });
    </script>
</body>
</html>
"""


def run_dashboard(host='0.0.0.0', port=5000, debug=False):
    """ダッシュボードを実行"""
    dashboard.start()
    try:
        logger.info(f"🚀 Starting Realtime Dashboard on http://{host}:{port}")
        socketio.run(app, host=host, port=port, debug=debug)
    finally:
        dashboard.stop()


if __name__ == "__main__":
    run_dashboard(debug=True)