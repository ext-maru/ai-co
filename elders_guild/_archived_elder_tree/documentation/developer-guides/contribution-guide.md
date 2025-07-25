# Auto Issue Processor A2A コントリビューションガイド

## 🤝 概要

Auto Issue Processor A2Aプロジェクトへの貢献を歓迎します！このガイドでは、コードの貢献方法とプロジェクトの開発規約について説明します。

## 🏛️ エルダーズギルド開発原則

### Iron Will (鉄の意志)
- **No Workarounds**: 回避策は禁止、根本解決のみ
- **No TODO/FIXME**: 未完成のコードはコミットしない
- **Test First**: テストなしのコードは存在しない

### 4賢者システムの尊重
すべての重要な変更は4賢者（Knowledge、Task、Incident、RAG）の承認が必要です。

## 🚀 貢献の始め方

### 1. 開発環境のセットアップ

```bash
# リポジトリをフォーク
# GitHub上でForkボタンをクリック

# フォークしたリポジトリをクローン
git clone https://github.com/YOUR_USERNAME/ai-co.git
cd ai-co

# アップストリームを追加
git remote add upstream https://github.com/ext-maru/ai-co.git

# 開発環境構築
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 開発用依存関係
```

### 2. ブランチ戦略

**エルダー評議会令第32号**に従い、以下のブランチ命名規則を使用：

```bash
# Feature Branch作成ツールを使用
./scripts/git-feature <issue-number> <description>

# 例
./scripts/git-feature 195 documentation-update
# → feature/issue-195-documentation-update
```

ブランチタイプ：
- `feature/issue-XX-description` - 新機能
- `fix/issue-XX-description` - バグ修正
- `docs/issue-XX-description` - ドキュメント
- `chore/issue-XX-description` - 雑務

## 📝 コーディング規約

### Python コードスタイル

```python
#!/usr/bin/env python3
"""
モジュールの説明を記載
Elder Flow準拠のコンポーネント
"""

import os
import sys
from typing import Dict, Any, Optional, List

# Elder System imports
from libs.knowledge_sage import KnowledgeSage
from libs.task_sage import TaskSage


class ElderCompliantClass:
    """クラスの説明"""
    
    def __init__(self):
        """初期化処理"""
        self.knowledge_sage = KnowledgeSage()
        self.task_sage = TaskSage()
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        リクエストを処理
        
        Args:
            request: 処理リクエスト
            
        Returns:
            処理結果
            
        Raises:
            ValueError: 無効なリクエスト
        """
        # 4賢者への相談
        sage_advice = await self._consult_sages(request)
        
        # ビジネスロジック
        result = self._execute_logic(request, sage_advice)
        
        return result
```

### テスト駆動開発（TDD）

**すべてのコードは先にテストを書く**：

```python
# tests/test_new_feature.py
import pytest
from libs.new_feature import NewFeature


class TestNewFeature:
    """新機能のテスト"""
    
    def test_basic_functionality(self):
        """基本機能のテスト"""
        # Given
        feature = NewFeature()
        input_data = {"key": "value"}
        
        # When
        result = feature.process(input_data)
        
        # Then
        assert result["status"] == "success"
        assert result["processed"] is True
    
    @pytest.mark.asyncio
    async def test_async_operation(self):
        """非同期処理のテスト"""
        feature = NewFeature()
        result = await feature.async_process()
        assert result is not None
```

### コミットメッセージ

**Conventional Commits**形式を使用：

```bash
# 形式
<type>(<scope>): <subject> (#<issue>)

# 例
feat(processor): Add template generation support (#184)
fix(sages): Fix RAG Manager process_request error (#156)
docs(runbooks): Add troubleshooting guide (#195)
test(api): Add integration tests for new endpoints
chore(deps): Update dependencies
```

タイプ：
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: フォーマット変更
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド・補助ツール

## 🔍 プルリクエストプロセス

### 1. PR作成前チェックリスト

```bash
# テスト実行
pytest tests/

# コードスタイルチェック
flake8 libs/
black libs/ --check

# 型チェック
mypy libs/

# セキュリティチェック
bandit -r libs/

# カバレッジ確認
pytest --cov=libs tests/
```

### 2. PR作成

```markdown
## 概要
Issue #XXXの対応として、YYY機能を実装しました。

## 変更内容
- [ ] 新機能の追加
- [ ] バグの修正
- [ ] ドキュメントの更新
- [ ] テストの追加

## テスト
- [ ] ユニットテスト追加
- [ ] 統合テスト実行
- [ ] 手動テスト完了

## 4賢者承認
- [ ] Knowledge Sage: ナレッジベース更新
- [ ] Task Sage: タスク影響評価
- [ ] Incident Sage: リスク分析
- [ ] RAG Sage: 関連情報検索

## スクリーンショット
（該当する場合）

Closes #XXX
```

### 3. レビュープロセス

1. **自動チェック**: CI/CDパイプラインでの検証
2. **コードレビュー**: 少なくとも1名のレビュアー承認
3. **4賢者レビュー**: システムへの影響評価
4. **エルダー承認**: 重要変更の場合

## 🧪 テストガイドライン

### テストカバレッジ基準

| コンポーネント | 最小カバレッジ | 推奨カバレッジ |
|---------------|--------------|--------------|
| Core機能 | 90% | 95% |
| 新規コード | 95% | 100% |
| API | 85% | 90% |
| ユーティリティ | 80% | 85% |

### テスト構造

```
tests/
├── unit/           # ユニットテスト
├── integration/    # 統合テスト
├── e2e/           # エンドツーエンドテスト
└── fixtures/      # テストデータ
```

## 🔐 セキュリティガイドライン

### 禁止事項
- APIキーやトークンのハードコーディング
- 機密情報のログ出力
- 安全でない文字列評価（eval、exec）
- 入力検証なしの外部入力使用

### 必須事項
```python
# 環境変数から機密情報を取得
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY not set")

# 入力検証
def validate_input(data: Dict[str, Any]) -> bool:
    """入力データの検証"""
    required_fields = ["issue_number", "priority"]
    return all(field in data for field in required_fields)
```

## 📚 ドキュメント貢献

### ドキュメント構造
```
docs/
├── user-guides/      # エンドユーザー向け
├── developer-guides/ # 開発者向け
├── api/             # API仕様
└── runbooks/        # 運用ドキュメント
```

### ドキュメント品質基準
- 明確で簡潔な説明
- 実行可能なコード例
- 最新の情報を反映
- 日英両言語対応（推奨）

## 🎯 初心者向けタスク

`good first issue`ラベルの付いたIssueから始めることを推奨：

1. ドキュメントの改善
2. テストの追加
3. 小さなバグ修正
4. コードスタイルの改善

## 🤔 質問・サポート

- **Issue**: バグ報告や機能提案
- **Discussions**: 一般的な質問や議論
- **Wiki**: 詳細な技術情報

## 📖 必読リソース

- [エルダーズギルド開発ガイド](../../CLAUDE.md)
- [アーキテクチャ概要](architecture-overview.md)
- [APIリファレンス](../api/auto-issue-processor-api-reference.md)

## 🙏 謝辞

貢献者の皆様に感謝します！あなたの貢献がAuto Issue Processorをより良いものにします。

---
*最終更新: 2025年7月21日*