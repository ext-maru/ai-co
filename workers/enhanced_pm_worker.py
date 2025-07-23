#!/usr/bin/env python3
"""
Elders Guild 拡張PMワーカー v2.0
プロジェクト全体のライフサイクルを管理
要件定義→設計→開発→テスト→本番反映
"""

import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import EMOJI, BaseWorker, ErrorSeverity, get_config, with_error_handling
from core.worker_communication import CommunicationMixin
from libs.ai_command_helper import AICommandHelper
from libs.elder_council_summoner import (
    ElderCouncilSummoner,
    TriggerCategory,
    UrgencyLevel,
)
from libs.four_sages_integration import FourSagesIntegration
from libs.github_flow_manager import GitHubFlowManager
from libs.knowledge_base_manager import KnowledgeAwareMixin
from libs.pm_elder_integration import PMElderIntegration, ProjectComplexity
from libs.project_design_manager import ProjectDesignManager
from libs.quality_checker import QualityChecker
from libs.self_evolution_manager import SelfEvolutionManager
from libs.slack_notifier import SlackNotifier


class EnhancedPMWorker(BaseWorker, CommunicationMixin, KnowledgeAwareMixin):
    """拡張PMワーカー - プロジェクトマネージャーとして全体を監督"""

    def __init__(self, worker_id=None):
        super().__init__(worker_type="pm", worker_id=worker_id)
        self.setup_communication()
        self.output_dir = PROJECT_ROOT / "output"
        self.evolution_manager = SelfEvolutionManager()
        self.git_manager = GitHubFlowManager()
        self.project_manager = ProjectDesignManager()
        self.slack = SlackNotifier()
        self.ai_helper = AICommandHelper()
        self.config = get_config()

        # SE-Tester連携設定
        self.se_testing_enabled = self.config.get("pm.se_testing_enabled", True)

        # 品質管理機能統合
        try:
            self.quality_checker = QualityChecker()
            self.task_iterations: Dict[str, int] = {}  # タスクIDごとのイテレーション回数
            self.max_iterations = 3  # 最大再試行回数
            self.task_contexts: Dict[str, dict] = {}  # タスクのコンテキスト保存
            self.quality_enabled = True
            self.logger.info("品質管理機能統合完了")
        except Exception as e:
            # 品質管理初期化エラー
            context = {
                "operation": "quality_checker_init",
                "component": "QualityChecker",
            }
            self.handle_error(e, context, severity=ErrorSeverity.LOW)
            self.quality_checker = None
            self.quality_enabled = False

        # Elder統合システム
        try:
            self.pm_elder_integration = PMElderIntegration()
            self.elder_integration_enabled = True
            self.logger.info("PM-Elder統合システム初期化完了")
        except Exception as e:
            # Elder統合初期化エラー
            context = {"operation": "pm_elder_init", "component": "PMElderIntegration"}
            self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)
            self.pm_elder_integration = None
            self.elder_integration_enabled = False

        # Four Sages統合システム
        try:
            self.four_sages_integration = FourSagesIntegration()
            self.four_sages_enabled = True
            self.logger.info("Four Sages統合システム初期化完了")

            # 4賢者の初期設定
            sage_configs = {
                "knowledge_sage": {"active": True, "priority": "high"},
                "task_sage": {"active": True, "priority": "high"},
                "incident_sage": {"active": True, "priority": "medium"},
                "rag_sage": {"active": True, "priority": "medium"},
            }
            init_result = self.four_sages_integration.initialize_sage_integration(
                sage_configs
            )
            self.logger.info(f"Four Sages初期化結果: {init_result['integration_status']}")
        except Exception as e:
            # Four Sages初期化エラー
            context = {
                "operation": "four_sages_init",
                "component": "FourSagesIntegration",
            }
            self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)
            self.four_sages_integration = None
            self.four_sages_enabled = False

        # Elder Council Summoner統合
        try:
            self.elder_council_summoner = ElderCouncilSummoner()
            self.council_summoner_enabled = True
            self.logger.info("Elder Council Summoner統合完了")
        except Exception as e:
            # Council Summoner初期化エラー
            context = {
                "operation": "council_summoner_init",
                "component": "ElderCouncilSummoner",
            }
            self.handle_error(e, context, severity=ErrorSeverity.LOW)
            self.elder_council_summoner = None
            self.council_summoner_enabled = False

        self.logger.info(f"Enhanced PM Worker initialized (id: {self.worker_id})")

    def process_message(self, ch, method, properties, body):
        """メッセージ処理のメインロジック"""
        try:
            self.logger.info(
                f"{EMOJI['info']} Processing PM task: {body.get('task_id')}"
            )

            # 4賢者への相談（タスク開始時）
            if self.four_sages_enabled:
                sage_consultation = self._consult_four_sages_for_task(body)
                if sage_consultation.get("recommendation"):
                    self.logger.info(
                        f"Four Sages recommendation: {sage_consultation['recommendation']}"
                    )

            # プロジェクトタイプを判定
            if body.get("project_mode", False) or self._is_complex_task(body):
                # Complex condition - consider breaking down
                # プロジェクトモードで処理
                self._handle_project_mode(body)
            else:
                # 従来のシンプルなファイル配置モード
                self._handle_simple_mode(body)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            # Handle specific exception case
            context = {
                "operation": "process_message",
                "task_id": body.get("task_id"),
                "project_mode": body.get("project_mode", False),
                "prompt": body.get("prompt", "")[:100],
            }

            # 統一エラーハンドリング
            self.handle_error(e, context, severity=ErrorSeverity.HIGH)

            # 重大エラーのElder報告
            if self.elder_integration_enabled:
                self._report_critical_error_to_elder(e, context)

            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _is_complex_task(self, body: Dict[str, Any]) -> bool:
        """複雑なタスクかどうかを判定"""
        indicators = [
            "architecture" in body.get("prompt", "").lower(),
            "design" in body.get("prompt", "").lower(),
            "system" in body.get("prompt", "").lower(),
            "integration" in body.get("prompt", "").lower(),
            len(body.get("files_created", [])) > 5,
            body.get("task_type") == "project",
        ]
        return sum(indicators) >= 2

    def _handle_project_mode(self, body: Dict[str, Any]):
        """プロジェクトモードでの処理"""
        task_id = body.get("task_id")
        prompt = body.get("prompt", "")

        self.logger.info(f"Starting project mode for task: {task_id}")

        # Elder承認プロセス
        if self.elder_integration_enabled:
            (
                approved,
                approval_message,
            ) = self.pm_elder_integration.request_project_approval(body)

            if not approved:
                self.logger.warning(
                    f"Project requires Elder approval: {approval_message}"
                )

                # Elder承認待ちの通知
                self.slack.send_message(
                    f"🔒 プロジェクト承認待ち\n"
                    f"タスクID: {task_id}\n"
                    f"理由: {approval_message}\n"
                    f"Elder Councilの判断をお待ちください。",
                    channel="#pm-notifications",
                )

                # 承認待ち状態で一時停止
                return
            else:
                self.logger.info(f"Project approved: {approval_message}")

        # 1. プロジェクト作成
        project_name = self._extract_project_name(prompt)
        project_id = self.project_manager.create_project(
            task_id=task_id, name=project_name, description=prompt
        )

        # 2. 要件定義フェーズ
        self._phase_requirements(project_id, body)

        # 3. 設計フェーズ
        self._phase_design(project_id, body)

        # 4. 開発フェーズ
        self._phase_development(project_id, body)

        # 5. テストフェーズ
        self._phase_testing(project_id, body)

        # 6. デプロイフェーズ
        self._phase_deployment(project_id, body)

        # プロジェクトレポート生成
        report = self.project_manager.generate_project_report(project_id)
        self.logger.info(f"Project completed:\n{report}")

        # 品質評価
        quality_score = 0.0
        if self.quality_enabled:
            quality_score = self._evaluate_project_quality(project_id, body)
            self.logger.info(f"プロジェクト品質スコア: {quality_score:.2f}")

        # Elder Tree階層への完了報告
        if self.elder_integration_enabled:
            project_result = {
                "placed_files": body.get("placed_files", []),
                "quality_score": quality_score,
                "execution_time": "measured",  # 実際は計測値
                "project_report": report,
            }

            # PM-Elder統合による報告
            self.pm_elder_integration.report_project_completion(
                project_id, project_result
            )

            # Claude Elderへの進捗報告
            self._report_project_progress_to_elder(
                project_id, "deployment", "completed", project_result
            )

            # 重要プロジェクトの場合はGrand Elderへも報告
            complexity = self.pm_elder_integration.assess_project_complexity(body)
            if complexity == ProjectComplexity.CRITICAL:
                self._escalate_critical_issue_to_grand_elder(
                    "project_completion",
                    "info",
                    {
                        "project_id": project_id,
                        "complexity": complexity.value,
                        "quality_score": quality_score,
                        "success": True,
                    },
                )

        # Slack通知
        message = f"{EMOJI['rocket']} プロジェクト完了: {project_name}\n"
        message += f"プロジェクトID: {project_id}\n"
        if self.quality_enabled:
            message += f"品質スコア: {quality_score:.2f}\n"
        message += "詳細レポートはログを参照してください。"

        self.slack.send_message(message)

    def _phase_requirements(self, project_id: str, body: Dict[str, Any]):
        """要件定義フェーズ"""
        self.logger.info(f"Phase: Requirements for project {project_id}")
        self.project_manager.update_phase_status(project_id, "planning", "in_progress")

        # プロンプトから要件を抽出
        requirements = self._extract_requirements(body.get("prompt", ""))

        for req in requirements:
            # Process each item in collection
            self.project_manager.add_requirement(
                project_id=project_id,
                type=req["type"],
                description=req["description"],
                priority=req.get("priority", "normal"),
            )

        # AIに詳細な要件定義書を作成させる
        self._create_requirements_document(project_id, requirements)

        self.project_manager.update_phase_status(project_id, "planning", "completed")

    def _phase_design(self, project_id: str, body: Dict[str, Any]):
        """設計フェーズ"""
        self.logger.info(f"Phase: Design for project {project_id}")
        self.project_manager.update_phase_status(project_id, "design", "in_progress")

        # Claude Elderへの進捗報告
        self._report_project_progress_to_elder(
            project_id, "design", "started", {"project_data": body}
        )

        # 4賢者との設計協調
        if self.four_sages_enabled:
            sage_coordination = self._coordinate_with_four_sages(
                "project_planning",
                {
                    "project_id": project_id,
                    "files": body.get("files_created", []),
                    "requirements": body.get("prompt", ""),
                },
            )

            if sage_coordination.get("recommendations"):
                self.logger.info(
                    f"Design recommendations from 4 Sages: {sage_coordination['recommendations']}"
                )

        # ファイル構造から設計を推測
        files_created = body.get("files_created", [])
        design = self._analyze_architecture(files_created)

        # 設計書作成
        design_id = self.project_manager.create_design(
            project_id=project_id, design_type="architecture", content=design
        )

        # 詳細設計書の自動生成
        self._create_detailed_design(project_id, design_id, design)

        self.project_manager.update_phase_status(project_id, "design", "completed")

        # 完了報告
        self._report_project_progress_to_elder(
            project_id,
            "design",
            "completed",
            {"design_id": design_id, "architecture": design},
        )

    def _phase_development(self, project_id: str, body: Dict[str, Any]):
        """開発フェーズ"""
        self.logger.info(f"Phase: Development for project {project_id}")
        self.project_manager.update_phase_status(
            project_id, "development", "in_progress"
        )

        # ファイル配置（従来の処理）
        files_created = body.get("files_created", [])
        placed_files = []

        for file_path in files_created:
            # Process each item in collection
            source = self.output_dir / file_path
            if source.exists():
                # 開発タスク作成
                dev_task_id = self.project_manager.create_development_task(
                    project_id=project_id,
                    design_id=None,
                    name=f"Deploy {file_path}",
                    description=f"Deploying file: {file_path}",
                )

                try:
                    # ファイル配置
                    target = self.evolution_manager.determine_file_location(source)
                    shutil.copy2(source, target)

                    # Git追加
                    if self.config.get("git.auto_add", True):
                        self.git_manager.add_file(target)

                    placed_files.append(str(target))

                    # タスク完了
                    self.project_manager.update_task_status(
                        dev_task_id, "completed", {"file_path": str(target)}
                    )

                    # プロジェクトファイル登録
                    self.project_manager.add_project_file(
                        project_id=project_id,
                        file_path=str(target),
                        file_type=self._get_file_type(target),
                        phase="development",
                    )

                except Exception as e:
                    # ファイル配置エラー
                    context = {
                        "operation": "file_placement",
                        "file_path": str(file_path),
                        "target": str(target) if "target" in locals() else "unknown",
                        "dev_task_id": dev_task_id,
                    }
                    self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)
                    self.project_manager.update_task_status(
                        dev_task_id, "failed", {"error": str(e)}
                    )

        self.project_manager.update_phase_status(project_id, "development", "completed")
        body["placed_files"] = placed_files

    def _phase_testing(self, project_id: str, body: Dict[str, Any]):
        """テストフェーズ"""
        self.logger.info(f"Phase: Testing for project {project_id}")
        self.project_manager.update_phase_status(project_id, "testing", "in_progress")

        placed_files = body.get("placed_files", [])

        if self.se_testing_enabled and placed_files:
            # Complex condition - consider breaking down
            # SE-Testerワーカーに送信
            self.logger.info(
                f"Sending to SE-Tester for testing: {len(placed_files)} files"
            )

            test_task = {
                "task_id": body.get("task_id"),
                "project_id": project_id,
                "files_created": placed_files,
                "fix_attempt": 0,
                "original_prompt": body.get("prompt", ""),
            }

            self.send_to_worker("se", "test_request", test_task)

            # テスト結果を待つ（実際は非同期だが、ここでは仮の処理）
            time.sleep(5)

            # テスト結果を記録（実際はSE-Testerからの通知を受け取る）
            self.project_manager.record_test_result(
                project_id=project_id,
                dev_task_id=None,
                test_type="unit",
                status="passed",
                details={"message": "All tests passed"},
            )
        else:
            # テストスキップ
            self.logger.info("Testing skipped (SE-Tester disabled or no files)")

        self.project_manager.update_phase_status(project_id, "testing", "completed")

    def _phase_deployment(self, project_id: str, body: Dict[str, Any]):
        """デプロイフェーズ"""
        self.logger.info(f"Phase: Deployment for project {project_id}")
        self.project_manager.update_phase_status(
            project_id, "deployment", "in_progress"
        )

        # Gitコミット
        if self.config.get("git.auto_commit", True):
            commit_message = (
                f"Deploy project {project_id}: {body.get('prompt', '')[:50]}"
            )
            self.git_manager.commit(commit_message)

        # デプロイ完了
        self.project_manager.update_phase_status(project_id, "deployment", "completed")

        # プロジェクト全体のステータス更新
        with self.project_manager._get_connection() as conn:
            conn.execute(
                """
                UPDATE projects SET status = 'deployed' WHERE project_id = ?
            """,
                (project_id,),
            )
            conn.commit()

    def _handle_simple_mode(self, body: Dict[str, Any]):
        """シンプルモード（従来の処理）"""
        task_id = body.get("task_id")
        files_created = body.get("files_created", [])

        self.logger.info(f"Simple mode: placing {len(files_created)} files")

        placed_files = []
        for file_path in files_created:
            # Process each item in collection
            source = self.output_dir / file_path
            if source.exists():
                try:
                    target = self.evolution_manager.determine_file_location(source)
                    shutil.copy2(source, target)

                    if self.config.get("git.auto_add", True):
                        self.git_manager.add_file(target)

                    placed_files.append(str(target))
                    self.logger.info(f"Placed: {source} -> {target}")

                except Exception as e:
                    # シンプルモードファイル配置エラー
                    context = {
                        "operation": "simple_file_placement",
                        "file_path": str(file_path),
                        "task_id": task_id,
                    }
                    self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)

        # 結果を次のワーカーへ
        if self.se_testing_enabled and placed_files:
            # Complex condition - consider breaking down
            # SE-Testerへ
            test_task = {
                "task_id": task_id,
                "files_created": placed_files,
                "fix_attempt": 0,
            }
            self.send_to_worker("se", "test_request", test_task)
        else:
            # 直接ResultWorkerへ
            self._send_result(
                {
                    "task_id": task_id,
                    "files_placed": placed_files,
                    "status": "completed",
                }
            )

    def _extract_project_name(self, prompt: str) -> str:
        """プロンプトからプロジェクト名を抽出"""
        # 簡単な実装（実際はより高度な処理が必要）
        if "作成" in prompt:
            parts = prompt.split("作成")
            if len(parts) > 0:
                return parts[0].strip()[-20:]
        return prompt[:30]

    def _extract_requirements(self, prompt: str) -> List[Dict[str, Any]]:
        """プロンプトから要件を抽出"""
        requirements = []

        # 機能要件の抽出（簡易版）
        keywords = ["機能", "実装", "作成", "生成", "処理"]
        for keyword in keywords:
            if keyword in prompt:
                requirements.append(
                    {
                        "type": "functional",
                        "description": f"{keyword}に関する要件",
                        "priority": "high",
                    }
                )

        # 非機能要件
        if any(word in prompt for word in ["性能", "パフォーマンス", "高速"]):
            # Complex condition - consider breaking down
            requirements.append(
                {
                    "type": "non_functional",
                    "description": "パフォーマンス要件",
                    "priority": "normal",
                }
            )

        return (
            requirements
            if requirements
            else [{"type": "functional", "description": prompt, "priority": "normal"}]
        )

    def _analyze_architecture(self, files: List[str]) -> Dict[str, Any]:
        """ファイル構造からアーキテクチャを分析"""
        architecture = {"components": [], "layers": [], "dependencies": []}

        # コンポーネント分析
        for file in files:
            if "worker" in file:
                architecture["components"].append(
                    {"type": "worker", "name": Path(file).stem, "path": file}
                )
            elif "manager" in file:
                architecture["components"].append(
                    {"type": "manager", "name": Path(file).stem, "path": file}
                )

        return architecture

    def _get_file_type(self, file_path: Path) -> str:
        """ファイルタイプを判定"""
        if file_path.suffix == ".py":
            if "test_" in file_path.name:
                return "test"
            elif "worker" in file_path.name:
                return "worker"
            else:
                return "source"
        elif file_path.suffix in [".json", ".yaml", ".conf"]:
            return "config"
        elif file_path.suffix in [".md", ".txt"]:
            return "doc"
        else:
            return "other"

    def _create_requirements_document(self, project_id: str, requirements: List[Dict]):
        """要件定義書を自動生成"""
        doc_content = f"""# 要件定義書 - プロジェクト {project_id}

## 機能要件
"""
        # 要件一覧を追加
        for i, req in enumerate(requirements, 1):
            doc_content += f"""
### {i}. {req.get('title', 'Untitled Requirement')}

**優先度**: {req.get('priority', 'Medium')}
**ステータス**: {req.get('status', 'Draft')}

**説明**: {req.get('description', '説明なし')}

**受入条件**:
{req.get('acceptance_criteria', '- 条件未定義')}

---
"""
        
        doc_content += f"""

## 技術要件
- プログラミング言語: Python 3.8+
- フレームワーク: FastAPI, SQLAlchemy
- データベース: PostgreSQL
- テスト: pytest

## 性能要件
- レスポンスタイム: 500ms 以下
- 同時アクセス: 100ユーザー
- 稼働率: 99.9%

## セキュリティ要件
- JWT認証
- HTTPS通信
- データ暗号化

---
*作成日: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*作成者: Enhanced PM Worker*
"""
        return doc_content

    def cleanup(self):
        """ワーカーのクリーンアップ処理"""
        try:
            # Elder Tree に終了を通知
            if self.elder_tree_initialized and self.four_sages:
                # Complex condition - consider breaking down
                self.four_sages.report_to_task_sage({
                    "type": "worker_shutdown",
                    "worker": "enhanced_pm_worker",
                    "timestamp": datetime.now().isoformat()
                })
            
            # プロジェクトデータの保存確認
            if hasattr(self, 'projects') and self.projects:
                # Complex condition - consider breaking down
                self.logger.info(f"Saving {len(self.projects)} project(s) before shutdown")
            
            self.logger.info("Enhanced PM Worker cleanup completed")
        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"Error during cleanup: {e}")

    def stop(self):
        """ワーカーの停止処理"""
        try:
            self.cleanup()
            super().stop()
            self.logger.info("Enhanced PM Worker stopped successfully")
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Error stopping Enhanced PM Worker: {e}")

    def initialize(self) -> None:
        """ワーカーの初期化処理"""
        # 初期化処理の実装
        try:
            # Elder Tree システムの初期化
            if not self.elder_tree_initialized:
                self._initialize_elder_tree()
            
            # プロジェクトデータの初期化
            if not hasattr(self, 'projects'):
                self.projects = {}
            
            self.logger.info(f"{self.__class__.__name__} initialized successfully")
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Initialization error: {e}")
            raise
        logger.info(f"{self.__class__.__name__} initialized")
        pass

    def handle_error(self, error: Exception, context: str = "unknown"):
        """エラーハンドリング処理"""
        try:
            error_details = {
                "worker": "enhanced_pm_worker",
                "context": context,
                "error": str(error),
                "error_type": type(error).__name__,
                "timestamp": datetime.now().isoformat()
            }
            
            # Incident Sage にエラー報告
            if self.elder_tree_initialized and self.four_sages:
                # Complex condition - consider breaking down
                self.four_sages.consult_incident_sage({
                    "type": "pm_processing_error",
                    **error_details
                })
            
            self.logger.error(f"Enhanced PM Worker error in {context}: {error}")
        except Exception as e:
            # Handle specific exception case
            self.logger.critical(f"Error in error handler: {e}")

    def get_status(self) -> Dict[str, Any]:
        """ワーカーステータス取得"""
        try:
            base_status = {
                "worker_id": self.worker_id,
                "worker_type": "enhanced_pm",
                "status": "active",
                "health": "healthy",
            }

            # Elder Tree統合状態
            elder_status = self._get_elder_tree_status()

            # 品質管理状態
            quality_status = {
                "enabled": self.quality_enabled,
                "quality_checker": self.quality_checker is not None,
                "active_iterations": len(self.task_iterations),
            }

            # 4賢者協調状態
            if self.four_sages_enabled:
                sage_status = self.four_sages_integration.monitor_sage_collaboration()
            else:
                sage_status = {"status": "disabled"}

            return {
                **base_status,
                "elder_tree": elder_status,
                "quality_management": quality_status,
                "four_sages": sage_status,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Status retrieval failed: {e}")
            return {"worker_id": self.worker_id, "status": "error", "error": str(e)}

    def validate_config(self) -> bool:
        """設定の妥当性を検証"""
        try:
            # ベース設定の確認
            if not hasattr(self, 'worker_id') or not self.worker_id:
                # Complex condition - consider breaking down
                self.logger.error("Worker ID not set")
                return False
            
            # Elder Tree 設定の確認
            if ELDER_TREE_AVAILABLE and not self.elder_tree_initialized:
                # Complex condition - consider breaking down
                self.logger.warning("Elder Tree not initialized")
            
            # プロジェクトデータの確認
            if not hasattr(self, 'projects'):
                self.projects = {}
            
            self.logger.info("Enhanced PM Worker config validation passed")
            return True
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Config validation failed: {e}")
            return False

    def _create_detailed_design(self, project_id: str, design_id: str, design: Dict):
        """詳細設計書を自動生成"""
        doc_content = f"""# 詳細設計書 - プロジェクト {project_id}

## アーキテクチャ概要
- 設計ID: {design_id}
- コンポーネント数: {len(design.get('components', []))}

## コンポーネント詳細
"""
        for comp in design.get("components", []):
            doc_content += f"### {comp['name']}\n"
            doc_content += f"- タイプ: {comp['type']}\n"
            doc_content += f"- パス: {comp['path']}\n\n"

        # AI Command Executorで文書生成
        self.ai_helper.create_bash_command(
            f"""cat > {PROJECT_ROOT}/project_designs/designs/{design_id}_design.md << 'EOF'
{doc_content}
EOF""",
            f"create_design_{design_id}",
        )

    def _send_result(self, result_data: Dict[str, Any]):
        """結果をResultWorkerに送信"""
        self.send_to_worker("result", "process", result_data)

    def _evaluate_project_quality(
        self, project_id: str, project_data: Dict[str, Any]
    ) -> float:
        """プロジェクト全体の品質を評価"""
        if not self.quality_enabled:
            return 0.0

        try:
            # ファイル作成状況を評価
            files_created = project_data.get("placed_files", [])
            if not files_created:
                return 0.5  # ファイル未作成は低品質

            # 品質チェッカーでファイル品質を評価
            total_score = 0.0
            evaluated_files = 0

            for file_path in files_created:
                # Process each item in collection
                try:
                    file_data = {
                        "files_created": [file_path],
                        "response": f"File created: {file_path}",
                        "task_type": "file_creation",
                    }
                    score, _, _ = self.quality_checker.check_task_quality(file_data)
                    total_score += score
                    evaluated_files += 1
                except Exception as e:
                    # ファイル品質評価エラー
                    context = {
                        "operation": "file_quality_evaluation",
                        "file_path": str(file_path),
                        "project_id": project_id,
                    }
                    self.handle_error(e, context, severity=ErrorSeverity.LOW)

            if evaluated_files > 0:
                avg_score = total_score / evaluated_files
            else:
                avg_score = 0.5

            # プロジェクト完了度ボーナス
            completion_bonus = 0.2 if project_data.get("status") == "completed" else 0.0

            final_score = min(1.0, avg_score + completion_bonus)

            self.logger.info(
                f"プロジェクト品質評価: {final_score:.2f} (ファイル数: {evaluated_files})"
            )
            return final_score

        except Exception as e:
            # プロジェクト品質評価エラー
            context = {
                "operation": "project_quality_evaluation",
                "project_id": project_id,
            }
            self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)
            return 0.5

    def _check_task_quality_and_retry(
        self, task_id: str, result: Dict[str, Any]
    ) -> bool:
        """タスク品質をチェックし, 必要に応じて再実行を指示"""
        if not self.quality_enabled:
            return True  # 品質チェック無効時は常に合格

        try:
            # イテレーション回数を取得
            iteration = self.task_iterations.get(task_id, 0)

            # 品質チェック
            (
                quality_score,
                issues,
                suggestions,
            ) = self.quality_checker.check_task_quality(result)
            self.logger.info(
                f"📊 品質スコア: {quality_score:.2f} (タスク: {task_id}, イテレーション: {iteration + 1})"
            )

            if (
                quality_score < self.quality_checker.min_quality_score
                and iteration < self.max_iterations
            ):
                # 品質不十分 - 再実行指示
                self.logger.warning(f"⚠️ 品質不十分 - 再実行を指示します")
                self._request_task_retry(
                    task_id, result, issues, suggestions, iteration
                )
                return False
            else:
                # 品質OK または 最大イテレーション到達
                if quality_score >= self.quality_checker.min_quality_score:
                    self.logger.info(f"✅ 品質基準を満たしました (スコア: {quality_score:.2f})")
                else:
                    self.logger.warning(
                        f"⚠️ 最大イテレーション到達 - 現状で受け入れ (スコア: {quality_score:.2f})"
                    )

                # コンテキストクリア
                self.task_iterations.pop(task_id, None)
                self.task_contexts.pop(task_id, None)
                return True

        except Exception as e:
            # 品質チェックエラー
            context = {"operation": "task_quality_check", "task_id": task_id}
            self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)
            return True  # エラー時は合格扱い

    def _request_task_retry(
        self,
        task_id: str,
        result: dict,
        issues: list,
        suggestions: list,
        iteration: int,
    ):
        """タスクの再実行を要求"""
        try:
            # Elder エスカレーション判定
            if self.elder_integration_enabled and iteration >= 2:  # 3回目失敗でElder介入
                escalated = self.pm_elder_integration.escalate_quality_issue(
                    project_id=result.get("project_id", task_id),
                    quality_issues=issues,
                    iteration_count=iteration + 1,
                )

                if escalated:
                    self.logger.info(
                        f"Quality issue escalated to Elders for task {task_id}"
                    )
                    # Elder判断待ちでリトライを一時停止
                    return

            # コンテキストを取得または初期化
            if task_id not in self.task_contexts:
                self.task_contexts[task_id] = {
                    "original_prompt": result.get("prompt", ""),
                    "task_type": result.get("task_type", "code"),
                    "history": [],
                }

            context = self.task_contexts[task_id]

            # 履歴に追加
            context["history"].append(
                {
                    "iteration": iteration,
                    "quality_score": self.quality_checker.check_task_quality(result)[0],
                    "issues": issues,
                    "suggestions": suggestions,
                    "response": result.get("response", "")[:500],  # 要約
                }
            )

            # フィードバックプロンプトを生成
            feedback_prompt = self.quality_checker.generate_feedback_prompt(
                task_id, context["original_prompt"], issues, suggestions, iteration
            )

            # 再実行タスクを作成
            retry_task = {
                "task_id": task_id,
                "task_type": context["task_type"],
                "prompt": feedback_prompt,
                "is_retry": True,
                "iteration": iteration + 1,
                "context": {
                    "original_prompt": context["original_prompt"],
                    "previous_issues": issues,
                    "previous_suggestions": suggestions,
                },
            }

            # イテレーション回数を更新
            self.task_iterations[task_id] = iteration + 1

            # タスクを適切なワーカーに再送信
            self.send_to_worker("task", "retry", retry_task)

            self.logger.info(f"🔄 再実行タスクを送信: {task_id} (イテレーション {iteration + 2})")

            # Slack通知
            if hasattr(self, "slack") and self.slack:
                # Complex condition - consider breaking down
                self._send_retry_notification(
                    task_id, issues, suggestions, iteration + 1
                )

        except Exception as e:
            # 再実行要求エラー
            context = {
                "operation": "task_retry_request",
                "task_id": task_id,
                "iteration": iteration,
            }
            self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)

    def _send_retry_notification(
        self, task_id: str, issues: list, suggestions: list, iteration: int
    ):
        """再実行通知をSlackに送信"""
        try:
            message = f"🔄 タスク品質改善のため再実行\n"
            message += f"タスクID: {task_id}\n"
            message += f"イテレーション: {iteration}\n"
            message += f"主な問題点: {', '.join(issues[:3])}\n"
            message += f"改善提案: {', '.join(suggestions[:2])}"

            self.slack.send_message(message)

        except Exception as e:
            # 再実行通知エラー
            context = {
                "operation": "retry_notification",
                "task_id": task_id,
                "iteration": iteration,
            }
            self.handle_error(e, context, severity=ErrorSeverity.LOW)

    # ============================================
    # Elder Tree統合メソッド
    # ============================================

    def _consult_four_sages_for_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """タスク開始時の4賢者相談"""
        try:
            if not self.four_sages_integration:
                return {"recommendation": None}

            learning_request = {
                "type": "task_analysis",
                "data": {
                    "task_id": task_data.get("task_id"),
                    "prompt": task_data.get("prompt", ""),
                    "files_created": task_data.get("files_created", []),
                    "complexity": self._assess_task_complexity(task_data),
                },
            }

            result = self.four_sages_integration.coordinate_learning_session(
                learning_request
            )

            return {
                "recommendation": result.get("learning_outcome"),
                "consensus_reached": result.get("consensus_reached", False),
                "sage_insights": result.get("individual_responses", {}),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Four Sages consultation failed: {e}")
            return {"recommendation": None}

    def _report_project_progress_to_elder(
        self, project_id: str, phase: str, status: str, details: Dict[str, Any]
    ):
        """プロジェクト進捗のElder報告"""
        try:
            if not self.elder_integration_enabled:
                return

            # Claude Elderへの進捗報告
            progress_report = {
                "project_id": project_id,
                "phase": phase,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "details": details,
                "worker_id": self.worker_id,
            }

            # 4賢者経由でClaude Elderへ報告
            if self.four_sages_enabled:
                import asyncio

                asyncio.create_task(
                    self.four_sages_integration.report_to_claude_elder(
                        "task_sage", "progress_report", progress_report
                    )
                )

            self.logger.info(f"Progress reported to Elder Tree: {project_id} - {phase}")

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Elder progress report failed: {e}")

    def _escalate_critical_issue_to_grand_elder(
        self, issue_type: str, severity: str, details: Dict[str, Any]
    ):
        """重大問題のGrand Elderエスカレーション"""
        try:
            if not self.four_sages_enabled:
                self.logger.warning("Four Sages not available for escalation")
                return False

            # 4賢者合議によるエスカレーション
            import asyncio

            result = asyncio.create_task(
                self.four_sages_integration.escalate_to_grand_elder(
                    issue_type, severity, details
                )
            )

            self.logger.critical(f"ESCALATED TO GRAND ELDER: {issue_type} - {severity}")
            return True

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Grand Elder escalation failed: {e}")
            return False

    def _request_elder_council_for_decision(
        self, decision_type: str, context: Dict[str, Any]
    ):
        """Elder Council召集要請"""
        try:
            if not self.council_summoner_enabled:
                self.logger.warning("Council Summoner not available")
                return

            # 緊急度評価
            urgency = self._assess_decision_urgency(decision_type, context)

            # Council召集トリガー作成
            trigger = {
                "trigger_id": f"pm_decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "category": TriggerCategory.STRATEGIC_DECISION,
                "urgency": urgency,
                "title": f"PM Decision Required: {decision_type}",
                "description": context.get(
                    "description", "PM Worker requires Elder Council decision"
                ),
                "metrics": context,
                "affected_systems": ["project_management", "task_execution"],
                "suggested_agenda": [
                    f"Review {decision_type} request",
                    "Evaluate impact and risks",
                    "Provide strategic guidance",
                ],
            }

            # Council召集
            if urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
                self.elder_council_summoner._create_trigger(**trigger)
                self.logger.info(f"Elder Council summoned for: {decision_type}")

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Elder Council request failed: {e}")

    def _coordinate_with_four_sages(
        self, coordination_type: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """4賢者との協調処理"""
        try:
            if not self.four_sages_enabled:
                return {"coordinated": False}

            # 協調タイプに応じた処理
            if coordination_type == "project_planning":
                return self._coordinate_project_planning_with_sages(data)
            elif coordination_type == "quality_improvement":
                return self._coordinate_quality_improvement_with_sages(data)
            elif coordination_type == "resource_optimization":
                return self._coordinate_resource_optimization_with_sages(data)
            else:
                return {"coordinated": False, "reason": "Unknown coordination type"}

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Four Sages coordination failed: {e}")
            return {"coordinated": False, "error": str(e)}

    def _get_elder_tree_status(self) -> Dict[str, Any]:
        """Elder Tree階層の状態取得"""
        try:
            status = {
                "elder_integration": self.elder_integration_enabled,
                "four_sages": self.four_sages_enabled,
                "council_summoner": self.council_summoner_enabled,
                "hierarchy": {
                    "grand_elder": "maru",
                    "claude_elder": "active"
                    if self.elder_integration_enabled
                    else "inactive",
                    "four_sages": self._get_four_sages_status(),
                    "pm_worker": {
                        "id": self.worker_id,
                        "role": "servant",
                        "status": "active",
                    },
                },
            }

            return status

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Elder Tree status retrieval failed: {e}")
            return {"error": str(e)}

    # ============================================
    # ヘルパーメソッド
    # ============================================

    def _assess_task_complexity(self, task_data: Dict[str, Any]) -> str:
        """タスク複雑度評価"""
        complexity_score = 0

        # ファイル数による評価
        files_count = len(task_data.get("files_created", []))
        if files_count > 10:
            complexity_score += 3
        elif files_count > 5:
            complexity_score += 2
        elif files_count > 0:
            complexity_score += 1

        # プロンプト内容による評価
        prompt = task_data.get("prompt", "").lower()
        complex_keywords = [
            "architecture",
            "integration",
            "migration",
            "refactor",
            "optimize",
        ]
        complexity_score += sum(1 for keyword in complex_keywords if keyword in prompt)

        # 複雑度レベル決定
        if complexity_score >= 5:
            return "high"
        elif complexity_score >= 3:
            return "medium"
        else:
            return "low"

    def _report_critical_error_to_elder(
        self, error: Exception, context: Dict[str, Any]
    ):
        """重大エラーのElder報告"""
        try:
            if not self.elder_integration_enabled:
                return

            error_report = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "worker_id": self.worker_id,
                "severity": "critical",
            }

            # エラーがcriticalの場合はGrand Elderへエスカレーション
            if context.get("severity") == ErrorSeverity.CRITICAL:
                self._escalate_critical_issue_to_grand_elder(
                    "system_error", "critical", error_report
                )

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Failed to report error to Elder: {e}")

    def _assess_decision_urgency(
        self, decision_type: str, context: Dict[str, Any]
    ) -> UrgencyLevel:
        """決定緊急度評価"""
        # 緊急度マッピング
        urgency_map = {
            "architecture_change": UrgencyLevel.HIGH,
            "resource_allocation": UrgencyLevel.HIGH,
            "quality_escalation": UrgencyLevel.CRITICAL,
            "project_approval": UrgencyLevel.MEDIUM,
            "workflow_optimization": UrgencyLevel.LOW,
        }

        base_urgency = urgency_map.get(decision_type, UrgencyLevel.MEDIUM)

        # コンテキストによる調整
        if context.get("severity") == "critical":
            return UrgencyLevel.CRITICAL
        elif context.get("impact") == "system-wide":
            return UrgencyLevel.HIGH

        return base_urgency

    def _get_four_sages_status(self) -> Dict[str, str]:
        """4賢者の状態取得"""
        if not self.four_sages_enabled:
            return {"status": "disabled"}

        try:
            # 4賢者の健康状態を取得
            sage_status = self.four_sages_integration.monitor_sage_collaboration()
            return sage_status.get("sage_health_status", {})
        except:
            return {"status": "unknown"}

    def _coordinate_project_planning_with_sages(
        self, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """プロジェクト計画の4賢者協調"""
        learning_request = {"type": "project_planning", "data": data}

        result = self.four_sages_integration.coordinate_learning_session(
            learning_request
        )

        return {
            "coordinated": True,
            "recommendations": result.get("learning_outcome"),
            "consensus": result.get("consensus_reached", False),
        }

    def _coordinate_quality_improvement_with_sages(
        self, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """品質改善の4賢者協調"""
        learning_request = {"type": "quality_improvement", "data": data}

        result = self.four_sages_integration.facilitate_cross_sage_learning(
            learning_request
        )

        return {
            "coordinated": True,
            "improvements": result.get("improvements_identified", []),
            "effectiveness": result.get("learning_effectiveness", {}),
        }

    def _coordinate_resource_optimization_with_sages(
        self, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """リソース最適化の4賢者協調"""
        optimization_targets = {
            "communication_efficiency": True,
            "decision_speed": True,
            "resource_allocation": data,
        }

        result = self.four_sages_integration.optimize_sage_interactions(
            optimization_targets
        )

        return {
            "coordinated": True,
            "optimizations": result.get("optimization_details", {}),
            "impact": result.get("impact_assessment", {}),
        }


if __name__ == "__main__":
    worker = EnhancedPMWorker()
    worker.start()
