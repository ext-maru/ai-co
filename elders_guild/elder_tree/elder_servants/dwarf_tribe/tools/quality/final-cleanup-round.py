#!/usr/bin/env python3
"""最終クリーンアップラウンド - 残存エラー完全撃破"""

def fix_elders_guild_integration():
    """elders_guild_integration_script.py再修正"""
    filepath = 'elders_guild_integration_script.py'
    
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Line 56付近の構文エラーを修正
        if len(lines) > 56:
            # docstringが関数外にある問題を修正
            if '"""' in lines[56] and 'テストファイルのimport修正' in lines[56]:
                # docstringを関数内に移動
                docstring = lines[56]
                lines[54] = lines[54].rstrip() + '\n'
                lines[55] = '    ' + docstring
                lines[56] = '    # ' + lines[57].strip() + '\n' if len(lines) > 57 else ''
        
        with open(filepath, 'w') as f:
            f.writelines(lines)
        
        print(f'✅ {filepath} 再修正完了')
    except Exception as e:
        print(f'❌ {filepath} エラー: {e}')

def fix_python_implement_ai_send():
    """scripts/python_implement_ai_send.py再修正"""
    filepath = 'scripts/python_implement_ai_send.py'
    
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Line 95の文字列リテラル問題を修正
        if len(lines) > 94:
            # f-string問題を修正
            lines[94] = '                                    f"    - {task_type:<10} : {info.get(\'description\', \'N/A\')} (優先度: "\n'
            lines[95] = '                                    f"{info.get(\'default_priority\', 5)})"\n'
        
        with open(filepath, 'w') as f:
            f.writelines(lines)
        
        print(f'✅ {filepath} 再修正完了')
    except Exception as e:
        print(f'❌ {filepath} エラー: {e}')

def fix_fix_all_syntax_errors():
    """scripts/fix_all_syntax_errors.py再修正"""
    filepath = 'scripts/fix_all_syntax_errors.py'
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # マルチライン文字列の問題を修正
        content = content.replace(
            '"return None\\n    def set("\n            self,\n            key,\n            value): return True',
            '"return None\\n    def set(self, key, value): return True'
        )
        
        content = content.replace(
            '"class Redis:\\n    def __init__(\n        self,\n        *args,\n        **kwargs)',
            '"class Redis:\\n    def __init__(self, *args, **kwargs)'
        )
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f'✅ {filepath} 再修正完了')
    except Exception as e:
        print(f'❌ {filepath} エラー: {e}')

def fix_show_command_results():
    """scripts/show_command_results.py再修正"""
    filepath = 'scripts/show_command_results.py'
    
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Line 69-72の構文エラーを修正
        if len(lines) > 72:
            lines[68] = '                        if not any(keyword in line for keyword in [\n'
            lines[69] = '                            "✅ 動作中",\n'
            lines[70] = '                            "❌ 停止中",\n'
            lines[71] = '                        ]):\n'
            lines[72] = '                            continue\n'
        
        with open(filepath, 'w') as f:
            f.writelines(lines)
        
        print(f'✅ {filepath} 再修正完了')
    except Exception as e:
        print(f'❌ {filepath} エラー: {e}')

def main():
    print("🔥 最終クリーンアップラウンド開始！")
    print("=" * 50)
    
    fix_elders_guild_integration()
    fix_python_implement_ai_send()
    fix_fix_all_syntax_errors()
    fix_show_command_results()
    
    print("\n✨ 最終クリーンアップ完了！")

if __name__ == '__main__':
    main()