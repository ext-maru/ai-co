#!/usr/bin/env python3
"""
エルダーズギルド 厳密品質監査システム
エルダー評議会令第700号 - 完璧品質追求令

機能:
1. 全コードベースの徹底的品質チェック
2. セキュリティ脆弱性の完全スキャン
3. パフォーマンス問題の検出
4. Iron Will基準の厳格適用
5. 技術負債の詳細分析
"""

import os
import re
import ast
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import argparse
from dataclasses import dataclass, asdict
import hashlib
import time

@dataclass
class QualityViolation:
    """品質違反"""
    file_path: str
    line_number: int
    violation_type: str
    severity: str  # critical, high, medium, low
    message: str
    suggestion: str

@dataclass
class SecurityIssue:
    """セキュリティ問題"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    cwe_id: Optional[str]
    description: str
    fix_suggestion: str

@dataclass
class PerformanceIssue:
    """パフォーマンス問題"""
    file_path: str
    line_number: int
    issue_type: str
    impact: str  # high, medium, low
    description: str
    optimization: str

@dataclass
class TechnicalDebt:
    """技術負債"""
    file_path: str
    debt_type: str
    estimated_hours: float
    priority: str
    description: str
    refactoring_suggestion: str

@dataclass
class QualityReport:
    """品質レポート"""
    timestamp: str
    total_files: int
    scanned_files: int
    quality_score: float
    violations: List[QualityViolation]
    security_issues: List[SecurityIssue]
    performance_issues: List[PerformanceIssue]
    technical_debts: List[TechnicalDebt]
    iron_will_compliance: float
    recommendations: List[str]

class StrictQualityAuditor:
    """厳密品質監査官"""
    
    def __init__(self, base_path: str = "/home/aicompany/ai_co"):
        self.base_path = Path(base_path)
        self.violations = []
        self.security_issues = []
        self.performance_issues = []
        self.technical_debts = []
        
        # 厳格な品質基準
        self.quality_rules = {
            # コード複雑度
            "max_complexity": 10,
            "max_function_length": 50,
            "max_file_length": 500,
            "max_line_length": 100,
            
            # 命名規則
            "min_variable_length": 3,
            "max_variable_length": 30,
            
            # コメント
            "min_comment_ratio": 0.15,  # 15%以上
            "docstring_required": True,
            
            # インポート
            "max_imports": 20,
            "no_wildcard_imports": True,
            
            # ネスト
            "max_nesting_depth": 4,
            
            # 引数
            "max_parameters": 5,
            "max_return_statements": 3,
        }
        
        # セキュリティパターン
        self.security_patterns = {
            "eval_usage": (r"eval\\s*\\(", "CWE-95", "Code Injection"),
            "exec_usage": (r"exec\\s*\\(", "CWE-95", "Code Injection"),
            "pickle_load": (r"pickle\\.load", "CWE-502", "Deserialization of Untrusted Data"),
            "os_system": (r"os\\.system\\s*\\(", "CWE-78", "OS Command Injection"),
            "subprocess_shell": (r"subprocess.*shell\\s*=\\s*True", "CWE-78", "Command Injection"),
            "sql_injection": (r'".*SELECT.*%s.*"', "CWE-89", "SQL Injection"),
            "hardcoded_password": (r"password\\s*=\\s*[\"'][^\"']+[\"']", "CWE-798", "Hardcoded Credentials"),
            "weak_random": (r"random\\.\\w+\\(", "CWE-330", "Weak Random"),
            "md5_usage": (r"hashlib\\.md5", "CWE-327", "Weak Cryptography"),
            "http_urls": (r"http://", "CWE-319", "Cleartext Transmission"),
            "temp_file": (r"tempfile\\.mktemp", "CWE-377", "Insecure Temporary File"),
            "__import__": (r"__import__\\s*\\(", "CWE-95", "Dynamic Import"),
            "yaml_load": (r"yaml\\.load\\s*\\([^,)]*\\)", "CWE-502", "Unsafe YAML Load"),
        }
        
        # パフォーマンスパターン
        self.performance_patterns = {
            "nested_loops": (r"for.*:\\s*\\n\\s*for.*:", "Nested loops detected"),
            "string_concat_loop": (r"for.*:\\s*\\n.*\\+=\\s*[\"']", "String concatenation in loop"),
            "list_comp_complex": (r"\\[.*for.*if.*for.*\\]", "Complex list comprehension"),
            "multiple_db_queries": (r"(execute|query)\\(.*\\).*\\n.*\\1\\(", "Multiple DB queries"),
            "synchronous_io": (r"(open|read|write)\\s*\\(", "Synchronous I/O operation"),
            "global_usage": (r"global\\s+", "Global variable usage"),
            "large_data_structure": (r"(list|dict)\\s*\\(\\s*range\\s*\\(\\s*\\d{4,}", "Large data structure"),
        }
        
        # 技術負債パターン
        self.debt_patterns = {
            "TODO": (r"#\\s*(TODO|todo)", 2.0, "Unfinished implementation"),
            "FIXME": (r"#\\s*(FIXME|fixme)", 4.0, "Known bug"),
            "HACK": (r"#\\s*(HACK|hack)", 8.0, "Temporary workaround"),
            "XXX": (r"#\\s*(XXX|xxx)", 3.0, "Warning or concern"),
            "REFACTOR": (r"#\\s*(REFACTOR|refactor)", 6.0, "Needs refactoring"),
            "DEPRECATED": (r"#\\s*(DEPRECATED|deprecated)", 5.0, "Deprecated code"),
            "duplicate_code": (None, 10.0, "Duplicate code detected"),
            "dead_code": (None, 3.0, "Unused code"),
            "complex_function": (None, 8.0, "Overly complex function"),
        }
        
        # Iron Will違反パターン
        self.iron_will_patterns = [
            "TODO", "FIXME", "HACK", "XXX", "TEMP", "REMOVE", "DELETE",
            "workaround", "temporary", "quick fix", "dirty", "ugly"
        ]
    
    def audit_codebase(self) -> QualityReport:
        """コードベース監査実行"""
        print("🔍 厳密品質監査開始...")
        start_time = time.time()
        
        # ファイル収集
        py_files = list(self.base_path.rglob("*.py"))
        py_files = [f for f in py_files if not any(
            p in str(f) for p in ["venv", ".git", "__pycache__", "migrations"]
        )]
        
        total_files = len(py_files)
        scanned_files = 0
        
        # 各ファイル監査
        for file_path in py_files:
            try:
                self._audit_file(file_path)
                scanned_files += 1
                
                # 進捗表示
                if scanned_files % 10 == 0:
                    progress = (scanned_files / total_files) * 100
                    print(f"進捗: {progress:.1f}% ({scanned_files}/{total_files})")
                    
            except Exception as e:
                print(f"エラー: {file_path} - {e}")
        
        # スコア計算
        quality_score = self._calculate_quality_score()
        iron_will_compliance = self._calculate_iron_will_compliance(py_files)
        
        # 推奨事項生成
        recommendations = self._generate_recommendations()
        
        # レポート作成
        report = QualityReport(
            timestamp=datetime.now().isoformat(),
            total_files=total_files,
            scanned_files=scanned_files,
            quality_score=quality_score,
            violations=self.violations,
            security_issues=self.security_issues,
            performance_issues=self.performance_issues,
            technical_debts=self.technical_debts,
            iron_will_compliance=iron_will_compliance,
            recommendations=recommendations
        )
        
        elapsed_time = time.time() - start_time
        print(f"\n✅ 監査完了（所要時間: {elapsed_time:.1f}秒）")
        
        return report
    
    def _audit_file(self, file_path: Path):
        """ファイル監査"""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # 基本チェック
            self._check_file_basics(file_path, content, lines)
            
            # ASTベースチェック
            try:
                tree = ast.parse(content)
                self._check_ast_patterns(file_path, tree, content)
            except SyntaxError:
                self.violations.append(QualityViolation(
                    file_path=str(file_path),
                    line_number=0,
                    violation_type="syntax_error",
                    severity="critical",
                    message="Syntax error in file",
                    suggestion="Fix syntax errors before proceeding"
                ))
            
            # パターンベースチェック
            self._check_security_patterns(file_path, content, lines)
            self._check_performance_patterns(file_path, content, lines)
            self._check_debt_patterns(file_path, content, lines)
            
        except Exception as e:
            print(f"ファイル監査エラー {file_path}: {e}")
    
    def _check_file_basics(self, file_path: Path, content: str, lines: List[str]):
        """基本チェック"""
        # ファイル長
        if len(lines) > self.quality_rules["max_file_length"]:
            self.violations.append(QualityViolation(
                file_path=str(file_path),
                line_number=len(lines),
                violation_type="file_too_long",
                severity="medium",
                message=f"File has {len(lines)} lines (max: {self.quality_rules['max_file_length']})",
                suggestion="Split into smaller modules"
            ))
        
        # 行長チェック
        for i, line in enumerate(lines, 1):
            if len(line) > self.quality_rules["max_line_length"]:
                self.violations.append(QualityViolation(
                    file_path=str(file_path),
                    line_number=i,
                    violation_type="line_too_long",
                    severity="low",
                    message=f"Line length {len(line)} exceeds {self.quality_rules['max_line_length']}",
                    suggestion="Break into multiple lines"
                ))
        
        # コメント率
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        if lines:
            comment_ratio = comment_lines / len(lines)
            if comment_ratio < self.quality_rules["min_comment_ratio"]:
                self.violations.append(QualityViolation(
                    file_path=str(file_path),
                    line_number=0,
                    violation_type="insufficient_comments",
                    severity="medium",
                    message=f"Comment ratio {comment_ratio:.1%} below minimum {self.quality_rules[ \
                        'min_comment_ratio']:.0%}",
                    suggestion="Add more explanatory comments"
                ))
    
    def _check_ast_patterns(self, file_path: Path, tree: ast.AST, content: str):
        """AST解析"""
        
        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self, auditor, file_path):
                self.auditor = auditor
                self.file_path = file_path
                self.current_function = None
                self.complexity = 0
                self.nesting_depth = 0
                
            def visit_FunctionDef(self, node):
                self.current_function = node.name
                old_complexity = self.complexity
                self.complexity = 1  # 基本複雑度
                
                # パラメータ数チェック
                if len(node.args.args) > self.auditor.quality_rules["max_parameters"]:
                    self.auditor.violations.append(QualityViolation(
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        violation_type="too_many_parameters",
                        severity="medium",
                        message=f"Function '{node.name}' has {len(node.args.args)} parameters",
                        suggestion="Consider using configuration object or builder pattern"
                    ))
                
                # ドキュメント文字列チェック
                if self.auditor.quality_rules["docstring_required"]:
                    if not (node.body and isinstance(node.body[0], ast.Expr) and 
                           isinstance(node.body[0].value, ast.Str)):
                        self.auditor.violations.append(QualityViolation(
                            file_path=str(self.file_path),
                            line_number=node.lineno,
                            violation_type="missing_docstring",
                            severity="medium",
                            message=f"Function '{node.name}' lacks docstring",
                            suggestion="Add descriptive docstring"
                        ))
                
                # 関数の処理
                self.generic_visit(node)
                
                # 複雑度チェック
                if self.complexity > self.auditor.quality_rules["max_complexity"]:
                    self.auditor.violations.append(QualityViolation(
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        violation_type="high_complexity",
                        severity="high",
                        message=f"Function '{node.name}' has complexity {self.complexity}",
                        suggestion="Simplify logic or split into smaller functions"
                    ))
                    
                    # 技術負債として記録
                    self.auditor.technical_debts.append(TechnicalDebt(
                        file_path=str(self.file_path),
                        debt_type="complex_function",
                        estimated_hours=8.0,
                        priority="high",
                        description=f"Function '{node.name}' is too complex",
                        refactoring_suggestion="Extract methods or use strategy pattern"
                    ))
                
                self.complexity = old_complexity
                self.current_function = None
                
            def visit_If(self, node):
                self.complexity += 1
                self.nesting_depth += 1
                
                if self.nesting_depth > self.auditor.quality_rules["max_nesting_depth"]:
                    self.auditor.violations.append(QualityViolation(
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        violation_type="deep_nesting",
                        severity="medium",
                        message=f"Nesting depth {self.nesting_depth} exceeds maximum",
                        suggestion="Extract nested logic into separate functions"
                    ))
                
                self.generic_visit(node)
                self.nesting_depth -= 1
                
            def visit_For(self, node):
                self.complexity += 1
                self.nesting_depth += 1
                self.generic_visit(node)
                self.nesting_depth -= 1
                
            def visit_While(self, node):
                self.complexity += 1
                self.nesting_depth += 1
                self.generic_visit(node)
                self.nesting_depth -= 1
                
            def visit_ExceptHandler(self, node):
                self.complexity += 1
                self.generic_visit(node)
        
        visitor = ComplexityVisitor(self, file_path)
        visitor.visit(tree)
    
    def _check_security_patterns(self, file_path: Path, content: str, lines: List[str]):
        """セキュリティパターンチェック"""
        for pattern_name, (pattern, cwe_id, description) in self.security_patterns.items():
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    severity = "critical" if pattern_name in [
                        "eval_usage", "exec_usage", "os_system", "subprocess_shell"
                    ] else "high"
                    
                    self.security_issues.append(SecurityIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type=pattern_name,
                        severity=severity,
                        cwe_id=cwe_id,
                        description=f"{description} vulnerability detected",
                        fix_suggestion=self._get_security_fix(pattern_name)
                    ))
    
    def _get_security_fix(self, issue_type: str) -> str:
        """セキュリティ修正提案"""
        fixes = {
            "eval_usage": "Use ast.literal_eval() or json.loads() instead",
            "exec_usage": "Avoid dynamic code execution, use specific functions",
            "pickle_load": "Use JSON or other safe serialization formats",
            "os_system": "Use subprocess.run() with shell=False",
            "subprocess_shell": "Set shell=False and use list arguments",
            "sql_injection": "Use parameterized queries with placeholders",
            "hardcoded_password": "Use environment variables or secure vaults",
            "weak_random": "Use secrets module for cryptographic randomness",
            "md5_usage": "Use SHA-256 or stronger hash algorithms",
            "http_urls": "Use HTTPS for all external communications",
            "temp_file": "Use tempfile.NamedTemporaryFile() or mkstemp()",
            "__import__": "Use explicit imports at module level",
            "yaml_load": "Use yaml.safe_load() instead",
        }
        return fixes.get(issue_type, "Review and fix security issue")
    
    def _check_performance_patterns(self, file_path: Path, content: str, lines: List[str]):
        """パフォーマンスパターンチェック"""
        for pattern_name, (pattern, description) in self.performance_patterns.items():
            # 複数行パターンは content 全体で検索
            if pattern_name in ["nested_loops", "multiple_db_queries"]:
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                for match in matches:
                    line_no = content[:match.start()].count('\n') + 1
                    self.performance_issues.append(PerformanceIssue(
                        file_path=str(file_path),
                        line_number=line_no,
                        issue_type=pattern_name,
                        impact="high" if pattern_name == "nested_loops" else "medium",
                        description=description,
                        optimization=self._get_performance_fix(pattern_name)
                    ))
            else:
                # 単一行パターン
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        self.performance_issues.append(PerformanceIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type=pattern_name,
                            impact="medium",
                            description=description,
                            optimization=self._get_performance_fix(pattern_name)
                        ))
    
    def _get_performance_fix(self, issue_type: str) -> str:
        """パフォーマンス改善提案"""
        fixes = {
            "nested_loops": "Consider using list comprehensions, numpy, or algorithmic optimization",
            "string_concat_loop": "Use list.append() and ''.join() for string building",
            "list_comp_complex": "Split into multiple simpler comprehensions or use regular loops",
            "multiple_db_queries": "Use JOIN queries or batch operations",
            "synchronous_io": "Consider using async/await for I/O operations",
            "global_usage": "Use function parameters or class attributes instead",
            "large_data_structure": "Use generators or process data in chunks",
        }
        return fixes.get(issue_type, "Optimize for better performance")
    
    def _check_debt_patterns(self, file_path: Path, content: str, lines: List[str]):
        """技術負債パターンチェック"""
        for pattern_name, (pattern, hours, description) in self.debt_patterns.items():
            if pattern:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        priority = "high" if hours >= 6 else "medium" if hours >= 3 else "low"
                        
                        self.technical_debts.append(TechnicalDebt(
                            file_path=str(file_path),
                            debt_type=pattern_name,
                            estimated_hours=hours,
                            priority=priority,
                            description=f"{description}: {line.strip()}",
                            refactoring_suggestion=self._get_debt_fix(pattern_name)
                        ))
    
    def _get_debt_fix(self, debt_type: str) -> str:
        """技術負債修正提案"""
        fixes = {
            "TODO": "Complete the implementation as planned",
            "FIXME": "Fix the identified issue promptly",
            "HACK": "Replace with proper solution",
            "XXX": "Review and address the concern",
            "REFACTOR": "Schedule refactoring sprint",
            "DEPRECATED": "Update to use modern alternatives",
            "duplicate_code": "Extract common functionality into shared module",
            "dead_code": "Remove unused code after verification",
            "complex_function": "Break down into smaller, focused functions",
        }
        return fixes.get(debt_type, "Address technical debt")
    
    def _calculate_quality_score(self) -> float:
        """品質スコア計算"""
        # 基本スコア 100
        score = 100.0
        
        # 違反による減点
        for violation in self.violations:
            if violation.severity == "critical":
                score -= 5
            elif violation.severity == "high":
                score -= 3
            elif violation.severity == "medium":
                score -= 1
            elif violation.severity == "low":
                score -= 0.5
        
        # セキュリティ問題による減点
        for issue in self.security_issues:
            if issue.severity == "critical":
                score -= 10
            elif issue.severity == "high":
                score -= 5
        
        # パフォーマンス問題による減点
        for issue in self.performance_issues:
            if issue.impact == "high":
                score -= 3
            elif issue.impact == "medium":
                score -= 1
        
        # 技術負債による減点
        total_debt_hours = sum(debt.estimated_hours for debt in self.technical_debts)
        score -= min(total_debt_hours / 10, 30)  # 最大30点減点
        
        return max(0, score)
    
    def _calculate_iron_will_compliance(self, files: List[Path]) -> float:
        """Iron Will準拠率計算"""
        total_files = len(files)
        compliant_files = 0
        
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Iron Will違反チェック
                has_violation = False
                for pattern in self.iron_will_patterns:
                    if re.search(rf"\\b{pattern}\\b", content, re.IGNORECASE):
                        has_violation = True
                        break
                
                if not has_violation:
                    compliant_files += 1
                    
            except:
                pass
        
        return (compliant_files / total_files * 100) if total_files > 0 else 0
    
    def _generate_recommendations(self) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        # セキュリティ推奨
        critical_security = sum(1 for i in self.security_issues if i.severity == "critical")
        if critical_security > 0:
            recommendations.append(
                f"🚨 CRITICAL: {critical_security}件の重大なセキュリティ脆弱性を即座に修正してください"
            )
        
        # 複雑度推奨
        high_complexity = sum(1 for v in self.violations if v.violation_type == "high_complexity")
        if high_complexity > 5:
            recommendations.append(
                f"🔧 {high_complexity}個の高複雑度関数をリファクタリングしてください"
            )
        
        # 技術負債推奨
        total_debt = sum(d.estimated_hours for d in self.technical_debts)
        if total_debt > 100:
            recommendations.append(
                f"💳 {total_debt:.0f}時間分の技術負債があります。計画的な返済を推奨"
            )
        
        # ドキュメント推奨
        missing_docs = sum(1 for v in self.violations if v.violation_type == "missing_docstring")
        if missing_docs > 10:
            recommendations.append(
                f"📝 {missing_docs}個の関数にドキュメント文字列を追加してください"
            )
        
        # パフォーマンス推奨
        perf_issues = len(self.performance_issues)
        if perf_issues > 5:
            recommendations.append(
                f"⚡ {perf_issues}件のパフォーマンス問題を最適化してください"
            )
        
        # Iron Will推奨
        iron_will_violations = sum(1 for d in self.technical_debts if d.debt_type in ["TODO", "FIXME", "HACK"])
        if iron_will_violations > 0:
            recommendations.append(
                f"🗡️ Iron Will違反: {iron_will_violations}件の回避策を正式実装に置き換えてください"
            )
        
        if not recommendations:
            recommendations.append("✅ 重大な品質問題は検出されませんでした")
        
        return recommendations
    
    def generate_report(self, report: QualityReport, output_path: Path):
        """レポート生成"""
        # Markdown版
        md_content = self._generate_markdown_report(report)
        md_path = output_path / f"quality-audit-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        md_path.write_text(md_content, encoding='utf-8')
        
        # JSON版
        json_path = md_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 レポート生成完了:")
        print(f"  - Markdown: {md_path}")
        print(f"  - JSON: {json_path}")
        
        return md_path
    
    def _generate_markdown_report(self, report: QualityReport) -> str:
        """Markdownレポート生成"""
        severity_counts = {
            "critical": sum(1 for v in report.violations if v.severity == "critical"),
            "high": sum(1 for v in report.violations if v.severity == "high"),
            "medium": sum(1 for v in report.violations if v.severity == "medium"),
            "low": sum(1 for v in report.violations if v.severity == "low"),
        }
        
        security_counts = {
            "critical": sum(1 for i in report.security_issues if i.severity == "critical"),
            "high": sum(1 for i in report.security_issues if i.severity == "high"),
        }
        
        total_debt_hours = sum(d.estimated_hours for d in report.technical_debts)
        
        return f"""---
