#!/usr/bin/env python3
"""
Implementation Issue Detector

Elder Flow Phase 2: 実装系Issue検出・警告システム
実装系Issueを高精度で検出し、適切な警告と推奨事項を提供する
IssueClassifierとElderFlowSafetyCheckerを統合した高度な検出システム
"""

import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from .issue_classifier import IssueTypeClassifier, IssueType, ClassificationResult
from .elder_flow_safety_check import ElderFlowSafetyChecker, SafetyCheckResult, SafetyLevel

logger = logging.getLogger(__name__)


class WarningLevel(Enum):
    """警告レベル"""
    NONE = "none"          # 警告なし（非実装系）
    LOW = "low"            # 低リスク
    MEDIUM = "medium"      # 中リスク
    HIGH = "high"          # 高リスク
    CRITICAL = "critical"  # 危険レベル


class ImplementationRecommendation(Enum):
    """実装系Issueへの推奨対応"""
    ELDER_FLOW_SAFE = "elder_flow_safe"         # Elder Flow推奨
    PROCEED_WITH_CAUTION = "proceed_with_caution"  # 注意して進行
    MANUAL_REVIEW = "manual_review"             # 手動レビュー推奨
    EXPERT_REQUIRED = "expert_required"         # 専門家レビュー必須


@dataclass
class DetectionResult:
    """検出結果"""
    is_implementation: bool
    warning_level: WarningLevel
    confidence: float
    warnings: List[str]
    recommendation: ImplementationRecommendation
    technical_context: str
    technical_complexity_score: float
    classifier_result: Optional[ClassificationResult] = None
    safety_check_result: Optional[SafetyCheckResult] = None


