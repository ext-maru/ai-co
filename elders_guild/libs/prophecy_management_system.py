#!/usr/bin/env python3
"""
🏛️ エルダーズギルド 予言書管理システム (Prophecy Management System)
4賢者による包括的な予言書管理・ガバナンス・品質保証システム
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import uuid
import hashlib

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProphecyLifecycleStage(Enum):
    """予言書ライフサイクル段階"""

    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class RiskLevel(Enum):
    """リスクレベル"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ApprovalStatus(Enum):
    """承認状況"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"

    """予言書テンプレート"""

        """初期化メソッド"""

        self.name = name
        self.description = description
        self.base_structure = {}
        self.customization_points = []
        self.validation_rules = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.version = "1.0"

    def generate_prophecy(self, customizations: Dict) -> Dict:
        """カスタマイズされた予言書生成"""
        prophecy_data = self.base_structure.copy()

        # カスタマイズ適用
        for key, value in customizations.items():
            if key in self.customization_points:
                prophecy_data[key] = value

        # 一意ID生成
        prophecy_data["prophecy_id"] = str(uuid.uuid4())

        prophecy_data["created_at"] = datetime.now().isoformat()

        return prophecy_data

    def validate_customizations(self, customizations: Dict) -> Dict:
        """カスタマイズ検証"""
        validation_result = {"valid": True, "errors": [], "warnings": []}

        for rule in self.validation_rules:
            result = rule.validate(customizations)
            if not result["valid"]:
                validation_result["valid"] = False
                validation_result["errors"].extend(result["errors"])
            validation_result["warnings"].extend(result.get("warnings", []))

        return validation_result

class ProphecyVersionControl:
    """予言書バージョン管理"""

    def __init__(self):
        """初期化メソッド"""
        self.version_history = {}
        self.branches = {}
        self.tags = {}

    def create_version(
        self, prophecy_name: str, prophecy_data: Dict, changes: Dict
    ) -> str:
        """新バージョン作成"""
        if prophecy_name not in self.version_history:
            self.version_history[prophecy_name] = []

        # バージョン番号生成
        version_number = self.generate_version_number(prophecy_name)

        # バージョン情報作成
        version_info = {
            "version": version_number,
            "prophecy_data": prophecy_data,
            "changes": changes,
            "author": "Claude Elder",
            "timestamp": datetime.now().isoformat(),
            "hash": self.calculate_hash(prophecy_data),
            "parent_version": self.get_latest_version(prophecy_name),
        }

        self.version_history[prophecy_name].append(version_info)

        logger.info(f"📋 新バージョン作成: {prophecy_name} v{version_number}")
        return version_number

    def create_branch(
        self, prophecy_name: str, branch_name: str, from_version: str = None
    ) -> str:
        """ブランチ作成"""
        if prophecy_name not in self.branches:
            self.branches[prophecy_name] = {}

        base_version = from_version or self.get_latest_version(prophecy_name)
        base_data = self.get_version_data(prophecy_name, base_version)

        branch_id = (
            f"{prophecy_name}_{branch_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        self.branches[prophecy_name][branch_name] = {
            "branch_id": branch_id,
            "base_version": base_version,
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }

        logger.info(f"🌿 ブランチ作成: {prophecy_name}/{branch_name}")
        return branch_id

    def merge_branch(
        self, prophecy_name: str, branch_name: str, target_branch: str = "main"
    ) -> bool:
        """ブランチマージ"""
        if self.has_conflicts(prophecy_name, branch_name, target_branch):
            logger.warning(f"⚠️ マージ競合検出: {prophecy_name}/{branch_name}")
            return False

        # マージ実行
        merge_data = self.prepare_merge_data(prophecy_name, branch_name, target_branch)
        self.create_version(
            prophecy_name, merge_data, {"type": "merge", "source": branch_name}
        )

        logger.info(
            f"🔄 ブランチマージ完了: {prophecy_name}/{branch_name} → {target_branch}"
        )
        return True

    def rollback_version(self, prophecy_name: str, target_version: str) -> bool:
        """バージョンロールバック"""
        if not self.version_exists(prophecy_name, target_version):
            logger.error(
                f"❌ バージョンが存在しません: {prophecy_name} v{target_version}"
            )
            return False

        # 安全性チェック
        if not self.is_safe_to_rollback(prophecy_name, target_version):
            logger.error(
                f"⚠️ ロールバックは安全ではありません: {prophecy_name} v{target_version}"
            )
            return False

        # ロールバック実行
        target_data = self.get_version_data(prophecy_name, target_version)
        self.create_version(
            prophecy_name,
            target_data,
            {
                "type": "rollback",
                "target_version": target_version,
                "reason": "manual_rollback",
            },
        )

        logger.info(
            f"🔙 バージョンロールバック完了: {prophecy_name} → v{target_version}"
        )
        return True

    def calculate_hash(self, data: Dict) -> str:
        """データハッシュ計算"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]

    def generate_version_number(self, prophecy_name: str) -> str:
        """バージョン番号生成"""
        history = self.version_history.get(prophecy_name, [])
        if not history:
            return "1.0.0"

        latest_version = history[-1]["version"]
        parts = latest_version.split(".")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        # マイナーバージョンアップ
        return f"{major}.{minor + 1}0.0"

    def get_latest_version(self, prophecy_name: str) -> str:
        """最新バージョン取得"""
        history = self.version_history.get(prophecy_name, [])
        return history[-1]["version"] if history else "1.0.0"

    def get_version_data(self, prophecy_name: str, version: str) -> Dict:
        """バージョンデータ取得"""
        history = self.version_history.get(prophecy_name, [])
        for version_info in history:
            if version_info["version"] == version:
                return version_info["prophecy_data"]
        return {}

    def version_exists(self, prophecy_name: str, version: str) -> bool:
        """バージョン存在確認"""
        history = self.version_history.get(prophecy_name, [])
        return any(v["version"] == version for v in history)

    def is_safe_to_rollback(self, prophecy_name: str, target_version: str) -> bool:
        """ロールバック安全性チェック"""
        # 実際の実装では、依存関係、実行中のタスク、データ整合性などをチェック
        return True

    def has_conflicts(
        self, prophecy_name: str, branch_name: str, target_branch: str
    ) -> bool:
        """マージ競合チェック"""
        # 実際の実装では、変更箇所の重複をチェック
        return False

    def prepare_merge_data(
        self, prophecy_name: str, branch_name: str, target_branch: str
    ) -> Dict:
        """マージデータ準備"""
        # 実際の実装では、ブランチの変更をマージ
        return {}

