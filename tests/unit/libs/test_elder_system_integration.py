#!/usr/bin/env python3
"""
🏛️ エルダーシステム統合 テストスイート
Elder System Integration Test Suite
Created: 2025-07-16
Author: Claude Elder
Version: 1.0.0
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# テスト対象のインポート
sys.path.insert(0, str(Path(__file__).parent.parent))
from libs.multiprocess_a2a.elder_system_integration import (
    ElderSystemIntegration, 
    ElderComponent, 
    ElderType, 
    ElderSystemStatus,
    ElderSystemMetrics
)


class TestElderComponent:
    """エルダーコンポーネントテスト"""
    
    def test_elder_component_creation(self):
        """エルダーコンポーネント作成テスト"""
        component = ElderComponent(
            component_id="test_comp_001",
            component_name="Test Component",
            elder_type=ElderType.SERVANT,
            capabilities=["test_capability"]
        )
        
        assert component.component_id == "test_comp_001"
        assert component.component_name == "Test Component"
        assert component.elder_type == ElderType.SERVANT
        assert component.status == ElderSystemStatus.ACTIVE
        assert component.capabilities == ["test_capability"]
        assert component.process_id is None
        assert component.last_heartbeat is not None
    
    def test_elder_component_to_dict(self):
        """エルダーコンポーネント辞書変換テスト"""
        component = ElderComponent(
            component_id="test_comp_002",
            component_name="Test Component 2",
            elder_type=ElderType.SAGE,
            capabilities=["sage_capability", "consultation"]
        )
        
        component_dict = component.to_dict()
        
        assert component_dict["component_id"] == "test_comp_002"
        assert component_dict["component_name"] == "Test Component 2"
        assert component_dict["elder_type"] == "sage"
        assert component_dict["status"] == "active"
        assert component_dict["capabilities"] == ["sage_capability", "consultation"]
        assert "last_heartbeat" in component_dict
        assert "metadata" in component_dict


class TestElderSystemMetrics:
    """エルダーシステムメトリクステスト"""
    
    def test_elder_system_metrics_creation(self):
        """エルダーシステムメトリクス作成テスト"""
        metrics = ElderSystemMetrics()
        
        assert metrics.total_components == 0
        assert metrics.active_components == 0
        assert metrics.council_members == 0
        assert metrics.servant_count == 0
        assert metrics.sage_count == 0
        assert metrics.knight_count == 0
        assert metrics.tree_nodes == 0
        assert metrics.ancient_elders == 0
        assert metrics.coordination_requests == 0
        assert metrics.system_health == 0.0
        assert metrics.timestamp is not None
    
    def test_elder_system_metrics_with_values(self):
        """値を持つエルダーシステムメトリクステスト"""
        metrics = ElderSystemMetrics(
            total_components=10,
            active_components=8,
            sage_count=4,
            servant_count=4,
            council_members=1,
            knight_count=1,
            coordination_requests=15,
            system_health=80.0
        )
        
        assert metrics.total_components == 10
        assert metrics.active_components == 8
        assert metrics.sage_count == 4
        assert metrics.servant_count == 4
        assert metrics.council_members == 1
        assert metrics.knight_count == 1
        assert metrics.coordination_requests == 15
        assert metrics.system_health == 80.0


class TestElderSystemIntegration:
    """エルダーシステム統合テスト"""
    
    def test_integration_initialization(self):
        """統合システム初期化テスト"""
        integration = ElderSystemIntegration(max_components=50)
        
        assert integration.max_components == 50
        assert integration.integration_id.startswith("elder_system_")
        assert len(integration.elder_components) == 0
        assert len(integration.component_instances) == 0
        assert integration.system_metrics.total_components == 0
        assert integration.a2a_core is not None
        assert integration.sages_coordinator is not None
    
    def test_integration_capabilities(self):
        """統合システム機能一覧テスト"""
        integration = ElderSystemIntegration()
        capabilities = integration.get_capabilities()
        
        expected_capabilities = [
            "elder_system_integration",
            "multiprocess_a2a_coordination",
            "full_elder_hierarchy_management",
            "council_session_management",
            "servant_deployment",
            "tree_navigation",
            "knight_patrol_system",
            "ancient_wisdom_access",
            "system_health_monitoring",
            "elder_flow_enhanced"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
    
    @pytest.mark.asyncio
    async def test_initialize_elder_system(self):
        """エルダーシステム初期化リクエストテスト"""
        integration = ElderSystemIntegration(max_components=100)
        
        # 4賢者のモック
        mock_sages_result = {
            "success": True,
            "coordinator_id": "test_coordinator",
            "initialized_sages": ["knowledge", "task", "incident", "rag"],
            "parallel_capacity": 10
        }
        
        with patch.object(integration.sages_coordinator, 'initialize_sages', return_value=mock_sages_result):
            result = await integration.process_request({
                "type": "initialize_elder_system"
            })
            
            assert result["success"] is True
            assert result["integration_id"] == integration.integration_id
            assert result["components_integrated"] >= 4  # 最低4賢者
            assert "system_metrics" in result
            assert "component_summary" in result
            
            # 4賢者が統合されていることを確認
            assert len([c for c in integration.elder_components.values() if c.elder_type == ElderType.SAGE]) >= 4
    
    @pytest.mark.asyncio
    async def test_integrate_component(self):
        """コンポーネント統合テスト"""
        integration = ElderSystemIntegration()
        
        request = {
            "type": "integrate_component",
            "component_config": {
                "component_id": "test_component",
                "component_name": "Test Component",
                "elder_type": "servant",
                "capabilities": ["test_capability"]
            }
        }
        
        result = await integration.process_request(request)
        
        assert result["success"] is True
        assert result["component_id"] == "test_component"
        assert result["integration_id"] == integration.integration_id
        assert "system_metrics" in result
        
        # コンポーネントが統合されていることを確認
        assert "test_component" in integration.elder_components
        assert integration.elder_components["test_component"].elder_type == ElderType.SERVANT
    
    @pytest.mark.asyncio
    async def test_get_system_status(self):
        """システム状態取得テスト"""
        integration = ElderSystemIntegration()
        
        # テストコンポーネントを追加
        test_component = ElderComponent(
            component_id="test_status_comp",
            component_name="Test Status Component",
            elder_type=ElderType.SAGE
        )
        integration.elder_components["test_status_comp"] = test_component
        
        result = await integration.process_request({
            "type": "get_system_status"
        })
        
        assert result["success"] is True
        assert result["integration_id"] == integration.integration_id
        assert "system_metrics" in result
        assert "components" in result
        assert "component_count_by_type" in result
        assert "timestamp" in result
        
        # コンポーネントが含まれていることを確認
        assert "test_status_comp" in result["components"]
        assert result["component_count_by_type"]["sage"] >= 1
    
    @pytest.mark.asyncio
    async def test_coordinate_elders(self):
        """エルダー協調テスト"""
        integration = ElderSystemIntegration()
        
        # モックレスポンス
        mock_sages_result = {"success": True, "coordination_type": "test_coordination"}
        mock_a2a_result = {"success": True, "message_id": "test_msg_123"}
        
        with patch.object(integration.sages_coordinator, 'process_request', return_value=mock_sages_result), \
             patch.object(integration.a2a_core, 'process_request', return_value=mock_a2a_result):
            
            result = await integration.process_request({
                "type": "coordinate_elders",
                "coordination_type": "test_coordination",
                "participating_elders": ["sages", "council"],
                "payload": {"task": "test coordination"}
            })
            
            assert result["success"] is True
            assert result["coordination_type"] == "test_coordination"
            assert result["sages_coordination"]["success"] is True
            assert result["a2a_coordination"]["success"] is True
            assert result["participating_elders"] == ["sages", "council"]
            assert result["integration_id"] == integration.integration_id
    
    @pytest.mark.asyncio
    async def test_elder_council_session(self):
        """エルダー評議会セッションテスト"""
        integration = ElderSystemIntegration()
        
        # モック評議会インスタンス
        mock_council = Mock()
        mock_council.process_request = Mock(return_value={"success": True, "session_result": "approved"})
        integration.component_instances["elder_council"] = mock_council
        
        result = await integration.process_request({
            "type": "elder_council_session",
            "session_type": "approval",
            "agenda": {"topic": "test approval"}
        })
        
        assert result["success"] is True
        assert result["session_type"] == "approval"
        assert result["council_result"]["success"] is True
        assert result["integration_id"] == integration.integration_id
    
    @pytest.mark.asyncio
    async def test_servant_deployment(self):
        """サーバント配置テスト"""
        integration = ElderSystemIntegration()
        
        # テストサーバントを追加
        for i in range(3):
            servant = ElderComponent(
                component_id=f"servant_{i}",
                component_name=f"Test Servant {i}",
                elder_type=ElderType.SERVANT,
                status=ElderSystemStatus.ACTIVE
            )
            integration.elder_components[f"servant_{i}"] = servant
        
        result = await integration.process_request({
            "type": "servant_deployment",
            "deployment_type": "standard",
            "servant_count": 2,
            "task_config": {"task": "test deployment"}
        })
        
        assert result["success"] is True
        assert result["deployment_type"] == "standard"
        assert result["servants_deployed"] == 2
        assert len(result["deployment_results"]) == 2
        assert result["integration_id"] == integration.integration_id
    
    @pytest.mark.asyncio
    async def test_servant_deployment_insufficient(self):
        """サーバント配置不足テスト"""
        integration = ElderSystemIntegration()
        
        # 1つのサーバントのみ追加
        servant = ElderComponent(
            component_id="servant_1",
            component_name="Test Servant 1",
            elder_type=ElderType.SERVANT,
            status=ElderSystemStatus.ACTIVE
        )
        integration.elder_components["servant_1"] = servant
        
        result = await integration.process_request({
            "type": "servant_deployment",
            "deployment_type": "standard",
            "servant_count": 3,  # 3つ要求するが1つしかない
            "task_config": {"task": "test deployment"}
        })
        
        assert result["success"] is False
        assert "Insufficient servants available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_tree_navigation(self):
        """ツリーナビゲーションテスト"""
        integration = ElderSystemIntegration()
        
        # モックツリー構造
        mock_tree = {
            "grand_elder_maru": {"level": 0, "children": ["claude_elder"]},
            "claude_elder": {"level": 1, "children": ["sages", "council"]}
        }
        integration.component_instances["elder_tree"] = mock_tree
        
        result = await integration.process_request({
            "type": "tree_navigation",
            "navigation_type": "hierarchy",
            "target_node": "claude_elder"
        })
        
        assert result["success"] is True
        assert result["navigation_type"] == "hierarchy"
        assert result["navigation_result"]["current_node"] == "claude_elder"
        assert result["navigation_result"]["tree_structure"] == mock_tree
        assert result["integration_id"] == integration.integration_id
    
    @pytest.mark.asyncio
    async def test_knight_patrol(self):
        """騎士団パトロールテスト"""
        integration = ElderSystemIntegration()
        
        # テスト騎士団を追加
        for i in range(2):
            knight = ElderComponent(
                component_id=f"knight_{i}",
                component_name=f"Test Knight {i}",
                elder_type=ElderType.KNIGHT,
                status=ElderSystemStatus.ACTIVE
            )
            integration.elder_components[f"knight_{i}"] = knight
        
        result = await integration.process_request({
            "type": "knight_patrol",
            "patrol_type": "security",
            "patrol_area": "all"
        })
        
        assert result["success"] is True
        assert result["patrol_type"] == "security"
        assert result["knights_deployed"] == 2
        assert len(result["patrol_results"]) == 2
        assert result["integration_id"] == integration.integration_id
    
    @pytest.mark.asyncio
    async def test_ancient_wisdom_access(self):
        """古代の知恵アクセステスト"""
        integration = ElderSystemIntegration()
        
        # モックAncient Elderインスタンス
        mock_ancient = Mock()
        mock_ancient.process_request = Mock(return_value={"success": True, "wisdom": "ancient knowledge"})
        integration.component_instances["ancient_elder"] = mock_ancient
        
        result = await integration.process_request({
            "type": "ancient_wisdom_access",
            "wisdom_query": "test wisdom query",
            "access_level": "standard"
        })
        
        assert result["success"] is True
        assert result["wisdom_query"] == "test wisdom query"
        assert result["access_level"] == "standard"
        assert result["wisdom_result"]["success"] is True
        assert result["integration_id"] == integration.integration_id
    
    @pytest.mark.asyncio
    async def test_full_system_health_check(self):
        """システム全体健全性チェックテスト"""
        integration = ElderSystemIntegration()
        
        # 各タイプのコンポーネントを追加
        component_configs = [
            ("sage_knowledge", "Knowledge Sage", ElderType.SAGE),
            ("sage_task", "Task Sage", ElderType.SAGE),
            ("servant_1", "Test Servant", ElderType.SERVANT),
            ("knight_1", "Test Knight", ElderType.KNIGHT),
            ("council_1", "Test Council", ElderType.COUNCIL)
        ]
        
        for comp_id, comp_name, elder_type in component_configs:
            component = ElderComponent(
                component_id=comp_id,
                component_name=comp_name,
                elder_type=elder_type,
                status=ElderSystemStatus.ACTIVE
            )
            integration.elder_components[comp_id] = component
        
        result = await integration.process_request({
            "type": "full_system_health_check"
        })
        
        assert result["success"] is True
        assert result["system_health_score"] == 100.0  # すべてのコンポーネントが健全
        assert "component_health" in result
        assert "system_metrics" in result
        assert "timestamp" in result
        assert result["integration_id"] == integration.integration_id
        
        # 各コンポーネントの健全性がチェックされていることを確認
        for comp_id in ["sage_knowledge", "sage_task", "servant_1", "knight_1", "council_1"]:
            assert comp_id in result["component_health"]
            assert result["component_health"][comp_id]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_invalid_request_type(self):
        """無効なリクエストタイプテスト"""
        integration = ElderSystemIntegration()
        
        result = await integration.process_request({
            "type": "invalid_request_type",
            "data": "test"
        })
        
        assert result["success"] is False
        assert "Unknown request type" in result["error"]
        assert result["integration_id"] == integration.integration_id
    
    @pytest.mark.asyncio
    async def test_validation_failure(self):
        """バリデーション失敗テスト"""
        integration = ElderSystemIntegration()
        
        # typeフィールドなしのリクエスト
        is_valid = await integration.validate_request({
            "data": "test"
        })
        
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_update_system_metrics(self):
        """システムメトリクス更新テスト"""
        integration = ElderSystemIntegration()
        
        # 各タイプのコンポーネントを追加
        sage_comp = ElderComponent("sage_1", "Sage 1", ElderType.SAGE, ElderSystemStatus.ACTIVE)
        servant_comp = ElderComponent("servant_1", "Servant 1", ElderType.SERVANT, ElderSystemStatus.ACTIVE)
        knight_comp = ElderComponent("knight_1", "Knight 1", ElderType.KNIGHT, ElderSystemStatus.INACTIVE)
        
        integration.elder_components.update({
            "sage_1": sage_comp,
            "servant_1": servant_comp,
            "knight_1": knight_comp
        })
        
        await integration._update_system_metrics()
        
        assert integration.system_metrics.total_components == 3
        assert integration.system_metrics.active_components == 2
        assert integration.system_metrics.system_health == (2/3) * 100
        assert integration.system_metrics.timestamp is not None


class TestIntegrationScenarios:
    """統合シナリオテスト"""
    
    @pytest.mark.asyncio
    async def test_full_integration_workflow(self):
        """完全統合ワークフローテスト"""
        integration = ElderSystemIntegration(max_components=100)
        
        # 4賢者のモック
        mock_sages_result = {
            "success": True,
            "coordinator_id": "test_coordinator",
            "initialized_sages": ["knowledge", "task", "incident", "rag"],
            "parallel_capacity": 10
        }
        
        with patch.object(integration.sages_coordinator, 'initialize_sages', return_value=mock_sages_result):
            # 1.0 システム初期化
            init_result = await integration.process_request({
                "type": "initialize_elder_system"
            })
            assert init_result["success"] is True
            
            # 2.0 システム状態確認
            status_result = await integration.process_request({
                "type": "get_system_status"
            })
            assert status_result["success"] is True
            assert status_result["system_metrics"]["total_components"] >= 4
            
            # 3.0 エルダー協調
            with patch.object(integration.sages_coordinator, 'process_request', return_value={"success": True}), \
                 patch.object(integration.a2a_core, 'process_request', return_value={"success": True}):
                
                coordination_result = await integration.process_request({
                    "type": "coordinate_elders",
                    "coordination_type": "full_system_test",
                    "participating_elders": ["sages", "council", "servants"],
                    "payload": {"task": "integration test"}
                })
                assert coordination_result["success"] is True
            
            # 4.0 健全性チェック
            health_result = await integration.process_request({
                "type": "full_system_health_check"
            })
            assert health_result["success"] is True
            assert health_result["system_health_score"] > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """並行操作テスト"""
        integration = ElderSystemIntegration()
        
        # 複数のコンポーネントを追加
        for i in range(5):
            component = ElderComponent(
                component_id=f"concurrent_comp_{i}",
                component_name=f"Concurrent Component {i}",
                elder_type=ElderType.SERVANT,
                status=ElderSystemStatus.ACTIVE
            )
            integration.elder_components[f"concurrent_comp_{i}"] = component
        
        # 複数のリクエストを並行実行
        tasks = []
        for i in range(3):
            task = integration.process_request({
                "type": "get_system_status"
            })
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # すべてのリクエストが成功していることを確認
        for result in results:
            assert result["success"] is True
            assert result["system_metrics"]["total_components"] == 5
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """エラーハンドリングテスト"""
        integration = ElderSystemIntegration()
        
        # 例外を発生させるモック
        with patch.object(integration, '_get_system_status', side_effect=Exception("Test error")):
            result = await integration.process_request({
                "type": "get_system_status"
            })
            
            assert result["success"] is False
            assert "Test error" in result["error"]
            assert result["integration_id"] == integration.integration_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])