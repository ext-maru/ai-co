# ⚙️ Auto Issue Processor A2A 運用者向け詳細運用ガイド

## 🎯 概要

このガイドでは、Auto Issue Processor A2Aの日常運用を担当する運用者向けに、詳細な運用手順と最適化手法を説明します。

## 📊 運用監視ダッシュボード

### リアルタイム監視コマンド

```bash
# メイン監視ダッシュボード
./scripts/monitor_auto_issue_processor.sh

# 別ターミナルで詳細監視
watch -n 5 'echo "=== System Status ===" && \
  ps aux | grep auto_issue_processor | head -3 && \
  echo "=== Processing Queue ===" && \
  curl -s http://localhost:8080/api/metrics | jq ".processing" && \
  echo "=== Recent Errors ===" && \
  tail -5 logs/auto_issue_processor.log | grep ERROR'
```

### パフォーマンスメトリクス

```python
# performance_monitor.py
import psutil
import json
from datetime import datetime

def collect_performance_metrics():
    """パフォーマンスメトリクス収集"""
    metrics = {
        'timestamp': datetime.utcnow().isoformat(),
        'system': {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg()[0]
        },
        'process': {},
        'application': {}
    }
    
    # Auto Issue Processor プロセス監視
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        if 'auto_issue_processor' in proc.info['name']:
            metrics['process'] = {
                'pid': proc.info['pid'],
                'cpu_percent': proc.info['cpu_percent'],
                'memory_percent': proc.info['memory_percent']
            }
            break
    
    # アプリケーションメトリクス
    try:
        with open('logs/auto_issue_processing.json', 'r') as f:
            app_data = json.load(f)
            metrics['application'] = {
                'total_processed': len(app_data.get('recent_issues', [])),
                'success_rate': app_data.get('success_rate', 0),
                'avg_processing_time': app_data.get('avg_processing_time', 0)
            }
    except Exception as e:
        metrics['application'] = {'error': str(e)}
    
    return metrics

# 使用例
if __name__ == "__main__":
    metrics = collect_performance_metrics()
    print(json.dumps(metrics, indent=2))
```

## 🔄 処理フロー管理

### キュー管理

```bash
# 処理待ちIssue確認
gh issue list --label "auto-processable" --state open --json number,title,createdAt

# 処理中タスク確認
curl -s http://localhost:8080/api/status | jq '.active_tasks'

# 処理完了PR確認
gh pr list --search "Auto-fix" --state open --json number,title,createdAt
```

### 処理優先度調整

```python
# priority_manager.py
from libs.integrations.github.auto_issue_processor import AutoIssueProcessor

class PriorityManager:
    """処理優先度管理"""
    
    def __init__(self):
        self.processor = AutoIssueProcessor()
    
    async def adjust_processing_capacity(self, load_level: str):
        """負荷レベルに応じた処理能力調整"""
        capacity_settings = {
            'low': {
                'max_parallel': 5,
                'target_priorities': ['critical', 'high', 'medium'],
                'processing_interval': 10
            },
            'medium': {
                'max_parallel': 3,
                'target_priorities': ['critical', 'high'],
                'processing_interval': 15
            },
            'high': {
                'max_parallel': 1,
                'target_priorities': ['critical'],
                'processing_interval': 30
            }
        }
        
        settings = capacity_settings.get(load_level, capacity_settings['medium'])
        
        # 環境変数更新
        os.environ['AUTO_ISSUE_MAX_PARALLEL'] = str(settings['max_parallel'])
        self.processor.target_priorities = settings['target_priorities']
        
        print(f"Processing capacity adjusted for {load_level} load")
        return settings

# 使用例
async def main():
    manager = PriorityManager()
    # システム負荷が高い時
    await manager.adjust_processing_capacity('high')
```

## 📈 パフォーマンス最適化

### 処理時間分析

