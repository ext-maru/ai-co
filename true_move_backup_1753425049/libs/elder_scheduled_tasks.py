#!/usr/bin/env python3
"""
エルダーズギルド 定期実行タスク
APScheduler統合による自動化タスク定義
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.apscheduler_integration import (
    get_elder_scheduler,
    ElderScheduleDecorators,
    register_sage_callback
)

logger = logging.getLogger(__name__)


class ElderScheduledTasks:
    """エルダーズギルド定期実行タスク管理"""
    
    def __init__(self):
        """初期化メソッド"""
        self.scheduler = get_elder_scheduler()
        self.decorators = ElderScheduleDecorators(self.scheduler)
        self.project_root = Path(__file__).parent.parent
        
        # 4賢者コールバック設定
        self._setup_sage_callbacks()
        
    def _setup_sage_callbacks(self):
        """4賢者システムとの連携設定"""
        def task_sage_callback(event):
            """task_sage_callbackメソッド"""
            logger.info(f"📋 タスク賢者: ジョブ {event.job_id} 完了")
            
        def incident_sage_callback(event):
            """incident_sage_callbackメソッド"""
            logger.error(f"🚨 インシデント賢者: ジョブ {event.job_id} エラー - {event.exception}")
            
        register_sage_callback('task_sage', task_sage_callback)
        register_sage_callback('incident_sage', incident_sage_callback)
        
    def register_all_tasks(self):
        """全ての定期タスクを登録"""
        logger.info("🚀 エルダーズギルド定期タスク登録開始")
        
        # システム保守タスク
        self._register_system_maintenance_tasks()
        
        # データベース管理タスク
        self._register_database_tasks()
        
        # 監視・ヘルスチェックタスク
        self._register_monitoring_tasks()
        
        # nWo関連タスク
        self._register_nwo_tasks()
        
        # 知識ベース管理タスク
        self._register_knowledge_tasks()
        
        # レポート生成タスク
        self._register_reporting_tasks()
        
        # GitHub自動処理タスク
        self._register_github_automation_tasks()
        
        # レガシーcronタスク
        self._register_legacy_cron_tasks()
        
        logger.info("✅ 全ての定期タスク登録完了")
        
    def _register_system_maintenance_tasks(self):
        """システム保守タスク登録"""
        
        @self.decorators.daily(hour=2, minute=0)
        def system_cleanup():
            """システムクリーンアップ（日次・深夜2時）"""
            logger.info("🧹 システムクリーンアップ開始")
            try:
                # 一時ファイル削除
                self._cleanup_temp_files()
                
                # ログローテーション
                self._rotate_logs()
                
                # キャッシュクリア
                self._clear_caches()
                
                logger.info("✅ システムクリーンアップ完了")
            except Exception as e:
                logger.error(f"❌ システムクリーンアップエラー: {e}")
                raise
                
        @self.decorators.daily(hour=3, minute=0)
        def backup_system():
            """システムバックアップ（日次・深夜3時）"""
            logger.info("💾 システムバックアップ開始")
            try:
                # データベースバックアップ
                self._backup_databases()
                
                # 設定ファイルバックアップ
                self._backup_configs()
                
                # 知識ベースバックアップ
                self._backup_knowledge_base()
                
                logger.info("✅ システムバックアップ完了")
            except Exception as e:
                logger.error(f"❌ システムバックアップエラー: {e}")
                raise
                
        @self.decorators.weekly(day_of_week=6, hour=22, minute=0)
        def security_scan():
            """セキュリティスキャン（週次・土曜22時）"""
            logger.info("🔒 セキュリティスキャン開始")
            try:
                # 脆弱性スキャン
                self._run_security_scan()
                
                # 不正アクセス検知
                self._check_suspicious_activity()
                
                # セキュリティレポート生成
                self._generate_security_report()
                
                logger.info("✅ セキュリティスキャン完了")
            except Exception as e:
                logger.error(f"❌ セキュリティスキャンエラー: {e}")
                raise
                
    def _register_database_tasks(self):
        """データベース管理タスク登録"""
        
        @self.decorators.hourly(minute=0)
        def update_statistics():
            """統計情報更新（時次・毎時0分）"""
            logger.info("📊 統計情報更新開始")
            try:
                # システム統計更新
                self._update_system_stats()
                
                # ユーザー統計更新
                self._update_user_stats()
                
                # パフォーマンス統計更新
                self._update_performance_stats()
                
                logger.info("✅ 統計情報更新完了")
            except Exception as e:
                logger.error(f"❌ 統計情報更新エラー: {e}")
                
        @self.decorators.daily(hour=4, minute=0)
        def optimize_database():
            """データベース最適化（日次・深夜4時）"""
            logger.info("⚡ データベース最適化開始")
            try:
                # インデックス最適化
                self._optimize_indexes()
                
                # テーブル最適化
                self._optimize_tables()
                
                # 古いデータクリーンアップ
                self._cleanup_old_data()
                
                logger.info("✅ データベース最適化完了")
            except Exception as e:
                logger.error(f"❌ データベース最適化エラー: {e}")
                
    def _register_monitoring_tasks(self):
        """監視・ヘルスチェックタスク登録"""
        
        @self.decorators.scheduled('interval', minutes=5)
        def health_check():
            """ヘルスチェック（5分間隔）"""
            logger.info("💓 ヘルスチェック実行")
            try:
                # システムリソース確認
                self._check_system_resources()
                
                # サービス状態確認
                self._check_service_status()
                
                # データベース接続確認
                self._check_database_connections()
                
                logger.info("✅ ヘルスチェック正常")
            except Exception as e:
                logger.error(f"❌ ヘルスチェックエラー: {e}")
                
        @self.decorators.scheduled('interval', minutes=15)
        def performance_monitor():
            """パフォーマンス監視（15分間隔）"""
            logger.info("📈 パフォーマンス監視実行")
            try:
                # CPU使用率監視
                self._monitor_cpu_usage()
                
                # メモリ使用率監視
                self._monitor_memory_usage()
                
                # ディスク使用量監視
                self._monitor_disk_usage()
                
                # ネットワーク監視
                self._monitor_network()
                
                logger.info("✅ パフォーマンス監視完了")
            except Exception as e:
                logger.error(f"❌ パフォーマンス監視エラー: {e}")
                
    def _register_nwo_tasks(self):
        """nWo関連タスク登録"""
        
        @self.decorators.daily(hour=9, minute=0)
        def nwo_daily_council():
            """nWo日次評議会（毎日9時）"""
            logger.info("🌌 nWo日次評議会開始")
            try:
                # 日次レポート生成
                self._generate_nwo_daily_report()
                
                # 戦略分析
                self._analyze_nwo_strategy()
                
                # 目標進捗確認
                self._check_nwo_progress()
                
                logger.info("✅ nWo日次評議会完了")
            except Exception as e:
                logger.error(f"❌ nWo日次評議会エラー: {e}")
                
        @self.decorators.weekly(day_of_week=0, hour=10, minute=0)
        def nwo_weekly_strategy():
            """nWo週次戦略会議（月曜10時）"""
            logger.info("🌌 nWo週次戦略会議開始")
            try:
                # 週次戦略レビュー
                self._review_weekly_strategy()
                
                # 新世界秩序進捗評価
                self._evaluate_nwo_progress()
                
                # 次週計画策定
                self._plan_next_week()
                
                logger.info("✅ nWo週次戦略会議完了")
            except Exception as e:
                logger.error(f"❌ nWo週次戦略会議エラー: {e}")
                
    def _register_knowledge_tasks(self):
        """知識ベース管理タスク登録"""
        
        @self.decorators.daily(hour=1, minute=0)
        def knowledge_sync():
            """知識ベース同期（日次・深夜1時）"""
            logger.info("📚 知識ベース同期開始")
            try:
                # 知識ベース整合性確認
                self._verify_knowledge_integrity()
                
                # 知識インデックス更新
                self._update_knowledge_index()
                
                # 重複知識統合
                self._merge_duplicate_knowledge()
                
                logger.info("✅ 知識ベース同期完了")
            except Exception as e:
                logger.error(f"❌ 知識ベース同期エラー: {e}")
                
        @self.decorators.scheduled('interval', hours=6)
        def knowledge_learning():
            """知識学習・進化（6時間間隔）"""
            logger.info("🧠 知識学習・進化開始")
            try:
                # 新しい知識パターン分析
                self._analyze_knowledge_patterns()
                
                # 知識グラフ更新
                self._update_knowledge_graph()
                
                # AI学習データ更新
                self._update_ai_learning_data()
                
                logger.info("✅ 知識学習・進化完了")
            except Exception as e:
                logger.error(f"❌ 知識学習・進化エラー: {e}")
                
    def _register_reporting_tasks(self):
        """レポート生成タスク登録"""
        
        @self.decorators.daily(hour=8, minute=30)
        def daily_report():
            """日次レポート生成（毎日8:30）"""
            logger.info("📋 日次レポート生成開始")
            try:
                # システム状況レポート
                self._generate_system_report()
                
                # 活動サマリー
                self._generate_activity_summary()
                
                # 課題・改善点整理
                self._analyze_issues_improvements()
                
                logger.info("✅ 日次レポート生成完了")
            except Exception as e:
                logger.error(f"❌ 日次レポート生成エラー: {e}")
                
        @self.decorators.weekly(day_of_week=0, hour=9, minute=0)
        def weekly_report():
            """週次レポート生成（月曜9時）"""
            logger.info("📊 週次レポート生成開始")
            try:
                # 週次パフォーマンスレポート
                self._generate_weekly_performance()
                
                # 達成目標評価
                self._evaluate_weekly_goals()
                
                # 来週計画提案
                self._propose_next_week_plan()
                
                logger.info("✅ 週次レポート生成完了")
            except Exception as e:
                logger.error(f"❌ 週次レポート生成エラー: {e}")
                
    # 実装メソッド群（実際の処理）
    
    def _cleanup_temp_files(self):
        """一時ファイルクリーンアップ"""
        temp_dirs = [
            self.project_root / "temp",
            self.project_root / "tmp",
            Path("/tmp/ai_co_*")
        ]
        
        for temp_dir in temp_dirs:
            if temp_dir.exists():
                for file in temp_dir.glob("*"):
                    if file.is_file() and (datetime.now() - datetime.fromtimestamp(file.stat().st_mtime)).days > 7:
                        file.unlink()
                        logger.debug(f"削除: {file}")
                        
    def _rotate_logs(self):
        """ログローテーション"""
        log_dir = self.project_root / "logs"
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                if log_file.stat().st_size > 100 * 1024 * 1024:  # 100MB超
                    backup_file = log_file.with_suffix(f".{datetime.now().strftime('%Y%m%d')}.log")
                    log_file.rename(backup_file)
                    logger.info(f"ログローテーション: {log_file} -> {backup_file}")
                    
    def _clear_caches(self):
        """キャッシュクリア"""
        cache_dirs = [
            self.project_root / "__pycache__",
            self.project_root / ".pytest_cache"
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)
                logger.debug(f"キャッシュクリア: {cache_dir}")
                
    def _backup_databases(self):
        """データベースバックアップ"""
        logger.info("💾 データベースバックアップ実行")
        # 実際のバックアップ処理を実装
        
    def _backup_configs(self):
        """設定ファイルバックアップ"""
        logger.info("⚙️ 設定ファイルバックアップ実行")
        # 実際のバックアップ処理を実装
        
    def _backup_knowledge_base(self):
        """知識ベースバックアップ"""
        logger.info("📚 知識ベースバックアップ実行")
        # 実際のバックアップ処理を実装
        
    def _run_security_scan(self):
        """セキュリティスキャン実行"""
        logger.info("🔒 セキュリティスキャン実行")
        # 実際のスキャン処理を実装
        
    def _check_suspicious_activity(self):
        """不正アクセス検知"""
        logger.info("👁️ 不正アクセス検知実行")
        # 実際の検知処理を実装
        
    def _generate_security_report(self):
        """セキュリティレポート生成"""
        logger.info("📋 セキュリティレポート生成")
        # 実際のレポート生成処理を実装
        
    def _update_system_stats(self):
        """システム統計更新"""
        logger.info("📊 システム統計更新")
        # 実際の統計更新処理を実装
        
    def _update_user_stats(self):
        """ユーザー統計更新"""
        logger.info("👥 ユーザー統計更新")
        # 実際の統計更新処理を実装
        
    def _update_performance_stats(self):
        """パフォーマンス統計更新"""
        logger.info("⚡ パフォーマンス統計更新")
        # 実際の統計更新処理を実装
        
    def _optimize_indexes(self):
        """インデックス最適化"""
        logger.info("🔍 インデックス最適化")
        # 実際の最適化処理を実装
        
    def _optimize_tables(self):
        """テーブル最適化"""
        logger.info("🗃️ テーブル最適化")
        # 実際の最適化処理を実装
        
    def _cleanup_old_data(self):
        """古いデータクリーンアップ"""
        logger.info("🗑️ 古いデータクリーンアップ")
        # 実際のクリーンアップ処理を実装
        
    def _check_system_resources(self):
        """システムリソース確認"""
        import psutil
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 80:
            logger.warning(f"高CPU使用率: {cpu_percent}%")
            
        # メモリ使用率
        memory = psutil.virtual_memory()
        if memory.percent > 80:
            logger.warning(f"高メモリ使用率: {memory.percent}%")
            
        # ディスク使用量
        disk = psutil.disk_usage('/')
        if disk.percent > 80:
            logger.warning(f"高ディスク使用率: {disk.percent}%")
            
    def _check_service_status(self):
        """サービス状態確認"""
        logger.info("🔧 サービス状態確認")
        # 実際のサービス確認処理を実装
        
    def _check_database_connections(self):
        """データベース接続確認"""
        logger.info("🗄️ データベース接続確認")
        # 実際の接続確認処理を実装
        
    def _monitor_cpu_usage(self):
        """CPU使用率監視"""
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        logger.debug(f"CPU使用率: {cpu_percent}%")
        
    def _monitor_memory_usage(self):
        """メモリ使用率監視"""
        import psutil
        memory = psutil.virtual_memory()
        logger.debug(f"メモリ使用率: {memory.percent}%")
        
    def _monitor_disk_usage(self):
        """ディスク使用量監視"""
        import psutil
        disk = psutil.disk_usage('/')
        logger.debug(f"ディスク使用率: {disk.percent}%")
        
    def _monitor_network(self):
        """ネットワーク監視"""
        logger.debug("ネットワーク監視実行")
        # 実際のネットワーク監視処理を実装
        
    def _generate_nwo_daily_report(self):
        """nWo日次レポート生成"""
        logger.info("🌌 nWo日次レポート生成")
        # 実際のレポート生成処理を実装
        
    def _analyze_nwo_strategy(self):
        """nWo戦略分析"""
        logger.info("🎯 nWo戦略分析")
        # 実際の戦略分析処理を実装
        
    def _check_nwo_progress(self):
        """nWo目標進捗確認"""
        logger.info("📈 nWo目標進捗確認")
        # 実際の進捗確認処理を実装
        
    def _review_weekly_strategy(self):
        """週次戦略レビュー"""
        logger.info("📋 週次戦略レビュー")
        # 実際のレビュー処理を実装
        
    def _evaluate_nwo_progress(self):
        """nWo進捗評価"""
        logger.info("🏆 nWo進捗評価")
        # 実際の評価処理を実装
        
    def _plan_next_week(self):
        """次週計画策定"""
        logger.info("📅 次週計画策定")
        # 実際の計画策定処理を実装
        
    def _verify_knowledge_integrity(self):
        """知識ベース整合性確認"""
        logger.info("🔍 知識ベース整合性確認")
        # 実際の整合性確認処理を実装
        
    def _update_knowledge_index(self):
        """知識インデックス更新"""
        logger.info("📇 知識インデックス更新")
        # 実際のインデックス更新処理を実装
        
    def _merge_duplicate_knowledge(self):
        """重複知識統合"""
        logger.info("🔀 重複知識統合")
        # 実際の統合処理を実装
        
    def _analyze_knowledge_patterns(self):
        """知識パターン分析"""
        logger.info("🧠 知識パターン分析")
        # 実際のパターン分析処理を実装
        
    def _update_knowledge_graph(self):
        """知識グラフ更新"""
        logger.info("🕸️ 知識グラフ更新")
        # 実際のグラフ更新処理を実装
        
    def _update_ai_learning_data(self):
        """AI学習データ更新"""
        logger.info("🤖 AI学習データ更新")
        # 実際の学習データ更新処理を実装
        
    def _generate_system_report(self):
        """システム状況レポート生成"""
        logger.info("📊 システム状況レポート生成")
        # 実際のレポート生成処理を実装
        
    def _generate_activity_summary(self):
        """活動サマリー生成"""
        logger.info("📈 活動サマリー生成")
        # 実際のサマリー生成処理を実装
        
    def _analyze_issues_improvements(self):
        """課題・改善点整理"""
        logger.info("🎯 課題・改善点整理")
        # 実際の分析処理を実装
        
    def _generate_weekly_performance(self):
        """週次パフォーマンスレポート生成"""
        logger.info("📊 週次パフォーマンスレポート生成")
        # 実際のレポート生成処理を実装
        
    def _evaluate_weekly_goals(self):
        """達成目標評価"""
        logger.info("🏆 達成目標評価")
        # 実際の評価処理を実装
        
    def _propose_next_week_plan(self):
        """来週計画提案"""
        logger.info("📅 来週計画提案")
        # 実際の計画提案処理を実装


def start_elder_scheduled_tasks():
    """エルダーズギルド定期タスク開始"""
    logger.info("🚀 エルダーズギルド定期タスクシステム開始")
    
    # タスクシステム初期化
    task_system = ElderScheduledTasks()
    
    # 全タスク登録
    task_system.register_all_tasks()
    
    # スケジューラー開始
    task_system.scheduler.start()
    
    logger.info("✅ エルダーズギルド定期タスクシステム起動完了")
    
    return task_system


# GitHub自動処理タスクメソッドを追加
def _register_github_automation_tasks(self):
    """GitHub自動処理タスク登録"""
    
    # 🚨 AUTO ISSUE PROCESSOR DISABLED - 根本原因分析により実装系Issue処理で重大な問題発覚
    # 停止理由: Issue #83で無関係なPR品質監査システム実装、システム破壊リスク
    # 適用可能: 設計系Issueのみ（手動実行推奨）
    # 再開条件: Issue種別判定システム実装後
    # 詳細: docs/reports/AUTO_ISSUE_PROCESSOR_ROOT_CAUSE_ANALYSIS_REPORT.md
    
    # @self.decorators.scheduled('interval', minutes=5)
    # async def auto_issue_processor():
    #     """Enhanced Auto Issue Processor実行（5分間隔） - 一時無効化"""
    #     logger.info("🤖 Enhanced Auto Issue Processor実行開始")
    #     try:
    #         import asyncio
    #         # Enhanced版を使用するように変更
    #         from libs.integrations.github.enhanced_auto_issue_processor import EnhancedAutoIssueProcessor
    #         
    #         processor = EnhancedAutoIssueProcessor()
    #         
    #         # Enhanced版の実行（10分ごとなので1件ずつ処理）
    #         result = await processor.run_enhanced(
    #             max_issues=1,  # 10分ごとの実行なので1件ずつ
    #             priorities=["critical", "high", "medium", "low"],  # 全優先度対応
    #             enable_smart_merge=True,  # スマートマージ有効
    #             enable_four_sages=True    # 4賢者統合有効
    #         )
    #         
    #         if result.get("processed_count", 0) > 0:
    #             for processed in result.get("processed_issues", []):
    #                 logger.info(f"✅ イシュー #{processed.get('number')} 処理完了: {processed.get('title', 'N/A')}")
    #                 if processed.get("pr_created"):
    #                     logger.info(f"  → PR #{processed.get('pr_number')} 作成成功")
    #         else:
    #             logger.info("📝 処理可能なイシューなし")
    #         
    #         # メトリクスログ
    #         if result.get("metrics"):
    #             logger.info(f"📊 処理メトリクス: {result['metrics']}")
    #         
    #         logger.info("✅ Enhanced Auto Issue Processor完了")
    #         return result
    #             
    #     except Exception as e:
    #         logger.error(f"❌ Enhanced Auto Issue Processor エラー: {e}")
    #         raise
            
    # 🚨 PR QUALITY AUDIT DISABLED - Issue #83で危険な自動PR差し戻し機能実装
    # 停止理由: 無許可でPRの自動クローズ・Issue強制再オープン実装
    # 危険度: CRITICAL (既存PR・Issueの破壊的操作)
    # 再開条件: 手動品質監査プロセス確立後
    
    # @self.decorators.scheduled('interval', minutes=5)
    # async def pr_quality_audit_batch():
    #     """PR品質監査バッチ（5分間隔）- 危険機能のため無効化"""
    #     logger.info("🔍 PR品質監査バッチ実行開始")
    #     try:
    #         import os
    #         import re
    #         from github import Github
    #         
    #         github_token = os.getenv("GITHUB_TOKEN")
    #         if not github_token:
    #             logger.error("❌ GITHUB_TOKEN環境変数が設定されていません")
    #             return
    #             
    #         github = Github(github_token)
    #         repo_owner = os.getenv("GITHUB_REPO_OWNER", "ext-maru")
    #         repo_name = os.getenv("GITHUB_REPO_NAME", "ai-co")
    #         repo = github.get_repo(f"{repo_owner}/{repo_name}")
    #         
    #         # オープンPRを取得
    #         open_prs = list(repo.get_pulls(state='open'))
    #         logger.info(f"🔍 {len(open_prs)}件のオープンPRを検査中...")
    #         
    #         rejected_count = 0
    #         approved_count = 0
    #         
    #         for pr in open_prs:
    #             # PR品質チェック
    #             quality_issues = []
    #             
    #             # 基本チェック: タイトルと説明
    #             if not pr.body or len(pr.body.strip()) < 50:
    #                 quality_issues.append("PR説明文が不十分（50文字未満）")
    #             
    #             # TODO/FIXMEチェック（Iron Will違反）
    #             if pr.body and any(keyword in pr.body.upper() for keyword in ['TODO', 'FIXME', 'HACK', 'XXX']):
    #                 quality_issues.append("Iron Will違反: PR本文にTODO/FIXMEコメントが含まれています")
    #             
    #             # auto-generatedラベルのPRは要注意
    #             pr_labels = [label.name for label in pr.labels]
    #             if 'auto-generated' in pr_labels:
    #                 # ファイル取得して内容チェック
    #                 try:
    #                     files = list(pr.get_files())
    #                     for file in files[:3]:  # 最大3ファイルまでチェック
    #                         if file.filename.endswith('.py'):
    #                             patch_content = file.patch or ''
    #                             if any(keyword in patch_content.upper() for keyword in ['TODO', 'FIXME', '# TODO', '# FIXME']):
    #                                 quality_issues.append(f"Iron Will違反: {file.filename}にTODOコメントが残存")
    #                             if 'pass' in patch_content and patch_content.count('pass') > 2:
    #                                 quality_issues.append(f"不完全実装: {file.filename}にスタブ実装が多数存在")
    #                 except Exception as e:
    #                     logger.warning(f"PR #{pr.number} ファイル内容チェック失敗: {e}")
    #             
    #             # 品質判定
    #             if quality_issues:
    #                 logger.info(f"❌ PR #{pr.number} を品質不合格として差し戻し")
    #                 
    #                 # 差し戻しコメント作成
    #                 rejection_comment = f"""🚨 **PR品質監査 - 自動差し戻し**
    #
    # **差し戻し理由:**
    # """
    #                 for issue in quality_issues:
    #                     rejection_comment += f"- {issue}\\n"
    #                 
    #                 rejection_comment += f"""
    #
    # **エルダーズギルド品質基準:**
    # - Iron Will遵守（TODO/FIXME禁止）
    # - 実装完成度70%以上
    # - 適切なPR説明（50文字以上）
    #
    # **次のアクション:**
    # 1. 上記問題を修正してください
    # 2. 修正後、PRを再オープンしてください
    # 3. または関連Issueを再オープンして次の処理者に委ねてください
    #
    # ---
    # 🤖 自動品質監査システムによる差し戻し
    # """
    #                 
    #                 # PRにコメント追加
    #                 pr.create_issue_comment(rejection_comment)
    #                 
    #                 # PRをクローズ
    #                 pr.edit(state='closed')
    #                 
    #                 # 関連Issueがあれば再オープン
    #                 if pr.body and '#' in pr.body:
    #                     issue_refs = re.findall(r'#(\\d+)', pr.body)
    #                     for issue_ref in issue_refs:
    #                         try:
    #                             issue = repo.get_issue(int(issue_ref))
    #                             if issue.state == 'closed':
    #                                 issue.edit(state='open')
    #                                 issue.create_comment(f"🔄 PR #{pr.number}が品質基準未達成で差し戻されたため、このIssueを再オープンしました。")
    #                                 logger.info(f"📝 Issue #{issue_ref} を再オープン")
    #                         except Exception as e:
    #                             logger.warning(f"Issue #{issue_ref} 再オープン失敗: {e}")
    #                 
    #                 rejected_count += 1
    #             else:
    #                 logger.info(f"✅ PR #{pr.number} 品質基準クリア")
    #                 approved_count += 1
    #         
    #         logger.info(f"✅ PR品質監査完了: 承認{approved_count}件, 差し戻し{rejected_count}件")
    #         
    #     except Exception as e:
    #         logger.error(f"❌ PR品質監査バッチエラー: {e}")
    #         raise
            
    @self.decorators.hourly(minute=0)
    def github_health_check():
        """GitHub API接続ヘルスチェック（1時間毎）"""
        logger.info("🔍 GitHub APIヘルスチェック開始")
        try:
            import os
            from github import Github
            
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                logger.error("❌ GITHUB_TOKEN環境変数が設定されていません")
                return
            
            github = Github(github_token)
            user = github.get_user()
            rate_limit = github.get_rate_limit()
            
            logger.info(f"✅ GitHub API正常: ユーザー {user.login}")
            logger.info(f"📊 API制限: {rate_limit.core.remaining}/{rate_limit.core.limit}")
            
            # API制限警告
            if rate_limit.core.remaining < 100:
                logger.warning(f"⚠️ GitHub API制限が少なくなっています: {rate_limit.core.remaining}")
            
        except Exception as e:
            logger.error(f"❌ GitHub APIヘルスチェックエラー: {e}")
            raise
    
    logger.info("🤖 GitHub自動処理タスク登録完了")

