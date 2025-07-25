#!/usr/bin/env python3
"""
Quick syntax error fixer for common patterns
"""

import os
import re
import sys

def fix_common_syntax_errors(content):
    """最も一般的な構文エラーパターンを修正"""
    
    # 1. メソッド定義のコロン欠落
    content = re.sub(
        r'def\s+__init__\s*\(self\)([^:\n]+)\n(\s*)"""',
        r'def __init__(self):\n\2"""',
        content
    )
    
    # 2. 連続したコロン
    content = re.sub(r':\s*:', ':', content)
    
    # 3. def行の最後の不正な文字
    content = re.sub(
        r'def\s+(\w+)\s*\(([^)]*)\)\s*([^:\n]+)\n',
        r'def \1(\2):\n',
        content
    )
    
    # 4. initメソッドの特殊ケース  
    content = re.sub(
        r'def\s+__init__\s*\(self\)(\w+)',
        r'def __init__(self):\n    """\1メソッド"""',
        content
    )
    
    # 5. 関数定義の後の誤った文字列
    content = re.sub(
        r'def\s+(\w+)\s*\(self\)(\w+)\s*\n(\s*)"""',
        r'def \1(self):\n\3"""\2メソッド\n\3',
        content
    )
    
    # 6. initialize メソッドの特殊なケース
    content = re.sub(
        r'def initialize\(self\)self\.logger',
        r'def initialize(self):\n        self.logger',
        content
    )
    
    # 7. 関数定義とdocstringの間の誤った配置
    content = re.sub(
        r'def\s+(\w+)\s*\(([^)]*)\)def\s+',
        r'def \1(\2):\n        """メソッド"""\n        \n    def ',
        content
    )
    
    return content

def process_file(filepath):
    """ファイルを処理"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = fix_common_syntax_errors(content)
        
        if content != new_content:
            # バックアップ作成
            backup_path = f"{filepath}.bak"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 修正内容を書き込み
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            # 構文チェック
            try:
                compile(new_content, filepath, 'exec')
                os.remove(backup_path)  # 成功したらバックアップ削除
                return True
            except SyntaxError:
                # 構文エラーがある場合は復元
                with open(backup_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                os.remove(backup_path)
                return False
                
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False
    
    return False

def main():
    """メイン処理"""
    # 優先的に修正するファイル
    priority_files = [
        'libs/knowledge_consolidator.py',
        'libs/elder_scheduled_tasks.py', 
        'libs/ai_test_generator.py',
        'libs/auto_adaptation_engine.py',
        'libs/intelligent_test_generator.py',
        'libs/elder_servants/integrations/production/health_check.py',
        'libs/elder_servants/hybrid/hybrid_elder_servants.py',
        'libs/mcp_servers/filesystem_server.py',
        'libs/ancient_elder/tdd_guardian.py',
        'libs/mcp_wrapper/executor_server.py'
    ]
    
    fixed = 0
    failed = 0
    
    print("🔧 Quick Syntax Fixer")
    print("=" * 50)
    
    for filepath in priority_files:
        if os.path.exists(filepath):
            print(f"Processing: {filepath}", end="... ")
            if process_file(filepath):
                print("✅ Fixed")
                fixed += 1
            else:
                print("❌ Failed")
                failed += 1
        else:
            print(f"Skipping: {filepath} (not found)")
            
    print(f"\n📊 Results:")
    print(f"  - Fixed: {fixed}")
    print(f"  - Failed: {failed}")
    
    # libs内の他のファイルも処理
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        print("\n🔍 Processing all files in libs/...")
        for root, dirs, files in os.walk('libs'):
            if any(skip in root for skip in ['venv', 'site-packages', '.git', '__pycache__']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    if filepath not in priority_files:
                        if process_file(filepath):
                            fixed += 1
                            print(f"  ✅ {filepath}")
                            
        print(f"\n📊 Final Results:")
        print(f"  - Total Fixed: {fixed}")

if __name__ == '__main__':
    main()