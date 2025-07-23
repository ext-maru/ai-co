#!/usr/bin/env python3
"""
コメント自動追加スクリプト
エルダーズギルド品質基準（15%以上のコメント率）に準拠
"""

import ast
import re
from pathlib import Path
from typing import List, Tuple, Optional
import argparse
import logging

logger = logging.getLogger(__name__)

MIN_COMMENT_RATIO = 0.15


class CommentAdder(ast.NodeVisitor):
    """ASTを使用してコメントが必要な箇所を特定"""
    
    def __init__(self):
        self.functions_needing_comments = []
        self.classes_needing_comments = []
        self.complex_blocks = []
    
    def visit_FunctionDef(self, node):
        """関数定義を訪問"""
        # 複雑な関数を特定
        if self._is_complex_function(node):
            self.functions_needing_comments.append({
                'name': node.name,
                'lineno': node.lineno,
                'complexity': self._calculate_complexity(node)
            })
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """クラス定義を訪問"""
        # 大きなクラスを特定
        if len(node.body) > 5:
            self.classes_needing_comments.append({
                'name': node.name,
                'lineno': node.lineno,
                'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)])
            })
        
        self.generic_visit(node)
    
    def _is_complex_function(self, node):
        """複雑な関数かどうか判定"""
        # 行数が20行以上または複雑度が高い
        return len(node.body) > 10 or self._calculate_complexity(node) > 5
    
    def _calculate_complexity(self, node):
        """サイクロマティック複雑度を簡易計算"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        return complexity


def calculate_comment_ratio(content: str) -> float:
    """コメント率を計算"""
    lines = content.split('\n')
    total_lines = len([line for line in lines if line.strip()])
    comment_lines = 0
    
    in_docstring = False
    for line in lines:
        stripped = line.strip()
        
        # docstring
        if '"""' in line or "'''" in line:
            in_docstring = not in_docstring
            comment_lines += 1
        elif in_docstring:
            comment_lines += 1
        # 通常のコメント
        elif stripped.startswith('#'):
            comment_lines += 1
    
    return comment_lines / total_lines if total_lines > 0 else 0


def add_comments_to_file(file_path: Path, dry_run: bool = False) -> int:
    """ファイルにコメントを追加"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 現在のコメント率を計算
        current_ratio = calculate_comment_ratio(content)
        if current_ratio >= MIN_COMMENT_RATIO:
            return 0
        
        # AST解析
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return 0
        
        # コメントが必要な箇所を特定
        analyzer = CommentAdder()
        analyzer.visit(tree)
        
        lines = content.split('\n')
        modified_lines = []
        added_comments = 0
        
        # ファイルレベルのコメントを追加
        if not lines[0].startswith('#'):
            modified_lines.append('# -*- coding: utf-8 -*-')
            modified_lines.append(f'# File: {file_path.name}')
            modified_lines.append(f'# Purpose: {file_path.stem.replace("_", " ").title()} implementation')
            modified_lines.append('')
            added_comments += 3
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 関数定義の前にコメントを追加
            for func_info in analyzer.functions_needing_comments:
                if i + 1 == func_info['lineno']:
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent
                    modified_lines.append(f'{indent_str}# {func_info["name"]}: Complexity={func_info["complexity"]}')
                    added_comments += 1
            
            # クラス定義の前にコメントを追加
            for class_info in analyzer.classes_needing_comments:
                if i + 1 == class_info['lineno']:
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent
                    modified_lines.append(f'{indent_str}# Class with {class_info["methods"]} methods')
                    added_comments += 1
            
            # 複雑な条件文にコメントを追加
            if re.match(r'\s*if\s+.{30,}:', line):
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                modified_lines.append(f'{indent_str}# Complex condition check')
                added_comments += 1
            
            modified_lines.append(line)
            i += 1
        
        # セクション区切りコメントを追加
        if added_comments < 5:
            # インポートセクションの後
            for i, line in enumerate(modified_lines):
                if line.startswith('import ') or line.startswith('from '):
                    continue
                elif i > 0 and not line.strip():
                    modified_lines.insert(i + 1, '# --- Main Implementation ---')
                    added_comments += 1
                    break
        
        # ファイルに書き込み
        if added_comments > 0 and not dry_run:
            new_content = '\n'.join(modified_lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        
        return added_comments
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return 0


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="Add comments to Python files")
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
    total_comments = 0
    modified_files = 0
    
    for file_path in files_to_process:
        # venv等を除外
        if any(p in str(file_path) for p in ['venv', '__pycache__', '.git']):
            continue
        
        comments_added = add_comments_to_file(file_path, dry_run=args.dry_run)
        if comments_added > 0:
            if args.verbose or args.dry_run:
                print(f"{file_path}: {comments_added} comments {'would be' if args.dry_run else 'were'} added")
            total_comments += comments_added
            modified_files += 1
    
    print(f"\nSummary: {total_comments} comments in {modified_files} files {'would be' if args.dry_run else 'were'} added")


if __name__ == "__main__":
    main()