title: "厳密品質監査レポート"
description: "エルダーズギルド品質基準に基づく完全監査結果"
category: "reports"
subcategory: "quality"
audience: "all"
difficulty: "advanced"
last_updated: "{datetime.now().strftime('%Y-%m-%d')}"
version: "1.0.0"
status: "approved"
author: "strict-quality-auditor"
tags:
  - "quality"
  - "security"
  - "performance"
  - "technical-debt"
report_type: "audit"
sage_assignment: "incident_sage"
---

# 🏛️ 厳密品質監査レポート

**監査日時**: {report.timestamp}  
**対象ファイル数**: {report.total_files}  
**スキャン完了数**: {report.scanned_files}

---

## 📊 総合評価

### 🎯 品質スコア
**{report.quality_score:.1f} / 100**

### 🗡️ Iron Will準拠率
**{report.iron_will_compliance:.1f}%**

### 📈 主要指標
| カテゴリ | 件数 | 重要度 |
|---------|------|--------|
| 品質違反 | {len(report.violations)} | Critical: {severity_counts['critical']}, High: {severity_counts['high']} |
| セキュリティ問題 | {len(report.security_issues)} | Critical: {security_counts['critical']}, High: {security_counts['high']} |
| パフォーマンス問題 | {len(report.performance_issues)} | - |
| 技術負債 | {len(report.technical_debts)} | 合計: {total_debt_hours:.0f}時間 |

