#!/usr/bin/env python3
"""
Issue Type Classifier V2
Phase 2強化版: Elder Flow適用可否の明確な判定機能追加

主な強化点:
1. 設計系/実装系の明確な判定（Elder Flow適用可否）
2. 信頼度スコアの精度向上
3. 技術キーワード辞書の大幅拡充
4. より詳細な推奨処理フロー
"""

import re
from enum import Enum
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class IssueCategory(Enum):
    """Issue大分類（Elder Flow適用判定用）"""
    DESIGN_ORIENTED = "design_oriented"      # 設計系（Elder Flow推奨）
    IMPLEMENTATION_ORIENTED = "implementation_oriented"  # 実装系（手動処理推奨）
    MAINTENANCE_ORIENTED = "maintenance_oriented"      # 保守系（ケースバイケース）
    UNKNOWN = "unknown"


class IssueType(Enum):
    """Issue詳細種別"""
    # 設計系
    ARCHITECTURE_DESIGN = "architecture_design"
    SYSTEM_DESIGN = "system_design"
    API_DESIGN = "api_design"
    DATABASE_DESIGN = "database_design"
    
    # 実装系
    FEATURE_IMPLEMENTATION = "feature_implementation"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    INTEGRATION = "integration"
    
    # 保守系
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TEST = "test"
    
    # その他
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


@dataclass
class EnhancedClassificationResult:
    """強化版分類結果"""
    # 基本分類
    category: IssueCategory
    issue_type: IssueType
    confidence: float
    
    # Elder Flow判定
    elder_flow_recommended: bool
    elder_flow_reason: str
    
    # 詳細情報
    keywords: List[str]
    recommended_flow: str
    technical_requirements: List[str]
    safety_checks: List[str]
    priority: str
    
    # 追加メタデータ
    detected_technologies: List[str]
    complexity_score: float  # 0-100
    risk_level: str  # low/medium/high/critical


