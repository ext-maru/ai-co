#!/usr/bin/env python3
"""
Syntax Zero Campaign - 構文エラー完全撲滅システム
🎯 Claude Elder 7200秒ミッション
"""
import os
import re
import ast
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from collections import defaultdict

class SyntaxZeroCampaign:
    """構文エラー完全撲滅キャンペーン"""
    
    def __init__(self):
        self.start_time = time.time()
        self.target_duration = 7200  # 2時間
        self.logger = self._setup_logger()
        self.repair_strategies = {
            'unexpected_indent': self._fix_unexpected_indent,
            'unterminated_string': self._fix_unterminated_string,
            'invalid_syntax_comma': self._fix_invalid_syntax_comma,
            'invalid_character': self._fix_invalid_character,
            'type_annotation_error': self._fix_type_annotation,
            'fstring_error': self._fix_fstring_error,
            'missing_parenthesis': self._fix_missing_parenthesis,
            'escape_sequence': self._fix_escape_sequence,
        }
        self.repair_history = []
        self.error_patterns = defaultdict(int)
        
    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger('SyntaxZeroCampaign')
        logger.setLevel(logging.INFO)
        
        # ファイルハンドラー
        fh = logging.FileHandler(f'logs/syntax_zero_{int(time.time())}.log')
        fh.setLevel(logging.DEBUG)
        
        # コンソールハンドラー
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # フォーマッター
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def identify_error_type(self, error_msg: str) -> str:
        """エラータイプを特定"""
        if 'unexpected indent' in error_msg:
            return 'unexpected_indent'
        elif 'unterminated string' in error_msg or 'EOL while scanning' in error_msg:
            return 'unterminated_string'
        elif 'invalid syntax' in error_msg and 'comma' in error_msg:
            return 'invalid_syntax_comma'
        elif 'invalid character' in error_msg:
            return 'invalid_character'
        elif 'expected an indented block' in error_msg:
            return 'type_annotation_error'
        elif 'unterminated f-string' in error_msg or 'f-string' in error_msg:
            return 'fstring_error'
        elif 'was never closed' in error_msg:
            return 'missing_parenthesis'
        elif 'invalid escape sequence' in error_msg:
            return 'escape_sequence'
        else:
            return 'unknown'
    
    def _fix_unexpected_indent(self, content: str, error_line: int) -> str:
        """インデントエラー修正"""
        lines = content.splitlines()
        if 0 <= error_line - 1 < len(lines):
            line = lines[error_line - 1]
            # 過剰なインデントを検出・修正
            if error_line > 1:
                prev_line = lines[error_line - 2]
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                
                # 前の行がコロンで終わる場合
                if prev_line.rstrip().endswith(':'):
                    expected_indent = prev_indent + 4
                else:
                    expected_indent = prev_indent
                
                # インデント修正
                lines[error_line - 1] = ' ' * expected_indent + line.lstrip()
        
        return '\n'.join(lines)
    
    def _fix_unterminated_string(self, content: str, error_line: int) -> str:
        """未終了文字列修正"""
        lines = content.splitlines()
        if 0 <= error_line - 1 < len(lines):
            line = lines[error_line - 1]
            
            # f-stringの特殊ケース
            if 'f"' in line or "f'" in line:
                # 壊れたf-string pattern: f"f"text" -> f"text"
                line = re.sub(r'f"f"([^"]*)"', r'f"\1"', line)
                line = re.sub(r"f'f'([^']*)'", r"f'\1'", line)
                
                # 複数引用符の修正
                if line.count('"') >= 3:
                    # f"text"other"text" -> f"textothertext"
                    parts = line.split('f"', 1)
                    if len(parts) == 2:
                        prefix, suffix = parts
                        quotes = suffix.split('"')
                        if len(quotes) >= 3:
                            # 引用符内のテキストを結合
                            fixed_text = ''.join(quotes[:-1])
                            line = prefix + 'f"' + fixed_text + '"'
            
            # 通常の未終了文字列
            else:
                # 奇数個の引用符を修正
                if line.count('"') % 2 == 1:
                    line += '"'
                if line.count("'") % 2 == 1:
                    line += "'"
            
            lines[error_line - 1] = line
        
        return '\n'.join(lines)
    
    def _fix_invalid_syntax_comma(self, content: str, error_line: int) -> str:
        """カンマ不足修正"""
        lines = content.splitlines()
        if 0 <= error_line - 2 < len(lines):
            # エラー行の前の行をチェック
            prev_line = lines[error_line - 2]
            
            # 関数引数でカンマが不足している場合
            if ('=' in prev_line and 
                not prev_line.strip().endswith((',', ':', '(', '[', '{'))):
                lines[error_line - 2] = prev_line + ','
        
        return '\n'.join(lines)
    
    def _fix_invalid_character(self, content: str, error_line: int) -> str:
        """無効文字修正"""
        # Unicode box-drawing characters
        invalid_chars = {
            '│': '|', '┌': '+', '┐': '+', '└': '+', '┘': '+',
            '├': '+', '┤': '+', '┬': '+', '┴': '+', '┼': '+'
        }
        
        for char, replacement in invalid_chars.items():
            content = content.replace(char, replacement)
        
        return content
    
    def _fix_type_annotation(self, content: str, error_line: int) -> str:
        """型アノテーションエラー修正"""
        # パターン: def func(param:\n    """docstring"""\ntype):
        pattern = r'def\s+(\w+)\s*\(\s*([^:]*?):\s*\n\s*"""([^"]+)"""\s*\n\s*([^)]+)\):'
        
        def replace_func(match):
            func_name, param, docstring, param_type = match.groups()
            return f'def {func_name}({param}: {param_type.strip()}):\n        """{docstring}"""'
        
        return re.sub(pattern, replace_func, content, flags=re.MULTILINE | re.DOTALL)
    
    def _fix_fstring_error(self, content: str, error_line: int) -> str:
        """f-stringエラー修正"""
        lines = content.splitlines()
        
        # 複数行にまたがるf-stringを検出・修正
        for i in range(len(lines)):
            line = lines[i]
            if 'f"' in line or "f'" in line:
                # 未閉じf-stringの検出
                if (line.count('"') - line.count('\\"')) % 2 == 1:
                    # 次の数行をチェック
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if '"' in lines[j]:
                            # 複数行を1行に結合
                            combined = ' '.join(lines[i:j+1])
                            lines[i] = combined
                            # 結合した行を削除
                            for k in range(j, i, -1):
                                lines.pop(k)
                            break
        
        return '\n'.join(lines)
    
    def _fix_missing_parenthesis(self, content: str, error_line: int) -> str:
        """括弧不足修正"""
        # 括弧のバランスをチェック
        open_parens = content.count('(') - content.count(')')
        open_brackets = content.count('[') - content.count(']')
        open_braces = content.count('{') - content.count('}')
        
        # 不足している括弧を追加
        if open_parens > 0:
            content += ')' * open_parens
        if open_brackets > 0:
            content += ']' * open_brackets
        if open_braces > 0:
            content += '}' * open_braces
        
        return content
    
    def _fix_escape_sequence(self, content: str, error_line: int) -> str:
        """エスケープシーケンス修正"""
        # raw文字列に変換すべきパターン
        patterns = [
            (r'([\'""])([^\'""]*\\[^\\tnr\'""]+[^\'""]*)\1', r'r\1\2\1'),
            (r're\.compile\(([\'"])([^\'""]+)\1\)', r're.compile(r\1\2\1)'),
            (r're\.search\(([\'"])([^\'""]+)\1', r're.search(r\1\2\1'),
            (r're\.match\(([\'"])([^\'""]+)\1', r're.match(r\1\2\1'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def analyze_file(self, file_path: str) -> Optional[Tuple[str, int, str]]:
        """ファイルの構文エラーを分析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 構文チェック
            try:
                ast.parse(content)
                return None  # エラーなし
            except SyntaxError as e:
                error_type = self.identify_error_type(str(e))
                self.error_patterns[error_type] += 1
                return (error_type, e.lineno or 0, str(e))
                
        except Exception as e:
            self.logger.error(f"Failed to analyze {file_path}: {e}")
            return None
    
    def repair_file(self, file_path: str) -> bool:
        """ファイルを修復"""
        try:
            # エラー分析
            error_info = self.analyze_file(file_path)
            if not error_info:
                return False  # エラーなし
            
            error_type, error_line, error_msg = error_info
            
            # 修復戦略選択
            if error_type in self.repair_strategies:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 修復実行
                repair_func = self.repair_strategies[error_type]
                repaired_content = repair_func(content, error_line)
                
                # 修復後の検証
                try:
                    ast.parse(repaired_content)
                    # 成功 - ファイル保存
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(repaired_content)
                    
                    self.repair_history.append({
                        'file': file_path,
                        'error_type': error_type,
                        'error_line': error_line,
                        'success': True,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    self.logger.info(f"✅ Fixed {file_path} ({error_type} at line {error_line})")
                    return True
                    
                except SyntaxError as e:
                    # まだエラーがある - 再帰的修復を試行
                    return self._recursive_repair(file_path, repaired_content, depth=1)
                    
            else:
                self.logger.warning(f"❓ Unknown error type for {file_path}: {error_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to repair {file_path}: {e}")
            return False
    
    def _recursive_repair(self, file_path: str, content: str, depth: int = 0) -> bool:
        """再帰的修復"""
        if depth > 5:  # 最大深度
            return False
        
        try:
            # 一時的にコンテンツで構文チェック
            ast.parse(content)
            # 成功したら保存
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
            
        except SyntaxError as e:
            # 新しいエラーを修復
            error_type = self.identify_error_type(str(e))
            if error_type in self.repair_strategies:
                repair_func = self.repair_strategies[error_type]
                repaired_content = repair_func(content, e.lineno or 0)
                return self._recursive_repair(file_path, repaired_content, depth + 1)
        
        return False
    
    def find_all_syntax_errors(self) -> List[str]:
        """全構文エラーファイルを検出"""
        error_files = []
        
        for root, dirs, files in os.walk('.'):
            # スキップするディレクトリ
            if any(skip in root for skip in ['.git', '__pycache__', '.venv', 'node_modules']):
                continue
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    if self.analyze_file(file_path):
                        error_files.append(file_path)
        
        return error_files
    
    def execute_campaign(self):
        """キャンペーン実行"""
        print("🎯 Syntax Zero Campaign - 2 Hour Mission")
        print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        campaign_start = time.time()
        total_fixed = 0
        iteration = 0
        
        while time.time() - campaign_start < self.target_duration:
            iteration += 1
            elapsed = time.time() - campaign_start
            remaining = self.target_duration - elapsed
            
            print(f"\n🔄 Iteration {iteration} | ⏱️  {elapsed/60:.1f}min / {self.target_duration/60}min")
            
            # エラーファイル検出
            error_files = self.find_all_syntax_errors()
            print(f"🔍 Found {len(error_files)} files with syntax errors")
            
            if not error_files:
                print("🎉 SYNTAX ZERO ACHIEVED! All syntax errors eliminated!")
                break
            
            # バッチ修復
            batch_fixed = 0
            for file_path in error_files[:20]:  # 20ファイルずつ処理
                if self.repair_file(file_path):
                    batch_fixed += 1
                    total_fixed += 1
                
                # 時間チェック
                if time.time() - campaign_start >= self.target_duration:
                    break
            
            print(f"📊 Batch result: {batch_fixed} files fixed")
            
            # エラーパターン分析
            if iteration % 5 == 0:
                self._analyze_patterns()
            
            # 短い休憩
            if remaining > 60:
                time.sleep(3)
        
        # 最終レポート
        self._generate_final_report(total_fixed)
    
    def _analyze_patterns(self):
        """エラーパターン分析"""
        print("\n📈 Error Pattern Analysis:")
        sorted_patterns = sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)
        for pattern, count in sorted_patterns[:5]:
            print(f"  - {pattern}: {count} occurrences")
    
    def _generate_final_report(self, total_fixed: int):
        """最終レポート生成"""
        final_errors = self.find_all_syntax_errors()
        duration = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("🏁 SYNTAX ZERO CAMPAIGN - FINAL REPORT")
        print(f"⏱️  Total Duration: {duration/60:.1f} minutes")
        print(f"🔧 Total Files Fixed: {total_fixed}")
        print(f"📊 Remaining Errors: {len(final_errors)}")
        
        if len(final_errors) == 0:
            print("🎯 MISSION ACCOMPLISHED: ZERO SYNTAX ERRORS!")
        else:
            print(f"📈 Success Rate: {total_fixed/(total_fixed + len(final_errors))*100:.1f}%")
        
        # 詳細レポート保存
        report = {
            'campaign_duration': duration,
            'total_fixed': total_fixed,
            'remaining_errors': len(final_errors),
            'error_patterns': dict(self.error_patterns),
            'repair_history': self.repair_history[-100:],  # 最後の100件
            'remaining_files': final_errors[:20]  # 最初の20件
        }
        
        report_file = f"data/syntax_zero_campaign_{int(self.start_time)}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📝 Detailed report saved to: {report_file}")
        
        # エラーパターン最終分析
        self._analyze_patterns()

def main():
    """メイン実行"""
    campaign = SyntaxZeroCampaign()
    campaign.execute_campaign()

if __name__ == "__main__":
    main()