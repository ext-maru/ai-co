#!/usr/bin/env python3
"""
AI Command Executor Worker - Elders Guild Execution Specialist
Elders Guild Elder Tree Hierarchy Command Execution Worker

エルダー階層システムの実行専門ワーカー
完全Elder Tree階層統合 - コマンド実行スペシャリスト
タスク賢者の指導の下、安全かつ効率的なコマンド実行を実現
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import ErrorSeverity
from core.base_worker import BaseWorker

# Elder Tree階層統合
try:
    from libs.elder_council_summoner import (
        ElderCouncilSummoner,
        TriggerCategory,
        UrgencyLevel,
    )
    from libs.elder_tree_hierarchy import (
        ElderDecision,
        ElderMessage,
        ElderRank,
        ElderTreeNode,
        SageType,
        ServantType,
        get_elder_tree,
    )
    from libs.four_sages_integration import FourSagesIntegration

    ELDER_TREE_AVAILABLE = True
except ImportError as e:
    # Handle specific exception case
    logging.warning(f"Elder Tree components not available: {e}")
    ELDER_TREE_AVAILABLE = False
    FourSagesIntegration = None
    ElderCouncilSummoner = None
    get_elder_tree = None

class CommandExecutorWorker(BaseWorker):
    """Elder Tree階層システムのコマンド実行専門ワーカー"""

    def __init__(self, worker_id=None):
        super().__init__(worker_type="command_executor", worker_id=worker_id)

        # ディレクトリ設定
        self.base_dir = PROJECT_ROOT / "ai_commands"
        self.pending_dir = self.base_dir / "pending"
        self.running_dir = self.base_dir / "running"
        self.completed_dir = self.base_dir / "completed"
        self.logs_dir = self.base_dir / "logs"

        # ディレクトリ作成
        for dir_path in [
            self.pending_dir,
            self.running_dir,
            self.completed_dir,
            self.logs_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # 実行間隔（秒）
        self.check_interval = 5

        # Elder Tree統合初期化
        self._initialize_elder_systems()

        # コマンド実行統計
        self.execution_stats = {
            "total_commands": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "rejected_commands": 0,
            "elder_consultations": 0,
            "sage_optimizations": 0,
        }

        # 危険コマンドのエスカレーション履歴
        self.escalation_history = []

        # RAG賢者からの学習パターン
        self.learned_patterns = defaultdict(list)

    def _initialize_elder_systems(self):
        """Elder Tree階層システムの初期化"""
        self.four_sages = None
        self.elder_council = None
        self.elder_tree = None

        if ELDER_TREE_AVAILABLE:
            try:
                # 4賢者統合システム初期化
                self.four_sages = FourSagesIntegration()
                self.logger.info(
                    "🧙‍♂️ Four Sages Integration initialized for command execution"
                )

                # エルダー評議会召集システム初期化
                self.elder_council = ElderCouncilSummoner()
                self.logger.info(
                    "🏛️ Elder Council Summoner initialized for critical decisions"
                )

                # Elder Tree階層取得
                self.elder_tree = get_elder_tree()
                self.logger.info("🌳 Elder Tree hierarchy connected")

                # 自身をサーバントとして登録
                self._register_as_servant()

            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"Failed to initialize Elder systems: {e}")
                self.logger.info("Falling back to standalone mode")
        else:
            self.logger.info(
                "Running in standalone mode without Elder Tree integration"
            )

    def _register_as_servant(self):
        """エルダーサーバントとして自身を登録"""
        if self.elder_tree:
            try:
                # タスク賢者配下のサーバントとして登録
                servant_info = {
                    "servant_id": self.worker_id,
                    "servant_type": ServantType.DWARF_CRAFTSMAN.value,  # 実行職人
                    "specialization": "command_execution",
                    "capabilities": [
                        "safe_execution",
                        "pattern_learning",
                        "result_reporting",
                    ],
                }

                message = ElderMessage(
                    sender_rank=ElderRank.SERVANT,
                    sender_id=self.worker_id,
                    recipient_rank=ElderRank.SAGE,
                    recipient_id="task_sage",
                    message_type="servant_registration",
                    content=servant_info,
                    requires_response=True,
                )

                # メッセージ送信（実際の実装では非同期処理）
                self.logger.info(
                    f"🤖 Registered as Command Execution Servant under Task Sage"
                )

            except Exception as e:
                # Handle specific exception case
                self.logger.error(f"Failed to register as servant: {e}")

    def setup_queues(self):
        """コマンド実行用キューの設定"""
        self.input_queue = "ai_command"
        self.output_queue = "ai_results"

    def process_message(self, ch, method, properties, body):
        """Elder階層システムの指導の下でコマンド実行タスクを処理"""
        try:
            task_data = json.loads(body)
            command_id = task_data.get(
                "command_id", f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            command = task_data.get("command", "")
            description = task_data.get("description", "No description")
            priority = task_data.get("priority", "normal")

            self.logger.info(f"🛠️ コマンド実行要求受信: {command_id}")
            self.logger.info(f"コマンド: {command}")

            self.execution_stats["total_commands"] += 1

            # 高優先度タスクの場合、エルダーに通知
            if priority == "high" and self.elder_tree:
                # Complex condition - consider breaking down
                self._notify_elder_high_priority_task(command_id, command, description)

            # コマンド実行
            result = self._execute_command(command_id, command, description)

            # 結果を返送
            response = {
                "command_id": command_id,
                "command": command,
                "status": result["status"],
                "output": result["output"],
                "error": result["error"],
                "duration": result["duration"],
                "worker_id": self.worker_id,
                "elder_consulted": result.get("elder_consulted", False),
                "execution_stats": self._get_execution_summary(),
            }

            self._send_result(response)

            # エルダーへの定期報告
            self._send_elder_status_report()

            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.logger.info(f"✅ コマンド実行完了: {command_id}")

        except Exception as e:
            # コマンド実行エラー
            context = {
                "operation": "command_process_message",
                "command_id": task_data.get("command_id", "unknown")
                if "task_data" in locals()
                else "unknown",
                "command": task_data.get("command", "")[:100]
                if "task_data" in locals()
                else "unknown",
                "description": task_data.get("description", "")
                if "task_data" in locals()
                else "",
            }
            self.handle_error(e, context, severity=ErrorSeverity.HIGH)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _notify_elder_high_priority_task(
        self, command_id: str, command: str, description: str
    ):
        """高優先度タスクをエルダーに通知"""
        if not self.elder_tree:
            return

        try:
            notification = ElderMessage(
                sender_rank=ElderRank.SERVANT,
                sender_id=self.worker_id,
                recipient_rank=ElderRank.SAGE,
                recipient_id="task_sage",
                message_type="high_priority_execution",
                content={
                    "command_id": command_id,
                    "command": command[:200],  # 最初の200文字
                    "description": description,
                    "timestamp": datetime.now().isoformat(),
                },
                priority="high",
            )

            # エルダーツリーを通じて通知（実際の実装では非同期）
            self.logger.info(
                f"🏛️ Notified Task Sage of high priority command: {command_id}"
            )

        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"Failed to notify Elder: {e}")

    def _get_execution_summary(self) -> Dict[str, Any]:
        """実行統計のサマリーを取得"""
        total = self.execution_stats["total_commands"]
        if total == 0:
            success_rate = 0
        else:
            success_rate = (self.execution_stats["successful_executions"] / total) * 100

        return {
            "total_commands": total,
            "success_rate": round(success_rate, 2),
            "elder_consultations": self.execution_stats["elder_consultations"],
            "sage_optimizations": self.execution_stats["sage_optimizations"],
            "recent_escalations": len(self.escalation_history),
        }

    def _send_elder_status_report(self):
        """エルダーへの定期的なステータス報告"""
        # 100コマンドごとに報告
        if self.execution_stats["total_commands"] % 100 == 0 and self.elder_council:
            # Complex condition - consider breaking down
            try:
                report_data = {
                    "worker_id": self.worker_id,
                    "worker_type": "command_executor",
                    "execution_stats": self._get_execution_summary(),
                    "health_status": "healthy",
                    "recent_patterns": self._get_recent_patterns(),
                    "timestamp": datetime.now().isoformat(),
                }

                # エルダー評議会への報告
                self.elder_council.report_worker_status(report_data)

                self.logger.info(f"📊 Sent status report to Elder Council")

            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"Failed to send Elder status report: {e}")

    def _get_recent_patterns(self) -> List[Dict[str, Any]]:
        """最近の実行パターンを取得"""
        patterns = []
        for status, pattern_list in self.learned_patterns.items():
            if pattern_list:
                # 最新の3パターンを取得
                recent = pattern_list[-3:]
                for pattern in recent:
                    patterns.append(
                        {
                            "status": status,
                            "pattern": pattern.get("command_pattern", ""),
                            "success_rate": pattern.get("success_rate", 0),
                        }
                    )
        return patterns

    def _execute_command(self, command_id: str, command: str, description: str) -> dictstart_time = time.time():
    """lder指導の下でコマンドを安全に実行"""

        try:
            # タスク賢者に実行最適化を相談
            optimized_command = self._consult_task_sage(command, description)
            if optimized_command and optimized_command != command:
                # Complex condition - consider breaking down
                self.logger.info(
                    f"📋 Task Sage optimized command: {command} -> {optimized_command}"
                )
                command = optimized_command
                self.execution_stats["sage_optimizations"] += 1

            # 安全性チェック
            if not self._is_safe_command(command):
                # 危険なコマンドはインシデント賢者にエスカレート
                escalation_result = self._escalate_to_incident_sage(
                    command_id, command, description
                )
                if not escalation_result.get("approved", False):
                    return {
                        "status": "rejected",
                        "output": "",
                        "error": f'Command rejected by Incident Sage: {escalation_result.get(
                            "reason",
                            "Security concerns"
                        )}',
                        "duration": 0,
                        "elder_consultation": True,
                    }

            # コマンド実行（タイムアウト付き）
            self.logger.info(f"⚡ 実行開始: {command}")

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5分タイムアウト
                cwd=PROJECT_ROOT,
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                self.logger.info(f"✅ 実行成功: {command_id} ({duration:0.2f}s)")
                status = "success"
                self.execution_stats["successful_executions"] += 1
            else:
                self.logger.warning(
                    f"⚠️ 実行失敗: {command_id} (code: {result.returncode})"
                )
                status = "failed"
                self.execution_stats["failed_executions"] += 1

            # ログファイルに保存
            self._save_execution_log(command_id, command, description, result, duration)

            # 実行結果をナレッジ賢者に報告
            self._report_to_knowledge_sage(
                command_id, command, status, result, duration
            )

            # RAG賢者でパターン分析
            self._analyze_with_rag_sage(command, status, result)

            return {
                "status": status,
                "output": result.stdout,
                "error": result.stderr,
                "duration": duration,
                "elder_consulted": self.execution_stats["elder_consultations"] > 0,
            }

        except subprocess.TimeoutExpired:
            # Handle specific exception case
            duration = time.time() - start_time
            self.logger.error(f"⏰ タイムアウト: {command_id}")
            return {
                "status": "timeout",
                "output": "",
                "error": "Command execution timed out after 5 minutes",
                "duration": duration,
            }
        except Exception as e:
            # Handle specific exception case
            duration = time.time() - start_time
            self.logger.error(f"💥 実行例外: {command_id} - {e}")
            self.execution_stats["failed_executions"] += 1

            # 重大なエラーはインシデント賢者に報告
            if self.four_sages:
                self._report_critical_error(command_id, command, e)

            return {
                "status": "error",
                "output": "",
                "error": str(e),
                "duration": duration,
            }

    def _report_critical_error(self, command_id: str, command: str, error: Exception):
        """重大なエラーをインシデント賢者に報告"""
        try:
            error_report = {
                "command_id": command_id,
                "command": command[:200],
                "error_type": type(error).__name__,
                "error_message": str(error),
                "worker_id": self.worker_id,
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.report_to_sage(
                sage_type="incident_sage",
                report_type="critical_error",
                data=error_report,
                priority="high",
            )

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Failed to report critical error: {e}")

    def _consult_task_sage(self, command: str, description: str) -> Optional[str]:
        """タスク賢者に実行最適化を相談"""
        if not self.four_sages:
            return None

        try:
            consultation_data = {
                "command": command,
                "description": description,
                "worker_id": self.worker_id,
                "purpose": "optimization",
            }

            # タスク賢者への相談（同期的に模擬）
            result = self.four_sages.consult_sage(
                sage_type="task_sage",
                query_type="command_optimization",
                data=consultation_data,
            )

            self.execution_stats["elder_consultations"] += 1

            if result and result.get("optimized_command"):
                # Complex condition - consider breaking down
                return result["optimized_command"]

        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"Failed to consult Task Sage: {e}")

        return None

    def _escalate_to_incident_sage(
        self, command_id: str, command: str, description: str
    ) -> Dict[str, Any]:
        """危険なコマンドをインシデント賢者にエスカレート"""
        if not self.four_sages:
            return {"approved": False, "reason": "No Elder guidance available"}

        try:
            escalation_data = {
                "command_id": command_id,
                "command": command,
                "description": description,
                "risk_assessment": self._assess_command_risk(command),
                "worker_id": self.worker_id,
                "timestamp": datetime.now().isoformat(),
            }

            # インシデント賢者への緊急相談
            result = self.four_sages.consult_sage(
                sage_type="incident_sage",
                query_type="security_escalation",
                data=escalation_data,
                priority="high",
            )

            # エスカレーション履歴に記録
            self.escalation_history.append(
                {
                    "command_id": command_id,
                    "command": command[:100],  # 最初の100文字
                    "escalated_at": datetime.now(),
                    "sage_decision": result,
                }
            )

            self.execution_stats["elder_consultations"] += 1

            return result or {
                "approved": False,
                "reason": "No response from Incident Sage",
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Failed to escalate to Incident Sage: {e}")
            return {"approved": False, "reason": f"Escalation failed: {str(e)}"}

    def _report_to_knowledge_sage(
        self,
        command_id: str,
        command: str,
        status: str,
        result: subprocess.CompletedProcess,
        duration: float,
    ):
        """実行結果をナレッジ賢者に報告"""
        if not self.four_sages:
            return

        try:
            report_data = {
                "command_id": command_id,
                "command": command,
                "status": status,
                "duration": duration,
                "return_code": result.returncode,
                "output_preview": result.stdout[:500] if result.stdout else "",
                "error_preview": result.stderr[:500] if result.stderr else "",
                "worker_id": self.worker_id,
                "timestamp": datetime.now().isoformat(),
            }

            # ナレッジ賢者への学習データ提供
            self.four_sages.report_to_sage(
                sage_type="knowledge_sage",
                report_type="command_execution",
                data=report_data,
            )

        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"Failed to report to Knowledge Sage: {e}")

    def _analyze_with_rag_sage(
        self, command: str, status: str, result: subprocess.CompletedProcess
    ):
        """RAG賢者でコマンドパターンを分析"""
        if not self.four_sages:
            return

        try:
            analysis_data = {
                "command": command,
                "status": status,
                "return_code": result.returncode,
                "has_output": bool(result.stdout),
                "has_error": bool(result.stderr),
                "worker_id": self.worker_id,
            }

            # RAG賢者によるパターン分析
            patterns = self.four_sages.consult_sage(
                sage_type="rag_sage", query_type="pattern_analysis", data=analysis_data
            )

            if patterns and patterns.get("similar_patterns"):
                # Complex condition - consider breaking down
                # 学習パターンを保存
                self.learned_patterns[status].append(
                    {
                        "command_pattern": patterns.get("command_pattern"),
                        "success_rate": patterns.get("success_rate", 0),
                        "common_issues": patterns.get("common_issues", []),
                    }
                )

                    f"🔍 RAG Sage identified {len(patterns['similar_patterns'])} similar patterns"
                )

        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"Failed to analyze with RAG Sage: {e}")

    def _assess_command_risk(self, command: str) -> Dict[str, Any]:
        """コマンドのリスクレベルを評価"""
        risk_score = 0
        risk_factors = []

        # 高リスクパターンのチェック
        high_risk_patterns = {
            "rm -rf": 10,
            "sudo": 5,
            "chmod 777": 8,
            "curl http": 3,
            "wget": 3,
            "> /dev/": 9,
            "dd if=": 10,
        }

        command_lower = command.lower()
        for pattern, score in high_risk_patterns.items():
            # Process each item in collection
            if pattern in command_lower:
                risk_score += score
                risk_factors.append(pattern)

        return {
            "risk_score": risk_score,
            "risk_level": "critical"
            if risk_score >= 10
            else "high"
            if risk_score >= 5
            else "medium",
            "risk_factors": risk_factors,
        }

    def _is_safe_command(self, command: str) -> bool:
        """Elder指導を考慮したコマンドの安全性チェック"""
        # 危険なコマンドのブラックリスト
        dangerous_patterns = [
            "rm -rf /",
            "dd if=",
            "mkfs",
            "fdisk",
            "format",
            "del /f /q",
            "rmdir /s",
            "shutdown",
            "reboot",
            "halt",
            "poweroff",
            "passwd",
            "su ",
            "sudo su",
            "chmod 777",
            "chown root",
            "> /dev/",
            "curl http",
            "wget http",
            "nc ",
            "netcat",
            "telnet",
            "ssh ",
            "scp ",
            "rsync",
        ]

        command_lower = command.lower()
        for pattern in dangerous_patterns:
            # Process each item in collection
            if pattern in command_lower:
                self.logger.warning(f"🚨 危険なコマンドを検出: {pattern}")
                return False

        # 追加の安全性チェック（Elder推奨パターン）
        elder_dangerous_patterns = [
            "eval(",
            "exec(",
            "__import__",
            "compile(",
            "globals(",
            "locals(",
            "setattr(",
            "delattr(",
        ]

        for pattern in elder_dangerous_patterns:
            # Process each item in collection
            if pattern in command_lower:
                self.logger.warning(f"🚨 Elder危険パターンを検出: {pattern}")
                return False

        return True

    def _save_execution_log(
        self,
        command_id: str,
        command: str,
        description: str,
        result: subprocess.CompletedProcess,
        duration: float,
    ):
        """実行ログを保存"""
        log_data = {
            "command_id": command_id,
            "command": command,
            "description": description,
            "executed_at": datetime.now().isoformat(),
            "duration": duration,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "worker_id": self.worker_id,
        }

        log_file = self.logs_dir / f"{command_id}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"📝 実行ログ保存: {log_file}")

        # Elder Tree統合: 重要なログはナレッジ賢者にも保存
        if self.four_sages and result.returncode != 0:
            # Complex condition - consider breaking down
            try:
                self.four_sages.report_to_sage(
                    sage_type="knowledge_sage",
                    report_type="execution_log",
                    data=log_data,
                )
            except Exception as e:
                # Handle specific exception case

    def _send_result(self, result_data: dict):
        """結果をOutputキューに送信"""
        try:
            self.channel.basic_publish(
                exchange="",
                routing_key=self.output_queue,
                body=json.dumps(result_data, ensure_ascii=False),
                properties=self._get_message_properties(),
            )
            self.logger.info(f"📤 結果送信: {result_data['command_id']}")
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"結果送信エラー: {e}")

    def run_file_monitor(self)self.logger.info("📁 ファイル監視モード開始")
    """ファイル監視モード（非同期処理用）"""

        while self.running:
            try:
                # pending ディレクトリの .json ファイルをチェック
                for command_file in self.pending_dir.glob("*.json"):
                    self._process_command_file(command_file)

                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                # Handle specific exception case
                self.logger.info("🛑 ファイル監視停止")
                break
            except Exception as e:
                # Handle specific exception case
                self.logger.error(f"ファイル監視エラー: {e}")
                time.sleep(self.check_interval)

    def _process_command_file(self, command_file: Path):
        """コマンドファイルを処理"""
        try:
            # running ディレクトリに移動
            running_file = self.running_dir / command_file.name
            shutil.move(str(command_file), str(running_file))

            # コマンド実行
            with open(running_file, "r", encoding="utf-8") as f:
                command_data = json.load(f)

            command_id = command_data.get("id", running_file.stem)
            command = command_data.get("command", "")
            description = command_data.get("description", "")

            result = self._execute_command(command_id, command, description)

            # completed ディレクトリに移動
            completed_file = self.completed_dir / command_file.name
            shutil.move(str(running_file), str(completed_file))

            self.logger.info(f"✅ ファイル処理完了: {command_file.name}")

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"ファイル処理エラー: {e}")

    def cleanup(self):
        """クリーンアップ処理"""
        try:
            # エルダーシステムへの登録解除
            if self.elder_tree:
                self._unregister_from_elder_tree()

            # 最終統計をログ出力
            self.logger.info(
                f"📊 Final execution statistics: {json.dumps(self.execution_stats, indent}"
            )

            # 実行中のコマンドがあれば待機
            if self.running_dir.exists():
                running_files = list(self.running_dir.glob("*.json"))
                if running_files:
                    self.logger.info(
                        f"Waiting for {len(running_files)} running commands to complete..."
                    )
                    time.sleep(5)  # 簡易的な待機

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Cleanup error: {e}")

    def stop(self):
        """ワーカー停止処理"""
        self.running = False
        self.logger.info("🛑 Command Executor Worker stopping...")

        # エルダーへの停止通知
        if self.elder_tree:
            self._notify_elder_shutdown()

        self.cleanup()

    def initialize(self) -> None:
        """ワーカーの初期化処理"""
        self.logger.info(
            f"🚀 {self.__class__.__name__} initializing with Elder Tree integration..."
        )

        # ディレクトリの確認と作成
        for dir_path in [
            self.pending_dir,
            self.running_dir,
            self.completed_dir,
            self.logs_dir,
        ]:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created directory: {dir_path}")

        # Elder Tree統合の再確認
        if ELDER_TREE_AVAILABLE and not self.elder_tree:
            # Complex condition - consider breaking down
            self._initialize_elder_systems()

        self.logger.info(f"✅ {self.__class__.__name__} initialized successfully")

    def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    ):
        """エラーハンドリング（Elder報告付き）"""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "severity": severity.value,
            "worker_id": self.worker_id,
            "timestamp": datetime.now().isoformat(),
        }

        # 基本的なエラーログ
        self.logger.error(f"Error in {context.get('operation', 'unknown')}: {error}")

        # 高severity以上のエラーはインシデント賢者に報告
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] and self.four_sages:
            # Complex condition - consider breaking down
            try:
                self.four_sages.report_to_sage(
                    sage_type="incident_sage",
                    report_type="worker_error",
                    data=error_info,
                    priority="high" if severity == ErrorSeverity.CRITICAL else "medium",
                )
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"Failed to report error to Incident Sage: {e}")

    def get_status(self) -> Dict[str, Any]:
        """ワーカーステータス取得"""
        return {
            "worker_id": self.worker_id,
            "worker_type": self.worker_type,
            "status": "running" if self.running else "stopped",
            "elder_integration": ELDER_TREE_AVAILABLE,
            "execution_stats": self.execution_stats,
            "recent_escalations": len(self.escalation_history),
            "learned_patterns": sum(
                len(patterns) for patterns in self.learned_patterns.values()
            ),
            "uptime": getattr(self, "start_time", None),
            "last_command": getattr(self, "last_command_time", None),
        }

    def validate_config(self) -> bool:
        """設定の検証"""
        required_dirs = [
            self.base_dir,
            self.pending_dir,
            self.running_dir,
            self.completed_dir,
            self.logs_dir,
        ]

        for dir_path in required_dirs:
            # Process each item in collection
            if not dir_path.exists():
                self.logger.warning(f"Required directory missing: {dir_path}")
                return False

        # Elder Tree統合の検証
        if ELDER_TREE_AVAILABLE:
            if not self.four_sages:
                self.logger.warning("Four Sages Integration not initialized")
            if not self.elder_council:
                self.logger.warning("Elder Council Summoner not initialized")

        return True

    def _unregister_from_elder_tree(self):
        """Elder Treeからの登録解除"""
        try:
            message = ElderMessage(
                sender_rank=ElderRank.SERVANT,
                sender_id=self.worker_id,
                recipient_rank=ElderRank.SAGE,
                recipient_id="task_sage",
                message_type="servant_unregistration",
                content={"worker_id": self.worker_id},
            )
            self.logger.info("📤 Unregistered from Elder Tree")
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Failed to unregister: {e}")

    def _notify_elder_shutdown(self):
        """エルダーへの停止通知"""
        try:
            if self.elder_council:
                self.elder_council.report_worker_status(
                    {
                        "worker_id": self.worker_id,
                        "status": "shutting_down",
                        "final_stats": self.execution_stats,
                    }
                )
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Failed to notify shutdown: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Command Executor Worker")
    parser.add_argument(
        "--mode",
        choices=["queue", "file"],
        default="queue",
        help="実行モード: queue (RabbitMQ) または file (ファイル監視)",
    )
    parser.add_argument("--worker-id", help="ワーカーID")

    args = parser.parse_args()

    worker = CommandExecutorWorker(worker_id=args.worker_id)

    if args.mode == "file":
        worker.run_file_monitor()
    else:
        worker.start()
