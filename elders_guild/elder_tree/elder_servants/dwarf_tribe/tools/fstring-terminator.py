#!/usr/bin/env python3
"""
F-String Terminator - f-string専用修正システム
🎯 19件のf-stringエラーを完全撲滅
"""
import os
import re
import ast
from pathlib import Path

def get_fstring_errors():
    pass


"""f-stringエラーを取得"""
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        ast.parse(f.read())
                except SyntaxError as e:
                    msg = e.msg.lower()
                    if 'f-string' in msg or 'unterminated' in msg:
                        errors.append({
                            'file': file_path,
                            'line': e.lineno,
                            'msg': e.msg,
                            'text': e.text.strip() if e.text else '',
                            'filename': os.path.basename(file_path)
                        })
                except Exception:
                    pass
    return errors

def fix_fstring_error(file_path: str) -> bool:
    """f-stringエラー修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # パターン1: 重複f prefix
        content = re.sub(r'f"([^"]*)"', r'f"\1"', content)
        content = re.sub(r"f'f'([^']*)'", r"f'\1'", content)
        
        # パターン2: 未終了f-string（行末）
        content = re.sub(r'f"([^"]*?)$', r'f"\1"', content, flags=re.MULTILINE)
        content = re.sub(r"f'([^']*?)$", r"f'\1'", content, flags=re.MULTILINE)
        
        # パターン3: ネストした引用符問題
        content = re.sub(r'f"([^"]*?)"([^"]*?)"([^"]*?)"', r'f"\1\2\3"', content)
        
        # パターン4: 改行を含む未終了f-string
        content = re.sub(r'f"""([^"]*?)(?<!")$', r'f"""\1"""', content, flags=re.MULTILINE | re.DOTALL)
        
        # パターン5: エスケープ問題
        content = re.sub(r'f"([^"]*?)\\([^"]*?)"', r'f"\1\\\\\2"', content)
        
        # パターン6: f-string内のformatting問題
        content = re.sub(r'f"([^{]*?)\{([^}]*?)\}([^"]*?)(?<!")$', r'f"\1{\2}\3"', content, flags=re.MULTILINE)
        
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

def main():
    pass

        """メイン実行""" {len(errors)}件")
    
    if not errors:
        print("✅ f-stringエラーなし！")
        return
    
    # エラーファイル一覧
    print(f"\n📋 修正対象:")
    for i, error in enumerate(errors):
        print(f"   {i+1:2d}. {error['filename']} (line {error['line']}) - {error['msg']}")
    
    # 修正実行
    print(f"\n🔧 f-stringエラー修正実行...")
    fixed_count = 0
    
    for error in errors:
        filename = error['filename']
        if fix_fstring_error(error['file']):
            print(f"✅ Fixed: {filename}")
            fixed_count += 1
        else:
            print(f"❌ Failed: {filename}")
    
    # 結果確認
    final_errors = get_fstring_errors()
    
    print("=" * 70)
    print(f"📊 F-String修正結果:")
    print(f"   修正前: {len(errors)}件")
    print(f"   修正成功: {fixed_count}件")
    print(f"   修正後: {len(final_errors)}件")
    
    if len(final_errors) == 0:
        print("\n🎉 f-stringエラー完全撲滅達成！")
    else:
        reduction = len(errors) - len(final_errors)
        reduction_rate = (reduction / max(1, len(errors))) * 100
        print(f"   削減率: {reduction_rate:0.1f}%")
        print(f"\n🎯 残存{len(final_errors)}件への継続対応が必要")

if __name__ == "__main__":
    main()