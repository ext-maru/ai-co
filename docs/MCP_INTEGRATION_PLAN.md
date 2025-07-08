# 🔌 AI Company MCP Integration Plan v1.0

## 📋 概要

MCP (Model Context Protocol) を AI Company に統合し、より汎用的で拡張可能な開発基盤を構築します。

## 🏗️ MCPサーバー構成案

### 1. **FileSystem MCPサーバー**
```yaml
name: ai-company-filesystem
description: AI Company専用ファイル操作
capabilities:
  - プロジェクト構造認識
  - 自動配置ルール適用
  - Git連携
tools:
  - create_worker
  - create_manager
  - deploy_file
  - auto_organize
```

### 2. **Command Executor MCPサーバー**
```yaml
name: ai-company-executor
description: コマンド自動実行管理
capabilities:
  - 非同期実行
  - ログ管理
  - 結果通知
tools:
  - execute_command
  - check_result
  - get_logs
  - schedule_task
```

### 3. **Worker Communication MCPサーバー**
```yaml
name: ai-company-workers
description: ワーカー間通信と管理
capabilities:
  - ワーカー状態監視
  - メッセージルーティング
  - 負荷分散
tools:
  - send_to_worker
  - get_worker_status
  - restart_worker
  - scale_workers
```

### 4. **Knowledge Base MCPサーバー**
```yaml
name: ai-company-knowledge
description: ナレッジベース管理
capabilities:
  - 過去タスク検索
  - ベストプラクティス提案
  - エラー解決策
tools:
  - search_tasks
  - get_solution
  - add_knowledge
  - analyze_patterns
```

### 5. **Testing MCPサーバー**
```yaml
name: ai-company-testing
description: テスト自動化
capabilities:
  - テスト生成
  - 自動実行
  - カバレッジ分析
tools:
  - generate_test
  - run_tests
  - fix_test_errors
  - get_coverage
```

## 🔄 統合アーキテクチャ

```
┌─────────────────────────────────────────┐
│          Claude (with MCP)              │
├─────────────────────────────────────────┤
│           MCP Router                    │
├────┬────┬────┬────┬────┬──────────────┤
│ FS │Exec│Work│Know│Test│ External MCP │
└────┴────┴────┴────┴────┴──────────────┘
     ↓    ↓    ↓    ↓    ↓
   AI Company Infrastructure
```

## 📦 実装計画

### Phase 1: 基本MCPサーバー構築
1. FileSystem MCPサーバー
2. Command Executor MCPサーバー
3. MCPクライアント統合

### Phase 2: 高度な機能
1. Worker Communication MCP
2. Knowledge Base MCP
3. Testing MCP

### Phase 3: 外部連携
1. GitHub MCP統合
2. Slack MCP統合
3. 外部API連携

## 🎯 期待される効果

1. **開発効率**: 10倍→50倍
2. **拡張性**: プラグイン式でツール追加可能
3. **相互運用性**: 他のMCP対応システムと連携
4. **標準化**: ツール利用の統一インターフェース
5. **自律性**: AIがより高度な判断と操作が可能に

## 💡 新しい開発フロー

```python
# 従来の方法
from libs.ai_command_helper import AICommandHelper
helper = AICommandHelper()
helper.create_bash_command(...)

# MCP導入後
# Claudeが直接MCPツールを使用
<use_mcp_tool>
<server_name>ai-company-executor</server_name>
<tool_name>execute_command</tool_name>
<arguments>
{
  "command": "python workers/new_worker.py",
  "async": true,
  "notify_slack": true
}
</arguments>
</use_mcp_tool>
```