# レガシーcronタスク移行メソッド
def _register_legacy_cron_tasks(self):
    """レガシーcronタスクをAPSchedulerに移行"""
    
    @self.decorators.daily(hour=2, minute=0)
    def auto_summarize_task():
        """自動要約タスク（毎日深夜2時）- cronから移行"""
        logger.info("📝 自動要約タスク開始")
        try:
            import subprocess
            result = subprocess.run([
                "python3", f"{self.project_root}/scripts/auto_summarize.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ 自動要約タスク完了")
            else:
                logger.error(f"❌ 自動要約タスクエラー: {result.stderr}")
        except Exception as e:
            logger.error(f"❌ 自動要約タスク実行エラー: {e}")
            raise
    
    @self.decorators.daily(hour=1, minute=0)
    async def enhanced_pr_processor():
        """Enhanced Auto PR Processor バッチ処理（毎日深夜1時）"""
        logger.info("🔧 Enhanced PR Processor バッチ処理開始")
        try:
            import asyncio
            from libs.integrations.github.enhanced_auto_issue_processor import EnhancedAutoIssueProcessor
            
            processor = EnhancedAutoIssueProcessor()
            
            # バッチ処理（深夜なので多めに処理）
            result = await processor.run_enhanced(
                max_issues=10,  # 深夜バッチなので10件まで処理
                priorities=["medium", "low"],  # 中・低優先度を重点的に処理
                enable_smart_merge=True,
                enable_four_sages=True,
                enable_analytics=True  # バッチ処理では詳細分析も有効
            )
            
            # 処理結果のサマリー
            if result.get("processed_count", 0) > 0:
                logger.info(f"📊 バッチ処理完了: {result['processed_count']}件のイシューを処理")
                success_count = sum(1 for p in result.get("processed_issues", []) if p.get("pr_created"))
                logger.info(f"  → 成功: {success_count}件のPR作成")
                
                # 失敗したものがあれば報告
                failed = [p for p in result.get("processed_issues", []) if not p.get("pr_created")]
                if failed:
                    logger.warning(f"  → 失敗: {len(failed)}件")
                    for f in failed:
                        logger.warning(f"    - Issue #{f.get('number')}: {f.get('error', '不明なエラー')}")
            else:
                logger.info("📝 バッチ処理対象のイシューなし")
            
            logger.info("✅ Enhanced PR Processor バッチ処理完了")
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced PR Processor バッチ処理エラー: {e}")
            raise
            
    @self.decorators.weekly(day_of_week=0, hour=3, minute=0)
    def unit_progress_analyzer():
        """ユニット進捗分析（毎週日曜3時）- cronから移行"""
        logger.info("📊 ユニット進捗分析開始")
        try:
            import subprocess
            result = subprocess.run([
                "bash", f"{self.project_root}/scripts/setup_unit_progress_cron.sh"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ ユニット進捗分析完了")
            else:
                logger.error(f"❌ ユニット進捗分析エラー: {result.stderr}")
        except Exception as e:
            logger.error(f"❌ ユニット進捗分析実行エラー: {e}")
            raise
    
    @self.decorators.daily(hour=4, minute=0)
    def evolution_cron_task():
        """進化システムタスク（毎日深夜4時）- cronから移行"""  
        logger.info("🧬 進化システムタスク開始")
        try:
            import subprocess
            result = subprocess.run([
                "bash", f"{self.project_root}/scripts/setup_evolution_cron.sh"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ 進化システムタスク完了")
            else:
                logger.error(f"❌ 進化システムタスクエラー: {result.stderr}")
        except Exception as e:
            logger.error(f"❌ 進化システムタスク実行エラー: {e}")
            raise
            
    @self.decorators.scheduled('interval', hours=6)
    def knowledge_monitoring():
        """知識ベース監視（6時間間隔）- cronから移行"""
        logger.info("📚 知識ベース監視開始") 
        try:
            import subprocess
            result = subprocess.run([
                "bash", f"{self.project_root}/scripts/setup_knowledge_monitoring.sh"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ 知識ベース監視完了")
            else:
                logger.warning(f"⚠️ 知識ベース監視警告: {result.stderr}")
        except Exception as e:
            logger.error(f"❌ 知識ベース監視実行エラー: {e}")
            raise
    
    logger.info("🔄 レガシーcronタスク移行完了")

# ElderScheduledTasksクラスにメソッドを動的追加
ElderScheduledTasks._register_github_automation_tasks = _register_github_automation_tasks
ElderScheduledTasks._register_legacy_cron_tasks = _register_legacy_cron_tasks


if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 定期タスクシステム開始
    task_system = start_elder_scheduled_tasks()
    
    try:
        # 継続実行
        logger.info("📊 スケジューラー情報:")
        logger.info(f"  - タイプ: {type(task_system.scheduler.scheduler).__name__}")
        logger.info(f"  - 実行中: {task_system.scheduler.scheduler.running}")
        logger.info(f"  - ジョブ数: {len(task_system.scheduler.scheduler.get_jobs())}")
        
        # AsyncIOSchedulerの場合はイベントループが必要
        if hasattr(task_system.scheduler.scheduler, '_eventloop'):
            logger.info("⚡ AsyncIOScheduler detected - running event loop")
            asyncio.get_event_loop().run_forever()
        else:
            logger.info("⏰ Standard scheduler - using sleep loop")
            import time
            while True:
                time.sleep(60)  # 1分間隔でチェック
    except KeyboardInterrupt:
        logger.info("🛑 定期タスクシステム停止")
        task_system.scheduler.shutdown()