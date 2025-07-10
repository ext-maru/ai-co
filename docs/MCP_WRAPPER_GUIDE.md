
# Elders Guild MCP Integration

## 概要
Elders GuildにMCP (Model Context Protocol) 風のインターフェースを実装しました。
これにより、ツールの呼び出しが統一され、開発効率が大幅に向上します。

## 実装内容

### 1. MCPラッパー構造
```
libs/mcp_wrapper/
├── __init__.py         # MCPServer基本クラス
├── filesystem_server.py # ファイル操作サーバー
├── executor_server.py   # コマンド実行サーバー
└── client.py           # クライアントライブラリ
```

### 2. 使用方法

#### 基本的な使い方
```python
from libs.mcp_wrapper.client import MCPClient

# クライアント初期化
client = MCPClient()

# ワーカー作成
result = client.call_tool(
    "filesystem",
    "create_worker",
    {"name": "example", "worker_type": "demo"}
)

# コマンド実行
result = client.call_tool(
    "executor",
    "execute_command",
    {"command": "echo 'Hello MCP!'", "task_name": "test"}
)
```

### 3. 利用可能なツール

#### FileSystem Server
- `create_worker`: ワーカーの作成
- `deploy_file`: ファイルの自動配置

#### Executor Server  
- `execute_command`: コマンドの実行（AI Command Executor経由）
- `check_result`: 実行結果の確認

### 4. メリット

1. **統一インターフェース**: 全ツールが同じ方法で呼び出し可能
2. **エラー処理**: 標準化されたエラーレスポンス
3. **拡張性**: 新しいサーバーの追加が容易
4. **将来性**: 本格的なMCPプロトコル対応への準備

### 5. 実装の特徴

- Elders Guildの既存インフラを活用
- 外部依存なし（MCPパッケージ不要）
- asyncio対応で非同期処理可能
- JSON-RPC風のリクエスト/レスポンス形式

### 6. テスト方法

```bash
# デモの実行
python3 demo_mcp_wrapper.py

# 実用的なテスト
python3 test_mcp_practical.py
```

## まとめ

MCPラッパーの実装により、Elders Guildの開発効率が大幅に向上しました。
将来的に本格的なMCPプロトコルが利用可能になった際も、
スムーズに移行できる設計となっています。
