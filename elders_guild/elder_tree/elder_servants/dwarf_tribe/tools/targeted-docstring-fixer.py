#!/usr/bin/env python3
"""
🎯 Targeted Docstring Fixer
特定パターンの不正配置docstringを検出・修正する専用ツール
"""

import ast
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class TargetedDocstringFixer:
    """特定パターンの不正配置docstring修正ツール"""
    
    def __init__(self):
        self.fixed_files = []
        self.backup_dir = "backups/targeted_docstring_fix"
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        
    def fix_all_targeted_docstring_errors(self) -> Dict:
        """特定パターンのdocstring配置エラーを修正"""
        print("🎯 Targeted Docstring Error Fixing - Starting...")
        
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
        
        print(f"Found {len(syntax_error_files)} files with syntax errors")
        
        # 特定パターンのdocstring配置エラーを修正
        for file_path in syntax_error_files:
            success = self._fix_targeted_docstring_pattern(file_path)
            if success:
                results['files_fixed'].append(file_path)
                results['total_fixes'] += 1
                print(f"🔧 Fixed: {file_path}")
            else:
                results['unfixable_files'].append(file_path)
            
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
    
    def _fix_targeted_docstring_pattern(self, file_path: str) -> bool:
        """特定パターンのdocstring配置エラーを修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # バックアップ作成
            backup_path = os.path.join(self.backup_dir, os.path.basename(file_path) + '.backup')
            shutil.copy2(file_path, backup_path)
            
            # 特定パターンを修正
            fixed_content = self._apply_targeted_fix(content)
            
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
    
    def _apply_targeted_fix(self, content: str) -> str:
        """特定パターンの修正を適用"""
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # パターン検出: 
            # def function_name():
            # """不正配置docstring"""
            #     """正しい位置のdocstring"""
            
            if self._is_function_def_line(line):
                fixed_lines.append(line)
                
                # 次の行をチェック
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    
                    # 不正配置docstring検出（インデントなし）
                    if self._is_misplaced_docstring(next_line):
                        # その次の行をチェック
                        if i + 2 < len(lines):
                            next_next_line = lines[i + 2]
                            
                            # 正しい位置のdocstringがある場合
                            if self._is_properly_indented_docstring(next_next_line, line):
                                # 不正配置docstringをスキップして、正しいものを残す
                                i += 2  # 不正配置をスキップ
                                fixed_lines.append(next_next_line)  # 正しいものを追加
                            else:
                                # 不正配置docstringを正しい位置に移動
                                i += 1
                                corrected_docstring = self._fix_docstring_indentation(next_line, line)
                                fixed_lines.append(corrected_docstring)
                        else:
                            # 不正配置docstringを正しい位置に移動
                            i += 1
                            corrected_docstring = self._fix_docstring_indentation(next_line, line)
                            fixed_lines.append(corrected_docstring)
                    else:
                        fixed_lines.append(line)
            else:
                fixed_lines.append(line)
            
            i += 1
        
        return '\n'.join(fixed_lines)
    
    def _is_function_def_line(self, line: str) -> bool:
        """関数定義行かチェック"""
        stripped = line.strip()
        return (stripped.startswith('def ') and 
                stripped.endswith(':'))
    
    def _is_misplaced_docstring(self, line: str) -> bool:
        """不正配置docstringかチェック（インデントなし）"""
        stripped = line.strip()
        # インデントがない（またはわずか）かつdocstringパターン
        return (stripped.startswith('"""') and 
                len(line) - len(line.lstrip()) < 4)  # インデントが4文字未満
    
    def _is_properly_indented_docstring(self, line: str, function_def_line: str) -> bool:
        """適切にインデントされたdocstringかチェック"""
        if not line.strip().startswith('"""'):
            return False
        
        # 関数定義のインデントレベルを取得
        func_indent = len(function_def_line) - len(function_def_line.lstrip())
        expected_indent = func_indent + 4
        
        line_indent = len(line) - len(line.lstrip())
        return line_indent >= expected_indent
    
    def _fix_docstring_indentation(self, docstring_line: str, function_def_line: str) -> str:
        """docstringのインデントを修正"""
        # 関数定義のインデントを取得
        func_indent_chars = ""
        for char in function_def_line:
            if char in (' ', '\t'):
                func_indent_chars += char
            else:
                break
        
        # 正しいインデント（関数インデント + 4スペース）
        correct_indent = func_indent_chars + "    "
        
        # docstringの内容を取得（既存インデント削除）
        docstring_content = docstring_line.lstrip()
        
        return correct_indent + docstring_content


def main():
    """メインエントリーポイント"""
    fixer = TargetedDocstringFixer()
    
    print("🎯🎯🎯 TARGETED DOCSTRING ERROR FIXING 🎯🎯🎯")
    print("特定パターンの不正配置docstringを修正します...")
    
    results = fixer.fix_all_targeted_docstring_errors()
    
    print(f"\n📊 Targeted Fix Results:")
    print(f"Files processed: {results['processed_files']}")
    print(f"Files fixed: {len(results['files_fixed'])}")
    print(f"Unfixable files: {len(results['unfixable_files'])}")
    
    if results['files_fixed']:
        print(f"\n✅ Successfully fixed files (first 10):")
        for i, file_path in enumerate(results['files_fixed'][:10]):
            print(f"{i+1:2d}. {file_path}")
            
        if len(results['files_fixed']) > 10:
            print(f"... and {len(results['files_fixed']) - 10} more files")
    
    if results['unfixable_files']:
        print(f"\n❌ Could not fix these files (first 5):")
        for i, file_path in enumerate(results['unfixable_files'][:5]):
            print(f"{i+1:2d}. {file_path}")
    
    return results


if __name__ == "__main__":
    main()