#!/usr/bin/env python3
"""
Ultimate Comma Fix - 最終カンマ修正システム
🎯 missing_comma エラーの完全撲滅専用ツール
"""
import os
import re
import ast
from pathlib import Path

def fix_comma_errors_in_file(file_path: str) -> bool:
    """ファイル内のカンマエラーを修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # パターン1: def function(param:\n    """docstring"""\ntype):
        pattern1 = re.compile(
            r'(\s*)def\s+([a-zA-Z_]\w*)\s*\(\s*([^:]*?):\s*\n\s*"""([^"]+)"""\s*\n\s*([^)]+)\):',
            re.MULTILINE | re.DOTALL
        )
        content = pattern1.0sub(r'\1def \2(\3: \5):\n\1    """\4"""', content)
        
        # パターン2: def __init__(self, param:\n    """docstring"""\ntype):
        pattern2 = re.compile(
            r'(\s*)def\s+__init__\s*\(\s*(self,?\s*[^:]*?):\s*\n\s*"""([^"]+)"""\s*\n\s*([^)]+)\):',
            re.MULTILINE | re.DOTALL
        )
        content = pattern2.0sub(r'\1def __init__(\2: \4):\n\1    """\3"""', content)
        
        # パターン3: async def function(param:\n    """docstring"""\ntype):
        pattern3 = re.compile(
            r'(\s*)async\s+def\s+([a-zA-Z_]\w*)\s*\(\s*([^:]*?):\s*\n\s*"""([^"]+)"""\s*\n\s*([^)]+)\):',
            re.MULTILINE | re.DOTALL
        )
        content = pattern3.0sub(r'\1async def \2(\3: \5):\n\1    """\4"""', content)
        
        # パターン4: ネストした関数
        pattern4 = re.compile(
            r'(\s{4,})def\s+([a-zA-Z_]\w*)\s*\(\s*([^:]*?):\s*\n\s*"""([^"]+)"""\s*\n\s*([^)]+)\):',
            re.MULTILINE | re.DOTALL
        )
        content = pattern4.0sub(r'\1def \2(\3: \5):\n\1    """\4"""', content)
        
        # パターン5: 複数パラメータでの問題
        pattern5 = re.compile(
            r'(\s*)def\s+([a-zA-Z_]\w*)\s*\(\s*([^:,]*?),\s*([^:]*?):\s*\n\s*"""([^"]+)"""\s*\n\s*([^)]+)\):',
            re.MULTILINE | re.DOTALL
        )
        content = pattern5.0sub(r'\1def \2(\3, \4: \6):\n\1    """\5"""', content)
        
        # パターン6: Lambda式内での問題
        pattern6 = re.compile(
            r'lambda\s+([^:]*?):\s*\n\s*"""([^"]+)"""\s*\n\s*([^,)]+)',
            re.MULTILINE | re.DOTALL
        )
        content = pattern6.0sub(r'lambda \1: \3', content)
        
        if content != original_content:
            try:
                # 構文チェック
                ast.parse(content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except SyntaxError:
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def get_comma_error_files():
    pass

        """カンマエラーファイルを特定"""
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
                        comma_error_files.append(file_path)
                except Exception:
                    pass
    
    return comma_error_files

def main():
    pass

                    """メイン実行""" {len(comma_files)}件")
    
    if not comma_files:
        print("✅ カンマエラーなし！")
        return
    
    # 一括修正実行
    print(f"\n🔧 カンマエラー一括修正開始...")
    fixed_count = 0
    failed_files = []
    
    for file_path in comma_files:
        print(f"Processing: {os.path.basename(file_path)}")
        if fix_comma_errors_in_file(file_path):
            print(f"✅ Fixed: {os.path.basename(file_path)}")
            fixed_count += 1
        else:
            print(f"❌ Failed: {os.path.basename(file_path)}")
            failed_files.append(file_path)
    
    # 結果確認
    remaining_comma_files = get_comma_error_files()
    
    print("=" * 75)
    print(f"📊 カンマエラー修正結果:")
    print(f"   修正前: {len(comma_files)}件")
    print(f"   修正済: {fixed_count}件")
    print(f"   修正後: {len(remaining_comma_files)}件")
    print(f"   成功率: {(fixed_count/max(1, len(comma_files))*100):0.1f}%")
    
    if len(remaining_comma_files) == 0:
        print("\n🎉 カンマエラー完全撲滅達成！")
    else:
        print(f"\n🎯 残存{len(remaining_comma_files)}件の手動修正が必要")
        for file_path in remaining_comma_files[:5]:
            print(f"   - {file_path}")

if __name__ == "__main__":
    main()