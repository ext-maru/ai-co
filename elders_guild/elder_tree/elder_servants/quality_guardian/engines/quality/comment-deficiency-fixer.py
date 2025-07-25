#!/usr/bin/env python3
"""
🔧 Comment Deficiency Fixer
コメント不足を自動修正するツール
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class CommentDeficiencyFixer:
    """コメント不足修正ツール"""
    
    def __init__(self):
        self.fixed_count = 0
        self.processed_files = 0
        
    def fix_all_deficiencies(self) -> Dict:
        """プロジェクト全体のコメント不足を修正"""
        print("🔧 Starting comment deficiency fixing...")
        
        skip_patterns = [
            '__pycache__', '.git', 'venv', '.venv', 'node_modules',
            'libs/elder_servants/integrations/continue_dev/venv_continue_dev'
        ]
        
        results = {
            'files_fixed': [],
            'total_fixes': 0,
            'processed_files': 0
        }
        
        for root, dirs, files in os.walk('.'):
            # スキップディレクトリ除外
            dirs[:] = [d for d in dirs if not any(skip in os.path.join(root, d) for skip in skip_patterns)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    if any(skip in file_path for skip in skip_patterns):
                        continue
                    
                    fixes = self._fix_file(file_path)
                    if fixes > 0:
                        results['files_fixed'].append({
                            'file': file_path,
                            'fixes': fixes
                        })
                        results['total_fixes'] += fixes
                        print(f"🔧 {file_path}: Fixed {fixes} comment deficiencies")
                    
                    results['processed_files'] += 1
        
        return results
    
    def _fix_file(self, file_path: str) -> int:
        """ファイルのコメント不足を修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # AST解析
            try:
                tree = ast.parse(content)
            except SyntaxError:
                # 構文エラーがある場合はスキップ
                return 0
            
            lines = content.split('\n')
            original_line_count = len(lines)
            
            # 修正を適用
            lines, fixes = self._apply_fixes(tree, lines, file_path)
            
            if fixes > 0:
                # ファイル更新
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
            
            return fixes
            
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return 0
    
    def _apply_fixes(self, tree: ast.AST, lines: List[str], file_path: str) -> Tuple[List[str], int]:
        """修正を適用"""
        fixes = 0
        new_lines = lines.copy()
        offset = 0  # 行追加によるオフセット
        
        # 修正対象を収集
        fixes_to_apply = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fix = self._generate_function_fix(node, lines, file_path)
                if fix:
                    fixes_to_apply.append(fix)
            
            elif isinstance(node, ast.ClassDef):
                fix = self._generate_class_fix(node, lines, file_path)
                if fix:
                    fixes_to_apply.append(fix)
        
        # 複雑なロジックの修正
        fixes_to_apply.extend(self._generate_complex_logic_fixes(tree, lines, file_path))
        
        # 行番号順にソート（逆順で適用）
        fixes_to_apply.sort(key=lambda x: x['line'], reverse=True)
        
        # 修正を適用
        for fix in fixes_to_apply:
            line_no = fix['line'] + offset
            comment = fix['comment']
            indent = fix['indent']
            
            if fix['type'] == 'function_docstring':
                # 関数の最初に docstring を挿入
                insert_line = line_no  # 関数定義の次の行
                new_lines.insert(insert_line, f'{indent}    """{comment}"""')
                offset += 1
                fixes += 1
            
            elif fix['type'] == 'class_docstring':
                # クラスの最初に docstring を挿入
                insert_line = line_no  # クラス定義の次の行
                new_lines.insert(insert_line, f'{indent}    """{comment}"""')
                offset += 1
                fixes += 1
            
            elif fix['type'] == 'inline_comment':
                # インラインコメントを挿入
                insert_line = line_no - 1  # 対象行の前
                new_lines.insert(insert_line, f'{indent}# {comment}')
                offset += 1
                fixes += 1
        
        return new_lines, fixes
    
    def _generate_function_fix(self, node: ast.FunctionDef, lines: List[str], file_path: str) -> Optional[Dict]:
        """関数のコメント修正を生成"""
        func_name = node.name
        line_no = node.lineno
        
        # 特殊関数は除外
        if func_name.startswith('__') and func_name.endswith('__'):
            return None
        
        # docstringチェック
        has_docstring = (
            node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)
        )
        
        if not has_docstring:
            # 短い関数（3行以下）は除外
            func_end_line = self._get_function_end_line(node, lines)
            if func_end_line - line_no <= 3:
                return None
            
            # インデントを取得
            indent = self._get_line_indent(lines[line_no - 1])
            
            # docstringを生成
            docstring = self._generate_function_docstring(node, file_path)
            
            return {
                'type': 'function_docstring',
                'line': line_no,
                'comment': docstring,
                'indent': indent
            }
        
        return None
    
    def _generate_class_fix(self, node: ast.ClassDef, lines: List[str], file_path: str) -> Optional[Dict]:
        """クラスのコメント修正を生成"""
        class_name = node.name
        line_no = node.lineno
        
        # docstringチェック
        has_docstring = (
            node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)
        )
        
        if not has_docstring:
            # インデントを取得
            indent = self._get_line_indent(lines[line_no - 1])
            
            # docstringを生成
            docstring = self._generate_class_docstring(node, file_path)
            
            return {
                'type': 'class_docstring',
                'line': line_no,
                'comment': docstring,
                'indent': indent
            }
        
        return None
    
    def _generate_complex_logic_fixes(self, tree: ast.AST, lines: List[str], file_path: str) -> List[Dict]:
        """複雑なロジックのコメント修正を生成"""
        fixes = []
        
        for node in ast.walk(tree):
            # 複雑な条件文
            if isinstance(node, ast.If) and self._is_complex_condition(node.test):
                line_no = node.lineno
                if not self._has_nearby_comment(lines, line_no):
                    indent = self._get_line_indent(lines[line_no - 1])
                    comment = self._generate_condition_comment(node.test)
                    
                    fixes.append({
                        'type': 'inline_comment',
                        'line': line_no,
                        'comment': comment,
                        'indent': indent
                    })
            
            # 複雑なループ
            elif isinstance(node, (ast.For, ast.While)) and self._is_complex_loop(node):
                line_no = node.lineno
                if not self._has_nearby_comment(lines, line_no):
                    indent = self._get_line_indent(lines[line_no - 1])
                    comment = self._generate_loop_comment(node)
                    
                    fixes.append({
                        'type': 'inline_comment',
                        'line': line_no,
                        'comment': comment,
                        'indent': indent
                    })
        
        return fixes
    
    def _generate_function_docstring(self, node: ast.FunctionDef, file_path: str) -> str:
        """関数用docstringを生成"""
        func_name = node.name
        
        # 名前から目的を推測
        if 'init' in func_name.lower():
            return "初期化メソッド"
        elif 'get' in func_name.lower():
            return f"{func_name}の値を取得"
        elif 'set' in func_name.lower():
            return f"{func_name}の値を設定"
        elif 'create' in func_name.lower():
            return f"{func_name}を作成"
        elif 'delete' in func_name.lower():
            return f"{func_name}を削除"
        elif 'update' in func_name.lower():
            return f"{func_name}を更新"
        elif 'process' in func_name.lower():
            return f"{func_name}を処理"
        elif 'validate' in func_name.lower():
            return f"{func_name}を検証"
        elif 'handle' in func_name.lower():
            return f"{func_name}を処理"
        elif 'parse' in func_name.lower():
            return f"{func_name}を解析"
        elif 'generate' in func_name.lower():
            return f"{func_name}を生成"
        elif 'load' in func_name.lower():
            return f"{func_name}を読み込み"
        elif 'save' in func_name.lower():
            return f"{func_name}を保存"
        elif 'run' in func_name.lower() or 'execute' in func_name.lower():
            return f"{func_name}を実行"
        else:
            return f"{func_name}メソッド"
    
    def _generate_class_docstring(self, node: ast.ClassDef, file_path: str) -> str:
        """クラス用docstringを生成"""
        class_name = node.name
        
        # 名前から目的を推測
        if 'manager' in class_name.lower():
            return f"{class_name}管理クラス"
        elif 'handler' in class_name.lower():
            return f"{class_name}処理クラス"
        elif 'processor' in class_name.lower():
            return f"{class_name}処理クラス"
        elif 'generator' in class_name.lower():
            return f"{class_name}生成クラス"
        elif 'parser' in class_name.lower():
            return f"{class_name}解析クラス"
        elif 'validator' in class_name.lower():
            return f"{class_name}検証クラス"
        elif 'config' in class_name.lower():
            return f"{class_name}設定クラス"
        elif 'client' in class_name.lower():
            return f"{class_name}クライアントクラス"
        elif 'server' in class_name.lower():
            return f"{class_name}サーバークラス"
        elif 'worker' in class_name.lower():
            return f"{class_name}ワーカークラス"
        elif 'test' in class_name.lower():
            return f"{class_name}テストクラス"
        else:
            return f"{class_name}クラス"
    
    def _generate_condition_comment(self, node: ast.expr) -> str:
        """条件文のコメントを生成"""
        return "複雑な条件判定"
    
    def _generate_loop_comment(self, node) -> str:
        """ループのコメントを生成"""
        if isinstance(node, ast.For):
            return "繰り返し処理"
        else:
            return "ループ処理"
    
    def _get_function_end_line(self, node: ast.FunctionDef, lines: List[str]) -> int:
        """関数の終了行を取得"""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno
        
        # fallback: 次の関数の開始行を探す
        start_line = node.lineno
        for i in range(start_line, len(lines)):
            line = lines[i].strip()
            if line.startswith('def ') or line.startswith('class ') or (
                line and not line.startswith(' ') and not line.startswith('\t') and not line.startswith('#')
            ):
                if i != start_line - 1:
                    return i
        
        return len(lines)
    
    def _get_line_indent(self, line: str) -> str:
        """行のインデントを取得"""
        return re.match(r'^(\s*)', line).group(1)
    
    def _is_complex_condition(self, node: ast.expr) -> bool:
        """条件が複雑かどうか判定"""
        if isinstance(node, ast.BoolOp):
            return len(node.values) >= 3  # 3つ以上の条件
        elif isinstance(node, ast.Compare):
            return len(node.comparators) >= 2  # 2つ以上の比較
        return False
    
    def _is_complex_loop(self, node) -> bool:
        """ループが複雑かどうか判定"""
        # ネストしたループや複雑な条件を持つループ
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)) and child != node:
                return True  # ネストループ
        return False
    
    def _has_nearby_comment(self, lines: List[str], line_no: int) -> bool:
        """近くにコメントがあるかチェック"""
        # 前後2行以内にコメントがあるかチェック
        start = max(0, line_no - 3)
        end = min(len(lines), line_no + 2)
        
        for i in range(start, end):
            if '#' in lines[i]:
                return True
        
        return False


def main():
    """メインエントリーポイント"""
    fixer = CommentDeficiencyFixer()
    
    print("🔧 Comment Deficiency Fixer Starting...")
    results = fixer.fix_all_deficiencies()
    
    print(f"\n✅ Fixing Complete!")
    print(f"Files processed: {results['processed_files']}")
    print(f"Files fixed: {len(results['files_fixed'])}")
    print(f"Total fixes applied: {results['total_fixes']}")
    
    return results


if __name__ == "__main__":
    main()