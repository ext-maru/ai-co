---
audience: developers
author: claude-elder
category: technical
dependencies: []
description: No description available
difficulty: intermediate
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: approved
subcategory: architecture
tags:
- technical
- python
title: 🔧 Command Executor 修復・監視システム v2.0
version: 1.0.0
---

# 🔧 Command Executor 修復・監視システム v2.0

## 📋 概要

Command Executorの安定性を大幅に向上させる修復・監視システムです。自動プログラム実行が停止する問題を完全に解決し、24時間365日の安定稼働を実現します。

**v2.0 新機能:**
- 🔍 包括的診断システム
- 🔧 自動修復機能
- 👁️ Watchdog監視
- 🔄 永続化設定

## 🚨 問題と解決策

### 確認された問題
1. **プロセスの予期しない停止**
   - 原因: システムリソース、エラーの蓄積
   - 解決: Watchdog監視による自動再起動

2. **pendingファイルの処理停止**
   - 原因: ワーカーのハング、ディレクトリ権限
   - 解決: 定期的な健全性チェックと自動修正

3. **再起動後の自動起動失敗**
   - 原因: 永続化設定の不足
   - 解決: crontab/systemdによる自動起動

## 🛠️ 修復システムコンポーネント

### 1. 診断スクリプト (`diagnose_command_executor.py`)

包括的な診断を実行し、問題を自動修正します。

```python
# 使用方法
cd /home/aicompany/ai_co
python3 scripts/diagnose_command_executor.py

# 診断内容
- プロセス状態（psutil使用）
- ディレクトリ構造
- ログファイル分析
- tmuxセッション確認
- 実行テスト
```

**自動修正機能:**
- プロセスが存在しない → tmuxで自動起動
- ディレクトリが存在しない → 自動作成
- 古いpendingファイル → アーカイブ

### 2. 健全性チェック (`check_executor_health.sh`)

システムの健全性を確認し、問題を修正するBashスクリプト。

```bash
# 使用方法
./scripts/check_executor_health.sh

# チェック項目
- プロセス動作確認
- ディレクトリ整合性
- ログの更新状況
- テスト実行
- Watchdog起動提案
```

### 3. Watchdogシステム (`executor_watchdog.py`)

Command Executorを常時監視し、停止時に自動再起動します。

```python
# 特徴
- 30秒ごとにプロセス監視
- 停止検出時の自動再起動
- 最大10回まで再起動試行
- Slack通知機能

# 起動方法
tmux new-session -d -s executor_watchdog 'python3 workers/executor_watchdog.py'
```

### 4. 永続化設定 (`setup_executor_persistence.py`)

システム再起動後も自動的に起動するよう設定します。

```python
# 生成される設定
1. systemdサービスファイル
2. cron用スクリプト
3. 設定手順ドキュメント

# 実行
python3 scripts/setup_executor_persistence.py
```

## 🔄 完全修復プロセス

### 修復プログラム (`fix_executor_complete.py`)

5段階の自動修復プロセスを実行します：

```python
# 実行方法
python3 fix_executor_complete.py

# 修復ステップ
1. 診断実行
2. 健全性チェックと修正
3. Watchdog起動
4. 永続化設定
5. 最終動作確認
```

各ステップは順次実行され、進捗がSlackに通知されます。

## 📊 監視・管理コマンド

### AI Command Executor管理

```bash
# 状態確認
ai-cmd-executor status

# 診断実行
python3 scripts/diagnose_command_executor.py

# 健全性チェック
./scripts/check_executor_health.sh

# ログ監視
tail -f /home/aicompany/ai_co/logs/command_executor.log
```

### tmuxセッション管理

```bash
# セッション一覧
tmux list-sessions

# Command Executorセッションに接続
tmux attach -t command_executor

# Watchdogセッションに接続
tmux attach -t executor_watchdog

# セッションから離脱
Ctrl+B, D
```

## 🎯 トラブルシューティング

### 問題: 実行が停止している

