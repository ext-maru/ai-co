#!/usr/bin/env python3
"""
🏛️ エルダーズギルド Issue品質検証システム

Auto Issue Processor A2Aで実証された高品質基準による
GitHub Issue自動品質チェック・スコア算出システム
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class PriorityLevel(Enum):
    CRITICAL = "critical"
    """PriorityLevelクラス"""
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class QualityScore:
    """QualityScoreクラス"""
    tier1_score: int  # 40点満点
    tier2_score: int  # 35点満点
    tier3_score: int  # 25点満点
    total_score: int  # 100点満点
    quality_level: str
    missing_requirements: List[str]
    recommendations: List[str]


class IssueQualityChecker:
    """Issue品質検証システム"""
    
    def __init__(self):
        # Tier 1 (絶対必須) - 40点満点
        self.tier1_requirements = {
            "root_cause_analysis": {
                "weight": 10,
                "patterns": [
                    r"根本原因",
                    r"root.*cause",
                    r"設計レベル",
                    r"technical.*root",
                    r"システム相互作用"
                ],
                "description": "根本原因分析の実施"
            },
            "technical_details": {
                "weight": 10,
                "patterns": [
                    r"実装仕様",
                    r"implementation.*spec",
                    r"使用技術",
                    r"技術スタック",
                    r"architecture.*pattern"
                ],
                "description": "技術実装方法の具体的記載"
            },
            "phased_implementation": {
                "weight": 10,
                "patterns": [
                    r"Phase\s*\d+",
                    r"段階的",
                    r"実装計画",
                    r"implementation.*plan",
                    r"- \[ \].*Phase"
                ],
                "description": "段階的実装計画の定義"
            },
            "quantitative_success_criteria": {
                "weight": 10,
                "patterns": [
                    r"定量的.*指標",
                    r"\d+%",
                    r"数値.*目標",
                    r"quantitative.*criteria",
                    r"performance.*baseline"
                ],
                "description": "定量的成功基準の設定"
            }
        }
        
        # Tier 2 (高品質) - 35点満点
        self.tier2_requirements = {
            "detailed_effort_estimation": {
                "weight": 10,
                "patterns": [
                    r"工数.*見積",
                    r"effort.*estimation",
                    r"\d+.*日",
                    r"\d+.*週間",
                    r"設計.*\d+.*日"
                ],
                "description": "詳細な工数見積もり"
            },
            "business_value": {
                "weight": 10,
                "patterns": [
                    r"ビジネス.*価値",
                    r"business.*value",
                    r"コスト.*削減",
                    r"効率.*向上",
                    r"competitive.*advantage"
                ],
                "description": "ビジネス価値の明示"
            },
            "test_strategy": {
                "weight": 10,
                "patterns": [
                    r"テスト.*戦略",
                    r"test.*strategy",
                    r"カバレッジ",
                    r"ユニットテスト",
                    r"統合テスト"
                ],
                "description": "テスト戦略の定義"
            },
            "risk_factors": {
                "weight": 5,
                "patterns": [
                    r"リスク.*要因",
                    r"risk.*factors",
                    r"技術的.*リスク",
                    r"影響度",
                    r"mitigation"
                ],
                "description": "リスク要因の特定"
            }
        }
        
        # Tier 3 (卓越性) - 25点満点
        self.tier3_requirements = {
            "comprehensive_nfr": {
                "weight": 10,
                "patterns": [
                    r"非機能.*要件",
                    r"non.*functional",
                    r"セキュリティ.*要件",
                    r"パフォーマンス.*要件",
                    r"scalability"
                ],
                "description": "非機能要件の考慮"
            },
            "future_extensibility": {
                "weight": 8,
                "patterns": [
                    r"拡張性",
                    r"extensibility",
                    r"将来.*拡張",
                    r"scalability",
                    r"future.*proof"
                ],
                "description": "将来の拡張性検討"
            },
            "technical_debt_analysis": {
                "weight": 7,
                "patterns": [
                    r"技術.*負債",
                    r"technical.*debt",
                    r"legacy.*impact",
                    r"refactoring",
                    r"maintenance.*burden"
                ],
                "description": "技術負債影響の分析"
            }
        }
        
    def check_issue_quality(self, issue_content: str, priority: PriorityLevel = PriorityLevel.MEDIUM) -> QualityScore:
        """Issue品質をチェックしてスコアを算出"""
        
        tier1_score = self._check_tier1(issue_content)
        tier2_score = self._check_tier2(issue_content, priority)
        tier3_score = self._check_tier3(issue_content, priority)
        
        total_score = tier1_score + tier2_score + tier3_score
        
        quality_level = self._determine_quality_level(total_score)
        missing_requirements = self._get_missing_requirements(issue_content, priority)
        recommendations = self._generate_recommendations(missing_requirements, priority)
        
        return QualityScore(
            tier1_score=tier1_score,
            tier2_score=tier2_score,
            tier3_score=tier3_score,
            total_score=total_score,
            quality_level=quality_level,
            missing_requirements=missing_requirements,
            recommendations=recommendations
        )
    
    def _check_tier1(self, content: str) -> int:
        """Tier 1要件チェック (40点満点)"""
        score = 0
        for req_name, req_config in self.tier1_requirements.items():
            if self._check_patterns(content, req_config["patterns"]):
                score += req_config["weight"]
        return score
    
    def _check_tier2(self, content: str, priority: PriorityLevel) -> int:
        """Tier 2要件チェック (35点満点)"""
        # High Priority以上で必須
        if priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]:
            score = 0
            for req_name, req_config in self.tier2_requirements.items():
                if self._check_patterns(content, req_config["patterns"]):
                    score += req_config["weight"]
            return score
        else:
            # Medium/Low Priorityでは任意（ボーナス点）
            score = 0
            for req_name, req_config in self.tier2_requirements.items():
                if self._check_patterns(content, req_config["patterns"]):
                    score += req_config["weight"] // 2  # 半分の点数
            return min(score, 35)  # 最大35点
    
    def _check_tier3(self, content: str, priority: PriorityLevel) -> int:
        """Tier 3要件チェック (25点満点)"""
        # Critical Priorityで必須
        if priority == PriorityLevel.CRITICAL:
            score = 0
            for req_name, req_config in self.tier3_requirements.items():
                if self._check_patterns(content, req_config["patterns"]):
                    score += req_config["weight"]
            return score
        else:
            # その他の優先度では任意（ボーナス点）
            score = 0
            for req_name, req_config in self.tier3_requirements.items():
                if self._check_patterns(content, req_config["patterns"]):
                    score += req_config["weight"] // 3  # 3分の1の点数
            return min(score, 25)  # 最大25点
    
    def _check_patterns(self, content: str, patterns: List[str]) -> bool:
        """パターンマッチング確認"""
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _determine_quality_level(self, total_score: int) -> str:
        """品質レベル判定"""
        if total_score >= 90:
            return "⭐⭐⭐⭐⭐ Grand Elder Quality"
        elif total_score >= 75:
            return "⭐⭐⭐⭐ Elder Quality"
        elif total_score >= 60:
            return "⭐⭐⭐ Iron Will Quality"
        elif total_score >= 40:
            return "⭐⭐ Apprentice Quality"
        else:
            return "❌ Quality Standards Not Met"
    
    def _get_missing_requirements(self, content: str, priority: PriorityLevel) -> List[str]:
        """不足要件の特定"""
        missing = []
        
        # Tier 1 (常に必須)
        for req_name, req_config in self.tier1_requirements.items():
            if not self._check_patterns(content, req_config["patterns"]):
                missing.append(f"Tier 1: {req_config['description']}")
        
        # Tier 2 (High Priority以上で必須)
        if priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]:
            for req_name, req_config in self.tier2_requirements.items():
                if not self._check_patterns(content, req_config["patterns"]):
                    missing.append(f"Tier 2: {req_config['description']}")
        
        # Tier 3 (Critical Priorityで必須)
        if priority == PriorityLevel.CRITICAL:
            for req_name, req_config in self.tier3_requirements.items():
                if not self._check_patterns(content, req_config["patterns"]):
                    missing.append(f"Tier 3: {req_config['description']}")
        
        return missing
    
    def _generate_recommendations(self, missing_requirements: List[str], priority: PriorityLevel) -> List[str]:
        """改善提案の生成"""
        recommendations = []
        
        if missing_requirements:
            recommendations.append("🔧 不足要件の追加が必要です:")
            recommendations.extend(f"  - {req}" for req in missing_requirements)
        
        # 優先度別の追加提案
        if priority == PriorityLevel.CRITICAL:
            recommendations.extend([
                "🚨 Critical Priority追加要件:",
                "  - 緊急度分析とロールバック計画の追加",
                "  - 責任者と期限の明確化",
                "  - モニタリング・アラート設定の定義"
            ])
        elif priority == PriorityLevel.HIGH:
            recommendations.extend([
                "⚡ High Priority推奨事項:",
                "  - 包括的なテスト戦略の詳細化",
                "  - セキュリティ考慮事項の追加",
                "  - パフォーマンス影響の評価"
            ])
        
        return recommendations


def analyze_issue_from_file(file_path: str, priority: str = "medium") -> QualityScore:
    """ファイルからIssue内容を読み込んで品質分析"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        priority_level = PriorityLevel(priority.lower())
        checker = IssueQualityChecker()
        return checker.check_issue_quality(content, priority_level)
    
    except FileNotFoundError:
        print(f"❌ ファイルが見つかりません: {file_path}")
        return None
    except ValueError as e:
        print(f"❌ 無効な優先度: {priority}")
        return None


