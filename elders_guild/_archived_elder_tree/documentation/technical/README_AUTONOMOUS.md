# 🤖 Knights Autonomous Guardian System

## 概要

騎士団自律守護システム - 完全自律的な24/7監視・診断・修復システムです。人間の介入なしにシステムの健康状態を維持し、問題を自動で検出・修復します。

## 🌟 主要機能

### 🔍 自動監視
- **リアルタイム監視**: 1分間隔でシステム全体をチェック
- **包括的チェック**: GitHub Actions、ローカル騎士団、ワーカー、RabbitMQ
- **予測的監視**: 問題が発生する前に警告

### 🔧 自動修復
- **ワーカー修復**: 停止したワーカーの自動再起動
- **RabbitMQ管理**: 接続問題の自動解決
- **依存関係更新**: パッケージの自動アップデート
- **ログ管理**: 古いログファイルの自動クリーンアップ

### 🛡️ セルフヒーリング
- **リトライ機能**: 失敗時の自動再試行
- **エスカレーション**: 重要な問題の手動介入要請
- **メンテナンスモード**: 自動修復の一時停止機能

## 🚀 セットアップ

### 1. 自動セットアップ（推奨）

```bash
# 自律運用システムを自動セットアップ
sudo ./scripts/setup_autonomous_service.sh
```

このスクリプトは以下を自動で設定します：
- systemdサービス作成
- ログローテーション設定
- Cron監視ジョブ
- 必要最小限のsudo権限
- 仮想環境とパッケージ

### 2. 手動起動

```bash
# 直接実行（テスト用）
python3 scripts/knights_autonomous_guardian.py

# メンテナンスモード（自動修復無効）
python3 scripts/knights_autonomous_guardian.py --maintenance

# チェック間隔変更（デフォルト60秒）
python3 scripts/knights_autonomous_guardian.py --interval 30

# ヘルスレポート表示
python3 scripts/knights_autonomous_guardian.py --report
```

## 📊 監視項目

### システムヘルス
- **ワーカー状況**: 期待される3つのワーカーの稼働状態
- **RabbitMQ接続**: メッセージキューの接続状態
- **騎士団スクリプト**: ローカル騎士団の実行可能性
- **ディスク容量**: 85%以上で自動ログクリーンアップ

### 自動修復ルール

| 問題 | 条件 | アクション | 重要度 | 自動実行 |
|------|------|------------|---------|----------|
| ワーカー停止 | 実行中 < 期待数 | ワーカー修復 | High | ✅ |
| RabbitMQ切断 | 接続失敗 | RabbitMQ再起動 | Critical | ✅ |
| 騎士団エラー | スクリプト実行失敗 | 依存関係更新 | Medium | ✅ |
| ディスク不足 | 使用率 > 85% | ログクリーンアップ | Medium | ✅ |

## 🔧 運用管理

### サービス管理

```bash
# サービス状態確認
sudo systemctl status knights-guardian

# サービス開始/停止/再起動
sudo systemctl start knights-guardian
sudo systemctl stop knights-guardian
sudo systemctl restart knights-guardian

# リアルタイムログ確認
sudo journalctl -u knights-guardian -f
```

### ログ監視

```bash
# アプリケーションログ
tail -f logs/knights_autonomous.log

# サービスログ
tail -f /var/log/knights-guardian/stdout.log
tail -f /var/log/knights-guardian/stderr.log

# ヘルスレポート
ls /var/log/knights-guardian/health_*.log
```

### 統計情報

```bash
# 現在の統計表示
python3 scripts/knights_autonomous_guardian.py --report
```

出力例：
```json
{
  "guardian_status": {
    "running": true,
    "uptime_hours": 24.5,
    "maintenance_mode": false
  },
  "statistics": {
    "total_checks": 1440,
    "total_issues_detected": 15,
    "total_auto_repairs": 12,
    "successful_repairs": 10,
    "failed_repairs": 2,
    "escalations": 1
  },
  "efficiency_metrics": {
    "success_rate": 83.3,
    "average_checks_per_hour": 60,
    "escalation_rate": 6.7
  }
}
```

## ⚙️ 設定カスタマイズ

### チェック間隔の調整

```bash
# サービス設定ファイル編集
sudo systemctl edit knights-guardian
```

```ini
[Service]
ExecStart=
ExecStart=/home/aicompany/ai_co/venv/bin/python scripts/knights_autonomous_guardian.py --interval 30
```

### 自動修復ルールの変更

`scripts/knights_autonomous_guardian.py`の`auto_repair_rules`セクションを編集：

```python
self.auto_repair_rules = {
    "custom_rule": {
        "condition": lambda status: your_condition_here,
        "action": "your_action_here",
        "severity": "high",
        "auto_execute": True
    }
}
```

## 🚨 トラブルシューティング

### よくある問題

1. **サービスが起動しない**
   ```bash
   # ログで詳細確認
   sudo journalctl -u knights-guardian --no-pager

   # 権限確認
   ls -la /home/aicompany/ai_co/scripts/knights_autonomous_guardian.py
   ```

2. **自動修復が動作しない**
   ```bash
   # メンテナンスモード確認
   python3 scripts/knights_autonomous_guardian.py --report

   # sudo権限確認
   sudo -l
   ```

3. **ログが出力されない**
   ```bash
   # ログディレクトリ権限確認
   ls -la logs/
   ls -la /var/log/knights-guardian/
   ```

### エスカレーション対応

システムが自動修復できない問題が発生した場合：

1. **critical.log**を確認
2. **escalation通知**をチェック
3. **手動介入**実行
4. **根本原因**を特定・修正

## 📈 パフォーマンス監視

### CPU・メモリ使用量

```bash
# サービスのリソース使用量
systemctl show knights-guardian --property=CPUUsageNSec,MemoryCurrent

# プロセス詳細
ps aux | grep knights_autonomous_guardian
```

### 効率メトリクス

- **成功率**: 90%以上が目標
- **平均チェック頻度**: 60回/時間
- **エスカレーション率**: 5%以下が目標

## 🔒 セキュリティ

### 最小権限の原則

システムは以下の最小限の権限のみで動作：
- RabbitMQサービスの再起動権限
- プロジェクトディレクトリの読み書き権限
- ログディレクトリの読み書き権限

### 監査ログ

全ての自動アクションは以下に記録：
- `/var/log/knights-guardian/`
- `logs/knights_autonomous.log`
- systemd journal

## 🎯 運用のベストプラクティス

1. **定期的な統計確認**: 週1回の効率メトリクス確認
2. **エスカレーション対応**: 24時間以内の手動介入
3. **ログ監視**: 重要な問題の早期発見
4. **設定調整**: 環境に応じたルールのカスタマイズ
5. **バックアップ**: 設定ファイルの定期バックアップ

---

## 🎉 結論

Knights Autonomous Guardian Systemにより、騎士団は完全自律的に運用され、24/7の監視・修復体制が確立されます。人間の介入を最小限に抑えながら、高い稼働率とシステムの健全性を維持できます。
