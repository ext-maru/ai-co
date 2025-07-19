"""
エルフの森とインシデント騎士団の協調システム
テスト失敗を自動的に修復
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from libs.incident_knights_framework import IncidentKnight, KnightBrigade


class TestFailureKnight(IncidentKnight):
    """テスト失敗専門の騎士"""

    def __init__(self):
        super().__init__("TestFailureKnight", ["test", "import", "mock"])
        self.fix_strategies = {
            "import_error": self._fix_import_error,
            "mock_error": self._fix_mock_error,
            "assertion_error": self._fix_assertion_error,
            "attribute_error": self._fix_attribute_error,
        }

    def diagnose(self, context: Dict) -> Dict:
        """テスト失敗の診断"""
        test_file = context.get("test_file")
        error_output = context.get("error_output", "")

        diagnosis = {
            "severity": "medium",
            "error_type": self._identify_error_type(error_output),
            "affected_file": test_file,
            "can_auto_fix": False,
            "suggested_fixes": [],
        }

        # エラータイプに基づいて自動修復可能か判断
        if diagnosis["error_type"] in self.fix_strategies:
            diagnosis["can_auto_fix"] = True
            diagnosis["suggested_fixes"] = [
                f"Apply {diagnosis['error_type']} fix strategy"
            ]

        return diagnosis

    def heal(self, diagnosis: Dict) -> bool:
        """テストの修復"""
        if not diagnosis.get("can_auto_fix"):
            return False

        error_type = diagnosis.get("error_type")
        test_file = diagnosis.get("affected_file")

        if error_type in self.fix_strategies:
            return self.fix_strategies[error_type](test_file)

        return False

    def _identify_error_type(self, error_output: str) -> str:
        """エラータイプの特定"""
        if "ModuleNotFoundError" in error_output or "ImportError" in error_output:
            return "import_error"
        elif "Mock" in error_output or "patch" in error_output:
            return "mock_error"
        elif "AssertionError" in error_output:
            return "assertion_error"
        elif "AttributeError" in error_output:
            return "attribute_error"
        else:
            return "unknown"

    def _fix_import_error(self, test_file: str) -> bool:
        """インポートエラーの修正"""
        try:
            with open(test_file, "r") as f:
                content = f.read()

            # 共通の修正パターン
            fixes = [
                ("from base_test import", "from tests.test_base_utils import"),
                ("from ..", "from "),
                ("import libs.", "from libs."),
            ]

            modified = False
            for old, new in fixes:
                if old in content:
                    content = content.replace(old, new)
                    modified = True

            if modified:
                with open(test_file, "w") as f:
                    f.write(content)
                return True

        except Exception as e:
            self.logger.error(f"Failed to fix import error: {e}")

        return False

    def _fix_mock_error(self, test_file: str) -> bool:
        """モックエラーの修正"""
        # モック設定の一般的な修正
        return False

    def _fix_assertion_error(self, test_file: str) -> bool:
        """アサーションエラーの修正"""
        # アサーションの修正は慎重に行う必要がある
        return False

    def _fix_attribute_error(self, test_file: str) -> bool:
        """属性エラーの修正"""
        # 属性エラーの一般的な修正
        return False


class ElfKnightCoordinator:
    """エルフとナイトの協調コーディネーター"""

    def __init__(self):
        self.test_knight = TestFailureKnight()
        self.knight_brigade = KnightBrigade()
        self.knight_brigade.register_knight(self.test_knight)

    def coordinate_test_healing(self, test_results: List[Dict]) -> Dict[str, int]:
        """テスト修復の協調実行"""
        results = {
            "total": len(test_results),
            "healed": 0,
            "failed": 0,
            "in_progress": 0,
        }

        for test_result in test_results:
            if not test_result.get("success"):
                # インシデントとして騎士団に報告
                incident = {
                    "type": "test_failure",
                    "test_file": test_result["file"],
                    "error_output": test_result.get("error", ""),
                    "priority": "medium",
                }

                # 騎士団による診断と修復
                diagnosis = self.test_knight.diagnose(incident)

                if diagnosis.get("can_auto_fix"):
                    if self.test_knight.heal(diagnosis):
                        results["healed"] += 1
                        # 修復後の再テスト
                        self._rerun_test(test_result["file"])
                    else:
                        results["failed"] += 1
                else:
                    results["in_progress"] += 1

        return results

    def _rerun_test(self, test_file: str) -> bool:
        """テストの再実行"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v"],
                capture_output=True,
                timeout=30,
            )
            return result.returncode == 0
        except Exception:
            return False

    def generate_incident_report(self, results: Dict[str, int]) -> str:
        """インシデントレポートの生成"""
        report = f"""
⚔️ インシデント騎士団 - テスト修復レポート
=========================================

📊 処理結果:
- 総テスト数: {results['total']}
- 自動修復成功: {results['healed']}
- 修復失敗: {results['failed']}
- 手動対応必要: {results['in_progress']}

🎯 成功率: {(results['healed'] / results['total'] * 100):.1f}%

推奨アクション:
1. 自動修復できなかったテストの手動確認
2. 修復パターンの騎士団知識ベースへの追加
3. エルフの森との継続的な連携強化
"""
        return report
