#!/usr/bin/env python3
"""
🧙‍♂️ Four Sages Overseer Magic テストスイート
4賢者監督監査魔法の完全テスト
"""

import asyncio
import json
import logging
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

import pytest

# プロジェクトルートをパスに追加
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.four_sages_overseer import (
    FourSagesOverseer,
    SageConsultationTracker,
    SageActivityAnalyzer,
    SageType,
    SageViolationType
)
from libs.ancient_elder.base import ViolationSeverity


class TestSageConsultationTracker(unittest.TestCase):
    """4賢者相談追跡システムテスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.tracker = SageConsultationTracker(self.project_root)
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_tracker_initialization(self):
        """トラッカーの初期化テスト"""
        self.assertIsInstance(self.tracker, SageConsultationTracker)
        self.assertEqual(self.tracker.project_root, self.project_root)
        
        # 4賢者のログパスが設定されていることを確認
        self.assertIn(SageType.KNOWLEDGE, self.tracker.sage_log_paths)
        self.assertIn(SageType.TASK, self.tracker.sage_log_paths)
        self.assertIn(SageType.INCIDENT, self.tracker.sage_log_paths)
        self.assertIn(SageType.RAG, self.tracker.sage_log_paths)
        
    def test_consultation_pattern_detection(self):
        """相談パターン検出テスト"""
        test_messages = [
            ("Consult with knowledge sage for implementation", SageType.KNOWLEDGE),
            ("Task sage consultation needed", SageType.TASK),
            ("Incident sage: emergency response", SageType.INCIDENT),
            ("RAG sage search optimization", SageType.RAG),
            ("知識賢者への相談", SageType.KNOWLEDGE),
            ("タスク賢者に確認", SageType.TASK),
            ("Regular commit message", None),  # パターンなし
        ]
        
        for message, expected_sage in test_messages:
        # 繰り返し処理
            detected_sages = []
            # 繰り返し処理
            for sage_type, patterns in self.tracker.consultation_patterns.items():
                for pattern in patterns:
                    if pattern.search(message):
                        detected_sages.append(sage_type)
                        break
                        
            if expected_sage:
                self.assertIn(expected_sage, detected_sages, 
                             f"Failed to detect {expected_sage} in message: '{message}'")
            else:
                self.assertEqual(len(detected_sages), 0,
                               f"Unexpected detection in message: '{message}'")
                
    @patch('subprocess.run')
    def test_consultation_records_retrieval(self, mock_subprocess):
        """相談記録取得テスト"""
        mock_subprocess.return_value.stdout = """abc123|2025-01-20 10:00:00|Knowledge sage consultation for auth|dev
