"""
🔮 Integrity Auditor - 誠実性監査魔法
虚偽報告、モック/スタブ悪用、実装詐称を検出する Ancient Elder の最重要魔法
"""

import ast
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Set, Optional, Tuple
from datetime import datetime
import logging

# プロジェクトルートをパスに追加
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.base import AncientElderBase, AuditResult, ViolationSeverity


class IntegrityViolationType:
    """誠実性違反の種類"""
    TODO_FIXME = "TODO_FIXME"
    MOCK_ABUSE = "MOCK_ABUSE"
    STUB_IMPLEMENTATION = "STUB_IMPLEMENTATION"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    GIT_INCONSISTENCY = "GIT_INCONSISTENCY"
    FALSE_CLAIM = "FALSE_CLAIM"
    PLACEHOLDER_CODE = "PLACEHOLDER_CODE"


class CodePatternAnalyzer:
    """コードパターン分析器"""
    
    def __init__(self):
        # TODO/FIXME パターン
        self.todo_patterns = [
            re.compile(r'#\s*(TODO|FIXME|HACK|XXX|BUG)\b.*', re.IGNORECASE),
            re.compile(r'//\s*(TODO|FIXME|HACK|XXX|BUG)\b.*', re.IGNORECASE),
            re.compile(r'/\*\s*(TODO|FIXME|HACK|XXX|BUG)\b.*?\*/', re.IGNORECASE | re.DOTALL),
            re.compile(r'""".*?(TODO|FIXME|HACK|XXX|BUG).*?"""', re.IGNORECASE | re.DOTALL),
        ]
        
        # スタブ実装パターン
        self.stub_patterns = [
            re.compile(r'pass\s*$', re.MULTILINE),
            re.compile(r'return\s+None\s*$', re.MULTILINE),
            re.compile(r'raise\s+NotImplementedError', re.IGNORECASE),
            re.compile(r'def\s+\w+\([^)]*\):\s*\.\.\.\s*$', re.MULTILINE),
            re.compile(r'def\s+\w+\([^)]*\):\s*return\s*$', re.MULTILINE),
        ]
        
        # プレースホルダーパターン
        self.placeholder_patterns = [
            re.compile(r'PLACEHOLDER|REPLACE_ME|CHANGE_THIS', re.IGNORECASE),
            re.compile(r'def\s+\w+\([^)]*\):\s*# TODO', re.IGNORECASE),
            re.compile(r'# This is a placeholder', re.IGNORECASE),
        ]
        
        # モック/スタブ使用パターン
        self.mock_patterns = [
            re.compile(r'from\s+unittest\.mock\s+import'),
            re.compile(r'import\s+mock'),
            re.compile(r'@mock\.patch'),
            re.compile(r'Mock\(\)'),
            re.compile(r'MagicMock\(\)'),
            re.compile(r'patch\('),
        ]

    def analyze_file(self, file_path: Path) -> Dict[str, List[Dict]]:
        """ファイルの誠実性を分析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"error": [{"message": f"Failed to read file: {e}"}]}
            
        violations = {
            "todo_fixme": [],
            "stub_impl": [],
            "placeholders": [],
            "mock_usage": []
        }
        
        lines = content.split('\n')
        
        # TODO/FIXME 検出
        for line_num, line in enumerate(lines, 1):
            for pattern in self.todo_patterns:
                if pattern.search(line):
                    violations["todo_fixme"].append({
                        "line": line_num,
                        "content": line.strip(),
                        "pattern": pattern.pattern
                    })
        
        # スタブ実装検出
        for line_num, line in enumerate(lines, 1):
            for pattern in self.stub_patterns:
                if pattern.search(line):
                    violations["stub_impl"].append({
                        "line": line_num,
                        "content": line.strip(),
                        "pattern": pattern.pattern
                    })
        
        # プレースホルダー検出
        for line_num, line in enumerate(lines, 1):
            for pattern in self.placeholder_patterns:
                if pattern.search(line):
                    violations["placeholders"].append({
                        "line": line_num,
                        "content": line.strip(),
                        "pattern": pattern.pattern
                    })
        
        # モック使用検出
        for line_num, line in enumerate(lines, 1):
            for pattern in self.mock_patterns:
                if pattern.search(line):
                    violations["mock_usage"].append({
                        "line": line_num,
                        "content": line.strip(),
                        "pattern": pattern.pattern
                    })
        
        return violations


class ASTAnalyzer:
    """AST（抽象構文木）分析器"""
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """ファイルのASTを分析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            analyzer = ASTViolationVisitor()
            analyzer.visit(tree)
            
            return {
                "functions": analyzer.functions,
                "classes": analyzer.classes,
                "not_implemented": analyzer.not_implemented,
                "empty_functions": analyzer.empty_functions,
                "suspicious_returns": analyzer.suspicious_returns
            }
            
        except SyntaxError as e:
            return {"error": f"Syntax error: {e}"}
        except Exception as e:
            return {"error": f"AST analysis failed: {e}"}


