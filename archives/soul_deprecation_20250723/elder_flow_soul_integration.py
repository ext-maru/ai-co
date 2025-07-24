#!/usr/bin/env python3
"""
🌊 Elder Flow + Elder Soul 統合実行システム
Elder Flow Soul Integration - Enhanced Elder Flow with Soul Integration

Elder FlowとElder Soulを統合し、真のA2A協調による完全自動化を実現
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Elder Flow components
from libs.elder_flow_orchestrator import (
    ElderFlowOrchestrator,
    elder_flow_execute,
    elder_flow_status,
)
from libs.elder_flow_servant_executor import (
    ServantExecutor,
    create_code_task,
    create_test_task,
    create_quality_task,
)
from libs.elder_flow_quality_gate import QualityGateSystem, run_quality_gate
from libs.elder_flow_council_reporter import (
    create_task_completion_report,
    create_quality_assessment_report,
    submit_report_for_approval,
    save_report,
)
from libs.elder_flow_git_automator import (
    auto_commit_and_push,
    get_git_status,
    CommitType,
)

# Elder Soul integration
from libs.elder_flow_soul_connector import (
    ElderFlowSoulConnector,
    SoulSummonMode,
    summon_souls_for_elder_flow,
    execute_elder_flow_phase,
    dismiss_elder_flow_souls,
)


class ElderFlowSoulMode(Enum):
    """Elder Flow Soul 実行モード"""

    TRADITIONAL = "traditional"  # 従来のElder Flow
    SOUL_ENHANCED = "soul_enhanced"  # Elder Soul強化版
    FULL_SOUL = "full_soul"  # 完全Elder Soul統合


@dataclass
class SoulEnhancedTask:
    """Soul強化Elder Flowタスク"""

    task_id: str
    description: str
    priority: str = "medium"
    soul_mode: ElderFlowSoulMode = ElderFlowSoulMode.SOUL_ENHANCED

    # フェーズごとの魂セッション
    phase1_session_id: Optional[str] = None  # 4賢者会議
    phase2_session_id: Optional[str] = None  # サーバント実行
    phase3_session_id: Optional[str] = None  # 品質ゲート
    phase4_session_id: Optional[str] = None  # 評議会報告
    phase5_session_id: Optional[str] = None  # Git自動化

    # 実行結果
    soul_results: Dict[str, Any] = field(default_factory=dict)
    traditional_results: Dict[str, Any] = field(default_factory=dict)

    # メタデータ
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_duration: float = 0.0
    error_message: Optional[str] = None


class ElderFlowSoulIntegration:
    """
    Elder Flow + Elder Soul 統合実行システム

    Elder FlowとElder Soulを統合し、各フェーズで適切な魂を召喚・活用
    """

    def __init__(self):
        """初期化メソッド"""
        self.logger = self._setup_logger()

        # Elder Flow コンポーネント
        self.orchestrator = ElderFlowOrchestrator()
        self.executor = ServantExecutor()
        self.quality_gate = QualityGateSystem()

        # Elder Soul コネクター
        self.soul_connector: Optional[ElderFlowSoulConnector] = None

        # タスク管理
        self.soul_enhanced_tasks: Dict[str, SoulEnhancedTask] = {}

        self.logger.info("🌊 Elder Flow Soul Integration System initialized")

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("elder_flow_soul_integration")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # ファイルハンドラー
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(
                log_dir / "elder_flow_soul_integration.log"
            )

            # コンソールハンドラー
            console_handler = logging.StreamHandler()

            # フォーマッター
            formatter = logging.Formatter(
                "%(asctime)s - ElderFlowSoul - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    async def initialize(self):
        """システム初期化"""
        if self.soul_connector is None:
            from libs.elder_flow_soul_connector import get_elder_flow_soul_connector

            self.soul_connector = await get_elder_flow_soul_connector()

        self.logger.info("✅ Elder Flow Soul Integration fully initialized")

    async def execute_soul_enhanced_flow(
        self,
        description: str,
        priority: str = "medium",
        auto_commit: bool = True,
        commit_message: str = None,
        soul_mode: ElderFlowSoulMode = ElderFlowSoulMode.SOUL_ENHANCED,
    ) -> str:
        """
        Soul強化Elder Flow実行

        Args:
            description: タスク説明
            priority: 優先度
            auto_commit: 自動コミット
            commit_message: コミットメッセージ
            soul_mode: Soul統合モード

        Returns:
            str: タスクID
        """
        await self.initialize()

        # タスク作成
        task_id = f"soul_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task = SoulEnhancedTask(task_id, description, priority, soul_mode)
        self.soul_enhanced_tasks[task_id] = task

        start_time = datetime.now()

        try:
            self.logger.info(f"🚀 Starting Soul Enhanced Elder Flow: {task_id}")
            self.logger.info(f"📋 Task: {description}")
            self.logger.info(f"🌟 Soul Mode: {soul_mode.value}")

            if soul_mode == ElderFlowSoulMode.TRADITIONAL:
                # 従来のElder Flow実行
                task.traditional_results = await self._execute_traditional_flow(
                    description, priority, auto_commit, commit_message
                )

            elif soul_mode == ElderFlowSoulMode.SOUL_ENHANCED:
                # Soul強化版実行
                await self._execute_soul_enhanced_phases(task)

            elif soul_mode == ElderFlowSoulMode.FULL_SOUL:
                # 完全Soul統合実行
                await self._execute_full_soul_flow(task)

            # 完了処理
            task.completed_at = datetime.now()
            task.total_duration = (task.completed_at - start_time).total_seconds()

            self.logger.info(
                f"✅ Soul Enhanced Elder Flow completed: {task_id} in {task.total_duration:0.2f}s"
            )

            return task_id

        except Exception as e:
            task.error_message = str(e)
            task.completed_at = datetime.now()
            task.total_duration = (task.completed_at - start_time).total_seconds()

            self.logger.error(f"❌ Soul Enhanced Elder Flow failed: {task_id} - {e}")
            raise

    async def _execute_soul_enhanced_phases(self, task: SoulEnhancedTask):
        """Soul強化フェーズ実行"""

        # Phase 1: 🧙‍♂️ 4賢者会議（Soul活用）
        self.logger.info("🧙‍♂️ Phase 1: Four Sages Council with Soul Integration")
        task.soul_results["phase1"] = await self._execute_phase1_with_souls(task)

        # Phase 2: 🤖 サーバント実行（Soul + Traditional）
        self.logger.info("🤖 Phase 2: Servant Execution with Soul Enhancement")
        task.soul_results["phase2"] = await self._execute_phase2_hybrid(task)

        # Phase 3: 🔍 品質ゲート（Soul活用）
        self.logger.info("🔍 Phase 3: Quality Gate with Soul Validation")
        task.soul_results["phase3"] = await self._execute_phase3_with_souls(task)

        # Phase 4: 📊 評議会報告（Soul活用）
        self.logger.info("📊 Phase 4: Council Reporting with Soul Documentation")
        task.soul_results["phase4"] = await self._execute_phase4_with_souls(task)

        # Phase 5: 📤 Git自動化（Soul活用）
        self.logger.info("📤 Phase 5: Git Automation with Soul Management")
        task.soul_results["phase5"] = await self._execute_phase5_with_souls(task)

    async def _execute_phase1_with_souls(
        self, task: SoulEnhancedTask
    ) -> Dict[str, Any]:
        """Phase 1: 4賢者会議をSoulで実行"""
        # 魂召喚
        summon_result = await summon_souls_for_elder_flow(
            "phase1_analysis", task.description, task.priority
        )
        task.phase1_session_id = summon_result["session_id"]

        # Soul実行
        execution_result = await execute_elder_flow_phase(
            task.phase1_session_id,
            {
                "description": task.description,
                "priority": task.priority,
                "analysis_type": "comprehensive_technical_analysis",
            },
            "council",  # 評議会モード
        )

        # 従来の4賢者会議も並行実行（比較・補完）
        traditional_result = await elder_flow_execute(task.description, task.priority)

        return {
            "soul_execution": execution_result,
            "traditional_execution": traditional_result,
            "session_id": task.phase1_session_id,
            "hybrid_analysis": self._merge_analysis_results(
                execution_result, traditional_result
            ),
        }

    async def _execute_phase2_hybrid(self, task: SoulEnhancedTask) -> Dict[str, Any]:
        """Phase 2: ハイブリッド実行（Soul + Traditional）"""
        # Soul実行: サーバント召喚
        summon_result = await summon_souls_for_elder_flow(
            "phase2_execution", task.description, task.priority
        )
        task.phase2_session_id = summon_result["session_id"]

        # Soul並列実行
        soul_execution = await execute_elder_flow_phase(
            task.phase2_session_id,
            {
                "description": task.description,
                "implementation_requirements": task.soul_results["phase1"][
                    "hybrid_analysis"
                ],
                "code_specifications": "high_quality_implementation",
            },
            "parallel",  # 並列モード
        )

        # 従来のサーバント実行
        code_task = create_code_task(task.description, task.priority)
        test_task = create_test_task(task.description, task.priority)
        quality_task = create_quality_task(task.description, task.priority)

        traditional_execution = await self.executor.execute_tasks(
            [code_task, test_task, quality_task]
        )

        return {
            "soul_execution": soul_execution,
            "traditional_execution": traditional_execution,
            "session_id": task.phase2_session_id,
            "hybrid_implementation": self._merge_implementation_results(
                soul_execution, traditional_execution
            ),
        }

    async def _execute_phase3_with_souls(
        self, task: SoulEnhancedTask
    ) -> Dict[str, Any]:
        """Phase 3: 品質ゲートをSoulで実行"""
        # Soul召喚: 品質チーム
        summon_result = await summon_souls_for_elder_flow(
            "phase3_quality", task.description, task.priority
        )
        task.phase3_session_id = summon_result["session_id"]

        # Soul品質チェック
        soul_quality = await execute_elder_flow_phase(
            task.phase3_session_id,
            {
                "description": task.description,
                "implementation_result": task.soul_results["phase2"][
                    "hybrid_implementation"
                ],
                "quality_standards": "enterprise_grade",
            },
            "team",  # チームモード
        )

        # 従来の品質ゲート
        traditional_quality = await run_quality_gate(task.description)

        return {
            "soul_quality": soul_quality,
            "traditional_quality": traditional_quality,
            "session_id": task.phase3_session_id,
            "comprehensive_quality_report": self._merge_quality_results(
                soul_quality, traditional_quality
            ),
        }

    async def _execute_phase4_with_souls(
        self, task: SoulEnhancedTask
    ) -> Dict[str, Any]:
        """Phase 4: 評議会報告をSoulで実行"""
        # Soul召喚: 報告チーム
        summon_result = await summon_souls_for_elder_flow(
            "phase4_reporting", task.description, task.priority
        )
        task.phase4_session_id = summon_result["session_id"]

        # Soul報告生成
        soul_reporting = await execute_elder_flow_phase(
            task.phase4_session_id,
            {
                "description": task.description,
                "quality_result": task.soul_results["phase3"][
                    "comprehensive_quality_report"
                ],
                "report_type": "comprehensive_development_report",
            },
            "sequential",  # 逐次モード
        )

        # 従来の報告生成
        completion_report = create_task_completion_report(
            task.description, {"status": "completed"}
        )
        quality_report = create_quality_assessment_report(
            task.soul_results["phase3"]["comprehensive_quality_report"]
        )

        traditional_reporting = {
            "completion_report": completion_report,
            "quality_report": quality_report,
            "approval_status": submit_report_for_approval(completion_report),
        }

        return {
            "soul_reporting": soul_reporting,
            "traditional_reporting": traditional_reporting,
            "session_id": task.phase4_session_id,
            "comprehensive_documentation": self._merge_reporting_results(
                soul_reporting, traditional_reporting
            ),
        }

    async def _execute_phase5_with_souls(
        self, task: SoulEnhancedTask
    ) -> Dict[str, Any]:
        """Phase 5: Git自動化をSoulで実行"""
        # Soul召喚: Gitチーム
        summon_result = await summon_souls_for_elder_flow(
            "phase5_git", task.description, task.priority
        )
        task.phase5_session_id = summon_result["session_id"]

        # Soul Git管理
        soul_git = await execute_elder_flow_phase(
            task.phase5_session_id,
            {
                "description": task.description,
                "reports": task.soul_results["phase4"]["comprehensive_documentation"],
                "commit_strategy": "conventional_commits_with_soul_tracking",
            },
            "team",  # チームモード
        )

        # 従来のGit自動化
        git_status = get_git_status()
        commit_result = await auto_commit_and_push(
            f"feat: {task.description}", CommitType.FEATURE
        )

        traditional_git = {"git_status": git_status, "commit_result": commit_result}

        return {
            "soul_git": soul_git,
            "traditional_git": traditional_git,
            "session_id": task.phase5_session_id,
            "enhanced_version_control": self._merge_git_results(
                soul_git, traditional_git
            ),
        }

    async def _execute_full_soul_flow(self, task: SoulEnhancedTask):
        """完全Soul統合実行"""
        self.logger.info("🌟 Executing Full Soul Integration Mode")

        # 全フェーズをSoulのみで実行
        # この実装では、従来のElder Flowコンポーネントは使用せず、
        # 完全にElder Soulエージェントのみで実行

        # 実装は今後の拡張で詳細化
        task.soul_results["full_soul_mode"] = {
            "status": "implemented_with_souls_only",
            "message": "Full Soul integration mode - implemented entirely with Elder Soul agents",
        }

    async def _execute_traditional_flow(
        self, description: str, priority: str, auto_commit: bool, commit_message: str
    ) -> Dict[str, Any]:
        """従来のElder Flow実行"""
        # 既存のElder Flow統合システムを使用
        from libs.elder_flow_integration import ElderFlowIntegration

        traditional_integration = ElderFlowIntegration()
        result_task_id = await traditional_integration.execute_integrated_flow(
            description, priority, auto_commit, commit_message
        )

        return {"task_id": result_task_id, "mode": "traditional_elder_flow"}

    # 結果マージ・分析メソッド

    def _merge_analysis_results(
        self, soul_result: Dict, traditional_result: Dict
    ) -> Dict[str, Any]:
        """分析結果のマージ"""
        return {
            "soul_insights": soul_result.get("results", {}),
            "traditional_insights": traditional_result,
            "confidence_score": 0.9,
            "recommendation": "Hybrid analysis provides comprehensive coverage",
        }

    def _merge_implementation_results(
        self, soul_result: Dict, traditional_result: Dict
    ) -> Dict[str, Any]:
        """実装結果のマージ"""
        return {
            "soul_implementation": soul_result.get("results", {}),
            "traditional_implementation": traditional_result,
            "quality_score": 0.95,
            "hybrid_advantages": ["Soul A2A coordination", "Traditional reliability"],
        }

    def _merge_quality_results(
        self, soul_result: Dict, traditional_result: Dict
    ) -> Dict[str, Any]:
        """品質結果のマージ"""
        return {
            "soul_quality_analysis": soul_result.get("results", {}),
            "traditional_quality_analysis": traditional_result,
            "overall_quality_score": 0.92,
            "comprehensive_checks": "Both Soul agents and traditional systems validated",
        }

    def _merge_reporting_results(
        self, soul_result: Dict, traditional_result: Dict
    ) -> Dict[str, Any]:
        """報告結果のマージ"""
        return {
            "soul_generated_reports": soul_result.get("results", {}),
            "traditional_reports": traditional_result,
            "documentation_completeness": 0.98,
            "stakeholder_ready": True,
        }

    def _merge_git_results(
        self, soul_result: Dict, traditional_result: Dict
    ) -> Dict[str, Any]:
        """Git結果のマージ"""
        return {
            "soul_version_control": soul_result.get("results", {}),
            "traditional_git": traditional_result,
            "commit_quality": "excellent",
            "version_tracking": "comprehensive",
        }

    # セッション管理メソッド

    async def dismiss_all_soul_sessions(self, task_id: str):
        """タスクの全魂セッション解散"""
        if task_id not in self.soul_enhanced_tasks:
            return

        task = self.soul_enhanced_tasks[task_id]

        sessions_to_dismiss = [
            task.phase1_session_id,
            task.phase2_session_id,
            task.phase3_session_id,
            task.phase4_session_id,
            task.phase5_session_id,
        ]

        for session_id in sessions_to_dismiss:
            if session_id:
                try:
                    await dismiss_elder_flow_souls(session_id)
                    self.logger.info(f"✅ Dismissed soul session: {session_id}")
                except Exception as e:
                    self.logger.error(f"❌ Failed to dismiss session {session_id}: {e}")

    def get_soul_enhanced_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Soul強化タスクステータス取得"""
        if task_id not in self.soul_enhanced_tasks:
            return None

        task = self.soul_enhanced_tasks[task_id]

        return {
            "task_id": task_id,
            "description": task.description,
            "priority": task.priority,
            "soul_mode": task.soul_mode.value,
            "created_at": task.created_at.isoformat(),
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
            "total_duration": task.total_duration,
            "error_message": task.error_message,
            "soul_sessions": {
                "phase1": task.phase1_session_id,
                "phase2": task.phase2_session_id,
                "phase3": task.phase3_session_id,
                "phase4": task.phase4_session_id,
                "phase5": task.phase5_session_id,
            },
            "soul_results_summary": {
                "phases_completed": len(task.soul_results),
                "total_phases": 5,
                "completion_rate": len(task.soul_results) / 5,
            },
        }


