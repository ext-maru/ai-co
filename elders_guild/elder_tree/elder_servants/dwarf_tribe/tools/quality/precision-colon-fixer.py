#!/usr/bin/env python3
"""
Precision Colon Fixer - 精密コロンエラー修正スクリプト
"""

import re
import ast
from pathlib import Path

def fix_single_file_colon_errors(file_path: Path):
    """単一ファイルのコロンエラーを精密修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = 0
        
        # AST Parse して syntax errorを検出
        try:
            ast.parse(content)
            return 0  # No syntax errors
        except SyntaxError as e:
            if 'expected' in e.msg and ':' in e.msg:
                # コロン関連エラーの場合のみ修正
                pass
            else:
                return 0  # 他の種類のエラーは無視
        
        lines = content.split('\n')
        modified_lines = []
        
        for i, line in enumerate(lines):
            original_line = line
            
            # Pattern 1: Function definition missing colon
            if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*$', line):
                if not line.rstrip().endswith(':'):
                    line = line.rstrip() + ':'
                    fixes_applied += 1
            
            # Pattern 2: Class definition missing colon
            elif re.match(r'^\s*class\s+\w+(?:\([^)]*\))?\s*$', line):
                if not line.rstrip().endswith(':'):
                    line = line.rstrip() + ':'
                    fixes_applied += 1
            
            # Pattern 3: if/elif/else/while/for missing colon
            elif re.match(r'^\s*(if|elif|else|while|for|with|try|except|finally)\s*.*[^:]$', line):
                if not line.rstrip().endswith(':'):
                    line = line.rstrip() + ':'
                    fixes_applied += 1
                    
            modified_lines.append(line)
        
        if fixes_applied > 0:
            new_content = '\n'.join(modified_lines)
            # Validate the fix
            try:
                ast.parse(new_content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return fixes_applied
            except SyntaxError:
                # Fix didn't work, revert
                return 0
        
        return 0
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return 0

def main():
    """メイン処理"""
    project_root = Path(__file__).parent.parent.parent
    
    # 特定の重要ファイルをターゲット
    target_files = [
        "commands/ai_shell.py",
        "commands/ai_dlq.py", 
        "commands/ai_worker_comm.py",
        "elders_guild_integration_script.py"
    ]
    
    total_fixes = 0
    files_fixed = 0
    
    for target_file in target_files:
        file_path = project_root / target_file
        if file_path.exists():
            fixes = fix_single_file_colon_errors(file_path)
            if fixes > 0:
                total_fixes += fixes
                files_fixed += 1
                print(f"🔧 Fixed {file_path.relative_to(project_root)}: {fixes} fixes")
    
    print(f"\n✅ Precision Colon Fixer 完了!")
    print(f"   修正ファイル数: {files_fixed}")
    print(f"   適用修正数: {total_fixes}")

if __name__ == "__main__":
    main()