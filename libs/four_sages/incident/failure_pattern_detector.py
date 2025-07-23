#!/usr/bin/env python3
"""
🔍 Failure Pattern Detector - 失敗パターン検出システム
Phase 26: Incident Sage統合実装
Created: 2025-07-17
Author: Claude Elder
Version: 1.0.0
"""

import asyncio
import json
import logging
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Elders Legacy Integration
from core.elders_legacy import EldersAILegacy
from libs.four_sages.incident.incident_sage import IncidentCategory, IncidentSeverity

logger = logging.getLogger("failure_pattern_detector")


@dataclass
class FailurePattern:
    """失敗パターンデータ構造"""

    pattern_id: str
    pattern_type: str  # "error_message", "time_series", "resource", "dependency"
    category: IncidentCategory
    severity: IncidentSeverity
    description: str
    detection_rules: List[Dict]
    occurrence_count: int
    first_seen: datetime
    last_seen: datetime
    affected_systems: List[str]
    resolution_actions: List[str]
    confidence_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.description,
            "detection_rules": self.detection_rules,
            "occurrence_count": self.occurrence_count,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "affected_systems": self.affected_systems,
            "resolution_actions": self.resolution_actions,
            "confidence_score": self.confidence_score,
            "metadata": self.metadata,
        }


