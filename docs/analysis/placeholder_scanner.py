#!/usr/bin/env python3
"""
包括的プレースホルダー・モック・未実装コード検査ツール
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

class PlaceholderScanner:
    """プレースホルダーとモック実装のスキャナー"""
    
    def __init__(self):
        self.results = {
            'placeholder_keywords': [],
            'todo_markers': [],
            'mock_implementations': [],
            'unimplemented_functions': [],
            'pass_only_functions': [],
            'empty_classes': [],
            'not_implemented_errors': []
        }
    
    def scan_file(self, filepath: Path) -> Dict[str, List[str]]:
        """単一ファイルをスキャン"""
        if not filepath.suffix == '.py':
            return {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_results = {}
            
            # 1. キーワード検索
            file_results['placeholder_keywords'] = self._find_placeholder_keywords(
                content,
                filepath
            )
            file_results['todo_markers'] = self._find_todo_markers(content, filepath)
            file_results['mock_implementations'] = self._find_mock_implementations(
                content,
                filepath
            )
            
            # 2. AST分析
            try:
                tree = ast.parse(content)
                file_results['unimplemented_functions'] = self._find_unimplemented_functions(
                    tree,
                    filepath
                )
                file_results['pass_only_functions'] = self._find_pass_only_functions(tree, filepath)
                file_results['empty_classes'] = self._find_empty_classes(tree, filepath)
                file_results['not_implemented_errors'] = self._find_not_implemented_errors(
                    tree,
                    filepath
                )
            except SyntaxError as e:
                file_results['syntax_errors'] = [f"{filepath}:{e.lineno}: Syntax error: {e.msg}"]
            
            return file_results
            
        except Exception as e:
            return {'errors': [f"{filepath}: Error reading file: {str(e)}"]}
    
    def _find_placeholder_keywords(self, content: str, filepath: Path) -> List[str]:
        """プレースホルダーキーワードを検索"""
        keywords = ['placeholder', 'PLACEHOLDER', 'Placeholder']
        found = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for keyword in keywords:
                if keyword in line and not line.strip().startswith('#'):
                    found.append(f"{filepath}:{i}: {line.strip()}")
        
        return found
    
    def _find_todo_markers(self, content: str, filepath: Path) -> List[str]:
        """TODO/FIXME/XXXマーカーを検索"""
        markers = ['TODO', 'FIXME', 'XXX', 'HACK', 'BUG']
        found = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for marker in markers:
        # 繰り返し処理
                if marker in line:
                    found.append(f"{filepath}:{i}: {line.strip()}")
        
        return found
    
    def _find_mock_implementations(self, content: str, filepath: Path) -> List[str]:
        """テスト外でのモック実装を検索"""
        if 'test' in str(filepath).lower():
            return []  # テストファイルはスキップ
        
        mock_patterns = [
            r'\bmock\b', r'\bMock\b', r'\bdummy\b', r'\bfake\b', r'\bstub\b'
        ]
        found = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
        # 繰り返し処理
            for pattern in mock_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    found.append(f"{filepath}:{i}: {line.strip()}")
        
        return found
    
    def _find_unimplemented_functions(self, tree: ast.AST, filepath: Path) -> List[str]:
        """未実装関数を検索"""
        found = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if len(node.body) == 1:
                    body_node = node.body[0]
                    if isinstance(body_node, ast.Raise) and isinstance(body_node.exc, ast.Call):
                        if not ((isinstance(body_node.exc.func, ast.Name) and):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if (isinstance(body_node.exc.func, ast.Name) and 
                            body_node.exc.func.id == 'NotImplementedError'):
                            found.append(f"{filepath}:{node.lineno}: Function '{node.name}' raises NotImplementedError")
        
        return found
    
    def _find_pass_only_functions(self, tree: ast.AST, filepath: Path) -> List[str]:
        """pass文のみの関数を検索"""
        found = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    # ただし、抽象メソッドや意図的なpass文は除外
                    if not self._is_intentional_pass(node):
                        found.append(f"{filepath}:{node.lineno}: Function '{node.name}' only contains pass")
        
        return found
    
    def _find_empty_classes(self, tree: ast.AST, filepath: Path) -> List[str]:
        """空のクラスを検索"""
        found = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 実装がpassまたはdocstringのみのクラス
                non_docstring_body = []
                for body_node in node.body:
                    if not (isinstance(body_node, ast.Expr) and 
                           isinstance(body_node.value, ast.Constant) and 
                           isinstance(body_node.value.value, str)):
                        non_docstring_body.append(body_node)
                
                if len(non_docstring_body) == 1 and isinstance(non_docstring_body[0], ast.Pass):
                    found.append(f"{filepath}:{node.lineno}: Class '{node.name}' only contains pass")
        
        return found
    
    def _find_not_implemented_errors(self, tree: ast.AST, filepath: Path) -> List[str]:
        """NotImplementedError の使用を検索"""
        found = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                if (isinstance(node.exc.func, ast.Name) and 
                    node.exc.func.id == 'NotImplementedError'):
                    found.append(f"{filepath}:{node.lineno}: NotImplementedError raised")
            elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Name):
                if node.exc.id == 'NotImplementedError':
                    found.append(f"{filepath}:{node.lineno}: NotImplementedError raised")
        
        return found
    
    def _is_intentional_pass(self, node: ast.FunctionDef) -> bool:
        """意図的なpass文かどうかを判定"""
        # デコレータで抽象メソッドかどうかをチェック
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in ['abstractmethod']:
                return True
            elif isinstance(decorator, ast.Attribute) and decorator.attr in ['abstractmethod']:
                return True
        
        # docstring に実装予定の記述があるかチェック
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value.lower()
            if any(
                keyword in docstring for keyword in ['abstract',
                'override',
                'implement',
                'subclass']
            ):
                return True
        
        return False
    
    def scan_directory(
        self,
        directory: Path,
        exclude_patterns: List[str] = None
    ) -> Dict[str, List[str]]:
        """ディレクトリ全体をスキャン"""
        if exclude_patterns is None:
            exclude_patterns = ['*env*', '*venv*', '__pycache__', '*.pyc']
        
        all_results = {
            'placeholder_keywords': [],
            'todo_markers': [],
            'mock_implementations': [],
            'unimplemented_functions': [],
            'pass_only_functions': [],
            'empty_classes': [],
            'not_implemented_errors': [],
            'syntax_errors': [],
            'errors': []
        }
        
        for filepath in directory.rglob('*.py'):
            # 除外パターンをチェック
            if any(pattern in str(filepath) for pattern in exclude_patterns):
                continue
            
            file_results = self.scan_file(filepath)
            
            # 結果をマージ
            for category, items in file_results.items():
                if category in all_results:
                    all_results[category].extend(items)
                else:
                    all_results[category] = items
        
        return all_results
    
    def print_report(self, results: Dict[str, List[str]]):
        """レポートを出力"""
        print("=" * 80)
        print("プレースホルダー・モック・未実装コード検査レポート")
        print("=" * 80)
        
        categories = [
            ('プレースホルダーキーワード', 'placeholder_keywords'),
            ('TODO/FIXME/XXXマーカー', 'todo_markers'),
            ('モック実装（テスト外）', 'mock_implementations'),
            ('未実装関数 (NotImplementedError)', 'unimplemented_functions'),
            ('pass文のみの関数', 'pass_only_functions'),
            ('空のクラス', 'empty_classes'),
            ('NotImplementedError使用箇所', 'not_implemented_errors'),
            ('構文エラー', 'syntax_errors'),
            ('その他のエラー', 'errors')
        ]
        
        total_issues = 0
        
        # 繰り返し処理
        for category_name, category_key in categories:
            items = results.get(category_key, [])
            if items:
                print(f"\n【{category_name}】({len(items)}件)")
                print("-" * 40)
                for item in items[:20]:  # 最大20件まで表示
                    print(f"  {item}")
                if len(items) > 20:
                    print(f"  ... and {len(items) - 20} more")
                total_issues += len(items)
        
        print(f"\n{'='*80}")
        print(f"総検出件数: {total_issues}")
        
        if total_issues == 0:
            print("✅ プレースホルダーやモック実装は検出されませんでした！")
        else:
            print(f"⚠️  {total_issues}件の潜在的な問題が検出されました。")
        
        print("=" * 80)


def main():
    """メイン関数"""
    libs_dir = Path("/home/aicompany/ai_co/libs")
    workers_dir = Path("/home/aicompany/ai_co/workers")
    scripts_dir = Path("/home/aicompany/ai_co/scripts")
    
    scanner = PlaceholderScanner()
    
    print("🔍 包括的プレースホルダー・モック・未実装コード検査を開始...")
    
    # 各ディレクトリをスキャン
    for directory_name, directory_path in [("libs", libs_dir), ("workers", workers_dir), ("scripts", scripts_dir)]:
        if directory_path.exists():
            print(f"\n📁 {directory_name}/ ディレクトリをスキャン中...")
            results = scanner.scan_directory(directory_path)
            
            # 結果を表示
            print(f"\n📊 {directory_name}/ ディレクトリの検査結果:")
            scanner.print_report(results)
        else:
            print(f"⚠️  {directory_name}/ ディレクトリが見つかりません: {directory_path}")


if __name__ == "__main__":
    main()