class ProphecyRiskAssessment:
    """予言書リスク評価"""

    def __init__(self):
        """初期化メソッド"""
        self.risk_factors = {
            "impact_scope": 0.3,
            "rollback_difficulty": 0.2,
            "stability_confidence": 0.2,
            "dependency_risk": 0.2,
            "novelty_risk": 0.1,
        }

    def assess_prophecy_risk(self, prophecy_data: Dict) -> Dict:
        """予言書リスク評価"""
        risk_scores = {}

        # 各リスク要因の評価
        risk_scores["impact_scope"] = self.assess_impact_scope(prophecy_data)
        risk_scores["rollback_difficulty"] = self.assess_rollback_difficulty(
            prophecy_data
        )
        risk_scores["stability_confidence"] = self.assess_stability_confidence(
            prophecy_data
        )
        risk_scores["dependency_risk"] = self.assess_dependency_risk(prophecy_data)
        risk_scores["novelty_risk"] = self.assess_novelty_risk(prophecy_data)

        # 総合リスクスコア計算
        overall_risk = sum(
            risk_scores[factor] * weight for factor, weight in self.risk_factors.items()
        )

        risk_level = self.determine_risk_level(overall_risk)

        return {
            "overall_risk": overall_risk,
            "risk_level": risk_level,
            "risk_scores": risk_scores,
            "mitigation_strategies": self.generate_mitigation_strategies(risk_scores),
            "approval_required": risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
        }

    def assess_impact_scope(self, prophecy_data: Dict) -> float:
        """影響範囲評価"""
        # 実際の実装では、影響するシステム・コンポーネントを分析
        phases = prophecy_data.get("phases", [])
        return min(len(phases) * 0.2, 1.0)

    def assess_rollback_difficulty(self, prophecy_data: Dict) -> float:
        """ロールバック難易度評価"""
        # 実際の実装では、進化アクションの可逆性を評価
        return 0.3  # 中程度の難易度

    def assess_stability_confidence(self, prophecy_data: Dict) -> float:
        """安定性信頼度評価"""
        # 実際の実装では、過去の類似ケースの成功率を分析
        return 0.2  # 高い信頼度

    def assess_dependency_risk(self, prophecy_data: Dict) -> float:
        """依存関係リスク評価"""
        # 実際の実装では、他システムとの依存関係を分析
        return 0.1  # 低い依存関係リスク

    def assess_novelty_risk(self, prophecy_data: Dict) -> float:
        """新規性リスク評価"""
        # 実際の実装では、新しい技術・手法の使用度を評価
        return 0.2  # 中程度の新規性

    def determine_risk_level(self, risk_score: float) -> RiskLevel:
        """リスクレベル判定"""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def generate_mitigation_strategies(self, risk_scores: Dict) -> List[str]:
        """リスク軽減戦略生成"""
        strategies = []

        if risk_scores["impact_scope"] > 0.5:
            strategies.append("段階的展開による影響範囲の制限")

        if risk_scores["rollback_difficulty"] > 0.5:
            strategies.append("詳細なロールバック手順の策定")

        if risk_scores["stability_confidence"] > 0.5:
            strategies.append("追加の安定性テスト実施")

        if risk_scores["dependency_risk"] > 0.5:
            strategies.append("依存関係の事前検証")

        if risk_scores["novelty_risk"] > 0.5:
            strategies.append("プロトタイプによる事前検証")

        return strategies

