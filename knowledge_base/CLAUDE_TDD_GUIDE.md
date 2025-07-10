# Claude CLI TDDガイド - Elders Guild公式ガイドライン

## 🎯 概要

このガイドは、Claude CLIを使用してElders Guild内で開発を行う際のTDD（テスト駆動開発）実践方法を定めた公式ガイドラインです。**すべての新規開発はTDDで行うことを必須とします**。

## 🔴🟢🔵 TDD基本原則

### TDDサイクル
1. **🔴 Red**: 失敗するテストを先に書く
2. **🟢 Green**: 最小限の実装でテストを通す  
3. **🔵 Refactor**: コードを改善する

### 鉄則
- ❌ **絶対にNG**: テストなしでコードを書く
- ✅ **必須**: テストが失敗することを確認してから実装

## 📋 Claude CLIへの依頼方法

### 1. 基本的な依頼フォーマット

```bash
ai-send "機能名をTDDで開発:
1. 機能要件: [具体的な要件]
2. 必要なテストケース:
   - 正常系: [期待される動作]
   - 異常系: [エラーケース]
   - 境界値: [エッジケース]
3. まずtest_*.pyを作成してテストが失敗することを確認
4. 最小限の実装でテストを通す
5. リファクタリングで品質向上"
```

### 2. 専用コマンドの使用

```bash
# 新機能開発
ai-tdd new EmailValidator "メールアドレスの形式を検証する機能"

# 既存コードへのテスト追加
ai-tdd test libs/data_processor.py

# カバレッジ改善
ai-tdd coverage workers

# 対話型TDD開発
ai-tdd session "CSV処理機能の設計と実装"
```

## 📝 良い依頼例と悪い依頼例

### ✅ 良い例

```bash
ai-send "UserAuthenticationManagerをTDDで開発:

要件:
- ユーザー登録（メールアドレスとパスワード）
- ログイン認証
- パスワードのハッシュ化

テストケース:
1. test_should_register_user_with_valid_email
   - user@example.com → 成功
2. test_should_reject_invalid_email
   - invalid-email → ValueError
3. test_should_hash_password_on_registration
   - パスワードが平文で保存されないこと
4. test_should_authenticate_valid_credentials
   - 正しい認証情報 → True
5. test_should_reject_invalid_credentials
   - 間違ったパスワード → False

まずこれらのテストをtests/unit/test_user_authentication_manager.pyに作成し、
すべて失敗することを確認してから実装してください。"
```

### ❌ 悪い例

```bash
# 曖昧すぎる
ai-send "ユーザー管理機能を作って"

# TDDを無視
ai-send "UserManagerを実装して、後でテストも追加して"

# テストケースが不明確
ai-send "何かテキトーにテスト書いてUserManager作って"
```

## 🔧 ワーカー開発のTDDフロー

### 1. ワーカー生成

```bash
# TDDテンプレートでワーカーを生成
./scripts/generate-tdd-worker.py DataAggregator data

# 以下が生成される:
# - workers/data_aggregator_worker.py（実装テンプレート）
# - tests/unit/test_data_aggregator_worker.py（テストテンプレート）
```

### 2. Claude CLIでテストを完成させる

```bash
ai-send "生成されたtest_data_aggregator_worker.pyを以下の要件で完成させて:

DataAggregatorWorkerの要件:
1. CSVファイルを読み込む
2. 指定カラムの合計、平均、最大、最小を計算
3. 結果をJSONで返す

エラーケース:
- ファイルが存在しない → FileNotFoundError
- 指定カラムが存在しない → KeyError
- 数値以外のデータ → ValueError

まずこれらのテストケースを実装し、pytest実行ですべて失敗することを確認してください。"
```

### 3. 実装の依頼

```bash
ai-send "test_data_aggregator_worker.pyのテストが失敗しています。
最小限の実装でテストを通してください。
この段階では美しさは求めません。テストが通ることが最優先です。"
```

### 4. リファクタリング

```bash
ai-send "DataAggregatorWorkerのテストが通りました。
以下の観点でリファクタリングしてください:
- コードの可読性向上
- DRY原則の適用
- エラーハンドリングの改善
- パフォーマンスの最適化
テストが通り続けることを確認しながら進めてください。"
```

## 📊 カバレッジ管理

### カバレッジ基準

```bash
# 新規コードは必ず90%以上
ai-send "現在のカバレッジを確認して90%未満の場合は改善:
1. coverage run -m pytest tests/unit/test_*.py
2. coverage report で現状確認
3. 未カバー部分のテストを追加
4. 特にエラーハンドリングとエッジケースに注目"
```