def456|2025-01-20 11:00:00|Task sage: priority update|dev
ghi789|2025-01-20 12:00:00|Regular feature implementation|dev"""
        
        records = self.tracker._get_consultation_records("test.py", timedelta(days=7))
        
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["hash"], "abc123")
        self.assertEqual(records[0]["message"], "Knowledge sage consultation for auth")
        
    def test_consultation_analysis(self):
        """相談分析テスト"""
        mock_records = [
            {"hash": "abc", "date": "2025-01-20", "message": "Knowledge sage consultation", "author": "dev"},
            {"hash": "def", "date": "2025-01-20", "message": "Task sage priority", "author": "dev"},
            {"hash": "ghi", "date": "2025-01-21", "message": "RAG sage search", "author": "dev"},
        ]
        
        analysis = self.tracker._analyze_consultation_patterns(mock_records)
        
        # 各賢者の分析結果を確認
        self.assertIn(SageType.KNOWLEDGE, analysis)
        self.assertIn(SageType.TASK, analysis)
        self.assertIn(SageType.RAG, analysis)
        
        # Knowledge賢者の相談が検出されることを確認
        knowledge_analysis = analysis[SageType.KNOWLEDGE]
        self.assertGreater(knowledge_analysis["consultation_count"], 0)
        self.assertIsNotNone(knowledge_analysis["last_consultation"])
        
    def test_consultation_violation_detection(self):
        """相談義務違反検出テスト"""
        # 不十分な相談のケース
        insufficient_analysis = {
            SageType.KNOWLEDGE: {"consultation_count": 0},
            SageType.TASK: {"consultation_count": 1},
            SageType.INCIDENT: {"consultation_count": 0},
            SageType.RAG: {"consultation_count": 0}
        }
        
        violations = self.tracker._detect_consultation_violations(insufficient_analysis, "test.py")
        
        # Knowledge, RAG賢者への相談不足が検出されることを確認
        violation_types = [v["sage_type"] for v in violations]
        self.assertIn(SageType.KNOWLEDGE, violation_types)
        self.assertIn(SageType.RAG, violation_types)
        
        # 十分な相談のケース
        sufficient_analysis = {
            SageType.KNOWLEDGE: {"consultation_count": 2},
            SageType.TASK: {"consultation_count": 1},
            SageType.INCIDENT: {"consultation_count": 0},  # 必須でない
            SageType.RAG: {"consultation_count": 1}
        }
        
        violations = self.tracker._detect_consultation_violations(sufficient_analysis, "test.py")
        self.assertEqual(len(violations), 0, "No violations should be detected for sufficient consultations")
        
    def test_consultation_score_calculation(self):
        """相談スコア計算テスト"""
        # 高スコアケース
        high_score_analysis = {
            SageType.KNOWLEDGE: {"consultation_count": 3},
            SageType.TASK: {"consultation_count": 2},
            SageType.INCIDENT: {"consultation_count": 1},
            SageType.RAG: {"consultation_count": 2}
        }
        
        score = self.tracker._calculate_consultation_score(high_score_analysis)
        self.assertGreaterEqual(score, 65.0, "High consultation activity should yield high score")
        
        # 低スコアケース
        low_score_analysis = {
            SageType.KNOWLEDGE: {"consultation_count": 0},
            SageType.TASK: {"consultation_count": 0},
            SageType.INCIDENT: {"consultation_count": 0},
            SageType.RAG: {"consultation_count": 0}
        }
        
        score = self.tracker._calculate_consultation_score(low_score_analysis)
        self.assertEqual(score, 0.0, "No consultations should yield zero score")


class TestSageActivityAnalyzer(unittest.TestCase):
    """4賢者活動実質性評価システムテスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.analyzer = SageActivityAnalyzer(self.project_root)
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_analyzer_initialization(self):
        """アナライザーの初期化テスト"""
        self.assertIsInstance(self.analyzer, SageActivityAnalyzer)
        self.assertEqual(self.analyzer.project_root, self.project_root)
        
    def test_individual_sage_activities_analysis(self):
        """個別賢者活動分析テスト"""
        time_window = timedelta(days=30)
        activities = self.analyzer._analyze_individual_sage_activities(time_window)
        
        # 全4賢者の活動分析が含まれることを確認
        self.assertIn(SageType.KNOWLEDGE, activities)
        self.assertIn(SageType.TASK, activities)
        self.assertIn(SageType.INCIDENT, activities)
        self.assertIn(SageType.RAG, activities)
        
        # 各賢者の活動指標が含まれることを確認
        for sage_type, activity in activities.items():
            self.assertIn("activity_count", activity)
            self.assertIn("quality_score", activity)
            self.assertIn("responsiveness", activity)
            self.assertIn("expertise_demonstration", activity)
            
    def test_sage_collaboration_analysis(self):
        """賢者間連携分析テスト"""
        time_window = timedelta(days=30)
        collaboration = self.analyzer._analyze_sage_collaboration(time_window)
        
        self.assertIn("collaboration_frequency", collaboration)
        self.assertIn("collaboration_patterns", collaboration)
        self.assertIn("cross_sage_consultations", collaboration)
        self.assertIn("collaborative_problem_solving", collaboration)
        
        # 連携パターンがリストであることを確認
        self.assertIsInstance(collaboration["collaboration_patterns"], list)
        
    def test_activity_violation_detection(self):
        """活動違反検出テスト"""
        # 活動不足のケース
        insufficient_activity = {
            SageType.KNOWLEDGE: {"activity_count": 1, "quality_score": 50},
            SageType.TASK: {"activity_count": 2, "quality_score": 60},
            SageType.INCIDENT: {"activity_count": 0, "quality_score": 0},
            SageType.RAG: {"activity_count": 1, "quality_score": 55}
        }
        
        insufficient_collaboration = {
            "collaboration_frequency": 1,
            "cross_sage_consultations": 2
        }
        
        violations = self.analyzer._detect_activity_violations(
            insufficient_activity, insufficient_collaboration, "test.py"
        )
        
        # 活動不足違反が検出されることを確認
        activity_violations = [v for v in violations if v["type"] == SageViolationType.INSUFFICIENT_SAGE_ACTIVITY]
        self.assertGreater(len(activity_violations), 0, "Should detect insufficient activity violations")
        
        # 連携不足違反が検出されることを確認
        collaboration_violations = [v for v in violations if v["type"] == SageViolationType.POOR_SAGE_COLLABORATION]
        self.assertGreater(len(collaboration_violations), 0, "Should detect poor collaboration violations")
        
    def test_activity_score_calculation(self):
        """活動スコア計算テスト"""
        # 高品質活動ケース
        high_quality_activity = {
            SageType.KNOWLEDGE: {"quality_score": 90},
            SageType.TASK: {"quality_score": 85},
            SageType.INCIDENT: {"quality_score": 80},
            SageType.RAG: {"quality_score": 88}
        }
        
        high_collaboration = {"collaborative_problem_solving": 95}
        
        score = self.analyzer._calculate_activity_score(high_quality_activity, high_collaboration)
        self.assertGreaterEqual(score, 85.0, "High quality activities should yield high score")
        
        # 低品質活動ケース
        low_quality_activity = {
            SageType.KNOWLEDGE: {"quality_score": 40},
            SageType.TASK: {"quality_score": 35},
            SageType.INCIDENT: {"quality_score": 30},
            SageType.RAG: {"quality_score": 38}
        }
        
        low_collaboration = {"collaborative_problem_solving": 25}
        
        score = self.analyzer._calculate_activity_score(low_quality_activity, low_collaboration)
        self.assertLessEqual(score, 50.0, "Low quality activities should yield low score")


