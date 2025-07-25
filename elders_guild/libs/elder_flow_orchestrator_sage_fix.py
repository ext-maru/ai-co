#!/usr/bin/env python3
"""
Elder Flow Orchestrator 賢者相談メソッド修正パッチ
Issue #157対応: 4賢者相談の非同期処理エラー修正
"""

# ElderFlowOrchestratorクラスに追加すべきメソッド

async def _consult_knowledge_sage(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """ナレッジ賢者への相談（互換性メソッド）"""
    if hasattr(self, 'sage_council') and self.sage_council:
        # SageCouncilSystemを使用
        return await self.sage_council.consult_sage(
            sage_type="knowledge",
            request=request
        )
    elif hasattr(self, 'knowledge_sage') and self.knowledge_sage:
        # 直接KnowledgeSageを使用
        return await self.knowledge_sage.process_request(request)
    else:
        # フォールバック
        self.logger.warning("Knowledge Sage not available, returning empty result")
        return {
            "status": "unavailable",
            "message": "Knowledge Sage is not initialized",
            "entries": []
        }

async def _consult_task_sage(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """タスク賢者への相談（互換性メソッド）"""
    if hasattr(self, 'sage_council') and self.sage_council:
        # SageCouncilSystemを使用
        return await self.sage_council.consult_sage(
            sage_type="task",
            request=request
        )
    elif hasattr(self, 'task_sage') and self.task_sage:
        # 直接TaskSageを使用
        return await self.task_sage.process_request(request)
    else:
        # フォールバック
        self.logger.warning("Task Sage not available, returning empty result")
        return {
            "status": "unavailable",
            "message": "Task Sage is not initialized",
            "plan": {}
        }

async def _consult_incident_sage(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """インシデント賢者への相談（互換性メソッド）"""
    if hasattr(self, 'sage_council') and self.sage_council:
        # SageCouncilSystemを使用
        return await self.sage_council.consult_sage(
            sage_type="incident",
            request=request
        )
    elif hasattr(self, 'incident_sage') and self.incident_sage:
        # 直接IncidentSageを使用
        return await self.incident_sage.process_request(request)
    else:
        # フォールバック
        self.logger.warning("Incident Sage not available, returning empty result")
        return {
            "status": "unavailable",
            "message": "Incident Sage is not initialized",
            "risks": []
        }

async def _consult_rag_sage(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """RAG賢者への相談（互換性メソッド）"""
    if hasattr(self, 'sage_council') and self.sage_council:
        # SageCouncilSystemを使用
        return await self.sage_council.consult_sage(
            sage_type="rag",
            request=request
        )
    elif hasattr(self, 'rag_sage') and self.rag_sage:
        # 直接RagManagerを使用
        return await self.rag_sage.process_request(request)
    else:
        # フォールバック
        self.logger.warning("RAG Sage not available, returning empty result")
        return {
            "status": "unavailable",
            "message": "RAG Sage is not initialized",
            "results": []
        }

# 初期化メソッドの改善案
def _ensure_sage_compatibility(self):
    """賢者システムの互換性を確保"""
    # SageCouncilSystemが初期化されていない場合の対処
    if not hasattr(self, 'sage_council') or self.sage_council is None:
        self.logger.warning("SageCouncilSystem not initialized, setting up fallback methods")
        
        # 個別の賢者オブジェクトを初期化
        try:
            if not hasattr(self, 'knowledge_sage'):
                from libs.knowledge_sage import KnowledgeSage
                self.knowledge_sage = KnowledgeSage()
        except Exception as e:
            self.logger.error(f"Failed to initialize Knowledge Sage: {e}")
            self.knowledge_sage = None
            
        try:
            if not hasattr(self, 'task_sage'):
                from libs.task_sage import TaskSage
                self.task_sage = TaskSage()
        except Exception as e:
            self.logger.error(f"Failed to initialize Task Sage: {e}")
            self.task_sage = None
            
        try:
            if not hasattr(self, 'incident_sage'):
                from libs.incident_sage import IncidentSage
                self.incident_sage = IncidentSage()
        except Exception as e:
            self.logger.error(f"Failed to initialize Incident Sage: {e}")
            self.incident_sage = None
            
        try:
            if not hasattr(self, 'rag_sage'):
                from libs.rag_manager import RagManager
                self.rag_sage = RagManager()
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG Sage: {e}")
            self.rag_sage = None