#!/usr/bin/env python3
"""
強化版コメント追加ツール
"""
import ast
import os
import sys
from typing import List, Tuple

def add_comments_to_file(file_path: str) -> Tuple[int, List[str]]:
    """ファイルにコメントを追加"""
    comments_added = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        modified = False
        new_lines = []
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # 複雑な条件文にコメント追加
            if 'if ' in line and ('and ' in line or 'or ' in line) and line.strip().endswith(':'):
                indent = len(line) - len(line.lstrip())
                comment = ' ' * indent + '    # Complex condition - consider breaking down\n'
                new_lines.append(comment)
                comments_added.append(f"Added comment for complex condition at line {i+1}")
                modified = True
            
            # ループにコメント追加
            elif 'for ' in line and line.strip().endswith(':') and 'in ' in line:
                if not any(lines[j].strip().startswith('#') for j in range(max(0, i-2), min(len(lines), i+3))):
                    indent = len(line) - len(line.lstrip())
                    comment = ' ' * indent + '    # Process each item in collection\n'
                    new_lines.append(comment)
                    comments_added.append(f"Added comment for loop at line {i+1}")
                    modified = True
            
            # Try-except块にコメント追加
            elif line.strip().startswith('except ') and line.strip().endswith(':'):
                if not any(lines[j].strip().startswith('#') for j in range(max(0, i-1), min(len(lines), i+2))):
                    indent = len(line) - len(line.lstrip())
                    comment = ' ' * indent + '    # Handle specific exception case\n'
                    new_lines.append(comment)
                    comments_added.append(f"Added comment for exception handling at line {i+1}")
                    modified = True
            
            # 大きなクラス定義にコメント追加
            elif line.strip().startswith('class ') and line.strip().endswith(':'):
                # 次の行がdocstringでない場合
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                    indent = len(line) - len(line.lstrip())
                    comment = ' ' * indent + '    # Main class implementation\n'
                    new_lines.append(comment)
                    comments_added.append(f"Added comment for class at line {i+1}")
                    modified = True
            
            # 重要な関数にコメント追加
            elif (line.strip().startswith('def ') or line.strip().startswith('async def ')) and line.strip().endswith(':'):
                if 'main' in line or 'execute' in line or 'process' in line or 'handle' in line:
                    if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                        indent = len(line) - len(line.lstrip())
                        comment = ' ' * indent + '    # Core functionality implementation\n'
                        new_lines.append(comment)
                        comments_added.append(f"Added comment for important function at line {i+1}")
                        modified = True
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return len(comments_added), comments_added
        
        return 0, []
        
    except Exception as e:
        return 0, [f"Error: {str(e)}"]

def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("Usage: add-comments-enhanced.py <file1> [file2] ...")
        sys.exit(1)
    
    total_comments = 0
    files_modified = 0
    
    for file_path in sys.argv[1:]:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        
        count, comments = add_comments_to_file(file_path)
        
        if count > 0:
            files_modified += 1
            total_comments += count
            print(f"  ✅ {file_path}: Added {count} comments")
        
    print(f"\n✅ Summary: {total_comments} comments in {files_modified} files were added")

if __name__ == "__main__":
    main()