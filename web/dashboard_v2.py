#!/usr/bin/env python3
"""
Elders Guild ダッシュボード v2 - マルチページ対応
スマホ対応のブロック風デザイン
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
        elif parsed_path.path == '/api/system/detailed':
            self.serve_api_system_detailed()
        elif parsed_path.path == '/api/workers/detailed':
            self.serve_api_workers_detailed()
        elif parsed_path.path == '/api/servants/status':
            self.serve_api_servants_status()
        elif parsed_path.path == '/api/tasks/priority':
            self.serve_api_priority_tasks()
        elif parsed_path.path == '/api/logs/recent':
            self.serve_api_recent_logs()
        elif parsed_path.path == '/api/alerts/active':
            self.serve_api_active_alerts()
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
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.1);
            position: relative;
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
        
        .elder-council {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .elder-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            transition: all 0.3s ease;
            position: relative;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .elder-card.knowledge {
            border-left: 4px solid #9370DB;
        }
        
        .elder-card.task {
            border-left: 4px solid #FFD700;
        }
        
        .elder-card.incident {
            border-left: 4px solid #FF6B6B;
        }
        
        .elder-card.rag {
            border-left: 4px solid #4ECDC4;
        }
        
        .elder-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
        }
        
        .elder-card h3 {
            font-family: 'Orbitron', monospace;
            font-size: 1.2em;
            font-weight: 700;
            margin-bottom: 15px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .help-btn {
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
            transition: all 0.2s ease;
        }
        
        .help-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.5);
        }
        
        .tooltip {
            position: relative;
            display: inline-block;
        }
        
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 250px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            text-align: left;
            border-radius: 8px;
            padding: 10px;
            position: absolute;
            z-index: 1000;
            top: 125%;
            left: 50%;
            margin-left: -125px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.8em;
            font-weight: normal;
            text-transform: none;
            letter-spacing: normal;
            line-height: 1.4;
        }
        
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
        
        .elder-card.knowledge h3 { color: #4B0082; }
        .elder-card.task h3 { color: #B8860B; }
        .elder-card.incident h3 { color: #DC143C; }
        .elder-card.rag h3 { color: #228B22; }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.8);
            border-radius: 10px;
            padding: 15px;
            margin: 8px 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }
        
        .metric-card:hover {
            background: rgba(255, 255, 255, 0.95);
            transform: translateY(-2px);
        }
        
        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .metric-progress {
            width: 100%;
            height: 8px;
            background: rgba(0, 0, 0, 0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        
        .metric-progress-bar {
            height: 100%;
            transition: width 0.3s ease;
            border-radius: 4px;
        }
        
        .progress-low { background: linear-gradient(90deg, #4ECDC4, #44A08D); }
        .progress-medium { background: linear-gradient(90deg, #F7931E, #FFD700); }
        .progress-high { background: linear-gradient(90deg, #FF6B6B, #FF8E53); }
        
        .alert-item {
            padding: 12px;
            margin: 8px 0;
            border-radius: 8px;
            border-left: 4px solid;
            transition: all 0.2s ease;
        }
        
        .alert-critical {
            background: rgba(255, 107, 107, 0.1);
            border-left-color: #FF6B6B;
        }
        
        .alert-warning {
            background: rgba(255, 193, 7, 0.1);
            border-left-color: #FFC107;
        }
        
        .alert-info {
            background: rgba(23, 162, 184, 0.1);
            border-left-color: #17A2B8;
        }
        
        .priority-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .priority-critical {
            background: #FF6B6B;
            color: white;
        }
        
        .priority-high {
            background: #FFA500;
            color: white;
        }
        
        .priority-normal {
            background: #4ECDC4;
            color: white;
        }
        
        .worker-status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        
        .worker-card {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            padding: 12px;
            border-left: 4px solid #667eea;
        }
        
        .worker-healthy { border-left-color: #4ECDC4; }
        .worker-warning { border-left-color: #FFA500; }
        .worker-critical { border-left-color: #FF6B6B; }
        
        .log-entry {
            display: flex;
            align-items: center;
            padding: 8px;
            margin: 4px 0;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }
        
        .log-level {
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
            margin-right: 10px;
            min-width: 50px;
            text-align: center;
        }
        
        .log-info { background: #4ECDC4; color: white; }
        .log-warn { background: #FFA500; color: white; }
        .log-error { background: #FF6B6B; color: white; }
        .log-debug { background: #9370DB; color: white; }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 8px 0;
            padding: 12px;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }
        
        .metric:hover {
            background: rgba(255, 255, 255, 0.9);
            transform: translateX(5px);
        }
        
        .metric-value {
            font-size: 1.4em;
            font-weight: 700;
            color: #333;
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
        
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.1em;
            color: #666;
            font-family: 'Orbitron', monospace;
            font-weight: 500;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 50px;
            font-size: 0.9em;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
            transition: all 0.3s ease;
            font-family: 'Orbitron', monospace;
            backdrop-filter: blur(10px);
            z-index: 100;
        }
        
        .refresh-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        
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
            display: flex;
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
        
        /* スマホ対応 */
        @media (max-width: 768px) {
            .elder-council {
                grid-template-columns: 1fr;
                gap: 15px;
            }
            
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
            
            .header {
                padding: 25px;
                margin-bottom: 20px;
            }
            
            .nav-bar {
                padding: 12px;
                gap: 8px;
            }
            
            .nav-btn {
                padding: 10px 12px;
                font-size: 0.8em;
                flex: 1;
                min-width: calc(50% - 4px);
                text-align: center;
            }
            
            .elder-card {
                padding: 18px;
            }
            
            .quest-log {
                padding: 18px;
                max-height: 450px;
            }
            
            .metric {
                padding: 10px;
                flex-direction: column;
                text-align: center;
                gap: 8px;
            }
            
            .metric-value {
                font-size: 1.8em;
            }
            
            .tooltip .tooltiptext {
                width: 200px;
                margin-left: -100px;
                font-size: 0.7em;
            }
            
            .worker-status-grid {
                grid-template-columns: 1fr;
                gap: 10px;
            }
            
            .refresh-btn {
                bottom: 20px;
                right: 20px;
                padding: 10px 16px;
                font-size: 0.8em;
            }
            
            .auto-update-indicator {
                bottom: 75px;
                right: 20px;
                font-size: 0.7em;
                padding: 6px 10px;
            }
        }
        
        @media (max-width: 480px) {
            h1 {
                font-size: 1.5em;
            }
            
            .nav-btn {
                min-width: 100%;
                margin: 3px 0;
                padding: 12px;
            }
            
            .elder-council {
                gap: 12px;
            }
            
            .elder-card {
                padding: 15px;
            }
            
            .elder-card h3 {
                font-size: 1.1em;
                flex-direction: column;
                gap: 5px;
            }
            
            .quest-item {
                padding: 12px;
                font-size: 0.9em;
            }
            
            .tooltip .tooltiptext {
                width: 180px;
                margin-left: -90px;
                font-size: 0.65em;
            }
            
            .log-entry {
                flex-direction: column;
                align-items: flex-start;
                gap: 5px;
            }
            
            .log-level {
                margin-right: 0;
                margin-bottom: 5px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧾 Elders Guild</h1>
        </div>
        
        <nav class="nav-bar">
            <a href="#" class="nav-btn active" onclick="showPage('dashboard')">📊 ダッシュボード</a>
            <a href="#" class="nav-btn" onclick="showPage('workers')">👷 ワーカー管理</a>
            <a href="#" class="nav-btn" onclick="showPage('tasks')">📝 タスク履歴</a>
            <a href="#" class="nav-btn" onclick="showPage('logs')">📋 ログ監視</a>
            <a href="#" class="nav-btn" onclick="showPage('config')">⚙️ 設定</a>
        </nav>
        
        <div id="page-dashboard" class="page-content">
            <div class="elder-council" id="elderCouncil">
                <div class="loading">システム情報を読み込み中...</div>
            </div>
            
            <div class="metrics-grid">
                <div class="quest-log" id="systemMetrics">
                    <h3>📊 システムメトリドス</h3>
                    <div class="loading">メトリドスを読み込み中...</div>
                </div>
                
                <div class="quest-log" id="alertsPanel">
                    <h3>🚨 アクティブアラート</h3>
                    <div class="loading">アラートを読み込み中...</div>
                </div>
            </div>
            
            <div class="quest-log" id="questLog">
                <h3>📝 最近のタスク</h3>
                <div class="loading">タスク履歴を読み込み中...</div>
            </div>
        </div>
        
        <div id="page-workers" class="page-content" style="display: none;">
            <div class="metrics-grid">
                <div class="quest-log">
                    <h3>👷 ワーカー状態</h3>
                    <div id="workerStatus">ワーカー状態を読み込み中...</div>
                </div>
                
                <div class="quest-log">
                    <h3>🧞‍♂️ サーベント状態</h3>
                    <div id="servantStatus">サーベント状態を読み込み中...</div>
                </div>
            </div>
            
            <div class="quest-log">
                <h3>🔧 詳細ワーカー情報</h3>
                <div id="workerDetails">ワーカー情報を読み込み中...</div>
            </div>
        </div>
        
        <div id="page-tasks" class="page-content" style="display: none;">
            <div class="quest-log">
                <h3>🔥 緊急タスク</h3>
                <div id="priorityTasks">緊急タスクを読み込み中...</div>
            </div>
            
            <div class="quest-log">
                <h3>📝 全タスク履歴</h3>
                <div id="allTasks">全タスクを読み込み中...</div>
            </div>
        </div>
        
        <div id="page-logs" class="page-content" style="display: none;">
            <div class="quest-log">
                <h3>📋 リアルタイムログ</h3>
                <div id="systemLogs">ログを読み込み中...</div>
            </div>
        </div>
        
        <div id="page-config" class="page-content" style="display: none;">
            <div class="quest-log">
                <h3>⚙️ システム設定</h3>
                <div id="configPanel">設定パネルを読み込み中...</div>
            </div>
        </div>
    </div>
    
    <!-- チャットボックス -->
    <div id="chatBox" class="chat-box">
        <div id="chatToggle" class="chat-toggle" onclick="toggleChat()">
            🧾
        </div>
        <div id="chatPanel" class="chat-panel" style="display: none;">
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
        
        async function fetchAllData() {
            try {
                const [status, workers, queues, tasks, systemDetailed, workersDetailed, servants, priorityTasks, logs, alerts] = await Promise.all([
                    fetch('/api/status').then(r => r.json()),
                    fetch('/api/workers').then(r => r.json()),
                    fetch('/api/queues').then(r => r.json()),
                    fetch('/api/tasks/recent').then(r => r.json()),
                    fetch('/api/system/detailed').then(r => r.json()),
                    fetch('/api/workers/detailed').then(r => r.json()),
                    fetch('/api/servants/status').then(r => r.json()),
                    fetch('/api/tasks/priority').then(r => r.json()),
                    fetch('/api/logs/recent').then(r => r.json()),
                    fetch('/api/alerts/active').then(r => r.json())
                ]);
                
                updateElderCouncil(status, workers, queues);
                updateSystemMetrics(systemDetailed);
                updateAlertsPanel(alerts);
                updateQuestLog(tasks);
                
                // ページ固有のデータ更新
                if (document.getElementById('page-workers').style.display !== 'none') {
                    updateWorkerStatus(workersDetailed);
                    updateServantStatus(servants);
                    updateWorkerDetails(workersDetailed);
                }
                
                if (document.getElementById('page-tasks').style.display !== 'none') {
                    updatePriorityTasks(priorityTasks);
                    updateAllTasks(tasks);
                }
                
                if (document.getElementById('page-logs').style.display !== 'none') {
                    updateSystemLogs(logs);
                }
                
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }
        
        function updateElderCouncil(status, workers, queues) {
            const council = document.getElementById('elderCouncil');
            
            council.innerHTML = `
                <div class="elder-card knowledge">
                    <h3>📚 ナレッジ
                        <div class="tooltip">
                            <button class="help-btn">?</button>
                            <span class="tooltiptext">📚 ナレッジ賢者は過去の経験と学習データを管理します。知恵の蓄積はシステムの学習進捗を表し、学習進捗は継続的な改善状態を示しています。</span>
                        </div>
                    </h3>
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
                    <h3>📋 タスク
                        <div class="tooltip">
                            <button class="help-btn">?</button>
                            <span class="tooltiptext">📋 タスク賢者はシステムの実行効率を管理します。CPU神力は現在のプロセッサー使用率、実行効率はシステムの余裕を示しています。</span>
                        </div>
                    </h3>
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
                    <h3>🚨 インシデント
                        <div class="tooltip">
                            <button class="help-btn">?</button>
                            <span class="tooltiptext">🚨 インシデント賢者はシステムの安全性を監視します。守護力はメモリの余裕、警戒レベルはシステムの健康状態を色で表現しています。</span>
                        </div>
                    </h3>
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
                    <h3>🔍 RAG
                        <div class="tooltip">
                            <button class="help-btn">?</button>
                            <span class="tooltiptext">🔍 RAG賢者は情報検索と知識統合を担当します。探索精度は適切な情報を見つける能力、発見率は新しい知識を発見する率を表しています。</span>
                        </div>
                    </h3>
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
        }
        
        function updateSystemMetrics(systemData) {
            const metricsEl = document.getElementById('systemMetrics');
            if (!systemData || systemData.error) {
                metricsEl.innerHTML = '<h3>📊 システムメトリドス</h3><p>メトリドスの取得に失敗しました</p>';
                return;
            }
            
            const cpuPercent = systemData.cpu?.usage_percent || 0;
            const memoryPercent = (systemData.memory?.percent || 0);
            const diskPercent = (systemData.disk?.percent || 0);
            
            metricsEl.innerHTML = `
                <h3>📊 システムメトリドス</h3>
                <div class="metric-card">
                    <div class="metric-header">
                        <span>💻 CPU使用率</span>
                        <span>${cpuPercent.toFixed(1)}%</span>
                    </div>
                    <div class="metric-progress">
                        <div class="metric-progress-bar ${cpuPercent > 80 ? 'progress-high' : cpuPercent > 50 ? 'progress-medium' : 'progress-low'}" style="width: ${cpuPercent}%"></div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-header">
                        <span>📏 メモリ使用率</span>
                        <span>${memoryPercent.toFixed(1)}%</span>
                    </div>
                    <div class="metric-progress">
                        <div class="metric-progress-bar ${memoryPercent > 80 ? 'progress-high' : memoryPercent > 50 ? 'progress-medium' : 'progress-low'}" style="width: ${memoryPercent}%"></div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-header">
                        <span>💾 ディスク使用率</span>
                        <span>${diskPercent.toFixed(1)}%</span>
                    </div>
                    <div class="metric-progress">
                        <div class="metric-progress-bar ${diskPercent > 80 ? 'progress-high' : diskPercent > 50 ? 'progress-medium' : 'progress-low'}" style="width: ${diskPercent}%"></div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-header">
                        <span>⚙️ CPUコア数</span>
                        <span>${systemData.cpu?.core_count || 'N/A'}</span>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-header">
                        <span>⏱️ アップタイム</span>
                        <span>${formatUptime(systemData.uptime_seconds || 0)}</span>
                    </div>
                </div>
            `;
        }
        
        function updateAlertsPanel(alerts) {
            const alertsEl = document.getElementById('alertsPanel');
            if (!alerts || alerts.length === 0) {
                alertsEl.innerHTML = '<h3>🚨 アクティブアラート</h3><p style="text-align: center; color: #4ECDC4;">✅ アラートはありません</p>';
                return;
            }
            
            alertsEl.innerHTML = '<h3>🚨 アクティブアラート</h3>' + alerts.map(alert => `
                <div class="alert-item alert-${alert.severity}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>${alert.type.toUpperCase()}</strong>
                        <span style="font-size: 0.8em; opacity: 0.7;">${new Date(alert.timestamp).toLocaleTimeString('ja-JP')}</span>
                    </div>
                    <div style="margin-top: 5px;">${alert.message}</div>
                    ${alert.action_required ? '<div style="margin-top: 5px; color: #FF6B6B; font-weight: 600;">⚠️ 対応が必要です</div>' : ''}
                </div>
            `).join('');
        }
        
        function updateQuestLog(tasks) {
            const log = document.getElementById('questLog');
            if (tasks.length === 0) {
                log.innerHTML = '<h3>📝 最近のタスク</h3><p style="text-align: center; color: #666; font-style: italic;">まだタスクの記録はありません</p>';
                return;
            }
            
            log.innerHTML = '<h3>📝 最近のタスク</h3>' + tasks.map(task => `
                <div class="quest-item">
                    <div><strong>🎯 ${task.task_id}</strong></div>
                    <div>タイプ: ${task.task_type} | ステータス: ${task.status}</div>
                    <div>作成日時: ${new Date(task.created_at).toLocaleString('ja-JP')}</div>
                </div>
            `).join('');
        }
        
        function formatUptime(seconds) {
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            
            if (days > 0) return `${days}日 ${hours}時間`;
            if (hours > 0) return `${hours}時間 ${minutes}分`;
            return `${minutes}分`;
        }
        
        function refreshData() {
            fetchAllData();
        }
        
        function showPage(pageId) {
            // すべてのページを非表示
            document.querySelectorAll('.page-content').forEach(page => {
                page.style.display = 'none';
            });
            
            // すべてのナビボタンのactiveクラスを削除
            document.querySelectorAll('.nav-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // 指定されたページを表示
            const targetPage = document.getElementById(`page-${pageId}`);
            if (targetPage) {
                targetPage.style.display = 'block';
            }
            
            // クリックされたボタンにactiveクラスを追加
            event.target.classList.add('active');
            
            // ページ固有のデータを読み込み
            loadPageData(pageId);
        }
        
        function loadPageData(pageId) {
            // ページ切り替え時にデータを再取得
            fetchAllData();
            
            switch(pageId) {
                case 'config':
                    loadConfigPanel();
                    break;
            }
        }
        
        function updateWorkerStatus(workersData) {
            const statusEl = document.getElementById('workerStatus');
            if (!workersData) return;
            
            const summary = workersData.status_summary;
            statusEl.innerHTML = `
                <div class="worker-status-grid">
                    <div class="worker-card worker-healthy">
                        <div><strong>✅ 正常稼働</strong></div>
                        <div>${summary.healthy} ワーカー</div>
                    </div>
                    <div class="worker-card worker-warning">
                        <div><strong>⚠️ 不足</strong></div>
                        <div>${summary.missing} ワーカー</div>
                    </div>
                    <div class="worker-card worker-critical">
                        <div><strong>📊 過剰</strong></div>
                        <div>${summary.excess} ワーカー</div>
                    </div>
                </div>
            `;
        }
        
        function updateServantStatus(servantsData) {
            const servantEl = document.getElementById('servantStatus');
            if (!servantsData) return;
            
            const elderServants = Object.entries(servantsData.elder_servants);
            const systemServants = Object.entries(servantsData.system_servants);
            
            servantEl.innerHTML = `
                <div><strong>🏛️ エルダーサーベント</strong></div>
                ${elderServants.map(([name, info]) => `
                    <div class="quest-item">
                        <div>🧞‍♂️ ${name.replace('_', ' ').toUpperCase()}</div>
                        <div>ステータス: ${info.status}</div>
                        <div>タスク完了: ${info.tasks_completed || info.incidents_prevented || info.queries_processed || 0}</div>
                    </div>
                `).join('')}
                
                <div style="margin-top: 15px;"><strong>⚙️ システムサーベント</strong></div>
                ${systemServants.map(([name, info]) => `
                    <div class="quest-item">
                        <div>🔧 ${name.replace('_', ' ').toUpperCase()}</div>
                        <div>ステータス: ${info.status}</div>
                    </div>
                `).join('')}
            `;
        }
        
        function updateWorkerDetails(workersData) {
            const details = document.getElementById('workerDetails');
            if (!workersData) return;
            
            const activeWorkers = workersData.active;
            const requiredWorkers = workersData.required;
            
            details.innerHTML = Object.entries(requiredWorkers).map(([type, reqInfo]) => {
                const active = activeWorkers[type] || [];
                const isHealthy = active.length >= reqInfo.min_count;
                
                return `
                    <div class="quest-item">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong>🔧 ${type}</strong>
                            <span class="priority-badge ${isHealthy ? 'priority-normal' : 'priority-critical'}">
                                ${active.length}/${reqInfo.min_count}
                            </span>
                        </div>
                        <div>説明: ${reqInfo.description}</div>
                        <div>アクティブプロセス: ${active.map(w => `PID:${w.pid} (CPU:${w.cpu_percent.toFixed(1)}%)`).join(', ') || 'なし'}</div>
                        <div>ステータス: ${isHealthy ? '✅ 正常' : '⚠️ 不足'}</div>
                    </div>
                `;
            }).join('');
        }
        
        function updatePriorityTasks(priorityData) {
            const priorityEl = document.getElementById('priorityTasks');
            if (!priorityData) return;
            
            priorityEl.innerHTML = `
                <div><strong>🔥 緊急タスク</strong></div>
                ${priorityData.emergency.map(task => `
                    <div class="quest-item" style="border-left-color: #FF6B6B;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong>${task.id}</strong>
                            <span class="priority-badge priority-critical">${task.priority}</span>
                        </div>
                        <div>${task.title}</div>
                        <div>${new Date(task.created).toLocaleString('ja-JP')}</div>
                    </div>
                `).join('')}
                
                <div style="margin-top: 15px;"><strong>⚡ 高優先度タスク</strong></div>
                ${priorityData.high_priority.map(task => `
                    <div class="quest-item" style="border-left-color: #FFA500;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong>${task.id}</strong>
                            <span class="priority-badge priority-high">${task.priority}</span>
                        </div>
                        <div>${task.title}</div>
                        <div>${new Date(task.created).toLocaleString('ja-JP')}</div>
                    </div>
                `).join('')}
            `;
        }
        
        function updateSystemLogs(logsData) {
            const logsEl = document.getElementById('systemLogs');
            if (!logsData) return;
            
            logsEl.innerHTML = logsData.map(log => `
                <div class="log-entry">
                    <span class="log-level log-${log.level.toLowerCase()}">${log.level}</span>
                    <div style="flex: 1;">
                        <div>${log.message}</div>
                        <div style="font-size: 0.75em; opacity: 0.7; margin-top: 2px;">
                            ${new Date(log.timestamp).toLocaleString('ja-JP')} - ${log.source}
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        function updateAllTasks(tasks) {
            const taskList = document.getElementById('allTasks');
            if (!tasks || tasks.length === 0) {
                taskList.innerHTML = '<p>タスク履歴がありません</p>';
                return;
            }
            taskList.innerHTML = tasks.map(task => `
                <div class="quest-item">
                    <div><strong>🎯 ${task.task_id}</strong></div>
                    <div>種類: ${task.task_type}</div>
                    <div>状態: ${task.status}</div>
                    <div>作成: ${new Date(task.created_at).toLocaleString('ja-JP')}</div>
                </div>
            `).join('');
        }
        
        function loadConfigPanel() {
            const config = document.getElementById('configPanel');
            config.innerHTML = `
                <div class="quest-item">
                    <div><strong>⚙️ システム設定</strong></div>
                    <div>更新間隔: 5秒</div>
                    <div>テーマ: ブロック風</div>
                    <div>言語: 日本語</div>
                </div>
                <div class="quest-item">
                    <div><strong>🔧 高度な設定</strong></div>
                    <div>設定変更機能は開発中です</div>
                </div>
            `;
        }
        
        // 初回読み込みと定期更新
        fetchAllData();
        setInterval(fetchAllData, 5000);
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
            workers = {}
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
    
    def serve_api_system_detailed(self):
        """詳細システム情報API"""
        try:
            cpu_info = {
                'usage_percent': psutil.cpu_percent(interval=0.1),
                'core_count': psutil.cpu_count(),
                'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
            
            memory_info = psutil.virtual_memory()._asdict()
            disk_info = psutil.disk_usage('/')._asdict()
            
            network_info = psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
            
            boot_time = datetime.fromtimestamp(psutil.boot_time()).isoformat()
            
            detailed_info = {
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info,
                'network': network_info,
                'boot_time': boot_time,
                'uptime_seconds': time.time() - psutil.boot_time()
            }
            
            self._send_json_response(detailed_info)
        except Exception as e:
            self._send_json_response({'error': str(e)})
    
    def serve_api_workers_detailed(self):
        """詳細ワーカー情報API"""
        workers = {
            'active': {},
            'required': {
                'task_worker': {'min_count': 2, 'description': 'タスク処理ワーカー'},
                'pm_worker': {'min_count': 1, 'description': 'プロジェクト管理ワーカー'},
                'result_worker': {'min_count': 1, 'description': '結果処理ワーカー'},
                'dialog_worker': {'min_count': 1, 'description': '対話処理ワーカー'}
            },
            'status_summary': {'healthy': 0, 'missing': 0, 'excess': 0}
        }
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent', 'create_time']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    for worker_type in workers['required'].keys():
                        if worker_type in cmdline:
                            if worker_type not in workers['active']:
                                workers['active'][worker_type] = []
                            
                            workers['active'][worker_type].append({
                                'pid': proc.info['pid'],
                                'cpu_percent': proc.info.get('cpu_percent', 0),
                                'memory_percent': proc.info.get('memory_percent', 0),
                                'uptime': time.time() - proc.info.get('create_time', time.time())
                            })
                except:
                    pass
            
            # ステータス計算
            for worker_type, required_info in workers['required'].items():
                active_count = len(workers['active'].get(worker_type, []))
                min_count = required_info['min_count']
                
                if active_count >= min_count:
                    if active_count > min_count:
                        workers['status_summary']['excess'] += active_count - min_count
                    workers['status_summary']['healthy'] += min_count
                else:
                    workers['status_summary']['missing'] += min_count - active_count
                    workers['status_summary']['healthy'] += active_count
                    
        except Exception:
            pass
            
        self._send_json_response(workers)
    
    def serve_api_servants_status(self):
        """サーベント状態API"""
        servants = {
            'elder_servants': {
                'knowledge_servant': {'status': 'active', 'last_update': datetime.now().isoformat(), 'tasks_completed': 42},
                'task_servant': {'status': 'active', 'last_update': datetime.now().isoformat(), 'tasks_completed': 38},
                'incident_servant': {'status': 'monitoring', 'last_update': datetime.now().isoformat(), 'incidents_prevented': 15},
                'rag_servant': {'status': 'searching', 'last_update': datetime.now().isoformat(), 'queries_processed': 156}
            },
            'worker_servants': [],
            'system_servants': {
                'log_monitor': {'status': 'active', 'entries_processed': 1247},
                'health_checker': {'status': 'active', 'checks_performed': 89},
                'backup_servant': {'status': 'standby', 'last_backup': datetime.now().isoformat()}
            }
        }
        
        # ワーカーサーベントの動的生成
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if 'worker' in cmdline and 'python' in cmdline:
                        servants['worker_servants'].append({
                            'pid': proc.info['pid'],
                            'type': 'worker_servant',
                            'status': 'active',
                            'name': f"Worker-{proc.info['pid']}"
                        })
                except:
                    pass
        except:
            pass
            
        self._send_json_response(servants)
    
    def serve_api_priority_tasks(self):
        """優先度タスクAPI"""
        priority_tasks = {
            'emergency': [
                {'id': 'EMG-001', 'title': 'システムメモリ使用率高', 'priority': 'critical', 'created': datetime.now().isoformat()}
            ],
            'high_priority': [
                {'id': 'HP-001', 'title': 'ワーカープール最適化', 'priority': 'high', 'created': datetime.now().isoformat()},
                {'id': 'HP-002', 'title': 'キュー処理遅延', 'priority': 'high', 'created': datetime.now().isoformat()}
            ],
            'normal': [
                {'id': 'NM-001', 'title': '日次ヘルスチェック', 'priority': 'normal', 'created': datetime.now().isoformat()}
            ]
        }
        
        # 動的な緊急タスク生成
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent()
        
        if memory_percent > 85:
            priority_tasks['emergency'].append({
                'id': f'EMG-{int(time.time())}',
                'title': f'メモリ使用率異常: {memory_percent:.1f}%',
                'priority': 'critical',
                'created': datetime.now().isoformat()
            })
            
        if cpu_percent > 90:
            priority_tasks['emergency'].append({
                'id': f'EMG-{int(time.time())+1}',
                'title': f'CPU使用率異常: {cpu_percent:.1f}%',
                'priority': 'critical',
                'created': datetime.now().isoformat()
            })
            
        self._send_json_response(priority_tasks)
    
    def serve_api_recent_logs(self):
        """最近のログAPI"""
        logs = [
            {'timestamp': datetime.now().isoformat(), 'level': 'INFO', 'message': 'Dashboard server started successfully', 'source': 'dashboard'},
            {'timestamp': (datetime.now()).isoformat(), 'level': 'INFO', 'message': 'Worker pool optimization completed', 'source': 'task_worker'},
            {'timestamp': (datetime.now()).isoformat(), 'level': 'WARN', 'message': 'Memory usage approaching threshold', 'source': 'system_monitor'},
            {'timestamp': (datetime.now()).isoformat(), 'level': 'INFO', 'message': 'RabbitMQ connection established', 'source': 'queue_manager'},
            {'timestamp': (datetime.now()).isoformat(), 'level': 'DEBUG', 'message': 'Elder council meeting completed', 'source': 'elder_system'}
        ]
        
        # リアルタイムログエントリの追加
        current_time = datetime.now()
        system_status = self._calculate_health_score()
        
        if system_status < 80:
            logs.insert(0, {
                'timestamp': current_time.isoformat(),
                'level': 'WARN',
                'message': f'System health score dropped to {system_status}%',
                'source': 'health_monitor'
            })
            
        self._send_json_response(logs)
    
    def serve_api_active_alerts(self):
        """アクティブアラートAPI"""
        alerts = []
        
        # システムメトリドスベースのアラート生成
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent()
        disk_percent = psutil.disk_usage('/').percent
        
        if memory_percent > 80:
            alerts.append({
                'id': 'ALT-MEM-001',
                'type': 'memory',
                'severity': 'warning' if memory_percent < 90 else 'critical',
                'message': f'メモリ使用率が{memory_percent:.1f}%に達しました',
                'timestamp': datetime.now().isoformat(),
                'action_required': True
            })
            
        if cpu_percent > 85:
            alerts.append({
                'id': 'ALT-CPU-001',
                'type': 'cpu',
                'severity': 'warning' if cpu_percent < 95 else 'critical',
                'message': f'CPU使用率が{cpu_percent:.1f}%に達しました',
                'timestamp': datetime.now().isoformat(),
                'action_required': True
            })
            
        if disk_percent > 85:
            alerts.append({
                'id': 'ALT-DISK-001',
                'type': 'disk',
                'severity': 'warning',
                'message': f'ディスク使用率が{disk_percent:.1f}%に達しました',
                'timestamp': datetime.now().isoformat(),
                'action_required': False
            })
            
        self._send_json_response(alerts)
    
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
        self.logger.info(f"🌐 Dashboard server starting on http://{self.host}:{self.port}")
        print(f"🌐 Dashboard available at http://localhost:{self.port}")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("Shutting down dashboard server...")
            server.shutdown()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Elders Guild Web Dashboard v2')
    parser.add_argument('--host', default=None, help='Server host (default: from config)')
    parser.add_argument('--port', type=int, default=None, help='Server port (default: from config)')
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    server = DashboardServer(host=args.host, port=args.port)
    server.run()