class FailurePatternDetector(EldersAILegacy):
    """失敗パターン検出システム"""

    def __init__(
        self,
        tracking_db_path: str = "elder_flow_tracking.db",
        incident_db_path: str = "data/incident_sage.db",
    ):
        super().__init__(
            name="FailurePatternDetector", model_type="pattern-detection-v1"
        )
        self.tracking_db_path = tracking_db_path
        self.incident_db_path = incident_db_path
        self.pattern_registry: Dict[str, FailurePattern] = {}
        self.pattern_threshold = 3  # パターン認識閾値
        self.analysis_window = timedelta(days=30)  # 分析対象期間

        # パターン検出ルール
        self.error_patterns = {
            "timeout": r"(timeout|timed out|deadline exceeded)",
            "memory": r"(out of memory|memory error|oom|heap space)",
            "connection": r"(connection refused|connection error|cannot connect)",
            "permission": r"(permission denied|access denied|unauthorized)",
            "notfound": r"(not found|404|missing|does not exist)",
            "syntax": r"(syntax error|parse error|invalid syntax)",
            "dependency": r"(dependency error|import error|module not found)",
            "disk": r"(disk full|no space left|storage error)",
        }

        logger.info("🔍 Failure Pattern Detector initialized")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """リクエスト処理"""
        request_type = request.get("type", "analyze")

        if request_type == "analyze":
            return await self._analyze_failures(request)
        elif request_type == "detect":
            return await self._detect_patterns(request)
        elif request_type == "predict":
            return await self._predict_failure(request)
        elif request_type == "get_patterns":
            return await self._get_patterns(request)
        else:
            return {"success": False, "error": f"Unknown request type: {request_type}"}

    async def analyze_historical_failures(self, days_back: int = 30) -> Dict[str, Any]:
        """過去の失敗データ分析"""
        try:
            logger.info(f"🔍 Analyzing failures from past {days_back} days")

            # 追跡データベースから失敗データ抽出
            failures = await self._extract_failure_data(days_back)

            # パターン抽出
            patterns = await self._extract_patterns(failures)

            # パターン分類と評価
            for pattern in patterns:
                classified = await self._classify_pattern(pattern)
                severity = await self._evaluate_pattern_severity(pattern)
                pattern["category"] = classified
                pattern["severity"] = severity

            # パターンレジストリ更新
            await self._update_pattern_registry(patterns)

            return {
                "success": True,
                "total_failures": len(failures),
                "patterns_found": len(patterns),
                "pattern_summary": self._summarize_patterns(patterns),
            }

        except Exception as e:
            logger.error(f"❌ Historical analysis failed: {e}")
            return {"success": False, "error": str(e)}

    async def _extract_failure_data(self, days_back: int) -> List[Dict[str, Any]]:
        """失敗データ抽出"""
        failures = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        try:
            conn = sqlite3.connect(self.tracking_db_path)
            conn.row_factory = sqlite3.Row

            # 失敗した実行詳細を取得
            cursor = conn.execute(
                """
                SELECT ed.*, t.description as task_description, t.priority
                FROM execution_details ed
                JOIN tasks t ON ed.task_id = t.task_id
                WHERE ed.success = 0
                AND ed.timestamp > ?
                ORDER BY ed.timestamp DESC
            """,
                (cutoff_date.isoformat(),),
            )

            for row in cursor:
                failure = {
                    "task_id": row["task_id"],
                    "task_description": row["task_description"],
                    "detail_type": row["detail_type"],
                    "command": row["command"],
                    "stderr": row["stderr"],
                    "exit_code": row["exit_code"],
                    "execution_time": row["execution_time"],
                    "timestamp": row["timestamp"],
                    "priority": row["priority"],
                }
                failures.append(failure)

            conn.close()
            logger.info(f"📊 Extracted {len(failures)} failure records")
            return failures

        except Exception as e:
            logger.error(f"❌ Failed to extract failure data: {e}")
            return []

    async def _extract_patterns(
        self, failures: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """失敗パターン抽出"""
        patterns = []

        # エラーメッセージパターン
        error_patterns = await self._extract_error_patterns(failures)
        patterns.extend(error_patterns)

        # 時系列パターン
        time_patterns = await self._extract_time_patterns(failures)
        patterns.extend(time_patterns)

        # リソース使用パターン
        resource_patterns = await self._extract_resource_patterns(failures)
        patterns.extend(resource_patterns)

        # 依存関係パターン
        dependency_patterns = await self._extract_dependency_patterns(failures)
        patterns.extend(dependency_patterns)

        return patterns

    async def _extract_error_patterns(
        self, failures: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """エラーメッセージパターン抽出"""
        error_groups = defaultdict(list)

        # 繰り返し処理
        for failure in failures:
            stderr = failure.get("stderr", "")
            if not stderr:
                continue

            # 既知のエラーパターンとマッチング
            for pattern_name, pattern_regex in self.error_patterns.items():
                if re.search(pattern_regex, stderr, re.IGNORECASE):
                    error_groups[pattern_name].append(failure)
                    break
            else:
                # 未知のパターンは汎用グループへ
                error_groups["unknown"].append(failure)

        # パターン化
        patterns = []
        for pattern_name, failures_list in error_groups.items():
            if len(failures_list) >= self.pattern_threshold:
                pattern = {
                    "pattern_type": "error_message",
                    "pattern_name": pattern_name,
                    "occurrences": len(failures_list),
                    "examples": failures_list[:5],  # 最初の5例
                    "affected_tasks": list(set(f["task_id"] for f in failures_list)),
                    "common_stderr": self._find_common_substring(
                        [f["stderr"] for f in failures_list]
                    ),
                }
                patterns.append(pattern)

        return patterns

    async def _extract_time_patterns(
        self, failures: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """時系列パターン抽出"""
        patterns = []

        # 時間帯別の失敗傾向
        hourly_failures = defaultdict(list)
        for failure in failures:
            timestamp = datetime.fromisoformat(failure["timestamp"])
            hour = timestamp.hour
            hourly_failures[hour].append(failure)

        # 特定時間帯に集中するパターン
        for hour, failures_list in hourly_failures.items():
            if len(failures_list) >= self.pattern_threshold * 2:
                pattern = {
                    "pattern_type": "time_series",
                    "pattern_name": f"peak_hour_{hour}",
                    "occurrences": len(failures_list),
                    "time_window": f"{hour:02d}:00-{hour:02d}:59",
                    "failure_rate": len(failures_list) / len(failures),
                }
                patterns.append(pattern)

        return patterns

    async def _extract_resource_patterns(
        self, failures: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """リソース使用パターン抽出"""
        patterns = []

        # 実行時間異常パターン
        execution_times = [
            f["execution_time"] for f in failures if f["execution_time"] > 0
        ]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            slow_failures = [f for f in failures if f["execution_time"] > avg_time * 2]

            if len(slow_failures) >= self.pattern_threshold:
                pattern = {
                    "pattern_type": "resource",
                    "pattern_name": "slow_execution",
                    "occurrences": len(slow_failures),
                    "average_execution_time": sum(
                        f["execution_time"] for f in slow_failures
                    )
                    / len(slow_failures),
                    "threshold": avg_time * 2,
                }
                patterns.append(pattern)

        return patterns

    async def _extract_dependency_patterns(
        self, failures: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """依存関係パターン抽出"""
        patterns = []

        # 連鎖的な失敗パターン
        task_failures = defaultdict(list)
        for failure in failures:
            task_failures[failure["task_id"]].append(failure)

        # 頻繁に失敗するタスクの組み合わせを検出
        failure_chains = []
        for task_id, failures_list in task_failures.items():
            if len(failures_list) >= self.pattern_threshold:
                # 近い時間に発生した他のタスクの失敗を探す
                related_failures = self._find_related_failures(task_id, failures)
                if related_failures:
                    failure_chains.append(
                        {
                            "primary_task": task_id,
                            "related_tasks": related_failures,
                            "occurrences": len(failures_list),
                        }
                    )

        if failure_chains:
            pattern = {
                "pattern_type": "dependency",
                "pattern_name": "failure_chain",
                "chains": failure_chains,
                "total_chains": len(failure_chains),
            }
            patterns.append(pattern)

        return patterns

    def _find_related_failures(
        self, task_id: str, all_failures: List[Dict[str, Any]]
    ) -> List[str]:
        """関連する失敗を検出"""
        related = set()
        task_failures = [f for f in all_failures if f["task_id"] == task_id]

        for failure in task_failures:
            failure_time = datetime.fromisoformat(failure["timestamp"])
            # 前後5分以内の他のタスクの失敗を探す
            for other in all_failures:
                if other["task_id"] != task_id:
                    other_time = datetime.fromisoformat(other["timestamp"])
                    if abs((failure_time - other_time).total_seconds()) <= 300:
                        related.add(other["task_id"])

        return list(related)

    def _find_common_substring(self, strings: List[str]) -> str:
        """共通部分文字列を検出"""
        if not strings:
            return ""

        # 簡易的な共通部分検出
        words_counter = Counter()
        for s in strings:
            words = s.lower().split()
            words_counter.update(words)

        # 最も頻出する単語を返す
        common_words = [
            word
            for word, count in words_counter.most_common(5)
            if count >= len(strings) * 0.5
        ]
        return " ".join(common_words)

    async def _classify_pattern(self, pattern: Dict[str, Any]) -> IncidentCategory:
        """パターン分類"""
        pattern_type = pattern.get("pattern_type", "")
        pattern_name = pattern.get("pattern_name", "")

        # パターンタイプとパターン名からカテゴリを推定
        if pattern_type == "error_message":
            if pattern_name in ["timeout", "slow_execution"]:
                return IncidentCategory.PERFORMANCE_ISSUE
            elif pattern_name in ["connection", "network"]:
                return IncidentCategory.NETWORK_ISSUE
            elif pattern_name in ["permission", "unauthorized"]:
                return IncidentCategory.SECURITY_BREACH
            elif pattern_name in ["syntax", "dependency"]:
                return IncidentCategory.CONFIGURATION_ERROR
            elif pattern_name in ["memory", "disk"]:
                return IncidentCategory.SYSTEM_FAILURE
        elif pattern_type == "dependency":
            return IncidentCategory.SYSTEM_FAILURE
        elif pattern_type == "resource":
            return IncidentCategory.PERFORMANCE_ISSUE

        return IncidentCategory.SYSTEM_FAILURE  # デフォルト

    async def _evaluate_pattern_severity(
        self, pattern: Dict[str, Any]
    ) -> IncidentSeverity:
        """パターン重要度評価"""
        occurrences = pattern.get("occurrences", 0)
        pattern_type = pattern.get("pattern_type", "")

        # 発生頻度ベースの重要度
        if occurrences >= 50:
            base_severity = IncidentSeverity.CRITICAL
        elif occurrences >= 20:
            base_severity = IncidentSeverity.HIGH
        elif occurrences >= 10:
            base_severity = IncidentSeverity.MEDIUM
        else:
            base_severity = IncidentSeverity.LOW

        # パターンタイプによる調整
        if pattern_type == "dependency":
            # 依存関係の失敗は影響が大きい
            if base_severity == IncidentSeverity.MEDIUM:
                return IncidentSeverity.HIGH
            elif base_severity == IncidentSeverity.LOW:
                return IncidentSeverity.MEDIUM

        return base_severity

    async def _update_pattern_registry(self, patterns: List[Dict[str, Any]]):
        """パターンレジストリ更新"""
        for pattern_data in patterns:
            pattern_id = (
                f"{pattern_data['pattern_type']}_{pattern_data['pattern_name']}"
            )

            if pattern_id in self.pattern_registry:
                # 既存パターン更新
                existing = self.pattern_registry[pattern_id]
                existing.occurrence_count += pattern_data.get("occurrences", 0)
                existing.last_seen = datetime.now()
                existing.confidence_score = min(1.0, existing.confidence_score + 0.1)
            else:
                # 新規パターン登録
                pattern = FailurePattern(
                    pattern_id=pattern_id,
                    pattern_type=pattern_data["pattern_type"],
                    category=pattern_data.get(
                        "category", IncidentCategory.SYSTEM_FAILURE
                    ),
                    severity=pattern_data.get("severity", IncidentSeverity.MEDIUM),
                    description=f"Pattern: {pattern_data['pattern_name']}",
                    detection_rules=[pattern_data],
                    occurrence_count=pattern_data.get("occurrences", 0),
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    affected_systems=pattern_data.get("affected_tasks", []),
                    resolution_actions=[],
                    confidence_score=0.5,
                    metadata=pattern_data,
                )
                self.pattern_registry[pattern_id] = pattern

    def _summarize_patterns(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """パターンサマリー生成"""
        summary = {
            "by_type": defaultdict(int),
            "by_severity": defaultdict(int),
            "total_occurrences": 0,
        }

        for pattern in patterns:
            pattern_type = pattern.get("pattern_type", "unknown")
            severity = pattern.get("severity", IncidentSeverity.MEDIUM)
            occurrences = pattern.get("occurrences", 0)

            summary["by_type"][pattern_type] += 1
            summary["by_severity"][severity.value] += 1
            summary["total_occurrences"] += occurrences

        return {
            "by_type": dict(summary["by_type"]),
            "by_severity": dict(summary["by_severity"]),
            "total_occurrences": summary["total_occurrences"],
        }

    async def predict_failure(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """失敗予測"""
        try:
            predictions = []

            # 各パターンに対して予測確率を計算
            for pattern_id, pattern in self.pattern_registry.items():
                probability = await self._calculate_failure_probability(
                    pattern, current_metrics
                )
                if probability > 0.3:  # 30%以上の確率で警告
                    predictions.append(
                        {
                            "pattern_id": pattern_id,
                            "probability": probability,
                            "severity": pattern.severity.value,
                            "category": pattern.category.value,
                            "description": pattern.description,
                            "recommended_actions": self._get_recommended_actions(
                                pattern
                            ),
                        }
                    )

            # 確率順にソート
            predictions.sort(key=lambda x: x["probability"], reverse=True)

            return {
                "success": True,
                "predictions": predictions[:5],  # 上位5件
                "highest_risk": predictions[0] if predictions else None,
                "risk_level": self._calculate_overall_risk(predictions),
            }

        except Exception as e:
            logger.error(f"❌ Failure prediction failed: {e}")
            return {"success": False, "error": str(e)}

    async def _calculate_failure_probability(
        self, pattern: FailurePattern, current_metrics: Dict[str, Any]
    ) -> float:
        """失敗確率計算"""
        base_probability = 0.0

        # パターンの信頼度スコアを基準に
        base_probability = pattern.confidence_score * 0.3

        # 最近の発生頻度を考慮
        time_since_last = (
            datetime.now() - pattern.last_seen
        ).total_seconds() / 3600  # 時間単位
        if time_since_last < 1:  # 1時間以内
            base_probability += 0.3
        elif time_since_last < 24:  # 24時間以内
            base_probability += 0.2
        elif time_since_last < 168:  # 1週間以内
            base_probability += 0.1

        # 現在のメトリクスとの類似度
        if pattern.pattern_type == "resource":
            # リソース使用率をチェック
            cpu_usage = current_metrics.get("cpu_usage", 0)
            memory_usage = current_metrics.get("memory_usage", 0)
            if cpu_usage > 80 or memory_usage > 80:
                base_probability += 0.2

        return min(1.0, base_probability)

    def _get_recommended_actions(self, pattern: FailurePattern) -> List[str]:
        """推奨アクション取得"""
        actions = []

        if pattern.pattern_type == "error_message":
            if "timeout" in pattern.pattern_id:
                actions.extend(
                    [
                        "Increase timeout values",
                        "Optimize slow operations",
                        "Check network latency",
                    ]
                )
            elif "memory" in pattern.pattern_id:
                actions.extend(
                    [
                        "Increase memory allocation",
                        "Check for memory leaks",
                        "Optimize memory usage",
                    ]
                )
            elif "connection" in pattern.pattern_id:
                actions.extend(
                    [
                        "Check network connectivity",
                        "Verify service availability",
                        "Review firewall rules",
                    ]
                )
        elif pattern.pattern_type == "resource":
            actions.extend(
                [
                    "Scale up resources",
                    "Optimize resource usage",
                    "Implement resource limits",
                ]
            )
        elif pattern.pattern_type == "dependency":
            actions.extend(
                [
                    "Review dependency chain",
                    "Implement circuit breakers",
                    "Add retry mechanisms",
                ]
            )

        return actions

    def _calculate_overall_risk(self, predictions: List[Dict[str, Any]]) -> str:
        """全体的なリスクレベル計算"""
        if not predictions:
            return "low"

        # 最高確率とクリティカルな予測の数を考慮
        max_probability = max(p["probability"] for p in predictions)
        critical_count = sum(1 for p in predictions if p["severity"] == "critical")

        if max_probability > 0.8 or critical_count >= 2:
            return "critical"
        elif max_probability > 0.6 or critical_count >= 1:
            return "high"
        elif max_probability > 0.4:
            return "medium"
        else:
            return "low"

    async def _analyze_failures(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """失敗分析リクエスト処理"""
        days_back = request.get("days_back", 30)
        return await self.analyze_historical_failures(days_back)

    async def _detect_patterns(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """パターン検出リクエスト処理"""
        failures = request.get("failures", [])
        patterns = await self._extract_patterns(failures)
        return {"success": True, "patterns": patterns, "count": len(patterns)}

    async def _predict_failure(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """失敗予測リクエスト処理"""
        metrics = request.get("metrics", {})
        return await self.predict_failure(metrics)

    async def _get_patterns(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """パターン取得リクエスト処理"""
        pattern_type = request.get("pattern_type")
        severity = request.get("severity")

        patterns = []
        for pattern_id, pattern in self.pattern_registry.items():
            if pattern_type and pattern.pattern_type != pattern_type:
                continue
            if severity and pattern.severity.value != severity:
                continue
            patterns.append(pattern.to_dict())

        return {"success": True, "patterns": patterns, "count": len(patterns)}

    def get_capabilities(self) -> List[str]:
        """能力一覧"""
        return [
            "failure_pattern_detection",
            "pattern_classification",
            "severity_evaluation",
            "failure_prediction",
            "risk_assessment",
            "recommendation_generation",
        ]


# エクスポート
__all__ = ["FailurePatternDetector", "FailurePattern"]
