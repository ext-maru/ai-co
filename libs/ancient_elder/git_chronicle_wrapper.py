"""
📚 Git Chronicle Wrapper for Ancient Elder System
AncientElderBase互換のラッパークラス
"""

from pathlib import Path
import sys
from typing import Dict, Any, Optional

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.base import AncientElderBase, AuditResult, ViolationSeverity


class GitChronicle(AncientElderBase):
    """
    📚 Git年代記魔法のAncientElderBase互換ラッパー
    """
    
    def __init__(self):
        """初期化メソッド"""
        super().__init__(specialty="git_chronicle")
        
    async def audit(self, target: Dict[str, Any]) -> AuditResult:
        """
        監査を実行する
        
        Args:
            target: 監査対象の情報
            
        Returns:
            AuditResult: 監査結果
        """
        result = AuditResult()
        result.auditor_name = self.name
        
        try:
            # 実装を使用
            from libs.ancient_elder.git_chronicle_impl import GitChronicleImpl
            impl = GitChronicleImpl(Path(target.get("path", ".")))
            
            # 分析期間
            days = target.get("time_window_days", 30)
            
            # コミットメッセージ分析
            commit_analysis = impl.analyze_commit_messages(days)
            for violation in commit_analysis.get("violations", []):
                result.add_violation(
                    severity=ViolationSeverity[violation["severity"]],
                    title=violation.get("type", "Git violation"),
                    description=violation["description"],
                    location=violation.get("location"),
                    suggested_fix=violation.get("suggested_fix"),
                    metadata={"category": "git_history", **violation}
                )
            
            # ブランチ戦略分析
            branch_analysis = impl.analyze_branch_strategy()
            for violation in branch_analysis.get("violations", []):
                result.add_violation(
                    severity=ViolationSeverity[violation["severity"]],
                    title=violation.get("type", "Branch violation"),
                    description=violation["description"],
                    location=violation.get("location"),
                    suggested_fix=violation.get("suggested_fix"),
                    metadata={"category": "branch_strategy", **violation}
                )
            
            # マージコンフリクトチェック
            conflict_analysis = impl.check_merge_conflicts()
            for violation in conflict_analysis.get("violations", []):
                result.add_violation(
                    severity=ViolationSeverity[violation["severity"]],
                    title=violation.get("type", "Conflict"),
                    description=violation["description"],
                    location=violation.get("location"),
                    suggested_fix=violation.get("suggested_fix"),
                    metadata={"category": "merge_conflict", **violation}
                )
            
            # コミット頻度分析
            frequency_analysis = impl.analyze_commit_frequency(days)
            for violation in frequency_analysis.get("violations", []):
                result.add_violation(
                    severity=ViolationSeverity[violation["severity"]],
                    title=violation.get("type", "Frequency issue"),
                    description=violation["description"],
                    location=violation.get("location"),
                    suggested_fix=violation.get("suggested_fix"),
                    metadata={"category": "commit_frequency", **violation}
                )
            
            # メトリクス計算
            total_violations = len(result.violations)
            conventional_rate = commit_analysis.get("conventional_rate", 0)
            branch_compliance_rate = branch_analysis.get("compliance_rate", 0)
            
            # スコア計算（違反が少ないほど高スコア）
            git_quality_score = max(0, 100 - (total_violations * 5))
            git_quality_score *= (conventional_rate * 0.5 + branch_compliance_rate * 0.5)
            
            result.add_metric("git_quality_score", git_quality_score)
            result.add_metric("commits_analyzed", commit_analysis.get("total_commits", 0))
            result.add_metric("branches_checked", branch_analysis.get("total_branches", 0))
            result.add_metric("conventional_commit_rate", conventional_rate)
            result.add_metric("branch_compliance_rate", branch_compliance_rate)
            result.add_metric("has_conflicts", conflict_analysis.get("has_conflicts", False))
            
        except Exception as e:
            result.add_violation(
                severity=ViolationSeverity.HIGH,
                title="Git chronicle audit failed",
                description=f"Audit execution failed: {str(e)}",
                metadata={"category": "system", "error": str(e)}
            )
            
        return result
        
    def get_audit_scope(self) -> Dict[str, Any]:
        """
        この監査者の監査範囲を返す
        
        Returns:
            Dict: 監査範囲の説明
        """
        return {
            "scope": "git_chronicle_magic",
            "targets": [
                "Commit message quality",
                "Conventional commits compliance",
                "Branch naming convention",
                "Merge strategy adherence",
                "Commit frequency analysis",
                "Code review process"
            ],
            "violation_types": [
                "POOR_COMMIT_MESSAGE",
                "NON_CONVENTIONAL_COMMIT",
                "INVALID_BRANCH_NAME",
                "DIRECT_MAIN_PUSH",
                "LARGE_COMMIT",
                "MISSING_PR_REVIEW"
            ],
            "description": "Git年代記魔法 - Git履歴の品質と規約遵守監査"
        }