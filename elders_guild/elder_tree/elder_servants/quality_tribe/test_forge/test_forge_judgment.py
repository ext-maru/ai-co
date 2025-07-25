"""
TestForge Judgment System - 🔨 テスト自動化サーバント判定システム

Issue #309: 自動化品質パイプライン実装 - Phase 2
担当サーバント: 🔨 TestForge (D14)

目的: TestAutomationEngine結果の専門判定・TDD品質評価
方針: Execute & Judge パターン - テスト戦略最適性判定に特化
"""

import asyncio
import time
import logging
import json
import uuid
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

from elders_guild.elder_tree.quality.test_automation_engine import TestExecutionResult


@dataclass
class TestQualityJudgmentResult:
    """テスト品質判定結果"""
    judgment_id: str
    overall_decision: str  # "ELDER_APPROVED" | "ELDER_CONDITIONAL" | "ELDER_REJECTED"  
    tdd_quality_score: float  # 90点以上でElder承認
    coverage_judgment: str  # "EXCELLENT" | "GOOD" | "INSUFFICIENT"
    test_architecture_score: float
    judgment_reasoning: List[str]
    improvement_recommendations: List[str]
    elder_council_report: Dict[str, Any]
    certification_level: Optional[str]
    next_review_required: bool
    judgment_timestamp: str


@dataclass
class TestArchitectureJudgment:
    """テストアーキテクチャ専門判定"""
    coverage_judgment: str      # "EXCELLENT" | "GOOD" | "INSUFFICIENT"
    test_quality_judgment: str  # "EXCEPTIONAL" | "SOLID" | "BASIC" | "POOR"
    tdd_compliance_judgment: str # "PERFECT" | "GOOD" | "PARTIAL" | "ABSENT"
    property_test_coverage: float  # 0-100%
    multi_env_compatibility: str  # "FULL" | "PARTIAL" | "NONE"
    auto_generation_effectiveness: float
    elder_recommendation: str