class ASTViolationVisitor(ast.NodeVisitor):
    """AST違反検出ビジター"""
    
    def __init__(self):
        self.functions = []
        self.classes = []
        self.not_implemented = []
        self.empty_functions = []
        self.suspicious_returns = []
        
    def visit_FunctionDef(self, node):
        """関数定義を訪問"""
        self.functions.append({
            "name": node.name,
            "line": node.lineno,
            "args": len(node.args.args),
            "body_length": len(node.body)
        })
        
        # 空の関数をチェック
        if len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Pass):
                self.empty_functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "type": "pass_only"
                })
            elif isinstance(stmt, ast.Raise) and isinstance(stmt.exc, ast.Call):
                if isinstance(stmt.exc.func, ast.Name) and stmt.exc.func.id == "NotImplementedError":
                    self.not_implemented.append({
                        "name": node.name,
                        "line": node.lineno
                    })
            elif isinstance(stmt, ast.Return):
                if stmt.value is None or (isinstance(stmt.value, ast.Constant) and stmt.value.value is None):
                    self.suspicious_returns.append({
                        "name": node.name,
                        "line": node.lineno,
                        "return_type": "None"
                    })
        
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        """クラス定義を訪問"""
        self.classes.append({
            "name": node.name,
            "line": node.lineno,
            "methods": len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
            "body_length": len(node.body)
        })
        
        self.generic_visit(node)


