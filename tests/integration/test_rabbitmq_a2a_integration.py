#!/usr/bin/env python3
"""
RabbitMQ A2A Communication Integration Tests - A2A通信統合テスト
エルダーツリー階層間のA2A通信をRabbitMQ経由で検証

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

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.perfect_a2a.perfect_rabbitmq_manager import PerfectRabbitMQManager


class TestA2ACommunicationIntegration:
    """A2A通信統合テストスイート"""
    
    @pytest_asyncio.fixture
    async def rabbitmq_manager(self):
        """RabbitMQマネージャー"""
        manager = PerfectRabbitMQManager()
        await manager.ensure_perfect_rabbitmq()
        yield manager
        await manager.perfect_shutdown()
    
    @pytest_asyncio.fixture
    async def a2a_comm(self, rabbitmq_manager):
        """A2A通信インスタンス（RabbitMQマネージャーを直接使用）"""
        # RabbitMQマネージャーを直接A2A通信として使用
        yield rabbitmq_manager
    
    @pytest.mark.asyncio
    async def test_01_a2a_basic_communication(self, rabbitmq_manager, a2a_comm):
        """テスト1: 基本的なA2A通信テスト"""
        print("\n🧪 テスト1: A2A基本通信テスト開始...")
        
        # 1. テスト用の送信者と受信者を定義
        sender_id = "claude_elder"
        receiver_id = "knowledge_sage"
        
        # 2. テストメッセージ作成
        test_request = {
            "request_id": str(uuid.uuid4()),
            "sender": sender_id,
            "receiver": receiver_id,
            "request_type": "knowledge_query",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "query": "RabbitMQ統合状況を教えてください",
                "context": "integration_test"
            }
        }
        
        # 3. メッセージ送信
        # Elder.directエクスチェンジ使用
        send_result = await rabbitmq_manager.publish_message(
            exchange="elder.direct",
            routing_key=f"a2a.{receiver_id}",
            body=json.dumps(test_request),
            properties={
                "message_id": test_request["request_id"],
                "correlation_id": test_request["request_id"],
                "reply_to": f"a2a.{sender_id}"
            }
        )
        assert send_result is True, "A2Aメッセージ送信失敗"
        print(f"✓ A2Aメッセージ送信成功: {sender_id} → {receiver_id}")
        
        # 4. 送信メッセージの記録確認
        print(f"✓ Request ID: {test_request['request_id']}")
        print(f"✓ Routing Key: a2a.{receiver_id}")
        
        print("✅ テスト1完了: A2A基本通信成功")
    
    @pytest.mark.asyncio
    async def test_02_a2a_elder_tree_hierarchy(self, rabbitmq_manager):
        """テスト2: エルダーツリー階層通信テスト"""
        print("\n🧪 テスト2: エルダーツリー階層通信テスト開始...")
        
        # 1. 階層間通信パターンテスト
        communication_patterns = [
            # クロードエルダー → 4賢者
            {"from": "claude_elder", "to": "knowledge_sage", "type": "sage_request"},
            {"from": "claude_elder", "to": "task_sage", "type": "sage_request"},
            {"from": "claude_elder", "to": "incident_sage", "type": "sage_request"},
            {"from": "claude_elder", "to": "rag_sage", "type": "sage_request"},
            
            # 4賢者間通信
            {"from": "knowledge_sage", "to": "task_sage", "type": "sage_collaboration"},
            
            # エルダーサーバント通信
            {"from": "claude_elder", "to": "code_artisan", "type": "servant_command"},
        ]
        
        # 2. 各パターンでメッセージ送信
        for pattern in communication_patterns:
            request = {
                "request_id": str(uuid.uuid4()),
                "sender": pattern["from"],
                "receiver": pattern["to"],
                "request_type": pattern["type"],
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "test": "hierarchy_communication",
                    "pattern": f"{pattern['from']} -> {pattern['to']}"
                }
            }
            
            # 送信
            result = await rabbitmq_manager.publish_message(
                exchange="elder.topic",  # トピックエクスチェンジ使用
                routing_key=f"elder.{pattern['to']}.{pattern['type']}",
                body=json.dumps(request),
                properties={
                    "message_id": request["request_id"],
                    "type": pattern["type"]
                }
            )
            
            assert result is True, f"階層通信失敗: {pattern['from']} → {pattern['to']}"
            print(f"✓ 階層通信成功: {pattern['from']} → {pattern['to']}")
        
        print("✅ テスト2完了: エルダーツリー階層通信成功")
    
    @pytest.mark.asyncio
    async def test_03_a2a_broadcast_communication(self, rabbitmq_manager):
        """テスト3: ブロードキャスト通信テスト"""
        print("\n🧪 テスト3: ブロードキャスト通信テスト開始...")
        
        # 1. エルダー評議会からの全体通知
        council_announcement = {
            "announcement_id": str(uuid.uuid4()),
            "sender": "elder_council",
            "type": "council_announcement",
            "timestamp": datetime.now().isoformat(),
            "priority": "high",
            "data": {
                "title": "緊急エルダー評議会決定",
                "message": "RabbitMQ統合を正式承認します",
                "effective_date": datetime.now().isoformat()
            }
        }
        
        # 2. Fanoutエクスチェンジでブロードキャスト
        broadcast_result = await rabbitmq_manager.publish_message(
            exchange="elder.fanout",
            routing_key="",  # fanoutは routing_key 不要
            body=json.dumps(council_announcement),
            properties={
                "message_id": council_announcement["announcement_id"],
                "priority": 9,  # 高優先度
                "type": "broadcast"
            }
        )
        assert broadcast_result is True, "ブロードキャスト送信失敗"
        print("✓ エルダー評議会ブロードキャスト送信成功")
        
        # 3. 複数の緊急度でのブロードキャストテスト
        priorities = ["low", "medium", "high", "critical"]
        for priority in priorities:
            alert = {
                "alert_id": str(uuid.uuid4()),
                "sender": "incident_sage",
                "type": "system_alert",
                "priority": priority,
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "alert_level": priority,
                    "message": f"{priority.upper()} priority test alert"
                }
            }
            
            result = await rabbitmq_manager.publish_message(
                exchange="elder.fanout",
                routing_key="",
                body=json.dumps(alert),
                properties={
                    "priority": ["low", "medium", "high", "critical"].index(priority),
                    "type": "alert"
                }
            )
            assert result is True, f"{priority}優先度ブロードキャスト失敗"
        
        print("✓ 多段階優先度ブロードキャスト成功")
        
        print("✅ テスト3完了: ブロードキャスト通信成功")


class TestA2AMessageQueue:
    """A2Aメッセージキュー動作確認テスト"""
    
    @pytest.mark.asyncio
    async def test_queue_durability(self):
        """キューの永続性確認"""
        manager = PerfectRabbitMQManager()
        await manager.ensure_perfect_rabbitmq()
        
        # elder.tasks と elder.responses は durable=True
        assert "elder.tasks" in manager.queues
        assert "elder.responses" in manager.queues
        
        # キューの設定確認（実際のqueue オブジェクトがあれば）
        print("✓ 永続キュー存在確認")
        
        await manager.perfect_shutdown()


if __name__ == "__main__":
    # 実行
    pytest.main([__file__, '-v', '-s', '--tb=short'])