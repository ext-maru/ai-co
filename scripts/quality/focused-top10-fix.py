#!/usr/bin/env python3
"""
Focused Top 10 Fix - 上位10ファイル集中修正
🎯 最も問題のあるファイルを特定し集中修正
"""
import os
import re
import ast
from pathlib import Path

def get_problem_files_prioritized():


"""問題ファイルを優先度順で取得"""
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content)
                except SyntaxError as e:
                    if 'comma' in e.msg.lower():
                        problem_files.append((file_path, e.lineno, e.msg))
                except Exception:
                    pass
    
    # ファイル名でソート（重要度考慮）
    priority_keywords = ['elder_flow', 'task_sage', 'knowledge', 'incident']
    
    def get_priority(filepath):
        filename = os.path.basename(filepath).lower()
        for i, keyword in enumerate(priority_keywords):
            if keyword in filename:
                return i
        return len(priority_keywords)
    
    problem_files.sort(key=lambda x: get_priority(x[0]))
    return problem_files[:10]  # Top 10

def smart_fix_comma_error(file_path: str) -> bool:
    """スマートなカンマエラー修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        content = ''.join(lines)
        original_content = content
        
        # パターン1: def func(param:\n    """doc"""\ntype):
        pattern1 = re.compile(
            r'(\s*)(def|async def)\s+([a-zA-Z_]\w*)\s*\(\s*([^)]*?):\s*\n(\s*)"""([^"]+?)"""\s*\n\s*([^)]+?)\):',
            re.MULTILINE | re.DOTALL
        )
        
        def fix_match1(match):
            indent, func_type, func_name, params, doc_indent, docstring, type_part = match.groups()
            return f'{indent}{func_type} {func_name}({params}: {type_part.strip()}):\n{doc_indent}"""{docstring}"""'
        
        content = pattern1.sub(fix_match1, content)
        
        # パターン2: __init__ specific
        pattern2 = re.compile(
            r'(\s*)def\s+__init__\s*\(\s*(self,?\s*[^)]*?):\s*\n(\s*)"""([^"]+?)"""\s*\n\s*([^)]+?)\):',
            re.MULTILINE | re.DOTALL
        )
        
        def fix_match2(match):
            indent, params, doc_indent, docstring, type_part = match.groups()
            return f'{indent}def __init__({params}: {type_part.strip()}):\n{doc_indent}"""{docstring}"""'
        
        content = pattern2.sub(fix_match2, content)
        
        # パターン3: 複数パラメータでの問題
        pattern3 = re.compile(
            r'(\s*)(def|async def)\s+([a-zA-Z_]\w*)\s*\(\s*([^:,]*?),\s*([^)]*?):\s*\n(\s*)"""([^"]+?)"""\s*\n\s*([^)]+?)\):',
            re.MULTILINE | re.DOTALL
        )
        
        def fix_match3(match):
            indent, func_type, func_name, param1, param2, doc_indent, docstring, type_part = match.groups()
            return f'{indent}{func_type} {func_name}({param1}, {param2}: {type_part.strip()}):\n{doc_indent}"""{docstring}"""'
        
        content = pattern3.sub(fix_match3, content)
        
        if content != original_content:
            try:
                ast.parse(content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except SyntaxError:
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():

        """メイン実行"""")
    for i, (file_path, line, msg) in enumerate(problem_files):
        print(f"   {i+1:2d}. {os.path.basename(file_path)} (line {line})")
    
    print(f"\n🔧 Focused repair execution...")
    fixed_count = 0
    
    for file_path, line, msg in problem_files:
        filename = os.path.basename(file_path)
        print(f"Processing: {filename}")
        
        if smart_fix_comma_error(file_path):
            print(f"✅ Fixed: {filename}")
            fixed_count += 1
        else:
            print(f"❌ Failed: {filename}")
    
    print("=" * 70)
    print(f"📊 Top 10 Focus Results:")
    print(f"   Fixed: {fixed_count}/10 files")
    print(f"   Success Rate: {(fixed_count/10*100):.1f}%")
    
    # 全体進捗確認
    remaining_comma_errors = 0
    for root, dirs, files in os.walk('./libs'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        ast.parse(f.read())
                except SyntaxError as e:
                    if 'comma' in e.msg.lower():
                        remaining_comma_errors += 1
                except Exception:
                    pass
    
    print(f"\n🎯 Overall Progress:")
    print(f"   Remaining comma errors: {remaining_comma_errors}")

if __name__ == "__main__":
    main()