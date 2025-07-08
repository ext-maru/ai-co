#!/usr/bin/env python3
"""
拡張版BaseWorker - 新機能を統合
モニタリング、リトライ、DLQ機能を含む
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.base_worker import BaseWorker as OriginalBaseWorker
from core.monitoring_mixin import MonitoringMixin
from core.retry_decorator import RetryableWorker, retry, RetryPresets
from core.dlq_mixin import DeadLetterQueueMixin
from typing import Optional, Dict, Any
import json
import logging

class EnhancedBaseWorker(OriginalBaseWorker, MonitoringMixin, RetryableWorker, DeadLetterQueueMixin):
    """機能拡張版BaseWorker"""
    
    def __init__(self, worker_type: str, worker_id: Optional[str] = None,
                 input_queue: Optional[str] = None, output_queue: Optional[str] = None,
                 enable_monitoring: bool = True, enable_dlq: bool = True,
                 retry_config: Optional[dict] = None):
        """
        Args:
            worker_type: ワーカータイプ
            worker_id: ワーカーID
            input_queue: 入力キュー名
            output_queue: 出力キュー名
            enable_monitoring: モニタリング機能の有効化
            enable_dlq: DLQ機能の有効化
            retry_config: リトライ設定
        """
        # 基底クラスの初期化
        OriginalBaseWorker.__init__(self, worker_type, worker_id, input_queue, output_queue)
        
        # ミックスインの初期化
        if enable_monitoring:
            MonitoringMixin.__init__(self)
        RetryableWorker.__init__(self, retry_config or RetryPresets.STANDARD)
        
        self.enable_monitoring = enable_monitoring
        self.enable_dlq = enable_dlq
        
        # DLQのセットアップ
        if enable_dlq and self.channel:
            self.setup_dlq()
    
    def process_message_with_retry(self, ch, method, properties, body):
        """リトライ機能付きメッセージ処理"""
        
        # モニタリング：タスク開始
        if self.enable_monitoring:
            start_time = self.record_task_start()
        
        # リトライ回数の追跡
        retry_count = 0
        if properties.headers and 'x-retry-count' in properties.headers:
            retry_count = properties.headers['x-retry-count']
        
        try:
            # リトライデコレータを使用してprocess_messageを実行
            @retry(**self.retry_config)
            def process_with_retry():
                return self.process_message(ch, method, properties, body)
            
            result = process_with_retry()
            
            # モニタリング：成功記録
            if self.enable_monitoring:
                self.record_task_complete(start_time, success=True)
            
            # メッセージの確認
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process message after retries: {str(e)}")
            
            # モニタリング：エラー記録
            if self.enable_monitoring:
                self.record_task_complete(start_time, success=False)
                self.record_error(e)
            
            # DLQへの送信
            if self.enable_dlq:
                try:
                    task = json.loads(body) if isinstance(body, bytes) else body
                    self.send_to_dlq(task, e, attempts=retry_count + 1)
                except:
                    self.logger.error("Failed to send to DLQ")
            
            # メッセージを削除（DLQに送信済み）
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
            raise
    
    def run(self):
        """拡張版run - リトライとモニタリング付き"""
        try:
            # 接続の確立
            self._setup_connection()
            
            self.logger.info(f"🚀 Enhanced {self.worker_type} worker {self.worker_id} started")
            self.logger.info(f"📊 Monitoring: {'Enabled' if self.enable_monitoring else 'Disabled'}")
            self.logger.info(f"💀 DLQ: {'Enabled' if self.enable_dlq else 'Disabled'}")
            self.logger.info(f"🔄 Retry: {self.retry_config}")
            
            # メッセージ消費（拡張版を使用）
            self.channel.basic_consume(
                queue=self.input_queue,
                on_message_callback=self.process_message_with_retry,
                auto_ack=False
            )
            
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            self.logger.info("Shutting down gracefully...")
            self.stop()
        except Exception as e:
            self.logger.error(f"Worker error: {str(e)}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """拡張版ヘルスチェック"""
        base_health = super().health_check()
        
        # モニタリング情報を追加
        if self.enable_monitoring:
            base_health['monitoring'] = self.performance_stats
            base_health['health_score'] = self.calculate_health_score()
        
        # DLQ情報を追加
        if self.enable_dlq:
            base_health['dlq'] = self.get_dlq_stats()
        
        return base_health
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """拡張統計情報"""
        stats = {
            'worker_info': {
                'type': self.worker_type,
                'id': self.worker_id,
                'status': 'running'
            }
        }
        
        if self.enable_monitoring:
            stats['performance'] = self.get_monitoring_data()
        
        if self.enable_dlq:
            stats['dlq'] = self.get_dlq_stats()
        
        stats['retry_config'] = self.retry_config
        
        return stats

# エクスポート用のエイリアス
BaseWorker = EnhancedBaseWorker
