#!/usr/bin/env python3
"""
FINAL 17 KILLER - 残存17エラー完全殲滅
個別ファイルを直接修正
"""

import re
from pathlib import Path

def fix_file(filepath, line_num, error_type):
    """個別ファイルを修正"""
    path = Path(f'/home/aicompany/ai_co/libs/{filepath}')
    if not path.exists():
        print(f"❌ {filepath} が見つかりません")
        return False
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed = False
        
        if error_type == "closing parenthesis":
            # 括弧不一致の修正
            # 該当行周辺をチェック
            for i in range(max(0, line_num - 5), min(len(lines), line_num + 5)):
                line = lines[i]
                # f-string内の不正な括弧を修正
                if 'f"' in line or "f'" in line:
                    # f"{var}" "{next}" -> f"{var} {next}"
                    new_line = re.sub(r'"\s*\{([^}]*)\}\s*"', r' {\1} ', line)
                    if new_line != line:
                        lines[i] = new_line
                        fixed = True
                
                # 辞書内の不正な括弧
                if '{' in line and '}' in line:
                    # 文字列内でない}を削除
                    if line.count('}') > line.count('{'):
                        # 最後の}を削除してみる
                        if line.rstrip().endswith('}') and '"' not in line[line.rfind('}'):]:
                            lines[i] = line[:line.rfind('}')] + line[line.rfind('}')+1:]
                            fixed = True
        
        elif error_type == "expected ':'":
            # コロン不足の修正
            idx = line_num - 1
            if idx < len(lines):
                line = lines[idx]
                # def method()メソッド内容 -> def method():\n    メソッド内容
                if 'def ' in line and not line.rstrip().endswith(':'):
                    # 関数定義とその内容が同じ行にある場合
                    match = re.match(r'^(\s*)(def\s+\w+\s*\([^)]*\)(?:\s*->\s*[^:]+)?)(.*?)$', line)
                    if match:
                        indent = match.group(1)
                        func_def = match.group(2)
                        remainder = match.group(3)
                        if remainder and not remainder.strip().startswith(':'):
                            lines[idx] = f"{indent}{func_def}:\n"
                            if remainder.strip():
                                lines.insert(idx + 1, f"{indent}    {remainder.strip()}\n")
                            fixed = True
                        elif not remainder:
                            lines[idx] = f"{indent}{func_def}:\n"
                            fixed = True
        
        elif error_type == "unterminated string literal":
            # 文字列リテラル未終了の修正
            idx = line_num - 1
            if idx < len(lines):
                line = lines[idx]
                # 未終了の"""を探す
                if '"""' in line and line.count('"""') % 2 == 1:
                    lines[idx] = line.rstrip() + '"""\n'
                    fixed = True
                # 未終了の"を探す
                elif line.count('"') % 2 == 1:
                    lines[idx] = line.rstrip() + '"\n'
                    fixed = True
        
        if fixed:
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True
        
        return False
            
    except Exception as e:
        print(f"❌ {filepath} 処理エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("🔥 FINAL 17 KILLER - 残存17エラー完全殲滅作戦")
    
    # エラーリスト
    errors = [
        ("knowledge_index_optimizer.py", 754, "closing parenthesis"),
        ("elder_flow_final_evolution.py", 95, "unterminated string literal"),
        ("grimoire_elder_flow_optimization.py", 308, "closing parenthesis"),
        ("demand_predictor.py", 992, "closing parenthesis"),
        ("elder_council_review_system.py", 486, "closing parenthesis"),
        ("retry_orchestrator.py", 573, "closing parenthesis"),
        ("elder_servant_a2a_optimization.py", 732, "closing parenthesis"),
        ("elder_council_summoner.py", 1555, "closing parenthesis"),
        ("learning_optimizer.py", 1128, "closing parenthesis"),
        ("enhanced_error_handling.py", 172, "expected ':'"),
        ("elder_cast_enhanced.py", 2, "unterminated string literal"),
        ("resource_allocation_optimizer.py", 599, "closing parenthesis"),
        ("elders_guild_precision_improvement.py", 762, "expected ':'"),
        ("elder_flow_violation_resolver.py", 226, "expected ':'"),
        ("advanced_search_analytics_platform.py", 725, "closing parenthesis"),
    ]
    
    fixed_count = 0
    
    for filepath, line_num, error_type in errors:
        print(f"\n🔧 修正中: {filepath}:{line_num} - {error_type}")
        if fix_file(filepath, line_num, error_type):
            print(f"✅ 修正成功")
            fixed_count += 1
        else:
            print(f"❌ 修正失敗")
    
    print(f"\n📊 結果: {fixed_count}/17 修正完了")
    
    # 最終確認
    import subprocess
    result = subprocess.run(
        ['python3', 'scripts/quality/quick-error-check.py'],
        capture_output=True,
        text=True
    )
    
    remaining = len([line for line in result.stdout.split('\n') if line.strip()])
    print(f"\n🎯 残存エラー: {remaining}")
    
    if remaining == 0:
        print("\n🎉 完全勝利！すべてのシンタックスエラーが殲滅されました！")
    else:
        print(f"\n⚔️  残り {remaining} エラー...")

if __name__ == "__main__":
    main()