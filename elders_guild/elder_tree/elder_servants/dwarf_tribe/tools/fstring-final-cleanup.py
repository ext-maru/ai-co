#!/usr/bin/env python3
"""
F-String Final Cleanup - 残りf-stringエラー完全撲滅
"""
import ast
import os

def fstring_final_cleanup():
    pass


"""残り5件のf-stringエラーを特定・修正"""
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        ast.parse(f.read())
                except SyntaxError as e:
                    if 'f-string' in e.msg.lower():
                        fstring_files.append({
                            'path': file_path,
                            'file': os.path.basename(file_path),
                            'line': e.lineno,
                            'msg': e.msg
                        })
    
    print(f"🎯 残りf-stringエラー: {len(fstring_files)}件")
    
    for i, file_info in enumerate(fstring_files):
        print(f"   {i+1:2d}. {file_info['file']}:{file_info['line']} - {file_info['msg'][:40]}...")
    
    return fstring_files

if __name__ == "__main__":
    fstring_final_cleanup()