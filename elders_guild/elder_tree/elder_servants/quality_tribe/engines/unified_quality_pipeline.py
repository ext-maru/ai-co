"""
Unified Quality Pipeline - 統合品質パイプライン

Issue #309: 自動化品質パイプライン実装 - Phase 3
目的: 全エンジン + サーバント統合システムの完全自動化
方針: Execute & Judge パターン - 統一品質管理の最終形態
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
from typing import List, Dict, Any, Optional, Tuple

# Engine imports
from elders_guild.elder_tree.elder_servants.quality_tribe.engines.static_analysis_engine import StaticAnalysisEngine
from elders_guild.elder_tree.elder_servants.quality_tribe.engines.test_automation_engine import TestAutomationEngine
from elders_guild.elder_tree.elder_servants.quality_tribe.engines.comprehensive_quality_engine import ComprehensiveQualityEngine

# Servant imports
from elders_guild.elder_tree.elder_servants.quality_tribe.quality_watcher.quality_watcher_judgment import QualityWatcherJudgment
from elders_guild.elder_tree.elder_servants.quality_tribe.test_forge.test_forge_judgment import TestForgeJudgment


@dataclass
class UnifiedQualityResult:
    """統合品質結果"""
    pipeline_id: str
    overall_status: str  # "ELDER_APPROVED" | "ELDER_CONDITIONAL" | "ELDER_REJECTED"
    unified_quality_score: float
    
    # エンジン結果統合
    static_analysis_score: float
    test_automation_score: float  
    comprehensive_quality_score: float
    
    # サーバント判定統合
    quality_watcher_decision: str
    test_forge_decision: str
    elder_council_consensus: str
    
    # 最終認定
    certification_level: Optional[str]
    graduation_certificate: Optional[Dict[str, Any]]
    
    # メタデータ
    execution_time: float
    total_iterations: int
    pipeline_efficiency: float
    judgment_reasoning: List[str]
    final_recommendations: List[str]
    
    timestamp: str


class UnifiedQualityPipeline:
    """
    統合品質パイプライン - Elder Guild自動品質管理の最終形態
    
    Execute & Judge パターンによる完全自動化:
    1. エンジンが実行を担当
    2. サーバントが判定を担当
    3. 統合システムが品質を保証
    """
    
    def __init__(self, parallel_execution: bool = True, enable_caching: bool = False):
        self.pipeline_id = f"UP-{uuid.uuid4().hex[:8].upper()}"
        self.logger = self._setup_logger()
        
        # Engine インスタンス初期化
        self.static_engine = StaticAnalysisEngine()
        self.test_engine = TestAutomationEngine()
        self.comprehensive_engine = ComprehensiveQualityEngine()
        
        # Servant インスタンス初期化
        self.quality_watcher = QualityWatcherJudgment()
        self.test_forge = TestForgeJudgment()
        
        # パイプライン設定
        self.parallel_execution = parallel_execution
        self.enable_caching = enable_caching
        self.max_total_iterations = 50
        
        # Iron Will品質基準
        self.unified_thresholds = {
            "elder_approval_minimum": 98.0,
            "elder_conditional_minimum": 85.0,
            "graduation_certificate_minimum": 95.0,
            "component_minimum": 90.0,
        }
        
        # 統計・キャッシュ
        self.execution_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "average_execution_time": 0.0,
            "quality_score_history": [],
        }
        self.result_cache = {} if enable_caching else None
        
        self.logger.info(f"🏛️ Unified Quality Pipeline initialized: {self.pipeline_id}")
    
    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("unified_quality_pipeline")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def execute_complete_quality_pipeline(
        self, 
        target_path: str
    ) -> UnifiedQualityResult:
        """
        完全品質パイプライン実行 - Phase統合の最終形態
        
        Args:
            target_path: 品質分析対象パス
            
        Returns:
            UnifiedQualityResult: 統合品質結果
        """
        start_time = time.time()
        total_iterations = 0
        
        self.logger.info(f"🚀 Starting unified quality pipeline: {self.pipeline_id}")
        
        try:
            # Cache check
            if self.enable_caching and target_path in self.result_cache:
                cached_result = self.result_cache[target_path]
                self.logger.info(f"📦 Using cached result for {target_path}")
                cached_result.execution_time = 0.1  # キャッシュアクセス時間
                return cached_result
            
            # Phase 1: エンジン実行フェーズ
            engine_results, engine_iterations = await self._execute_engine_phase(target_path)
            total_iterations += engine_iterations
            
            # Phase 2: サーバント判定フェーズ
            servant_judgments = await self._execute_judgment_phase(
                engine_results, target_path
            )
            
            # Phase 3: 統合・最終判定フェーズ
            unified_result = await self._execute_integration_phase(
                engine_results, servant_judgments, target_path, 
                start_time, total_iterations
            )
            
            # 実行メトリクス更新
            self._update_execution_metrics(unified_result)
            
            # キャッシュ保存
            if self.enable_caching:
                self.result_cache[target_path] = unified_result
            
            self.logger.info(
                f"✅ Unified pipeline completed: {unified_result.overall_status} "
                f"({unified_result.unified_quality_score:.1f})"
            )
            
            return unified_result
        
        except Exception as e:
            self.logger.error(f"❌ Unified pipeline error: {e}", exc_info=True)
            
            # エラー時のフォールバック結果
            return UnifiedQualityResult(
                pipeline_id=self.pipeline_id,
                overall_status="ELDER_REJECTED",
                unified_quality_score=0.0,
                static_analysis_score=0.0,
                test_automation_score=0.0,
                comprehensive_quality_score=0.0,
                quality_watcher_decision="ELDER_REJECTED",
                test_forge_decision="ELDER_REJECTED",
                elder_council_consensus="REJECTED",
                certification_level=None,
                graduation_certificate=None,
                execution_time=time.time() - start_time,
                total_iterations=total_iterations,
                pipeline_efficiency=0.0,
                judgment_reasoning=[f"Pipeline execution error: {str(e)}"],
                final_recommendations=["Fix pipeline system issues"],
                timestamp=datetime.now().isoformat()
            )
    
    async def _execute_engine_phase(
        self, 
        target_path: str
    ) -> Tuple[Dict[str, Any], int]:
        """エンジン実行フェーズ"""
        self.logger.info("🔧 Executing engine phase")
        total_iterations = 0
        
        if self.parallel_execution:
            # 並列実行
            tasks = [
                self.static_engine.execute_full_pipeline(target_path),
                self.test_engine.execute_full_pipeline(target_path),
                self.comprehensive_engine.execute_full_pipeline(target_path)
            ]
            
            static_result, test_result, comprehensive_result = await asyncio.gather(
                *tasks, return_exceptions=True
            )
        else:
            # シーケンシャル実行
            static_result = await self.static_engine.execute_full_pipeline(target_path)
            test_result = await self.test_engine.execute_full_pipeline(target_path)
            comprehensive_result = await self.comprehensive_engine.execute_full_pipeline(target_path)
        
        # エラーハンドリング
        if isinstance(static_result, Exception):
            self.logger.error(f"Static analysis engine error: {static_result}")
            static_result = self._create_error_static_result(static_result)
        
        if isinstance(test_result, Exception):
            self.logger.error(f"Test automation engine error: {test_result}")
            test_result = self._create_error_test_result(test_result)
        
        if isinstance(comprehensive_result, Exception):
            self.logger.error(f"Comprehensive quality engine error: {comprehensive_result}")
            comprehensive_result = self._create_error_comprehensive_result(comprehensive_result)
        
        # イテレーション数集計
        total_iterations += getattr(static_result, 'iterations', 0)
        total_iterations += getattr(test_result, 'iterations', 0)
        total_iterations += getattr(comprehensive_result, 'iterations', 0)
        
        return {
            "static_result": static_result,
            "test_result": test_result,
            "comprehensive_result": comprehensive_result
        }, total_iterations
    
    async def _execute_judgment_phase(
        self, 
        engine_results: Dict[str, Any], 
        target_path: str
    ) -> Dict[str, Any]:
        """サーバント判定フェーズ"""
        self.logger.info("🧙‍♂️ Executing judgment phase")
        
        # 並列判定実行
        quality_judgment_task = self.quality_watcher.judge_static_analysis_quality(
            engine_results["static_result"], target_path
        )
        
        test_judgment_task = self.test_forge.judge_test_automation_quality(
            engine_results["test_result"], target_path
        )
        
        quality_judgment, test_judgment = await asyncio.gather(
            quality_judgment_task,
            test_judgment_task,
            return_exceptions=True
        )
        
        # エラーハンドリング
        if isinstance(quality_judgment, Exception):
            self.logger.error(f"Quality judgment error: {quality_judgment}")
            quality_judgment = self._create_error_quality_judgment(quality_judgment)
        
        if isinstance(test_judgment, Exception):
            self.logger.error(f"Test judgment error: {test_judgment}")
            test_judgment = self._create_error_test_judgment(test_judgment)
        
        return {
            "quality_judgment": quality_judgment,
            "test_judgment": test_judgment
        }
    
    async def _execute_integration_phase(
        self,
        engine_results: Dict[str, Any],
        servant_judgments: Dict[str, Any],
        target_path: str,
        start_time: float,
        total_iterations: int
    ) -> UnifiedQualityResult:
        """統合・最終判定フェーズ"""
        self.logger.info("🏛️ Executing integration phase")
        
        # エンジン結果統合
        integrated_scores = self._integrate_engine_results(engine_results)
        
        # サーバント判定統合
        consensus = self._determine_elder_council_consensus(servant_judgments)
        
        # 統合品質スコア算出
        unified_score = self._calculate_unified_quality_score(
            integrated_scores, 
            {
                "quality_watcher_decision": servant_judgments["quality_judgment"].overall_decision,
                "test_forge_decision": servant_judgments["test_judgment"].overall_decision
            }
        )
        
        # 最終決定
        overall_status = self._make_final_pipeline_decision(
            unified_score, consensus, servant_judgments
        )
        
        # 実行効率計算
        execution_time = time.time() - start_time
        pipeline_efficiency = self._calculate_pipeline_efficiency({
            "total_execution_time": execution_time,
            "engine_time": execution_time * 0.7,  # 推定
            "judgment_time": execution_time * 0.25,  # 推定
            "integration_time": execution_time * 0.05,  # 推定
            "total_iterations": total_iterations,
            "successful_operations": 8,  # 基本操作数
            "total_operations": 8
        })
        
        # 判定根拠生成
        reasoning = self._generate_unified_judgment_reasoning(
            integrated_scores, servant_judgments, unified_score, overall_status
        )
        
        # 最終推奨事項生成
        recommendations = self._generate_final_recommendations(
            engine_results, servant_judgments, overall_status
        )
        
        # 認定レベル決定
        certification_level = self._determine_unified_certification_level(unified_score)
        
        # 卒業証明書発行（条件満たした場合）
        graduation_certificate = None
        if unified_score >= self.unified_thresholds["graduation_certificate_minimum"]:
            graduation_certificate = self._issue_graduation_certificate({
                "pipeline_id": self.pipeline_id,
                "unified_quality_score": unified_score,
                "overall_status": overall_status,
                "certification_level": certification_level
            })
        
        return UnifiedQualityResult(
            pipeline_id=self.pipeline_id,
            overall_status=overall_status,
            unified_quality_score=unified_score,
            static_analysis_score=integrated_scores["static_analysis_score"],
            test_automation_score=integrated_scores["test_automation_score"],
            comprehensive_quality_score=integrated_scores["comprehensive_quality_score"],
            quality_watcher_decision=servant_judgments["quality_judgment"].overall_decision,
            test_forge_decision=servant_judgments["test_judgment"].overall_decision,
            elder_council_consensus=consensus["consensus_decision"],
            certification_level=certification_level,
            graduation_certificate=graduation_certificate,
            execution_time=execution_time,
            total_iterations=total_iterations,
            pipeline_efficiency=pipeline_efficiency,
            judgment_reasoning=reasoning,
            final_recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
    
    def _integrate_engine_results(self, engine_results: Dict[str, Any]) -> Dict[str, float]:
        """エンジン結果統合"""
        # 静的解析スコア抽出
        static_result = engine_results["static_result"]
        if hasattr(static_result, 'pylint_score'):
            static_score = static_result.pylint_score * 10.0  # 10点満点→100点満点
        else:
            static_score = 0.0
        
        # テスト自動化スコア抽出
        test_result = engine_results["test_result"]
        if hasattr(test_result, 'coverage_percentage'):
            test_score = test_result.coverage_percentage
        else:
            test_score = 0.0
        
        # 包括品質スコア抽出
        comprehensive_result = engine_results["comprehensive_result"]
        if hasattr(comprehensive_result, 'unified_quality_score'):
            comprehensive_score = comprehensive_result.unified_quality_score
        else:
            comprehensive_score = 0.0
        
        return {
            "static_analysis_score": max(0.0, min(100.0, static_score)),
            "test_automation_score": max(0.0, min(100.0, test_score)),
            "comprehensive_quality_score": max(0.0, min(100.0, comprehensive_score))
        }
    
    def _determine_elder_council_consensus(
        self, 
        servant_judgments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Elder Council合意決定"""
        quality_decision = servant_judgments["quality_judgment"].overall_decision
        test_decision = servant_judgments["test_judgment"].overall_decision
        
        # 決定マトリックス
        decision_matrix = {
            ("ELDER_APPROVED", "ELDER_APPROVED"): "APPROVED",
            ("ELDER_APPROVED", "ELDER_CONDITIONAL"): "CONDITIONAL",
            ("ELDER_APPROVED", "ELDER_REJECTED"): "CONDITIONAL",
            ("ELDER_CONDITIONAL", "ELDER_APPROVED"): "CONDITIONAL",
            ("ELDER_CONDITIONAL", "ELDER_CONDITIONAL"): "CONDITIONAL",
            ("ELDER_CONDITIONAL", "ELDER_REJECTED"): "REJECTED",
            ("ELDER_REJECTED", "ELDER_APPROVED"): "CONDITIONAL",
            ("ELDER_REJECTED", "ELDER_CONDITIONAL"): "REJECTED",
            ("ELDER_REJECTED", "ELDER_REJECTED"): "REJECTED",
        }
        
        consensus_decision = decision_matrix.get(
            (quality_decision, test_decision), "REJECTED"
        )
        
        # 信頼度計算
        approval_count = sum([
            1 for decision in [quality_decision, test_decision] 
            if decision == "ELDER_APPROVED"
        ])
        
        confidence_level = {
            2: "VERY_HIGH",
            1: "HIGH", 
            0: "MEDIUM"
        }.get(approval_count, "LOW")
        
        # 根拠生成
        reasoning = [
            f"Quality Watcher: {quality_decision}",
            f"Test Forge: {test_decision}",
            f"Consensus Algorithm: {consensus_decision}"
        ]
        
        return {
            "consensus_decision": consensus_decision,
            "confidence_level": confidence_level,
            "reasoning": reasoning
        }
    
    def _calculate_unified_quality_score(
        self, 
        component_scores: Dict[str, float], 
        servant_decisions: Dict[str, str]
    ) -> float:
        """統合品質スコア算出"""
        # 基本重み付け
        weights = {
            "static_analysis": 0.35,  # 35%
            "test_automation": 0.35,  # 35%
            "comprehensive_quality": 0.30,  # 30%
        }
        
        # ベーススコア計算
        base_score = (
            component_scores["static_analysis_score"] * weights["static_analysis"] +
            component_scores["test_automation_score"] * weights["test_automation"] +
            component_scores["comprehensive_quality_score"] * weights["comprehensive_quality"]
        )
        
        # サーバント判定ボーナス/ペナルティ
        servant_multiplier = 1.0
        
        approved_count = sum([
            1 for decision in servant_decisions.values() 
            if decision == "ELDER_APPROVED"
        ])
        
        if approved_count == 2:
            servant_multiplier = 1.05  # 5%ボーナス
        elif approved_count == 1:
            servant_multiplier = 1.0   # ボーナスなし
        else:
            servant_multiplier = 0.95  # 5%ペナルティ
        
        # 最終スコア
        unified_score = base_score * servant_multiplier
        
        return max(0.0, min(100.0, unified_score))
    
    def _calculate_pipeline_efficiency(
        self, 
        execution_metrics: Dict[str, Any]
    ) -> float:
        """パイプライン効率性算出"""
        total_time = execution_metrics["total_execution_time"]
        total_operations = execution_metrics["total_operations"]
        successful_operations = execution_metrics["successful_operations"]
        
        # 成功率
        success_rate = successful_operations / total_operations if total_operations > 0 else 0.0
        
        # 時間効率（逆数ベース、60秒を基準として正規化）
        time_efficiency = min(1.0, 60.0 / max(1.0, total_time))
        
        # イテレーション効率（少ないほど良い、10回を基準）
        iteration_efficiency = min(1.0, 10.0 / max(1.0, execution_metrics["total_iterations"]))
        
        # 総合効率
        overall_efficiency = (success_rate * 0.5 + time_efficiency * 0.3 + iteration_efficiency * 0.2) * 100.0
        
        return max(0.0, min(100.0, overall_efficiency))
    
    def _make_final_pipeline_decision(
        self,
        unified_score: float,
        consensus: Dict[str, Any],
        servant_judgments: Dict[str, Any]
    ) -> str:
        """最終パイプライン決定"""
        # Iron Will絶対基準チェック
        if unified_score >= self.unified_thresholds["elder_approval_minimum"]:
            if consensus["consensus_decision"] == "APPROVED":
                return "ELDER_APPROVED"
        
        # 条件付き承認判断
        if unified_score >= self.unified_thresholds["elder_conditional_minimum"]:
            if consensus["consensus_decision"] in ["APPROVED", "CONDITIONAL"]:
                return "ELDER_CONDITIONAL"
        
        # それ以外は拒否
        return "ELDER_REJECTED"
    
    def _generate_unified_judgment_reasoning(
        self,
        integrated_scores: Dict[str, float],
        servant_judgments: Dict[str, Any],
        unified_score: float,
        overall_status: str
    ) -> List[str]:
        """統合判定根拠生成"""
        reasoning = [
            f"Unified Quality Score: {unified_score:.1f}/100",
            f"Static Analysis: {integrated_scores['static_analysis_score']:.1f}/100",
            f"Test Automation: {integrated_scores['test_automation_score']:.1f}/100",
            f"Comprehensive Quality: {integrated_scores['comprehensive_quality_score']:.1f}/100",
            f"Quality Watcher: {servant_judgments['quality_judgment'].overall_decision}",
            f"Test Forge: {servant_judgments['test_judgment'].overall_decision}"
        ]
        
        # 決定根拠
        if overall_status == "ELDER_APPROVED":
            reasoning.append("✅ Exceeds all Elder Council unified standards")
        elif overall_status == "ELDER_CONDITIONAL":
            reasoning.append("⚠️ Meets basic unified standards but requires improvement")
        else:
            reasoning.append("❌ Does not meet Elder Council minimum unified standards")
        
        return reasoning
    
    def _generate_final_recommendations(
        self,
        engine_results: Dict[str, Any],
        servant_judgments: Dict[str, Any],
        overall_status: str
    ) -> List[str]:
        """最終推奨事項生成"""
        recommendations = []
        
        if overall_status != "ELDER_APPROVED":
            # QualityWatcher推奨事項
            if hasattr(servant_judgments["quality_judgment"], 'improvement_recommendations'):
                recommendations.extend(servant_judgments["quality_judgment"].improvement_recommendations)
            
            # TestForge推奨事項
            if hasattr(servant_judgments["test_judgment"], 'improvement_recommendations'):
                recommendations.extend(servant_judgments["test_judgment"].improvement_recommendations)
            
            # 統合レベル推奨事項
            recommendations.append("Implement Elder Council unified standards")
            recommendations.append("Schedule regular quality monitoring sessions")
        
        return recommendations
    
    def _determine_unified_certification_level(self, unified_score: float) -> Optional[str]:
        """統合認定レベル決定"""
        certification_levels = {
            99.0: "UNIFIED_EXCELLENCE_MASTER",
            98.0: "UNIFIED_EXCELLENCE", 
            95.0: "UNIFIED_CERTIFIED",
            90.0: "UNIFIED_QUALIFIED",
        }
        
        for threshold, level in sorted(certification_levels.items(), reverse=True):
            if unified_score >= threshold:
                return level
        
        return None
    
    def _issue_graduation_certificate(
        self, 
        result_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """卒業証明書発行"""
        certificate_id = f"CERT-{uuid.uuid4().hex[:8].upper()}"
        
        return {
            "certificate_id": certificate_id,
            "pipeline_id": result_data["pipeline_id"],
            "unified_quality_score": result_data["unified_quality_score"],
            "certification_level": result_data["certification_level"],
            "overall_status": result_data["overall_status"],
            "elder_council_seal": "UNIFIED_QUALITY_EXCELLENCE",
            "issued_timestamp": datetime.now().isoformat(),
            "valid_until": (datetime.now() + timedelta(days=90)).isoformat(),
            "issuing_authority": "Elder Council Unified Quality Authority"
        }
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """パイプラインメトリクス取得"""
        return {
            "total_executions": self.execution_metrics["total_executions"],
            "successful_executions": self.execution_metrics["successful_executions"],
            "average_execution_time": self.execution_metrics["average_execution_time"],
            "success_rate": (
                self.execution_metrics["successful_executions"] / 
                max(1, self.execution_metrics["total_executions"]) * 100.0
            ),
            "quality_score_distribution": {
                "mean": statistics.mean(self.execution_metrics["quality_score_history"]) if self.execution_metrics["quality_score_history"] else 0.0,
                "median": statistics.median(self.execution_metrics["quality_score_history"]) if self.execution_metrics["quality_score_history"] else 0.0,
                "count": len(self.execution_metrics["quality_score_history"])
            }
        }
    
    def _update_execution_metrics(self, result: UnifiedQualityResult):
        """実行メトリクス更新"""
        self.execution_metrics["total_executions"] += 1
        
        if result.overall_status == "ELDER_APPROVED":
            self.execution_metrics["successful_executions"] += 1
        
        # 平均実行時間更新
        prev_avg = self.execution_metrics["average_execution_time"]
        total_count = self.execution_metrics["total_executions"]
        self.execution_metrics["average_execution_time"] = (
            (prev_avg * (total_count - 1) + result.execution_time) / total_count
        )
        
        # 品質スコア履歴
        self.execution_metrics["quality_score_history"].append(result.unified_quality_score)
        
        # 履歴は最新100件まで保持
        if len(self.execution_metrics["quality_score_history"]) > 100:
            self.execution_metrics["quality_score_history"] = self.execution_metrics["quality_score_history"][-100:]
    
    # エラーハンドリング用フォールバック結果生成
    def _create_error_static_result(self, error: Exception):
        """エラー時静的解析結果生成"""
        from elders_guild.elder_tree.elder_servants.quality_tribe.engines.static_analysis_engine import StaticAnalysisResult
        
        return StaticAnalysisResult(
            status="ERROR",
            iterations=0,
            formatting_applied=False,
            imports_organized=False,
            type_errors=[str(error)],
            pylint_score=0.0,
            pylint_issues=[{"type": "error", "message": str(error)}],
            auto_fixes_applied=0,
            execution_time=0.0,
            summary={"pipeline_status": "ERROR", "error": str(error)}
        )
    
    def _create_error_test_result(self, error: Exception):
        """エラー時テスト結果生成"""
        from elders_guild.elder_tree.elder_servants.quality_tribe.engines.test_automation_engine import TestExecutionResult, PytestResult, HypothesisResult
        
        pytest_result = PytestResult(
            all_passed=False, test_count=0, passed_count=0, failed_count=0,
            skipped_count=0, duration=0.0, failures=[{"error": str(error)}], output=""
        )
        
        hypothesis_result = HypothesisResult(
            passed_properties=[], failed_properties=[], examples_tested=0,
            shrinking_attempts=0, output=""
        )
        
        return TestExecutionResult(
            status="ERROR", iterations=0, test_results=pytest_result,
            coverage_percentage=0.0, uncovered_lines=[], 
            property_test_results=hypothesis_result, multi_env_results=None,
            auto_generated_tests=0, execution_time=0.0,
            summary={"pipeline_status": "ERROR", "error": str(error)}
        )
    
    def _create_error_comprehensive_result(self, error: Exception):
        """エラー時包括結果生成"""
        from elders_guild.elder_tree.elder_servants.quality_tribe.engines.comprehensive_quality_engine import ComprehensiveQualityResult
        
        return ComprehensiveQualityResult(
            unified_quality_score=0.0, status="ERROR", iterations=0,
            documentation_score=0.0, security_score=0.0, configuration_score=0.0,
            performance_score=0.0, elder_council_report={"error": str(error)},
            quality_certificate=None, execution_time=0.0,
            summary={"pipeline_status": "ERROR", "error": str(error)}
        )
    
    def _create_error_quality_judgment(self, error: Exception):
        """エラー時品質判定生成"""
        from elders_guild.quality_servants.quality_watcher_judgment import QualityJudgmentResult
        
        return QualityJudgmentResult(
            judgment_id=f"ERROR-{uuid.uuid4().hex[:8]}",
            overall_decision="ELDER_REJECTED",
            quality_score=0.0,
            iron_will_compliance=False,
            judgment_reasoning=[f"Quality judgment error: {str(error)}"],
            improvement_recommendations=["Fix quality judgment system"],
            elder_council_report={"error": str(error)},
            certification_level=None,
            next_review_required=True,
            judgment_timestamp=datetime.now().isoformat()
        )
    
    def _create_error_test_judgment(self, error: Exception):
        """エラー時テスト判定生成"""
        from elders_guild.quality_servants.test_forge_judgment import TestQualityJudgmentResult
        
        return TestQualityJudgmentResult(
            judgment_id=f"ERROR-{uuid.uuid4().hex[:8]}",
            overall_decision="ELDER_REJECTED",
            tdd_quality_score=0.0,
            coverage_judgment="INSUFFICIENT",
            test_architecture_score=0.0,
            judgment_reasoning=[f"Test judgment error: {str(error)}"],
            improvement_recommendations=["Fix test judgment system"],
            elder_council_report={"error": str(error)},
            certification_level=None,
            next_review_required=True,
            judgment_timestamp=datetime.now().isoformat()
        )
