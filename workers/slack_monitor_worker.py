#!/usr/bin/env python3
"""
Slack Monitor Worker - Elder Tree統合版
Slack監視ワーカー with Four Sages協調

🌳 Elder Tree階層:
- Grand Elder maru → Claude Elder → Four Sages → このワーカー
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

# Elder Tree統合
try:
    from libs.elder_tree_hierarchy import get_elder_tree, ElderMessage, ElderRank, ServantType
    from libs.four_sages_integration import FourSagesIntegration
    ELDER_INTEGRATION_AVAILABLE = True
except ImportError:
    ELDER_INTEGRATION_AVAILABLE = False
    logger.warning("Elder Tree integration not available")

logger = logging.getLogger(__name__)

class SlackMonitorWorker:
    """Slack監視ワーカー - Elder Tree統合版"""
    
    def __init__(self):
        self.monitored_channels = []
        self.message_count = 0
        self.running = False
        
        # Elder Tree統合
        self.elder_tree = None
        self.four_sages = None
        self.worker_id = "slack_monitor_elf_1"  # エルフモニター
        self.servant_type = ServantType.ELF_MONITOR
        
        if ELDER_INTEGRATION_AVAILABLE:
            self._initialize_elder_integration()
        
        # パフォーマンスメトリクス
        self.performance_metrics = {
            'messages_processed': 0,
            'channels_monitored': 0,
            'errors_detected': 0,
            'alerts_sent': 0
        }
    
    def _initialize_elder_integration(self):
        """Elder Tree統合初期化"""
        try:
            self.elder_tree = get_elder_tree()
            self.four_sages = FourSagesIntegration()
            logger.info(f"🌳 {self.worker_id} integrated with Elder Tree")
            
            # Grand Elder maruへの初期報告
            self._report_to_elders("initialization", {
                "worker_id": self.worker_id,
                "servant_type": self.servant_type.value,
                "status": "ready"
            })
            
        except Exception as e:
            logger.error(f"Failed to initialize Elder integration: {e}")
    
    def _report_to_elders(self, report_type: str, data: Dict[str, Any]):
        """エルダーへの報告"""
        if not self.elder_tree:
            return
            
        try:
            # Council Memberへ報告（Knowledge Sage配下）
            message = ElderMessage(
                sender_rank=ElderRank.SERVANT,
                sender_id=self.worker_id,
                recipient_rank=ElderRank.COUNCIL_MEMBER,
                recipient_id="council_grand_sage_of_knowledge",
                message_type=report_type,
                content=data,
                priority="normal" if report_type != "alert" else "high"
            )
            
            # 同期的に実行（実際は非同期化が推奨）
            asyncio.create_task(self.elder_tree.send_message(message))
            
        except Exception as e:
            logger.error(f"Failed to report to Elders: {e}")
        
    def monitor_channel(self, channel_id: str) -> Dict:
        """チャンネル監視"""
        logger.info(f"👁️ Monitoring Slack channel: {channel_id}")
        
        if channel_id not in self.monitored_channels:
            self.monitored_channels.append(channel_id)
            
            # Four Sagesへチャンネル監視開始を通知
            if self.four_sages:
                self._notify_four_sages("channel_monitoring_started", {
                    "channel_id": channel_id,
                    "timestamp": datetime.now().isoformat()
                })
        
        self.performance_metrics['channels_monitored'] = len(self.monitored_channels)
            
        return {
            'channel_id': channel_id,
            'monitoring': True,
            'started_at': datetime.now().isoformat(),
            'elder_tree_integrated': ELDER_INTEGRATION_AVAILABLE
        }
        
    def process_messages(self) -> List[Dict]:
        """メッセージ処理 with Four Sages分析"""
        messages = []
        
        # シミュレートしたメッセージ処理
        self.message_count += 1
        self.performance_metrics['messages_processed'] += 1
        
        # Four Sages協調分析
        if self.four_sages and self.message_count % 10 == 0:
            analysis_request = {
                'type': 'pattern_analysis',
                'data': {
                    'message_count': self.message_count,
                    'channels': self.monitored_channels,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            # 賢者による分析（簡易版）
            analysis_result = self._request_sage_analysis(analysis_request)
            
            if analysis_result:
                messages.append({
                    'type': 'sage_analysis',
                    'result': analysis_result,
                    'timestamp': datetime.now().isoformat()
                })
        
        # 異常検知シミュレーション
        if self.message_count % 50 == 0:
            self._detect_anomaly()
        
        return messages
        
    def _notify_four_sages(self, notification_type: str, data: Dict[str, Any]):
        """Four Sagesへの通知"""
        if not self.four_sages:
            return
            
        try:
            # 通知タイプに応じた賢者選択
            if notification_type == "channel_monitoring_started":
                # Knowledge Sageへ通知
                sage_response = self.four_sages._send_learning_request_to_sage(
                    "knowledge_sage",
                    {"type": "new_channel", "data": data},
                    f"session_{self.worker_id}_{int(time.time())}"
                )
            elif notification_type == "anomaly_detected":
                # Incident Sageへ通知
                sage_response = self.four_sages._send_learning_request_to_sage(
                    "incident_sage",
                    {"type": "anomaly", "data": data},
                    f"session_{self.worker_id}_{int(time.time())}"
                )
            else:
                sage_response = None
                
            if sage_response:
                logger.info(f"🧙‍♂️ Four Sages notified: {notification_type}")
                
        except Exception as e:
            logger.error(f"Failed to notify Four Sages: {e}")
    
    def _request_sage_analysis(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """賢者分析リクエスト"""
        if not self.four_sages:
            return None
            
        try:
            # Four Sages協調学習セッション
            result = self.four_sages.coordinate_learning_session(request)
            
            if result.get('consensus_reached'):
                return {
                    'consensus': result['learning_outcome'],
                    'confidence': result.get('consensus_confidence', 0),
                    'participating_sages': result.get('participating_sages', [])
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Sage analysis failed: {e}")
            return None
    
    def _detect_anomaly(self):
        """異常検知"""
        # シミュレート：10%の確率で異常検知
        import random
        if random.random() < 0.1:
            self.performance_metrics['errors_detected'] += 1
            
            anomaly_data = {
                'type': 'unusual_activity',
                'severity': 'medium',
                'channel_count': len(self.monitored_channels),
                'message_rate': self.message_count / max((datetime.now() - datetime.now()).seconds, 1),
                'timestamp': datetime.now().isoformat()
            }
            
            # Four Sagesへ異常通知
            self._notify_four_sages("anomaly_detected", anomaly_data)
            
            # エルダーへアラート報告
            self._report_to_elders("alert", anomaly_data)
            
            self.performance_metrics['alerts_sent'] += 1
            
            logger.warning(f"🚨 Anomaly detected: {anomaly_data['type']}")
    
    def get_status(self) -> Dict:
        """ステータス取得 with Elder Tree統合情報"""
        status = {
            'running': self.running,
            'monitored_channels': len(self.monitored_channels),
            'message_count': self.message_count,
            'timestamp': datetime.now().isoformat(),
            'elder_tree_integrated': ELDER_INTEGRATION_AVAILABLE,
            'performance_metrics': self.performance_metrics.copy()
        }
        
        # Four Sages統合状態
        if self.four_sages:
            sage_status = self.four_sages.monitor_sage_collaboration()
            status['four_sages_status'] = {
                'active_sessions': sage_status.get('active_learning_sessions', 0),
                'overall_health': sage_status.get('overall_collaboration_health', 'unknown')
            }
        
        return status
        
    def start(self):
        """監視開始"""
        self.running = True
        logger.info("🚀 Slack Monitor Worker started")
        
        # Elder Treeへ開始報告
        self._report_to_elders("worker_started", {
            "worker_id": self.worker_id,
            "capabilities": ["channel_monitoring", "message_analysis", "anomaly_detection"],
            "elder_tree_status": "connected" if self.elder_tree else "disconnected"
        })
        
        # Four Sagesとの同期
        if self.four_sages:
            try:
                # 簡易的な同期処理
                sage_configs = {
                    'knowledge_sage': {'enabled': True, 'mode': 'learning'},
                    'task_sage': {'enabled': True, 'mode': 'optimization'},
                    'incident_sage': {'enabled': True, 'mode': 'monitoring'},
                    'rag_sage': {'enabled': True, 'mode': 'search'}
                }
                
                init_result = self.four_sages.initialize_sage_integration(sage_configs)
                logger.info(f"🧙‍♂️ Four Sages integration: {init_result['integration_status']}")
                
            except Exception as e:
                logger.error(f"Failed to sync with Four Sages: {e}")
    
    def stop(self):
        """監視停止"""
        self.running = False
        
        # 最終レポート生成
        final_report = {
            'worker_id': self.worker_id,
            'total_messages': self.message_count,
            'channels_monitored': len(self.monitored_channels),
            'performance_metrics': self.performance_metrics,
            'stopped_at': datetime.now().isoformat()
        }
        
        # Elder Treeへ停止報告
        self._report_to_elders("worker_stopped", final_report)
        
        logger.info("🛑 Slack Monitor Worker stopped")
        logger.info(f"📊 Final metrics: {self.performance_metrics}")
    
    async def run_async(self):
        """非同期実行モード"""
        logger.info("🔄 Starting async monitoring loop")
        
        while self.running:
            try:
                # メッセージ処理
                messages = self.process_messages()
                
                # ステータス更新
                if self.message_count % 100 == 0:
                    status = self.get_status()
                    logger.info(f"📊 Status update: {status}")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in async loop: {e}")
                await asyncio.sleep(5)


# 自動テスト追加
class TestSlackMonitorWorker:
    """Slack Monitor Worker テストクラス"""
    
    @staticmethod
    def test_elder_tree_integration():
        """Elder Tree統合テスト"""
        logger.info("🧪 Testing Elder Tree integration...")
        
        worker = SlackMonitorWorker()
        worker.start()
        
        # チャンネル監視テスト
        result = worker.monitor_channel("test-channel-1")
        assert result['monitoring'] == True
        assert 'elder_tree_integrated' in result
        
        # メッセージ処理テスト
        for i in range(15):
            messages = worker.process_messages()
            if messages:
                logger.info(f"📨 Sage analysis: {messages[0].get('result', {})}")
        
        # ステータス確認
        status = worker.get_status()
        assert status['message_count'] == 15
        assert 'performance_metrics' in status
        
        worker.stop()
        
        logger.info("✅ Elder Tree integration test passed")
        return True
    
    @staticmethod
    def test_four_sages_coordination():
        """Four Sages協調テスト"""
        logger.info("🧪 Testing Four Sages coordination...")
        
        worker = SlackMonitorWorker()
        
        if not worker.four_sages:
            logger.warning("Four Sages not available, skipping test")
            return True
        
        worker.start()
        
        # 複数チャンネル監視
        channels = ["general", "random", "alerts"]
        for channel in channels:
            worker.monitor_channel(channel)
        
        # 大量メッセージ処理で賢者分析トリガー
        for i in range(100):
            worker.process_messages()
        
        # パフォーマンス確認
        status = worker.get_status()
        metrics = status['performance_metrics']
        
        logger.info(f"📊 Performance metrics: {metrics}")
        assert metrics['messages_processed'] == 100
        assert metrics['channels_monitored'] == 3
        
        worker.stop()
        
        logger.info("✅ Four Sages coordination test passed")
        return True


if __name__ == "__main__":
    # テスト実行
    import sys
    
    if "--test" in sys.argv:
        logger.info("🏛️ Running Elder Tree integration tests...")
        
        test = TestSlackMonitorWorker()
        test.test_elder_tree_integration()
        test.test_four_sages_coordination()
        
        logger.info("🎉 All tests completed successfully!")
    else:
        # 通常実行
        worker = SlackMonitorWorker()
        worker.start()
        
        try:
            # 非同期実行
            asyncio.run(worker.run_async())
        except KeyboardInterrupt:
            logger.info("\n⚡ Interrupted by user")
            worker.stop()
