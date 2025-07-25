# Auto Issue Processor A2A API リファレンス

## 概要

Auto Issue Processor A2Aは、RESTful APIとPython APIの両方を提供します。このドキュメントでは、各APIエンドポイントの詳細仕様と使用例を説明します。

## 🔐 認証

### GitHub Token認証
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxx"
```

### Claude API認証
```bash
export CLAUDE_API_KEY="sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxx"
```

## 📡 REST API エンドポイント

### 1. Issue処理エンドポイント

#### POST /api/process-issue
指定されたIssueを処理します。

**リクエスト:**
```json
{
  "issue_number": 123,
  "mode": "process",
  "priority": "high",
  "options": {
    "force": false,
    "skip_quality_gate": false
  }
}
```

**レスポンス:**
```json
{
  "status": "success",
  "pr_url": "https://github.com/ext-maru/ai-co/pull/456",
  "pr_number": 456,
  "execution_time": 45.2,
  "phases_completed": {
    "four_sages_consultation": true,
    "elder_flow_execution": true,
    "quality_gate": true,
    "pr_creation": true
  }
}
```

**エラーレスポンス:**
```json
{
  "status": "error",
  "error_code": "ISSUE_NOT_FOUND",
  "message": "Issue #123 not found",
  "details": {}
}
```

### 2. スキャンエンドポイント

#### GET /api/scan-issues
処理可能なIssueをスキャンします。

**パラメータ:**
- `priority`: (optional) "critical", "high", "medium", "low"
- `limit`: (optional) 最大取得数（デフォルト: 10）
- `include_assigned`: (optional) アサイン済みIssueを含むか（デフォルト: false）

**レスポンス:**
```json
{
  "status": "success",
  "issues": [
    {
      "number": 123,
      "title": "Implement new feature",
      "priority": "high",
      "complexity_score": 65.5,
      "estimated_time": "2-3 hours",
      "processable": true
    }
  ],
  "total_count": 5
}
```

### 3. ステータス確認エンドポイント

#### GET /api/status/{issue_number}
特定のIssueの処理状況を確認します。

**レスポンス:**
```json
{
  "issue_number": 123,
  "status": "processing",
  "current_phase": "elder_flow_execution",
  "phases": {
    "four_sages_consultation": {
      "status": "completed",
      "duration": 5.2
    },
    "elder_flow_execution": {
      "status": "in_progress",
      "progress": 65
    },
    "quality_gate": {
      "status": "pending"
    },
    "pr_creation": {
      "status": "pending"
    }
  },
  "started_at": "2025-07-21T10:30:00Z",
  "estimated_completion": "2025-07-21T10:45:00Z"
}
```

## 🐍 Python API

### 基本的な使用方法

```python
from libs.integrations.github.auto_issue_processor import AutoIssueProcessor

# 初期化
processor = AutoIssueProcessor()

# Issue処理
async def process_issue_example():
    result = await processor.process_request({
        "mode": "process",
        "issue_number": 123
    })
    print(f"PR created: {result['pr_url']}")

# スキャン
async def scan_issues_example():
    issues = await processor.scan_processable_issues()
    for issue in issues:
        print(f"Issue #{issue.number}: {issue.title}")
```

### 高度な使用方法

```python
# カスタム設定での初期化
processor = AutoIssueProcessor()
processor.limiter.max_daily = 20  # 1日の最大処理数
processor.limiter.max_pr_per_issue = 3  # Issue毎の最大PR数

# 4賢者への個別相談
async def consult_sages_example(issue):
    sage_advice = await processor.consult_four_sages(issue)
    
    # 各賢者のアドバイスを確認
    print(f"Knowledge Sage: {sage_advice['knowledge_sage']}")
    print(f"Task Sage: {sage_advice['task_sage']}")
    print(f"Incident Sage: {sage_advice['incident_sage']}")
    print(f"RAG Sage: {sage_advice['rag_sage']}")

# 複雑度評価
async def evaluate_complexity_example(issue):
    evaluator = ComplexityEvaluator()
    complexity = await evaluator.evaluate(issue)
    
    print(f"Score: {complexity.score}")
    print(f"Processable: {complexity.is_processable}")
    print(f"Factors: {complexity.factors}")
```

### Elder Flow Engine API

```python
from libs.elder_system.flow.elder_flow_engine import ElderFlowEngine

# Elder Flow実行
engine = ElderFlowEngine()

result = await engine.process_request({
    "type": "execute",
    "task_name": "新機能実装",
    "priority": "high",
    "context": {
        "issue_number": 123,
        "issue_title": "Add OAuth support"
    }
})

# 結果確認
if result["status"] == "success":
    print(f"Task ID: {result['task_id']}")
    print(f"Execution time: {result['execution_time']}s")
```

## 🔄 Webhook API

### GitHub Webhook受信

#### POST /api/webhooks/github
GitHub Webhookイベントを受信します。

**対応イベント:**
- `issues.opened` - 新規Issue作成時
- `issues.labeled` - ラベル追加時
- `pull_request.closed` - PR完了時

**ペイロード例:**
```json
{
  "action": "opened",
  "issue": {
    "number": 123,
    "title": "New feature request",
    "body": "Description...",
    "labels": [
      {"name": "enhancement"},
      {"name": "auto-processable"}
    ]
  }
}
```

## 📊 メトリクスAPI

### GET /api/metrics
システムメトリクスを取得します。

**レスポンス:**
```json
{
  "system": {
    "uptime": 86400,
    "cpu_usage": 45.2,
    "memory_usage": 62.8
  },
  "processing": {
    "total_issues_processed": 150,
    "success_rate": 92.5,
    "average_processing_time": 180.5,
    "active_tasks": 3
  },
  "four_sages": {
    "knowledge_sage_queries": 450,
    "task_sage_assignments": 150,
    "incident_sage_alerts": 12,
    "rag_sage_searches": 320
  }
}
```

## 🚨 エラーコード

| コード | 説明 | 対処法 |
|--------|------|--------|
| `ISSUE_NOT_FOUND` | 指定されたIssueが存在しない | Issue番号を確認 |
| `ALREADY_PROCESSING` | 既に処理中 | 処理完了を待つ |
| `RATE_LIMIT_EXCEEDED` | レート制限超過 | 時間を置いて再試行 |
| `INVALID_PRIORITY` | 無効な優先度 | critical/high/medium/lowを使用 |
| `AUTHENTICATION_FAILED` | 認証失敗 | トークンを確認 |
| `QUALITY_GATE_FAILED` | 品質ゲート失敗 | ログで詳細を確認 |

## 📡 レート制限

- **Issue処理**: 10件/時間
- **スキャン**: 60回/時間
- **ステータス確認**: 300回/時間
- **メトリクス**: 120回/時間

## 🔗 関連ドキュメント

- [クイックスタートガイド](../user-guides/quickstart.md)
- [包括的ドキュメント](../AUTO_ISSUE_PROCESSOR_A2A_COMPLETE_DOCUMENTATION.md)
- [トラブルシューティング](../runbooks/troubleshooting-guide.md)

---
*最終更新: 2025年7月21日*