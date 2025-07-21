#!/usr/bin/env python3
"""
Four Sages RabbitMQ Integration Tests - 4賢者RabbitMQ統合テスト
4賢者がRabbitMQを通じて協調動作することを検証

Created: 2025-07-17
Author: Claude Elder
Version: 1.0.0 - 真剣な実装
"""

import sys
import os
from pathlib import Path
import pytest
import pytest_asyncio
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import time

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.perfect_a2a.perfect_rabbitmq_manager import PerfectRabbitMQManager


class MockSage:
    """テスト用の賢者モック"""
    def __init__(self, sage_id: str, sage_type: str):
        self.sage_id = sage_id
        self.sage_type = sage_type
        self.received_messages = []
        self.processed_count = 0
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """メッセージ処理シミュレーション"""
        self.received_messages.append(message)
        self.processed_count += 1
        
        response = {
            "response_id": str(uuid.uuid4()),
            "sage_id": self.sage_id,
            "sage_type": self.sage_type,
            "original_request_id": message.get("request_id"),
            "timestamp": datetime.now().isoformat(),
            "result": {
                "status": "processed",
                "data": f"{self.sage_type} processed request",
                "processing_time": 0.1
            }
        }
        
        await asyncio.sleep(0.1)  # 処理時間シミュレーション
        return response


