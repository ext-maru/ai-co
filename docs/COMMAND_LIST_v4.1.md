# 📚 Elders Guild コマンド一覧（2025年7月版 - 精査後）

## 🎯 メインコマンド
```bash
ai                  # インタラクティブメニュー（メインエントリーポイント）
ai-help             # ヘルプ表示（--list で全コマンド一覧）
ai-version          # バージョン情報表示（--check-update で更新確認）
```

## 🚀 基本操作
```bash
ai-start            # システム起動（tmuxセッション elders_guild で全ワーカー起動）
ai-stop             # システム停止（完全停止・リセット）
ai-restart          # システム再起動（stop → start）※ショートカット
ai-status           # システム状態確認（ワーカー稼働・キュー状況）
```

## 📝 タスク実行
```bash
ai-send             # タスク送信（ai-send "要件" code/general）
ai-code             # コード生成ショートカット（ai-send "..." code と同等）
ai-dialog           # 対話型タスク開始（複雑なタスクを対話形式で）
ai-reply            # 対話応答送信（ai-reply <conversation_id> "回答"）
ai-run              # テンプレート実行ショートカット（ai-template run と同等）
```

## 📊 情報表示
```bash
ai-logs             # ログ確認（--follow, --grep, --tail オプション対応）
ai-tasks            # タスク一覧・履歴（--type, --limit, --since）
ai-stats            # 統計情報表示（--period today/week/month/all）
ai-monitor          # リアルタイムモニタリング（CPU/メモリ/キュー状態）
ai-queue            # キュー状態確認（RabbitMQキューの詳細）
ai-metrics          # メトリクス表示（--worker, --summary）🆕
```

## 👷 ワーカー管理
```bash
ai-workers          # ワーカー一覧・状態確認
ai-worker-restart   # ワーカー再起動（task/pm/result/dialog/all）
ai-worker-add       # ワーカー追加
ai-worker-rm        # ワーカー削除
ai-worker-scale     # ワーカースケーリング
```

## 📋 タスク詳細管理
```bash
ai-task-info        # タスク詳細表示（タスクIDで詳細確認）
ai-task-cancel      # タスクキャンセル
ai-task-retry       # タスクリトライ
```

## 💬 会話管理
```bash
ai-conversations    # 会話一覧
ai-conv-info        # 会話詳細
ai-conv-resume      # 会話再開
ai-conv-export      # 会話エクスポート
```

## ⚙️ 設定管理
```bash
ai-config           # 設定確認（--list で一覧、--get で個別取得）
ai-config-edit      # 設定編集
ai-config-reload    # 設定再読込
```

## 🔍 RAG/検索
```bash
ai-rag              # RAG管理
ai-rag-search       # RAG検索（--include-code でGitHubコード含む）
```

## 🧬 自己進化・学習
```bash
ai-evolve           # 自己進化実行
ai-evolve-test      # 自己進化テスト
ai-learn            # 学習実行
```

## 💾 システム管理
```bash
ai-backup           # バックアップ
ai-clean            # クリーンアップ
ai-update           # システム更新
ai-queue-clear      # キュークリア
```

## 📈 レポート・エクスポート
```bash
ai-report           # レポート生成
ai-export           # データエクスポート
```

## 🛠️ 開発支援
```bash
ai-venv             # 仮想環境管理（--info, --check, --create）
ai-debug            # デバッグモード
ai-test             # テスト実行
ai-shell            # インタラクティブシェル
ai-simulate         # シミュレーション
ai-git              # Git Flow操作（status, flow, release, cleanup）
```

## 🆕 新機能（v4.1）
```bash
ai-template         # タスクテンプレート（list, run, create, show）✅
ai-worker-comm      # ワーカー間通信（routes, monitor, send）✅
ai-dlq              # Dead Letter Queue管理（status, show, retry, purge）✅
ai-dashboard        # ターミナルダッシュボード ✅
ai-webui            # Webダッシュボード（start, stop, status）🆕
ai-plugin           # プラグイン管理（list, enable, disable）🆕
ai-schedule         # スケジュール管理（list, add, remove）🆕
ai-scale            # オートスケーリング管理 ⚡
```

## 📌 使用例

### 基本的なタスク実行
```bash
# 明確な要件指定
ai-send "Pythonでファイル管理システム。検索、タグ付け、バージョン管理機能付き" code
ai-code "素数判定関数を実装"

# 対話が必要な複雑タスク
ai-dialog "複雑なWebアプリケーションを設計したい"
ai-reply conv_dialog_20250701_123456 "ECサイトで、ハンドメイド商品を..."
```

### 情報確認
```bash
ai-status                           # 現在の状態
ai-logs task -f --grep ERROR       # エラーログをリアルタイム監視
ai-tasks --type code --limit 10    # 最近のコード生成タスク10件
ai-stats --period week             # 今週の統計
ai-metrics --summary               # メトリクスサマリー
```

### ワーカー管理
```bash
ai-workers                          # ワーカー状態確認
ai-worker-restart task             # TaskWorkerのみ再起動
ai-worker-restart all              # 全ワーカー再起動
```

### RAG検索
```bash
ai-rag-search "TaskWorker"         # 過去のタスクから検索
ai-rag-search "エラー処理" -c      # GitHubコードも含めて検索
```

### 設定確認
```bash
ai-config --list                   # 全設定ファイル一覧
ai-config slack                    # slack.conf の内容表示
ai-config --get slack.ENABLE_SLACK # 特定の設定値取得
```

### 新機能の使用
```bash
# タスクテンプレート
ai-template list                   # テンプレート一覧
ai-run daily_report               # テンプレート実行（ショートカット）

# Webダッシュボード
ai-webui start                    # ダッシュボード起動
ai-webui status                   # 状態確認

# スケジュール管理
ai-schedule add "0 9 * * *" "ai-run daily_report" --name "日次レポート"
ai-schedule list                  # スケジュール一覧
```

## 🎯 ショートカット・エイリアス

```bash
# ~/.bashrc に追加推奨
alias aic='ai-code'
alias aid='ai-dialog'
alias ais='ai-status'
alias ail='ai-logs'
alias aiw='ai-workers'
```

## 📊 コマンド分類

| カテゴリ | コマンド数 | 主な用途 |
|---------|-----------|---------|
| 基本操作 | 4 | システムの起動・停止・状態確認 |
| タスク実行 | 5 | AIタスクの送信・対話 |
| 情報表示 | 6 | ログ・統計・モニタリング |
| ワーカー管理 | 5 | ワーカーの制御・スケーリング |
| 設定管理 | 3 | 設定の確認・編集 |
| 新機能 | 9 | テンプレート・通信・DLQ等 |
| 開発支援 | 6 | デバッグ・テスト・仮想環境 |
| **合計** | **54** | 完全なAI基盤システム管理 |

## 🗑️ 削除されたコマンド（2025年7月精査）
- `ai-git-config` → ai-gitに統合
- `ai-slack-config` → ai-configに統合
- `ai-slack-detect` → 未使用のため削除
- `ai-venv-cmd` → 実装なしのため削除
- `ai-venv-helper` → 実装なしのため削除

---

💡 **Tips**: 
- `ai` コマンドだけでインタラクティブメニューが開きます
- ほとんどのコマンドは `--help` オプションで詳細ヘルプを表示
- `ai-help --list` で最新のコマンド一覧を確認可能
- 新機能は🆕マークで表示（実装済みは✅、部分実装は⚡）
