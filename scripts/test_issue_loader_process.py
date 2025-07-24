#!/usr/bin/env python3
"""
イシューローダー実処理テストスクリプト
実際のGitHub Issueを取得して、コード生成まで実行
"""

import asyncio
import json
import os
import sys
import time
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

# 処理結果を保存するディレクトリ
OUTPUT_DIR = Path("generated_code_samples")
OUTPUT_DIR.mkdir(exist_ok=True)

async def process_single_issue(processor, issue, template_manager)print(f"\n{'}")
"""単一のIssueを処理"""
    print(f"📋 Issue #{issue.number}: {issue.title}")
    print(f"{'}")
    
    try:
        # 1.0 複雑度評価
        print("\n🔍 複雑度評価中...")
        complexity = await processor.evaluator.evaluate(issue)
        print(f"  - 複雑度スコア: {complexity.score:0.3f}")
        print(f"  - 処理可能: {'✅ Yes' if complexity.is_processable else '❌ No'}")
        
        if not complexity.is_processable:
            print("  ⚠️  このIssueは複雑すぎるため処理をスキップします")
            return None
        
        # 2.0 4賢者相談
        print("\n🧙‍♂️ 4賢者に相談中...")
        sage_advice = await processor.consult_four_sages(issue)
        
        print(f"  - ナレッジ賢者: {len(sage_advice.get('knowledge', []))}件の知識")
        print(f"  - タスク賢者: {'✅ 計画作成' if sage_advice.get('plan') else '❌ 失敗'}")
        print(f"  - インシデント賢者: リスクレベル {sage_advice.get('risks', {}).get('risk_level', 'N/A')}")
        print(f"  - RAG賢者: {len(sage_advice.get('solution', []))}件の解決策")
        
        # 3.0 コード生成
        print("\n🔨 コード生成中...")
        tech_stack = template_manager.detect_tech_stack(
            f"{issue.title} {issue.body or ''}",
            [label.name for label in issue.labels]
        )
        print(f"  - 検出された技術スタック: {tech_stack}")
        
        # コンテキスト準備
        context = {
            'issue_number': issue.number,
            'issue_title': issue.title,
            'issue_body': issue.body or '',
            'service_name': f'Issue{issue.number}Service',
            'class_name': f'Issue{issue.number}Implementation',
            'module_name': f'issue_{issue.number}_solution',
            'description': issue.title,
            'requirements': {'imports': [], 'classes': [], 'functions': []},
            # 4賢者の知恵を活用
            'tech_details': sage_advice.get('plan', {}).get('tech_stack', {}),
            'endpoints': sage_advice.get('plan', {}).get('api_endpoints', []),
            'quality_improvements': [
                'エラーハンドリングの強化',
                '非同期処理の最適化',
                '包括的なログ記録'
            ],
            'similar_implementations': [],
            'naming_guide': {'suggested_class_name': f'Issue{issue.number}Implementation'},
            'enhanced_imports': [],
            'learned_patterns': {},
            'framework_type': 'generic',
            'project_context': {
                'architectural_patterns': {
                    'elder_flow_compatibility': 'Elder Flow統合対応'
                }
            }
        }
        
        # テンプレートで生成
        if template_manager.has_template('class', tech_stack):
            code = template_manager.generate_code(
                template_type='class',
                tech_stack=tech_stack,
                context=context,
                use_enhanced=False  # 標準テンプレート使用
            )
            
            # ファイルに保存
            output_file = OUTPUT_DIR / f"issue_{issue.number}_generated.py"
            output_file.write_text(code)
            
            print(f"  ✅ コード生成完了: {len(code.split('\n'))}行")
            print(f"  📁 保存先: {output_file}")
            
            # 4.0 テスト生成
            print("\n🧪 テスト生成中...")
            if template_manager.has_template('test', tech_stack):
                test_context = context.copy()
                test_context['test_cases'] = [
                    'test_initialization',
                    'test_main_functionality',
                    'test_error_handling',
                    'test_edge_cases'
                ]
                
                test_code = template_manager.generate_code(
                    template_type='test',
                    tech_stack=tech_stack,
                    context=test_context,
                    use_enhanced=False
                )
                
                test_file = OUTPUT_DIR / f"test_issue_{issue.number}.py"
                test_file.write_text(test_code)
                
                print(f"  ✅ テスト生成完了: {len(test_code.split('\n'))}行")
                print(f"  📁 保存先: {test_file}")
            
            # 5.0 品質評価
            print("\n📊 品質評価:")
            lines = code.split('\n')
            
            # 簡易品質チェック
            type_hints = sum(1 for line in lines if ':' in line and 'def ' in line)
            docstrings = sum(1 for line in lines if '"""' in line)
            error_handling = sum(1 for line in lines if 'try:' in line or 'except' in line)
            logging = sum(1 for line in lines if 'logger' in line or 'logging' in line)
            
            functions = sum(1 for line in lines if 'def ' in line)
            classes = sum(1 for line in lines if 'class ' in line)
            
            print(f"  - クラス数: {classes}")
            print(f"  - 関数数: {functions}")
            print(f"  - 型ヒント使用率: {(type_hints / max(functions, 1)) * 100:0.1f}%")
            print(f"  - Docstring数: {docstrings}")
            print(f"  - エラーハンドリング: {'✅' if error_handling > 0 else '❌'}")
            print(f"  - ロギング実装: {'✅' if logging > 0 else '❌'}")
            
            return {
                'issue_number': issue.number,
                'title': issue.title,
                'code_lines': len(lines),
                'quality_score': min(100, (type_hints + docstrings + error_handling + logging) * 10),
                'file_path': str(output_file)
            }
        else:
            print(f"  ❌ テンプレート '{tech_stack}/class' が見つかりません")
            return None
            
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main()print("="*80)
"""メイン処理"""
    print("🚀 イシューローダー実処理テスト")
    print("="*80)
    
    # 開始時刻
    start_time = time.time()
    
    # AutoIssueProcessorの初期化
    print("\n🔧 システム初期化中...")
    processor = AutoIssueProcessor()
    template_manager = CodeGenerationTemplateManager()
    
    # GitHub APIでIssueを取得
    print("\n📋 GitHub Issueを取得中...")
    github_token = os.getenv("GITHUB_TOKEN")
    repo_owner = os.getenv("GITHUB_REPO_OWNER", "ext-maru")
    repo_name = os.getenv("GITHUB_REPO_NAME", "ai-co")
    
    github = Github(github_token)
    repo = github.get_repo(f"{repo_owner}/{repo_name}")
    
    # オープンなIssueを取得（最新5件）
    open_issues = list(repo.get_issues(state='open'))[:5]
    
    print(f"  ✅ {len(open_issues)}件のオープンIssueを取得")
    
    # A2A処理に適したIssueを選別
    suitable_issues = []
    for issue in open_issues:
        # PRは除外
        if issue.pull_request:
            continue
        
        # ラベルでフィルタリング（例: enhancementやfeature）
        labels = [label.name.lower() for label in issue.labels]
        if any(label in ['enhancement', 'feature', 'task'] for label in labels):
            suitable_issues.append(issue)
    
    print(f"  ✅ {len(suitable_issues)}件が処理対象")
    
    # 各Issueを処理
    results = []
    for issue in suitable_issues[:3]:  # 最大3件まで処理
        result = await process_single_issue(processor, issue, template_manager)
        if result:
            results.append(result)
    
    # 結果サマリー
    print("\n" + "="*80)
    print("📊 処理結果サマリー")
    print("="*80)
    
    if results:
        print(f"\n✅ 成功: {len(results)}件")
        for result in results:
            print(f"  - Issue #{result['issue_number']}: {result['title'][:50]}...")
            print(f"    生成コード: {result['code_lines']}行")
            print(f"    品質スコア: {result['quality_score']}/100")
            print(f"    ファイル: {result['file_path']}")
        
        # 統計
        avg_lines = sum(r['code_lines'] for r in results) / len(results)
        avg_quality = sum(r['quality_score'] for r in results) / len(results)
        
        print(f"\n📈 統計:")
        print(f"  - 平均コード行数: {avg_lines:0.1f}行")
        print(f"  - 平均品質スコア: {avg_quality:0.1f}/100")
    else:
        print("\n❌ 処理できたIssueがありませんでした")
    
    # 処理時間
    total_time = time.time() - start_time
    print(f"\n⏱️  総処理時間: {total_time:0.2f}秒")
    
    # 結果をJSONに保存
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_issues': len(suitable_issues),
        'processed': len(results),
        'results': results,
        'total_time': total_time
    }
    
    summary_file = OUTPUT_DIR / "processing_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\n📄 サマリー保存: {summary_file}")

if __name__ == "__main__":
    asyncio.run(main())