def analyze_issue_from_text(issue_text: str, priority: str = "medium") -> QualityScore:
    """テキストから直接Issue品質を分析"""
    try:
        priority_level = PriorityLevel(priority.lower())
        checker = IssueQualityChecker()
        return checker.check_issue_quality(issue_text, priority_level)
    
    except ValueError as e:
        print(f"❌ 無効な優先度: {priority}")
        return None


def print_quality_report(score: QualityScore):
    """品質レポートの出力"""
    print("\n" + "="*60)
    print("🏛️ エルダーズギルド Issue品質レポート")
    print("="*60)
    
    print(f"\n📊 総合評価: {score.quality_level}")
    print(f"📈 総合スコア: {score.total_score}/100点")
    
    print(f"\n📋 詳細スコア:")
    print(f"  Tier 1 (絶対必須): {score.tier1_score}/40点")
    print(f"  Tier 2 (高品質):   {score.tier2_score}/35点")
    print(f"  Tier 3 (卓越性):   {score.tier3_score}/25点")
    
    if score.missing_requirements:
        print(f"\n⚠️ 不足要件 ({len(score.missing_requirements)}項目):")
        for req in score.missing_requirements:
            print(f"  - {req}")
    
    if score.recommendations:
        print(f"\n💡 改善提案:")
        for rec in score.recommendations:
            print(f"  {rec}")
    
    print("\n" + "="*60)


def main():
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python issue_quality_checker.py <issue_file_path> [priority]")
        print("  python issue_quality_checker.py --text '<issue_text>' [priority]")
        print("")
        print("優先度: critical, high, medium, low (デフォルト: medium)")
        sys.exit(1)
    
    priority = sys.argv[2] if len(sys.argv) > 2 else "medium"
    
    if sys.argv[1] == "--text":
        if len(sys.argv) < 3:
            print("❌ --textオプション使用時はIssueテキストが必要です")
            sys.exit(1)
        
        issue_text = sys.argv[2]
        priority = sys.argv[3] if len(sys.argv) > 3 else "medium"
        score = analyze_issue_from_text(issue_text, priority)
    else:
        file_path = sys.argv[1]
        score = analyze_issue_from_file(file_path, priority)
    
    if score:
        print_quality_report(score)
        
        # 終了コードで品質レベルを表現
        if score.total_score >= 60:
            sys.exit(0)  # 合格
        else:
            sys.exit(1)  # 不合格


if __name__ == "__main__":
    main()