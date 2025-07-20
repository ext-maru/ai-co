# 📚 Elders Guild コアナレッジベース v5.1

## 🎯 システム概要

### **Elders Guild とは**
AIによるコード生成と自動化を極限まで推し進めた開発基盤システム。Claude CLIを中核に、タスクの受信から実行、配置、通知まで全て自動化。

### **システム構成図**
```
User → ai-send/ai-dialog → RabbitMQ
                              ↓
                         TaskWorker
                         (Claude CLI)
                              ↓
                          PMWorker
                     (ファイル配置・Git)
                              ↓
                        ResultWorker
                        (Slack通知)

     Command Executor (バックグラウンド常駐)
```

## 🏗️ アーキテクチャ

### **ディレクトリ構造**
```
/home/aicompany/ai_co/
├── core/           # 基盤モジュール（BaseWorker, BaseManager）
├── workers/        # ワーカー実装（自己進化対象）
├── libs/           # ライブラリ・マネージャー（自己進化対象）
├── scripts/        # 実行スクリプト（ai-*コマンド）
├── commands/       # AIコマンド実装（ai_start.py等）
├── bin/            # 実行可能コマンド（シンボリックリンク）
├── config/         # 設定ファイル
├── output/         # Claude CLI作業ディレクトリ
├── logs/           # ログファイル
├── db/             # SQLiteデータベース
├── ai_commands/    # AI Command Executor用
├── ai_programs/    # AI Program Runner用
├── templates/      # タスクテンプレート
├── knowledge_base/ # ナレッジベース
└── web/            # Webダッシュボード
```

### **主要コンポーネント**

#### 1. ワーカー群（v5.1更新）
| ワーカー | 役割 | キュー | 起動方法 |
|---------|------|--------|----------|
| TaskWorker | Claude CLI実行 | ai_tasks | ai-start（デフォルト） |
| PMWorker | ファイル配置・Git | ai_pm | ai-start（デフォルト） |
| ResultWorker | 結果処理・Slack | ai_results | ai-start（デフォルト） |
| CommandExecutorWorker | コマンド自動実行 | (ディレクトリ監視) | ai-start（デフォルト） |
| DialogTaskWorker | 対話型処理 | ai_dialog | ai-start --dialog |
| SE-TesterWorker | テスト自動実行・修正 | ai_se | ai-start --se-tester |

#### 2. Core基盤
| モジュール | 機能 |
|-----------|------|
| BaseWorker | ワーカー基底クラス |
| BaseManager | マネージャー基底クラス |
| get_config() | 統合設定管理 |
| CommunicationMixin | ワーカー間通信 |
| PriorityMixin | 優先度処理 |
| DLQMixin | Dead Letter Queue |

#### 3. マネージャー群
| マネージャー | 機能 |
|-------------|------|
| RAGManager | 過去タスク検索・活用 |
| ConversationManager | 対話履歴管理 |
| SelfEvolutionManager | 自己進化（ファイル配置） |
| GitFlowManager | Git操作自動化 |
| AICommandHelper | AI Command Executor連携 |
| AIProgramRunner | プログラム自動実行 |
| AILogViewer | ログ参照ヘルパー |

## 🚀 基本操作（v5.1更新）

### **システム管理**
```bash
ai              # インタラクティブメニュー
ai-start        # 全基本ワーカー起動（Command Executor含む）
ai-stop         # システム停止（Command Executor含む）
ai-status       # 状態確認
ai-restart      # 再起動
```

### **起動オプション（新機能）**
```bash
# 基本起動（TaskWorker×2、PM、Result、Command Executor）
ai-start

# SE-Testerも含めて起動
ai-start --se-tester

# 対話型ワーカーも起動
ai-start --dialog

# Command Executorなしで起動
ai-start --no-executor

# カスタム設定
ai-start --workers 3 --se-tester --dialog
```

