#!/usr/bin/env python3
"""最終構文エラー一括修正スクリプト"""

import re
import subprocess
from pathlib import Path

def get_syntax_errors():
    """構文エラーファイルリストを取得"""
    result = subprocess.run(['python3', 'scripts/quality/quick-error-check.py'], 
                          capture_output=True, text=True)
    files = []
    for line in result.stdout.split('\n'):
        if '❌' in line and 'invalid syntax' in line:
            # パターン: ❌ filename.py:123 - error message
            match = re.search(r'❌\s+(\S+\.py):(\d+)\s+-', line)
            if match:
                file_name = match.group(1)
                line_num = int(match.group(2))
                files.append((file_name, line_num))
    return files

def fix_type_annotation_syntax(file_path, line_num):
    """型アノテーション構文修正"""
    try:
        path = Path(f'/home/aicompany/ai_co/libs/{file_path}')
        if not path.exists():
            return False
            
        lines = path.read_text().split('\n')
        if line_num >= len(lines):
            return False
            
        # パターン1: def method(param: の修正
        if line_num < len(lines) - 2:
            line1 = lines[line_num - 1].strip()
            line2 = lines[line_num].strip()
            line3 = lines[line_num + 1].strip()
            
            # 型アノテーション分離パターン
            if (line1.endswith(':') and 
                line2.startswith('"""') and line2.endswith('"""') and
                line3.endswith('):')):
                
                # 修正: パラメータ名と型を結合
                method_line = line1[:-1]  # 末尾の:を削除
                param_line = line3[:-2]  # 末尾の):を削除
                docstring = line2
                
                fixed_line = f"{method_line} {param_line}):"
                
                lines[line_num - 1] = fixed_line
                lines[line_num] = "        " + docstring
                lines[line_num + 1] = ""
                
                path.write_text('\n'.join(lines))
                return True
                
    except Exception as e:
        print(f"Error fixing {file_path}:{line_num} - {e}")
    return False

def main():
    """メイン処理"""
    errors = get_syntax_errors()
    print(f"修正対象: {len(errors)}件")
    
    fixed = 0
    for file_path, line_num in errors:
        if fix_type_annotation_syntax(file_path, line_num):
            fixed += 1
            print(f"✅ {file_path}:{line_num}")
        else:
            print(f"❌ {file_path}:{line_num} (修正失敗)")
    
    print(f"\n修正完了: {fixed}/{len(errors)}件")
    
    # 最終確認
    final_errors = get_syntax_errors()
    print(f"残りエラー: {len(final_errors)}件")

if __name__ == "__main__":
    main()