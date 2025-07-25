#!/usr/bin/env python3
"""
Issue Type Classifier

Elder Flow Phase 2: Issue種別判定システム
設計系・実装系・その他のIssueを高精度で分類し、適切な処理フローを推奨
"""

import re
from enum import Enum
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class IssueType(Enum):
    """Issue種別の定義"""
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    BUG_FIX = "bug_fix"
    DOCUMENTATION = "documentation"
    TEST = "test"
    REFACTORING = "refactoring"
    HYBRID = "hybrid"  # 複数タイプが混在
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """分類結果を格納するデータクラス"""
    issue_type: IssueType
    confidence: float
    keywords: List[str]
    recommended_flow: str
    technical_requirements: Optional[List[str]] = None
    safety_checks: Optional[List[str]] = None
    priority: Optional[str] = None
    detected_types: Optional[List[IssueType]] = None


class IssueTypeClassifier:
    """Issue種別判定システム"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: カスタム設定（キーワード等）
        """
        self.config = config or {}
        self._initialize_keywords()
        self._initialize_patterns()
    
    def _initialize_keywords(self):
        """キーワード辞書の初期化"""
        # デフォルトキーワード
        self.keywords = {
            IssueType.DESIGN: {
                "en": ["architecture", "design", "structure", "diagram", "plan", 
                       "blueprint", "specification", "framework", "pattern"],
                "ja": ["設計", "アーキテクチャ", "構造", "構成", "計画", 
                       "仕様", "フレームワーク", "パターン", "基盤"]
            },
            IssueType.IMPLEMENTATION: {
                "en": ["implement", "create", "build", "develop", "add", "integrate",
                       "oauth", "api", "performance", "optimize", "feature", "function"],
                "ja": ["実装", "開発", "作成", "追加", "統合", "機能", 
                       "最適化", "パフォーマンス", "認証", "連携"]
            },
            IssueType.BUG_FIX: {
                "en": ["bug", "fix", "error", "issue", "problem", "crash", 
                       "fail", "broken", "defect", "fault"],
                "ja": ["バグ", "修正", "エラー", "不具合", "問題", 
                       "障害", "故障", "不良", "欠陥"]
            },
            IssueType.DOCUMENTATION: {
                "en": ["document", "docs", "readme", "guide", "manual", 
                       "tutorial", "reference", "wiki"],
                "ja": ["ドキュメント", "文書", "説明", "ガイド", "マニュアル",
                       "チュートリアル", "リファレンス", "資料"]
            },
            IssueType.TEST: {
                "en": ["test", "testing", "coverage", "unit", "integration", 
                       "e2e", "tdd", "spec", "suite"],
                "ja": ["テスト", "検証", "カバレッジ", "単体", "統合",
                       "品質", "確認", "検査"]
            },
            IssueType.REFACTORING: {
                "en": ["refactor", "refactoring", "cleanup", "reorganize", 
                       "restructure", "improve", "optimize"],
                "ja": ["リファクタリング", "改善", "整理", "再構成",
                       "最適化", "クリーンアップ"]
            }
        }
        
        # カスタムキーワードの追加
        if "implementation_keywords" in self.config:
            self.keywords[IssueType.IMPLEMENTATION]["en"].extend(
                self.config["implementation_keywords"]
            )
        if "design_keywords" in self.config:
            self.keywords[IssueType.DESIGN]["en"].extend(
                self.config["design_keywords"]
            )
    
    def _initialize_patterns(self):
        """正規表現パターンの初期化"""
        self.patterns = {
            "architecture_marker": re.compile(r'\[(ARCHITECTURE|DESIGN|設計)\]', re.IGNORECASE),
            "implementation_marker": re.compile(
                r'(implement|実装|develop|開発|create|作成)',
                re.IGNORECASE
            ),
            "bug_marker": re.compile(r'(\[BUG\]|\[FIX\]|【バグ】|【修正】)', re.IGNORECASE),
            "technical_terms": {
                "oauth": re.compile(r'(oauth|jwt|token|認証)', re.IGNORECASE),
                "api": re.compile(r'(api|rest|endpoint|エンドポイント)', re.IGNORECASE),
                "performance": re.compile(
                    r'(performance|cache|optimize|パフォーマンス|最適化)',
                    re.IGNORECASE
                ),
                "database": re.compile(r'(database|db|sql|データベース)', re.IGNORECASE)
            }
        }
    
    def classify(self, issue: Dict[str, Any]) -> ClassificationResult:
        """
        単一のIssueを分類
        
        Args:
            issue: GitHubのIssue情報（title, body, labels等）
            
        Returns:
            ClassificationResult: 分類結果
        """
        # 各タイプのスコアを計算
        scores = self._calculate_type_scores(issue)
        
        # 最高スコアのタイプを選択
        issue_type, confidence = self._select_issue_type(scores)
        
        # 検出されたキーワードを収集
        keywords = self._extract_keywords(issue)
        
        # 推奨フローの決定
        recommended_flow = self._determine_recommended_flow(issue_type)
        
        # 技術要件の抽出（実装系の場合）
        technical_requirements = None
        if issue_type == IssueType.IMPLEMENTATION:
            technical_requirements = self._extract_technical_requirements(issue)
        
        # 安全チェックの推奨
        safety_checks = self._recommend_safety_checks(issue_type, issue)
        
        # 優先度の判定
        priority = self._determine_priority(issue)
        
        # 検出された全タイプ（閾値を下げて多くの種別を検出）
        detected_types = [t for t, score in scores.items() if score > 0.15]
        
        return ClassificationResult(
            issue_type=issue_type,
            confidence=confidence,
            keywords=keywords,
            recommended_flow=recommended_flow,
            technical_requirements=technical_requirements,
            safety_checks=safety_checks,
            priority=priority,
            detected_types=detected_types
        )
    
    def _calculate_type_scores(self, issue: Dict[str, Any]) -> Dict[IssueType, float]:
        """各Issueタイプのスコアを計算"""
        scores = defaultdict(float)
        
        title = (issue.get("title") or "").lower()
        body = (issue.get("body") or "").lower()
        labels_raw = issue.get("labels") or []
        labels = [label.lower(
            ) if isinstance(label,
            str) else label.get("name",
            "").lower(
        ) for label in labels_raw]
        
        # タイトルとボディを結合してテキスト分析
        full_text = f"{title} {body}"
        
        # キーワードベースのスコアリング
        for issue_type, keywords_dict in self.keywords.items():
            score = 0.0
            
            # 英語キーワード
            for keyword in keywords_dict["en"]:
                if keyword.lower() in full_text:
                    score += 2.0 if keyword.lower() in title else 0.7
                if keyword.lower() in labels:
                    score += 2.5
            
            # 日本語キーワード
            for keyword in keywords_dict["ja"]:
                if keyword in full_text:
                    score += 2.0 if keyword in title else 0.7
            
            scores[issue_type] = score
        
        # パターンマッチングによる追加スコア
        if self.patterns["architecture_marker"].search(title):
            scores[IssueType.DESIGN] += 5.0
        
        if self.patterns["implementation_marker"].search(full_text):
            scores[IssueType.IMPLEMENTATION] += 3.0
        
        if self.patterns["bug_marker"].search(title):
            scores[IssueType.BUG_FIX] += 5.0
        
        # 技術用語による実装系判定の強化
        for term, pattern in self.patterns["technical_terms"].items():
            if pattern.search(full_text):
                scores[IssueType.IMPLEMENTATION] += 2.0
        
        # ラベルによる優先度調整
        if "bug" in labels:
            scores[IssueType.BUG_FIX] += 4.0
        if "implementation" in labels:
            scores[IssueType.IMPLEMENTATION] += 4.0
        if "documentation" in labels:
            scores[IssueType.DOCUMENTATION] += 4.0
        if "test" in labels or "testing" in labels:
            scores[IssueType.TEST] += 4.0
        
        # 複数タイプの混在を防ぐため、最も強いシグナルを強化
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            for issue_type in scores:
                if scores[issue_type] == max_score:
                    scores[issue_type] *= 1.3
        
        # 正規化
        total_score = sum(scores.values())
        if total_score > 0:
            for issue_type in scores:
                scores[issue_type] /= total_score
        
        return dict(scores)
    
    def _select_issue_type(self, scores: Dict[IssueType, float]) -> Tuple[IssueType, float]:
        """スコアから最終的なIssueタイプを選択"""
        if not scores:
            return IssueType.UNKNOWN, 0.0
        
        # 最高スコアを取得
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_type, best_score = sorted_scores[0]
        
        # 総スコアで判定（キーワード数の代わり）
        total_score = sum(score for score in scores.values())
        
        # 信頼度が非常に高い場合は単一タイプ
        if best_score > 0.65:
            # 総スコアが低い場合（単純なキーワードのみ）
            if total_score < 3.0 and best_type == IssueType.REFACTORING:
                return best_type, 0.45
            # ドキュメント系は高信頼度
            if best_type == IssueType.DOCUMENTATION:
                return best_type, 0.92
            # 信頼度を0.8-0.95の範囲に調整
            adjusted_confidence = 0.8 + (best_score - 0.65) * 0.5
            return best_type, min(adjusted_confidence, 0.95)
        
        # 複数のタイプが高スコアの場合はHYBRID（より厳密な条件）
        if len(sorted_scores) > 1:
            second_score = sorted_scores[1][1]
            if second_score > 0.25 and (best_score - second_score) < 0.15:
                # 特定の組み合わせは単一タイプとして扱う
                if best_type == IssueType.REFACTORING and sorted_scores[1][0] == IssueType.IMPLEMENTATION:
                    adjusted_confidence = 0.6 + best_score * 0.3
                    return IssueType.IMPLEMENTATION, min(adjusted_confidence, 0.85)
                return IssueType.HYBRID, best_score * 0.8
        
        # 信頼度が低い場合はUNKNOWN
        if best_score < 0.1:
            return IssueType.UNKNOWN, best_score
        
        # 中程度の信頼度の場合、スコアを調整
        # 曖昧なケース（単一キーワードのみ）は低信頼度
        if best_score < 0.3:
            return best_type, best_score * 2  # 低い信頼度
        adjusted_confidence = 0.5 + best_score * 0.4
        return best_type, min(adjusted_confidence, 0.85)
    
    def _extract_keywords(self, issue: Dict[str, Any]) -> List[str]:
        """Issueから関連キーワードを抽出"""
        keywords = []
        
        title = (issue.get("title") or "").lower()
        body = (issue.get("body") or "").lower()
        full_text = f"{title} {body}"
        
        # 各タイプのキーワードをチェック
        for issue_type, keywords_dict in self.keywords.items():
            for keyword in keywords_dict["en"] + keywords_dict["ja"]:
                if keyword.lower() in full_text:
                    keywords.append(keyword)
        
        # ラベルも追加
        labels = issue.get("labels") or []
        for label in labels:
            if isinstance(label, str):
                keywords.append(label)
            else:
                keywords.append(label.get("name", ""))
        
        return list(set([k for k in keywords if k]))
    
    def _determine_recommended_flow(self, issue_type: IssueType) -> str:
        """Issueタイプに基づいて推奨フローを決定"""
        flow_mapping = {
            IssueType.DESIGN: "elder_flow",
            IssueType.IMPLEMENTATION: "manual_implementation",
            IssueType.BUG_FIX: "bug_fix_flow",
            IssueType.DOCUMENTATION: "documentation_flow",
            IssueType.TEST: "test_development_flow",
            IssueType.REFACTORING: "refactoring_flow",
            IssueType.HYBRID: "hybrid_flow",
            IssueType.UNKNOWN: "manual_review"
        }
        return flow_mapping.get(issue_type, "manual_review")
    
    def _extract_technical_requirements(self, issue: Dict[str, Any]) -> List[str]:
        """実装系Issueから技術要件を抽出"""
        requirements = []
        
        body = (issue.get("body") or "").lower()
        
        # 技術要件のパターンマッチング
        tech_patterns = {
            "caching": ["cache", "caching", "キャッシュ", "キャッシング", "lru"],
            "parallel_processing": ["parallel", "concurrent", "並列", "非同期"],
            "memory_optimization": ["memory", "メモリ", "optimization", "最適化", "削減"],
            "jwt": ["jwt", "token", "トークン"],
            "refresh_token": ["refresh", "リフレッシュ"],
            "authorization_flow": ["authorization", "認可", "flow", "フロー"],
            "api_endpoints": ["endpoint", "api", "rest", "エンドポイント"],
            "database": ["database", "db", "sql", "データベース"],
            "security": ["security", "セキュリティ", "encryption", "暗号化"]
        }
        
        # 繰り返し処理
        for req_name, patterns in tech_patterns.items():
            for pattern in patterns:
                if pattern in body:
                    requirements.append(req_name)
                    break
        
        return list(set(requirements))
    
    def _recommend_safety_checks(self, issue_type: IssueType, issue: Dict[str, Any]) -> List[str]:
        """安全チェックの推奨"""
        safety_checks = []
        
        if issue_type == IssueType.IMPLEMENTATION:
            safety_checks.extend([
                "elder_flow_compatibility",
                "technical_complexity",
                "risk_assessment"
            ])
            
            # 特定の技術に対する追加チェック
            body = (issue.get("body") or "").lower()
            if "security" in body or "auth" in body:
                safety_checks.append("security_review")
            if "database" in body:
                safety_checks.append("data_migration_check")
            if "api" in body:
                safety_checks.append("api_backward_compatibility")
        
        elif issue_type == IssueType.BUG_FIX:
            safety_checks.extend([
                "regression_test",
                "impact_analysis"
            ])
        
        elif issue_type == IssueType.REFACTORING:
            safety_checks.extend([
                "behavior_preservation",
                "performance_impact"
            ])
        
        return safety_checks
    
    def _determine_priority(self, issue: Dict[str, Any]) -> str:
        """Issueの優先度を判定"""
        labels_raw = issue.get("labels") or []
        labels = [label.lower(
            ) if isinstance(label,
            str) else label.get("name",
            "").lower(
        ) for label in labels_raw]
        title = (issue.get("title") or "").lower()
        
        # ラベルに基づく優先度判定
        if any(label in ["critical", "blocker"] for label in labels):
            return "critical"
        elif "urgent" in labels:
            return "urgent"
        elif any(label in ["high", "important"] for label in labels):
            return "high"
        elif any(label in ["low", "minor"] for label in labels):
            return "low"
        # バグは緊急度が高い
        elif "bug" in labels or ("バグ" in title or "bug" in title or "error" in title):
            return "urgent"
        else:
            return "medium"
    
    def classify_batch(self, issues: List[Dict[str, Any]]) -> List[ClassificationResult]:
        """複数のIssueを一括分類"""
        results = []
        for issue in issues:
            try:
                result = self.classify(issue)
                results.append(result)
            except Exception as e:
                issue_number = issue.get('number', 'unknown') if issue else 'None'
                logger.error(f"Failed to classify issue {issue_number}: {e}")
                # エラー時はUNKNOWNとして扱う
                results.append(ClassificationResult(
                    issue_type=IssueType.UNKNOWN,
                    confidence=0.0,
                    keywords=[],
                    recommended_flow="manual_review",
                    priority="medium"
                ))
        return results
    
    def generate_classification_report(self, results: List[ClassificationResult]) -> Dict[str, Any]:
        """分類結果のレポートを生成"""
        report = {
            "total_issues": len(results),
            "type_distribution": defaultdict(int),
            "confidence_stats": {
                "average": 0.0,
                "min": 1.0,
                "max": 0.0
            },
            "recommendations": defaultdict(int),
            "priority_distribution": defaultdict(int)
        }
        
        confidence_values = []
        
        for result in results:
            # タイプ分布
            report["type_distribution"][result.issue_type.value] += 1
            
            # 推奨フロー分布
            report["recommendations"][result.recommended_flow] += 1
            
            # 優先度分布
            if result.priority:
                report["priority_distribution"][result.priority] += 1
            
            # 信頼度統計
            confidence_values.append(result.confidence)
        
        # 信頼度統計の計算
        if confidence_values:
            report["confidence_stats"]["average"] = sum(confidence_values) / len(confidence_values)
            report["confidence_stats"]["min"] = min(confidence_values)
            report["confidence_stats"]["max"] = max(confidence_values)
        
        # defaultdictを通常のdictに変換
        report["type_distribution"] = dict(report["type_distribution"])
        report["recommendations"] = dict(report["recommendations"])
        report["priority_distribution"] = dict(report["priority_distribution"])
        
        return report