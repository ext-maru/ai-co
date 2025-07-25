"""
QualityWatcher Judgment System - 🧝‍♂️ 品質監視サーバント判定システム

Issue #309: 自動化品質パイプライン実装 - Phase 2
担当サーバント: 🧝‍♂️ QualityWatcher (E01)

目的: StaticAnalysisEngine結果の専門判定・Elder Council承認判断
方針: Execute & Judge パターン - 判定・意思決定に特化
"""

import asyncio
import time
import logging
import json
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import statistics

from elders_guild.quality.static_analysis_engine import StaticAnalysisResult


@dataclass
class QualityJudgmentResult:
    """品質判定結果"""
    judgment_id: str
    overall_decision: str  # "ELDER_APPROVED" | "ELDER_CONDITIONAL" | "ELDER_REJECTED"
    quality_score: float  # 95点以上でElder承認
    iron_will_compliance: bool
    judgment_reasoning: List[str]
    improvement_recommendations: List[str]
    elder_council_report: Dict[str, Any]
    certification_level: Optional[str]
    next_review_required: bool
    judgment_timestamp: str


@dataclass
class StaticAnalysisJudgment:
    """静的解析専門判定"""
    pylint_score_judgment: str  # "EXCELLENT" | "GOOD" | "NEEDS_IMPROVEMENT"
    type_safety_judgment: str   # "PERFECT" | "ACCEPTABLE" | "CRITICAL_ISSUES"
    code_style_judgment: str    # "FLAWLESS" | "MINOR_ISSUES" | "MAJOR_ISSUES"
    iron_will_adherence: float  # 0-100%
    quality_trend_analysis: Dict[str, Any]
    auto_fix_effectiveness: float
    elder_recommendation: str


