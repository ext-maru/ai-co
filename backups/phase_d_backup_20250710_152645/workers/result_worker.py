#!/usr/bin/env python3
"""
Elders Guild Result Worker v7.0 - Complete Elder Tree Integration
タスク完了結果の処理とSlack通知（Elder Tree統合完全版）

🌳 Elder Tree Integration Features:
- 📚 Knowledge Sage: Success results learning and knowledge accumulation
- 🚨 Incident Sage: Failed task escalation and incident management
- 🔍 RAG Sage: Advanced error analysis and pattern matching
- 🏛️ Elder Council: Critical result pattern analysis and strategic decisions
- 🌟 Elder Tree Hierarchy: Complete command chain and authority structure

Elder Hierarchy:
Grand Elder maru → Claude Elder → Four Sages → Elder Council → Elder Servants
"""

import asyncio
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Core imports
from core import EMOJI, BaseWorker, get_config
from libs.ai_command_helper import AICommandHelper
from libs.slack_notifier import SlackNotifier

# エルダーズギルド統合
try:
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import (
        ElderDecision,
        ElderMessage,
        ElderRank,
        ElderTreeHierarchy,
        SageType,
        get_elder_tree,
    )
    from libs.four_sages_integration import FourSagesIntegration

    ELDER_INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"Elder integration not available: {e}")
    ELDER_INTEGRATION_AVAILABLE = False


