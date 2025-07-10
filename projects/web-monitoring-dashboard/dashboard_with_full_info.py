#!/usr/bin/env python3
"""
Elders Guild ダッシュボード - 完全版（CPU・メモリ詳細表示付き）
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
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """ダッシュボードHTMLを提供"""
        html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Elders Guild - Elder Assembly Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
            min-height: 100vh;
            -webkit-text-size-adjust: 100%;
        }
        
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.1);
        }
        
        h1 { 
            font-size: 2.5em; 
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .metric-card h3 {
            color: #333;
            font-size: 1.3em;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .metric-item {
            padding: 15px;
            margin: 10px 0;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        
        .metric-value {
            font-size: 1.2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .status-good {
            color: #4CAF50;
        }
        
        .status-warning {
            color: #FFA500;
        }
        
        .status-critical {
            color: #F44336;
        }
        
        /* チャットボックス */
        .chat-box {
            position: fixed;
            bottom: 20px;
            right: 20px;
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
        }
        
        .chat-panel {
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 350px;
            height: 450px;
            background: rgba(255, 255, 255, 0.95);
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
        }
        
        .elder-message {
            background: rgba(102, 126, 234, 0.1);
            color: #333;
            align-self: flex-start;
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
            font-size: 16px !important;
        }
        
        .chat-input-container button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            cursor: pointer;
        }
        
        /* タッチデバイス対応 */
        @media (hover: none) and (pointer: coarse) {
            .chat-toggle:hover {
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
            }
            
            .container {
                padding: 15px;
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
        
        input, textarea, select {
            font-size: 16px !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Elders Guild Elder Assembly</h1>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>📊 システム概要</h3>
                <div id="systemOverview">システム概要を読み込み中...</div>
            </div>
            
            <div class="metric-card">
                <h3>🎯 システムリソース</h3>
                <div id="systemResources">リソース情報を読み込み中...</div>
            </div>
        </div>
        
        <div class="metric-card">
            <h3>📈 詳細メトリクス</h3>
            <div id="detailedMetrics">詳細情報を読み込み中...</div>
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
                <input type="text" id="chatInput" placeholder="メッセージを入力..." onkeypress="handleChatInput(event)">
                <button onclick="sendMessage()">💬</button>
            </div>
        </div>
    </div>
    
    <script>
        function updateDashboard() {
            fetch('/api/status')
                .then(response => response.json())
                .then(status => {
                    console.log('Status received:', status);
                    updateSystemOverview(status);
                    updateSystemResources(status);
                    updateDetailedMetrics(status);
                })
                .catch(error => {
                    console.error('Error fetching status:', error);
                });
        }
        
        function updateSystemOverview(status) {
            const overview = document.getElementById('systemOverview');
            const healthStatus = status.health_score > 80 ? 'status-good' : 
                               status.health_score > 60 ? 'status-warning' : 'status-critical';
            
            overview.innerHTML = `
                <div class="metric-item">
                    <div><strong>💯 システムヘルススコア</strong></div>
                    <div class="metric-value ${healthStatus}">${status.health_score}%</div>
                    <div>ステータス: ${status.health_score > 80 ? '🟢 健全' : status.health_score > 60 ? '🟡 注意' : '🔴 要対応'}</div>
                </div>
                <div class="metric-item">
                    <div><strong>⏰ 最終更新</strong></div>
                    <div>${new Date(status.timestamp).toLocaleString('ja-JP')}</div>
                </div>
            `;
        }
        
        function updateSystemResources(status) {
            const resources = document.getElementById('systemResources');
            const cpuStatus = status.cpu_percent < 50 ? 'status-good' : 
                             status.cpu_percent < 80 ? 'status-warning' : 'status-critical';
            const memStatus = status.memory_percent < 60 ? 'status-good' : 
                             status.memory_percent < 80 ? 'status-warning' : 'status-critical';
            
            resources.innerHTML = `
                <div class="metric-item">
                    <div><strong>💻 CPU使用率</strong></div>
                    <div class="metric-value ${cpuStatus}">${status.cpu_percent.toFixed(1)}%</div>
                    <div>コア数: ${status.cpu_count}コア</div>
                </div>
                <div class="metric-item">
                    <div><strong>🧠 メモリ使用率</strong></div>
                    <div class="metric-value ${memStatus}">${status.memory_percent.toFixed(1)}%</div>
                    <div>総容量: ${(status.memory_total / (1024*1024*1024)).toFixed(1)}GB</div>
                    <div>使用可能: ${(status.memory_available / (1024*1024*1024)).toFixed(1)}GB</div>
                </div>
            `;
        }
        
        function updateDetailedMetrics(status) {
            const detailed = document.getElementById('detailedMetrics');
            
            detailed.innerHTML = `
                <div class="metric-item">
                    <div><strong>📊 負荷平均</strong></div>
                    <div>1分: ${status.load_avg ? status.load_avg[0].toFixed(2) : 'N/A'}</div>
                    <div>5分: ${status.load_avg ? status.load_avg[1].toFixed(2) : 'N/A'}</div>
                    <div>15分: ${status.load_avg ? status.load_avg[2].toFixed(2) : 'N/A'}</div>
                </div>
                <div class="metric-item">
                    <div><strong>💾 ディスク使用率</strong></div>
                    <div class="metric-value">${status.disk_percent.toFixed(1)}%</div>
                </div>
                <div class="metric-item">
                    <div><strong>🏛️ エルダーシステム</strong></div>
                    <div>📚 ナレッジ賢者: 学習中</div>
                    <div>📋 タスク賢者: 調整中</div>
                    <div>🚨 インシデント賢者: 監視中</div>
                    <div>🔍 RAG賢者: 探索中</div>
                </div>
            `;
        }
        
        function toggleChat() {
            const panel = document.getElementById('chatPanel');
            const toggle = document.getElementById('chatToggle');
            
            if (panel.style.display === 'none' || panel.style.display === '') {
                panel.style.display = 'flex';
                toggle.innerHTML = '×';
                
                // スマホでチャット開いた時の制御
                if (window.innerWidth <= 768) {
                    document.body.style.overflow = 'hidden';
                }
            } else {
                panel.style.display = 'none';
                toggle.innerHTML = '🧾';
                
                // スマホでチャット閉じた時の制御
                if (window.innerWidth <= 768) {
                    document.body.style.overflow = '';
                }
            }
        }
        
        function handleChatInput(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            addChatMessage(message, 'user');
            input.value = '';
            
            // 簡易レスポンス
            setTimeout(() => {
                let response = '🧾 クロードエルダー: ';
                
                if (message.includes('CPU') || message.includes('cpu')) {
                    response += 'CPU使用率の詳細情報をダッシュボードに表示しています。';
                } else if (message.includes('メモリ') || message.includes('memory')) {
                    response += 'メモリ使用状況の詳細をご確認ください。';
                } else if (message.includes('状態') || message.includes('status')) {
                    response += 'システムは正常に稼働しています。詳細はダッシュボードをご覧ください。';
                } else {
                    response += 'お問い合わせありがとうございます。ダッシュボードに詳細情報を表示しています。';
                }
                
                addChatMessage(response, 'elder');
            }, 500);
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
            updateDashboard();
            setInterval(updateDashboard, 10000); // 10秒間隔で更新
        });
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
        try:
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        except:
            load_avg = [0, 0, 0]
            
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'cpu_count': psutil.cpu_count(),
            'load_avg': load_avg,
            'health_score': self._calculate_health_score()
        }
        self._send_json_response(status)
    
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
        config = get_config()
        self.host = host or config.WEB_UI_HOST
        self.port = port or config.WEB_UI_PORT
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """サーバーを起動"""
        server = HTTPServer((self.host, self.port), DashboardHandler)
        self.logger.info(f"🌐 Dashboard starting on http://{self.host}:{self.port}")
        print(f"🏛️ Elders Guild Dashboard available at http://localhost:{self.port}")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("Shutting down dashboard...")
            server.shutdown()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Elders Guild Dashboard with Full Info')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=5555, help='Server port')
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    server = DashboardServer(host=args.host, port=args.port)
    server.run()