#!/usr/bin/env python3
"""
APScheduler統合システム使用例
エルダーズギルド APScheduler活用ガイド
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.apscheduler_integration import (
    ElderScheduler,
    ElderScheduleBuilder,
    ElderScheduleDecorators,
    get_elder_scheduler,
    schedule_with_elder,
    start_elder_scheduler,
    stop_elder_scheduler,
    register_sage_callback
)


def example_basic_usage():
    """基本的な使用例"""
    print("🚀 APScheduler基本使用例")
    
    # スケジューラー取得・開始
    scheduler = get_elder_scheduler()
    scheduler.start()
    
    # 1. 間隔実行ジョブ
    def interval_job():
        print(f"⏰ 間隔ジョブ実行: {datetime.now()}")
    
    scheduler.add_job(
        func=interval_job,
        trigger='interval',
        seconds=30,
        id='interval_example',
        name='30秒間隔ジョブ'
    )
    
    # 2. Cronジョブ（毎日9時）
    def daily_job():
        print(f"🌅 日次ジョブ実行: {datetime.now()}")
    
    scheduler.add_job(
        func=daily_job,
        trigger='cron',
        hour=9,
        minute=0,
        id='daily_example',
        name='日次レポート生成'
    )
    
    # 3. 一回限りジョブ
    def one_time_job():
        print(f"🎯 一回限りジョブ実行: {datetime.now()}")
    
    scheduler.add_job(
        func=one_time_job,
        trigger='date',
        run_date=datetime.now() + timedelta(minutes=5),
        id='onetime_example',
        name='5分後実行'
    )
    
    print("📋 ジョブが登録されました")
    print("停止するには stop_elder_scheduler() を呼び出してください")


def example_builder_pattern():
    """ビルダーパターン使用例"""
    print("🏗️ ビルダーパターン使用例")
    
    scheduler = get_elder_scheduler()
    scheduler.start()
    
    builder = ElderScheduleBuilder(scheduler)
    
    # 1. 毎分実行
    def every_minute_job():
        print(f"📅 毎分ジョブ: {datetime.now()}")
    
    builder.every(1).minutes().do(every_minute_job)
    
    # 2. 5秒間隔
    def every_5_seconds_job():
        print(f"⚡ 5秒間隔ジョブ: {datetime.now()}")
    
    builder.every(5).seconds().do(every_5_seconds_job)
    
    # 3. 2時間間隔
    def every_2_hours_job():
        print(f"🕐 2時間間隔ジョブ: {datetime.now()}")
    
    builder.every(2).hours().do(every_2_hours_job)
    
    print("✅ ビルダーパターンでジョブ登録完了")


def example_decorators():
    """デコレータ使用例"""
    print("🎭 デコレータ使用例")
    
    scheduler = get_elder_scheduler()
    decorators = ElderScheduleDecorators(scheduler)
    
    # 1. 日次実行デコレータ
    @decorators.daily(hour=8, minute=30)
    def morning_report():
        print(f"🌅 朝次レポート: {datetime.now()}")
        return "Morning report generated"
    
    # 2. 時次実行デコレータ
    @decorators.hourly(minute=0)
    def hourly_cleanup():
        print(f"🧹 時次クリーンアップ: {datetime.now()}")
        return "Cleanup completed"
    
    # 3. 週次実行デコレータ（月曜日10時）
    @decorators.weekly(day_of_week=0, hour=10, minute=0)
    def weekly_summary():
        print(f"📊 週次サマリー: {datetime.now()}")
        return "Weekly summary generated"
    
    # 4. カスタムスケジュールデコレータ
    @decorators.scheduled('interval', minutes=10)
    def custom_monitor():
        print(f"👁️ カスタム監視: {datetime.now()}")
        return "Monitoring check completed"
    
    scheduler.start()
    print("🎯 デコレータベースのジョブ登録完了")


def example_global_decorator():
    """グローバルデコレータ使用例"""
    print("🌍 グローバルデコレータ使用例")
    
    # グローバルデコレータ使用
    @schedule_with_elder('interval', seconds=15)
    def global_scheduled_job():
        print(f"🌐 グローバルスケジュールジョブ: {datetime.now()}")
        return "Global job executed"
    
    # スケジューラー開始
    start_elder_scheduler()
    print("🚀 グローバルスケジューラー開始")


def example_4sages_integration():
    """4賢者システム統合例"""
    print("🧙‍♂️ 4賢者システム統合例")
    
    # 4賢者コールバック定義
    def task_sage_callback(event):
        print(f"📋 タスク賢者: ジョブ {event.job_id} が完了しました")
        # タスク完了をデータベースに記録など
    
    def incident_sage_callback(event):
        print(f"🚨 インシデント賢者: ジョブ {event.job_id} でエラー発生!")
        print(f"   エラー内容: {event.exception}")
        # インシデント報告・自動復旧処理など
    
    def knowledge_sage_callback(event):
        print(f"📚 ナレッジ賢者: ジョブ実行パターンを学習中...")
        # 実行パターンを知識ベースに蓄積
    
    def rag_sage_callback(event):
        print(f"🔍 RAG賢者: 最適化候補を検索中...")
        # 類似ジョブから最適化提案を生成
    
    # コールバック登録
    register_sage_callback('task_sage', task_sage_callback)
    register_sage_callback('incident_sage', incident_sage_callback)
    register_sage_callback('knowledge_sage', knowledge_sage_callback)
    register_sage_callback('rag_sage', rag_sage_callback)
    
    scheduler = get_elder_scheduler()
    scheduler.start()
    
    # 成功ジョブ
    def success_job():
        print("✅ 成功ジョブ実行")
        return "Success"
    
    # エラージョブ
    def error_job():
        print("❌ エラージョブ実行")
        raise ValueError("意図的なエラー")
    
    # ジョブ登録
    scheduler.add_job(func=success_job, trigger='interval', seconds=20, id='success_job')
    scheduler.add_job(func=error_job, trigger='interval', seconds=25, id='error_job')
    
    print("🧙‍♂️ 4賢者統合システム起動完了")


def example_database_tasks():
    """データベースタスク例"""
    print("🗄️ データベースタスク例")
    
    scheduler = get_elder_scheduler()
    scheduler.start()
    
    # 1. データベースクリーンアップ（日次）
    def db_cleanup():
        print(f"🧹 データベースクリーンアップ開始: {datetime.now()}")
        # 古いログエントリ削除
        # 一時ファイル削除
        # インデックス最適化
        print("✅ データベースクリーンアップ完了")
    
        """db_cleanupメソッド"""
    scheduler.add_job(
        func=db_cleanup,
        trigger='cron',
        hour=2,  # 深夜2時実行
        minute=0,
        id='db_cleanup',
        name='データベースクリーンアップ'
    )
    
    # 2. バックアップ（日次）
    def db_backup():
        print(f"💾 データベースバックアップ開始: {datetime.now()}")
        # PostgreSQLダンプ作成
        # ファイル圧縮
        # クラウドストレージアップロード
        print("✅ データベースバックアップ完了")
        """db_backupメソッド"""
    
    scheduler.add_job(
        func=db_backup,
        trigger='cron',
        hour=3,  # 深夜3時実行
        minute=0,
        id='db_backup',
        name='データベースバックアップ'
    )
    
    # 3. 統計情報更新（時次）
    def update_stats():
        print(f"📊 統計情報更新: {datetime.now()}")
        # ユーザー統計計算
        # システム利用統計
        # パフォーマンスメトリクス
        """update_statsを更新"""
        print("✅ 統計情報更新完了")
    
    scheduler.add_job(
        func=update_stats,
        trigger='cron',
        minute=0,  # 毎時0分実行
        id='update_stats',
        name='統計情報更新'
    )
    
    print("📈 データベースタスク登録完了")


def example_monitoring_tasks():
    """監視タスク例"""
    print("👁️ 監視タスク例")
    
    scheduler = get_elder_scheduler()
    scheduler.start()
    
    # 1. ヘルスチェック（5分間隔）
    def health_check():
        print(f"💓 ヘルスチェック: {datetime.now()}")
        # API エンドポイント確認
        # データベース接続確認
        """health_checkメソッド"""
        # Redis接続確認
        # ディスク容量確認
        print("✅ システム正常")
    
    scheduler.add_job(
        func=health_check,
        trigger='interval',
        minutes=5,
        id='health_check',
        name='システムヘルスチェック'
    )
    
    # 2. ログローテーション（日次）
    def log_rotation():
        print(f"📋 ログローテーション: {datetime.now()}")
        # 古いログファイル圧縮
        """log_rotationメソッド"""
        # ログファイルアーカイブ
        # ディスク容量確保
        print("✅ ログローテーション完了")
    
    scheduler.add_job(
        func=log_rotation,
        trigger='cron',
        hour=1,  # 深夜1時実行
        minute=0,
        id='log_rotation',
        name='ログローテーション'
    )
    
    # 3. セキュリティスキャン（週次）
    def security_scan():
        print(f"🔒 セキュリティスキャン: {datetime.now()}")
        """security_scanメソッド"""
        # 脆弱性スキャン
        # 不正アクセス検知
        # セキュリティレポート生成
        print("✅ セキュリティスキャン完了")
    
    scheduler.add_job(
        func=security_scan,
        trigger='cron',
        day_of_week=6,  # 土曜日実行
        hour=22,
        minute=0,
        id='security_scan',
        name='セキュリティスキャン'
    )
    
    print("🛡️ 監視タスク登録完了")


def example_async_jobs():
    """非同期ジョブ例"""
    print("⚡ 非同期ジョブ例")
    
    scheduler = ElderScheduler('asyncio')  # 非同期スケジューラー
    scheduler.start()
    
    # 非同期ジョブ
    async def async_data_processing():
        """async_data_processingを処理"""
        print(f"⚡ 非同期データ処理開始: {datetime.now()}")
        # 非同期でデータ処理
        await asyncio.sleep(2)  # 重い処理のシミュレーション
        print(f"✅ 非同期データ処理完了: {datetime.now()}")
    
    scheduler.add_job(
        func=async_data_processing,
        trigger='interval',
        minutes=10,
        id='async_processing',
        name='非同期データ処理',
        executor='asyncio'  # 非同期エグゼキューター指定
    )
    
    print("⚡ 非同期ジョブ登録完了")


def example_job_management():
    """ジョブ管理例"""
    print("🎛️ ジョブ管理例")
    
    scheduler = get_elder_scheduler()
    scheduler.start()
    
    # テストジョブ
    def test_job():
        print(f"🧪 テストジョブ: {datetime.now()}")
    
    # ジョブ追加
    job = scheduler.add_job(
        func=test_job,
        trigger='interval',
        seconds=10,
        id='management_test',
        name='管理テストジョブ'
    )
    
    print(f"✅ ジョブ追加: {job.id}")
    
    # ジョブ一覧取得
    jobs = scheduler.get_jobs()
    print(f"📋 現在のジョブ数: {len(jobs)}")
    
    # ジョブ一時停止
    scheduler.pause_job('management_test')
    print("⏸️ ジョブ一時停止")
    
    # ジョブ再開
    scheduler.resume_job('management_test')
    print("▶️ ジョブ再開")
    
    # ジョブ変更
    modified_job = scheduler.modify_job(
        'management_test',
        name='変更されたテストジョブ'
    )
    print(f"✏️ ジョブ変更: {modified_job.name}")
    
    # ジョブ削除
    scheduler.remove_job('management_test')
    print("🗑️ ジョブ削除")


def main():
    """メイン実行関数"""
    print("🚀 APScheduler統合システム使用例")
    print("=" * 50)
    
    try:
        # 各使用例を実行
        example_basic_usage()
        print("\n" + "=" * 50)
        
        example_builder_pattern()
        print("\n" + "=" * 50)
        
        example_decorators()
        print("\n" + "=" * 50)
        
        example_global_decorator()
        print("\n" + "=" * 50)
        
        example_4sages_integration()
        print("\n" + "=" * 50)
        
        example_database_tasks()
        print("\n" + "=" * 50)
        
        example_monitoring_tasks()
        print("\n" + "=" * 50)
        
        example_job_management()
        print("\n" + "=" * 50)
        
        print("🎯 すべての使用例完了")
        print("📊 現在の統計:")
        
        from libs.apscheduler_integration import get_scheduler_stats
        stats = get_scheduler_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    except KeyboardInterrupt:
        print("\n🛑 使用例中断")
    finally:
        # クリーンアップ
        stop_elder_scheduler()
        print("🧹 スケジューラー停止・クリーンアップ完了")


if __name__ == "__main__":
    main()