class GitConsistencyChecker:
    """Git履歴整合性チェッカー"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        
    def check_file_consistency(self, file_path: Path) -> Dict[str, Any]:
        """ファイルのGit履歴整合性をチェック"""
        try:
            # ファイルの最新コミット情報を取得
            result = subprocess.run([
                'git', 'log', '-1', '--format=%H|%an|%ae|%at|%s', 
                str(file_path)
            ], 
            cwd=self.repo_path, 
            capture_output=True, 
            text=True
            )
            
            if result.returncode != 0:
                return {"error": f"Git log failed: {result.stderr}"}
                
            if not result.stdout.strip():
                return {"warning": "No git history found for file"}
                
            commit_info = result.stdout.strip().split('|')
            
            # ファイルの変更統計を取得
            stat_result = subprocess.run([
                'git', 'log', '--numstat', '--oneline', str(file_path)
            ], 
            cwd=self.repo_path, 
            capture_output=True, 
            text=True
            )
            
            return {
                "last_commit": {
                    "hash": commit_info[0],
                    "author_name": commit_info[1],
                    "author_email": commit_info[2],
                    "timestamp": int(commit_info[3]),
                    "message": commit_info[4]
                },
                "change_stats": stat_result.stdout if stat_result.returncode == 0 else None
            }
            
        except Exception as e:
            return {"error": f"Git consistency check failed: {e}"}


class IntegrityAuditor(AncientElderBase):
    """
    🔮 誠実性監査魔法
    
    虚偽報告、モック/スタブ悪用、実装詐称を検出する
    Ancient Elder システムの最重要魔法
    """
    
    def __init__(self):
        super().__init__("IntegrityAuditor")
        
        # 分析エンジンを初期化
        self.pattern_analyzer = CodePatternAnalyzer()
        self.ast_analyzer = ASTAnalyzer()
        
        # 設定
        self.max_todo_ratio = 0.05  # 5%以上のTODO/FIXMEで警告
        self.max_mock_ratio = 0.3   # 30%以上のモック使用で警告
        self.max_stub_ratio = 0.1   # 10%以上のスタブ実装で警告
        
    async def audit(self, target: Dict[str, Any]) -> AuditResult:
        """
        誠実性監査を実行
        
        Args:
            target: 監査対象
                - type: "file", "directory", "commit", "pull_request"
                - path: ファイル/ディレクトリパス
                - files: ファイルリスト（省略可）
                
        Returns:
            AuditResult: 監査結果
        """
        result = AuditResult()
        result.auditor_name = self.name
        
        target_type = target.get("type", "directory")
        target_path = target.get("path", ".")
        
        try:
            if target_type == "file":
                await self._audit_file(Path(target_path), result)
            elif target_type == "directory":
                await self._audit_directory(Path(target_path), result)
            elif target_type == "files":
                files = target.get("files", [])
                for file_path in files:
                    await self._audit_file(Path(file_path), result)
            else:
                result.add_violation(
                    severity=ViolationSeverity.MEDIUM,
                    title="Unsupported audit target type",
                    description=f"Target type '{target_type}' is not supported",
                    metadata={"category": "integrity"}
                )
                
            # 全体的なメトリクスを計算
            self._calculate_integrity_metrics(result)
            
        except Exception as e:
            result.add_violation(
                severity=ViolationSeverity.HIGH,
                title="Integrity audit failed",
                description=f"Audit execution failed: {str(e)}",
                metadata={"category": "integrity", "error": str(e)}
            )
            
        return result
        
    async def _audit_file(self, file_path: Path, result: AuditResult):
        """単一ファイルの監査"""
        if not file_path.exists():
            result.add_violation(
                severity=ViolationSeverity.MEDIUM,
                title="File not found",
                description=f"Target file does not exist: {file_path}",
                location=str(file_path),
                metadata={"category": "integrity"}
            )
            return
            
        # Python ファイルのみを対象とする
        if file_path.suffix != '.py':
            return
            
        # パターン分析
        pattern_violations = self.pattern_analyzer.analyze_file(file_path)
        if "error" not in pattern_violations:
            self._process_pattern_violations(file_path, pattern_violations, result)
            
        # AST分析
        ast_violations = self.ast_analyzer.analyze_file(file_path)
        if "error" not in ast_violations:
            self._process_ast_violations(file_path, ast_violations, result)
            
        # Git整合性チェック（リポジトリ内の場合）
        repo_path = self._find_git_repo(file_path)
        if repo_path:
            git_checker = GitConsistencyChecker(repo_path)
            git_result = git_checker.check_file_consistency(file_path)
            self._process_git_violations(file_path, git_result, result)
            
    async def _audit_directory(self, dir_path: Path, result: AuditResult):
        """ディレクトリの再帰的監査"""
        if not dir_path.exists():
            result.add_violation(
                severity=ViolationSeverity.MEDIUM,
                title="Directory not found",
                description=f"Target directory does not exist: {dir_path}",
                location=str(dir_path),
                metadata={"category": "integrity"}
            )
            return
            
        # Python ファイルを再帰的に検索
        python_files = list(dir_path.rglob("*.py"))
        
        # 除外パターン
        exclude_patterns = [
            "*/__pycache__/*",
            "*/venv/*",
            "*/env/*",
            "*/.git/*",
            "*/node_modules/*"
        ]
        
        filtered_files = []
        for file_path in python_files:
            skip = False
            for pattern in exclude_patterns:
                if file_path.match(pattern):
                    skip = True
                    break
            if not skip:
                filtered_files.append(file_path)
                
        # 各ファイルを監査
        for file_path in filtered_files:
            await self._audit_file(file_path, result)
            
    def _process_pattern_violations(self, file_path: Path, violations: Dict, result: AuditResult):
        """パターン違反を処理"""
        # TODO/FIXME違反
        for todo in violations.get("todo_fixme", []):
            result.add_violation(
                severity=ViolationSeverity.MEDIUM,
                title="TODO/FIXME found",
                description=f"Unresolved TODO/FIXME comment: {todo['content']}",
                location=f"{file_path}:{todo['line']}",
                suggested_fix="Resolve the TODO/FIXME or remove the comment",
                metadata={
                    "category": "integrity",
                    "violation_type": IntegrityViolationType.TODO_FIXME,
                    "pattern": todo["pattern"]
                }
            )
            
        # スタブ実装違反
        for stub in violations.get("stub_impl", []):
            severity = ViolationSeverity.HIGH if "NotImplementedError" in stub["content"] else ViolationSeverity.MEDIUM
            result.add_violation(
                severity=severity,
                title="Stub implementation detected",
                description=f"Incomplete implementation found: {stub['content']}",
                location=f"{file_path}:{stub['line']}",
                suggested_fix="Provide actual implementation",
                metadata={
                    "category": "integrity",
                    "violation_type": IntegrityViolationType.STUB_IMPLEMENTATION,
                    "pattern": stub["pattern"]
                }
            )
            
        # プレースホルダー違反
        for placeholder in violations.get("placeholders", []):
            result.add_violation(
                severity=ViolationSeverity.HIGH,
                title="Placeholder code detected",
                description=f"Placeholder code found: {placeholder['content']}",
                location=f"{file_path}:{placeholder['line']}",
                suggested_fix="Replace placeholder with actual implementation",
                metadata={
                    "category": "integrity",
                    "violation_type": IntegrityViolationType.PLACEHOLDER_CODE,
                    "pattern": placeholder["pattern"]
                }
            )
            
    def _process_ast_violations(self, file_path: Path, violations: Dict, result: AuditResult):
        """AST違反を処理"""
        # NotImplementedError違反
        for not_impl in violations.get("not_implemented", []):
            result.add_violation(
                severity=ViolationSeverity.CRITICAL,
                title="NotImplementedError found",
                description=f"Function '{not_impl['name']}' raises NotImplementedError",
                location=f"{file_path}:{not_impl['line']}",
                suggested_fix="Implement the function",
                metadata={
                    "category": "integrity",
                    "violation_type": IntegrityViolationType.NOT_IMPLEMENTED,
                    "function_name": not_impl["name"]
                }
            )
            
        # 空の関数違反
        for empty in violations.get("empty_functions", []):
            result.add_violation(
                severity=ViolationSeverity.MEDIUM,
                title="Empty function detected",
                description=f"Function '{empty['name']}' has no implementation",
                location=f"{file_path}:{empty['line']}",
                suggested_fix="Provide implementation or add docstring explaining purpose",
                metadata={
                    "category": "integrity",
                    "violation_type": IntegrityViolationType.STUB_IMPLEMENTATION,
                    "function_name": empty["name"]
                }
            )
            
    def _process_git_violations(self, file_path: Path, git_result: Dict, result: AuditResult):
        """Git違反を処理"""
        if "error" in git_result:
            result.add_violation(
                severity=ViolationSeverity.LOW,
                title="Git consistency check failed",
                description=f"Unable to verify git consistency: {git_result['error']}",
                location=str(file_path),
                metadata={"category": "integrity"}
            )
            
    def _calculate_integrity_metrics(self, result: AuditResult):
        """誠実性メトリクスを計算"""
        violations_by_type = {}
        violations_by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for violation in result.violations:
            severity = violation["severity"]
            violations_by_severity[severity] += 1
            
            violation_type = violation.get("metadata", {}).get("violation_type", "UNKNOWN")
            violations_by_type[violation_type] = violations_by_type.get(violation_type, 0) + 1
            
        # 誠実性スコアを計算（100点満点）
        integrity_score = 100.0
        integrity_score -= violations_by_severity["CRITICAL"] * 25
        integrity_score -= violations_by_severity["HIGH"] * 10
        integrity_score -= violations_by_severity["MEDIUM"] * 5
        integrity_score -= violations_by_severity["LOW"] * 1
        integrity_score = max(0, integrity_score)
        
        result.add_metric("integrity_score", integrity_score)
        result.add_metric("total_violations", len(result.violations))
        result.add_metric("violations_by_severity", violations_by_severity)
        result.add_metric("violations_by_type", violations_by_type)
        result.add_metric("critical_violations", violations_by_severity["CRITICAL"])
        
    def _find_git_repo(self, file_path: Path) -> Optional[Path]:
        """ファイルのGitリポジトリルートを探す"""
        current = file_path.parent if file_path.is_file() else file_path
        
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
            
        return None
        
    def get_audit_scope(self) -> Dict[str, Any]:
        """監査範囲を返す"""
        return {
            "scope": "code_integrity",
            "targets": [
                "Python source files (.py)",
                "TODO/FIXME comments",
                "Stub implementations", 
                "Mock usage patterns",
                "Git history consistency"
            ],
            "violation_types": [
                IntegrityViolationType.TODO_FIXME,
                IntegrityViolationType.MOCK_ABUSE,
                IntegrityViolationType.STUB_IMPLEMENTATION,
                IntegrityViolationType.NOT_IMPLEMENTED,
                IntegrityViolationType.GIT_INCONSISTENCY,
                IntegrityViolationType.FALSE_CLAIM,
                IntegrityViolationType.PLACEHOLDER_CODE
            ],
            "description": "誠実性監査魔法 - 虚偽報告、モック/スタブ悪用、実装詐称を検出"
        }