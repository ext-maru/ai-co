#!/usr/bin/env python3
"""
AI Company Slack PM Worker - 修正版
Slack統合プロジェクトマネージャーワーカー

このワーカーは以下の機能を提供します：
1. Slack統合プロジェクトマネージャー連携
2. タスクキューイングと優先度管理
3. Claude API統合によるタスク処理
4. リアルタイム進捗報告
5. 結果配信とファイル作成報告
"""

import sys
import json
import time
import threading
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

# Core dependencies
sys.path.append('/home/aicompany/ai_co')
from core.enhanced_base_worker import EnhancedBaseWorker
from libs.queue_manager import QueueManager
from workers.pm_worker import PMWorker

# Slack PM integration
from knowledge_base.slack_integration.slack_pm_manager import SlackPMManager

# Task processing
from libs.async_worker_optimization import ProcessorOptimizer
from libs.common_utils import setup_logger

logger = setup_logger(__name__)

class SlackPMWorker(EnhancedBaseWorker):
    """Slack統合プロジェクトマネージャーワーカー"""
    
    def __init__(self, worker_id: str = "slack-pm-1"):
        super().__init__(worker_id)
        
        # Slack PM管理
        self.slack_pm = SlackPMManager()
        
        # キュープロセッサー
        self.queue_processor = QueueManager()
        
        # Claude APIクライアント
        from libs.claude_client_with_rotation import ClaudeClientWithRotation
        self.claude_client = ClaudeClientWithRotation()
        
        # タスク管理
        self.active_tasks: Dict[str, Dict] = {}
        self.task_results: Dict[str, Dict] = {}
        
        # ワーカー状態
        self.running = False
        self.progress_thread: Optional[threading.Thread] = None
        
        # Slack PMコールバック設定
        self.slack_pm.set_task_creation_callback(self._handle_task_creation)
        self.slack_pm.set_approval_callback(self._handle_approval_request)
        self.slack_pm.set_completion_callback(self._handle_task_completion)
        
        logger.info(f"📋 {self.worker_id} 初期化完了")
    
    def start(self):
        """ワーカー開始"""
        logger.info(f"🚀 {self.worker_id} 開始")
        
        # RabbitMQ接続
        try:
            import pika
            connection_params = pika.ConnectionParameters(host='localhost')
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            
            # キュー宣言
            self.channel.queue_declare(queue='slack_pm_tasks', durable=True)
            logger.info("📡 RabbitMQ接続成功")
        except Exception as e:
            logger.error(f"RabbitMQ接続失敗: {e}")
            return
        
        # Slack PM開始
        try:
            # RTMは別スレッドで開始
            rtm_thread = threading.Thread(target=self.slack_pm.start_rtm, daemon=True)
            rtm_thread.start()
            logger.info("📱 Slack RTM開始")
        except Exception as e:
            logger.error(f"Slack RTM開始失敗: {e}")
        
        # 進捗監視スレッド開始
        self.running = True
        self.progress_thread = threading.Thread(target=self._progress_monitor, daemon=True)
        self.progress_thread.start()
        
        # メインループ
        try:
            logger.info(f"📋 {self.worker_id} 待機中 - Slack対話型PM有効")
            
            # キュー消費設定
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue='slack_pm_tasks', 
                on_message_callback=self._process_slack_task
            )
            
            # メッセージ消費開始
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("🛑 ワーカー停止中...")
            self.stop()
    
    def stop(self):
        """ワーカー停止"""
        self.running = False
        
        # Slack PM停止
        try:
            self.slack_pm.stop_rtm()
        except Exception as e:
            logger.error(f"Slack PM停止エラー: {e}")
        
        # キュープロセッサー停止
        try:
            self.queue_processor.stop_processing()
        except Exception as e:
            logger.error(f"Queue Processor停止エラー: {e}")
        
        # RabbitMQ停止
        try:
            if self.channel:
                self.channel.stop_consuming()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            logger.error(f"RabbitMQ停止エラー: {e}")
        
        # スレッド終了待機
        if self.progress_thread:
            self.progress_thread.join(timeout=5)
        
        logger.info("👋 Slack PM Worker 終了")
    
    def get_status(self) -> dict:
        """ワーカーステータス取得"""
        return {
            'worker_id': self.worker_id,
            'running': self.running,
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.task_results),
            'slack_sessions': len(getattr(self.slack_pm, 'active_sessions', {})),
        }

if __name__ == "__main__":
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "slack-pm-1"
    worker = SlackPMWorker(worker_id)
    
    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("キーボード割り込み受信")
    finally:
        worker.stop()