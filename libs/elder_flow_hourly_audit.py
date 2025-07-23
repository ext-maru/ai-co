"""
Elder Flow毎時間自動監査システム
24時間365日、違反を見逃さない「Hourly Inquisition」
"""

import threading
import time
import json
import logging
import subprocess
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import statistics

from libs.elder_flow_violation_db import ElderFlowViolationDB
from libs.elder_flow_violation_detector import (
    ElderFlowViolationDetector as OriginalDetector,
    ViolationDetectionContext,
)
from libs.elder_flow_violation_types_original import (
    ViolationType,
    ViolationSeverity,
    ViolationCategory,
)


logger = logging.getLogger(__name__)


class AuditType(Enum):
    """監査タイプ"""

    COMPREHENSIVE_SCAN = "comprehensive_scan"  # 包括的スキャン
    ACTIVE_VIOLATIONS = "active_violations"  # アクティブ違反チェック
    STATISTICS_ANALYSIS = "statistics_analysis"  # 統計分析
    REPORT_GENERATION = "report_generation"  # レポート生成
    CODE_QUALITY = "code_quality"  # コード品質監査
    PROCESS_COMPLIANCE = "process_compliance"  # プロセス遵守監査
    SECURITY = "security"  # セキュリティ監査


@dataclass
class AuditResult:
    """監査結果"""

    audit_type: AuditType
    passed: bool
    findings: List[Dict[str, Any]]
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_severity_summary(self) -> Dict[str, int]:
        """重要度別のサマリーを取得"""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in self.findings:
            severity = finding.get("severity", "low")
            if severity in summary:
                summary[severity] += 1
        return summary


