#!/usr/bin/env python3
"""
🧙‍♂️ Four Sages Overseer Magic - 4賢者監督魔法
====================================================

4賢者（Knowledge, Task, Incident, RAG）への相談義務、活動品質、連携を監査する古代魔法システム
Issue #200対応

Features:
- 4賢者相談義務履行検証
- 賢者活動の実質性評価  
- 賢者間連携・助言実施追跡
- プロジェクト品質向上への貢献度分析
- 自動改善提案生成

Author: Claude Elder
Created: 2025-07-21
"""

import asyncio
import json
import logging
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import xml.etree.ElementTree as ET

# プロジェクトルートをパスに追加
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.base import AncientElderBase, AuditResult, ViolationSeverity


class SageType:
    """4賢者の種類"""
    KNOWLEDGE = "knowledge"      # ナレッジ賢者
    TASK = "task"               # タスク賢者
    INCIDENT = "incident"       # インシデント賢者
    RAG = "rag"                 # RAG賢者


class SageViolationType:
    """4賢者監督違反の種類"""
    MISSING_CONSULTATION = "MISSING_CONSULTATION"          # 相談義務違反
    INSUFFICIENT_SAGE_ACTIVITY = "INSUFFICIENT_SAGE_ACTIVITY"  # 賢者活動不足
    POOR_SAGE_COLLABORATION = "POOR_SAGE_COLLABORATION"    # 賢者間連携不足
    FAKE_SAGE_CONSULTATION = "FAKE_SAGE_CONSULTATION"      # 偽相談（形式的相談）
    SAGE_ADVICE_IGNORED = "SAGE_ADVICE_IGNORED"            # 賢者助言無視
    INCOMPLETE_SAGE_IMPLEMENTATION = "INCOMPLETE_SAGE_IMPLEMENTATION"  # 賢者実装不完全


