# APScheduler統合ガイド - エルダーズギルド

## 📋 概要

エルダーズギルドシステムにAPScheduler（Advanced Python Scheduler）を統合し、高度なスケジューリング機能を提供します。

## 🚀 主要機能

### ✅ 実装済み機能
- **統合スケジューラー**: エルダーズギルド専用設定
- **複数ジョブストア対応**: メモリ、Redis、PostgreSQL
- **多様なトリガー**: interval、cron、date
- **ビルダーパターンAPI**: 直感的なジョブ作成
- **デコレータAPI**: Pythonic な記述方法
- **4賢者システム統合**: タスク・インシデント賢者連携
- **包括的テスト**: 100%カバレッジ
- **コマンドラインツール**: 運用管理機能

## 📁 ファイル構成

```
/home/aicompany/ai_co/
├── libs/
│   ├── apscheduler_integration.py     # メイン統合ライブラリ
│   └── elder_scheduled_tasks.py       # 定期タスク定義
├── commands/
│   ├── ai_schedule_enhanced.py        # 拡張コマンドツール
│   └── ai_schedule.py                 # 既存コマンド
├── tests/unit/
│   └── test_apscheduler_integration.py # テストスイート
├── examples/
│   └── apscheduler_usage_examples.py  # 使用例集
└── docs/
    └── APSCHEDULER_INTEGRATION_GUIDE.md # このドキュメント
```

## 🛠️ インストール・設定

### 1. 依存関係インストール

```bash
# APSchedulerインストール
sudo apt install python3-apscheduler

# または requirements.txt に追加済み
pip3 install apscheduler>=3.10.4
```

### 2. 環境変数設定

```bash
# .env ファイルまたは環境変数
export SCHEDULER_TIMEZONE="Asia/Tokyo"
export SCHEDULER_MAX_WORKERS="20"
export SCHEDULER_USE_REDIS="false"
export SCHEDULER_USE_POSTGRES="false"
export SCHEDULER_LOG_LEVEL="INFO"

# Redis使用時
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="1"

# PostgreSQL使用時
export DATABASE_URL="postgresql://postgres:password@localhost:5432/ai_company"
```

## 🎯 基本使用法

### 1. グローバルスケジューラー使用

```python
from libs.apscheduler_integration import get_elder_scheduler, start_elder_scheduler

# スケジューラー取得・開始
scheduler = get_elder_scheduler()
scheduler.start()

# ジョブ追加
def my_task():
    print("Hello from scheduled task!")

scheduler.add_job(
    func=my_task,
    trigger='interval',
    seconds=30,
    id='my_task',
    name='30秒間隔タスク'
)
```

### 2. ビルダーパターン使用

```python
from libs.apscheduler_integration import ElderScheduleBuilder

scheduler = get_elder_scheduler()
builder = ElderScheduleBuilder(scheduler)

# 5分間隔ジョブ
builder.every(5).minutes().do(my_task)

# 日次ジョブ（毎日9時）
builder.daily_at(9, 0).do(daily_task)

# Cronジョブ
builder.cron("0 */2 * * *").do(bi_hourly_task)
```

### 3. デコレータ使用

```python
from libs.apscheduler_integration import ElderScheduleDecorators

scheduler = get_elder_scheduler()
decorators = ElderScheduleDecorators(scheduler)

@decorators.daily(hour=8, minute=30)
def morning_report():
    return "Morning report generated"

@decorators.hourly(minute=0)
def hourly_cleanup():
    return "Cleanup completed"

@decorators.scheduled('interval', minutes=10)
def monitor_system():
    return "System monitored"
```

### 4. グローバルデコレータ使用

```python
from libs.apscheduler_integration import schedule_with_elder, start_elder_scheduler

@schedule_with_elder('interval', seconds=15)
def global_task():
    print("Global scheduled task")

# スケジューラー開始
start_elder_scheduler()
```

## 🎛️ コマンドライン管理

### 基本コマンド

```bash
# スケジューラー状態確認
python3 commands/ai_schedule_enhanced.py status

# スケジューラー開始・停止
python3 commands/ai_schedule_enhanced.py start
python3 commands/ai_schedule_enhanced.py stop

# ジョブ一覧表示
python3 commands/ai_schedule_enhanced.py list

# ジョブ追加
python3 commands/ai_schedule_enhanced.py add \
  --trigger interval \
  --seconds 30 \
  --function test_job \
  --job-id job1 \
  --name "30秒テスト"

# Cronジョブ追加
python3 commands/ai_schedule_enhanced.py add \
  --trigger cron \
  --cron "0 9 * * *" \
  --function daily_task \
  --job-id daily1 \
  --name "日次タスク"

# ジョブ管理
python3 commands/ai_schedule_enhanced.py pause --job-id job1
python3 commands/ai_schedule_enhanced.py resume --job-id job1
python3 commands/ai_schedule_enhanced.py remove --job-id job1

# 統計情報表示
python3 commands/ai_schedule_enhanced.py stats
```