```bash
# processing_analysis.sh
#!/bin/bash

echo "=== Processing Time Analysis ==="

# 平均処理時間
grep "PROCESSING_COMPLETED" logs/auto_issue_processor.log | \
  awk '{print $NF}' | awk '{sum+=$1; count++} END {printf "Average: %.2f seconds\n", sum/count}'

# 最長処理時間
grep "PROCESSING_COMPLETED" logs/auto_issue_processor.log | \
  awk '{print $NF}' | sort -n | tail -1 | \
  xargs printf "Longest: %.2f seconds\n"

# 処理時間分布
echo "=== Processing Time Distribution ==="
grep "PROCESSING_COMPLETED" logs/auto_issue_processor.log | \
  awk '{print $NF}' | \
  awk '{
    if ($1 < 60) fast++
    else if ($1 < 300) medium++
    else slow++
  } END {
    printf "Fast (<60s): %d\n", fast
    printf "Medium (60-300s): %d\n", medium  
    printf "Slow (>300s): %d\n", slow
  }'
```

### リソース最適化

```python
# resource_optimizer.py
import gc
import os
from libs.performance_optimizer import get_performance_optimizer

class ResourceOptimizer:
    """リソース最適化管理"""
    
    def __init__(self):
        self.optimizer = get_performance_optimizer()
    
    def optimize_memory(self):
        """メモリ最適化"""
        # ガベージコレクション強制実行
        collected = gc.collect()
        
        # キャッシュクリア
        self.optimizer.clear_cache()
        
        # 大きなオブジェクトの解放
        self.optimizer.cleanup_large_objects()
        
        return f"Memory optimized: {collected} objects collected"
    
    def optimize_disk_usage(self):
        """ディスク使用量最適化"""
        # 古いログの圧縮
        os.system("find logs/ -name '*.log' -mtime +7 -exec gzip {} \;")
        
        # 一時ファイル削除
        os.system("find /tmp -name 'auto_issue_*' -mtime +1 -delete")
        
        # キャッシュディレクトリクリーンアップ
        os.system("find cache/ -mtime +3 -delete")
        
        return "Disk usage optimized"
    
    def optimize_network(self):
        """ネットワーク最適化"""
        # 接続プール最適化
        self.optimizer.optimize_connection_pools()
        
        # APIレート制限調整
        self.optimizer.adjust_rate_limits()
        
        return "Network optimized"

# 使用例
optimizer = ResourceOptimizer()
print(optimizer.optimize_memory())
print(optimizer.optimize_disk_usage())
print(optimizer.optimize_network())
```

## 🔧 設定管理

### 動的設定変更

```python
# config_manager.py
import yaml
import json
from typing import Dict, Any

class ConfigManager:
    """設定管理"""
    
    def __init__(self):
        self.config_files = {
            'main': 'configs/auto_issue_processor.yaml',
            'quality': 'configs/quality_gate.yaml',
            'security': 'configs/security_settings.yaml'
        }
    
    def load_config(self, config_type: str) -> Dict[str, Any]:
        """設定読み込み"""
        with open(self.config_files[config_type], 'r') as f:
            return yaml.safe_load(f)
    
    def update_config(self, config_type: str, updates: Dict[str, Any]):
        """設定更新"""
        config = self.load_config(config_type)
        config.update(updates)
        
        with open(self.config_files[config_type], 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def get_runtime_config(self) -> Dict[str, Any]:
        """実行時設定取得"""
        return {
            'max_parallel': os.getenv('AUTO_ISSUE_MAX_PARALLEL', '3'),
            'timeout': os.getenv('AUTO_ISSUE_TIMEOUT', '300'),
            'log_level': os.getenv('AUTO_ISSUE_LOG_LEVEL', 'INFO'),
            'debug_mode': os.getenv('AUTO_ISSUE_DEBUG', 'false').lower() == 'true'
        }

# 使用例
config_mgr = ConfigManager()

# 品質ゲート基準を一時的に緩和
config_mgr.update_config('quality', {
    'minimum_score': 60,  # 通常は70
    'security_threshold': 8  # 通常は5
})
```

### 環境別設定

```yaml
# configs/environments.yaml
development:
  debug: true
  log_level: DEBUG
  max_parallel: 1
  timeout: 600
  use_cache: false

staging:
  debug: false
  log_level: INFO
  max_parallel: 2
  timeout: 300
  use_cache: true

production:
  debug: false
  log_level: WARNING
  max_parallel: 5
  timeout: 180
  use_cache: true
  enable_monitoring: true
```

