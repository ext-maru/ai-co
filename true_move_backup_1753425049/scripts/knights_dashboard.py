#!/usr/bin/env python3
"""
Knights Dashboard - 騎士団統合監視ダッシュボード
リアルタイム状況監視とワンクリック修復機能
"""

import json
import subprocess
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request
import logging

# パス設定
sys.path.append(str(Path(__file__).parent.parent))

from scripts.knights_status_monitor import KnightsStatusMonitor

# Flask設定
app = Flask(__name__)
app.secret_key = "knights_dashboard_secret_key"

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# グローバル状態
latest_status = {}
auto_refresh = True


class KnightsDashboard:
    """騎士団ダッシュボードメインクラス"""

    def __init__(self):
        self.monitor = KnightsStatusMonitor()
        self.update_interval = 30  # 30秒ごとに更新

    def start_auto_update(self):
        """自動更新スレッドを開始"""

        def update_loop():
            """update_loopを更新"""
            global latest_status
            while auto_refresh:
                try:
                    latest_status = self.monitor.generate_report("dict")
                    logger.info("Status updated")
                    time.sleep(self.update_interval)
                except Exception as e:
                    logger.error(f"Update failed: {e}")
                    time.sleep(5)

        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
        logger.info("Auto-update thread started")


# HTML テンプレート
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ Knights Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .health-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .health-healthy { background: #4CAF50; }
        .health-warning { background: #FF9800; }
        .health-critical { background: #F44336; }
        .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .status-item:last-child {
            border-bottom: none;
        }
        .btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        .btn:hover {
            background: #45a049;
        }
        .btn-danger {
            background: #F44336;
        }
        .btn-danger:hover {
            background: #da190b;
        }
        .actions {
            text-align: center;
            margin: 20px 0;
        }
        .timestamp {
            text-align: center;
            opacity: 0.7;
            font-size: 0.9em;
        }
        .auto-refresh {
            color: #4CAF50;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
    <script>
        function refreshStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateDashboard(data);
                })
                .catch(error => console.error('Error:', error));
        }

        function updateDashboard(status) {
            // Update overall health
            const healthBadge = document.getElementById('health-badge');
            healthBadge.className = 'health-badge health-' + status.overall_health;
            healthBadge.textContent = status.overall_health;

            // Update timestamp
            document.getElementById('timestamp').textContent = new Date(status.timestamp).toLocaleString('ja-JP');
        }

        function executeAction(action) {
            fetch('/api/action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({action: action})
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                setTimeout(refreshStatus, 2000);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('アクション実行に失敗しました');
            });
        }

        // Auto refresh every 10 seconds
        setInterval(refreshStatus, 10000);

        // Initial load
        window.onload = function() {
            refreshStatus();
        };
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Knights Dashboard</h1>
            <h2>騎士団統合監視システム</h2>
            <div class="health-badge" id="health-badge">{{ status.overall_health }}</div>
        </div>

        <div class="actions">
            <button class="btn" onclick="refreshStatus()">🔄 手動更新</button>
            <button class="btn" onclick="executeAction('fix_workers')">👥 ワーカー修復</button>
            <button class="btn" onclick="executeAction('test_knights')">⚔️ 騎士団テスト</button>
            <button class="btn btn-danger" onclick="executeAction('emergency_restart')">🚨 緊急再起動</button>
        </div>

        <div class="status-grid">
            <!-- GitHub Actions Card -->
            <div class="status-card">
                <h3>📡 GitHub Actions</h3>
                <div class="status-item">
                    <span>ステータス:</span>
                    <span>{{ status.github_actions.status }}</span>
                </div>
                {% if status.github_actions.recent_runs is defined %}
                <div class="status-item">
                    <span>最近の実行:</span>
                    <span>{{ status.github_actions.recent_runs }}回</span>
                </div>
                {% endif %}
                {% if status.github_actions.error %}
                <div class="status-item">
                    <span>エラー:</span>
                    <span style="color: #FF6B6B;">{{ status.github_actions.error }}</span>
                </div>
                {% endif %}
            </div>

            <!-- Local Knights Card -->
            <div class="status-card">
                <h3>⚔️ ローカル騎士団</h3>
                <div class="status-item">
                    <span>ステータス:</span>
                    <span>{{ status.local_knights.status }}</span>
                </div>
                <div class="status-item">
                    <span>実行可能:</span>
                    <span>{{ "✅" if status.local_knights.script_executable else "❌" }}</span>
                </div>
                {% if status.local_knights.last_analysis %}
                <div class="status-item">
                    <span>検出問題:</span>
                    <span>{{ status.local_knights.last_analysis.total_issues }}件</span>
                </div>
                {% endif %}
            </div>

            <!-- Workers Card -->
            <div class="status-card">
                <h3>👥 ワーカー</h3>
                <div class="status-item">
                    <span>実行中:</span>
                    <span>{{ status.workers.running_count }}/{{ status.workers.total_expected }}</span>
                </div>
                {% for worker, info in status.workers.processes.items() %}
                <div class="status-item">
                    <span>{{ worker }}:</span>
                    <span>{{ "✅" if info.status == "running" else "❌" }} {{ info.status }}</span>
                </div>
                {% endfor %}
            </div>

            <!-- RabbitMQ Card -->
            <div class="status-card">
                <h3>🐰 RabbitMQ</h3>
                <div class="status-item">
                    <span>接続:</span>
                    <span>{{ "✅" \
                        if status.rabbitmq.status == "connected" \:
                        else "❌" }} {{ status.rabbitmq.status }}</span>
                </div>
                {% if status.rabbitmq.queues %}
                {% for queue, info in status.rabbitmq.queues.items() %}
                <div class="status-item">
                    <span>{{ queue }}:</span>
                    <span>{{ info.message_count if info.exists else "❌" }}{% if info.exists %} メッセージ{% endif %}</span>
                </div>
                {% endfor %}
                {% endif %}
            </div>
        </div>

        <!-- Issues Section -->
        {% if status.issues %}
        <div class="status-card">
            <h3>⚠️ 検出された問題</h3>
            {% for issue in status.issues %}
            <div class="status-item">
                <span>• {{ issue }}</span>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="timestamp">
            <span class="auto-refresh">●</span>
            最終更新: <span id="timestamp">{{ status.timestamp }}</span>
            <br>
            <small>10秒ごとに自動更新</small>
        </div>
    </div>