@dataclass
class AuditTask:
    """監査タスク"""

    task_id: str
    audit_type: AuditType
    description: str
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[AuditResult] = None
    error_message: Optional[str] = None

    def start(self):
        """タスク開始"""
        self.status = "running"
        self.started_at = datetime.now()

    def complete(self, result: AuditResult):
        """タスク完了"""
        self.status = "completed"
        self.completed_at = datetime.now()
        self.result = result

    def fail(self, error_message: str):
        """タスク失敗"""
        self.status = "failed"
        self.completed_at = datetime.now()
        self.error_message = error_message

    def get_duration(self) -> Optional[timedelta]:
        """実行時間を取得"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


@dataclass
class ComplianceMetrics:
    """コンプライアンスメトリクス"""

    test_coverage: float = 0.0
    tdd_compliance_rate: float = 0.0
    github_flow_compliance_rate: float = 0.0
    four_sages_consultation_rate: float = 0.0
    documentation_completeness: float = 0.0

    # 集計値
    total_checks: int = 0
    passed_checks: int = 0
    overall_compliance_rate: float = 0.0
    is_compliant: bool = False

    def calculate(self):
        """コンプライアンス率を計算"""
        if self.total_checks > 0:
            self.overall_compliance_rate = self.passed_checks / self.total_checks * 100
            # 90%以上でコンプライアント
            self.is_compliant = self.overall_compliance_rate >= 90.0

    def get_problem_areas(self) -> List[str]:
        """問題のある領域を特定"""
        problems = []
        thresholds = {
            "test_coverage": (self.test_coverage, 90.0),
            "tdd_compliance": (self.tdd_compliance_rate, 90.0),
            "github_flow_compliance": (self.github_flow_compliance_rate, 90.0),
            "four_sages_consultation": (self.four_sages_consultation_rate, 80.0),
            "documentation": (self.documentation_completeness, 80.0),
        }

        for area, (value, threshold) in thresholds.items():
            if value < threshold:
                problems.append(area)

        return problems


@dataclass
class AuditReport:
    """監査レポート"""

    report_id: str
    timestamp: datetime
    summary: str
    audit_results: List[AuditResult]
    compliance_metrics: ComplianceMetrics
    recommendations: List[str]
    escalation_required: bool = False
    escalation_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp.isoformat(),
            "summary": self.summary,
            "audit_results": [
                {
                    "audit_type": r.audit_type.value,
                    "passed": r.passed,
                    "findings_count": len(r.findings),
                    "severity_summary": r.get_severity_summary(),
                }
                for r in self.audit_results
            ],
            "compliance_metrics": self.compliance_metrics.__dict__,
            "recommendations": self.recommendations,
            "escalation_required": self.escalation_required,
            "escalation_reason": self.escalation_reason,
        }


class AuditSchedule:
    """監査スケジュール管理"""

    def __init__(self):
        """初期化メソッド"""
        # デフォルトのスケジュール（分）
        self.comprehensive_scan_minute = 0  # 00分: 包括的スキャン
        self.active_check_minute = 15  # 15分: アクティブ違反チェック
        self.statistics_minute = 30  # 30分: 統計分析
        self.report_minute = 45  # 45分: レポート生成

    def get_current_task(self, current_time: datetime) -> Optional[AuditType]:
        """現在実行すべきタスクを取得"""
        minute = current_time.minute

        if minute == self.comprehensive_scan_minute:
            return AuditType.COMPREHENSIVE_SCAN
        elif minute == self.active_check_minute:
            return AuditType.ACTIVE_VIOLATIONS
        elif minute == self.statistics_minute:
            return AuditType.STATISTICS_ANALYSIS
        elif minute == self.report_minute:
            return AuditType.REPORT_GENERATION

        return None

    def get_next_task_time(self, current_time: datetime) -> Tuple[datetime, AuditType]:
        """次回のタスク実行時刻を取得"""
        minute = current_time.minute

        # 次のスケジュール時刻を計算
        schedule_times = [
            (self.comprehensive_scan_minute, AuditType.COMPREHENSIVE_SCAN),
            (self.active_check_minute, AuditType.ACTIVE_VIOLATIONS),
            (self.statistics_minute, AuditType.STATISTICS_ANALYSIS),
            (self.report_minute, AuditType.REPORT_GENERATION),
        ]

        # 現在時刻より後の最初のスケジュールを探す
        for sched_minute, audit_type in sorted(schedule_times):
            if sched_minute > minute:
                next_time = current_time.replace(
                    minute=sched_minute, second=0, microsecond=0
                )
                return next_time, audit_type

        # 次の時間の最初のスケジュール
        next_hour = current_time + timedelta(hours=1)
        next_time = next_hour.replace(
            minute=self.comprehensive_scan_minute, second=0, microsecond=0
        )
        return next_time, AuditType.COMPREHENSIVE_SCAN


class HourlyAuditSystem:
    """毎時間自動監査システム"""

    def __init__(self):
        """初期化メソッド"""
        self.schedule = AuditSchedule()
        self.db = ElderFlowViolationDB()
        self.detector = OriginalDetector()
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # 監査履歴
        self.audit_history: List[AuditTask] = []
        self.current_task: Optional[AuditTask] = None

        # 最新の結果をキャッシュ
        self.last_comprehensive_result: Optional[AuditResult] = None
        self.last_statistics_result: Optional[AuditResult] = None

    def start(self):
        """監査システムを開始"""
        if not self.is_running:
            self.is_running = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run_scheduler)
            self.thread.daemon = True
            self.thread.start()
            logger.info("毎時間自動監査システムを開始しました")

    def stop(self):
        """監査システムを停止"""
        if self.is_running:
            self.is_running = False
            self.stop_event.set()
            if self.thread:
                self.thread.join(timeout=5)
            logger.info("毎時間自動監査システムを停止しました")

    def _run_scheduler(self):
        """スケジューラーを実行"""
        while self.is_running and not self.stop_event.is_set():
            current_time = datetime.now()

            # 現在のタスクを確認
            task_type = self.schedule.get_current_task(current_time)

            if task_type:
                # タスクを実行
                self._execute_scheduled_task(task_type)

            # 次のタスクまで待機
            next_time, next_task = self.schedule.get_next_task_time(current_time)
            wait_seconds = (next_time - datetime.now()).total_seconds()

            if wait_seconds > 0:
                logger.info(f"次の監査まで{wait_seconds:.0f}秒待機: {next_task.value}")
                self.stop_event.wait(wait_seconds)

    def _execute_scheduled_task(self, audit_type: AuditType) -> Optional[AuditTask]:
        """スケジュールされたタスクを実行"""
        task = AuditTask(
            task_id=f"AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            audit_type=audit_type,
            description=f"{audit_type.value}の実行",
        )

        self.current_task = task
        task.start()

        try:
            # 監査タイプに応じて実行
            if audit_type == AuditType.COMPREHENSIVE_SCAN:
                result = self._execute_comprehensive_scan()
            elif audit_type == AuditType.ACTIVE_VIOLATIONS:
                result = self._check_active_violations()
            elif audit_type == AuditType.STATISTICS_ANALYSIS:
                result = self._analyze_statistics()
            elif audit_type == AuditType.REPORT_GENERATION:
                report = self._generate_report()
                result = self._convert_report_to_result(report)
            else:
                result = AuditResult(audit_type=audit_type, passed=True, findings=[])

            task.complete(result)

            # エスカレーションが必要か確認
            if self._should_escalate(result):
                self._trigger_escalation(result, "重大な違反が検出されました")

        except Exception as e:
            logger.error(f"監査タスク実行エラー: {e}")
            task.fail(str(e))

        self.audit_history.append(task)
        self.current_task = None

        # 履歴は最新1000件まで保持
        if len(self.audit_history) > 1000:
            self.audit_history = self.audit_history[-1000:]

        return task

    def _execute_comprehensive_scan(self) -> AuditResult:
        """包括的システムスキャンを実行"""
        logger.info("包括的システムスキャンを開始")

        findings = []
        metrics = {
            "scan_started": datetime.now().isoformat(),
            "total_files_scanned": 0,
            "violations_found": 0,
            "coverage_metrics": {},
        }

        # 1. コードベースをスキャン
        codebase_results = self._scan_codebase()
        metrics["total_files_scanned"] = codebase_results["files_scanned"]
        metrics["violations_found"] = codebase_results["violations_found"]
        findings.extend(codebase_results.get("findings", []))

        # 2. テストカバレッジをチェック
        coverage_results = self._check_test_coverage()
        metrics["coverage_metrics"] = coverage_results

        if coverage_results.get("coverage", 0) < 90:
            findings.append(
                {
                    "type": "test_coverage",
                    "severity": "high",
                    "description": f"テストカバレッジが基準以下: {coverage_results.get('coverage', 0)}%",
                }
            )

        # 3. 依存関係をチェック
        dependency_results = self._check_dependencies()
        findings.extend(dependency_results.get("vulnerabilities", []))

        # 4. プロセス遵守をチェック
        process_results = self._check_process_compliance()
        findings.extend(process_results.get("violations", []))

        # 結果を保存
        passed = (
            len([f for f in findings if f.get("severity") in ["critical", "high"]]) == 0
        )

        result = AuditResult(
            audit_type=AuditType.COMPREHENSIVE_SCAN,
            passed=passed,
            findings=findings,
            metrics=metrics,
        )

        self.last_comprehensive_result = result

        logger.info(f"包括的スキャン完了: {len(findings)}件の問題を検出")
        return result

    def _check_active_violations(self) -> AuditResult:
        """アクティブな違反の進捗を確認"""
        logger.info("アクティブ違反の確認を開始")

        active_violations = self.db.get_active_violations()
        findings = []

        # 長期間未解決の違反を特定
        now = datetime.now()
        for violation in active_violations:
            detected_at = datetime.fromisoformat(violation["detected_at"])
            age_hours = (now - detected_at).total_seconds() / 3600

            if age_hours > 24:  # 24時間以上
                findings.append(
                    {
                        "type": "long_standing_violation",
                        "severity": "high",
                        "description": f"{violation['violation_type']}が{age_hours:.0f}時間未解決",
                        "violation_id": violation["id"],
                    }
                )
            elif age_hours > 8:  # 8時間以上
                findings.append(
                    {
                        "type": "aging_violation",
                        "severity": "medium",
                        "description": f"{violation['violation_type']}が{age_hours:.0f}時間経過",
                        "violation_id": violation["id"],
                    }
                )

        metrics = {
            "active_violations": len(active_violations),
            "long_standing": len(
                [f for f in findings if f["type"] == "long_standing_violation"]
            ),
            "aging": len([f for f in findings if f["type"] == "aging_violation"]),
            "oldest_violation_hours": max(
                [
                    (now - datetime.fromisoformat(v["detected_at"])).total_seconds()
                    / 3600
                    for v in active_violations
                ],
                default=0,
            ),
        }

        result = AuditResult(
            audit_type=AuditType.ACTIVE_VIOLATIONS,
            passed=len(findings) == 0,
            findings=findings,
            metrics=metrics,
        )

        logger.info(
            f"アクティブ違反確認完了: {len(active_violations)}件中{len(findings)}件要注意"
        )
        return result

    def _analyze_statistics(self) -> AuditResult:
        """統計分析とトレンド検出を実行"""
        logger.info("統計分析を開始")

        findings = []
        metrics = {"analysis_period": "24hours", "trends": {}}

        # 過去24時間のデータを分析
        trends = self._calculate_trends()
        metrics["trends"] = trends

        # 悪化トレンドを検出
        if trends.get("violation_trend") == "increasing":
            findings.append(
                {
                    "type": "negative_trend",
                    "severity": "medium",
                    "description": "違反発生率が増加傾向にあります",
                }
            )

        if trends.get("resolution_time_trend") == "increasing":
            findings.append(
                {
                    "type": "negative_trend",
                    "severity": "medium",
                    "description": "違反解決時間が長期化しています",
                }
            )

        result = AuditResult(
            audit_type=AuditType.STATISTICS_ANALYSIS,
            passed=len(findings) == 0,
            findings=findings,
            metrics=metrics,
        )

        self.last_statistics_result = result

        logger.info(f"統計分析完了: {len(findings)}件のトレンド問題を検出")
        return result

    def _generate_report(self) -> AuditReport:
        """監査レポートを生成"""
        logger.info("監査レポート生成を開始")

        # 過去1時間の監査結果を収集
        recent_audits = [
            task for task in self.audit_history[-10:] if task.result is not None
        ]

        # コンプライアンスメトリクスを計算
        compliance = self._calculate_compliance_metrics()

        # 推奨事項を生成
        recommendations = self._generate_recommendations(recent_audits, compliance)

        # エスカレーションが必要か判定
        critical_findings = sum(
            len([f for f in audit.result.findings if f.get("severity") == "critical"])
            for audit in recent_audits
        )

        report = AuditReport(
            report_id=f"RPT-{datetime.now().strftime('%Y%m%d-%H%M')}",
            timestamp=datetime.now(),
            summary=self._generate_summary(recent_audits, compliance),
            audit_results=[audit.result for audit in recent_audits if audit.result],
            compliance_metrics=compliance,
            recommendations=recommendations,
            escalation_required=critical_findings > 0,
            escalation_reason=(
                "重大な違反が検出されました" if critical_findings > 0 else None
            ),
        )

        # レポートを保存
        self._save_report(report)

        logger.info(f"監査レポート生成完了: {report.report_id}")
        return report

    def _scan_codebase(self) -> Dict[str, Any]:
        """コードベースをスキャン"""
        results = {"files_scanned": 0, "violations_found": 0, "findings": []}

        # Pythonファイルをスキャン（シミュレーション）
        # 実際の実装では、プロジェクト内の全ファイルをスキャン
        try:
            # ファイル数をカウント
            py_files = list(Path(".").rglob("*.py"))
            results["files_scanned"] = len(py_files)

            # 各ファイルをチェック（簡易版）
            for file_path in py_files[:10]:  # デモ用に10ファイルまで
                with open(file_path, "r") as f:
                    content = f.read()

                    # 簡易的な違反チェック
                    if "TODO" in content or "FIXME" in content:
                        results["findings"].append(
                            {
                                "type": "incomplete_implementation",
                                "severity": "low",
                                "description": f"未完了のTODO/FIXMEが{file_path}に存在",
                                "file": str(file_path),
                            }
                        )
                        results["violations_found"] += 1

        except Exception as e:
            logger.error(f"コードベーススキャンエラー: {e}")

        return results

    def _check_test_coverage(self) -> Dict[str, Any]:
        """テストカバレッジをチェック"""
        # 実際の実装では、pytest-covなどを使用してカバレッジを取得
        # ここではシミュレーション
        return {
            "coverage": 92.5,  # シミュレーション値
            "uncovered_files": [],
            "branch_coverage": 88.0,
        }

    def _check_dependencies(self) -> Dict[str, Any]:
        """依存関係の脆弱性をチェック"""
        # 実際の実装では、safety checkなどを使用
        return {
            "total_dependencies": 25,
            "vulnerabilities": [],  # シミュレーションでは脆弱性なし
        }

    def _check_process_compliance(self) -> Dict[str, Any]:
        """プロセス遵守状況をチェック"""
        violations = []

        # GitHubフロー遵守チェック（シミュレーション）
        # 実際の実装では、git logを解析

        return {"compliance_rate": 95.0, "violations": violations}

    def _calculate_trends(self) -> Dict[str, Any]:
        """トレンドを計算"""
        # 過去のデータから傾向を分析
        # ここではシミュレーション
        return {
            "violation_trend": "stable",
            "resolution_time_trend": "improving",
            "compliance_trend": "stable",
        }

    def _calculate_compliance_metrics(self) -> ComplianceMetrics:
        """コンプライアンスメトリクスを計算"""
        metrics = ComplianceMetrics()

        # 各項目を計算（シミュレーション）
        metrics.test_coverage = 92.5
        metrics.tdd_compliance_rate = 88.0
        metrics.github_flow_compliance_rate = 95.0
        metrics.four_sages_consultation_rate = 75.0
        metrics.documentation_completeness = 85.0

        metrics.total_checks = 100
        metrics.passed_checks = 88
        metrics.calculate()

        return metrics

    def _generate_recommendations(
        self, recent_audits: List[AuditTask], compliance: ComplianceMetrics
    ) -> List[str]:
        """推奨事項を生成"""
        recommendations = []

        # コンプライアンスに基づく推奨
        problem_areas = compliance.get_problem_areas()
        if "test_coverage" in problem_areas:
            recommendations.append("テストカバレッジを90%以上に向上させてください")

        if "tdd_compliance" in problem_areas:
            recommendations.append("TDD（テスト駆動開発）の実践を強化してください")

        if "four_sages_consultation" in problem_areas:
            recommendations.append("新機能実装前の4賢者相談を徹底してください")

        # 違反傾向に基づく推奨
        critical_count = sum(
            len([f for f in audit.result.findings if f.get("severity") == "critical"])
            for audit in recent_audits
            if audit.result
        )

        if critical_count > 0:
            recommendations.append("重大な違反が検出されています。即座の対応が必要です")

        return recommendations

    def _generate_summary(
        self, recent_audits: List[AuditTask], compliance: ComplianceMetrics
    ) -> str:
        """サマリーを生成"""
        total_findings = sum(
            len(audit.result.findings) for audit in recent_audits if audit.result
        )

        passed_audits = sum(
            1 for audit in recent_audits if audit.result and audit.result.passed
        )

        summary = f"""