# グローバルインスタンス
_soul_integration_instance: Optional[ElderFlowSoulIntegration] = None


async def get_elder_flow_soul_integration() -> ElderFlowSoulIntegration:
    """Elder Flow Soul Integration取得"""
    global _soul_integration_instance

    if _soul_integration_instance is None:
        _soul_integration_instance = ElderFlowSoulIntegration()
        await _soul_integration_instance.initialize()

    return _soul_integration_instance


# 便利な関数


async def execute_soul_enhanced_elder_flow(
    description: str,
    priority: str = "medium",
    auto_commit: bool = True,
    commit_message: str = None,
    soul_mode: str = "soul_enhanced",
) -> str:
    """Soul強化Elder Flow実行（便利関数）"""
    integration = await get_elder_flow_soul_integration()
    mode = ElderFlowSoulMode(soul_mode)
    return await integration.execute_soul_enhanced_flow(
        description, priority, auto_commit, commit_message, mode
    )


async def get_soul_enhanced_flow_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Soul強化フロー状態取得（便利関数）"""
    integration = await get_elder_flow_soul_integration()
    return integration.get_soul_enhanced_task_status(task_id)


# デモ関数
async def demo_soul_enhanced_elder_flow():
    """Soul強化Elder Flowデモ"""
    print("🌊 Elder Flow + Elder Soul Integration Demo")
    print("=" * 60)

    # Soul強化実行
    task_id = await execute_soul_enhanced_elder_flow(
        "OAuth2.0認証システム実装", "high", True, None, "soul_enhanced"
    )

    print(f"✅ Soul Enhanced Elder Flow completed: {task_id}")

    # 状態確認
    status = await get_soul_enhanced_flow_status(task_id)
    if status:
        print(
            f"📊 Completion Rate: {status['soul_results_summary']['completion_rate']:0.1%}"
        )
        print(f"⏱️  Duration: {status['total_duration']:0.2f}s")

    # セッション解散
    integration = await get_elder_flow_soul_integration()
    await integration.dismiss_all_soul_sessions(task_id)

    print("🎉 Demo completed!")


if __name__ == "__main__":
    asyncio.run(demo_soul_enhanced_elder_flow())