class IssueTypeClassifierV2:
    """Phase 2強化版Issue種別判定システム"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialize_enhanced_keywords()
        self._initialize_technology_patterns()
        self._initialize_elder_flow_rules()
    
    def _initialize_enhanced_keywords(self):
        """強化版キーワード辞書の初期化"""
        self.design_keywords = {
            "architecture": ["architecture", "design", "structure", "diagram", "blueprint",
                           "specification", "framework", "pattern", "schema", "model",
                           "アーキテクチャ", "設計", "構造", "仕様", "フレームワーク"],
            "api_design": ["api design", "endpoint design", "rest design", "graphql design",
                          "interface design", "contract", "API設計", "エンドポイント設計"],
            "database": ["database design", "db schema", "data model", "erd", "normalization",
                        "データベース設計", "スキーマ", "データモデル"]
        }
        
        self.implementation_keywords = {
            "feature": ["implement", "create", "build", "develop", "add feature", "new function",
                       "実装", "開発", "作成", "機能追加", "新機能"],
            "performance": ["optimize", "performance", "speed up", "cache", "parallel", "async",
                           "最適化", "パフォーマンス", "高速化", "キャッシュ", "並列"],
            "integration": ["integrate", "connect", "oauth", "sso", "webhook", "api integration",
                           "統合", "連携", "認証", "接続"]
        }
        
        self.maintenance_keywords = {
            "bug": ["bug", "fix", "error", "issue", "problem", "crash", "broken",
                   "バグ", "修正", "エラー", "不具合", "障害"],
            "refactor": ["refactor", "cleanup", "improve", "reorganize", "technical debt",
                        "リファクタリング", "改善", "整理", "技術的負債"],
            "test": ["test", "testing", "tdd", "coverage", "unit test", "integration test",
                    "テスト", "検証", "カバレッジ", "単体テスト", "統合テスト"],
            "docs": ["document", "docs", "readme", "guide", "manual", "comment",
                    "ドキュメント", "文書", "説明", "ガイド", "コメント"]
        }
    
    def _initialize_technology_patterns(self):
        """技術スタック検出パターンの初期化"""
        self.tech_patterns = {
            # フロントエンド
            "react": re.compile(r'\b(react|jsx|component|hooks?|useState|useEffect)\b', re.I),
            "vue": re.compile(r'\b(vue|vuex|v-model|component)\b', re.I),
            "angular": re.compile(r'\b(angular|ng-|directive|service)\b', re.I),
            
            # バックエンド
            "python": re.compile(r'\b(python|django|flask|fastapi|pytest)\b', re.I),
            "nodejs": re.compile(r'\b(node\.?js|express|npm|yarn|package\.json)\b', re.I),
            "java": re.compile(r'\b(java|spring|maven|gradle|junit)\b', re.I),
            
            # インフラ
            "docker": re.compile(r'(docker|container|dockerfile|compose|コンテナ)', re.I),
            "kubernetes": re.compile(r'\b(kubernetes|k8s|kubectl|pod|deployment)\b', re.I),
            "aws": re.compile(r'\b(aws|ec2|s3|lambda|cloudformation)\b', re.I),
            
            # データベース
            "sql": re.compile(r'\b(sql|mysql|postgresql|database|query)\b', re.I),
            "nosql": re.compile(r'\b(mongodb|elasticsearch|dynamodb)\b', re.I),
            "redis": re.compile(r'\b(redis)\b', re.I),
            
            # その他
            "api": re.compile(r'\b(api|rest|graphql|endpoint|swagger)\b', re.I),
            "auth": re.compile(r'\b(auth|oauth|jwt|sso|authentication|authorization|token)\b', re.I),
            "cache": re.compile(r'\b(cache|caching|memcached|cdn)\b', re.I),
            "performance": re.compile(r'\b(performance|optimize|speed|latency|throughput)\b', re.I),
            
            # 特定ツール
            "continue_dev": re.compile(r'\b(continue\.?dev|continue)\b', re.I),
        }
    
    def _initialize_elder_flow_rules(self):
        """Elder Flow適用ルールの初期化"""
        self.elder_flow_rules = {
            # 設計系は基本的にElder Flow推奨
            IssueType.ARCHITECTURE_DESIGN: {
                "recommended": True,
                "reason": "アーキテクチャ設計書の生成に適している"
            },
            IssueType.SYSTEM_DESIGN: {
                "recommended": True,
                "reason": "システム設計文書の作成に最適"
            },
            IssueType.API_DESIGN: {
                "recommended": True,
                "reason": "API仕様書の自動生成が可能"
            },
            IssueType.DATABASE_DESIGN: {
                "recommended": True,
                "reason": "データベース設計書の作成に適している"
            },
            
            # 実装系は基本的に手動処理推奨
            IssueType.FEATURE_IMPLEMENTATION: {
                "recommended": False,
                "reason": "具体的な技術実装には手動処理が必要"
            },
            IssueType.PERFORMANCE_OPTIMIZATION: {
                "recommended": False,
                "reason": "パフォーマンス最適化は技術固有の知識が必要"
            },
            IssueType.INTEGRATION: {
                "recommended": False,
                "reason": "外部サービス統合は詳細な技術理解が必要"
            },
            
            # 保守系はケースバイケース
            IssueType.BUG_FIX: {
                "recommended": False,
                "reason": "バグ修正は具体的なコード理解が必要"
            },
            IssueType.REFACTORING: {
                "recommended": False,
                "reason": "リファクタリングは既存コードの深い理解が必要"
            },
            IssueType.DOCUMENTATION: {
                "recommended": True,
                "reason": "ドキュメント生成はElder Flowの得意分野"
            },
            IssueType.TEST: {
                "recommended": False,
                "reason": "テスト実装は具体的なコード知識が必要"
            }
        }
    
    def classify(self, issue: Dict[str, Any]) -> EnhancedClassificationResult:
        """Issueを分類し、Elder Flow適用可否を判定"""
        # 基本情報の抽出
        title = issue.get("title", "").lower()
        body = (issue.get("body") or "").lower()
        labels = [label.lower() for label in issue.get("labels", [])]
        full_text = f"{title} {body}"
        
        # 技術スタックの検出
        detected_technologies = self._detect_technologies(full_text)
        
        # スコアリング
        category_scores = self._calculate_category_scores(full_text, labels)
        type_scores = self._calculate_type_scores(full_text, labels, detected_technologies)
        
        # 最終判定
        category = self._determine_category(category_scores)
        issue_type, confidence = self._determine_issue_type(type_scores, category)
        
        # Elder Flow適用判定
        elder_flow_rule = self.elder_flow_rules.get(issue_type, {
            "recommended": False,
            "reason": "不明なIssueタイプのため手動処理を推奨"
        })
        
        # 複雑度とリスクレベルの計算
        complexity_score = self._calculate_complexity(full_text, detected_technologies)
        risk_level = self._calculate_risk_level(issue_type, complexity_score, labels)
        
        # 技術要件の抽出
        technical_requirements = self._extract_technical_requirements(
            full_text, issue_type, detected_technologies
        )
        
        # 安全チェックの決定
        safety_checks = self._determine_safety_checks(issue_type, risk_level)
        
        # 推奨フローの決定
        recommended_flow = self._determine_recommended_flow(
            issue_type, elder_flow_rule["recommended"], confidence
        )
        
        # キーワードの抽出
        keywords = self._extract_keywords(full_text, category, issue_type)
        
        # 優先度の判定
        priority = self._determine_priority(labels, title, risk_level)
        
        return EnhancedClassificationResult(
            category=category,
            issue_type=issue_type,
            confidence=confidence,
            elder_flow_recommended=elder_flow_rule["recommended"],
            elder_flow_reason=elder_flow_rule["reason"],
            keywords=keywords,
            recommended_flow=recommended_flow,
            technical_requirements=technical_requirements,
            safety_checks=safety_checks,
            priority=priority,
            detected_technologies=detected_technologies,
            complexity_score=complexity_score,
            risk_level=risk_level
        )
    
    def _detect_technologies(self, text: str) -> List[str]:
        """テキストから技術スタックを検出"""
        detected = []
        for tech_name, pattern in self.tech_patterns.items():
            if pattern.search(text):
                detected.append(tech_name)
        return detected
    
    def _calculate_category_scores(self, text: str, labels: List[str]) -> Dict[IssueCategory, float]:
        """カテゴリースコアの計算"""
        scores = defaultdict(float)
        
        # キーワードベースのスコアリング
        for keyword_group in self.design_keywords.values():
            for keyword in keyword_group:
                if keyword.lower() in text:
                    scores[IssueCategory.DESIGN_ORIENTED] += 2.0
        
        for keyword_group in self.implementation_keywords.values():
            for keyword in keyword_group:
                if keyword.lower() in text:
                    scores[IssueCategory.IMPLEMENTATION_ORIENTED] += 2.0
        
        for keyword_group in self.maintenance_keywords.values():
            for keyword in keyword_group:
                if keyword.lower() in text:
                    scores[IssueCategory.MAINTENANCE_ORIENTED] += 1.5
        
        # ラベルによる調整
        if any(label in ["design", "architecture", "設計"] for label in labels):
            scores[IssueCategory.DESIGN_ORIENTED] += 5.0
        if any(label in ["implementation", "feature", "実装"] for label in labels):
            scores[IssueCategory.IMPLEMENTATION_ORIENTED] += 5.0
        if any(label in ["bug", "test", "docs", "documentation"] for label in labels):
            scores[IssueCategory.MAINTENANCE_ORIENTED] += 3.0
        
        return dict(scores)
    
    def _calculate_type_scores(self, text: str, labels: List[str], 
                              technologies: List[str]) -> Dict[IssueType, float]:
        """詳細タイプスコアの計算"""
        scores = defaultdict(float)
        
        # 設計系
        if any(kw in text for kw in ["architecture", "アーキテクチャ", "設計"]):
            scores[IssueType.ARCHITECTURE_DESIGN] += 3.0
            # 明示的なアーキテクチャマーカーがある場合は追加ボーナス
            if "[architecture]" in text.lower():
                scores[IssueType.ARCHITECTURE_DESIGN] += 5.0
        if any(kw in text for kw in ["api design", "endpoint", "API設計"]):
            scores[IssueType.API_DESIGN] += 3.0
        if any(kw in text for kw in ["database design", "schema", "データベース設計"]):
            scores[IssueType.DATABASE_DESIGN] += 3.0
        
        # 実装系
        if any(kw in text for kw in ["implement", "create", "build", "実装", "作成"]):
            scores[IssueType.FEATURE_IMPLEMENTATION] += 3.0
        if any(kw in text for kw in ["optimize", "performance", "最適化", "パフォーマンス"]):
            scores[IssueType.PERFORMANCE_OPTIMIZATION] += 3.0
            # Continue.dev + パフォーマンスは強い信号
            if "continue" in technologies:
                scores[IssueType.PERFORMANCE_OPTIMIZATION] += 2.0
        if any(kw in text for kw in ["cache", "caching", "キャッシュ", "並列", "parallel"]):
            scores[IssueType.PERFORMANCE_OPTIMIZATION] += 2.5
        if any(kw in text for kw in ["integrate", "oauth", "webhook", "統合", "連携"]):
            scores[IssueType.INTEGRATION] += 3.0
        
        # 保守系
        if any(kw in text for kw in ["bug", "fix", "error", "バグ", "修正"]):
            scores[IssueType.BUG_FIX] += 3.0
        if any(kw in text for kw in ["refactor", "cleanup", "リファクタリング"]):
            scores[IssueType.REFACTORING] += 2.5
        if any(kw in text for kw in ["test", "testing", "テスト"]):
            scores[IssueType.TEST] += 2.5
        if any(kw in text for kw in ["document", "docs", "readme", "ドキュメント", "更新"]):
            scores[IssueType.DOCUMENTATION] += 2.5
        
        # 技術スタックによる調整
        if "performance" in technologies:
            scores[IssueType.PERFORMANCE_OPTIMIZATION] += 2.0
        if any(tech in technologies for tech in ["api", "auth"]):
            scores[IssueType.INTEGRATION] += 1.5
        
        return dict(scores)
    
    def _determine_category(self, scores: Dict[IssueCategory, float]) -> IssueCategory:
        """カテゴリーの最終決定"""
        if not scores:
            return IssueCategory.UNKNOWN
        
        max_category = max(scores.items(), key=lambda x: x[1])
        if max_category[1] > 0:
            return max_category[0]
        return IssueCategory.UNKNOWN
    
    def _determine_issue_type(self, scores: Dict[IssueType, float], 
                             category: IssueCategory) -> Tuple[IssueType, float]:
        """Issue種別と信頼度の決定"""
        if not scores:
            return IssueType.UNKNOWN, 0.0
        
        # スコアでソート
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_scores or sorted_scores[0][1] == 0:
            return IssueType.UNKNOWN, 0.0
            
        best_type, best_score = sorted_scores[0]
        
        # 信頼度の計算
        total_score = sum(s[1] for s in sorted_scores)
        if total_score == 0:
            return IssueType.UNKNOWN, 0.0
        
        # パフォーマンス最適化の特別処理
        if best_type == IssueType.PERFORMANCE_OPTIMIZATION and best_score >= 3.0:
            # パフォーマンス最適化は高信頼度で判定
            confidence = min(0.85, 0.7 + (best_score / total_score) * 0.3)
            return best_type, confidence
        
        confidence = best_score / total_score
        
        # 複数の高スコアタイプがある場合
        if len(sorted_scores) > 1:
            second_score = sorted_scores[1][1]
            # HYBRID判定の閾値を厳しくする
            if second_score > 0 and (best_score - second_score) / best_score < 0.1:
                return IssueType.HYBRID, confidence * 0.7
        
        # 信頼度の調整（0.3〜0.95の範囲）
        adjusted_confidence = max(0.3, min(0.95, confidence))
        
        return best_type, adjusted_confidence
    
    def _calculate_complexity(self, text: str, technologies: List[str]) -> float:
        """複雑度スコアの計算（0-100）"""
        complexity = 0.0
        
        # テキスト長による基本スコア
        text_length = len(text)
        if text_length > 1000:
            complexity += 20
        elif text_length > 500:
            complexity += 10
        
        # 技術スタック数
        complexity += len(technologies) * 5
        
        # 特定のキーワード
        complex_keywords = ["complex", "difficult", "challenge", "multiple", 
                          "integration", "migration", "refactor", "optimize",
                          "複雑", "難しい", "困難", "複数", "統合", "移行"]
        for keyword in complex_keywords:
            if keyword in text:
                complexity += 8
        
        # パフォーマンスや最適化は複雑度高
        if any(kw in text for kw in ["performance", "optimize", "scale", "最適化"]):
            complexity += 15
        
        return min(100, complexity)
    
    def _calculate_risk_level(self, issue_type: IssueType, 
                             complexity: float, labels: List[str]) -> str:
        """リスクレベルの計算"""
        risk_score = 0
        
        # Issue種別によるリスク
        high_risk_types = [IssueType.PERFORMANCE_OPTIMIZATION, 
                          IssueType.INTEGRATION, IssueType.BUG_FIX]
        if issue_type in high_risk_types:
            risk_score += 30
        
        # 複雑度によるリスク
        if complexity > 70:
            risk_score += 30
        elif complexity > 40:
            risk_score += 15
        
        # ラベルによるリスク
        if any(label in ["critical", "urgent", "security"] for label in labels):
            risk_score += 40
        
        # リスクレベルの決定
        if risk_score >= 60:
            return "critical"
        elif risk_score >= 40:
            return "high"
        elif risk_score >= 20:
            return "medium"
        else:
            return "low"
    
    def _extract_technical_requirements(self, text: str, issue_type: IssueType,
                                       technologies: List[str]) -> List[str]:
        """技術要件の抽出"""
        requirements = []
        
        # パフォーマンス関連
        if issue_type == IssueType.PERFORMANCE_OPTIMIZATION or issue_type == IssueType.FEATURE_IMPLEMENTATION:
            if any(kw in text for kw in ["cache", "caching", "キャッシュ", "キャッシング"]):
                requirements.append("caching_implementation")
            if "parallel" in text or "concurrent" in text or "並列" in text:
                requirements.append("parallel_processing")
            if "memory" in text or "メモリ" in text:
                requirements.append("memory_optimization")
            if "async" in text or "非同期" in text:
                requirements.append("asynchronous_processing")
        
        # 認証関連
        if "auth" in technologies or any(kw in text.lower() for kw in ["oauth", "jwt", "認証"]):
            if "oauth" in text.lower():
                requirements.append("oauth_implementation")
            if "jwt" in text.lower():
                requirements.append("jwt_tokens")
            if "sso" in text.lower():
                requirements.append("single_sign_on")
        
        # API関連
        if "api" in technologies or issue_type == IssueType.API_DESIGN:
            if "rest" in text:
                requirements.append("rest_api")
            if "graphql" in text:
                requirements.append("graphql_api")
            if "endpoint" in text:
                requirements.append("api_endpoints")
        
        # データベース関連
        if "sql" in technologies or "nosql" in technologies:
            requirements.append("database_operations")
            if "migration" in text:
                requirements.append("data_migration")
        
        # セキュリティ関連
        if "security" in text:
            requirements.append("security_implementation")
            if "encryption" in text:
                requirements.append("data_encryption")
        
        return requirements
    
    def _determine_safety_checks(self, issue_type: IssueType, risk_level: str) -> List[str]:
        """必要な安全チェックの決定"""
        checks = []
        
        # 基本チェック
        checks.append("code_review")
        
        # リスクレベルによるチェック
        if risk_level in ["high", "critical"]:
            checks.append("security_review")
            checks.append("performance_testing")
        
        # Issue種別によるチェック
        if issue_type == IssueType.FEATURE_IMPLEMENTATION:
            checks.extend(["unit_testing", "integration_testing"])
        elif issue_type == IssueType.PERFORMANCE_OPTIMIZATION:
            checks.extend(["performance_benchmarking", "load_testing"])
        elif issue_type == IssueType.INTEGRATION:
            checks.extend(["api_testing", "security_audit"])
        elif issue_type == IssueType.BUG_FIX:
            checks.extend(["regression_testing", "root_cause_analysis"])
        
        return list(set(checks))  # 重複を除去
    
    def _determine_recommended_flow(self, issue_type: IssueType, 
                                   elder_flow_recommended: bool,
                                   confidence: float) -> str:
        """推奨処理フローの決定"""
        # 信頼度が低い場合は手動レビュー
        if confidence < 0.3:
            return "manual_review_required"
        
        # Elder Flow推奨の場合
        if elder_flow_recommended:
            if confidence > 0.8:
                return "elder_flow_auto"
            else:
                return "elder_flow_with_review"
        
        # 手動処理推奨の場合
        if issue_type in [IssueType.BUG_FIX, IssueType.PERFORMANCE_OPTIMIZATION]:
            return "manual_implementation_required"
        elif issue_type == IssueType.FEATURE_IMPLEMENTATION:
            return "manual_development_with_assistance"
        else:
            return "manual_review_and_decision"
    
    def _extract_keywords(self, text: str, category: IssueCategory, 
                         issue_type: IssueType) -> List[str]:
        """関連キーワードの抽出"""
        keywords = []
        
        # カテゴリー別キーワード抽出
        if category == IssueCategory.DESIGN_ORIENTED:
            for keyword_group in self.design_keywords.values():
                for keyword in keyword_group:
                    if keyword.lower() in text:
                        keywords.append(keyword)
        elif category == IssueCategory.IMPLEMENTATION_ORIENTED:
            for keyword_group in self.implementation_keywords.values():
                for keyword in keyword_group:
                    if keyword.lower() in text:
                        keywords.append(keyword)
        elif category == IssueCategory.MAINTENANCE_ORIENTED:
            for keyword_group in self.maintenance_keywords.values():
                for keyword in keyword_group:
                    if keyword.lower() in text:
                        keywords.append(keyword)
        
        return list(set(keywords))[:10]  # 最大10個まで
    
    def _determine_priority(self, labels: List[str], title: str, 
                           risk_level: str) -> str:
        """優先度の判定"""
        # ラベルベース
        if any(label in ["critical", "urgent", "blocker"] for label in labels):
            return "critical"
        elif any(label in ["high", "important"] for label in labels):
            return "high"
        elif any(label in ["low", "minor"] for label in labels):
            return "low"
        
        # リスクレベルベース
        if risk_level == "critical":
            return "high"
        elif risk_level == "high":
            return "medium"
        
        # デフォルト
        return "medium"
    
    def generate_summary_report(self, result: EnhancedClassificationResult) -> str:
        """分類結果の要約レポート生成"""
        report = f"""
