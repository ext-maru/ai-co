#!/usr/bin/env python3
"""
Analyze GitHub Issue for Elder Flow Enhancement
Issue分析CLIツール
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_system.elder_flow_enhancement_engine import ElderFlowEnhancementEngine


def main():
    """mainメソッド"""
    parser = argparse.ArgumentParser(description='Analyze GitHub Issue for Elder Flow')
    parser.add_argument('issue_number', type=int, help='Issue number to analyze')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--prompt', action='store_true', help='Generate Elder Flow prompt')
    
    args = parser.parse_args()
    
    # テスト用のIssueデータ（本来はGitHub APIから取得）
    test_issues = {
        83: {
            'number': 83,
            'title': '⚡ Continue.dev Phase 2 - パフォーマンス最適化',
            'body': '''## 概要
Continue.devの第2フェーズとして、パフォーマンスの最適化を行います。

## 要件
- レスポンスタイムを50ms以下に改善
- メモリ使用量を30%削減
- 並列処理の実装
- キャッシュ層の追加（Redis使用）
- 10000同時接続をサポート

## 技術詳細
- Python 3.11+
- FastAPI
- PostgreSQL
- Redis
- Docker

## テスト要件
- 90%以上のテストカバレッジ
- パフォーマンステストの実装
- 負荷テストの実装
''',
            'labels': ['enhancement', 'performance', 'continue-dev']
        },
        254: {
            'number': 254,
            'title': 'Auto Issue Processor緊急停止・根本原因分析・改善計画',
            'body': '''## 問題
Auto Issue ProcessorがIssue #83で予期しない動作をしました。

## 根本原因
Elder Flowが実装系タスクに対して不適切に適用されている

## 改善計画
1.0 Issue種別判定システムの実装
2.0 技術要件抽出エンジンの開発
3.0 Elder Flow Phase 2アーキテクチャ
''',
            'labels': ['bug', 'critical', 'elder-flow']
        }
    }
    
    if args.issue_number not in test_issues:
        print(f"Error: Issue #{args.issue_number} not found in test data")
        sys.exit(1)
    
    issue_data = test_issues[args.issue_number]
    
    # 分析実行
    engine = ElderFlowEnhancementEngine()
    result = engine.analyze_issue(issue_data)
    
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        # 人間が読みやすい形式で出力
        print(f"\n🔍 Analysis for Issue #{args.issue_number}")
        print("=" * 60)
        print(f"Title: {issue_data['title']}")
        print(f"Category: {result['issue_category']}")
        print(f"Type: {result['issue_type']}")
        print(f"Confidence: {result['confidence']:0.2%}")
        print(f"Elder Flow Mode: {result['elder_flow_mode']}")
        print(f"Recommended Approach: {result['recommended_approach']}")
        
        if 'technical_analysis' in result:
            tech = result['technical_analysis']
            print("\n📦 Technical Stack:")
            stack = tech['technical_stack']
            if stack['languages']:
                print(f"  Languages: {', '.join(stack['languages'])}")
            if stack['frameworks']:
                print(f"  Frameworks: {', '.join(stack['frameworks'])}")
            if stack['databases']:
                print(f"  Databases: {', '.join(stack['databases'])}")
            
            print(f"\n📊 Requirements Summary:")
            print(f"  Total: {tech['requirements_summary']['total']}")
            print(f"  High Priority: {tech['requirements_summary']['high_priority']}")
            print(f"  Complexity: {tech['complexity']}")
            
            if tech['implementation_steps']:
                print(f"\n📋 Implementation Steps:")
                for step in tech['implementation_steps']:
                    print(f"  {step['order']}. {step['description']}")
        
        risk = result['risk_assessment']
        if risk['mitigation_required']:
            print(f"\n⚠️ Risk Assessment:")
            print(f"  Overall Risk: {risk['overall_risk_level']}")
            for factor in risk['risk_factors']:
                print(f"  - {factor['type']}: {factor['description']}")
        
        print("\n" + "=" * 60)
    
    if args.prompt:
        print("\n📝 Elder Flow Prompt:")
        print("-" * 60)
        print(engine.generate_elder_flow_prompt(result))
        print("-" * 60)


if __name__ == "__main__":
    main()