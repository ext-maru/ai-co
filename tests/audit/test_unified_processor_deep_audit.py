#!/usr/bin/env python3
"""
統一Auto Issue Processor 深層監査
実際のコード実装の詳細検証
"""

import ast
import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class CodeAnalyzer:
    """コード品質分析"""
    
    def __init__(self):
        self.issues = []
        self.base_path = Path("/home/aicompany/ai_co/libs/auto_issue_processor")
    
    def analyze_all_files(self):
        """すべてのPythonファイルを分析"""
        for py_file in self.base_path.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                self.analyze_file(py_file)
        return self.issues
    
    def analyze_file(self, file_path: Path):
        """個別ファイルの分析"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. AST解析
        try:
            tree = ast.parse(content)
            self.analyze_ast(tree, file_path)
        except SyntaxError as e:
            self.issues.append(f"❌ 構文エラー in {file_path}: {e}")
        
        # 2. セキュリティパターン検出
        self.check_security_patterns(content, file_path)
        
        # 3. コード品質チェック
        self.check_code_quality(content, file_path)
        
        # 4. エラーハンドリングチェック
        self.check_error_handling(content, file_path)
    
    def analyze_ast(self, tree: ast.AST, file_path: Path):
        """AST解析による問題検出"""
        class SecurityVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.file_path = file_path
            
            def visit_Call(self, node):
            """SecurityVisitorクラス"""
                # 危険な関数呼び出し
                if isinstance(node.func, ast.Name):
                    dangerous_funcs = ['eval', 'exec', '__import__']
                    if node.func.id in dangerous_funcs:
                """visit_Callメソッド"""
                        self.analyzer.issues.append(
                            f"❌ 危険な関数 {node.func.id} in {self.file_path}:{node.lineno}"
                        )
                
                # os.system呼び出し
                if isinstance(node.func, ast.Attribute):
                    if (isinstance(node.func.value, ast.Name) and 
                        node.func.value.id == 'os' and 
                        node.func.attr == 'system'):
                        self.analyzer.issues.append(
                            f"❌ os.system使用 in {self.file_path}:{node.lineno}"
                        )
                
                self.generic_visit(node)
            
            def visit_Import(self, node):
                # 危険なモジュールのインポート
                for alias in node.names:
                    if alias.name in ['pickle', 'marshal']:
                """visit_Importメソッド"""
                        self.analyzer.issues.append(
                            f"⚠️ 危険なモジュール {alias.name} in {self.file_path}"
                        )
                self.generic_visit(node)
        
        visitor = SecurityVisitor(self)
        visitor.visit(tree)
    
    def check_security_patterns(self, content: str, file_path: Path):
        """セキュリティパターンの検出"""
        patterns = [
            (r'token\s*=\s*["\'][^"\']+["\']', "トークンのハードコード"),
            (r'password\s*=\s*["\'][^"\']+["\']', "パスワードのハードコード"),
            (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', "shell=Trueの使用"),
            (r'\.format\s*\([^)]*\).*\bsql\b', "SQLインジェクションの可能性"),
            (r'open\s*\([^)]*\)(?!.*\bencoding\b)', "エンコーディング未指定のopen"),
        ]
        
        for pattern, description in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
        # 繰り返し処理
            for match in matches:
                line_no = content[:match.start()].count('\n') + 1
                self.issues.append(f"⚠️ {description} in {file_path}:{line_no}")
    
    def check_code_quality(self, content: str, file_path: Path):
        """コード品質チェック"""
        lines = content.split('\n')
        
        # 1. 長すぎる行
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self.issues.append(f"⚠️ 行が長すぎる({len(line)}文字) in {file_path}:{i}")
        
        # 2. TODO/FIXMEコメント
        for i, line in enumerate(lines, 1):
            if 'TODO' in line or 'FIXME' in line:
                self.issues.append(f"⚠️ 未完了タスク in {file_path}:{i}")
        
        # 3. 複雑度の高い関数（簡易チェック）
        function_lines = []
        in_function = False
        indent_level = 0
        
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('def ') or line.strip().startswith('async def '):
                in_function = True
                function_lines = [i]
                indent_level = len(line) - len(line.lstrip())
            elif in_function and line.strip() and len(line) - len(line.lstrip()) <= indent_level:
                # 関数終了
                if len(function_lines) > 50:
                    self.issues.append(
                        f"⚠️ 関数が長すぎる({len(function_lines)}行) in {file_path}:{function_lines[0]}"
                    )
                in_function = False
            elif in_function:
                function_lines.append(i)
    
    def check_error_handling(self, content: str, file_path: Path):
        """エラーハンドリングチェック"""
        # 1. 裸のexcept
        if re.search(r'except\s*:', content):
            self.issues.append(f"❌ 裸のexcept節 in {file_path}")
        
        # 2. エラーの握りつぶし
        if re.search(r'except.*:\s*\n\s*pass', content):
            self.issues.append(f"⚠️ エラーの握りつぶし in {file_path}")
        
        # 3. assertの使用（本番コードで無効化される）
        if 'assert ' in content and 'test' not in str(file_path):
            self.issues.append(f"⚠️ 本番コードでのassert使用 in {file_path}")


class DependencyAnalyzer:
    """依存関係分析"""
    
    def __init__(self):
        self.issues = []
        self.base_path = Path("/home/aicompany/ai_co/libs/auto_issue_processor")
    
    def analyze_dependencies(self):
        """依存関係の分析"""
        # 1. 循環参照チェック
        imports = self.collect_imports()
        cycles = self.find_circular_dependencies(imports)
        
        for cycle in cycles:
            self.issues.append(f"❌ 循環参照: {' -> '.join(cycle)}")
        
        # 2. 未使用インポート
        for file_path, imported_modules in imports.items():
            content = file_path.read_text()
            for module in imported_modules:
                # 簡易チェック（完全ではない）
                module_name = module.split('.')[-1]
                if module_name not in content:
                    self.issues.append(f"⚠️ 未使用インポートの可能性: {module} in {file_path}")
        
        return self.issues
    
    def collect_imports(self) -> Dict[Path, List[str]]:
        """インポート情報を収集"""
        imports = {}
        
        for py_file in self.base_path.rglob("*.py"):
        # 繰り返し処理
            if "__pycache__" not in str(py_file):
                with open(py_file, 'r') as f:
                    content = f.read()
                
                try:
                    tree = ast.parse(content)
                    file_imports = []
                    
                    # 繰り返し処理
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                file_imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                file_imports.append(node.module)
                    
                    imports[py_file] = file_imports
                except:
                    pass
        
        return imports
    
    def find_circular_dependencies(self, imports: Dict[Path, List[str]]) -> List[List[str]]:
        """循環参照を検出"""
        # 簡易実装
        cycles = []
        # TODO: 実装
        return cycles


class ConfigurationAnalyzer:
    """設定の分析"""
    
    def __init__(self):
        self.issues = []
    
    def analyze_configs(self):
        """設定ファイルの分析"""
        # 1. YAMLファイルの検証
        yaml_files = [
            "configs/auto_issue_processor.yaml",
            "configs/elder_scheduler_config.yaml"
        ]
        
        for yaml_file in yaml_files:
            if os.path.exists(yaml_file):
                self.check_yaml_security(yaml_file)
        
        # 2. 環境変数の使用状況
        self.check_env_usage()
        
        return self.issues
    
    def check_yaml_security(self, file_path: str):
        """YAML設定のセキュリティチェック"""
        with open(file_path, 'r') as f:
            content = f.read()
        
        # 危険なパターン
        if '!!' in content:  # YAMLタグ
            self.issues.append(f"❌ 危険なYAMLタグ使用 in {file_path}")
        
        if 'ghp_' in content or 'github_pat_' in content:
            self.issues.append(f"❌ トークンがハードコード in {file_path}")
    
    def check_env_usage(self):
        """環境変数の使用チェック"""
        required_env_vars = [
            "GITHUB_TOKEN",
            "GITHUB_REPOSITORY"
        ]
        
        for env_var in required_env_vars:
            if not os.getenv(env_var):
                self.issues.append(f"⚠️ 必須環境変数が未設定: {env_var}")


class ProcessLockAnalyzer:
    """プロセスロックの詳細分析"""
    
    def __init__(self):
        self.issues = []
    
    def analyze_lock_implementation(self):
        """ロック実装の分析"""
        lock_file = Path("/home/aicompany/ai_co/libs/auto_issue_processor/utils/locking.py")
        
        if not lock_file.exists():
            self.issues.append("❌ ロック実装ファイルが存在しない")
            return self.issues
        
        with open(lock_file, 'r') as f:
            content = f.read()
        
        # 1. アトミック操作の確認
        if 'rename' not in content and 'link' not in content:
            self.issues.append("⚠️ ファイルロックがアトミックでない可能性")
        
        # 2. デッドロック対策
        if 'ttl' not in content.lower() and 'timeout' not in content.lower():
            self.issues.append("❌ TTL/タイムアウトが実装されていない")
        
        # 3. クリーンアップ機能
        if 'cleanup' not in content.lower():
            self.issues.append("⚠️ 古いロックのクリーンアップ機能がない")
        
        # 4. プロセス生存確認
        if 'psutil' in content or 'kill' in content:
            # プロセス生存確認あり
            pass
        else:
            self.issues.append("⚠️ プロセス生存確認機能がない")
        
        return self.issues


def run_deep_audit():
    """深層監査の実行"""
    print("=" * 80)
    print("統一Auto Issue Processor 深層監査")
    print("=" * 80)
    print()
    
    all_issues = []
    
    # 1. コード品質分析
    print("📝 コード品質分析")
    print("-" * 40)
    code_analyzer = CodeAnalyzer()
    code_issues = code_analyzer.analyze_all_files()
    
    if code_issues:
        for issue in code_issues:
            print(f"  {issue}")
        all_issues.extend(code_issues)
    else:
        print("  ✅ コード品質問題なし")
    print()
    
    # 2. 依存関係分析
    print("🔗 依存関係分析")
    print("-" * 40)
    dep_analyzer = DependencyAnalyzer()
    dep_issues = dep_analyzer.analyze_dependencies()
    
    if dep_issues:
        for issue in dep_issues:
            print(f"  {issue}")
        all_issues.extend(dep_issues)
    else:
        print("  ✅ 依存関係問題なし")
    print()
    
    # 3. 設定分析
    print("⚙️ 設定分析")
    print("-" * 40)
    config_analyzer = ConfigurationAnalyzer()
    config_issues = config_analyzer.analyze_configs()
    
    if config_issues:
        for issue in config_issues:
            print(f"  {issue}")
        all_issues.extend(config_issues)
    else:
        print("  ✅ 設定問題なし")
    print()
    
    # 4. ロック実装分析
    print("🔒 ロック実装分析")
    print("-" * 40)
    lock_analyzer = ProcessLockAnalyzer()
    lock_issues = lock_analyzer.analyze_lock_implementation()
    
    if lock_issues:
        for issue in lock_issues:
            print(f"  {issue}")
        all_issues.extend(lock_issues)
    else:
        print("  ✅ ロック実装問題なし")
    print()
    
    # 総合結果
    print("=" * 80)
    print("深層監査結果")
    print("=" * 80)
    
    critical_count = len([i for i in all_issues if i.startswith("❌")])
    warning_count = len([i for i in all_issues if i.startswith("⚠️")])
    
    print(f"🔴 重大な問題: {critical_count}件")
    print(f"🟡 警告: {warning_count}件")
    print(f"📋 総問題数: {len(all_issues)}件")
    
    if critical_count > 0:
        print("\n❌ 深層監査失敗: 重大な問題があります")
        return False
    else:
        print("\n✅ 深層監査合格")
        return True


if __name__ == "__main__":
    success = run_deep_audit()
    sys.exit(0 if success else 1)