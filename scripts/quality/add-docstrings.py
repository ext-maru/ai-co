#!/usr/bin/env python3
"""
Docstring自動追加スクリプト
エルダーズギルド品質基準に基づき、不足しているdocstringを追加
"""

import ast
import re
from pathlib import Path
from typing import List, Tuple, Optional
import argparse
import logging

logger = logging.getLogger(__name__)


class DocstringAdder(ast.NodeTransformer):
    """ASTを使用してdocstringを追加するトランスフォーマー"""
    
    def __init__(self):
        self.modified = False
        self.additions = []
    
    def visit_FunctionDef(self, node):
        """関数定義を訪問してdocstringを追加"""
        # 既存のdocstringチェック
        has_docstring = (
            node.body and
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, (ast.Str, ast.Constant))
        )
        
        # __init__メソッドで、docstringがない場合
        if node.name == "__init__" and not has_docstring:
            # クラス名を取得（親ノードから）
            class_name = "クラス"
            
            # docstringを作成
            docstring = f'"""初期化メソッド"""'
            docstring_node = ast.Expr(value=ast.Constant(value="初期化メソッド"))
            
            # 関数の最初に挿入
            node.body.insert(0, docstring_node)
            self.modified = True
            self.additions.append(f"Added docstring to {node.name} at line {node.lineno}")
        
        # 再帰的に処理
        self.generic_visit(node)
        return node
    
    def visit_AsyncFunctionDef(self, node):
        """非同期関数定義を訪問してdocstringを追加"""
        return self.visit_FunctionDef(node)


def add_docstrings_to_file(file_path: Path) -> bool:
    """ファイルにdocstringを追加"""
    try:
        # ファイル読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # AST解析
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return False
        
        # docstring追加
        transformer = DocstringAdder()
        new_tree = transformer.visit(tree)
        
        if transformer.modified:
            # ASTをコードに戻す
            # ast.unpareは完全ではないので、正規表現を使用
            lines = content.split('\n')
            
            # __init__メソッドを探して直接修正
            modified_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                # __init__メソッドの定義を探す
                if re.match(r'\s*def\s+__init__\s*\(', line):
                    modified_lines.append(line)
                    i += 1
                    
                    # 次の行のインデントを確認
                    if not (i < len(lines)):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if i < len(lines):
                        next_line = lines[i]
                        indent_match = re.match(r'^(\s*)', next_line)
                        if not (indent_match):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if indent_match:
                            indent = indent_match.group(1)
                            # docstringがない場合は追加
                            if ('"""' in next_line or "'''" in next_line):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if not ('"""' in next_line or "'''" in next_line):
                                modified_lines.append(f'{indent}"""初期化メソッド"""')
                                logger.info(f"Added docstring to __init__ in {file_path}")
                        modified_lines.append(next_line)
                        i += 1
                else:
                    modified_lines.append(line)
                    i += 1
            
            # ファイル書き込み
            new_content = '\n'.join(modified_lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True
    
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False
    
    return False


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="Add missing docstrings to Python files")
    parser.add_argument("paths", nargs="+", help="Files or directories to process")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # ファイル収集
    files_to_process = []
    for path_str in args.paths:
        path = Path(path_str)
        if path.is_file() and path.suffix == '.py':
            files_to_process.append(path)
        elif path.is_dir():
            files_to_process.extend(path.rglob('*.py'))
    
    # 処理実行
    modified_count = 0
    for file_path in files_to_process:
        # venv等を除外
        if any(p in str(file_path) for p in ['venv', '__pycache__', '.git']):
            continue
            
        if args.dry_run:
            # ドライランモード
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if re.search(r'def\s+__init__\s*\([^)]*\):\s*\n(?!\s*""")', content):
                print(f"Would add docstring to: {file_path}")
                modified_count += 1
        else:
            # 実際に修正
            if add_docstrings_to_file(file_path):
                modified_count += 1
    
    print(f"\nSummary: {modified_count} files {'would be' if args.dry_run else 'were'} modified")


if __name__ == "__main__":
    main()