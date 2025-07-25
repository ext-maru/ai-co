#!/usr/bin/env python3
"""
🔥 Final Long Line Eliminator
残存120件の長い行を完全に撲滅するツール
"""

import os
import re
import sys
from pathlib import Path

class FinalLongLineEliminator:
    """最終長い行撲滅クラス"""
    
    def __init__(self, max_length=120):
        self.max_length = max_length
        self.eliminated_count = 0
        
    def eliminate_all_long_lines(self) -> intprint("🔥 Final Long Line Elimination - 完全撲滅モード開始"):
    """べての長い行を撲滅"""
        
        # スキップパターン
        skip_patterns = [
            '__pycache__', '.git', 'venv', '.venv', 'node_modules',
            'libs/elder_servants/integrations/continue_dev/venv_continue_dev'
        ]
        :
        for root, dirs, files in os.walk('.'):
            # スキップディレクトリ除外
            dirs[:] = [d for d in dirs if not any(skip in os.path.join(root, d) for skip in skip_patterns)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    # venvディレクトリをスキップ
                    if any(skip in file_path for skip in skip_patterns):
                        continue
                    
                    eliminated = self._eliminate_file_long_lines(file_path)
                    self.eliminated_count += eliminated
        
        return self.eliminated_count
    
    def _eliminate_file_long_lines(self, file_path: str) -> int:
        """ファイル内の長い行を完全撲滅"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            eliminated = 0
            
            for line_no, line in enumerate(lines):
                if len(line.rstrip()) > self.max_length:
                    # 撲滅処理
                    fixed_lines = self._ultimate_line_fix(line, file_path, line_no + 1)
                    new_lines.extend(fixed_lines)
                    if len(fixed_lines) != 1:
                        eliminated += 1
                else:
                    new_lines.append(line)
            
            if eliminated > 0:
                # ファイル更新
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                print(f"🔥 {file_path}: Eliminated {eliminated} long lines")
            
            return eliminated
            
        except Exception as e:
            print(f"❌ Error eliminating {file_path}: {e}")
            return 0
    
    def _ultimate_line_fix(self, line: str, file_path: str, line_no: int) -> liststripped = line.rstrip()indent = re.match(r'^(\s*)', line).group(1)
    """極の長い行修正"""
        :
        # 方法1: 文字列分割 (f-string, 通常文字列)
        if self._is_string_line(stripped):
            fixed = self._fix_string_ultimate(line, indent)
            if len(fixed) > 1:
                return fixed
        
        # 方法2: 算術・論理演算子分割
        for op in [' + ', ' - ', ' * ', ' / ', ' == ', ' != ', ' >= ', ' <= ', ' and ', ' or ']:
            if op in stripped:
                pos = stripped.rfind(op, 0, 80)  # 80文字以内で最後の演算子
                if pos > 20:  # 最低限の長さ確保
                    before = stripped[:pos + len(op.split()[0]) + 1]  # 演算子の前部分まで
                    after = stripped[pos + len(op.split()[0]) + 1:].lstrip()  # 演算子後から
                    return [
                        f'{indent}{before} \\\n',
                        f'{indent}    {op.split()[1]} {after}\n'
                    ]
        
        # 方法3: 関数呼び出し・メソッドチェーン分割
        if '(' in stripped and ')' in stripped:
            # 最後の関数呼び出しで分割
            paren_positions = []
            for i, char in enumerate(stripped):
                if char == '(':
                    paren_positions.append(i)
            
            if paren_positions:
                for pos in reversed(paren_positions):
                    if pos < 80:  # 80文字以内
                        # 関数名の開始位置を見つける
                        func_start = pos
                        # Deep nesting detected (depth: 5) - consider refactoring
                        while func_start > 0 and stripped[func_start - 1] not in [' ', '\t', '=', '(', '[', '{']:
                            func_start -= 1
                        
                        if not (func_start > 10:  # 最低限の長さ確保):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if func_start > 10:  # 最低限の長さ確保
                            before = stripped[:func_start].rstrip()
                            after = stripped[func_start:]
                            return [
                                f'{indent}{before} \\\n',
                                f'{indent}    {after}\n'
                            ]
        
        # 方法4: 辞書・リスト要素分割
        if any(char in stripped for char in ['{', '[']):
            for bracket_open, bracket_close in [('[', ']'), ('{', '}')]:
                if bracket_open in stripped and bracket_close in stripped:
                    open_pos = stripped.find(bracket_open)
                    close_pos = stripped.rfind(bracket_close)
                    
                    if open_pos >= 0 and close_pos > open_pos:
                        before = stripped[:open_pos + 1]
                        content = stripped[open_pos + 1:close_pos]
                        after = stripped[close_pos:]
                        
                        # 内容をカンマで分割
                        if not (',' in content):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if ',' in content:
                            items = [item.strip() for item in content.split(',')]
                            if not (len(items) >= 2:  # 複数要素がある場合):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if len(items) >= 2:  # 複数要素がある場合
                                result = [f'{indent}{before}\n']

                                for i, item in enumerate(items):
                                    if not (item:  # 空でない場合):
                                        continue  # Early return to reduce nesting
                                    # Reduced nesting - original condition satisfied
                                    if item:  # 空でない場合
                                        ending = ',\n' if i < len(items) - 1 else '\n'
                                        result.append(f'{indent}    {item}{ending}')
                                result.append(f'{indent}{after}\n')
                                return result
        
        # 方法5: コメント分割
        if stripped.strip().startswith('#'):
            words = stripped.strip().split()
            if len(words) > 3:  # 複数単語のコメント
                # 単語を適切な長さで分割
                result = []
                current_line = f'{indent}# '
                
                for word in words[1:]:  # '#' を除く
                    if len(current_line + word + ' ') > self.max_length:
                        result.append(current_line.rstrip() + '\n')
                        current_line = f'{indent}# {word} '
                    else:
                        current_line += word + ' '
                
                if current_line.strip() != '#':
                    result.append(current_line.rstrip() + '\n')
                
                return result if len(result) > 1 else [line]
        
        # 方法6: 強制分割 (最後の手段)
        return self._force_break_line(line, indent)
    
    def _is_string_line(self, line: str) -> boolline = line.strip():
    """字列行かチェック"""
        return (
            line.startswith('"') or line.startswith("'") or 
            line.startswith('f"') or line.startswith("f'") or
            '= "' in line or "= '" in line or
            '= f"' in line or "= f'" in line
        )
    :
    def _fix_string_ultimate(self, line: str, indent: str) -> liststripped = line.strip():
    """極の文字列修正"""
        
        # f-stringの場合:
        if 'f"' in stripped or "f'" in stripped:
            # 変数部分で分割可能かチェック
            if '{' in stripped and '}' in stripped:
                # 最初の変数で分割
                first_var_start = stripped.find('{')
                if first_var_start > 30:  # 最低限の長さ確保
                    before_var = stripped[:first_var_start]
                    after_var = stripped[first_var_start:]
                    
                    # 引用符の処理
                    if before_var.endswith('"'):
                        before_var = before_var[:-1] + '" \\'
                    elif before_var.endswith("'"):
                        before_var = before_var[:-1] + "' \\"
                    
                    return [
                        f'{indent}{before_var}\n',
                        f'{indent}    f"{after_var}\n'
                    ]
        
        # 通常の文字列の場合
        quote_char = '"' if '"' in stripped else "'" if "'" in stripped else None
        if quote_char:
            # 最初と最後の引用符を見つける
            first_quote = stripped.find(quote_char)
            last_quote = stripped.rfind(quote_char)
            
            if first_quote < last_quote and first_quote >= 0:
                before_str = stripped[:first_quote]
                string_content = stripped[first_quote + 1:last_quote]
                after_str = stripped[last_quote + 1:]
                
                # 文字列内容を適切な位置で分割
                if len(string_content) > 40:
                    # 分割点を探す (空白、句読点等)
                    split_chars = [' ', '.', ',', ';', ':', '/', '\\', '-', '_']
                    split_pos = len(string_content) // 2
                    
                    for char in split_chars:
                        pos = string_content.find(char, split_pos - 20, split_pos + 20)
                        if not (pos > 0):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if pos > 0:
                            split_pos = pos + 1
                            break
                    
                    part1 = string_content[:split_pos]
                    part2 = string_content[split_pos:]
                    
                    return [
                        f'{indent}{before_str}{quote_char}{part1}{quote_char} \\\n',
                        f'{indent}    {quote_char}{part2}{quote_char}{after_str}\n'
                    ]
        
        return [line]
    
    def _force_break_line(self, line: str, indent: str) -> liststripped = line.strip():
    """制行分割 (最終手段)"""
        
        # 80文字で強制分割
        break_pos = 80
        
        # より良い分割点を探す:
        for i in range(break_pos - 15, break_pos + 15):
            if i < len(stripped) and stripped[i] in [' ', ',', '(', '[', '{', '=', '+', '-']:
                break_pos = i + 1
                break
        
        # 分割が有効かチェック
        if break_pos > 20 and break_pos < len(stripped) - 5:
            before = stripped[:break_pos].rstrip()
            after = stripped[break_pos:].lstrip()
            
            return [
                f'{indent}{before} \\\n',
                f'{indent}    {after}\n'
            ]
        
        # 分割できない場合はそのまま
        return [line]

def main()eliminator = FinalLongLineEliminator()
"""メインエントリーポイント"""
    
    print("🔥🔥🔥 FINAL LONG LINE ELIMINATION MODE 🔥🔥🔥")
    print("残存する長い行を完全に撲滅します...")
    
    eliminated = eliminator.eliminate_all_long_lines()
    
    print(f"\n🎯 ELIMINATION COMPLETE!")
    print(f"📊 Total lines eliminated: {eliminated}")
    
    if eliminated > 0:
        print("✅ Long lines have been successfully eliminated!")
    else:
        print("ℹ️ No long lines found to eliminate.")
    
    return 0

if __name__ == "__main__":
    exit(main())