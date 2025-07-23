#!/usr/bin/env python3
"""
Elder Flow Safety Check System

Elder Flow Phase 2: Elder Flow適用前の安全チェック機能
実装系Issueに対してElder Flowを適用する前の安全性を評価し、
適切な推奨事項を提供する
"""

import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from .issue_classifier import IssueType, ClassificationResult

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """安全性レベル"""
    SAFE = "safe"       # 安全：Elder Flow推奨
    WARNING = "warning"  # 警告：注意して進行
    DANGEROUS = "dangerous"  # 危険：Elder Flow非推奨


class ElderFlowRecommendation(Enum):
    """Elder Flow適用推奨度"""
    PROCEED = "proceed"  # 実行推奨
    CAUTION = "caution"  # 注意して実行
    BLOCK = "block"      # 実行非推奨


@dataclass
class SafetyCheckResult:
    """安全チェック結果"""
    safety_level: SafetyLevel
    recommendation: ElderFlowRecommendation
    confidence: float
    warnings: List[str]
    reasoning: str
    alternative_suggestions: Optional[List[str]] = None


class ElderFlowSafetyChecker:
    """Elder Flow安全チェックシステム"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: カスタム設定
        """
        self.config = config or {}
        self._initialize_risk_patterns()
        self._initialize_thresholds()
    
    def _initialize_risk_patterns(self):
        """リスクパターンの初期化"""
        default_keywords = [
            "security", "authentication", "oauth", "jwt", "token",
            "database", "migration", "schema", "production",
            "payment", "billing", "sensitive", "encryption",
            "セキュリティ", "認証", "本番", "決済", "機密"
        ]
        
        # カスタムキーワードがある場合はデフォルトに追加
        custom_keywords = self.config.get("high_risk_keywords", [])
        self.high_risk_keywords = default_keywords + custom_keywords
        
        self.complexity_indicators = {
            "high": ["complex", "integrate", "migrate", "refactor", "optimize", 
                    "parallel", "distributed", "複雑", "統合", "移行", "最適化"],
            "medium": ["modify", "update", "enhance", "improve", "追加", "更新", "改善"],
            "low": ["add", "create", "simple", "basic", "fix", "追加", "作成", "簡単", "修正"]
        }
    
    def _initialize_thresholds(self):
        """閾値の初期化"""
        self.thresholds = {
            "complexity": self.config.get("complexity_thresholds", {
                "low": 0.3,
                "medium": 0.6,
                "high": 0.8
            }),
            "compatibility": {
                "safe": 0.8,
                "warning": 0.5,
                "dangerous": 0.3
            },
            "confidence": {
                "high": 0.85,
                "medium": 0.7,
                "low": 0.5
            }
        }
    
    def check_elder_flow_safety(
        self, 
        issue: Dict[str, Any], 
        classification: ClassificationResult
    ) -> SafetyCheckResult:
        """
        単一IssueのElder Flow適用安全性をチェック
        
        Args:
            issue: Issue情報
            classification: Issue分類結果
            
        Returns:
            SafetyCheckResult: 安全チェック結果
        """
        try:
            # 基本的な安全性評価
            if classification.issue_type == IssueType.DESIGN:
                return self._create_safe_result(
                    "Design issues are well-suited for Elder Flow"
                )
            
            # UNKNOWNタイプは警告として扱う
            if classification.issue_type == IssueType.UNKNOWN:
                return SafetyCheckResult(
                    safety_level=SafetyLevel.WARNING,
                    recommendation=ElderFlowRecommendation.CAUTION,
                    confidence=0.5,
                    warnings=["Issue type could not be determined with confidence"],
                    reasoning="Unknown issue type - manual review recommended",
                    alternative_suggestions=["Manual classification and review recommended"]
                )
            
            # 詳細な分析を実行
            analysis = self._analyze_issue(issue, classification)
            
            # 安全性レベルを決定
            safety_level = self._determine_safety_level(analysis)
            
            # 推奨事項を決定
            recommendation = self._determine_recommendation(safety_level, analysis)
            
            # 警告メッセージを生成
            warnings = self._generate_warnings(analysis)
            
            # 理由を構築
            reasoning = self._build_reasoning(analysis, safety_level)
            
            # 代替案を生成
            alternatives = None
            if safety_level != SafetyLevel.SAFE:
                alternatives = self._generate_alternative_suggestions(
                    classification, analysis
                )
            
            # 分類の信頼度を使用（より高い値を保証）
            final_confidence = max(
                analysis.get("confidence", 0.7),
                analysis.get("classification_confidence", 0.7) * 0.9
            )
            
            return SafetyCheckResult(
                safety_level=safety_level,
                recommendation=recommendation,
                confidence=final_confidence,
                warnings=warnings,
                reasoning=reasoning,
                alternative_suggestions=alternatives
            )
            
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            return self._create_caution_result(
                "Error during safety check - proceed with caution"
            )
    
    def _analyze_issue(
        self, 
        issue: Dict[str, Any], 
        classification: ClassificationResult
    ) -> Dict[str, Any]:
        """Issueの詳細分析"""
        analysis = {}
        
        # 技術的複雑度の評価
        analysis["technical_complexity"] = self._assess_technical_complexity({
            "technical_requirements": classification.technical_requirements,
            "keywords": classification.keywords
        })
        
        # リスク要因の検出
        analysis["risk_factors"] = self._detect_risk_factors({
            "title": issue.get("title", ""),
            "body": issue.get("body", ""),
            "technical_requirements": classification.technical_requirements
        })
        
        # Elder Flow互換性の計算
        analysis["elder_flow_compatibility"] = self._calculate_elder_flow_compatibility(
            classification, analysis
        )
        
        # 信頼度の計算
        analysis["confidence"] = self._calculate_confidence(
            classification, analysis
        )
        
        # 分類の信頼度も保持
        analysis["classification_confidence"] = classification.confidence
        
        return analysis
    
    def _assess_technical_complexity(self, data: Dict[str, Any]) -> float:
        """技術的複雑度の評価"""
        score = 0.0
        
        # 技術要件の数による評価
        tech_reqs = data.get("technical_requirements") or []
        if len(tech_reqs) >= 5:
            score += 0.4
        elif len(tech_reqs) >= 3:
            score += 0.25
        elif len(tech_reqs) >= 1:
            score += 0.1
        
        # 複雑度キーワードによる評価
        keywords = [k.lower() for k in (data.get("keywords") or [])]
        
        for level, indicators in self.complexity_indicators.items():
            for indicator in indicators:
                if any(indicator in keyword for keyword in keywords):
                    if level == "high":
                        score += 0.2  # 少し減らす
                    elif level == "medium":
                        score += 0.1
                    break  # 各レベルで最初のマッチのみカウント
        
        # 特定の高複雑度要件
        high_complexity_techs = ["security", "oauth", "database", "parallel_processing"]
        for tech in high_complexity_techs:
            if tech in tech_reqs:
                score += 0.15
        
        return min(score, 1.0)
    
    def _detect_risk_factors(self, data: Dict[str, Any]) -> List[str]:
        """リスク要因の検出"""
        risk_factors = []
        
        title = (data.get("title") or "").lower()
        body = (data.get("body") or "").lower()
        tech_reqs = data.get("technical_requirements") or []
        
        # 高リスクキーワードのチェック
        for keyword in self.high_risk_keywords:
            if keyword.lower() in title or keyword.lower() in body:
                if keyword in ["security", "authentication", "oauth", "セキュリティ", "認証"]:
                    risk_factors.append("security_critical")
                elif keyword in ["database", "migration", "schema", "データベース", "移行"]:
                    risk_factors.append("data_migration")
                elif keyword in ["production", "payment", "billing", "本番", "決済"]:
                    risk_factors.append("business_critical")
                else:
                    # カスタムキーワードの場合
                    risk_factors.append(f"custom_risk_{keyword}")
        
        # 技術要件からのリスク検出
        if "security" in tech_reqs or "oauth" in tech_reqs or "jwt" in tech_reqs:
            risk_factors.append("authentication_system")
        
        if "database" in tech_reqs:
            risk_factors.append("data_operations")
        
        if "parallel_processing" in tech_reqs or "caching" in tech_reqs:
            risk_factors.append("performance_critical")
        
        return list(set(risk_factors))
    
    def _calculate_elder_flow_compatibility(
        self, 
        classification: ClassificationResult,
        analysis: Dict[str, Any]
    ) -> float:
        """Elder Flow互換性の計算"""
        # 基本スコア（Issueタイプによる）
        base_scores = {
            IssueType.DESIGN: 0.95,
            IssueType.DOCUMENTATION: 0.9,
            IssueType.TEST: 0.7,
            IssueType.BUG_FIX: 0.6,
            IssueType.REFACTORING: 0.5,
            IssueType.IMPLEMENTATION: 0.3,
            IssueType.HYBRID: 0.4,
            IssueType.UNKNOWN: 0.2  # UNKNOWNは少し高く（完全に危険でないように）
        }
        
        score = base_scores.get(classification.issue_type, 0.3)
        
        # 技術的複雑度による減点
        complexity = analysis.get("technical_complexity", 0)
        if complexity > 0.7:
            score *= 0.5
        elif complexity > 0.5:
            score *= 0.7
        elif complexity > 0.3:
            score *= 0.85
        
        # リスク要因による減点
        risk_count = len(analysis.get("risk_factors", []))
        if risk_count >= 3:
            score *= 0.4
        elif risk_count >= 2:
            score *= 0.6
        elif risk_count >= 1:
            score *= 0.8
        
        # 分類信頼度による調整
        if classification.confidence < 0.7:
            score *= 0.9
        
        return max(0.0, min(score, 1.0))
    
    def _calculate_confidence(
        self,
        classification: ClassificationResult,
        analysis: Dict[str, Any]
    ) -> float:
        """総合的な信頼度の計算"""
        # 分類信頼度を基準
        confidence = classification.confidence
        
        # Elder Flow互換性による調整
        compatibility = analysis.get("elder_flow_compatibility", 0.5)
        if compatibility < 0.3:
            confidence *= 0.9
        elif compatibility > 0.8:
            confidence *= 1.05
        
        # 複雑度による調整
        complexity = analysis.get("technical_complexity", 0.5)
        if complexity > 0.8:
            confidence *= 0.95
        
        # 最小値を0.5、最大値を0.98に制限
        return max(0.5, min(confidence, 0.98))
    
    def _determine_safety_level(self, analysis: Dict[str, Any]) -> SafetyLevel:
        """安全性レベルの決定"""
        compatibility = analysis.get("elder_flow_compatibility", 0)
        risk_count = len(analysis.get("risk_factors", []))
        complexity = analysis.get("technical_complexity", 0)
        
        # 高リスク条件
        if (compatibility < self.thresholds["compatibility"]["dangerous"] or
            risk_count >= 3 or
            complexity > self.thresholds["complexity"]["high"]):
            return SafetyLevel.DANGEROUS
        
        # 警告条件
        elif (compatibility < self.thresholds["compatibility"]["warning"] or
              risk_count >= 1 or
              complexity > self.thresholds["complexity"]["medium"]):
            return SafetyLevel.WARNING
        
        # 安全条件
        else:
            return SafetyLevel.SAFE
    
    def _determine_recommendation(
        self, 
        safety_level: SafetyLevel,
        analysis: Dict[str, Any]
    ) -> ElderFlowRecommendation:
        """推奨事項の決定"""
        if safety_level == SafetyLevel.SAFE:
            return ElderFlowRecommendation.PROCEED
        elif safety_level == SafetyLevel.WARNING:
            # 追加条件でCAUTIONかBLOCKを決定
            compatibility = analysis.get("elder_flow_compatibility", 0)
            complexity = analysis.get("technical_complexity", 0)
            risk_count = len(analysis.get("risk_factors", []))
            
            # より寛容な判定（単純な実装はCAUTION）
            # 閾値を調整 - 単純なAPIエンドポイントはCAUTION
            if compatibility >= 0.25 and complexity <= 0.5 and risk_count == 0:
                return ElderFlowRecommendation.CAUTION
            else:
                return ElderFlowRecommendation.BLOCK
        else:  # DANGEROUS
            return ElderFlowRecommendation.BLOCK
    
    def _generate_warnings(self, analysis: Dict[str, Any]) -> List[str]:
        """警告メッセージの生成"""
        warnings = []
        
        # 複雑度警告
        complexity = analysis.get("technical_complexity", 0)
        if complexity > self.thresholds["complexity"]["high"]:
            warnings.append("Very high technical complexity detected")
        elif complexity > self.thresholds["complexity"]["medium"]:
            warnings.append("Moderate to high technical complexity")
        
        # リスク警告
        risk_factors = analysis.get("risk_factors", [])
        risk_messages = {
            "security_critical": "Security-critical implementation detected",
            "authentication_system": "Authentication system modifications detected",
            "data_migration": "Database or data migration operations detected",
            "business_critical": "Business-critical operations detected",
            "data_operations": "Database operations detected",
            "performance_critical": "Performance-critical operations detected"
        }
        
        for risk in risk_factors:
            if risk in risk_messages:
                warnings.append(risk_messages[risk])
        
        # Elder Flow互換性警告
        compatibility = analysis.get("elder_flow_compatibility", 0)
        if compatibility < 0.3:
            warnings.append("Low Elder Flow compatibility - manual implementation strongly recommended" \
                "Low Elder Flow compatibility - manual implementation strongly recommended")
        elif compatibility < 0.5:
            warnings.append("Limited Elder Flow compatibility - proceed with caution")
        
        return warnings
    
    def _build_reasoning(
        self, 
        analysis: Dict[str, Any],
        safety_level: SafetyLevel
    ) -> str:
        """理由の構築"""
        reasons = []
        
        # 複雑度に基づく理由
        complexity = analysis.get("technical_complexity", 0)
        if complexity > 0.7:
            reasons.append("high technical complexity")
        elif complexity > 0.4:
            reasons.append("moderate technical complexity")
        else:
            reasons.append("low technical complexity")
        
        # リスクに基づく理由
        risk_count = len(analysis.get("risk_factors", []))
        if risk_count > 0:
            reasons.append(f"{risk_count} risk factor(s) identified")
        
        # 互換性に基づく理由
        compatibility = analysis.get("elder_flow_compatibility", 0)
        if compatibility < 0.3:
            reasons.append("poor Elder Flow compatibility")
        elif compatibility > 0.7:
            reasons.append("good Elder Flow compatibility")
        
        # 安全レベルに基づく結論
        if safety_level == SafetyLevel.SAFE:
            conclusion = "Safe for Elder Flow execution"
        elif safety_level == SafetyLevel.WARNING:
            conclusion = "Proceed with caution - manual review recommended"
        else:
            conclusion = "Too complex for Elder Flow - manual implementation recommended"
        
        reasoning = f"Based on {', '.join(reasons)}: {conclusion}"
        return reasoning
    
    def _generate_alternative_suggestions(
        self,
        classification: ClassificationResult,
        analysis: Dict[str, Any]
    ) -> List[str]:
        """代替案の生成"""
        suggestions = []
        
        # 基本的な代替案
        if classification.issue_type == IssueType.IMPLEMENTATION:
            suggestions.append("Consider manual implementation with expert review")
            suggestions.append("Break down into smaller, manageable tasks")
        
        # リスクに基づく提案
        risk_factors = analysis.get("risk_factors", [])
        if "security_critical" in risk_factors:
            suggestions.append("Security expert review required before implementation")
        if "data_migration" in risk_factors:
            suggestions.append("Create backup and rollback plan before proceeding")
        if "performance_critical" in risk_factors:
            suggestions.append("Implement performance benchmarks and monitoring")
        
        # 複雑度に基づく提案
        complexity = analysis.get("technical_complexity", 0)
        if complexity > 0.6:  # 閾値を下げる
            suggestions.append("Consider phased or incremental implementation approach")
            suggestions.append("Create detailed technical design document first")
        
        # Elder Flow部分適用の提案
        if analysis.get("elder_flow_compatibility", 0) > 0.3:
            suggestions.append("Use Elder Flow for design phase only, then manual implementation")
        
        return suggestions
    
    def check_batch(
        self, 
        issues_with_classifications: List[Dict[str, Any]]
    ) -> List[SafetyCheckResult]:
        """複数Issueの一括安全チェック"""
        results = []
        
        for item in issues_with_classifications:
            try:
                issue = {k: v for k, v in item.items() if k != "classification"}
                classification = item.get("classification")
                
                if classification:
                    result = self.check_elder_flow_safety(issue, classification)
                else:
                    result = self._create_caution_result(
                        "No classification provided"
                    )
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Batch safety check error: {e}")
                results.append(self._create_caution_result(
                    f"Error during safety check: {str(e)}"
                ))
        
        return results
    
    def generate_safety_report(
        self, 
        results: List[SafetyCheckResult]
    ) -> Dict[str, Any]:
        """安全性レポートの生成"""
        report = {
            "total_checks": len(results),
            "safety_distribution": {
                "safe": 0,
                "warning": 0,
                "dangerous": 0
            },
            "recommendation_distribution": {
                "proceed": 0,
                "caution": 0,
                "block": 0
            },
            "average_confidence": 0.0,
            "high_risk_issues": [],
            "suggested_manual_implementations": []
        }
        
        if not results:
            return report
        
        confidence_sum = 0.0
        
        for i, result in enumerate(results):
            # 安全性分布
            report["safety_distribution"][result.safety_level.value] += 1
            
            # 推奨事項分布
            report["recommendation_distribution"][result.recommendation.value] += 1
            
            # 信頼度合計
            confidence_sum += result.confidence
            
            # 高リスクIssueの記録
            if result.safety_level == SafetyLevel.DANGEROUS:
                report["high_risk_issues"].append({
                    "index": i,
                    "warnings": result.warnings,
                    "reasoning": result.reasoning
                })
            
            # 手動実装推奨の記録
            if result.recommendation == ElderFlowRecommendation.BLOCK:
                report["suggested_manual_implementations"].append({
                    "index": i,
                    "alternatives": result.alternative_suggestions
                })
        
        # 平均信頼度
        report["average_confidence"] = confidence_sum / len(results)
        
        return report
    
    def _create_safe_result(self, reasoning: str) -> SafetyCheckResult:
        """安全な結果の作成"""
        return SafetyCheckResult(
            safety_level=SafetyLevel.SAFE,
            recommendation=ElderFlowRecommendation.PROCEED,
            confidence=0.95,
            warnings=[],
            reasoning=reasoning,
            alternative_suggestions=None
        )
    
    def _create_caution_result(self, reasoning: str) -> SafetyCheckResult:
        """注意結果の作成"""
        return SafetyCheckResult(
            safety_level=SafetyLevel.WARNING,
            recommendation=ElderFlowRecommendation.CAUTION,
            confidence=0.5,
            warnings=["Unable to perform complete safety analysis"],
            reasoning=reasoning,
            alternative_suggestions=["Manual review recommended"]
        )