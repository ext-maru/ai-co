#!/usr/bin/env python3
"""
イシューローダー完全性能テストスクリプト
4賢者修正後の性能とコード生成品質を評価
"""

import asyncio
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime
import tempfile

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
from libs.code_generation.template_manager import CodeGenerationTemplateManager
from libs.code_generation.pattern_learning import PatternLearningEngine
from github import Github

async def test_full_issue_processing():
    """イシューローダーの完全テスト"""
    print("=" * 80)
    print("🧪 イシューローダー完全性能テスト")
    print("=" * 80)
    
    # 開始時刻とメモリ使用量
    start_time = time.time()
    start_memory = get_memory_usage()
    
    print(f"\n📊 初期状態:")
    print(f"  - 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  - 初期メモリ: {start_memory:0.1f} MB")
    
    try:
        # AutoIssueProcessorの初期化
        print("\n🔧 システム初期化中...")
        init_start = time.time()
        processor = AutoIssueProcessor()
        init_end = time.time()
        print(f"  ✅ 初期化完了 ({init_end - init_start:0.2f}秒)")
        
        # Issue #193を取得
        print("\n📋 Issue #193を取得中...")
        fetch_start = time.time()
        
        github_token = os.getenv("GITHUB_TOKEN")
        repo_owner = os.getenv("GITHUB_REPO_OWNER", "ext-maru")
        repo_name = os.getenv("GITHUB_REPO_NAME", "ai-co")
        
        github = Github(github_token)
        repo = github.get_repo(f"{repo_owner}/{repo_name}")
        issue = repo.get_issue(193)
        
        fetch_end = time.time()
        print(f"  ✅ Issue取得完了 ({fetch_end - fetch_start:0.2f}秒)")
        print(f"  - タイトル: {issue.title}")
        print(f"  - 本文長: {len(issue.body or '')} 文字")
        
        # 複雑度評価
        print("\n🔍 複雑度評価中...")
        eval_start = time.time()
        complexity = await processor.evaluator.evaluate(issue)
        eval_end = time.time()
        
        print(f"  ✅ 複雑度評価完了 ({eval_end - eval_start:0.2f}秒)")
        print(f"  - 複雑度スコア: {complexity.score:0.3f}")
        print(f"  - 処理可能: {'✅ Yes' if complexity.is_processable else '❌ No'}")
        
        # 4賢者相談（修正版）
        print("\n🧙‍♂️ 4賢者相談（修正版）テスト...")
        sage_start = time.time()
        sage_advice = await processor.consult_four_sages(issue)
        sage_end = time.time()
        
        print(f"  ✅ 4賢者相談完了 ({sage_end - sage_start:0.2f}秒)")
        print(f"  - ナレッジ賢者: {len(sage_advice.get('knowledge', []))}件の知識")
        print(f"  - タスク賢者: {'✅ 計画作成' if sage_advice.get('plan') else '❌ 失敗'}")
        print(f"  - インシデント賢者: リスクレベル {sage_advice.get('risks', {}).get('risk_level', 'N/A')}")
        print(f"  - RAG賢者: {len(sage_advice.get('solution', []))}件の解決策")
        
        errors = sage_advice.get('consultation_errors', [])
        if errors:
            print(f"  ⚠️  エラー: {len(errors)}件")
            for error in errors:
                print(f"    - {error}")
        
        # コード生成テスト
        print("\n🔨 コード生成テスト...")
        codegen_start = time.time()
        
        # テンプレートマネージャーを使用
        template_manager = CodeGenerationTemplateManager()
        pattern_learner = PatternLearningEngine()
        
        # Issue情報からコード生成
        issue_data = {
            'number': issue.number,
            'title': issue.title,
            'body': issue.body or '',
            'labels': [label.name for label in issue.labels],
            'tech_stack': 'web',  # 監視ダッシュボードなのでweb系
        }
        
        # テンプレート選択とコード生成
        # 正しいテンプレート名: 'class' または 'class_enhanced'
        template_type = 'class'
        tech_stack = 'web'  # 監視ダッシュボードなのでweb系
        generated_files = []
        
        if template_manager.has_template(template_type, tech_stack):
            context = {
                'issue_number': issue.number,
                'issue_title': issue.title,
                'issue_body': issue.body or '',
                'service_name': 'ObservabilityDashboard',
                'class_name': 'ObservabilityDashboard',
                'module_name': 'observability_dashboard',
                'description': 'Auto Issue Processor監視・可観測性ダッシュボード',
                'tech_details': {
                    'framework': 'FastAPI',
                    'monitoring': 'Prometheus',
                    'logging': 'Structured JSON',
                    'dashboard': 'Grafana'
                },
                'endpoints': [
                    {'path': '/health', 'method': 'GET', 'description': 'ヘルスチェック'},
                    {'path': '/metrics', 'method': 'GET', 'description': 'Prometheusメトリクス'},
                    {'path': '/dashboard', 'method': 'GET', 'description': 'ダッシュボード表示'},
                ],
                # テンプレート必須変数
                'quality_improvements': [
                    'エラーハンドリングの強化',
                    '非同期処理の最適化',
                    '包括的なログ記録'
                ],
                'similar_implementations': [],
                'naming_guide': {'suggested_class_name': 'ObservabilityDashboard'},
                'enhanced_imports': [],
                'learned_patterns': {},
                'framework_type': 'fastapi',
                # プロジェクトコンテキスト
                'project_context': {
                    'architectural_patterns': {
                        'elder_flow_compatibility': 'Elder Flow統合対応'
                    }
                }
            }
            
            # generate_codeメソッドを使用
            code = template_manager.generate_code(
                template_type=template_type,
                tech_stack=tech_stack,
                context=context,
                use_enhanced=False  # 標準テンプレートを使用（強化版は複雑すぎる）
            )
            generated_files.append({
                'name': 'observability_dashboard.py',
                'content': code,
                'lines': len(code.split('\n'))
            })
        else:
            print(f"  ⚠️  テンプレート '{template_type}' ({tech_stack}) が見つかりません")
        
        codegen_end = time.time()
        
        print(f"  ✅ コード生成完了 ({codegen_end - codegen_start:0.2f}秒)")
        print(f"  - 生成ファイル数: {len(generated_files)}")
        for file in generated_files:
            print(f"    - {file['name']}: {file['lines']}行")
        
        # コード品質分析
        if generated_files:
            print("\n📊 生成コード品質分析...")
            code_content = generated_files[0]['content']
            
            # 基本的な品質メトリクス
            quality_metrics = analyze_code_quality(code_content)
            
            print(f"  - 型ヒント使用率: {quality_metrics['type_hints_ratio']:0.1%}")
            print(f"  - docstring使用率: {quality_metrics['docstring_ratio']:0.1%}")
            print(f"  - エラーハンドリング: {'✅' if quality_metrics['has_error_handling'] else '❌'}")
            print(f"  - async/await使用: {'✅' if quality_metrics['uses_async'] else '❌'}")
            print(f"  - ロギング実装: {'✅' if quality_metrics['has_logging'] else '❌'}")
            
            # サンプルコード表示
            print("\n📝 生成コードサンプル（最初の30行）:")
            print("-" * 60)
            lines = code_content.split('\n')[:30]
            for i, line in enumerate(lines, 1):
                print(f"{i:3d} | {line}")
            print("-" * 60)
        
        # テスト生成機能テスト
        print("\n🧪 テスト自動生成テスト...")
        test_start = time.time()
        
        # テストテンプレートが存在するか確認
        test_template_type = 'test'
        test_tech_stack = 'web'
        test_code = None
        
        if template_manager.has_template(test_template_type, test_tech_stack):
            test_context = {
                'issue_number': issue.number,
                'issue_title': issue.title,
                'issue_body': issue.body or '',
                'service_name': 'ObservabilityDashboard',
                'class_name': 'ObservabilityDashboard',
                'module_name': 'observability_dashboard',
                'test_cases': [
                    'test_health_endpoint',
                    'test_metrics_format',
                    'test_dashboard_rendering',
                    'test_error_handling'
                ],
                # テンプレート必須変数
                'requirements': {'imports': [], 'classes': [], 'functions': []}
            }
            test_code = template_manager.generate_code(
                template_type=test_template_type,
                tech_stack=test_tech_stack,
                context=test_context,
                use_enhanced=False  # テストテンプレートは標準版のみ
            )
        else:
            # 簡易テストコード生成
            test_code = generate_simple_test_code('ObservabilityDashboard', 'observability_dashboard')
        
        test_end = time.time()
        
        if test_code:
            print(f"  ✅ テスト生成完了 ({test_end - test_start:0.2f}秒)")
            print(f"  - テストコード行数: {len(test_code.split('\n'))}行")
        else:
            print(f"  ❌ テスト生成失敗 ({test_end - test_start:0.2f}秒)")
        
        # 全体の性能サマリー
        total_time = time.time() - start_time
        end_memory = get_memory_usage()
        memory_increase = end_memory - start_memory
        
        print("\n" + "=" * 80)
        print("📊 完全テスト結果サマリー")
        print("=" * 80)
        print(f"  - 総処理時間: {total_time:0.2f}秒")
        print(f"  - 初期化時間: {init_end - init_start:0.2f}秒")
        print(f"  - Issue取得時間: {fetch_end - fetch_start:0.2f}秒")
        print(f"  - 複雑度評価時間: {eval_end - eval_start:0.2f}秒")
        print(f"  - 4賢者相談時間: {sage_end - sage_start:0.2f}秒")
        print(f"  - コード生成時間: {codegen_end - codegen_start:0.2f}秒")
        print(f"  - テスト生成時間: {test_end - test_start:0.2f}秒")
        print(f"  - メモリ使用量: {start_memory:0.1f} MB → {end_memory:0.1f} MB (+{memory_increase:0.1f} MB)")
        
        # 品質サマリー
        print("\n🎯 品質評価サマリー:")
        print(f"  - 4賢者相談: {'✅ 成功' if not errors else f'⚠️  部分的成功（{len(errors)}エラー）'}")
        print(f"  - コード生成: {'✅ 成功' if generated_files else '❌ 失敗'}")
        print(f"  - テスト生成: {'✅ 成功' if test_code else '❌ 失敗'}")
        
        if generated_files and quality_metrics:
            overall_quality = calculate_overall_quality(quality_metrics)
            print(f"  - コード品質スコア: {overall_quality:0.1f}/100")
            
            if overall_quality >= 80:
                print("  ✅ Production Ready品質")
            elif overall_quality >= 60:
                print("  ⚠️  改善の余地あり")
            else:
                print("  ❌ 品質改善が必要")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def get_memory_usage():
    """現在のメモリ使用量を取得（MB単位）"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except:
        return 0.0

def analyze_code_quality(code: str) -> dict:
    """生成されたコードの品質を分析"""
    lines = code.split('\n')
    
    # 基本メトリクス
    total_functions = code.count('def ') + code.count('async def ')
    functions_with_type_hints = len([line for line in lines if 'def ' in line and '->' in line])
    functions_with_docstrings = 0
    
    # docstring検出（簡易版）
    for i, line in enumerate(lines):
        if 'def ' in line or 'class ' in line:
            if i + 1 < len(lines) and '"""' in lines[i + 1]:
                functions_with_docstrings += 1
    
    return {
        'type_hints_ratio': functions_with_type_hints / max(total_functions, 1),
        'docstring_ratio': functions_with_docstrings / max(total_functions, 1),
        'has_error_handling': 'try:' in code and 'except' in code,
        'uses_async': 'async def' in code,
        'has_logging': 'logger' in code or 'logging' in code,
        'total_lines': len(lines),
        'total_functions': total_functions
    }