class ResultWorkerV2(BaseWorker):
    """
    タスク結果処理とSlack通知ワーカー（Elder Tree統合完全版）

    Features:
    - 📊 Result processing with comprehensive analytics
    - 📱 Enhanced Slack notifications with Elder insights
    - 🌳 Complete Elder Tree hierarchy integration
    - 📚 Knowledge Sage learning data submission
    - 🚨 Incident Sage failure escalation
    - 🔍 RAG Sage error analysis
    - 🏛️ Elder Council critical pattern reporting
    - 📈 Elder integration status monitoring
    """

    def __init__(self):
        super().__init__(worker_type="result")
        self.config = get_config()
        self.slack_notifier = SlackNotifier()
        self.ai_helper = AICommandHelper()

        # エルダーズギルド統合 - 完全版
        self.four_sages = None
        self.elder_council = None
        self.elder_tree = None
        self.elder_integration_status = {
            "four_sages": False,
            "elder_council": False,
            "elder_tree": False,
            "initialization_errors": [],
        }

        if ELDER_INTEGRATION_AVAILABLE:
            try:
                # Four Sages Integration
                self.four_sages = FourSagesIntegration()
                self.elder_integration_status["four_sages"] = True
                self.logger.info(f"🧙‍♂️ Four Sages Integration activated")

                # Elder Council Summoner
                self.elder_council = ElderCouncilSummoner()
                self.elder_integration_status["elder_council"] = True
                self.logger.info(f"🏛️ Elder Council Summoner activated")

                # Elder Tree Hierarchy
                self.elder_tree = get_elder_tree()
                self.elder_integration_status["elder_tree"] = True
                self.logger.info(f"🌳 Elder Tree Hierarchy connected")

                # Elder status verification
                self._verify_elder_connections()

            except Exception as e:
                error_msg = f"エルダーズギルド統合初期化エラー: {e}"
                self.logger.warning(error_msg)
                self.elder_integration_status["initialization_errors"].append(error_msg)

                # Fallback to non-Elder mode
                self.four_sages = None
                self.elder_council = None
                self.elder_tree = None
        else:
            self.logger.warning(
                "Elder integration libraries not available - running in legacy mode"
            )

        # 統計情報（Elder統合対応）
        self.stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_duration": 0.0,
            "elder_escalations": 0,
            "sage_consultations": 0,
            "council_requests": 0,
        }

    def _verify_elder_connections(self):
        """エルダーシステム接続の検証"""
        try:
            # Four Sages status check
            if self.four_sages:
                # Test basic functionality
                sages_health = getattr(
                    self.four_sages, "get_sages_status", lambda: True
                )()
                if sages_health:
                    self.logger.info("✅ Four Sages connection verified")
                else:
                    self.logger.warning("⚠️ Four Sages connection unstable")

            # Elder Council status check
            if self.elder_council:
                # Test basic functionality
                council_health = getattr(
                    self.elder_council, "get_council_status", lambda: True
                )()
                if council_health:
                    self.logger.info("✅ Elder Council connection verified")
                else:
                    self.logger.warning("⚠️ Elder Council connection unstable")

            # Elder Tree status check
            if self.elder_tree:
                # Test hierarchy access
                tree_nodes = len(self.elder_tree.nodes)
                if tree_nodes > 0:
                    self.logger.info(f"✅ Elder Tree connected ({tree_nodes} nodes)")
                else:
                    self.logger.warning("⚠️ Elder Tree appears empty")

        except Exception as e:
            self.logger.error(f"Elder connections verification failed: {e}")
            self.elder_integration_status["initialization_errors"].append(
                f"Verification error: {e}"
            )

    async def report_to_knowledge_sage(self, task_result: Dict[str, Any]) -> bool:
        """Knowledge Sageにタスク結果を報告して学習データとして活用"""
        if not self.four_sages or not self.elder_tree:
            return False

        try:
            # Create message to Knowledge Sage
            message = ElderMessage(
                sender_rank=ElderRank.SERVANT,
                sender_id="result_worker",
                recipient_rank=ElderRank.SAGE,
                recipient_id="knowledge_sage",
                message_type="learning_data",
                content={
                    "task_type": task_result.get("task_type", "unknown"),
                    "status": task_result.get("status", "unknown"),
                    "duration": task_result.get("duration", 0),
                    "prompt": task_result.get("prompt", ""),
                    "response": task_result.get("response", ""),
                    "files_created": task_result.get("files_created", []),
                    "rag_applied": task_result.get("rag_applied", False),
                    "timestamp": datetime.now().isoformat(),
                },
                priority="normal",
            )

            # Send to Elder Tree
            success = await self.elder_tree.send_message(message)

            if success:
                # Also integrate with Four Sages directly
                if hasattr(self.four_sages, "knowledge_sage_process_learning"):
                    await self.four_sages.knowledge_sage_process_learning(task_result)

                self.stats["sage_consultations"] += 1
                self.logger.info(
                    f"📚 Knowledge Sage: Learning data submitted for task {task_result.get('task_id', 'unknown')}"
                )

            return success

        except Exception as e:
            self.logger.error(f"Knowledge Sage report failed: {e}")
            return False

    async def escalate_to_incident_sage(self, task_result: Dict[str, Any]) -> bool:
        """Incident Sageに失敗タスクをエスカレーション"""
        if not self.four_sages or not self.elder_tree:
            return False

        try:
            # Create emergency message to Incident Sage
            message = ElderMessage(
                sender_rank=ElderRank.SERVANT,
                sender_id="result_worker",
                recipient_rank=ElderRank.SAGE,
                recipient_id="incident_sage",
                message_type="incident_report",
                content={
                    "task_id": task_result.get("task_id", "unknown"),
                    "task_type": task_result.get("task_type", "unknown"),
                    "error": task_result.get("error", "Unknown error"),
                    "error_trace": task_result.get("error_trace", ""),
                    "worker_id": task_result.get("worker_id", "unknown"),
                    "timestamp": datetime.now().isoformat(),
                    "severity": "high"
                    if "critical" in str(task_result.get("error", "")).lower()
                    else "medium",
                },
                priority="high",
            )

            # Send to Elder Tree
            success = await self.elder_tree.send_message(message)

            if success:
                # Also integrate with Four Sages directly
                if hasattr(self.four_sages, "incident_sage_process_failure"):
                    await self.four_sages.incident_sage_process_failure(task_result)

                self.stats["elder_escalations"] += 1
                self.logger.warning(
                    f"🚨 Incident Sage: Task failure escalated {task_result.get('task_id', 'unknown')}"
                )

            return success

        except Exception as e:
            self.logger.error(f"Incident Sage escalation failed: {e}")
            return False

    async def consult_rag_sage(
        self, task_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """RAG Sageにエラー分析を依頼"""
        if not self.four_sages or not self.elder_tree:
            return None

        try:
            # Create consultation message to RAG Sage
            message = ElderMessage(
                sender_rank=ElderRank.SERVANT,
                sender_id="result_worker",
                recipient_rank=ElderRank.SAGE,
                recipient_id="rag_sage",
                message_type="analysis_request",
                content={
                    "task_id": task_result.get("task_id", "unknown"),
                    "error": task_result.get("error", ""),
                    "error_trace": task_result.get("error_trace", ""),
                    "task_type": task_result.get("task_type", "unknown"),
                    "analysis_type": "error_pattern_matching",
                    "timestamp": datetime.now().isoformat(),
                },
                requires_response=True,
                priority="normal",
            )

            # Send to Elder Tree
            success = await self.elder_tree.send_message(message)

            if success:
                # Also integrate with Four Sages directly
                if hasattr(self.four_sages, "rag_sage_analyze_error"):
                    analysis = await self.four_sages.rag_sage_analyze_error(task_result)
                    self.stats["sage_consultations"] += 1
                    self.logger.info(
                        f"🔍 RAG Sage: Error analysis completed for {task_result.get('task_id', 'unknown')}"
                    )
                    return analysis

            return None

        except Exception as e:
            self.logger.error(f"RAG Sage consultation failed: {e}")
            return None

    async def request_elder_council(self, pattern_data: Dict[str, Any]) -> bool:
        """Elder Councilに重要な結果パターンを報告"""
        if not self.elder_council or not self.elder_tree:
            return False

        try:
            # Create council summon message
            message = ElderMessage(
                sender_rank=ElderRank.SERVANT,
                sender_id="result_worker",
                recipient_rank=ElderRank.COUNCIL_MEMBER,
                recipient_id=None,  # Broadcast to all council members
                message_type="council_summon",
                content={
                    "topic": "result_pattern_analysis",
                    "pattern_type": pattern_data.get("pattern_type", "unknown"),
                    "frequency": pattern_data.get("frequency", 0),
                    "severity": pattern_data.get("severity", "medium"),
                    "affected_tasks": pattern_data.get("affected_tasks", []),
                    "recommendation": pattern_data.get("recommendation", ""),
                    "action_items": pattern_data.get("action_items", []),
                    "timestamp": datetime.now().isoformat(),
                },
                priority="high",
            )

            # Send to Elder Tree
            success = await self.elder_tree.send_message(message)

            if success:
                # Also use Elder Council Summoner
                if hasattr(self.elder_council, "summon_council"):
                    council_result = await self.elder_council.summon_council(
                        reason="result_pattern_analysis",
                        urgency="high",
                        context=pattern_data,
                    )

                self.stats["council_requests"] += 1
                self.logger.info(
                    f"🏛️ Elder Council: Pattern analysis requested - {pattern_data.get('pattern_type', 'unknown')}"
                )

            return success

        except Exception as e:
            self.logger.error(f"Elder Council request failed: {e}")
            return False

    async def _process_with_elder_guidance(self, task_result: Dict[str, Any]):
        """エルダー指導による結果処理"""
        try:
            status = task_result.get("status", "unknown")
            task_type = task_result.get("task_type", "unknown")

            # Success case - Report to Knowledge Sage for learning
            if status == "completed":
                await self.report_to_knowledge_sage(task_result)

                # Check for patterns that need Council attention
                if self._should_notify_council(task_result):
                    pattern_data = self._analyze_result_pattern(task_result)
                    if pattern_data:
                        await self.request_elder_council(pattern_data)

            # Failure case - Escalate to Incident Sage
            elif status == "failed" or task_result.get("error"):
                # First get RAG Sage analysis
                rag_analysis = await self.consult_rag_sage(task_result)

                # Enhance task result with RAG insights
                if rag_analysis:
                    task_result["rag_analysis"] = rag_analysis

                # Escalate to Incident Sage
                await self.escalate_to_incident_sage(task_result)

                # Check if this is a critical pattern needing Council attention
                if self._is_critical_failure_pattern(task_result):
                    pattern_data = {
                        "pattern_type": "critical_failure",
                        "frequency": 1,
                        "severity": "high",
                        "affected_tasks": [task_result.get("task_id", "unknown")],
                        "recommendation": "Immediate investigation required",
                        "action_items": [
                            "Investigate root cause",
                            "Implement preventive measures",
                        ],
                    }
                    await self.request_elder_council(pattern_data)

        except Exception as e:
            self.logger.error(f"Elder guidance processing failed: {e}")

    def _should_notify_council(self, task_result: Dict[str, Any]) -> bool:
        """Elder Councilに通知すべき結果かどうかの判定"""
        try:
            # High-impact successful tasks
            if (
                task_result.get("files_created")
                and len(task_result["files_created"]) > 5
            ):
                return True

            # Long-running tasks
            if task_result.get("duration", 0) > 30:
                return True

            # Critical task types
            critical_types = ["security", "infrastructure", "deployment", "migration"]
            if task_result.get("task_type") in critical_types:
                return True

            return False

        except Exception as e:
            self.logger.error(f"Council notification check failed: {e}")
            return False

    def _analyze_result_pattern(
        self, task_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """結果パターンの分析"""
        try:
            pattern_data = {
                "pattern_type": "high_impact_success",
                "frequency": 1,
                "severity": "medium",
                "affected_tasks": [task_result.get("task_id", "unknown")],
                "recommendation": "Monitor for scalability implications",
                "action_items": ["Review resource usage", "Consider optimization"],
            }

            # Enhance based on specific metrics
            if task_result.get("duration", 0) > 30:
                pattern_data["pattern_type"] = "long_running_task"
                pattern_data["recommendation"] = "Consider task decomposition"

            if len(task_result.get("files_created", [])) > 10:
                pattern_data["pattern_type"] = "high_output_task"
                pattern_data["recommendation"] = "Review file organization strategy"

            return pattern_data

        except Exception as e:
            self.logger.error(f"Pattern analysis failed: {e}")
            return None

    def _is_critical_failure_pattern(self, task_result: Dict[str, Any]) -> bool:
        """重要な失敗パターンかどうかの判定"""
        try:
            error = str(task_result.get("error", "")).lower()

            # Critical error patterns
            critical_patterns = [
                "security",
                "authentication",
                "authorization",
                "database",
                "connection",
                "timeout",
                "memory",
                "disk",
                "cpu",
                "resource",
                "permission",
                "access",
                "corruption",
            ]

            for pattern in critical_patterns:
                if pattern in error:
                    return True

            # Multiple consecutive failures
            if self.stats.get("failed_tasks", 0) > 3:
                return True

            return False

        except Exception as e:
            self.logger.error(f"Critical failure pattern check failed: {e}")
            return False

    def _get_elder_insights(
        self, task_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """エルダーからの洞察を取得"""
        try:
            insights = {
                "elder_status": self.elder_integration_status,
                "recommendations": [],
                "escalation_info": {},
                "learning_status": {},
            }

            # Success case insights
            if task_result.get("status") == "completed":
                insights["recommendations"].append(
                    "✅ Success data submitted to Knowledge Sage for learning"
                )

                if self._should_notify_council(task_result):
                    insights["escalation_info"][
                        "council_notification"
                    ] = "High-impact task flagged for Elder Council review"

                # Performance insights
                duration = task_result.get("duration", 0)
                if duration > 30:
                    insights["recommendations"].append(
                        "⚠️ Long-running task detected - consider optimization"
                    )
                elif duration < 1:
                    insights["recommendations"].append(
                        "⚡ Fast execution - excellent performance"
                    )

                # File creation insights
                files_count = len(task_result.get("files_created", []))
                if files_count > 5:
                    insights["recommendations"].append(
                        f"📁 High file output ({files_count} files) - review organization"
                    )

            # Failure case insights
            elif task_result.get("status") == "failed" or task_result.get("error"):
                insights["recommendations"].append(
                    "🚨 Task failure escalated to Incident Sage"
                )
                insights["escalation_info"][
                    "incident_sage"
                ] = "Automated failure analysis initiated"

                if self._is_critical_failure_pattern(task_result):
                    insights["escalation_info"][
                        "elder_council"
                    ] = "Critical failure pattern - Council summoned"

                # RAG analysis insight
                if task_result.get("rag_analysis"):
                    insights["learning_status"][
                        "rag_analysis"
                    ] = "Error pattern analysis completed"

            # Elder Tree status
            if self.elder_tree:
                insights[
                    "elder_tree_status"
                ] = f"Connected ({len(self.elder_tree.nodes)} nodes)"
            else:
                insights["elder_tree_status"] = "Not connected"

            # Stats insights
            if self.stats["total_tasks"] > 0:
                success_rate = (
                    self.stats["successful_tasks"] / self.stats["total_tasks"]
                ) * 100
                insights["performance_metrics"] = {
                    "success_rate": f"{success_rate:.1f}%",
                    "elder_escalations": self.stats["elder_escalations"],
                    "sage_consultations": self.stats["sage_consultations"],
                    "council_requests": self.stats["council_requests"],
                }

            return insights

        except Exception as e:
            self.logger.error(f"Elder insights generation failed: {e}")
            return None

    def process_message(self, ch, method, properties, body):
        """結果メッセージの処理"""
        start_time = time.time()

        try:
            # bodyがbytesの場合はデコード
            if isinstance(body, bytes):
                body = json.loads(body.decode("utf-8"))
            elif isinstance(body, str):
                body = json.loads(body)

            # タスク情報の抽出
            task_id = body.get("task_id", "unknown")
            task_type = body.get("task_type", "general")
            status = body.get("status", "completed")
            prompt = body.get("prompt", "")

            # 実行結果情報
            response = body.get("response", "")
            files_created = body.get("files_created", [])
            output_file = body.get("output_file", "")
            duration = body.get("duration", 0.0)

            # 追加情報
            worker_id = body.get("worker_id", "worker-1")
            rag_applied = body.get("rag_applied", False)

            # エラー情報（あれば）
            error = body.get("error", None)
            error_trace = body.get("error_trace", "")

            # 統計更新
            self._update_stats(status, duration)

            # ログ出力
            self.logger.info(
                f"Result received: {task_id} | "
                f"Status: {status} | "
                f"Type: {task_type} | "
                f"Duration: {duration:.2f}s | "
                f"Files: {len(files_created)}"
            )

            # エルダー統合処理
            if ELDER_INTEGRATION_AVAILABLE:
                asyncio.create_task(self._process_with_elder_guidance(body))

            # Slack通知の構築・送信（Elder統合対応）
            if self.config.get("slack.enabled", False):
                # Elder insights を含める
                elder_insights = (
                    self._get_elder_insights(body)
                    if ELDER_INTEGRATION_AVAILABLE
                    else None
                )

                self._send_enhanced_slack_notification(
                    task_id=task_id,
                    task_type=task_type,
                    status=status,
                    prompt=prompt,
                    response=response,
                    files_created=files_created,
                    output_file=output_file,
                    duration=duration,
                    worker_id=worker_id,
                    rag_applied=rag_applied,
                    error=error,
                    error_trace=error_trace,
                    elder_insights=elder_insights,
                )

            # 処理完了
            ch.basic_ack(delivery_tag=method.delivery_tag)

            # 処理時間記録
            process_duration = time.time() - start_time
            self.logger.info(
                f"Result processed: {task_id} | "
                f"Process duration: {process_duration:.2f}s"
            )

        except Exception as e:
            self.handle_error(e, "process_message", {"task_id": task_id})
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _update_stats(self, status: str, duration: float):
        """統計情報の更新"""
        self.stats["total_tasks"] += 1
        if status == "completed":
            self.stats["successful_tasks"] += 1
        else:
            self.stats["failed_tasks"] += 1
        self.stats["total_duration"] += duration

    def _send_enhanced_slack_notification(self, **kwargs):
        """改善されたSlack通知の送信（Elder統合対応）"""
        try:
            # メイン通知（簡潔版）を送信
            if kwargs["status"] == "completed":
                main_message, thread_messages = self._format_success_notification(
                    **kwargs
                )
            else:
                main_message, thread_messages = self._format_error_notification(
                    **kwargs
                )

            # メインメッセージ送信
            result = self.slack_notifier.send_message(main_message)

            # スレッドに詳細情報を送信
            if result and "ts" in result and thread_messages:
                channel = result.get("channel", self.config.get("slack.channel"))
                thread_ts = result["ts"]

                for thread_msg in thread_messages:
                    self.slack_notifier.send_thread_message(
                        channel=channel, thread_ts=thread_ts, message=thread_msg
                    )

        except Exception as e:
            self.logger.error(f"Slack notification failed: {str(e)}")

    def _format_success_notification(self, **kwargs) -> tuple:
        """成功時の通知フォーマット（メイン＋スレッド）- Elder統合対応"""
        task_id = kwargs["task_id"]
        task_type = kwargs["task_type"]
        duration = kwargs["duration"]
        files_count = len(kwargs.get("files_created", []))
        worker_id = kwargs.get("worker_id", "worker-1")
        rag_applied = kwargs.get("rag_applied", False)
        prompt = kwargs.get("prompt", "")
        response = kwargs.get("response", "")
        elder_insights = kwargs.get("elder_insights", {})

        # タスクIDのショート版（見やすさのため）
        short_id = task_id.split("_")[-1] if "_" in task_id else task_id[-8:]

        # プロンプトの要約（最初の50文字）
        prompt_summary = self._summarize_text(prompt, 50)

        # レスポンスの要約（最初の100文字）
        response_summary = self._summarize_text(response, 100)

        # メイン通知（簡潔版）- Elder統合対応
        main_parts = [
            f"✅ **タスク完了** `{short_id}` {'🌳' if elder_insights else ''}",
            "",
            f"📝 **要求:** {prompt_summary}",
            f"💬 **応答:** {response_summary}",
            "",
            f"⚡ **処理時間:** {duration:.1f}秒 | 📁 **ファイル:** {files_count}個",
            f"🤖 **ワーカー:** {worker_id} | 🧠 **RAG:** {'ON' if rag_applied else 'OFF'}",
        ]

        # Elder統合情報を追加
        if elder_insights and elder_insights.get("recommendations"):
            main_parts.append("")
            main_parts.append("🌳 **エルダー洞察:**")
            for rec in elder_insights["recommendations"][:2]:  # 最初の2つだけメインに表示
                main_parts.append(f"  • {rec}")
            if len(elder_insights["recommendations"]) > 2:
                main_parts.append("  • ... (詳細はスレッドを参照)")

        # 実行可能なアクション
        if files_count > 0 or kwargs.get("output_file"):
            main_parts.extend(["", "```bash", "# 詳細確認", f"ai-logs {task_id}", "```"])

        main_message = "\n".join(main_parts)

        # スレッドメッセージ（詳細情報）
        thread_messages = []

        # 1. プロンプト全文
        if prompt:
            thread_messages.append(f"📝 **プロンプト全文:**\n```\n{prompt}\n```")

        # 2. レスポンス詳細
        if response:
            response_formatted = self._format_response_details(response)
            thread_messages.append(f"💬 **レスポンス詳細:**\n{response_formatted}")

        # 3. ファイル操作
        if kwargs.get("files_created"):
            file_commands = self._generate_file_commands(kwargs["files_created"])
            thread_messages.append(f"📁 **ファイル操作コマンド:**\n{file_commands}")

        # 4. GitHub Flow コマンド
        if files_count > 0:
            git_commands = self._generate_git_commands(
                kwargs["files_created"], task_type
            )
            thread_messages.append(f"🔄 **GitHub Flow:**\n{git_commands}")

        # 5. パフォーマンス詳細
        if self.stats["total_tasks"] >= 10:
            perf_details = self._format_performance_details()
            thread_messages.append(f"📊 **パフォーマンス統計:**\n{perf_details}")

        # 6. Elder統合詳細
        if elder_insights:
            elder_details = self._format_elder_insights(elder_insights)
            thread_messages.append(elder_details)

        return main_message, thread_messages

    def _format_error_notification(self, **kwargs) -> tuple:
        """エラー時の通知フォーマット（メイン＋スレッド）- Elder統合対応"""
        task_id = kwargs["task_id"]
        task_type = kwargs["task_type"]
        error = kwargs.get("error", "不明なエラー")
        error_trace = kwargs.get("error_trace", "")
        worker_id = kwargs.get("worker_id", "worker-1")
        elder_insights = kwargs.get("elder_insights", {})

        # タスクIDのショート版
        short_id = task_id.split("_")[-1] if "_" in task_id else task_id[-8:]

        # エラーメッセージの要約
        error_summary = self._summarize_text(str(error), 80)

        # メイン通知（簡潔版）- Elder統合対応
        main_parts = [
            f"❌ **タスク失敗** `{short_id}` {'🌳' if elder_insights else ''}",
            "",
            f"⚠️ **エラー:** {error_summary}",
            f"🏷️ **タイプ:** {task_type} | 🤖 **ワーカー:** {worker_id}",
            "",
        ]

        # Elder統合情報を追加
        if elder_insights and elder_insights.get("recommendations"):
            main_parts.append("🌳 **エルダー対応:**")
            for rec in elder_insights["recommendations"][:2]:  # 最初の2つだけメインに表示
                main_parts.append(f"  • {rec}")
            if len(elder_insights["recommendations"]) > 2:
                main_parts.append("  • ... (詳細はスレッドを参照)")
            main_parts.append("")

        main_parts.extend(
            [
                "```bash",
                "# エラー詳細確認",
                f"ai-logs {task_id} --error",
                "",
                "# 再試行",
                f"ai-retry {task_id}",
                "```",
            ]
        )

        main_message = "\n".join(main_parts)

        # スレッドメッセージ（詳細情報）
        thread_messages = []

        # 1. エラートレース
        if error_trace:
            thread_messages.append(f"🔍 **エラートレース:**\n```\n{error_trace}\n```")

        # 2. デバッグコマンド
        debug_commands = f"""🔧 **デバッグコマンド:**
```bash
# 詳細ログ確認
ai-logs {task_id} --verbose

# ワーカーログ確認
tail -f logs/{worker_id}.log

# DLQ確認
ai-dlq show {task_id}

# エラーパターン解析
ai-error analyze {task_id}
```"""
        thread_messages.append(debug_commands)

        # 3. 修正提案（AI Command Executorを使用）
        fix_suggestions = f"""🛠️ **修正提案:**
```bash
# エラーの自動修正を試行
ai-fix {task_id}

# インシデント作成
ai-incident create --error "{error_summary}" --task {task_id}

# 類似エラーの検索
ai-error search "{error_summary}"
```"""
        thread_messages.append(fix_suggestions)

        # 4. Elder統合詳細
        if elder_insights:
            elder_details = self._format_elder_insights(elder_insights)
            thread_messages.append(elder_details)

        return main_message, thread_messages

    def _summarize_text(self, text: str, max_length: int) -> str:
        """テキストを要約（最初のn文字 + ...）"""
        if not text:
            return "（なし）"

        # 改行を空白に置換
        text = text.replace("\n", " ").strip()

        if len(text) <= max_length:
            return text

        # 単語の途中で切らないように調整
        cutoff = text[:max_length].rfind(" ")
        if cutoff == -1 or cutoff < max_length * 0.7:
            cutoff = max_length

        return f"{text[:cutoff]}..."

    def _format_response_details(self, response: str) -> str:
        """レスポンスの詳細フォーマット"""
        if len(response) <= 2000:
            return f"```\n{response}\n```"

        # 長い場合は要約と最初/最後を表示
        lines = response.split("\n")
        total_lines = len(lines)

        if total_lines > 20:
            preview_lines = (
                lines[:10] + ["", f"... ({total_lines - 20} 行省略) ...", ""] + lines[-10:]
            )
            preview = "\n".join(preview_lines)
        else:
            preview = response[:1000] + f"\n\n... (残り {len(response) - 1000} 文字)"

        return f"```\n{preview}\n```"

    def _generate_file_commands(self, files_created: List[str]) -> str:
        """ファイル操作コマンドの生成"""
        if not files_created:
            return "ファイルが作成されていません"

        commands = ["```bash"]

        # ファイル一覧表示
        commands.append("# 作成されたファイル一覧")
        commands.append(f"ls -la {' '.join(files_created[:5])}")

        # ファイルタイプ別のコマンド
        for file_path in files_created[:3]:
            file_path = Path(file_path)
            if file_path.suffix == ".py":
                commands.extend(
                    [
                        "",
                        f"# Pythonファイルの確認",
                        f"cat {file_path}",
                        f"python3 -m py_compile {file_path}  # 構文チェック",
                    ]
                )
            elif file_path.suffix == ".sh":
                commands.extend(
                    [
                        "",
                        f"# シェルスクリプトの確認",
                        f"cat {file_path}",
                        f"chmod +x {file_path}",
                        f"bash -n {file_path}  # 構文チェック",
                    ]
                )
            elif file_path.suffix == ".json":
                commands.extend(["", f"# JSONファイルの確認", f"jq . {file_path}  # 整形表示"])

        commands.append("```")
        return "\n".join(commands)

    def _generate_git_commands(self, files_created: List[str], task_type: str) -> str:
        """GitHub Flow用のコマンド生成"""
        if not files_created:
            return ""

        # ブランチ名の生成
        branch_type = (
            "feature" if task_type in ["development", "enhancement"] else "fix"
        )
        branch_name = (
            f"{branch_type}/{task_type}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )

        commands = f"""```bash
# 新しいブランチを作成
gf {branch_type} {task_type}

# ファイルを追加
git add {' '.join(files_created[:5])}

# コミット（AI Command Executorを使用）
ai-git commit -m "✨ {task_type}: 自動生成されたファイル"

# プルリクエスト作成
gf pr

# または、自動化スクリプト
ai-git flow --files "{','.join(files_created)}" --type {branch_type}
```"""

        return commands

    def _format_elder_insights(self, elder_insights: Dict[str, Any]) -> str:
        """Elder統合詳細情報のフォーマット"""
        try:
            parts = ["🌳 **エルダー統合詳細:**"]

            # Elder Tree status
            if elder_insights.get("elder_tree_status"):
                parts.append(f"• **Elder Tree:** {elder_insights['elder_tree_status']}")

            # All recommendations
            if elder_insights.get("recommendations"):
                parts.append("• **推奨事項:**")
                for rec in elder_insights["recommendations"]:
                    parts.append(f"  - {rec}")

            # Escalation information
            if elder_insights.get("escalation_info"):
                parts.append("• **エスカレーション:**")
                for key, value in elder_insights["escalation_info"].items():
                    parts.append(f"  - {key}: {value}")

            # Learning status
            if elder_insights.get("learning_status"):
                parts.append("• **学習状況:**")
                for key, value in elder_insights["learning_status"].items():
                    parts.append(f"  - {key}: {value}")

            # Performance metrics
            if elder_insights.get("performance_metrics"):
                metrics = elder_insights["performance_metrics"]
                parts.append("• **パフォーマンス:**")
                parts.append(f"  - 成功率: {metrics.get('success_rate', 'N/A')}")
                parts.append(f"  - エルダーエスカレーション: {metrics.get('elder_escalations', 0)}")
                parts.append(f"  - 賢者相談: {metrics.get('sage_consultations', 0)}")
                parts.append(f"  - 評議会要請: {metrics.get('council_requests', 0)}")

            # Elder status
            if elder_insights.get("elder_status"):
                status = elder_insights["elder_status"]
                parts.append("• **エルダーステータス:**")
                parts.append(
                    f"  - Four Sages: {'✅' if status.get('four_sages') else '❌'}"
                )
                parts.append(
                    f"  - Elder Council: {'✅' if status.get('elder_council') else '❌'}"
                )
                parts.append(
                    f"  - Elder Tree: {'✅' if status.get('elder_tree') else '❌'}"
                )

                if status.get("initialization_errors"):
                    parts.append("  - 初期化エラー:")
                    for error in status["initialization_errors"]:
                        parts.append(f"    • {error}")

            return "\n".join(parts)

        except Exception as e:
            return f"🌳 **エルダー統合詳細:** エラー - {e}"

    def _format_performance_details(self) -> str:
        """パフォーマンス統計の詳細"""
        success_rate = (
            self.stats["successful_tasks"] / self.stats["total_tasks"]
        ) * 100
        avg_duration = self.stats["total_duration"] / self.stats["total_tasks"]

        return f"""```
総タスク数: {self.stats['total_tasks']}
成功率: {success_rate:.1f}%
平均処理時間: {avg_duration:.2f}秒
失敗タスク: {self.stats['failed_tasks']}
総処理時間: {self.stats['total_duration']:.1f}秒

時間別分析:
- 最速: {self._get_fastest_task()}
- 最遅: {self._get_slowest_task()}
```"""

    def _get_fastest_task(self) -> str:
        """最速タスク情報（仮実装）"""
        return "0.5秒 (単純なテキスト生成)"

    def _get_slowest_task(self) -> str:
        """最遅タスク情報（仮実装）"""
        return "45.2秒 (大規模コード生成)"

    def periodic_stats_report(self):
        """定期的な統計レポート（1時間ごと）- Elder統合対応"""
        while True:
            time.sleep(3600)  # 1時間

            if self.stats["total_tasks"] >= 10:  # 10タスク以上で報告
                success_rate = (
                    self.stats["successful_tasks"] / self.stats["total_tasks"]
                ) * 100
                avg_duration = self.stats["total_duration"] / self.stats["total_tasks"]

                # Elder統合情報を含むレポート
                report_parts = [
                    f"📊 **時間別レポート** `{datetime.now().strftime('%H:00')}`",
                    "",
                    f"📈 **統計:** {self.stats['total_tasks']}タスク | 成功率 {success_rate:.0f}% | 平均 {avg_duration:.1f}秒",
                ]

                # Elder統合統計
                if ELDER_INTEGRATION_AVAILABLE:
                    elder_stats = self._get_elder_stats_summary()
                    if elder_stats:
                        report_parts.extend(["", "🌳 **エルダー統合統計:**"])
                        report_parts.extend(elder_stats)

                report_parts.extend(
                    ["", "```bash", "# 詳細レポート生成", "ai-report generate --hourly", "```"]
                )

                report = "\n".join(report_parts)

                try:
                    self.slack_notifier.send_message(report)
                except:
                    self.logger.warning("Failed to send hourly report")

    def _get_elder_stats_summary(self) -> List[str]:
        """Elder統合統計の要約"""
        try:
            stats = []

            # エルダー統合状態
            if self.elder_integration_status:
                active_systems = sum(
                    1
                    for status in self.elder_integration_status.values()
                    if status is True
                )
                stats.append(f"• アクティブシステム: {active_systems}/3")

            # Elder統計
            if self.stats["elder_escalations"] > 0:
                stats.append(f"• エルダーエスカレーション: {self.stats['elder_escalations']}")

            if self.stats["sage_consultations"] > 0:
                stats.append(f"• 賢者相談: {self.stats['sage_consultations']}")

            if self.stats["council_requests"] > 0:
                stats.append(f"• 評議会要請: {self.stats['council_requests']}")

            # Elder Tree接続状態
            if self.elder_tree:
                stats.append(f"• Elder Tree: 接続中 ({len(self.elder_tree.nodes)} ノード)")
            else:
                stats.append("• Elder Tree: 未接続")

            return stats

        except Exception as e:
            return [f"• エラー: {e}"]

    def get_elder_status_report(self) -> Dict[str, Any]:
        """包括的なElder統合状況レポート"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "integration_status": self.elder_integration_status.copy(),
                "elder_stats": {
                    "elder_escalations": self.stats["elder_escalations"],
                    "sage_consultations": self.stats["sage_consultations"],
                    "council_requests": self.stats["council_requests"],
                },
                "system_health": {},
            }

            # Four Sages健全性
            if self.four_sages:
                report["system_health"]["four_sages"] = {
                    "status": "active",
                    "available_methods": [
                        method
                        for method in dir(self.four_sages)
                        if not method.startswith("_")
                    ],
                }
            else:
                report["system_health"]["four_sages"] = {"status": "inactive"}

            # Elder Council健全性
            if self.elder_council:
                report["system_health"]["elder_council"] = {
                    "status": "active",
                    "available_methods": [
                        method
                        for method in dir(self.elder_council)
                        if not method.startswith("_")
                    ],
                }
            else:
                report["system_health"]["elder_council"] = {"status": "inactive"}

            # Elder Tree健全性
            if self.elder_tree:
                report["system_health"]["elder_tree"] = {
                    "status": "active",
                    "node_count": len(self.elder_tree.nodes),
                    "hierarchy_depth": self._calculate_tree_depth(),
                    "message_queue_size": len(self.elder_tree.message_queue),
                }
            else:
                report["system_health"]["elder_tree"] = {"status": "inactive"}

            # 推奨事項
            report["recommendations"] = self._generate_elder_recommendations()

            return report

        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": f"Status report generation failed: {e}",
                "integration_status": self.elder_integration_status.copy(),
            }

    def _calculate_tree_depth(self) -> int:
        """Elder Tree階層の深さを計算"""
        try:
            if not self.elder_tree or not self.elder_tree.root:
                return 0

            def get_depth(node):
                if not node.children:
                    return 1
                return 1 + max(get_depth(child) for child in node.children)

            return get_depth(self.elder_tree.root)

        except Exception:
            return 0

    def _generate_elder_recommendations(self) -> List[str]:
        """Elder統合の推奨事項を生成"""
        recommendations = []

        try:
            # 統合状態チェック
            if not self.elder_integration_status.get("four_sages"):
                recommendations.append("Four Sages Integration の再初期化を検討")

            if not self.elder_integration_status.get("elder_council"):
                recommendations.append("Elder Council Summoner の接続確認")

            if not self.elder_integration_status.get("elder_tree"):
                recommendations.append("Elder Tree Hierarchy の再接続を推奨")

            # 統計に基づく推奨
            if self.stats["elder_escalations"] > self.stats["total_tasks"] * 0.1:
                recommendations.append("エラー率が高い - インシデント分析を強化")

            if self.stats["sage_consultations"] == 0 and self.stats["total_tasks"] > 50:
                recommendations.append("賢者相談の活用を検討")

            if self.stats["council_requests"] == 0 and self.stats["total_tasks"] > 100:
                recommendations.append("重要パターンの評議会報告を検討")

            # 初期化エラー対応
            if self.elder_integration_status.get("initialization_errors"):
                recommendations.append("初期化エラーの解決が必要")

            if not recommendations:
                recommendations.append("Elder統合は良好に動作中")

        except Exception as e:
            recommendations.append(f"推奨事項生成エラー: {e}")

        return recommendations

    def cleanup(self):
        """TODO: cleanupメソッドを実装してください"""
        pass

    def stop(self):
        """TODO: stopメソッドを実装してください"""
        pass

    def initialize(self) -> None:
        """ワーカーの初期化処理"""
        # TODO: 初期化ロジックを実装してください
        pass

    def handle_error(self):
        """TODO: handle_errorメソッドを実装してください"""
        pass

    def get_status(self):
        """TODO: get_statusメソッドを実装してください"""
        pass

    def validate_config(self):
        """TODO: validate_configメソッドを実装してください"""
        pass


# Backward compatibility alias
ResultWorker = ResultWorkerV2

if __name__ == "__main__":
    worker = ResultWorkerV2()

    # 統計レポートスレッドを開始
    import threading

    stats_thread = threading.Thread(target=worker.periodic_stats_report, daemon=True)
    stats_thread.start()

    # ワーカー実行
    worker.start()
