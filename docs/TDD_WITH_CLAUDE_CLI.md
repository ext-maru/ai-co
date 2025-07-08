# Claude CLIでのTDD実践ガイド

## 🤖 Claude CLIとTDDの組み合わせ

Claude CLIを使用した開発でも、TDDは非常に効果的です。むしろ、AIと協働する際にこそTDDが重要になります。

## 📋 基本的な流れ

### 1. テストファースト開発の依頼

```bash
# Claude CLIにTDDでの開発を依頼
ai-send "新しいデータ集計ワーカーをTDDで開発してください。まずテストから書いて、Red-Green-Refactorサイクルで実装してください"

# または、より具体的に
ai-send "CSVファイルを読み込んで集計するDataAggregatorWorkerをTDDで作成。以下の要件で：
1. CSVファイルのパスを受け取る
2. 指定されたカラムの合計を計算
3. 結果をJSONで返す
まずtest_data_aggregator_worker.pyから作成してください"
```

### 2. Claude CLIでのTDDサイクル

#### Red Phase（失敗するテストを書く）
```python
# Claude CLIが最初に生成するテスト例
def test_should_aggregate_csv_data():
    """CSVデータを正しく集計できることを確認"""
    # Arrange
    worker = DataAggregatorWorker()
    csv_path = "test_data.csv"
    column = "amount"
    
    # Act
    result = worker.aggregate(csv_path, column)
    
    # Assert
    assert result["total"] == 1500
    assert result["count"] == 3
```

#### Green Phase（最小限の実装）
```python
# Claude CLIが次に生成する実装
class DataAggregatorWorker(BaseWorker):
    def aggregate(self, csv_path, column):
        # 最小限の実装でテストを通す
        return {"total": 1500, "count": 3}
```

#### Refactor Phase（改善）
```python
# Claude CLIが最後に改善する実装
class DataAggregatorWorker(BaseWorker):
    def aggregate(self, csv_path, column):
        df = pd.read_csv(csv_path)
        return {
            "total": df[column].sum(),
            "count": len(df),
            "average": df[column].mean()
        }
```

## 🎯 Claude CLIへの効果的な指示

### 良い例 ✅

```bash
# 明確なTDD指示
ai-send "UserAuthenticationManagerをTDDで開発:
1. まずtest_user_authentication_manager.pyを作成
2. 以下のテストケースを含める：
   - ユーザー登録成功
   - 重複ユーザー登録失敗
   - ログイン成功
   - 無効な認証情報でログイン失敗
3. テストが失敗することを確認してから実装
4. 各テスト通過後にリファクタリング"

# 既存コードの改善
ai-send "libs/report_generator.pyにテストを追加:
1. 現在のカバレッジを確認
2. カバーされていない部分のテストを追加
3. エッジケースとエラーハンドリングのテスト
4. モックを使用して外部依存を分離"
```

### 避けるべき例 ❌

```bash
# 曖昧な指示
ai-send "新しい機能を作って"

# テストを後回しにする指示
ai-send "まず機能を実装して、後でテストを書いて"
```

## 🔧 Claude CLI専用TDDコマンド

### 1. TDD開発リクエスト生成

```bash
#!/bin/bash
# scripts/ai-tdd-request.sh

FEATURE=$1
REQUIREMENTS=$2

cat << EOF | ai-send --stdin
以下の機能をTDDで開発してください：

機能名: $FEATURE
要件: $REQUIREMENTS

手順:
1. テストファイルをtests/unit/に作成
2. Red: 失敗するテストを書く
3. Green: 最小限のコードでテストを通す
4. Refactor: コードを改善
5. カバレッジ90%以上を目指す

使用するツール:
- pytest
- pytest-mock
- coverage

テストには以下を含めてください:
- 正常系テスト
- 異常系テスト
- エッジケース
- モックを使った外部依存の分離
EOF
```

### 2. テスト生成専用リクエスト

```bash
#!/bin/bash
# scripts/ai-generate-tests.sh

FILE_PATH=$1

ai-send "
$FILE_PATH のテストを生成してください:

1. 現在のコードを分析
2. 不足しているテストケースを特定
3. 以下の観点でテストを作成:
   - 全ての公開メソッド
   - エラーハンドリング
   - 境界値
   - 並行処理（該当する場合）
4. カバレッジ95%を目標
5. pytestのベストプラクティスに従う
"
```

