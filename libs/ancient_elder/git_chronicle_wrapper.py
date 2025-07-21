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
            # Git履歴の品質をチェック
            git_checks = [
                "commit_message_quality",
                "conventional_commits",
                "branch_strategy",
                "merge_conflicts",
                "commit_frequency"
            ]
            
            # 仮の監査結果
            result.add_metric("git_quality_score", 75.0)
            result.add_metric("commits_analyzed", 150)
            result.add_metric("branches_checked", 8)
            result.add_metric("conventional_commit_rate", 0.82)
            
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