class TestFourSagesOverseer(unittest.TestCase):
    """4賢者監督魔法総合テスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.overseer = FourSagesOverseer(self.project_root)
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_overseer_initialization(self):
        """オーバーシーアの初期化テスト"""
        self.assertIsInstance(self.overseer, FourSagesOverseer)
        self.assertEqual(self.overseer.project_root, self.project_root)
        self.assertIsInstance(self.overseer.consultation_tracker, SageConsultationTracker)
        self.assertIsInstance(self.overseer.activity_analyzer, SageActivityAnalyzer)
        
    @patch.object(SageConsultationTracker, 'track_sage_consultations')
    @patch.object(SageActivityAnalyzer, 'analyze_sage_activity_quality')
    async def test_execute_audit_success(self, mock_activity_analyzer, mock_consultation_tracker):
        """監査実行成功テスト"""
        # モックレスポンス設定
        mock_consultation_tracker.return_value = {
            "violations": [],
            "overall_consultation_score": 85.0
        }
        
        mock_activity_analyzer.return_value = {
            "violations": [],
            "overall_activity_score": 90.0
        }
        
        result = await self.overseer.execute_audit("test.py")
        
        self.assertEqual(result.auditor_name, "FourSagesOverseer")
        self.assertEqual(result.target_path, "test.py")
        self.assertIsInstance(result.violations, list)
        self.assertIsInstance(result.metrics, dict)
        self.assertIn("overall_sage_score", result.metrics)
        self.assertGreater(result.metrics["overall_sage_score"], 80.0)
        
    @patch.object(SageConsultationTracker, 'track_sage_consultations')
    @patch.object(SageActivityAnalyzer, 'analyze_sage_activity_quality')
    async def test_execute_audit_with_violations(self, mock_activity_analyzer, mock_consultation_tracker):
        """違反検出時の監査実行テスト"""
        # 違反を含むモックレスポンス設定
        mock_consultation_tracker.return_value = {
            "violations": [
                {
                    "type": SageViolationType.MISSING_CONSULTATION,
                    "severity": "HIGH",
                    "sage_type": SageType.KNOWLEDGE,
                    "description": "Missing knowledge sage consultation"
                }
            ],
            "overall_consultation_score": 40.0
        }
        
        mock_activity_analyzer.return_value = {
            "violations": [
                {
                    "type": SageViolationType.INSUFFICIENT_SAGE_ACTIVITY,
                    "severity": "MEDIUM",
                    "sage_type": SageType.RAG,
                    "description": "Insufficient RAG sage activity"
                }
            ],
            "overall_activity_score": 55.0
        }
        
        result = await self.overseer.execute_audit("test.py")
        
        # 違反が適切に統合されることを確認
        self.assertEqual(len(result.violations), 2)
        self.assertLessEqual(result.metrics["overall_sage_score"], 50.0)
        
    def test_overall_sage_score_calculation(self):
        """総合4賢者スコア計算テスト"""
        # 高スコアケース
        high_metrics = {
            "consultation_score": 90.0,
            "activity_score": 85.0
        }
        
        score = self.overseer._calculate_overall_sage_score(high_metrics)
        expected_score = (90.0 * 0.4) + (85.0 * 0.6)  # 87.0
        self.assertAlmostEqual(score, expected_score, places=1)
        
        # 低スコアケース
        low_metrics = {
            "consultation_score": 30.0,
            "activity_score": 40.0
        }
        
        score = self.overseer._calculate_overall_sage_score(low_metrics)
        expected_score = (30.0 * 0.4) + (40.0 * 0.6)  # 36.0
        self.assertAlmostEqual(score, expected_score, places=1)
        
    def test_sage_improvement_recommendations(self):
        """4賢者改善提案生成テスト"""
        consultation_result = {"overall_consultation_score": 60.0}
        activity_result = {"overall_activity_score": 70.0}
        violations = [
            {
                "type": SageViolationType.MISSING_CONSULTATION,
                "sage_type": SageType.KNOWLEDGE
            }
        ]
        
        recommendations = self.overseer._generate_sage_improvement_recommendations(
            consultation_result, activity_result, violations
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0, "Should generate improvement recommendations")
        
        # 相談頻度向上の提案が含まれることを確認
        consultation_recommendations = [r for r in recommendations if "consultation" in r.lower()]
        self.assertGreater(len(consultation_recommendations), 0)


class TestFourSagesOverseerIntegration(unittest.TestCase):
    """4賢者監督魔法統合テスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.overseer = FourSagesOverseer(self.project_root)
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    async def test_comprehensive_sage_audit(self):
        """包括的4賢者監査テスト"""
        # テストファイル作成
        test_file = self.project_root / "test_module.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("""