---

## 🚨 重大な問題（Critical）

### セキュリティ脆弱性
{self._format_critical_security_issues(report.security_issues)}

### 品質違反
{self._format_critical_violations(report.violations)}

---

## ⚠️ 重要な問題（High）

### セキュリティ
{self._format_high_security_issues(report.security_issues)}

### 品質
{self._format_high_violations(report.violations)}

### パフォーマンス
{self._format_high_performance_issues(report.performance_issues)}

---

## 💳 技術負債

### 優先度別内訳
{self._format_technical_debt_summary(report.technical_debts)}

### 詳細リスト（上位10件）
{self._format_technical_debt_details(report.technical_debts[:10])}

---

## 📋 推奨事項

{self._format_recommendations(report.recommendations)}

---

## 📊 詳細統計

### 違反タイプ別分布
{self._format_violation_distribution(report.violations)}

### ファイル別ワースト10
{self._format_worst_files(report)}

---

## 🎯 改善計画

### 即座実施（1週間以内）
1. すべてのCriticalセキュリティ脆弱性の修正
2. High優先度の品質違反の対応
3. Iron Will違反の除去

### 短期実施（1ヶ月以内）
1. パフォーマンス問題の最適化
2. 技術負債の計画的返済開始
3. ドキュメント整備

### 長期実施（3ヶ月以内）
1. コード品質基準の完全達成
2. 自動品質チェックの強化
3. 継続的改善プロセスの確立