class TestForgeJudgment:
    """
    TestForge テスト品質判定システム
    
    専門領域: テスト自動化・TDD実行・カバレッジ分析
    判定能力: テスト品質評価・テスト戦略最適化
    責任範囲: TDD完全サイクル管理・Elder承認判断
    """
    
    def __init__(self):
        self.servant_id = "TestForge-D14"
        self.logger = self._setup_logger()
        
        # Elder承認判定基準
        self.judgment_thresholds = {
            "elder_approval_minimum": 90.0,
            "coverage_excellent": 95.0,
            "coverage_good": 85.0,
            "test_pass_rate_minimum": 95.0,
            "tdd_compliance_minimum": 85.0,
            "property_test_minimum": 70.0,
        }
        
        # TDD品質基準
        self.tdd_standards = {
            "red_green_refactor_cycle": True,
            "test_first_development": True,
            "comprehensive_coverage": True,
            "property_based_testing": True,
            "multi_environment_testing": True,
        }
        
        # テスト履歴ストレージ（簡易実装）
        self.test_history = {}
        self.judgment_cache = {}
        
        # 認定レベル基準
        self.certification_levels = {
            95.0: "TDD_MASTER",
            90.0: "TDD_EXPERT",
            85.0: "TDD_CERTIFIED",
        }
    
    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("test_forge_judgment")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def judge_test_automation_quality(
        self, 
        test_result: TestExecutionResult,
        target_path: str
    ) -> TestQualityJudgmentResult:
        """
        テスト自動化品質の専門判定
        
        Args:
            test_result: TestAutomationEngine実行結果
            target_path: テスト対象パス
            
        Returns:
            TestQualityJudgmentResult: 専門判定結果
        """
        judgment_id = f"TF-{uuid.uuid4().hex[:8].upper()}"
        self.logger.info(f"🔨 Starting test quality judgment: {judgment_id}")
        
        try:
            # Phase 1: 詳細テストアーキテクチャ判定
            architecture_judgment = await self._analyze_test_architecture_details(test_result)
            
            # Phase 2: TDD遵守評価
            tdd_compliance = await self._assess_tdd_compliance(test_result)
            
            # Phase 3: カバレッジ品質分析
            coverage_judgment = self._analyze_coverage_quality(
                test_result.coverage_percentage, 
                test_result.uncovered_lines
            )
            
            # Phase 4: プロパティベーステスト評価
            property_evaluation = await self._evaluate_property_based_testing(
                test_result.property_test_results
            )
            
            # Phase 5: マルチ環境互換性評価
            multi_env_assessment = await self._assess_multi_environment_compatibility(
                test_result.multi_env_results
            )
            
            # Phase 6: 自動テスト生成効果評価
            auto_gen_effectiveness = self._evaluate_auto_test_generation_effectiveness(
                test_result.auto_generated_tests,
                test_result.coverage_percentage
            )
            
            # Phase 7: テスト品質トレンド分析
            historical_data = await self._get_test_history(target_path)
            trend_analysis = await self._analyze_test_quality_trends(target_path, historical_data)
            
            # Phase 8: TDD品質スコア算出
            tdd_quality_score = self._calculate_tdd_quality_score(test_result)
            
            # Phase 9: テストアーキテクチャスコア算出
            architecture_score = self._calculate_test_architecture_score(
                architecture_judgment, coverage_judgment, property_evaluation, multi_env_assessment
            )
            
            # Phase 10: Elder承認判断
            overall_decision = self._make_elder_test_approval_decision(
                tdd_quality_score, test_result, tdd_compliance
            )
            
            # Phase 11: 判定根拠生成
            reasoning = self._generate_test_judgment_reasoning(
                test_result, architecture_judgment, tdd_quality_score, overall_decision
            )
            
            # Phase 12: テスト戦略改善推奨事項生成（必要時）
            recommendations = []
            if overall_decision != "ELDER_APPROVED":
                recommendations = await self._generate_test_strategy_recommendations(test_result)
            
            # Phase 13: 認定レベル決定
            certification_level = self._determine_test_certification_level(tdd_quality_score)
            
            # Phase 14: Elder Council報告書生成
            elder_report = self._generate_elder_council_test_report(
                judgment_id, test_result, tdd_quality_score, overall_decision, reasoning
            )
            
            # 判定結果構築
            judgment_result = TestQualityJudgmentResult(
                judgment_id=judgment_id,
                overall_decision=overall_decision,
                tdd_quality_score=tdd_quality_score,
                coverage_judgment=coverage_judgment,
                test_architecture_score=architecture_score,
                judgment_reasoning=reasoning,
                improvement_recommendations=recommendations,
                elder_council_report=elder_report,
                certification_level=certification_level,
                next_review_required=(overall_decision != "ELDER_APPROVED"),
                judgment_timestamp=datetime.now().isoformat()
            )
            
            # 判定結果永続化
            await self._persist_test_judgment(judgment_result)
            
            # テスト履歴更新
            await self._update_test_history(target_path, test_result, tdd_quality_score)
            
            self.logger.info(f"✅ Test quality judgment completed: {overall_decision} ({tdd_quality_score:.1f})")
            return judgment_result
        
        except Exception as e:
            self.logger.error(f"❌ Test quality judgment error: {e}", exc_info=True)
            # エラー時のフォールバック判定
            return TestQualityJudgmentResult(
                judgment_id=judgment_id,
                overall_decision="ELDER_REJECTED",
                tdd_quality_score=0.0,
                coverage_judgment="INSUFFICIENT",
                test_architecture_score=0.0,
                judgment_reasoning=[f"Test judgment system error: {str(e)}"],
                improvement_recommendations=["Fix test judgment system issues"],
                elder_council_report={"error": str(e)},
                certification_level=None,
                next_review_required=True,
                judgment_timestamp=datetime.now().isoformat()
            )
    
    async def _analyze_test_architecture_details(
        self, 
        test_result: TestExecutionResult
    ) -> TestArchitectureJudgment:
        """詳細テストアーキテクチャ判定"""
        # カバレッジ判定
        coverage_judgment = self._analyze_coverage_quality(
            test_result.coverage_percentage, 
            test_result.uncovered_lines
        )
        
        # テスト品質判定
        if test_result.test_results.all_passed and test_result.test_results.test_count >= 20:
            if test_result.coverage_percentage >= 95.0:
                test_quality_judgment = "EXCEPTIONAL"
            else:
                test_quality_judgment = "SOLID"
        elif test_result.test_results.all_passed and test_result.test_results.test_count >= 10:
            test_quality_judgment = "SOLID"
        elif test_result.test_results.test_count >= 5:
            test_quality_judgment = "BASIC"
        else:
            test_quality_judgment = "POOR"
        
        # TDD遵守判定
        if test_result.status == "COMPLETED" and test_result.coverage_percentage >= 95.0:
            if test_result.test_results.all_passed:
                tdd_compliance_judgment = "PERFECT"
            else:
                tdd_compliance_judgment = "GOOD"
        elif test_result.coverage_percentage >= 80.0:
            tdd_compliance_judgment = "PARTIAL"
        else:
            tdd_compliance_judgment = "ABSENT"
        
        # プロパティテストカバレッジ
        property_test_coverage = min(100.0, len(test_result.property_test_results.passed_properties) * 25.0)
        
        # マルチ環境互換性
        if test_result.multi_env_results and test_result.multi_env_results.all_passed:
            multi_env_compatibility = "FULL"
        elif test_result.multi_env_results and len(test_result.multi_env_results.environments) > 0:
            multi_env_compatibility = "PARTIAL"
        else:
            multi_env_compatibility = "NONE"
        
        # 自動生成効果性
        auto_generation_effectiveness = min(100.0, test_result.auto_generated_tests * 20.0)
        
        # Elder推奨決定
        if (test_quality_judgment == "EXCEPTIONAL" and 
            tdd_compliance_judgment == "PERFECT" and
            coverage_judgment == "EXCELLENT"):
            elder_recommendation = "STRONGLY_RECOMMENDED"
        elif (test_quality_judgment in ["EXCEPTIONAL", "SOLID"] and 
              tdd_compliance_judgment in ["PERFECT", "GOOD"]):
            elder_recommendation = "RECOMMENDED"
        else:
            elder_recommendation = "REQUIRES_IMPROVEMENT"
        
        return TestArchitectureJudgment(
            coverage_judgment=coverage_judgment,
            test_quality_judgment=test_quality_judgment,
            tdd_compliance_judgment=tdd_compliance_judgment,
            property_test_coverage=property_test_coverage,
            multi_env_compatibility=multi_env_compatibility,
            auto_generation_effectiveness=auto_generation_effectiveness,
            elder_recommendation=elder_recommendation
        )
    
    def _analyze_coverage_quality(
        self, 
        coverage_percentage: float, 
        uncovered_lines: List[int]
    ) -> str:
        """カバレッジ品質分析"""
        if coverage_percentage >= self.judgment_thresholds["coverage_excellent"]:
            return "EXCELLENT"
        elif coverage_percentage >= self.judgment_thresholds["coverage_good"]:
            return "GOOD"
        else:
            return "INSUFFICIENT"
    
    async def _assess_tdd_compliance(
        self, 
        test_result: TestExecutionResult
    ) -> Dict[str, Any]:
        """TDD遵守評価"""
        violations = []
        compliance_areas = {
            "test_first_development": test_result.test_results.test_count > 0,
            "comprehensive_coverage": test_result.coverage_percentage >= 90.0,
            "all_tests_passing": test_result.test_results.all_passed,
            "property_based_testing": len(test_result.property_test_results.passed_properties) > 0,
            "multi_environment_testing": (
                test_result.multi_env_results and test_result.multi_env_results.all_passed
            ) if test_result.multi_env_results else False,
        }
        
        # 違反チェック
        if not compliance_areas["test_first_development"]:
            violations.append("No tests found - TDD requires test-first development")
        
        if not compliance_areas["comprehensive_coverage"]:
            violations.append(f"Coverage {test_result.coverage_percentage}% below 90% TDD standard")
        
        if not compliance_areas["all_tests_passing"]:
            violations.append(f"{test_result.test_results.failed_count} failing tests violate TDD green phase")
        
        if not compliance_areas["property_based_testing"]:
            violations.append("No property-based tests found")
        
        if not compliance_areas["multi_environment_testing"]:
            violations.append("Multi-environment testing not implemented")
        
        # 遵守度計算
        compliance_score = sum(compliance_areas.values()) / len(compliance_areas) * 100.0
        overall_compliance = compliance_score >= self.judgment_thresholds["tdd_compliance_minimum"]
        
        return {
            "overall_compliance": overall_compliance,
            "compliance_score": compliance_score,
            "tdd_violations": violations,
            "compliance_areas": compliance_areas
        }
    
    async def _evaluate_property_based_testing(
        self, 
        property_test_results
    ) -> Dict[str, Any]:
        """プロパティベーステスト評価"""
        passed_count = len(property_test_results.passed_properties)
        failed_count = len(property_test_results.failed_properties)
        total_count = passed_count + failed_count
        
        if total_count == 0:
            quality_grade = "F"
            coverage_percentage = 0.0
            effectiveness_score = 0.0
        else:
            pass_rate = passed_count / total_count * 100.0
            
            if pass_rate >= 95.0 and passed_count >= 5:
                quality_grade = "A+"
            elif pass_rate >= 90.0 and passed_count >= 3:
                quality_grade = "A"
            elif pass_rate >= 80.0 and passed_count >= 2:
                quality_grade = "B"
            elif pass_rate >= 70.0:
                quality_grade = "C"
            elif pass_rate >= 50.0:
                quality_grade = "D"
            else:
                quality_grade = "F"
            
            coverage_percentage = min(100.0, passed_count * 20.0)
            effectiveness_score = (pass_rate + coverage_percentage) / 2.0
        
        recommendations = []
        if quality_grade in ["C", "D", "F"]:
            recommendations.extend([
                "Implement more property-based tests",
                "Focus on edge cases and invariants",
                "Use hypothesis library for automated test generation"
            ])
        
        return {
            "quality_grade": quality_grade,
            "coverage_percentage": coverage_percentage,
            "effectiveness_score": effectiveness_score,
            "recommendations": recommendations
        }
    
    async def _assess_multi_environment_compatibility(
        self, 
        multi_env_results
    ) -> Dict[str, Any]:
        """マルチ環境互換性評価"""
        if not multi_env_results:
            return {
                "compatibility_level": "NONE",
                "supported_environments": [],
                "failed_environments": [],
                "compatibility_score": 0.0
            }
        
        supported_envs = [env for env, status in multi_env_results.environments.items() if status]
        failed_envs = multi_env_results.failed_environments
        total_envs = len(multi_env_results.environments)
        
        if len(failed_envs) == 0 and total_envs >= 2:
            compatibility_level = "FULL"
        elif len(supported_envs) > 0:
            compatibility_level = "PARTIAL"
        else:
            compatibility_level = "NONE"
        
        compatibility_score = (len(supported_envs) / total_envs * 100.0) if total_envs > 0 else 0.0
        
        return {
            "compatibility_level": compatibility_level,
            "supported_environments": supported_envs,
            "failed_environments": failed_envs,
            "compatibility_score": compatibility_score
        }
    
    def _evaluate_auto_test_generation_effectiveness(
        self, 
        auto_generated_tests: int,
        coverage_percentage: float
    ) -> Dict[str, Any]:
        """自動テスト生成効果評価"""
        if auto_generated_tests == 0:
            effectiveness_score = 0.0
            generation_quality = "NONE"
            coverage_improvement = 0.0
        else:
            # 生成されたテスト数に基づく効果スコア
            effectiveness_score = min(100.0, auto_generated_tests * 15.0)
            
            if auto_generated_tests >= 5:
                generation_quality = "EXCELLENT"
            elif auto_generated_tests >= 3:
                generation_quality = "GOOD"
            elif auto_generated_tests >= 1:
                generation_quality = "BASIC"
            else:
                generation_quality = "NONE"
            
            # カバレッジ改善推定（簡易）
            coverage_improvement = min(10.0, auto_generated_tests * 2.0)
        
        return {
            "effectiveness_score": effectiveness_score,
            "generation_quality": generation_quality,
            "coverage_improvement": coverage_improvement
        }
    
    def _calculate_tdd_quality_score(self, test_result: TestExecutionResult) -> float:
        """TDD品質スコア算出"""
        # ベーススコア（カバレッジベース）
        coverage_score = test_result.coverage_percentage * 0.4  # 40点満点
        
        # テスト合格率スコア
        if test_result.test_results.test_count > 0:
            pass_rate = test_result.test_results.passed_count / test_result.test_results.test_count
            test_score = pass_rate * 30.0  # 30点満点
        else:
            test_score = 0.0
        
        # プロパティテストスコア
        property_score = min(15.0, len(test_result.property_test_results.passed_properties) * 3.0)
        
        # マルチ環境テストスコア
        if test_result.multi_env_results and test_result.multi_env_results.all_passed:
            multi_env_score = 10.0
        elif test_result.multi_env_results:
            multi_env_score = 5.0
        else:
            multi_env_score = 0.0
        
        # 自動生成テストボーナス
        auto_gen_bonus = min(5.0, test_result.auto_generated_tests * 1.0)
        
        # 実行完了ボーナス/ペナルティ
        if test_result.status == "COMPLETED":
            completion_bonus = 0.0  # ベースライン
        elif test_result.status == "MAX_ITERATIONS_EXCEEDED":
            completion_bonus = -5.0
        else:
            completion_bonus = -10.0
        
        # 総合スコア計算
        total_score = (
            coverage_score + 
            test_score + 
            property_score + 
            multi_env_score + 
            auto_gen_bonus + 
            completion_bonus
        )
        
        return max(0.0, min(100.0, total_score))
    
    def _calculate_test_architecture_score(
        self,
        architecture_judgment: TestArchitectureJudgment,
        coverage_judgment: str,
        property_evaluation: Dict[str, Any],
        multi_env_assessment: Dict[str, Any]
    ) -> float:
        """テストアーキテクチャスコア算出"""
        # カバレッジスコア
        coverage_scores = {"EXCELLENT": 30.0, "GOOD": 20.0, "INSUFFICIENT": 10.0}
        coverage_score = coverage_scores.get(coverage_judgment, 0.0)
        
        # テスト品質スコア
        quality_scores = {"EXCEPTIONAL": 25.0, "SOLID": 20.0, "BASIC": 15.0, "POOR": 5.0}
        quality_score = quality_scores.get(architecture_judgment.test_quality_judgment, 0.0)
        
        # TDD遵守スコア
        tdd_scores = {"PERFECT": 20.0, "GOOD": 15.0, "PARTIAL": 10.0, "ABSENT": 0.0}
        tdd_score = tdd_scores.get(architecture_judgment.tdd_compliance_judgment, 0.0)
        
        # プロパティテストスコア
        property_score = property_evaluation["effectiveness_score"] * 0.15  # 15点満点
        
        # マルチ環境スコア
        multi_env_score = multi_env_assessment["compatibility_score"] * 0.1  # 10点満点
        
        total_score = coverage_score + quality_score + tdd_score + property_score + multi_env_score
        return max(0.0, min(100.0, total_score))
    
    def _make_elder_test_approval_decision(
        self,
        tdd_quality_score: float,
        test_result: TestExecutionResult,
        tdd_compliance: Dict[str, Any]
    ) -> str:
        """Elder承認判断"""
        # 絶対基準チェック
        if tdd_quality_score >= self.judgment_thresholds["elder_approval_minimum"]:
            if tdd_compliance["overall_compliance"]:
                if test_result.test_results.all_passed:
                    if test_result.coverage_percentage >= 95.0:
                        return "ELDER_APPROVED"
        
        # 条件付き承認判断
        if tdd_quality_score >= 80.0:
            if test_result.test_results.all_passed:
                if test_result.coverage_percentage >= 85.0:
                    return "ELDER_CONDITIONAL"
        
        # それ以外は拒否
        return "ELDER_REJECTED"
    
    def _generate_test_judgment_reasoning(
        self,
        test_result: TestExecutionResult,
        architecture_judgment: TestArchitectureJudgment,
        tdd_quality_score: float,
        overall_decision: str
    ) -> List[str]:
        """テスト判定根拠生成"""
        reasoning = []
        
        # TDDスコア根拠
        reasoning.append(f"TDD quality score: {tdd_quality_score:.1f}/100")
        reasoning.append(f"Test coverage: {test_result.coverage_percentage:.1f}% ({architecture_judgment.coverage_judgment})")
        reasoning.append(f"Test architecture: {architecture_judgment.test_quality_judgment}")
        reasoning.append(f"TDD compliance: {architecture_judgment.tdd_compliance_judgment}")
        
        # テスト実行状況
        reasoning.append(f"Tests: {test_result.test_results.passed_count}/{test_result.test_results.test_count} passed")
        if test_result.auto_generated_tests > 0:
            reasoning.append(f"Auto-generated tests: {test_result.auto_generated_tests}")
        
        # プロパティテスト
        if test_result.property_test_results.passed_properties:
            reasoning.append(f"Property tests: {len(test_result.property_test_results.passed_properties)} passed")
        
        # 決定根拠
        if overall_decision == "ELDER_APPROVED":
            reasoning.append("✅ Meets all Elder Council TDD standards")
        elif overall_decision == "ELDER_CONDITIONAL":
            reasoning.append("⚠️ Meets basic TDD standards but requires monitoring")
        else:
            reasoning.append("❌ Does not meet Elder Council minimum TDD standards")
        
        return reasoning
    
    async def _generate_test_strategy_recommendations(
        self, 
        test_result: TestExecutionResult
    ) -> List[str]:
        """テスト戦略改善推奨事項生成"""
        recommendations = []
        
        # カバレッジ改善
        if test_result.coverage_percentage < 95.0:
            recommendations.append({
                "priority": "HIGH",
                "category": "COVERAGE",
                "description": f"Increase test coverage from {test_result.coverage_percentage:.1f}% to 95%+",
                "expected_impact": "TDD score increase +10-20 points",
                "implementation_effort": "2-4 hours"
            })
        
        # 失敗テスト修正
        if test_result.test_results.failed_count > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "TEST_QUALITY",
                "description": f"Fix {test_result.test_results.failed_count} failing tests",
                "expected_impact": "TDD score increase +15-25 points",
                "implementation_effort": "1-3 hours"
            })
        
        # プロパティテスト追加
        if len(test_result.property_test_results.passed_properties) == 0:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "TDD_COMPLIANCE",
                "description": "Implement property-based testing with hypothesis",
                "expected_impact": "TDD score increase +10-15 points",
                "implementation_effort": "2-3 hours"
            })
        
        # マルチ環境テスト
        if not test_result.multi_env_results or not test_result.multi_env_results.all_passed:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "TDD_COMPLIANCE",
                "description": "Implement multi-environment testing with tox",
                "expected_impact": "TDD score increase +5-10 points",
                "implementation_effort": "1-2 hours"
            })
        
        # 実行完了改善
        if test_result.status != "COMPLETED":
            recommendations.append({
                "priority": "HIGH",
                "category": "EXECUTION",
                "description": "Ensure test automation pipeline completes successfully",
                "expected_impact": "TDD score increase +10-15 points",
                "implementation_effort": "Variable"
            })
        
        return recommendations
    
    def _determine_test_certification_level(self, tdd_quality_score: float) -> Optional[str]:
        """テスト認定レベル決定"""
        for threshold, level in sorted(self.certification_levels.items(), reverse=True):
            if tdd_quality_score >= threshold:
                return level
        return None
    
    def _generate_elder_council_test_report(
        self,
        judgment_id: str,
        test_result: TestExecutionResult,
        tdd_quality_score: float,
        overall_decision: str,
        reasoning: List[str]
    ) -> Dict[str, Any]:
        """Elder Council テスト報告書生成"""
        return {
            "servant_identity": "TestForge (D14)",
            "judgment_id": judgment_id,
            "timestamp": datetime.now().isoformat(),
            "test_assessment_summary": {
                "decision": overall_decision,
                "tdd_quality_score": tdd_quality_score,
                "confidence_level": "HIGH" if tdd_quality_score > 85 else "MEDIUM"
            },
            "tdd_compliance_evaluation": {
                "coverage_percentage": test_result.coverage_percentage,
                "test_pass_rate": (
                    test_result.test_results.passed_count / test_result.test_results.test_count * 100.0
                ) if test_result.test_results.test_count > 0 else 0.0,
                "property_tests": len(test_result.property_test_results.passed_properties),
                "multi_env_support": test_result.multi_env_results.all_passed if test_result.multi_env_results else False
            },
            "coverage_analysis": {
                "percentage": test_result.coverage_percentage,
                "uncovered_lines": len(test_result.uncovered_lines),
                "auto_generated_tests": test_result.auto_generated_tests,
                "coverage_judgment": self._analyze_coverage_quality(test_result.coverage_percentage, test_result.uncovered_lines)
            },
            "quality_certification": {
                "approval_level": overall_decision,
                "certification_eligible": tdd_quality_score >= 90.0,
                "monitoring_required": overall_decision != "ELDER_APPROVED"
            },
            "elder_endorsement": {
                "endorsed_by": "TestForge Elder Servant",
                "endorsement_strength": "STRONG" if overall_decision == "ELDER_APPROVED" else "CONDITIONAL",
                "review_cycle": "QUARTERLY" if overall_decision == "ELDER_APPROVED" else "MONTHLY"
            },
            "judgment_reasoning": reasoning
        }
    
    async def _analyze_test_quality_trends(
        self, 
        target_path: str, 
        historical_data: List[Dict]
    ) -> Dict[str, Any]:
        """テスト品質トレンド分析"""
        if len(historical_data) < 2:
            return {
                "trend_direction": "INSUFFICIENT_DATA",
                "quality_velocity": 0.0,
                "projected_score": 0.0,
                "elder_confidence": 0.0
            }
        
        # TDDスコア履歴から傾向を分析
        scores = [data.get("tdd_score", 0.0) for data in historical_data[-5:]]  # 最新5件
        
        if len(scores) >= 2:
            # 傾向計算
            slope = (scores[-1] - scores[0]) / (len(scores) - 1)
            
            if slope > 2.0:
                trend_direction = "IMPROVING"
            elif slope < -2.0:
                trend_direction = "DECLINING"
            else:
                trend_direction = "STABLE"
            
            quality_velocity = slope * 10  # 変化率
            projected_score = scores[-1] + slope * 2  # 2期先予測
            
            # Elder信頼度（改善傾向ほど高い）
            elder_confidence = max(0.0, min(100.0, 50.0 + slope * 10))
        else:
            trend_direction = "STABLE"
            quality_velocity = 0.0
            projected_score = scores[-1]
            elder_confidence = 50.0
        
        return {
            "trend_direction": trend_direction,
            "quality_velocity": quality_velocity,
            "projected_score": projected_score,
            "elder_confidence": elder_confidence,
            "data_points": len(historical_data)
        }
    
    async def _analyze_test_failure_patterns(
        self, 
        test_failures: List[Dict]
    ) -> Dict[str, Any]:
        """テスト失敗パターン分析"""
        if not test_failures:
            return {
                "common_patterns": [],
                "failure_categories": {},
                "improvement_suggestions": []
            }
        
        # エラー種別集計
        error_types = {}
        categories = {}
        
        for failure in test_failures:
            error_type = failure.get("error", "Unknown").split(":")[0]
            category = failure.get("category", "unknown")
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
            categories[category] = categories.get(category, 0) + 1
        
        # 共通パターン特定
        common_patterns = [
            {"pattern": error, "count": count, "percentage": count/len(test_failures)*100}
            for error, count in error_types.items() if count > 1
        ]
        
        # 改善提案生成
        improvement_suggestions = []
        if "AssertionError" in error_types:
            improvement_suggestions.append("Review test assertions for accuracy")
        if "AttributeError" in error_types:
            improvement_suggestions.append("Add null/None checks in test setup")
        if "ValueError" in error_types:
            improvement_suggestions.append("Validate input data in test cases")
        
        return {
            "common_patterns": common_patterns,
            "failure_categories": categories,
            "improvement_suggestions": improvement_suggestions
        }
    
    async def _persist_test_judgment(self, judgment_result: TestQualityJudgmentResult):
        """テスト判定結果永続化"""
        # 簡易実装：メモリキャッシュ
        self.judgment_cache[judgment_result.judgment_id] = judgment_result
        self.logger.info(f"📝 Test judgment persisted: {judgment_result.judgment_id}")
    
    async def _retrieve_test_judgment(self, judgment_id: str) -> Optional[TestQualityJudgmentResult]:
        """テスト判定結果取得"""
        return self.judgment_cache.get(judgment_id)
    
    async def _get_test_history(self, target_path: str) -> List[Dict]:
        """テスト履歴取得"""
        return self.test_history.get(target_path, [])
    
    async def _update_test_history(
        self, 
        target_path: str, 
        test_result: TestExecutionResult,
        tdd_quality_score: float
    ):
        """テスト履歴更新"""
        if target_path not in self.test_history:
            self.test_history[target_path] = []
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "coverage": test_result.coverage_percentage,
            "tdd_score": tdd_quality_score,
            "tests_count": test_result.test_results.test_count,
            "passed_count": test_result.test_results.passed_count,
            "status": test_result.status
        }
        
        self.test_history[target_path].append(history_entry)
        
        # 履歴は最新20件まで保持
        if len(self.test_history[target_path]) > 20:
            self.test_history[target_path] = self.test_history[target_path][-20:]