#!/usr/bin/env python3
"""
PM-Elder統合システム v1.0
Enhanced PM WorkerとElder Councilの連携強化
重要なプロジェクト決定における Elder 承認プロセス
"""

import json
import logging
import os
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from libs.elder_council_summoner import (
        CouncilTrigger,
        ElderCouncilSummoner,
        SystemEvolutionMetrics,
        TriggerCategory,
        UrgencyLevel,
    )
    from libs.slack_notifier import SlackNotifier
except ImportError as e:
    logging.warning(f"Some imports failed: {e}")

logger = logging.getLogger(__name__)


class ProjectComplexity(Enum):
    """プロジェクト複雑度レベル"""

    SIMPLE = "simple"  # 自動承認可能
    MODERATE = "moderate"  # PM判断 + Elder通知
    COMPLEX = "complex"  # Elder事前承認必要
    CRITICAL = "critical"  # Elder Council必須


class ElderDecisionType(Enum):
    """Elder判断タイプ"""

    PROJECT_APPROVAL = "project_approval"
    ARCHITECTURE_CHANGE = "architecture_change"
    QUALITY_ESCALATION = "quality_escalation"
    RESOURCE_ALLOCATION = "resource_allocation"
    STRATEGIC_DIRECTION = "strategic_direction"
    EMERGENCY_RESPONSE = "emergency_response"


@dataclass
class ElderConsultationRequest:
    """Elder相談要求"""

    request_id: str
    decision_type: ElderDecisionType
    urgency: UrgencyLevel
    project_id: Optional[str]
    title: str
    description: str
    context: Dict[str, Any]
    pm_recommendation: str
    four_sages_input: Optional[Dict[str, Any]]
    required_decision_by: datetime
    created_at: datetime
    status: str = "pending"  # pending, approved, rejected, escalated


