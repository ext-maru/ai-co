#!/usr/bin/env python3
"""
Development Incident Predictor
開発時インシデント予測システム - インポートエラー・テスト失敗の事前予測

インシデント賢者の機能を開発時まで拡張し、以下を予測・防止：
1. Pythonインポートエラー
2. テスト実行時の失敗
3. 依存関係の問題
4. 環境設定エラー
"""

import ast
import importlib
import json
import logging
import os
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ImportIssue:
    """インポート問題情報"""

    file_path: str
    line_number: int
    import_statement: str
    issue_type: str  # 'missing_module', 'circular_import', 'path_error'
    severity: str  # 'critical', 'high', 'medium', 'low'
    suggested_fix: str
    confidence: float  # 0.0-1.0


@dataclass
class TestPrediction:
    """テスト予測情報"""

    test_file: str
    test_function: str
    predicted_result: str  # 'pass', 'fail', 'error', 'skip'
    failure_reason: Optional[str]
    confidence: float
    dependencies: List[str]


@dataclass
class DevelopmentRisk:
    """開発リスク評価"""

    risk_type: str
    description: str
    likelihood: float  # 0.0-1.0
    impact: str  # 'critical', 'high', 'medium', 'low'
    mitigation: str
    files_affected: List[str]


class ImportAnalyzer:
    """インポート分析器"""

    def __init__(self, project_root: Path):
        """初期化メソッド"""
        self.project_root = project_root
        self.import_graph = defaultdict(set)
        self.known_modules = set()
        self.virtual_env_modules = set()
        self._scan_environment()

    def _scan_environment(self):
        """環境の既存モジュールをスキャン"""
        try:
            # 標準ライブラリモジュール
            import sys

            self.known_modules.update(sys.builtin_module_names)

            # インストール済みパッケージ
            try:
                import pkg_resources

                for pkg in pkg_resources.working_set:
                    self.known_modules.add(pkg.project_name.lower())
            except ImportError:
                pass

            # プロジェクト内モジュール
            for py_file in self.project_root.rglob("*.py"):
                if not py_file.name.startswith("__"):
                    rel_path = py_file.relative_to(self.project_root)
                    module_path = str(rel_path.with_suffix("")).replace("/", ".")
                    self.known_modules.add(module_path)

        except Exception as e:
            logger.warning(f"Environment scan failed: {e}")

    def analyze_file(self, file_path: Path) -> List[ImportIssue]:
        """ファイルのインポートを分析"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        issue = self._check_import(file_path, node.lineno, alias.name)
                        if issue:
                            issues.append(issue)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        issue = self._check_from_import(
                            file_path, node.lineno, node.module, node.names
                        )
                        if issue:
                            issues.append(issue)

        except SyntaxError as e:
            issues.append(
                ImportIssue(
                    file_path=str(file_path),
                    line_number=e.lineno or 0,
                    import_statement="",
                    issue_type="syntax_error",
                    severity="critical",
                    suggested_fix=f"Fix syntax error: {e}",
                    confidence=1.0,
                )
            )
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")

        return issues

    def _check_import(
        self, file_path: Path, line_number: int, module_name: str
    ) -> Optional[ImportIssue]:
        """単純インポートをチェック"""
        # モジュール存在確認
        if not self._module_exists(module_name):
            return ImportIssue(
                file_path=str(file_path),
                line_number=line_number,
                import_statement=f"import {module_name}",
                issue_type="missing_module",
                severity="high",
                suggested_fix=f"Install module: pip install {module_name}",
                confidence=0.9,
            )

        # 循環インポートチェック
        if self._detect_circular_import(file_path, module_name):
            return ImportIssue(
                file_path=str(file_path),
                line_number=line_number,
                import_statement=f"import {module_name}",
                issue_type="circular_import",
                severity="critical",
                suggested_fix="Refactor to avoid circular imports",
                confidence=0.8,
            )

        return None

    def _check_from_import(
        self,
        file_path: Path,
        line_number: int,
        module_name: str,
        names: List[ast.alias],
    ) -> Optional[ImportIssue]:
        """from インポートをチェック"""
        if not self._module_exists(module_name):
            return ImportIssue(
                file_path=str(file_path),
                line_number=line_number,
                import_statement=f"from {module_name} import ...",
                issue_type="missing_module",
                severity="high",
                suggested_fix=f"Install module: pip install {module_name}",
                confidence=0.9,
            )

        # 属性存在確認
        for name in names:
            if name.name != "*" and not self._attribute_exists(module_name, name.name):
                return ImportIssue(
                    file_path=str(file_path),
                    line_number=line_number,
                    import_statement=f"from {module_name} import {name.name}",
                    issue_type="missing_attribute",
                    severity="medium",
                    suggested_fix=f"Check if {name.name} exists in {module_name}",
                    confidence=0.7,
                )

        return None

    def _module_exists(self, module_name: str) -> bool:
        """モジュール存在確認"""
        if module_name in self.known_modules:
            return True

        try:
            importlib.import_module(module_name)
            self.known_modules.add(module_name)
            return True
        except ImportError:
            return False

    def _attribute_exists(self, module_name: str, attr_name: str) -> bool:
        """モジュール属性存在確認"""
        try:
            module = importlib.import_module(module_name)
            return hasattr(module, attr_name)
        except ImportError:
            return False

    def _detect_circular_import(self, current_file: Path, target_module: str) -> bool:
        """循環インポート検出"""
        # 簡易実装：実際にはより詳細な依存関係グラフが必要
        current_module = self._file_to_module(current_file)
        return target_module == current_module

    def _file_to_module(self, file_path: Path) -> str:
        """ファイルパスをモジュール名に変換"""
        try:
            rel_path = file_path.relative_to(self.project_root)
            return str(rel_path.with_suffix("")).replace("/", ".")
        except ValueError:
            return file_path.stem


class TestExecutionPredictor:
    """テスト実行予測器"""

    def __init__(self, project_root: Path):
        """初期化メソッド"""
        self.project_root = project_root
        self.test_history = {}
        self.dependency_map = {}

    def predict_test_results(self, test_files: List[Path]) -> List[TestPrediction]:
        """テスト結果を予測"""
        predictions = []

        for test_file in test_files:
            file_predictions = self._analyze_test_file(test_file)
            predictions.extend(file_predictions)

        return predictions

    def _analyze_test_file(self, test_file: Path) -> List[TestPrediction]:
        """テストファイルを分析"""
        predictions = []

        try:
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    prediction = self._predict_test_function(test_file, node)
                    predictions.append(prediction)

        except Exception as e:
            logger.error(f"Failed to analyze test file {test_file}: {e}")
            predictions.append(
                TestPrediction(
                    test_file=str(test_file),
                    test_function="<parse_error>",
                    predicted_result="error",
                    failure_reason=str(e),
                    confidence=1.0,
                    dependencies=[],
                )
            )

        return predictions

    def _predict_test_function(
        self, test_file: Path, func_node: ast.FunctionDef
    ) -> TestPrediction:
        """個別テスト関数の結果を予測"""
        # 基本的な予測ロジック
        dependencies = self._extract_dependencies(func_node)

        # インポートエラーの可能性
        for dep in dependencies:
            if not self._can_import(dep):
                return TestPrediction(
                    test_file=str(test_file),
                    test_function=func_node.name,
                    predicted_result="error",
                    failure_reason=f"Import error: {dep}",
                    confidence=0.9,
                    dependencies=dependencies,
                )

        # アサーション分析
        assertions = self._count_assertions(func_node)
        if assertions == 0:
            return TestPrediction(
                test_file=str(test_file),
                test_function=func_node.name,
                predicted_result="pass",
                failure_reason=None,
                confidence=0.3,  # アサーションなしは不確実
                dependencies=dependencies,
            )

        # 履歴ベース予測
        historical_success = self._get_historical_success_rate(
            test_file, func_node.name
        )

        if historical_success > 0.8:
            predicted_result = "pass"
            confidence = 0.8
        elif historical_success < 0.3:
            predicted_result = "fail"
            confidence = 0.7
        else:
            predicted_result = "pass"  # デフォルト楽観的
            confidence = 0.5

        return TestPrediction(
            test_file=str(test_file),
            test_function=func_node.name,
            predicted_result=predicted_result,
            failure_reason=None,
            confidence=confidence,
            dependencies=dependencies,
        )

    def _extract_dependencies(self, func_node: ast.FunctionDef) -> List[str]:
        """関数の依存関係を抽出"""
        dependencies = []

        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    dependencies.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        dependencies.append(f"{node.func.value.id}.{node.func.attr}")

        return list(set(dependencies))

    def _count_assertions(self, func_node: ast.FunctionDef) -> int:
        """アサーション数をカウント"""
        count = 0
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id.startswith(
                    "assert"
                ):
                    count += 1
                elif isinstance(node.func, ast.Attribute) and node.func.attr.startswith(
                    "assert"
                ):
                    count += 1
        return count

    def _can_import(self, module_name: str) -> bool:
        """モジュールインポート可能性確認"""
        try:
            if "." in module_name:
                module_name = module_name.split(".")[0]
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    def _get_historical_success_rate(self, test_file: Path, func_name: str) -> float:
        """履歴成功率取得"""
        key = f"{test_file}::{func_name}"
        return self.test_history.get(key, 0.7)  # デフォルト70%


class DevelopmentIncidentPredictor:
    """開発インシデント予測器メインクラス"""

    def __init__(self, project_root: Optional[Path] = None):
        """初期化メソッド"""
        self.project_root = project_root or Path.cwd()
        self.import_analyzer = ImportAnalyzer(self.project_root)
        self.test_predictor = TestExecutionPredictor(self.project_root)

    def predict_development_risks(
        self, target_files: Optional[List[Path]] = None
    ) -> Dict[str, Any]:
        """開発リスクを総合予測"""
        if target_files is None:
            target_files = list(self.project_root.rglob("*.py"))

        results = {
            "timestamp": datetime.now().isoformat(),
            "import_issues": [],
            "test_predictions": [],
            "development_risks": [],
            "overall_risk_score": 0.0,
            "recommendations": [],
        }

        # インポート問題分析
        for file_path in target_files:
            if not file_path.name.startswith("test_"):
                issues = self.import_analyzer.analyze_file(file_path)
                results["import_issues"].extend(issues)

        # テスト予測
        test_files = [f for f in target_files if f.name.startswith("test_")]
        if test_files:
            predictions = self.test_predictor.predict_test_results(test_files)
            results["test_predictions"].extend(predictions)

        # 開発リスク評価
        risks = self._assess_development_risks(
            results["import_issues"], results["test_predictions"]
        )
        results["development_risks"] = risks

        # 総合リスクスコア計算
        results["overall_risk_score"] = self._calculate_overall_risk_score(results)

        # 推奨事項生成
        results["recommendations"] = self._generate_recommendations(results)

        return results

    def _assess_development_risks(
        self, import_issues: List[ImportIssue], test_predictions: List[TestPrediction]
    ) -> List[DevelopmentRisk]:
        """開発リスクを評価"""
        risks = []

        # インポートエラーリスク
        critical_imports = [i for i in import_issues if i.severity == "critical"]
        if critical_imports:
            risks.append(
                DevelopmentRisk(
                    risk_type="critical_import_errors",
                    description=f"{len(critical_imports)} critical import errors detected",
                    likelihood=0.9,
                    impact="critical",
                    mitigation="Fix import errors before proceeding",
                    files_affected=[i.file_path for i in critical_imports],
                )
            )

        # テスト失敗リスク
        failing_tests = [
            p for p in test_predictions if p.predicted_result in ["fail", "error"]
        ]
        if failing_tests:
            risks.append(
                DevelopmentRisk(
                    risk_type="test_failures",
                    description=f"{len(failing_tests)} tests predicted to fail",
                    likelihood=0.7,
                    impact="high",
                    mitigation="Review and fix failing tests",
                    files_affected=list(set([p.test_file for p in failing_tests])),
                )
            )

        # 依存関係リスク
        missing_deps = [i for i in import_issues if i.issue_type == "missing_module"]
        if missing_deps:
            risks.append(
                DevelopmentRisk(
                    risk_type="missing_dependencies",
                    description=f"{len(missing_deps)} missing dependencies",
                    likelihood=0.8,
                    impact="medium",
                    mitigation="Install missing dependencies",
                    files_affected=[i.file_path for i in missing_deps],
                )
            )

        return risks

    def _calculate_overall_risk_score(self, results: Dict[str, Any]) -> float:
        """総合リスクスコア計算"""
        score = 0.0

        # インポート問題の重み付け
        for issue in results["import_issues"]:
            if issue.severity == "critical":
                score += 0.3
            elif issue.severity == "high":
                score += 0.2
            elif issue.severity == "medium":
                score += 0.1

        # テスト予測の重み付け
        for prediction in results["test_predictions"]:
            if prediction.predicted_result == "error":
                score += 0.2
            elif prediction.predicted_result == "fail":
                score += 0.1

        # 開発リスクの重み付け
        for risk in results["development_risks"]:
            if risk.impact == "critical":
                score += 0.4 * risk.likelihood
            elif risk.impact == "high":
                score += 0.3 * risk.likelihood
            elif risk.impact == "medium":
                score += 0.2 * risk.likelihood

        return min(score, 1.0)  # 0.0-1.0に正規化

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """推奨事項を生成"""
        recommendations = []

        # 高優先度の推奨事項
        critical_issues = [
            i for i in results["import_issues"] if i.severity == "critical"
        ]
        if critical_issues:
            recommendations.append("🚨 CRITICAL: Fix import errors immediately")
            for issue in critical_issues[:3]:  # 上位3件
                recommendations.append(f"  - {issue.suggested_fix}")

        # テスト関連推奨事項
        error_tests = [
            p for p in results["test_predictions"] if p.predicted_result == "error"
        ]
        if error_tests:
            recommendations.append("⚠️ HIGH: Review tests with predicted errors")
            for test in error_tests[:3]:
                recommendations.append(f"  - {test.test_file}: {test.failure_reason}")

        # 一般的推奨事項
        if results["overall_risk_score"] > 0.7:
            recommendations.append("🔧 Consider running tests in isolated environment")
            recommendations.append("📋 Update documentation with current dependencies")
        elif results["overall_risk_score"] > 0.3:
            recommendations.append("✅ Review code before committing")
            recommendations.append("🧪 Run tests locally before pushing")
        else:
            recommendations.append("🎉 Low risk detected - proceed with confidence")

        return recommendations

    def save_prediction_report(
        self, results: Dict[str, Any], output_file: Optional[Path] = None
    ):
        """予測レポートを保存"""
        if output_file is None:
            output_file = self.project_root / "development_incident_prediction.json"

        # シリアライズ可能な形式に変換
        serializable_results = self._make_serializable(results)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)

        logger.info(f"Prediction report saved to {output_file}")

    def _make_serializable(self, obj):
        """オブジェクトをシリアライズ可能に変換"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif hasattr(obj, "__dict__"):
            return self._make_serializable(obj.__dict__)
        else:
            return obj


def demo_development_prediction():
    """開発予測のデモンストレーション"""
    print("🔮 Development Incident Prediction Demo")
    print("=" * 60)

    predictor = DevelopmentIncidentPredictor()

    # 現在のプロジェクトを分析
    results = predictor.predict_development_risks()

    print(f"\n📊 Overall Risk Score: {results['overall_risk_score']:.2f}")
    print(f"📁 Import Issues: {len(results['import_issues'])}")
    print(f"🧪 Test Predictions: {len(results['test_predictions'])}")
    print(f"⚠️ Development Risks: {len(results['development_risks'])}")

    print("\n🎯 Recommendations:")
    for rec in results["recommendations"]:
        print(f"  {rec}")

    # レポート保存
    predictor.save_prediction_report(results)

    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_development_prediction()
