#!/usr/bin/env python3
"""
Elders Guild Webダッシュボード
システム状態をブラウザで監視
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import sqlite3
import pika
import psutil
from typing import Dict, Any, List
from libs.env_config import get_config

class DashboardHandler(BaseHTTPRequestHandler):
    """HTTPリクエストハンドラー"""
    
    def do_GET(self):
        """GETリクエストの処理"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_dashboard()
        elif parsed_path.path == '/api/status':
            self.serve_api_status()
        elif parsed_path.path == '/api/workers':
            self.serve_api_workers()
        elif parsed_path.path == '/api/queues':
            self.serve_api_queues()
        elif parsed_path.path == '/api/tasks/recent':
            self.serve_api_recent_tasks()
        elif parsed_path.path == '/api/elder/council':
            self.serve_api_elder_council()
        elif parsed_path.path == '/api/metrics':
            self.serve_api_metrics()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """ダッシュボードHTMLを提供"""
        html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elders Guild Dashboard</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Orbitron', monospace;
            background: linear-gradient(45deg, #87CEEB 0%, #98FB98 25%, #F0E68C 50%, #FFB6C1 75%, #DDA0DD 100%);
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
            color: #2F4F4F;
            line-height: 1.6;
            min-height: 100vh;
            position: relative;
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                repeating-linear-gradient(0deg, transparent, transparent 15px, rgba(255,255,255,0.1) 16px),
                repeating-linear-gradient(90deg, transparent, transparent 15px, rgba(255,255,255,0.1) 16px);
            pointer-events: none;
            z-index: -1;
        }
        
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        .header {
            background: linear-gradient(135deg, #4169E1 0%, #00CED1 100%);
            border: 4px solid #FFFFFF;
            border-radius: 0;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 
                8px 8px 0px #1E90FF,
                16px 16px 0px #87CEEB;
            position: relative;
            image-rendering: pixelated;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 10px;
            left: 10px;
            right: 10px;
            bottom: 10px;
            background: repeating-linear-gradient(
                45deg,
                transparent,
                transparent 2px,
                rgba(255,255,255,0.1) 2px,
                rgba(255,255,255,0.1) 4px
            );
            pointer-events: none;
        }
        
        h1 { 
            font-family: 'Orbitron', monospace;
            font-size: 2.5em; 
            font-weight: 900;
            text-align: center;
            color: #FFFFFF;
            text-shadow: 
                4px 4px 0px #1E90FF,
                8px 8px 0px #87CEEB;
            z-index: 1;
            position: relative;
            letter-spacing: 2px;
        }
        
        .elder-council {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .elder-card {
            background: #FFFFFF;
            border: 4px solid #2F4F4F;
            border-radius: 0;
            padding: 20px;
            transition: all 0.2s ease;
            position: relative;
            image-rendering: pixelated;
        }
        
        .elder-card.knowledge {
            background: linear-gradient(135deg, #DDA0DD 0%, #E6E6FA 100%);
            box-shadow: 6px 6px 0px #9370DB;
        }
        
        .elder-card.task {
            background: linear-gradient(135deg, #F0E68C 0%, #FFFFE0 100%);
            box-shadow: 6px 6px 0px #DAA520;
        }
        
        .elder-card.incident {
            background: linear-gradient(135deg, #FFB6C1 0%, #FFE4E1 100%);
            box-shadow: 6px 6px 0px #DC143C;
        }
        
        .elder-card.rag {
            background: linear-gradient(135deg, #98FB98 0%, #F0FFF0 100%);
            box-shadow: 6px 6px 0px #32CD32;
        }
        
        .elder-card:hover {
            transform: translate(-2px, -2px);
            box-shadow: 8px 8px 0px #2F4F4F;
        }
        
        .elder-card h3 {
            font-family: 'Orbitron', monospace;
            font-size: 1.2em;
            font-weight: 700;
            margin-bottom: 15px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .elder-card.knowledge h3 { color: #4B0082; }
        .elder-card.task h3 { color: #B8860B; }
        .elder-card.incident h3 { color: #DC143C; }
        .elder-card.rag h3 { color: #228B22; }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 8px 0;
            padding: 10px;
            background: rgba(255, 255, 255, 0.9);
            border: 2px solid #2F4F4F;
            border-radius: 0;
            box-shadow: 2px 2px 0px #696969;
        }
        
        .metric-value {
            font-size: 1.4em;
            font-weight: 700;
            color: #2F4F4F;
            text-shadow: 1px 1px 0px #FFFFFF;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 0;
            margin-right: 8px;
            animation: pixelBlink 1s infinite;
            image-rendering: pixelated;
        }
        
        .status-healthy { 
            background: #32CD32;
            border: 1px solid #228B22;
            box-shadow: 1px 1px 0px #006400;
        }
        .status-warning { 
            background: #FFA500;
            border: 1px solid #FF8C00;
            box-shadow: 1px 1px 0px #FF6347;
        }
        .status-error { 
            background: #FF6B6B;
            border: 1px solid #DC143C;
            box-shadow: 1px 1px 0px #B22222;
        }
        
        @keyframes pixelBlink {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .quest-log {
            background: linear-gradient(135deg, #87CEEB 0%, #B0E0E6 100%);
            border: 4px solid #2F4F4F;
            border-radius: 0;
            padding: 20px;
            max-height: 600px;
            overflow-y: auto;
            position: relative;
            box-shadow: 6px 6px 0px #4682B4;
        }
        
        .quest-log::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                repeating-linear-gradient(
                    90deg,
                    transparent,
                    transparent 32px,
                    rgba(255, 255, 255, 0.2) 32px,
                    rgba(255, 255, 255, 0.2) 34px
                );
            pointer-events: none;
        }
        
        .quest-log h3 {
            font-family: 'Orbitron', monospace;
            color: #2F4F4F;
            font-size: 1.3em;
            font-weight: 700;
            margin-bottom: 20px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .quest-item {
            padding: 12px;
            margin: 8px 0;
            background: rgba(255, 255, 255, 0.9);
            border: 2px solid #2F4F4F;
            border-radius: 0;
            transition: all 0.2s ease;
            position: relative;
            box-shadow: 2px 2px 0px #696969;
        }
        
        .quest-item:hover {
            transform: translate(-1px, -1px);
            box-shadow: 3px 3px 0px #696969;
        }
        
        .quest-item::before {
            content: '⛏️';
            position: absolute;
            left: -20px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 1.2em;
            background: #FFFFFF;
            padding: 2px;
            border: 2px solid #2F4F4F;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.2em;
            color: #2F4F4F;
            font-family: 'Orbitron', monospace;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: linear-gradient(135deg, #32CD32 0%, #228B22 100%);
            color: #FFFFFF;
            border: 4px solid #2F4F4F;
            padding: 15px 25px;
            border-radius: 0;
            font-size: 1em;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 4px 4px 0px #006400;
            transition: all 0.2s ease;
            font-family: 'Orbitron', monospace;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .refresh-btn:hover {
            transform: translate(-2px, -2px);
            box-shadow: 6px 6px 0px #006400;
        }
        
        .refresh-btn:active {
            transform: translate(2px, 2px);
            box-shadow: 2px 2px 0px #006400;
        }
        
        /* マイクラ風スクロールバー */
        ::-webkit-scrollbar {
            width: 16px;
        }
        
        ::-webkit-scrollbar-track {
            background: #87CEEB;
            border: 2px solid #2F4F4F;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #32CD32;
            border: 2px solid #2F4F4F;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #228B22;
        }
        
        /* レスポンシブ対応 */
        @media (max-width: 768px) {
            .elder-council {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 1.8em;
            }
            
            .container {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧾 Elders Guild マインクラフトサーバー</h1>
        </div>
        
        <div class="elder-council" id="elderCouncil">
            <div class="loading">4賢者の知恵を結集中...</div>
        </div>
        
        <div class="quest-log" id="questLog">
            <h3>📜 クエストログ - 最近の冒険</h3>
            <div class="loading">冒険の記録を読み込み中...</div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshData()">🔄 リスポーン</button>
    
    <script>
        async function fetchData() {
            try {
                const [status, workers, queues, tasks] = await Promise.all([
                    fetch('/api/status').then(r => r.json()),
                    fetch('/api/workers').then(r => r.json()),
                    fetch('/api/queues').then(r => r.json()),
                    fetch('/api/tasks/recent').then(r => r.json())
                ]);
                
                updateElderCouncil(status, workers, queues);
                updateQuestLog(tasks);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }
        
        function updateElderCouncil(status, workers, queues) {
            const council = document.getElementById('elderCouncil');
            
            // ワーカータイプの日本語マッピング
            const workerNames = {
                'task_worker': '🔨 ドワーフ工房',
                'pm_worker': '🛡️ 騎士団',
                'result_worker': '🧝‍♂️ エルフの森',
                'dialog_worker': '🧙‍♂️ ウィザーズ'
            };
            
            // キュー名の日本語マッピング
            const queueNames = {
                'ai_tasks': '⚒️ 鍛造依頼',
                'ai_pm': '⚔️ 討伐任務',
                'ai_results': '🌿 森の報告',
                'ai_dialog': '📜 魔法研究'
            };
            
            council.innerHTML = `
                <div class="elder-card knowledge">
                    <h3>📚 ナレッジ賢者</h3>
                    <div class="metric">
                        <span>知恵の蓄積</span>
                        <span class="metric-value">${status.health_score}%</span>
                    </div>
                    <div class="metric">
                        <span>学習進捗</span>
                        <span class="metric-value">∞</span>
                    </div>
                </div>
                
                <div class="elder-card task">
                    <h3>📋 タスク賢者</h3>
                    <div class="metric">
                        <span>CPU神力</span>
                        <span class="metric-value">${status.cpu_percent}%</span>
                    </div>
                    <div class="metric">
                        <span>実行効率</span>
                        <span class="metric-value">${Math.max(0, 100 - status.cpu_percent)}%</span>
                    </div>
                </div>
                
                <div class="elder-card incident">
                    <h3>🚨 インシデント賢者</h3>
                    <div class="metric">
                        <span>守護力</span>
                        <span class="metric-value">${Math.max(0, 100 - status.memory_percent)}%</span>
                    </div>
                    <div class="metric">
                        <span>警戒レベル</span>
                        <span class="metric-value">${status.memory_percent < 80 ? '🟢' : status.memory_percent < 90 ? '🟡' : '🔴'}</span>
                    </div>
                </div>
                
                <div class="elder-card rag">
                    <h3>🔍 RAG賢者</h3>
                    <div class="metric">
                        <span>探索精度</span>
                        <span class="metric-value">${status.health_score}%</span>
                    </div>
                    <div class="metric">
                        <span>発見率</span>
                        <span class="metric-value">95%</span>
                    </div>
                </div>
            `;
            
            // ワーカー情報を各カードに追加
            Object.entries(workers).forEach(([type, info]) => {
                const workerName = workerNames[type] || type;
                const card = council.querySelector(`.elder-card.${type.includes('task') ? 'task' : type.includes('pm') ? 'incident' : type.includes('result') ? 'rag' : 'knowledge'}`);
                if (card) {
                    card.innerHTML += `
                        <div class="metric">
                            <span>
                                <span class="status-indicator status-healthy"></span>
                                ${workerName}
                            </span>
                            <span class="metric-value">${info.count}</span>
                        </div>
                    `;
                }
            });
        }
        
        function updateQuestLog(tasks) {
            const log = document.getElementById('questLog');
            if (tasks.length === 0) {
                log.innerHTML = '<h3>📜 クエストログ - 最近の冒険</h3><p style="text-align: center; color: #d4af37; font-style: italic;">まだ冒険の記録はありません</p>';
                return;
            }
            
            // タスクタイプの日本語マッピング
            const taskTypes = {
                'task': '🔨 製作クエスト',
                'pm': '⚔️ 討伐クエスト',
                'result': '🌿 調査クエスト',
                'dialog': '📜 研究クエスト'
            };
            
            // ステータスの日本語マッピング
            const statusTypes = {
                'pending': '⏳ 準備中',
                'running': '⚡ 実行中',
                'completed': '✅ 完了',
                'failed': '❌ 失敗'
            };
            
            log.innerHTML = '<h3>📜 クエストログ - 最近の冒険</h3>' + tasks.map(task => `
                <div class="quest-item">
                    <div><strong>🎯 ${task.task_id}</strong></div>
                    <div>🎭 ${taskTypes[task.task_type] || task.task_type} | ${statusTypes[task.status] || task.status}</div>
                    <div>📅 開始: ${new Date(task.created_at).toLocaleString('ja-JP')}</div>
                </div>
            `).join('');
        }
        
        function refreshData() {
            fetchData();
        }
        
        // 初回読み込みと定期更新
        fetchData();
        setInterval(fetchData, 5000);
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def serve_api_status(self):
        """システムステータスAPI"""
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'health_score': self._calculate_health_score()
        }
        self._send_json_response(status)
    
    def serve_api_workers(self):
        """ワーカー情報API"""
        workers = {}
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    for worker_type in ['task_worker', 'pm_worker', 'result_worker', 'dialog_worker']:
                        if worker_type in cmdline:
                            if worker_type not in workers:
                                workers[worker_type] = {'count': 0, 'pids': []}
                            workers[worker_type]['count'] += 1
                            workers[worker_type]['pids'].append(proc.info['pid'])
                except:
                    pass
        except Exception:
            # psutil の例外を適切に処理
            workers = {}  # エラー時は空の辞書を返す
        self._send_json_response(workers)
    
    def serve_api_queues(self):
        """キュー情報API"""
        queues = {}
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            
            for queue_name in ['ai_tasks', 'ai_pm', 'ai_results', 'ai_dialog']:
                try:
                    method = channel.queue_declare(queue=queue_name, passive=True)
                    queues[queue_name] = method.method.message_count
                except:
                    queues[queue_name] = 0
            
            connection.close()
        except:
            pass
        
        self._send_json_response(queues)
    
    def serve_api_recent_tasks(self):
        """最近のタスクAPI"""
        tasks = []
        try:
            db_path = '/home/aicompany/ai_co/db/task_history.db'
            if Path(db_path).exists():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT task_id, task_type, status, created_at
                    FROM task_history
                    ORDER BY created_at DESC
                    LIMIT 10
                """)
                for row in cursor.fetchall():
                    tasks.append({
                        'task_id': row[0],
                        'task_type': row[1],
                        'status': row[2],
                        'created_at': row[3]
                    })
                conn.close()
        except:
            pass
        
        self._send_json_response(tasks)
    
    def serve_api_elder_council(self):
        """エルダーズ評議会API"""
        council_data = {
            'council_status': 'active',
            'elders': {
                'knowledge_sage': {
                    'status': 'healthy',
                    'wisdom_level': 95,
                    'learning_progress': 'infinite',
                    'knowledge_base_size': '∞'
                },
                'task_oracle': {
                    'status': 'healthy', 
                    'efficiency': max(0, 100 - psutil.cpu_percent()),
                    'active_tasks': len([p for p in psutil.process_iter() if 'python' in p.name().lower()]),
                    'queue_management': 'optimal'
                },
                'crisis_sage': {
                    'status': 'vigilant',
                    'protection_level': max(0, 100 - psutil.virtual_memory().percent),
                    'alert_level': 'green' if psutil.virtual_memory().percent < 80 else 'yellow' if psutil.virtual_memory().percent < 90 else 'red',
                    'incidents_prevented': 42
                },
                'search_mystic': {
                    'status': 'seeking',
                    'search_accuracy': 95,
                    'discovery_rate': 98,
                    'knowledge_connections': 1337
                }
            },
            'last_council_meeting': datetime.now().isoformat(),
            'next_scheduled_meeting': (datetime.now()).isoformat()
        }
        self._send_json_response(council_data)
    
    def serve_api_metrics(self):
        """メトリクスAPI"""
        metrics = {
            'throughput_history': [5, 8, 12, 10, 15, 20, 18, 22, 25, 20],
            'error_rate': 0.02,
            'avg_processing_time': 3.5
        }
        self._send_json_response(metrics)
    
    def _send_json_response(self, data):
        """JSON応答を送信"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _calculate_health_score(self):
        """ヘルススコア計算"""
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        score = 100
        if cpu > 80:
            score -= 20
        elif cpu > 60:
            score -= 10
        if memory > 80:
            score -= 20
        elif memory > 60:
            score -= 10
        return max(0, score)
    
    def log_message(self, format, *args):
        """ログ出力を抑制"""
        pass

class DashboardServer:
    """Webダッシュボードサーバー"""
    
    def __init__(self, host=None, port=None):
        # 設定ファイルからデフォルト値を取得
        config = get_config()
        self.host = host or config.WEB_UI_HOST
        self.port = port or config.WEB_UI_PORT
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """サーバーを起動"""
        server = HTTPServer((self.host, self.port), DashboardHandler)
        self.logger.info(f"🌐 Dashboard server starting on http://{self.host}:{self.port}")
        print(f"🌐 Dashboard available at http://localhost:{self.port}")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("Shutting down dashboard server...")
            server.shutdown()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Elders Guild Web Dashboard')
    parser.add_argument('--host', default=None, help='Server host (default: from config)')
    parser.add_argument('--port', type=int, default=None, help='Server port (default: from config)')
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    server = DashboardServer(host=args.host, port=args.port)
    server.run()
