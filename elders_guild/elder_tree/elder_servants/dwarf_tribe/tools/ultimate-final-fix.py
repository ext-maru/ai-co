#!/usr/bin/env python3
"""
ULTIMATE FINAL FIX - 最終修正
残存17エラーを個別に修正
"""

import ast
import re
from pathlib import Path

def fix_enhanced_error_handling():
    """enhanced_error_handling.pyの修正"""
    path = Path('/home/aicompany/ai_co/libs/enhanced_error_handling.py')
    with open(path, 'r') as f:
        lines = f.readlines()
    
    # Line 126のexpected ':'エラーを探して修正
    for i, line in enumerate(lines):
        if i == 125:  # line 126 (0-indexed)
            if 'def' in line and not line.strip().endswith(':'):
                lines[i] = line.rstrip() + ':\n'
    
    with open(path, 'w') as f:
        f.writelines(lines)
    print("✅ enhanced_error_handling.py 修正完了")

def fix_elder_flow_violation_resolver():
    """elder_flow_violation_resolver.pyの修正"""
    path = Path('/home/aicompany/ai_co/libs/elder_flow_violation_resolver.py')
    with open(path, 'r') as f:
        lines = f.readlines()
    
    # Line 82のexpected ':'エラーを探して修正
    for i, line in enumerate(lines):
        if i == 81:  # line 82 (0-indexed)
            if 'def' in line and not line.strip().endswith(':'):
                lines[i] = line.rstrip() + ':\n'
    
    with open(path, 'w') as f:
        f.writelines(lines)
    print("✅ elder_flow_violation_resolver.py 修正完了")

def fix_elder_cast_enhanced():
    """elder_cast_enhanced.pyの修正"""
    path = Path('/home/aicompany/ai_co/libs/elder_cast_enhanced.py')
    try:
        with open(path, 'r') as f:
            content = f.read()
        
        # Line 40のinvalid syntaxを修正
        lines = content.split('\n')
        for i in range(min(50, len(lines))):
            # f-string関連のエラーを修正
            lines[i] = re.sub(r'f"([^"]*)"([^"]*)"', r'f"\1\2"', lines[i])
            # 不正な文字列連結を修正
            lines[i] = re.sub(r'"\s*"', '', lines[i])
        
        with open(path, 'w') as f:
            f.write('\n'.join(lines))
        print("✅ elder_cast_enhanced.py 修正完了")
    except Exception as e:
        print(f"❌ elder_cast_enhanced.py 修正失敗: {e}")

def fix_parenthesis_mismatch_files():
    """括弧不一致エラーのあるファイルを修正"""
    files = [
        'libs/knowledge_index_optimizer.py',
        'libs/grimoire_elder_flow_optimization.py',
        'libs/demand_predictor.py',
        'libs/elder_council_review_system.py',
        'libs/retry_orchestrator.py',
        'libs/elder_servant_a2a_optimization.py',
        'libs/elder_council_summoner.py',
        'libs/resource_allocation_optimizer.py',
        'libs/advanced_search_analytics_platform.py',
    ]
    
    for file in files:
        path = Path('/home/aicompany/ai_co') / file
        if not path.exists():
            continue
            
        try:
            with open(path, 'r') as f:
                content = f.read()
            
            # f-string内の不正な括弧を修正
            content = re.sub(r'(f"[^"]*)\{([^}]*)\}([^"]*")\s*"([^"]*")', r'\1{\2}\3\4', content)
            
            # 括弧のバランスを取る
            lines = content.split('\n')
            for i, line in enumerate(lines):
                # 閉じ括弧が多い場合
                if line.count('}') > line.count('{'):
                    # f-string外の余分な}を削除
                    if 'f"' not in line and "f'" not in line:
                        line = line.replace('}', '', line.count('}') - line.count('{'))
                        lines[i] = line
            
            content = '\n'.join(lines)
            
            # テスト
            try:
                ast.parse(content)
                with open(path, 'w') as f:
                    f.write(content)
                print(f"✅ {file} 修正完了")
            except SyntaxError:
                print(f"❌ {file} まだエラーあり")
                
        except Exception as e:
            print(f"❌ {file} 処理エラー: {e}")

def fix_unterminated_string():
    """elder_flow_final_evolution.pyの文字列リテラルエラーを修正"""
    path = Path('/home/aicompany/ai_co/libs/elder_flow_final_evolution.py')
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
        
        # Line 95付近で開いている文字列を探す
        for i in range(90, min(100, len(lines))):
            if '"""' in lines[i] and lines[i].count('"""') % 2 == 1:
                # 閉じられていないdocstring
                lines[i] = lines[i].rstrip() + '"""\n'
        
        with open(path, 'w') as f:
            f.writelines(lines)
        print("✅ elder_flow_final_evolution.py 修正完了")
    except Exception as e:
        print(f"❌ elder_flow_final_evolution.py 修正失敗: {e}")

def main():
    """メイン処理"""
    print("🔥 ULTIMATE FINAL FIX - 残存17エラーの個別修正")
    
    # 個別修正実行
    fix_enhanced_error_handling()
    fix_elder_flow_violation_resolver()
    fix_elder_cast_enhanced()
    fix_parenthesis_mismatch_files()
    fix_unterminated_string()
    
    # 最終確認
    print("\n🔍 最終確認...")
    from pathlib import Path
    import ast
    
    project_root = Path('/home/aicompany/ai_co')
    error_count = 0
    
    for py_file in project_root.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'node_modules', '.git', 'site-packages']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError:
            error_count += 1
    
    print(f"\n🎯 最終結果: {error_count} エラー残存")
    
    if error_count == 0:
        print("\n🎉 完全勝利！すべてのシンタックスエラーが撃破されました！")
    else:
        print(f"\n⚔️  まだ戦いは続く... 残り {error_count} エラー")

if __name__ == "__main__":
    main()