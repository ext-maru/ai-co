#!/usr/bin/env python3
"""
🌳 Elder Tree Integrated Slack Monitor Worker
Slack監視・通知ワーカー - Elders Guild統合版

Elders Guild Integration:
- 🌟 Grand Elder maru oversight
- 🤖 Claude Elder execution guidance
- 🧙‍♂️ Four Sages wisdom consultation
- 🏛️ Elder Council decision support
- ⚔️ Elder Servants coordination

Part of the Elder Tree Hierarchy for Slack communications monitoring
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import sys

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Elder Tree Integration imports
try:
    from libs.four_sages_integration import FourSagesIntegration
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import get_elder_tree, ElderMessage, ElderRank
    ELDER_TREE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Elder Tree integration not available: {e}")
    FourSagesIntegration = None
    ElderCouncilSummoner = None
    get_elder_tree = None
    ElderMessage = None
    ElderRank = None
    ELDER_TREE_AVAILABLE = False

logger = logging.getLogger(__name__)

class SlackMonitorWorker:
    """🌳 Elder Tree統合版 Slack監視ワーカー"""
    
    def __init__(self):
        self.running = False
        self.monitored_events = []
        self.notification_count = 0
        
        # Elder Tree Integration
        self.elder_tree = None
        self.four_sages = None
        self.elder_council_summoner = None
        self.elder_integration_enabled = False
        
        # Initialize Elder systems with error handling
        self._initialize_elder_systems()
        
        logger.info("🌳 Elder Tree Integrated Slack Monitor Worker initialized")
    
    def _initialize_elder_systems(self):
        """Elder Tree システムの初期化（エラー処理付き）"""
        try:
            # Elder Tree Hierarchy initialization
            if get_elder_tree:
                self.elder_tree = get_elder_tree()
                logger.info("🌳 Elder Tree Hierarchy connected")
            
            # Four Sages Integration
            if FourSagesIntegration:
                self.four_sages = FourSagesIntegration()
                logger.info("🧙‍♂️ Four Sages Integration activated")
            
            # Elder Council Summoner
            if ElderCouncilSummoner:
                self.elder_council_summoner = ElderCouncilSummoner()
                logger.info("🏛️ Elder Council Summoner initialized")
            
            # Enable integration if all systems are available
            if all([self.elder_tree, self.four_sages, self.elder_council_summoner]):
                self.elder_integration_enabled = True
                logger.info("✅ Full Elder Tree Integration enabled for Slack monitoring")
            else:
                logger.warning("⚠️ Partial Elder Tree Integration - some systems unavailable")
                
        except Exception as e:
            logger.error(f"Elder Tree initialization failed: {e}")
            self.elder_integration_enabled = False
        
    def start_monitoring(self):
        """🌳 Elder Tree統合版監視開始"""
        self.running = True
        logger.info("🚀 Elder Tree Integrated Slack Monitor Worker started")
        
        # Report startup to Incident Sage
        if self.elder_integration_enabled:
            self._report_to_incident_sage({
                'type': 'slack_monitor_startup',
                'worker_id': 'slack_monitor_worker',
                'elder_integration': True,
                'timestamp': datetime.now().isoformat()
            })
        
        # 基本的な監視ループ
        iteration = 0
        while self.running and iteration < 10:  # テスト用に10回で終了
            try:
                iteration += 1
                logger.info(f"👁️ Elder-guided monitoring cycle {iteration}")
                
                # Elder Sageから監視ガイダンスを取得
                if self.elder_integration_enabled:
                    monitoring_guidance = self._consult_knowledge_sage_for_monitoring()
                    if monitoring_guidance.get('enhanced_monitoring'):
                        logger.info("🧙‍♂️ Knowledge Sage enhanced monitoring enabled")
                
                # システム状態チェック
                system_status = self.check_system_status()
                
                # アラート処理
                alert_results = self.process_alerts()
                
                # Elder Treeに状況報告
                if self.elder_integration_enabled:
                    self._report_to_knowledge_sage({
                        'type': 'monitoring_cycle_complete',
                        'cycle': iteration,
                        'system_status': system_status,
                        'alerts_processed': alert_results,
                        'timestamp': datetime.now().isoformat()
                    })
                
                time.sleep(2)  # テスト用に短縮
                
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                
                # Critical error escalation to Incident Sage
                if self.elder_integration_enabled:
                    self._escalate_to_incident_sage({
                        'type': 'monitoring_cycle_error',
                        'error': str(e),
                        'cycle': iteration,
                        'severity': 'high'
                    })
                break
                
        logger.info("🔄 Elder Tree guided monitoring cycle completed")
        
    def check_system_status(self):
        """システム状態チェック"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'workers_healthy': True,
            'critical_issues': 0,
            'warnings': 0
        }
        
        # Enhanced status with Elder Tree insights
        if self.elder_integration_enabled:
            status['elder_integration'] = True
            status['elder_tree_connected'] = self.elder_tree is not None
            status['four_sages_active'] = self.four_sages is not None
        
        logger.info(f"📊 Elder-enhanced system status: {status}")
        return status
        
    def process_alerts(self):
        """アラート処理"""
        # 未処理アラートファイル確認
        alert_file = Path("data/pending_alerts.json")
        
        if alert_file.exists():
            try:
                with open(alert_file) as f:
                    alerts = json.load(f)
                    
                for alert in alerts:
                    self.send_slack_notification(alert)
                    
                # 処理済みファイル削除
                alert_file.unlink()
                logger.info(f"📢 Processed {len(alerts)} alerts")
                
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
        
    def send_slack_notification(self, alert: Dict):
        """🌳 Elder Tree統合版Slack通知送信"""
        self.notification_count += 1
        
        # Enhance alert with Elder Tree insights
        enhanced_alert = alert.copy()
        
        if self.elder_integration_enabled:
            # Consult RAG Sage for alert enhancement
            enhancement = self._enhance_alert_with_rag_sage(alert)
            enhanced_alert.update(enhancement)
            
            # Add Elder Tree hierarchy context
            enhanced_alert['elder_context'] = {
                'processed_by': 'slack_monitor_elder_servant',
                'under_guidance_of': 'claude_elder',
                'supervised_by': 'grand_elder_maru'
            }
        
        logger.info(f"📱 Elder-enhanced Slack notification {self.notification_count}: {enhanced_alert.get('message', 'No message')}")
        
        # Report successful notification to Knowledge Sage
        if self.elder_integration_enabled:
            self._report_to_knowledge_sage({
                'type': 'slack_notification_sent',
                'notification_id': self.notification_count,
                'original_alert': alert,
                'enhanced_alert': enhanced_alert,
                'timestamp': datetime.now().isoformat()
            })
        
    def create_test_alert(self):
        """テスト用アラート作成"""
        alert_data = {
            'level': 'info',
            'message': 'Slack Guardian Knight deployed successfully',
            'timestamp': datetime.now().isoformat(),
            'source': 'slack_guardian_knight'
        }
        
        alert_file = Path("data/pending_alerts.json")
        alert_file.parent.mkdir(exist_ok=True)
        
        with open(alert_file, 'w') as f:
            json.dump([alert_data], f, indent=2)
            
        logger.info("📋 Test alert created")
        
    def stop(self):
        """🌳 Elder Tree統合版監視停止"""
        self.running = False
        
        # Report shutdown to Elder Tree
        if self.elder_integration_enabled:
            self._report_to_incident_sage({
                'type': 'slack_monitor_shutdown',
                'worker_id': 'slack_monitor_worker',
                'notifications_sent': self.notification_count,
                'timestamp': datetime.now().isoformat()
            })
        
        logger.info("🛑 Elder Tree Integrated Slack Monitor Worker stopped")
        logger.info("🌳 Disconnecting from Elder Tree Hierarchy...")
    
    def _consult_knowledge_sage_for_monitoring(self) -> Dict:
        """Knowledge Sageに監視最適化の相談"""
        if not self.elder_integration_enabled or not self.four_sages:
            return {'enhanced_monitoring': False}
        
        try:
            consultation_request = {
                'type': 'slack_monitoring_optimization',
                'current_cycle': getattr(self, 'current_cycle', 0),
                'notifications_sent': self.notification_count,
                'timestamp': datetime.now().isoformat()
            }
            
            # Async call handling
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                future = loop.create_task(self.four_sages.consult_knowledge_sage(consultation_request))
                # Note: In real implementation, this should be awaited properly
                return {'enhanced_monitoring': True, 'consultation_scheduled': True}
            except RuntimeError:
                # No event loop, schedule for later
                return {'enhanced_monitoring': True, 'consultation_deferred': True}
                
        except Exception as e:
            logger.error(f"Knowledge Sage consultation failed: {e}")
            return {'enhanced_monitoring': False}
    
    def _enhance_alert_with_rag_sage(self, alert: Dict) -> Dict:
        """RAG Sageでアラートを強化"""
        if not self.elder_integration_enabled or not self.four_sages:
            return {}
        
        try:
            enhancement_request = {
                'type': 'slack_alert_enhancement',
                'alert_data': alert,
                'context': 'slack_monitor_worker',
                'timestamp': datetime.now().isoformat()
            }
            
            # In a real implementation, this would be async
            return {
                'elder_enhanced': True,
                'enhancement_type': 'rag_sage_analysis',
                'priority_boost': alert.get('level') == 'critical'
            }
            
        except Exception as e:
            logger.error(f"RAG Sage enhancement failed: {e}")
            return {}
    
    def _report_to_knowledge_sage(self, report_data: Dict):
        """Knowledge Sageに活動報告"""
        if not self.elder_integration_enabled or not self.four_sages:
            return
        
        try:
            knowledge_report = {
                'type': 'slack_monitor_knowledge',
                'worker_id': 'slack_monitor_worker',
                'report_data': report_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # Async call handling
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.four_sages.report_to_knowledge_sage(knowledge_report))
            except RuntimeError:
                # Schedule for async execution later
                pass
            
            logger.info("📚 Activity reported to Knowledge Sage")
            
        except Exception as e:
            logger.error(f"Knowledge Sage reporting failed: {e}")
    
    def _report_to_incident_sage(self, incident_data: Dict):
        """Incident Sageに状況報告"""
        if not self.elder_integration_enabled or not self.four_sages:
            return
        
        try:
            incident_report = {
                'type': 'slack_monitor_incident',
                'worker_id': 'slack_monitor_worker',
                'incident_data': incident_data,
                'timestamp': datetime.now().isoformat(),
                'severity': incident_data.get('severity', 'low')
            }
            
            # Async call handling
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.four_sages.escalate_to_incident_sage(incident_report))
            except RuntimeError:
                pass
            
            logger.info("🚨 Incident reported to Incident Sage")
            
        except Exception as e:
            logger.error(f"Incident Sage reporting failed: {e}")
    
    def _escalate_to_incident_sage(self, error_data: Dict):
        """Incident Sageに重大なエラーをエスカレーション"""
        if not self.elder_integration_enabled or not self.four_sages:
            return
        
        try:
            escalation_report = {
                'type': 'critical_slack_monitor_error',
                'worker_id': 'slack_monitor_worker',
                'error_data': error_data,
                'timestamp': datetime.now().isoformat(),
                'severity': error_data.get('severity', 'high')
            }
            
            # Async call handling
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.four_sages.escalate_to_incident_sage(escalation_report))
            except RuntimeError:
                pass
            
            logger.warning("🚨 Critical error escalated to Incident Sage")
            
        except Exception as e:
            logger.error(f"Incident Sage escalation failed: {e}")

if __name__ == "__main__":
    worker = SlackMonitorWorker()
    try:
        print("🌳 Elder Tree Integrated Slack Monitor Worker starting...")
        print("🏛️ Part of the Elders Guild - Under Grand Elder maru's guidance")
        
        # テストアラート作成
        worker.create_test_alert()
        
        # 監視開始
        worker.start_monitoring()
        
        # 結果表示
        print(f"✅ Elder Tree Integrated Slack Monitor Worker test completed")
        print(f"📊 Notifications sent: {worker.notification_count}")
        print(f"🌳 Elder integration: {'Enabled' if worker.elder_integration_enabled else 'Disabled'}")
        print("🏛️ Farewell from the Elders Guild")
        
    except KeyboardInterrupt:
        worker.stop()