### **タスク実行**
```bash
# 基本的なタスク送信
ai-send "要件" code          # コード生成
ai-send "要件" general       # 一般タスク

# 優先度付き
ai-send "緊急タスク" code --priority critical

# 対話型（複雑なタスク）
ai-dialog "複雑な要件"
ai-reply <conversation_id> "回答"

# テンプレート実行
ai-run daily_report --params date=2025-07-02
```

### **情報確認**
```bash
ai-logs         # ログ確認
ai-tasks        # タスク一覧
ai-stats        # 統計情報
ai-monitor      # リアルタイムモニタ
ai-queue        # キュー状態
ai-cmd-executor status  # Command Executor状態
```

## 🔧 Claude CLI統合

### **実行パラメータ**
```python
# TaskWorkerでの実行
claude_cmd = [
    "claude",
    "--allowedTools", "Edit,Write,FileSystem",
    "--cwd", "/home/aicompany/ai_co/output",
    "--print"
]
```

### **権限付与プロンプト（必須）**
```python
# 全タスクのプロンプトに含める
"""
You have permission to use all tools including Edit, Write, and FileSystem.
Please proceed with the task without asking for permissions.
"""
```

## 📋 データベース構造

### **task_history.db**
```sql
CREATE TABLE task_history (
    task_id TEXT UNIQUE,          -- code_20250702_123456
    task_type TEXT,               -- code/general
    prompt TEXT,                  -- 元の要件
    response TEXT,                -- Claude応答
    summary TEXT,                 -- AI生成要約
    files_created TEXT,           -- JSON配列
    status TEXT,                  -- completed/failed
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### **conversations.db**
```sql
CREATE TABLE conversations (
    conversation_id TEXT UNIQUE,  -- conv_dialog_20250702_123456
    status TEXT,                  -- active/completed
    initial_prompt TEXT,
    created_at TIMESTAMP
);

CREATE TABLE messages (
    conversation_id TEXT,
    message_index INTEGER,
    role TEXT,                    -- user/assistant
    content TEXT,
    created_at TIMESTAMP
);
```

## ⚙️ 設定管理

### **主要設定ファイル**
| ファイル | 内容 |
|---------|------|
| slack.conf | Slack通知設定 |
| worker.json | ワーカー詳細設定 |
| git.json | Git Flow設定 |
| priority.json | 優先度設定 |
| templates/ | タスクテンプレート |

### **統合設定アクセス**
```python
from core import get_config

config = get_config()
model = config.worker.default_model        # ドット記法
timeout = config.get('worker.timeout', 300) # デフォルト値付き
```

## 🌍 環境設定

### **必須環境変数**
```bash
export AI_COMPANY_HOME="/home/aicompany/ai_co"
export PYTHONPATH="${AI_COMPANY_HOME}:${PYTHONPATH}"
export PATH="${AI_COMPANY_HOME}/bin:${PATH}"

# オプション
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
export CLAUDE_MODEL="claude-sonnet-4-20250514"
```

### **Python環境**
```bash
# 仮想環境
cd /home/aicompany/ai_co
python3.12 -m venv venv
source venv/bin/activate

# 依存関係
pip install -r requirements.txt
```

## 🤖 AI Command Executor（v5.1: デフォルト起動）

### **概要**
AIが作成したコマンドを自動実行するシステム。手動でのコピペ作業を完全排除。
**v5.1より`ai-start`でデフォルトで起動される。**

### **使用方法**
```python
from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# コマンド作成
helper.create_bash_command("echo 'Hello'", "test_cmd")

# 結果確認（自動実行される）
import time
time.sleep(6)
result = helper.check_results("test_cmd")
```

### **動作フロー**
```
AI creates → pending/ → Executor detects → running/ → execute → logs/ → completed/
```

### **管理コマンド**
```bash
# 個別管理（通常は不要）
ai-cmd-executor start   # 起動
ai-cmd-executor stop    # 停止
ai-cmd-executor status  # 状態確認
ai-cmd-executor logs    # ログ表示
ai-cmd-executor test    # テスト実行
```

## 🚀 AI Program Runner

### **概要**
AI Command Executorを拡張したプログラム自動実行システム。

### **使用方法**
```python
from libs.ai_program_runner import AIProgramRunner

