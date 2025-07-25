#!/usr/bin/env python3
"""
PARENTHESIS MISMATCH FIXER
括弧の不一致エラーを修正
"""

import ast
import re
from pathlib import Path

def fix_parenthesis_mismatch(content):
    """括弧の不一致を修正"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # パターン1: f-string内の不正な括弧
        # f"{var}" "{next}" -> f"{var} {next}"
        line = re.sub(r'"\s*\{([^}]*)\}\s*"', r' {\1} ', line)
        
        # パターン2: 辞書定義の修正
        # {"key": value"} -> {"key": "value"}
        line = re.sub(r'\{([^:]+):\s*([^"}]+)"\}', r'{\1: "\2"}', line)
        
        # パターン3: f-string内の余分な引用符
        # f"text" "more" -> f"text more"
        if 'f"' in line or "f'" in line:
            line = re.sub(r'(f"[^"]*")\s*"([^"]*")', r'\1 \2', line)
            line = re.sub(r"(f'[^']*')\s*'([^']*')", r'\1 \2', line)
        
        # パターン4: 括弧の不一致を検出して修正
        open_count = line.count('(') + line.count('[') + line.count('{')
        close_count = line.count(')') + line.count(']') + line.count('}')
        
        if open_count < close_count:
            # 閉じ括弧が多い場合
            # 最後の不要な閉じ括弧を削除
            if line.rstrip().endswith('}') and '{' not in line:
                line = line.rstrip()[:-1]
            elif line.rstrip().endswith(')') and '(' not in line:
                line = line.rstrip()[:-1]
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def main():
    """メイン処理"""
    print("🔧 PARENTHESIS MISMATCH FIXER - 括弧不一致修正")
    
    project_root = Path('/home/aicompany/ai_co')
    
    # 対象ファイル
    target_files = [
        'libs/knowledge_index_optimizer.py',
        'libs/grimoire_elder_flow_optimization.py',
        'libs/demand_predictor.py',
        'libs/elder_council_review_system.py',
        'libs/retry_orchestrator.py',
        'libs/elder_servant_a2a_optimization.py',
        'libs/elder_council_summoner.py',
        'libs/resource_allocation_optimizer.py',
        'libs/spacetime_manipulation_interface.py',
        'libs/auto_fix_executor.py',
        'libs/elders_guild_data_mapper.py',
        'libs/self_healing_orchestrator.py',
        'libs/elders_guild_monitoring.py',
        'libs/celery_migration_poc.py',
        'scripts/test_issue_loader_batch.py',
        'scripts/slack_diagnosis_tool.py',
        'scripts/cc_startup_auto_elder_check.py',
        'scripts/task_elder_comprehensive_registration.py',
        'scripts/test_issue_auto_processor.py',
        'scripts/test_auto_issue_processor.py',
        'scripts/iron_will_final_compliance_push.py',
        'scripts/elders_guild_integration_test.py',
        'elders_guild/run_incident_sage_server.py',
        'elders_guild/test_incident_sage_client.py',
        'commands/ai_shell.py',
        'commands/ai_nwo_library_update.py',
    ]
    
    fixed_count = 0
    
    for file_path in target_files:
        full_path = project_root / file_path
        if not full_path.exists():
            continue
            
        print(f"\n修正中: {file_path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 現在の状態を確認
            try:
                ast.parse(content)
                print("  ⚠️  エラーなし（スキップ）")
                continue
            except SyntaxError as e:
                if 'closing parenthesis' not in str(e):
                    print(f"  ⚠️  異なるエラー: {e}")
                    continue
            
            # 修正適用
            fixed_content = fix_parenthesis_mismatch(content)
            
            # テスト
            try:
                ast.parse(fixed_content)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print("  ✅ 修正成功")
                fixed_count += 1
            except SyntaxError as e:
                print(f"  ❌ まだエラー: {e}")
                # より詳細な修正を試みる
                lines = fixed_content.split('\n')
                if e.lineno:
                    error_line = lines[e.lineno - 1]
                    print(f"     エラー行: {error_line}")
                
        except Exception as e:
            print(f"  ❌ 処理エラー: {e}")
    
    print(f"\n📊 結果: {fixed_count} ファイル修正")

if __name__ == "__main__":
    main()