</body>
</html>
"""


# Flask ルート
@app.route("/")
def dashboard():
    """ダッシュボードメインページ"""
    global latest_status
    if not latest_status:
        # 初回アクセス時は即座にステータス取得
        monitor = KnightsStatusMonitor()
        latest_status = monitor.generate_report("dict")

    return render_template_string(DASHBOARD_TEMPLATE, status=latest_status)


@app.route("/api/status")
def api_status():
    """ステータスAPI"""
    global latest_status
    return jsonify(latest_status)


@app.route("/api/action", methods=["POST"])
def api_action():
    """アクション実行API"""
    data = request.json
    action = data.get("action")

    try:
        if action == "fix_workers":
            result = subprocess.run(
                ["python3", "check_and_fix_workers.py"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return jsonify(
                {
                    "success": True,
                    "message": "ワーカー修復を実行しました",
                    "output": result.stdout,
                }
            )

        elif action == "test_knights":
            result = subprocess.run(
                [
                    "python3",
                    "scripts/knights-github-action.py",
                    "analyze",
                    "--output-format",
                    "text",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return jsonify(
                {
                    "success": True,
                    "message": "騎士団テストを実行しました",
                    "output": result.stdout,
                }
            )

        elif action == "emergency_restart":
            # 緊急再起動シミュレーション（実際の再起動は危険なので模擬）
            return jsonify(
                {
                    "success": True,
                    "message": "緊急再起動シミュレーションを実行しました（実際の再起動はされていません）",
                }
            )

        else:
            return jsonify({"success": False, "message": f"未知のアクション: {action}"})

    except subprocess.TimeoutExpired:
        return jsonify(
            {"success": False, "message": "アクション実行がタイムアウトしました"}
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"アクション実行エラー: {str(e)}"})


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Knights Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=5000, help="Port number")
    parser.add_argument("--debug", action="store_true", help="Debug mode")

    args = parser.parse_args()

    # ダッシュボード初期化
    dashboard = KnightsDashboard()
    dashboard.start_auto_update()

    print(
        f"""
🛡️ Knights Dashboard Starting...

URL: http://{args.host}:{args.port}
Debug: {args.debug}

統合監視機能:
- GitHub Actions監視
- ローカル騎士団スクリプト監視
- ワーカープロセス監視
- RabbitMQ接続監視
- ワンクリック修復機能

Ctrl+C で停止
"""
    )

    # Flask サーバー起動
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == "__main__":
    main()
