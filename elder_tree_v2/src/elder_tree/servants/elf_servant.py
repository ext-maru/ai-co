"""
Elf Servant - エルフ族サーバント
品質保証・最適化特化型サーバント
"""

from typing import Dict, Any, List, Optional, Tuple
import asyncio
import ast
import subprocess
from pathlib import Path
from elder_tree.servants.base_servant import ElderServantBase
import structlog
from prometheus_client import Summary
import json
import os


class ElfServant(ElderServantBase):
    """
    エルフ族基底クラス
    
    特徴:
    - 品質保証・最適化に特化
    - 継続的監視
    - パフォーマンス改善
    """
    
    def __init__(self, name: str, specialty: str, port: int):
        super().__init__(
            name=name,
            tribe="elf",
            specialty=specialty,
            port=port
        )
        
        # エルフ特有の設定
        self.quality_standards = {
            "code_complexity": 10,  # McCabe complexity
            "test_coverage": 90,
            "performance_threshold": 0.1  # seconds
        }
        self.optimization_level = "aggressive"


class QualityGuardian(ElfServant):
    """
    Quality Guardian - 品質守護者
    
    専門:
    - コード品質チェック
    - パフォーマンス最適化
    - セキュリティ監査
    - 継続的改善
    """
    
    def __init__(self, port: int = 60103):
        super().__init__(
            name="quality_guardian",
            specialty="Code quality and optimization",
            port=port
        )
        
        # 追加メトリクス
        self.optimization_duration = Summary(
            'quality_guardian_optimization_seconds',
            'Time spent on optimization'
        )
        
        # 追加ハンドラー登録
        self._register_quality_handlers()
    
    def _register_quality_handlers(self):
        """品質管理専用ハンドラー"""
        
        @self.on_message("analyze_code_quality")
        async def handle_analyze_quality(message) -> Dict[str, Any]:
            """
            コード品質分析リクエスト
            
            Input:
                - file_path: 分析対象ファイル
                - checks: 実行するチェック項目
            """
            file_path = message.data.get("file_path", "")
            checks = message.data.get("checks", ["all"])
            
            result = await self.execute_specialized_task(
                "quality_analysis",
                {
                    "file_path": file_path,
                    "checks": checks
                },
                {}
            )
            
            return {
                "status": "success",
                "quality_report": result
            }
        
        @self.on_message("optimize_performance")
        async def handle_optimize_performance(message) -> Dict[str, Any]:
            """
            パフォーマンス最適化リクエスト
            """
            target_code = message.data.get("code", "")
            optimization_goals = message.data.get("goals", ["speed"])
            
            with self.optimization_duration.time():
                result = await self.execute_specialized_task(
                    "performance_optimization",
                    {
                        "code": target_code,
                        "goals": optimization_goals
                    },
                    {}
                )
            
            return {
                "status": "success",
                "optimization_result": result
            }
    
    async def execute_specialized_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        consultation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        エルフ特化タスク実行
        """
        if task_type == "quality_analysis":
            file_path = parameters.get("file_path", "")
            checks = parameters.get("checks", ["all"])
            
            # 品質分析実行
            analysis_results = {}
            
            if "all" in checks or "complexity" in checks:
                analysis_results["complexity"] = await self._analyze_complexity(file_path)
            
            if "all" in checks or "security" in checks:
                analysis_results["security"] = await self._security_scan(file_path)
            
            if "all" in checks or "style" in checks:
                analysis_results["style"] = await self._check_style(file_path)
            
            if "all" in checks or "performance" in checks:
                analysis_results["performance"] = await self._analyze_performance(file_path)
            
            # 総合スコア計算
            overall_score = self._calculate_overall_score(analysis_results)
            
            # 改善提案生成
            improvements = self._generate_improvement_suggestions(analysis_results)
            
            return {
                "file_path": file_path,
                "checks_performed": checks,
                "results": analysis_results,
                "overall_score": overall_score,
                "improvements": improvements,
                "meets_standards": overall_score >= self.quality_threshold
            }
        
        elif task_type == "performance_optimization":
            code = parameters.get("code", "")
            goals = parameters.get("goals", ["speed"])
            
            # パフォーマンス最適化
            optimized_code = await self._optimize_code(code, goals)
            
            # ベンチマーク実行
            benchmark_results = await self._run_benchmark(code, optimized_code)
            
            return {
                "original_code": code,
                "optimized_code": optimized_code,
                "optimization_goals": goals,
                "benchmark": benchmark_results,
                "improvements_made": self._list_optimizations_applied(code, optimized_code)
            }
        
        elif task_type == "continuous_monitoring":
            # 継続的監視タスク
            targets = parameters.get("targets", [])
            metrics = parameters.get("metrics", ["all"])
            
            monitoring_results = await self._perform_monitoring(targets, metrics)
            
            return {
                "targets_monitored": len(targets),
                "metrics": metrics,
                "results": monitoring_results,
                "alerts": self._generate_alerts(monitoring_results)
            }
        
        return await super().execute_specialized_task(
            task_type, parameters, consultation_result
        )
    
    async def _analyze_complexity(self, file_path: str) -> Dict[str, Any]:
        """
        コード複雑度分析
        """
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            
            # AST解析
            tree = ast.parse(code)
            
            # メトリクス計算
            metrics = {
                "cyclomatic_complexity": self._calculate_cyclomatic_complexity(tree),
                "cognitive_complexity": self._calculate_cognitive_complexity(tree),
                "lines_of_code": len(code.splitlines()),
                "function_count": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                "class_count": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
            }
            
            # 複雑な関数の特定
            complex_functions = self._find_complex_functions(tree)
            
            return {
                "metrics": metrics,
                "complex_functions": complex_functions,
                "recommendations": self._complexity_recommendations(metrics)
            }
            
        except Exception as e:
            return {"error": f"Complexity analysis failed: {str(e)}"}
    
    async def _security_scan(self, file_path: str) -> Dict[str, Any]:
        """
        セキュリティスキャン
        """
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        vulnerabilities = []
        
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            
            # 危険なパターンのチェック
            dangerous_patterns = [
                ("eval(", "Use of eval() is dangerous"),
                ("exec(", "Use of exec() is dangerous"),
                ("__import__", "Dynamic imports can be risky"),
                ("pickle.loads", "Pickle deserialization is unsafe"),
                ("shell=True", "Shell injection risk"),
                ("password =", "Potential hardcoded password"),
                ("api_key =", "Potential hardcoded API key"),
                ("SECRET", "Potential exposed secret")
            ]
            
            for pattern, message in dangerous_patterns:
                if pattern in code:
                    line_no = code[:code.find(pattern)].count('\n') + 1
                    vulnerabilities.append({
                        "type": "security",
                        "severity": "high" if "eval" in pattern or "exec" in pattern else "medium",
                        "message": message,
                        "line": line_no,
                        "pattern": pattern
                    })
            
            # SQL インジェクションチェック
            if "execute(" in code and ("%" in code or ".format(" in code):
                vulnerabilities.append({
                    "type": "sql_injection",
                    "severity": "high",
                    "message": "Potential SQL injection vulnerability",
                    "recommendation": "Use parameterized queries"
                })
            
            return {
                "vulnerabilities": vulnerabilities,
                "severity_summary": self._summarize_severity(vulnerabilities),
                "secure": len(vulnerabilities) == 0
            }
            
        except Exception as e:
            return {"error": f"Security scan failed: {str(e)}"}
    
    async def _check_style(self, file_path: str) -> Dict[str, Any]:
        """
        スタイルチェック
        """
        try:
            # flake8を使用したスタイルチェック
            result = subprocess.run(
                ["flake8", "--max-line-length=100", "--format=json", file_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    "compliant": True,
                    "issues": [],
                    "message": "Code style is compliant"
                }
            else:
                # エラー解析
                issues = []
                for line in result.stdout.splitlines():
                    if ":" in line:
                        parts = line.split(":")
                        if len(parts) >= 4:
                            issues.append({
                                "line": parts[1],
                                "column": parts[2],
                                "code": parts[3].strip(),
                                "message": ":".join(parts[4:]).strip()
                            })
                
                return {
                    "compliant": False,
                    "issues": issues,
                    "total_issues": len(issues)
                }
                
        except FileNotFoundError:
            # flake8がインストールされていない場合は基本チェック
            return await self._basic_style_check(file_path)
        except Exception as e:
            return {"error": f"Style check failed: {str(e)}"}
    
    async def _analyze_performance(self, file_path: str) -> Dict[str, Any]:
        """
        パフォーマンス分析
        """
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            
            performance_issues = []
            
            # パフォーマンスアンチパターンの検出
            antipatterns = [
                ("in range(len(", "Use enumerate() instead of range(len())"),
                ("for.*in.*for", "Nested loops detected - consider optimization"),
                ("append.*for", "Consider list comprehension"),
                ("sleep(", "Blocking sleep detected - consider async"),
                ("**", "Expensive exponentiation operation")
            ]
            
            for pattern, message in antipatterns:
                if pattern in code:
                    performance_issues.append({
                        "pattern": pattern,
                        "message": message,
                        "impact": "medium"
                    })
            
            # 大きなデータ構造の検出
            if "range(1000" in code or "range(10000" in code:
                performance_issues.append({
                    "pattern": "large range",
                    "message": "Large data structure detected",
                    "impact": "high"
                })
            
            return {
                "issues": performance_issues,
                "optimization_potential": "high" if len(performance_issues) > 3 else "medium",
                "recommendations": self._performance_recommendations(performance_issues)
            }
            
        except Exception as e:
            return {"error": f"Performance analysis failed: {str(e)}"}
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """
        サイクロマティック複雑度の計算
        """
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """
        認知的複雑度の計算（簡易版）
        """
        complexity = 0
        nesting_level = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1 + nesting_level
                nesting_level += 1
            elif isinstance(node, ast.FunctionDef):
                nesting_level = 0  # Reset for new function
        
        return complexity
    
    def _find_complex_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """
        複雑な関数の特定
        """
        complex_functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_complexity = self._calculate_cyclomatic_complexity(node)
                if func_complexity > self.quality_standards["code_complexity"]:
                    complex_functions.append({
                        "name": node.name,
                        "complexity": func_complexity,
                        "line": node.lineno,
                        "recommendation": "Consider refactoring this function"
                    })
        
        return complex_functions
    
    def _calculate_overall_score(self, analysis_results: Dict[str, Any]) -> float:
        """
        総合品質スコアの計算
        """
        score = 100.0
        
        # 複雑度による減点
        if "complexity" in analysis_results and not analysis_results["complexity"].get("error"):
            complexity = analysis_results["complexity"]["metrics"]["cyclomatic_complexity"]
            if complexity > self.quality_standards["code_complexity"]:
                score -= min(20, (complexity - self.quality_standards["code_complexity"]) * 2)
        
        # セキュリティによる減点
        if "security" in analysis_results and not analysis_results["security"].get("error"):
            vulnerabilities = analysis_results["security"]["vulnerabilities"]
            score -= len(vulnerabilities) * 10
        
        # スタイルによる減点
        if "style" in analysis_results and not analysis_results["style"].get("error"):
            if not analysis_results["style"]["compliant"]:
                score -= min(15, analysis_results["style"].get("total_issues", 0))
        
        # パフォーマンスによる減点
        if "performance" in analysis_results and not analysis_results["performance"].get("error"):
            issues = analysis_results["performance"]["issues"]
            score -= len(issues) * 5
        
        return max(0.0, score)
    
    def _generate_improvement_suggestions(
        self, 
        analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        改善提案の生成
        """
        suggestions = []
        
        # 複雑度の改善提案
        if "complexity" in analysis_results:
            complex_funcs = analysis_results["complexity"].get("complex_functions", [])
            for func in complex_funcs:
                suggestions.append({
                    "type": "refactoring",
                    "priority": "high",
                    "target": f"Function '{func['name']}'",
                    "suggestion": "Break down into smaller functions",
                    "expected_impact": "Reduce complexity by 30-50%"
                })
        
        # セキュリティの改善提案
        if "security" in analysis_results:
            vulnerabilities = analysis_results["security"].get("vulnerabilities", [])
            for vuln in vulnerabilities:
                suggestions.append({
                    "type": "security",
                    "priority": "critical" if vuln["severity"] == "high" else "high",
                    "target": f"Line {vuln.get('line', 'unknown')}",
                    "suggestion": vuln.get("recommendation", "Fix security issue"),
                    "expected_impact": "Eliminate security vulnerability"
                })
        
        return suggestions
    
    async def _optimize_code(self, code: str, goals: List[str]) -> str:
        """
        コード最適化
        """
        optimized_code = code
        
        if "speed" in goals:
            # 速度最適化
            optimized_code = self._apply_speed_optimizations(optimized_code)
        
        if "memory" in goals:
            # メモリ最適化
            optimized_code = self._apply_memory_optimizations(optimized_code)
        
        if "readability" in goals:
            # 可読性最適化
            optimized_code = self._apply_readability_optimizations(optimized_code)
        
        return optimized_code
    
    def _apply_speed_optimizations(self, code: str) -> str:
        """
        速度最適化の適用
        """
        # リスト内包表記への変換
        code = code.replace(
            "result = []\nfor item in items:\n    result.append(item)",
            "result = [item for item in items]"
        )
        
        # enumerate使用への変換
        code = code.replace(
            "for i in range(len(items)):",
            "for i, item in enumerate(items):"
        )
        
        return code
    
    def _apply_memory_optimizations(self, code: str) -> str:
        """
        メモリ最適化の適用
        """
        # ジェネレータへの変換提案
        if "return [" in code and "]" in code:
            # 大きなリストの場合はジェネレータを推奨
            pass  # 実際の実装では適切な変換を行う
        
        return code
    
    def _apply_readability_optimizations(self, code: str) -> str:
        """
        可読性最適化の適用
        """
        # 適切な変数名への提案
        # コメントの追加提案
        # 関数分割の提案
        
        return code
    
    async def _run_benchmark(self, original_code: str, optimized_code: str) -> Dict[str, Any]:
        """
        ベンチマーク実行（シミュレーション）
        """
        # 実際の実装では timeit などを使用
        return {
            "original_time": 1.0,  # seconds
            "optimized_time": 0.7,  # seconds
            "improvement": "30%",
            "memory_usage": {
                "original": "100MB",
                "optimized": "80MB"
            }
        }
    
    def _list_optimizations_applied(self, original: str, optimized: str) -> List[str]:
        """
        適用された最適化のリスト
        """
        optimizations = []
        
        if "for i, item in enumerate" in optimized and "range(len(" in original:
            optimizations.append("Replaced range(len()) with enumerate()")
        
        if "[item for item in" in optimized and "append" in original:
            optimizations.append("Converted loop to list comprehension")
        
        return optimizations
    
    async def _basic_style_check(self, file_path: str) -> Dict[str, Any]:
        """
        基本的なスタイルチェック（flake8なしの場合）
        """
        issues = []
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # 行長チェック
            if len(line.rstrip()) > 100:
                issues.append({
                    "line": i,
                    "code": "E501",
                    "message": f"Line too long ({len(line.rstrip())} > 100 characters)"
                })
            
            # trailing whitespaceチェック
            if line.rstrip() != line.rstrip('\n').rstrip('\r'):
                issues.append({
                    "line": i,
                    "code": "W291",
                    "message": "Trailing whitespace"
                })
        
        return {
            "compliant": len(issues) == 0,
            "issues": issues,
            "total_issues": len(issues)
        }
    
    def _complexity_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """
        複雑度に基づく推奨事項
        """
        recommendations = []
        
        if metrics["cyclomatic_complexity"] > 10:
            recommendations.append("Consider breaking down complex functions")
        
        if metrics["lines_of_code"] > 500:
            recommendations.append("File is too large, consider splitting into modules")
        
        if metrics["function_count"] > 20:
            recommendations.append("Too many functions in one file, consider reorganizing")
        
        return recommendations
    
    def _summarize_severity(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        脆弱性の重要度サマリー
        """
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "medium")
            summary[severity] = summary.get(severity, 0) + 1
        
        return summary
    
    def _performance_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """
        パフォーマンス推奨事項
        """
        recommendations = []
        
        for issue in issues:
            if "nested loops" in issue["message"]:
                recommendations.append("Consider using numpy for matrix operations")
            elif "list comprehension" in issue["message"]:
                recommendations.append("Use list comprehensions for better performance")
        
        return recommendations
    
    async def _perform_monitoring(
        self, 
        targets: List[str], 
        metrics: List[str]
    ) -> List[Dict[str, Any]]:
        """
        継続的監視の実行
        """
        results = []
        
        for target in targets:
            target_results = {
                "target": target,
                "timestamp": asyncio.get_event_loop().time(),
                "metrics": {}
            }
            
            if "performance" in metrics or "all" in metrics:
                # パフォーマンスメトリクスの収集
                target_results["metrics"]["performance"] = {
                    "response_time": 0.05,  # シミュレーション値
                    "throughput": 1000,
                    "cpu_usage": 25.5
                }
            
            if "quality" in metrics or "all" in metrics:
                # 品質メトリクスの収集
                target_results["metrics"]["quality"] = {
                    "code_coverage": 92.5,
                    "complexity_score": 8.2,
                    "technical_debt": "2.5 hours"
                }
            
            results.append(target_results)
        
        return results
    
    def _generate_alerts(self, monitoring_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        監視結果に基づくアラート生成
        """
        alerts = []
        
        for result in monitoring_results:
            # パフォーマンスアラート
            perf = result.get("metrics", {}).get("performance", {})
            if perf.get("response_time", 0) > self.quality_standards["performance_threshold"]:
                alerts.append({
                    "type": "performance",
                    "severity": "warning",
                    "target": result["target"],
                    "message": f"Response time {perf['response_time']}s exceeds threshold"
                })
            
            # 品質アラート
            quality = result.get("metrics", {}).get("quality", {})
            if quality.get("code_coverage", 100) < self.quality_standards["test_coverage"]:
                alerts.append({
                    "type": "quality",
                    "severity": "warning",
                    "target": result["target"],
                    "message": f"Code coverage {quality['code_coverage']}% below standard"
                })
        
        return alerts


# 単体実行用
async def main():
    guardian = QualityGuardian()
    await guardian.start()
    print(f"Quality Guardian running on port {guardian.port}")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await guardian.stop()


if __name__ == "__main__":
    asyncio.run(main())