---

**Iron Will**: No Workarounds! 🗡️  
**Quality First**: 妥協なき品質追求! 🏛️

---

**監査実行日**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**次回監査予定**: {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}
"""
    
    def _format_critical_security_issues(self, issues: List[SecurityIssue]) -> str:
        critical = [i for i in issues if i.severity == "critical"]
        if not critical:
            return "なし ✅"
        
        lines = []
        for issue in critical[:5]:  # 上位5件
            lines.append(f"""
**{issue.issue_type}** ({issue.cwe_id})
- ファイル: `{issue.file_path}:{issue.line_number}`
- 説明: {issue.description}
- 修正案: {issue.fix_suggestion}
""")
        
        if len(critical) > 5:
            lines.append(f"\n... 他 {len(critical) - 5} 件")
        
        return '\n'.join(lines)
    
    def _format_critical_violations(self, violations: List[QualityViolation]) -> str:
        critical = [v for v in violations if v.severity == "critical"]
        if not critical:
            return "なし ✅"
        
        lines = []
        for violation in critical[:5]:
            lines.append(f"""
**{violation.violation_type}**
- ファイル: `{violation.file_path}:{violation.line_number}`
- メッセージ: {violation.message}
- 提案: {violation.suggestion}
""")
        
        if len(critical) > 5:
            lines.append(f"\n... 他 {len(critical) - 5} 件")
        
        return '\n'.join(lines)
    
    def _format_high_security_issues(self, issues: List[SecurityIssue]) -> str:
        high = [i for i in issues if i.severity == "high"]
        if not high:
            return "なし ✅"
        
        # タイプ別に集計
        by_type = {}
        for issue in high:
            if issue.issue_type not in by_type:
                by_type[issue.issue_type] = []
            by_type[issue.issue_type].append(issue)
        
        lines = []
        for issue_type, issues in sorted(by_type.items()):
            lines.append(f"- **{issue_type}**: {len(issues)}件")
        
        return '\n'.join(lines)
    
    def _format_high_violations(self, violations: List[QualityViolation]) -> str:
        high = [v for v in violations if v.severity == "high"]
        if not high:
            return "なし ✅"
        
        by_type = {}
        for violation in high:
            if violation.violation_type not in by_type:
                by_type[violation.violation_type] = 0
            by_type[violation.violation_type] += 1
        
        lines = []
        for vtype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{vtype}**: {count}件")
        
        return '\n'.join(lines)
    
    def _format_high_performance_issues(self, issues: List[PerformanceIssue]) -> str:
        high = [i for i in issues if i.impact == "high"]
        if not high:
            return "なし ✅"
        
        by_type = {}
        for issue in high:
            if issue.issue_type not in by_type:
                by_type[issue.issue_type] = 0
            by_type[issue.issue_type] += 1
        
        lines = []
        for itype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{itype}**: {count}件")
        
        return '\n'.join(lines)
    
    def _format_technical_debt_summary(self, debts: List[TechnicalDebt]) -> str:
        by_priority = {"high": 0, "medium": 0, "low": 0}
        hours_by_priority = {"high": 0, "medium": 0, "low": 0}
        
        for debt in debts:
            by_priority[debt.priority] += 1
            hours_by_priority[debt.priority] += debt.estimated_hours
        
        lines = []
        for priority in ["high", "medium", "low"]:
            if by_priority[priority] > 0:
                lines.append(
                    f"- **{priority.upper()}**: {by_priority[priority]}件 "
                    f"({hours_by_priority[priority]:.0f}時間)"
                )
        
        return '\n'.join(lines)
    
    def _format_technical_debt_details(self, debts: List[TechnicalDebt]) -> str:
        if not debts:
            return "技術負債なし ✅"
        
        lines = []
        for debt in debts:
            lines.append(f"""
