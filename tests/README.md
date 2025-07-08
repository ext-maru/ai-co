# 🧪 AI Company テスト自動化システム

## 概要

AI Companyのテスト自動化システムは、GitHub Actionsと連携した包括的なテストフレームワークです。AIを活用して自動的にテストを生成し、継続的な品質向上を実現します。

## 主な機能

### 1. **3層テスト戦略**
- **ユニットテスト**: 個別関数・メソッドの動作検証
- **統合テスト**: コンポーネント間の連携確認
- **E2Eテスト**: システム全体のワークフロー検証

### 2. **AI駆動テスト生成**
- カバレッジが低いコードを自動検出
- Claude AIがコンテキストを理解してテストを生成
- エッジケースとエラーシナリオを網羅

### 3. **GitHub Actions CI/CD**
- push/PRで自動テスト実行
- 並列実行による高速化
- セキュリティスキャンとコード品質チェック

### 4. **カバレッジ追跡**
- リアルタイムカバレッジモニタリング
- コンポーネント別の目標設定（workers: 85%, libs: 90%）
- HTMLレポートとバッジ生成

## クイックスタート

### 基本的な使用方法

```bash
# 全テスト実行
ai-test

# ユニットテストのみ
ai-test unit

# カバレッジレポート生成
ai-test coverage --html

# AIによるテスト自動生成
ai-test generate
```

### CI/CDワークフロー

```yaml
# プッシュ時に自動実行
on:
  push:
    branches: [main, develop]
```

## ディレクトリ構造

```
tests/
├── unit/           # ユニットテスト
├── integration/    # 統合テスト  
├── e2e/           # E2Eテスト
└── fixtures/      # テストフィクスチャ

.github/
└── workflows/
    └── ci.yml     # GitHub Actions設定
```

## テスト作成ガイドライン

### 1. 命名規則
- ファイル名: `test_[module_name].py`
- クラス名: `Test[ClassName]`
- メソッド名: `test_[what_it_does]`

### 2. マーカー使用
```python
@pytest.mark.unit          # ユニットテスト
@pytest.mark.integration   # 統合テスト
@pytest.mark.e2e          # E2Eテスト
@pytest.mark.slow         # 遅いテスト
@pytest.mark.ai_generated # AI生成テスト
```

### 3. フィクスチャ活用
```python
@pytest.fixture
def mock_claude():
    """Claude CLIのモック"""
    with patch('libs.claude_cli_executor.ClaudeCLIExecutor') as mock:
        yield mock
```

## TestGeneratorWorker

AIによるテスト自動生成を担当するワーカーです。

### 動作フロー
1. カバレッジ分析
2. 不足箇所の特定
3. コード構造解析
4. テスト生成プロンプト構築
5. Claude実行
6. テスト検証
7. 自動配置

### トリガー方法
```bash
# 手動実行
ai-test generate

# スケジュール実行（GitHub Actions）
# 毎日午前2時に自動実行
```

## カバレッジ目標

| コンポーネント | 目標 | 現在 |
|-------------|-----|-----|
| 全体         | 80% | -   |
| workers/    | 85% | -   |
| libs/       | 90% | -   |

## トラブルシューティング

### テストが見つからない
```bash
# pytestパス確認
pytest --collect-only

# マーカー確認
pytest --markers
```

### カバレッジが計測されない
```bash
# .coveragercファイル確認
cat .coveragerc

# カバレッジ再計算
coverage erase
pytest --cov=workers --cov=libs
```

### CI/CDエラー
- ログを確認: Actions → ワークフロー → 失敗したジョブ
- ローカルで再現: `ai-test --ci`

## ベストプラクティス

1. **テストファースト開発**
   - 機能実装前にテストを書く
   - TDDサイクルを意識

2. **モックの適切な使用**
   - 外部依存は必ずモック
   - 実装詳細ではなくインターフェースをテスト

3. **読みやすいテスト**
   - Arrange-Act-Assertパターン
   - 説明的な変数名とアサーション

4. **継続的改善**
   - 定期的なテストレビュー
   - AIが生成したテストも人間がレビュー

## 今後の拡張予定

- [ ] ミューテーションテスト導入
- [ ] プロパティベーステスト
- [ ] パフォーマンステスト自動化
- [ ] ビジュアルリグレッションテスト
- [ ] テストインパクト分析

## 関連ドキュメント

- [AI Company ナレッジベース](../docs/knowledge_base.md)
- [開発ガイドライン](../docs/development.md)
- [CI/CD設定](../.github/workflows/ci.yml)

---

**🎯 高品質なコードは包括的なテストから生まれます**
