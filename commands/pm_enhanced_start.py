#!/usr/bin/env python3
"""
Enhanced PM Worker Starter - PMが納得するまで繰り返すシステムの起動
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pika
import json
import logging
import subprocess
import os
import traceback
from datetime import datetime
import threading
import time

# Git Flow対応のインポート
from libs.github_flow_manager import GitHubFlowManager
from libs.pm_git_integration import PMGitIntegration
from libs.test_manager import TestManager
from libs.worker_monitor import WorkerMonitor
from libs.worker_controller import WorkerController
from libs.scaling_policy import ScalingPolicy
from libs.health_checker import HealthChecker
from libs.slack_notifier import SlackNotifier
from libs.pm_feedback_loop import PMFeedbackLoop
from commands.base_command import BaseCommand, CommandResult

PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR = PROJECT_DIR / "logs"

class PMEnhancedWorker:
    """PMフィードバック機能付きワーカー"""
    
    def __init__(self):
        self.model = "claude-opus-4-20250514"
        
        # Git Flow対応
        self.git_flow = GitHubFlowManager()
        self.git_integration = PMGitIntegration()
        
        # テスト管理
        self.test_manager = TestManager(str(PROJECT_DIR))
        self.test_before_commit = True
        
        # 動的管理関連
        self.monitor = WorkerMonitor()
        self.controller = WorkerController()
        self.policy = ScalingPolicy()
        self.health_checker = HealthChecker()
        self.scaling_enabled = True
        self.check_interval = 30
        self.health_check_interval = 60
        
        # PMフィードバックループ（新機能）
        self.feedback_loop = PMFeedbackLoop()
        self.feedback_enabled = True
        
        # Slack通知
        try:
            self.slack = SlackNotifier()
        except Exception as e:
            logging.warning(f"Slack通知の初期化に失敗: {e}")
            self.slack = None
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [PMEnhancedWorker] %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(LOG_DIR / "pm_enhanced_worker.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("PMEnhancedWorker")
    
    def connect(self):
        """RabbitMQ接続"""
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            self.channel = self.connection.channel()
            
            # 基本キュー
            self.channel.queue_declare(queue='pm_task_queue', durable=True)
            self.channel.queue_declare(queue='result_queue', durable=True)
            
            # フィードバック用キュー
            self.channel.queue_declare(queue='pm_feedback_queue', durable=True, arguments={'x-max-priority': 10})
            self.channel.queue_declare(queue='pm_retry_queue', durable=True, arguments={'x-max-priority': 10})
            
            self.logger.info("RabbitMQ接続成功")
            return True
        except Exception as e:
            self.logger.error(f"RabbitMQ接続失敗: {e}")
            return False
    
    def handle_task_completion(self, ch, method, properties, body):
        """タスク完了時の処理（PMフィードバック対応版）"""
        try:
            result = json.loads(body)
            task_id = result.get('task_id', 'unknown')
            status = result.get('status', 'unknown')
            
            self.logger.info(f"📋 タスク完了検知: {task_id} ({status})")
            
            # ResultWorkerへの転送用データを準備
            result_data = {
                'task_id': task_id,
                'task_type': result.get('task_type', 'general'),
                'status': status,
                'worker_id': result.get('worker_id', 'worker-1'),
                'rag_applied': result.get('rag_applied', False),
                'prompt': result.get('prompt', ''),
                'response': result.get('response', ''),
                'files_created': [],
                'output_file': result.get('output_file', ''),
                'duration': result.get('duration', 0.0),
                'error': result.get('error'),
                'error_trace': result.get('error_trace', ''),
                'attempt_count': result.get('attempt_count', 1)
            }
            
            if status == "completed":
                # 自動Git処理を一時的に無効化チェック
                if os.environ.get('AI_AUTO_GIT_DISABLED', 'false').lower() == 'true':
                    self.logger.info(f"🚫 自動Git処理は無効化されています: {task_id}")
                else:
                    # 新しいファイルが生成されたかチェック
                    new_files = self.detect_new_files()
                    result_data['files_created'] = new_files
                    
                    if new_files:
                        self.logger.info(f"📁 新規ファイル検出: {len(new_files)}件")
                        
                        # PMフィードバック評価（新機能）
                        if self.feedback_enabled:
                            feedback_result = self.feedback_loop.process_task_result(task_id, result_data)
                            
                            pm_approved = feedback_result.get('pm_approved', False)
                            retry_required = feedback_result.get('retry_required', False)
                            
                            if pm_approved:
                                self.logger.info(f"✅ PM承認済み - Git処理実行: {task_id}")
                                self._execute_git_flow(task_id, result_data, new_files)
                            elif retry_required:
                                self.logger.info(f"🔄 PM再試行要請 - Git処理スキップ: {task_id}")
                                # 再試行はフィードバックループが処理
                                self._send_retry_notification(task_id, feedback_result)
                            else:
                                self.logger.info(f"❌ PM最終却下 - Git処理スキップ: {task_id}")
                                self._send_rejection_notification(task_id, feedback_result)
                        else:
                            # フィードバック無効時は従来の処理
                            self.logger.info(f"🔄 従来のGit処理実行: {task_id}")
                            self._execute_git_flow(task_id, result_data, new_files)
                    else:
                        self.logger.info(f"📁 新規ファイル未検出: {task_id}")
            
            # ResultWorkerへ転送
            self._send_to_result_worker(result_data)
            
        except Exception as e:
            self.logger.error(f"タスク完了処理エラー: {e}")
            traceback.print_exc()
    
    def _execute_git_flow(self, task_id: str, result_data: dict, new_files: list):
        """Git Flow処理を実行"""
        try:
            # Git Flow対応の処理
            git_result_data = {
                'task_id': task_id,
                'files_created': new_files,
                'files_updated': [],
                'summary': result_data.get('prompt', 'Task completion')[:100]
            }
            
            # 作業ブランチ作成
            branch_name = self.git_flow.create_feature_branch(task_id)
            self.logger.info(f"🌿 作業ブランチ作成: {branch_name}")
            
            # テスト実行（オプション）
            test_passed = True
            if self.test_before_commit:
                test_passed = self._run_tests_for_files(new_files, task_id)
            
            if test_passed:
                # ファイルをコミット
                commit_message = f"Task {task_id}: {git_result_data['summary']}"
                if self.git_flow.commit_changes(commit_message, new_files, use_best_practices=True):
                    self.logger.info(f"✅ {branch_name} にコミット成功")
                    
                    # mainへPR作成またはマージ
                    if self.git_flow.create_pull_request(branch_name, f"feat: {git_result_data['summary']}", f"Auto-generated: {git_result_data['summary']}"):
                        self.logger.info(f"🔀 main へのPR作成成功")
                        
                        # 成功通知
                        if self.slack:
                            self._send_success_notification(task_id, branch_name, new_files, test_passed)
                    else:
                        self.logger.warning(f"⚠️ main へのPR作成失敗")
                        if self.slack:
                            self._send_merge_failure_notification(task_id, branch_name)
                else:
                    self.logger.warning(f"⚠️ コミット失敗")
            else:
                self.logger.error(f"❌ テスト失敗のためコミットをスキップ")
                if self.slack:
                    self._send_test_failure_notification(task_id, new_files)
                    
        except Exception as e:
            self.logger.error(f"Git Flow実行エラー: {e}")
    
    def _send_retry_notification(self, task_id: str, feedback_result: dict):
        """再試行通知"""
        try:
            if not self.slack:
                return
            
            evaluation_result = feedback_result.get('evaluation_result', {})
            overall_score = evaluation_result.get('overall_score', 0.0)
            
            message = f"🔄 PM品質評価 - 再試行要請\n"
            message += f"タスク: {task_id}\n"
            message += f"総合スコア: {overall_score:.1f}%\n"
            message += f"フィードバック: {evaluation_result.get('feedback_message', '')}\n"
            message += "改善後に再処理されます。"
            
            self.slack.send_task_completion_simple(
                task_id=f"pm_retry_{task_id}",
                worker="pm_enhanced_worker",
                prompt="PM品質評価 - 再試行",
                response=message
            )
        except Exception as e:
            self.logger.error(f"再試行通知エラー: {e}")
    
    def _send_rejection_notification(self, task_id: str, feedback_result: dict):
        """最終却下通知"""
        try:
            if not self.slack:
                return
            
            evaluation_result = feedback_result.get('evaluation_result', {})
            overall_score = evaluation_result.get('overall_score', 0.0)
            
            message = f"❌ PM品質評価 - 最終却下\n"
            message += f"タスク: {task_id}\n"
            message += f"総合スコア: {overall_score:.1f}%\n"
            message += f"理由: {evaluation_result.get('feedback_message', '')}\n"
            message += "最大再試行回数に達しました。"
            
            self.slack.send_task_completion_simple(
                task_id=f"pm_rejection_{task_id}",
                worker="pm_enhanced_worker",
                prompt="PM品質評価 - 最終却下",
                response=message
            )
        except Exception as e:
            self.logger.error(f"最終却下通知エラー: {e}")
    
    def _send_to_result_worker(self, result_data):
        """ResultWorkerへタスク結果を送信"""
        try:
            # ai_resultsキューに送信
            self.channel.queue_declare(queue='ai_results', durable=True)
            
            self.channel.basic_publish(
                exchange='',
                routing_key='ai_results',
                body=json.dumps(result_data, ensure_ascii=False),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 永続化
                )
            )
            
            self.logger.info(f"📤 ResultWorkerへ転送: {result_data['task_id']}")
            
        except Exception as e:
            self.logger.error(f"ResultWorker転送エラー: {e}")
    
    def _run_tests_for_files(self, files: list, task_id: str) -> bool:
        """ファイルに関連するテストを実行"""
        try:
            self.logger.info(f"🧪 テスト実行開始: {task_id}")
            
            # Pythonファイルが含まれているかチェック
            python_files = [f for f in files if f.endswith('.py')]
            
            if not python_files:
                self.logger.info(f"Pythonファイルなし - テストスキップ")
                return True
            
            # テスト実行
            test_results = []
            
            for py_file in python_files:
                file_path = Path(py_file)
                test_file = None
                
                # workersまたはlibsディレクトリのファイルの場合
                if file_path.parts[0] in ['workers', 'libs']:
                    test_file = PROJECT_DIR / 'tests' / 'unit' / f"test_{file_path.name}"
                
                if test_file and test_file.exists():
                    self.logger.info(f"テスト実行: {test_file}")
                    result = self.test_manager.run_specific_test(str(test_file))
                    test_results.append(result)
                else:
                    # 基本的な構文チェック
                    self.logger.info(f"構文チェック: {py_file}")
                    result = self._run_syntax_check(py_file)
                    test_results.append(result)
            
            # 全テストが成功したかチェック
            all_passed = all(r.get('success', False) for r in test_results)
            
            if all_passed:
                self.logger.info(f"✅ 全テスト成功")
            else:
                self.logger.error(f"❌ テスト失敗")
                # 失敗したテストの詳細をログ
                for i, result in enumerate(test_results):
                    if not result.get('success', False):
                        self.logger.error(f"失敗テスト {i+1}: {result.get('errors', 'Unknown error')}")
            
            return all_passed
            
        except Exception as e:
            self.logger.error(f"テスト実行エラー: {e}")
            return False
    
    def _run_syntax_check(self, file_path: str) -> dict:
        """Pythonファイルの構文チェック"""
        try:
            full_path = PROJECT_DIR / file_path
            cmd = ['python3', '-m', 'py_compile', str(full_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'errors': str(e)
            }
    
    def detect_new_files(self):
        """新しく生成されたファイルを検出"""
        try:
            import time
            current_time = time.time()
            recent_threshold = current_time - 300  # 5分前
            
            new_files = []
            
            # 複数のディレクトリを検索対象に
            search_dirs = [OUTPUT_DIR, PROJECT_DIR / "workers", PROJECT_DIR / "libs", 
                          PROJECT_DIR / "scripts", PROJECT_DIR / "config", PROJECT_DIR / "web"]
            
            extensions = ['*.py', '*.txt', '*.js', '*.html', '*.css', '*.json', '*.md', '*.sh', '*.conf']
            
            for search_dir in search_dirs:
                if search_dir.exists():
                    for ext in extensions:
                        files = search_dir.rglob(ext)
                        for file_path in files:
                            if file_path.stat().st_mtime > recent_threshold:
                                relative_path = file_path.relative_to(PROJECT_DIR)
                                # __pycache__やvenvは除外
                                if not any(part in str(relative_path) for part in ['__pycache__', 'venv', '.git']):
                                    new_files.append(str(relative_path))
            
            return list(set(new_files))  # 重複を削除
            
        except Exception as e:
            self.logger.error(f"新規ファイル検出エラー: {e}")
            return []
    
    def process_pm_task(self, ch, method, properties, body):
        """PM専用タスク処理"""
        try:
            task = json.loads(body)
            task_id = task.get("task_id", f"pm_unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            command = task.get("command", "")
            params = task.get("params", {})
            
            self.logger.info(f"PMタスク受信: {task_id} コマンド: {command}")
            
            if command == "toggle_feedback":
                # フィードバック機能のオン/オフ
                self.feedback_enabled = params.get("enable", True)
                self.logger.info(f"PMフィードバック機能: {'有効' if self.feedback_enabled else '無効'}")
                
                if self.slack:
                    self.slack.send_task_completion_simple(
                        task_id=f"feedback_toggle_{task_id}",
                        worker="pm_enhanced_worker",
                        prompt="フィードバック機能切り替え",
                        response=f"🔄 PMフィードバック機能: {'有効' if self.feedback_enabled else '無効'}"
                    )
            
            elif command == "feedback_stats":
                # フィードバック統計
                stats = self.feedback_loop.get_feedback_statistics()
                self.logger.info(f"フィードバック統計: {stats}")
                
                if self.slack:
                    message = f"📊 PMフィードバック統計\n"
                    message += f"アクティブタスク: {stats['active_tasks']}\n"
                    message += f"再試行タスク: {stats['retry_tasks']}\n"
                    quality_stats = stats.get('quality_stats', {})
                    message += f"承認率: {quality_stats.get('approval_rate', 0.0):.1f}%\n"
                    message += f"平均スコア: {quality_stats.get('average_score', 0.0):.1f}%"
                    
                    self.slack.send_task_completion_simple(
                        task_id=f"feedback_stats_{task_id}",
                        worker="pm_enhanced_worker",
                        prompt="フィードバック統計",
                        response=message
                    )
            
            elif command == "git_release":
                # リリース実行
                version = params.get("version")
                success = self.git_flow.create_release(version)
                self.logger.info(f"リリース処理: {'成功' if success else '失敗'}")
                
                if success and self.slack:
                    self.slack.send_task_completion_simple(
                        task_id=f"release_{version or datetime.now().strftime('%Y.%m.%d')}",
                        worker="pm_enhanced_worker",
                        prompt="Git Flow リリース",
                        response=f"🚀 Release v{version or datetime.now().strftime('%Y.%m.%d')} 作成完了"
                    )
            
            elif command == "toggle_test":
                # テスト実行のオン/オフ
                self.test_before_commit = params.get("enable", True)
                self.logger.info(f"テスト実行: {'有効' if self.test_before_commit else '無効'}")
            
            else:
                self.logger.warning(f"未知のコマンド: {command}")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self.logger.error(f"PMタスク処理例外: {e}")
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _send_success_notification(self, task_id: str, branch_name: str, files: list, test_passed: bool):
        """成功通知"""
        try:
            if not self.slack:
                return
            
            message = f"🌊 Git Flow 自動処理完了（PM承認済み）\n"
            message += f"タスク: {task_id}\n"
            message += f"ブランチ: {branch_name} → main\n"
            
            if test_passed and self.test_before_commit:
                message += f"テスト: ✅ 成功\n"
            
            message += f"ファイル数: {len(files)}\n"
            
            if len(files) <= 3:
                message += "ファイル:\n"
                for f in files:
                    message += f"  - {f}\n"
            
            self.slack.send_task_completion_simple(
                task_id=f"gitflow_{task_id}",
                worker="pm_enhanced_worker",
                prompt="Git Flow自動処理（PM承認済み）",
                response=message
            )
        except Exception as e:
            self.logger.error(f"Slack通知エラー: {e}")
    
    def _send_test_failure_notification(self, task_id: str, files: list):
        """テスト失敗通知"""
        try:
            if not self.slack:
                return
            
            message = f"❌ テスト失敗によりコミット中止\n"
            message += f"タスク: {task_id}\n"
            message += f"ファイル数: {len(files)}\n"
            message += "対象ファイル:\n"
            
            for f in files[:5]:  # 最大5ファイルまで表示
                message += f"  - {f}\n"
            
            message += "\nテストを修正してから再度コミットしてください。"
            
            self.slack.send_task_completion_simple(
                task_id=f"test_failure_{task_id}",
                worker="pm_enhanced_worker",
                prompt="テスト失敗通知",
                response=message
            )
        except Exception as e:
            self.logger.error(f"Slack通知エラー: {e}")
    
    def _send_merge_failure_notification(self, task_id: str, branch_name: str):
        """マージ失敗通知"""
        try:
            if not self.slack:
                return
            
            message = f"⚠️ mainへのマージ失敗\n"
            message += f"タスク: {task_id}\n"
            message += f"ブランチ: {branch_name}\n"
            message += "手動でのマージが必要です。"
            
            self.slack.send_task_completion_simple(
                task_id=f"merge_failure_{task_id}",
                worker="pm_enhanced_worker",
                prompt="マージ失敗通知",
                response=message
            )
        except Exception as e:
            self.logger.error(f"Slack通知エラー: {e}")
    
    def start(self):
        """Enhanced PMWorker起動"""
        # 初期設定
        self.logger.info("🌊 Enhanced PMWorker起動準備（PMフィードバック機能付き）")
        
        # Git Flow状態確認
        git_status = self.git_flow.get_status()
        self.logger.info(f"📊 Git状態 - ブランチ: {git_status.get('current_branch', 'unknown')}")
        self.logger.info(f"🧪 テスト実行: {'有効' if self.test_before_commit else '無効'}")
        self.logger.info(f"🔄 PMフィードバック: {'有効' if self.feedback_enabled else '無効'}")
        
        if not self.connect():
            return
        
        # キューの監視設定
        self.channel.basic_qos(prefetch_count=1)
        
        # PM専用タスク処理
        self.channel.basic_consume(queue='pm_task_queue', on_message_callback=self.process_pm_task)
        
        # 結果監視（自動Git処理）
        self.channel.queue_declare(queue='result_queue', durable=True)
        self.channel.basic_consume(
            queue='result_queue',
            on_message_callback=self.handle_task_completion,
            auto_ack=True
        )
        
        self.logger.info("🚀 Enhanced PM Worker起動完了")
        self.logger.info("📋 監視中: pm_task_queue (PM専用)")
        self.logger.info("📁 監視中: result_queue (Git Flow自動処理)")
        self.logger.info("🎯 PM品質評価: PMが納得するまで繰り返し")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.logger.info("Enhanced PMワーカー停止中...")
            self.channel.stop_consuming()
            self.connection.close()


class PMEnhancedStartCommand(BaseCommand):
    """Enhanced PM Worker起動コマンド"""
    
    def __init__(self):
        super().__init__(
            name="pm-enhanced-start",
            description="PMフィードバック機能付きワーカーを起動",
            version="1.0.0"
        )
    
    def execute(self, args) -> CommandResult:
        """実行"""
        try:
            worker = PMEnhancedWorker()
            worker.start()
            
            return CommandResult(
                success=True,
                message="Enhanced PM Worker起動完了"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Enhanced PM Worker起動失敗: {str(e)}"
            )


def main():
    command = PMEnhancedStartCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()