**{debt.debt_type}** ({debt.priority})
- ファイル: `{debt.file_path}`
- 推定時間: {debt.estimated_hours}時間
- 説明: {debt.description}
- 提案: {debt.refactoring_suggestion}
""")
        
        return '\n'.join(lines)
    
    def _format_recommendations(self, recommendations: List[str]) -> str:
        if not recommendations:
            return "- 推奨事項なし"
        
        return '\n'.join(f"- {rec}" for rec in recommendations)
    
    def _format_violation_distribution(self, violations: List[QualityViolation]) -> str:
        distribution = {}
        for violation in violations:
            if violation.violation_type not in distribution:
                distribution[violation.violation_type] = 0
            distribution[violation.violation_type] += 1
        
        lines = ["| 違反タイプ | 件数 |", "|-----------|------|"]
        for vtype, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"| {vtype} | {count} |")
        
        return '\n'.join(lines)
    
    def _format_worst_files(self, report: QualityReport) -> str:
        file_scores = {}
        
        # 各ファイルのスコア計算
        for violation in report.violations:
            if violation.file_path not in file_scores:
                file_scores[violation.file_path] = 0
            
            if violation.severity == "critical":
                file_scores[violation.file_path] += 10
            elif violation.severity == "high":
                file_scores[violation.file_path] += 5
            elif violation.severity == "medium":
                file_scores[violation.file_path] += 2
            else:
                file_scores[violation.file_path] += 1
        
        for issue in report.security_issues:
            if issue.file_path not in file_scores:
                file_scores[issue.file_path] = 0
            file_scores[issue.file_path] += 20 if issue.severity == "critical" else 10
        
        # 上位10ファイル
        worst_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        
        lines = ["| ファイル | スコア |", "|---------|--------|"]
        for file_path, score in worst_files:
            # パスを短縮
            short_path = file_path.replace(str(self.base_path) + "/", "")
            lines.append(f"| {short_path} | {score} |")
        
        return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='エルダーズギルド厳密品質監査')
    parser.add_argument('--path', default='/home/aicompany/ai_co', help='監査対象パス')
    parser.add_argument('--output', default='/home/aicompany/ai_co/docs/reports/quality', help='出力先')
    parser.add_argument('--threshold', type=float, default=80.0, help='合格閾値')
    
    args = parser.parse_args()
    
    # 出力ディレクトリ作成
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 監査実行
    auditor = StrictQualityAuditor(args.path)
    report = auditor.audit_codebase()
    
    # レポート生成
    report_path = auditor.generate_report(report, output_path)
    
    # サマリー表示
    print(f"\n{'='*60}")
    print(f"📊 監査結果サマリー")
    print(f"{'='*60}")
    print(f"品質スコア: {report.quality_score:.1f}/100")
    print(f"Iron Will準拠率: {report.iron_will_compliance:.1f}%")
    print(f"重大な問題: {sum(1 for v in report.violations if v.severity == 'critical')}件")
    print(f"セキュリティ脆弱性: {len(report.security_issues)}件")
    print(f"技術負債: {sum(d.estimated_hours for d in report.technical_debts):.0f}時間")
    print(f"{'='*60}")
    
    # 合否判定
    if report.quality_score >= args.threshold:
        print(f"✅ 品質基準合格（閾値: {args.threshold}）")
        exit_code = 0
    else:
        print(f"❌ 品質基準不合格（閾値: {args.threshold}）")
        exit_code = 1
    
    print(f"\n📄 詳細レポート: {report_path}")
    
    return exit_code

if __name__ == "__main__":
    exit(main())