#!/usr/bin/env python3
"""
Precision Manual Fix - 精密手動修正システム
🎯 残存する複雑なカンマエラーを高精度で修正
"""
import os
import re
import ast
from pathlib import Path

def get_remaining_comma_errors():


"""残存カンマエラーを取得"""
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        ast.parse(f.read())
                except SyntaxError as e:
                    if 'comma' in e.msg.lower():
                        errors.append({
                            'file': file_path,
                            'line': e.lineno,
                            'msg': e.msg,
                            'filename': os.path.basename(file_path)
                        })
                except Exception:
                    pass
    return errors

def precision_fix_file(file_path: str) -> bool:
    """精密修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        filename = os.path.basename(file_path)
        
        # ファイル別特化修正
        if 'incident_sage' in filename:
            content = fix_incident_sage_pattern(content)
        elif 'elder_tree_vector' in filename:
            content = fix_elder_tree_pattern(content)
        elif 'elder_council' in filename:
            content = fix_elder_council_pattern(content)
        elif 'comprehensive_grimoire' in filename:
            content = fix_grimoire_pattern(content)
        elif 'database_manager' in filename:
            content = fix_database_pattern(content)
        else:
            # 汎用パターン
            content = fix_generic_comma_pattern(content)
        
        if content != original:
            try:
                ast.parse(content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except SyntaxError:
                return False
        
        return False
        
    except Exception:
        return False

def fix_incident_sage_pattern(content: str) -> str:
    """Incident Sage特化修正"""
    # 特殊なf-string込みのパターン
    patterns = [
        (r'def\s+([a-zA-Z_]\w*)\s*\(\s*([^)]*?):\s*\n\s*"""([^"]*?)"""\s*\n\s*([^)]+?)\):', 
         r'def \1(\2: \4):\n        """\3"""'),
        (r'async def\s+([a-zA-Z_]\w*)\s*\(\s*([^)]*?):\s*\n\s*"""([^"]*?)"""\s*\n\s*([^)]+?)\):', 
         r'async def \1(\2: \4):\n        """\3"""'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    return content

def fix_elder_tree_pattern(content: str) -> str:
    """Elder Tree特化修正"""
    # ネットワーク関連の複雑な型
    pattern = r'def\s+([a-zA-Z_]\w*)\s*\(\s*(self,?\s*[^)]*?):\s*\n\s*"""([^"]*?)"""\s*\n\s*([^)]+?)\):'
    replacement = r'def \1(\2: \4):\n        """\3"""'
    
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    return content

def fix_elder_council_pattern(content: str) -> str:
    """Elder Council特化修正"""
    # 複雑なDict型アノテーション
    patterns = [
        (r'def\s+([a-zA-Z_]\w*)\s*\(\s*(self,?\s*[^)]*?):\s*\n\s*"""([^"]*?)"""\s*\n\s*(Dict\[[^\]]+\])\s*=\s*([^)]+?)\):', 
         r'def \1(\2: \4 = \5):\n        """\3"""'),
        (r'def\s+([a-zA-Z_]\w*)\s*\(\s*(self,?\s*[^)]*?):\s*\n\s*"""([^"]*?)"""\s*\n\s*([^)]+?)\):', 
         r'def \1(\2: \4):\n        """\3"""'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    return content

def fix_grimoire_pattern(content: str) -> str:
    """Grimoire特化修正"""
    # データベース関連の複雑なパターン
    pattern = r'def\s+([a-zA-Z_]\w*)\s*\(\s*(self,?\s*[^)]*?):\s*\n\s*"""([^"]*?)"""\s*\n\s*(Optional\[[^\]]+\])\s*=\s*([^)]+?)\):'
    replacement = r'def \1(\2: \4 = \5):\n        """\3"""'
    
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    return content

def fix_database_pattern(content: str) -> str:
    """Database特化修正"""
    # データベース接続関連
    patterns = [
        (r'def\s+([a-zA-Z_]\w*)\s*\(\s*(self,?\s*[^)]*?):\s*\n\s*"""([^"]*?)"""\s*\n\s*(str)\s*=\s*([^)]+?)\):', 
         r'def \1(\2: \4 = \5):\n        """\3"""'),
        (r'def\s+([a-zA-Z_]\w*)\s*\(\s*(self,?\s*[^)]*?):\s*\n\s*"""([^"]*?)"""\s*\n\s*([^)]+?)\):', 
         r'def \1(\2: \4):\n        """\3"""'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    return content

def fix_generic_comma_pattern(content: str) -> str:
    """汎用カンマパターン修正"""
    patterns = [
        # 基本パターン
        (r'(\s*)def\s+([a-zA-Z_]\w*)\s*\(\s*([^)]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*([^)]+?)\):', 
         r'\1def \2(\3: \6):\n\4"""\5"""'),
        
        # asyncパターン
        (r'(\s*)async def\s+([a-zA-Z_]\w*)\s*\(\s*([^)]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*([^)]+?)\):', 
         r'\1async def \2(\3: \6):\n\4"""\5"""'),
        
        # __init__特化
        (r'(\s*)def\s+__init__\s*\(\s*(self[^)]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*([^)]+?)\):', 
         r'\1def __init__(\2: \5):\n\3"""\4"""'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    return content

def main():

        """メイン実行""" {len(errors)}件")
    
    if not errors:
        print("✅ カンマエラー完全撲滅達成！")
        return
    
    # 上位10件表示
    print(f"\n📋 修正対象ファイル:")
    for i, error in enumerate(errors[:10]):
        print(f"   {i+1:2d}. {error['filename']} (line {error['line']})")
    
    # 精密修正実行
    print(f"\n🔧 精密修正実行...")
    fixed_count = 0
    
    for error in errors:
        filename = error['filename']
        if precision_fix_file(error['file']):
            print(f"✅ Fixed: {filename}")
            fixed_count += 1
        else:
            print(f"❌ Failed: {filename}")
    
    # 結果確認
    final_errors = get_remaining_comma_errors()
    
    print("=" * 70)
    print(f"📊 精密修正結果:")
    print(f"   修正前: {len(errors)}件")
    print(f"   修正成功: {fixed_count}件")
    print(f"   修正後: {len(final_errors)}件")
    reduction = len(errors) - len(final_errors)
    reduction_rate = (reduction / max(1, len(errors))) * 100
    print(f"   削減率: {reduction_rate:.1f}%")
    
    if len(final_errors) == 0:
        print("\n🎉 カンマエラー完全撲滅達成！")
    else:
        print(f"\n🎯 {len(final_errors)}件が残存 - 継続対応中...")

if __name__ == "__main__":
    main()