class QualityWatcherJudgment:
    """
    QualityWatcher品質判定システム
    
    専門領域: 品質監視・コード品質評価
    判定能力: 静的解析結果の品質スコア算出
    責任範囲: Iron Will基準遵守チェック・Elder承認判断
    """
    
    def __init__(self):
        self.servant_id = "QualityWatcher-E01"
        self.logger = self._setup_logger()
        
        # Elder承認判定基準
        self.judgment_thresholds = {
            "elder_approval_minimum": 95.0,
            "iron_will_compliance_minimum": 90.0,
            "pylint_score_excellent": 9.5,
            "pylint_score_good": 8.0,
            "type_errors_critical": 3,
            "auto_fix_effectiveness_good": 70.0,
        }
        
        # 品質履歴ストレージ（簡易実装）
        self.quality_history = {}
        self.judgment_cache = {}
        
        # 認定レベル基準
        self.certification_levels = {
            99.5: "LEGENDARY_QUALITY_MASTER",
            99.0: "GRAND_ELDER_QUALITY",
            98.0: "ELDER_QUALITY_EXCELLENCE",
            95.0: "QUALITY_CERTIFIED",
        }
    
    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("quality_watcher_judgment")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def judge_static_analysis_quality(
        self, 
        analysis_result: StaticAnalysisResult,
        target_path: str
    ) -> QualityJudgmentResult:
        """
        静的解析品質の専門判定
        
        Args:
            analysis_result: StaticAnalysisEngine実行結果
            target_path: 解析対象パス
            
        Returns:
            QualityJudgmentResult: 専門判定結果
        """
        judgment_id = f"QW-{uuid.uuid4().hex[:8].upper()}"
        self.logger.info(f"🧝‍♂️ Starting quality judgment: {judgment_id}")
        
        try:
            # Phase 1: 詳細静的解析判定
            detailed_judgment = await self._analyze_static_analysis_details(analysis_result)
            
            # Phase 2: Iron Will遵守評価
            iron_will_assessment = await self._assess_iron_will_compliance(analysis_result)
            
            # Phase 3: 品質トレンド分析
            historical_data = await self._get_quality_history(target_path)
            trend_analysis = await self._analyze_quality_trends(target_path, historical_data)
            
            # Phase 4: 総合品質スコア算出
            quality_score = self._calculate_comprehensive_quality_score(
                analysis_result, detailed_judgment, iron_will_assessment, trend_analysis
            )
            
            # Phase 5: Elder承認判断
            overall_decision = self._make_elder_approval_decision(
                quality_score, iron_will_assessment, analysis_result
            )
            
            # Phase 6: 判定根拠生成
            reasoning = self._generate_judgment_reasoning(
                analysis_result, detailed_judgment, quality_score, overall_decision
            )
            
            # Phase 7: 改善推奨事項生成（必要時）
            recommendations = []
            if overall_decision != "ELDER_APPROVED":
                recommendations = await self._generate_improvement_recommendations(analysis_result)
            
            # Phase 8: 認定レベル決定
            certification_level = self._determine_certification_level(quality_score)
            
            # Phase 9: Elder Council報告書生成
            elder_report = self._generate_elder_council_report(
                judgment_id, analysis_result, quality_score, overall_decision, reasoning
            )
            
            # 判定結果構築
            judgment_result = QualityJudgmentResult(
                judgment_id=judgment_id,
                overall_decision=overall_decision,
                quality_score=quality_score,
                iron_will_compliance=iron_will_assessment["overall_compliance"],
                judgment_reasoning=reasoning,
                improvement_recommendations=recommendations,
                elder_council_report=elder_report,
                certification_level=certification_level,
                next_review_required=(overall_decision != "ELDER_APPROVED"),
                judgment_timestamp=datetime.now().isoformat()
            )
            
            # 判定結果永続化
            await self._persist_judgment(judgment_result)
            
            # 品質履歴更新
            await self._update_quality_history(target_path, analysis_result, quality_score)
            
            self.logger.info(f"✅ Quality judgment completed: {overall_decision} ({quality_score:.1f})")
            return judgment_result
        
        except Exception as e:
            self.logger.error(f"❌ Quality judgment error: {e}", exc_info=True)
            # エラー時のフォールバック判定
            return QualityJudgmentResult(
                judgment_id=judgment_id,
                overall_decision="ELDER_REJECTED",
                quality_score=0.0,
                iron_will_compliance=False,
                judgment_reasoning=[f"Judgment system error: {str(e)}"],
                improvement_recommendations=["Fix judgment system issues"],
                elder_council_report={"error": str(e)},
                certification_level=None,
                next_review_required=True,
                judgment_timestamp=datetime.now().isoformat()
            )
    
    async def _analyze_static_analysis_details(
        self, 
        analysis_result: StaticAnalysisResult
    ) -> StaticAnalysisJudgment:
        """詳細静的解析判定"""
        # Pylint スコア判定
        if analysis_result.pylint_score >= self.judgment_thresholds["pylint_score_excellent"]:
            pylint_judgment = "EXCELLENT"
        elif analysis_result.pylint_score >= self.judgment_thresholds["pylint_score_good"]:
            pylint_judgment = "GOOD"
        else:
            pylint_judgment = "NEEDS_IMPROVEMENT"
        
        # 型安全性判定
        if len(analysis_result.type_errors) == 0:
            type_judgment = "PERFECT"
        elif len(analysis_result.type_errors) <= self.judgment_thresholds["type_errors_critical"]:
            type_judgment = "ACCEPTABLE"
        else:
            type_judgment = "CRITICAL_ISSUES"
        
        # コードスタイル判定
        if analysis_result.formatting_applied and analysis_result.imports_organized:
            if len(analysis_result.pylint_issues) == 0:
                style_judgment = "FLAWLESS"
            elif len(analysis_result.pylint_issues) <= 2:
                style_judgment = "MINOR_ISSUES"
            else:
                style_judgment = "MAJOR_ISSUES"
        else:
            style_judgment = "MAJOR_ISSUES"
        
        # Iron Will遵守度計算
        iron_will_score = 100.0
        if analysis_result.status != "COMPLETED":
            iron_will_score -= 30.0
        if len(analysis_result.type_errors) > 0:
            iron_will_score -= len(analysis_result.type_errors) * 5.0
        if analysis_result.pylint_score < 9.5:
            iron_will_score -= (9.5 - analysis_result.pylint_score) * 10.0
        
        iron_will_adherence = max(0.0, iron_will_score)
        
        # 自動修正効果性評価
        auto_fix_effectiveness = min(100.0, analysis_result.auto_fixes_applied * 25.0)
        
        # Elder推奨決定
        if pylint_judgment == "EXCELLENT" and type_judgment == "PERFECT":
            elder_recommendation = "STRONGLY_RECOMMENDED"
        elif pylint_judgment in ["EXCELLENT", "GOOD"] and type_judgment in ["PERFECT", "ACCEPTABLE"]:
            elder_recommendation = "RECOMMENDED"
        else:
            elder_recommendation = "REQUIRES_IMPROVEMENT"
        
        return StaticAnalysisJudgment(
            pylint_score_judgment=pylint_judgment,
            type_safety_judgment=type_judgment,
            code_style_judgment=style_judgment,
            iron_will_adherence=iron_will_adherence,
            quality_trend_analysis={},  # Will be filled by trend analysis
            auto_fix_effectiveness=auto_fix_effectiveness,
            elder_recommendation=elder_recommendation
        )
    
    async def _assess_iron_will_compliance(
        self, 
        analysis_result: StaticAnalysisResult
    ) -> Dict[str, Any]:
        """Iron Will遵守評価"""
        violations = []
        compliance_areas = {
            "no_compromise": True,
            "complete_execution": analysis_result.status == "COMPLETED",
            "type_safety": len(analysis_result.type_errors) == 0,
            "code_quality": analysis_result.pylint_score >= 9.5,
            "style_consistency": analysis_result.formatting_applied and analysis_result.imports_organized,
        }
        
        # 違反チェック
        if not compliance_areas["complete_execution"]:
            violations.append("Pipeline did not complete successfully")
        
        if not compliance_areas["type_safety"]:
            violations.append(f"{len(analysis_result.type_errors)} type errors found")
        
        if not compliance_areas["code_quality"]:
            violations.append(f"Pylint score {analysis_result.pylint_score} below 9.5 requirement")
        
        if not compliance_areas["style_consistency"]:
            violations.append("Code style not fully consistent")
        
        # 総合遵守度計算
        compliance_score = sum(compliance_areas.values()) / len(compliance_areas) * 100.0
        overall_compliance = compliance_score >= self.judgment_thresholds["iron_will_compliance_minimum"]
        
        return {
            "overall_compliance": overall_compliance,
            "compliance_score": compliance_score,
            "violations": violations,
            "compliance_areas": compliance_areas
        }
    
    async def _analyze_quality_trends(
        self, 
        target_path: str, 
        historical_data: List[Dict]
    ) -> Dict[str, Any]:
        """品質トレンド分析"""
        if len(historical_data) < 2:
            return {
                "trend_direction": "INSUFFICIENT_DATA",
                "quality_velocity": 0.0,
                "projected_score": 0.0,
                "elder_confidence": 0.0
            }
        
        # スコア履歴から傾向を分析
        scores = [data.get("pylint_score", 0.0) for data in historical_data[-5:]]  # 最新5件
        
        if len(scores) >= 2:
            # 線形回帰による傾向分析（簡易）
            x_values = list(range(len(scores)))
            y_values = scores
            
            # 傾向計算
            if len(scores) > 1:
                slope = (y_values[-1] - y_values[0]) / (len(y_values) - 1)
                
                if slope > 0.1:
                    trend_direction = "IMPROVING"
                elif slope < -0.1:
                    trend_direction = "DECLINING"
                else:
                    trend_direction = "STABLE"
                
                quality_velocity = slope * 100  # 変化率パーセント
                projected_score = y_values[-1] + slope * 2  # 2期先予測
                
                # Elder信頼度（改善傾向ほど高い）
                elder_confidence = max(0.0, min(100.0, 50.0 + slope * 50))
            else:
                trend_direction = "STABLE"
                quality_velocity = 0.0
                projected_score = scores[-1]
                elder_confidence = 50.0
        else:
            trend_direction = "INSUFFICIENT_DATA"
            quality_velocity = 0.0
            projected_score = 0.0
            elder_confidence = 0.0
        
        return {
            "trend_direction": trend_direction,
            "quality_velocity": quality_velocity,
            "projected_score": projected_score,
            "elder_confidence": elder_confidence,
            "data_points": len(historical_data)
        }
    
    def _calculate_comprehensive_quality_score(
        self,
        analysis_result: StaticAnalysisResult,
        detailed_judgment: StaticAnalysisJudgment,
        iron_will_assessment: Dict[str, Any],
        trend_analysis: Dict[str, Any]
    ) -> float:
        """総合品質スコア算出"""
        # ベーススコア（Pylintスコアベース）
        base_score = analysis_result.pylint_score * 10.0  # 0-100スケール
        
        # 型安全性ボーナス/ペナルティ
        if detailed_judgment.type_safety_judgment == "PERFECT":
            type_bonus = 5.0
        elif detailed_judgment.type_safety_judgment == "ACCEPTABLE":
            type_bonus = 0.0
        else:
            type_bonus = -10.0
        
        # コードスタイルボーナス/ペナルティ
        if detailed_judgment.code_style_judgment == "FLAWLESS":
            style_bonus = 3.0
        elif detailed_judgment.code_style_judgment == "MINOR_ISSUES":
            style_bonus = 0.0
        else:
            style_bonus = -5.0
        
        # Iron Will遵守ボーナス/ペナルティ
        iron_will_bonus = (iron_will_assessment["compliance_score"] - 90.0) * 0.2
        
        # 実行完了ボーナス/ペナルティ
        if analysis_result.status == "COMPLETED":
            completion_bonus = 2.0
        elif analysis_result.status == "MAX_ITERATIONS_EXCEEDED":
            completion_bonus = -5.0
        else:
            completion_bonus = -10.0
        
        # 自動修正効果ボーナス
        auto_fix_bonus = min(3.0, analysis_result.auto_fixes_applied * 1.0)
        
        # トレンドボーナス
        if trend_analysis.get("trend_direction") == "IMPROVING":
            trend_bonus = 2.0
        elif trend_analysis.get("trend_direction") == "DECLINING":
            trend_bonus = -3.0
        else:
            trend_bonus = 0.0
        
        # 総合スコア計算
        comprehensive_score = (
            base_score + 
            type_bonus + 
            style_bonus + 
            iron_will_bonus + 
            completion_bonus + 
            auto_fix_bonus + 
            trend_bonus
        )
        
        return max(0.0, min(100.0, comprehensive_score))
    
    def _make_elder_approval_decision(
        self,
        quality_score: float,
        iron_will_assessment: Dict[str, Any],
        analysis_result: StaticAnalysisResult
    ) -> str:
        """Elder承認判断"""
        # 絶対基準チェック
        if quality_score >= self.judgment_thresholds["elder_approval_minimum"]:
            if iron_will_assessment["overall_compliance"]:
                if analysis_result.status == "COMPLETED":
                    return "ELDER_APPROVED"
        
        # 条件付き承認判断
        if quality_score >= 90.0:
            if iron_will_assessment["compliance_score"] >= 80.0:
                if len(analysis_result.type_errors) <= 1:
                    return "ELDER_CONDITIONAL"
        
        # それ以外は拒否
        return "ELDER_REJECTED"
    
    def _generate_judgment_reasoning(
        self,
        analysis_result: StaticAnalysisResult,
        detailed_judgment: StaticAnalysisJudgment,
        quality_score: float,
        overall_decision: str
    ) -> List[str]:
        """判定根拠生成"""
        reasoning = []
        
        # スコア根拠
        reasoning.append(f"Comprehensive quality score: {quality_score:.1f}/100")
        reasoning.append(f"Pylint score: {analysis_result.pylint_score}/10 ({detailed_judgment.pylint_score_judgment})")
        reasoning.append(f"Type safety: {detailed_judgment.type_safety_judgment}")
        reasoning.append(f"Code style: {detailed_judgment.code_style_judgment}")
        
        # 実行状況
        reasoning.append(f"Pipeline execution: {analysis_result.status}")
        if analysis_result.auto_fixes_applied > 0:
            reasoning.append(f"Auto-fixes applied: {analysis_result.auto_fixes_applied}")
        
        # 決定根拠
        if overall_decision == "ELDER_APPROVED":
            reasoning.append("✅ Meets all Elder Council quality standards")
        elif overall_decision == "ELDER_CONDITIONAL":
            reasoning.append("⚠️ Meets basic standards but requires monitoring")
        else:
            reasoning.append("❌ Does not meet Elder Council minimum standards")
        
        return reasoning
    
    async def _generate_improvement_recommendations(
        self, 
        analysis_result: StaticAnalysisResult
    ) -> List[str]:
        """改善推奨事項生成"""
        recommendations = []
        
        # Pylintスコア改善
        if analysis_result.pylint_score < 9.5:
            recommendations.append({
                "priority": "HIGH",
                "category": "PYLINT",
                "description": f"Improve Pylint score from {analysis_result.pylint_score} to 9.5+",
                "expected_impact": "Quality score increase +10-20 points",
                "implementation_effort": "2-4 hours"
            })
        
        # 型安全性改善
        if len(analysis_result.type_errors) > 0:
            recommendations.append({
                "priority": "HIGH",
                "category": "TYPE_SAFETY",
                "description": f"Fix {len(analysis_result.type_errors)} type errors",
                "expected_impact": "Quality score increase +5-15 points",
                "implementation_effort": "1-3 hours"
            })
        
        # 実行完了改善
        if analysis_result.status != "COMPLETED":
            recommendations.append({
                "priority": "CRITICAL",
                "category": "EXECUTION",
                "description": "Ensure pipeline completes successfully",
                "expected_impact": "Quality score increase +10-15 points",
                "implementation_effort": "Variable"
            })
        
        # コードスタイル改善
        if not analysis_result.formatting_applied or not analysis_result.imports_organized:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "CODE_STYLE",
                "description": "Apply consistent code formatting and import organization",
                "expected_impact": "Quality score increase +3-8 points",
                "implementation_effort": "30 minutes"
            })
        
        return recommendations
    
    def _determine_certification_level(self, quality_score: float) -> Optional[str]:
        """認定レベル決定"""
        for threshold, level in sorted(self.certification_levels.items(), reverse=True):
            if quality_score >= threshold:
                return level
        return None
    
    def _generate_elder_council_report(
        self,
        judgment_id: str,
        analysis_result: StaticAnalysisResult,
        quality_score: float,
        overall_decision: str,
        reasoning: List[str]
    ) -> Dict[str, Any]:
        """Elder Council報告書生成"""
        return {
            "servant_identity": "QualityWatcher (E01)",
            "judgment_id": judgment_id,
            "timestamp": datetime.now().isoformat(),
            "judgment_summary": {
                "decision": overall_decision,
                "quality_score": quality_score,
                "confidence_level": "HIGH" if quality_score > 90 else "MEDIUM"
            },
            "technical_assessment": {
                "pylint_score": analysis_result.pylint_score,
                "type_errors": len(analysis_result.type_errors),
                "pylint_issues": len(analysis_result.pylint_issues),
                "execution_status": analysis_result.status,
                "iterations_required": analysis_result.iterations
            },
            "recommendation_tier": {
                "approval_level": overall_decision,
                "certification_eligible": quality_score >= 95.0,
                "monitoring_required": overall_decision != "ELDER_APPROVED"
            },
            "elder_endorsement": {
                "endorsed_by": "QualityWatcher Elder Servant",
                "endorsement_strength": "STRONG" if overall_decision == "ELDER_APPROVED" else "CONDITIONAL",
                "review_cycle": "QUARTERLY" if overall_decision == "ELDER_APPROVED" else "MONTHLY"
            },
            "judgment_reasoning": reasoning
        }
    
    async def _persist_judgment(self, judgment_result: QualityJudgmentResult):
        """判定結果永続化"""
        # 簡易実装：メモリキャッシュ
        self.judgment_cache[judgment_result.judgment_id] = judgment_result
        self.logger.info(f"📝 Judgment persisted: {judgment_result.judgment_id}")
    
    async def _retrieve_judgment(self, judgment_id: str) -> Optional[QualityJudgmentResult]:
        """判定結果取得"""
        return self.judgment_cache.get(judgment_id)
    
    async def _get_quality_history(self, target_path: str) -> List[Dict]:
        """品質履歴取得"""
        return self.quality_history.get(target_path, [])
    
    async def _update_quality_history(
        self, 
        target_path: str, 
        analysis_result: StaticAnalysisResult,
        quality_score: float
    ):
        """品質履歴更新"""
        if target_path not in self.quality_history:
            self.quality_history[target_path] = []
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "pylint_score": analysis_result.pylint_score,
            "type_errors": len(analysis_result.type_errors),
            "quality_score": quality_score,
            "status": analysis_result.status
        }
        
        self.quality_history[target_path].append(history_entry)
        
        # 履歴は最新20件まで保持
        if len(self.quality_history[target_path]) > 20:
            self.quality_history[target_path] = self.quality_history[target_path][-20:]
    
    async def judge_integrated_quality(
        self,
        analysis_results: Dict[str, Any],
        target_path: str
    ) -> QualityJudgmentResult:
        """統合品質判定（複数解析結果統合）"""
        # 基本的には静的解析を主軸とし、他の結果を補完的に使用
        static_result = analysis_results.get("static_analysis")
        if static_result:
            base_judgment = await self.judge_static_analysis_quality(static_result, target_path)
            
            # 他の解析結果による調整
            security_result = analysis_results.get("security_scan", {})
            performance_result = analysis_results.get("performance_profile", {})
            
            # セキュリティ調整
            if security_result.get("threat_level") in ["HIGH", "CRITICAL"]:
                base_judgment.quality_score *= 0.8  # 20%減点
                base_judgment.overall_decision = "ELDER_REJECTED"
            
            # パフォーマンス調整
            if performance_result.get("efficiency", 100) < 70:
                base_judgment.quality_score *= 0.9  # 10%減点
            
            return base_judgment
        else:
            # 静的解析結果がない場合はエラー判定
            return QualityJudgmentResult(
                judgment_id=f"QW-ERROR-{uuid.uuid4().hex[:8]}",
                overall_decision="ELDER_REJECTED",
                quality_score=0.0,
                iron_will_compliance=False,
                judgment_reasoning=["Static analysis result missing"],
                improvement_recommendations=["Run static analysis first"],
                elder_council_report={},
                certification_level=None,
                next_review_required=True,
                judgment_timestamp=datetime.now().isoformat()
            )