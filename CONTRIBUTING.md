# 🤝 AI Company Contributing Guide

## 📋 概要

AI Companyへの貢献を歓迎します！このガイドは、プロジェクトへの貢献方法とベストプラクティスについて説明します。

## 🚀 はじめに

### 必要な環境
- Ubuntu 24.04 LTS (WSL2対応)
- Python 3.12+
- RabbitMQ
- pytest

### セットアップ
```bash
# リポジトリのクローン
git clone https://github.com/YOUR_USERNAME/ai-company.git
cd ai-company

# 仮想環境の作成
python3 -m venv venv
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
pip install -r requirements-dev.txt

# pre-commitフックの設定
pre-commit install
```

## 🧪 テスト駆動開発（TDD）必須

**重要**: AI Companyのすべての開発はTDDで行います。コードを書く前に必ずテストを書いてください。

### TDDワークフロー
1. **Red**: 失敗するテストを先に書く
2. **Green**: 最小限の実装でテストを通す
3. **Refactor**: コードを改善する

### テストの実行
```bash
# ユニットテストの実行
pytest tests/unit/

# カバレッジレポートの生成
pytest --cov=. --cov-report=html

# 特定のテストのみ実行
pytest tests/unit/test_base_worker.py::TestBaseWorker::test_stats_tracking
```

## 📝 コーディング規約

### Pythonコードスタイル
- PEP 8に準拠
- 最大行長: 120文字
- インデント: スペース4つ
- 関数・変数名: snake_case
- クラス名: PascalCase

### 構文エラーを避けるために
1. **エスケープシーケンス**: raw文字列を使用するか、適切にエスケープ
   ```python
   # Good
   pattern = r"test\d+"
   path = "path\\to\\file"
   
   # Bad
   pattern = "test\d+"  # SyntaxWarning
   ```

2. **文字列リテラル**: トリプルクォートは正しく閉じる
   ```python
   # Good
   description = """
   Multi-line
   description
   """
   
   # Bad
   description = """
   Unclosed string
   ```

3. **インポート**: 使用前に依存関係を確認
   ```python
   # Good
   try:
       from PIL import Image
       PIL_AVAILABLE = True
   except ImportError:
       PIL_AVAILABLE = False
   ```

## 🏗️ BaseWorker統計機能の使用

新しいワーカーを作成する際は、BaseWorkerの統計機能を活用してください：

```python
from core.base_worker import BaseWorker

class MyWorker(BaseWorker):
    def __init__(self):
        super().__init__(worker_type='my_worker')
        # self.stats は自動的に初期化される
    
    def process_message(self, ch, method, properties, body):
        try:
            # メッセージ処理
            result = self.do_work(body)
            
            # 統計を更新
            self.stats['processed_count'] += 1
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            # handle_errorが自動的にstats['error_count']を更新
            self.handle_error(e, "process_message")
            ch.basic_nack(delivery_tag=method.delivery_tag)
```

## 📊 テストカバレッジ目標

### 現在の状況（2025年7月）
- コアモジュール: 15.62%
- 目標: 段階的な改善

### 新規コードの基準
- 新規コード: 最低90%のカバレッジ
- バグ修正: 修正箇所のテストを必ず追加

## 🔄 プルリクエストのプロセス

1. **Issue作成**: 作業開始前にIssueを作成
2. **ブランチ作成**: `feature/issue-番号-機能名` 形式
3. **TDDで開発**: テストを先に書く
4. **コミット**: 意味のある単位でコミット
5. **プルリクエスト**: テンプレートに従って作成

### コミットメッセージ
```
feat: 新機能の追加
fix: バグ修正
docs: ドキュメントのみの変更
style: コードスタイルの変更
refactor: リファクタリング
test: テストの追加・修正
chore: ビルドプロセスや補助ツールの変更
```

## 🐛 バグ報告

### Issueテンプレート
```markdown
## 概要
バグの簡潔な説明

## 再現手順
1. ...
2. ...

## 期待される動作
正常な場合の動作

## 実際の動作
現在の問題のある動作

## 環境
- OS: Ubuntu 24.04
- Python: 3.12.x
- 関連パッケージのバージョン
```

## 📚 ドキュメント

### ドキュメント更新時の注意
1. READMEは実際の状態を反映する（カバレッジ率など）
2. 新機能は必ずドキュメント化
3. コード例は動作確認済みのものを使用

### 重要なドキュメント
- [CLAUDE.md](CLAUDE.md) - Claude CLI開発ガイド
- [docs/TESTING_STANDARDS.md](docs/TESTING_STANDARDS.md) - テスト標準
- [knowledge_base/](knowledge_base/) - ナレッジベース

## 🎯 貢献のチェックリスト

- [ ] テストを先に書いた（TDD）
- [ ] すべてのテストが通る
- [ ] カバレッジが低下していない
- [ ] 構文エラーがない
- [ ] ドキュメントを更新した
- [ ] コミットメッセージが規約に従っている
- [ ] PRテンプレートを埋めた

## 🙏 行動規範

- 建設的なフィードバックを心がける
- 多様性を尊重する
- 質問を歓迎する
- 初心者にも親切に

## 📞 サポート

質問がある場合は：
1. [ドキュメント](docs/)を確認
2. [既存のIssue](https://github.com/YOUR_USERNAME/ai-company/issues)を検索
3. 新しいIssueを作成

---

**ありがとうございます！** あなたの貢献がAI Companyをより良いものにします。