#!/usr/bin/env python3
"""
Elder Legacy統合テスト
Elder Legacy アーキテクチャの統合動作を検証
"""

import pytest
import asyncio

import shutil
from pathlib import Path
import sys

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.conversation_manager import ConversationManager
from libs.rag_manager import RAGManager
from libs.self_evolution_manager import SelfEvolutionManager
from libs.pm_git_integration import PMGitIntegration
from workers.enhanced_task_worker import EnhancedTaskWorker
from workers.enhanced_pm_worker import EnhancedPMWorker

class TestElderLegacyIntegration:
    """Elder Legacy統合テスト"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """テスト環境セットアップ"""

        yield

    @pytest.mark.asyncio
    async def test_conversation_rag_integration(self):
        """ConversationManagerとRAGManagerの統合テスト"""
        # マネージャー初期化

        conversation_manager = ConversationManager(str(conv_db))
        rag_manager = RAGManager(str(rag_db))
        
        # 会話開始
        conv_result = await conversation_manager.process_request({
            "operation": "start_conversation",
            "task_id": "test_integration_1",
            "initial_prompt": "Elder Legacyについて教えてください",
            "context": {"test": True}
        })
        assert conv_result["status"] == "success"
        conversation_id = conv_result["conversation_id"]
        
        # RAGにドキュメント追加
        rag_result = await rag_manager.process_request({
            "operation": "add_document",
            "content": "Elder Legacyは統合ベースクラスアーキテクチャです。AI、Service、Flow、Entityの4要素を統合します。",
            "doc_type": "documentation",
            "metadata": {"source": "integration_test"}
        })
        assert rag_result["status"] in ["success", "warning"]
        
        # RAGで検索
        search_result = await rag_manager.process_request({
            "operation": "search_documents",
            "query": "Elder Legacy",
            "limit": 5
        })
        assert search_result["status"] == "success"
        
        # 検索結果を会話に追加
        if search_result["results"]:
            # RAGManager実装に応じて適切なフィールドを使用
            first_result = search_result["results"][0]
            context_text = first_result.get("text", first_result.get("content", ""))
            msg_result = await conversation_manager.process_request({
                "operation": "add_message",
                "conversation_id": conversation_id,
                "sender": "assistant",
                "content": f"RAGから取得した情報: {context_text}",
                "message_type": "ai_response"
            })
            assert msg_result["status"] == "success"
        
        # 会話完了
        complete_result = await conversation_manager.process_request({
            "operation": "complete_conversation",
            "conversation_id": conversation_id,
            "summary": "Elder Legacy統合テスト完了"
        })
        assert complete_result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_task_pm_worker_integration(self):
        """TaskWorkerとPMWorkerの統合テスト"""
        # ワーカー初期化
        task_worker = EnhancedTaskWorker(worker_id="integration-task-1")
        pm_worker = EnhancedPMWorker(worker_id="integration-pm-1")
        
        # PMでプロジェクト作成
        project_result = await pm_worker.process_request({
            "operation": "create_project",
            "name": "Elder Legacy Integration",
            "description": "統合テストプロジェクト"
        })
        assert project_result["status"] == "success"
        project_id = project_result["project"]["id"]
        
        # PMでタスク作成
        task_result = await pm_worker.process_request({
            "operation": "create_task",
            "project_id": project_id,
            "title": "統合テストタスク",
            "description": "Elder Legacy統合動作確認",
            "priority": "high"
        })
        assert task_result["status"] == "success"
        
        # TaskWorkerでタスク実行
        submit_result = await task_worker.process_request({
            "operation": "submit_task",
            "task_type": "execution",
            "payload": {
                "action": "test_integration",
                "project_id": project_id,
                "task_title": "統合テストタスク"
            },
            "priority": "high"
        })
        assert submit_result["status"] == "success"
        
        # キュー処理
        process_result = await task_worker.process_request({
            "operation": "process_queue"
        })
        assert process_result["status"] == "success"
        
        # ダッシュボード確認
        dashboard_result = await pm_worker.process_request({
            "operation": "get_dashboard"
        })
        assert dashboard_result["status"] == "success"
        # 実際のレスポンス構造に合わせて確認
        assert "dashboard" in dashboard_result
        assert dashboard_result["dashboard"]["overview"]["total_projects"] >= 1
    
    @pytest.mark.asyncio
    async def test_evolution_git_integration(self):
        """SelfEvolutionManagerとPMGitIntegrationの統合テスト"""
        # マネージャー初期化

        git_integration = PMGitIntegration()
        
        # ファイル分析
        analyze_result = await evolution_manager.process_request({
            "operation": "analyze_file",
            "file_path": "test_integration_worker.py",
            "content": "class IntegrationWorker:\n    pass"
        })
        assert analyze_result["status"] == "success"
        assert "workers" in analyze_result["target_directory"]
        
        # Git状態確認
        git_status = await git_integration.process_request({
            "operation": "get_git_status"
        })
        assert git_status["status"] == "success"
        
        # 配置プレビュー
        preview_result = await evolution_manager.process_request({
            "operation": "get_placement_preview",
            "file_path": "test_manager.py",
            "content": "class TestManager:\n    pass"
        })
        assert preview_result["status"] == "success"
        
        # フィードバック記録
        feedback_result = await evolution_manager.process_request({
            "operation": "record_feedback",
            "file_path": "test_worker.py",
            "target_dir": "workers/",
            "success": True
        })
        assert feedback_result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_full_elder_legacy_flow(self):
        """完全なElder Legacyフロー統合テスト"""
        # 全コンポーネント初期化

        task_worker = EnhancedTaskWorker(worker_id="flow-task-1")
        pm_worker = EnhancedPMWorker(worker_id="flow-pm-1")
        
        # 1.0 会話開始
        conv_result = await conv_manager.process_request({
            "operation": "start_conversation",
            "task_id": "flow_test_1",
            "initial_prompt": "Elder Legacy統合フローテスト"
        })
        conversation_id = conv_result["conversation_id"]
        
        # 2.0 プロジェクト作成
        project_result = await pm_worker.process_request({
            "operation": "create_project",
            "name": "Flow Test Project",
            "description": "統合フローテスト"
        })
        project_id = project_result["project"]["id"]
        
        # 3.0 タスク投入
        task_result = await task_worker.process_request({
            "operation": "submit_task",
            "task_type": "analysis",
            "payload": {
                "conversation_id": conversation_id,
                "project_id": project_id,
                "action": "analyze_elder_legacy"
            }
        })
        
        # 4.0 RAGに結果保存
        rag_result = await rag_manager.process_request({
            "operation": "add_document",
            "content": f"タスク{task_result.get('task_id', 'unknown')}の実行結果",
            "doc_type": "documentation",  # 有効なドキュメントタイプに変更
            "metadata": {
                "conversation_id": conversation_id,
                "project_id": project_id,
                "type": "result"
            }
        })
        
        # 5.0 会話完了
        complete_result = await conv_manager.process_request({
            "operation": "complete_conversation",
            "conversation_id": conversation_id,
            "summary": "統合フローテスト完了"
        })
        
        # 検証
        assert conv_result["status"] == "success"
        assert project_result["status"] == "success"
        assert task_result["status"] == "success"
        assert rag_result["status"] in ["success", "warning"]
        assert complete_result["status"] == "success"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])