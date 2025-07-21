# 🚫 非推奨cronスクリプト一覧

**⚠️ 重要**: 以下のcronスクリプトは **APScheduler統合システム** に移行済みです。

## 🔄 移行済みスクリプト

### 既にAPSchedulerに統合済み
- `setup_summarize_cron.sh` → `ElderScheduledTasks.auto_summarize_task`
- `enhanced_auto_pr_cron.sh` → `ElderScheduledTasks.enhanced_pr_processor`
- `setup_unit_progress_cron.sh` → `ElderScheduledTasks.unit_progress_analyzer`
- `setup_evolution_cron.sh` → `ElderScheduledTasks.evolution_cron_task`
- `setup_knowledge_monitoring.sh` → `ElderScheduledTasks.knowledge_monitoring`
- `auto_issue_processor_cron.sh` → `ElderScheduledTasks.auto_issue_processor`
- `nwo_library_update_cron.sh` → `ElderScheduledTasks.nwo_weekly_strategy`

### 新しい統合スケジューラーの使用方法

```bash
# スケジューラー起動
./scripts/start-elder-scheduler.sh

# スケジューラー停止
./scripts/stop-elder-scheduler.sh

# スケジューラー状態確認
ps aux | grep elder_scheduled_tasks
```

## 📊 APScheduler統合システムの利点

1. **🎯 中央管理**: 全スケジュールタスクが一箇所で管理
2. **🔧 高度な制御**: 間隔、cron式、日時指定などの柔軟なスケジューリング
3. **📝 統合ログ**: 全タスクのログが統一形式で記録
4. **🛡️ エラー処理**: 4賢者システム連携による高度なエラー処理
5. **⚡ パフォーマンス**: Pythonネイティブで高速実行
6. **🔄 動的管理**: 実行時にスケジュール変更可能

## 🏛️ エルダーズギルド統合スケジュール

**現在登録されているタスク数**: 20タスク

**主要スケジュール**:
- **Auto Issue Processor**: 10分間隔
- **GitHub Health Check**: 1時間間隔
- **Knowledge Monitoring**: 6時間間隔
- **nWo Daily Council**: 毎日9:00
- **System Backup**: 毎日3:00

## ❌ 削除推奨ファイル

以下のファイルは安全に削除できます（バックアップ推奨）：

```bash
# 移行済みcronスクリプト（削除可能）
rm scripts/setup_summarize_cron.sh
rm scripts/enhanced_auto_pr_cron.sh  
rm scripts/setup_unit_progress_cron.sh
rm scripts/setup_evolution_cron.sh
rm scripts/setup_knowledge_monitoring.sh
rm scripts/auto_issue_processor_cron.sh
rm scripts/nwo_library_update_cron.sh

# 古いcron設定ファイル
rm scripts/install_cron_commands.sh
rm scripts/practical_pr_cron_setup.sh
```

---

**🚀 現在**: APScheduler統合システム（`ElderScheduledTasks`）使用  
**📅 移行日**: 2025-07-21  
**👑 責任者**: Claude Elder