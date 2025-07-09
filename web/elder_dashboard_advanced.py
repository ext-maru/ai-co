#!/usr/bin/env python3
"""
Elder Dashboard Advanced Features
エルダーズ・ハーモニー・システム高度機能拡張

新機能:
- リアルタイム4賢者ステータス監視
- プロトコル実行アラート
- 予測分析とトレンド表示
- エルダー評議会レポート統合
- 自動最適化提案

設計: クロードエルダー
実装日: 2025年7月9日
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from flask import Blueprint, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import time
from dataclasses import dataclass

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ElderAlert:
    """エルダーアラート"""
    id: str
    type: str  # 'warning', 'error', 'info', 'success'
    title: str
    message: str
    timestamp: datetime
    protocol: Optional[str] = None
    sage: Optional[str] = None
    priority: str = 'normal'  # 'low', 'normal', 'high', 'critical'

class AdvancedElderDashboard:
    """高度Elder Dashboard拡張機能"""
    
    def __init__(self, socketio: SocketIO, project_root: Path):
        self.socketio = socketio
        self.project_root = project_root
        self.logs_dir = project_root / "logs"
        self.db_path = project_root / "elder_dashboard.db"
        
        # 監視状態
        self.monitoring_active = False
        self.monitoring_thread = None
        self.connected_clients = set()
        self.alerts = []
        
        # 4賢者ステータス
        self.sage_status = {
            'knowledge': {'active': True, 'last_consultation': None, 'load': 0},
            'task': {'active': True, 'last_consultation': None, 'load': 0},
            'incident': {'active': True, 'last_consultation': None, 'load': 0},
            'rag': {'active': True, 'last_consultation': None, 'load': 0}
        }
        
        # プロトコル実行統計
        self.protocol_stats = {
            'lightning': {'executions': 0, 'success_rate': 0, 'avg_time': 0},
            'council': {'executions': 0, 'success_rate': 0, 'avg_time': 0},
            'grand': {'executions': 0, 'success_rate': 0, 'avg_time': 0}
        }
        
        logger.info("🚀 Advanced Elder Dashboard 初期化完了")
    
    def start_advanced_monitoring(self):
        """高度監視機能開始"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._advanced_monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            logger.info("📡 高度監視機能開始")
    
    def stop_advanced_monitoring(self):
        """高度監視機能停止"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        logger.info("⏹️ 高度監視機能停止")
    
    def _advanced_monitoring_loop(self):
        """高度監視ループ"""
        while self.monitoring_active:
            try:
                # 1. 4賢者ステータス更新
                self._update_sage_status()
                
                # 2. プロトコル統計更新
                self._update_protocol_stats()
                
                # 3. アラート検出
                self._detect_alerts()
                
                # 4. 予測分析実行
                predictions = self._run_predictive_analysis()
                
                # 5. クライアントに送信
                if self.connected_clients:
                    self.socketio.emit('advanced_update', {
                        'timestamp': datetime.now().isoformat(),
                        'sage_status': self.sage_status,
                        'protocol_stats': self.protocol_stats,
                        'alerts': [self._alert_to_dict(a) for a in self.alerts[-10:]],
                        'predictions': predictions
                    })
                
                time.sleep(5)  # 5秒間隔
                
            except Exception as e:
                logger.error(f"❌ 高度監視ループエラー: {e}")
                time.sleep(10)
    
    def _update_sage_status(self):
        """4賢者ステータス更新"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 過去1時間の相談回数
            one_hour_ago = datetime.now() - timedelta(hours=1)
            cursor.execute('''
                SELECT sage_name, COUNT(*) as consultations,
                       MAX(timestamp) as last_consultation
                FROM sage_consultations 
                WHERE timestamp > ?
                GROUP BY sage_name
            ''', (one_hour_ago.isoformat(),))
            
            recent_activity = cursor.fetchall()
            
            # ステータス更新
            for sage_name in self.sage_status:
                found = False
                for sage, count, last_time in recent_activity:
                    if sage == sage_name:
                        self.sage_status[sage_name]['load'] = count
                        self.sage_status[sage_name]['last_consultation'] = last_time
                        found = True
                        break
                
                if not found:
                    self.sage_status[sage_name]['load'] = 0
                    self.sage_status[sage_name]['last_consultation'] = None
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ 4賢者ステータス更新エラー: {e}")
    
    def _update_protocol_stats(self):
        """プロトコル統計更新"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 過去24時間の統計
            day_ago = datetime.now() - timedelta(days=1)
            cursor.execute('''
                SELECT protocol, COUNT(*) as executions,
                       AVG(CASE WHEN approved = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                       AVG(execution_time) as avg_time
                FROM protocol_history 
                WHERE timestamp > ?
                GROUP BY protocol
            ''', (day_ago.isoformat(),))
            
            stats = cursor.fetchall()
            
            for protocol, executions, success_rate, avg_time in stats:
                if protocol.lower() in self.protocol_stats:
                    self.protocol_stats[protocol.lower()] = {
                        'executions': executions,
                        'success_rate': success_rate * 100,
                        'avg_time': avg_time or 0
                    }
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ プロトコル統計更新エラー: {e}")
    
    def _detect_alerts(self):
        """アラート検出"""
        current_time = datetime.now()
        
        # 1. 4賢者の負荷チェック
        for sage_name, status in self.sage_status.items():
            if status['load'] > 50:  # 1時間で50回以上の相談
                alert = ElderAlert(
                    id=f"sage_overload_{sage_name}_{int(time.time())}",
                    type='warning',
                    title=f'{sage_name}賢者 高負荷警告',
                    message=f'{sage_name}賢者の相談回数が1時間で{status["load"]}回を記録',
                    timestamp=current_time,
                    sage=sage_name,
                    priority='high'
                )
                self._add_alert(alert)
        
        # 2. プロトコル成功率チェック
        for protocol, stats in self.protocol_stats.items():
            if stats['success_rate'] < 80 and stats['executions'] > 5:
                alert = ElderAlert(
                    id=f"protocol_failure_{protocol}_{int(time.time())}",
                    type='error',
                    title=f'{protocol} Protocol 成功率低下',
                    message=f'{protocol}プロトコルの成功率が{stats["success_rate"]:.1f}%に低下',
                    timestamp=current_time,
                    protocol=protocol,
                    priority='high'
                )
                self._add_alert(alert)
        
        # 3. 実行時間異常チェック
        for protocol, stats in self.protocol_stats.items():
            expected_time = {'lightning': 1, 'council': 5, 'grand': 30}
            if stats['avg_time'] > expected_time.get(protocol, 10) * 2:
                alert = ElderAlert(
                    id=f"protocol_slow_{protocol}_{int(time.time())}",
                    type='warning',
                    title=f'{protocol} Protocol 実行時間異常',
                    message=f'{protocol}プロトコルの平均実行時間が{stats["avg_time"]:.1f}秒',
                    timestamp=current_time,
                    protocol=protocol,
                    priority='medium'
                )
                self._add_alert(alert)
    
    def _add_alert(self, alert: ElderAlert):
        """アラート追加"""
        # 重複チェック
        for existing in self.alerts:
            if existing.id == alert.id:
                return
        
        self.alerts.append(alert)
        
        # 古いアラートを削除（最新100件を保持）
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        # 即座にクライアントに通知
        if self.connected_clients:
            self.socketio.emit('new_alert', self._alert_to_dict(alert))
    
    def _alert_to_dict(self, alert: ElderAlert) -> Dict:
        """アラートを辞書に変換"""
        return {
            'id': alert.id,
            'type': alert.type,
            'title': alert.title,
            'message': alert.message,
            'timestamp': alert.timestamp.isoformat(),
            'protocol': alert.protocol,
            'sage': alert.sage,
            'priority': alert.priority
        }
    
    def _run_predictive_analysis(self) -> Dict:
        """予測分析実行"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 過去7日間のデータ
            week_ago = datetime.now() - timedelta(days=7)
            cursor.execute('''
                SELECT DATE(timestamp) as date, 
                       protocol, 
                       COUNT(*) as count
                FROM protocol_history 
                WHERE timestamp > ?
                GROUP BY DATE(timestamp), protocol
                ORDER BY date
            ''', (week_ago.isoformat(),))
            
            daily_stats = cursor.fetchall()
            
            # 単純な線形予測
            predictions = {
                'next_day_commits': 0,
                'trend': 'stable',
                'busiest_protocol': 'council',
                'recommended_actions': []
            }
            
            if daily_stats:
                # 過去3日の平均
                recent_total = sum(count for _, _, count in daily_stats[-3:])
                predictions['next_day_commits'] = recent_total // 3
                
                # トレンド分析
                if len(daily_stats) >= 2:
                    recent_avg = sum(count for _, _, count in daily_stats[-2:]) / 2
                    older_avg = sum(count for _, _, count in daily_stats[-4:-2]) / 2 if len(daily_stats) >= 4 else recent_avg
                    
                    if recent_avg > older_avg * 1.2:
                        predictions['trend'] = 'increasing'
                    elif recent_avg < older_avg * 0.8:
                        predictions['trend'] = 'decreasing'
                    else:
                        predictions['trend'] = 'stable'
                
                # 最も多用されるプロトコル
                protocol_counts = {}
                for _, protocol, count in daily_stats:
                    protocol_counts[protocol] = protocol_counts.get(protocol, 0) + count
                
                if protocol_counts:
                    predictions['busiest_protocol'] = max(protocol_counts, key=protocol_counts.get)
            
            # 推奨アクション
            if predictions['trend'] == 'increasing':
                predictions['recommended_actions'].append('システムリソースの監視強化を推奨')
            if predictions['next_day_commits'] > 20:
                predictions['recommended_actions'].append('Grand Protocolの準備を推奨')
            
            conn.close()
            return predictions
            
        except Exception as e:
            logger.error(f"❌ 予測分析エラー: {e}")
            return {'error': str(e)}
    
    def get_elder_council_reports(self) -> List[Dict]:
        """エルダー評議会レポート取得"""
        try:
            reports_dir = self.project_root / "knowledge_base" / "elder_council_reports"
            if not reports_dir.exists():
                return []
            
            reports = []
            for report_file in reports_dir.glob("*.json"):
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    report_data['file_name'] = report_file.name
                    reports.append(report_data)
            
            # 時系列順にソート
            reports.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return reports[:10]  # 最新10件
            
        except Exception as e:
            logger.error(f"❌ エルダー評議会レポート取得エラー: {e}")
            return []
    
    def get_optimization_suggestions(self) -> List[Dict]:
        """最適化提案取得"""
        suggestions = []
        
        # プロトコル使用パターン分析
        council_usage = self.protocol_stats.get('council', {}).get('executions', 0)
        lightning_usage = self.protocol_stats.get('lightning', {}).get('executions', 0)
        grand_usage = self.protocol_stats.get('grand', {}).get('executions', 0)
        
        if council_usage > lightning_usage * 5:
            suggestions.append({
                'type': 'protocol_optimization',
                'title': 'Lightning Protocol活用推奨',
                'description': 'Council Protocolの使用頻度が高いため、緊急性の高いタスクはLightning Protocolを検討してください',
                'priority': 'medium'
            })
        
        if grand_usage == 0:
            suggestions.append({
                'type': 'protocol_preparation',
                'title': 'Grand Protocol準備推奨',
                'description': 'Grand Protocolが未使用です。大規模変更に備えて事前テストを推奨します',
                'priority': 'low'
            })
        
        # 4賢者負荷バランス
        loads = [status['load'] for status in self.sage_status.values()]
        if max(loads) > min(loads) * 3:
            suggestions.append({
                'type': 'load_balancing',
                'title': '4賢者負荷バランス調整',
                'description': '賢者間の負荷に偏りが見られます。タスク分散の見直しを推奨します',
                'priority': 'high'
            })
        
        return suggestions
    
    def handle_client_connect(self, client_id: str):
        """クライアント接続処理"""
        self.connected_clients.add(client_id)
        logger.info(f"📱 Advanced Dashboard クライアント接続: {client_id}")
        
        # 初期データ送信
        self.socketio.emit('initial_advanced_data', {
            'sage_status': self.sage_status,
            'protocol_stats': self.protocol_stats,
            'alerts': [self._alert_to_dict(a) for a in self.alerts[-10:]],
            'council_reports': self.get_elder_council_reports(),
            'optimization_suggestions': self.get_optimization_suggestions()
        })
    
    def handle_client_disconnect(self, client_id: str):
        """クライアント切断処理"""
        self.connected_clients.discard(client_id)
        logger.info(f"📱 Advanced Dashboard クライアント切断: {client_id}")
    
    def get_system_overview(self) -> Dict:
        """システム概要取得"""
        return {
            'sage_status': self.sage_status,
            'protocol_stats': self.protocol_stats,
            'active_alerts': len([a for a in self.alerts if a.priority in ['high', 'critical']]),
            'total_alerts': len(self.alerts),
            'monitoring_active': self.monitoring_active,
            'connected_clients': len(self.connected_clients)
        }

# グローバルインスタンス
advanced_dashboard = None

def init_advanced_dashboard(socketio: SocketIO, project_root: Path):
    """高度Dashboard初期化"""
    global advanced_dashboard
    advanced_dashboard = AdvancedElderDashboard(socketio, project_root)
    return advanced_dashboard