def calculate_overall_quality(metrics: dict) -> float:
    """総合品質スコアを計算"""
    score = 0
    score += metrics['type_hints_ratio'] * 25  # 型ヒント: 25点
    score += metrics['docstring_ratio'] * 25   # docstring: 25点
    score += 20 if metrics['has_error_handling'] else 0  # エラーハンドリング: 20点
    score += 15 if metrics['uses_async'] else 0  # 非同期処理: 15点
    score += 15 if metrics['has_logging'] else 0  # ロギング: 15点
    return score

def generate_simple_test_code(class_name: str, module_name: str) -> str:
    """簡易的なテストコードを生成"""
    return f'''import pytest
from unittest.mock import Mock, patch
from {module_name} import {class_name}

class Test{class_name}:
    """Auto-generated tests for {class_name}"""
    
    @pytest.fixture
    def instance(self):
        """Create test instance"""
        return {class_name}()
    
    def test_initialization(self, instance):
        """Test {class_name} initialization"""
        assert instance is not None
    
    def test_health_check(self, instance):
        """Test health check endpoint"""
        result = instance.health_check()
        assert result["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_async_operations(self, instance):
        """Test async operations"""
        # Add async test implementation
        pass
'''

if __name__ == "__main__":
    asyncio.run(test_full_issue_processing())