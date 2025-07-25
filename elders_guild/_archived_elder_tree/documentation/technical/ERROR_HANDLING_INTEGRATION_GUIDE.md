# Auto Issue Processor エラーハンドリング統合ガイド

**作成日**: 2025-07-21  
**バージョン**: v1.0  
**対象**: Issue #191 実装機能

---

## 📋 概要

Auto Issue Processor A2A のエラーハンドリング・回復システムの統合ガイドです。本システムにより、GitHub Issue処理の信頼性と可用性が大幅に向上します。

## 🔧 統合手順

### 1. モジュールインポート

```python
from libs.auto_issue_processor_error_handling import (
    AutoIssueProcessorErrorHandler,
    ErrorClassifier,
    CircuitBreaker,
    RetryStrategy,
    ErrorReporter,
    ErrorAnalytics
)
```

### 2. 基本的な使用方法

#### エラーハンドラーの初期化
```python
# エラーハンドラーの作成
error_handler = AutoIssueProcessorErrorHandler()

# サーキットブレーカー付きの操作実行
@error_handler.handle_errors(
    operation_name="github_api_call",
    max_retries=3,
    circuit_breaker_threshold=5
)
async def process_github_issue(issue_number):
    # GitHub API呼び出し処理
    pass
```

#### 手動エラー処理
```python
try:
    # 危険な操作
    result = await risky_github_operation()
except Exception as e:
    # エラー分類
    error_type = ErrorClassifier.classify_error(e, "github_operation")
    
    # エラーレポート作成
    report = await error_reporter.create_report(
        error=e,
        operation="github_operation",
        issue_number=123
    )
    
    # 回復戦略実行
    recovery_result = await error_handler.execute_recovery(
        error_type=error_type,
        context={"issue_number": 123}
    )
```

### 3. サーキットブレーカーの設定

```python
# GitHub API用サーキットブレーカー
github_circuit = CircuitBreaker(
    failure_threshold=5,        # 5回連続失敗でオープン
    recovery_timeout=60.0,      # 60秒後に回復試行
    expected_exception=Exception
)

# 使用例
async def safe_github_call():
    return await github_circuit.call(github_api_function, *args)
```

### 4. エラー分析・監視

```python
# エラー分析エンジンの初期化
analytics = ErrorAnalytics()

# MTTR (Mean Time To Recovery) 計算
mttr = await analytics.calculate_mttr()
print(f"平均回復時間: {mttr}秒")

# エラーパターンの特定
patterns = await error_reporter.get_error_patterns()
for pattern in patterns:
    print(f"{pattern.error_type}: {pattern.count}回発生")
```

## 📊 監視・メトリクス

### 主要メトリクス
- **エラー発生率**: 時間あたりのエラー数
- **回復成功率**: 自動回復の成功割合
- **MTTR**: 平均回復時間
- **サーキットブレーカー状態**: CLOSED/OPEN/HALF_OPEN

### ダッシュボード統合
```python
# メトリクス取得
metrics = await error_handler.get_metrics()
dashboard_data = {
    "error_count": metrics["total_errors"],
    "recovery_rate": metrics["recovery_success_rate"],
    "circuit_status": metrics["circuit_breaker_status"]
}
```

## 🔍 トラブルシューティング

### よくある問題と対処法

#### 1. サーキットブレーカーがOPENになる
```python
# 強制的にCLOSEDに戻す
circuit_breaker._state = CircuitState.CLOSED
circuit_breaker.failure_count = 0
```

#### 2. 大量のエラーレポート生成
```python
# レポート生成を制限
error_reporter = ErrorReporter(
    report_dir="/tmp/error_reports",
    max_reports_per_hour=100  # 時間あたり最大100レポート
)
```

#### 3. メモリ使用量増加
```python
# 古いエラーデータのクリーンアップ
analytics.cleanup_old_data(days=7)  # 7日以上古いデータを削除
```

## ⚙️ 設定カスタマイズ

### デフォルト設定
```python
DEFAULT_CONFIG = {
    "max_retries": 3,
    "circuit_breaker_threshold": 5,
    "recovery_timeout": 60.0,
    "report_retention_days": 30,
    "max_memory_usage_mb": 100
}
```

### 環境別設定
```python
# 本番環境
PRODUCTION_CONFIG = {
    "max_retries": 5,
    "circuit_breaker_threshold": 10,
    "recovery_timeout": 120.0
}

# 開発環境
DEVELOPMENT_CONFIG = {
    "max_retries": 1,
    "circuit_breaker_threshold": 3,
    "recovery_timeout": 30.0
}
```

## 🚀 パフォーマンス最適化

### 推奨設定
- **高負荷環境**: より寛容な閾値設定
- **低レイテンシ要求**: 短いタイムアウト設定
- **リソース制約**: メモリ使用量制限

### 監視ポイント
1. エラーハンドリングによるオーバーヘッド (< 5ms)
2. メモリ使用量 (< 100MB)
3. エラーレポート生成頻度

## 🔗 関連ドキュメント

- [Auto Issue Processor 基本ガイド](../guides/AUTO_ISSUE_PROCESSOR_GUIDE.md)
- [4賢者統合ドキュメント](../guides/FOUR_SAGES_INTEGRATION.md)
- [Elder Flow 統合ガイド](../technical/ELDER_FLOW_INTEGRATION.md)

---

*🏛️ Elders Guild Quality Standards*  
*📊 Ancient Elder Approved*  
*⚡ 4 Sages Integration Ready*