def process_data():
    # TODO: Implement knowledge sage consultation
    pass

def manage_tasks():
    # Missing task sage consultation
    pass
""")
        
        # 統合監査実行
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.stdout = "abc123|2025-01-20|Basic implementation|dev"
            
            result = await self.overseer.execute_audit(str(test_file))
            
        # 結果検証
        self.assertEqual(result.auditor_name, "FourSagesOverseer")
        self.assertIsInstance(result.violations, list)
        self.assertIsInstance(result.metrics, dict)
        self.assertIn("overall_sage_score", result.metrics)
        self.assertIsInstance(result.recommendations, list)
        
    async def test_sage_collaboration_assessment(self):
        """賢者連携評価テスト"""
        test_path = "collaborative_module.py"
        
        # 連携不足のシナリオをテスト
        with patch.object(self.overseer.consultation_tracker, 'track_sage_consultations') as mock_consultation:
            with patch.object(self.overseer.activity_analyzer, 'analyze_sage_activity_quality') as mock_activity:
                pass
                
                # 連携不足のレスポンス設定
                mock_consultation.return_value = {
                    "violations": [],
                    "overall_consultation_score": 50.0
                }
                
                mock_activity.return_value = {
                    "violations": [
                        {
                            "type": SageViolationType.POOR_SAGE_COLLABORATION,
                            "severity": "HIGH",
                            "description": "Poor sage collaboration detected"
                        }
                    ],
                    "overall_activity_score": 45.0
                }
                
                result = await self.overseer.execute_audit(test_path)
                
                # 連携不足が検出されることを確認
                collaboration_violations = [
                    v for v in result.violations 
                    if v.get("type") == SageViolationType.POOR_SAGE_COLLABORATION
                ]
                self.assertGreater(len(collaboration_violations), 0)
                
                # 改善提案が生成されることを確認
                self.assertGreater(len(result.recommendations), 0)


if __name__ == "__main__":
    # 基本テスト実行
    unittest.main(verbosity=2)