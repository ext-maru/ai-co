#!/usr/bin/env python3
"""
DECIMAL LITERAL FIXER
invalid decimal literal エラーを修正
"""

import ast
import re
from pathlib import Path

def fix_decimal_literals(content):
    """invalid decimal literalエラーを修正"""
    # パターン1: .0lower() -> .lower()
    content = re.sub(r'\.0lower\(\)', '.lower()', content)
    content = re.sub(r'\.0upper\(\)', '.upper()', content)
    
    # パターン2: .0get( -> .get(
    content = re.sub(r'\.0get\(', '.get(', content)
    
    # パターン3: .0intersection( -> .intersection(
    content = re.sub(r'\.0intersection\(', '.intersection(', content)
    content = re.sub(r'\.0union\(', '.union(', content)
    
    # パターン4: sqlite3 -> sqlite3
    content = re.sub(r'\bsqlite3\.0\b', 'sqlite3', content)
    
    # パターン5: 一般的な .0method( -> .method(
    content = re.sub(r'\.0(\w+)\(', r'.\1(', content)
    
    # パターン6: 誤った小数点表記の修正
    # 例: words1.0 -> words1
    content = re.sub(r'(\w+)\.0(?!\d)', r'\1', content)
    
    return content

def main():
    """メイン処理"""
    print("🔧 DECIMAL LITERAL FIXER - 小数リテラル修正")
    
    project_root = Path('/home/aicompany/ai_co')
    error_files = []
    
    # エラーファイルのリスト（quick-error-checkの結果から）
    target_files = [
        'libs/self_evolution_manager.py',
        'libs/pytest_integration_poc.py',
        'libs/comprehensive_grimoire_migration.py',
        'libs/elder_flow_servant_executor_real.py',
        'libs/self_evolving_code_generator.py',
        'libs/elder_tree_vector_network.py',
        'libs/smart_code_generator.py',
        'libs/security_level_enforcer.py',
        'libs/github_security_enhancement.py',
        'libs/learning_optimizer.py',
        'libs/enhanced_error_handling.py',
        'libs/knowledge_evolution.py',
        'libs/model_training.py',
        'libs/rag_grimoire_integration.py',
        'libs/knowledge_evolution_tracker.py',
        'libs/knowledge_sage_doc_generator.py',
        'libs/memory_stream_optimizer.py',
        'libs/error_classification_system.py',
        'libs/four_sages_diagnostic_system.py',
        'libs/ai_self_evolution_engine.py',
        'libs/elders_code_quality_engine.py',
        'libs/conversation_search.py',
        'libs/syntax_error_fixer.py',
        'libs/multi_cc_coordination.py',
        'libs/performance_optimizer.py',
        'libs/enhanced_error_intelligence.py',
        'libs/pgvector_direct_reconstruction.py',
        'libs/quantum_parallel_engine.py',
        'data/worker_optimization_report.py',
        'scripts/pgvector_a2a_integration.py',
        'scripts/compare_test_performance.py',
        'scripts/setup_pgvector_database.py',
        'scripts/migrate_a2a_to_pgvector.py',
        'scripts/github_issue_update_elder_flow.py',
        'scripts/pipeline_status_reporter.py',
        'scripts/a2a_performance_benchmark.py',
        'tests/test_issue_133.py',
        'libs/database_manager.py',
        'libs/pattern_analyzer.py',
        'libs/intelligent_test_generator.py',
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
                if 'invalid decimal literal' not in str(e):
                    print(f"  ⚠️  異なるエラー: {e}")
                    continue
            
            # 修正適用
            fixed_content = fix_decimal_literals(content)
            
            # テスト
            try:
                ast.parse(fixed_content)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print("  ✅ 修正成功")
                fixed_count += 1
            except SyntaxError as e:
                print(f"  ❌ まだエラー: {e}")
                
        except Exception as e:
            print(f"  ❌ 処理エラー: {e}")
    
    print(f"\n📊 結果: {fixed_count} ファイル修正")

if __name__ == "__main__":
    main()