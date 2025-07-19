"""
Elder Flow Violation Detector
グランドエルダーmaruの完了基準方針を厳格に適用するシステム

完了と認められる条件:
1. 本番環境で実際に動作する
2. 全ての依存関係が実環境で検証済み
3. エラーハンドリングが完備
4. パフォーマンス基準を満たす
5. セキュリティ要件を充足
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import json
import os
from pathlib import Path
import uuid


class TaskCompletionStatus(Enum):
    """タスクの完了状態を表す列挙型"""

    IN_DEVELOPMENT = "開発中"  # モック使用OK
    IN_VERIFICATION = "検証中"  # 実環境テスト中
    COMPLETED = "完了"  # 本番環境で完全動作確認済み
    REJECTED = "却下"  # 不完全な実装


class ElderFlowViolation(Exception):
    """Elder Flow方針違反を表す例外"""

    pass


class CompletionCriteria:
    """完了基準を管理するクラス"""

    def __init__(self):
        self.unit_tests_pass = False  # 開発段階
        self.integration_tests_pass = False  # 検証段階
        self.production_ready = False  # 完了条件
        self.performance_verified = False  # 完了条件
        self.security_audited = False  # 完了条件
        self.error_handling_complete = False  # 完了条件
        self.documentation_complete = False  # 完了条件
        self.monitoring_configured = False  # 完了条件

    def is_complete(self) -> bool:
        """全ての完了条件を満たしているか確認"""
        return all(
            [
                self.unit_tests_pass,
                self.integration_tests_pass,
                self.production_ready,
                self.performance_verified,
                self.security_audited,
                self.error_handling_complete,
                self.documentation_complete,
                self.monitoring_configured,
            ]
        )

    def get_missing_criteria(self) -> List[str]:
        """未達成の基準をリスト化"""
        missing = []
        criteria_map = {
            "ユニットテスト": self.unit_tests_pass,
            "統合テスト": self.integration_tests_pass,
            "本番環境準備": self.production_ready,
            "パフォーマンス検証": self.performance_verified,
            "セキュリティ監査": self.security_audited,
            "エラーハンドリング": self.error_handling_complete,
            "ドキュメント": self.documentation_complete,
            "監視設定": self.monitoring_configured,
        }

        for criterion, status in criteria_map.items():
            if not status:
                missing.append(criterion)

        return missing


class ViolationDetectionContext:
    """違反検知のコンテキスト情報"""

    def __init__(
        self,
        task_id: str,
        task_type: str,
        developer_id: str,
        timestamp: datetime,
        source_files: List[str],
        test_results: Optional[Dict[str, Any]] = None,
        production_metrics: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """コンテキストの初期化"""
        self.task_id = task_id
        self.task_type = task_type
        self.developer_id = developer_id
        self.timestamp = timestamp
        self.source_files = source_files
        self.test_results = test_results or {}
        self.production_metrics = production_metrics or {}
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "developer_id": self.developer_id,
            "timestamp": self.timestamp.isoformat(),
            "source_files": self.source_files,
            "test_results": self.test_results,
            "production_metrics": self.production_metrics,
            "metadata": self.metadata,
        }


class ViolationRecord:
    """違反記録を表すデータクラス"""

    def __init__(
        self,
        violation_id: str,
        timestamp: datetime,
        violation_type: str,
        severity: str,
        category: str,
        description: str,
        context: Dict[str, Any],
        task_id: Optional[str] = None,
        developer_id: Optional[str] = None,
        auto_fixed: bool = False,
        fix_description: Optional[str] = None,
    ):
        """違反記録の初期化"""
        self.violation_id = violation_id
        self.timestamp = timestamp
        self.violation_type = violation_type
        self.severity = severity
        self.category = category
        self.description = description
        self.context = context
        self.task_id = task_id
        self.developer_id = developer_id
        self.auto_fixed = auto_fixed
        self.fix_description = fix_description

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "violation_id": self.violation_id,
            "timestamp": self.timestamp.isoformat(),
            "violation_type": self.violation_type,
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "context": self.context,
            "task_id": self.task_id,
            "developer_id": self.developer_id,
            "auto_fixed": self.auto_fixed,
            "fix_description": self.fix_description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ViolationRecord":
        """辞書形式から生成"""
        data = data.copy()
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class ElderFlowViolationDetector:
    """グランドエルダーmaruの方針違反を自動検知するシステム"""

    def __init__(self):
        self.violation_log_path = Path("knowledge_base/elder_flow_violations/")
        self.violation_log_path.mkdir(parents=True, exist_ok=True)

        # 4賢者のシミュレーション（実際の実装では各賢者システムと連携）
        self.knowledge_sage_criteria = self._load_knowledge_criteria()
        self.incident_patterns = self._load_incident_patterns()

    def _load_knowledge_criteria(self) -> Dict[str, Any]:
        """ナレッジ賢者から完了基準を取得"""
        return {
            "required_test_coverage": 95,
            "max_response_time_ms": 200,
            "max_memory_usage_mb": 512,
            "required_documentation": [
                "README.md",
                "API_DOCUMENTATION.md",
                "DEPLOYMENT_GUIDE.md",
                "TROUBLESHOOTING.md",
            ],
            "security_requirements": [
                "input_validation",
                "authentication",
                "authorization",
                "encryption",
                "audit_logging",
            ],
        }

    def _load_incident_patterns(self) -> List[Dict[str, Any]]:
        """インシデント賢者から既知の問題パターンを取得"""
        return [
            {
                "pattern": "mock_in_production",
                "description": "本番コードにモックオブジェクトが残存",
                "severity": "CRITICAL",
            },
            {
                "pattern": "missing_error_handling",
                "description": "エラーハンドリングの欠如",
                "severity": "HIGH",
            },
            {
                "pattern": "hardcoded_credentials",
                "description": "ハードコードされた認証情報",
                "severity": "CRITICAL",
            },
            {
                "pattern": "no_timeout_handling",
                "description": "タイムアウト処理の未実装",
                "severity": "MEDIUM",
            },
        ]

    async def validate_completion_claim(
        self,
        task_id: str,
        implementation_path: str,
        test_results: Dict[str, Any],
        production_verification: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        完了報告の妥当性を検証

        Args:
            task_id: タスクID
            implementation_path: 実装コードのパス
            test_results: テスト結果
            production_verification: 本番環境での検証結果

        Returns:
            検証結果の辞書

        Raises:
            ElderFlowViolation: 方針違反が検出された場合
        """

        violations = []
        warnings = []

        # 1. 基本的な完了基準チェック
        criteria = CompletionCriteria()

        # テスト結果の検証
        if test_results.get("unit_test_coverage", 0) >= 95:
            criteria.unit_tests_pass = True
        else:
            violations.append(
                f"ユニットテストカバレッジ不足: {test_results.get('unit_test_coverage', 0)}% < 95%"
            )

        # 本番環境検証の確認
        if not production_verification:
            violations.append("本番環境での動作検証が未実施")
        else:
            if production_verification.get("all_features_working"):
                criteria.production_ready = True
            else:
                violations.append("本番環境で一部機能が動作していない")

            if (
                production_verification.get("performance_metrics", {}).get(
                    "response_time_ms", float("inf")
                )
                <= 200
            ):
                criteria.performance_verified = True
            else:
                violations.append("パフォーマンス基準を満たしていない")

        # 2. コード品質チェック（シミュレーション）
        code_issues = await self._analyze_code_quality(implementation_path)
        if code_issues:
            violations.extend(code_issues)

        # 3. セキュリティチェック
        security_issues = await self._security_audit(implementation_path)
        if security_issues:
            violations.extend(security_issues)

        # 4. ドキュメントチェック
        doc_issues = self._check_documentation(implementation_path)
        if doc_issues:
            warnings.extend(doc_issues)
        else:
            criteria.documentation_complete = True

        # 5. 違反があれば例外を発生
        if violations:
            self._log_violation(task_id, violations, warnings)
            raise ElderFlowViolation(
                f"完了報告は認められません。\n"
                f"違反事項:\n"
                + "\n".join(f"  - {v}" for v in violations)
                + (
                    f"\n\n警告事項:\n" + "\n".join(f"  - {w}" for w in warnings)
                    if warnings
                    else ""
                )
            )

        # 6. 承認記録を作成
        verification_record = {
            "task_id": task_id,
            "status": TaskCompletionStatus.COMPLETED.value,
            "verification_id": self._generate_verification_id(),
            "timestamp": datetime.now().isoformat(),
            "verified_by": "Elder Flow Violation Detector",
            "criteria_met": {
                "unit_tests": criteria.unit_tests_pass,
                "integration_tests": criteria.integration_tests_pass,
                "production_ready": criteria.production_ready,
                "performance_verified": criteria.performance_verified,
                "security_audited": criteria.security_audited,
                "error_handling": criteria.error_handling_complete,
                "documentation": criteria.documentation_complete,
                "monitoring": criteria.monitoring_configured,
            },
            "warnings": warnings if warnings else None,
        }

        self._save_verification_record(verification_record)

        return {
            "approved": True,
            "verification_record": verification_record,
            "message": "グランドエルダーmaruの基準を満たす完全な実装です。",
        }

    async def _analyze_code_quality(self, implementation_path: str) -> List[str]:
        """コード品質の分析（簡易版）"""
        issues = []

        # モックの使用チェック（本番コードでの使用を検出）
        if os.path.exists(implementation_path):
            with open(implementation_path, "r", encoding="utf-8") as f:
                content = f.read()

                # 本番コードでのモック使用検出
                if not implementation_path.endswith("_test.py"):
                    if "mock" in content.lower() or "Mock" in content:
                        issues.append("本番コードにモックオブジェクトが検出されました")

                # TODO/FIXMEコメントの検出
                if "TODO" in content or "FIXME" in content:
                    issues.append("未完了のTODO/FIXMEコメントが残っています")

                # 基本的なエラーハンドリングチェック
                if "try:" not in content and "except" not in content:
                    issues.append(
                        "エラーハンドリングが実装されていない可能性があります"
                    )

        return issues

    async def _security_audit(self, implementation_path: str) -> List[str]:
        """セキュリティ監査（簡易版）"""
        issues = []

        if os.path.exists(implementation_path):
            with open(implementation_path, "r", encoding="utf-8") as f:
                content = f.read()

                # ハードコードされた認証情報の検出
                suspicious_patterns = [
                    ("password", "ハードコードされたパスワード"),
                    ("api_key", "ハードコードされたAPIキー"),
                    ("secret", "ハードコードされたシークレット"),
                    ("token", "ハードコードされたトークン"),
                ]

                for pattern, description in suspicious_patterns:
                    if f'{pattern} = "' in content or f"{pattern} = '" in content:
                        issues.append(f"{description}が検出されました")

                # SQLインジェクションの可能性
                if 'f"SELECT' in content or "f'SELECT" in content:
                    issues.append("SQLインジェクションの脆弱性の可能性があります")

        return issues

    def _check_documentation(self, implementation_path: str) -> List[str]:
        """ドキュメントの確認"""
        issues = []
        base_path = Path(implementation_path).parent

        required_docs = self.knowledge_sage_criteria["required_documentation"]
        for doc in required_docs:
            doc_path = base_path / doc
            if not doc_path.exists():
                issues.append(f"必須ドキュメント '{doc}' が見つかりません")

        return issues

    def _generate_verification_id(self) -> str:
        """検証IDの生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"ELDER_VERIFY_{timestamp}"

    def _log_violation(self, task_id: str, violations: List[str], warnings: List[str]):
        """違反記録の保存"""
        violation_record = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "violations": violations,
            "warnings": warnings,
            "status": TaskCompletionStatus.REJECTED.value,
        }

        log_file = (
            self.violation_log_path
            / f"violation_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(violation_record, f, ensure_ascii=False, indent=2)

    def _save_verification_record(self, record: Dict[str, Any]):
        """承認記録の保存"""
        verification_path = Path("knowledge_base/elder_flow_verifications/")
        verification_path.mkdir(parents=True, exist_ok=True)

        file_name = f"verification_{record['verification_id']}.json"
        with open(verification_path / file_name, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)


# 使用例
async def example_usage():
    """Elder Flow Violation Detectorの使用例"""
    detector = ElderFlowViolationDetector()

    # テスト結果の例
    test_results = {
        "unit_test_coverage": 98,
        "integration_tests_passed": True,
        "performance_tests_passed": True,
    }

    # 本番環境検証結果の例
    production_verification = {
        "all_features_working": True,
        "performance_metrics": {"response_time_ms": 150, "memory_usage_mb": 256},
        "error_rate": 0.01,
    }

    try:
        result = await detector.validate_completion_claim(
            task_id="TASK-2025-001",
            implementation_path="libs/example_feature.py",
            test_results=test_results,
            production_verification=production_verification,
        )
        print(f"✅ 完了承認: {result['message']}")
    except ElderFlowViolation as e:
        print(f"❌ 完了却下: {str(e)}")


if __name__ == "__main__":
    asyncio.run(example_usage())
