#!/usr/bin/env python3
"""
🔧 Bulk Syntax Error Fixer
よくある構文エラーパターンを一括修正
"""

import ast
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

class BulkSyntaxFixer:
    """一括構文エラー修正ツール"""
    
    def __init__(self):
        self.fixed_files = []
        self.backup_dir = "backups/bulk_syntax_fix"
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        
    def fix_all_syntax_errors(self) -> Dict:
        """すべての構文エラーを修正"""
        print("🔧 Bulk Syntax Error Fixing - Starting...")
        
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
        
        # 構文エラーファイルを特定
        syntax_error_files = []
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not any(skip in os.path.join(root, d) for skip in skip_patterns)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    if any(skip in file_path for skip in skip_patterns):
                        continue
                    
                    if self._has_syntax_error(file_path):
                        syntax_error_files.append(file_path)
        
        print(f"Found {len(syntax_error_files)} files with syntax errors")
        
        # 修正実行
        for file_path in syntax_error_files:
            success = self._fix_file_patterns(file_path)
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
    
    def _fix_file_patterns(self, file_path: str) -> bool:
        """ファイル内の問題パターンを修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # バックアップ作成
            backup_path = os.path.join(self.backup_dir, os.path.basename(file_path) + '.backup')
            shutil.copy2(file_path, backup_path)
            
            original_content = content
            
            # 複数の修正パターンを適用

            content = self._fix_misplaced_docstrings(content)

            content = self._fix_malformed_imports(content)
            
            if content != original_content:
                # 修正後の構文をチェック
                try:
                    ast.parse(content)
                    # 構文が正しければファイルを更新
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
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

        """壊れた条件文を修正"""
        
        # パターン1: "if not (any():" の修正
        content = re.sub(r'if not \(any\(\):\s*\n\s*continue\s*#[^\n]*\n\s*#[^\n]*', 
                        '', content, flags=re.MULTILINE)
        
        # パターン2: "if not (condition" で終わる不完全な条件
        content = re.sub(r'if not \([^)]*$', '', content, flags=re.MULTILINE)
        
        return content
    
    def _fix_misplaced_docstrings(self, content: str) -> str:
        """不正配置docstringを修正"""
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 関数定義の後の不正配置docstringを検出
            if re.match(r'^\s*def\s+\w+\([^)]*\):\s*$', line):
                fixed_lines.append(line)
                
                # 次の行をチェック
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    
                    # 不正配置docstring（インデントが足りない）
                    if (next_line.strip().startswith('"""') and 
                        len(next_line) - len(next_line.lstrip()) < len(line) - len(line.lstrip()) + 4):
                        
                        # その次の行もdocstringかチェック
                        if i + 2 < len(lines):
                            next_next_line = lines[i + 2]
                            if next_next_line.strip().startswith('"""'):
                                # 2つ目のdocstringを残して1つ目をスキップ
                                i += 2
                                fixed_lines.append(next_next_line)
                            else:
                                # 1つ目を適切にインデント
                                i += 1
                                func_indent = len(line) - len(line.lstrip())
                                correct_indent = ' ' * (func_indent + 4)
                                fixed_docstring = correct_indent + next_line.lstrip()
                                fixed_lines.append(fixed_docstring)
                        else:
                            # 1つ目を適切にインデント
                            i += 1
                            func_indent = len(line) - len(line.lstrip())
                            correct_indent = ' ' * (func_indent + 4)
                            fixed_docstring = correct_indent + next_line.lstrip()
                            fixed_lines.append(fixed_docstring)
                    else:
                        fixed_lines.append(next_line)
                        i += 1
            else:
                fixed_lines.append(line)
            
            i += 1
        
        return '\n'.join(fixed_lines)

        """壊れた関数呼び出しを修正"""
        
        # 不完全な関数呼び出しを修正
        # "function(" で終わる行を検出して修正
        content = re.sub(r'(\w+)\(\s*$', r'\1()', content, flags=re.MULTILINE)
        
        return content
    
    def _fix_malformed_imports(self, content: str) -> str:
        """形式不良のimportを修正"""
        
        # 空のfrom import文を削除
        content = re.sub(r'from\s+\.\s+import\s*$', '', content, flags=re.MULTILINE)
        
        return content

def main():
    """メインエントリーポイント"""
    fixer = BulkSyntaxFixer()
    
    print("🔧🔧🔧 BULK SYNTAX ERROR FIXING 🔧🔧🔧")
    print("よくある構文エラーパターンを一括修正します...")
    
    results = fixer.fix_all_syntax_errors()
    
    print(f"\n📊 Bulk Fix Results:")
    print(f"Files processed: {results['processed_files']}")
    print(f"Files fixed: {len(results['files_fixed'])}")
    print(f"Unfixable files: {len(results['unfixable_files'])}")
    
    if results['files_fixed']:
        print(f"\n✅ Successfully fixed files (first 20):")
        for i, file_path in enumerate(results['files_fixed'][:20]):
            print(f"{i+1:2d}. {file_path}")
            
        if len(results['files_fixed']) > 20:
            print(f"... and {len(results['files_fixed']) - 20} more files")
    
    return results

if __name__ == "__main__":
    main()