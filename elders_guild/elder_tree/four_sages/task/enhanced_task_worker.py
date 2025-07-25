#!/usr/bin/env python3
"""

プロンプトテンプレート機能を統合した強化版TaskWorker
エルダーズギルド統合対応版 v2.0
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.base_worker import BaseWorker
from libs.env_config import get_config

# エルダーズギルド統合
try:
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import ElderMessage, ElderRank, get_elder_tree
    from libs.four_sages_integration import FourSagesIntegration

    ELDER_INTEGRATION_AVAILABLE = True
except ImportError:
    # Handle specific exception case
    ELDER_INTEGRATION_AVAILABLE = False

# 絵文字定義
EMOJI = {
    "start": "🚀",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "task": "📋",
    "thinking": "🤔",
    "complete": "🎉",
    "process": "⚙️",
    "robot": "🤖",
    "elder": "🏛️",
    "sage": "🧙‍♂️",
}
import logging

from core import ErrorSeverity, msg, with_error_handling

from libs.rag_grimoire_integration import RagGrimoireConfig, RagGrimoireIntegration
from libs.slack_notifier import SlackNotifier

    """プロンプトテンプレート対応の強化版TaskWorker"""

    def __init__(self, worker_id=None):
        # BaseWorker初期化
        BaseWorker.__init__(self, worker_type="task", worker_id=worker_id)

        # キュー設定をオーバーライド
        self.input_queue = "ai_tasks"
        self.output_queue = "ai_pm"

        self.config = get_config()
        self.output_dir = PROJECT_ROOT / "output"
        self.output_dir.mkdir(exist_ok=True)

        # エルダーズギルド統合
        self.four_sages = None
        self.elder_council = None
        self.elder_tree = None
        if ELDER_INTEGRATION_AVAILABLE:
            try:
                self.four_sages = FourSagesIntegration()
                self.elder_council = ElderCouncilSummoner()
                self.elder_tree = get_elder_tree()
                self.logger.info(f"{EMOJI['elder']} エルダーズギルド統合有効化")
                self.logger.info(f"{EMOJI['sage']} 4賢者システム統合完了")
                self.logger.info(f"🏛️ エルダー評議会システム統合完了")
                self.logger.info(f"🌳 エルダーツリー階層システム統合完了")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"エルダーズギルド統合初期化エラー: {e}")
                self.four_sages = None
                self.elder_council = None
                self.elder_tree = None

        # ツールの設定（開発用に大幅拡張）
        self.model = getattr(
            self.config, "WORKER_DEFAULT_MODEL", "claude-sonnet-4-20250514"
        )
        self.allowed_tools = getattr(
            self.config,
            "WORKER_ALLOWED_TOOLS",
            [
                # ファイル操作
                "Edit",
                "Write",
                "Read",
                "MultiEdit",
                "Glob",
                "Grep",
                "LS",
                # システム操作
                "Bash",
                "Task",
                # Web操作
                "WebFetch",
                "WebSearch",
                # ノートブック操作
                "NotebookRead",
                "NotebookEdit",
                # タスク管理

                # 計画モード
                "exit_plan_mode",
            ],
        )

        # 通知設定
        self.slack_notifier = SlackNotifier()

        # タスク履歴DB
        try:
            from libs.task_history_db import TaskHistoryDB

            self.task_history_db = TaskHistoryDB()
        except ImportError:
            # Handle specific exception case
            self.task_history_db = None

        # RAG Grimoire Integration
        self.rag_integration = None
        self.rag_config = RagGrimoireConfig(
            database_url=getattr(
                self.config, "GRIMOIRE_DATABASE_URL", "postgresql://localhost/grimoire"
            ),
            search_threshold=getattr(self.config, "RAG_SEARCH_THRESHOLD", 0.7),
            max_search_results=getattr(self.config, "RAG_MAX_RESULTS", 10),
        )

        self.logger.info(

        )

        # Initialize RAG Grimoire Integration asynchronously
        self._initialize_rag_integration()

    def process_message(self, ch, method, properties, body):
        """メッセージを処理（プロンプトテンプレート使用）"""
        try:
            # メッセージをパース
            task = json.loads(body.decode("utf-8"))
            task_id = task.get("id", "unknown")
            task_type = task.get("type", "general")
            user_prompt = task.get("prompt", "")
            priority = task.get("priority", "normal")

            self.logger.info(
                f"{EMOJI['task']} Processing task {task_id} with priority: {priority}"
            )

            # 🌳 Elder Tree Integration: タスク賢者による事前相談
            task_advice = None
            if task_type in ["code_generation", "system_task", "complex_analysis"]:
                task_advice = asyncio.run(
                    self.consult_task_sage(
                        {
                            "id": task_id,
                            "type": task_type,
                            "prompt": user_prompt,
                            "priority": priority,
                            "dependencies": task.get("dependencies", []),
                        }
                    )
                )

                if task_advice.get("available") and task_advice.get(
                    "recommended_approach"
                ):
                    self.logger.info(
                        f"{EMOJI['sage']} タスク賢者推奨アプローチ: {task_advice['recommended_approach']}"
                    )

            # テンプレート選択

            # 🌳 Elder Tree Integration: RAG賢者によるプロンプト強化
            enhanced_prompt = asyncio.run(
                self.enhance_prompt_with_rag_sage(
                    user_prompt,
                    {
                        "task_id": task_id,
                        "task_type": task_type,
                        "priority": priority,
                        "sage_advice": task_advice,
                    },
                )
            )

            # プロンプト生成（RAG含む）
            generated_prompt = self.generate_prompt(

                variables={
                    "task_id": task_id,
                    "task_type": task_type,
                    "user_prompt": enhanced_prompt,  # RAG賢者で強化されたプロンプトを使用
                    "priority": priority,
                    "additional_instructions": self._get_additional_instructions(task),
                    "rag_context": self._get_rag_context(enhanced_prompt),
                    "sage_advice": task_advice.get("recommended_approach", "")
                    if task_advice
                    else "",
                },
                include_rag=True,
            )

            if not generated_prompt:

            # タスク履歴に記録開始
            self._record_task_start(task_id, task_type, user_prompt, generated_prompt)

            # Claude実行（Elder Tree統合含む）
            result = self._execute_claude(
                task_id,
                generated_prompt,
                task_context={"task_data": task, "sage_advice": task_advice},
            )

            if result["success"]:
                # 成功時の処理
                self._handle_success(task_id, task, result)

                # プロンプトパフォーマンス評価
                self.evaluate_last_prompt(task_id, 0.9)  # 成功は高スコア

                # 🌳 Elder Tree Integration: ナレッジ賢者への学習記録
                asyncio.run(
                    self.report_task_execution_to_knowledge_sage(task_id, task, result)
                )
            else:
                # 失敗時の処理
                self._handle_failure(task_id, task, result)

                # プロンプトパフォーマンス評価
                self.evaluate_last_prompt(task_id, 0.3)  # 失敗は低スコア

                # 🌳 Elder Tree Integration: インシデント賢者への重要エスカレーション
                error_data = {
                    "error_type": "task_execution_failure",
                    "error": result.get("error", "不明なエラー"),
                    "context": {
                        "task_type": task_type,
                        "prompt": user_prompt,
                        "priority": priority,
                    },
                }

                asyncio.run(
                    self.escalate_critical_failure_to_incident_sage(task_id, error_data)
                )

            # ACK送信
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            # メッセージ処理エラー
            context = {
                "operation": "process_message",
                "task_id": task.get("id", "unknown")
                if "task" in locals()
                else "unknown",
                "task_type": task.get("type", "unknown")
                if "task" in locals()
                else "unknown",

                else "unknown",
            }
            self.handle_error(e, context, severity=ErrorSeverity.HIGH)

            # エラー時もACK（無限ループ防止）
            ch.basic_ack(delivery_tag=method.delivery_tag)

            # エラー結果を送信
            if "task_id" in locals():
                self._send_error_result(task_id, str(e))

    def _initialize_rag_integration(self):
        """RAG Grimoire Integration を初期化"""
        try:
            import asyncio

            self.rag_integration = RagGrimoireIntegration(self.rag_config)
            # Create a new event loop for async initialization
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.rag_integration.initialize())
            loop.close()
            self.logger.info(
                f"{EMOJI['success']} RAG Grimoire Integration initialized successfully"
            )
        except Exception as e:
            # Handle specific exception case
            self.logger.error(
                f"{EMOJI['error']} Failed to initialize RAG Grimoire Integration: {e}"
            )
            self.rag_integration = None

    def _get_rag_context(self, user_prompt: str) -> str:
        """RAG統合システムからコンテキストを取得"""
        # まずエルダーズギルドのRAG賢者に相談
        if self.four_sages:
            try:
                rag_sage_results = self.four_sages.search_knowledge(user_prompt)
                if rag_sage_results and rag_sage_results.get("results"):
                    # Complex condition - consider breaking down
                    context = "\n\n## Elder RAG Sage Knowledge:\n"
                    for result in rag_sage_results["results"][:3]:
                        # Process each item in collection
                        context += f"- {result.get('content', '')[:200]}...\n"
                        context += f"  Source: Elder Knowledge Base (Score: {result.get(
                            'score',
                            0):0.2f}
                        )\n"
                    return context
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"RAG賢者相談エラー: {e}")

        # 従来のRAG統合も使用
        if not self.rag_integration:
            return ""

        try:
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Unified search using grimoire integration
            results = loop.run_until_complete(
                self.rag_integration.search_unified(
                    query=user_prompt,
                    limit=5,
                    threshold=self.rag_config.search_threshold,
                )
            )
            loop.close()

            if not results:
                return ""

            # Format RAG context
            context = "\n\n## Related Knowledge:\n"
            for result in results:
                context += f"- {result['content'][:200]}...\n"
                context += f"  Source: {result['source']} (Score: {result['similarity_score']:0.2f})\n"

            return context

        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"{EMOJI['warning']} RAG context retrieval failed: {e}")
            return ""

        """タスクに応じてテンプレートを選択"""
        # コード生成タスクの判定
        code_keywords = ["コード", "プログラム", "実装", "code", "implement", "create", "build"]
        if task_type == "code" or any(
            keyword in user_prompt.lower() for keyword in code_keywords
        ):
            return "code_generation"

        # 高度なタスクの判定
        advanced_keywords = ["complex", "複雑", "advanced", "高度", "comprehensive"]
        if any(keyword in user_prompt.lower() for keyword in advanced_keywords):
            # Complex condition - consider breaking down
            return "advanced"

        # デフォルト
        return "default"

    def _get_additional_instructions(self, task: dict) -> str:
        """タスクから追加指示を生成"""
        instructions = []

        # 優先度に応じた指示
        priority = task.get("priority", "normal")
        if priority == "critical":
            instructions.append(
                "This is a CRITICAL priority task. Focus on reliability and quick completion."
            )
        elif priority == "high":
            instructions.append(
                "This is a high priority task. Ensure quality and timely completion."
            )

        # 特定の要件
        if task.get("require_tests"):
            instructions.append(
                "Include comprehensive unit tests for all functionality."
            )

        if task.get("require_docs"):
            instructions.append("Include detailed documentation and usage examples.")

        return "\n".join(instructions)

    def _execute_claude(self, task_id: str, prompt: str, task_context: dict = None)timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    """Claude CLIを実行（Elder Tree統合対応）"""
        session_name = f"claude_session_{task_id}_{timestamp}"

        # 🌳 Elder Tree Integration: タスクコンテキストからElder推奨事項を取得
        elder_recommendations = ""
        if task_context and task_context.get("sage_advice"):
            # Complex condition - consider breaking down
            sage_advice = task_context["sage_advice"]
            if sage_advice.get("available") and sage_advice.get("recommended_approach"):
                # Complex condition - consider breaking down
                elder_recommendations = f"\n\n🌳 Elder Tree Recommendations:\n"
                elder_recommendations += (
                    f"- Recommended Approach: {sage_advice['recommended_approach']}\n"
                )

                if sage_advice.get("resource_optimization"):
                    elder_recommendations += f"- Resource Optimization: {sage_advice['resource_optimization']}\n"

                if sage_advice.get("execution_strategy"):
                    elder_recommendations += (
                        f"- Execution Strategy: {sage_advice['execution_strategy']}\n"
                    )

                if sage_advice.get("risk_mitigation"):
                    elder_recommendations += (
                        f"- Risk Mitigation: {sage_advice['risk_mitigation']}\n"
                    )

                self.logger.info(f"{EMOJI['elder']} タスク実行にElder推奨事項を適用")

        # Elder推奨事項をプロンプトに統合
        enhanced_prompt = prompt + elder_recommendations

        # ツールパラメータ構築
        tools_param = f"--allowedTools {','.join(self.allowed_tools)}"

        # コマンド構築（開発用に拡張）
        cmd = [
            "claude",
            "--model",
            self.model,
            "--profile",
            "aicompany",
            "--chat-name",
            session_name,
            "--print",
            "--continue",
            "10",  # より多くの継続実行
            "--no-confirm",  # 確認プロンプトをスキップ
        ] + tools_param.split()

        # 開発環境用の追加設定
        if getattr(self.config, "WORKER_DEV_MODE", True):
            cmd.extend(
                [

                    "--verbose",  # 詳細ログ
                ]
            )

        # --print フラグ使用時はプロンプトをコマンドライン引数として追加
        cmd.append(enhanced_prompt)

        self.logger.info(
            f"{EMOJI['robot']} Executing Claude with Elder-enhanced prompt"
        )

        try:
            # 作業ディレクトリを設定（プロジェクトルートで実行）
            work_dir = getattr(self.config, "WORKER_WORK_DIR", str(PROJECT_ROOT))

            # 環境変数の設定
            env = os.environ.copy()
            env.update(
                {
                    "PYTHONPATH": str(PROJECT_ROOT),
                    "AI_VENV_ACTIVE": "1",
                    "AI_AUTO_GIT_DISABLED": "false",  # 開発用はGit有効
                    "ANTHROPIC_API_KEY": self.config.ANTHROPIC_API_KEY,
                }
            )

            # --print フラグ使用時はstdinを使わない
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=work_dir,
                timeout=600,  # タイムアウトを10分に延長
                env=env,
            )

            if result.returncode == 0:
                self.logger.info(f"{EMOJI['success']} Claude execution completed")
                return {
                    "success": True,
                    "output": result.stdout,
                    "error": None,
                    "session_name": session_name,
                }
            else:
                self.logger.error(f"{EMOJI['error']} Claude execution failed")
                return {
                    "success": False,
                    "output": result.stdout,
                    "error": result.stderr,
                    "session_name": session_name,
                }

        except subprocess.TimeoutExpired:
            # Handle specific exception case
            self.logger.error(f"{EMOJI['error']} Claude execution timeout")
            return {
                "success": False,
                "output": None,
                "error": "Execution timeout after 300 seconds",
                "session_name": session_name,
            }
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"{EMOJI['error']} Claude execution error: {str(e)}")
            return {
                "success": False,
                "output": None,
                "error": str(e),
                "session_name": session_name,
            }

    def _record_task_start(
        self, task_id: str, task_type: str, prompt: str, generated_prompt: str
    ):
        """タスク開始を記録"""
        try:
            if self.task_history_db:
                self.task_history_db.add_task(
                    task_id=task_id,
                    worker=self.worker_id,
                    prompt=prompt,
                    model=self.model,
                    task_type=task_type,
                    request_content=generated_prompt,
                )
        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"Failed to record task start: {e}")

    def _handle_success(self, task_id: str, task: dict, result: dict):
        """成功時の処理"""
        # 作成されたファイルを収集
        created_files = self._collect_created_files(task_id)

        # タスク履歴を更新
        self._update_task_history(task_id, "completed", result["output"], created_files)

        # PMWorkerに送信
        pm_message = {
            "task_id": task_id,
            "status": "completed",
            "files": created_files,
            "output": result["output"],

        }

        self.send_result(pm_message)

        # Slack通知（エラー時でも処理を続行）
        try:
            self.slack_notifier.send_success(

                details={
                    "Files created": len(created_files),

                },
            )
        except Exception as notification_error:
            # Handle specific exception case
            self.logger.warning(
                f"Failed to send Slack success notification: {notification_error}"
            )

        self.logger.info(
            f"{EMOJI['success']} Task {task_id} completed with {len(created_files)} files"
        )

    def _handle_failure(self, task_id: str, task: dict, result: dict):
        """失敗時の処理"""
        # タスク履歴を更新
        self._update_task_history(
            task_id, "failed", result.get("output"), [], result["error"]
        )

        # エラー結果を送信
        error_message = {
            "task_id": task_id,
            "status": "failed",
            "error": result["error"],
            "output": result.get("output"),

        }

        self.send_result(error_message)

        # Slack通知（エラー時でも処理を続行）
        try:
            self.slack_notifier.send_error(
                f"Task {task_id} failed", error=result["error"]
            )
        except Exception as notification_error:
            # Handle specific exception case
            self.logger.warning(
                f"Failed to send Slack error notification: {notification_error}"
            )

        self.logger.error(f"{EMOJI['error']} Task {task_id} failed: {result['error']}")

    def _collect_created_files(self, task_id: str) -> list:
        """作成されたファイルを収集"""
        created_files = []

        try:
            # outputディレクトリ内のファイルを検索
            for file_path in self.output_dir.rglob("*"):
                try:
                    if file_path.is_file():
                        # 最近作成されたファイルをチェック
                        if (
                            datetime.now()
                            - datetime.fromtimestamp(file_path.stat().st_mtime)
                        ).seconds < 600:
                            created_files.append(
                                {
                                    "path": str(file_path.relative_to(PROJECT_ROOT)),
                                    "size": file_path.stat().st_size,
                                    "created": datetime.fromtimestamp(
                                        file_path.stat().st_mtime
                                    ).isoformat(),
                                }
                            )
                except (OSError, PermissionError) as e:
                    # 権限エラーや読み取りエラーを無視して継続
                    self.logger.warning(f"Unable to access file {file_path}: {e}")
                    continue
        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"Error collecting files: {e}")

        return created_files

    def _update_task_history(
        self, task_id: str, status: str, response: str, files: list, error: str = None
    ):
        """タスク履歴を更新"""
        try:
            if self.task_history_db:
                # Claudeの要約を抽出
                summary = self._extract_summary(response) if response else None

                self.task_history_db.update_task(
                    task_id=task_id,
                    status=status,
                    response=response,
                    files_created=json.dumps(files) if files else None,
                    summary=summary,
                    error=error,
                )
        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"Failed to update task history: {e}")

    def _extract_summary(self, response: str) -> str:
        """レスポンスから要約を抽出"""
        if not response:
            return "No response"

        # 最初の数行を要約として使用
        lines = response.strip().split("\n")
        summary_lines = []

        for line in lines[:5]:
            # Process each item in collection
            if line.strip():
                summary_lines.append(line.strip())

        return " ".join(summary_lines)[:200]

    def _send_error_result(self, task_id: str, error: str):
        """エラー結果を送信"""
        error_message = {
            "task_id": task_id,
            "status": "error",
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }

        self.send_result(error_message)

    # ========== 🌳 Elder Tree Integration Methods ==========

    async def consult_task_sage(self, task_data: dict) -> dict:
        """タスク賢者に複雑なタスクの最適化を相談"""
        try:
            if not self.four_sages:
                self.logger.warning("4賢者システムが利用できません")
                return {"available": False, "advice": None}

            # タスク賢者への相談
            consultation_request = {
                "task_id": task_data.get("id", "unknown"),
                "task_type": task_data.get("type", "general"),
                "priority": task_data.get("priority", "normal"),
                "complexity": self._assess_task_complexity(task_data),
                "resource_requirements": self._estimate_resource_requirements(
                    task_data
                ),
                "deadline": task_data.get("deadline"),
                "dependencies": task_data.get("dependencies", []),
            }

            # 4賢者統合システムを通じてタスク賢者に相談
            sage_response = await self.four_sages.coordinate_learning_session(
                {
                    "type": "task_optimization",
                    "data": consultation_request,
                    "requesting_worker": self.worker_id,
                }
            )

            # タスク賢者からの具体的なアドバイスを抽出
            task_advice = {
                "available": True,
                "optimization_suggestions": sage_response.get("learning_outcome", {}),
                "recommended_approach": self._extract_task_approach(sage_response),
                "resource_optimization": self._extract_resource_optimization(
                    sage_response
                ),
                "execution_strategy": self._extract_execution_strategy(sage_response),
                "risk_mitigation": self._extract_risk_mitigation(sage_response),
                "consultation_confidence": sage_response.get(
                    "consensus_reached", False
                ),
            }

            # エルダーツリーへの報告
            if self.elder_tree:
                await self._report_to_elder_tree(
                    "task_sage_consultation",
                    "task_sage",
                    {
                        "task_id": task_data.get("id"),
                        "consultation_result": task_advice,
                        "worker_id": self.worker_id,
                    },
                )

            self.logger.info(
                f"{EMOJI['sage']} タスク賢者からのアドバイス受領: {task_advice['recommended_approach']}"
            )

            return task_advice

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"タスク賢者相談エラー: {e}")
            return {"available": False, "error": str(e)}

    async def report_task_execution_to_knowledge_sage(
        self, task_id: str, task_data: dict, result: dict
    ) -> bool:
        """タスク実行結果をナレッジ賢者に報告"""
        try:
            if not self.four_sages:
                return False

            # 実行結果の分析
            execution_analysis = {
                "task_id": task_id,
                "task_type": task_data.get("type", "general"),
                "execution_time": result.get("execution_time"),
                "success": result.get("success", False),
                "output_quality": self._assess_output_quality(result),
                "techniques_used": self._extract_techniques_used(result),
                "challenges_encountered": self._extract_challenges(result),
                "solutions_applied": self._extract_solutions(result),
                "lessons_learned": self._extract_lessons_learned(result),
                "knowledge_patterns": self._identify_knowledge_patterns(
                    task_data, result
                ),
                "worker_id": self.worker_id,
                "timestamp": datetime.now().isoformat(),
            }

            # ナレッジ賢者への学習データ送信
            learning_result = await self.four_sages.coordinate_learning_session(
                {
                    "type": "execution_learning",
                    "data": execution_analysis,
                    "requesting_worker": self.worker_id,
                }
            )

            # エルダーツリーへの報告
            if self.elder_tree:
                await self._report_to_elder_tree(
                    "knowledge_sage_learning",
                    "knowledge_sage",
                    {
                        "task_id": task_id,
                        "learning_data": execution_analysis,
                        "learning_result": learning_result,
                        "worker_id": self.worker_id,
                    },
                )

            self.logger.info(f"{EMOJI['sage']} ナレッジ賢者への学習データ送信完了: {task_id}")

            return learning_result.get("consensus_reached", False)

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"ナレッジ賢者報告エラー: {e}")
            return False

    async def escalate_critical_failure_to_incident_sage(
        self, task_id: str, error_data: dict
    ) -> dict:
        """重要なタスク失敗をインシデント賢者に報告"""
        try:
            if not self.four_sages:
                return {"escalated": False, "reason": "4賢者システムが利用できません"}

            # インシデント分析
            incident_analysis = {
                "incident_id": f"task_failure_{task_id}_{int(datetime.now().timestamp())}",
                "task_id": task_id,
                "worker_id": self.worker_id,
                "error_type": error_data.get("error_type", "unknown"),
                "error_message": error_data.get("error", "No error message"),
                "severity": self._assess_error_severity(error_data),
                "impact_scope": self._assess_impact_scope(error_data),
                "system_state": self._capture_system_state(),

                "context": error_data.get("context", {}),
                "timestamp": datetime.now().isoformat(),
            }

            # インシデント賢者への報告
            incident_response = await self.four_sages.coordinate_learning_session(
                {
                    "type": "incident_analysis",
                    "data": incident_analysis,
                    "requesting_worker": self.worker_id,
                }
            )

            # 緊急度に応じてエルダー評議会へのエスカレーション
            if incident_analysis["severity"] == "critical":
                await self._escalate_to_elder_council(incident_analysis)

            # エルダーツリーへの報告
            if self.elder_tree:
                await self._report_to_elder_tree(
                    "incident_sage_escalation",
                    "incident_sage",
                    {
                        "incident_id": incident_analysis["incident_id"],
                        "task_id": task_id,
                        "incident_data": incident_analysis,
                        "sage_response": incident_response,
                        "worker_id": self.worker_id,
                    },
                )

            escalation_result = {
                "escalated": True,
                "incident_id": incident_analysis["incident_id"],
                "sage_response": incident_response,
                "auto_recovery_recommended": incident_response.get(
                    "learning_outcome", {}
                ).get("auto_recovery", False),
                "manual_intervention_required": incident_analysis["severity"]
                in ["critical", "high"],
            }

            self.logger.error(
                f"{EMOJI['sage']} インシデント賢者への重要エスカレーション: {incident_analysis['incident_id']}"
            )

            return escalation_result

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"インシデント賢者エスカレーションエラー: {e}")
            return {"escalated": False, "error": str(e)}

    async def enhance_prompt_with_rag_sage(
        self, user_prompt: str, task_context: dict
    ) -> str:
        """RAG賢者を使用してプロンプトを強化"""
        try:
            if not self.four_sages:
                return user_prompt  # RAG賢者が利用できない場合は元のプロンプトを返す

            # RAG賢者への知識検索要求
            rag_request = {
                "query": user_prompt,
                "task_context": task_context,
                "search_depth": "comprehensive",
                "include_patterns": True,
                "include_examples": True,
                "include_best_practices": True,
                "worker_id": self.worker_id,
            }

            # RAG賢者による知識検索と分析
            rag_response = await self.four_sages.coordinate_learning_session(
                {
                    "type": "rag_enhancement",
                    "data": rag_request,
                    "requesting_worker": self.worker_id,
                }
            )

            # プロンプト強化
            enhanced_prompt = self._build_enhanced_prompt(
                user_prompt, rag_response.get("learning_outcome", {}), task_context
            )

            # エルダーツリーへの報告
            if self.elder_tree:
                await self._report_to_elder_tree(
                    "rag_sage_enhancement",
                    "rag_sage",
                    {
                        "original_prompt_length": len(user_prompt),
                        "enhanced_prompt_length": len(enhanced_prompt),
                        "enhancement_quality": rag_response.get(
                            "consensus_reached", False
                        ),
                        "worker_id": self.worker_id,
                    },
                )

            self.logger.info(
                f"{EMOJI['sage']} RAG賢者によるプロンプト強化完了: {len(user_prompt)} -> {len(enhanced_prompt)} characters"
            )

            return enhanced_prompt

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"RAG賢者プロンプト強化エラー: {e}")
            return user_prompt  # エラー時は元のプロンプトを返す

    async def _report_to_elder_tree(
        self, report_type: str, sage_type: str, content: dict
    ) -> bool:
        """エルダーツリーへの報告"""
        try:
            if not self.elder_tree:
                return False

            # エルダーメッセージの作成
            message = ElderMessage(
                sender_rank=ElderRank.SERVANT,  # TaskWorkerはサーバントレベル
                sender_id=f"task_worker_{self.worker_id}",
                recipient_rank=ElderRank.SAGE,
                recipient_id=sage_type,
                message_type=report_type,
                content=content,
                priority="high" if report_type.endswith("_escalation") else "normal",
            )

            # メッセージ送信
            success = await self.elder_tree.send_message(message)

            if success:
                self.logger.info(f"🌳 エルダーツリー報告完了: {report_type} -> {sage_type}")
            else:
                self.logger.warning(f"🌳 エルダーツリー報告失敗: {report_type}")

            return success

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"エルダーツリー報告エラー: {e}")
            return False

    async def _escalate_to_elder_council(self, incident_data: dict) -> bool:
        """重要事項をエルダー評議会にエスカレーション"""
        try:
            if not self.elder_council:
                return False

            # エルダー評議会への緊急召集要求
            escalation_request = {
                "urgency": "critical",
                "category": "task_execution_failure",
                "incident_data": incident_data,
                "requesting_worker": self.worker_id,
                "timestamp": datetime.now().isoformat(),
            }

            # エルダー評議会召集システムに通知
            council_response = self.elder_council.force_trigger_evaluation()

            self.logger.critical(
                f"🏛️ エルダー評議会への緊急エスカレーション: {incident_data['incident_id']}"
            )

            return True

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"エルダー評議会エスカレーションエラー: {e}")
            return False

    # ========== Helper Methods for Elder Tree Integration ==========

    def _assess_task_complexity(self, task_data: dict) -> str:
        """タスクの複雑度を評価"""
        complexity_score = 0

        # プロンプトの長さ
        prompt_length = len(task_data.get("prompt", ""))
        if prompt_length > 1000:
            complexity_score += 3
        elif prompt_length > 500:
            complexity_score += 2
        elif prompt_length > 200:
            complexity_score += 1

        # 複雑度キーワード
        complex_keywords = [
            "architecture",
            "integration",
            "migration",
            "optimization",
            "complex",
            "advanced",
        ]
        prompt_lower = task_data.get("prompt", "").lower()
        for keyword in complex_keywords:
            # Process each item in collection
            if keyword in prompt_lower:
                complexity_score += 2
                break

        # 依存関係の数
        dependencies = task_data.get("dependencies", [])
        if len(dependencies) > 5:
            complexity_score += 3
        elif len(dependencies) > 2:
            complexity_score += 2
        elif len(dependencies) > 0:
            complexity_score += 1

        if complexity_score >= 6:
            return "high"
        elif complexity_score >= 3:
            return "medium"
        else:
            return "low"

    def _estimate_resource_requirements(self, task_data: dict) -> dictprompt = task_data.get("prompt", "").lower():
    """スクのリソース要求を推定"""

        # CPU要求度
        cpu_intensive = any(
            word in prompt for word in ["compile", "build", "analyze", "process"]
        )

        # メモリ要求度
        memory_intensive = any(
            word in prompt for word in ["large", "massive", "dataset", "database"]
        )

        # ネットワーク要求度
        network_intensive = any(
            word in prompt for word in ["api", "download", "upload", "web"]
        )

        return {:
            "cpu_requirement": "high" if cpu_intensive else "medium",
            "memory_requirement": "high" if memory_intensive else "medium",
            "network_requirement": "high" if network_intensive else "low",
            "estimated_duration": self._estimate_task_duration(task_data),
        }

    def _estimate_task_duration(self, task_data: dict) -> strcomplexity = self._assess_task_complexity(task_data)prompt_length = len(task_data.get("prompt", ""))
    """スクの推定実行時間"""
:
        if complexity == "high" or prompt_length > 1000:
            # Complex condition - consider breaking down
            return "10-30 minutes"
        elif complexity == "medium" or prompt_length > 500:
            # Complex condition - consider breaking down
            return "5-15 minutes"
        else:
            return "2-10 minutes"

    def _extract_task_approach(self, sage_response: dict) -> strlearning_outcome = sage_response.get("learning_outcome", {})if isinstance(learning_outcome, dict):
    """スクアプローチの抽出""":
            return learning_outcome.get(
                "recommended_approach", "Standard iterative approach"
            )
        return "Standard iterative approach"

    def _extract_resource_optimization(self, sage_response: dict) -> dictlearning_outcome = sage_response.get("learning_outcome", {})if isinstance(learning_outcome, dict)return learning_outcome.get("resource_optimization", {})
    """ソース最適化の抽出""":
        return {"cpu_optimization": "standard", "memory_optimization": "standard"}

    def _extract_execution_strategy(self, sage_response: dict) -> strlearning_outcome = sage_response.get("learning_outcome", {})if isinstance(learning_outcome, dict)return learning_outcome.get("execution_strategy", "Sequential execution")
    """行戦略の抽出""":
        return "Sequential execution"

    def _extract_risk_mitigation(self, sage_response: dict) -> listlearning_outcome = sage_response.get("learning_outcome", {})if isinstance(learning_outcome, dict)return learning_outcome.get("risk_mitigation", [])
    """スク軽減策の抽出""":
        return ["Monitor execution closely", "Implement fallback procedures"]

    def _assess_output_quality(self, result: dict) -> floatif not result.get("success", False):
    """出力品質の評価"""
            return 0.0

        output = result.get("output", "")
        if not output:
            return 0.2

        # 出力の長さに基づく基本スコア
        base_score = min(len(output) / 1000, 0.8)

        # エラーメッセージの有無
        if "error" in output.lower():
            base_score *= 0.7

        # 成功指標
        if any(word in output.lower() for word in ["completed", "success", "finished"]):
            # Complex condition - consider breaking down
            base_score += 0.2

        return min(base_score, 1.0)

    def _extract_techniques_used(self, result: dict) -> listoutput = result.get("output", "").lower():
    """用されたテクニックの抽出"""
        techniques = []
:
        if "claude" in output:
            techniques.append("Claude AI processing")

        if "rag" in output:
            techniques.append("RAG knowledge retrieval")
        if "optimization" in output:
            techniques.append("Code optimization")

        return techniques if techniques else ["Standard processing"]

    def _extract_challenges(self, result: dict) -> listoutput = result.get("output", "").lower()error = result.get("error", "").lower()
    """遇した課題の抽出"""

        challenges = []
:
        if "timeout" in output or "timeout" in error:
            # Complex condition - consider breaking down
            challenges.append("Execution timeout")
        if "memory" in error:
            challenges.append("Memory constraints")
        if "permission" in error:
            challenges.append("Permission issues")
        if "network" in error:
            challenges.append("Network connectivity")

        return challenges if challenges else ["No significant challenges"]

    def _extract_solutions(self, result: dict) -> listoutput = result.get("output", "").lower():
    """用された解決策の抽出"""

        solutions = []
:
        if "retry" in output:
            solutions.append("Automatic retry mechanism")
        if "fallback" in output:
            solutions.append("Fallback procedure")
        if "optimization" in output:
            solutions.append("Performance optimization")

        return solutions if solutions else ["Standard execution flow"]

    def _extract_lessons_learned(self, result: dict) -> list:
        """学習した教訓の抽出"""
        lessons = []

        if not result.get("success", False):
            lessons.append("Error handling improvement needed")

        if result.get("execution_time", 0) > 300:  # 5分以上
            lessons.append("Long execution time requires optimization")

        output = result.get("output", "")
        if len(output) > 5000:
            lessons.append("Large output requires summary generation")

        return lessons if lessons else ["Task completed within normal parameters"]

    def _identify_knowledge_patterns(self, task_data: dict, result: dict) -> list:
        """知識パターンの特定"""
        patterns = []

        task_type = task_data.get("type", "general")
        prompt = task_data.get("prompt", "").lower()

        if task_type == "code_generation":
            if "python" in prompt:
                patterns.append("Python code generation")
            if "web" in prompt:
                patterns.append("Web development")
            if "api" in prompt:
                patterns.append("API development")

        if result.get("success", False):
            patterns.append("Successful task completion")
        else:
            patterns.append("Task failure recovery")

        return patterns if patterns else ["General task processing"]

    def _assess_error_severity(self, error_data: dict) -> strerror_message = error_data.get("error", "").lower():
    """ラーの重要度を評価"""
:
        if any(word in error_message for word in ["critical", "fatal", "system"]):
            # Complex condition - consider breaking down
            return "critical"
        elif any(word in error_message for word in ["timeout", "memory", "resource"]):
            # Complex condition - consider breaking down
            return "high"
        elif any(
            word in error_message for word in ["permission", "access", "connection"]
        ):
            return "medium"
        else:
            return "low"

    def _assess_impact_scope(self, error_data: dict) -> strerror_message = error_data.get("error", "").lower():
    """ラーの影響範囲を評価"""
:
        if any(word in error_message for word in ["system", "service", "database"]):
            # Complex condition - consider breaking down
            return "system_wide"
        elif any(word in error_message for word in ["worker", "process", "queue"]):
            # Complex condition - consider breaking down
            return "service_level"
        else:
            return "task_level"

    def _capture_system_state(self) -> dict:
        """システム状態のキャプチャ"""
        import psutil

        try:
            return {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
                "worker_status": self.get_status(),
                "timestamp": datetime.now().isoformat(),
            }
        except:
            return {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0,
                "worker_status": "unknown",
                "timestamp": datetime.now().isoformat(),
            }

    def _build_enhanced_prompt(
        self, original_prompt: str, rag_outcome: dict, task_context: dict
    ) -> str:
        """RAG知識を使用してプロンプトを強化"""
        enhanced_prompt = original_prompt

        # RAGからの知識追加
        if isinstance(rag_outcome, dict) and "knowledge_enhancement" in rag_outcome:
            # Complex condition - consider breaking down
            knowledge = rag_outcome["knowledge_enhancement"]
            enhanced_prompt += f"\n\n## Related Knowledge:\n{knowledge}"

        # ベストプラクティス追加
        if isinstance(rag_outcome, dict) and "best_practices" in rag_outcome:
            # Complex condition - consider breaking down
            practices = rag_outcome["best_practices"]
            enhanced_prompt += f"\n\n## Best Practices:\n{practices}"

        # 例の追加
        if isinstance(rag_outcome, dict) and "examples" in rag_outcome:
            # Complex condition - consider breaking down
            examples = rag_outcome["examples"]
            enhanced_prompt += f"\n\n## Examples:\n{examples}"

        return enhanced_prompt

    # 実行
    def cleanup(self):
        """Cleanup resources including RAG integration"""
        if self.rag_integration:
            try:
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.rag_integration.cleanup())
                loop.close()
                self.logger.info(f"{EMOJI['info']} RAG Grimoire Integration cleaned up")
            except Exception as e:
                # Handle specific exception case
                self.logger.error(f"{EMOJI['error']} Error during RAG cleanup: {e}")

        # Additional cleanup logic can be added here
        pass

    def stop(self):
        """ワーカーの停止処理"""
        try:
            # RAGクリーンアップ
            self.cleanup()

            # BaseWorkerの停止処理を呼び出し
            super().stop()

            self.logger.info(
                f"{EMOJI['info']} Enhanced TaskWorker stopped successfully"
            )
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"{EMOJI['error']} Error during stop: {e}")

    def initialize(self) -> Noneself.logger.info(f"{EMOJI['start']} Initializing {self.__class__.__name__}..."):
    """ーカーの初期化処理"""

        # 設定の妥当性を確認:
        if not self.validate_config():
            raise ValueError("Configuration validation failed")

        # 出力ディレクトリの作成
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # プロンプトテンプレートシステムの初期化
        try:

        except Exception as e:
            # Handle specific exception case
            self.logger.warning(

            )

        # RAG統合の初期化（非同期）
        self._initialize_rag_integration()

        # Slack通知の初期化確認
        try:
            if hasattr(self.slack_notifier, "test_connection"):
                self.slack_notifier.test_connection()
            self.logger.info(f"{EMOJI['success']} Slack notifier initialized")
        except Exception as e:
            # Handle specific exception case
            self.logger.warning(
                f"{EMOJI['warning']} Slack notifier initialization failed: {e}"
            )

        self.logger.info(
            f"{EMOJI['success']} {self.__class__.__name__} initialization completed"
        )

    def _execute_claude_cli(self, task: dict) -> str:
        """Claude CLIを実行（テスト用メソッド）"""
        # テスト用に_execute_claudeを呼び出し
        result = self._execute_claude(task.get("id", "test"), task.get("prompt", ""))
        if result["success"]:
            return result["output"]
        else:
            raise Exception(result["error"])

    def _send_result(self, result_data: dict)return self.send_result(result_data)
    """結果を送信（テスト用メソッド）"""

    def _extract_created_files(self, output: str) -> list:
        """作成されたファイルを抽出（テスト用メソッド）"""
        import re

        files = []

        # ファイル作成パターンを検索
        patterns = [
            r"Creating file:\s*([^\n]+)",
            r"Writing to file:\s*([^\n]+)",
            r"Created\s+([^\n]+\.[a-zA-Z0-9]+)",
            r"Wrote\s+([^\n]+\.[a-zA-Z0-9]+)",
        ]

        for pattern in patterns:
            # Process each item in collection
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                # Process each item in collection
                filename = match.strip()
                if filename and filename not in files:
                    # Complex condition - consider breaking down
                    files.append(filename)

        return files

    def handle_error(self, error: Exception, context: dict = None, severity=None):
        """エラー処理メソッド"""
        if context is None:
            context = {}

        # エラー情報をログに記録
        self.logger.error(
            f"Error in {context.get('operation', 'unknown')}: {str(error)}"
        )

        # Slack通知を送信（エラー発生時でも処理を続行）
        try:
            self.slack_notifier.send_error(
                f"Enhanced TaskWorker Error", error=str(error), context=context
            )
        except Exception as notification_error:
            # Handle specific exception case
            self.logger.warning(
                f"Failed to send Slack notification: {notification_error}"
            )

        # 重要度に応じた処理
        if severity and hasattr(severity, "value"):
            # Complex condition - consider breaking down
            if severity.value >= 3:  # HIGH以上
                self.logger.critical(f"High severity error: {str(error)}")

        return False

    def get_status(self)base_status = self.health_check()
    """ワーカーの状態を取得（Elder Tree統合対応）"""

        # 🌳 Elder Tree Integration: Elder系システムのステータス
        elder_status = {
            "four_sages_available": self.four_sages is not None,
            "elder_council_available": self.elder_council is not None,
            "elder_tree_available": self.elder_tree is not None,
            "elder_integration_enabled": ELDER_INTEGRATION_AVAILABLE,
        }

        # Elder Tree階層ステータス詳細
        if self.elder_tree:
            try:
                elder_tree_details = {
                    "elder_tree_status": "active",
                    "hierarchy_levels": [
                        "Grand Elder",
                        "Claude Elder",
                        "Sages",
                        "Council",
                        "Servants",
                    ],
                    "current_worker_level": "Servant",
                    "message_queue_status": "operational",
                }
                elder_status.update(elder_tree_details)
            except Exception as e:
                # Handle specific exception case
                elder_status["elder_tree_error"] = str(e)

        # 4賢者統合ステータス
        if self.four_sages:
            try:
                sage_status = {
                    "knowledge_sage_status": "active",
                    "task_sage_status": "active",
                    "incident_sage_status": "active",
                    "rag_sage_status": "active",
                    "sage_coordination_status": "operational",
                }
                elder_status.update(sage_status)
            except Exception as e:
                # Handle specific exception case
                elder_status["four_sages_error"] = str(e)

        # エルダー評議会ステータス
        if self.elder_council:
            try:
                council_status = {
                    "elder_council_status": "standby",
                    "escalation_ready": True,
                    "trigger_monitoring": "active",
                }
                elder_status.update(council_status)
            except Exception as e:
                # Handle specific exception case
                elder_status["elder_council_error"] = str(e)

        # 拡張ステータス情報を追加
        enhanced_status = {
            **base_status,

            else 0,
            "rag_integration": self.rag_integration is not None,
            "allowed_tools": len(self.allowed_tools),
            "model": self.model,
            "last_prompt_score": getattr(self, "last_prompt_score", None),
            "elder_tree_integration": elder_status,
        }

        return enhanced_status

    def validate_config(self):
        """設定の妥当性を検証"""
        validation_errors = []

        # 必須設定の確認
        required_attrs = ["ANTHROPIC_API_KEY"]
        for attr in required_attrs:
            if not hasattr(self.config, attr) or not getattr(self.config, attr):
                # Complex condition - consider breaking down
                validation_errors.append(f"Missing required config: {attr}")

        # モデルの妥当性確認
        valid_models = ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022"]
        if self.model not in valid_models:
            validation_errors.append(f"Invalid model: {self.model}")

        # ツールの妥当性確認
        valid_tools = [
            "Edit",
            "Write",
            "Read",
            "MultiEdit",
            "Bash",
            "Glob",
            "Grep",
            "LS",
            "WebFetch",
            "WebSearch",
            "NotebookRead",
            "NotebookEdit",

            "Task",
            "exit_plan_mode",
        ]
        invalid_tools = [tool for tool in self.allowed_tools if tool not in valid_tools]
        if invalid_tools:
            validation_errors.append(f"Invalid tools: {invalid_tools}")

        # ディレクトリの存在確認
        if not self.output_dir.exists():
            validation_errors.append(
                f"Output directory does not exist: {self.output_dir}"
            )

        if validation_errors:
            self.logger.error(f"Configuration validation failed: {validation_errors}")
            return False

        self.logger.info("Configuration validation passed")
        return True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(

    )
    parser.add_argument("--worker-id", help="Worker ID")
    parser.add_argument("--test", action="store_true", help="Test mode")

    args = parser.parse_args()

    if args.test:
        # テストモード
        print(f"{EMOJI['info']} Running in test mode...")
        worker = EnhancedTaskWorker(worker_id="test-worker")

        # 利用可能なテンプレート表示

            print(

            )

        # テストプロンプト生成
        test_prompt = worker.generate_prompt(

            variables={
                "task_id": "test_001",
                "task_type": "code",
                "user_prompt": "Create a Python web scraper",
                "language": "Python",
            },
            include_rag=False,
        )

        print(f"\nGenerated test prompt:\n{test_prompt[:300]}...")
        print(f"\n{EMOJI['success']} Test completed successfully")
    else:
        # 本番モード
        worker = EnhancedTaskWorker(worker_id=args.worker_id)
        print(

        )
        print(f"{EMOJI['info']} Worker ID: {worker.worker_id}")
        print(f"{EMOJI['info']} Input queue: {worker.input_queue}")
        print(f"{EMOJI['info']} Output queue: {worker.output_queue}")

        try:
            worker.start()
        except KeyboardInterrupt:
            # Handle specific exception case
            print(f"\n{EMOJI['warning']} Worker stopped by user")
        except Exception as e:
            # Handle specific exception case
            print(f"{EMOJI['error']} Worker error: {str(e)}")
            raise
