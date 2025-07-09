#!/usr/bin/env python3
"""
Four Sages A2A Communication Demo
4賢者間A2A通信のデモンストレーション
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from libs.a2a_communication import (
    A2AClient, AgentInfo, AgentType, MessageType, MessagePriority,
    A2AMessage, create_a2a_client, A2AError
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FourSagesOrchestrator:
    """4賢者協調システム"""
    
    def __init__(self):
        self.sages = {}
        self.collaboration_history = []
    
    async def initialize_sages(self):
        """4賢者を初期化"""
        sage_ids = ['knowledge_sage', 'task_sage', 'rag_sage', 'incident_sage']
        
        for sage_id in sage_ids:
            try:
                client = await create_a2a_client(sage_id)
                self.sages[sage_id] = client
                await self._setup_sage_handlers(sage_id, client)
                logger.info(f"Initialized {sage_id}")
            except Exception as e:
                logger.error(f"Failed to initialize {sage_id}: {e}")
                raise
    
    async def _setup_sage_handlers(self, sage_id: str, client: A2AClient):
        """各賢者のメッセージハンドラーを設定"""
        
        if sage_id == 'knowledge_sage':
            await self._setup_knowledge_sage_handlers(client)
        elif sage_id == 'task_sage':
            await self._setup_task_sage_handlers(client)
        elif sage_id == 'rag_sage':
            await self._setup_rag_sage_handlers(client)
        elif sage_id == 'incident_sage':
            await self._setup_incident_sage_handlers(client)
    
    async def _setup_knowledge_sage_handlers(self, client: A2AClient):
        """ナレッジ賢者のハンドラー設定"""
        
        async def handle_knowledge_query(message: A2AMessage):
            query = message.payload.params.get('query', '')
            logger.info(f"Knowledge Sage processing query: {query}")
            
            # 模擬的な知識検索
            knowledge_results = {
                'query': query,
                'results': [
                    {
                        'title': 'A2A Communication Protocol',
                        'content': 'A2A protocol enables secure agent-to-agent communication',
                        'relevance': 0.95,
                        'source': 'docs/a2a_protocol_specification_v1.md'
                    },
                    {
                        'title': 'Message Types',
                        'content': 'Support for query, command, event, and response messages',
                        'relevance': 0.87,
                        'source': 'libs/a2a_communication.py'
                    }
                ],
                'timestamp': datetime.utcnow().isoformat(),
                'processed_by': 'knowledge_sage'
            }
            
            self.collaboration_history.append({
                'sage': 'knowledge_sage',
                'action': 'knowledge_query',
                'query': query,
                'results_count': len(knowledge_results['results']),
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return knowledge_results
        
        async def handle_pattern_sharing(message: A2AMessage):
            pattern_data = message.payload.params.get('pattern', {})
            logger.info(f"Knowledge Sage received pattern: {pattern_data.get('name', 'Unknown')}")
            
            # パターンの保存・分析
            analysis_result = {
                'pattern_id': pattern_data.get('id'),
                'analysis': {
                    'complexity': 'medium',
                    'applicability': 'high',
                    'related_patterns': ['observer', 'strategy'],
                    'recommendations': [
                        'Consider combining with async patterns',
                        'Add error handling wrappers'
                    ]
                },
                'stored': True,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return analysis_result
        
        client.register_handler(MessageType.KNOWLEDGE_QUERY, handle_knowledge_query)
        client.register_handler(MessageType.PATTERN_SHARING, handle_pattern_sharing)
    
    async def _setup_task_sage_handlers(self, client: A2AClient):
        """タスク賢者のハンドラー設定"""
        
        async def handle_task_assignment(message: A2AMessage):
            task_data = message.payload.params.get('task', {})
            logger.info(f"Task Sage assigning task: {task_data.get('title', 'Unknown')}")
            
            # タスクの分析と割り当て
            assignment_result = {
                'task_id': task_data.get('id'),
                'assigned_to': 'elder_servant_001',
                'priority': task_data.get('priority', 'normal'),
                'estimated_duration': '2h',
                'dependencies': task_data.get('dependencies', []),
                'scheduled_start': datetime.utcnow().isoformat(),
                'status': 'assigned'
            }
            
            self.collaboration_history.append({
                'sage': 'task_sage',
                'action': 'task_assignment',
                'task_id': task_data.get('id'),
                'assigned_to': assignment_result['assigned_to'],
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return assignment_result
        
        async def handle_task_status(message: A2AMessage):
            task_id = message.payload.params.get('task_id')
            logger.info(f"Task Sage checking status for task: {task_id}")
            
            # タスクステータスの照会
            status_result = {
                'task_id': task_id,
                'current_status': 'in_progress',
                'progress': 65,
                'remaining_time': '45m',
                'last_update': datetime.utcnow().isoformat(),
                'issues': []
            }
            
            return status_result
        
        client.register_handler(MessageType.TASK_ASSIGNMENT, handle_task_assignment)
        client.register_handler(MessageType.TASK_STATUS, handle_task_status)
    
    async def _setup_rag_sage_handlers(self, client: A2AClient):
        """RAG賢者のハンドラー設定"""
        
        async def handle_knowledge_query(message: A2AMessage):
            query = message.payload.params.get('query', '')
            context = message.payload.params.get('context', {})
            logger.info(f"RAG Sage enhancing query: {query}")
            
            # コンテキスト強化とセマンティック検索
            enhanced_result = {
                'original_query': query,
                'enhanced_query': f"semantic:{query} context:{context.get('domain', 'general')}",
                'retrieved_documents': [
                    {
                        'id': 'doc_001',
                        'title': 'A2A Architecture Guide',
                        'snippet': 'Comprehensive guide to A2A communication patterns',
                        'similarity_score': 0.92,
                        'embedding_vector': [0.1, 0.2, 0.3]  # Simplified
                    },
                    {
                        'id': 'doc_002', 
                        'title': 'Message Queue Best Practices',
                        'snippet': 'Best practices for reliable message queuing',
                        'similarity_score': 0.88,
                        'embedding_vector': [0.2, 0.3, 0.4]
                    }
                ],
                'context_enrichment': {
                    'domain_keywords': ['communication', 'protocol', 'messaging'],
                    'related_concepts': ['async', 'reliability', 'security'],
                    'confidence': 0.89
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return enhanced_result
        
        client.register_handler(MessageType.KNOWLEDGE_QUERY, handle_knowledge_query)
    
    async def _setup_incident_sage_handlers(self, client: A2AClient):
        """インシデント賢者のハンドラー設定"""
        
        async def handle_incident_alert(message: A2AMessage):
            incident_data = message.payload.params.get('incident', {})
            logger.info(f"Incident Sage processing alert: {incident_data.get('type', 'Unknown')}")
            
            # インシデント分析とリスク評価
            assessment_result = {
                'incident_id': incident_data.get('id'),
                'severity': incident_data.get('severity', 'medium'),
                'risk_assessment': {
                    'impact': 'medium',
                    'probability': 'low',
                    'affected_systems': ['a2a_gateway', 'message_queue'],
                    'mitigation_urgency': 'high'
                },
                'recommended_actions': [
                    'Increase monitoring frequency',
                    'Prepare rollback procedure',
                    'Alert on-call engineer'
                ],
                'auto_recovery_possible': True,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.collaboration_history.append({
                'sage': 'incident_sage',
                'action': 'incident_assessment',
                'incident_id': incident_data.get('id'),
                'severity': assessment_result['severity'],
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return assessment_result
        
        async def handle_health_check(message: A2AMessage):
            component = message.payload.params.get('component', 'unknown')
            logger.info(f"Incident Sage health check for: {component}")
            
            # コンポーネントヘルスチェック
            health_result = {
                'component': component,
                'status': 'healthy',
                'metrics': {
                    'response_time': '45ms',
                    'error_rate': '0.01%',
                    'throughput': '1500 msg/s',
                    'memory_usage': '67%'
                },
                'issues': [],
                'last_check': datetime.utcnow().isoformat()
            }
            
            return health_result
        
        client.register_handler(MessageType.INCIDENT_ALERT, handle_incident_alert)
        client.register_handler(MessageType.HEALTH_CHECK, handle_health_check)
    
    async def demonstrate_collaboration(self):
        """4賢者協調のデモンストレーション"""
        logger.info("Starting Four Sages A2A Collaboration Demo")
        
        try:
            # Scenario 1: Knowledge Query with RAG Enhancement
            logger.info("\\n=== Scenario 1: Knowledge Query with RAG Enhancement ===")
            
            # RAG Sageに知識検索を依頼
            rag_response = await self.sages['knowledge_sage'].send_message(
                target_agent='rag_sage',
                message_type=MessageType.KNOWLEDGE_QUERY,
                method='semantic_search',
                params={
                    'query': 'A2A communication best practices',
                    'context': {'domain': 'system_architecture', 'urgency': 'high'}
                },
                wait_for_response=True,
                timeout=10.0
            )
            
            logger.info(f"RAG enhanced search results: {len(rag_response.payload.data['retrieved_documents'])} documents")
            
            # Knowledge Sageで詳細分析
            knowledge_response = await self.sages['rag_sage'].send_message(
                target_agent='knowledge_sage',
                message_type=MessageType.KNOWLEDGE_QUERY,
                method='analyze_documents',
                params={
                    'query': rag_response.payload.data['enhanced_query'],
                    'documents': rag_response.payload.data['retrieved_documents']
                },
                wait_for_response=True,
                timeout=10.0
            )
            
            logger.info(f"Knowledge analysis completed: {len(knowledge_response.payload.data['results'])} insights")
            
            # Scenario 2: Task Assignment with Incident Monitoring
            logger.info("\\n=== Scenario 2: Task Assignment with Incident Monitoring ===")
            
            # Task Sageにタスク割り当て
            task_response = await self.sages['incident_sage'].send_message(
                target_agent='task_sage',
                message_type=MessageType.TASK_ASSIGNMENT,
                method='assign_critical_task',
                params={
                    'task': {
                        'id': 'task_001',
                        'title': 'A2A Protocol Performance Optimization',
                        'priority': 'high',
                        'dependencies': ['system_analysis', 'load_testing']
                    }
                },
                wait_for_response=True,
                timeout=10.0
            )
            
            logger.info(f"Task assigned to: {task_response.payload.data['assigned_to']}")
            
            # Incident Sageでヘルスチェック
            health_response = await self.sages['task_sage'].send_message(
                target_agent='incident_sage',
                message_type=MessageType.HEALTH_CHECK,
                method='check_system_health',
                params={'component': 'a2a_communication'},
                wait_for_response=True,
                timeout=10.0
            )
            
            logger.info(f"System health: {health_response.payload.data['status']}")
            
            # Scenario 3: Pattern Sharing and Learning
            logger.info("\\n=== Scenario 3: Pattern Sharing and Learning ===")
            
            # 新しいパターンの共有
            pattern_response = await self.sages['task_sage'].send_message(
                target_agent='knowledge_sage',
                message_type=MessageType.PATTERN_SHARING,
                method='share_communication_pattern',
                params={
                    'pattern': {
                        'id': 'async_circuit_breaker',
                        'name': 'Asynchronous Circuit Breaker',
                        'description': 'Prevents cascade failures in A2A communication',
                        'implementation': 'libs/a2a_communication.py',
                        'use_cases': ['high_load', 'service_degradation']
                    }
                },
                wait_for_response=True,
                timeout=10.0
            )
            
            logger.info(f"Pattern analysis: {pattern_response.payload.data['analysis']['complexity']}")
            
            # Scenario 4: Incident Simulation and Response
            logger.info("\\n=== Scenario 4: Incident Simulation and Response ===")
            
            # 模擬インシデント発生
            incident_response = await self.sages['knowledge_sage'].send_message(
                target_agent='incident_sage',
                message_type=MessageType.INCIDENT_ALERT,
                method='report_incident',
                params={
                    'incident': {
                        'id': 'inc_001',
                        'type': 'communication_failure',
                        'severity': 'high',
                        'description': 'A2A message delivery timeout',
                        'affected_agents': ['task_sage', 'rag_sage']
                    }
                },
                wait_for_response=True,
                timeout=10.0
            )
            
            logger.info(f"Incident assessment: {incident_response.payload.data['risk_assessment']['impact']}")
            
            # タスク再割り当て
            recovery_task = await self.sages['incident_sage'].send_message(
                target_agent='task_sage',
                message_type=MessageType.TASK_ASSIGNMENT,
                method='assign_recovery_task',
                params={
                    'task': {
                        'id': 'recovery_001',
                        'title': 'A2A Communication Recovery',
                        'priority': 'critical',
                        'incident_id': 'inc_001'
                    }
                },
                wait_for_response=True,
                timeout=10.0
            )
            
            logger.info(f"Recovery task assigned: {recovery_task.payload.data['task_id']}")
            
        except A2AError as e:
            logger.error(f"A2A Communication error: {e}")
        except Exception as e:
            logger.error(f"Demo error: {e}")
    
    async def display_metrics(self):
        """各賢者のメトリクス表示"""
        logger.info("\\n=== Four Sages Metrics ===")
        
        for sage_id, client in self.sages.items():
            metrics = await client.get_metrics()
            logger.info(f"{sage_id}: Sent={metrics['messages_sent']}, "
                       f"Received={metrics['messages_received']}, "
                       f"Errors={metrics['errors_count']}")
        
        logger.info(f"\\nCollaboration events: {len(self.collaboration_history)}")
        for event in self.collaboration_history[-5:]:  # 最新5件
            logger.info(f"  {event['timestamp']}: {event['sage']} - {event['action']}")
    
    async def shutdown(self):
        """4賢者システムのシャットダウン"""
        logger.info("Shutting down Four Sages...")
        
        for sage_id, client in self.sages.items():
            try:
                await client.disconnect()
                logger.info(f"Disconnected {sage_id}")
            except Exception as e:
                logger.error(f"Error disconnecting {sage_id}: {e}")

async def main():
    """メイン実行関数"""
    orchestrator = FourSagesOrchestrator()
    
    try:
        # 4賢者初期化
        await orchestrator.initialize_sages()
        
        # 協調デモの実行
        await orchestrator.demonstrate_collaboration()
        
        # メトリクス表示
        await orchestrator.display_metrics()
        
        # 少し待機（ログ出力の確認）
        await asyncio.sleep(2)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise
    finally:
        # クリーンアップ
        await orchestrator.shutdown()

if __name__ == "__main__":
    print("Four Sages A2A Communication Demo")
    print("=" * 50)
    print("This demo shows how the four sages collaborate using A2A communication:")
    print("1. Knowledge Sage - Pattern analysis and knowledge management")
    print("2. Task Sage - Task assignment and resource allocation") 
    print("3. RAG Sage - Document retrieval and context enhancement")
    print("4. Incident Sage - Risk assessment and recovery planning")
    print("=" * 50)
    
    try:
        asyncio.run(main())
        print("\\nDemo completed successfully!")
    except KeyboardInterrupt:
        print("\\nDemo interrupted by user")
    except Exception as e:
        print(f"\\nDemo failed with error: {e}")
        sys.exit(1)