class ProphecyQualityAssurance:
    """予言書品質保証"""

    def __init__(self):
        """初期化メソッド"""
        self.quality_criteria = {
            "completeness": 0.25,
            "consistency": 0.25,
            "feasibility": 0.25,
            "maintainability": 0.25,
        }

    def validate_prophecy_quality(self, prophecy_data: Dict) -> Dict:
        """予言書品質検証"""
        quality_scores = {}

        # 各品質基準の評価
        quality_scores["completeness"] = self.check_completeness(prophecy_data)
        quality_scores["consistency"] = self.check_consistency(prophecy_data)
        quality_scores["feasibility"] = self.check_feasibility(prophecy_data)
        quality_scores["maintainability"] = self.check_maintainability(prophecy_data)

        # 総合品質スコア計算
        overall_quality = sum(
            quality_scores[criterion] * weight
            for criterion, weight in self.quality_criteria.items()
        )

        return {
            "overall_quality": overall_quality,
            "quality_scores": quality_scores,
            "passed": overall_quality >= 0.7,
            "recommendations": self.generate_quality_recommendations(quality_scores),
        }

    def check_completeness(self, prophecy_data: Dict) -> float:
        """完全性チェック"""
        required_fields = ["prophecy_name", "description", "phases"]
        present_fields = sum(1 for field in required_fields if field in prophecy_data)
        return present_fields / len(required_fields)

    def check_consistency(self, prophecy_data: Dict) -> float:
        """一貫性チェック"""
        # 実際の実装では、フェーズ間の一貫性、命名の一貫性などをチェック
        return 0.8  # 高い一貫性

    def check_feasibility(self, prophecy_data: Dict) -> float:
        """実現可能性チェック"""
        # 実際の実装では、技術的実現可能性、リソース要件などをチェック
        return 0.7  # 実現可能

    def check_maintainability(self, prophecy_data: Dict) -> float:
        """保守性チェック"""
        # 実際の実装では、複雑度、文書化レベル、拡張性などをチェック
        return 0.8  # 高い保守性

    def generate_quality_recommendations(self, quality_scores: Dict) -> List[str]:
        """品質改善推奨事項生成"""
        recommendations = []

        if quality_scores["completeness"] < 0.7:
            recommendations.append("必須フィールドの追加")

        if quality_scores["consistency"] < 0.7:
            recommendations.append("命名規則の統一")

        if quality_scores["feasibility"] < 0.7:
            recommendations.append("実現可能性の再検討")

        if quality_scores["maintainability"] < 0.7:
            recommendations.append("文書化の改善")

        return recommendations

