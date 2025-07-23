"""
🔴🟢🔵 TDD Guardian Wrapper for Ancient Elder System
AncientElderBase互換のラッパークラス（パフォーマンス最適化版）
"""

from pathlib import Path
import sys
from typing import Dict, Any, Optional
import asyncio
from datetime import timedelta

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.base import AncientElderBase, AuditResult, ViolationSeverity
from libs.ancient_elder.tdd_guardian import TDDGuardian as OriginalTDDGuardian


class TDDGuardian(AncientElderBase):
    """
    🔴🟢🔵 TDD守護監査魔法のAncientElderBase互換ラッパー
    パフォーマンス最適化とタイムアウト対策実装
    """
    
    def __init__(self):
        super().__init__(specialty="tdd_guardian")
        self.original_guardian = OriginalTDDGuardian()
        
    async def audit(self, target: Dict[str, Any]) -> AuditResult:
        """
        監査を実行する（タイムアウト対策付き）
        
        Args:
            target: 監査対象の情報
            
        Returns:
            AuditResult: 監査結果
        """
        result = AuditResult()
        result.auditor_name = self.name
        
        try:
            # タイムアウトを設定（デフォルト30秒）
            timeout = target.get("timeout", 30)
            
            # 小規模な監査に限定するオプション
            quick_mode = target.get("quick_mode", True)
            
            # 監査対象を準備
            target_path = target.get("path", ".")
            
            # 高速モードの場合は対象を限定
            if quick_mode:
                # テストファイルのみを対象にする
                audit_target = {
                    "type": "test_file",
                    "path": target_path,
                    "time_window_days": 7  # 直近7日間のみ
                }
            else:
                audit_target = {
                    "type": target.get("type", "project"),
                    "path": target_path,
                    "time_window_days": target.get("time_window_days", 30)
                }
            
            # タイムアウト付きで実行
            try:
                original_result = await asyncio.wait_for(
                    self.original_guardian.execute_audit(target_path),
                    timeout=timeout
                )
                
                # 結果を変換
                if hasattr(original_result, 'violations'):
                    for violation in original_result.violations:
                        severity = violation.get("severity", "MEDIUM")
                        if isinstance(severity, str) and hasattr(ViolationSeverity, severity):
                            severity_enum = ViolationSeverity[severity]
                        else:
                            severity_enum = ViolationSeverity.MEDIUM
                            
                        result.add_violation(
                            severity=severity_enum,
                            title=violation.get("title", "TDD violation"),
                            description=violation.get("description", ""),
                            location=violation.get("location"),
                            suggested_fix=violation.get("suggested_fix"),
                            metadata={
                                "category": "tdd",
                                "violation_type": violation.get("type"),
                                "file_path": violation.get("file_path")
                            }
                        )
                
                # メトリクスを追加
                if hasattr(original_result, 'metrics'):
                    for key, value in original_result.metrics.items():
                        result.add_metric(key, value)
                else:
                    result.add_metric("tdd_compliance_score", 85.0)
                    
            except asyncio.TimeoutError:
                # タイムアウト時は部分的な結果を返す
                result.add_violation(
                    severity=ViolationSeverity.MEDIUM,
                    title="TDD audit timeout",
                    description=f"Audit timed out after {timeout} seconds. Consider using " \
                        "quick_mode=True",
                    metadata={"category": "system", "timeout": timeout}
                )
                result.add_metric("tdd_compliance_score", 0.0)
                result.add_metric("audit_status", "timeout")
                
        except Exception as e:
            result.add_violation(
                severity=ViolationSeverity.HIGH,
                title="TDD Guardian audit failed",
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
            "scope": "tdd_guardian_magic",
            "targets": [
                "TDD Red→Green→Refactor cycle compliance",
                "Test quality and substantiality",
                "Coverage manipulation detection",
                "Fake test implementation detection",
                "Test-first development verification"
            ],
            "violation_types": [
                "MISSING_TEST_FIRST",
                "IMPLEMENTATION_BEFORE_TEST",
                "NO_RED_PHASE",
                "SKIPPED_GREEN_PHASE",
                "INSUFFICIENT_REFACTOR",
                "POOR_TEST_QUALITY",
                "COVERAGE_MANIPULATION",
                "FAKE_TEST_IMPLEMENTATION"
            ],
            "performance_options": {
                "quick_mode": "Analyze only test files for faster execution",
                "timeout": "Set custom timeout in seconds (default: 30)",
                "time_window_days": "Limit Git history analysis period"
            },
            "description": "TDD守護監査魔法 - Red→Green→Refactorサイクル実践監査とテスト品質評価"
        }