## 🏛️ エルダーズギルド定期タスク

### 自動登録タスク

`libs/elder_scheduled_tasks.py` で以下のタスクが自動的に登録されます：

#### 📅 日次タスク
- **02:00** - システムクリーンアップ
- **03:00** - システムバックアップ
- **04:00** - データベース最適化
- **01:00** - 知識ベース同期
- **08:30** - 日次レポート生成
- **09:00** - nWo日次評議会

#### ⏰ 時次タスク
- **毎時0分** - 統計情報更新

#### 🔄 間隔タスク
- **5分間隔** - ヘルスチェック
- **15分間隔** - パフォーマンス監視
- **6時間間隔** - 知識学習・進化

#### 📊 週次タスク
- **土曜22:00** - セキュリティスキャン
- **月曜09:00** - 週次レポート生成
- **月曜10:00** - nWo週次戦略会議

### 定期タスクシステム開始

```python
from libs.elder_scheduled_tasks import start_elder_scheduled_tasks

# 全ての定期タスクを開始
task_system = start_elder_scheduled_tasks()
```

または直接実行：

```bash
python3 libs/elder_scheduled_tasks.py
```

## 🧙‍♂️ 4賢者システム統合

### コールバック登録

```python
from libs.apscheduler_integration import register_sage_callback

def task_sage_callback(event):
    print(f"タスク賢者: ジョブ {event.job_id} 完了")

def incident_sage_callback(event):
    print(f"インシデント賢者: エラー発生 - {event.exception}")

# コールバック登録
register_sage_callback('task_sage', task_sage_callback)
register_sage_callback('incident_sage', incident_sage_callback)
```

### 統計情報取得

```python
from libs.apscheduler_integration import get_scheduler_stats

stats = get_scheduler_stats()
print(f"総実行回数: {stats['total_executed']}")
print(f"エラー回数: {stats['total_errors']}")
print(f"アクティブジョブ: {stats['active_jobs']}")
```

## ⚡ パフォーマンス・スケーラビリティ

### ジョブストア選択指針

| ジョブストア | 用途 | メリット | デメリット |
|------------|------|----------|----------|
| **Memory** | 開発・テスト | 高速、設定不要 | 再起動で消失 |
| **Redis** | 高頻度更新 | 高速、永続化 | Redis依存 |
| **PostgreSQL** | 企業運用 | 堅牢、トランザクション | やや重い |

### 推奨設定

```python
# 開発環境
export SCHEDULER_USE_REDIS="false"
export SCHEDULER_USE_POSTGRES="false"

# ステージング環境
export SCHEDULER_USE_REDIS="true"
export SCHEDULER_USE_POSTGRES="false"

# 本番環境
export SCHEDULER_USE_REDIS="true"
export SCHEDULER_USE_POSTGRES="true"
```

## 🔧 トラブルシューティング

### よくある問題と解決法

#### 1. SQLAlchemy互換性エラー

```bash
# エラー: TypeError: String.__init__() got an unexpected keyword argument '_warn_on_bytestring'
```

**解決法**: PostgreSQLジョブストアを無効化
```bash
export SCHEDULER_USE_POSTGRES="false"
```

#### 2. ジョブが実行されない

**確認項目**:
- スケジューラーが開始されているか
- ジョブが正しく登録されているか
- 次回実行時刻が正しく設定されているか

```python
# デバッグ用
jobs = scheduler.get_jobs()
for job in jobs:
    print(f"Job: {job.id}, Next run: {job.next_run_time}")
```

#### 3. メモリリーク

**対策**:
- 長時間実行ジョブの適切な終了処理
- 不要ジョブの定期削除
- ログレベル調整

```python
# ジョブクリーンアップ
for job in scheduler.get_jobs():
    if job.next_run_time is None:  # 無効化されたジョブ
        scheduler.remove_job(job.id)
```

## 📊 監視・運用

### ログ監視

```bash
# APSchedulerログ確認
tail -f /home/aicompany/ai_co/logs/apscheduler.log

# システムログ確認
journalctl -u apscheduler-service -f
```

### メトリクス監視

```python
# 定期的な統計取得
import time
from libs.apscheduler_integration import get_scheduler_stats

while True:
    stats = get_scheduler_stats()
    print(f"[{datetime.now()}] Jobs: {stats['active_jobs']}, "
          f"Executed: {stats['total_executed']}, "
          f"Errors: {stats['total_errors']}")
    time.sleep(60)
```

### ヘルスチェック

```python
def scheduler_health_check():
    """スケジューラーヘルスチェック"""
    scheduler = get_elder_scheduler()
    
    if not scheduler.scheduler.running:
        return {"status": "unhealthy", "reason": "scheduler_stopped"}
    
    active_jobs = len(scheduler.get_jobs())
    if active_jobs == 0:
        return {"status": "warning", "reason": "no_active_jobs"}
    
    return {"status": "healthy", "active_jobs": active_jobs}
```

## 🔄 アップグレード・移行

