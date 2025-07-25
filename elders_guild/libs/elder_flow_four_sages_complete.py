"""
Elder Flow Four Sages Complete - 4賢者統合システム

4賢者（Knowledge, Task, Incident, RAG）を統合し、
Elder Flowに対する包括的な助言を提供します。
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ElderFlowFourSagesComplete:
    """4賢者統合システム"""

    def __init__(self):
        """4賢者システムを初期化"""
        self.logger = logger
        self._init_sages()

    def _init_sages(self):
        """各賢者を初期化"""
        try:
            # 各賢者をインポート
            from libs.knowledge_sage import KnowledgeSage
            from libs.task_sage import TaskSage
            from libs.incident_sage import IncidentSage
            from libs.rag_manager import RagManager

            self.knowledge_sage = KnowledgeSage()
            self.task_sage = TaskSage()
            self.incident_sage = IncidentSage()
            self.rag_sage = RagManager()
            
            self.logger.info("🧙‍♂️ 4賢者システム初期化完了")
        except Exception as e:
            self.logger.error(f"賢者初期化エラー: {e}")
            # フォールバック実装を使用
            self._use_fallback_sages()

    def _use_fallback_sages(self):
        """フォールバック賢者を使用"""
        self.knowledge_sage = None
        self.task_sage = None
        self.incident_sage = None
        self.rag_sage = None
        self.logger.warning("⚠️ フォールバック賢者モードで動作中")

    async def consult_for_elder_flow(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elder Flow用の4賢者統合相談
        
        Args:
            request: リクエスト情報
                - task_description: タスクの説明
                - task_type: タスクタイプ
                - priority: 優先度
                - context: 追加コンテキスト
                
        Returns:
            Dict[str, Any]: 4賢者の統合助言
        """
        try:
            task_description = request.get("task_description", "")
            task_type = request.get("task_type", "general")
            priority = request.get("priority", "medium")
            context = request.get("context", {})

            self.logger.info(f"🏛️ 4賢者会議開始: {task_description[:50]}...")

            # 各賢者に並行して相談
            sage_tasks = []
            
            # Knowledge賢者への相談
            if self.knowledge_sage:
                sage_tasks.append(self._consult_knowledge_sage(task_description, context))
            else:
                sage_tasks.append(self._create_fallback_response("knowledge"))

            # Task賢者への相談
            if self.task_sage:
                sage_tasks.append(self._consult_task_sage(task_description, context))
            else:
                sage_tasks.append(self._create_fallback_response("task"))

            # Incident賢者への相談
            if self.incident_sage:
                sage_tasks.append(self._consult_incident_sage(task_description, context))
            else:
                sage_tasks.append(self._create_fallback_response("incident"))

            # RAG賢者への相談
            if self.rag_sage:
                sage_tasks.append(self._consult_rag_sage(task_description, context))
            else:
                sage_tasks.append(self._create_fallback_response("rag"))

            # 並行実行
            results = await asyncio.gather(*sage_tasks, return_exceptions=True)

            # 結果を整理
            individual_responses = {}
            consensus_advice = []
            errors = []

            sage_names = ["knowledge", "task", "incident", "rag"]
            for i, result in enumerate(results):
                sage_name = sage_names[i]
                if isinstance(result, Exception):
                    errors.append(f"{sage_name}: {str(result)}")
                    individual_responses[f"{sage_name}_sage"] = {
                        "status": "error",
                        "error": str(result)
                    }
                else:
                    individual_responses[f"{sage_name}_sage"] = result
                    if result.get("advice"):
                        consensus_advice.extend(result["advice"])

            # コンセンサスを形成
            consensus = self._form_consensus(consensus_advice)

            return {
                "status": "success",
                "individual_responses": individual_responses,
                "consensus": consensus,
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"4賢者会議エラー: {e}")
            return {
                "status": "error",
                "error": str(e),
                "individual_responses": {},
                "consensus": {"recommendations": ["エラーが発生しました。手動での対応を推奨します。"]}
            }

    async def _consult_knowledge_sage(self, task_description: str, context: Dict) -> Dict[str, Any]:
        """Knowledge賢者に相談"""
        try:
            response = await self.knowledge_sage.process_request({
                "type": "search",
                "query": task_description,
                "limit": 5
            })
            
            advice = []
            if response.get("entries"):
                advice.append("過去の類似事例が見つかりました。参考にしてください。")
                
            return {
                "status": "success",
                "sage": "knowledge",
                "advice": advice,
                "entries": response.get("entries", []),
                "confidence": 0.8
            }
        except Exception as e:
            raise Exception(f"Knowledge sage error: {e}")

    async def _consult_task_sage(self, task_description: str, context: Dict) -> Dict[str, Any]:
        """Task賢者に相談"""
        try:
            response = await self.task_sage.process_request({
                "type": "create_plan",
                "title": task_description,
                "description": context.get("issue_body", "")
            })
            
            advice = ["タスクの実行計画を立案しました。"]
            if response.get("plan"):
                advice.append("段階的な実装を推奨します。")
                
            return {
                "status": "success",
                "sage": "task",
                "advice": advice,
                "plan": response,
                "confidence": 0.85
            }
        except Exception as e:
            raise Exception(f"Task sage error: {e}")

    async def _consult_incident_sage(self, task_description: str, context: Dict) -> Dict[str, Any]:
        """Incident賢者に相談"""
        try:
            response = await self.incident_sage.process_request({
                "type": "evaluate_risk",
                "task": task_description,
                "context": str(context)
            })
            
            advice = []
            risk_level = response.get("risk_level", "unknown")
            if risk_level == "high":
                advice.append("高リスクのタスクです。慎重な実装を推奨します。")
            elif risk_level == "medium":
                advice.append("中程度のリスクがあります。テストを重視してください。")
            else:
                advice.append("低リスクのタスクです。標準的な実装で問題ありません。")
                
            return {
                "status": "success",
                "sage": "incident",
                "advice": advice,
                "risk_assessment": response,
                "confidence": 0.9
            }
        except Exception as e:
            raise Exception(f"Incident sage error: {e}")

    async def _consult_rag_sage(self, task_description: str, context: Dict) -> Dict[str, Any]:
        """RAG賢者に相談"""
        try:
            response = await self.rag_sage.process_request({
                "type": "search",
                "query": f"how to implement: {task_description}",
                "max_results": 3
            })
            
            advice = []
            if response.get("results"):
                advice.append("関連する実装パターンが見つかりました。")
                advice.append("既存のコードベースとの整合性を保ってください。")
            else:
                advice.append("新規実装となります。設計ドキュメントの作成を推奨します。")
                
            return {
                "status": "success",
                "sage": "rag",
                "advice": advice,
                "search_results": response.get("results", []),
                "confidence": 0.75
            }
        except Exception as e:
            raise Exception(f"RAG sage error: {e}")

    async def _create_fallback_response(self, sage_type: str) -> Dict[str, Any]:
        """フォールバック応答を生成"""
        fallback_advice = {
            "knowledge": ["過去の知見を参考にしてください。"],
            "task": ["段階的な実装を推奨します。"],
            "incident": ["リスク評価を行い、慎重に進めてください。"],
            "rag": ["既存コードとの整合性を確認してください。"]
        }
        
        return {
            "status": "fallback",
            "sage": sage_type,
            "advice": fallback_advice.get(sage_type, ["標準的な実装を推奨します。"]),
            "confidence": 0.5
        }

    def _form_consensus(self, all_advice: List[str]) -> Dict[str, Any]:
        """4賢者のコンセンサスを形成"""
        # 重複を除去
        unique_advice = list(set(all_advice))
        
        # 優先度付け（簡易版）
        prioritized = []
        high_priority_keywords = ["リスク", "慎重", "テスト", "設計"]
        medium_priority_keywords = ["推奨", "確認", "参考"]
        
        for advice in unique_advice:
            if any(keyword in advice for keyword in high_priority_keywords):
                prioritized.insert(0, advice)  # 高優先度は先頭に
            elif any(keyword in advice for keyword in medium_priority_keywords):
                prioritized.append(advice)  # 中優先度は末尾に
            else:
                prioritized.append(advice)  # その他も末尾に
        
        return {
            "recommendations": prioritized[:5],  # 最大5つの推奨事項
            "consensus_level": "high" if len(unique_advice) > 3 else "medium",
            "total_advice_count": len(all_advice)
        }


# 互換性のための関数
def setup(*args, **kwargs):
    """セットアップ関数"""
    logger.info("🧙‍♂️ 4賢者統合システムセットアップ")
    return ElderFlowFourSagesComplete()


def main(*args, **kwargs):
    """メイン関数"""
    logger.info("🧙‍♂️ 4賢者統合システム実行")
    four_sages = ElderFlowFourSagesComplete()
    return four_sages


# Export
__all__ = ["ElderFlowFourSagesComplete", "setup", "main"]