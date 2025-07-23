#!/usr/bin/env python3
"""
長い行を自動修正するスクリプト
エルダーズギルド品質基準（100文字以内）に準拠
"""

import re
import argparse
from pathlib import Path
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

MAX_LINE_LENGTH = 100


def split_long_string(line: str, max_length: int, indent: str) -> List[str]:
    """長い文字列を適切に分割"""
    # 文字列リテラルの分割
    if '"""' in line or "'''" in line:
        # docstringは分割しない
        return [line]
    
    # 通常の文字列
    if '"' in line or "'" in line:
        # 文字列の前後を分離
        match = re.match(r'^(\s*)(.*?)(["\'])(.*?)(["\'])(.*?)$', line)
        if match:
            indent_str, prefix, quote, content, _, suffix = match.groups()
            
            # 文字列が長い場合
            if len(content) > max_length - len(indent_str) - len(prefix) - 10:
                # 適切な位置で分割
                parts = []
                current = content
                
                while len(current) > max_length - len(indent_str) - 10:
                    # スペースまたは句読点で分割
                    split_pos = max_length - len(indent_str) - 10
                    for i in range(split_pos, 0, -1):
                        if current[i] in ' ,.:;!?':
                            split_pos = i + 1
                            break
                    
                    parts.append(current[:split_pos])
                    current = current[split_pos:]
                
                if current:
                    parts.append(current)
                
                # 分割した文字列を結合
                lines = []
                lines.append(f'{indent_str}{prefix}{quote}{parts[0]}{quote} \\')
                for part in parts[1:-1]:
                    lines.append(f'{indent_str}    {quote}{part}{quote} \\')
                lines.append(f'{indent_str}    {quote}{parts[-1]}{quote}{suffix}')
                
                return lines
    
    return [line]


def split_function_call(line: str, max_length: int, indent: str) -> List[str]:
    """関数呼び出しを適切に分割"""
    # 関数呼び出しパターン
    match = re.match(r'^(\s*)(.*?)(\w+)\((.*)\)(.*)$', line)
    if match:
        indent_str, prefix, func_name, args, suffix = match.groups()
        
        # 引数を分割
        arg_parts = []
        current_arg = ""
        paren_depth = 0
        in_string = False
        string_char = None
        
        for char in args:
            if not in_string:
                if char in '"\'':
                    in_string = True
                    string_char = char
                elif char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                elif char == ',' and paren_depth == 0:
                    arg_parts.append(current_arg.strip())
                    current_arg = ""
                    continue
            elif char == string_char and args[args.index(char)-1] != '\\':
                in_string = False
            
            current_arg += char
        
        if current_arg:
            arg_parts.append(current_arg.strip())
        
        # 複数行に分割
        if len(arg_parts) > 1:
            lines = []
            lines.append(f'{indent_str}{prefix}{func_name}(')
            for i, arg in enumerate(arg_parts[:-1]):
                lines.append(f'{indent_str}    {arg},')
            lines.append(f'{indent_str}    {arg_parts[-1]}')
            lines.append(f'{indent_str}){suffix}')
            return lines
    
    return [line]


def fix_long_lines_in_file(file_path: Path, dry_run: bool = False) -> int:
    """ファイル内の長い行を修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        modified_lines = []
        modifications = 0
        
        for line in lines:
            # 改行を除いた長さをチェック
            line_content = line.rstrip('\n')
            
            if len(line_content) > MAX_LINE_LENGTH:
                # コメント行は分割しない
                if line_content.strip().startswith('#'):
                    modified_lines.append(line)
                    continue
                
                # インデントを保持
                indent_match = re.match(r'^(\s*)', line_content)
                indent = indent_match.group(1) if indent_match else ''
                
                # 文字列の分割を試みる
                split_lines = split_long_string(line_content, MAX_LINE_LENGTH, indent)
                if len(split_lines) > 1:
                    for split_line in split_lines:
                        modified_lines.append(split_line + '\n')
                    modifications += 1
                    continue
                
                # 関数呼び出しの分割を試みる
                split_lines = split_function_call(line_content, MAX_LINE_LENGTH, indent)
                if len(split_lines) > 1:
                    for split_line in split_lines:
                        modified_lines.append(split_line + '\n')
                    modifications += 1
                    continue
                
                # それ以外はそのまま
                modified_lines.append(line)
            else:
                modified_lines.append(line)
        
        # ファイルに書き込み
        if modifications > 0 and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(modified_lines)
        
        return modifications
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return 0


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="Fix long lines in Python files")
    parser.add_argument("paths", nargs="+", help="Files or directories to process")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # ファイル収集
    files_to_process = []
    for path_str in args.paths:
        path = Path(path_str)
        if path.is_file() and path.suffix == '.py':
            files_to_process.append(path)
        elif path.is_dir():
            files_to_process.extend(path.rglob('*.py'))
    
    # 処理実行
    total_modifications = 0
    modified_files = 0
    
    for file_path in files_to_process:
        # venv等を除外
        if any(p in str(file_path) for p in ['venv', '__pycache__', '.git']):
            continue
        
        modifications = fix_long_lines_in_file(file_path, dry_run=args.dry_run)
        if modifications > 0:
            if args.verbose or args.dry_run:
                print(f"{file_path}: {modifications} long lines {'would be' if args.dry_run else 'were'} fixed")
            total_modifications += modifications
            modified_files += 1
    
    print(f"\nSummary: {total_modifications} long lines in {modified_files} files {'would be' if args.dry_run else 'were'} fixed")


if __name__ == "__main__":
    main()