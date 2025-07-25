#!/usr/bin/env python3
"""
💪 Aggressive Long Line Fixer
残存340件の長い行を積極的に修正するツール
"""

import os
import re
import sys
from pathlib import Path


class AggressiveLongLineFixer:
    """積極的長い行修正クラス"""
    
    def __init__(self, max_length=120):
        self.max_length = max_length
        self.fixed_count = 0
        
    def fix_aggressive(self, file_path: str) -> int:
        """積極的に長い行を修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            fixes_made = 0
            
            for line in lines:
                if len(line.rstrip()) > self.max_length:
                    fixed_lines = self._aggressive_fix(line)
                    new_lines.extend(fixed_lines)
                    if len(fixed_lines) > 1:
                        fixes_made += 1
                else:
                    new_lines.append(line)
            
            if fixes_made > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                print(f"✅ {file_path}: Fixed {fixes_made} long lines")
                
            return fixes_made
            
        except Exception as e:
            print(f"❌ Error in {file_path}: {e}")
            return 0
    
    def _aggressive_fix(self, line: str) -> list:
        """積極的な長い行修正"""
        stripped = line.rstrip()
        indent = self._get_indent(line)
        
        # f-string分割
        if stripped.strip().startswith('f"') or stripped.strip().startswith("f'"):
            return self._fix_fstring(line, indent)
        
        # 文字列連結分割  
        if any(op in stripped for op in [' + ', ' += ']):
            return self._fix_string_concat(line, indent)
        
        # 長い条件式分割
        if any(op in stripped for op in [' and ', ' or ', ' if ', ' else ']):
            return self._fix_condition(line, indent)
        
        # 辞書・リスト分割
        if any(char in stripped for char in ['{', '[']) and any(char in stripped for char in ['}', ']']):
            return self._fix_collection(line, indent)
        
        # 関数引数分割
        if '(' in stripped and ')' in stripped and ',' in stripped:
            return self._fix_function_args(line, indent)
        
        # コメント分割
        if stripped.strip().startswith('#'):
            return self._fix_comment(line, indent)
        
        # 単純な行継続
        return self._simple_break(line, indent)
    
    def _get_indent(self, line: str) -> str:
        """インデント取得"""
        return re.match(r'^(\s*)', line).group(1)
    
    def _fix_fstring(self, line: str, indent: str) -> list:
        """f-string修正"""
        stripped = line.strip()
        
        # 変数が多い場合は分割
        if '{' in stripped and '}' in stripped:
            # f"text {var1} more {var2} text" -> 複数行に分割
            parts = re.split(r'(\{[^}]+\})', stripped)
            
            if len(parts) > 3:  # 複数の変数がある場合
                result = [f'{indent}(\n']
                current_line = f'{indent}    f"'
                
                for part in parts:
                    if part.startswith('{') and part.endswith('}'):
                        # 変数部分
                        if not (len(current_line + part + '"') > self.max_length - 10):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if len(current_line + part + '"') > self.max_length - 10:
                            current_line += '"\n'
                            result.append(current_line)
                            current_line = f'{indent}    f"{part}'
                        else:
                            current_line += part
                    else:
                        # テキスト部分
                        current_line += part
                
                current_line += '"\n'
                result.append(current_line)
                result.append(f'{indent})\n')
                return result
        
        # 長いf-stringは通常の文字列分割
        return self._simple_break(line, indent)
    
    def _fix_string_concat(self, line: str, indent: str) -> list:
        """文字列連結修正"""
        stripped = line.strip()
        
        if ' + ' in stripped:
            parts = [p.strip() for p in stripped.split(' + ')]
            if len(parts) > 1:
                result = []
                for i, part in enumerate(parts):
                    if i == 0:
                        result.append(f'{indent}{part} + \\\n')
                    elif i == len(parts) - 1:
                        result.append(f'{indent}    {part}\n')
                    else:
                        result.append(f'{indent}    {part} + \\\n')
                return result
        
        return [line]
    
    def _fix_condition(self, line: str, indent: str) -> list:
        """条件式修正"""
        stripped = line.strip()
        
        # 論理演算子で分割
        for op in [' and ', ' or ']:
            if op in stripped:
                parts = stripped.split(op, 1)
                if len(parts) == 2:
                    return [
                        f'{indent}{parts[0]} {op.strip()} \\\n',
                        f'{indent}    {parts[1]}\n'
                    ]
        
        # 三項演算子で分割
        if ' if ' in stripped and ' else ' in stripped:
            # value if condition else other
            if_pos = stripped.find(' if ')
            else_pos = stripped.find(' else ')
            
            # 複雑な条件判定
            if 0 < if_pos < else_pos:
                value = stripped[:if_pos]
                condition = stripped[if_pos + 4:else_pos]
                else_value = stripped[else_pos + 6:]
                
                return [
                    f'{indent}{value} \\\n',
                    f'{indent}    if {condition} \\\n',
                    f'{indent}    else {else_value}\n'
                ]
        
        return [line]
    
    def _fix_collection(self, line: str, indent: str) -> list:
        """辞書・リスト修正"""
        stripped = line.strip()
        
        # 辞書の場合
        if '{' in stripped and '}' in stripped and ':' in stripped:
            brace_start = stripped.find('{')
            brace_end = stripped.rfind('}')
            
            if brace_start >= 0 and brace_end > brace_start:
                before = stripped[:brace_start + 1]
                content = stripped[brace_start + 1:brace_end]
                after = stripped[brace_end:]
                
                if ',' in content:
                    items = [item.strip() for item in content.split(',')]
                    result = [f'{indent}{before}\n']
                    
                    for i, item in enumerate(items):
                        if not (item):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if item:
                            ending = ',\n' if i < len(items) - 1 else '\n'
                            result.append(f'{indent}    {item}{ending}')
                    
                    result.append(f'{indent}{after}\n')
                    return result
        
        # リストの場合
        elif '[' in stripped and ']' in stripped:
            bracket_start = stripped.find('[')
            bracket_end = stripped.rfind(']')
            
            if bracket_start >= 0 and bracket_end > bracket_start:
                before = stripped[:bracket_start + 1]
                content = stripped[bracket_start + 1:bracket_end]
                after = stripped[bracket_end:]
                
                if ',' in content:
                    items = [item.strip() for item in content.split(',')]
                    result = [f'{indent}{before}\n']
                    
                    # Deep nesting detected (depth: 5) - consider refactoring
                    for i, item in enumerate(items):
                        if not (item):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if item:
                            ending = ',\n' if i < len(items) - 1 else '\n'
                            result.append(f'{indent}    {item}{ending}')
                    
                    result.append(f'{indent}{after}\n')
                    return result
        
        return [line]
    
    def _fix_function_args(self, line: str, indent: str) -> list:
        """関数引数修正"""
        stripped = line.strip()
        
        paren_start = stripped.find('(')
        paren_end = stripped.rfind(')')
        
        if paren_start > 0 and paren_end > paren_start:
            before = stripped[:paren_start + 1]
            args = stripped[paren_start + 1:paren_end]
            after = stripped[paren_end:]
            
            if ',' in args:
                arg_list = [arg.strip() for arg in args.split(',')]
                result = [f'{indent}{before}\n']
                
                for i, arg in enumerate(arg_list):
                    if arg:
                        ending = ',\n' if i < len(arg_list) - 1 else '\n'
                        result.append(f'{indent}    {arg}{ending}')
                
                result.append(f'{indent}{after}\n')
                return result
        
        return [line]
    
    def _fix_comment(self, line: str, indent: str) -> list:
        """コメント修正"""
        stripped = line.strip()
        
        if len(stripped) > self.max_length:
            # コメントプレフィックス取得
            prefix = '#'
            content = stripped[1:].strip()
            
            # 単語単位で分割
            words = content.split()
            result = []
            current = f'{indent}{prefix} '
            
            for word in words:
                if len(current + word + ' ') > self.max_length:
                    result.append(current.rstrip() + '\n')
                    current = f'{indent}{prefix} {word} '
                else:
                    current += word + ' '
            
            if current.strip() != prefix:
                result.append(current.rstrip() + '\n')
            
            return result if len(result) > 1 else [line]
        
        return [line]
    
    def _simple_break(self, line: str, indent: str) -> list:
        """単純な行分割"""
        stripped = line.strip()
        
        # 適切な分割点を見つける
        break_points = [', ', ' = ', ' == ', ' != ', ' + ', ' - ']
        
        for bp in break_points:
            if bp in stripped:
                pos = stripped.rfind(bp, 0, self.max_length - 20)
                if pos > 20:  # 最低限の長さを確保
                    before = stripped[:pos + len(bp)]
                    after = stripped[pos + len(bp):]
                    
                    return [
                        f'{indent}{before} \\\n',
                        f'{indent}    {after}\n'
                    ]
        
        # 適切な分割点が見つからない場合は80文字で強制分割
        if len(stripped) > 80:
            break_pos = 80
            # 単語境界を探す
            for i in range(break_pos - 10, break_pos + 10):
                if i < len(stripped) and stripped[i] == ' ':
                    break_pos = i
                    break
            
            before = stripped[:break_pos]
            after = stripped[break_pos:].lstrip()
            
            return [
                f'{indent}{before} \\\n',
                f'{indent}    {after}\n'
            ]
        
        return [line]


def main():
    """メインエントリーポイント"""
    fixer = AggressiveLongLineFixer()
    total_fixed = 0
    
    # スキップするディレクトリ
    skip_patterns = [
        '__pycache__', '.git', 'venv', '.venv', 'node_modules',
        'libs/elder_servants/integrations/continue_dev/venv_continue_dev'
    ]
    
    print("💪 Starting aggressive long line fixing...")
    
    for root, dirs, files in os.walk('.'):
        # スキップディレクトリを除外
        dirs[:] = [d for d in dirs if not any(skip in os.path.join(root, d) for skip in skip_patterns)]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # venvディレクトリをスキップ
                if any(skip in file_path for skip in skip_patterns):
                    continue
                
                fixes = fixer.fix_aggressive(file_path)
                total_fixed += fixes
    
    print(f"\n🎉 Aggressive long line fix completed!")
    print(f"📊 Total lines fixed: {total_fixed}")
    
    return 0 if total_fixed >= 0 else 1


if __name__ == "__main__":
    exit(main())