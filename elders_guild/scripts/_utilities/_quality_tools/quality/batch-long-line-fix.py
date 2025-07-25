#!/usr/bin/env python3
"""
🏛️ Elder Guild Long Line Batch Fixer
エルダーズギルド バッチ長い行修正スクリプト

1932件の長い行を効率的に修正するツール
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


class LongLineFixer:
    """長い行自動修正クラス"""
    
    def __init__(self, max_line_length: int = 120):
        self.max_line_length = max_line_length
        self.fixed_count = 0
        self.total_count = 0
        
    def fix_file_long_lines(self, file_path: str) -> bool:
        """ファイル内の長い行を修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            original_lines = lines.copy()
            modified = False
            
            new_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                line_length = len(line.rstrip('\n\r'))
                
                if line_length > self.max_line_length:
                    # 長い行を修正
                    fixed_lines = self._fix_long_line(line, file_path, i + 1)
                    if fixed_lines and len(fixed_lines) > 1:
                        new_lines.extend(fixed_lines)
                        modified = True
                        self.fixed_count += 1
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
                
                i += 1
            
            if modified:
                # ファイルに書き戻し
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                print(f"✅ Fixed long lines in {file_path}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            return False
    
    def _fix_long_line(self, line: str, file_path: str, line_num: int) -> List[str]:
        """長い行を適切に分割"""
        stripped_line = line.rstrip('\n\r')
        original_indent = self._get_indent(line)
        
        # コメント行の場合
        if stripped_line.strip().startswith('#'):
            return self._fix_comment_line(line, original_indent)
        
        # docstring行の場合
        if '"""' in stripped_line or "'''" in stripped_line:
            return self._fix_docstring_line(line, original_indent)
        
        # import行の場合
        if stripped_line.strip().startswith('import ') or stripped_line.strip().startswith('from '):
            return self._fix_import_line(line, original_indent)
        
        # 文字列リテラルの場合
        if self._contains_long_string(stripped_line):
            return self._fix_string_line(line, original_indent)
        
        # 関数呼び出し・定義の場合
        if '(' in stripped_line and ')' in stripped_line:
            return self._fix_function_line(line, original_indent)
        
        # リストや辞書の場合
        if any(char in stripped_line for char in '[{'):
            return self._fix_collection_line(line, original_indent)
        
        # 論理演算子での分割
        if any(op in stripped_line for op in [' and ', ' or ', ' if ', ' else ']):
            return self._fix_logical_line(line, original_indent)
        
        # その他の場合はそのまま返す
        return [line]
    
    def _get_indent(self, line: str) -> str:
        """行のインデントを取得"""
        match = re.match(r'^(\s*)', line)
        return match.group(1) if match else ''
    
    def _fix_comment_line(self, line: str, indent: str) -> List[str]:
        """コメント行を修正"""
        content = line.strip()
        if len(content) <= self.max_line_length:
            return [line]
        
        # コメント記号を取得
        comment_prefix = '#'
        if content.startswith('##'):
            comment_prefix = '##'
        elif content.startswith('###'):
            comment_prefix = '###'
        
        # コメント内容を取得
        comment_content = content[len(comment_prefix):].strip()
        
        # 単語単位で分割
        words = comment_content.split()
        lines = []
        current_line = f"{indent}{comment_prefix} "
        
        for word in words:
            test_line = f"{current_line}{word} "
            if len(test_line) <= self.max_line_length:
                current_line = test_line
            else:
                if current_line.strip() != f"{comment_prefix}":
                    lines.append(current_line.rstrip() + '\n')
                current_line = f"{indent}{comment_prefix} {word} "
        
        if current_line.strip() != f"{comment_prefix}":
            lines.append(current_line.rstrip() + '\n')
        
        return lines if len(lines) > 1 else [line]
    
    def _fix_docstring_line(self, line: str, indent: str) -> List[str]:
        """docstring行を修正"""
        stripped = line.strip()
        
        # 三重引用符の開始・終了行はそのまま
        if stripped in ['"""', "'''"]:
            return [line]
        
        # docstring内容を分割
        if stripped.startswith('"""') and stripped.endswith('"""') and len(stripped) > 6:
            content = stripped[3:-3]
            if len(stripped) <= self.max_line_length:
                return [line]
            
            # 短いdocstringの場合は複数行に分割
            return [
                f'{indent}"""\n',
                f'{indent}{content}\n',
                f'{indent}"""\n'
            ]
        
        return [line]
    
    def _fix_import_line(self, line: str, indent: str) -> List[str]:
        """import行を修正"""
        stripped = line.strip()
        
        if stripped.startswith('from ') and ' import ' in stripped:
            # from ... import の場合
            parts = stripped.split(' import ', 1)
            from_part = parts[0]
            import_part = parts[1]
            
            # import部分にカンマがある場合
            if ',' in import_part:
                imports = [imp.strip() for imp in import_part.split(',')]
                
                lines = [f'{indent}{from_part} import (\n']
                for i, imp in enumerate(imports):
                    ending = ',\n' if i < len(imports) - 1 else '\n'
                    lines.append(f'{indent}    {imp}{ending}')
                lines.append(f'{indent})\n')
                
                return lines
        
        # 通常のimport行はそのまま
        return [line]
    
    def _fix_string_line(self, line: str, indent: str) -> List[str]:
        """文字列行を修正"""
        stripped = line.strip()
        
        # f-stringの場合
        if stripped.startswith('f"') or stripped.startswith("f'"):
            # f-stringは分割が複雑なのでそのまま返す
            return [line]
        
        # 通常の文字列リテラル
        if ('"' in stripped or "'" in stripped) and len(stripped) > self.max_line_length:
            # 文字列を複数行に分割
            quote_char = '"' if '"' in stripped else "'"
            
            # 簡単な文字列の場合のみ分割
            if stripped.count(quote_char) == 2:
                start = stripped.find(quote_char)
                end = stripped.rfind(quote_char)
                if start < end:
                    before = stripped[:start]
                    string_content = stripped[start+1:end]
                    after = stripped[end+1:]
                    
                    if len(string_content) > 80:
                        # 長い文字列を分割
                        mid_point = len(string_content) // 2
                        # 適切な分割点を見つける
                        split_point = mid_point
                        # Deep nesting detected (depth: 5) - consider refactoring
                        for i in range(max(0, mid_point-20), min(len(string_content), mid_point+20)):
                            if not (string_content[i] in [' ', '.', ',', ';']):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if string_content[i] in [' ', '.', ',', ';']:
                                split_point = i + 1
                                break
                        
                        part1 = string_content[:split_point]
                        part2 = string_content[split_point:]
                        
                        return [
                            f'{indent}{before}{quote_char}{part1}{quote_char} \\\n',
                            f'{indent}    {quote_char}{part2}{quote_char}{after}\n'
                        ]
        
        return [line]
    
    def _fix_function_line(self, line: str, indent: str) -> List[str]:
        """関数行を修正"""
        stripped = line.strip()
        
        # 関数定義の場合
        if stripped.startswith('def ') or stripped.startswith('async def '):
            return self._fix_function_definition(line, indent)
        
        # 関数呼び出しの場合
        if '(' in stripped and ')' in stripped:
            return self._fix_function_call(line, indent)
        
        return [line]
    
    def _fix_function_definition(self, line: str, indent: str) -> List[str]:
        """関数定義を修正"""
        stripped = line.strip()
        
        # 関数名と引数部分を分離
        paren_start = stripped.find('(')
        paren_end = stripped.rfind(')')
        
        if paren_start > 0 and paren_end > paren_start:
            func_part = stripped[:paren_start + 1]
            args_part = stripped[paren_start + 1:paren_end]
            end_part = stripped[paren_end:]
            
            # 引数が長い場合は複数行に分割
            if ',' in args_part:
                args = [arg.strip() for arg in args_part.split(',')]
                
                lines = [f'{indent}{func_part}\n']
                for i, arg in enumerate(args):
                    if arg:  # 空の引数をスキップ
                        ending = ',\n' if i < len(args) - 1 else '\n'
                        lines.append(f'{indent}    {arg}{ending}')
                lines.append(f'{indent}{end_part}\n')
                
                return lines
        
        return [line]
    
    def _fix_function_call(self, line: str, indent: str) -> List[str]:
        """関数呼び出しを修正"""
        stripped = line.strip()
        
        # 単純な関数呼び出しで引数が多い場合
        paren_start = stripped.find('(')
        paren_end = stripped.rfind(')')
        
        if paren_start > 0 and paren_end > paren_start:
            func_part = stripped[:paren_start + 1]
            args_part = stripped[paren_start + 1:paren_end]
            end_part = stripped[paren_end:]
            
            # 引数が長い場合は複数行に分割
            if ',' in args_part and len(args_part) > 60:
                args = [arg.strip() for arg in args_part.split(',')]
                
                lines = [f'{indent}{func_part}\n']
                for i, arg in enumerate(args):
                    if arg:  # 空の引数をスキップ
                        ending = ',\n' if i < len(args) - 1 else '\n'
                        lines.append(f'{indent}    {arg}{ending}')
                lines.append(f'{indent}{end_part}\n')
                
                return lines
        
        return [line]
    
    def _fix_collection_line(self, line: str, indent: str) -> List[str]:
        """コレクション行を修正"""
        stripped = line.strip()
        
        # リストや辞書が長い場合
        if '[' in stripped and ']' in stripped:
            return self._fix_list_line(line, indent)
        elif '{' in stripped and '}' in stripped:
            return self._fix_dict_line(line, indent)
        
        return [line]
    
    def _fix_list_line(self, line: str, indent: str) -> List[str]:
        """リスト行を修正"""
        stripped = line.strip()
        
        bracket_start = stripped.find('[')
        bracket_end = stripped.rfind(']')
        
        if bracket_start >= 0 and bracket_end > bracket_start:
            before = stripped[:bracket_start + 1]
            content = stripped[bracket_start + 1:bracket_end]
            after = stripped[bracket_end:]
            
            if ',' in content and len(content) > 60:
                items = [item.strip() for item in content.split(',')]
                
                lines = [f'{indent}{before}\n']
                for i, item in enumerate(items):
                    if item:  # 空の項目をスキップ
                        ending = ',\n' if i < len(items) - 1 else '\n'
                        lines.append(f'{indent}    {item}{ending}')
                lines.append(f'{indent}{after}\n')
                
                return lines
        
        return [line]
    
    def _fix_dict_line(self, line: str, indent: str) -> List[str]:
        """辞書行を修正"""
        stripped = line.strip()
        
        brace_start = stripped.find('{')
        brace_end = stripped.rfind('}')
        
        if brace_start >= 0 and brace_end > brace_start:
            before = stripped[:brace_start + 1]
            content = stripped[brace_start + 1:brace_end]
            after = stripped[brace_end:]
            
            if ',' in content and len(content) > 60:
                items = [item.strip() for item in content.split(',')]
                
                lines = [f'{indent}{before}\n']
                for i, item in enumerate(items):
                    if item:  # 空の項目をスキップ
                        ending = ',\n' if i < len(items) - 1 else '\n'
                        lines.append(f'{indent}    {item}{ending}')
                lines.append(f'{indent}{after}\n')
                
                return lines
        
        return [line]
    
    def _fix_logical_line(self, line: str, indent: str) -> List[str]:
        """論理演算子行を修正"""
        stripped = line.strip()
        
        # and/or で分割
        for op in [' and ', ' or ']:
            if op in stripped:
                parts = stripped.split(op)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    return [
                        f'{indent}{left} {op.strip()} \\\n',
                        f'{indent}    {right}\n'
                    ]
        
        # if/else で分割
        if ' if ' in stripped and ' else ' in stripped:
            # 三項演算子の場合
            if_pos = stripped.find(' if ')
            else_pos = stripped.find(' else ')
            
            if if_pos < else_pos:
                before_if = stripped[:if_pos].strip()
                condition = stripped[if_pos + 4:else_pos].strip()
                after_else = stripped[else_pos + 6:].strip()
                
                return [
                    f'{indent}{before_if} if \\\n',
                    f'{indent}    {condition} else \\\n',
                    f'{indent}    {after_else}\n'
                ]
        
        return [line]
    
    def _contains_long_string(self, line: str) -> bool:
        """長い文字列リテラルを含むかチェック"""
        quotes = ['"', "'"]
        for quote in quotes:
            if line.count(quote) >= 2:
                start = line.find(quote)
                end = line.rfind(quote)
                if start < end and (end - start) > 60:
                    return True
        return False


def main():
    """メインエントリーポイント"""
    if len(sys.argv) < 2:
        print("Usage: python3 batch-long-line-fix.py <directory_or_file>")
        return 1
    
    target_path = Path(sys.argv[1])
    fixer = LongLineFixer()
    
    if target_path.is_file():
        # 単一ファイル処理
        files_to_process = [target_path]
    elif target_path.is_dir():
        # ディレクトリ処理
        files_to_process = list(target_path.rglob("*.py"))
    else:
        print(f"❌ Path not found: {target_path}")
        return 1
    
    print(f"🔧 Processing {len(files_to_process)} Python files for long lines...")
    
    for file_path in files_to_process:
        # テストファイル、__pycache__、migrations等をスキップ
        if any(skip in str(file_path) for skip in ['__pycache__', '.pyc', 'migrations', 'venv']):
            continue
            
        fixer.total_count += 1
        fixer.fix_file_long_lines(str(file_path))
    
    print(f"\n✅ Batch long line fix completed!")
    print(f"📊 Fixed: {fixer.fixed_count} long lines in {fixer.total_count} files")
    
    return 0


if __name__ == "__main__":
    exit(main())