# Issue分類結果サマリー

## 基本分類
- **カテゴリー**: {result.category.value}
- **詳細タイプ**: {result.issue_type.value}
- **信頼度**: {result.confidence:.2%}

## Elder Flow判定
- **推奨**: {'✅ Yes' if result.elder_flow_recommended else '❌ No'}
- **理由**: {result.elder_flow_reason}

## 詳細情報
- **優先度**: {result.priority}
- **複雑度スコア**: {result.complexity_score:.1f}/100
- **リスクレベル**: {result.risk_level}
- **推奨処理フロー**: {result.recommended_flow}

## 技術情報
- **検出技術**: {', '.join(result.detected_technologies) if result.detected_technologies else 'なし'}
- **技術要件**: {', '.join(result.technical_requirements) if result.technical_requirements else 'なし'}
- **必要な安全チェック**: {', '.join(result.safety_checks)}

## キーワード
{', '.join(result.keywords) if result.keywords else 'なし'}
"""
        return report.strip()


# 使用例
if __name__ == "__main__":
    classifier = IssueTypeClassifierV2()
    
    # テストケース
    test_issues = [
        {
            "title": "⚡ Continue.dev Phase 2 - パフォーマンス最適化",
            "body": "Continue.devのキャッシング機能実装と並列処理最適化を行います。",
            "labels": ["enhancement", "priority:low"]
        },
        {
            "title": "[ARCHITECTURE] AI Companyシステム再設計提案",
            "body": "現在のモノリシックアーキテクチャをマイクロサービスに移行する設計提案",
            "labels": ["design", "architecture"]
        }
    ]
    
    for issue in test_issues:
        result = classifier.classify(issue)
        print(f"\nIssue: {issue['title']}")
        print(f"Elder Flow推奨: {'Yes' if result.elder_flow_recommended else 'No'}")
        print(f"理由: {result.elder_flow_reason}")
        print(f"信頼度: {result.confidence:.2%}")