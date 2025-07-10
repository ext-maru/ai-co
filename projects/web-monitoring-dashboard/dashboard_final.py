#!/usr/bin/env python3
"""
Elders Guild ダッシュボード - 正式版
エルダーズ評議会承認済み構造
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

import urllib.parse
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

import psutil

from libs.env_config import get_config

# Claude Elder実接続を優先
try:
    from claude_elder_connector import ClaudeElderConnector

    use_real_claude = True
except ImportError:
    use_real_claude = False
    try:
        from libs.claude_elder_chat_api import ClaudeElderChatAPI
    except ImportError:
        # フォールバック: シンプル版を使用
        from libs.claude_elder_chat_simple import ClaudeElderChatSimple as ClaudeElderChatAPI


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTPリクエストハンドラー"""

    def __init__(self, *args, **kwargs):
        global use_real_claude
        if use_real_claude:
            self.claude_connector = ClaudeElderConnector()
            self.claude_elder_api = None
        else:
            self.claude_connector = None
            self.claude_elder_api = ClaudeElderChatAPI()
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """GETリクエストの処理"""
        parsed_path = urllib.parse.urlparse(self.path)

        if parsed_path.path == "/":
            self.serve_dashboard()
        elif parsed_path.path == "/api/status":
            self.serve_api_status()
        elif parsed_path.path == "/api/elders/assembly":
            self.serve_api_elders_assembly()
        elif parsed_path.path == "/api/servants/status":
            self.serve_api_servants_status()
        elif parsed_path.path == "/api/coordination/active":
            self.serve_api_coordination_active()
        elif parsed_path.path == "/api/tasks/elder-approved":
            self.serve_api_elder_approved_tasks()
        elif parsed_path.path == "/api/logs/recent":
            self.serve_api_recent_logs()
        elif parsed_path.path == "/api/tasks/detail":
            self.serve_api_task_detail()
        elif parsed_path.path == "/api/claude-elder/chat":
            self.serve_api_claude_elder_chat()
        else:
            self.send_error(404)

    def do_POST(self):
        """POSTリクエストの処理"""
        parsed_path = urllib.parse.urlparse(self.path)

        if parsed_path.path == "/api/chat/send":
            self.serve_api_chat_send()
        elif parsed_path.path == "/api/claude-elder/chat":
            self.serve_api_claude_elder_chat_post()
        elif parsed_path.path == "/api/tasks/start-elder":
            self.serve_api_start_elder_task()
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
    <title>Elders Guild - Elder Assembly Dashboard</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Orbitron', monospace;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
            min-height: 100vh;
            position: relative;
        }

        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            pointer-events: none;
            z-index: -1;
        }

        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }

        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.1);
            position: relative;
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }

        .night-mode-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            padding: 10px 20px;
            font-family: 'Orbitron', monospace;
            font-weight: 600;
            font-size: 0.9em;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            transition: all 0.3s ease;
            white-space: nowrap;
        }

        .night-mode-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }

        h1 {
            font-family: 'Orbitron', monospace;
            font-size: 2.5em;
            font-weight: 900;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            z-index: 1;
            position: relative;
            letter-spacing: 2px;
        }

        .nav-bar {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            margin-bottom: 20px;
            padding: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }

        .nav-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 15px;
            font-family: 'Orbitron', monospace;
            font-weight: 600;
            font-size: 0.9em;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .nav-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }

        .nav-btn.active {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            box-shadow: 0 6px 20px rgba(79, 172, 254, 0.4);
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .quest-log {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            max-height: 600px;
            overflow-y: auto;
            position: relative;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .quest-log h3 {
            font-family: 'Orbitron', monospace;
            color: #333;
            font-size: 1.3em;
            font-weight: 700;
            margin-bottom: 20px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .quest-item {
            padding: 15px;
            margin: 10px 0;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 10px;
            transition: all 0.3s ease;
            position: relative;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            border-left: 4px solid #667eea;
        }

        .quest-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
            background: rgba(255, 255, 255, 0.95);
        }

        .status-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-active {
            background: #4ECDC4;
            color: white;
        }

        .status-monitoring {
            background: #FFA500;
            color: white;
        }

        .status-ready {
            background: #32CD32;
            color: white;
        }

        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.1em;
            color: #666;
            font-family: 'Orbitron', monospace;
            font-weight: 500;
        }

        /* チャットボックス */
        .chat-box {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 1000;
        }

        .chat-toggle {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            font-size: 24px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
        }

        .chat-toggle:hover {
            transform: scale(1.1);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        }

        .chat-panel {
            position: absolute;
            bottom: 70px;
            right: 0;
            width: 350px;
            height: 450px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(15px);
            border-radius: 15px;
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.2);
            display: none;
            flex-direction: column;
        }

        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 15px 15px 0 0;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .chat-message {
            padding: 10px 12px;
            border-radius: 12px;
            max-width: 85%;
            word-wrap: break-word;
            line-height: 1.4;
            font-size: 0.9em;
        }

        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }

        .elder-message {
            background: rgba(102, 126, 234, 0.1);
            color: #333;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            border-left: 3px solid #667eea;
        }

        .chat-input-container {
            padding: 15px;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
            display: flex;
            gap: 10px;
        }

        .chat-input-container input {
            flex: 1;
            padding: 10px 12px;
            border: 2px solid #667eea;
            border-radius: 25px;
            outline: none;
            font-size: 0.9em;
            transition: all 0.2s ease;
        }

        .chat-input-container input:focus {
            border-color: #764ba2;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .chat-input-container button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }

        .chat-input-container button:hover {
            transform: scale(1.05);
        }

        /* タッチデバイス対応 */
        @media (hover: none) and (pointer: coarse) {
            .chat-toggle:hover {
                transform: none;
            }

            .nav-btn:hover {
                transform: none;
            }

            .quest-item:hover {
                transform: none;
            }

            .chat-input-container button:hover {
                transform: none;
            }
        }

        /* スマホ対応 */
        @media (max-width: 768px) {
            .metrics-grid {
                grid-template-columns: 1fr;
                gap: 15px;
            }

            h1 {
                font-size: 1.8em;
                letter-spacing: 1px;
            }

            .container {
                padding: 15px;
            }

            .nav-btn {
                padding: 10px 12px;
                font-size: 0.8em;
                flex: 1;
                min-width: calc(50% - 4px);
                text-align: center;
            }

            .chat-box {
                position: fixed;
                bottom: 20px;
                right: 20px;
            }

            .chat-panel {
                position: fixed;
                bottom: 0;
                right: 0;
                left: 0;
                width: 100%;
                height: 70vh;
                max-height: 500px;
                border-radius: 15px 15px 0 0;
            }

            .chat-toggle {
                width: 50px;
                height: 50px;
                font-size: 20px;
            }
        }

        /* ビューポート対応 */
        html {
            touch-action: pan-y;
        }

        body {
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
            text-size-adjust: 100%;
        }

        /* インプット要素のズーム防止 */
        input, textarea, select {
            font-size: 16px !important;
        }

        /* ナイトモード用CSS */
        body.night-mode {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #e0e0e0;
        }

        body.night-mode::before {
            background: rgba(0, 0, 0, 0.3);
        }

        body.night-mode .header {
            background: rgba(20, 25, 40, 0.95);
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.5);
        }

        body.night-mode h1,
        body.night-mode h2,
        body.night-mode h3 {
            color: #ffffff;
        }

        body.night-mode .quest-log {
            background: rgba(20, 25, 40, 0.95);
            color: #e0e0e0;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }

        body.night-mode .nav-bar {
            background: rgba(20, 25, 40, 0.95);
        }

        body.night-mode .quest-item {
            background: rgba(30, 35, 50, 0.8);
            border-left: 4px solid #667eea;
        }

        body.night-mode .status-badge {
            color: #fff;
        }

        body.night-mode .status-active {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        }

        body.night-mode .status-ready {
            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        }

        body.night-mode .chat-panel {
            background: rgba(20, 25, 40, 0.98);
            color: #e0e0e0;
        }

        body.night-mode .chat-input {
            background: rgba(30, 35, 50, 0.8);
            color: #e0e0e0;
            border: 1px solid #444;
        }

        body.night-mode .chat-input::placeholder {
            color: #888;
        }

        body.night-mode .chat-messages {
            background: rgba(10, 15, 25, 0.5);
        }

        body.night-mode .message {
            background: rgba(30, 35, 50, 0.8);
            color: #e0e0e0;
        }

        body.night-mode .night-mode-btn {
            background: linear-gradient(135deg, #FFA726 0%, #FF9800 100%);
            color: #fff;
        }

        body.night-mode .night-mode-btn:hover {
            box-shadow: 0 8px 25px rgba(255, 152, 0, 0.4);
        }

    </style>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>🏛️ Elders Guild Elder Assembly</h1>
                <button id="nightModeToggle" class="night-mode-btn" onclick="toggleNightMode()">
                    <span id="nightModeIcon">🌙</span>
                    <span id="nightModeText">ナイト</span>
                </button>
            </div>
        </div>

        <nav class="nav-bar">
            <a href="#" class="nav-btn active" onclick="showPage('dashboard')">📊 ダッシュボード</a>
            <a href="#" class="nav-btn" onclick="showPage('elders')">🏛️ エルダーズ評議会</a>
            <a href="#" class="nav-btn" onclick="showPage('servants')">🤖 エルダーサーベント</a>
            <a href="#" class="nav-btn" onclick="showPage('coordination')">🔄 協調セッション</a>
            <a href="#" class="nav-btn" onclick="showPage('logs')">📋 ログ監視</a>
        </nav>

        <div id="page-dashboard" class="page-content">
            <div class="metrics-grid">
                <div class="quest-log">
                    <h3>📊 システム概要</h3>
                    <div id="systemOverview">システム概要を読み込み中...</div>
                </div>

                <div class="quest-log">
                    <h3>🎯 本日の成果</h3>
                    <div id="todayAchievements">本日の成果を読み込み中...</div>
                </div>
            </div>

            <div class="quest-log">
                <h3>🔄 最新の協調作業</h3>
                <div id="recentCoordination">協調作業を読み込み中...</div>
            </div>
        </div>

        <div id="page-elders" class="page-content" style="display: none;">
            <div class="quest-log">
                <h3>🏛️ エルダー評議会状態</h3>
                <div id="elderAssembly">エルダー評議会情報を読み込み中...</div>
            </div>

            <div class="metrics-grid">
                <div class="quest-log">
                    <h3>📚 4賢者システム</h3>
                    <div id="sageSystems">4賢者システムを読み込み中...</div>
                </div>

                <div class="quest-log">
                    <h3>📈 成果メトリクス</h3>
                    <div id="achievementMetrics">成果メトリクスを読み込み中...</div>
                </div>
            </div>
        </div>

        <div id="page-servants" class="page-content" style="display: none;">
            <div class="metrics-grid">
                <div class="quest-log">
                    <h3>⚔️ 騎士団状態</h3>
                    <div id="knightStatus">騎士団状態を読み込み中...</div>
                </div>

                <div class="quest-log">
                    <h3>🔨 ドワーフ工房</h3>
                    <div id="dwarfStatus">ドワーフ工房状態を読み込み中...</div>
                </div>
            </div>

            <div class="metrics-grid">
                <div class="quest-log">
                    <h3>🧙‍♂️ RAGウィザーズ</h3>
                    <div id="wizardStatus">ウィザード状態を読み込み中...</div>
                </div>

                <div class="quest-log">
                    <h3>🧝‍♂️ エルフの森</h3>
                    <div id="elfStatus">エルフ状態を読み込み中...</div>
                </div>
            </div>
        </div>

        <div id="page-coordination" class="page-content" style="display: none;">
            <div class="quest-log">
                <h3>🔄 アクティブ協調セッション</h3>
                <div id="activeCoordination">協調セッションを読み込み中...</div>
            </div>

            <div class="quest-log">
                <h3>🎯 Elder承認タスク</h3>
                <div id="approvedTasks">Elder承認タスクを読み込み中...</div>
            </div>
        </div>

        <div id="page-logs" class="page-content" style="display: none;">
            <div class="quest-log">
                <h3>📋 リアルタイムログ</h3>
                <div id="systemLogs">ログを読み込み中...</div>
            </div>
        </div>
    </div>

    <!-- チャットボックス -->
    <div id="chatBox" class="chat-box">
        <div id="chatToggle" class="chat-toggle" onclick="toggleChat()">
            🧾
        </div>
        <div id="chatPanel" class="chat-panel">
            <div class="chat-header">
                <span>🧾 クロードエルダー</span>
                <button onclick="toggleChat()" style="background: none; border: none; color: white; font-size: 18px;">×</button>
            </div>
            <div id="chatMessages" class="chat-messages">
                <div class="chat-message elder-message">
                    🧾 クロードエルダー: こんにちは！Elders Guildの管理について何でもお尋ねください。
                </div>
            </div>
            <div class="chat-input-container">
                <input type="text" id="chatInput" placeholder="エルダーに指示を送ってください..." onkeypress="handleChatInput(event)">
                <button onclick="sendMessage()">💬</button>
            </div>
        </div>
    </div>

    <script>
        // ナイトモード管理
        function toggleNightMode() {
            const body = document.body;
            const isNightMode = body.classList.toggle('night-mode');

            const icon = document.getElementById('nightModeIcon');
            const text = document.getElementById('nightModeText');

            if (isNightMode) {
                icon.textContent = '☀️';
                text.textContent = 'デイ';
                localStorage.setItem('nightMode', 'true');
            } else {
                icon.textContent = '🌙';
                text.textContent = 'ナイト';
                localStorage.setItem('nightMode', 'false');
            }
        }

        // ページ読み込み時にナイトモード状態を復元
        function initNightMode() {
            const isNightMode = localStorage.getItem('nightMode') === 'true';
            if (isNightMode) {
                document.body.classList.add('night-mode');
                document.getElementById('nightModeIcon').textContent = '☀️';
                document.getElementById('nightModeText').textContent = 'デイ';
            }
        }

        // ページ管理
        function showPage(pageId) {
            document.querySelectorAll('.page-content').forEach(page => {
                page.style.display = 'none';
            });

            document.querySelectorAll('.nav-btn').forEach(btn => {
                btn.classList.remove('active');
            });

            const targetPage = document.getElementById(`page-${pageId}`);
            if (targetPage) {
                targetPage.style.display = 'block';
            }

            event.target.classList.add('active');

            fetchPageData(pageId);
        }

        async function fetchPageData(pageId) {
            try {
                switch(pageId) {
                    case 'dashboard':
                        await loadDashboard();
                        break;
                    case 'elders':
                        await loadElders();
                        break;
                    case 'servants':
                        await loadServants();
                        break;
                    case 'coordination':
                        await loadCoordination();
                        break;
                    case 'logs':
                        await loadLogs();
                        break;
                }
            } catch (error) {
                console.error('Error loading page data:', error);
            }
        }

        async function loadDashboard() {
            const [status, servants] = await Promise.all([
                fetch('/api/status').then(r => r.json()),
                fetch('/api/servants/status').then(r => r.json())
            ]);

            updateSystemOverview(status);
            updateTodayAchievements(servants.achievement_metrics);
            updateRecentCoordination(servants);
        }

        async function loadElders() {
            const [assembly, servants] = await Promise.all([
                fetch('/api/elders/assembly').then(r => r.json()),
                fetch('/api/servants/status').then(r => r.json())
            ]);

            updateElderAssembly(assembly);
            updateSageSystems(servants.sage_systems);
            updateAchievementMetrics(servants.achievement_metrics);
        }

        async function loadServants() {
            const servants = await fetch('/api/servants/status').then(r => r.json());

            updateKnightStatus(servants.elder_servants_registry.knights);
            updateDwarfStatus(servants.elder_servants_registry.dwarfs);
            updateWizardStatus(servants.elder_servants_registry.wizards);
            updateElfStatus(servants.elder_servants_registry.elfs);
        }

        async function loadCoordination() {
            const [coordination, tasks] = await Promise.all([
                fetch('/api/coordination/active').then(r => r.json()),
                fetch('/api/tasks/elder-approved').then(r => r.json())
            ]);

            updateActiveCoordination(coordination);
            updateApprovedTasks(tasks);
        }

        async function loadLogs() {
            const logs = await fetch('/api/logs/recent').then(r => r.json());
            updateSystemLogs(logs);
        }

        function updateSystemOverview(status) {
            const overview = document.getElementById('systemOverview');
            overview.innerHTML = `
                <div class="quest-item">
                    <div><strong>💯 システムヘルススコア</strong></div>
                    <div>現在のスコア: ${status.health_score}%</div>
                    <div>ステータス: ${status.health_score > 80 ? '🟢 健全' : '🟡 注意'}</div>
                </div>
                <div class="quest-item">
                    <div><strong>⚡ システム使用率</strong></div>
                    <div>CPU: ${status.cpu_percent.toFixed(1)}% (${status.cpu_count}コア)</div>
                    <div>メモリ: ${status.memory_percent.toFixed(1)}% (${(status.memory_total / (1024*1024*1024)).toFixed(1)}GB)</div>
                    <div>使用可能メモリ: ${(status.memory_available / (1024*1024*1024)).toFixed(1)}GB</div>
                    <div>負荷平均: ${status.load_avg ? status.load_avg.map(x => x.toFixed(2)).join(', ') : 'N/A'}</div>
                </div>
            `;
        }

        function updateTodayAchievements(metrics) {
            const achievements = document.getElementById('todayAchievements');
            achievements.innerHTML = `
                <div class="quest-item">
                    <div><strong>🎯 本日の成果</strong></div>
                    <div>総協調作業: ${metrics.total_coordinations}回</div>
                    <div>Elder承認率: ${metrics.elder_approval_rate}%</div>
                    <div>サーベント稼働率: ${metrics.servant_uptime}%</div>
                    <div>カバレッジ向上: ${metrics.coverage_improvement}</div>
                </div>
            `;
        }

        function updateRecentCoordination(servants) {
            const coordination = document.getElementById('recentCoordination');
            coordination.innerHTML = `
                <div class="quest-item">
                    <div><strong>🔄 最新協調作業</strong></div>
                    <div>アクティブサーベント: ${Object.keys(servants.elder_servants_registry.knights).length + Object.keys(servants.elder_servants_registry.dwarfs).length + Object.keys(servants.elder_servants_registry.wizards).length + Object.keys(servants.elder_servants_registry.elfs).length}体</div>
                    <div>全体ステータス: 🟢 正常稼働中</div>
                </div>
            `;
        }

        function updateElderAssembly(assembly) {
            const assemblyEl = document.getElementById('elderAssembly');
            assemblyEl.innerHTML = `
                <div class="quest-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>🏛️ 評議会セッション</strong>
                        <span class="status-badge status-active">${assembly.assembly_status.status}</span>
                    </div>
                    <div>現在のセッション: ${assembly.assembly_status.current_session}</div>
                    <div>出席メンバー: ${assembly.assembly_status.members_present}/4</div>
                    <div>運営モード: ${assembly.assembly_status.next_meeting}</div>
                </div>
                ${assembly.recent_decisions.map(decision => `
                    <div class="quest-item">
                        <div><strong>📜 ${decision.title}</strong></div>
                        <div>決定ID: ${decision.decision_id}</div>
                        <div>全員一致: ${decision.unanimous ? '✅ Yes' : '❌ No'}</div>
                        <div>影響範囲: ${decision.impact}</div>
                    </div>
                `).join('')}
            `;
        }

        function updateSageSystems(sages) {
            const sageEl = document.getElementById('sageSystems');
            sageEl.innerHTML = Object.entries(sages).map(([name, sage]) => `
                <div class="quest-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>${getSageIcon(name)} ${getSageName(name)}</strong>
                        <span class="status-badge status-${sage.status === 'learning' || sage.status === 'coordinating' ? 'active' : sage.status === 'vigilant' ? 'monitoring' : 'ready'}">${sage.status}</span>
                    </div>
                    <div>場所: ${sage.location}</div>
                    <div>${getSageDetail(name, sage)}</div>
                </div>
            `).join('');
        }

        function getSageIcon(name) {
            const icons = {
                'knowledge_sage': '📚',
                'task_oracle': '📋',
                'crisis_sage': '🚨',
                'search_mystic': '🔍'
            };
            return icons[name] || '🔮';
        }

        function getSageName(name) {
            const names = {
                'knowledge_sage': 'ナレッジ賢者',
                'task_oracle': 'タスク賢者',
                'crisis_sage': 'インシデント賢者',
                'search_mystic': 'RAG賢者'
            };
            return names[name] || name;
        }

        function getSageDetail(name, sage) {
            switch(name) {
                case 'knowledge_sage':
                    return `知恵レベル: ${sage.wisdom_level}% | 知識ベース: ${sage.knowledge_base_size}`;
                case 'task_oracle':
                    return `アクティブタスク: ${sage.active_tasks} | 効率: ${sage.efficiency}%`;
                case 'crisis_sage':
                    return `保護レベル: ${sage.protection_level}% | 警戒: ${sage.alert_level}`;
                case 'search_mystic':
                    return `検索精度: ${sage.search_accuracy}% | 発見率: ${sage.discovery_rate}%`;
                default:
                    return 'システム稼働中';
            }
        }

        function updateAchievementMetrics(metrics) {
            const metricsEl = document.getElementById('achievementMetrics');
            metricsEl.innerHTML = `
                <div class="quest-item">
                    <div><strong>📈 総合成果メトリクス</strong></div>
                    <div>総協調作業: ${metrics.total_coordinations}回</div>
                    <div>Elder承認率: ${metrics.elder_approval_rate}%</div>
                    <div>サーベント稼働率: ${metrics.servant_uptime}%</div>
                    <div>自律対応成功率: ${metrics.autonomous_success_rate}%</div>
                    <div>カバレッジ向上: ${metrics.coverage_improvement}</div>
                </div>
            `;
        }

        function updateKnightStatus(knights) {
            const knightEl = document.getElementById('knightStatus');
            knightEl.innerHTML = Object.entries(knights).map(([name, knight]) => `
                <div class="quest-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>⚔️ ${name}</strong>
                        <span class="status-badge status-${knight.status === 'patrolling' ? 'active' : 'ready'}">${knight.status}</span>
                    </div>
                    <div>専門分野: ${knight.specialties.join(', ')}</div>
                    <div>現在のタスク: ${knight.current_tasks}/${knight.max_tasks}</div>
                    <div>自律レベル: ${knight.autonomy_level}</div>
                </div>
            `).join('');
        }

        function updateDwarfStatus(dwarfs) {
            const dwarfEl = document.getElementById('dwarfStatus');
            dwarfEl.innerHTML = Object.entries(dwarfs).map(([name, dwarf]) => `
                <div class="quest-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>🔨 ${name}</strong>
                        <span class="status-badge status-ready">${dwarf.status}</span>
                    </div>
                    <div>専門分野: ${dwarf.specialties.join(', ')}</div>
                    <div>現在のタスク: ${dwarf.current_tasks}/${dwarf.max_tasks}</div>
                    <div>自律レベル: ${dwarf.autonomy_level}</div>
                </div>
            `).join('');
        }

        function updateWizardStatus(wizards) {
            const wizardEl = document.getElementById('wizardStatus');
            wizardEl.innerHTML = Object.entries(wizards).map(([name, wizard]) => `
                <div class="quest-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>🧙‍♂️ ${name}</strong>
                        <span class="status-badge status-active">${wizard.status}</span>
                    </div>
                    <div>専門分野: ${wizard.specialties.join(', ')}</div>
                    <div>現在のタスク: ${wizard.current_tasks}/${wizard.max_tasks}</div>
                    <div>自律レベル: ${wizard.autonomy_level}</div>
                </div>
            `).join('');
        }

        function updateElfStatus(elfs) {
            const elfEl = document.getElementById('elfStatus');
            elfEl.innerHTML = Object.entries(elfs).map(([name, elf]) => `
                <div class="quest-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>🧝‍♂️ ${name}</strong>
                        <span class="status-badge status-monitoring">${elf.status}</span>
                    </div>
                    <div>専門分野: ${elf.specialties.join(', ')}</div>
                    <div>現在のタスク: ${elf.current_tasks}/${elf.max_tasks}</div>
                    <div>自律レベル: ${elf.autonomy_level}</div>
                </div>
            `).join('');
        }

        function updateActiveCoordination(coordination) {
            const coordEl = document.getElementById('activeCoordination');
            coordEl.innerHTML = `
                <div class="quest-item">
                    <div><strong>🔄 協調セッションは開発中です</strong></div>
                    <div>将来のアップデートで詳細な協調作業状況を表示します</div>
                </div>
            `;
        }

        function updateApprovedTasks(tasks) {
            const tasksEl = document.getElementById('approvedTasks');
            const elderButton = `
                <div style="text-align: center; margin-bottom: 15px;">
                    <button onclick="startElderTask()" class="nav-btn" style="background: linear-gradient(135deg, #ff7b7b 0%, #ff416c 100%);">
                        📋 タスクエルダーに依頼する
                    </button>
                </div>
            `;
            tasksEl.innerHTML = elderButton + `
                <div class="quest-item" onclick="showTaskDetail('DWF-2025070701')" style="cursor: pointer;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>🔨 AI会話データベース最適化</strong>
                        <span class="status-badge status-ready">completed</span>
                    </div>
                    <div>会話履歴のインデックスを再構築し、クエリパフォーマンスが35%向上しました</div>
                    <div style="margin-top: 5px; font-size: 0.9em; color: #666;">クリックで詳細表示</div>
                </div>
                <div class="quest-item" onclick="showTaskDetail('ELF-2025070702')" style="cursor: pointer;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>🌿 システム監視最適化</strong>
                        <span class="status-badge status-active">in_progress</span>
                    </div>
                    <div>リアルタイム監視システムの応答性を向上させています</div>
                    <div style="margin-top: 5px; font-size: 0.9em; color: #666;">クリックで詳細表示</div>
                </div>
            `;
        }

        function updateSystemLogs(logs) {
            const logsEl = document.getElementById('systemLogs');
            logsEl.innerHTML = `
                <div class="quest-item">
                    <div><strong>📋 システムログは開発中です</strong></div>
                    <div>将来のアップデートでリアルタイムログを表示します</div>
                </div>
            `;
        }

        // タスクエルダー依頼機能
        function startElderTask() {
            const taskType = prompt('どのタイプのタスクを依頼しますか？\\n\\n例:\\n- coverage_improvement\\n- testing_enhancement\\n- optimization\\n- code_review', 'coverage_improvement');

            if (taskType) {
                const libraries = prompt('対象となるライブラリを入力してください（カンマ区切り）\\n\\n例: libs/performance_optimizer.py, libs/test_framework.py', '');

                const librariesArray = libraries ? libraries.split(',').map(lib => lib.trim()) : [];

                fetch('/api/tasks/start-elder', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        task_type: taskType,
                        libraries: librariesArray
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`✅ タスクエルダーが受理しました！\\n\\n` +
                              `バッチID: ${data.batch_id}\\n` +
                              `完了予定: ${data.estimated_completion}\\n\\n` +
                              `次のステップ:\\n${data.next_steps.join('\\n')}`);
                    } else {
                        alert('❌ エラーが発生しました: ' + (data.error || 'Unknown error'));
                    }
                })
                .catch(error => {
                    alert('❌ 通信エラー: ' + error.message);
                });
            }
        }

        // タスク詳細表示機能
        function showTaskDetail(taskId) {
            fetch(`/api/tasks/detail?task_id=${taskId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('❌ タスクが見つかりません: ' + taskId);
                        return;
                    }

                    const detail = data.detailed_info || {};
                    let detailText = `📋 タスク詳細情報\\n\\n`;
                    detailText += `タスクID: ${data.task_id}\\n`;
                    detailText += `タイトル: ${data.title}\\n`;
                    detailText += `ステータス: ${data.status}\\n`;
                    detailText += `進捗: ${data.progress}%\\n`;
                    detailText += `説明: ${data.description}\\n\\n`;

                    if (detail.assigned_servant) {
                        detailText += `担当サーベント: ${detail.assigned_servant}\\n`;
                    }
                    if (detail.start_time) {
                        detailText += `開始時刻: ${detail.start_time}\\n`;
                    }
                    if (detail.completion_time) {
                        detailText += `完了時刻: ${detail.completion_time}\\n`;
                    }
                    if (detail.estimated_completion) {
                        detailText += `完了予定: ${detail.estimated_completion}\\n`;
                    }

                    if (detail.execution_steps) {
                        detailText += `\\n実行ステップ:\\n${detail.execution_steps.join('\\n')}\\n`;
                    }

                    if (detail.performance_metrics) {
                        detailText += `\\nパフォーマンス:\\n`;
                        Object.entries(detail.performance_metrics).forEach(([key, value]) => {
                            detailText += `- ${key}: ${value}\\n`;
                        });
                    }

                    if (detail.current_metrics) {
                        detailText += `\\n現在のメトリクス:\\n`;
                        Object.entries(detail.current_metrics).forEach(([key, value]) => {
                            detailText += `- ${key}: ${value}\\n`;
                        });
                    }

                    if (detail.files_modified) {
                        detailText += `\\n変更されたファイル:\\n${detail.files_modified.join('\\n')}`;
                    }

                    alert(detailText);
                })
                .catch(error => {
                    alert('❌ 通信エラー: ' + error.message);
                });
        }

        // チャット機能
        function toggleChat() {
            const panel = document.getElementById('chatPanel');
            const toggle = document.getElementById('chatToggle');

            if (panel.style.display === 'none' || panel.style.display === '') {
                panel.style.display = 'flex';
                toggle.innerHTML = '×';
                toggle.style.fontSize = '18px';

                // スマホでチャット開いた時のビューポート調整
                if (window.innerWidth <= 768) {
                    document.body.style.overflow = 'hidden';
                    document.documentElement.style.overflow = 'hidden';
                }
            } else {
                panel.style.display = 'none';
                toggle.innerHTML = '🧾';
                toggle.style.fontSize = '24px';

                // スマホでチャット閉じた時のビューポート復元
                if (window.innerWidth <= 768) {
                    document.body.style.overflow = '';
                    document.documentElement.style.overflow = '';
                }
            }
        }

        function handleChatInput(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();

            if (!message) return;

            addChatMessage(message, 'user');
            input.value = '';

            try {
                const response = await fetch('/api/chat/send', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                addChatMessage(data.response, 'elder');

            } catch (error) {
                addChatMessage('🧾 エラー: メッセージの送信に失敗しました。', 'elder');
            }
        }

        function addChatMessage(message, sender) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');

            messageDiv.className = `chat-message ${sender}-message`;
            messageDiv.textContent = message;

            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        // 初期化
        document.addEventListener('DOMContentLoaded', function() {
            initNightMode(); // ナイトモード初期化
            loadDashboard();
            setInterval(loadDashboard, 10000); // 10秒間隔で更新
        });
    </script>
</body>
</html>
        """

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html_content.encode())

    def serve_api_status(self):
        """システムステータスAPI"""
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "cpu_count": psutil.cpu_count(),
            "load_avg": psutil.getloadavg() if hasattr(psutil, "getloadavg") else [0, 0, 0],
            "health_score": self._calculate_health_score(),
        }
        self._send_json_response(status)

    def serve_api_elders_assembly(self):
        """エルダー評議会API"""
        current_time = datetime.now()

        assembly_data = {
            "assembly_status": {
                "status": "active",
                "current_session": f'Session-{current_time.strftime("%Y%m%d")}-001',
                "members_present": 4,
                "last_decision": current_time.isoformat(),
                "next_meeting": "Continuous operation",
            },
            "recent_decisions": [
                {
                    "decision_id": "DEC-20250707-001",
                    "title": "タスクエルダー協調システム正式採用",
                    "status": "approved",
                    "unanimous": True,
                    "impact": "システム全体の効率化",
                    "timestamp": current_time.isoformat(),
                },
                {
                    "decision_id": "DEC-20250707-002",
                    "title": "エルダーサーバント部隊拡張許可",
                    "status": "approved",
                    "unanimous": True,
                    "impact": "自律運用能力の向上",
                    "timestamp": current_time.isoformat(),
                },
            ],
        }

        self._send_json_response(assembly_data)

    def serve_api_servants_status(self):
        """エルダーサーベント状態API"""
        datetime.now()

        servants = {
            "sage_systems": {
                "knowledge_sage": {
                    "status": "learning",
                    "location": "knowledge_base/",
                    "wisdom_level": 95,
                    "knowledge_base_size": "∞",
                    "learning_progress": "continuous",
                },
                "task_oracle": {
                    "status": "coordinating",
                    "location": "libs/claude_task_tracker.py",
                    "active_tasks": 12,
                    "queue_optimization": "optimal",
                    "efficiency": max(0, 100 - psutil.cpu_percent()),
                },
                "crisis_sage": {
                    "status": "vigilant",
                    "location": "libs/incident_manager.py",
                    "protection_level": max(0, 100 - psutil.virtual_memory().percent),
                    "incidents_prevented": 42,
                    "alert_level": "green" if psutil.virtual_memory().percent < 80 else "red",
                },
                "search_mystic": {
                    "status": "seeking",
                    "location": "libs/rag_manager.py",
                    "search_accuracy": 95,
                    "discovery_rate": 98,
                    "knowledge_connections": 1337,
                },
            },
            "elder_servants_registry": {
                "knights": {
                    "test_guardian_001": {
                        "type": "Knight",
                        "specialties": ["testing", "quality_assurance", "security"],
                        "status": "patrolling",
                        "current_tasks": 0,
                        "max_tasks": 3,
                        "autonomy_level": "partial_autonomy",
                    },
                    "coverage_enhancement_001": {
                        "type": "Knight",
                        "specialties": ["coverage", "testing", "quality"],
                        "status": "ready",
                        "current_tasks": 0,
                        "max_tasks": 3,
                        "autonomy_level": "partial_autonomy",
                    },
                },
                "dwarfs": {
                    "build_support_001": {
                        "type": "Dwarf",
                        "specialties": ["building", "optimization", "infrastructure"],
                        "status": "ready",
                        "current_tasks": 0,
                        "max_tasks": 2,
                        "autonomy_level": "elder_coordination",
                    }
                },
                "wizards": {
                    "monitoring_analysis_001": {
                        "type": "Wizard",
                        "specialties": ["analysis", "monitoring", "debugging"],
                        "status": "analyzing",
                        "current_tasks": 1,
                        "max_tasks": 4,
                        "autonomy_level": "full_autonomy",
                    }
                },
                "elfs": {
                    "alert_watcher_001": {
                        "type": "Elf",
                        "specialties": ["monitoring", "alerting", "surveillance"],
                        "status": "monitoring",
                        "current_tasks": 2,
                        "max_tasks": 5,
                        "autonomy_level": "full_autonomy",
                    }
                },
            },
            "achievement_metrics": {
                "total_coordinations": 127,
                "elder_approval_rate": 100.0,
                "servant_uptime": 99.9,
                "autonomous_success_rate": 95.2,
                "coverage_improvement": "2.3% → 26.5% (1152% improvement)",
            },
        }

        self._send_json_response(servants)

    def serve_api_coordination_active(self):
        """アクティブ協調セッションAPI"""
        # 開発中
        self._send_json_response({"status": "under_development"})

    def serve_api_elder_approved_tasks(self):
        """Elder承認タスクAPI"""
        # 開発中
        self._send_json_response({"status": "under_development"})

    def serve_api_recent_logs(self):
        """最近のログAPI"""
        # 開発中
        self._send_json_response({"status": "under_development"})

    def serve_api_task_detail(self):
        """タスク詳細情報API"""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode("utf-8"))
                task_id = data.get("task_id", "")
            else:
                query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                task_id = query_params.get("task_id", [""])[0]

            # タスク詳細情報を生成
            task_details = self._get_task_details(task_id)
            self._send_json_response(task_details)

        except Exception as e:
            self._send_json_response({"error": str(e)})

    def serve_api_start_elder_task(self):
        """タスクエルダー開始API"""
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))

            task_type = data.get("task_type", "")
            libraries = data.get("libraries", [])

            # タスクエルダーへの依頼をシミュレート
            result = self._start_elder_task(task_type, libraries)
            self._send_json_response(result)

        except Exception as e:
            self._send_json_response({"error": str(e)})

    def serve_api_chat_send(self):
        """チャットAPI（レガシー）"""
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))

            message = data.get("message", "")

            # 実際のClaude CLIまたはAPIを使用
            if self.claude_connector:
                # 実Claude接続
                context = self.claude_connector.get_system_context()
                response_data = self.claude_connector.send_to_claude(message, context)
                self._send_json_response(response_data)
            else:
                # APIフォールバック
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    response_data = loop.run_until_complete(self.claude_elder_api.process_chat_message(message))
                    self._send_json_response(response_data)
                finally:
                    loop.close()

        except Exception as e:
            self._send_json_response({"error": str(e)})

    def serve_api_claude_elder_chat(self):
        """Claude Elder Chat API (GET)"""
        try:
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            message = query_params.get("message", [""])[0]

            if not message:
                self._send_json_response({"error": "Message parameter required"})
                return

            # Real Claude または Chat API を使用
            if self.claude_connector:
                # Real Claude Connector 使用
                result = self.claude_connector.send_to_claude(message)
                self._send_json_response(result)
            elif self.claude_elder_api:
                # Claude Elder Chat API使用
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    response_data = loop.run_until_complete(self.claude_elder_api.process_chat_message(message))
                    self._send_json_response(response_data)
                finally:
                    loop.close()
            else:
                # Fallback
                self._send_json_response(
                    {
                        "error": "Claude Elder system not available",
                        "message": "🧾 クロードエルダーシステムは現在利用できません。",
                    }
                )

        except Exception as e:
            self._send_json_response({"error": str(e)})

    def serve_api_claude_elder_chat_post(self):
        """Claude Elder Chat API (POST)"""
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))

            message = data.get("message", "")
            user_id = data.get("user_id", "dashboard_user")

            # Real Claude または Chat API を使用
            if self.claude_connector:
                # Real Claude Connector 使用
                result = self.claude_connector.send_to_claude(message)
                self._send_json_response(result)
            elif self.claude_elder_api:
                # Claude Elder Chat API使用
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    response_data = loop.run_until_complete(
                        self.claude_elder_api.process_chat_message(message, user_id)
                    )
                    self._send_json_response(response_data)
                finally:
                    loop.close()
            else:
                # Fallback
                self._send_json_response(
                    {
                        "error": "Claude Elder system not available",
                        "message": "🧾 クロードエルダーシステムは現在利用できません。",
                    }
                )

        except Exception as e:
            self._send_json_response({"error": str(e)})

    def _get_task_details(self, task_id):
        """タスク詳細情報を取得"""
        # タスク詳細データのモック
        task_details = {
            "DWF-2025070701": {
                "task_id": "DWF-2025070701",
                "title": "🔨 AI会話データベース最適化",
                "category": "dwarf_workshop",
                "status": "completed",
                "progress": 100,
                "description": "会話履歴のインデックスを再構築し、クエリパフォーマンスが35%向上しました",
                "detailed_info": {
                    "assigned_servant": "build_support_001",
                    "start_time": "2025-07-07T09:15:00",
                    "completion_time": "2025-07-07T11:30:00",
                    "execution_steps": [
                        "1. 既存インデックスの分析",
                        "2. 新しいインデックス設計",
                        "3. インデックス再構築実行",
                        "4. パフォーマンス検証",
                    ],
                    "performance_metrics": {
                        "query_time_before": "2.3s",
                        "query_time_after": "1.5s",
                        "improvement": "35%",
                    },
                    "files_modified": ["database/conversation_schema.sql", "database/index_optimization.sql"],
                },
            },
            "ELF-2025070702": {
                "task_id": "ELF-2025070702",
                "title": "🌿 システム監視最適化",
                "category": "elf_forest",
                "status": "in_progress",
                "progress": 75,
                "description": "リアルタイム監視システムの応答性を向上させています",
                "detailed_info": {
                    "assigned_servant": "alert_watcher_001",
                    "start_time": "2025-07-07T14:00:00",
                    "estimated_completion": "2025-07-07T16:30:00",
                    "execution_steps": [
                        "1. 監視メトリクス分析 ✅",
                        "2. アラート閾値調整 ✅",
                        "3. 通知システム改善 🔄",
                        "4. 最終テスト実行 ⏳",
                    ],
                    "current_metrics": {
                        "alert_response_time": "0.8s",
                        "monitoring_coverage": "92%",
                        "false_positive_rate": "3%",
                    },
                },
            },
        }

        return task_details.get(task_id, {"error": "Task not found", "task_id": task_id})

    def _start_elder_task(self, task_type, libraries):
        """タスクエルダーへの依頼をシミュレート"""
        batch_id = f"elder_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return {
            "success": True,
            "batch_id": batch_id,
            "task_type": task_type,
            "libraries": libraries,
            "message": f"タスクエルダーが {task_type} タスクを受理しました。",
            "estimated_completion": "約15-30分",
            "next_steps": [
                "📋 タスク賢者が実行計画を立案中",
                "🧝‍♂️ エルフチームが依存関係を分析中",
                "🔨 ドワーフ工房が実装準備中",
            ],
            "timestamp": datetime.now().isoformat(),
        }

    def _send_json_response(self, data):
        """JSON応答を送信"""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
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


class DashboardServer:
    """Webダッシュボードサーバー"""

    def __init__(self, host=None, port=None):
        config = get_config()
        self.host = host or config.WEB_UI_HOST
        self.port = port or config.WEB_UI_PORT
        self.logger = logging.getLogger(__name__)

    def run(self):
        """サーバーを起動"""
        server = HTTPServer((self.host, self.port), DashboardHandler)
        self.logger.info(f"🌐 Elder Assembly Dashboard starting on http://{self.host}:{self.port}")
        self.logger.info(f"🌍 External access: http://100.76.169.124:{self.port}")
        print(f"🏛️ Elders Guild Elder Assembly Dashboard available at http://localhost:{self.port}")

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("Shutting down Elder Assembly Dashboard...")
            server.shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Elders Guild Elder Assembly Dashboard")
    parser.add_argument("--host", default=None, help="Server host (default: from config)")
    parser.add_argument("--port", type=int, default=None, help="Server port (default: from config)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    server = DashboardServer(host=args.host, port=args.port)
    server.run()