```bash
# 1. 診断実行
python3 scripts/diagnose_command_executor.py

# 2. 手動再起動（必要な場合）
tmux new-session -d -s command_executor 'cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/command_executor_worker.py'

# 3. Watchdog起動
tmux new-session -d -s executor_watchdog 'cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/executor_watchdog.py'
```

### 問題: pendingファイルが処理されない

```bash
# 古いファイルの確認
find /home/aicompany/ai_co/ai_commands/pending -mmin +30 -type f

# 手動でcompletedに移動
find /home/aicompany/ai_co/ai_commands/pending -mmin +30 -type f -exec mv {} /home/aicompany/ai_co/ai_commands/completed/ \;

# プロセス再起動
ai-cmd-executor stop && ai-cmd-executor start
```

### 問題: ログが出力されない

```bash
# ディレクトリ権限確認
ls -la /home/aicompany/ai_co/ai_commands/logs/

# 権限修正
chmod 755 /home/aicompany/ai_co/ai_commands/logs/

# ログファイル確認
tail -n 50 /home/aicompany/ai_co/logs/command_executor.log
```

## 🔐 永続化設定

### 方法1: crontab（推奨）

```bash
# crontabに追加
crontab -e

# 以下を追加（5分ごとにチェック）
*/5 * * * * /home/aicompany/ai_co/scripts/ensure_executor_running.sh >> /home/aicompany/ai_co/logs/cron_executor.log 2>&1
```

### 方法2: systemd

```bash
# サービスファイルをコピー
sudo cp /home/aicompany/ai_co/config/ai-command-executor.service /etc/systemd/system/

# サービス有効化
sudo systemctl daemon-reload
sudo systemctl enable ai-command-executor
sudo systemctl start ai-command-executor
```

### 方法3: tmux永続化

```bash
# .bashrcに追加
echo 'tmux new-session -d -s command_executor "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/command_executor_worker.py"' >> ~/.bashrc
```

## 📈 パフォーマンス最適化

### リソース使用状況

```bash
# CPU/メモリ使用率確認
ps aux | grep command_executor
htop -p $(pgrep -f command_executor_worker.py)

# ディスク使用状況
du -sh /home/aicompany/ai_co/ai_commands/*
```

### ログローテーション（手動）

```bash
# 古いログのアーカイブ
cd /home/aicompany/ai_co/ai_commands/logs
tar -czf archive_$(date +%Y%m%d).tar.gz *.log
find . -name "*.log" -mtime +30 -delete
```

## 🚀 ベストプラクティス

### 1. 定期的な監視

```python
# AIから定期的に状態確認
helper.create_bash_command("""
echo "=== Command Executor Health Check ==="
ps aux | grep command_executor | grep -v grep
ls -la /home/aicompany/ai_co/ai_commands/pending | wc -l
tail -5 /home/aicompany/ai_co/logs/command_executor.log
""", "periodic_health_check")
```

### 2. エラーハンドリング

```python
# コマンド作成時のエラーハンドリング
try:
    result = helper.create_bash_command(cmd, cmd_id)
    time.sleep(10)
    check = helper.check_results(cmd_id)

    if check.get('exit_code', 1) != 0:
        # エラー処理
        log = helper.get_latest_log(cmd_id)
        # 分析と対処
except Exception as e:
    # 例外処理
```

### 3. Slack通知活用

```python
# 重要なイベントの通知
slack.send_message(
    f"⚠️ Command Executor Alert\n"
    f"Status: {status}\n"
    f"Action: {action_taken}"
)
```

## 📋 メンテナンスチェックリスト

### 日次
- [ ] プロセス動作確認
- [ ] pendingディレクトリ確認
- [ ] エラーログ確認

### 週次
- [ ] ディスク使用量確認
- [ ] 古いログのクリーンアップ
- [ ] パフォーマンス分析

### 月次
- [ ] 完全診断実行
- [ ] 設定見直し
- [ ] アップデート確認

---

**🎯 この修復・監視システムにより、Command Executorは24時間365日安定稼働を実現します**
