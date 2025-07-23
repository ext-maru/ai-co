#!/usr/bin/env python3
"""
自動イシュー処理システムの改善点をGitHub Issueとして登録するスクリプト
"""

import os
import sys
from github import Github
from datetime import datetime

# GitHub認証
github_token = os.environ.get("GITHUB_TOKEN")
if not github_token:
    print("❌ GITHUB_TOKEN環境変数が設定されていません")
    sys.exit(1)

g = Github(github_token)
repo = g.get_repo("ext-maru/ai-co")

# 登録するイシューのリスト
issues_to_create = [
    {
        "title": "🔧 [改善] RAG Manager process_requestメソッド実装",
        "body": """## 概要
自動イシュー処理システムでRAG賢者の`process_request`メソッドが未実装のため、4賢者相談の一部が失敗しています。

## エラー詳細
```
ERROR:libs.rag_manager:RAG Manager process_request error: 'RagManager' object has no attribute 'search'
WARNING:AutoIssueProcessor:Sage consultation partial failure: 'RagManager' object has no attribute 'process_request'
```

## 影響
- 4賢者相談でRAG賢者の知見が得られない
- 他の3賢者で補完されているため、処理自体は継続

## 改善案
1. `libs/rag_manager.py`に`process_request`メソッドを実装
2. 既存の`search_knowledge`メソッドをラップする形で実装
3. 非同期処理対応（async/await）

## 優先度
Medium - システムは動作しているが、4賢者の完全な協調のために必要

## 関連ファイル
- `/home/aicompany/ai_co/libs/rag_manager.py`
- `/home/aicompany/ai_co/libs/integrations/github/auto_issue_processor.py`
""",
        "labels": ["enhancement", "bug", "auto-issue-processor", "4sages"]
    },
    {
        "title": "🔧 [改善] 4賢者相談の非同期処理エラー修正",
        "body": """## 概要
Elder Flow Phase 1（4賢者会議）で非同期処理のエラーが発生し、リトライが必要になっています。

## エラー詳細
```
ERROR:libs.elder_flow_orchestrator:Sage consultation failed: object NoneType can't be used in 'await' expression
WARNING:ElderFlowErrorHandler:Attempt 1/3 failed: Sage consultation failed: knowledge -  \
    object NoneType can't be used in 'await' expression
```

## 影響
- Phase 1の初回実行が失敗
- リトライ機能により2-3回目で成功
- 処理時間の増加

## 改善案
1. `libs/elder_flow_four_sages_complete.py`の非同期処理を修正
2. Noneチェックの追加
3. プレースホルダー実装の改善

## 優先度
Medium - リトライで回復するが、パフォーマンス向上のため修正推奨

## 関連ファイル
- `/home/aicompany/ai_co/libs/elder_flow_four_sages_complete.py`
- `/home/aicompany/ai_co/libs/elder_flow_orchestrator.py`
""",
        "labels": ["bug", "performance", "elder-flow", "async"]
    },
    {
        "title": "🔧 [改善] 品質ゲートのsecurity_issuesキーエラー修正",
        "body": """## 概要
Elder Flow Phase 3（品質ゲート）でsecurity_issuesキーが見つからないエラーが発生しています。

## エラー詳細
```
ERROR:ElderFlowErrorHandler:Unhandled error: 'security_issues'
ERROR:libs.elder_flow_orchestrator:Quality gate execution failed: 'security_issues'
```

## 影響
- セキュリティチェックがスキップされる
- 品質ゲートが部分的に失敗
- PR作成は成功するが、セキュリティ面の確認が不完全

## 改善案
1. 品質ゲート結果のデータ構造を確認
2. security_issuesキーの存在チェックを追加
3. デフォルト値の設定

## 優先度
High - セキュリティチェックは重要な機能

## 関連ファイル
- `/home/aicompany/ai_co/libs/elder_flow_orchestrator.py`
- `/home/aicompany/ai_co/libs/elder_flow_quality_gate.py`
""",
        "labels": ["bug", "security", "quality-gate", "high-priority"]
    }
]

# イシューを作成
created_issues = []
for issue_data in issues_to_create:
    try:
        issue = repo.create_issue(
            title=issue_data["title"],
            body=issue_data["body"],
            labels=issue_data["labels"]
        )
        created_issues.append(issue)
        print(f"✅ Issue作成成功: #{issue.number} - {issue.title}")
        print(f"   URL: {issue.html_url}")
    except Exception as e:
        print(f"❌ Issue作成失敗: {issue_data['title']}")
        print(f"   エラー: {e}")

# サマリー表示
if created_issues:
    print(f"\n📊 作成されたIssue: {len(created_issues)}件")
    print("\n🔗 Issue一覧:")
    for issue in created_issues:
        print(f"  - #{issue.number}: {issue.title}")
        print(f"    {issue.html_url}")
else:
    print("\n❌ Issueが作成されませんでした")