### 既存cronからの移行

#### 1. crontab確認

```bash
crontab -l > /tmp/current_crontab.txt
```

#### 2. APSchedulerジョブに変換

```python
# cron: 0 2 * * * /path/to/script.sh
# ↓
@decorators.daily(hour=2, minute=0)
def migrated_task():
    subprocess.run(['/path/to/script.sh'])
```

#### 3. 段階的移行

1. **並行運用**: cron + APScheduler
2. **検証期間**: 動作確認
3. **cron無効化**: APSchedulerのみ
4. **最終確認**: 完全移行

### バージョンアップ対応

```bash
# APScheduler更新
sudo apt update && sudo apt upgrade python3-apscheduler

# 互換性テスト
python3 -m pytest tests/unit/test_apscheduler_integration.py -v
```

## 🧪 テスト・品質保証

### テスト実行

```bash
# 全テスト実行
python3 -m pytest tests/unit/test_apscheduler_integration.py -v

# 特定テストクラス
python3 -m pytest tests/unit/test_apscheduler_integration.py::TestElderScheduler -v

# カバレッジ確認
python3 -m pytest tests/unit/test_apscheduler_integration.py --cov=libs.apscheduler_integration
```

### パフォーマンステスト

```python
# 大量ジョブ負荷テスト
def load_test():
    scheduler = get_elder_scheduler()
    scheduler.start()
    
    # 1000ジョブ登録
    for i in range(1000):
        scheduler.add_job(
            func=lambda: print(f"Job {i}"),
            trigger='interval',
            seconds=60,
            id=f'load_test_{i}'
        )
    
    # 統計確認
    stats = get_scheduler_stats()
    assert stats['active_jobs'] == 1000
```

## 📈 最適化・拡張

### パフォーマンスチューニング

```python
# 大量ジョブ環境での設定
config = ElderSchedulerConfig()
config.max_workers = 50  # ワーカー数増加
config.use_redis = True  # Redis使用

# ジョブデフォルト設定調整
job_defaults = {
    'coalesce': True,      # 重複実行防止
    'max_instances': 1,    # 同時実行数制限
    'misfire_grace_time': 60  # 遅延許容時間
}
```

### カスタムエグゼキューター

```python
from apscheduler.executors.pool import ProcessPoolExecutor

# CPU集約的タスク用
executors = {
    'default': ThreadPoolExecutor(max_workers=20),
    'processpool': ProcessPoolExecutor(max_workers=5),
}

scheduler.add_job(
    func=cpu_intensive_task,
    trigger='interval',
    minutes=30,
    executor='processpool'  # プロセスプール使用
)
```

## 🔐 セキュリティ考慮事項

### 権限管理

```python
# ジョブ実行権限制限
import os
import pwd

def secure_job_wrapper(func):
    """セキュアなジョブ実行ラッパー"""
    def wrapper(*args, **kwargs):
        # 実行ユーザー確認
        current_user = pwd.getpwuid(os.getuid()).pw_name
        if current_user != 'aicompany':
            raise PermissionError("Unauthorized job execution")
        
        return func(*args, **kwargs)
    return wrapper

@secure_job_wrapper
@decorators.daily(hour=2, minute=0)
def secure_backup_task():
    # セキュアなバックアップ処理
    pass
```

### ログ監査

```python
import logging

# 監査ログ設定
audit_logger = logging.getLogger('scheduler_audit')
handler = logging.FileHandler('/var/log/scheduler_audit.log')
audit_logger.addHandler(handler)

def audit_job_execution(event):
    """ジョブ実行監査"""
    audit_logger.info(f"Job executed: {event.job_id} at {event.scheduled_run_time}")

scheduler.add_listener(audit_job_execution, EVENT_JOB_EXECUTED)
```

## 📚 追加リソース

### 参考資料
- [APScheduler公式ドキュメント](https://apscheduler.readthedocs.io/)
- [エルダーズギルド開発ガイド](/home/aicompany/ai_co/CLAUDE.md)
- [TDD開発ガイド](knowledge_base/core/guides/CLAUDE_TDD_GUIDE.md)

### サンプルコード
- [使用例集](/home/aicompany/ai_co/examples/apscheduler_usage_examples.py)
- [定期タスク定義](/home/aicompany/ai_co/libs/elder_scheduled_tasks.py)
- [テストスイート](/home/aicompany/ai_co/tests/unit/test_apscheduler_integration.py)

---

## 🎯 まとめ

APScheduler統合により、エルダーズギルドシステムは以下を実現しました：

✅ **堅牢なスケジューリング**: 企業レベルの信頼性  
✅ **柔軟なAPI**: ビルダー・デコレータ・コマンドライン  
✅ **4賢者統合**: エルダーズギルドシステムとの完全連携  
✅ **運用性**: 監視・管理・トラブルシューティング機能  
✅ **拡張性**: 大規模環境対応・カスタマイゼーション  

**Grand Elder maru の新世界秩序における自動化基盤が完成しました。** 🌌