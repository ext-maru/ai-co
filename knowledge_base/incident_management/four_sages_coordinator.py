#!/usr/bin/env python3
"""
Four Sages Coordinator - 4賢者統合協調システム
ナレッジ賢者、タスク賢者、インシデント賢者、RAG賢者の完全統合
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class SageType(Enum):
    """賢者タイプ"""

    KNOWLEDGE = "knowledge_sage"  # ナレッジ賢者
    TASK = "task_oracle"  # タスク賢者
    INCIDENT = "crisis_sage"  # インシデント賢者
    RAG = "search_mystic"  # RAG賢者


class SageMessage:
    """賢者間メッセージ"""

    def __init__(
        self,
        sender: SageType,
        recipient: SageType,
        message_type: str,
        content: Dict,
        session_id: str = None,
    ):
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.recipient = recipient
        self.message_type = message_type
        self.content = content
        self.session_id = session_id or str(uuid.uuid4())
        self.timestamp = datetime.now().isoformat()
        self.status = "pending"


class SageCouncilSession:
    """賢者会議セッション"""

    def __init__(self, session_id: str, topic: str, priority: str = "medium"):
        self.session_id = session_id
        self.topic = topic
        self.priority = priority
        self.start_time = datetime.now().isoformat()
        self.end_time = None
        self.participants = []
        self.messages = []
        self.decisions = []
        self.status = "active"
        self.final_outcome = None


class FourSagesCoordinator:
    """4賢者統合協調システム"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_co_path = Path("/home/aicompany/ai_co")

        # 賢者エージェント参照
        self.sages = {}
        self.active_sessions = {}
        self.session_history = []
        self.collaboration_patterns = {}

        # 通信チャンネル
        self.message_queue = asyncio.Queue()
        self.broadcast_channels = {sage_type: [] for sage_type in SageType}

        # 協調ルール
        self.collaboration_rules = self._load_collaboration_rules()

        self.logger.info("🧙‍♂️ FourSagesCoordinator initialized - 4賢者協調システム起動")

    def _load_collaboration_rules(self) -> Dict:
        """協調ルール読み込み"""
        return {
            "emergency_response": {
                "trigger": ["critical_incident", "system_failure"],
                "participants": [SageType.INCIDENT, SageType.KNOWLEDGE, SageType.TASK],
                "response_time": 60,  # seconds
                "escalation_threshold": 300,
            },
            "proactive_optimization": {
                "trigger": ["performance_degradation", "resource_shortage"],
                "participants": [SageType.RAG, SageType.KNOWLEDGE, SageType.TASK],
                "response_time": 300,
                "collaboration_mode": "consensus",
            },
            "learning_synthesis": {
                "trigger": ["new_knowledge", "pattern_discovery"],
                "participants": [SageType.KNOWLEDGE, SageType.RAG, SageType.INCIDENT],
                "response_time": 600,
                "collaboration_mode": "knowledge_building",
            },
            "strategic_planning": {
                "trigger": ["planning_request", "resource_allocation"],
                "participants": [SageType.TASK, SageType.KNOWLEDGE, SageType.RAG],
                "response_time": 900,
                "collaboration_mode": "strategic",
            },
        }

    async def register_sage(self, sage_type: SageType, sage_instance: Any) -> bool:
        """賢者エージェント登録"""
        try:
            self.sages[sage_type] = sage_instance
            self.logger.info(f"🧙‍♂️ {sage_type.value} registered successfully")

            # 既存セッションに通知
            await self._notify_sage_availability(sage_type)

            return True
        except Exception as e:
            self.logger.error(f"Failed to register {sage_type.value}: {str(e)}")
            return False

    async def initiate_council_session(
        self, topic: str, priority: str = "medium", participants: List[SageType] = None
    ) -> str:
        """賢者会議セッション開始"""
        session_id = str(uuid.uuid4())

        if participants is None:
            participants = list(SageType)  # 全賢者参加

        session = SageCouncilSession(session_id, topic, priority)
        session.participants = participants

        self.active_sessions[session_id] = session

        self.logger.info(f"🏛️ Council session started: {topic} (ID: {session_id})")

        # 参加者に通知
        for participant in participants:
            if participant in self.sages:
                await self._send_session_invite(participant, session)

        return session_id

    async def handle_emergency_response(self, incident_data: Dict) -> Dict:
        """緊急対応協調"""
        session_id = await self.initiate_council_session(
            f"Emergency Response: {incident_data.get('title', 'Unknown Incident')}",
            priority="critical",
            participants=[
                SageType.INCIDENT,
                SageType.KNOWLEDGE,
                SageType.TASK,
                SageType.RAG,
            ],
        )

        emergency_response = {
            "session_id": session_id,
            "incident_data": incident_data,
            "start_time": datetime.now().isoformat(),
            "sage_responses": {},
            "coordinated_actions": [],
            "final_resolution": None,
        }

        try:
            # Phase 1: 各賢者からの初期評価
            sage_evaluations = await self._gather_emergency_evaluations(
                session_id, incident_data
            )
            emergency_response["sage_responses"] = sage_evaluations

            # Phase 2: 協調アクション計画
            action_plan = await self._create_coordinated_action_plan(
                sage_evaluations, incident_data
            )
            emergency_response["coordinated_actions"] = action_plan

            # Phase 3: 並行実行
            execution_results = await self._execute_coordinated_actions(action_plan)
            emergency_response["execution_results"] = execution_results

            # Phase 4: 結果統合と学習
            final_resolution = await self._synthesize_resolution(
                execution_results, incident_data
            )
            emergency_response["final_resolution"] = final_resolution

        except Exception as e:
            emergency_response["error"] = str(e)
            self.logger.error(f"Emergency response failed: {str(e)}")

        emergency_response["end_time"] = datetime.now().isoformat()

        # セッション終了
        await self._end_council_session(session_id, emergency_response)

        return emergency_response

    async def _gather_emergency_evaluations(
        self, session_id: str, incident_data: Dict
    ) -> Dict:
        """緊急時評価収集"""
        evaluations = {}

        # 各賢者に並行して評価を要求
        evaluation_tasks = []

        if SageType.INCIDENT in self.sages:
            evaluation_tasks.append(
                self._request_incident_evaluation(session_id, incident_data)
            )

        if SageType.KNOWLEDGE in self.sages:
            evaluation_tasks.append(
                self._request_knowledge_evaluation(session_id, incident_data)
            )

        if SageType.TASK in self.sages:
            evaluation_tasks.append(
                self._request_task_evaluation(session_id, incident_data)
            )

        if SageType.RAG in self.sages:
            evaluation_tasks.append(
                self._request_rag_evaluation(session_id, incident_data)
            )

        # 並行実行（タイムアウト付き）
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*evaluation_tasks, return_exceptions=True), timeout=60
            )

            for i, result in enumerate(results):
                if not isinstance(result, Exception):
                    sage_type = [
                        SageType.INCIDENT,
                        SageType.KNOWLEDGE,
                        SageType.TASK,
                        SageType.RAG,
                    ][i]
                    evaluations[sage_type.value] = result

        except asyncio.TimeoutError:
            self.logger.warning("Emergency evaluation timeout")

        return evaluations

    async def _request_incident_evaluation(
        self, session_id: str, incident_data: Dict
    ) -> Dict:
        """インシデント賢者評価要求"""
        try:
            incident_sage = self.sages[SageType.INCIDENT]

            # 自動修復可能性評価
            auto_fix_assessment = getattr(
                incident_sage, "assess_auto_fix_probability", None
            )
            if auto_fix_assessment:
                auto_fix_prob = auto_fix_assessment(incident_data)
            else:
                auto_fix_prob = 0.5

            # 類似インシデント検索
            similar_incidents = getattr(incident_sage, "search_similar_incidents", None)
            if similar_incidents:
                similar = similar_incidents(incident_data.get("description", ""), 3)
            else:
                similar = []

            return {
                "sage_type": "crisis_sage",
                "auto_fix_probability": auto_fix_prob,
                "similar_incidents": similar,
                "immediate_response_needed": incident_data.get("priority")
                in ["critical", "high"],
                "estimated_resolution_time": self._estimate_resolution_time(
                    incident_data
                ),
                "confidence": 0.9,
            }

        except Exception as e:
            return {"sage_type": "crisis_sage", "error": str(e), "confidence": 0.1}

    async def _request_knowledge_evaluation(
        self, session_id: str, incident_data: Dict
    ) -> Dict:
        """ナレッジ賢者評価要求"""
        try:
            # ナレッジベースから関連情報検索
            kb_path = self.ai_co_path / "knowledge_base"
            relevant_docs = []

            keywords = incident_data.get("description", "").lower().split()

            for md_file in kb_path.rglob("*.md"):
                try:
                    with open(md_file, "r") as f:
                        content = f.read().lower()
                        relevance = sum(1 for keyword in keywords if keyword in content)
                        if relevance > 0:
                            relevant_docs.append(
                                {"file": str(md_file.name), "relevance": relevance}
                            )
                except:
                    continue

            # 過去の成功パターン分析
            success_patterns = self._analyze_success_patterns(incident_data)

            return {
                "sage_type": "knowledge_sage",
                "relevant_documentation": sorted(
                    relevant_docs, key=lambda x: x["relevance"], reverse=True
                )[:3],
                "success_patterns": success_patterns,
                "recommended_approaches": self._extract_recommended_approaches(
                    relevant_docs
                ),
                "confidence": min(len(relevant_docs) * 0.2, 0.8),
            }

        except Exception as e:
            return {"sage_type": "knowledge_sage", "error": str(e), "confidence": 0.1}

    async def _request_task_evaluation(
        self, session_id: str, incident_data: Dict
    ) -> Dict:
        """タスク賢者評価要求"""
        try:
            # リソース可用性評価
            resource_availability = self._assess_resource_availability()

            # 優先度とスケジューリング
            priority_assessment = self._assess_priority_impact(incident_data)

            # 並行実行可能タスク
            parallel_tasks = self._identify_parallel_response_tasks(incident_data)

            return {
                "sage_type": "task_oracle",
                "resource_availability": resource_availability,
                "priority_assessment": priority_assessment,
                "parallel_tasks": parallel_tasks,
                "estimated_effort": self._estimate_response_effort(incident_data),
                "optimal_execution_order": self._determine_execution_order(
                    parallel_tasks
                ),
                "confidence": 0.8,
            }

        except Exception as e:
            return {"sage_type": "task_oracle", "error": str(e), "confidence": 0.1}

    async def _request_rag_evaluation(
        self, session_id: str, incident_data: Dict
    ) -> Dict:
        """RAG賢者評価要求"""
        try:
            # 関連情報検索
            search_query = f"{incident_data.get('category', '')} {incident_data.get('description', '')}"

            # 技術的解決策検索
            technical_solutions = await self._search_technical_solutions(search_query)

            # 外部ナレッジ統合
            external_references = await self._find_external_references(incident_data)

            # コンテキスト統合
            integrated_context = self._integrate_context(
                incident_data, technical_solutions
            )

            return {
                "sage_type": "search_mystic",
                "technical_solutions": technical_solutions,
                "external_references": external_references,
                "integrated_context": integrated_context,
                "search_confidence": min(len(technical_solutions) * 0.25, 0.9),
                "recommended_research": self._recommend_additional_research(
                    incident_data
                ),
                "confidence": 0.7,
            }

        except Exception as e:
            return {"sage_type": "search_mystic", "error": str(e), "confidence": 0.1}

    async def _create_coordinated_action_plan(
        self, evaluations: Dict, incident_data: Dict
    ) -> List[Dict]:
        """協調アクション計画作成"""
        action_plan = []

        # 各賢者の評価を統合
        overall_confidence = (
            sum(eval_data.get("confidence", 0) for eval_data in evaluations.values())
            / len(evaluations)
            if evaluations
            else 0
        )

        # 即座の対応が必要か判定
        immediate_response = any(
            eval_data.get("immediate_response_needed", False)
            for eval_data in evaluations.values()
        )

        if immediate_response:
            # 緊急対応アクション
            action_plan.extend(
                self._create_emergency_actions(evaluations, incident_data)
            )

        # 協調修復アクション
        if overall_confidence > 0.6:
            action_plan.extend(
                self._create_collaborative_fix_actions(evaluations, incident_data)
            )

        # 学習・改善アクション
        action_plan.extend(self._create_learning_actions(evaluations, incident_data))

        return action_plan

    def _create_emergency_actions(
        self, evaluations: Dict, incident_data: Dict
    ) -> List[Dict]:
        """緊急対応アクション作成"""
        actions = []

        # インシデント賢者の自動修復
        incident_eval = evaluations.get("crisis_sage", {})
        if incident_eval.get("auto_fix_probability", 0) > 0.7:
            actions.append(
                {
                    "type": "auto_fix",
                    "executor": "crisis_sage",
                    "priority": 1,
                    "timeout": 300,
                    "description": "Automated incident resolution",
                    "rollback_enabled": True,
                }
            )

        # タスク賢者のリソース確保
        task_eval = evaluations.get("task_oracle", {})
        if task_eval.get("resource_availability", {}).get(
            "critical_resources_available", True
        ):
            actions.append(
                {
                    "type": "resource_allocation",
                    "executor": "task_oracle",
                    "priority": 2,
                    "timeout": 120,
                    "description": "Allocate emergency resources",
                    "resources_needed": task_eval.get("estimated_effort", {}),
                }
            )

        return actions

    def _create_collaborative_fix_actions(
        self, evaluations: Dict, incident_data: Dict
    ) -> List[Dict]:
        """協調修復アクション作成"""
        actions = []

        # ナレッジベース検索結果に基づく対応
        knowledge_eval = evaluations.get("knowledge_sage", {})
        if knowledge_eval.get("success_patterns"):
            actions.append(
                {
                    "type": "pattern_based_fix",
                    "executor": "knowledge_sage",
                    "priority": 3,
                    "timeout": 600,
                    "description": "Apply known success patterns",
                    "patterns": knowledge_eval["success_patterns"],
                }
            )

        # RAG検索に基づく技術的解決
        rag_eval = evaluations.get("search_mystic", {})
        if rag_eval.get("technical_solutions"):
            actions.append(
                {
                    "type": "technical_solution",
                    "executor": "search_mystic",
                    "priority": 4,
                    "timeout": 900,
                    "description": "Apply technical solutions",
                    "solutions": rag_eval["technical_solutions"],
                }
            )

        return actions

    def _create_learning_actions(
        self, evaluations: Dict, incident_data: Dict
    ) -> List[Dict]:
        """学習アクション作成"""
        return [
            {
                "type": "knowledge_synthesis",
                "executor": "all_sages",
                "priority": 10,
                "timeout": 300,
                "description": "Synthesize learnings from incident response",
                "data_to_capture": {
                    "incident_patterns": True,
                    "solution_effectiveness": True,
                    "response_time_metrics": True,
                },
            }
        ]

    async def _execute_coordinated_actions(self, action_plan: List[Dict]) -> Dict:
        """協調アクション実行"""
        execution_results = {
            "start_time": datetime.now().isoformat(),
            "actions_executed": [],
            "successful_actions": [],
            "failed_actions": [],
            "overall_success": False,
        }

        # 優先度順にソート
        sorted_actions = sorted(action_plan, key=lambda x: x.get("priority", 999))

        for action in sorted_actions:
            action_id = str(uuid.uuid4())
            execution_results["actions_executed"].append(action_id)

            try:
                result = await self._execute_single_action(action)

                if result.get("success", False):
                    execution_results["successful_actions"].append(
                        {"action_id": action_id, "action": action, "result": result}
                    )
                else:
                    execution_results["failed_actions"].append(
                        {
                            "action_id": action_id,
                            "action": action,
                            "error": result.get("error", "Unknown error"),
                        }
                    )

            except Exception as e:
                execution_results["failed_actions"].append(
                    {"action_id": action_id, "action": action, "error": str(e)}
                )

        # 全体成功判定
        total_actions = len(action_plan)
        successful_actions = len(execution_results["successful_actions"])
        execution_results["overall_success"] = (
            successful_actions / total_actions >= 0.7 if total_actions > 0 else False
        )

        execution_results["end_time"] = datetime.now().isoformat()

        return execution_results

    async def _execute_single_action(self, action: Dict) -> Dict:
        """単一アクション実行"""
        executor = action.get("executor")
        action_type = action.get("type")
        timeout = action.get("timeout", 300)

        try:
            if executor == "crisis_sage" and action_type == "auto_fix":
                return await self._execute_auto_fix(action)
            elif executor == "task_oracle" and action_type == "resource_allocation":
                return await self._execute_resource_allocation(action)
            elif executor == "knowledge_sage" and action_type == "pattern_based_fix":
                return await self._execute_pattern_based_fix(action)
            elif executor == "search_mystic" and action_type == "technical_solution":
                return await self._execute_technical_solution(action)
            elif action_type == "knowledge_synthesis":
                return await self._execute_knowledge_synthesis(action)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type}",
                }

        except asyncio.TimeoutError:
            return {"success": False, "error": f"Action timeout after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _synthesize_resolution(
        self, execution_results: Dict, incident_data: Dict
    ) -> Dict:
        """解決策統合"""
        resolution = {
            "timestamp": datetime.now().isoformat(),
            "resolution_successful": execution_results.get("overall_success", False),
            "key_actions": [],
            "lessons_learned": [],
            "future_improvements": [],
            "effectiveness_score": 0.0,
        }

        # 成功したアクションから主要なものを抽出
        for successful_action in execution_results.get("successful_actions", []):
            action = successful_action["action"]
            if action.get("priority", 999) <= 5:  # 高優先度アクション
                resolution["key_actions"].append(
                    {
                        "type": action["type"],
                        "description": action["description"],
                        "effectiveness": successful_action["result"].get(
                            "effectiveness", 0.5
                        ),
                    }
                )

        # 学習ポイント抽出
        resolution["lessons_learned"] = self._extract_lessons_learned(
            execution_results, incident_data
        )

        # 改善提案
        resolution["future_improvements"] = self._suggest_improvements(
            execution_results, incident_data
        )

        # 効果スコア計算
        if resolution["resolution_successful"]:
            resolution["effectiveness_score"] = min(
                len(resolution["key_actions"]) * 0.3
                + len(resolution["lessons_learned"]) * 0.2,
                1.0,
            )

        return resolution

    # =============== ヘルパーメソッド ===============

    def _estimate_resolution_time(self, incident_data: Dict) -> int:
        """解決時間見積もり（分）"""
        category = incident_data.get("category", "unknown")
        priority = incident_data.get("priority", "medium")

        base_times = {"error": 30, "failure": 60, "security": 120, "performance": 45}

        priority_multipliers = {
            "critical": 0.5,  # 緊急時は迅速対応
            "high": 1.0,
            "medium": 1.5,
            "low": 2.0,
        }

        base_time = base_times.get(category, 45)
        multiplier = priority_multipliers.get(priority, 1.0)

        return int(base_time * multiplier)

    def _analyze_success_patterns(self, incident_data: Dict) -> List[Dict]:
        """成功パターン分析"""
        # 簡易実装
        return [
            {"pattern": "restart_services", "success_rate": 0.8},
            {"pattern": "clear_cache", "success_rate": 0.6},
            {"pattern": "resource_scaling", "success_rate": 0.7},
        ]

    def _extract_recommended_approaches(self, relevant_docs: List[Dict]) -> List[str]:
        """推奨アプローチ抽出"""
        approaches = []
        for doc in relevant_docs[:3]:
            if "troubleshooting" in doc["file"].lower():
                approaches.append("systematic_troubleshooting")
            elif "recovery" in doc["file"].lower():
                approaches.append("automated_recovery")
            elif "monitoring" in doc["file"].lower():
                approaches.append("enhanced_monitoring")

        return list(set(approaches))

    def _assess_resource_availability(self) -> Dict:
        """リソース可用性評価"""
        try:
            import psutil

            return {
                "cpu_available": psutil.cpu_percent() < 80,
                "memory_available": psutil.virtual_memory().percent < 80,
                "disk_available": psutil.disk_usage("/").percent < 90,
                "critical_resources_available": True,
            }
        except:
            return {"critical_resources_available": False}

    def _assess_priority_impact(self, incident_data: Dict) -> Dict:
        """優先度影響評価"""
        priority = incident_data.get("priority", "medium")
        category = incident_data.get("category", "unknown")

        impact_score = {"critical": 10, "high": 7, "medium": 4, "low": 2}.get(
            priority, 4
        )

        if category == "security":
            impact_score += 3

        return {
            "impact_score": min(impact_score, 10),
            "business_impact": "high" if impact_score > 7 else "medium",
            "user_impact": "severe" if impact_score > 8 else "moderate",
        }

    async def _search_technical_solutions(self, query: str) -> List[Dict]:
        """技術的解決策検索"""
        # 簡易実装
        return [
            {"solution": "service_restart", "confidence": 0.8},
            {"solution": "configuration_update", "confidence": 0.6},
            {"solution": "dependency_update", "confidence": 0.4},
        ]

    async def _find_external_references(self, incident_data: Dict) -> List[str]:
        """外部参照検索"""
        return [
            "System Documentation",
            "Best Practices Guide",
            "Troubleshooting Manual",
        ]

    # =============== 実行メソッド ===============

    async def _execute_auto_fix(self, action: Dict) -> Dict:
        """自動修復実行"""
        # CommonFixes との連携
        try:
            from .auto_fix.common_fixes import CommonFixes

            fixer = CommonFixes()

            # 簡易インシデントデータ作成
            incident_data = {
                "category": "error",
                "description": action.get("description", ""),
                "incident_id": "auto_fix_" + str(uuid.uuid4())[:8],
            }

            result = fixer.diagnose_and_fix(incident_data)

            return {
                "success": result.get("status") == "resolved",
                "effectiveness": 0.8 if result.get("successful_fixes") else 0.2,
                "details": result,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_resource_allocation(self, action: Dict) -> Dict:
        """リソース割り当て実行"""
        # 簡易実装
        await asyncio.sleep(1)  # シミュレーション
        return {"success": True, "effectiveness": 0.7}

    async def _execute_pattern_based_fix(self, action: Dict) -> Dict:
        """パターンベース修復実行"""
        patterns = action.get("patterns", [])
        successful_patterns = 0

        for pattern in patterns:
            if pattern.get("success_rate", 0) > 0.5:
                successful_patterns += 1

        success = successful_patterns > len(patterns) / 2

        return {
            "success": success,
            "effectiveness": successful_patterns / max(len(patterns), 1),
            "applied_patterns": successful_patterns,
        }

    async def _execute_technical_solution(self, action: Dict) -> Dict:
        """技術的解決策実行"""
        solutions = action.get("solutions", [])
        success_count = 0

        for solution in solutions:
            if solution.get("confidence", 0) > 0.6:
                success_count += 1

        return {
            "success": success_count > 0,
            "effectiveness": success_count / max(len(solutions), 1),
            "applied_solutions": success_count,
        }

    async def _execute_knowledge_synthesis(self, action: Dict) -> Dict:
        """知識統合実行"""
        # 学習データ記録
        synthesis_data = {
            "timestamp": datetime.now().isoformat(),
            "data_captured": action.get("data_to_capture", {}),
            "synthesis_successful": True,
        }

        # ナレッジベースに保存
        try:
            synthesis_file = (
                self.ai_co_path
                / "knowledge_base"
                / "incident_management"
                / "synthesis_log.json"
            )

            if synthesis_file.exists():
                with open(synthesis_file, "r") as f:
                    existing_data = json.load(f)
            else:
                existing_data = {"synthesis_sessions": []}

            existing_data["synthesis_sessions"].append(synthesis_data)

            with open(synthesis_file, "w") as f:
                json.dump(existing_data, f, indent=2)

            return {"success": True, "effectiveness": 0.9}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _extract_lessons_learned(
        self, execution_results: Dict, incident_data: Dict
    ) -> List[str]:
        """学習事項抽出"""
        lessons = []

        if execution_results.get("overall_success"):
            lessons.append("4賢者協調による迅速な問題解決を実現")

        successful_actions = execution_results.get("successful_actions", [])
        if successful_actions:
            lessons.append(f"{len(successful_actions)}の協調アクションが成功")

        failed_actions = execution_results.get("failed_actions", [])
        if failed_actions:
            lessons.append(f"{len(failed_actions)}のアクションで改善の余地を確認")

        return lessons

    def _suggest_improvements(
        self, execution_results: Dict, incident_data: Dict
    ) -> List[str]:
        """改善提案"""
        improvements = []

        if execution_results.get("failed_actions"):
            improvements.append("失敗したアクションのロバスト性向上")

        if not execution_results.get("overall_success"):
            improvements.append("賢者間の協調プロトコル改善")

        improvements.append("予防的監視の強化")
        improvements.append("自動修復パターンの拡充")

        return improvements

    # =============== ユーティリティメソッド ===============

    async def _notify_sage_availability(self, sage_type: SageType):
        """賢者可用性通知"""
        # 他の賢者に新しい賢者の参加を通知
        for other_sage_type, sage_instance in self.sages.items():
            if other_sage_type != sage_type:
                try:
                    notify_method = getattr(sage_instance, "on_sage_joined", None)
                    if notify_method:
                        await notify_method(sage_type)
                except:
                    pass

    async def _send_session_invite(
        self, participant: SageType, session: SageCouncilSession
    ):
        """セッション招待送信"""
        message = SageMessage(
            sender=SageType.INCIDENT,  # コーディネーターとして
            recipient=participant,
            message_type="session_invite",
            content={
                "session_id": session.session_id,
                "topic": session.topic,
                "priority": session.priority,
                "participants": [p.value for p in session.participants],
            },
            session_id=session.session_id,
        )

        await self.message_queue.put(message)

    async def _end_council_session(self, session_id: str, outcome: Dict):
        """会議セッション終了"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.end_time = datetime.now().isoformat()
            session.status = "completed"
            session.final_outcome = outcome

            # 履歴に移動
            self.session_history.append(session)
            del self.active_sessions[session_id]

            self.logger.info(f"🏛️ Council session ended: {session.topic}")

    def get_coordination_statistics(self) -> Dict:
        """協調統計取得"""
        total_sessions = len(self.session_history)
        successful_sessions = sum(
            1
            for session in self.session_history
            if session.final_outcome
            and session.final_outcome.get("overall_success", False)
        )

        return {
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "success_rate": successful_sessions / total_sessions
            if total_sessions > 0
            else 0,
            "active_sessions": len(self.active_sessions),
            "registered_sages": len(self.sages),
            "average_session_participants": sum(
                len(session.participants) for session in self.session_history
            )
            / max(total_sessions, 1),
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Four Sages Coordination System")
    parser.add_argument(
        "action", choices=["start", "status", "test"], help="Action to perform"
    )

    args = parser.parse_args()

    coordinator = FourSagesCoordinator()

    if args.action == "status":
        stats = coordinator.get_coordination_statistics()
        print(json.dumps(stats, indent=2))

    elif args.action == "test":
        # テスト用緊急対応シミュレーション
        async def test_emergency():
            test_incident = {
                "incident_id": "TEST-001",
                "category": "failure",
                "priority": "critical",
                "title": "Test Emergency Response",
                "description": "RabbitMQ connection failure test",
            }

            result = await coordinator.handle_emergency_response(test_incident)
            print(json.dumps(result, indent=2))

        asyncio.run(test_emergency())

    else:
        print("🧙‍♂️ Four Sages Coordinator ready for collaboration")


if __name__ == "__main__":
    main()
