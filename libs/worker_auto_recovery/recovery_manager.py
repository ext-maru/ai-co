"""
Worker Recovery Manager

ワーカーの自動復旧を管理するメインコンポーネント
"""

import os
import time
import threading
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import yaml

from .health_checker import HealthChecker
from .recovery_strategies import RecoveryStrategies
from .state_manager import StateManager
from .notification_handler import NotificationHandler

logger = logging.getLogger(__name__)


class WorkerRecoveryManager:
    """ワーカー自動復旧システムのメインマネージャー"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルパス
        """
        self.config = self._load_config(config_path)
        self.health_checker = HealthChecker(self.config.get('health_check'))
        self.recovery_strategies = RecoveryStrategies()
        self.state_manager = StateManager()
        self.notification_handler = NotificationHandler()
        
        self.monitoring_active = False
        self.monitor_thread = None
        self.recovery_in_progress = {}
        self.recovery_cooldown = {}
        
        logger.info("Worker Recovery Manager initialized")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        if not config_path:
            config_path = '/home/aicompany/ai_co/config/worker_recovery.yaml'
        
        # デフォルト設定 - 99.999% uptime optimized
        default_config = {
            'recovery': {
                'check_interval': 10,  # 30秒→10秒に短縮（99.999%対応）
                'max_retries': 5,      # リトライ回数増加
                'retry_delay': 5,      # リトライ間隔を短縮
                'cooldown_period': 120  # クールダウンを2分に短縮
            },
            'health_check': {
                'thresholds': {
                    'cpu_percent': 90.0,
                    'memory_mb': 1024,
                    'error_rate': 0.1,
                    'queue_size': 100
                }
            },
            'notification': {
                'slack_enabled': True,
                'log_enabled': True
            }
        }
        
        # ファイルから設定を読み込み
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                    # デフォルト設定とマージ
                    self._merge_config(default_config, file_config)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}, using defaults")
        
        return default_config
    
    def _merge_config(self, base: Dict, override: Dict):
        """設定を再帰的にマージ"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def start_monitoring(self):
        """監視を開始"""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("Worker monitoring started")
        
        # 開始通知
        self.notification_handler.send_notification(
            "Worker Recovery System Started",
            "自動復旧システムが起動しました。",
            severity='info'
        )
    
    def stop_monitoring(self):
        """監視を停止"""
        self.monitoring_active = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Worker monitoring stopped")
        
        # 停止通知
        self.notification_handler.send_notification(
            "Worker Recovery System Stopped",
            "自動復旧システムが停止しました。",
            severity='info'
        )
    
    def _monitoring_loop(self):
        """監視ループ"""
        check_interval = self.config['recovery']['check_interval']
        
        while self.monitoring_active:
            try:
                # 全ワーカーの健康状態をチェック
                health_results = self.health_checker.check_all_workers()
                
                # 不健康なワーカーを特定
                unhealthy_workers = {
                    name: data for name, data in health_results.items()
                    if not data.get('healthy', True)
                }
                
                # 復旧が必要なワーカーを処理
                for worker_name, health_data in unhealthy_workers.items():
                    if self._should_recover(worker_name):
                        self._handle_recovery(worker_name, health_data)
                
                # トレンド分析
                self._analyze_trends()
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
            
            # 次のチェックまで待機
            time.sleep(check_interval)
    
    def _should_recover(self, worker_name: str) -> bool:
        """復旧を実行すべきか判断"""
        # 既に復旧中の場合
        if worker_name in self.recovery_in_progress:
            return False
        
        # クールダウン期間中の場合
        if worker_name in self.recovery_cooldown:
            cooldown_end = self.recovery_cooldown[worker_name]
            if datetime.now() < cooldown_end:
                return False
            else:
                del self.recovery_cooldown[worker_name]
        
        return True
    
    def _handle_recovery(self, worker_name: str, health_data: Dict[str, Any]):
        """ワーカーの復旧を処理"""
        logger.info(f"Initiating recovery for {worker_name}")
        
        # 復旧中フラグを設定
        self.recovery_in_progress[worker_name] = True
        
        try:
            # 状態を保存
            self.state_manager.save_worker_state(worker_name, health_data)
            
            # 復旧前の通知
            self.notification_handler.send_notification(
                f"Worker Recovery Started: {worker_name}",
                f"健康スコア: {health_data.get('health_score', 0):.1f}%",
                severity='warning'
            )
            
            # 復旧戦略を選択
            strategy = self.recovery_strategies.select_strategy(health_data)
            
            # 復旧を実行
            recovery_result = self.recovery_strategies.execute_recovery(
                worker_name, strategy, health_data
            )
            
            if recovery_result.get('success'):
                # 復旧成功
                logger.info(f"Recovery successful for {worker_name}")
                
                # 状態を復元
                self.state_manager.restore_worker_state(worker_name)
                
                # 成功通知
                self.notification_handler.send_notification(
                    f"Worker Recovery Successful: {worker_name}",
                    f"戦略: {strategy}",
                    severity='info'
                )
                
                # クールダウン期間を設定
                cooldown_period = self.config['recovery']['cooldown_period']
                self.recovery_cooldown[worker_name] = (
                    datetime.now() + timedelta(seconds=cooldown_period)
                )
            else:
                # 復旧失敗
                logger.error(f"Recovery failed for {worker_name}")
                
                # 失敗通知
                error_msg = recovery_result.get('error', 'Unknown error')
                self.notification_handler.send_notification(
                    f"Worker Recovery Failed: {worker_name}",
                    f"エラー: {error_msg}",
                    severity='error'
                )
                
                # エスカレーション
                self._escalate_recovery_failure(worker_name, recovery_result)
            
        except Exception as e:
            logger.error(f"Recovery handling error: {e}")
            self.notification_handler.send_notification(
                f"Worker Recovery Error: {worker_name}",
                f"例外: {str(e)}",
                severity='error'
            )
        
        finally:
            # 復旧中フラグを解除
            if worker_name in self.recovery_in_progress:
                del self.recovery_in_progress[worker_name]
    
    def _analyze_trends(self):
        """トレンド分析を実行"""
        try:
            # 各ワーカーのトレンドを分析
            for worker_name in self.health_checker.worker_configs:
                trend = self.health_checker.get_worker_trend(worker_name)
                
                if trend.get('trend') == 'degrading':
                    # 劣化傾向の場合は警告
                    self.notification_handler.send_notification(
                        f"Worker Health Degrading: {worker_name}",
                        f"現在のスコア: {trend.get('current_score', 0):.1f}%",
                        severity='warning'
                    )
        
        except Exception as e:
            logger.error(f"Trend analysis error: {e}")
    
    def _escalate_recovery_failure(self, worker_name: str, 
                                  recovery_result: Dict[str, Any]):
        """復旧失敗時のエスカレーション"""
        # Elder Councilへの報告
        try:
            from libs.elder_council_summoner import ElderCouncilSummoner
            
            summoner = ElderCouncilSummoner()
            summoner.trigger_council(
                category='worker_recovery_failure',
                urgency='HIGH',
                data={
                    'worker_name': worker_name,
                    'recovery_result': recovery_result,
                    'timestamp': datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to escalate to Elder Council: {e}")
    
    def recover_worker(self, worker_name: str) -> Dict[str, Any]:
        """
        特定のワーカーを手動で復旧
        
        Args:
            worker_name: ワーカー名
            
        Returns:
            復旧結果
        """
        logger.info(f"Manual recovery requested for {worker_name}")
        
        # 健康状態をチェック
        health_data = self.health_checker.check_worker_health(worker_name)
        
        # 復旧を実行
        self._handle_recovery(worker_name, health_data)
        
        return {
            'worker_name': worker_name,
            'health_data': health_data,
            'recovery_initiated': True
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        システムステータスを取得
        
        Returns:
            ステータス情報
        """
        # 全ワーカーの健康状態
        health_status = self.health_checker.check_all_workers()
        
        # 復旧履歴
        recovery_history = self.recovery_strategies.get_recovery_history(limit=5)
        
        return {
            'monitoring_active': self.monitoring_active,
            'workers_health': health_status,
            'recovery_in_progress': list(self.recovery_in_progress.keys()),
            'recovery_cooldown': {
                name: end_time.isoformat() 
                for name, end_time in self.recovery_cooldown.items()
            },
            'recent_recoveries': recovery_history,
            'config': self.config
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        設定を更新
        
        Args:
            new_config: 新しい設定
        """
        self._merge_config(self.config, new_config)
        
        # 各コンポーネントに設定を反映
        self.health_checker.config = self.config.get('health_check', {})
        
        logger.info("Configuration updated")
        
        # 設定ファイルに保存
        config_path = '/home/aicompany/ai_co/config/worker_recovery.yaml'
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)


# CLI用のエントリーポイント
def main():
    """CLIエントリーポイント"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Worker Recovery Manager')
    parser.add_argument('command', choices=['start', 'stop', 'status', 'recover'],
                       help='Command to execute')
    parser.add_argument('--worker', help='Worker name for recover command')
    parser.add_argument('--config', help='Config file path')
    
    args = parser.parse_args()
    
    manager = WorkerRecoveryManager(args.config)
    
    if args.command == 'start':
        manager.start_monitoring()
        print("Monitoring started. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            manager.stop_monitoring()
    
    elif args.command == 'stop':
        manager.stop_monitoring()
    
    elif args.command == 'status':
        status = manager.get_status()
        import json
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    elif args.command == 'recover':
        if not args.worker:
            print("Worker name required for recover command")
            return
        
        result = manager.recover_worker(args.worker)
        print(f"Recovery initiated for {args.worker}")


if __name__ == '__main__':
    main()