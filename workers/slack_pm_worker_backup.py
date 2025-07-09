#!/usr/bin/env python3
"""
Slack PM Worker - Slack統合プロジェクトマネージャーワーカー
既存のPM Workerを拡張してSlack対話機能を追加
"""

import os
import re
import sys
import json
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
import pika

# プロジェクトパス追加
sys.path.append(str(Path(__file__).parent.parent))

from libs.slack_pm_manager import SlackPMManager, ConversationState
from libs.slack_notifier import SlackNotifier
from libs.rate_limit_queue_processor import RateLimitQueueProcessor
from libs.claude_client_with_rotation import ClaudeClientWithRotation

PROJECT_DIR = Path(__file__).parent.parent
LOG_DIR = PROJECT_DIR / "logs"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SlackPMWorker] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "slack_pm_worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SlackPMWorker")

class SlackPMWorker:
    """
    Slack統合プロジェクトマネージャーワーカー
    """
    
    def __init__(self, worker_id="slack-pm-1"):
        self.worker_id = worker_id
        self.config_path = str(PROJECT_DIR / "config" / "config.json")
        
        # コンポーネント初期化
        self.slack_pm = SlackPMManager(self.config_path)
        self.slack_notifier = SlackNotifier()
        self.queue_processor = RateLimitQueueProcessor(self.config_path)
        self.claude_client = ClaudeClientWithRotation(self.config_path)
        
        # RabbitMQ
        self.connection = None
        self.channel = None
        
        # タスク管理
        self.active_tasks = {}
        self.task_results = {}
        
        # 状態管理
        self.running = False
        self.progress_thread = None
        
        # コールバック設定
        self._setup_callbacks()
        
    def _setup_callbacks(self):
        """コールバック関数の設定"""
        
        # SlackPMからのコールバック
        self.slack_pm.on_task_created = self._handle_task_creation
        self.slack_pm.on_approval_needed = self._handle_approval_request
        self.slack_pm.on_task_completed = self._handle_task_completion
        
        logger.info("📞 コールバック設定完了")
    
    def connect_rabbitmq(self):
        """RabbitMQ接続"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            self.channel = self.connection.channel()
            
            # キュー宣言
            self.channel.queue_declare(queue='ai_tasks', durable=True)
            self.channel.queue_declare(queue='ai_pm', durable=True)
            self.channel.queue_declare(queue='ai_slack_pm', durable=True)
            
            logger.info("✅ RabbitMQ接続成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ RabbitMQ接続失敗: {e}")
            return False
    
    def start(self):
        """ワーカー開始"""
        logger.info(f"🚀 {self.worker_id} 開始中...")
        
        # RabbitMQ接続
        if not self.connect_rabbitmq():
            logger.error("RabbitMQ接続失敗のため終了")
            return
        
        # キュープロセッサー開始
        self.queue_processor.start_processing()
        
        # Slack PM開始
        try:
            # RTMは別スレッドで開始
            rtm_thread = threading.Thread(target=self.slack_pm.start_rtm, daemon=True)
            rtm_thread.start()
            logger.info("📱 Slack RTM開始")
        except Exception as e:
            logger.error(f"Slack RTM開始失敗: {e}")
        
        # 進捗監視スレッド開始
        self.running = True
        self.progress_thread = threading.Thread(target=self._progress_monitor, daemon=True)
        self.progress_thread.start()
        
        # メインループ
        try:
            logger.info(f"📋 {self.worker_id} 待機中 - Slack対話型PM有効")
            
            # キュー消費設定
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue='slack_pm_tasks', 
                on_message_callback=self._process_slack_task
            )
            
            # メッセージ消費開始
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("🛑 ワーカー停止中...")
            self.stop()
    
    def stop(self):\n        \"\"\"ワーカー停止\"\"\"\n        self.running = False\n        \n        # Slack PM停止\n        try:\n            self.slack_pm.stop_rtm()\n        except Exception as e:\n            logger.error(f\"Slack PM停止エラー: {e}\")\n        \n        # キュープロセッサー停止\n        try:\n            self.queue_processor.stop_processing()\n        except Exception as e:\n            logger.error(f\"Queue Processor停止エラー: {e}\")\n        \n        # RabbitMQ停止\n        try:\n            if self.channel:\n                self.channel.stop_consuming()\n            if self.connection and not self.connection.is_closed:\n                self.connection.close()\n        except Exception as e:\n            logger.error(f\"RabbitMQ停止エラー: {e}\")\n        \n        # スレッド終了待機\n        if self.progress_thread:\n            self.progress_thread.join(timeout=5)\n        \n        logger.info(\"👋 Slack PM Worker 終了\")\n    \n    def _handle_task_creation(self, task_id: str, task_analysis: dict, session):\n        \"\"\"タスク作成時のコールバック\"\"\"\n        logger.info(f\"📋 タスク作成: {task_id}\")\n        \n        try:\n            # タスクの詳細分析\n            enhanced_analysis = self._enhance_task_analysis(task_analysis)\n            \n            # プロンプト生成\n            enhanced_prompt = self._generate_enhanced_prompt(\n                task_analysis['original_request'],\n                enhanced_analysis\n            )\n            \n            # タスクをキューに追加（優先度付き）\n            result = self.queue_processor.process_task_with_fallback(\n                task_id=task_id,\n                prompt=enhanced_prompt,\n                priority=3,  # 高優先度\n                task_type=\"slack_pm_task\"\n            )\n            \n            # タスク状態管理\n            self.active_tasks[task_id] = {\n                'session': session,\n                'analysis': enhanced_analysis,\n                'started_at': datetime.now(),\n                'status': 'queued' if not result['success'] else 'processing',\n                'progress': 0\n            }\n            \n            if result['success']:\n                logger.info(f\"✅ タスク即座実行: {task_id}\")\n                self._handle_immediate_task_result(task_id, result)\n            else:\n                logger.info(f\"📥 タスクキューイング: {task_id}\")\n                \n                # キューイング通知\n                if result.get('queued'):\n                    self.slack_pm._send_slack_message(\n                        session.channel_id,\n                        f\"⏳ **タスクをキューに追加しました**\\n\\n\"\n                        f\"**タスクID**: {task_id}\\n\"\n                        f\"**推定待機時間**: {result.get('estimated_delay', 'N/A')}秒\\n\\n\"\n                        f\"順番が来次第、処理を開始いたします。\"\n                    )\n                    \n        except Exception as e:\n            logger.error(f\"タスク作成処理エラー: {e}\")\n            self._handle_task_error(task_id, str(e), session)\n    \n    def _enhance_task_analysis(self, task_analysis: dict) -> dict:\n        \"\"\"タスク分析の強化\"\"\"\n        try:\n            # Claude APIで詳細分析\n            analysis_prompt = f\"\"\"\n以下のタスク要求を詳細分析してください：\n\n要求: {task_analysis['original_request']}\n\n以下の観点で分析結果をJSONで返してください：\n1. 技術要件\n2. 実装ステップ\n3. 必要なファイル\n4. テスト方針\n5. 潜在的な課題\n\"\"\"\n            \n            messages = [{\"role\": \"user\", \"content\": analysis_prompt}]\n            response = self.claude_client.create_message(messages=messages)\n            \n            # 分析結果をパース（簡易実装）\n            enhanced = task_analysis.copy()\n            enhanced['detailed_analysis'] = response['content']\n            enhanced['enhanced_at'] = datetime.now().isoformat()\n            \n            return enhanced\n            \n        except Exception as e:\n            logger.error(f\"タスク分析強化エラー: {e}\")\n            return task_analysis\n    \n    def _generate_enhanced_prompt(self, original_request: str, analysis: dict) -> str:\n        \"\"\"強化されたプロンプト生成\"\"\"\n        return f\"\"\"\n# AI Company Slack PM タスク実行\n\n## 元の要求\n{original_request}\n\n## 詳細分析\n{analysis.get('detailed_analysis', '分析なし')}\n\n## 実行指示\n上記の要求と分析に基づいて、以下を実行してください：\n\n1. **要件の整理**: 要求を明確にし、実装すべき内容を特定\n2. **技術選択**: 適切な技術スタック・アプローチを選択\n3. **実装**: 実際にコードを作成・ファイルを生成\n4. **テスト**: 動作確認とテストコード作成\n5. **ドキュメント**: 必要に応じて説明資料作成\n\n## 出力要求\n- 作成したファイルの内容をすべて表示\n- 実装の説明と使用方法\n- テスト結果（可能な場合）\n\n完了したら詳細な報告をお願いします。\n\"\"\"\n    \n    def _handle_immediate_task_result(self, task_id: str, result: dict):\n        \"\"\"即座実行されたタスクの結果処理\"\"\"\n        task_info = self.active_tasks.get(task_id)\n        if not task_info:\n            return\n        \n        # 結果保存\n        self.task_results[task_id] = {\n            'result': result,\n            'completed_at': datetime.now(),\n            'execution_time': (datetime.now() - task_info['started_at']).total_seconds()\n        }\n        \n        # 完了報告\n        self._send_completion_report(task_id, result)\n        \n        # タスク状態更新\n        task_info['status'] = 'completed'\n        task_info['progress'] = 100\n    \n    def _handle_task_error(self, task_id: str, error_msg: str, session):\n        \"\"\"タスクエラー処理\"\"\"\n        logger.error(f\"タスクエラー {task_id}: {error_msg}\")\n        \n        # エラー通知\n        self.slack_pm._send_slack_message(\n            session.channel_id,\n            f\"❌ **タスク実行エラー**\\n\\n\"\n            f\"**タスクID**: {task_id}\\n\"\n            f\"**エラー**: {error_msg}\\n\\n\"\n            f\"申し訳ございません。技術者が確認いたします。\"\n        )\n        \n        # タスク状態更新\n        if task_id in self.active_tasks:\n            self.active_tasks[task_id]['status'] = 'failed'\n            self.active_tasks[task_id]['error'] = error_msg\n    \n    def _process_slack_task(self, ch, method, properties, body):\n        \"\"\"Slackタスクキューからの処理\"\"\"\n        try:\n            task_data = json.loads(body)\n            task_id = task_data.get('task_id')\n            \n            logger.info(f\"📨 Slackタスク処理: {task_id}\")\n            \n            # タスク実行\n            result = self._execute_task(task_data)\n            \n            # 結果処理\n            if result['success']:\n                self._handle_task_success(task_id, result)\n            else:\n                self._handle_task_failure(task_id, result)\n            \n            ch.basic_ack(delivery_tag=method.delivery_tag)\n            \n        except Exception as e:\n            logger.error(f\"Slackタスク処理エラー: {e}\")\n            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)\n    \n    def _execute_task(self, task_data: dict) -> dict:\n        \"\"\"タスク実行\"\"\"\n        try:\n            task_id = task_data['task_id']\n            prompt = task_data['prompt']\n            \n            # Claude API実行\n            messages = [{\"role\": \"user\", \"content\": prompt}]\n            response = self.claude_client.create_message(messages=messages)\n            \n            return {\n                'success': True,\n                'response': response['content'],\n                'task_id': task_id,\n                'metadata': response\n            }\n            \n        except Exception as e:\n            return {\n                'success': False,\n                'error': str(e),\n                'task_id': task_data.get('task_id', 'unknown')\n            }\n    \n    def _handle_task_success(self, task_id: str, result: dict):\n        \"\"\"タスク成功処理\"\"\"\n        logger.info(f\"✅ タスク成功: {task_id}\")\n        \n        # 結果保存\n        self.task_results[task_id] = {\n            'result': result,\n            'completed_at': datetime.now()\n        }\n        \n        # 完了報告\n        self._send_completion_report(task_id, result)\n        \n        # タスク状態更新\n        if task_id in self.active_tasks:\n            self.active_tasks[task_id]['status'] = 'completed'\n            self.active_tasks[task_id]['progress'] = 100\n    \n    def _handle_task_failure(self, task_id: str, result: dict):\n        \"\"\"タスク失敗処理\"\"\"\n        logger.error(f\"❌ タスク失敗: {task_id} - {result.get('error')}\")\n        \n        task_info = self.active_tasks.get(task_id)\n        if task_info:\n            session = task_info['session']\n            self._handle_task_error(task_id, result.get('error', '不明なエラー'), session)\n    \n    def _send_completion_report(self, task_id: str, result: dict):\n        \"\"\"完了報告送信\"\"\"\n        task_info = self.active_tasks.get(task_id)\n        if not task_info:\n            return\n        \n        session = task_info['session']\n        response_content = result.get('response', result.get('result', {}).get('response', ''))\n        \n        # ファイル作成を検出\n        created_files = self._extract_created_files(response_content)\n        \n        # 実行時間計算\n        execution_time = (datetime.now() - task_info['started_at']).total_seconds()\n        \n        completion_data = {\n            'execution_time': f\"{int(execution_time // 60)}分{int(execution_time % 60)}秒\",\n            'deliverables': ['実装コード', 'テストコード', 'ドキュメント'],\n            'result_summary': '正常完了',\n            'created_files': created_files\n        }\n        \n        # Slack PM経由で報告\n        self.slack_pm.send_completion_report(task_id, completion_data)\n        \n        # 詳細結果も送信\n        if len(response_content) > 500:\n            summary = response_content[:500] + \"\\n\\n[結果が長いため省略...詳細は個別確認してください]\"\n        else:\n            summary = response_content\n        \n        self.slack_pm._send_slack_message(\n            session.channel_id,\n            f\"📝 **実行結果詳細**\\n\\n```\\n{summary}\\n```\"\n        )\n    \n    def _extract_created_files(self, content: str) -> List[str]:\n        \"\"\"作成されたファイルを抽出\"\"\"\n        files = []\n        \n        # ファイル作成パターンを検索\n        patterns = [\n            r'作成.*?ファイル.*?[：:]\\s*([^\\n]+)',\n            r'ファイル.*?[：:]\\s*([^\\n]+)',\n            r'Created.*?file.*?[：:]\\s*([^\\n]+)',\n            r'```.*?\\n.*?#.*?([\\w\\./]+\\.[\\w]+)',\n        ]\n        \n        for pattern in patterns:\n            matches = re.findall(pattern, content, re.IGNORECASE)\n            files.extend(matches)\n        \n        return list(set(files))  # 重複除去\n    \n    def _progress_monitor(self):\n        \"\"\"進捗監視スレッド\"\"\"\n        logger.info(\"📊 進捗監視スレッド開始\")\n        \n        while self.running:\n            try:\n                # 長時間実行中のタスクに進捗報告\n                current_time = datetime.now()\n                \n                for task_id, task_info in self.active_tasks.items():\n                    if task_info['status'] != 'processing':\n                        continue\n                    \n                    elapsed = (current_time - task_info['started_at']).total_seconds()\n                    \n                    # 2分毎に進捗報告\n                    if elapsed > 120 and elapsed % 120 < 30:\n                        progress = min(90, int(elapsed / 60 * 15))  # 大雑把な進捗計算\n                        \n                        progress_data = {\n                            'progress': progress,\n                            'status': '実行中',\n                            'completed_items': ['要件分析', 'プランニング'],\n                            'next_step': '実装・テスト'\n                        }\n                        \n                        self.slack_pm.send_progress_report(task_id, progress_data)\n                        task_info['progress'] = progress\n                \n                time.sleep(30)  # 30秒間隔でチェック\n                \n            except Exception as e:\n                logger.error(f\"進捗監視エラー: {e}\")\n                time.sleep(60)\n    \n    def _handle_approval_request(self, task_id: str, approval_data: dict):\n        \"\"\"承認要求処理\"\"\"\n        logger.info(f\"📋 承認要求: {task_id}\")\n        # 必要に応じて実装\n    \n    def _handle_task_completion(self, task_id: str, completion_data: dict):\n        \"\"\"タスク完了処理\"\"\"\n        logger.info(f\"🎯 タスク完了: {task_id}\")\n        # 必要に応じて実装\n    \n    def get_status(self) -> dict:\n        \"\"\"ワーカーステータス取得\"\"\"\n        return {\n            'worker_id': self.worker_id,\n            'running': self.running,\n            'active_tasks': len(self.active_tasks),\n            'completed_tasks': len(self.task_results),\n            'slack_sessions': len(self.slack_pm.active_sessions),\n            'queue_processor_status': self.queue_processor.get_status()\n        }\n\nif __name__ == \"__main__\":\n    worker_id = sys.argv[1] if len(sys.argv) > 1 else \"slack-pm-1\"\n    worker = SlackPMWorker(worker_id)\n    \n    try:\n        worker.start()\n    except KeyboardInterrupt:\n        logger.info(\"キーボード割り込み受信\")\n    finally:\n        worker.stop()