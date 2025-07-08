# AI Company 統一エラーハンドリング標準 v1.0

## 概要

AI Companyのすべてのワーカーで統一されたエラーハンドリングを実現するための標準仕様書です。

## エラーハンドリングの基本方針

1. **統一性**: すべてのワーカーで同じエラーハンドリングパターンを使用
2. **追跡可能性**: すべてのエラーに一意のIDを付与し、追跡可能に
3. **自動リトライ**: 一時的なエラーは自動的にリトライ
4. **エスカレーション**: 重大なエラーは自動的にエラーインテリジェンスワーカーへ

## エラーカテゴリー

```python
class ErrorCategory:
    NETWORK = "network"      # ネットワーク関連エラー
    API = "api"              # API関連エラー
    DATA = "data"            # データ処理エラー
    SYSTEM = "system"        # システムエラー
    PERMISSION = "permission" # 権限エラー
    VALIDATION = "validation" # バリデーションエラー
    TIMEOUT = "timeout"      # タイムアウト
    UNKNOWN = "unknown"      # 不明なエラー
```

## エラー深刻度

```python
class ErrorSeverity:
    CRITICAL = "critical"  # システム停止級
    HIGH = "high"         # 機能停止級
    MEDIUM = "medium"     # 一部機能影響
    LOW = "low"           # 軽微な影響
    INFO = "info"         # 情報レベル
```

## 使用方法

### 1. 基本的なエラーハンドリング

```python
try:
    # 処理
    result = some_risky_operation()
except Exception as e:
    context = {
        'operation': 'operation_name',
        'task_id': task_id,
        'additional_info': 'any relevant information'
    }
    self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)
```

### 2. リトライ付きエラーハンドリング

```python
def retry_operation(context):
    # リトライ時に実行する処理
    return perform_operation_again()

try:
    result = network_operation()
except Exception as e:
    context = {
        'operation': 'network_call',
        'url': api_url,
        'retry_count': 0  # 初回の場合
    }
    result = self.handle_error(
        e, context, 
        severity=ErrorSeverity.HIGH,
        retry_callback=retry_operation
    )
```

### 3. デコレーターを使用したエラーハンドリング

```python
@with_error_handling(severity=ErrorSeverity.HIGH)
def important_task(self, data):
    # エラーが発生する可能性のある処理
    return process_data(data)
```

## リトライ設定

デフォルトのリトライ設定：

```python
retry_config = {
    ErrorCategory.NETWORK: {"max_attempts": 3, "delay": 5},
    ErrorCategory.API: {"max_attempts": 2, "delay": 10},
    ErrorCategory.TIMEOUT: {"max_attempts": 2, "delay": 5},
    ErrorCategory.DATA: {"max_attempts": 1, "delay": 0},
}
```

## エラーログ形式

統一されたログ形式：
```
[ERR-20250705093045-1] HIGH | network | ConnectionError: Connection refused | Context: {"operation": "api_call", "task_id": "task_001"}
```

フォーマット：
- `[error_id]`: 一意のエラーID
- `severity`: エラー深刻度
- `category`: エラーカテゴリー
- `error_type`: エラーの型名
- `error_message`: エラーメッセージ
- `Context`: エラーコンテキスト（JSON形式）

## エラー通知

### Slack通知

CRITICALまたはHIGH深刻度のエラーは自動的にSlackに通知されます：

```
🚨 CRITICAL Error
Worker: task (task-worker-1)
Category: network
Error: ConnectionError - Connection refused
ID: ERR-20250705093045-1
```

### エラーインテリジェンスワーカー連携

CRITICALまたはHIGH深刻度のエラーは自動的にエラーインテリジェンスワーカーに送信され、以下の処理が行われます：

1. エラーパターン分析
2. 自動修正提案
3. インシデント記録
4. 再発防止策の提案

## エラー統計

エラー統計を取得：

```python
stats = self.get_error_statistics()
# {
#     "total_errors": 10,
#     "by_category": {"network": 5, "api": 3, "data": 2},
#     "by_severity": {"critical": 1, "high": 3, "medium": 6},
#     "recent_errors": [...]  # 最新10件
# }
```

## ベストプラクティス

1. **適切な深刻度を設定**
   - ユーザー影響の大きさで判断
   - システム全体への影響を考慮

2. **十分なコンテキスト情報を提供**
   - 操作名、タスクID、関連データ
   - デバッグに必要な情報を含める

3. **エラーカテゴリーを正しく分類**
   - 自動リトライの判断に使用される
   - 統計分析の精度に影響

4. **リトライ可能な処理を識別**
   - ネットワーク、API系は基本的にリトライ対象
   - データエラーはリトライしない

## 移行ガイド

既存のエラーハンドリングから移行する場合：

### Before:
```python
except Exception as e:
    self.logger.error(f"Error: {e}")
    self.handle_error(e, "operation_name", critical=True)
```

### After:
```python
except Exception as e:
    context = {
        'operation': 'operation_name',
        'task_id': task_id,
        # その他の関連情報
    }
    self.handle_error(e, context, severity=ErrorSeverity.HIGH)
```

## エラーハンドリングチェックリスト

- [ ] BaseWorkerを継承している
- [ ] ErrorHandlerMixinが初期化されている
- [ ] 適切なErrorSeverityを使用している
- [ ] 十分なコンテキスト情報を提供している
- [ ] リトライが必要な場合はretry_callbackを提供している
- [ ] エラーカテゴリーが自動判定される内容になっている

---
*このドキュメントはPhase 3エラーハンドリング標準化の一環として作成されました*