class ProphecyDependencyAnalyzer:
    """予言書依存関係分析"""

    def __init__(self):
        """初期化メソッド"""
        self.dependency_graph = {}

    def analyze_dependencies(self, prophecy_name: str, prophecy_data: Dict) -> Dict:
        """依存関係分析"""
        dependencies = {
            "prerequisites": [],  # 前提条件
            "dependents": [],  # 依存する予言書
            "conflicts": [],  # 競合する予言書
            "synergies": [],  # 相乗効果
            "impact_analysis": {},  # 影響分析
        }

        # 各種依存関係の分析
        dependencies["prerequisites"] = self.find_prerequisites(prophecy_data)
        dependencies["dependents"] = self.find_dependents(prophecy_name)
        dependencies["conflicts"] = self.find_conflicts(prophecy_data)
        dependencies["synergies"] = self.find_synergies(prophecy_data)
        dependencies["impact_analysis"] = self.analyze_impact(prophecy_name)

        return dependencies

    def find_prerequisites(self, prophecy_data: Dict) -> List[str]:
        """前提条件の特定"""
        # 実際の実装では、予言書の要求事項から前提条件を特定
        return []

    def find_dependents(self, prophecy_name: str) -> List[str]:
        """依存する予言書の特定"""
        # 実際の実装では、他の予言書がこの予言書に依存しているかをチェック
        return []

    def find_conflicts(self, prophecy_data: Dict) -> List[str]:
        """競合する予言書の特定"""
        # 実際の実装では、同じリソースを使用する予言書を特定
        return []

    def find_synergies(self, prophecy_data: Dict) -> List[str]:
        """相乗効果のある予言書の特定"""
        # 実際の実装では、一緒に実行すると効果的な予言書を特定
        return []

    def analyze_impact(self, prophecy_name: str) -> Dict:
        """影響分析"""
        return {
            "affected_systems": [],
            "affected_processes": [],
            "affected_users": [],
            "mitigation_required": False,
        }

class ProphecyGovernanceSystem:
    """予言書ガバナンスシステム"""

    def __init__(self):
        """初期化メソッド"""
        self.approval_workflows = {
            "creation": self.creation_approval_workflow,
            "evolution": self.evolution_approval_workflow,
            "modification": self.modification_approval_workflow,
            "retirement": self.retirement_approval_workflow,
        }

        self.approval_thresholds = {
            RiskLevel.LOW: ApprovalStatus.APPROVED,
            RiskLevel.MEDIUM: "senior_elder_approval",
            RiskLevel.HIGH: "elder_council_approval",
            RiskLevel.CRITICAL: "grand_elder_approval",
        }

    def review_prophecy_creation(self, prophecy_data: Dict, assessments: Dict) -> Dict:
        """予言書作成レビュー"""
        risk_level = assessments["risk_assessment"]["risk_level"]
        quality_passed = assessments["quality_assessment"]["passed"]

        # 基本チェック
        if not quality_passed:
            return {
                "approved": False,
                "status": ApprovalStatus.REJECTED,
                "reason": "Quality standards not met",
                "recommendations": assessments["quality_assessment"]["recommendations"],
            }

        # リスクベースの承認判定
        if risk_level == RiskLevel.LOW:
            return {
                "approved": True,
                "status": ApprovalStatus.APPROVED,
                "reason": "Low risk, automatic approval",
                "conditions": [],
            }

        # 高リスクの場合は評議会承認が必要
        return {
            "approved": False,
            "status": ApprovalStatus.PENDING,
            "reason": f"Requires {self.approval_thresholds[risk_level]} due to {risk_level.value} risk",
            "required_approvals": [self.approval_thresholds[risk_level]],
        }

    def creation_approval_workflow(
        self, prophecy_data: Dict, assessments: Dict
    ) -> Dict:
        """作成承認ワークフロー"""
        return self.review_prophecy_creation(prophecy_data, assessments)

    def evolution_approval_workflow(
        self, prophecy_name: str, evolution_plan: Dict
    ) -> Dict:
        """進化承認ワークフロー"""
        # 実際の実装では、進化計画の詳細な審査を行う
        return {
            "approved": True,
            "status": ApprovalStatus.APPROVED,
            "conditions": ["monitoring_required"],
        }

    def modification_approval_workflow(
        self, prophecy_name: str, modifications: Dict
    ) -> Dict:
        """修正承認ワークフロー"""
        # 実際の実装では、修正内容の影響度を評価する
        return {"approved": True, "status": ApprovalStatus.APPROVED, "conditions": []}

    def retirement_approval_workflow(
        self, prophecy_name: str, retirement_plan: Dict
    ) -> Dict:
        """廃止承認ワークフロー"""
        # 実際の実装では、廃止の影響と計画を評価する
        return {
            "approved": True,
            "status": ApprovalStatus.APPROVED,
            "conditions": ["migration_plan_required"],
        }

