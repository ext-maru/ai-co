# Developer Guides

Auto Issue Processor A2Aの開発者向けドキュメントです。

## 💻 開発ガイド

### 🔥 主要ドキュメント
- **[コントリビューションガイド](contribution-guide.md)** - 開発参加の完全ガイド
- **[アーキテクチャ概要](architecture-overview.md)** - システム設計と主要コンポーネント

### 📋 開発内容

#### 🤝 貢献方法
- **エルダーズギルド開発原則** - Iron Will、TDD必須、4賢者システム
- **ブランチ戦略** - Feature Branch必須化（エルダー評議会令第32号）
- **コーディング規約** - Python、テスト駆動開発
- **プルリクエストプロセス** - レビュー基準、品質ゲート

#### 🏗️ システム理解
- **8つのコアコンポーネント** - 統一ワークフロー、セキュリティ、監視等
- **4賢者システム** - ナレッジ、タスク、インシデント、RAG賢者
- **Elder Flow統合** - 自動化フロー
- **SafeGitOperations** - 安全なGit操作（v2.0新機能）

## 🧪 テストとテクノロジー

### TDD必須方針
```python
# 1. テストを先に書く（Red）
def test_new_feature():
    assert new_feature() == expected_result

# 2. 最小実装（Green）
def new_feature():
    return expected_result

# 3. リファクタリング（Refactor）
```

### 技術スタック
- **言語**: Python 3.8+
- **フレームワーク**: AsyncIO、GitHub API、Claude API
- **テスト**: pytest、覆盖率95%以上
- **品質**: flake8、black、mypy

## 🎯 開発フロー

### 新機能開発手順
1. **Issue作成** - GitHub Issue作成
2. **ブランチ作成** - `./scripts/git-feature <issue-number> <description>`
3. **TDD開発** - テスト → 実装 → リファクタリング
4. **PR作成** - 4賢者レビュー必須
5. **品質ゲート** - 自動品質チェック
6. **マージ** - 承認後自動マージ

### 開発環境セットアップ
```bash
# リポジトリクローン
git clone https://github.com/ext-maru/ai-co.git
cd ai-co

# 開発環境構築
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4賢者システム確認
python3 -c "from libs.knowledge_sage import KnowledgeSage; print('OK')"
```

## 🔗 技術ドキュメント

### 詳細仕様
- **[technical](../technical/)ディレクトリ** - 技術仕様書
- **[API リファレンス](../api/)** - API詳細仕様
- **[包括的ドキュメント v2.0](../AUTO_ISSUE_PROCESSOR_A2A_COMPLETE_DOCUMENTATION_V2.md)** - システム全体概要

### サポート
- **バグ報告**: [GitHub Issues](https://github.com/ext-maru/ai-co/issues)
- **機能提案**: [Feature Request](https://github.com/ext-maru/ai-co/issues/new?template=feature_request.md)
- **質問**: [GitHub Discussions](https://github.com/ext-maru/ai-co/discussions)

---
*最終更新: 2025年7月21日*