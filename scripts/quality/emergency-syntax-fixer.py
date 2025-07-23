#!/usr/bin/env python3
"""
🚨 Emergency Syntax Fixer
大量の構文エラーを緊急修正するツール
"""

import ast
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


class EmergencySyntaxFixer:
    """緊急構文エラー修正ツール"""
    
    def __init__(self):
        self.fixed_files = []
        self.error_patterns = {}
        
    def fix_all_syntax_errors(self) -> Dict:
        """すべての構文エラーを修正"""
        print("🚨 Emergency Syntax Error Fixing - Starting...")
        
        skip_patterns = [
            '__pycache__', '.git', 'venv', '.venv', 'node_modules',
            'libs/elder_servants/integrations/continue_dev/venv_continue_dev'
        ]
        
        results = {
            'files_fixed': [],
            'total_fixes': 0,
            'processed_files': 0,
            'unfixable_files': []
        }
        
        # まず、全ての構文エラーを特定
        syntax_errors = []
        for root, dirs, files in os.walk('.'):
            # スキップディレクトリ除外
            dirs[:] = [d for d in dirs if not any(skip in os.path.join(root, d) for skip in skip_patterns)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    if any(skip in file_path for skip in skip_patterns):
                        continue
                    
                    error = self._check_syntax_error(file_path)
                    if error:
                        syntax_errors.append((file_path, error))
        
        print(f"Found {len(syntax_errors)} syntax errors to fix")
        
        # 構文エラーを修正
        for file_path, error in syntax_errors:
            success = self._fix_file_syntax_error(file_path, error)
            if success:
                results['files_fixed'].append(file_path)
                results['total_fixes'] += 1
                print(f"🔧 Fixed: {file_path}")
            else:
                results['unfixable_files'].append((file_path, error))
                print(f"❌ Could not fix: {file_path}")
            
            results['processed_files'] += 1
        
        return results
    
    def _check_syntax_error(self, file_path: str) -> str:
        """構文エラーをチェック"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            return None
        except SyntaxError as e:
            return str(e)
        except Exception as e:
            return f"Read error: {str(e)}"
    
    def _fix_file_syntax_error(self, file_path: str, error: str) -> bool:
        """ファイルの構文エラーを修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # バックアップ作成
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)
            
            # エラータイプごとに修正を試行
            fixed_content = self._apply_syntax_fixes(content, error, file_path)
            
            if fixed_content != content:
                # 修正後の構文をチェック
                try:
                    ast.parse(fixed_content)
                    # 構文が正しければファイルを更新
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    os.remove(backup_path)  # バックアップ削除
                    return True
                except SyntaxError:
                    # まだエラーがある場合は元に戻す
                    shutil.move(backup_path, file_path)
                    return False
            else:
                os.remove(backup_path)
                return False
                
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False
    
    def _apply_syntax_fixes(self, content: str, error: str, file_path: str) -> str:
        """構文修正を適用"""
        lines = content.split('\n')
        
        # エラータイプ別の修正
        if "unexpected indent" in error:
            return self._fix_unexpected_indent(lines, error)
        elif "expected an indented block" in error:
            return self._fix_missing_indent(lines, error)
        elif "unterminated string literal" in error:
            return self._fix_unterminated_string(lines, error)
        elif "unterminated f-string literal" in error:
            return self._fix_unterminated_fstring(lines, error)
        elif "invalid character" in error:
            return self._fix_invalid_character(lines, error)
        elif "Perhaps you forgot a comma" in error:
            return self._fix_missing_comma(lines, error)
        elif "invalid syntax" in error:
            return self._fix_general_syntax(lines, error)
        else:
            return content
    
    def _fix_unexpected_indent(self, lines: List[str], error: str) -> str:
        """予期しないインデントを修正"""
        line_no = self._extract_line_number(error)
        if line_no and line_no <= len(lines):
            idx = line_no - 1
            if idx >= 0 and lines[idx].strip():
                # インデントを削除
                lines[idx] = lines[idx].lstrip()
        
        return '\n'.join(lines)
    
    def _fix_missing_indent(self, lines: List[str], error: str) -> str:
        """不足しているインデントを修正"""
        line_no = self._extract_line_number(error)
        if line_no and line_no <= len(lines):
            idx = line_no - 1
            if idx >= 0:
                # 前の行のインデントを確認
                prev_indent = ""
                if idx > 0:
                    prev_line = lines[idx - 1]
                    prev_indent = re.match(r'^(\s*)', prev_line).group(1)
                    if prev_line.rstrip().endswith(':'):
                        prev_indent += "    "  # 4スペース追加
                
                # 空の行や pass を追加
                if not lines[idx].strip():
                    lines[idx] = f"{prev_indent}pass"
                elif not lines[idx].startswith(prev_indent):
                    lines[idx] = f"{prev_indent}{lines[idx].lstrip()}"
        
        return '\n'.join(lines)
    
    def _fix_unterminated_string(self, lines: List[str], error: str) -> str:
        """未終了の文字列リテラルを修正"""
        line_no = self._extract_line_number(error)
        if line_no and line_no <= len(lines):
            idx = line_no - 1
            if idx >= 0:
                line = lines[idx]
                
                # 文字列の終了を補完
                if line.count('"') % 2 == 1:  # 奇数個の"
                    lines[idx] = line + '"'
                elif line.count("'") % 2 == 1:  # 奇数個の'
                    lines[idx] = line + "'"
                elif '"""' in line and line.count('"""') == 1:
                    lines[idx] = line + '"""'
                elif "'''" in line and line.count("'''") == 1:
                    lines[idx] = line + "'''"
        
        return '\n'.join(lines)
    
    def _fix_unterminated_fstring(self, lines: List[str], error: str) -> str:
        """未終了のf-stringを修正"""
        line_no = self._extract_line_number(error)
        if line_no and line_no <= len(lines):
            idx = line_no - 1
            if idx >= 0:
                line = lines[idx]
                
                # f-stringの終了を補完
                if line.count('"') % 2 == 1:
                    lines[idx] = line + '"'
                elif line.count("'") % 2 == 1:
                    lines[idx] = line + "'"
                
                # 未閉じの{}を修正
                open_braces = line.count('{') - line.count('{{') * 2
                close_braces = line.count('}') - line.count('}}') * 2
                if open_braces > close_braces:
                    lines[idx] = line + '}' * (open_braces - close_braces)
        
        return '\n'.join(lines)
    
    def _fix_invalid_character(self, lines: List[str], error: str) -> str:
        """無効な文字を修正"""
        line_no = self._extract_line_number(error)
        if line_no and line_no <= len(lines):
            idx = line_no - 1
            if idx >= 0:
                line = lines[idx]
                
                # 一般的な無効文字を除去
                invalid_chars = ['│', '─', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼']
                for char in invalid_chars:
                    line = line.replace(char, '')
                
                # ゼロ幅文字を除去
                line = re.sub(r'[\u200b-\u200f\ufeff]', '', line)
                
                lines[idx] = line
        
        return '\n'.join(lines)
    
    def _fix_missing_comma(self, lines: List[str], error: str) -> str:
        """不足しているカンマを修正"""
        line_no = self._extract_line_number(error)
        if line_no and line_no <= len(lines):
            idx = line_no - 1
            if idx >= 0:
                line = lines[idx]
                
                # 関数呼び出しや辞書/リストでカンマが必要そうな場所を検出
                if re.search(r'\w\s+\w', line) and ('(' in line or '[' in line or '{' in line):
                    # 単語間にカンマを挿入（簡単なヒューリスティック）
                    line = re.sub(r'(\w)\s+(\w)', r'\1, \2', line)
                    lines[idx] = line
        
        return '\n'.join(lines)
    
    def _fix_general_syntax(self, lines: List[str], error: str) -> str:
        """一般的な構文エラーを修正"""
        line_no = self._extract_line_number(error)
        if line_no and line_no <= len(lines):
            idx = line_no - 1
            if idx >= 0:
                line = lines[idx]
                original_line = line
                
                # よくある問題を修正
                # 1. 不正な演算子
                line = re.sub(r'===', '==', line)
                line = re.sub(r'!==', '!=', line)
                
                # 2. セミコロンを削除
                line = re.sub(r';$', '', line)
                
                # 3. 未閉じの括弧
                open_parens = line.count('(') - line.count(')')
                if open_parens > 0:
                    line += ')' * open_parens
                
                open_brackets = line.count('[') - line.count(']')
                if open_brackets > 0:
                    line += ']' * open_brackets
                
                open_braces = line.count('{') - line.count('}')
                if open_braces > 0:
                    line += '}' * open_braces
                
                # 4. 不正な引用符の修正
                if line.count('"') % 2 == 1:
                    line += '"'
                if line.count("'") % 2 == 1:
                    line += "'"
                
                lines[idx] = line
        
        return '\n'.join(lines)
    
    def _extract_line_number(self, error: str) -> int:
        """エラーメッセージから行番号を抽出"""
        match = re.search(r'line (\d+)', error)
        if match:
            return int(match.group(1))
        return None


def main():
    """メインエントリーポイント"""
    fixer = EmergencySyntaxFixer()
    
    print("🚨🚨🚨 EMERGENCY SYNTAX ERROR FIXING 🚨🚨🚨")
    print("大量の構文エラーを緊急修正します...")
    
    results = fixer.fix_all_syntax_errors()
    
    print(f"\n📊 Emergency Fix Results:")
    print(f"Files processed: {results['processed_files']}")
    print(f"Files fixed: {len(results['files_fixed'])}")
    print(f"Unfixable files: {len(results['unfixable_files'])}")
    
    if results['unfixable_files']:
        print(f"\n❌ Unfixable files (first 10):")
        for i, (file_path, error) in enumerate(results['unfixable_files'][:10]):
            print(f"{i+1:2d}. {file_path}: {error}")
    
    return results


if __name__ == "__main__":
    main()