#!/usr/bin/env python3
"""
Advanced Syntax Repair Engine - Claude Elder Auto Mode
🤖 高度構文修復エンジン - 3600秒自動継続モード
"""
import os
import re
import ast
import time
import json
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

class SyntaxRepairEngine:
    """高度構文修復エンジン"""
    
    def __init__(self):
        self.repair_log = []
        self.start_time = time.time()
        self.target_duration = 3600  # 1時間
        self.repair_patterns = {
            'docstring_position': self._fix_docstring_position,
            'unterminated_string': self._fix_unterminated_string, 
            'bracket_mismatch': self._fix_bracket_mismatch,
            'indentation_error': self._fix_indentation_error,
            'comma_syntax': self._fix_comma_syntax,
            'invalid_chars': self._fix_invalid_chars,
            'fstring_corruption': self._fix_fstring_corruption,
            'continue_outside_loop': self._fix_continue_outside_loop,
        }
        
    def log_repair(self, file_path: str, pattern: str, success: bool, details: str = ""):
        """修復ログ記録"""
        self.repair_log.append({
            'timestamp': datetime.now().isoformat(),
            'file': file_path,
            'pattern': pattern,
            'success': success,
            'details': details,
            'elapsed': time.time() - self.start_time
        })
        
    def _fix_docstring_position(self, content: str) -> str:
        """docstringの位置修正"""
        # パターン1: def func(param:\n    """docstring"""\ntype):
        pattern = r'def\s+(\w+)\s*\(\s*([^:]*?):\s*\n\s*"""([^"]+)"""\s*\n\s*([^)]+)\):'
        
        def replace_func(match):
            func_name, param_start, docstring, param_end = match.groups()
            return f'def {func_name}({param_start}: {param_end.strip()}):\n        """{docstring}"""'
        
        return re.sub(pattern, replace_func, content, flags=re.MULTILINE | re.DOTALL)
    
    def _fix_unterminated_string(self, content: str) -> str:
        """未終了文字列修正"""
        lines = content.splitlines()
        for i, line in enumerate(lines):
            # 奇数個のクォートチェック
            if line.count('"') % 2 == 1 and not line.strip().endswith('\\'):
                # f-string内の壊れたクォートを検出
                if 'f"' in line and line.count('"') >= 3:
                    # f"text"other"text" パターンを修正
                    fixed_line = re.sub(r'f"([^"]*)"([^"]*)"([^"]*)"', r'f"\1\2\3"', line)
                    if fixed_line != line:
                        lines[i] = fixed_line
                        continue
                
                # 通常の未終了クォート
                lines[i] = line + '"'
            
            if line.count("'") % 2 == 1 and not line.strip().endswith('\\'):
                lines[i] = line + "'"
        
        return '\n'.join(lines)
    
    def _fix_bracket_mismatch(self, content: str) -> str:
        """括弧の不一致修正"""
        # 括弧カウント
        open_parens = content.count('(') - content.count(')')
        open_brackets = content.count('[') - content.count(']')
        open_braces = content.count('{') - content.count('}')
        
        if open_parens > 0:
            content += ')' * open_parens
        elif open_parens < 0:
            content = '(' * abs(open_parens) + content
            
        if open_brackets > 0:
            content += ']' * open_brackets
        elif open_brackets < 0:
            content = '[' * abs(open_brackets) + content
            
        if open_braces > 0:
            content += '}' * open_braces
        elif open_braces < 0:
            content = '{' * abs(open_braces) + content
            
        return content
    
    def _fix_indentation_error(self, content: str) -> str:
        """インデントエラー修正"""
        lines = content.splitlines()
        for i in range(1, len(lines)):
            line = lines[i]
            prev_line = lines[i-1]
            
            # 前の行がコロンで終わっている場合
            if prev_line.rstrip().endswith(':'):
                expected_indent = len(prev_line) - len(prev_line.lstrip()) + 4
                actual_indent = len(line) - len(line.lstrip())
                
                if line.strip() and actual_indent != expected_indent:
                    lines[i] = ' ' * expected_indent + line.lstrip()
        
        return '\n'.join(lines)
    
    def _fix_comma_syntax(self, content: str) -> str:
        """カンマ構文エラー修正"""
        lines = content.splitlines()
        for i in range(len(lines) - 1):
            line = lines[i]
            next_line = lines[i + 1]
            
            # 関数引数でのカンマ不足検出
            if ('=' in line and 
                '=' in next_line and 
                not line.strip().endswith((',', ':', '(', '[', '{')) and
                not next_line.strip().startswith((')', ']', '}'))):
                lines[i] = line + ','
        
        return '\n'.join(lines)
    
    def _fix_invalid_chars(self, content: str) -> str:
        """無効文字の修正"""
        # Unicode box-drawing characters to spaces
        invalid_chars = ['│', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼']
        for char in invalid_chars:
            content = content.replace(char, ' ')
        
        return content
    
    def _fix_fstring_corruption(self, content: str) -> str:
        """f-string破損修正"""
        # f"f"text" -> f"text"
        content = re.sub(r'f"f"([^"]*)"', r'f"\1"', content)
        
        # 複数引用符の修正
        content = re.sub(r'f"([^"]*)"([^"]*)"([^"]*)"', r'f"\1\2\3"', content)
        
        return content
    
    def _fix_continue_outside_loop(self, content: str) -> str:
        """ループ外continue文の修正"""
        # Early return pattern comments
        content = re.sub(r'\s*continue\s*#\s*Early return.*\n', '\n', content)
        
        return content
    
    def repair_file(self, file_path: str) -> bool:
        """ファイル修復実行"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # 修復前の構文チェック
            try:
                ast.parse(original_content)
                return False  # 既に正常
            except SyntaxError as e:
                error_type = str(e)
            
            content = original_content
            applied_patterns = []
            
            # パターンベース修復適用
            for pattern_name, repair_func in self.repair_patterns.items():
                try:
                    new_content = repair_func(content)
                    if new_content != content:
                        content = new_content
                        applied_patterns.append(pattern_name)
                except Exception as e:
                    self.log_repair(file_path, pattern_name, False, f"Pattern error: {e}")
            
            # 修復後の構文チェック
            try:
                ast.parse(content)
                # 修復成功
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                details = f"Applied: {', '.join(applied_patterns)}"
                self.log_repair(file_path, 'complete', True, details)
                return True
                
            except SyntaxError as e:
                self.log_repair(file_path, 'failed', False, f"Still broken: {e}")
                return False
                
        except Exception as e:
            self.log_repair(file_path, 'error', False, f"File error: {e}")
            return False
    
    def find_syntax_errors(self) -> List[str]:
        """構文エラーファイル検出"""
        error_files = []
        
        for root, dirs, files in os.walk('.'):
            # Skip directories
            if any(skip in root for skip in ['.git', '__pycache__', '.venv', 'archives']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        ast.parse(content)
                    except SyntaxError:
                        error_files.append(file_path)
                    except Exception:
                        pass
        
        return error_files
    
    def auto_repair_session(self):
        """自動修復セッション実行"""
        print(f"🚀 Advanced Syntax Repair Engine - Auto Mode (3600s)")
        print(f"⏰ Start Time: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        session_start = time.time()
        total_fixed = 0
        iteration = 0
        
        while time.time() - session_start < self.target_duration:
            iteration += 1
            elapsed = time.time() - session_start
            remaining = self.target_duration - elapsed
            
            print(f"\n🔄 Iteration {iteration} (Elapsed: {elapsed:.0f}s, Remaining: {remaining:.0f}s)")
            
            # 構文エラーファイル検出
            error_files = self.find_syntax_errors()
            print(f"🔍 Found {len(error_files)} syntax error files")
            
            if not error_files:
                print("✅ No syntax errors found! Session complete.")
                break
            
            # バッチ修復実行
            batch_fixed = 0
            batch_size = min(20, len(error_files))  # 20ファイルずつ処理
            
            for file_path in error_files[:batch_size]:
                if self.repair_file(file_path):
                    batch_fixed += 1
                    total_fixed += 1
                    print(f"✅ Fixed: {file_path}")
                else:
                    print(f"❌ Failed: {file_path}")
                
                # Time check
                if time.time() - session_start >= self.target_duration:
                    break
            
            print(f"📊 Batch Result: {batch_fixed}/{batch_size} files fixed")
            
            # 短い休憩
            if remaining > 30:
                time.sleep(5)
        
        # 最終レポート
        final_errors = self.find_syntax_errors()
        print("\n" + "=" * 60)
        print(f"🏁 Auto Repair Session Complete")
        print(f"⏱️  Total Duration: {time.time() - session_start:.0f}s")
        print(f"🔧 Total Files Fixed: {total_fixed}")
        print(f"📋 Remaining Errors: {len(final_errors)}")
        print(f"📈 Success Rate: {total_fixed/(total_fixed + len(final_errors))*100:.1f}%")
        
        # ログ保存
        log_file = f"data/syntax_repair_log_{int(session_start)}.json"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'w') as f:
            json.dump(self.repair_log, f, indent=2)
        
        print(f"📝 Log saved to: {log_file}")
        
        return total_fixed, len(final_errors)

def main():
    """メイン実行"""
    engine = SyntaxRepairEngine()
    return engine.auto_repair_session()

if __name__ == "__main__":
    main()