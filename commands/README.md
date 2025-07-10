# Elders Guild コマンドシステム

## 🚀 インストール方法

```bash
# インストールスクリプトを実行
cd /home/aicompany/ai_co/commands
chmod +x install_commands.sh
./install_commands.sh
```

## 📋 コマンド一覧

### 既存コマンド（Python実装版）

| コマンド | 説明 | 使用例 |
|---------|------|--------|
| `ai-start` | システム起動 | `ai-start --workers 3 --dialog` |
| `ai-stop` | システム停止 | `ai-stop --force --clear-queues` |
| `ai-status` | 状態確認 | `ai-status --verbose` |
| `ai-send` | タスク送信 | `ai-send "タスク内容" code --priority 8` |
| `ai-dialog` | 対話型タスク開始 | `ai-dialog "複雑なWebアプリを作成"` |
| `ai-reply` | 対話応答送信 | `ai-reply conv_123 "回答内容"` |
| `ai-logs` | ログ確認 | `ai-logs task -f --error` |
| `ai-tasks` | タスク一覧 | `ai-tasks --type code --limit 5` |
| `ai-venv` | 仮想環境管理 | `ai-venv --info` |

### 新コマンド

#### ai-dialog
- `ai-dialog "プロンプト"`: 対話型タスク開始
- `--context`: 追加コンテキスト（JSON形式）
- `--no-slack`: Slack通知を無効化

#### ai-reply  
- `ai-reply <conversation_id> <response>`: 対話応答送信
- `--file`: ファイルから応答を読み込み

#### ai-logs
- `worker`: 表示するワーカー（task/pm/result/dialog/all）
- `-f, --follow`: リアルタイム追跡
- `-n, --lines`: 表示行数
- `--since`: 指定時間以降のログ
- `--grep`: 文字列フィルタ
- `--error`: エラーログのみ
- `--task-id`: 特定タスクIDのログ

#### ai-tasks
- `--status`: タスク状態（active/completed/failed/all）
- `--type`: タスクタイプ
- `--limit`: 表示件数
- `--since`: 指定時間以降のタスク
- `--conversation`: 特定会話IDのタスク
- `--task-id`: 特定タスクIDの詳細
- `--json`: JSON形式出力

#### ai-venv
- `--info`: 仮想環境情報表示
- `--check`: 環境の健全性チェック
- `--create`: 仮想環境作成/再作成
- `source ai-venv`: 仮想環境アクティベート

### 既存コマンドオプション

#### ai-start
- `--workers N`: 起動するワーカー数（デフォルト: 2）
- `--no-pm`: PMワーカーを起動しない
- `--no-result`: Resultワーカーを起動しない
- `--dialog`: 対話型ワーカーも起動

#### ai-stop
- `--force`: プロセスを強制終了
- `--clear-queues`: キューもクリア

#### ai-status
- `--json`: JSON形式で出力
- `--verbose, -v`: 詳細情報表示

#### ai-send
- `prompt`: タスクのプロンプト（必須）
- `type`: タスクタイプ（general/code/analysis/report）
- `--priority`: 優先度 1-10
- `--tags`: タスクタグ
- `--no-wait`: 結果を待たない
- `--json`: JSON形式で出力

## 🏗️ アーキテクチャ

```
commands/
├── __init__.py
├── base_command.py     # 基底クラス（共通機能）
├── ai_start.py         # 起動コマンド
├── ai_stop.py          # 停止コマンド
├── ai_status.py        # 状態確認コマンド
├── ai_send.py          # タスク送信コマンド
└── install_commands.sh # インストールスクリプト

bin/
├── ai-start    # → commands/ai_start.py を呼び出すラッパー
├── ai-stop     # → commands/ai_stop.py を呼び出すラッパー
├── ai-status   # → commands/ai_status.py を呼び出すラッパー
└── ai-send     # → commands/ai_send.py を呼び出すラッパー
```

## 🔧 開発ガイド

### 新しいコマンドの追加方法

1. `commands/ai_newcmd.py` を作成
2. `BaseCommand` を継承
3. `setup_arguments()` で引数定義
4. `execute()` でメイン処理実装
5. `bin/ai-newcmd` ラッパー作成
6. `install_commands.sh` を再実行

### コマンドテンプレート

```python
#!/usr/bin/env python3
"""
ai-newcmd: 新しいコマンドの説明
"""
from base_command import BaseCommand

class NewCommand(BaseCommand):
    def __init__(self):
        super().__init__(
            name="newcmd",
            description="新しいコマンドの説明"
        )
        
    def setup_arguments(self):
        self.parser.add_argument(
            '--option',
            help='オプションの説明'
        )
        
    def execute(self, args):
        self.header("コマンド実行")
        # 処理実装
        self.success("完了！")

if __name__ == "__main__":
    cmd = NewCommand()
    cmd.run()
```

## 🎨 共通機能（BaseCommand）

- カラー出力（success, error, warning, info）
- テーブル表示
- 設定ファイル読み込み
- RabbitMQ接続
- データベース接続
- プロセス管理
- コマンド実行ヘルパー

## 📝 実装済みコマンド

- ✅ `ai-start`: システム起動
- ✅ `ai-stop`: システム停止
- ✅ `ai-status`: 状態確認
- ✅ `ai-send`: タスク送信
- ✅ `ai-dialog`: 対話型タスク開始
- ✅ `ai-reply`: 対話応答送信
- ✅ `ai-logs`: ログ確認
- ✅ `ai-tasks`: タスク一覧・履歴
- ✅ `ai-venv`: 仮想環境管理

## 🎆 次の実装予定

- `ai-workers`: ワーカー管理
- `ai-rag`: RAG学習状況
- `ai-evolve`: 自己進化状況
- `ai-config`: 設定管理