## 📊 Claude CLIでのテスト分析

```bash
# テストカバレッジの改善を依頼
ai-send "現在のテストカバレッジを分析して改善案を提示:
1. coverage run -m pytest でカバレッジ測定
2. coverage report で現状確認
3. カバーされていない部分を特定
4. 優先順位をつけてテスト追加提案"

# テストの品質改善
ai-send "tests/ディレクトリのテストを分析:
1. 重複しているテストの特定
2. 不足しているアサーションの追加
3. テストの可読性改善
4. パフォーマンスの最適化提案"
```

## 🎓 Claude CLIとのペアプログラミング

### TDDセッション例

```bash
# セッション開始
ai-dialog "TDDセッションを開始します。EmailNotificationWorkerを一緒に開発しましょう"

# 対話形式で進める
> まず、どんなテストから書くべきですか？
< 最初は基本的なメール送信成功のテストから始めましょう...

> テストを実行したら失敗しました。次は？
< 完璧です！これがRedフェーズです。次は最小限の実装を...

> リファクタリングのポイントは？
< 以下の点を改善できます：1) エラーハンドリングの共通化...
```

## 🚀 自動化されたTDDワークフロー

### Claude CLI + TDDの自動化

```python
#!/usr/bin/env python3
# scripts/ai-tdd-workflow.py

import subprocess
import time

def run_tdd_cycle(feature_name, requirements):
    """Claude CLIを使用したTDDサイクルの自動実行"""
    
    # 1. テスト生成を依頼
    print("🔴 Red Phase: テスト生成中...")
    subprocess.run([
        "ai-send",
        f"{feature_name}のテストを作成: {requirements}"
    ])
    
    time.sleep(30)  # 処理待ち
    
    # 2. テスト実行
    print("📋 テスト実行中...")
    result = subprocess.run(
        ["pytest", f"tests/unit/test_{feature_name}.py", "-v"],
        capture_output=True
    )
    
    if result.returncode == 0:
        print("⚠️ テストが通ってしまいました。テストを見直してください")
        return
    
    # 3. 実装を依頼
    print("🟢 Green Phase: 実装中...")
    subprocess.run([
        "ai-send",
        f"テストが失敗しています。最小限の実装でテストを通してください"
    ])
    
    time.sleep(30)
    
    # 4. テスト再実行
    result = subprocess.run(
        ["pytest", f"tests/unit/test_{feature_name}.py", "-v"],
        capture_output=True
    )
    
    if result.returncode != 0:
        print("❌ テストがまだ失敗しています")
        return
    
    # 5. リファクタリング依頼
    print("🔵 Refactor Phase: 改善中...")
    subprocess.run([
        "ai-send",
        "テストが通りました！コードをリファクタリングして品質を向上させてください"
    ])
```

## 📈 メトリクスとレポート

```bash
# Claude CLIにメトリクス分析を依頼
ai-send "TDDメトリクスレポートを生成:
1. 各モジュールのテストカバレッジ
2. テスト実行時間の分析
3. 最も頻繁に失敗するテスト
4. テストコードとプロダクションコードの比率
5. 改善提案"
```

## 🎯 ベストプラクティス

1. **明確な要件定義**: Claude CLIに依頼する前に要件を整理
2. **段階的な開発**: 一度に大きな機能ではなく、小さな単位で
3. **継続的な確認**: 各フェーズでテストを実行
4. **対話的な改善**: ai-dialogを使用してインタラクティブに開発
5. **自動化の活用**: 繰り返しタスクはスクリプト化

## 🔍 トラブルシューティング

### Claude CLIがテストを書かない場合
```bash
ai-send "必ずテストファーストで開発してください。最初にテストを書いて、それが失敗することを確認してから実装に進んでください"
```

### テストが複雑すぎる場合
```bash
ai-send "テストをもっとシンプルに分割してください。1つのテストメソッドは1つの振る舞いのみをテストするようにしてください"
```

### カバレッジが低い場合
```bash
ai-send "現在のカバレッジは{X}%です。以下の部分のテストを追加してください: [未カバー部分のリスト]"
```

---

**Claude CLIでもTDD: Red → Green → Refactor** 🤖🔴🟢🔵