class ImplementationIssueDetector:
    """実装系Issue検出・警告システム"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: カスタム設定
        """
        self.config = config or {}
        self.classifier = IssueTypeClassifier()
        self.safety_checker = ElderFlowSafetyChecker(config)
        self._initialize_patterns()
        self._initialize_thresholds()
    
    def _initialize_patterns(self):
        """検出パターンの初期化"""
        # デフォルトの高リスクキーワード
        default_high_risk = [
            "authentication", "security", "payment", "production",
            "database", "migration", "breaking", "replace",
            "認証", "セキュリティ", "決済", "本番",
            "データベース", "移行", "破壊的", "置換"
        ]
        
        # カスタムキーワードを追加
        custom_keywords = self.config.get("high_risk_keywords", [])
        self.high_risk_keywords = default_high_risk + custom_keywords
        
        # 技術キーワード
        self.tech_keywords = {
            "continue.dev": ["continue", "continue.dev", "キャッシング"],
            "oauth": ["oauth", "jwt", "token", "authorization"],
            "api": ["api", "graphql", "rest", "endpoint"],
            "database": ["database", "sql", "migration", "schema"],
            "performance": ["performance", "cache", "optimize", "parallel"],
            "frontend": ["react", "vue", "angular", "ui", "ux"]
        }
    
    def _initialize_thresholds(self):
        """閾値の初期化"""
        self.thresholds = self.config.get("warning_thresholds", {
            "critical": 0.7,
            "high": 0.5,
            "medium": 0.3,
            "low": 0.1
        })
    
    def detect(self, issue: Dict[str, Any]) -> DetectionResult:
        """
        単一Issueの実装系検出
        
        Args:
            issue: Issue情報
            
        Returns:
            DetectionResult: 検出結果
        """
        try:
            if not issue:
                logger.error("Null issue provided to detector")
                return self._create_empty_result()
            
            # Issue分類を実行
            classification = self.classifier.classify(issue)
            
            # 実装系でない場合は早期リターン
            if classification.issue_type not in [
                IssueType.IMPLEMENTATION,
                IssueType.REFACTORING,
                IssueType.BUG_FIX
            ]:
                return self._create_non_implementation_result(classification)
            
            # 安全チェックを実行
            safety_result = self.safety_checker.check_elder_flow_safety(issue, classification)
            
            # 詳細分析
            analysis = self._analyze_implementation_issue(issue, classification, safety_result)
            
            # 警告レベルの決定
            warning_level = self._determine_warning_level(analysis)
            
            # 警告メッセージの生成
            warnings = self._generate_warnings(analysis, safety_result)
            
            # 推奨事項の決定
            recommendation = self._determine_recommendation(
                warning_level, safety_result, analysis
            )
            
            # 技術的コンテキストの抽出
            tech_context = self._extract_technical_context(issue, classification)
            
            # タイトルのみの場合は信頼度を下げる
            final_confidence = analysis["confidence"]
            if not issue.get("body"):
                final_confidence *= 0.7
            
            return DetectionResult(
                is_implementation=True,
                warning_level=warning_level,
                confidence=final_confidence,
                warnings=warnings,
                recommendation=recommendation,
                technical_context=tech_context,
                technical_complexity_score=analysis["complexity_score"],
                classifier_result=classification,
                safety_check_result=safety_result
            )
            
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return self._create_empty_result()
    
    def _analyze_implementation_issue(
        self,
        issue: Dict[str, Any],
        classification: ClassificationResult,
        safety_result: SafetyCheckResult
    ) -> Dict[str, Any]:
        """実装系Issueの詳細分析"""
        analysis = {}
        
        # リスク要因の検出
        analysis["risk_factors"] = self._detect_risk_factors(issue)
        
        # 複雑度スコアの計算
        analysis["complexity_score"] = self._calculate_complexity_score(
            issue, classification
        )
        
        # 影響範囲の評価
        analysis["impact_scope"] = self._assess_impact_scope(issue)
        
        # 総合的な信頼度
        analysis["confidence"] = self._calculate_confidence(
            classification, safety_result, analysis
        )
        
        return analysis
    
    def _detect_risk_factors(self, issue: Dict[str, Any]) -> List[str]:
        """リスク要因の検出"""
        risk_factors = []
        
        title = (issue.get("title") or "").lower()
        body = (issue.get("body") or "").lower()
        labels = [label.lower() if isinstance(label, str) else label.get("name", "").lower() 
                 for label in (issue.get("labels") or [])]
        
        # 高リスクキーワードのチェック
        for keyword in self.high_risk_keywords:
            if keyword.lower() in title or keyword.lower() in body:
                risk_factors.append(f"high_risk_keyword:{keyword}")
                # 特定のキーワードに対する追加リスク
                if keyword.lower() in ["payment", "production"]:
                    risk_factors.append("business_critical")
        
        # ラベルからのリスク検出
        risk_labels = ["security", "breaking-change", "major-change", "production"]
        for label in risk_labels:
            if label in labels:
                risk_factors.append(f"risk_label:{label}")
        
        # 特定パターンの検出
        if "replace" in title or "rewrite" in title:
            risk_factors.append("major_replacement")
        
        if "authentication" in body or "oauth" in body:
            risk_factors.append("authentication_system")
        
        if "database" in body and ("migration" in body or "schema" in body):
            risk_factors.append("database_migration")
        
        # 複雑な条件判定
        if "performance" in title or "パフォーマンス" in title or "最適化" in title:
            risk_factors.append("performance_optimization")
        
        if "continue.dev" in title.lower() or "continue.dev" in body.lower():
            risk_factors.append("continue_dev_specific")
        
        return list(set(risk_factors))
    
    def _calculate_complexity_score(
        self,
        issue: Dict[str, Any],
        classification: ClassificationResult
    ) -> float:
        """複雑度スコアの計算"""
        score = 0.0
        
        # 技術要件の数
        tech_reqs = classification.technical_requirements or []
        if len(tech_reqs) >= 5:
            score += 0.3
        elif len(tech_reqs) >= 3:
            score += 0.2
        elif len(tech_reqs) >= 1:
            score += 0.1
        
        # Issue本文の長さ（詳細な仕様の指標）
        body = issue.get("body") or ""
        if len(body) > 500:
            score += 0.2
        elif len(body) > 200:
            score += 0.1
        
        # リスト項目の数（複数のタスク）
        list_items = body.count("-") + body.count("*") + body.count("・")
        if list_items >= 4:  # 閾値を下げる
            score += 0.4  # さらに上げる
        elif list_items >= 3:
            score += 0.3
        elif list_items >= 2:
            score += 0.2
        
        # 技術キーワードの多様性
        tech_diversity = 0
        for tech_type, keywords in self.tech_keywords.items():
            if any(kw.lower() in body.lower() for kw in keywords):
                tech_diversity += 1
        
        if tech_diversity >= 3:
            score += 0.2
        elif tech_diversity >= 2:
            score += 0.1
        
        return min(score, 1.0)
    
    def _assess_impact_scope(self, issue: Dict[str, Any]) -> str:
        """影響範囲の評価"""
        title = (issue.get("title") or "").lower()
        body = (issue.get("body") or "").lower()
        
        # 影響範囲のキーワード
        if any(word in title + body for word in ["entire", "all", "complete", "全体", "すべて"]):
            return "system_wide"
        elif any(word in title + body for word in ["module", "component", "service"]):
            return "module_level"
        elif any(word in title + body for word in ["function", "method", "endpoint"]):
            return "function_level"
        else:
            return "limited"
    
    def _calculate_confidence(
        self,
        classification: ClassificationResult,
        safety_result: SafetyCheckResult,
        analysis: Dict[str, Any]
    ) -> float:
        """総合的な信頼度の計算"""
        # 各コンポーネントの信頼度を統合
        classification_conf = classification.confidence
        safety_conf = safety_result.confidence
        
        # リスク要因の数による調整
        risk_count = len(analysis.get("risk_factors", []))
        risk_adjustment = 1.0 - (risk_count * 0.05)
        risk_adjustment = max(0.7, risk_adjustment)
        
        # 重み付け平均
        confidence = (
            classification_conf * 0.4 +
            safety_conf * 0.4 +
            risk_adjustment * 0.2
        )
        
        return min(confidence, 0.98)
    
    def _determine_warning_level(self, analysis: Dict[str, Any]) -> WarningLevel:
        """警告レベルの決定"""
        risk_count = len(analysis.get("risk_factors", []))
        complexity = analysis.get("complexity_score", 0)
        impact = analysis.get("impact_scope", "limited")
        
        # スコアリング
        score = 0.0
        
        # リスク要因によるスコア
        if risk_count >= 3:
            score += 0.5  # より高く
        elif risk_count >= 2:
            score += 0.4
        elif risk_count >= 1:
            score += 0.3
        
        # 複雑度によるスコア
        score += complexity * 0.3
        
        # 影響範囲によるスコア
        if impact == "system_wide":
            score += 0.3
        elif impact == "module_level":
            score += 0.2
        elif impact == "function_level":
            score += 0.1
        
        # 特別なケースの処理
        # セキュリティ関連は自動的に高レベル
        if any("security" in risk or "authentication" in risk for risk in analysis.get("risk_factors", [])):
            return WarningLevel.CRITICAL if risk_count >= 2 else WarningLevel.HIGH
        
        # ビジネスクリティカル（payment + production）
        if any("business_critical" in risk for risk in analysis.get("risk_factors", [])):
            if any("payment" in risk for risk in analysis.get("risk_factors", [])):
                return WarningLevel.CRITICAL
            return WarningLevel.HIGH
        
        # パフォーマンス最適化も重要
        if any("performance" in risk or "optimization" in risk for risk in analysis.get("risk_factors", [])):
            return WarningLevel.HIGH if complexity > 0.3 else WarningLevel.MEDIUM
        
        # 警告レベルの決定
        if score >= self.thresholds["critical"]:
            return WarningLevel.CRITICAL
        elif score >= self.thresholds["high"]:
            return WarningLevel.HIGH
        elif score >= self.thresholds["medium"]:
            return WarningLevel.MEDIUM
        elif score >= self.thresholds["low"]:
            return WarningLevel.LOW
        else:
            return WarningLevel.LOW
    
    def _generate_warnings(
        self,
        analysis: Dict[str, Any],
        safety_result: SafetyCheckResult
    ) -> List[str]:
        """警告メッセージの生成"""
        warnings = []
        
        # 安全チェックからの警告を追加
        warnings.extend(safety_result.warnings)
        
        # リスク要因に基づく警告
        risk_factors = analysis.get("risk_factors", [])
        for risk in risk_factors:
            if "authentication" in risk:
                warnings.append("Authentication system changes require security review")
            elif "database_migration" in risk:
                warnings.append("Database migration detected - ensure backup and rollback plan")
            elif "major_replacement" in risk:
                warnings.append("Major system replacement - high risk of breaking changes")
        
        # 複雑度に基づく警告
        complexity_score = analysis.get("complexity_score", 0)
        if complexity_score > 0.7:
            warnings.append("Very high complexity detected - consider breaking into smaller tasks")
        elif complexity_score > 0.5:
            warnings.append("High complexity detected - careful planning required")
        
        # 影響範囲に基づく警告
        if analysis.get("impact_scope") == "system_wide":
            warnings.append("System-wide impact - thorough testing required")
        
        # パフォーマンス関連の警告
        if any("performance" in w.lower() for w in warnings):
            warnings.append("Performance optimization requires benchmarking before and after")
        
        return list(set(warnings))  # 重複を除去
    
    def _determine_recommendation(
        self,
        warning_level: WarningLevel,
        safety_result: SafetyCheckResult,
        analysis: Dict[str, Any]
    ) -> ImplementationRecommendation:
        """推奨事項の決定"""
        # 警告レベルと安全性レベルを考慮
        if warning_level == WarningLevel.CRITICAL:
            return ImplementationRecommendation.EXPERT_REQUIRED
        elif warning_level == WarningLevel.HIGH:
            if safety_result.safety_level == SafetyLevel.DANGEROUS:
                return ImplementationRecommendation.EXPERT_REQUIRED
            else:
                return ImplementationRecommendation.MANUAL_REVIEW
        elif warning_level == WarningLevel.MEDIUM:
            return ImplementationRecommendation.MANUAL_REVIEW
        elif warning_level == WarningLevel.LOW:
            if not (analysis.get("complexity_score", 0) < 0.3):
                continue  # Early return to reduce nesting
            # Reduced nesting - original condition satisfied
            if analysis.get("complexity_score", 0) < 0.3:
                return ImplementationRecommendation.PROCEED_WITH_CAUTION
            else:
                return ImplementationRecommendation.MANUAL_REVIEW
        else:
            return ImplementationRecommendation.ELDER_FLOW_SAFE
    
    def _extract_technical_context(
        self,
        issue: Dict[str, Any],
        classification: ClassificationResult
    ) -> str:
        """技術的コンテキストの抽出"""
        contexts = []
        
        body = (issue.get("body") or "").lower()
        title = (issue.get("title") or "").lower()
        full_text = f"{title} {body}"
        
        # 技術キーワードの検出
        for tech_type, keywords in self.tech_keywords.items():
            for keyword in keywords:
                if keyword.lower() in full_text:
                    contexts.append(keyword)
        
        # 追加の技術キーワード（Apolloの前に処理）
        additional_tech = ["websocket", "subscription", "resolver"]
        for tech in additional_tech:
            if tech in full_text:
                contexts.append(tech.capitalize() if tech == "websocket" else tech)
        
        # 技術要件も追加
        if classification.technical_requirements:
            contexts.extend(classification.technical_requirements)
        
        # 特定のフレームワーク・ツールの検出
        frameworks = ["apollo", "stripe", "redis", "webpack", "docker", "kubernetes"]
        for framework in frameworks:
            if framework in full_text:
                contexts.append(framework.capitalize())
        
        # 重複を除去して文字列化（大文字小文字を保持）
        seen = set()
        unique_contexts = []
        for ctx in contexts:
            ctx_lower = ctx.lower()
            if ctx_lower not in seen:
                seen.add(ctx_lower)
                # 特定のキーワードは大文字表記を優先
                if ctx_lower == "continue.dev":
                    unique_contexts.append("Continue.dev")
                elif ctx_lower == "oauth":
                    unique_contexts.append("OAuth")
                elif ctx_lower == "jwt":
                    unique_contexts.append("JWT")
                elif ctx_lower == "graphql":
                    unique_contexts.append("GraphQL")
                elif ctx_lower == "websocket":
                    unique_contexts.append("WebSocket")
                else:
                    unique_contexts.append(ctx)
        
        return ", ".join(unique_contexts[:7])  # 最大7個まで（Apollo含めるため）
    
    def detect_batch(self, issues: List[Dict[str, Any]]) -> List[DetectionResult]:
        """複数Issueの一括検出"""
        results = []
        
        for issue in issues:
            try:
                result = self.detect(issue)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch detection error for issue {issue.get('number', 'unknown')}: {e}")
                results.append(self._create_empty_result())
        
        return results
    
    def generate_detection_report(self, results: List[DetectionResult]) -> Dict[str, Any]:
        """検出結果のレポート生成"""
        report = {
            "total_issues": len(results),
            "implementation_issues": {
                "count": 0,
                "percentage": 0.0
            },
            "warning_distribution": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "none": 0
            },
            "recommendation_distribution": {
                "elder_flow_safe": 0,
                "proceed_with_caution": 0,
                "manual_review": 0,
                "expert_required": 0
            },
            "high_risk_issues": [],
            "average_confidence": 0.0,
            "technical_contexts": []
        }
        
        if not results:
            return report
        
        confidence_sum = 0.0
        impl_count = 0
        
        for i, result in enumerate(results):
            # 実装系カウント
            if result.is_implementation:
                impl_count += 1
                report["technical_contexts"].append(result.technical_context)
            
            # 警告レベル分布
            report["warning_distribution"][result.warning_level.value] += 1
            
            # 推奨事項分布
            report["recommendation_distribution"][result.recommendation.value] += 1
            
            # 信頼度合計
            confidence_sum += result.confidence
            
            # 高リスクIssueの記録
            if result.warning_level in [WarningLevel.CRITICAL, WarningLevel.HIGH]:
                report["high_risk_issues"].append({
                    "index": i,
                    "warning_level": result.warning_level.value,
                    "warnings": result.warnings,
                    "recommendation": result.recommendation.value
                })
        
        # 統計の計算
        report["implementation_issues"]["count"] = impl_count
        report["implementation_issues"]["percentage"] = (
            (impl_count / len(results)) * 100 if results else 0
        )
        report["average_confidence"] = confidence_sum / len(results)
        
        # 技術コンテキストの重複を除去
        report["technical_contexts"] = list(set(report["technical_contexts"]))
        
        return report
    
    def _create_empty_result(self) -> DetectionResult:
        """空の結果を作成"""
        return DetectionResult(
            is_implementation=False,
            warning_level=WarningLevel.NONE,
            confidence=0.0,
            warnings=[],
            recommendation=ImplementationRecommendation.ELDER_FLOW_SAFE,
            technical_context="",
            technical_complexity_score=0.0
        )
    
    def _create_non_implementation_result(
        self,
        classification: ClassificationResult
    ) -> DetectionResult:
        """非実装系の結果を作成"""
        return DetectionResult(
            is_implementation=False,
            warning_level=WarningLevel.NONE,
            confidence=classification.confidence,
            warnings=[],
            recommendation=ImplementationRecommendation.ELDER_FLOW_SAFE,
            technical_context="",
            technical_complexity_score=0.0,
            classifier_result=classification
        )