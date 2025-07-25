# Auto Issue Processor A2A 日常運用ガイド

## 📋 概要

このガイドでは、Auto Issue Processor A2Aの日常的な運用タスクと手順を説明します。

## 🌅 日次タスク

### 1. システムヘルスチェック（推奨時間: 9:00）

```bash
# システムステータス確認
./scripts/check_system_health.sh

# 処理統計確認
python3 -c "
from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
import asyncio
import json

async def check_stats():
    processor = AutoIssueProcessor()
    with open('logs/auto_issue_processing.json', 'r') as f:
        data = json.load(f)
    print(f'Yesterday processed: {len(data.get(\"recent_issues\", []))}')
    print(f'Success rate: {data.get(\"success_rate\", 0)}%')

asyncio.run(check_stats())
"
```

### 2. ログ確認とクリーンアップ

```bash
# エラーログ確認
grep -i error logs/auto_issue_processor.log | tail -20

# 古いログのアーカイブ（7日以上）
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;
find logs/ -name "*.gz" -mtime +30 -delete

# ディスク使用量確認
du -sh logs/
```

### 3. 処理キューの確認

```bash
# 未処理Issueの確認
gh issue list --label "auto-processable" --state open --limit 10

# 処理中のPR確認
gh pr list --search "Auto-fix" --state open
```

## 📅 週次タスク

### 1. パフォーマンスレビュー（推奨: 月曜日）

```bash
# 週次レポート生成
python3 scripts/generate_weekly_report.py

# 処理時間の分析
cat logs/auto_issue_processing.json | jq '.processing_times | add/length'
```

### 2. 依存関係の更新（推奨: 水曜日）

```bash
# セキュリティアップデートの確認
pip list --outdated
pip-audit

# 必要に応じて更新
pip install --upgrade -r requirements.txt
```

### 3. バックアップ（推奨: 金曜日）

```bash
# 設定とログのバックアップ
tar -czf backups/aip_backup_$(date +%Y%m%d).tar.gz \
  .env \
  logs/ \
  configs/ \
  knowledge_base/

# S3へのアップロード（オプション）
aws s3 cp backups/aip_backup_$(date +%Y%m%d).tar.gz \
  s3://your-backup-bucket/auto-issue-processor/
```

## 🔄 定期メンテナンス

### 月次タスク

#### 1. システムパフォーマンス最適化

```python
# キャッシュクリア
from libs.performance_optimizer import get_performance_optimizer

optimizer = get_performance_optimizer()
optimizer.clear_cache()
optimizer.reset_statistics()
```

#### 2. セキュリティ監査

```bash
# セキュリティスキャン実行
python3 -m libs.security_audit_system --full-scan

# 認証トークンのローテーション確認
echo "GitHub Token expires: $(gh auth status 2>&1 | grep 'Token:' | awk '{print $NF}')"
```

### 四半期タスク

#### 1. 容量計画

```bash
# リソース使用傾向分析
python3 scripts/analyze_resource_usage.py --period 90d

# 将来の容量予測
python3 scripts/capacity_planning.py --forecast 6m
```

## 🚨 緊急時対応

### システム停止時

```bash
# 1. ステータス確認
systemctl status auto-issue-processor

# 2. 再起動試行
systemctl restart auto-issue-processor

# 3. ログ確認
journalctl -u auto-issue-processor -n 100

# 4. 手動起動（デバッグモード）
python3 libs/integrations/github/auto_issue_processor.py --debug
```

### 処理エラー多発時

```bash
# 1. エラーパターン分析
grep ERROR logs/auto_issue_processor.log | \
  awk '{print $5}' | sort | uniq -c | sort -nr

# 2. 一時的な処理停止
touch /tmp/auto_issue_processor.pause

# 3. 問題調査
python3 scripts/diagnose_issues.py

# 4. 処理再開
rm /tmp/auto_issue_processor.pause
```

## 📊 監視ダッシュボード

### リアルタイム監視

```bash
# 監視ツール起動
./scripts/monitor_auto_issue_processor.sh

# 別ターミナルでメトリクス確認
watch -n 5 'curl -s http://localhost:8080/api/metrics | jq .'
```

### アラート設定

```yaml
# alerts.yaml
alerts:
  - name: high_error_rate
    condition: error_rate > 0.1
    action: email
    recipients: ["ops@example.com"]
  
  - name: processing_delay
    condition: avg_processing_time > 300
    action: slack
    channel: "#auto-issue-alerts"
```

## 🔧 チューニングパラメータ

### パフォーマンス設定

```bash
# .env ファイル
AUTO_ISSUE_MAX_PARALLEL=5      # 並列処理数
AUTO_ISSUE_TIMEOUT=300          # タイムアウト（秒）
AUTO_ISSUE_CACHE_SIZE=100       # キャッシュサイズ
AUTO_ISSUE_RETRY_COUNT=3        # リトライ回数
```

### リソース制限

```bash
# systemd設定
[Service]
CPUQuota=80%
MemoryLimit=2G
TasksMax=100
```

## 📝 運用チェックリスト

### 日次チェックリスト
- [ ] システムヘルスチェック完了
- [ ] エラーログ確認（Critical/Errorなし）
- [ ] 処理キュー確認（滞留なし）
- [ ] ディスク容量確認（80%未満）
- [ ] 監視アラート確認

### 週次チェックリスト
- [ ] パフォーマンスレポート作成
- [ ] 依存関係の更新確認
- [ ] バックアップ完了
- [ ] セキュリティアラート確認

### 月次チェックリスト
- [ ] キャッシュクリア実施
- [ ] セキュリティ監査完了
- [ ] 容量計画レビュー
- [ ] SLA達成率確認

## 🔗 関連ドキュメント

- [トラブルシューティングガイド](troubleshooting-guide.md)
- [最新改善事項](recent-improvements-july-2025.md)
- [監視設定ガイド](monitoring-setup-guide.md)

---
*最終更新: 2025年7月21日*