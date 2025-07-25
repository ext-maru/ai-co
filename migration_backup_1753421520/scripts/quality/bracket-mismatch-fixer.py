#!/usr/bin/env python3
"""
BRACKET MISMATCH FIXER - 括弧不一致エラー専門修正
"""

import re
from pathlib import Path

# 対象ファイルと行番号
targets = [
    ("demand_predictor.py", 992),
    ("elder_council_review_system.py", 486),
    ("retry_orchestrator.py", 573),
    ("elder_servant_a2a_optimization.py", 732),
    ("elder_council_summoner.py", 1555),
    ("learning_optimizer.py", 1128),
    ("resource_allocation_optimizer.py", 599),
    ("advanced_search_analytics_platform.py", 725),
]

def fix_bracket_mismatch(filepath, line_num):
    """括弧不一致を修正"""
    path = Path(f'/home/aicompany/ai_co/libs/{filepath}')
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 該当行付近を確認
        idx = line_num - 1
        if idx < len(lines):
            line = lines[idx]
            
            # json.dumps の不完全な呼び出しを探す
            if 'json.dumps' in line:
                # json.dumps(data, indent} -> json.dumps(data, indent=2)}
                new_line = re.sub(r'json\.dumps\(([^,]+),\s*(\w+)\}', r'json.dumps(\1, \2=2)}', line)
                # json.dumps(data, ensure_ascii} -> json.dumps(data, ensure_ascii=False)}
                new_line = re.sub(r'json\.dumps\(([^,]+),\s*ensure_ascii\}', r'json.dumps(\1, ensure_ascii=False)}', new_line)
                
                if new_line != line:
                    lines[idx] = new_line
                    with open(path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    return True
            
            # f-string内の不正な括弧
            if 'f"' in line or "f'" in line:
                # f"{data" -> f"{data}"
                new_line = re.sub(r'(f"[^"]*)\}([^"]*)"', r'\1}\2"', line)
                # f"{data}" "next}" -> f"{data} next}"
                new_line = re.sub(r'"\s*"([^"]*)\}"', r' \1}"', new_line)
                
                if new_line != line:
                    lines[idx] = new_line
                    with open(path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    return True
                    
        return False
        
    except Exception as e:
        print(f"  エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("🔧 BRACKET MISMATCH FIXER - 括弧不一致修正")
    
    fixed_count = 0
    
    for filepath, line_num in targets:
        print(f"\n修正中: {filepath}:{line_num}")
        if fix_bracket_mismatch(filepath, line_num):
            print("  ✅ 修正成功")
            fixed_count += 1
        else:
            print("  ❌ 修正失敗")
    
    print(f"\n📊 結果: {fixed_count}/{len(targets)} 修正")

if __name__ == "__main__":
    main()