runner = AIProgramRunner()

# Pythonプログラム実行
result = runner.run_python_program(
    code="print('Hello')",
    task_name="test",
    description="テストプログラム"
)
```

## 🎯 自己進化システム

### **ファイル配置ルール**
```python
# ファイル名パターンと配置先
patterns = {
    r'.*_worker\.py$': 'workers/',
    r'.*_manager\.py$': 'libs/',
    r'.*\.sh$': 'scripts/',
    r'.*\.conf$': 'config/',
    r'.*\.json$': 'config/',
    r'.*\.html$': 'web/'
}
```

### **Git Flow運用**
```
main (安定版)
├── develop (開発版) ← 日常開発
├── auto/task_* ← AI自動生成（自動マージ）
└── feature/* ← 手動開発
```

## 🚨 トラブルシューティング（v5.1更新）

### **よくある問題と対処**

#### 1. ワーカーが起動しない
```bash
# プロセス確認（Command Executor含む）
ps aux | grep -E "(worker|command_executor)"

# ログ確認
tail -f logs/task_worker.log
tail -f logs/command_executor.log

# 手動起動テスト
cd /home/aicompany/ai_co
source venv/bin/activate
python3 workers/task_worker.py
```

#### 2. Command Executorが起動しない
```bash
# 個別起動
./scripts/start-command-executor.sh

# または
ai-cmd-executor start

# ログ確認
tail -f logs/command_executor.log
```

#### 3. Claude CLIエラー
```bash
# バージョン確認
claude --version

# 設定確認
claude config

# テスト実行
echo "print('test')" | claude --allowedTools Write --print
```

#### 4. RabbitMQエラー
```bash
# サービス確認
sudo systemctl status rabbitmq-server

# キュー確認
sudo rabbitmqctl list_queues

# キュークリア（緊急時）
sudo rabbitmqctl purge_queue ai_tasks
```

## 📊 パフォーマンス指標（v5.1）

### **処理能力**
- タスク処理: 50-100 タスク/分
- Command Executor: 5秒チェック間隔
- 平均処理時間: 1-5分（タスク複雑度による）
- 同時実行: ワーカー数に依存

### **信頼性**
- エラー率: < 0.5%（リトライ機能）
- タスク喪失: 0%（DLQ導入後）
- 自動復旧: 90%以上
- Command Executor: 99.9%稼働率

## 🎓 ベストプラクティス（v5.1）

### **タスク送信**
```bash
# 明確で具体的な要件
ai-send "PythonでRESTful APIサーバー。FastAPI使用、認証付き、Docker対応" code

# 複雑なタスクは対話型
ai-dialog "マイクロサービスアーキテクチャの設計と実装"
```

### **システム運用**
```bash
# 起動（Command Executor自動起動）
ai-start

# SE-Testerも含めた完全起動
ai-start --se-tester --dialog

# 状態確認（Command Executor含む）
ai-status
```

### **定期メンテナンス**
```bash
# 週次
./cleanup_project.sh      # プロジェクトクリーンアップ
ai-git release            # リリース作成

# 月次
ai-backup full            # フルバックアップ
```

## 📈 v5.1 の主な変更点

1. **Command Executorのデフォルト起動**
   - `ai-start`で自動的に起動
   - `--no-executor`オプションで無効化可能

2. **SE-Testerワーカーの統合**
   - `--se-tester`オプションで起動
   - テスト自動実行・修正機能

3. **起動・停止の改善**
   - 全ワーカーの適切な管理
   - Command Executorの確実な停止

4. **新しいワーカー対応**
   - 10種類以上のワーカーに対応
   - 必要に応じて個別起動可能

---

**📚 このコアナレッジベースが、Elders Guild v5.1開発の基礎となります**