@dataclass
class ProjectElderApproval:
    """プロジェクトElder承認"""

    project_id: str
    approval_id: str
    complexity: ProjectComplexity
    request_summary: str
    elder_decision: Optional[str] = None
    conditions: List[str] = None
    approved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class PMElderIntegration:
    """PM-Elder統合システム"""

    def __init__(self):
        """初期化"""
        self.elder_summoner = ElderCouncilSummoner()
        self.slack = SlackNotifier()

        # 相談要求の管理
        self.consultation_requests: Dict[str, ElderConsultationRequest] = {}
        self.project_approvals: Dict[str, ProjectElderApproval] = {}

        # 閾値設定
        self.complexity_thresholds = self._load_complexity_thresholds()

        logger.info("PM-Elder Integration System initialized")

    def _load_complexity_thresholds(self) -> Dict[str, Any]:
        """複雑度判定閾値の設定"""
        return {
            "critical_indicators": [
                "system-wide architectural change",
                "breaking changes to public API",
                "database schema migration",
                "security-critical modification",
                "multi-service integration",
                "performance-critical optimization",
            ],
            "complex_indicators": [
                "new service creation",
                "integration with external systems",
                "workflow modification",
                "significant algorithm changes",
                "infrastructure changes",
            ],
            "moderate_indicators": [
                "feature enhancement",
                "bug fix with architectural impact",
                "configuration changes",
                "documentation updates",
                "testing framework changes",
            ],
        }

    # ============================================
    # プロジェクト複雑度評価
    # ============================================

    def assess_project_complexity(
        self, project_data: Dict[str, Any]
    ) -> ProjectComplexity:
        """プロジェクト複雑度評価"""
        try:
            prompt = project_data.get("prompt", "").lower()
            files_created = project_data.get("files_created", [])
            task_type = project_data.get("task_type", "")

            # 重要度スコア計算
            complexity_score = 0

            # Critical indicators
            critical_matches = sum(
                1
                for indicator in self.complexity_thresholds["critical_indicators"]
                if any(word in prompt for word in indicator.split())
            )
            complexity_score += critical_matches * 10

            # Complex indicators
            complex_matches = sum(
                1
                for indicator in self.complexity_thresholds["complex_indicators"]
                if any(word in prompt for word in indicator.split())
            )
            complexity_score += complex_matches * 5

            # Moderate indicators
            moderate_matches = sum(
                1
                for indicator in self.complexity_thresholds["moderate_indicators"]
                if any(word in prompt for word in indicator.split())
            )
            complexity_score += moderate_matches * 2

            # ファイル数による追加判定
            if len(files_created) > 10:
                complexity_score += 5
            elif len(files_created) > 5:
                complexity_score += 2

            # 複雑度レベル決定
            if complexity_score >= 15:
                return ProjectComplexity.CRITICAL
            elif complexity_score >= 8:
                return ProjectComplexity.COMPLEX
            elif complexity_score >= 3:
                return ProjectComplexity.MODERATE
            else:
                return ProjectComplexity.SIMPLE

        except Exception as e:
            logger.error(f"Project complexity assessment failed: {e}")
            return ProjectComplexity.MODERATE  # デフォルトは慎重に

    # ============================================
    # Elder承認プロセス
    # ============================================

    def request_project_approval(
        self, project_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """プロジェクト承認要求"""
        try:
            project_id = project_data.get("project_id") or str(uuid.uuid4())
            complexity = self.assess_project_complexity(project_data)

            logger.info(
                f"Project {project_id} complexity assessed as: {complexity.value}"
            )

            if complexity == ProjectComplexity.SIMPLE:
                # 単純プロジェクトは自動承認
                return True, "Auto-approved (simple project)"

            elif complexity == ProjectComplexity.MODERATE:
                # 中程度は通知のみで進行可能
                self._notify_elders_project_start(project_id, project_data, complexity)
                return True, "Approved with Elder notification"

            else:  # COMPLEX or CRITICAL
                # 複雑・重要プロジェクトはElder承認必要
                approval_request = self._create_approval_request(
                    project_id, project_data, complexity
                )

                if complexity == ProjectComplexity.CRITICAL:
                    # CRITICALの場合はElder Council召集
                    self._summon_elder_council_for_project(project_id, project_data)

                return False, f"Elder approval required ({complexity.value})"

        except Exception as e:
            logger.error(f"Project approval request failed: {e}")
            return False, f"Approval process error: {e}"

    def _create_approval_request(
        self,
        project_id: str,
        project_data: Dict[str, Any],
        complexity: ProjectComplexity,
    ) -> ProjectElderApproval:
        """承認要求作成"""
        approval = ProjectElderApproval(
            project_id=project_id,
            approval_id=str(uuid.uuid4()),
            complexity=complexity,
            request_summary=self._generate_approval_summary(project_data),
            expires_at=datetime.now() + timedelta(days=7),  # 1週間有効
        )

        self.project_approvals[project_id] = approval

        # Slack通知
        self._send_approval_request_notification(approval, project_data)

        return approval

    def _generate_approval_summary(self, project_data: Dict[str, Any]) -> str:
        """承認要求サマリー生成"""
        prompt = project_data.get("prompt", "")
        files_count = len(project_data.get("files_created", []))
        task_type = project_data.get("task_type", "general")

        summary = f"""
## プロジェクト承認要求

**タスク内容**: {prompt[:200]}...

**ファイル作成予定**: {files_count}ファイル

**タスクタイプ**: {task_type}

**影響範囲**: {self._assess_impact_scope(project_data)}

**推定リスク**: {self._assess_project_risk(project_data)}
        """.strip()

        return summary

    def _assess_impact_scope(self, project_data: Dict[str, Any]) -> str:
        """影響範囲評価"""
        prompt = project_data.get("prompt", "").lower()

        scopes = []
        if any(word in prompt for word in ["api", "interface", "endpoint"]):
            scopes.append("API層")
        if any(word in prompt for word in ["database", "db", "schema"]):
            scopes.append("データベース層")
        if any(word in prompt for word in ["worker", "process", "service"]):
            scopes.append("ワーカー層")
        if any(word in prompt for word in ["config", "setting", "parameter"]):
            scopes.append("設定層")

        return ", ".join(scopes) if scopes else "限定的"

    def _assess_project_risk(self, project_data: Dict[str, Any]) -> str:
        """プロジェクトリスク評価"""
        prompt = project_data.get("prompt", "").lower()

        risk_indicators = [
            ("高リスク", ["breaking", "migration", "security", "critical"]),
            ("中リスク", ["integration", "new service", "algorithm"]),
            ("低リスク", ["enhancement", "documentation", "config"]),
        ]

        for risk_level, indicators in risk_indicators:
            if any(indicator in prompt for indicator in indicators):
                return risk_level

        return "未評価"

    # ============================================
    # Elder Council召集
    # ============================================

    def _summon_elder_council_for_project(
        self, project_id: str, project_data: Dict[str, Any]
    ):
        """プロジェクト用Elder Council召集"""
        try:
            trigger = CouncilTrigger(
                trigger_id=f"project_approval_{project_id}",
                category=TriggerCategory.STRATEGIC_DECISION,
                urgency=UrgencyLevel.HIGH,
                title=f"重要プロジェクト承認要求: {project_id}",
                description=f"複雑度CRITICALプロジェクトの承認が必要です。\n\n{project_data.get('prompt', '')[:300]}",
                triggered_at=datetime.now(),
                metrics={
                    "project_complexity": "CRITICAL",
                    "files_count": len(project_data.get("files_created", [])),
                    "task_type": project_data.get("task_type", "unknown"),
                },
                affected_systems=["project_management", "system_architecture"],
                suggested_agenda=[
                    "プロジェクト要件の詳細審査",
                    "アーキテクチャ影響度評価",
                    "リスク評価と緩和策",
                    "リソース配分の確認",
                    "承認・却下・条件付き承認の決定",
                ],
                auto_analysis={
                    "pm_recommendation": "Elder Council承認待ち",
                    "complexity_assessment": "CRITICAL",
                    "urgent_decision_required": True,
                },
            )

            # 4賢者からの意見収集
            trigger.four_sages_input = self._collect_four_sages_input_for_project(
                project_data
            )

            # Elder Council召集
            self.elder_summoner._evaluate_and_schedule_council(trigger)

            logger.info(f"Elder Council summoned for project {project_id}")

        except Exception as e:
            logger.error(f"Elder Council summoning failed: {e}")

    def _collect_four_sages_input_for_project(
        self, project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """プロジェクト用4賢者意見収集"""
        return {
            "knowledge_sage": {
                "opinion": "既存知識ベースとの整合性確認が必要",
                "concerns": ["重複する実装の可能性", "既存パターンからの逸脱"],
                "recommendations": ["既存アーキテクチャパターンの再利用検討"],
            },
            "task_oracle": {
                "opinion": "プロジェクト実行計画の詳細化が必要",
                "concerns": ["リソース競合の可能性", "依存関係の複雑化"],
                "recommendations": ["段階的実装アプローチの採用"],
            },
            "crisis_sage": {
                "opinion": "リスク評価と緩和策の策定が重要",
                "concerns": ["システム停止リスク", "データ損失の可能性"],
                "recommendations": ["包括的なロールバック計画の作成"],
            },
            "search_mystic": {
                "opinion": "情報アクセスパターンへの影響評価必要",
                "concerns": ["検索性能への影響", "データ整合性の維持"],
                "recommendations": ["段階的移行による影響最小化"],
            },
        }

    # ============================================
    # 通知システム
    # ============================================

    def _notify_elders_project_start(
        self,
        project_id: str,
        project_data: Dict[str, Any],
        complexity: ProjectComplexity,
    ):
        """Elderへのプロジェクト開始通知"""
        try:
            message = f"""
🚀 **プロジェクト開始通知**

**プロジェクトID**: {project_id}
**複雑度**: {complexity.value}
**内容**: {project_data.get('prompt', '')[:200]}...

このプロジェクトは自動承認で開始されましたが、
進捗について定期的にご報告いたします。

Elder Councilによる介入が必要な場合は、
いつでもお申し付けください。
            """.strip()

            self.slack.send_message(message, channel="#elders-notifications")
            logger.info(f"Elder notification sent for project {project_id}")

        except Exception as e:
            logger.error(f"Elder notification failed: {e}")

    def _send_approval_request_notification(
        self, approval: ProjectElderApproval, project_data: Dict[str, Any]
    ):
        """承認要求通知送信"""
        try:
            message = f"""
🔔 **Elder承認要求**

**プロジェクトID**: {approval.project_id}
**承認ID**: {approval.approval_id}
**複雑度**: {approval.complexity.value}
**有効期限**: {approval.expires_at.strftime('%Y-%m-%d %H:%M')}

{approval.request_summary}

**対応方法**:
- 承認: `/elder approve {approval.approval_id}`
- 却下: `/elder reject {approval.approval_id} [理由]`
- 条件付き承認: `/elder approve {approval.approval_id} --conditions "条件"`
- Council召集: `/elder council {approval.approval_id}`
            """.strip()

            self.slack.send_message(message, channel="#elders-urgent")
            logger.info(f"Approval request notification sent for {approval.project_id}")

        except Exception as e:
            logger.error(f"Approval notification failed: {e}")

    # ============================================
    # 品質エスカレーション
    # ============================================

    def escalate_quality_issue(
        self, project_id: str, quality_issues: List[str], iteration_count: int
    ) -> bool:
        """品質問題のElder エスカレーション"""
        try:
            if iteration_count >= 3:  # 3回失敗でElder介入
                consultation = ElderConsultationRequest(
                    request_id=str(uuid.uuid4()),
                    decision_type=ElderDecisionType.QUALITY_ESCALATION,
                    urgency=UrgencyLevel.HIGH,
                    project_id=project_id,
                    title=f"品質問題エスカレーション: プロジェクト {project_id}",
                    description=f"""
プロジェクト {project_id} で品質問題が継続しています。

**失敗回数**: {iteration_count}回
**主な問題**:
{chr(10).join(f'- {issue}' for issue in quality_issues)}

PM判断だけでは解決困難と判断し、Elder Councilの
戦略的指導を要請いたします。
                    """.strip(),
                    context={
                        "iteration_count": iteration_count,
                        "quality_issues": quality_issues,
                        "project_complexity": "escalated",
                    },
                    pm_recommendation="Elder Council による代替アプローチの検討を推奨",
                    four_sages_input=None,
                    required_decision_by=datetime.now() + timedelta(hours=24),
                    created_at=datetime.now(),
                )

                self.consultation_requests[consultation.request_id] = consultation

                # Elder Council 召集
                self._summon_elder_council_for_quality_issue(consultation)

                return True

            return False

        except Exception as e:
            logger.error(f"Quality escalation failed: {e}")
            return False

    def _summon_elder_council_for_quality_issue(
        self, consultation: ElderConsultationRequest
    ):
        """品質問題用Elder Council召集"""
        try:
            trigger = CouncilTrigger(
                trigger_id=f"quality_escalation_{consultation.request_id}",
                category=TriggerCategory.STRATEGIC_DECISION,
                urgency=UrgencyLevel.HIGH,
                title=consultation.title,
                description=consultation.description,
                triggered_at=datetime.now(),
                metrics={
                    "escalation_type": "quality_issue",
                    "iteration_count": consultation.context.get("iteration_count", 0),
                },
                affected_systems=["quality_management", "project_execution"],
                suggested_agenda=[
                    "品質問題の根本原因分析",
                    "現在のアプローチの評価",
                    "代替実装戦略の検討",
                    "品質基準の再評価",
                    "プロジェクト継続・中止の判断",
                ],
                auto_analysis={
                    "pm_escalation": True,
                    "quality_crisis": True,
                    "urgent_intervention_required": True,
                },
            )

            self.elder_summoner._evaluate_and_schedule_council(trigger)

            logger.info(
                f"Elder Council summoned for quality issue {consultation.request_id}"
            )

        except Exception as e:
            logger.error(f"Quality issue Elder Council summoning failed: {e}")

    # ============================================
    # プロジェクト完了報告
    # ============================================

    def report_project_completion(
        self, project_id: str, project_result: Dict[str, Any]
    ):
        """プロジェクト完了のElder報告"""
        try:
            complexity = self.project_approvals.get(project_id, {}).get(
                "complexity", ProjectComplexity.SIMPLE
            )

            # COMPLEX以上のプロジェクトは完了報告必須
            if complexity in [ProjectComplexity.COMPLEX, ProjectComplexity.CRITICAL]:
                report_message = f"""
✅ **プロジェクト完了報告**

**プロジェクトID**: {project_id}
**複雑度**: {complexity.value}
**完了日時**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

**実施結果**:
- 配置ファイル数: {len(project_result.get('placed_files', []))}
- 品質スコア: {project_result.get('quality_score', '未評価')}
- 実行時間: {project_result.get('execution_time', '未計測')}

**主な成果物**:
{chr(10).join(f'- {file}' for file in project_result.get('placed_files', [])[:5])}

Elder Councilにより承認いただいたプロジェクトが
正常に完了いたしました。ご指導ありがとうございました。
                """.strip()

                self.slack.send_message(report_message, channel="#elders-reports")

                # 承認記録をクリーンアップ
                if project_id in self.project_approvals:
                    del self.project_approvals[project_id]

                logger.info(f"Project completion reported to Elders: {project_id}")

        except Exception as e:
            logger.error(f"Project completion reporting failed: {e}")

    # ============================================
    # 状態管理
    # ============================================

    def get_pending_approvals(self) -> List[ProjectElderApproval]:
        """保留中の承認要求一覧"""
        return [
            approval
            for approval in self.project_approvals.values()
            if approval.elder_decision is None
        ]

    def approve_project(self, approval_id: str, conditions: List[str] = None) -> bool:
        """プロジェクト承認"""
        try:
            for approval in self.project_approvals.values():
                if approval.approval_id == approval_id:
                    approval.elder_decision = "approved"
                    approval.conditions = conditions or []
                    approval.approved_at = datetime.now()

                    logger.info(f"Project {approval.project_id} approved by Elders")
                    return True

            return False

        except Exception as e:
            logger.error(f"Project approval failed: {e}")
            return False

    def reject_project(self, approval_id: str, reason: str) -> bool:
        """プロジェクト却下"""
        try:
            for approval in self.project_approvals.values():
                if approval.approval_id == approval_id:
                    approval.elder_decision = f"rejected: {reason}"

                    logger.info(
                        f"Project {approval.project_id} rejected by Elders: {reason}"
                    )
                    return True

            return False

        except Exception as e:
            logger.error(f"Project rejection failed: {e}")
            return False

    def get_integration_status(self) -> Dict[str, Any]:
        """統合システムの状態取得"""
        return {
            "pending_approvals": len(self.get_pending_approvals()),
            "consultation_requests": len(self.consultation_requests),
            "elder_summoner_active": self.elder_summoner.monitoring_active,
            "last_assessment": datetime.now().isoformat(),
        }


# ============================================
# ユーティリティ関数
# ============================================


def create_pm_elder_integration() -> PMElderIntegration:
    """PM-Elder統合システムのファクトリー関数"""
    return PMElderIntegration()


# ============================================
# テスト実行
# ============================================

if __name__ == "__main__":
    # 基本機能テスト
    integration = PMElderIntegration()

    # サンプルプロジェクトの複雑度評価
    sample_project = {
        "project_id": "test_001",
        "prompt": "Create a new microservice with database integration and API endpoints",
        "files_created": ["service.py", "api.py", "database.py", "config.py"],
        "task_type": "service_creation",
    }

    complexity = integration.assess_project_complexity(sample_project)
    print(f"Project complexity: {complexity.value}")

    approved, message = integration.request_project_approval(sample_project)
    print(f"Approval result: {approved}, Message: {message}")

    status = integration.get_integration_status()
    print(f"Integration status: {status}")