class SageConsultationTracker:
    """4賢者相談追跡システム"""
    
    def __init__(self, project_root: Optional[Path] = None)self.project_root = project_root or Path.cwd()
    """初期化メソッド"""
        self.logger = logging.getLogger("SageConsultationTracker")
        
        # 4賢者ログパス
        self.sage_log_paths = {
            SageType.KNOWLEDGE: self.project_root / "logs" / "knowledge_sage.log",
            SageType.TASK: self.project_root / "logs" / "task_sage.log", 
            SageType.INCIDENT: self.project_root / "logs" / "incident_sage.log",
            SageType.RAG: self.project_root / "logs" / "rag_sage.log"
        }
        
        # 相談パターン
        self.consultation_patterns = {
            SageType.KNOWLEDGE: [
                re.compile(r'knowledge.*sage|sage.*knowledge|knowledge.*consult|consult.*knowledge' \
                    'knowledge.*sage|sage.*knowledge|knowledge.*consult|consult.*knowledge', re.IGNORECASE),
                re.compile(r'知識.*相談|相談.*知識|知識.*賢者|ナレッジ.*賢者', re.IGNORECASE),
            ],
            SageType.TASK: [
                re.compile(r'task.*sage|sage.*task|task.*consult|consult.*task', re.IGNORECASE),
                re.compile(r'タスク.*相談|相談.*タスク|タスク.*賢者', re.IGNORECASE),
            ],
            SageType.INCIDENT: [
                re.compile(r'incident.*sage|sage.*incident|incident.*consult|consult.*incident' \
                    'incident.*sage|sage.*incident|incident.*consult|consult.*incident', re.IGNORECASE),
                re.compile(r'インシデント.*相談|相談.*インシデント|インシデント.*賢者', re.IGNORECASE),
            ],
            SageType.RAG: [
                re.compile(r'rag.*sage|sage.*rag|rag.*consult|consult.*rag', re.IGNORECASE),
                re.compile(r'RAG.*相談|相談.*RAG|RAG.*賢者', re.IGNORECASE),
            ]
        }
        
    def track_sage_consultations(self, 
                               file_path: str,
                               time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """4賢者相談状況を追跡"""
        if time_window is None:
            time_window = timedelta(days=7)  # デフォルト1週間
            
        try:
            # Git履歴から相談記録を取得
            consultation_records = self._get_consultation_records(file_path, time_window)
            
            # 各賢者への相談頻度を分析
            consultation_analysis = self._analyze_consultation_patterns(consultation_records)
            
            # 相談義務違反を検出
            violations = self._detect_consultation_violations(consultation_analysis, file_path)
            
            return {
                "file_path": file_path,
                "time_window": str(time_window),
                "consultation_records": consultation_records,
                "consultation_analysis": consultation_analysis,
                "violations": violations,
                "overall_consultation_score": self._calculate_consultation_score(consultation_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Sage consultation tracking failed for {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "consultation_records": [],
                "violations": [],
                "overall_consultation_score": 0.0
            }
            
    def _get_consultation_records(
        self,
        file_path: str,
        time_window: timedelta
    ) -> List[Dict[str, Any]]:
        """Git履歴から相談記録を取得"""
        try:
            since_date = (datetime.now() - time_window).strftime("%Y-%m-%d")
            cmd = [
                "git", "log", 
                "--since", since_date,
                "--grep", "sage",
                "--grep", "賢者",
                "--grep", "consult",
                "--grep", "相談",
                "--all-match",
                "--pretty=format:%H|%ad|%s|%an",
                "--date=iso",
                "--", file_path
            ]
            
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            records = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        records.append({
                            "hash": parts[0],
                            "date": parts[1],
                            "message": parts[2],
                            "author": parts[3]
                        })
                        
            return records
            
        except Exception as e:
            self.logger.error(f"Failed to get consultation records: {e}")
            return []
            
    def _analyze_consultation_patterns(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """相談パターンを分析"""
        sage_consultations = {
            SageType.KNOWLEDGE: [],
            SageType.TASK: [],
            SageType.INCIDENT: [],
            SageType.RAG: []
        }
        
        for record in records:
            message = record["message"]
            for sage_type, patterns in self.consultation_patterns.items():
                for pattern in patterns:
                    if pattern.search(message):
                        sage_consultations[sage_type].append(record)
                        break
                        
        # 各賢者への相談頻度・質を分析
        analysis = {}
        for sage_type, consultations in sage_consultations.items():
            analysis[sage_type] = {
                "consultation_count": len(consultations),
                "recent_consultations": consultations,
                "consultation_frequency": len(consultations) / 7.0,  # 週当たり
                "last_consultation": consultations[0]["date"] if consultations else None
            }
            
        return analysis
        
    def _detect_consultation_violations(
        self,
        analysis: Dict[str,
        Any],
        file_path: str
    ) -> List[Dict[str, Any]]:
        """相談義務違反を検出"""
        violations = []
        
        # 最小相談要件（賢者毎）
        min_consultations = {
            SageType.KNOWLEDGE: 1,  # 知識系タスクには必須
            SageType.TASK: 1,       # タスク管理には必須
            SageType.INCIDENT: 0,   # 問題発生時のみ
            SageType.RAG: 1         # 情報検索には必須
        }
        
        for sage_type, min_count in min_consultations.items():
            sage_analysis = analysis.get(sage_type, {})
            consultation_count = sage_analysis.get("consultation_count", 0)
            
            if consultation_count < min_count:
                violations.append({
                    "type": SageViolationType.MISSING_CONSULTATION,
                    "severity": "HIGH",
                    "sage_type": sage_type,
                    "description": f"Insufficient consultation with {
                        sage_type} sage (required: {min_count},
                        actual: {consultation_count
                    })",
                    "file_path": file_path,
                    "suggestion": f"Consult with {sage_type} sage for proper guidance"
                })
                
        return violations
        
    def _calculate_consultation_score(self, analysis: Dict[str, Any]) -> float:
        """相談スコアを計算"""
        total_score = 0.0
        
        for sage_type, sage_analysis in analysis.items():
            consultation_count = sage_analysis.get("consultation_count", 0)
            # 各賢者25点満点（相談3回で満点）
            sage_score = min(consultation_count * 8.33, 25)
            total_score += sage_score
            
        return total_score


class SageActivityAnalyzer:
    """4賢者活動実質性評価システム"""
    
    def __init__(self, project_root: Optional[Path] = None)self.project_root = project_root or Path.cwd()
    """初期化メソッド"""
        self.logger = logging.getLogger("SageActivityAnalyzer")
        
    def analyze_sage_activity_quality(self, 
                                    target_path: str,
                                    time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """4賢者活動の実質性を評価"""
        if time_window is None:
            time_window = timedelta(days=30)  # デフォルト30日
            
        try:
            # 各賢者の活動ログを分析
            activity_analysis = self._analyze_individual_sage_activities(time_window)
            
            # 賢者間連携を評価
            collaboration_analysis = self._analyze_sage_collaboration(time_window)
            
            # 実質性違反を検出
            violations = self._detect_activity_violations(
                activity_analysis,
                collaboration_analysis,
                target_path
            )
            
            return {
                "target_path": target_path,
                "time_window": str(time_window),
                "sage_activities": activity_analysis,
                "collaboration_analysis": collaboration_analysis,
                "violations": violations,
                "overall_activity_score": self._calculate_activity_score(
                    activity_analysis,
                    collaboration_analysis
                )
            }
            
        except Exception as e:
            self.logger.error(f"Sage activity analysis failed for {target_path}: {e}")
            return {
                "target_path": target_path,
                "error": str(e),
                "sage_activities": {},
                "violations": [],
                "overall_activity_score": 0.0
            }
            
    def _analyze_individual_sage_activities(self, time_window: timedelta) -> Dict[str, Any]:
        """各賢者の個別活動を分析"""
        activities = {}
        
        for sage_type in [SageType.KNOWLEDGE, SageType.TASK, SageType.INCIDENT, SageType.RAG]:
            activities[sage_type] = {
                "activity_count": self._count_sage_activities(sage_type, time_window),
                "quality_score": self._evaluate_sage_quality(sage_type, time_window),
                "responsiveness": self._evaluate_sage_responsiveness(sage_type, time_window),
                "expertise_demonstration": self._evaluate_sage_expertise(sage_type, time_window)
            }
            
        return activities
        
    def _analyze_sage_collaboration(self, time_window: timedelta) -> Dict[str, Any]collaboration_patterns = self._detect_collaboration_patterns(time_window):
    """者間連携を評価"""
        
        return {:
            "collaboration_frequency": len(collaboration_patterns),
            "collaboration_patterns": collaboration_patterns,
            "cross_sage_consultations": self._count_cross_sage_consultations(time_window),
            "collaborative_problem_solving": self._evaluate_collaborative_solving(time_window)
        }
        
    def _count_sage_activities(self, sage_type: str, time_window: timedelta) -> int:
        """賢者活動回数をカウント"""
        # 実装：ログファイルやGit履歴から活動回数を取得
        return 5  # モックデータ
        
    def _evaluate_sage_quality(self, sage_type: str, time_window: timedelta) -> float:
        """賢者活動の質を評価"""
        # 実装：活動内容の深度・有用性を評価
        return 85.0  # モックスコア
        
    def _evaluate_sage_responsiveness(self, sage_type: str, time_window: timedelta) -> float:
        """賢者応答性を評価"""
        # 実装：相談に対する応答速度・適切性を評価
        return 90.0  # モックスコア
        
    def _evaluate_sage_expertise(self, sage_type: str, time_window: timedelta) -> float:
        """賢者専門性実証を評価"""
        # 実装：専門分野での知見・助言の質を評価
        return 88.0  # モックスコア
        
    def _detect_collaboration_patterns(self, time_window: timedelta) -> List[Dict[str, Any]]:
        """連携パターンを検出"""
        # 実装：賢者間の連携・協調パターンを検出
        return [
            {
                "pattern": "knowledge_rag_collaboration",
                "frequency": 3,
                "quality": "high"
            }
        ]
        
    def _count_cross_sage_consultations(self, time_window: timedelta) -> int:
        """賢者間相談回数をカウント"""
        # 実装：賢者同士の相談・連携回数
        return 7  # モックデータ
        
    def _evaluate_collaborative_solving(self, time_window: timedelta) -> float:
        """協調問題解決を評価"""
        # 実装：複数賢者による問題解決の効果性を評価
        return 92.0  # モックスコア
        
    def _detect_activity_violations(self, 
                                  activity_analysis: Dict[str, Any],
                                  collaboration_analysis: Dict[str, Any],
                                  target_path: str) -> List[Dict[str, Any]]:
        """活動違反を検出"""
        violations = []
        
        # 各賢者の活動不足をチェック
        for sage_type, activity in activity_analysis.items():
            if activity["activity_count"] < 3:  # 最低3回の活動
                violations.append({
                    "type": SageViolationType.INSUFFICIENT_SAGE_ACTIVITY,
                    "severity": "MEDIUM",
                    "sage_type": sage_type,
                    "description": f"{sage_type} sage shows insufficient activity",
                    "target_path": target_path,
                    "actual_count": activity["activity_count"],
                    "expected_minimum": 3
                })
                
        # 賢者間連携不足をチェック
        if collaboration_analysis["collaboration_frequency"] < 2:
            violations.append({
                "type": SageViolationType.POOR_SAGE_COLLABORATION,
                "severity": "HIGH",
                "description": "Insufficient collaboration between sages",
                "target_path": target_path,
                "collaboration_frequency": collaboration_analysis["collaboration_frequency"],
                "expected_minimum": 2
            })
            
        return violations
        
    def _calculate_activity_score(self, 
                                activity_analysis: Dict[str, Any],
                                collaboration_analysis: Dict[str, Any]) -> float:
        """活動スコアを計算"""
        # 個別賢者活動スコア（70%）
        individual_score = 0.0
        for sage_activity in activity_analysis.values():
            individual_score += sage_activity["quality_score"] * 0.175  # 各賢者17.5%
            
        # 連携スコア（30%）
        collaboration_score = collaboration_analysis.get("collaborative_problem_solving", 0) * 0.3
        
        return individual_score + collaboration_score


class FourSagesOverseer(AncientElderBase):
    """4賢者監督魔法 - 総合監査システム"""
    
    def __init__(self, project_root: Optional[Path] = None)super().__init__(specialty="four_sages_overseer")
    """初期化メソッド"""
        self.project_root = project_root or Path.cwd()
        self.logger = logging.getLogger("FourSagesOverseer")
        
        # コンポーネント初期化
        self.consultation_tracker = SageConsultationTracker(project_root)
        self.activity_analyzer = SageActivityAnalyzer(project_root)
        
    async def audit(self, target_path: str, **kwargs) -> AuditResultreturn await self.execute_audit(target_path, **kwargs):
    """ncientElderBaseの抽象メソッド実装"""
        :
    def get_audit_scope(self) -> List[str]:
        """監査対象スコープを返す"""
        return [
            "sage_consultations",
            "sage_activity_quality", 
            "sage_collaboration",
            "four_sages_compliance"
        ]
        
    async def execute_audit(self, target_path: str, **kwargs) -> AuditResultstart_time = datetime.now():
    """賢者監督監査を実行"""
        violations = []
        metrics = {}
        :
        try:
            self.logger.info(f"🧙‍♂️ Starting Four Sages Overseer audit for: {target_path}")
            
            # 1.0 相談義務履行検証
            consultation_result = self.consultation_tracker.track_sage_consultations(target_path)
            violations.extend(consultation_result.get("violations", []))
            metrics["consultation_score"] = consultation_result.get("overall_consultation_score", 0)
            
            # 2.0 賢者活動実質性評価
            activity_result = self.activity_analyzer.analyze_sage_activity_quality(target_path)
            violations.extend(activity_result.get("violations", []))
            metrics["activity_score"] = activity_result.get("overall_activity_score", 0)
            
            # 3.0 総合4賢者スコア計算
            overall_score = self._calculate_overall_sage_score(metrics)
            metrics["overall_sage_score"] = overall_score
            
            # 4.0 改善提案生成
            recommendations = self._generate_sage_improvement_recommendations(
                consultation_result, activity_result, violations
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            metrics["execution_time"] = execution_time
            
            self.logger.info(f"✅ Four Sages Overseer audit completed in {execution_time:0.2f}s")
            
            return AuditResult(
                auditor_name="FourSagesOverseer",
                target_path=target_path,
                violations=violations,
                metrics=metrics,
                recommendations=recommendations,
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"❌ Four Sages Overseer audit failed: {e}")
            return AuditResult(
                auditor_name="FourSagesOverseer",
                target_path=target_path,
                violations=[{
                    "type": "AUDIT_EXECUTION_FAILURE",
                    "severity": ViolationSeverity.HIGH,
                    "description": f"Four Sages audit execution failed: {str(e)}",
                    "location": target_path
                }],
                metrics={"error": str(e)},
                recommendations=[],
                execution_time=(datetime.now() - start_time).total_seconds()
            )
            
    def _calculate_overall_sage_score(self, metrics: Dict[str, Any]) -> floatconsultation_score = metrics.get("consultation_score", 0)activity_score = metrics.get("activity_score", 0)
    """合4賢者スコアを計算"""
        
        # 相談義務 40% + 活動実質性 60%
        overall_score = (consultation_score * 0.4) + (activity_score * 0.6)
        return min(overall_score, 100.0)
        
    def _generate_sage_improvement_recommendations(self,:
                                                 consultation_result: Dict[str, Any],
                                                 activity_result: Dict[str, Any],
                                                 violations: List[Dict[str, Any]]) -> List[str]:
        """4賢者改善提案を生成"""
        recommendations = []
        
        # 相談義務改善提案
        consultation_score = consultation_result.get("overall_consultation_score", 0)
        if consultation_score < 70:
            recommendations.append(
                "Increase consultation frequency with all four sages (Knowledge, Task, " \
                    "Incident, RAG)"
            )
            
        # 活動実質性改善提案
        activity_score = activity_result.get("overall_activity_score", 0)
        if activity_score < 75:
            recommendations.append(
                "Improve sage activity quality and cross-sage collaboration"
            )
            
        # 違反固有の改善提案
        for violation in violations:
            if violation.get("type") == SageViolationType.MISSING_CONSULTATION:
                sage_type = violation.get("sage_type", "unknown")
                recommendations.append(f"Implement mandatory consultation with {sage_type} sage")
                
        return recommendations