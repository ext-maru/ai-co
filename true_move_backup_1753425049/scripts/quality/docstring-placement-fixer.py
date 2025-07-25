#!/usr/bin/env python3
"""
🔧 Docstring Placement Fixer
修正コメントツールが生成した不正配置docstringを修正する専用ツール
"""

import ast
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DocstringPlacementFixer:
    """不正配置docstringの専用修正ツール"""
    
    def __init__(self):
        self.fixed_files = []
        self.error_patterns = {}
        self.backup_dir = "backups/docstring_fix"
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        
    def fix_all_docstring_placement_errors(self) -> Dict:
        """すべてのdocstring配置エラーを修正"""
        print("🔧 Docstring Placement Error Fixing - Starting...")
        
        skip_patterns = [
            '__pycache__', '.git', 'venv', '.venv', 'node_modules',
            'libs/elder_servants/integrations/continue_dev/venv_continue_dev',
            'backups'
        ]
        
        results = {
            'files_fixed': [],
            'total_fixes': 0,
            'processed_files': 0,
            'unfixable_files': []
        }
        
        # 構文エラーのあるファイルを特定
        syntax_error_files = []
        for root, dirs, files in os.walk('.'):
            # スキップディレクトリ除外
            dirs[:] = [d for d in dirs if not any(skip in os.path.join(root, d) for skip in skip_patterns)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    if any(skip in file_path for skip in skip_patterns):
                        continue
                    
                    if self._has_syntax_error(file_path):
                        syntax_error_files.append(file_path)
        
        print(f"Found {len(syntax_error_files)} files with syntax errors to fix")
        
        # docstring配置エラーを修正
        for file_path in syntax_error_files:
            success = self._fix_docstring_placement(file_path)
            if success:
                results['files_fixed'].append(file_path)
                results['total_fixes'] += 1
                print(f"🔧 Fixed: {file_path}")
            else:
                results['unfixable_files'].append(file_path)
                print(f"❌ Could not fix: {file_path}")
            
            results['processed_files'] += 1
        
        return results
    
    def _has_syntax_error(self, file_path: str) -> bool:
        """構文エラーがあるかチェック"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            return False
        except SyntaxError:
            return True
        except Exception:
            return False
    
    def _fix_docstring_placement(self, file_path: str) -> bool:
        """docstring配置エラーを修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # バックアップ作成
            backup_path = os.path.join(self.backup_dir, os.path.basename(file_path) + '.backup')
            shutil.copy2(file_path, backup_path)
            
            # docstring配置を修正
            fixed_content = self._fix_docstring_content(content)
            
            if fixed_content != content:
                # 修正後の構文をチェック
                try:
                    ast.parse(fixed_content)
                    # 構文が正しければファイルを更新
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    return True
                except SyntaxError:
                    # まだエラーがある場合は元に戻す
                    shutil.copy2(backup_path, file_path)
                    return False
            else:
                return False
                
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False
    
    def _fix_docstring_content(self, content: str) -> str:
        """docstring配置の修正を適用"""
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            fixed_lines.append(line)
            
            # 関数・クラス定義の次にdocstringがある場合をチェック
            if self._is_function_or_class_def(line):
                # 次の行をチェック
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    
                    # docstringが関数定義の直後にある場合（不正配置）
                    if self._is_misplaced_docstring(next_line):
                        # その次の行が正しいdocstringかチェック
                        if i + 2 < len(lines):
                            next_next_line = lines[i + 2]
                            
                            # 両方がdocstringの場合、最初を削除し、2つ目をインデント調整
                            if self._is_docstring(next_next_line):
                                # 不正配置のdocstringをスキップ
                                i += 1
                                # 次の正しい位置のdocstringを処理
                                i += 1
                                docstring_line = lines[i]
                                # インデントを調整
                                fixed_docstring = self._fix_docstring_indent(docstring_line, line)
                                fixed_lines.append(fixed_docstring)
                            else:
                                # 不正配置のdocstringをインデントして正しい位置に移動
                                i += 1
                                docstring_line = lines[i]
                                fixed_docstring = self._fix_docstring_indent(docstring_line, line)
                                fixed_lines.append(fixed_docstring)
            
            i += 1
        
        return '\n'.join(fixed_lines)
    
    def _is_function_or_class_def(self, line: str) -> bool:
        """関数またはクラス定義かチェック"""
        stripped = line.strip()
        return (stripped.startswith('def ') or 
                stripped.startswith('class ') or
                stripped.startswith('async def '))
    
    def _is_misplaced_docstring(self, line: str) -> bool:
        """不正配置のdocstringかチェック（インデントなし）"""
        stripped = line.strip()
        return (stripped.startswith('"""') and 
                not line.startswith('    ') and
                not line.startswith('\t'))
    
    def _is_docstring(self, line: str) -> bool:
        """docstringかチェック"""
        stripped = line.strip()
        return stripped.startswith('"""') and stripped.endswith('"""')
    
    def _fix_docstring_indent(self, docstring_line: str, def_line: str) -> str:
        """docstringのインデントを修正"""
        # 定義行のインデントを取得
        def_indent = ""
        for char in def_line:
            if char in (' ', '\t'):
                def_indent += char
            else:
                break
        
        # docstringに追加インデントを付与
        additional_indent = "    "  # 4スペース
        correct_indent = def_indent + additional_indent
        
        # 既存のインデントを削除して正しいインデントを付与
        stripped_docstring = docstring_line.lstrip()
        return correct_indent + stripped_docstring
    
    def _extract_line_number_from_error(self, error: str) -> Optional[int]:
        """エラーメッセージから行番号を抽出"""
        match = re.search(r'line (\d+)', error)
        if match:
            return int(match.group(1))
        return None


def main():
    """メインエントリーポイント"""
    fixer = DocstringPlacementFixer()
    
    print("🔧🔧🔧 DOCSTRING PLACEMENT ERROR FIXING 🔧🔧🔧")
    print("不正配置docstringを修正します...")
    
    results = fixer.fix_all_docstring_placement_errors()
    
    print(f"\n📊 Docstring Fix Results:")
    print(f"Files processed: {results['processed_files']}")
    print(f"Files fixed: {len(results['files_fixed'])}")
    print(f"Unfixable files: {len(results['unfixable_files'])}")
    
    if results['files_fixed']:
        print(f"\n✅ Successfully fixed files:")
        for i, file_path in enumerate(results['files_fixed'][:10]):
            print(f"{i+1:2d}. {file_path}")
    
    if results['unfixable_files']:
        print(f"\n❌ Could not fix these files:")
        for i, file_path in enumerate(results['unfixable_files'][:10]):
            print(f"{i+1:2d}. {file_path}")
    
    return results


if __name__ == "__main__":
    main()