# API Documentation

Auto Issue Processor A2AのAPIリファレンスドキュメントです。

## 📡 完全APIリファレンス

### 🔥 メインドキュメント
- **[Auto Issue Processor API リファレンス](auto-issue-processor-api-reference.md)** - 完全仕様書

### 📋 API種別

#### REST API
- Issue処理エンドポイント (`POST /api/process-issue`)
- スキャンエンドポイント (`GET /api/scan-issues`)
- ステータス確認 (`GET /api/status/{issue_number}`)
- メトリクス取得 (`GET /api/metrics`)

#### Python API
- `AutoIssueProcessor` クラス
- `ElderFlowEngine` API
- 4賢者システム API

#### Webhook API
- GitHub Webhook受信 (`POST /api/webhooks/github`)
- イベント処理（issues.opened, pull_request.closed等）

## 🔐 認証・セキュリティ

- **GitHub Token認証** - Personal Access Token、GitHub App
- **Claude API認証** - APIキー管理
- **レート制限** - エンドポイント別制限

## 🚨 エラーハンドリング

| エラーコード | 説明 | 対処法 |
|-------------|------|--------|
| `ISSUE_NOT_FOUND` | Issue存在せず | Issue番号確認 |
| `AUTHENTICATION_FAILED` | 認証失敗 | Token確認 |
| `RATE_LIMIT_EXCEEDED` | レート制限 | 時間を置いて再試行 |

## 📖 使用例

### 基本的な使用方法
```python
from libs.integrations.github.auto_issue_processor import AutoIssueProcessor

processor = AutoIssueProcessor()
result = await processor.process_request({
    "mode": "process",
    "issue_number": 123
})
```

### REST API呼び出し
```bash
curl -X POST http://localhost:8080/api/process-issue \
  -H "Content-Type: application/json" \
  -d '{"issue_number": 123, "mode": "process"}'
```

## 🔗 関連ドキュメント

- **[クイックスタートガイド](../user-guides/quickstart.md)** - 初回セットアップ
- **[コントリビューションガイド](../developer-guides/contribution-guide.md)** - 開発参加
- **[包括的ドキュメント v2.0](../AUTO_ISSUE_PROCESSOR_A2A_COMPLETE_DOCUMENTATION_V2.md)** - 全体概要

---
*最終更新: 2025年7月21日*