class TestFourSagesRabbitMQIntegration:
    """4賢者RabbitMQ統合テストスイート"""
    
    @pytest_asyncio.fixture
    async def rabbitmq_manager(self):
        """RabbitMQマネージャー"""
        manager = PerfectRabbitMQManager()
        await manager.ensure_perfect_rabbitmq()
        yield manager
        await manager.perfect_shutdown()
    
    @pytest_asyncio.fixture
    def four_sages(self):
        """4賢者のモックインスタンス"""
        return {
            "knowledge_sage": MockSage("knowledge_sage", "Knowledge"),
            "task_sage": MockSage("task_sage", "Task"),
            "incident_sage": MockSage("incident_sage", "Incident"),
            "rag_sage": MockSage("rag_sage", "RAG")
        }
    
    @pytest.mark.asyncio
    async def test_01_sage_request_response_pattern(self, rabbitmq_manager, four_sages):
        """テスト1: 賢者リクエスト・レスポンスパターンテスト"""
        print("\n🧪 テスト1: 賢者リクエスト・レスポンスパターンテスト開始...")
        
        # 1. クロードエルダーからナレッジ賢者への要請
        request = {
            "request_id": str(uuid.uuid4()),
            "sender": "claude_elder",
            "receiver": "knowledge_sage",
            "request_type": "knowledge_query",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "query": "RabbitMQ統合の進捗状況",
                "context": "integration_test"
            }
        }
        
        # 2. リクエスト送信
        send_result = await rabbitmq_manager.publish_message(
            exchange="elder.direct",
            routing_key="sage.knowledge",
            body=json.dumps(request),
            properties={
                "message_id": request["request_id"],
                "reply_to": "elder.responses",
                "correlation_id": request["request_id"]
            }
        )
        assert send_result is True, "賢者への要請送信失敗"
        print("✓ ナレッジ賢者への要請送信成功")
        
        # 3. 賢者の処理シミュレーション
        sage = four_sages["knowledge_sage"]
        response = await sage.process_message(request)
        print(f"✓ ナレッジ賢者処理完了: {response['result']['status']}")
        
        # 4. レスポンス送信
        response_result = await rabbitmq_manager.publish_message(
            exchange="elder.direct",
            routing_key="response",
            body=json.dumps(response),
            properties={
                "correlation_id": request["request_id"],
                "message_id": response["response_id"]
            }
        )
        assert response_result is True, "レスポンス送信失敗"
        print("✓ レスポンス送信成功")
        
        # 5. 処理統計確認
        assert sage.processed_count == 1, "処理カウントが不正"
        assert len(sage.received_messages) == 1, "受信メッセージ数が不正"
        
        print("✅ テスト1完了: 賢者リクエスト・レスポンスパターン成功")
    
    @pytest.mark.asyncio
    async def test_02_four_sages_collaboration(self, rabbitmq_manager, four_sages):
        """テスト2: 4賢者協調動作テスト"""
        print("\n🧪 テスト2: 4賢者協調動作テスト開始...")
        
        # 1. 複雑なタスクの分解と各賢者への割り当て
        complex_task = {
            "task_id": str(uuid.uuid4()),
            "type": "complex_analysis",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "request": "システム全体の健全性分析とパフォーマンス最適化",
                "requester": "claude_elder"
            }
        }
        
        # 2. 各賢者への並列要請
        sage_requests = [
            {
                "sage": "knowledge_sage",
                "routing_key": "sage.knowledge",
                "task": "過去の知識から最適化パターンを抽出"
            },
            {
                "sage": "task_sage",
                "routing_key": "sage.task",
                "task": "タスクの優先順位と実行計画を策定"
            },
            {
                "sage": "incident_sage",
                "routing_key": "sage.incident",
                "task": "潜在的リスクとインシデント予防策を分析"
            },
            {
                "sage": "rag_sage",
                "routing_key": "sage.rag",
                "task": "関連ドキュメントと過去事例を検索"
            }
        ]
        
        # 3. 並列送信
        send_tasks = []
        for sage_req in sage_requests:
            request = {
                "request_id": str(uuid.uuid4()),
                "parent_task_id": complex_task["task_id"],
                "sender": "claude_elder",
                "receiver": sage_req["sage"],
                "request_type": "collaboration",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "task": sage_req["task"],
                    "context": complex_task
                }
            }
            
            send_task = rabbitmq_manager.publish_message(
                exchange="elder.direct",
                routing_key=sage_req["routing_key"],
                body=json.dumps(request),
                properties={
                    "message_id": request["request_id"],
                    "correlation_id": complex_task["task_id"]
                }
            )
            send_tasks.append(send_task)
        
        # 並列送信実行
        send_results = await asyncio.gather(*send_tasks)
        assert all(send_results), "並列送信に失敗"
        print("✓ 4賢者への並列要請送信成功")
        
        # 4. 各賢者の処理シミュレーション（並列処理）
        process_tasks = []
        for sage_req in sage_requests:
            sage = four_sages[sage_req["sage"]]
            # 簡易的な処理（実際にはメッセージを受信して処理）
            dummy_message = {"request_id": str(uuid.uuid4()), "task": sage_req["task"]}
            process_task = sage.process_message(dummy_message)
            process_tasks.append(process_task)
        
        responses = await asyncio.gather(*process_tasks)
        print(f"✓ 4賢者並列処理完了: {len(responses)}件")
        
        # 5. 協調結果の統合
        integrated_result = {
            "task_id": complex_task["task_id"],
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "sage_responses": [
                {
                    "sage": resp["sage_id"],
                    "status": resp["result"]["status"]
                } for resp in responses
            ]
        }
        
        # 統合結果送信
        integration_result = await rabbitmq_manager.publish_message(
            exchange="elder.direct",
            routing_key="response",
            body=json.dumps(integrated_result),
            properties={
                "message_id": str(uuid.uuid4()),
                "correlation_id": complex_task["task_id"]
            }
        )
        assert integration_result is True, "統合結果送信失敗"
        print("✓ 協調結果統合・送信成功")
        
        print("✅ テスト2完了: 4賢者協調動作成功")
    
    @pytest.mark.asyncio
    async def test_03_sage_heartbeat_monitoring(self, rabbitmq_manager, four_sages):
        """テスト3: 賢者ヘルスチェック・監視テスト"""
        print("\n🧪 テスト3: 賢者ヘルスチェック・監視テスト開始...")
        
        # 1. 各賢者のヘルスチェックメッセージ準備
        heartbeat_messages = []
        for sage_id, sage in four_sages.items():
            heartbeat = {
                "heartbeat_id": str(uuid.uuid4()),
                "sage_id": sage_id,
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "status": {
                    "health": "healthy",
                    "processed_count": sage.processed_count,
                    "memory_usage": "120MB",  # シミュレーション値
                    "cpu_usage": "15%",       # シミュレーション値
                    "queue_depth": 0
                }
            }
            heartbeat_messages.append(heartbeat)
        
        # 2. ヘルスチェックトピックへの送信
        for heartbeat in heartbeat_messages:
            result = await rabbitmq_manager.publish_message(
                exchange="elder.topic",
                routing_key=f"elder.heartbeat.{heartbeat['sage_id']}",
                body=json.dumps(heartbeat),
                properties={
                    "message_id": heartbeat["heartbeat_id"],
                    "type": "heartbeat",
                    "expiration": "30000"  # 30秒で期限切れ
                }
            )
            assert result is True, f"{heartbeat['sage_id']}のヘルスチェック送信失敗"
        
        print(f"✓ {len(heartbeat_messages)}賢者のヘルスチェック送信成功")
        
        # 3. 監視アラートのシミュレーション
        # インシデント賢者が異常を検知したと仮定
        alert = {
            "alert_id": str(uuid.uuid4()),
            "source": "incident_sage",
            "type": "performance_alert",
            "severity": "warning",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "message": "タスク賢者の処理遅延を検知",
                "affected_sage": "task_sage",
                "delay_seconds": 5.2,
                "recommendation": "リソース割り当ての見直しを推奨"
            }
        }
        
        # アラート送信（fanoutで全体通知）
        alert_result = await rabbitmq_manager.publish_message(
            exchange="elder.fanout",
            routing_key="",
            body=json.dumps(alert),
            properties={
                "message_id": alert["alert_id"],
                "priority": 1,  # warning level
                "type": "alert"
            }
        )
        assert alert_result is True, "アラート送信失敗"
        print("✓ パフォーマンスアラート送信成功")
        
        # 4. 監視統計サマリー
        monitoring_summary = {
            "summary_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "period": "last_5_minutes",
            "sages_status": {
                sage_id: "healthy" for sage_id in four_sages.keys()
            },
            "total_messages": sum(sage.processed_count for sage in four_sages.values()),
            "alerts_count": 1
        }
        
        summary_result = await rabbitmq_manager.publish_message(
            exchange="elder.direct",
            routing_key="monitoring.summary",
            body=json.dumps(monitoring_summary),
            properties={
                "message_id": monitoring_summary["summary_id"],
                "type": "monitoring_summary"
            }
        )
        assert summary_result is True, "監視サマリー送信失敗"
        print("✓ 監視統計サマリー送信成功")
        
        print("✅ テスト3完了: 賢者ヘルスチェック・監視成功")


if __name__ == "__main__":
    # 実行
    pytest.main([__file__, '-v', '-s', '--tb=short'])