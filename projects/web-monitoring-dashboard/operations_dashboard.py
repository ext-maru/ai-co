#!/usr/bin/env python3
"""
運用監視ダッシュボード
リアルタイム監視・アラート・自動復旧機能
"""

import time
import asyncio
import logging
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import sys
from collections import deque, defaultdict
import psutil
import sqlite3

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, Blueprint, jsonify, request, render_template_string
# from flask_socketio import SocketIO, emit  # Optional WebSocket support

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 運用ダッシュボードBlueprint
operations_dashboard = Blueprint('operations_dashboard', __name__, url_prefix='/api/ops')

class OperationsMonitor:
    """運用監視システム"""
    
    def __init__(self):
        # 監視メトリクス
        self.metrics = {
            'system': deque(maxlen=1000),
            'application': deque(maxlen=1000),
            'errors': deque(maxlen=500),
            'alerts': deque(maxlen=200)
        }
        
        # アラート設定
        self.alert_rules = {
            'cpu_usage': {'threshold': 80, 'severity': 'warning'},
            'memory_usage': {'threshold': 85, 'severity': 'warning'},
            'disk_usage': {'threshold': 90, 'severity': 'critical'},
            'error_rate': {'threshold': 5, 'severity': 'critical'},
            'response_time': {'threshold': 1000, 'severity': 'warning'}
        }
        
        # 監視状態
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # WebSocketクライアント
        self.websocket_clients = set()
        
        # データベース接続
        self.db_path = "/tmp/operations_monitor.db"
        self._init_database()
        
        # 自動復旧設定
        self.auto_recovery_enabled = True
        self.recovery_actions = {
            'high_memory_usage': self._recover_memory,
            'high_cpu_usage': self._recover_cpu,
            'disk_full': self._recover_disk,
            'service_down': self._recover_service
        }
        
        # 履歴データ
        self.historical_data = {
            'daily_stats': [],
            'weekly_trends': [],
            'incident_history': []
        }
    
    def start_monitoring(self):
        """監視開始"""
        if self.monitoring_active:
            logger.warning("監視は既に実行中です")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info("運用監視を開始しました")
    
    def stop_monitoring(self):
        """監視停止"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("運用監視を停止しました")
    
    def _monitoring_loop(self):
        """監視ループ"""
        while self.monitoring_active:
            try:
                # システムメトリクス収集
                system_metrics = self._collect_system_metrics()
                self.metrics['system'].append(system_metrics)
                
                # アプリケーションメトリクス収集
                app_metrics = self._collect_application_metrics()
                self.metrics['application'].append(app_metrics)
                
                # アラートチェック
                alerts = self._check_alerts(system_metrics, app_metrics)
                for alert in alerts:
                    self.metrics['alerts'].append(alert)
                    self._handle_alert(alert)
                
                # データベース保存
                self._save_metrics_to_db(system_metrics, app_metrics)
                
                # WebSocket配信
                self._broadcast_metrics({
                    'system': system_metrics,
                    'application': app_metrics,
                    'alerts': list(self.metrics['alerts'])[-10:]  # 最新10件
                })
                
                time.sleep(10)  # 10秒間隔
                
            except Exception as e:
                logger.error(f"監視ループエラー: {e}")
                time.sleep(5)
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス収集"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # ディスク使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # ネットワーク統計
            network = psutil.net_io_counters()
            
            # プロセス数
            process_count = len(psutil.pids())
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': round(cpu_percent, 2),
                'memory_usage': round(memory_percent, 2),
                'disk_usage': round(disk_percent, 2),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_total_gb': round(disk.total / (1024**3), 2),
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'process_count': process_count,
                'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            }
            
        except Exception as e:
            logger.error(f"システムメトリクス収集エラー: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _collect_application_metrics(self) -> Dict[str, Any]:
        """アプリケーションメトリクス収集"""
        try:
            # 模擬アプリケーションメトリクス
            # 実際の実装では各サービスのAPIから取得
            import random
            
            base_response_time = 200 + random.gauss(0, 50)
            base_throughput = 150 + random.gauss(0, 30)
            base_error_rate = 0.5 + random.gauss(0, 0.2)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'response_time_ms': max(50, round(base_response_time, 2)),
                'throughput_rps': max(10, round(base_throughput, 2)),
                'error_rate_percent': max(0, round(base_error_rate, 3)),
                'active_connections': random.randint(50, 200),
                'queue_length': random.randint(0, 25),
                'cache_hit_rate': round(85 + random.gauss(0, 5), 2),
                'database_connections': random.randint(5, 20),
                'memory_usage_mb': random.randint(500, 1500),
                'gc_collections': random.randint(0, 5)
            }
            
        except Exception as e:
            logger.error(f"アプリケーションメトリクス収集エラー: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _check_alerts(self, system_metrics: Dict[str, Any], 
                     app_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """アラートチェック"""
        alerts = []
        current_time = datetime.now().isoformat()
        
        # システムアラート
        if system_metrics.get('cpu_usage', 0) > self.alert_rules['cpu_usage']['threshold']:
            alerts.append({
                'id': f"cpu_alert_{int(time.time())}",
                'type': 'cpu_usage',
                'severity': self.alert_rules['cpu_usage']['severity'],
                'message': f"CPU使用率が高いです: {system_metrics['cpu_usage']}%",
                'value': system_metrics['cpu_usage'],
                'threshold': self.alert_rules['cpu_usage']['threshold'],
                'timestamp': current_time
            })
        
        if system_metrics.get('memory_usage', 0) > self.alert_rules['memory_usage']['threshold']:
            alerts.append({
                'id': f"memory_alert_{int(time.time())}",
                'type': 'memory_usage',
                'severity': self.alert_rules['memory_usage']['severity'],
                'message': f"メモリ使用率が高いです: {system_metrics['memory_usage']}%",
                'value': system_metrics['memory_usage'],
                'threshold': self.alert_rules['memory_usage']['threshold'],
                'timestamp': current_time
            })
        
        if system_metrics.get('disk_usage', 0) > self.alert_rules['disk_usage']['threshold']:
            alerts.append({
                'id': f"disk_alert_{int(time.time())}",
                'type': 'disk_usage',
                'severity': self.alert_rules['disk_usage']['severity'],
                'message': f"ディスク使用率が高いです: {system_metrics['disk_usage']}%",
                'value': system_metrics['disk_usage'],
                'threshold': self.alert_rules['disk_usage']['threshold'],
                'timestamp': current_time
            })
        
        # アプリケーションアラート
        if app_metrics.get('error_rate_percent', 0) > self.alert_rules['error_rate']['threshold']:
            alerts.append({
                'id': f"error_rate_alert_{int(time.time())}",
                'type': 'error_rate',
                'severity': self.alert_rules['error_rate']['severity'],
                'message': f"エラー率が高いです: {app_metrics['error_rate_percent']}%",
                'value': app_metrics['error_rate_percent'],
                'threshold': self.alert_rules['error_rate']['threshold'],
                'timestamp': current_time
            })
        
        if app_metrics.get('response_time_ms', 0) > self.alert_rules['response_time']['threshold']:
            alerts.append({
                'id': f"response_time_alert_{int(time.time())}",
                'type': 'response_time',
                'severity': self.alert_rules['response_time']['severity'],
                'message': f"応答時間が遅いです: {app_metrics['response_time_ms']}ms",
                'value': app_metrics['response_time_ms'],
                'threshold': self.alert_rules['response_time']['threshold'],
                'timestamp': current_time
            })
        
        return alerts
    
    def _handle_alert(self, alert: Dict[str, Any]):
        """アラート処理"""
        logger.warning(f"アラート発生: {alert['message']}")
        
        # 自動復旧実行
        if self.auto_recovery_enabled:
            recovery_action = None
            
            if alert['type'] == 'memory_usage':
                recovery_action = 'high_memory_usage'
            elif alert['type'] == 'cpu_usage':
                recovery_action = 'high_cpu_usage'
            elif alert['type'] == 'disk_usage':
                recovery_action = 'disk_full'
            
            if recovery_action and recovery_action in self.recovery_actions:
                try:
                    self.recovery_actions[recovery_action](alert)
                    logger.info(f"自動復旧を実行しました: {recovery_action}")
                except Exception as e:
                    logger.error(f"自動復旧エラー: {e}")
    
    def _recover_memory(self, alert: Dict[str, Any]):
        """メモリ復旧処理"""
        logger.info("メモリ使用率削減処理を実行中...")
        # 実際の実装例:
        # - 不要なキャッシュクリア
        # - アイドルプロセス終了
        # - ガベージコレクション強制実行
        pass
    
    def _recover_cpu(self, alert: Dict[str, Any]):
        """CPU復旧処理"""
        logger.info("CPU使用率削減処理を実行中...")
        # 実際の実装例:
        # - 重い処理の一時停止
        # - 優先度調整
        # - 負荷分散
        pass
    
    def _recover_disk(self, alert: Dict[str, Any]):
        """ディスク復旧処理"""
        logger.info("ディスク容量確保処理を実行中...")
        # 実際の実装例:
        # - 古いログファイル削除
        # - 一時ファイルクリーンアップ
        # - アーカイブ実行
        pass
    
    def _recover_service(self, alert: Dict[str, Any]):
        """サービス復旧処理"""
        logger.info("サービス復旧処理を実行中...")
        # 実際の実装例:
        # - サービス再起動
        # - ヘルスチェック
        # - フェイルオーバー
        pass
    
    def _broadcast_metrics(self, data: Dict[str, Any]):
        """WebSocketでメトリクス配信"""
        # 実際の実装ではSocketIOを使用
        # ここでは簡易実装
        pass
    
    def _init_database(self):
        """データベース初期化"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # システムメトリクステーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    process_count INTEGER
                )
            """)
            
            # アプリケーションメトリクステーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    response_time_ms REAL,
                    throughput_rps REAL,
                    error_rate_percent REAL,
                    active_connections INTEGER
                )
            """)
            
            # アラートテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT,
                    type TEXT,
                    severity TEXT,
                    message TEXT,
                    value REAL,
                    threshold REAL,
                    timestamp TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"データベース初期化エラー: {e}")
    
    def _save_metrics_to_db(self, system_metrics: Dict[str, Any], 
                           app_metrics: Dict[str, Any]):
        """メトリクスをデータベースに保存"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # システムメトリクス保存
            cursor.execute("""
                INSERT INTO system_metrics 
                (timestamp, cpu_usage, memory_usage, disk_usage, process_count)
                VALUES (?, ?, ?, ?, ?)
            """, (
                system_metrics.get('timestamp'),
                system_metrics.get('cpu_usage'),
                system_metrics.get('memory_usage'),
                system_metrics.get('disk_usage'),
                system_metrics.get('process_count')
            ))
            
            # アプリケーションメトリクス保存
            cursor.execute("""
                INSERT INTO app_metrics 
                (timestamp, response_time_ms, throughput_rps, error_rate_percent, active_connections)
                VALUES (?, ?, ?, ?, ?)
            """, (
                app_metrics.get('timestamp'),
                app_metrics.get('response_time_ms'),
                app_metrics.get('throughput_rps'),
                app_metrics.get('error_rate_percent'),
                app_metrics.get('active_connections')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"データベース保存エラー: {e}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """現在のシステム状態取得"""
        # 最新のメトリクス
        latest_system = list(self.metrics['system'])[-1] if self.metrics['system'] else {}
        latest_app = list(self.metrics['application'])[-1] if self.metrics['application'] else {}
        recent_alerts = list(self.metrics['alerts'])[-5:]  # 最新5件
        
        # ヘルススコア計算
        health_score = self._calculate_health_score(latest_system, latest_app)
        
        return {
            'monitoring_active': self.monitoring_active,
            'health_score': health_score,
            'system_metrics': latest_system,
            'application_metrics': latest_app,
            'recent_alerts': recent_alerts,
            'alert_count': len(self.metrics['alerts']),
            'auto_recovery_enabled': self.auto_recovery_enabled,
            'uptime_hours': self._get_uptime_hours()
        }
    
    def _calculate_health_score(self, system_metrics: Dict[str, Any], 
                               app_metrics: Dict[str, Any]) -> float:
        """ヘルススコア計算"""
        score = 100.0
        
        # システムメトリクスによる減点
        cpu_usage = system_metrics.get('cpu_usage', 0)
        memory_usage = system_metrics.get('memory_usage', 0)
        disk_usage = system_metrics.get('disk_usage', 0)
        
        if cpu_usage > 80:
            score -= min(20, (cpu_usage - 80) * 2)
        if memory_usage > 85:
            score -= min(15, (memory_usage - 85) * 3)
        if disk_usage > 90:
            score -= min(25, (disk_usage - 90) * 5)
        
        # アプリケーションメトリクスによる減点
        error_rate = app_metrics.get('error_rate_percent', 0)
        response_time = app_metrics.get('response_time_ms', 0)
        
        if error_rate > 1:
            score -= min(15, error_rate * 3)
        if response_time > 500:
            score -= min(10, (response_time - 500) / 100)
        
        return max(0, round(score, 1))
    
    def _get_uptime_hours(self) -> float:
        """稼働時間取得"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            return round(uptime_seconds / 3600, 1)
        except:
            return 0.0
    
    def get_historical_data(self, hours: int = 24) -> Dict[str, Any]:
        """履歴データ取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 指定時間前からのデータ取得
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # システムメトリクス履歴
            cursor.execute("""
                SELECT timestamp, cpu_usage, memory_usage, disk_usage
                FROM system_metrics
                WHERE timestamp > ?
                ORDER BY timestamp
            """, (cutoff_time,))
            
            system_history = [
                {
                    'timestamp': row[0],
                    'cpu_usage': row[1],
                    'memory_usage': row[2],
                    'disk_usage': row[3]
                }
                for row in cursor.fetchall()
            ]
            
            # アプリケーションメトリクス履歴
            cursor.execute("""
                SELECT timestamp, response_time_ms, throughput_rps, error_rate_percent
                FROM app_metrics
                WHERE timestamp > ?
                ORDER BY timestamp
            """, (cutoff_time,))
            
            app_history = [
                {
                    'timestamp': row[0],
                    'response_time_ms': row[1],
                    'throughput_rps': row[2],
                    'error_rate_percent': row[3]
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                'system_history': system_history,
                'application_history': app_history,
                'period_hours': hours
            }
            
        except Exception as e:
            logger.error(f"履歴データ取得エラー: {e}")
            return {'error': str(e)}

class AlertManager:
    """アラート管理システム"""
    
    def __init__(self):
        self.notification_channels = {
            'email': self._send_email_notification,
            'slack': self._send_slack_notification,
            'webhook': self._send_webhook_notification
        }
        
        self.alert_suppression = {}  # アラート抑制
        self.escalation_rules = {}   # エスカレーションルール
    
    def send_notification(self, alert: Dict[str, Any], channels: List[str]):
        """通知送信"""
        for channel in channels:
            if channel in self.notification_channels:
                try:
                    self.notification_channels[channel](alert)
                except Exception as e:
                    logger.error(f"通知送信エラー ({channel}): {e}")
    
    def _send_email_notification(self, alert: Dict[str, Any]):
        """Email通知"""
        logger.info(f"Email通知: {alert['message']}")
        # 実際の実装ではSMTPで送信
    
    def _send_slack_notification(self, alert: Dict[str, Any]):
        """Slack通知"""
        logger.info(f"Slack通知: {alert['message']}")
        # 実際の実装ではSlack APIを使用
    
    def _send_webhook_notification(self, alert: Dict[str, Any]):
        """Webhook通知"""
        logger.info(f"Webhook通知: {alert['message']}")
        # 実際の実装ではHTTP POSTで送信

# グローバルインスタンス
operations_monitor = OperationsMonitor()
alert_manager = AlertManager()

# API エンドポイント

@operations_dashboard.route('/status')
def get_status():
    """システム状態取得"""
    try:
        status = operations_monitor.get_current_status()
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@operations_dashboard.route('/metrics/history')
def get_metrics_history():
    """メトリクス履歴取得"""
    try:
        hours = int(request.args.get('hours', 24))
        history = operations_monitor.get_historical_data(hours)
        return jsonify(history)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@operations_dashboard.route('/monitoring/start', methods=['POST'])
def start_monitoring():
    """監視開始"""
    try:
        operations_monitor.start_monitoring()
        return jsonify({'success': True, 'message': '監視を開始しました'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@operations_dashboard.route('/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """監視停止"""
    try:
        operations_monitor.stop_monitoring()
        return jsonify({'success': True, 'message': '監視を停止しました'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@operations_dashboard.route('/alerts')
def get_alerts():
    """アラート一覧取得"""
    try:
        limit = int(request.args.get('limit', 50))
        alerts = list(operations_monitor.metrics['alerts'])[-limit:]
        return jsonify({'alerts': alerts, 'total': len(operations_monitor.metrics['alerts'])})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@operations_dashboard.route('/dashboard')
def dashboard_html():
    """ダッシュボードHTML"""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Elders Guild - 運用ダッシュボード</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric { display: flex; justify-content: space-between; margin: 10px 0; }
            .health-score { font-size: 2em; font-weight: bold; color: #4CAF50; }
            .alert { padding: 10px; margin: 5px 0; border-radius: 4px; }
            .alert.warning { background: #FFF3CD; border-left: 4px solid #FFC107; }
            .alert.critical { background: #F8D7DA; border-left: 4px solid #DC3545; }
            .status { display: inline-block; padding: 4px 8px; border-radius: 4px; color: white; }
            .status.active { background: #28A745; }
            .status.inactive { background: #6C757D; }
        </style>
    </head>
    <body>
        <h1>🖥️ Elders Guild - 運用ダッシュボード</h1>
        
        <div class="dashboard">
            <div class="card">
                <h3>システム状態</h3>
                <div class="health-score" id="healthScore">-</div>
                <div class="metric">
                    <span>監視状態:</span>
                    <span class="status" id="monitoringStatus">-</span>
                </div>
                <div class="metric">
                    <span>稼働時間:</span>
                    <span id="uptime">-</span>
                </div>
            </div>
            
            <div class="card">
                <h3>リソース使用率</h3>
                <div class="metric">
                    <span>CPU:</span>
                    <span id="cpuUsage">-</span>
                </div>
                <div class="metric">
                    <span>メモリ:</span>
                    <span id="memoryUsage">-</span>
                </div>
                <div class="metric">
                    <span>ディスク:</span>
                    <span id="diskUsage">-</span>
                </div>
            </div>
            
            <div class="card">
                <h3>アプリケーション</h3>
                <div class="metric">
                    <span>応答時間:</span>
                    <span id="responseTime">-</span>
                </div>
                <div class="metric">
                    <span>スループット:</span>
                    <span id="throughput">-</span>
                </div>
                <div class="metric">
                    <span>エラー率:</span>
                    <span id="errorRate">-</span>
                </div>
            </div>
            
            <div class="card">
                <h3>最近のアラート</h3>
                <div id="recentAlerts">
                    <p>アラートなし</p>
                </div>
            </div>
        </div>
        
        <script>
            function updateDashboard() {
                fetch('/api/ops/status')
                    .then(response => response.json())
                    .then(data => {
                        // ヘルススコア
                        document.getElementById('healthScore').textContent = data.health_score + '%';
                        
                        // 監視状態
                        const statusEl = document.getElementById('monitoringStatus');
                        if (data.monitoring_active) {
                            statusEl.textContent = 'アクティブ';
                            statusEl.className = 'status active';
                        } else {
                            statusEl.textContent = '停止中';
                            statusEl.className = 'status inactive';
                        }
                        
                        // 稼働時間
                        document.getElementById('uptime').textContent = data.uptime_hours + ' 時間';
                        
                        // システムメトリクス
                        const sys = data.system_metrics;
                        document.getElementById('cpuUsage').textContent = (sys.cpu_usage || 0) + '%';
                        document.getElementById('memoryUsage').textContent = (sys.memory_usage || 0) + '%';
                        document.getElementById('diskUsage').textContent = (sys.disk_usage || 0) + '%';
                        
                        // アプリケーションメトリクス
                        const app = data.application_metrics;
                        document.getElementById('responseTime').textContent = (app.response_time_ms || 0) + 'ms';
                        document.getElementById('throughput').textContent = (app.throughput_rps || 0) + ' RPS';
                        document.getElementById('errorRate').textContent = (app.error_rate_percent || 0) + '%';
                        
                        // アラート
                        const alertsEl = document.getElementById('recentAlerts');
                        if (data.recent_alerts && data.recent_alerts.length > 0) {
                            alertsEl.innerHTML = data.recent_alerts.map(alert => 
                                `<div class="alert ${alert.severity}">
                                    <strong>${alert.type}:</strong> ${alert.message}
                                </div>`
                            ).join('');
                        } else {
                            alertsEl.innerHTML = '<p>アラートなし</p>';
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                    });
            }
            
            // 初回更新
            updateDashboard();
            
            // 10秒間隔で更新
            setInterval(updateDashboard, 10000);
        </script>
    </body>
    </html>
    """
    
    return template

@operations_dashboard.route('/health')
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'status': 'healthy',
        'service': 'operations_dashboard',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == "__main__":
    # テスト実行
    from flask import Flask
    
    app = Flask(__name__)
    app.register_blueprint(operations_dashboard)
    
    print("=== 運用監視ダッシュボード ===")
    print("エンドポイント:")
    print("- GET  /api/ops/status")
    print("- GET  /api/ops/metrics/history")
    print("- POST /api/ops/monitoring/start")
    print("- POST /api/ops/monitoring/stop")
    print("- GET  /api/ops/alerts")
    print("- GET  /api/ops/dashboard")
    
    # 監視開始
    operations_monitor.start_monitoring()
    
    print("\n監視ダッシュボード: http://localhost:5007/api/ops/dashboard")
    
    try:
        app.run(debug=True, port=5007)
    finally:
        operations_monitor.stop_monitoring()