#!/usr/bin/env python3
"""
Elders Guild Flask Web Application
Apache mod_wsgi対応版
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3

import pika
import psutil
from flask import Flask
from flask import jsonify
from flask import render_template_string
from flask import request

from libs.env_config import get_config

# Flask アプリケーション初期化
app = Flask(__name__)
app.secret_key = "ai_company_secret_key_2025"

# 設定読み込み
config = get_config()

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Docker API Blueprint登録
try:
    from web.docker_api import docker_api

    app.register_blueprint(docker_api)
    logger.info("Docker API blueprint registered successfully")
except Exception as e:
    logger.warning(f"Failed to register Docker API blueprint: {e}")

# 4賢者 API Blueprint登録
try:
    from web.sages_api import sages_api

    app.register_blueprint(sages_api)
    logger.info("Sages API blueprint registered successfully")
except Exception as e:
    logger.warning(f"Failed to register Sages API blueprint: {e}")

# ダッシュボードHTMLテンプレート
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elders Guild Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            line-height: 1.6;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header {
            background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(124, 58, 237, 0.3);
        }
        h1 {
            font-size: 2.5em;
            font-weight: 700;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 25px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(124, 58, 237, 0.2);
            border-color: #7c3aed;
        }
        .card h3 {
            color: #7c3aed;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            padding: 10px;
            background: #0a0a0a;
            border-radius: 8px;
        }
        .metric-value {
            font-size: 1.8em;
            font-weight: 700;
            color: #10b981;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        .status-healthy { background: #10b981; }
        .status-warning { background: #f59e0b; }
        .status-error { background: #ef4444; }

        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
            100% { opacity: 1; transform: scale(1); }
        }

        .task-list {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 20px;
            max-height: 500px;
            overflow-y: auto;
        }
        .task-item {
            padding: 15px;
            margin: 10px 0;
            background: #0a0a0a;
            border-radius: 8px;
            border-left: 4px solid #7c3aed;
            transition: all 0.2s ease;
        }
        .task-item:hover {
            transform: translateX(5px);
            background: #1a1a1a;
        }
        .loading {
            text-align: center;
            padding: 50px;
            font-size: 1.2em;
            color: #666;
        }
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: linear-gradient(135deg, #7c3aed 0%, #1e3a8a 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 1.1em;
            cursor: pointer;
            box-shadow: 0 5px 20px rgba(124, 58, 237, 0.4);
            transition: all 0.3s ease;
        }
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(124, 58, 237, 0.6);
        }
        .server-info {
            background: #1a1a1a;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #10b981;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Elders Guild Dashboard</h1>
        </div>

        <div class="server-info">
            <h3>🌐 サーバー情報</h3>
            <p><strong>Flask/WSGI版</strong> - {{ server_info.timestamp }}</p>
            <p>ホスト: {{ server_info.host }}:{{ server_info.port }}</p>
            <p>環境: {{ server_info.environment }}</p>
        </div>

        <div class="status-grid" id="statusGrid">
            <div class="loading">Loading system status...</div>
        </div>

        <div class="task-list" id="recentTasks">
            <h3>📝 Recent Tasks</h3>
            <div class="loading">Loading tasks...</div>
        </div>
    </div>

    <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>

    <script>
        async function fetchData() {
            try {
                const [status, workers, queues, tasks] = await Promise.all([
                    fetch('/api/status').then(r => r.json()),
                    fetch('/api/workers').then(r => r.json()),
                    fetch('/api/queues').then(r => r.json()),
                    fetch('/api/tasks/recent').then(r => r.json())
                ]);

                updateStatusGrid(status, workers, queues);
                updateTaskList(tasks);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }

        function updateStatusGrid(status, workers, queues) {
            const grid = document.getElementById('statusGrid');
            grid.innerHTML = `
                <div class="card">
                    <h3>⚡ System Status</h3>
                    <div class="metric">
                        <span>Health Score</span>
                        <span class="metric-value">${status.health_score}%</span>
                    </div>
                    <div class="metric">
                        <span>CPU Usage</span>
                        <span class="metric-value">${status.cpu_percent}%</span>
                    </div>
                    <div class="metric">
                        <span>Memory Usage</span>
                        <span class="metric-value">${status.memory_percent}%</span>
                    </div>
                </div>

                <div class="card">
                    <h3>👷 Workers</h3>
                    ${Object.entries(workers).map(([type, info]) => `
                        <div class="metric">
                            <span>
                                <span class="status-indicator status-healthy"></span>
                                ${type}
                            </span>
                            <span class="metric-value">${info.count}</span>
                        </div>
                    `).join('')}
                </div>

                <div class="card">
                    <h3>📬 Queues</h3>
                    ${Object.entries(queues).map(([name, count]) => `
                        <div class="metric">
                            <span>${name}</span>
                            <span class="metric-value">${count}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        function updateTaskList(tasks) {
            const list = document.getElementById('recentTasks');
            if (tasks.length === 0) {
                list.innerHTML = '<h3>📝 Recent Tasks</h3><p>No recent tasks</p>';
                return;
            }

            list.innerHTML = '<h3>📝 Recent Tasks</h3>' + tasks.map(task => `
                <div class="task-item">
                    <div><strong>${task.task_id}</strong></div>
                    <div>Type: ${task.task_type} | Status: ${task.status}</div>
                    <div>Created: ${new Date(task.created_at).toLocaleString()}</div>
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


@app.route("/")
def dashboard():
    """ダッシュボード表示"""
    server_info = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "host": request.host,
        "port": config.WEB_UI_PORT,
        "environment": "Flask/WSGI",
    }
    return render_template_string(DASHBOARD_TEMPLATE, server_info=server_info)


@app.route("/api/status")
def api_status():
    """システムステータスAPI"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "health_score": _calculate_health_score(),
    }
    return jsonify(status)