class ProphecyManagementSystem:
    """予言書統合管理システム"""

    def __init__(self):
        """初期化メソッド"""
        self.version_control = ProphecyVersionControl()
        self.risk_assessment = ProphecyRiskAssessment()
        self.quality_assurance = ProphecyQualityAssurance()
        self.dependency_analyzer = ProphecyDependencyAnalyzer()
        self.governance_system = ProphecyGovernanceSystem()

        self.managed_prophecies = {}
        self.audit_logs = []

    ) -> Dict:
        """テンプレートから予言書作成"""

        # 1.0 カスタマイズ検証

        if not validation_result["valid"]:
            return {
                "error": "Customization validation failed",
                "details": validation_result,
            }

        # 2.0 予言書生成

        # 3.0 品質・リスク評価
        assessments = self.conduct_comprehensive_assessment(prophecy_data)

        # 4.0 ガバナンス審査
        approval_result = self.governance_system.review_prophecy_creation(
            prophecy_data, assessments
        )

        if approval_result["approved"]:
            # 5.0 予言書登録
            prophecy_name = prophecy_data["prophecy_name"]
            self.managed_prophecies[prophecy_name] = {
                "prophecy_data": prophecy_data,
                "lifecycle_stage": ProphecyLifecycleStage.ACTIVE,
                "assessments": assessments,
                "created_at": datetime.now().isoformat(),
            }

            # 6.0 初期バージョン作成
            self.version_control.create_version(
                prophecy_name, prophecy_data, {"type": "initial_creation"}
            )

            logger.info(f"📜 予言書作成完了: {prophecy_name}")
            return {
                "success": True,
                "prophecy_name": prophecy_name,
                "prophecy_data": prophecy_data,
            }

        return {"error": "Prophecy creation not approved", "details": approval_result}

    def conduct_comprehensive_assessment(self, prophecy_data: Dict) -> Dict:
        """包括的評価実施"""
        assessments = {}

        # 品質評価
        assessments["quality_assessment"] = (
            self.quality_assurance.validate_prophecy_quality(prophecy_data)
        )

        # リスク評価
        assessments["risk_assessment"] = self.risk_assessment.assess_prophecy_risk(
            prophecy_data
        )

        # 依存関係分析
        prophecy_name = prophecy_data.get("prophecy_name", "unknown")
        assessments["dependency_analysis"] = (
            self.dependency_analyzer.analyze_dependencies(prophecy_name, prophecy_data)
        )

        return assessments

        """テンプレート登録"""

    def modify_prophecy(self, prophecy_name: str, modifications: Dict) -> Dict:
        """予言書修正"""
        if prophecy_name not in self.managed_prophecies:
            return {"error": f"Prophecy {prophecy_name} not found"}

        current_data = self.managed_prophecies[prophecy_name]["prophecy_data"]

        # 修正適用
        modified_data = current_data.copy()
        modified_data.update(modifications)

        # 再評価
        assessments = self.conduct_comprehensive_assessment(modified_data)

        # 承認チェック
        approval_result = self.governance_system.modification_approval_workflow(
            prophecy_name, modifications
        )

        if approval_result["approved"]:
            # 新バージョン作成
            self.version_control.create_version(
                prophecy_name,
                modified_data,
                {"type": "modification", "changes": modifications},
            )

            # 管理情報更新
            self.managed_prophecies[prophecy_name]["prophecy_data"] = modified_data
            self.managed_prophecies[prophecy_name]["assessments"] = assessments
            self.managed_prophecies[prophecy_name][
                "updated_at"
            ] = datetime.now().isoformat()

            logger.info(f"🔧 予言書修正完了: {prophecy_name}")
            return {"success": True, "prophecy_name": prophecy_name}

        return {"error": "Modification not approved", "details": approval_result}

    def audit_prophecy(self, prophecy_name: str) -> Dict:
        """予言書監査"""
        if prophecy_name not in self.managed_prophecies:
            return {"error": f"Prophecy {prophecy_name} not found"}

        prophecy_info = self.managed_prophecies[prophecy_name]

        audit_result = {
            "prophecy_name": prophecy_name,
            "audit_timestamp": datetime.now().isoformat(),
            "lifecycle_stage": prophecy_info["lifecycle_stage"].value,
            "current_assessments": prophecy_info["assessments"],
            "version_history": self.version_control.version_history.get(
                prophecy_name, []
            ),
            "compliance_status": "compliant",  # 実際の実装では詳細なコンプライアンスチェック
            "recommendations": [],
        }

        # 監査ログ記録
        self.audit_logs.append(audit_result)

        logger.info(f"📊 予言書監査完了: {prophecy_name}")
        return audit_result

    def get_prophecy_status(self, prophecy_name: str) -> Dict:
        """予言書状況取得"""
        if prophecy_name not in self.managed_prophecies:
            return {"error": f"Prophecy {prophecy_name} not found"}

        prophecy_info = self.managed_prophecies[prophecy_name]

        return {
            "prophecy_name": prophecy_name,
            "lifecycle_stage": prophecy_info["lifecycle_stage"].value,
            "prophecy_data": prophecy_info["prophecy_data"],
            "assessments": prophecy_info["assessments"],
            "latest_version": self.version_control.get_latest_version(prophecy_name),
            "created_at": prophecy_info.get("created_at"),
            "updated_at": prophecy_info.get("updated_at"),
        }

    def list_managed_prophecies(self) -> List[Dict]:
        """管理予言書一覧"""
        prophecy_list = []

        for prophecy_name, prophecy_info in self.managed_prophecies.items():
            prophecy_list.append(
                {
                    "prophecy_name": prophecy_name,
                    "lifecycle_stage": prophecy_info["lifecycle_stage"].value,
                    "latest_version": self.version_control.get_latest_version(
                        prophecy_name
                    ),
                    "risk_level": prophecy_info["assessments"]["risk_assessment"][
                        "risk_level"
                    ].value,
                    "quality_score": prophecy_info["assessments"]["quality_assessment"][
                        "overall_quality"
                    ],
                    "created_at": prophecy_info.get("created_at"),
                    "updated_at": prophecy_info.get("updated_at"),
                }
            )

        return prophecy_list

# 使用例
async def main():
    """テスト用メイン関数"""
    # 管理システム初期化
    pms = ProphecyManagementSystem()

    # テンプレート作成

        name="品質進化テンプレート",
        description="品質を段階的に進化させるためのテンプレート",
    )

        "prophecy_name": "quality_evolution",
        "description": "品質を段階的に自動進化させる予言書",
        "category": "quality",
        "phases": [],
    }

        "prophecy_name",
        "description",
        "target_system",
    ]

    # テンプレート登録

    # 予言書作成
    customizations = {
        "prophecy_name": "test_quality_evolution",
        "description": "テスト用品質進化予言書",
        "target_system": "test_system",
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 予言書一覧表示
    prophecy_list = pms.list_managed_prophecies()
    print(json.dumps(prophecy_list, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
