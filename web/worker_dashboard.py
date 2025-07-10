#!/usr/bin/env python3
"""
Worker Dashboard - Worker専用リアルタイムダッシュボード
AICompanyのWorker達の状態をリアルタイムで可視化
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import time
import threading
import logging
from datetime import datetime
from typing import Dict, List
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from libs.worker_status_monitor import WorkerStatusMonitor

logger = logging.getLogger(__name__)

class WorkerDashboardHandler(BaseHTTPRequestHandler):
    """Worker Dashboard HTTPハンドラー"""
    
    def do_GET(self):
        """GETリクエストの処理"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        try:
            if parsed_path.path == '/':
                self.serve_dashboard()
            elif parsed_path.path == '/api/workers':
                self.serve_api_workers()
            elif parsed_path.path.startswith('/api/worker/'):
                worker_id = parsed_path.path.split('/')[-1]
                self.serve_api_worker_detail(worker_id)
            elif parsed_path.path == '/api/dashboard-data':
                self.serve_api_dashboard_data()
            elif parsed_path.path == '/api/queue-status':
                self.serve_api_queue_status()
            else:
                self.send_error(404)
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_error(500)
    
    def serve_dashboard(self):
        """ダッシュボードHTMLを提供"""
        html_content = self._generate_dashboard_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_api_workers(self):
        """Workers API"""
        try:
            monitor = getattr(self.server, 'monitor', None)
            if not monitor:
                raise Exception("Monitor not available")
            
            workers = {}
            for worker_id, worker_data in monitor.workers_status.items():
                workers[worker_id] = {
                    **worker_data,
                    'started_at': worker_data['started_at'].isoformat() if worker_data.get('started_at') else None,
                    'last_updated': worker_data['last_updated'].isoformat() if worker_data.get('last_updated') else None
                }
            
            response_data = {'workers': workers}
            self._send_json_response(response_data)
            
        except Exception as e:
            logger.error(f"Error getting workers: {e}")
            self._send_json_response({'error': str(e)}, status=500)
    
    def serve_api_worker_detail(self, worker_id):
        """Worker詳細API"""
        try:
            monitor = getattr(self.server, 'monitor', None)
            if not monitor:
                raise Exception("Monitor not available")
            
            worker_status = monitor.get_worker_status(worker_id)
            if not worker_status:
                self._send_json_response({'error': 'Worker not found'}, status=404)
                return
            
            # 詳細情報を追加
            performance = monitor.get_worker_performance(worker_id)
            health = monitor.check_worker_health(worker_id)
            error_stats = monitor.get_worker_error_stats(worker_id)
            
            detailed_info = {
                **worker_status,
                'performance': performance,
                'health': health,
                'error_stats': error_stats,
                'started_at': worker_status['started_at'].isoformat() if worker_status.get('started_at') else None,
                'last_updated': worker_status['last_updated'].isoformat() if worker_status.get('last_updated') else None
            }
            
            self._send_json_response(detailed_info)
            
        except Exception as e:
            logger.error(f"Error getting worker detail: {e}")
            self._send_json_response({'error': str(e)}, status=500)
    
    def serve_api_dashboard_data(self):
        """ダッシュボードデータAPI"""
        try:
            monitor = getattr(self.server, 'monitor', None)
            if not monitor:
                raise Exception("Monitor not available")
            
            dashboard_data = monitor.generate_dashboard_data()
            self._send_json_response(dashboard_data)
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            self._send_json_response({'error': str(e)}, status=500)
    
    def serve_api_queue_status(self):
        """キューステータスAPI"""
        try:
            monitor = getattr(self.server, 'monitor', None)
            if not monitor:
                raise Exception("Monitor not available")
            
            queue_status = monitor.get_queue_status()
            self._send_json_response({'queues': queue_status})
            
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            self._send_json_response({'error': str(e)}, status=500)
    
    def _send_json_response(self, data, status=200):
        """JSON レスポンスを送信"""
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """ログメッセージを制御"""
        pass  # 標準出力への冗長なログを無効化
    
    def _generate_dashboard_html(self) -> str:
        """ダッシュボードHTMLを生成"""
        return '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Worker Dashboard - Elders Guild</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }
        .dashboard { 
            max-width: 1400px; 
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 2px solid #eee;
            padding-bottom: 20px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status-bar {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            gap: 20px;
        }
        .status-card {
            flex: 1;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        .status-card h3 { margin-bottom: 10px; font-size: 1.1em; }
        .status-card .value { font-size: 2em; font-weight: bold; }
        .workers-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        .worker-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
            transition: all 0.3s ease;
        }
        .worker-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }
        .worker-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .worker-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }
        .worker-status {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-idle { background: #e3f2fd; color: #1976d2; }
        .status-processing { background: #fff3e0; color: #f57c00; }
        .status-error { background: #ffebee; color: #d32f2f; }
        .worker-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
        }
        .metric {
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .metric-label {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
        }
        .queue-section {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .queue-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .queue-card {
            background: linear-gradient(135deg, #4fc3f7 0%, #29b6f6 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .queue-name {
            font-size: 1.1em;
            margin-bottom: 10px;
            opacity: 0.9;
        }
        .queue-count {
            font-size: 2.5em;
            font-weight: bold;
        }
        .last-updated {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 0.9em;
        }
        .refresh-btn {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4caf50;
            color: white;
            border: none;
            padding: 15px 20px;
            border-radius: 25px;
            font-weight: bold;
            cursor: pointer;
            z-index: 1000;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .refresh-btn:hover {
            background: #45a049;
            transform: translateY(-2px);
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        .processing { animation: pulse 2s infinite; }
        .loading { text-align: center; padding: 40px; color: #666; }
    </style>
</head>
<body>
    <button class="refresh-btn" onclick="loadDashboardData()">🔄 更新</button>
    
    <div class="dashboard">
        <div class="header">
            <h1>🤖 Worker Dashboard</h1>
            <p>Elders Guild Worker リアルタイム監視システム</p>
        </div>
        
        <div class="status-bar" id="statusBar">
            <div class="status-card">
                <h3>🔧 アクティブWorker</h3>
                <div class="value" id="activeWorkers">-</div>
            </div>
            <div class="status-card">
                <h3>📋 処理中タスク</h3>
                <div class="value" id="processingTasks">-</div>
            </div>
            <div class="status-card">
                <h3>⏱️ 平均処理時間</h3>
                <div class="value" id="avgProcessingTime">-</div>
            </div>
            <div class="status-card">
                <h3>✅ 成功率</h3>
                <div class="value" id="successRate">-</div>
            </div>
        </div>
        
        <div class="workers-grid" id="workersGrid">
            <div class="loading">Worker データを読み込み中...</div>
        </div>
        
        <div class="queue-section">
            <h2>📡 キューステータス</h2>
            <div class="queue-grid" id="queueGrid">
                <div class="loading">キューデータを読み込み中...</div>
            </div>
        </div>
        
        <div class="last-updated" id="lastUpdated">
            最終更新: -
        </div>
    </div>

    <script>
        class WorkerDashboard {
            constructor() {
                this.init();
                this.loadDashboardData();
                
                // 自動更新（30秒間隔）
                setInterval(() => this.loadDashboardData(), 30000);
            }
            
            init() {
                console.log('Worker Dashboard initialized');
            }
            
            async loadDashboardData() {
                try {
                    // ダッシュボードデータを取得
                    const dashboardResponse = await fetch('/api/dashboard-data');
                    const dashboardData = await dashboardResponse.json();
                    
                    // Workerデータを取得
                    const workersResponse = await fetch('/api/workers');
                    const workersData = await workersResponse.json();
                    
                    // キューデータを取得
                    const queueResponse = await fetch('/api/queue-status');
                    const queueData = await queueResponse.json();
                    
                    this.updateDashboard(dashboardData, workersData, queueData);
                    this.updateLastUpdated();
                    
                } catch (error) {
                    console.error('Error loading dashboard data:', error);
                    this.showError('データの読み込みに失敗しました');
                }
            }
            
            updateDashboard(dashboardData, workersData, queueData) {
                this.updateStatusBar(dashboardData);
                this.updateWorkers(workersData);
                this.updateQueues(queueData);
            }
            
            updateStatusBar(data) {
                const summary = data.workers_summary || {};
                const performance = data.performance_metrics || {};
                
                document.getElementById('activeWorkers').textContent = summary.total_workers || 0;
                
                // 処理中タスク数を計算
                let processingTasks = 0;
                // TODO: 実際の処理中タスク数を計算
                
                document.getElementById('processingTasks').textContent = processingTasks;
                
                // 平均処理時間を計算
                let totalAvgTime = 0;
                let workerCount = 0;
                
                Object.values(performance).forEach(perf => {
                    if (perf.avg_processing_time) {
                        totalAvgTime += perf.avg_processing_time;
                        workerCount++;
                    }
                });
                
                const avgTime = workerCount > 0 ? (totalAvgTime / workerCount).toFixed(1) : 0;
                document.getElementById('avgProcessingTime').textContent = `${avgTime}s`;
                
                // 成功率を計算
                let totalSuccessRate = 0;
                let successWorkerCount = 0;
                
                Object.values(performance).forEach(perf => {
                    if (perf.avg_success_rate !== undefined) {
                        totalSuccessRate += perf.avg_success_rate;
                        successWorkerCount++;
                    }
                });
                
                const successRate = successWorkerCount > 0 ? 
                    ((totalSuccessRate / successWorkerCount) * 100).toFixed(1) : 100;
                document.getElementById('successRate').textContent = `${successRate}%`;
            }
            
            updateWorkers(workersData) {
                const workersGrid = document.getElementById('workersGrid');
                const workers = workersData.workers || {};
                
                if (Object.keys(workers).length === 0) {
                    workersGrid.innerHTML = '<div class="loading">登録されたWorkerはありません</div>';
                    return;
                }
                
                let html = '';
                Object.entries(workers).forEach(([workerId, worker]) => {
                    const statusClass = `status-${worker.status || 'idle'}`;
                    const currentTask = worker.current_task ? 
                        `タスク: ${worker.current_task.task_id || 'unknown'}` : 
                        'アイドル状態';
                    
                    html += `
                        <div class="worker-card">
                            <div class="worker-header">
                                <div class="worker-title">🔧 ${worker.worker_type || 'Unknown'}</div>
                                <div class="worker-status ${statusClass}">${worker.status || 'idle'}</div>
                            </div>
                            <div style="color: #666; margin-bottom: 10px;">ID: ${workerId}</div>
                            <div style="margin-bottom: 15px;">${currentTask}</div>
                            <div class="worker-metrics">
                                <div class="metric">
                                    <div class="metric-label">完了タスク</div>
                                    <div class="metric-value">${worker.tasks_completed || 0}</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-label">成功率</div>
                                    <div class="metric-value">${((worker.performance_metrics?.success_rate || 1) * 100).toFixed(0)}%</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-label">平均時間</div>
                                    <div class="metric-value">${(worker.performance_metrics?.avg_processing_time || 0).toFixed(1)}s</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-label">最終更新</div>
                                    <div class="metric-value">${this.formatTime(worker.last_updated)}</div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                workersGrid.innerHTML = html;
            }
            
            updateQueues(queueData) {
                const queueGrid = document.getElementById('queueGrid');
                const queues = queueData.queues || {};
                
                let html = '';
                Object.entries(queues).forEach(([queueName, count]) => {
                    html += `
                        <div class="queue-card">
                            <div class="queue-name">${queueName}</div>
                            <div class="queue-count">${count}</div>
                        </div>
                    `;
                });
                
                queueGrid.innerHTML = html || '<div class="loading">キューデータがありません</div>';
            }
            
            formatTime(timeString) {
                if (!timeString) return '-';
                
                try {
                    const date = new Date(timeString);
                    const now = new Date();
                    const diffMs = now - date;
                    const diffMins = Math.floor(diffMs / 60000);
                    
                    if (diffMins < 1) return '今';
                    if (diffMins < 60) return `${diffMins}分前`;
                    
                    const diffHours = Math.floor(diffMins / 60);
                    if (diffHours < 24) return `${diffHours}時間前`;
                    
                    return date.toLocaleDateString('ja-JP');
                } catch (e) {
                    return '-';
                }
            }
            
            updateLastUpdated() {
                const now = new Date();
                const formatted = now.toLocaleString('ja-JP');
                document.getElementById('lastUpdated').textContent = `最終更新: ${formatted}`;
            }
            
            showError(message) {
                const workersGrid = document.getElementById('workersGrid');
                workersGrid.innerHTML = `<div class="loading" style="color: #f44336;">❌ ${message}</div>`;
            }
        }
        
        // Initialize dashboard
        const dashboard = new WorkerDashboard();
        
        // Global function for refresh button
        function loadDashboardData() {
            dashboard.loadDashboardData();
        }
    </script>
</body>
</html>'''


class WorkerDashboard:
    """Worker専用ダッシュボードサーバー"""
    
    def __init__(self, port: int = 8082):
        self.port = port
        self.monitor = WorkerStatusMonitor()
        self.server = None
        self.monitor_thread = None
        
        logger.info(f"Worker Dashboard initialized on port {port}")
    
    def start(self):
        """ダッシュボードサーバーを開始"""
        # HTTPサーバー作成
        self.server = HTTPServer(('localhost', self.port), WorkerDashboardHandler)
        
        # モニターをサーバーに添付
        self.server.monitor = self.monitor
        
        # バックグラウンド監視開始
        self.monitor.start_monitoring(interval=2.0)
        
        logger.info(f"Worker Dashboard starting on http://localhost:{self.port}")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down Worker Dashboard...")
        finally:
            self.stop()
    
    def stop(self):
        """ダッシュボードサーバーを停止"""
        if self.monitor:
            self.monitor.stop_monitoring()
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        logger.info("Worker Dashboard stopped")
    
    def _generate_dashboard_html(self) -> str:
        """ダッシュボードHTMLを生成"""
        return '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Worker Dashboard - Elders Guild</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }
        .dashboard { 
            max-width: 1400px; 
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 2px solid #eee;
            padding-bottom: 20px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status-bar {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            gap: 20px;
        }
        .status-card {
            flex: 1;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        .status-card h3 { margin-bottom: 10px; font-size: 1.1em; }
        .status-card .value { font-size: 2em; font-weight: bold; }
        .workers-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        .worker-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
            transition: all 0.3s ease;
        }
        .worker-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }
        .worker-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .worker-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }
        .worker-status {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-idle { background: #e3f2fd; color: #1976d2; }
        .status-processing { background: #fff3e0; color: #f57c00; }
        .status-error { background: #ffebee; color: #d32f2f; }
        .worker-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
        }
        .metric {
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .metric-label {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
        }
        .queue-section {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .queue-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .queue-card {
            background: linear-gradient(135deg, #4fc3f7 0%, #29b6f6 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .queue-name {
            font-size: 1.1em;
            margin-bottom: 10px;
            opacity: 0.9;
        }
        .queue-count {
            font-size: 2.5em;
            font-weight: bold;
        }
        .last-updated {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 0.9em;
        }
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 20px;
            font-weight: bold;
            z-index: 1000;
        }
        .connected { background: #4caf50; color: white; }
        .disconnected { background: #f44336; color: white; }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        .processing { animation: pulse 2s infinite; }
    </style>
</head>
<body>
    <div class="connection-status" id="connectionStatus">🔴 接続中...</div>
    
    <div class="dashboard">
        <div class="header">
            <h1>🤖 Worker Dashboard</h1>
            <p>Elders Guild Worker リアルタイム監視システム</p>
        </div>
        
        <div class="status-bar" id="statusBar">
            <div class="status-card">
                <h3>🔧 アクティブWorker</h3>
                <div class="value" id="activeWorkers">-</div>
            </div>
            <div class="status-card">
                <h3>📋 処理中タスク</h3>
                <div class="value" id="processingTasks">-</div>
            </div>
            <div class="status-card">
                <h3>⏱️ 平均処理時間</h3>
                <div class="value" id="avgProcessingTime">-</div>
            </div>
            <div class="status-card">
                <h3>✅ 成功率</h3>
                <div class="value" id="successRate">-</div>
            </div>
        </div>
        
        <div class="workers-grid" id="workersGrid">
            <!-- Worker cards will be dynamically generated -->
        </div>
        
        <div class="queue-section">
            <h2>📡 キューステータス</h2>
            <div class="queue-grid" id="queueGrid">
                <!-- Queue cards will be dynamically generated -->
            </div>
        </div>
        
        <div class="last-updated" id="lastUpdated">
            最終更新: -
        </div>
    </div>

    <script>
        class WorkerDashboard {
            constructor() {
                this.ws = null;
                this.reconnectInterval = 3000;
                this.data = null;
                this.init();
            }
            
            init() {
                this.connectWebSocket();
                this.updateConnectionStatus('connecting');
            }
            
            connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                this.ws = new WebSocket(wsUrl);
                
                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.updateConnectionStatus('connected');
                    this.ws.send(JSON.stringify({type: 'subscribe'}));
                };
                
                this.ws.onmessage = (event) => {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                };
                
                this.ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    this.updateConnectionStatus('disconnected');
                    setTimeout(() => this.connectWebSocket(), this.reconnectInterval);
                };
                
                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.updateConnectionStatus('error');
                };
            }
            
            handleMessage(message) {
                if (message.type === 'dashboard_update') {
                    this.data = message.data;
                    this.updateDashboard();
                    this.updateLastUpdated(message.timestamp);
                }
            }
            
            updateConnectionStatus(status) {
                const statusEl = document.getElementById('connectionStatus');
                
                switch(status) {
                    case 'connected':
                        statusEl.textContent = '🟢 接続済み';
                        statusEl.className = 'connection-status connected';
                        break;
                    case 'connecting':
                        statusEl.textContent = '🟡 接続中...';
                        statusEl.className = 'connection-status';
                        break;
                    case 'disconnected':
                    case 'error':
                        statusEl.textContent = '🔴 切断';
                        statusEl.className = 'connection-status disconnected';
                        break;
                }
            }
            
            updateDashboard() {
                if (!this.data) return;
                
                this.updateStatusBar();
                this.updateWorkers();
                this.updateQueues();
            }
            
            updateStatusBar() {
                const summary = this.data.workers_summary || {};
                const performance = this.data.performance_metrics || {};
                
                document.getElementById('activeWorkers').textContent = summary.total_workers || 0;
                
                // 処理中タスク数を計算
                let processingTasks = 0;
                // TODO: 実際の処理中タスク数を計算
                
                document.getElementById('processingTasks').textContent = processingTasks;
                
                // 平均処理時間を計算
                let totalAvgTime = 0;
                let workerCount = 0;
                
                Object.values(performance).forEach(perf => {
                    if (perf.avg_processing_time) {
                        totalAvgTime += perf.avg_processing_time;
                        workerCount++;
                    }
                });
                
                const avgTime = workerCount > 0 ? (totalAvgTime / workerCount).toFixed(1) : 0;
                document.getElementById('avgProcessingTime').textContent = `${avgTime}s`;
                
                // 成功率を計算
                let totalSuccessRate = 0;
                let successWorkerCount = 0;
                
                Object.values(performance).forEach(perf => {
                    if (perf.avg_success_rate !== undefined) {
                        totalSuccessRate += perf.avg_success_rate;
                        successWorkerCount++;
                    }
                });
                
                const successRate = successWorkerCount > 0 ? 
                    ((totalSuccessRate / successWorkerCount) * 100).toFixed(1) : 100;
                document.getElementById('successRate').textContent = `${successRate}%`;
            }
            
            updateWorkers() {
                // This would be populated with actual worker data
                // For now, showing placeholder
                const workersGrid = document.getElementById('workersGrid');
                workersGrid.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">Worker データを読み込み中...</div>';
            }
            
            updateQueues() {
                const queueStatus = this.data.queue_status || {};
                const queueGrid = document.getElementById('queueGrid');
                
                let html = '';
                Object.entries(queueStatus).forEach(([queueName, count]) => {
                    html += `
                        <div class="queue-card">
                            <div class="queue-name">${queueName}</div>
                            <div class="queue-count">${count}</div>
                        </div>
                    `;
                });
                
                queueGrid.innerHTML = html;
            }
            
            updateLastUpdated(timestamp) {
                const date = new Date(timestamp);
                const formatted = date.toLocaleString('ja-JP');
                document.getElementById('lastUpdated').textContent = `最終更新: ${formatted}`;
            }
        }
        
        // Initialize dashboard
        const dashboard = new WorkerDashboard();
    </script>
</body>
</html>'''
    

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    dashboard = WorkerDashboard(port=8082)
    
    try:
        dashboard.start()
    except KeyboardInterrupt:
        print("\nWorker Dashboard stopped.")