## 📊 レポート生成

### 日次運用レポート

```python
# daily_report_generator.py
from datetime import datetime, timedelta
import json

def generate_daily_report():
    """日次運用レポート生成"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # ログ分析
    processed_issues = analyze_processed_issues(yesterday)
    error_analysis = analyze_errors(yesterday)
    performance_stats = analyze_performance(yesterday)
    
    report = {
        'date': yesterday.isoformat(),
        'summary': {
            'total_issues_processed': processed_issues['total'],
            'success_rate': processed_issues['success_rate'],
            'avg_processing_time': performance_stats['avg_time'],
            'errors_count': error_analysis['total_errors']
        },
        'issues_breakdown': processed_issues['breakdown'],
        'performance': performance_stats,
        'errors': error_analysis['error_types'],
        'recommendations': generate_recommendations(processed_issues, error_analysis, performance_stats)
    }
    
    # レポート保存
    report_file = f'reports/daily_report_{yesterday.strftime("%Y%m%d")}.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def generate_recommendations(issues, errors, performance):
    """改善提案生成"""
    recommendations = []
    
    # 成功率が低い場合
    if issues['success_rate'] < 80:
        recommendations.append({
            'type': 'alert',
            'message': 'Success rate below threshold (80%)',
            'action': 'Review error logs and adjust quality gate settings'
        })
    
    # 処理時間が長い場合
    if performance['avg_time'] > 300:
        recommendations.append({
            'type': 'optimization',
            'message': 'Average processing time exceeds 5 minutes',
            'action': 'Consider reducing parallel processing or optimizing code generation'
        })
    
    # エラーが多い場合
    if errors['total_errors'] > 10:
        recommendations.append({
            'type': 'maintenance',
            'message': 'High error count detected',
            'action': 'Investigate most common error types and apply fixes'
        })
    
    return recommendations
```

### 週次パフォーマンスレポート

```bash
# weekly_performance_report.sh
#!/bin/bash

WEEK_START=$(date -d '7 days ago' '+%Y-%m-%d')
WEEK_END=$(date '+%Y-%m-%d')

echo "=== Weekly Performance Report ($WEEK_START to $WEEK_END) ==="

# 処理統計
echo "## Processing Statistics"
grep "ISSUE_PROCESSED" logs/auto_issue_processor.log | \
  grep -E "$WEEK_START|$WEEK_END" | wc -l | \
  xargs printf "Total Issues Processed: %d\n"

# 成功率
SUCCESS_COUNT=$(grep "PR_CREATED_SUCCESS" logs/auto_issue_processor.log | \
  grep -E "$WEEK_START|$WEEK_END" | wc -l)
TOTAL_COUNT=$(grep "ISSUE_PROCESSED" logs/auto_issue_processor.log | \
  grep -E "$WEEK_START|$WEEK_END" | wc -l)

if [ $TOTAL_COUNT -gt 0 ]; then
  awk "BEGIN {printf \"Success Rate: %.1f%%\n\", ($SUCCESS_COUNT/$TOTAL_COUNT)*100}"
fi

# エラー分析
echo "## Error Analysis"
grep "ERROR" logs/auto_issue_processor.log | \
  grep -E "$WEEK_START|$WEEK_END" | \
  awk '{print $5}' | sort | uniq -c | sort -nr | head -5
```

## 🚨 アラート管理

### カスタムアラート設定

