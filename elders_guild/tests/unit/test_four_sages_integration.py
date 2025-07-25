#!/usr/bin/env python3
"""
Four Sages Integration System - 統合テスト
4賢者システムの完全な動作検証とパフォーマンステスト

Elder Flow TDD実装:
1.0 🔴 Red: 失敗するテストを作成
2.0 🟢 Green: 最小限のコードで成功
3.0 🔵 Refactor: コード改善

テスト対象:
- 4賢者の協調動作
- Elder Tree統合
- 賢者間通信
- コンセンサス形成
- エラーハンドリング
"""

import pytest
import asyncio
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import time

# プロジェクトルートをパスに追加
import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.four_sages_integration import FourSagesIntegration

class TestFourSagesIntegration:
    """4賢者統合システムテスト"""

    @pytest.fixture

        """テスト用一時データベースパス"""

            yield Path(tmpdir) / "test_sages.db"

    @pytest.fixture

        """テスト用統合システムインスタンス"""

            system = FourSagesIntegration()

            system._init_database()
            yield system

    @pytest.fixture
    def mock_elder_tree(self):
        """Elder Treeモック"""
        mock_tree = Mock()
        mock_tree.nodes = {
            "knowledge_sage": Mock(soul_bound=True),
            "task_sage": Mock(soul_bound=True),
            "incident_sage": Mock(soul_bound=True),
            "rag_sage": Mock(soul_bound=True),
        }
        mock_tree.bind_soul_to_elder = Mock(return_value=True)
        mock_tree.send_elder_message = Mock(return_value=True)
        mock_tree.process_message_queue = Mock(return_value=4)
        mock_tree.get_elder_tree_status = Mock(return_value={"hierarchy_health": 0.95})
        return mock_tree

    @pytest.fixture
    def mock_soul_binding_system(self):
        """Soul Binding Systemモック"""
        mock_binding = AsyncMock()
        mock_binding.create_soul_binding = AsyncMock(return_value=True)
        mock_binding.get_soul_binding_status = Mock(return_value={"active_bindings": 6})
        return mock_binding

    # ========== 基本機能テスト ==========

    def test_initialization(self, integration_system):
        """初期化テスト"""
        assert integration_system is not None
        assert len(integration_system.sages_status) == 4
        assert all(sage["active"] for sage in integration_system.sages_status.values())
        assert integration_system.collaboration_config["auto_sync"] is True
        assert integration_system.collaboration_config["consensus_threshold"] == 0.75

    def test_database_initialization(self, integration_system):
        """データベース初期化テスト"""
        assert integration_system.db_path.parent.exists()
        
        # テーブル存在確認
        conn = sqlite3connect(str(integration_system.db_path))
        cursor = conn.cursor()
        
        # テーブル一覧取得
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        expected_tables = {
            "sage_communications",
            "learning_sessions",
            "sage_performance"
        }
        
        assert expected_tables.issubset(tables)
        conn.close()

    def test_sage_status_management(self, integration_system):
        """賢者状態管理テスト"""
        # 初期状態確認
        for sage_name, status in integration_system.sages_status.items():
            assert status["active"] is True
            assert status["health"] == "healthy"
            assert status["last_interaction"] is None

        # 状態更新
        integration_system.sages_status["knowledge_sage"]["health"] = "warning"
        integration_system.sages_status["knowledge_sage"]["last_interaction"] = datetime.now()
        
        assert integration_system.sages_status["knowledge_sage"]["health"] == "warning"
        assert integration_system.sages_status["knowledge_sage"]["last_interaction"] is not None

    # ========== Elder Tree統合テスト ==========

    @patch('libs.four_sages_integration.get_elder_tree')
    @patch('libs.four_sages_integration.get_soul_binding_system')
    @patch('libs.four_sages_integration.ELDER_TREE_AVAILABLE', True)
    def test_elder_tree_integration(self, mock_get_soul_binding, mock_get_elder_tree, 
                                   mock_elder_tree, mock_soul_binding_system):
        """Elder Tree統合テスト"""
        mock_get_elder_tree.return_value = mock_elder_tree
        mock_get_soul_binding.return_value = mock_soul_binding_system
        
        # 統合システム初期化
        system = FourSagesIntegration()
        
        # Elder Tree統合確認
        assert system.elder_tree is not None
        assert system.soul_binding_system is not None
        assert len(system.sage_nodes) == 4
        
        # 各賢者のsoul binding確認
        for sage_name in system.sages_status.keys():
            assert sage_name in system.sage_nodes

    @pytest.mark.asyncio
    async def test_send_elder_message_to_sage(self, integration_system, mock_elder_tree):
        """賢者へのElderメッセージ送信テスト"""
        integration_system.elder_tree = mock_elder_tree
        integration_system.sage_nodes = {
            "knowledge_sage": Mock(),
            "task_sage": Mock(),
            "incident_sage": Mock(),
            "rag_sage": Mock(),
        }
        
        # メッセージ送信
        message_content = {"type": "learning_request", "data": "test"}
        result = await integration_system.send_elder_message_to_sage("knowledge_sage", message_content)
        
        assert result is True
        mock_elder_tree.send_elder_message.assert_called_once()
        mock_elder_tree.process_message_queue.assert_called_once()
        
        # メッセージキュー確認
        assert len(integration_system.message_queues["knowledge_sage"]) == 1
        queued_message = integration_system.message_queues["knowledge_sage"][0]
        assert queued_message["type"] == "elder_tree_message"
        assert queued_message["content"] == message_content

    @pytest.mark.asyncio
    async def test_broadcast_to_all_sages(self, integration_system, mock_elder_tree):
        """全賢者へのブロードキャストテスト"""
        integration_system.elder_tree = mock_elder_tree
        integration_system.sage_nodes = {
            sage: Mock() for sage in integration_system.sages_status.keys()
        }
        
        message_content = {"type": "system_update", "data": "broadcast_test"}
        results = await integration_system.broadcast_to_all_sages(message_content)
        
        assert len(results) == 4
        assert all(results.values())
        assert mock_elder_tree.send_elder_message.call_count == 4

    # ========== 協調学習テスト ==========

    def test_coordinate_learning_session(self, integration_system):
        """協調学習セッションテスト"""
        learning_request = {
            "type": "pattern_analysis",
            "data": {"patterns": ["test_pattern1", "test_pattern2"]},
            "priority": "high"
        }
        
        result = integration_system.coordinate_learning_session(learning_request)
        
        assert result["session_id"] is not None
        assert "learning_session_" in result["session_id"]
        assert len(result["participating_sages"]) > 0
        assert "consensus_reached" in result
        assert "learning_outcome" in result
        assert result["session_duration"] >= 0

    def test_determine_participating_sages(self, integration_system):
        """参加賢者決定テスト"""
        # パターン分析の場合
        request = {"type": "pattern_analysis"}
        sages = integration_system._determine_participating_sages(request)
        assert "knowledge_sage" in sages
        assert "rag_sage" in sages
        
        # パフォーマンス最適化の場合
        request = {"type": "performance_optimization"}
        sages = integration_system._determine_participating_sages(request)
        assert "task_sage" in sages
        assert "incident_sage" in sages
        
        # 一般的な場合
        request = {"type": "general"}
        sages = integration_system._determine_participating_sages(request)
        assert len(sages) == 4

    def test_form_consensus(self, integration_system):
        """コンセンサス形成テスト"""
        sage_responses = {
            "knowledge_sage": {
                "success": True,
                "recommendation": "Store patterns",
                "confidence_score": 0.9
            },
            "rag_sage": {
                "success": True,
                "recommendation": "Store patterns",
                "confidence_score": 0.8
            },
            "task_sage": {
                "success": True,
                "recommendation": "Optimize workflow",
                "confidence_score": 0.6
            }
        }
        
        result = integration_system._form_consensus(sage_responses, {})
        
        assert result["consensus_reached"] is True
        assert result["final_decision"] == "Store patterns"
        assert result["consensus_confidence"] > integration_system.collaboration_config["consensus_threshold"]
        assert len(result["participating_sages"]) == 3

    def test_consensus_failure(self, integration_system):
        """コンセンサス失敗テスト"""
        # 低信頼度の場合
        sage_responses = {
            "knowledge_sage": {
                "success": True,
                "recommendation": "Option A",
                "confidence_score": 0.3
            },
            "task_sage": {
                "success": True,
                "recommendation": "Option B",
                "confidence_score": 0.3
            }
        }
        
        result = integration_system._form_consensus(sage_responses, {})
        assert result["consensus_reached"] is False

    # ========== クロス学習テスト ==========

    def test_facilitate_cross_sage_learning(self, integration_system):
        """賢者間クロス学習テスト"""
        learning_data = {
            "topic": "optimization_patterns",
            "source": "performance_analysis"
        }
        
        result = integration_system.facilitate_cross_sage_learning(learning_data)
        
        assert result["cross_learning_completed"] is True
        assert len(result["knowledge_transfers"]) > 0
        assert "learning_effectiveness" in result
        assert result["learning_effectiveness"]["overall_effectiveness"] >= 0
        assert len(result["improvements_identified"]) > 0

    def test_share_knowledge_between_sages(self, integration_system):
        """賢者間知識共有テスト"""
        knowledge = {"patterns": ["pattern1"], "insights": ["insight1"]}
        
        result = integration_system._share_knowledge_between_sages(
            "knowledge_sage", "task_sage", knowledge
        )
        
        assert result["transfer_successful"] is True
        assert result["knowledge_integrated"] is True
        assert result["integration_quality"] > 0
        assert result["new_insights_generated"] >= 0

    # ========== 競合解決テスト ==========

    def test_resolve_sage_conflicts(self, integration_system):
        """賢者間競合解決テスト"""
        conflicting_recommendations = {
            "knowledge_sage": {
                "recommendation": "Approach A",
                "confidence_score": 0.9
            },
            "task_sage": {
                "recommendation": "Approach B",
                "confidence_score": 0.7
            },
            "incident_sage": {
                "recommendation": "Approach C",
                "confidence_score": 0.6
            }
        }
        
        result = integration_system.resolve_sage_conflicts(conflicting_recommendations)
        
        assert result["conflict_resolved"] is True
        assert result["resolution_strategy"] in ["simple_majority", "weighted_vote", "expert_arbitration"]
        assert result["final_recommendation"] == "Approach A"  # 最高信頼度
        assert result["confidence_score"] == 0.9
        assert len(result["participating_sages"]) == 3

    # ========== 監視・分析テスト ==========

    def test_monitor_sage_collaboration(self, integration_system):
        """賢者協調監視テスト"""
        result = integration_system.monitor_sage_collaboration()
        
        assert "timestamp" in result
        assert "active_learning_sessions" in result
        assert "sage_health_status" in result
        assert "performance_metrics" in result
        assert "communication_statistics" in result
        assert "alerts" in result
        assert result["overall_collaboration_health"] in ["excellent", "good", "needs_attention"]

    def test_optimize_sage_interactions(self, integration_system):
        """賢者間相互作用最適化テスト"""
        optimization_targets = {
            "communication_efficiency": True,
            "decision_speed": True,
            "learning_effectiveness": True,
            "consensus_quality": True
        }
        
        result = integration_system.optimize_sage_interactions(optimization_targets)
        
        assert result["optimization_completed"] is True
        assert len(result["optimized_areas"]) == 4
        assert "impact_assessment" in result
        assert len(result["next_optimization_recommendations"]) > 0

    def test_get_integration_analytics(self, integration_system):
        """統合分析データ取得テスト"""
        result = integration_system.get_integration_analytics(time_range_days=7)
        
        assert result["analysis_period"]["days"] == 7
        assert "learning_session_analytics" in result
        assert "communication_analytics" in result
        assert "performance_trends" in result
        assert "sage_effectiveness" in result
        assert len(result["improvement_opportunities"]) > 0

    # ========== パフォーマンステスト ==========

    def test_message_queue_performance(self, integration_system):
        """メッセージキューパフォーマンステスト"""
        # 大量メッセージ投入
        start_time = time.time()
        
        # 繰り返し処理
        for i in range(1000):
            for sage in integration_system.message_queues.keys():
                integration_system.message_queues[sage].append({
                    "type": "test",
                    "data": f"message_{i}",
                    "timestamp": datetime.now()
                })
        
        elapsed_time = time.time() - start_time
        
        # 1000メッセージ × 4賢者 = 4000メッセージを1秒以内で処理
        assert elapsed_time < 1.0
        
        # 各キューのサイズ確認（maxlen=100）
        for sage, queue in integration_system.message_queues.items():
            assert len(queue) == 100

    @pytest.mark.asyncio
    async def test_concurrent_learning_sessions(self, integration_system):
        """並行学習セッションテスト"""
        # 10個の並行セッション
        tasks = []
        for i in range(10):
            request = {
                "type": "general",
                "data": {"session": i}
            }
            task = asyncio.create_task(
                asyncio.to_thread(
                    integration_system.coordinate_learning_session,
                    request
                )
            )
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed_time = time.time() - start_time
        
        # すべてのセッションが成功
        assert len(results) == 10
        assert all(r["session_id"] is not None for r in results)
        
        # 10セッションを5秒以内で処理
        assert elapsed_time < 5.0

    # ========== エラーハンドリングテスト ==========

    def test_error_handling_in_learning_session(self, integration_system):
        """学習セッションエラーハンドリングテスト"""
        # 無効なリクエスト
        with patch.object(integration_system, '_determine_participating_sages', side_effect=Exception("Test error")):
            result = integration_system.coordinate_learning_session({})
            
            assert result["session_id"] is None
            assert "error" in result
            assert result["consensus_reached"] is False

    def test_database_error_recovery(self, integration_system):
        """データベースエラー復旧テスト"""
        # データベース接続エラーシミュレーション
        with patch('sqlite3connect', side_effect=sqlite3Error("Database error")):
            # エラーが発生してもクラッシュしない
            session_data = {
                "session_id": "test_session",
                "participating_sages": ["knowledge_sage"],
                "learning_request": {"type": "test"},
                "start_time": datetime.now(),
                "end_time": datetime.now()
            }
            
            # 例外が発生してもログに記録されるだけ
            integration_system._save_learning_session(session_data)
            # テストが通ればOK（例外でクラッシュしない）

    # ========== 統合システムAPI テスト ==========

    @pytest.mark.asyncio
    async def test_initialize_api(self, integration_system):
        """初期化APIテスト"""
        with patch.object(integration_system, '_initialize_database', new_callable=AsyncMock):
            with patch.object(integration_system, '_verify_sages_health', new_callable=AsyncMock):
                with patch.object(integration_system, '_setup_collaboration_systems', new_callable=AsyncMock):
                    await integration_system.initialize()
                    
                    integration_system._initialize_database.assert_called_once()
                    integration_system._verify_sages_health.assert_called_once()
                    integration_system._setup_collaboration_systems.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_system_status_api(self, integration_system):
        """システム状態取得APIテスト"""
        status = await integration_system.get_system_status()
        
        assert status["system_status"] == "operational"
        assert "sages_status" in status
        assert "collaboration_metrics" in status
        assert "elder_hierarchy" in status
        assert status["elder_hierarchy"]["grand_elder"] == "maru"
        assert status["elder_hierarchy"]["claude_elder"] == "active"
        assert "knowledge_stats" in status
        assert "timestamp" in status

    @pytest.mark.asyncio
    async def test_cleanup_api(self, integration_system):
        """クリーンアップAPIテスト"""
        with patch.object(integration_system, '_terminate_active_sessions', new_callable=AsyncMock):
            with patch.object(integration_system, '_close_database_connections', new_callable=AsyncMock):
                with patch.object(integration_system, '_notify_sages_shutdown', new_callable=AsyncMock):
                    await integration_system.cleanup()
                    
                    integration_system._terminate_active_sessions.assert_called_once()
                    integration_system._close_database_connections.assert_called_once()
                    integration_system._notify_sages_shutdown.assert_called_once()

    # ========== デプロイメント設定テスト ==========

    def test_optimize_deployment_config(self, integration_system):
        """デプロイメント設定最適化テスト"""
        config = {
            "project": {"type": "web-app"},
            "deployment_method": "manual",
            "environments": {
                "production": {}
            }
        }
        
        optimized = integration_system.optimize_deployment_config(config)
        
        # 各賢者の最適化が適用されているか確認
        assert optimized["rollback_enabled"] is True  # ナレッジ賢者
        assert optimized["environments"]["production"]["approval_required"] is True  # インシデント賢者
        assert "resources" in optimized  # RAG賢者

    def test_validate_deployment_config(self, integration_system):
        """デプロイメント設定検証テスト"""
        # 有効な設定
        valid_config = {
            "deployment_method": "github_actions",
            "environments": {
                "production": {"approval_required": True}
            }
        }
        
        result = integration_system.validate_deployment_config(valid_config)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        
        # 無効な設定
        invalid_config = {}
        result = integration_system.validate_deployment_config(invalid_config)
        assert result["valid"] is False
        assert "deployment_method is required" in result["errors"]

    def test_pre_deployment_analysis(self, integration_system):
        """デプロイ前分析テスト"""
        config = {
            "deployment_method": "github_actions",
            "environments": {
                "production": {"approval_required": False}
            }
        }
        
        analysis = integration_system.pre_deployment_analysis(config)
        
        assert analysis["risk_level"] in ["low", "medium", "high"]
        assert isinstance(analysis["estimated_duration"], int)
        assert len(analysis["recommendations"]) > 0

    # ========== 賢者健全性チェックテスト ==========

    def test_check_integration_health(self, integration_system):
        """統合システム健全性チェックテスト"""
        health = integration_system._check_integration_health()
        
        assert health["overall_health"] in ["healthy", "warning", "critical"]
        assert health["active_sages"] == 4
        assert health["total_sages"] == 4
        assert health["health_score"] == 1.0

    def test_detect_collaboration_alerts(self, integration_system):
        """協調アラート検出テスト"""
        # 健全な状態
        alerts = integration_system._detect_collaboration_alerts()
        assert len(alerts) == 0
        
        # 賢者を非アクティブに
        integration_system.sages_status["knowledge_sage"]["active"] = False
        integration_system.sages_status["task_sage"]["health"] = "error"
        
        alerts = integration_system._detect_collaboration_alerts()
        assert len(alerts) == 2
        assert any("knowledge_sage is inactive" in alert for alert in alerts)
        assert any("task_sage health issue" in alert for alert in alerts)

    # ========== 統計情報テスト ==========

    def test_performance_metrics_update(self, integration_system):
        """パフォーマンスメトリクス更新テスト"""
        initial_metrics = integration_system.performance_metrics.copy()
        
        # 成功セッション
        session_data = {
            "consensus_result": {"consensus_reached": True},
            "duration": 10.0
        }
        
        integration_system._update_performance_metrics(session_data)
        
        assert integration_system.performance_metrics["total_collaborations"] \
            == initial_metrics["total_collaborations"] + \
            \
            1
        assert integration_system.performance_metrics["successful_consensus"] \
            == initial_metrics["successful_consensus"] + \
            \
            1
        assert integration_system.performance_metrics["avg_response_time"] > 0

    def test_sage_performance_tracking(self, integration_system):
        """賢者パフォーマンス追跡テスト"""
        # パフォーマンスデータ保存
        conn = sqlite3connect(str(integration_system.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sage_performance (sage_name, metric_type, metric_value, timestamp, context)
            VALUES (?, ?, ?, ?, ?)
        """, ("knowledge_sage", "response_time", 1.5, datetime.now(), "test_context"))
        
        conn.commit()
        
        # データ確認
        cursor.execute("SELECT COUNT(*) FROM sage_performance WHERE sage_name = 'knowledge_sage'")
        count = cursor.fetchone()[0]
        
        assert count == 1
        conn.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])