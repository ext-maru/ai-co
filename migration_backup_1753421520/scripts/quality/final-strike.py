#!/usr/bin/env python3
"""最終11件エラー手動修正スクリプト"""

import re
from pathlib import Path

# エラーファイルと行番号の手動リスト
errors = [
    ("elder_flow_servant_executor_real.py", 1782),
    ("apscheduler_integration.py", 344), 
    ("next_gen_ai_integration.py", 842),
    ("connection_pool_optimizer.py", 184),
    ("monitoring_optimization_system.py", 118),
    ("next_gen_worker.py", 77),
    ("database_manager.py", 41),
    ("dynamic_parallel_processor.py", 82),
    ("elder_council_auto_decision.py", 586),
    ("optimized_auto_issue_processor.py", 57),
    ("next_generation_rag_strategy.py", 137)
]

def fix_file(filename, line_num):
    """ファイルの型アノテーション修正"""
    try:
        path = Path(f'/home/aicompany/ai_co/libs/{filename}')
        if not path.exists():
            print(f"❌ {filename} - ファイルが見つからない")
            return False
            
        lines = path.read_text().split('\n')
        if line_num >= len(lines):
            print(f"❌ {filename}:{line_num} - 行番号が範囲外")
            return False
            
        # パターン検索・修正
        for i in range(max(0, line_num - 3), min(len(lines), line_num + 3)):
            line = lines[i].strip()
            if (line.endswith(':') and 
                i + 1 < len(lines) and 
                lines[i + 1].strip().startswith('"""') and
                i + 2 < len(lines) and
                lines[i + 2].strip().endswith('):')):
                
                # 修正実行
                method_line = lines[i][:-1]  # 末尾の:削除
                docstring = lines[i + 1].strip()
                param_line = lines[i + 2].strip()[:-2]  # 末尾の):削除
                
                lines[i] = f"{method_line} {param_line}):"
                lines[i + 1] = f"        {docstring}"
                lines[i + 2] = ""
                
                path.write_text('\n'.join(lines))
                print(f"✅ {filename}:{line_num}")
                return True
                
    except Exception as e:
        print(f"❌ {filename}:{line_num} - {e}")
    return False

def main():
    """メイン処理"""
    print("🔥 最終11件エラー修正開始")
    fixed = 0
    
    for filename, line_num in errors:
        if fix_file(filename, line_num):
            fixed += 1
    
    print(f"🎯 修正完了: {fixed}/{len(errors)}件")

if __name__ == "__main__":
    main()