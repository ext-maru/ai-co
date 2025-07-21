#!/usr/bin/env python3
"""
🏛️ エンシェントエルダー古代魔法 - StrictOutputValidator

生成物への厳格検証システム
Tier 3: Output Validation Engine (生成物検証エンジン)

このモジュールは以下の厳格テストを実装：
- 構文完璧性チェック
- 論理一貫性検証
- 性能ベンチマーク
- セキュリティ侵入テスト
- 保守性スコア計算
- スケーラビリティ解析
"""

import ast
import re
import time
import inspect
import tokenize
import io
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import statistics
from pathlib import Path
import traceback

# エルダーズギルド品質システムとの統合
try:
    from libs.elders_code_quality_engine import EldersCodeQualityEngine
except ImportError:
    logging.warning("EldersCodeQualityEngine not available")
    EldersCodeQualityEngine = None

# 既存古代魔法システムとの統合
try:
    from libs.ancient_elder.base import AncientMagicBase
except ImportError:
    logging.warning("AncientMagicBase not available")
    AncientMagicBase = object

@dataclass
class ValidationResult:
    """検証結果データクラス"""
    is_valid: bool
    score: float  # 0-100
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    execution_time: float
    details: Dict[str, Any]

class SecurityRiskLevel(Enum):
    """セキュリティリスクレベル"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class StrictOutputValidator(AncientMagicBase):
    """🛡️ 厳格な生成物検証エンジン"""
    
    def __init__(self):
        """バリデーター初期化"""
        super().__init__()
        
        # EldersCodeQualityEngineの安全な初期化
        try:
            if EldersCodeQualityEngine:
                # デフォルトパラメータでの初期化を試行
                self.quality_engine = EldersCodeQualityEngine({})
            else:
                self.quality_engine = None
        except Exception as e:
            logging.warning(f"Could not initialize EldersCodeQualityEngine: {e}")
            self.quality_engine = None
            
        self.security_patterns = self._load_security_patterns()
        self.performance_thresholds = self._load_performance_thresholds()
        
        # 検証統計
        self.validation_history = []
        
    def validate_code_output(self, code_output: str) -> ValidationResult:
        """コード生成物の厳格検証
        
        Args:
            code_output: 検証対象のコード文字列
            
        Returns:
            ValidationResult: 包括的検証結果
        """
        start_time = time.time()
        
        try:
            checks = [
                self._syntax_perfection_check(code_output),
                self._logic_consistency_check(code_output),
                self._performance_benchmark(code_output),
                self._security_penetration_test(code_output),
                self._maintainability_score(code_output),
                self._scalability_analysis(code_output),
            ]
            
            result = self._comprehensive_evaluation(checks, code_output)
            result.execution_time = time.time() - start_time
            
            # 検証履歴に追加
            self.validation_history.append(result)
            
            return result
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                issues=[{"type": "validation_error", "message": str(e)}],
                suggestions=["Fix validation error"],
                execution_time=time.time() - start_time,
                details={"error": str(e), "traceback": traceback.format_exc()}
            )
    
    def _syntax_perfection_check(self, code: str) -> Dict[str, Any]:
        """構文完璧性チェック"""
        try:
            # ASTパース試行
            tree = ast.parse(code)
            
            # 構文解析詳細チェック
            issues = []
            
            # 不完全な文の検出
            for node in ast.walk(tree):
                if isinstance(node, ast.If) and not node.body:
                    issues.append({
                        "type": "incomplete_if",
                        "line": node.lineno,
                        "message": "Empty if statement body"
                    })
                elif isinstance(node, ast.FunctionDef) and not node.body:
                    issues.append({
                        "type": "empty_function",
                        "line": node.lineno,
                        "message": "Empty function body"
                    })
            
            return {
                "check_name": "syntax_perfection",
                "passed": len(issues) == 0,
                "score": max(0, 100 - len(issues) * 10),
                "issues": issues,
                "details": {"ast_nodes": len(list(ast.walk(tree)))}
            }
            
        except SyntaxError as e:
            return {
                "check_name": "syntax_perfection",
                "passed": False,
                "score": 0,
                "issues": [{
                    "type": "syntax_error",
                    "line": e.lineno,
                    "message": str(e)
                }],
                "details": {"syntax_error": str(e)}
            }
    
    def _logic_consistency_check(self, code: str) -> Dict[str, Any]:
        """論理一貫性チェック"""
        try:
            tree = ast.parse(code)
            issues = []
            
            # 論理的不整合パターンの検出
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 関数の論理チェック
                    func_issues = self._check_function_logic(node)
                    issues.extend(func_issues)
            
            return {
                "check_name": "logic_consistency",
                "passed": len(issues) == 0,
                "score": max(0, 100 - len(issues) * 15),
                "issues": issues,
                "details": {"functions_checked": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])}
            }
            
        except Exception as e:
            return {
                "check_name": "logic_consistency",
                "passed": False,
                "score": 0,
                "issues": [{"type": "analysis_error", "message": str(e)}],
                "details": {"error": str(e)}
            }
    
    def _check_function_logic(self, func_node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """関数の論理チェック"""
        issues = []
        
        # 正数を負数で返すパターンなどの検出
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return) and isinstance(node.value, ast.BinOp):
                if isinstance(node.value.op, ast.Mult):
                    # x * -1 パターンの検出
                    if (isinstance(node.value.right, ast.UnaryOp) and 
                        isinstance(node.value.right.op, ast.USub)):
                        issues.append({
                            "type": "logic_inconsistency",
                            "line": node.lineno,
                            "message": "Potential logic inconsistency: positive input to negative output"
                        })
        
        return issues
    
    def _performance_benchmark(self, code: str) -> Dict[str, Any]:
        """性能ベンチマーク"""
        try:
            tree = ast.parse(code)
            issues = []
            complexity_score = 0
            
            # サイクロマティック複雑度の計算
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    complexity_score += 1
                elif isinstance(node, ast.FunctionDef):
                    # ネストしたループの検出（O(n²)パターン）
                    nested_loops = self._detect_nested_loops(node)
                    if nested_loops > 1:
                        issues.append({
                            "type": "performance_issue",
                            "line": node.lineno,
                            "message": f"Detected O(n^{nested_loops}) complexity in function {node.name}"
                        })
            
            # 性能スコア計算
            performance_score = max(0, 100 - complexity_score * 5 - len(issues) * 20)
            
            return {
                "check_name": "performance_benchmark",
                "passed": len(issues) == 0,
                "score": performance_score,
                "issues": issues,
                "details": {
                    "complexity_score": complexity_score,
                    "nested_loops_detected": len(issues)
                }
            }
            
        except Exception as e:
            return {
                "check_name": "performance_benchmark",
                "passed": False,
                "score": 50,  # デフォルトスコア
                "issues": [{"type": "analysis_error", "message": str(e)}],
                "details": {"error": str(e)}
            }
    
    def _detect_nested_loops(self, func_node: ast.FunctionDef) -> int:
        """ネストしたループの深度を検出"""
        max_depth = 0
        
        def count_depth(node, current_depth=0):
            nonlocal max_depth
            if isinstance(node, (ast.For, ast.While)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                count_depth(child, current_depth)
        
        count_depth(func_node)
        return max_depth
    
    def _security_penetration_test(self, code: str) -> Dict[str, Any]:
        """セキュリティ侵入テスト"""
        issues = []
        risk_level = SecurityRiskLevel.NONE
        
        # 危険なパターンの検出
        dangerous_patterns = [
            (r'os\.system\s*\(', SecurityRiskLevel.CRITICAL, "Arbitrary command execution"),
            (r'eval\s*\(', SecurityRiskLevel.CRITICAL, "Code injection vulnerability"),
            (r'exec\s*\(', SecurityRiskLevel.HIGH, "Dynamic code execution"),
            (r'subprocess\.call\s*\(', SecurityRiskLevel.MEDIUM, "Subprocess execution"),
            (r'__import__\s*\(', SecurityRiskLevel.MEDIUM, "Dynamic import"),
        ]
        
        for pattern, level, message in dangerous_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_no = code[:match.start()].count('\n') + 1
                issues.append({
                    "type": "security_risk",
                    "line": line_no,
                    "level": level.name,
                    "message": message,
                    "pattern": pattern
                })
                if level.value > risk_level.value:
                    risk_level = level
        
        # セキュリティスコア計算
        security_score = max(0, 100 - sum(issue.get("level_value", 0) for issue in issues))
        
        return {
            "check_name": "security_penetration",
            "passed": risk_level == SecurityRiskLevel.NONE,
            "score": security_score,
            "issues": issues,
            "details": {
                "max_risk_level": risk_level.name,
                "patterns_checked": len(dangerous_patterns)
            }
        }
    
    def _maintainability_score(self, code: str) -> Dict[str, Any]:
        """保守性スコア"""
        try:
            tree = ast.parse(code)
            issues = []
            
            # 保守性の問題を検出
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # パラメータ数チェック
                    if len(node.args.args) > 10:
                        issues.append({
                            "type": "too_many_parameters",
                            "line": node.lineno,
                            "message": f"Function {node.name} has {len(node.args.args)} parameters (max: 10)"
                        })
                    
                    # 関数の複雑度チェック
                    lines = len(code.split('\n'))
                    if lines > 50:
                        issues.append({
                            "type": "long_function",
                            "line": node.lineno,
                            "message": f"Function {node.name} is too long ({lines} lines)"
                        })
            
            maintainability_score = max(0, 100 - len(issues) * 15)
            
            return {
                "check_name": "maintainability_score",
                "passed": len(issues) == 0,
                "score": maintainability_score,
                "issues": issues,
                "details": {"total_lines": len(code.split('\n'))}
            }
            
        except Exception as e:
            return {
                "check_name": "maintainability_score",
                "passed": False,
                "score": 50,
                "issues": [{"type": "analysis_error", "message": str(e)}],
                "details": {"error": str(e)}
            }
    
    def _scalability_analysis(self, code: str) -> Dict[str, Any]:
        """スケーラビリティ解析"""
        issues = []
        
        # スケーラビリティを阻害するパターンの検出
        scalability_patterns = [
            (r'global\s+\w+', "Global variable usage reduces scalability"),
            (r'singleton', "Singleton pattern may limit scalability"),
            (r'time\.sleep\s*\(', "Blocking sleep calls reduce scalability"),
        ]
        
        for pattern, message in scalability_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_no = code[:match.start()].count('\n') + 1
                issues.append({
                    "type": "scalability_issue",
                    "line": line_no,
                    "message": message,
                    "pattern": pattern
                })
        
        scalability_score = max(0, 100 - len(issues) * 20)
        
        return {
            "check_name": "scalability_analysis",
            "passed": len(issues) == 0,
            "score": scalability_score,
            "issues": issues,
            "details": {"patterns_checked": len(scalability_patterns)}
        }
    
    def _comprehensive_evaluation(self, checks: List[Dict[str, Any]], code: str) -> ValidationResult:
        """包括的評価"""
        all_issues = []
        all_suggestions = []
        scores = []
        
        for check in checks:
            all_issues.extend(check.get("issues", []))
            scores.append(check.get("score", 0))
        
        # 総合スコア計算
        overall_score = statistics.mean(scores) if scores else 0
        
        # 提案生成
        if overall_score < 70:
            all_suggestions.append("Code quality is below acceptable threshold")
        if any(issue.get("type") == "security_risk" for issue in all_issues):
            all_suggestions.append("Address security vulnerabilities immediately")
        if any(issue.get("type") == "performance_issue" for issue in all_issues):
            all_suggestions.append("Optimize performance bottlenecks")
        
        return ValidationResult(
            is_valid=overall_score >= 70,
            score=overall_score,
            issues=all_issues,
            suggestions=all_suggestions,
            execution_time=0.0,  # 呼び出し元で設定
            details={
                "individual_scores": {check["check_name"]: check["score"] for check in checks},
                "total_checks": len(checks),
                "code_length": len(code)
            }
        )
    
    def validate_design_output(self, design_output: Dict[str, Any]) -> ValidationResult:
        """設計生成物の厳格検証"""
        start_time = time.time()
        
        checks = [
            self._architecture_soundness(design_output),
            self._design_pattern_compliance(design_output),
            self._future_extensibility(design_output),
            self._technical_debt_prediction(design_output),
        ]
        
        all_issues = []
        scores = []
        
        for check in checks:
            all_issues.extend(check.get("issues", []))
            scores.append(check.get("score", 0))
        
        overall_score = statistics.mean(scores) if scores else 0
        
        return ValidationResult(
            is_valid=overall_score >= 70,
            score=overall_score,
            issues=all_issues,
            suggestions=["Review design architecture", "Consider scalability"],
            execution_time=time.time() - start_time,
            details={"design_type": "architecture"}
        )
    
    def _architecture_soundness(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """アーキテクチャ健全性チェック"""
        issues = []
        score = 80  # ベーススコア
        
        # レイヤー構造のチェック
        if "layers" not in design:
            issues.append({
                "type": "missing_layers",
                "message": "Architecture layers not defined"
            })
            score -= 20
        
        return {
            "check_name": "architecture_soundness",
            "passed": len(issues) == 0,
            "score": max(0, score),
            "issues": issues,
            "details": {"design_keys": list(design.keys())}
        }
    
    def _design_pattern_compliance(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """デザインパターン準拠性チェック"""
        issues = []
        score = 75
        
        patterns = design.get("patterns", [])
        if not patterns:
            issues.append({
                "type": "no_patterns",
                "message": "No design patterns specified"
            })
            score -= 25
        
        return {
            "check_name": "design_pattern_compliance",
            "passed": len(issues) == 0,
            "score": max(0, score),
            "issues": issues,
            "details": {"patterns": patterns}
        }
    
    def _future_extensibility(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """将来拡張性チェック"""
        score = 70
        issues = []
        
        # 拡張性指標のチェック
        if "extensibility" not in design:
            issues.append({
                "type": "no_extensibility_plan",
                "message": "Future extensibility not considered"
            })
            score -= 30
        
        return {
            "check_name": "future_extensibility",
            "passed": len(issues) == 0,
            "score": max(0, score),
            "issues": issues,
            "details": {}
        }
    
    def _technical_debt_prediction(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """技術負債予測"""
        debt_indicators = [
            "TODO", "HACK", "FIXME", "TEMPORARY", "WORKAROUND"
        ]
        
        issues = []
        debt_score = 0
        
        # 文字列表現での技術負債指標チェック
        design_str = str(design)
        for indicator in debt_indicators:
            if indicator in design_str.upper():
                issues.append({
                    "type": "technical_debt",
                    "message": f"Technical debt indicator found: {indicator}"
                })
                debt_score += 10
        
        score = max(0, 100 - debt_score)
        
        return {
            "check_name": "technical_debt_prediction",
            "passed": len(issues) == 0,
            "score": score,
            "issues": issues,
            "details": {"debt_indicators_checked": len(debt_indicators)}
        }
    
    def _load_security_patterns(self) -> List[str]:
        """セキュリティパターンの読み込み"""
        return [
            r'os\.system',
            r'eval\s*\(',
            r'exec\s*\(',
            r'subprocess\.call',
            r'__import__'
        ]
    
    def _load_performance_thresholds(self) -> Dict[str, Any]:
        """性能閾値の読み込み"""
        return {
            "max_complexity": 10,
            "max_nested_loops": 2,
            "max_function_lines": 50
        }
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """検証統計情報取得"""
        if not self.validation_history:
            return {"message": "No validation history available"}
        
        scores = [result.score for result in self.validation_history]
        
        return {
            "total_validations": len(self.validation_history),
            "average_score": statistics.mean(scores),
            "median_score": statistics.median(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "success_rate": len([r for r in self.validation_history if r.is_valid]) / len(self.validation_history)
        }

# 便利関数
def validate_code(code: str) -> ValidationResult:
    """コード検証の便利関数"""
    validator = StrictOutputValidator()
    return validator.validate_code_output(code)

def validate_design(design: Dict[str, Any]) -> ValidationResult:
    """設計検証の便利関数"""
    validator = StrictOutputValidator()
    return validator.validate_design_output(design)

if __name__ == "__main__":
    # 簡単なテスト実行
    sample_code = """
def hello_world():
    print("Hello, World!")
    return True
"""
    
    validator = StrictOutputValidator()
    result = validator.validate_code_output(sample_code)
    
    print(f"Validation Result: {result.is_valid}")
    print(f"Score: {result.score:.2f}")
    print(f"Issues: {len(result.issues)}")
    print(f"Execution Time: {result.execution_time:.4f}s")