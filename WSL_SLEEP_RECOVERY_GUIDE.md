# 🚀 WSL スリープ復旧システム完全ガイド

**作成日**: 2025年7月9日  
**対象**: WSL2 + Windows環境でのAI Company運用

---

## 📋 問題と解決策

### 🔍 **問題**
- **PCスリープ時**: WSL内のワーカープロセスが停止
- **WSL再開時**: 手動でワーカーを再起動する必要がある
- **忘れやすい**: 復旧手順を忘れてシステムが停止したまま

### ✅ **解決策**
自動復旧システムを構築し、PCスリープ後も即座にワーカーが復活するようにします。

---

## 🛠️ インストール済みコンポーネント

### 1. **メインシステム**
- `scripts/wsl_sleep_recovery_system.py` - 完全復旧システム
- `scripts/wsl_quick_start.py` - 軽量起動スクリプト
- `scripts/auto_startup.sh` - 自動起動スクリプト

### 2. **Windows側**
- `start_ai_company.bat` - Windows実行用バッチファイル

### 3. **自動監視**
- **cron ジョブ**: 5分毎の自動復旧チェック
- **エルダーウォッチドッグ**: 継続的システム監視

---

## 🚀 使用方法

### 方法1: Windows バッチファイル（推奨）

```batch
# Windows コマンドプロンプトまたはPowerShellで実行
cd /path/to/ai_co
start_ai_company.bat
```

### 方法2: WSL内で直接実行

```bash
# WSL内で実行
cd /home/aicompany/ai_co

# クイックスタート（軽量版）
python3 scripts/wsl_quick_start.py

# 完全復旧版
python3 scripts/wsl_sleep_recovery_system.py
```

### 方法3: 自動起動スクリプト

```bash
# WSL起動時に自動実行
./scripts/auto_startup.sh
```

---

## 🔧 自動復旧の仕組み

### 1. **スリープ検出**
- 前回の状態保存から10分以上の空白時間を検出
- 必要なプロセスの停止を検出
- システムアップタイムの変化を検出

### 2. **段階的復旧**
```
1. サービス復旧   → RabbitMQ状態確認
2. ワーカー復旧   → check_and_fix_workers.py実行
3. プロセス復旧   → ウォッチドッグ・監視システム起動
4. 状態保存     → 次回の復旧基準として保存
```

### 3. **継続監視**
- **cron ジョブ**: 5分毎に自動復旧チェック
- **エルダーウォッチドッグ**: リアルタイム監視
- **ヘルスチェック**: システム状態の定期報告

---

## 📊 復旧システムの特徴

### ✅ **自動検出機能**
- スリープからの復旧を自動検出
- 停止したプロセスの特定
- 必要な復旧作業の自動判断

### ⚡ **高速復旧**
- 軽量版: 10秒以内で基本システム起動
- 完全版: 30秒以内で全システム復旧
- 段階的復旧で安全性を確保

### 🔄 **継続監視**
- 5分毎の自動ヘルスチェック
- 問題発生時の即座復旧
- 詳細ログによる問題追跡

---

## 📝 復旧ログの確認

### 主要ログファイル
```bash
# 復旧システムのログ
tail -f logs/wsl_recovery.log

# ウォッチドッグのログ
tail -f logs/elder_watchdog.log

# 自動起動のログ
tail -f logs/auto_startup.log

# ヘルスチェックのログ
tail -f logs/cron/health_alerts.log
```

---

## 🎯 日常の使用パターン

### 📅 **朝の起動時**
```bash
# PCを起動してWSLを開いたら
python3 scripts/wsl_quick_start.py
```

### 🌙 **夜の終了時**
```bash
# 特に何もしない（自動でスリープ対応）
# 状態は自動保存される
```

### 🔄 **昼間の再開時**
```bash
# WSLが既に起動していれば何もしない
# 自動復旧システムが働いている

# 手動で確認したい場合
python3 scripts/check_knight_patrol_status.py
```

---

## 🛡️ 騎士団巡回警備との連携

### 現在の状態
- **エルダーウォッチドッグ**: ✅ 稼働中
- **騎士団ファイル**: 231個配備完了
- **自動監視**: 5分毎のヘルスチェック

### 復旧後の確認
```bash
# 騎士団の状態確認
python3 scripts/check_knight_patrol_status.py

# ログの確認
tail -20 logs/elder_watchdog.log
```

---

## 🔧 トラブルシューティング

### 問題1: RabbitMQが起動しない
```bash
# 手動起動
sudo systemctl start rabbitmq-server

# 状態確認
systemctl status rabbitmq-server
```

### 問題2: ワーカーが起動しない
```bash
# 手動修復
python3 check_and_fix_workers.py

# 状態確認
ps aux | grep worker
```

### 問題3: ウォッチドッグが停止している
```bash
# 手動起動
nohup bash elder_watchdog.sh > /dev/null 2>&1 &

# 状態確認
ps aux | grep elder_watchdog
```

---

## 📈 システム監視ダッシュボード

### リアルタイム確認
```bash
# 現在の状態
python3 scripts/wsl_quick_start.py

# 詳細な状態確認
python3 scripts/check_knight_patrol_status.py

# 復旧システムの状態
python3 scripts/wsl_sleep_recovery_system.py
```

---

## 🎉 まとめ

### 🎯 **達成された目標**
- ✅ PCスリープ後の自動復旧
- ✅ WSL再開時の即座起動
- ✅ 継続的なシステム監視
- ✅ 簡単な手動復旧方法

### 🚀 **今後の拡張可能性**
- Windows タスクスケジューラとの連携
- より高度な障害検出
- 復旧性能の最適化

---

**これで、PCをスリープしても AI Company が自動で復活します！** 🛡️⚔️🚀

*作成者: クロードエルダー（AI Company開発実行責任者）*