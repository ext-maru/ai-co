#!/usr/bin/env python3
"""
統合タスクトラッカー(UTT)プロジェクトのGitHub Issue作成スクリプト
"""

import json
import os
import sys
from datetime import datetime

import requests
from libs.env_manager import EnvManager

# GitHubトークンを環境変数から取得
GITHUB_TOKEN = EnvManager.get_github_token()
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN environment variable not set")
    sys.exit(1)

# リポジトリ情報
REPO_OWNER = EnvManager.get_github_repo_owner()
REPO_NAME = EnvManager.get_github_repo_name()
API_BASE_URL = f"{EnvManager.get_github_api_base_url()}/repos/{REPO_OWNER}/{REPO_NAME}"

# ヘッダー設定
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Claude-Elder-UTT",
}


def create_issue(title, body, labels=None):
    """GitHub Issueを作成"""
    issue_data = {"title": title, "body": body, "labels": labels or []}

    response = requests.post(f"{API_BASE_URL}/issues", json=issue_data, headers=HEADERS)

    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(
            f"Failed to create issue: {response.status_code} - {response.text}"
        )


def create_utt_issues():
    """統合タスクトラッカーのIssue構造を作成"""

    print(
        f"🏗️ Creating issues for Unified Task Tracker project in {REPO_OWNER}/{REPO_NAME}..."
    )

    # メインEpic Issue
    epic_title = "🏗️ [EPIC] 統合タスクトラッカーシステム実装 (UTT-2025-07)"
    epic_body = """## 🎯 概要
エルダーズギルドの中核システムであるタスクトラッカーを、内部高速処理と外部可視性を両立するハイブリッド型統合システムとして再構築する。

## 📋 背景
- 現在のタスクトラッカー実装が失われ、プレースホルダーのみ存在
- データベースには2,452件の履歴データが存在
- 4賢者システムとの統合が不完全

## 🎯 目標
- ハイブリッド型統合タスクトラッカーの実装
- 4賢者システムとの完全統合
- Elder Flowとのシームレス連携
- 既存データの移行と活用

## 📊 成功指標
- 応答時間: < 100ms（内部DB操作）
- 同期遅延: < 5秒（GitHub同期）
- テストカバレッジ: 95%以上
- 可用性: 99.9%以上

## 📋 Sub Issues

### Phase 1: 基盤構築（Week 1）
- [ ] #ISSUE_1 データモデル設計・実装
- [ ] #ISSUE_2 基本CRUD実装
- [ ] #ISSUE_3 テスト基盤構築

### Phase 2: 統合実装（Week 2）
- [ ] #ISSUE_4 4賢者システム統合
- [ ] #ISSUE_5 Elder Flow統合
- [ ] #ISSUE_6 サーバント統合

### Phase 3: GitHub連携（Week 3）
- [ ] #ISSUE_7 GitHub API統合
- [ ] #ISSUE_8 同期メカニズム実装
- [ ] #ISSUE_9 Webhook処理実装

### Phase 4: UI/UX・最適化（Week 4）
- [ ] #ISSUE_10 CLI強化
- [ ] #ISSUE_11 ダッシュボード実装
- [ ] #ISSUE_12 パフォーマンス最適化

## 📊 Progress: 0%
[░░░░░░░░░░] 0/12 completed

## 📚 関連ドキュメント
- [実装計画書](/docs/plans/UNIFIED_TASK_TRACKER_IMPLEMENTATION_PLAN.md)
- [アーキテクチャ設計書](TBD)
- [API仕様書](TBD)

## 🏷️ ラベル
- enhancement
- epic
- priority:high
- project:utt
- elders-guild
"""

    # メインEpic作成
    try:
        epic = create_issue(
            title=epic_title,
            body=epic_body,
            labels=[
                "enhancement",
                "epic",
                "priority:high",
                "project:utt",
                "elders-guild",
            ],
        )
        print(f"✅ Created main Epic: #{epic['number']} - {epic_title}")
        epic_number = epic["number"]
    except Exception as e:
        print(f"❌ Failed to create Epic: {e}")
        return

    # Sub Issues定義
    sub_issues = [
        # Phase 1: 基盤構築
        {
            "title": "📐 [UTT-P1-1] データモデル設計・実装",
            "body": """## 📋 タスク内容
統合タスクトラッカーのデータモデルを設計・実装する

## ✅ 完了条件
- [ ] 統一タスクスキーマ定義完了
- [ ] データベーステーブル作成
- [ ] マイグレーションスクリプト実装
- [ ] バリデーションルール実装
- [ ] ドキュメント作成

## 🔧 技術仕様
- SQLAlchemy使用
- 既存DBとの互換性維持
- Elders Legacy準拠

## 📊 見積もり
- 予定工数: 2日
- 優先度: Critical

## 🏷️ 関連
- Epic: #{epic_number}
- Phase: 1 (基盤構築)
""",
            "labels": ["enhancement", "phase:1", "priority:critical", "size:m"],
            "milestone": "Phase 1: Foundation",
        },
        {
            "title": "🛠️ [UTT-P1-2] 基本CRUD実装",
            "body": """## 📋 タスク内容
タスクの基本的なCRUD操作を実装する

## ✅ 完了条件
- [ ] Create（タスク作成）API実装
- [ ] Read（タスク取得）API実装
- [ ] Update（タスク更新）API実装
- [ ] Delete（タスク削除）API実装
- [ ] 履歴管理機能実装
- [ ] 検索・フィルタリング機能実装
- [ ] 100%テストカバレッジ

## 🔧 技術仕様
- 非同期処理対応
- バッチ操作サポート
- トランザクション管理

## 📊 見積もり
- 予定工数: 3日
- 優先度: Critical

## 🏷️ 関連
- Epic: #{epic_number}
- Phase: 1 (基盤構築)
- 依存: データモデル設計
""",
            "labels": ["enhancement", "phase:1", "priority:critical", "size:l"],
            "milestone": "Phase 1: Foundation",
        },
        {
            "title": "🧪 [UTT-P1-3] テスト基盤構築",
            "body": """## 📋 タスク内容
包括的なテスト基盤を構築する

## ✅ 完了条件
- [ ] ユニットテストフレームワーク設定
- [ ] 統合テスト環境構築
- [ ] パフォーマンステスト実装
- [ ] モックデータ生成ツール
- [ ] CI/CD統合
- [ ] カバレッジレポート設定

## 🔧 技術仕様
- pytest使用
- テストデータファクトリー
- 並列テスト実行

## 📊 見積もり
- 予定工数: 2日
- 優先度: High

## 🏷️ 関連
- Epic: #{epic_number}
- Phase: 1 (基盤構築)
""",
            "labels": ["test", "phase:1", "priority:high", "size:m"],
            "milestone": "Phase 1: Foundation",
        },
        # Phase 2: 統合実装
        {
            "title": "🧙‍♂️ [UTT-P2-1] 4賢者システム統合",
            "body": """## 📋 タスク内容
4賢者システムとの完全統合を実装する

## ✅ 完了条件
- [ ] タスク賢者との連携実装
- [ ] ナレッジ賢者への自動記録
- [ ] インシデント賢者の監視統合
- [ ] RAG賢者の検索統合
- [ ] 賢者間通信プロトコル実装
- [ ] 統合テスト実施

## 🔧 技術仕様
- 非同期メッセージング
- イベント駆動アーキテクチャ
- 賢者APIラッパー実装

## 📊 見積もり
- 予定工数: 3日
- 優先度: Critical

## 🏷️ 関連
- Epic: #{epic_number}
- Phase: 2 (統合実装)
- 依存: 基本CRUD実装
""",
            "labels": ["enhancement", "phase:2", "priority:critical", "size:l"],
            "milestone": "Phase 2: Integration",
        },
        {
            "title": "🌊 [UTT-P2-2] Elder Flow統合",
            "body": """## 📋 タスク内容
Elder Flowワークフローエンジンとの統合

## ✅ 完了条件
- [ ] ワークフロー自動化実装
- [ ] ステータス自動更新機能
- [ ] 品質ゲート連携
- [ ] フロー定義インターフェース
- [ ] 実行監視ダッシュボード
- [ ] エラーハンドリング強化

## 🔧 技術仕様
- Elder Flow API統合
- リアルタイムステータス同期
- ワークフロー定義DSL

## 📊 見積もり
- 予定工数: 3日
- 優先度: High

## 🏷️ 関連
- Epic: #{epic_number}
- Phase: 2 (統合実装)
""",
            "labels": ["enhancement", "phase:2", "priority:high", "size:l"],
            "milestone": "Phase 2: Integration",
        },
        {
            "title": "🤖 [UTT-P2-3] サーバント統合",
            "body": """## 📋 タスク内容
エルダーサーバント部隊との統合実装

## ✅ 完了条件
- [ ] 自動タスク割当アルゴリズム
- [ ] サーバント能力マッチング
- [ ] 進捗リアルタイムトラッキング
- [ ] 完了報告自動化
- [ ] 負荷分散メカニズム
- [ ] パフォーマンス監視

## 🔧 技術仕様
- サーバントレジストリ統合
- スキルベースルーティング
- 自動エスカレーション

## 📊 見積もり
- 予定工数: 2日
- 優先度: Medium

## 🏷️ 関連
- Epic: #{epic_number}
- Phase: 2 (統合実装)
""",
            "labels": ["enhancement", "phase:2", "priority:medium", "size:m"],
            "milestone": "Phase 2: Integration",
        },
        # Phase 3: GitHub連携
        {
            "title": "🔗 [UTT-P3-1] GitHub API統合",
            "body": """## 📋 タスク内容
GitHub APIとの包括的な統合を実装

## ✅ 完了条件
- [ ] Issue作成・更新API実装
- [ ] ラベル管理自動化
- [ ] マイルストーン同期
- [ ] アサイン自動化
- [ ] プロジェクトボード連携
- [ ] レート制限対策

## 🔧 技術仕様
- PyGithub使用
- 非同期API呼び出し
- キャッシング戦略

## 📊 見積もり
- 予定工数: 3日
- 優先度: High

## 🏷️ 関連
- Epic: #{epic_number}
- Phase: 3 (GitHub連携)
""",
            "labels": ["enhancement", "phase:3", "priority:high", "size:l"],
            "milestone": "Phase 3: GitHub Integration",
        },
        {
            "title": "🔄 [UTT-P3-2] 同期メカニズム実装",
            "body": """## 📋 タスク内容
内部DBとGitHubの双方向同期を実装

## ✅ 完了条件
- [ ] 選択的同期ルールエンジン
- [ ] 双方向同期プロトコル
- [ ] コンフリクト解決アルゴリズム
- [ ] 同期状態監視
- [ ] ロールバック機能
- [ ] 同期ログ記録

## 🔧 技術仕様
- イベントソーシング
- CRDT使用検討
- 楽観的ロック

## 📊 見積もり
- 予定工数: 4日
- 優先度: Critical

## 🏷️ 関連
- Epic: #{epic_number}
- Phase: 3 (GitHub連携)
- 依存: GitHub API統合
""",
            "labels": ["enhancement", "phase:3", "priority:critical", "size:xl"],
            "milestone": "Phase 3: GitHub Integration",
        },
        {
            "title": "🪝 [UTT-P3-3] Webhook処理実装",
            "body": """## 📋 タスク内容
GitHub Webhookのリアルタイム処理を実装

## ✅ 完了条件
- [ ] Webhookエンドポイント実装
- [ ] イベントハンドラー作成
- [ ] リアルタイム状態更新
- [ ] セキュリティ検証
- [ ] リトライメカニズム
- [ ] イベントログ記録

## 🔧 技術仕様
- FastAPI使用
- 署名検証実装
- 非同期イベント処理

## 📊 見積もり
- 予定工数: 2日
- 優先度: Medium

## 🏷️ 関連
- Epic: #{epic_number}
- Phase: 3 (GitHub連携)
""",
            "labels": ["enhancement", "phase:3", "priority:medium", "size:m"],
            "milestone": "Phase 3: GitHub Integration",
        },
        # Phase 4: UI/UX・最適化
        {
            "title": "💻 [UTT-P4-1] CLI強化",
            "body": """## 📋 タスク内容
統合CLIツールの実装と既存CLI統合

## ✅ 完了条件
- [ ] 統一コマンド体系設計
- [ ] インタラクティブモード実装
- [ ] バッチ操作サポート
- [ ] 自動補完機能
- [ ] ヘルプシステム強化
- [ ] エイリアス設定

## 🔧 技術仕様
- Click使用
- Rich出力対応
- 設定ファイル対応

## 📊 見積もり
- 予定工数: 3日
- 優先度: High

## 🏷️ 関連
- Epic: #{epic_number}
- Phase: 4 (UI/UX・最適化)
""",
            "labels": ["enhancement", "phase:4", "priority:high", "size:l"],
            "milestone": "Phase 4: UI/UX & Optimization",
        },
        {
            "title": "📊 [UTT-P4-2] ダッシュボード実装",
            "body": """## 📋 タスク内容
Webベースの統合ダッシュボード実装

## ✅ 完了条件
- [ ] リアルタイムダッシュボード
- [ ] 統計・分析ビュー
- [ ] カスタムウィジェット
- [ ] モバイル対応
- [ ] ダークモード対応
- [ ] エクスポート機能

## 🔧 技術仕様
- FastAPI + React
- WebSocket使用
- チャート表示

## 📊 見積もり
- 予定工数: 4日
- 優先度: Medium

## 🏷️ 関連
- Epic: #{epic_number}
- Phase: 4 (UI/UX・最適化)
""",
            "labels": ["enhancement", "phase:4", "priority:medium", "size:xl"],
            "milestone": "Phase 4: UI/UX & Optimization",
        },
        {
            "title": "⚡ [UTT-P4-3] パフォーマンス最適化",
            "body": """## 📋 タスク内容
システム全体のパフォーマンス最適化

## ✅ 完了条件
- [ ] クエリ最適化完了
- [ ] インデックス設計見直し
- [ ] キャッシュ戦略実装
- [ ] 非同期処理強化
- [ ] メモリ使用量最適化
- [ ] ベンチマーク達成

## 🔧 技術仕様
- Redis統合
- 接続プール最適化
- プロファイリング実施

## 📊 見積もり
- 予定工数: 3日
- 優先度: High

## 🏷️ 関連
- Epic: #{epic_number}
- Phase: 4 (UI/UX・最適化)
""",
            "labels": ["performance", "phase:4", "priority:high", "size:l"],
            "milestone": "Phase 4: UI/UX & Optimization",
        },
    ]

    # Sub Issues作成
    created_issues = []
    for idx, issue_data in enumerate(sub_issues, 1):
        try:
            sub_issue = create_issue(
                title=issue_data["title"],
                body=issue_data["body"].replace(f"#{epic_number}", f"#{epic_number}"),
                labels=issue_data["labels"],
            )
            created_issues.append(sub_issue)
            print(
                f"✅ Created Sub Issue {idx}/12: #{sub_issue['number']} - {issue_data['title']}"
            )
        except Exception as e:
            print(f"❌ Failed to create Sub Issue {idx}: {e}")

    # Epic Issueの本文を更新（実際のIssue番号で）
    if created_issues:
        updated_body = epic_body
        for idx, issue in enumerate(created_issues):
            updated_body = updated_body.replace(
                f"#ISSUE_{idx+1}", f"#{issue['number']}"
            )

        try:
            update_data = {"body": updated_body}
            response = requests.patch(
                f"{API_BASE_URL}/issues/{epic_number}",
                json=update_data,
                headers=HEADERS,
            )
            if response.status_code == 200:
                print(f"✅ Updated Epic with actual Sub Issue numbers")
            else:
                print(
                    f"❌ Failed to update Epic: {response.status_code} - {response.text}"
                )
        except Exception as e:
            print(f"❌ Failed to update Epic: {e}")

    print(
        f"\n🎉 Successfully created {len(created_issues) + 1} issues for UTT project!"
    )
    print(f"📊 Epic Issue: #{epic_number}")
    print(f"📋 Sub Issues: {', '.join([f'#{i['number']}' for i in created_issues])}")

    # サマリー
    print("\n📊 Project Summary:")
    print(f"- Total Issues: {len(created_issues) + 1}")
    print(f"- Phases: 4")
    print(f"- Estimated Duration: 4 weeks")
    print(f"- Priority: High/Critical")


if __name__ == "__main__":
    create_utt_issues()