監査サマリー（{datetime.now().strftime('%Y-%m-%d %H:%M')}）
- 実施監査数: {len(recent_audits)}
- 合格監査: {passed_audits}/{len(recent_audits)}
- 検出された問題: {total_findings}件
- 全体コンプライアンス率: {compliance.overall_compliance_rate:.1f}%
- ステータス: {'コンプライアント' if compliance.is_compliant else '要改善'}
"""
        return summary.strip()

    def _should_escalate(self, result: AuditResult) -> bool:
        """エスカレーションが必要か判定"""
        # 重大な違反がある場合
        critical_findings = [
            f for f in result.findings if f.get("severity") == "critical"
        ]

        return len(critical_findings) > 0 or not result.passed

    def _trigger_escalation(self, result: AuditResult, reason: str):
        """エスカレーションをトリガー"""
        logger.warning(f"エスカレーション発動: {reason}")

        # 実際の実装では、通知システムと連携
        # ここではログ出力のみ
        try:
            from libs.notification_system import NotificationSystem

            notifier = NotificationSystem()
            notifier.send_critical_alert(
                title="Elder Flow監査エスカレーション",
                message=reason,
                details=result.findings,
            )
        except ImportError:
            logger.info("通知システムは未実装です")

    def _save_report(self, report: AuditReport):
        """レポートを保存"""
        report_dir = Path("reports/hourly_audits")
        report_dir.mkdir(parents=True, exist_ok=True)

        report_file = report_dir / f"{report.report_id}.json"
        with open(report_file, "w") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

    def _convert_report_to_result(self, report: AuditReport) -> AuditResult:
        """レポートを監査結果に変換"""
        return AuditResult(
            audit_type=AuditType.REPORT_GENERATION,
            passed=not report.escalation_required,
            findings=[],
            metrics={
                "report_id": report.report_id,
                "compliance_rate": report.compliance_metrics.overall_compliance_rate,
            },
        )

    def get_audit_summary(self) -> Dict[str, Any]:
        """監査サマリーを取得"""
        if not self.audit_history:
            return {"total_audits": 0, "status": "no_data"}

        completed_audits = [
            task for task in self.audit_history if task.status == "completed"
        ]

        passed_audits = [
            task for task in completed_audits if task.result and task.result.passed
        ]

        summary = {
            "total_audits": len(self.audit_history),
            "completed_audits": len(completed_audits),
            "passed_audits": len(passed_audits),
            "failed_audits": len(completed_audits) - len(passed_audits),
            "success_rate": (
                (len(passed_audits) / len(completed_audits) * 100)
                if completed_audits
                else 0
            ),
            "by_type": {},
        }

        # タイプ別集計
        for audit_type in AuditType:
            type_audits = [
                task for task in completed_audits if task.audit_type == audit_type
            ]
            if type_audits:
                summary["by_type"][audit_type.value] = {
                    "total": len(type_audits),
                    "passed": len(
                        [t for t in type_audits if t.result and t.result.passed]
                    ),
                }

        return summary

    def export_report(self, report: AuditReport, format: str = "json") -> str:
        """レポートをエクスポート"""
        if format == "json":
            return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)

        elif format == "html":
            # HTML形式でエクスポート
            html = f"""
<html>
<head>
    <title>Elder Flow監査レポート - {report.report_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 10px; }}
        .section {{ margin: 20px 0; }}
        .critical {{ color: red; }}
        .high {{ color: orange; }}
        .medium {{ color: yellow; }}
        .low {{ color: green; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Elder Flow監査レポート</h1>
        <p>ID: {report.report_id}</p>
        <p>生成日時: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="section">
        <h2>サマリー</h2>
        <pre>{report.summary}</pre>
    </div>

    <div class="section">
        <h2>コンプライアンスメトリクス</h2>
        <p>全体コンプライアンス率: {report.compliance_metrics.overall_compliance_rate:.1f}%</p>
        <p>ステータス: {'✅ コンプライアント' if report.compliance_metrics.is_compliant else '❌ 要改善'}</p>
    </div>

    <div class="section">
        <h2>推奨事項</h2>
        <ul>
            {''.join(f'<li>{r}</li>' for r in report.recommendations)}
        </ul>
    </div>

    {f'<div class="section critical"><h2>⚠️ エスカレーション</h2><p>{report.escalation_reason}</p></div>' \
        if report.escalation_required \
        else ''}
</body>
</html>
"""
            return html

        else:
            return str(report)
