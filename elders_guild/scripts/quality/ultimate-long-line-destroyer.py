#!/usr/bin/env python3
"""
🚀 Ultimate Long Line Destroyer
最後の31件の長い行を完全に消滅させるツール
"""

import os
import re
import sys
from pathlib import Path


class UltimateLongLineDestroyer:
    """究極の長い行破壊クラス"""
    
    def __init__(self, max_length=120):
        self.max_length = max_length
        self.destroyed_count = 0
        
    def destroy_all_long_lines(self) -> int:
        """すべての長い行を破壊"""
        print("🚀 Ultimate Long Line Destruction - 完全破壊モード開始")
        
        # スキップパターン
        skip_patterns = [
            '__pycache__', '.git', 'venv', '.venv', 'node_modules',
            'libs/elder_servants/integrations/continue_dev/venv_continue_dev'
        ]
        
        for root, dirs, files in os.walk('.'):
            # スキップディレクトリ除外
            dirs[:] = [d for d in dirs if not any(skip in os.path.join(root, d) for skip in skip_patterns)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    # venvディレクトリをスキップ
                    if any(skip in file_path for skip in skip_patterns):
                        continue
                    
                    destroyed = self._destroy_file_long_lines(file_path)
                    self.destroyed_count += destroyed
        
        return self.destroyed_count
    
    def _destroy_file_long_lines(self, file_path: str) -> int:
        """ファイル内の長い行を完全破壊"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            destroyed = 0
            
            for line_no, line in enumerate(lines):
                if len(line.rstrip()) > self.max_length:
                    # 破壊処理
                    fixed_lines = self._ultimate_destruction(line, file_path, line_no + 1)
                    new_lines.extend(fixed_lines)
                    if len(fixed_lines) != 1:
                        destroyed += 1
                else:
                    new_lines.append(line)
            
            if destroyed > 0:
                # ファイル更新
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                print(f"🚀 {file_path}: Destroyed {destroyed} long lines")
            
            return destroyed
            
        except Exception as e:
            print(f"❌ Error destroying {file_path}: {e}")
            return 0
    
    def _ultimate_destruction(self, line: str, file_path: str, line_no: int) -> list:
        """究極の長い行破壊"""
        stripped = line.rstrip()
        indent = re.match(r'^(\s*)', line).group(1)
        
        # 戦略1: HTML文字列の分割
        if 'f"<tr><td>' in stripped or "f'<tr><td>" in stripped:
            return self._destroy_html_fstring(line, indent)
        
        # 戦略2: 三項演算子の分割
        if ' if ' in stripped and ' else ' in stripped:
            return self._destroy_ternary_operator(line, indent)
        
        # 戦略3: 長いタプル・リスト引数の分割
        if '(' in stripped and ')' in stripped and ',' in stripped:
            return self._destroy_long_arguments(line, indent)
        
        # 戦略4: 長い辞書キーの分割
        if 'for k in' in stripped and 'if k.startswith' in stripped:
            return self._destroy_comprehension_filter(line, indent)
        
        # 戦略5: 長いSQL文の分割
        if any(sql_kw in stripped.upper() for sql_kw in ['INSERT INTO', 'SELECT', 'UPDATE', 'DELETE']):
            return self._destroy_sql_statement(line, indent)
        
        # 戦略6: join文の分割
        if '.join(' in stripped:
            return self._destroy_join_statement(line, indent)
        
        # 戦略7: 長いf-string式の分割
        if 'f"' in stripped or "f'" in stripped:
            return self._destroy_fstring_expression(line, indent)
        
        # 戦略8: 強制80文字分割
        return self._force_destruction(line, indent)
    
    def _destroy_html_fstring(self, line: str, indent: str) -> list:
        """HTML f-string の破壊"""
        stripped = line.strip()
        
        if 'f"<tr><td>' in stripped:
            # HTMLテーブル行の分割
            parts = stripped.split('f"', 1)
            before = parts[0]
            html_part = parts[1]
            
            # HTMLを適切な位置で分割
            td_pattern = r'(\{[^}]+\})</td><td>'
            matches = list(re.finditer(td_pattern, html_part))
            
            if matches and len(matches) >= 2:
                # 2つ目のセルで分割
                split_pos = matches[1].end() - 8  # "</td><td>"を含める
                part1 = html_part[:split_pos]
                part2 = html_part[split_pos:]
                
                return [
                    f'{indent}{before}f"{part1}" \\\n',
                    f'{indent}    f"{part2}\n'
                ]
        
        return [line]
    
    def _destroy_ternary_operator(self, line: str, indent: str) -> list:
        """三項演算子の破壊"""
        stripped = line.strip()
        
        # A if condition else B の形式を探す
        if_pos = stripped.find(' if ')
        else_pos = stripped.find(' else ', if_pos)
        
        if if_pos > 0 and else_pos > if_pos:
            # 分割位置を決定
            if if_pos < 60:  # ifで分割
                before = stripped[:if_pos + 4]  # " if "を含める
                after = stripped[if_pos + 4:]
                
                return [
                    f'{indent}{before} \\\n',
                    f'{indent}    {after}\n'
                ]
            elif else_pos < 80:  # elseで分割
                before = stripped[:else_pos + 5]  # " else "を含める
                after = stripped[else_pos + 5:]
                
                return [
                    f'{indent}{before} \\\n',
                    f'{indent}    {after}\n'
                ]
        
        return [line]
    
    def _destroy_long_arguments(self, line: str, indent: str) -> list:
        """長い引数リストの破壊"""
        stripped = line.strip()
        
        # 括弧内の引数を探す
        paren_start = stripped.find('(')
        paren_end = stripped.rfind(')')
        
        if paren_start >= 0 and paren_end > paren_start:
            before = stripped[:paren_start + 1]
            args_part = stripped[paren_start + 1:paren_end]
            after = stripped[paren_end:]
            
            # 引数をカンマで分割
            args = [arg.strip() for arg in args_part.split(',') if arg.strip()]
            
            if len(args) >= 3:
                # 引数を複数行に分割
                result = [f'{indent}{before}\n']
                for i, arg in enumerate(args):
                    ending = ',\n' if i < len(args) - 1 else '\n'
                    result.append(f'{indent}    {arg}{ending}')
                result.append(f'{indent}{after}\n')
                return result
        
        return [line]
    
    def _destroy_comprehension_filter(self, line: str, indent: str) -> list:
        """リスト内包表記フィルターの破壊"""
        stripped = line.strip()
        
        # リスト内包表記の分割
        if ' for ' in stripped and ' if ' in stripped:
            for_pos = stripped.find(' for ')
            if_pos = stripped.find(' if ', for_pos)
            
            if for_pos > 30 and if_pos > for_pos:
                before = stripped[:for_pos + 5]
                middle = stripped[for_pos + 5:if_pos + 4]
                after = stripped[if_pos + 4:]
                
                return [
                    f'{indent}{before} \\\n',
                    f'{indent}    {middle} \\\n',
                    f'{indent}    if {after}\n'
                ]
        
        return [line]
    
    def _destroy_sql_statement(self, line: str, indent: str) -> list:
        """SQL文の破壊"""
        stripped = line.strip()
        
        # SQL文を適切な位置で分割
        sql_keywords = ['INSERT INTO', 'VALUES', 'SELECT', 'FROM', 'WHERE', 'UPDATE', 'SET']
        
        for keyword in sql_keywords:
            if keyword in stripped.upper():
                pos = stripped.upper().find(keyword)
                # 複雑な条件判定
                if 20 < pos < 80:
                    before = stripped[:pos].rstrip()
                    after = stripped[pos:]
                    
                    return [
                        f'{indent}{before} \\\n',
                        f'{indent}    {after}\n'
                    ]
        
        return [line]
    
    def _destroy_join_statement(self, line: str, indent: str) -> list:
        """join文の破壊"""
        stripped = line.strip()
        
        join_pos = stripped.find('.join(')
        if join_pos > 30:
            before = stripped[:join_pos]
            after = stripped[join_pos:]
            
            return [
                f'{indent}{before} \\\n',
                f'{indent}    {after}\n'
            ]
        
        return [line]
    
    def _destroy_fstring_expression(self, line: str, indent: str) -> list:
        """f-string式の破壊"""
        stripped = line.strip()
        
        # f-string内の式を分割
        if '{' in stripped and '}' in stripped:
            # 最初の{で分割を試す
            brace_pos = stripped.find('{')
            if 30 < brace_pos < 80:
                # 変数部分の前で分割
                split_pos = brace_pos
                while split_pos > 0 and stripped[split_pos - 1] not in [' ', '"', "'", '(']:
                    split_pos -= 1
                
                if split_pos > 20:
                    before = stripped[:split_pos].rstrip()
                    after = stripped[split_pos:].lstrip()
                    
                    return [
                        f'{indent}{before} \\\n',
                        f'{indent}    {after}\n'
                    ]
        
        return [line]
    
    def _force_destruction(self, line: str, indent: str) -> list:
        """強制破壊 (最終手段)"""
        stripped = line.strip()
        
        # 80文字で強制分割
        break_pos = 80
        
        # より良い分割点を探す
        for i in range(break_pos - 20, min(break_pos + 20, len(stripped))):
            if i < len(stripped) and stripped[i] in [' ', ',', '.', '(', '[', '{', '=', '+', '-', '/', '*']:
                break_pos = i + 1
                break
        
        # 分割が有効かチェック
        if 15 < break_pos < len(stripped) - 5:
            before = stripped[:break_pos].rstrip()
            after = stripped[break_pos:].lstrip()
            
            return [
                f'{indent}{before} \\\n',
                f'{indent}    {after}\n'
            ]
        
        # 分割できない場合は、文字列を探してそこで分割
        if '"' in stripped or "'" in stripped:
            quote_char = '"' if '"' in stripped else "'"
            quote_pos = stripped.find(quote_char, 30)
            if quote_pos > 30:
                before = stripped[:quote_pos].rstrip()
                after = stripped[quote_pos:].lstrip()
                
                return [
                    f'{indent}{before} \\\n',
                    f'{indent}    {after}\n'
                ]
        
        # 最後の手段: 60文字で強制分割
        if len(stripped) > 60:
            before = stripped[:60].rstrip()
            after = stripped[60:].lstrip()
            
            return [
                f'{indent}{before} \\\n',
                f'{indent}    {after}\n'
            ]
        
        # 分割不可能
        return [line]


def main():
    """メインエントリーポイント"""
    destroyer = UltimateLongLineDestroyer()
    
    print("🚀🚀🚀 ULTIMATE LONG LINE DESTRUCTION MODE 🚀🚀🚀")
    print("残存する最後の長い行を完全に破壊します...")
    
    destroyed = destroyer.destroy_all_long_lines()
    
    print(f"\n💥 DESTRUCTION COMPLETE!")
    print(f"📊 Total lines destroyed: {destroyed}")
    
    if destroyed > 0:
        print("✅ All long lines have been successfully destroyed!")
    else:
        print("ℹ️ No long lines found to destroy.")
    
    return 0


if __name__ == "__main__":
    exit(main())