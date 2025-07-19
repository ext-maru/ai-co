#!/usr/bin/env python3
"""
Elders Guild Intelligent PM Worker
知的PM Worker - 内容判断してAIコマンド実行
本格的なプロジェクト管理・意思決定システム with Elder Tree階層統合
"""

import asyncio
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import requests

from core.async_base_worker_v2 import AsyncBaseWorkerV2
from libs.elder_council_summoner import (
    CouncilTrigger,
    ElderCouncilSummoner,
    TriggerCategory,
    UrgencyLevel,
)
from libs.elder_tree_hierarchy import (
    ElderDecision,
    ElderMessage,
    ElderRank,
    ElderTreeHierarchy,
    SageType,
    get_elder_tree,
)
from libs.env_config import get_config

# Elder Tree Integration imports
from libs.four_sages_integration import FourSagesIntegration


@dataclass
class ProjectContext:
    """プロジェクト管理コンテキスト"""

    task_id: str
    project_type: str  # 'development', 'analysis', 'testing', 'documentation'
    complexity: str  # 'simple', 'moderate', 'complex', 'critical'
    urgency: str  # 'low', 'normal', 'high', 'critical'
    requires_elder_guidance: bool = False
    elder_recommendations: List[str] = field(default_factory=list)
    sage_consultations: Dict[str, Any] = field(default_factory=dict)


