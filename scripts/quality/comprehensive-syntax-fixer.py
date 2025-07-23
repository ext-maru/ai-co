#!/usr/bin/env python3
"""
🚀 Comprehensive Syntax Fixer
複数の構文エラーパターンを包括的に修正
"""

import ast
import os
import re
import shutil
from pathlib import Path


class ComprehensiveSyntaxFixer:
    """包括的構文エラー修正ツール"""
    
    def __init__(self):
        self.backup_dir = "backups/comprehensive_syntax_fix"
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        
    def fix_file(self, file_path: str) -> bool:
        """ファイルの構文エラーを包括的に修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # バックアップ作成
            backup_path = os.path.join(self.backup_dir, os.path.basename(file_path) + '.backup')
            shutil.copy2(file_path, backup_path)
            
            original_content = content
            
            # 修正パターンを順次適用
            content = self._fix_misplaced_docstrings(content)
            content = self._fix_broken_conditions(content)
            content = self._fix_incomplete_statements(content)
            content = self._fix_indentation_issues(content)
            
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
            
            return False
            
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False
    
    def _fix_misplaced_docstrings(self, content: str) -> str:
        """不正配置docstringを修正"""
        
        # パターン1: def func(): \n """docstring""" \n     """correct"""
        pattern1 = re.compile(
            r'(^\s*(?:def|class)\s+\w+.*?:\s*\n)'  # function/class definition
            r'(\s*)"""[^"]*"""\s*\n'               # misplaced docstring
            r'(\s+)"""([^"]*)"""',                 # correct docstring
            re.MULTILINE | re.DOTALL
        )
        content = pattern1.sub(r'\1\3"""\4"""', content)
        
        # パターン2: def func(): \n """docstring""" (単独の不正配置)
        pattern2 = re.compile(
            r'(^\s*(?:def|class)\s+\w+.*?:\s*\n)'  # function/class definition  
            r'(\s*)"""([^"]*)"""\s*\n'             # misplaced docstring
            r'(?![\s]*""")',                       # not followed by another docstring
            re.MULTILINE | re.DOTALL
        )
        
        def fix_single_docstring(match):
            func_def = match.group(1)
            docstring_content = match.group(3)
            # 適切なインデントを計算
            func_lines = func_def.split('\n')
            func_line = func_lines[-2] if len(func_lines) > 1 else func_lines[0]
            func_indent = len(func_line) - len(func_line.lstrip())
            correct_indent = ' ' * (func_indent + 4)
            return f'{func_def}{correct_indent}"""{docstring_content}"""\n'
        
        content = pattern2.sub(fix_single_docstring, content)
        
        return content
    
    def _fix_broken_conditions(self, content: str) -> str:
        """壊れた条件文を修正"""
        
        # "if not (any():" パターンの削除
        content = re.sub(
            r'if not \(any\(\):\s*\n\s*continue[^\n]*\n\s*#[^\n]*\n',
            '',
            content,
            flags=re.MULTILINE
        )
        
        # 不完全な条件文の削除
        content = re.sub(
            r'if not \([^)]*$',
            '',
            content,
            flags=re.MULTILINE
        )
        
        return content
    
    def _fix_incomplete_statements(self, content: str) -> str:
        """不完全な文を修正"""
        
        # 不完全な関数呼び出し: "function(" -> "function()"
        content = re.sub(r'(\w+)\(\s*$', r'\1()', content, flags=re.MULTILINE)
        
        # 空のfrom import文を削除
        content = re.sub(r'from\s+\.\s+import\s*$', '', content, flags=re.MULTILINE)
        
        return content
    
    def _fix_indentation_issues(self, content: str) -> str:
        """インデントの問題を修正"""
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 関数定義後の不正なインデント
            if re.match(r'^\s*(?:def|class)\s+\w+.*?:\s*$', line):
                fixed_lines.append(line)
                
                # 次の行が適切にインデントされているかチェック
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip() and not next_line.startswith('    '):
                        # 空行でもdocstringでもない場合、passを追加
                        if not next_line.strip().startswith('"""'):
                            func_indent = len(line) - len(line.lstrip())
                            correct_indent = ' ' * (func_indent + 4)
                            fixed_lines.append(f'{correct_indent}pass')
                        
                fixed_lines.append(next_line if i + 1 < len(lines) else '')
                i += 1
            else:
                fixed_lines.append(line)
            
            i += 1
        
        return '\n'.join(fixed_lines)


def main():
    """メインエントリーポイント"""
    print("🚀 Comprehensive Syntax Fixing - Starting...")
    
    skip_patterns = [
        '__pycache__', '.git', 'venv', '.venv', 'node_modules', 'backups'
    ]
    
    fixer = ComprehensiveSyntaxFixer()
    syntax_error_files = []
    fixed_files = []
    
    # 構文エラーファイルを特定
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not any(skip in os.path.join(root, d) for skip in skip_patterns)]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                if any(skip in file_path for skip in skip_patterns):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content)
                except SyntaxError:
                    syntax_error_files.append(file_path)
                except Exception:
                    pass
    
    print(f"Found {len(syntax_error_files)} files with syntax errors")
    
    # 修正実行（バッチ処理）
    for i, file_path in enumerate(syntax_error_files):
        if fixer.fix_file(file_path):
            fixed_files.append(file_path)
            print(f"🔧 Fixed ({i+1}/{len(syntax_error_files)}): {file_path}")
        
        # 進捗表示
        if (i + 1) % 50 == 0:
            print(f"📊 Progress: {i+1}/{len(syntax_error_files)} processed, {len(fixed_files)} fixed")
    
    print(f"\n🎯 Final Results:")
    print(f"Files processed: {len(syntax_error_files)}")
    print(f"Files fixed: {len(fixed_files)}")
    print(f"Success rate: {len(fixed_files)/len(syntax_error_files)*100:.1f}%")
    
    if fixed_files:
        print(f"\n✅ Fixed files:")
        for i, file_path in enumerate(fixed_files[:20]):
            print(f"{i+1:2d}. {file_path}")
        
        if len(fixed_files) > 20:
            print(f"... and {len(fixed_files) - 20} more files")


if __name__ == "__main__":
    main()