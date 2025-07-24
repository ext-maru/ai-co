#!/usr/bin/env python3
"""
イシューローダー性能テストスクリプト
Issue #193を処理して性能を評価
"""

import asyncio
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
from github import Github

async def test_issue_loader_performance():
    """イシューローダーの性能テスト"""
    print("=" * 80)
    print("🧪 イシューローダー性能テスト開始")
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
        
        # Issue #193を直接取得
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
        print(f"  - 評価要因:")
        for factor, score in complexity.factors.items():
            print(f"    - {factor}: {score:0.2f}")
        
        # ドライラン実行
        print("\n🏃 ドライラン実行中...")
        dry_run_start = time.time()
        
        result = await processor.process_request({
            'mode': 'dry_run',
            'issue_number': 193
        })
        
        dry_run_end = time.time()
        
        print(f"  ✅ ドライラン完了 ({dry_run_end - dry_run_start:0.2f}秒)")
        print(f"  - ステータス: {result.get('status')}")
        
        if result.get('status') == 'dry_run':
            issue_info = result.get('issue', {})
            print(f"\n📊 処理可能性分析:")
            print(f"  - Issue番号: #{issue_info.get('number')}")
            print(f"  - 優先度: {issue_info.get('priority')}")
            print(f"  - 複雑度: {issue_info.get('complexity', 0):0.3f}")
            print(f"  - 処理可能: {'✅ Yes' if issue_info.get('processable') else '❌ No'}")
            
            if not issue_info.get('processable'):
                print(f"\n❌ 処理不可理由:")
                print(f"  - 複雑度が高すぎます (閾値: 0.7)")
                
        # 4賢者相談のテスト
        print("\n🧙‍♂️ 4賢者相談テスト...")
        sage_start = time.time()
        sage_advice = await processor.consult_four_sages(issue)
        sage_end = time.time()
        
        print(f"  ✅ 4賢者相談完了 ({sage_end - sage_start:0.2f}秒)")
        print(f"  - タスク賢者: {'✅' if 'task_sage' in sage_advice else '❌'}")
        print(f"  - インシデント賢者: {'✅' if 'incident_sage' in sage_advice else '❌'}")
        print(f"  - ナレッジ賢者: {'✅' if 'knowledge_sage' in sage_advice else '❌'}")
        print(f"  - RAG賢者: {'✅' if 'rag_sage' in sage_advice else '❌'}")
        
        # 全体の性能サマリー
        total_time = time.time() - start_time
        end_memory = get_memory_usage()
        memory_increase = end_memory - start_memory
        
        print("\n" + "=" * 80)
        print("📊 性能テスト結果サマリー")
        print("=" * 80)
        print(f"  - 総処理時間: {total_time:0.2f}秒")
        print(f"  - 初期化時間: {init_end - init_start:0.2f}秒")
        print(f"  - Issue取得時間: {fetch_end - fetch_start:0.2f}秒")
        print(f"  - 複雑度評価時間: {eval_end - eval_start:0.2f}秒")
        print(f"  - ドライラン時間: {dry_run_end - dry_run_start:0.2f}秒")
        print(f"  - 4賢者相談時間: {sage_end - sage_start:0.2f}秒")
        print(f"  - メモリ使用量: {start_memory:0.1f} MB → {end_memory:0.1f} MB (+{memory_increase:0.1f} MB)")
        
        # 期待値との比較
        print("\n🎯 期待値との比較:")
        expected_time = 3.2  # Issue Loader Performance Reportより
        print(f"  - 期待処理時間: {expected_time}秒")
        print(f"  - 実測処理時間: {total_time:0.2f}秒")
        print(f"  - 差分: {total_time - expected_time:+0.2f}秒")
        
        if total_time <= expected_time * 1.2:  # 20%の許容範囲
            print("  ✅ 性能は期待範囲内です")
        else:
            print("  ⚠️  性能が期待値を下回っています")
            
        # 推定スループット
        estimated_throughput = 3600 / total_time  # issues/hour
        print(f"\n📈 推定スループット: {estimated_throughput:0.0f} issues/hour")
        print(f"  - 期待値: 1,126 issues/hour")
        print(f"  - 達成率: {(estimated_throughput / 1126) * 100:0.1f}%")
        
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
        # psutilが利用できない場合は0を返す
        return 0.0

if __name__ == "__main__":
    asyncio.run(test_issue_loader_performance())