### カバレッジレポート

```bash
# HTMLレポート生成
ai-test-coverage --html

# 継続的監視
ai-test-coverage --watch
```

## 🎓 TDD実践のコツ

### 1. 小さく始める

```bash
ai-send "EmailValidatorをTDDで開発。
まず最もシンプルなケースから:
1. test_should_accept_valid_email
   - 'user@example.com' → True
このテストだけ書いて、失敗を確認後、
最小限の実装（return True）でテストを通してください。"
```

### 2. 段階的に複雑にする

```bash
ai-send "EmailValidatorに次のテストを追加:
2. test_should_reject_email_without_at_sign
   - 'userexample.com' → False
テストが失敗することを確認後、実装を改善してください。"
```

### 3. リファクタリングは安全に

```bash
ai-send "EmailValidatorのリファクタリング:
- 正規表現を使った実装に変更
- すべてのテストが通り続けることを確認
- 新しいエッジケースがあれば先にテストを追加"
```

## 🚀 自動化スクリプト

### TDDワークフロー自動化

```python
#!/usr/bin/env python3
# scripts/ai-tdd-workflow.py

import subprocess
import sys

def run_tdd_cycle(feature_name, requirements):
    # 1. テスト作成依頼
    subprocess.run([
        "ai-send",
        f"{feature_name}のテストを作成: {requirements}"
    ])
    
    # 2. テスト実行（失敗確認）
    result = subprocess.run(
        ["pytest", f"tests/unit/test_{feature_name.lower()}.py", "-v"],
        capture_output=True
    )
    
    if result.returncode == 0:
        print("⚠️ テストが通ってしまいました！")
        sys.exit(1)
    
    # 3. 実装依頼
    subprocess.run([
        "ai-send",
        "テストが失敗しています。最小限の実装でテストを通してください"
    ])
    
    # 4. リファクタリング依頼
    subprocess.run([
        "ai-send",
        "テストが通りました。コードをリファクタリングしてください"
    ])
```

## 📋 チェックリスト

### 新機能開発時

- [ ] テストファイルを最初に作成
- [ ] テストが失敗することを確認
- [ ] 最小限の実装でテストを通す
- [ ] すべてのテストが通ることを確認
- [ ] リファクタリング実施
- [ ] カバレッジ90%以上を確認
- [ ] pre-commitチェックをパス

### 既存コード修正時

- [ ] 変更部分のテストが存在することを確認
- [ ] 新しいテストケースを追加（必要に応じて）
- [ ] テストが失敗することを確認
- [ ] 修正を実装
- [ ] すべてのテストが通ることを確認
- [ ] 回帰テストの実施

## 🔍 トラブルシューティング

### Claude CLIがテストを書かない場合

```bash
ai-send "重要: 必ずテストファーストで開発してください。
1. まずtest_*.pyファイルを作成
2. テストケースを実装
3. pytestでテストが失敗することを確認
4. その後で実装に進む
この順序を必ず守ってください。"
```

### テストが最初から通ってしまう場合

```bash
ai-send "テストが最初から通っています。これはTDD違反です。
より厳密なアサーションを追加してテストを失敗させてください:
- 具体的な戻り値をチェック
- エッジケースを追加
- 例外発生を確認"
```

### カバレッジが上がらない場合

```bash
ai-send "カバレッジレポートを確認して以下を実施:
1. coverage html でHTMLレポート生成
2. 赤い（未カバー）行を特定
3. その行を通るテストケースを追加
特に以下に注意:
- except節のエラーハンドリング
- if文の両方の分岐
- ループの0回、1回、複数回のケース"
```

## 📚 参考資料

- [TDD_WORKFLOW.md](/home/aicompany/ai_co/docs/TDD_WORKFLOW.md) - 一般的なTDDワークフロー
- [TDD_WITH_CLAUDE_CLI.md](/home/aicompany/ai_co/docs/TDD_WITH_CLAUDE_CLI.md) - Claude CLI特有のTDD手法
- [TDD_TEST_RULES.md](/home/aicompany/ai_co/tests/TDD_TEST_RULES.md) - テスト作成ルール

## 🎯 まとめ

Claude CLIを使用する際も、通常の開発と同じくTDDの原則を守ることが重要です。AIの力を借りることで、より効率的にTDDサイクルを回すことができます。

**Remember: Always Red → Green → Refactor** 🔴🟢🔵