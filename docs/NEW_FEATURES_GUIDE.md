# 🚀 Elders Guild 新機能ガイド

## 📝 タスクテンプレート機能

### 概要
よく使うタスクをテンプレート化して、簡単に再利用できます。

### 基本コマンド

```bash
# テンプレート一覧
ai-template list

# テンプレート詳細
ai-template show daily_report

# テンプレート実行
ai-template run daily_report --params date=2025-07-02

# 人気テンプレート
ai-template popular
```

### 組み込みテンプレート

1. **daily_report** - 日次レポート生成
   ```bash
   ai-template run daily_report --params date=today
   ```

2. **code_review** - コードレビュー
   ```bash
   ai-template run code_review --params file_path=/home/aicompany/ai_co/workers/task_worker.py
   ```

3. **api_client** - APIクライアント生成
   ```bash
   ai-template run api_client --params language=python base_url=https://api.example.com auth_type=api_key
   ```

4. **data_analysis** - データ分析
   ```bash
   ai-template run data_analysis --params data_source=/path/to/data.csv output_format=markdown
   ```

### カスタムテンプレート作成

#### インタラクティブ作成
```bash
ai-template create
```

#### ファイルから作成
```yaml
# my_template.yaml
name: "My Custom Template"
description: "Custom task template"
task_type: "code"
template_data:
  prompt: |
    Create a {{component_type}} with the following features:
    - Name: {{name}}
    - Description: {{description}}
    {{#if include_tests}}
    - Include unit tests
    {{/if}}
parameters:
  - name: component_type
    type: string
    description: "Type of component"
    choices: ["worker", "manager", "script"]
    default: "worker"
  - name: name
    type: string
    description: "Component name"
    required: true
  - name: description
    type: string
    description: "Component description"
  - name: include_tests
    type: bool
    description: "Include unit tests"
    default: true
tags:
  - custom
  - development
```

```bash
ai-template create --file my_template.yaml
```

### テンプレートのエクスポート/インポート

```bash
# エクスポート
ai-template export daily_report --format yaml > daily_report.yaml

# インポート
ai-template import custom_template.yaml
```

## 🔗 ワーカー間通信機能

### 概要
ワーカー同士が協調して動作できる通信システムです。

### 基本コマンド

```bash
# 通信ルート確認
ai-worker-comm routes

# メッセージ送信
ai-worker-comm send pm file_created --data '{"file": "/tmp/test.py"}'

# 通信モニタリング
ai-worker-comm monitor --verbose

# 通信テスト
ai-worker-comm test
```

### 実装例

```python
from core import BaseWorker
from core.worker_communication import CommunicationMixin

class MyWorker(BaseWorker, CommunicationMixin):
    def __init__(self):
        super().__init__(worker_type='my_worker')
        self.setup_communication()
        
        # メッセージハンドラー登録
        self.register_message_handler('task_request', self.handle_task_request)
        
    def process_message(self, ch, method, properties, body):
        # ワーカー間通信メッセージをチェック
        data = json.loads(body)
        if self.process_worker_message(data):
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        # 通常の処理...
        
        # 他のワーカーに通知
        self.send_to_worker(
            'pm',
            'task_completed',
            {'task_id': task_id, 'status': 'success'},
            priority='high'
        )
        
    def handle_task_request(self, data):
        """他のワーカーからのリクエスト処理"""
        # 処理実装
        return {'status': 'completed', 'result': '...'}
```

### 通信パターン

1. **ファイル作成通知**
   ```python
   self.send_to_worker('pm', 'file_created', {
       'file_path': '/path/to/file.py',
       'task_id': 'task_123'
   })
   ```

2. **タスク完了通知**
   ```python
   self.send_to_worker('result', 'task_completed', {
       'task_id': 'task_123',
       'status': 'success',
       'output': 'result_data'
   })
   ```

3. **サブタスク要求**
   ```python
   result = self.communication.request_and_wait(
       'task',
       'execute_subtask',
       {'prompt': 'Generate helper function'},
       timeout=60
   )
   ```

## 🎯 活用シナリオ

### シナリオ1: 定期レポート自動化

```bash
# テンプレート作成
cat > weekly_report.yaml << EOF
name: "Weekly Report"
description: "Generate weekly summary report"
task_type: "code"
template_data:
  prompt: |
    Generate a weekly report for week {{week_number}} including:
    - Task completion metrics
    - System performance
    - Top errors and resolutions
    - Recommendations
parameters:
  - name: week_number
    type: int
    description: "Week number"
    required: true
EOF

# インポート
ai-template import weekly_report.yaml

# 実行
ai-template run weekly_report --params week_number=27
```

### シナリオ2: 画像処理パイプライン

```python
# 複数のワーカーが協調して画像処理
# 1. ImageProcessingWorker が画像を受信
# 2. リサイズ処理を実行
# 3. ThumbnailWorker にサムネイル生成を依頼
# 4. FilterWorker にフィルター適用を依頼
# 5. 全ての処理完了後、ResultWorker に通知
```

### シナリオ3: コード生成とレビューの自動化

```bash
# APIクライアント生成
ai-template run api_client \
  --params language=python \
  base_url=https://api.github.com \
  auth_type=oauth2 \
  endpoints='["repos", "users", "issues"]'

# 生成されたコードを自動レビュー
ai-template run code_review \
  --params file_path=/home/aicompany/ai_co/output/github_client.py
```

## 📊 モニタリングとデバッグ

### ワーカー通信の監視

```bash
# 全ワーカーの通信を監視
ai-worker-comm monitor --verbose

# 特定ワーカーのみ監視
ai-worker-comm monitor --worker task
```

### テンプレート使用状況

```bash
# 人気テンプレートTop10
ai-template popular --limit 10

# テンプレート使用履歴（今後実装予定）
ai-template history
```

## 🚀 クイックスタート

### 1分で始める

```bash
# 1. 利用可能なテンプレートを確認
ai-template list

# 2. 日次レポートを生成
ai-template run daily_report

# 3. ワーカー間通信を確認
ai-worker-comm test

# 4. 通信をモニタリング
ai-worker-comm monitor
```

### 実用的な例

```bash
# データ分析タスクを実行
ai-template run data_analysis \
  --params data_source=/home/aicompany/ai_co/data/metrics.csv \
  output_format=html

# 結果はSlackに自動通知される
```

## 📝 ベストプラクティス

1. **テンプレートの活用**
   - 繰り返し使うタスクは必ずテンプレート化
   - パラメータで柔軟性を確保
   - タグで整理

2. **ワーカー間通信**
   - 単一責任の原則に従う
   - メッセージは小さく保つ
   - エラーハンドリングを忘れない

3. **パフォーマンス**
   - 大きなデータはファイル経由で共有
   - 優先度を適切に設定
   - タイムアウトを設定

---

**🎊 新機能により、Elders Guildはさらに強力で使いやすくなりました！**
