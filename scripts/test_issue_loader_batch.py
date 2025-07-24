#!/usr/bin/env python3
"""
イシューローダーバッチ処理テスト
複数のGitHub Issueを並列処理
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
from github import Github

# 進捗表示用のロック
print_lock = threading.Lock()

def safe_print(message):
    """スレッドセーフな出力"""
    with print_lock:
        print(message)

async def evaluate_issue(processor, issue):
    """Issueの評価のみ実行（高速）"""
    try:
        complexity = await processor.evaluator.evaluate(issue)
        
        result = {
            'issue_number': issue.number,
            'title': issue.title,
            'labels': [label.name for label in issue.labels],
            'complexity_score': complexity.score,
            'is_processable': complexity.is_processable,
            'created_at': issue.created_at.isoformat(),
            'comments': issue.comments,
            'state': issue.state
        }
        
        safe_print(f"✅ Issue #{issue.number}: 複雑度 {complexity.score:0.3f}")
        return result
        
    except Exception as e:
        safe_print(f"❌ Issue #{issue.number}: エラー {e}")
        return None

async def batch_process_issues(issues, max_concurrent=5)processor = AutoIssueProcessor()
"""複数のIssueを並列処理"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_limit(issue):
        async with semaphore:
            return await evaluate_issue(processor, issue)
    
    tasks = [process_with_limit(issue) for issue in issues]
    results = await asyncio.gather(*tasks)
    
    return [r for r in results if r is not None]

def analyze_batch_results(results)total = len(results)
"""バッチ処理結果の分析"""
    processable = sum(1 for r in results if r['is_processable'])
    
    # 複雑度の統計
    complexities = [r['complexity_score'] for r in results]
    avg_complexity = sum(complexities) / len(complexities) if complexities else 0
    
    # ラベル別統計
    label_stats = {}
    for result in results:
        for label in result['labels']:
            label_stats[label] = label_stats.get(label, 0) + 1
    
    # 処理可能なIssueの詳細
    processable_issues = [r for r in results if r['is_processable']]
    
    return {
        'total_issues': total,
        'processable_count': processable,
        'processable_rate': processable / total * 100 if total > 0 else 0,
        'average_complexity': avg_complexity,
        'complexity_range': {
            'min': min(complexities) if complexities else 0,
            'max': max(complexities) if complexities else 0
        },
        'label_distribution': label_stats,
        'processable_issues': processable_issues
    }

async def main()print("="*80)
"""メイン処理"""
    print("🚀 イシューローダーバッチ処理テスト")
    print("="*80)
    
    start_time = time.time()
    
    # GitHub APIでIssueを取得
    print("\n📋 GitHub Issueを取得中...")
    github_token = os.getenv("GITHUB_TOKEN")
    repo_owner = os.getenv("GITHUB_REPO_OWNER", "ext-maru")
    repo_name = os.getenv("GITHUB_REPO_NAME", "ai-co")
    
    github = Github(github_token)
    repo = github.get_repo(f"{repo_owner}/{repo_name}")
    
    # オープンなIssueとクローズされたIssueを取得
    print("  - オープンなIssueを取得中...")
    open_issues = list(repo.get_issues(state='open'))[:20]
    
    print("  - 最近クローズされたIssueを取得中...")
    closed_issues = list(repo.get_issues(state='closed'))[:10]
    
    all_issues = open_issues + closed_issues
    
    # PRを除外
    issues = [issue for issue in all_issues if not issue.pull_request]
    
    print(f"\n📊 取得結果:")
    print(f"  - 総Issue数: {len(issues)}")
    print(f"  - オープン: {sum(1 for i in issues if i.state }")
    print(f"  - クローズ: {sum(1 for i in issues if i.state }")
    
    # バッチ処理実行
    print(f"\n⚡ バッチ処理開始（並列度: 5）...")
    batch_start = time.time()
    
    results = await batch_process_issues(issues, max_concurrent=5)
    
    batch_time = time.time() - batch_start
    print(f"\n✅ バッチ処理完了: {batch_time:0.2f}秒")
    print(f"  - 処理速度: {len(results)/batch_time:0.1f} issues/秒")
    
    # 結果分析
    print("\n📊 処理結果分析...")
    analysis = analyze_batch_results(results)
    
    print(f"\n📈 統計情報:")
    print(f"  - 処理成功: {len(results)}/{len(issues)} Issues")
    print(f"  - 処理可能: {analysis['processable_count']} ({analysis['processable_rate']:0.1f}%)")
    print(f"  - 平均複雑度: {analysis['average_complexity']:0.3f}")
    print(f"  - 複雑度範囲: {analysis['complexity_range']['min']:0.3f} - {analysis['complexity_range']['max']:0.3f}")
    
    print(f"\n🏷️ ラベル分布:")
    for label, count in sorted(analysis['label_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {label}: {count}件")
    
    print(f"\n✅ 処理可能なIssue Top 10:")
    for issue in sorted(analysis['processable_issues'], key=lambda x: x['complexity_score'])[:10]:
        print(f"  - Issue #{issue['issue_number']}: {issue['title'][:50]}... (複雑度: {issue['complexity_score']:0.3f})")
    
    # 総処理時間
    total_time = time.time() - start_time
    print(f"\n⏱️ 総処理時間: {total_time:0.2f}秒")
    
    # 結果をJSONに保存
    output_dir = Path("batch_processing_results")
    output_dir.mkdir(exist_ok=True)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'repository': f"{repo_owner}/{repo_name}",
        'total_issues_fetched': len(all_issues),
        'issues_processed': len(issues),
        'batch_processing_time': batch_time,
        'total_time': total_time,
        'analysis': analysis,
        'detailed_results': results
    }
    
    report_file = output_dir / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    
    print(f"\n📄 詳細レポート保存: {report_file}")
    
    # パフォーマンス推定
    print(f"\n🚀 パフォーマンス推定:")
    issues_per_hour = (len(results) / batch_time) * 3600
    print(f"  - 推定処理能力: {issues_per_hour:0.0f} issues/hour")
    print(f"  - リポジトリ全Issue処理時間: {len(all_issues) / (len(results) / batch_time) / 60:0.1f}分")

if __name__ == "__main__":
    asyncio.run(main())