```python
# alert_manager.py
import smtplib
import json
from email.mime.text import MIMEText
from datetime import datetime

class AlertManager:
    """アラート管理"""
    
    def __init__(self):
        self.alert_rules = self.load_alert_rules()
        self.notification_channels = {
            'email': self.send_email_alert,
            'slack': self.send_slack_alert,
            'webhook': self.send_webhook_alert
        }
    
    def check_alert_conditions(self, metrics: dict):
        """アラート条件チェック"""
        for rule in self.alert_rules:
            if self.evaluate_condition(rule['condition'], metrics):
                self.trigger_alert(rule, metrics)
    
    def evaluate_condition(self, condition: str, metrics: dict) -> bool:
        """条件評価"""
        # 安全な条件評価
        allowed_keys = metrics.keys()
        for key in allowed_keys:
            condition = condition.replace(key, f"metrics['{key}']")
        
        try:
            return eval(condition)
        except:
            return False
    
    def trigger_alert(self, rule: dict, metrics: dict):
        """アラート発動"""
        alert_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'rule_name': rule['name'],
            'severity': rule['severity'],
            'message': rule['message'],
            'metrics': metrics
        }
        
        # 通知送信
        for channel in rule['channels']:
            if channel in self.notification_channels:
                self.notification_channels[channel](alert_data)
    
    def send_email_alert(self, alert_data: dict):
        """メールアラート送信"""
        msg = MIMEText(json.dumps(alert_data, indent=2))
        msg['Subject'] = f"[AUTO-ISSUE] {alert_data['severity']}: {alert_data['rule_name']}"
        msg['From'] = 'auto-issue-processor@example.com'
        msg['To'] = 'ops-team@example.com'
        
        # SMTP送信（設定に応じて）
        # smtp = smtplib.SMTP('localhost')
        # smtp.send_message(msg)
        # smtp.quit()

# alert_rules.yaml
rules:
  - name: high_error_rate
    condition: "error_rate > 0.1"
    severity: HIGH
    message: "Error rate exceeds 10%"
    channels: ["email", "slack"]
  
  - name: processing_delay
    condition: "avg_processing_time > 300"
    severity: MEDIUM
    message: "Processing time exceeds 5 minutes"
    channels: ["slack"]
  
  - name: memory_usage_high
    condition: "memory_percent > 80"
    severity: MEDIUM
    message: "Memory usage exceeds 80%"
    channels: ["email"]
```

## 📋 運用チェックリスト

### 日次運用チェックリスト

```markdown
## 日次運用チェックリスト

### システム健全性 (毎朝9:00)
- [ ] システムステータス確認
- [ ] プロセス生存確認
- [ ] リソース使用率確認（CPU < 70%, Memory < 80%, Disk < 80%）
- [ ] ログエラー確認（前日分）

### 処理状況確認 (毎朝9:15)
- [ ] 前日処理Issue数確認
- [ ] 成功率確認（目標: >85%）
- [ ] 処理待ちキュー確認
- [ ] 異常な処理時間Issue確認

### 運用メトリクス (毎朝9:30)
- [ ] API使用量確認
- [ ] ストレージ使用量確認
- [ ] バックアップ状況確認
- [ ] セキュリティアラート確認

### 品質監視 (毎朝9:45)
- [ ] 生成されたPRの品質確認
- [ ] テスト失敗率確認
- [ ] コードレビュー待ちPR確認
- [ ] 品質ゲート失敗Issue確認
```

### 週次運用チェックリスト

```markdown
## 週次運用チェックリスト (毎週月曜日)

### パフォーマンス分析
- [ ] 週次パフォーマンスレポート生成
- [ ] 処理時間トレンド分析
- [ ] リソース使用傾向確認
- [ ] ボトルネック特定

### 設定最適化
- [ ] 並列処理数調整検討
- [ ] 品質ゲート基準見直し
- [ ] タイムアウト設定確認
- [ ] キャッシュ設定最適化

### 保守作業
- [ ] ログローテーション確認
- [ ] 依存関係更新確認
- [ ] セキュリティパッチ適用
- [ ] データベース最適化

### レポート作成
- [ ] 運用サマリーレポート作成
- [ ] 改善提案書作成
- [ ] インシデント振り返り
- [ ] 次週運用計画策定
```

## 🔗 関連ドキュメント

- [日常運用ガイド](../runbooks/daily-operations-guide.md)
- [トラブルシューティングガイド](../runbooks/troubleshooting-guide.md)
- [インシデント対応ガイド](../runbooks/incident-response-guide.md)
- [管理者向けセキュリティガイド](administrator-security-guide.md)

---
*最終更新: 2025年7月21日*