@app.route("/api/workers")
def api_workers():
    """ワーカー情報API"""
    workers = {}
    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = " ".join(proc.info.get("cmdline", []))
                for worker_type in ["task_worker", "pm_worker", "result_worker", "dialog_worker"]:
                    if worker_type in cmdline:
                        if worker_type not in workers:
                            workers[worker_type] = {"count": 0, "pids": []}
                        workers[worker_type]["count"] += 1
                        workers[worker_type]["pids"].append(proc.info["pid"])
            except:
                pass
    except Exception as e:
        # psutil の例外を適切に処理
        logger.warning(f"Failed to get worker information: {e}")
        workers = {}  # エラー時は空の辞書を返す
    return jsonify(workers)


@app.route("/api/queues")
def api_queues():
    """キュー情報API"""
    queues = {}
    try:
        rabbitmq_config = config.get_rabbitmq_config()
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_config["host"], port=rabbitmq_config["port"])
        )
        channel = connection.channel()

        for queue_name in ["ai_tasks", "ai_pm", "ai_results", "ai_dialog"]:
            try:
                method = channel.queue_declare(queue=queue_name, passive=True)
                queues[queue_name] = method.method.message_count
            except:
                queues[queue_name] = 0

        connection.close()
    except:
        # RabbitMQ接続失敗時のデフォルト値
        queues = {"ai_tasks": 0, "ai_pm": 0, "ai_results": 0, "ai_dialog": 0}

    return jsonify(queues)


@app.route("/api/tasks/recent")
def api_recent_tasks():
    """最近のタスクAPI"""
    tasks = []
    try:
        db_path = config.PROJECT_ROOT / "data" / "tasks.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT task_id, task_type, status, created_at
                FROM task_history
                ORDER BY created_at DESC
                LIMIT 10
            """
            )
            for row in cursor.fetchall():
                tasks.append({"task_id": row[0], "task_type": row[1], "status": row[2], "created_at": row[3]})
            conn.close()
    except Exception as e:
        logger.warning(f"Failed to load tasks: {e}")

    return jsonify(tasks)


@app.route("/api/metrics")
def api_metrics():
    """メトリクスAPI"""
    metrics = {
        "throughput_history": [5, 8, 12, 10, 15, 20, 18, 22, 25, 20],
        "error_rate": 0.02,
        "avg_processing_time": 3.5,
        "server_type": "Flask/WSGI",
    }
    return jsonify(metrics)


@app.route("/health")
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat(), "server": "Flask/WSGI"})


def _calculate_health_score():
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


# WSGI アプリケーション
application = app

if __name__ == "__main__":
    # 開発サーバーとして実行
    app.run(host=config.WEB_UI_HOST, port=config.WEB_UI_PORT, debug=False)