class IntelligentPMWorker(AsyncBaseWorkerV2):
    """Elders Guild Intelligent PM Worker - 内容分析→AIコマンド選択→実行指示 with Elder Tree統合"""

    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        super().__init__(
            worker_name="intelligent_pm_worker",
            config=config,
            input_queues=["ai_pm"],
            output_queues=["ai_results"],
        )

        self.env_config = get_config()

        # Elder Tree Integration
        self._initialize_elder_systems()

        # AI コマンド定義
        self.ai_commands = {
            "code_generation": {
                "command": "ai-send",
                "patterns": [
                    "コード",
                    "code",
                    "実装",
                    "implement",
                    "作成",
                    "create",
                    "function",
                    "関数",
                ],
                "description": "コード生成・実装",
            },
            "testing": {
                "command": "ai-tdd",
                "patterns": ["テスト", "test", "TDD", "テスト駆動", "pytest", "unittest"],
                "description": "テスト作成・実行",
            },
            "project_analysis": {
                "command": "ai-analyze",
                "patterns": ["分析", "analyze", "プロジェクト", "project", "構造", "structure"],
                "description": "プロジェクト分析",
            },
            "documentation": {
                "command": "ai-doc",
                "patterns": ["ドキュメント", "document", "README", "docs", "説明", "explain"],
                "description": "ドキュメント生成",
            },
            "general_task": {
                "command": "ai-send",
                "patterns": ["一般", "general", "help", "ヘルプ"],
                "description": "一般的なタスク",
            },
        }

    def _initialize_elder_systems(self):
        """Elder Tree階層システムの初期化"""
        try:
            # Elder Tree接続
            self.elder_tree = get_elder_tree()
            self.four_sages = FourSagesIntegration()
            self.elder_council_summoner = ElderCouncilSummoner()

            # このワーカーをServantとして登録
            self.elder_rank = ElderRank.SERVANT
            self.elder_id = f"intelligent_pm_servant_{self.worker_name}"

            # Four Sages初期設定
            sage_configs = {
                "knowledge_sage": {"active": True, "priority": "high"},
                "task_sage": {"active": True, "priority": "high"},
                "incident_sage": {"active": True, "priority": "medium"},
                "rag_sage": {"active": True, "priority": "medium"},
            }
            init_result = self.four_sages.initialize_sage_integration(sage_configs)

            self.logger.info(
                f"🌳 Elder Tree Integration initialized for {self.elder_id}"
            )
            self.logger.info(
                f"📜 Four Sages initialization: {init_result['integration_status']}"
            )
            self.logger.info("🏛️ Connected to Elder Council summoning system")

            self.elder_integration_enabled = True

        except Exception as e:
            self.logger.error(f"❌ Elder Tree Integration failed: {e}")
            self.logger.warning(
                "⚠️ Intelligent PM Worker operating without Elder guidance"
            )
            self.elder_tree = None
            self.four_sages = None
            self.elder_council_summoner = None
            self.elder_integration_enabled = False

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """PMメッセージ処理 - 知的判断とAIコマンド実行 with Elder guidance"""
        task_id = message.get("task_id", "unknown")
        output = message.get("output", "")
        original_prompt = message.get("original_prompt", "")
        task_type = message.get("task_type", "general")
        is_slack_task = message.get("is_slack_task", False)

        self.logger.info(f"🧠 PM知的判断開始: {task_id}")

        try:
            # 1. 内容分析
            analysis = await self._analyze_content(original_prompt, output)

            # 1.5. Elder Treeコンサルテーション（複雑なタスクの場合）
            project_context = await self._create_project_context(task_id, analysis)
            if (
                project_context.requires_elder_guidance
                and self.elder_integration_enabled
            ):
                await self._consult_elders(project_context, analysis)

            # 2. 適切なAIコマンド選択（Elder推奨も考慮）
            selected_command = await self._select_ai_command(analysis, project_context)

            # 3. 必要に応じてAIコマンド実行
            command_result = await self._execute_ai_command(selected_command, analysis)

            # 3.5. プロジェクト分析をKnowledge Sageに報告
            if self.elder_integration_enabled and command_result.get("executed"):
                await self._report_to_knowledge_sage(task_id, analysis, command_result)

            # 4. 結果評価と次アクション決定（Elder評価含む）
            final_result = await self._evaluate_and_decide_next_action(
                task_id, analysis, command_result, is_slack_task, project_context
            )

            # 5. Slack応答（Slackタスクの場合）
            if is_slack_task:
                await self._send_slack_response(task_id, final_result)

            self.logger.info(f"🎯 PM処理完了: {task_id}")

            return {
                "task_id": task_id,
                "status": "pm_completed",
                "pm_analysis": analysis,
                "executed_command": selected_command,
                "final_output": final_result,
                "processed_at": datetime.utcnow().isoformat(),
                "worker": self.worker_name,
                "elder_consultations": project_context.sage_consultations
                if project_context
                else {},
                "elder_recommendations": project_context.elder_recommendations
                if project_context
                else [],
            }

        except Exception as e:
            self.logger.error(f"❌ PM処理エラー: {task_id} - {str(e)}")

            # 重大なエラーの場合はIncident Sageに報告
            if self.elder_integration_enabled:
                await self._report_critical_error_to_sage(task_id, e)

            # エラー時もSlack応答
            if is_slack_task:
                await self._send_slack_error_response(task_id, str(e))

            return {
                "task_id": task_id,
                "status": "pm_failed",
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat(),
                "worker": self.worker_name,
            }

    async def _analyze_content(self, prompt: str, claude_output: str) -> Dict[str, Any]:
        """内容分析 - ユーザー要求とClaude応答を分析"""

        # ユーザー要求の分析
        user_intent = self._classify_user_intent(prompt)

        # Claude応答の分析
        response_analysis = self._analyze_claude_response(claude_output)

        # 日本語判定
        has_japanese = any(ord(char) > 127 for char in prompt)

        analysis = {
            "user_intent": user_intent,
            "response_analysis": response_analysis,
            "language": "japanese" if has_japanese else "english",
            "complexity": self._assess_complexity(prompt),
            "requires_action": self._requires_further_action(prompt, claude_output),
            "original_prompt": prompt,
            "claude_output": claude_output,
        }

        self.logger.info(
            f"📊 内容分析: {analysis['user_intent']} | 複雑度: {analysis['complexity']}"
        )
        return analysis

    def _classify_user_intent(self, prompt: str) -> str:
        """ユーザー意図の分類"""
        prompt_lower = prompt.lower()

        for intent, config in self.ai_commands.items():
            if any(pattern in prompt_lower for pattern in config["patterns"]):
                return intent

        return "general_task"

    def _analyze_claude_response(self, output: str) -> Dict[str, Any]:
        """Claude応答の分析"""
        return {
            "has_code": "```" in output,
            "has_explanation": len(output.split(".")) > 3,
            "is_question": "?" in output,
            "word_count": len(output.split()),
            "appears_complete": not output.endswith("...") and len(output) > 50,
        }

    def _assess_complexity(self, prompt: str) -> str:
        """タスク複雑度評価"""
        complexity_indicators = {
            "high": [
                "プロジェクト全体",
                "システム",
                "アーキテクチャ",
                "complex",
                "system",
                "architecture",
            ],
            "medium": ["機能", "feature", "モジュール", "module", "クラス", "class"],
            "low": ["関数", "function", "メソッド", "method", "変数", "variable"],
        }

        prompt_lower = prompt.lower()

        for level, indicators in complexity_indicators.items():
            if any(indicator in prompt_lower for indicator in indicators):
                return level

        return "medium"

    def _requires_further_action(self, prompt: str, claude_output: str) -> bool:
        """追加アクション必要性判定"""

        # コード生成要求だがコードが含まれていない
        if any(word in prompt.lower() for word in ["コード", "code", "実装", "implement"]):
            if "```" not in claude_output:
                return True

        # 質問形式で終わっている
        if claude_output.strip().endswith("?") or claude_output.strip().endswith("？"):
            return True

        # 短すぎる応答
        if len(claude_output.split()) < 20:
            return True

        return False

    async def _select_ai_command(
        self, analysis: Dict[str, Any], project_context: Optional[ProjectContext] = None
    ) -> Dict[str, Any]:
        """適切なAIコマンド選択（Elder推奨考慮）"""

        user_intent = analysis["user_intent"]
        complexity = analysis["complexity"]
        requires_action = analysis["requires_action"]

        # 基本コマンド選択
        if user_intent in self.ai_commands:
            base_command = self.ai_commands[user_intent]
        else:
            base_command = self.ai_commands["general_task"]

        # Elder推奨がある場合は考慮
        if project_context and project_context.elder_recommendations:
            for recommendation in project_context.elder_recommendations:
                if "use_command:" in recommendation:
                    recommended_cmd = recommendation.split("use_command:")[1].strip()
                    if recommended_cmd in ["ai-tdd", "ai-analyze", "ai-doc"]:
                        base_command["command"] = recommended_cmd
                        self.logger.info(f"🌟 Elder推奨コマンドを採用: {recommended_cmd}")

        # 複雑度に応じた調整
        command_config = {
            "command": base_command["command"],
            "description": base_command["description"],
            "priority": "high" if complexity == "high" else "normal",
            "additional_tools": [],
        }

        # 追加ツール判定
        if analysis["user_intent"] == "code_generation":
            command_config["additional_tools"] = ["Edit", "Write", "Read", "MultiEdit"]
        elif analysis["user_intent"] == "testing":
            command_config["additional_tools"] = ["Bash", "Read", "Write"]
        elif analysis["user_intent"] == "project_analysis":
            command_config["additional_tools"] = ["Glob", "Grep", "Read", "LS"]

        self.logger.info(
            f"🎯 選択コマンド: {command_config['command']} ({command_config['description']})"
        )
        return command_config

    async def _execute_ai_command(
        self, command_config: Dict[str, Any], analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AIコマンド実行"""

        # 追加アクションが不要な場合はスキップ
        if not analysis["requires_action"]:
            return {
                "executed": False,
                "reason": "No additional action required",
                "output": analysis["claude_output"],
            }

        command = command_config["command"]
        prompt = analysis["original_prompt"]

        # より具体的なプロンプト作成
        enhanced_prompt = self._create_enhanced_prompt(prompt, command_config, analysis)

        try:
            self.logger.info(f"⚡ AIコマンド実行: {command}")

            # AIコマンド実行
            if command == "ai-send":
                result = await self._execute_ai_send(enhanced_prompt, command_config)
            elif command == "ai-tdd":
                result = await self._execute_ai_tdd(enhanced_prompt, command_config)
            else:
                result = await self._execute_generic_ai_command(
                    command, enhanced_prompt, command_config
                )

            return {
                "executed": True,
                "command": command,
                "output": result,
                "enhanced_prompt": enhanced_prompt,
            }

        except Exception as e:
            self.logger.error(f"❌ AIコマンド実行エラー: {str(e)}")
            return {
                "executed": False,
                "error": str(e),
                "output": analysis["claude_output"],
            }

    def _create_enhanced_prompt(
        self,
        original_prompt: str,
        command_config: Dict[str, Any],
        analysis: Dict[str, Any],
    ) -> str:
        """プロンプト強化"""

        language = "Japanese" if analysis["language"] == "japanese" else "English"

        enhanced = f"""Task: {original_prompt}

Context:
- User Intent: {analysis['user_intent']}
- Complexity: {analysis['complexity']}
- Language: {language}
- Required Output: Practical, actionable solution

Please provide a detailed response that includes:
1. Concrete implementation or solution
2. Step-by-step instructions if applicable
3. Code examples if requested
4. Best practices and considerations

Respond in {language}."""

        return enhanced

    async def _execute_ai_send(
        self, prompt: str, command_config: Dict[str, Any]
    ) -> str:
        """ai-send コマンド実行"""

        cmd = [
            "python3",
            "commands/ai_send.py",
            "--prompt",
            prompt,
            "--priority",
            command_config.get("priority", "normal"),
            "--type",
            "pm_enhanced",
        ]

        if command_config.get("additional_tools"):
            tools = ",".join(command_config["additional_tools"])
            cmd.extend(["--tools", tools])

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=300
        )

        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(f"ai-send failed: {result.stderr}")

    async def _execute_ai_tdd(self, prompt: str, command_config: Dict[str, Any]) -> str:
        """ai-tdd コマンド実行"""

        cmd = ["python3", "scripts/ai-tdd", "session", prompt]

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=300
        )

        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(f"ai-tdd failed: {result.stderr}")

    async def _execute_generic_ai_command(
        self, command: str, prompt: str, command_config: Dict[str, Any]
    ) -> str:
        """汎用AIコマンド実行"""

        cmd = [command, prompt]

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=300
        )

        if result.returncode == 0:
            return result.stdout
        else:
            return f"Command {command} execution completed with some issues."

    async def _evaluate_and_decide_next_action(
        self,
        task_id: str,
        analysis: Dict[str, Any],
        command_result: Dict[str, Any],
        is_slack_task: bool,
        project_context: Optional[ProjectContext] = None,
    ) -> str:
        """結果評価と次アクション決定（Elder評価含む）"""

        if command_result.get("executed"):
            final_output = command_result["output"]
            decision = "✅ PM enhanced response generated"
        else:
            final_output = analysis["claude_output"]
            decision = "📝 Original Claude response sufficient"

        # 言語に応じた応答調整
        if analysis["language"] == "japanese":
            if not command_result.get("executed"):
                final_output = self._localize_response_japanese(final_output)

        self.logger.info(f"🎯 PM判定: {decision}")

        return final_output

    def _localize_response_japanese(self, output: str) -> str:
        """日本語応答のローカライゼーション"""

        # 基本的な英語→日本語置換
        replacements = {
            "Hello": "こんにちは",
            "Thank you": "ありがとうございます",
            "Please": "お願いします",
            "Here is": "こちらが",
            "You can": "できます",
        }

        localized = output
        for en, jp in replacements.items():
            localized = localized.replace(en, jp)

        return localized

    async def _send_slack_response(self, task_id: str, response: str):
        """Slack応答送信"""
        try:
            slack_config = self.env_config.get_slack_config()
            bot_token = slack_config.get("bot_token")
            channel_id = self.env_config.SLACK_POLLING_CHANNEL_ID

            if not bot_token:
                self.logger.warning("Slack bot token not found")
                return

            url = "https://slack.com/api/chat.postMessage"
            headers = {
                "Authorization": f"Bearer {bot_token}",
                "Content-Type": "application/json",
            }

            payload = {"channel": channel_id, "text": response, "username": "PM-AI"}

            response_obj = requests.post(url, json=payload, headers=headers, timeout=10)

            if response_obj.status_code == 200:
                result = response_obj.json()
                if result.get("ok"):
                    self.logger.info(f"✅ PM-Slack応答送信成功: {task_id}")
                else:
                    self.logger.error(
                        f"❌ Slack API Error: {result.get('error', 'Unknown')}"
                    )
            else:
                self.logger.error(f"❌ HTTP Error: {response_obj.status_code}")

        except Exception as e:
            self.logger.error(f"❌ PM-Slack応答送信エラー: {str(e)}")

    async def _send_slack_error_response(self, task_id: str, error: str):
        """Slackエラー応答送信"""
        error_message = f"🚨 **PM-AI エラー**\n\n申し訳ございません。処理中にエラーが発生しました。\n\nエラー: {error}\n\nタスクID: {task_id}"
        await self._send_slack_response(task_id, error_message)

    async def _create_project_context(
        self, task_id: str, analysis: Dict[str, Any]
    ) -> ProjectContext:
        """プロジェクトコンテキストの作成"""
        # プロジェクトタイプ判定
        user_intent = analysis["user_intent"]
        project_type_map = {
            "code_generation": "development",
            "testing": "testing",
            "project_analysis": "analysis",
            "documentation": "documentation",
            "general_task": "development",
        }
        project_type = project_type_map.get(user_intent, "development")

        # 複雑度マッピング
        complexity_map = {"low": "simple", "medium": "moderate", "high": "complex"}
        complexity = complexity_map.get(analysis["complexity"], "moderate")

        # 緊急度判定（日本語の緊急キーワードチェック）
        prompt = analysis["original_prompt"]
        urgency = "normal"
        if any(word in prompt for word in ["緊急", "至急", "urgent", "critical", "ASAP"]):
            urgency = "critical"
        elif any(word in prompt for word in ["急ぎ", "早め", "soon", "quickly"]):
            urgency = "high"

        # Elder指導が必要かどうか
        requires_elder_guidance = (
            complexity in ["complex", "critical"]
            or urgency in ["high", "critical"]
            or analysis["complexity"] == "high"
        )

        return ProjectContext(
            task_id=task_id,
            project_type=project_type,
            complexity=complexity,
            urgency=urgency,
            requires_elder_guidance=requires_elder_guidance,
        )

    async def _consult_elders(
        self, project_context: ProjectContext, analysis: Dict[str, Any]
    ):
        """Elder Treeへのコンサルテーション"""
        try:
            # Task Sageへのコンサルテーション（タスク最適化）
            if project_context.complexity in ["complex", "critical"]:
                task_sage_result = await self.four_sages.consult_task_sage(
                    task_description=analysis["original_prompt"],
                    task_metadata={
                        "complexity": project_context.complexity,
                        "urgency": project_context.urgency,
                        "project_type": project_context.project_type,
                    },
                )

                if task_sage_result["status"] == "success":
                    project_context.sage_consultations["task_sage"] = task_sage_result
                    recommendations = task_sage_result.get("recommendations", [])
                    project_context.elder_recommendations.extend(
                        [f"Task Sage: {rec}" for rec in recommendations]
                    )
                    self.logger.info("📋 Task Sageからの最適化提案を受領")

            # Incident Sageへのリスク評価依頼
            if project_context.urgency == "critical":
                incident_sage_result = await self.four_sages.consult_incident_sage(
                    context={
                        "task_id": project_context.task_id,
                        "urgency": project_context.urgency,
                        "description": analysis["original_prompt"][:200],
                    }
                )

                if incident_sage_result["status"] == "success":
                    project_context.sage_consultations[
                        "incident_sage"
                    ] = incident_sage_result
                    risk_level = incident_sage_result.get("risk_level", "unknown")
                    if risk_level in ["high", "critical"]:
                        project_context.elder_recommendations.append(
                            f"Incident Sage: 高リスクプロジェクト - 慎重な実行を推奨"
                        )
                    self.logger.info("⚠️ Incident Sageからのリスク評価を受領")

            # RAG Sageへの類似プロジェクト検索
            rag_sage_result = await self.four_sages.consult_rag_sage(
                query=analysis["original_prompt"],
                search_type="similar_projects",
                limit=3,
            )

            if rag_sage_result["status"] == "success":
                project_context.sage_consultations["rag_sage"] = rag_sage_result
                similar_projects = rag_sage_result.get("results", [])
                if similar_projects:
                    project_context.elder_recommendations.append(
                        f"RAG Sage: {len(similar_projects)}件の類似プロジェクトを発見"
                    )
                    self.logger.info("🔍 RAG Sageから類似プロジェクト情報を受領")

            # 重大案件の場合はElder Councilを召喚
            if (
                project_context.complexity == "critical"
                and project_context.urgency == "critical"
            ):
                council_trigger = CouncilTrigger(
                    category=TriggerCategory.CRITICAL_DECISION,
                    urgency=UrgencyLevel.CRITICAL,
                    context={
                        "task_id": project_context.task_id,
                        "project_type": project_context.project_type,
                        "description": analysis["original_prompt"],
                    },
                    requestor_id=self.elder_id,
                )

                council_result = await self.elder_council_summoner.summon_council(
                    council_trigger
                )

                if council_result and council_result.get("decision"):
                    project_context.sage_consultations["elder_council"] = council_result
                    project_context.elder_recommendations.insert(
                        0,
                        f"🏛️ Elder Council決定: {council_result['decision']['summary']}",
                    )
                    self.logger.info("🏛️ Elder Councilから戦略的指針を受領")

        except Exception as e:
            self.logger.warning(f"Elder consultation failed: {e}")

    async def _report_to_knowledge_sage(
        self, task_id: str, analysis: Dict[str, Any], command_result: Dict[str, Any]
    ):
        """Knowledge Sageへのプロジェクト知識報告"""
        try:
            knowledge_entry = {
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
                "project_type": analysis["user_intent"],
                "complexity": analysis["complexity"],
                "command_executed": command_result.get("command"),
                "success": command_result.get("executed", False),
                "original_prompt": analysis["original_prompt"][:500],
                "insights": {
                    "language": analysis["language"],
                    "response_quality": "complete"
                    if analysis["response_analysis"].get("appears_complete")
                    else "partial",
                    "has_code": analysis["response_analysis"].get("has_code", False),
                },
            }

            result = await self.four_sages.report_to_knowledge_sage(
                knowledge_type="project_execution",
                knowledge_data=knowledge_entry,
                tags=["pm_worker", "intelligent_pm", analysis["user_intent"]],
            )

            if result["status"] == "success":
                self.logger.info(f"📚 Knowledge Sageへプロジェクト知識を報告: {task_id}")

        except Exception as e:
            self.logger.warning(f"Failed to report to Knowledge Sage: {e}")

    async def _report_critical_error_to_sage(self, task_id: str, error: Exception):
        """Incident Sageへの重大エラー報告"""
        try:
            error_report = {
                "task_id": task_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "timestamp": datetime.utcnow().isoformat(),
                "worker": self.worker_name,
                "severity": "high",
            }

            result = await self.four_sages.report_incident(
                incident_type="pm_critical_error",
                incident_data=error_report,
                severity="high",
            )

            if result["status"] == "success":
                self.logger.info(f"🚨 Incident Sageへ重大エラーを報告: {task_id}")

                # エラーパターンが繰り返される場合はClaude Elderへエスカレーション
                if result.get("escalation_required"):
                    council_trigger = CouncilTrigger(
                        category=TriggerCategory.CRITICAL_ERROR,
                        urgency=UrgencyLevel.HIGH,
                        context={
                            "task_id": task_id,
                            "error": error_report,
                            "pattern": result.get("error_pattern", "unknown"),
                        },
                        requestor_id=self.elder_id,
                    )

                    await self.elder_council_summoner.escalate_to_claude_elder(
                        council_trigger
                    )
                    self.logger.info("🌟 Claude Elderへエスカレーション完了")

        except Exception as e:
            self.logger.warning(f"Failed to report critical error to Sage: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Intelligent PM Worker")
    parser.add_argument("--worker-id", help="Worker ID", default="intelligent-pm")

    args = parser.parse_args()

    worker = IntelligentPMWorker()
    print(f"🧠 Intelligent PM Worker starting...")

    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        print(f"\n❌ Worker stopped by user")
