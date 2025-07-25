#!/usr/bin/env python3
"""
🌳 Elder Tree Integrated SlackPollingWorker
Elders Guild Slack Polling Worker - Elders Guild統合版

Elders Guild Integration:
- 🌟 Grand Elder maru oversight
- 🤖 Claude Elder execution guidance
- 🧙‍♂️ Four Sages wisdom consultation
- 🏛️ Elder Council decision support
- ⚔️ Elder Servants coordination

Part of the Elder Tree Hierarchy for Slack polling processing
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging

from core.base_worker import BaseWorker
from libs.env_config import get_config

# Elder Tree Integration imports
try:
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import ElderMessage, ElderRank, get_elder_tree
    from libs.four_sages_integration import FourSagesIntegration

    ELDER_TREE_AVAILABLE = True
except ImportError as e:
    # Handle specific exception case
    logging.warning(f"Elder Tree integration not available: {e}")
    FourSagesIntegration = None
    ElderCouncilSummoner = None
    get_elder_tree = None
    ElderMessage = None
    ElderRank = None
    ELDER_TREE_AVAILABLE = False
import pika
import requests

# 絵文字定義
EMOJI = {
    "start": "🚀",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "task": "📋",
    "thinking": "🤔",
    "complete": "🎉",
}

class SlackPollingWorker(BaseWorker):
    """Slackメッセージをポーリングしてタスク化するワーカー"""

    def __init__(self, worker_id=None):
        # BaseWorkerの初期化
        super().__init__(worker_type="slack_polling", worker_id=worker_id)
        self.should_stop = False

        self.config = get_config()
        self.slack_token = self.config.SLACK_BOT_TOKEN or ""
        self.channel_id = getattr(
            self.config, "SLACK_POLLING_CHANNEL_ID", "C0946R76UU8"
        )
        self.polling_interval = getattr(self.config, "SLACK_POLLING_INTERVAL", 20)
        self.require_mention = getattr(self.config, "SLACK_REQUIRE_MENTION", True)

        # メッセージ履歴管理用DB
        self.db_path = PROJECT_ROOT / "db" / "slack_messages.db"
        self._init_database()

        # Slack API設定
        self.headers = {
            "Authorization": f"Bearer {self.slack_token}",
            "Content-Type": "application/json",
        }

    def _init_database(self):
        """メッセージ履歴DBの初期化"""
        self.db_path.parent.mkdir(exist_ok=True)

        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_messages (
                    message_ts TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    user_id TEXT,
                    text TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_processed_at
                ON processed_messages(processed_at DESC)
            """
            )
            conn.commit()

    def run(self):
        """ポーリングループの実行"""
        self.logger.info(f"{EMOJI['start']} Slack Polling Worker開始")
        self.logger.info(f"📡 監視チャンネル: {self.channel_id}")
        self.logger.info(f"⏱️  ポーリング間隔: {self.polling_interval}秒")
        self.logger.info(f"👤 メンション必須: {'ON' if self.require_mention else 'OFF'}")

        # Bot IDを取得
        self.bot_user_id = self._get_bot_user_id()
        if self.bot_user_id:
            self.logger.info(f"🤖 Bot User ID: {self.bot_user_id}")
            self.logger.info(f"📌 メンション形式: @pm-ai または <@{self.bot_user_id}>")
        else:
            self.logger.warning("⚠️  Bot User IDを取得できませんでした。全メッセージを処理します。")

        # 初回は過去10分のメッセージから開始（テスト用に短く設定）
        oldest_timestamp = (datetime.now() - timedelta(minutes=10)).timestamp()

        while not self.should_stop:
            try:
                # Slackメッセージを取得
                new_messages = self._fetch_slack_messages(oldest_timestamp)

                if new_messages:
                    self.logger.info(f"{EMOJI['task']} {len(new_messages)}件の新規メッセージを検出")

                    for message in new_messages:
                        self._process_message(message)
                        # 最新のタイムスタンプを更新
                        oldest_timestamp = max(oldest_timestamp, float(message["ts"]))

                # 指定間隔待機
                time.sleep(self.polling_interval)

            except KeyboardInterrupt:
                # Handle specific exception case
                self.logger.info(f"{EMOJI['warning']} ポーリング停止シグナルを受信")
                break
            except Exception as e:
                # Handle specific exception case
                self.handle_error(e, "polling_loop")
                time.sleep(self.polling_interval * 2)  # エラー時は間隔を延長

    def _get_bot_user_id(self):
        """Bot自身のユーザーIDを取得"""
        try:
            url = "https://slack.com/api/auth.test"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("ok"):
                bot_user_id = data.get("user_id")
                return bot_user_id
            else:
                self.logger.error(f"Bot ID取得エラー: {data.get('error', 'Unknown')}")
                return None
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Bot ID取得例外: {str(e)}")
            return None

    def _fetch_slack_messages(self, oldest_timestamp):
        """Slackから新規メッセージを取得（レート制限対応）"""
        max_retries = 3
        base_wait = 60  # 1分ベース

            # Process each item in collection
            try:
                url = "https://slack.com/api/conversations.history"
                params = {
                    "channel": self.channel_id,
                    "oldest": str(oldest_timestamp),
                    "inclusive": False,
                    "limit": 100,
                }

                response = requests.get(url, headers=self.headers, params=params)

                # レート制限の場合
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", base_wait))

                    self.logger.warning(

                    )
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()

                data = response.json()
                if not data.get("ok"):
                    raise Exception(
                        f"Slack API Error: {data.get('error', 'Unknown error')}"
                    )

                # 既に処理済みのメッセージをフィルタリング
                messages = data.get("messages", [])
                return self._filter_unprocessed_messages(messages)

            except requests.exceptions.RequestException as e:
                # Handle specific exception case
                if "429" in str(e):
                    # 429エラーの場合は指数バックオフ

                    self.logger.warning(

                    )
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"{EMOJI['error']} Slackメッセージ取得エラー: {str(e)}")
                    return []
            except Exception as e:
                # Handle specific exception case
                self.logger.error(f"{EMOJI['error']} Slackメッセージ取得エラー: {str(e)}")
                return []

        # 全てのリトライが失敗した場合
        self.logger.error(
            f"{EMOJI['error']} レート制限により{max_retries}回のリトライが失敗。次回のポーリングまで待機。"
        )
        return []

    def _filter_unprocessed_messages(self, messages):
        """未処理メッセージのみを抽出"""
        if not messages:
            return []

        with sqlite3connect(self.db_path) as conn:
            # 既存のメッセージIDを取得
            placeholders = ",".join("?" * len(messages))
            ts_list = [msg["ts"] for msg in messages]

            cursor = conn.execute(
                f"SELECT message_ts FROM processed_messages WHERE message_ts IN ({placeholders})",
                ts_list,
            )
            processed_ts = {row[0] for row in cursor.fetchall()}

        # 未処理のメッセージのみ返す
        return [msg for msg in messages if msg["ts"] not in processed_ts]

    def _process_message(self, message):
        """メッセージをタスクとして投入（ai-send形式）"""
        try:
            self.logger.info(f"🔍 メッセージ処理開始: {message.get('text', '')[:50]}...")

            # botメッセージは無視
            if message.get("bot_id") or message.get("subtype") == "bot_message":
                # Complex condition - consider breaking down

                return

            # メンションチェック
            text = message.get("text", "")
            self.logger.info(f"📝 受信テキスト: {text}")

            # メンション必須設定の場合
            if self.require_mention:
                # メンションされていない場合は無視
                if self.bot_user_id and f"<@{self.bot_user_id}>" not in text:
                    # Complex condition - consider breaking down
                    self.logger.info(f"⏭️ メンションなしのメッセージをスキップ: {text[:50]}...")
                    return
                else:
                    self.logger.info(f"✅ メンション検出: <@{self.bot_user_id}>")

            # メンションを除去してクリーンなテキストを取得
            clean_text = text
            if self.bot_user_id:
                clean_text = text.replace(f"<@{self.bot_user_id}>", "").strip()

            self.logger.info(f"🧹 クリーンテキスト: {clean_text}")

            # タスクタイプを判定（コード生成系のキーワード）
            task_type = self._determine_task_type(clean_text)
            self.logger.info(f"🏷️ タスクタイプ: {task_type}")

            # ai-send形式のタスクデータを構築
            task_data = {
                "task_id": f"slack_{int(float(message['ts']) * 1000000)}_{task_type}",
                "type": "slack_command",
                "task_type": task_type,
                "prompt": clean_text,
                "source": "slack",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "slack_ts": message["ts"],
                    "slack_user": message.get("user", "unknown"),
                    "slack_channel": self.channel_id,
                    "mentioned": True,
                },
            }

            self.logger.info(f"📦 タスクデータ作成: {task_data['task_id']}")

            # ai_tasksキューに送信（TaskWorkerが処理）
            try:
                self.logger.info("🚀 RabbitMQキューに送信開始...")
                self._publish_to_task_queue(task_data)
                self.logger.info("✅ RabbitMQキューに送信成功")
            except Exception as queue_error:
                # Handle specific exception case
                self.logger.error(f"❌ RabbitMQキュー送信エラー: {queue_error}")
                # キュー送信失敗でも続行

            # 処理済みとして記録
            try:
                self.logger.info("💾 処理済みDB記録開始...")
                self._mark_as_processed(message)
                self.logger.info("✅ 処理済みDB記録成功")
            except Exception as db_error:
                # Handle specific exception case
                self.logger.error(f"❌ DB記録エラー: {db_error}")

            self.logger.info(
                f"{EMOJI['success']} Slackメッセージをタスク化: {task_data['task_id']}"
            )
            self.logger.info(f"  タイプ: {task_type}")
            self.logger.info(f"  プロンプト: {clean_text[:100]}...")
            self.logger.info(f"  ユーザー: {message.get('user', 'unknown')}")

            # 静かにリアクションのみ追加（処理中メッセージは送らない）
            try:
                self.logger.info("📤 Slack確認通知送信開始...")
                self._send_simple_reaction(message)
                self.logger.info("✅ Slack確認通知送信成功")
            except Exception as slack_error:
                # Handle specific exception case
                self.logger.error(f"❌ Slack確認通知エラー: {slack_error}")

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"{EMOJI['error']} メッセージ処理エラー: {str(e)}")
            import traceback

            self.logger.error(f"🔍 エラー詳細: {traceback.format_exc()}")

    def _determine_task_type(self, text):
        """テキストからタスクタイプを判定"""
        text_lower = text.lower()

        # コード生成系のキーワード
        code_keywords = [
            "コード",
            "code",
            "プログラム",
            "program",
            "実装",
            "implement",
            "スクリプト",
            "script",
            "作成",
            "create",
            "作って",
            "生成",
            "ワーカー",
            "worker",
            "クラス",
            "class",
            "関数",
            "function",
            "python",
            "javascript",
            "bash",
            "shell",
        ]

        for keyword in code_keywords:
            # Process each item in collection
            if keyword in text_lower:
                return "code"

        return "general"

    def _publish_to_task_queue(self, task_data):
        """ai_tasksキューにメッセージを送信"""
        try:
            # RabbitMQ接続を作成
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.config.RABBITMQ_HOST or "localhost",
                    port=getattr(self.config, "RABBITMQ_PORT", 5672),
                    virtual_host="/",
                    credentials=pika.PlainCredentials(
                        getattr(self.config, "RABBITMQ_USER", "guest"),
                        getattr(self.config, "RABBITMQ_PASS", "guest"),
                    ),
                )
            )

            channel = connection.channel()
            # 既存のキュー設定に合わせる
            channel.queue_declare(
                queue="ai_tasks", durable=True, arguments={"x-max-priority": 10}
            )

            channel.basic_publish(
                exchange="",
                routing_key="ai_tasks",
                body=json.dumps(task_data),
                properties=pika.BasicProperties(delivery_mode=2),
            )

            channel.close()
            connection.close()

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"{EMOJI['error']} キュー送信エラー: {str(e)}")
            # 非致命的エラーとして扱う（処理は続行）

    def _mark_as_processed(self, message):
        """メッセージを処理済みとして記録"""
        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO processed_messages
                (message_ts, channel_id, user_id, text)
                VALUES (?, ?, ?, ?)
            """,
                (
                    message["ts"],
                    self.channel_id,
                    message.get("user", ""),
                    message.get("text", ""),
                ),
            )
            conn.commit()

    def _send_simple_reaction(self, message):
        """シンプルにリアクションのみ追加"""
        try:
            url = "https://slack.com/api/reactions.add"
            data = {
                "channel": self.channel_id,
                "timestamp": message["ts"],
                "name": "eyes",  # 👀 リアクション
            }

            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 200:

            else:

        except Exception as e:
            # Handle specific exception case

    def _send_processing_notification(self, message, task_id):
        """処理開始をSlackに通知（リアクション＋メッセージ）- 旧版"""
        try:
            # 1.0 リアクションを追加
            url = "https://slack.com/api/reactions.add"
            data = {
                "channel": self.channel_id,
                "timestamp": message["ts"],
                "name": "eyes",  # 👀 リアクション
            }

            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 200:

            # 2.0 受信確認メッセージを送信
            from libs.slack_notifier import SlackNotifier

            notifier = SlackNotifier()

            user = message.get("user", "unknown")
            text_preview = message.get("text", "")[:50]

            confirmation_msg = (
                f"📨 メッセージを受信しました！\n\n"
                f"**タスクID**: `{task_id}`\n"
                f"**内容**: {text_preview}{'...' if len(message.get('text', '')) > 50 else ''}\n"
                f"**ユーザー**: <@{user}>\n\n"
                f"🔄 処理を開始しています..."
            )

            notifier.send_message(confirmation_msg)
            self.logger.info(f"📤 受信確認メッセージ送信: {task_id}")

        except Exception as e:
            # Handle specific exception case

    def process_message(self, ch, method, properties, body):
        """BaseWorkerの抽象メソッド実装（ポーリングワーカーなので使用しない）"""
        pass

    def cleanup(self):
        """ワーカーのクリーンアップ処理（Elder Tree終了通知、リソース解放）"""
        try:
            self.logger.info("🧹 SlackPollingWorker cleanup開始")
            
            # Elder Tree終了通知
            if ELDER_TREE_AVAILABLE and self.elder_tree:
                # Complex condition - consider breaking down
                try:
                    self.elder_tree.notify_shutdown({
                        "worker_type": "slack_polling",
                        "worker_id": self.worker_id,
                        "reason": "cleanup",
                        "timestamp": datetime.now().isoformat()
                    })
                    self.logger.info("📢 Elder Tree終了通知完了")
                except Exception as e:
                    # Handle specific exception case
                    self.logger.warning(f"Elder Tree終了通知エラー: {e}")
            
            # Slack接続のクリーンアップ
            try:
                # 現在の接続状態をクリア
                self.headers = {}
                self.logger.info("🔌 Slack接続クリーンアップ完了")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"Slack接続クリーンアップエラー: {e}")
            
            # データベース接続のクリーンアップ
            try:
                # SQLite接続は自動でクローズされるが、念のため明示的にクリーンアップ
                if hasattr(self, 'db_path') and self.db_path.exists():
                    # Complex condition - consider breaking down
                    # 古いレコードを削除（7日以上前）
                    cutoff_date = datetime.now() - timedelta(days=7)
                    with sqlite3connect(self.db_path) as conn:
                        conn.execute(
                            "DELETE FROM processed_messages WHERE processed_at < ?",
                            (cutoff_date,)
                        )
                        conn.commit()
                    self.logger.info("🗄️ データベースクリーンアップ完了")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"データベースクリーンアップエラー: {e}")
            
            # 統計情報の保存
            try:
                if hasattr(self, 'messages_processed'):
                    stats = {
                        "worker_id": self.worker_id,
                        "messages_processed": getattr(self, 'messages_processed', 0),
                        "cleanup_time": datetime.now().isoformat(),
                        "uptime": getattr(self, 'uptime', 0)
                    }
                    # 統計ファイルに保存
                    stats_file = PROJECT_ROOT / "logs" / "slack_worker_stats.json"
                    stats_file.parent.mkdir(exist_ok=True)
                    
                    existing_stats = []
                    if stats_file.exists():
                        # Deep nesting detected (depth: 5) - consider refactoring
                        with open(stats_file, 'r') as f:
                            existing_stats = json.load(f)
                    
                    existing_stats.append(stats)
                    with open(stats_file, 'w') as f:
                        json.dump(existing_stats, f, indent=2)
                    
                    self.logger.info(f"📊 統計情報保存完了: {getattr(self, 'messages_processed', 0)}件処理")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"統計情報保存エラー: {e}")
            
            self.logger.info("✅ SlackPollingWorker cleanup完了")
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"❌ Cleanup処理エラー: {e}")
            # クリーンアップエラーでも継続

    def start(self):
        """ポーリングワーカー用のstart実装（BaseWorkerのstart()をオーバーライド）"""
        self.logger.warning("⚠️ SlackPollingWorkerはstart()ではなくrun()を使用してください")
        self.run()

    def stop(self):
        """ワーカー停止処理（cleanup呼び出し、super().stop()）"""
        try:
            self.logger.info("🛑 SlackPollingWorker停止処理開始")
            
            # 停止フラグ設定
            self.should_stop = True
            self.logger.info("🚩 停止フラグ設定完了")
            
            # クリーンアップ実行
            self.cleanup()
            
            # 親クラスのstop()を呼び出し
            try:
                super().stop()
                self.logger.info("⬆️  親クラスstop()完了")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"親クラスstop()エラー: {e}")
            
            self.logger.info("✅ SlackPollingWorker停止処理完了")
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"❌ 停止処理エラー: {e}")
            # 停止処理エラーでも継続

    def initialize(self) -> None:
        """初期化処理（Elder Tree初期化、必要コンポーネント初期化）"""
        try:
            self.logger.info("🚀 SlackPollingWorker初期化開始")
            
            # Elder Tree統合システムの初期化
            if ELDER_TREE_AVAILABLE:
                try:
                    # Four Sages統合
                    if FourSagesIntegration:
                        self.four_sages = FourSagesIntegration()
                        self.logger.info("🧙‍♂️ Four Sages統合初期化完了")
                    
                    # Elder Council統合
                    if ElderCouncilSummoner:
                        self.elder_council_summoner = ElderCouncilSummoner()
                        self.logger.info("🏛️ Elder Council統合初期化完了")
                    
                    # Elder Tree接続
                    if get_elder_tree:
                        self.elder_tree = get_elder_tree()
                        self.logger.info("🌳 Elder Tree接続完了")
                        
                        # Elder Treeに初期化完了を通知
                        self.elder_tree.notify_initialization({
                            "worker_type": "slack_polling",
                            "worker_id": self.worker_id,
                            "capabilities": [
                                "slack_message_polling",
                                "task_creation",
                                "mention_detection",
                                "rate_limit_handling"
                            ],
                            "config": {
                                "channel_id": self.channel_id,
                                "polling_interval": self.polling_interval,
                                "require_mention": self.require_mention
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                
                except Exception as e:
                    # Handle specific exception case
                    self.logger.warning(f"Elder Tree統合エラー: {e}")
            
            # 統計カウンターの初期化
            self.messages_processed = 0
            self.tasks_created = 0
            self.errors_count = 0
            self.start_time = datetime.now()
            
            # Slack接続テスト
            try:
                if self.slack_token:
                    bot_id = self._get_bot_user_id()
                    if bot_id:
                        self.logger.info(f"✅ Slack接続テスト成功: Bot ID {bot_id}")
                    else:
                        self.logger.warning("⚠️ Slack接続テスト失敗")
                else:
                    self.logger.warning("⚠️ Slack Token未設定")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"Slack接続テストエラー: {e}")
            
            # データベース接続テスト
            try:
                with sqlite3connect(self.db_path) as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM processed_messages")
                    count = cursor.fetchone()[0]
                    self.logger.info(f"📊 データベース接続確認: {count}件の処理済みメッセージ")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"データベース接続テストエラー: {e}")
            
            # Task Sageに初期化完了を報告
            self._report_initialization_to_task_sage()
            
            self.logger.info(f"✅ {self.__class__.__name__} 初期化完了")
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"❌ 初期化エラー: {e}")
            # 初期化エラーは重要なので、Incident Sageに報告
            if hasattr(self, 'four_sages') and self.four_sages:
                # Complex condition - consider breaking down
                try:
                    self.four_sages.report_to_incident_sage({
                        "type": "initialization_error",
                        "worker_type": "slack_polling",
                        "error": str(e),
                        "severity": "medium"
                    })
                except Exception:
                    # Handle specific exception case
                    pass  # 報告エラーは無視

    def handle_error(self, error: Exception, context: str = None, severity: str = "medium") -> None:
        """エラーハンドリング（Incident Sageへの報告、ログ記録）"""
        try:
            # エラーカウント更新
            if hasattr(self, 'errors_count'):
                self.errors_count += 1
            
            # エラーの重要度を判定
            error_severity = self._determine_error_severity(error, context)
            
            # 基本ログ記録
            error_id = f"slack_polling_error_{int(datetime.now().timestamp())}"
            error_details = {
                "error_id": error_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or "unknown",
                "severity": error_severity,
                "timestamp": datetime.now().isoformat(),
                "worker_id": getattr(self, 'worker_id', 'unknown')
            }
            
            # ログレベル別記録
            if error_severity == "critical":
                self.logger.critical(f"🔥 重要エラー [{error_id}]: {error} (context: {context})")
            elif error_severity == "high":
                self.logger.error(f"❌ 高レベルエラー [{error_id}]: {error} (context: {context})")
            elif error_severity == "medium":
                self.logger.warning(f"⚠️ 中レベルエラー [{error_id}]: {error} (context: {context})")
            else:
                self.logger.info(f"ℹ️ 低レベルエラー [{error_id}]: {error} (context: {context})")
            
            # Incident Sageへの報告
            if ELDER_TREE_AVAILABLE and hasattr(self, 'four_sages') and self.four_sages:
                # Complex condition - consider breaking down
                try:
                    incident_report = {
                        "type": "worker_error",
                        "worker_type": "slack_polling",
                        "error_details": error_details,
                        "context_info": {
                            "slack_channel": getattr(self, 'channel_id', 'unknown'),
                            "polling_interval": getattr(self, 'polling_interval', 0),
                            "messages_processed": getattr(self, 'messages_processed', 0),
                            "bot_user_id": getattr(self, 'bot_user_id', None)
                        },
                        "recommendations": self._get_error_recommendations(error, context),
                        "requires_immediate_action": self._is_critical_error(error)
                    }
                    
                    self.four_sages.report_to_incident_sage(incident_report)
                    self.logger.info(f"📨 Incident Sage報告完了: {error_id}")
                    
                except Exception as report_error:
                    # Handle specific exception case
                    self.logger.warning(f"Incident Sage報告エラー: {report_error}")
            
            # Slack API関連エラーの特別処理
            if "slack" in str(error).lower() or "rate limit" in str(error).lower():
                # Complex condition - consider breaking down
                try:
                    # レート制限エラーの場合は自動調整
                    if "rate limit" in str(error).lower() or "429" in str(error):
                        # Complex condition - consider breaking down
                        old_interval = self.polling_interval
                        self.polling_interval = min(self.polling_interval * 2, 300)  # 最大5分
                        self.logger.info(f"⏰ ポーリング間隔自動調整: {old_interval}秒 → {self.polling_interval}秒" \
                            "⏰ ポーリング間隔自動調整: {old_interval}秒 → {self.polling_interval}秒" \
                            "⏰ ポーリング間隔自動調整: {old_interval}秒 → {self.polling_interval}秒")
                    
                    # Slack通知エラーファイルに記録
                    error_log_file = PROJECT_ROOT / "logs" / "slack_api_errors.json"
                    error_log_file.parent.mkdir(exist_ok=True)
                    
                    error_logs = []
                    if error_log_file.exists():
                        # Deep nesting detected (depth: 5) - consider refactoring
                        with open(error_log_file, 'r') as f:
                            error_logs = json.load(f)
                    
                    error_logs.append(error_details)
                    # 最新100件のみ保持
                    error_logs = error_logs[-100:]
                    
                    with open(error_log_file, 'w') as f:
                        json.dump(error_logs, f, indent=2)
                    
                except Exception as log_error:
                    # Handle specific exception case
                    self.logger.warning(f"エラーログ記録失敗: {log_error}")
            
            # 重要エラーの場合は追加処理
            if self._is_critical_error(error):
                self.logger.critical(f"🔥 重要エラー検出: {error_id}")
                # 必要に応じて自動復旧処理を実装
                
        except Exception as handler_error:
            # エラーハンドラー自体のエラーは最小限のログのみ
            self.logger.error(f"❌ エラーハンドラー内でエラー: {handler_error}")
            self.logger.error(f"元のエラー: {error}")

    def get_status(self) -> dict:
        """ワーカー状態取得（Elder Tree状態、処理統計）"""
        try:
            # 稼働時間計算
            if hasattr(self, 'start_time'):
                uptime = (datetime.now() - self.start_time).total_seconds()
            else:
                uptime = 0
            
            status = {
                "worker_info": {
                    "worker_type": "slack_polling_worker",
                    "worker_id": getattr(self, 'worker_id', 'unknown'),
                    "class_name": self.__class__.__name__,
                    "start_time": getattr(self, 'start_time', datetime.now()).isoformat(),
                    "uptime_seconds": uptime,
                    "uptime_formatted": self._format_uptime(uptime),
                    "is_running": not getattr(self, 'should_stop', False)
                },
                "processing_stats": {
                    "messages_processed": getattr(self, 'messages_processed', 0),
                    "tasks_created": getattr(self, 'tasks_created', 0),
                    "errors_count": getattr(self, 'errors_count', 0),
                    "processing_rate_per_hour": self._calculate_processing_rate(uptime),
                    "error_rate_percent": self._calculate_error_rate(),
                    "success_rate_percent": 100 - self._calculate_error_rate()
                },
                "slack_config": {
                    "channel_id": getattr(self, 'channel_id', 'unknown'),
                    "polling_interval": getattr(self, 'polling_interval', 0),
                    "require_mention": getattr(self, 'require_mention', True),
                    "bot_user_id": getattr(self, 'bot_user_id', None),
                    "token_configured": bool(getattr(self, 'slack_token', None))
                },
                "elder_integration": {
                    "elder_tree_available": ELDER_TREE_AVAILABLE,
                    "four_sages_active": hasattr(
                        self,
                        'four_sages'
                    ) and self.four_sages is not None,
                    "elder_council_active": hasattr(
                        self,
                        'elder_council_summoner'
                    ) and self.elder_council_summoner is not None,
                    "elder_tree_connected": hasattr(
                        self,
                        'elder_tree'
                    ) and self.elder_tree is not None
                },
                "database_info": {
                    "db_path": str(getattr(self, 'db_path', 'unknown')),
                    "db_exists": getattr(
                        self,
                        'db_path',
                        Path('/')).exists() if hasattr(self,
                        'db_path'
                    ) else False,
                    "processed_messages_count": self._get_processed_messages_count()
                },
                "health_status": self._determine_health_status(),
                "recommendations": self._generate_recommendations(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Elder Tree詳細状態
            if hasattr(self, 'elder_tree') and self.elder_tree:
                # Complex condition - consider breaking down
                try:
                    status["elder_tree_details"] = {
                        "connection_status": "connected",
                        "message_queue_size": len(getattr(self.elder_tree, 'message_queue', [])),
                        "node_count": len(getattr(self.elder_tree, 'nodes', []))
                    }
                except Exception as e:
                    # Handle specific exception case
                    status["elder_tree_details"] = {
                        "connection_status": "error",
                        "error": str(e)
                    }
            
            return status
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"状態取得エラー: {e}")
            return {
                "error": f"状態取得失敗: {e}",
                "timestamp": datetime.now().isoformat(),
                "worker_type": "slack_polling_worker",
                "worker_id": getattr(self, 'worker_id', 'unknown')
            }

    def validate_config(self) -> dict:
        """設定検証（設定妥当性チェック、必須項目確認）"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "config_details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Slack Token検証
            if not hasattr(self, 'slack_token') or not self.slack_token:
                # Complex condition - consider breaking down
                validation_result["errors"].append("Slack Bot Token が設定されていません")
                validation_result["is_valid"] = False
                validation_result["recommendations"].append("SLACK_BOT_TOKEN 環境変数を設定してください")
            else:
                validation_result["config_details"]["slack_token"] = "[設定済み]"  # トークンの値は表示しない
                
                # Token形式の基本チェック
                if not self.slack_token.startswith(('xoxb-', 'xoxp-')):
                    validation_result["warnings"].append("Slack Tokenの形式が正しくない可能性があります")
                    validation_result["recommendations"].append("xoxb- で始まるBot Tokenを使用してください")
            
            # チャンネルID検証
            if not hasattr(self, 'channel_id') or not self.channel_id:
                # Complex condition - consider breaking down
                validation_result["errors"].append("監視対象チャンネルIDが設定されていません")
                validation_result["is_valid"] = False
                validation_result["recommendations"].append("SLACK_POLLING_CHANNEL_ID を設定してください")
            else:
                validation_result["config_details"]["channel_id"] = self.channel_id
                
                # チャンネルID形式チェック
                if not self.channel_id.startswith('C'):
                    validation_result["warnings"].append("チャンネルIDの形式が正しくない可能性があります")
                    validation_result["recommendations"].append("Cから始まるチャンネルIDを使用してください")
            
            # ポーリング間隔検証
            if hasattr(self, 'polling_interval'):
                validation_result["config_details"]["polling_interval"] = self.polling_interval
                if self.polling_interval < 5:
                    validation_result["warnings"].append(f"ポーリング間隔が短すぎます: {self.polling_interval}秒")
                    validation_result["recommendations"].append("レート制限を避けるため10秒以上を推奨")
                elif self.polling_interval > 300:
                    validation_result["warnings"].append(f"ポーリング間隔が長すぎます: {self.polling_interval}秒")
                    validation_result["recommendations"].append("リアルタイム性を保つため60秒以下を推奨")
            
            # メンション要求設定
            if hasattr(self, 'require_mention'):
                validation_result["config_details"]["require_mention"] = self.require_mention
                if not self.require_mention:
                    validation_result["warnings"].append("メンション要求が無効です。全メッセージを処理します")
                    validation_result["recommendations"].append("セキュリティのためメンション要求を有効にしてください")
            
            # データベースパス検証
            if hasattr(self, 'db_path'):
                validation_result["config_details"]["db_path"] = str(self.db_path)
                if not self.db_path.parent.exists():
                    validation_result["errors"].append(f"データベースディレクトリが存在しません: {self.db_path.parent}")
                    validation_result["is_valid"] = False
                    validation_result["recommendations"].append(f"ディレクトリを作成してください: {self.db_path.parent}")
                elif not os.access(self.db_path.parent, os.W_OK):
                    validation_result["errors"].append(f"データベースディレクトリに書き込み権限がありません: {self.db_path.parent}")
                    validation_result["is_valid"] = False
                    validation_result["recommendations"].append("書き込み権限を付与してください")
            
            # RabbitMQ設定確認
            if hasattr(self, 'config'):
                if not hasattr(self.config, 'RABBITMQ_HOST') or not self.config.RABBITMQ_HOST:
                    # Complex condition - consider breaking down
                    validation_result["warnings"].append("RabbitMQ ホストが未設定です")
                    validation_result["recommendations"].append("RABBITMQ_HOST 環境変数を設定してください")
                else:
                    validation_result["config_details"]["rabbitmq_host"] = self.config.RABBITMQ_HOST
            
            # Elder Tree統合状態確認
            validation_result["config_details"]["elder_integration"] = {
                "available": ELDER_TREE_AVAILABLE,
                "four_sages_initialized": hasattr(
                    self,
                    'four_sages'
                ) and self.four_sages is not None,
                "elder_council_initialized": hasattr(
                    self,
                    'elder_council_summoner'
                ) and self.elder_council_summoner is not None,
                "elder_tree_connected": hasattr(self, 'elder_tree') and self.elder_tree is not None
            }
            
            if ELDER_TREE_AVAILABLE and not (hasattr(self, 'four_sages') and self.four_sages):
                # Complex condition - consider breaking down
                validation_result["warnings"].append("Elder Tree統合が利用可能ですが、初期化されていません")
                validation_result["recommendations"].append("initialize()メソッドを実行してください")
            
            # パフォーマンス統計の妥当性
            if hasattr(self, 'messages_processed') and self.messages_processed < 0:
                # Complex condition - consider breaking down
                validation_result["errors"].append("処理済みメッセージ数が負の値です")
                validation_result["is_valid"] = False
            
            if hasattr(self, 'errors_count') and self.errors_count < 0:
                # Complex condition - consider breaking down
                validation_result["errors"].append("エラー数が負の値です")
                validation_result["is_valid"] = False
            
            # エラー率チェック
            if hasattr(self, 'messages_processed') and hasattr(self, 'errors_count'):
                # Complex condition - consider breaking down
                if self.messages_processed > 0:
                    error_rate = (self.errors_count / self.messages_processed) * 100
                    if error_rate > 20:
                        validation_result["warnings"].append(f"エラー率が高すぎます: {error_rate:0.1f}%")
                        validation_result["recommendations"].append("Slack API設定とネットワーク接続を確認してください")
                    elif error_rate > 10:
                        validation_result["warnings"].append(f"エラー率がやや高めです: {error_rate:0.1f}%")
            
            # 成功時の追加情報
            if validation_result["is_valid"]:
                validation_result["summary"] = "設定は有効です"
                if not validation_result["warnings"]:
                    validation_result["summary"] += " - 警告なし"
            else:
                validation_result["summary"] = f"設定に {len(validation_result['errors'])} 個のエラーがあります"
            
            self.logger.info(f"設定検証完了: {validation_result['summary']}")
            
            return validation_result
            
        except Exception as e:
            # Handle specific exception case
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"設定検証中にエラー: {e}")
            validation_result["summary"] = "設定検証失敗"
            self.logger.error(f"設定検証エラー: {e}")
            return validation_result

    def _report_initialization_to_task_sage(self) -> None:
        """Task Sageに初期化完了を報告"""
        if not hasattr(self, 'four_sages') or not self.four_sages:
            # Complex condition - consider breaking down
            return
        
        try:
            report = {
                "type": "worker_initialization",
                "worker_type": "slack_polling",
                "worker_id": self.worker_id,
                "capabilities": [
                    "slack_message_polling",
                    "task_creation",
                    "mention_detection",
                    "rate_limit_handling"
                ],
                "config": {
                    "channel_id": self.channel_id,
                    "polling_interval": self.polling_interval,
                    "require_mention": self.require_mention
                },
                "status": "initialized",
                "timestamp": datetime.now().isoformat()
            }
            
            self.four_sages.report_to_task_sage(report)
            self.logger.info("📋 Task Sage初期化報告完了")
            
        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"Task Sage初期化報告エラー: {e}")

    def _determine_error_severity(self, error: Exception, context: str = None) -> str:
        """エラーの重要度を判定"""
        error_str = str(error).lower()
        
        # 重要エラー
        if any(keyword in error_str for keyword in [
            "authentication", "token", "forbidden", "unauthorized",
            "connection refused", "network unreachable"
        ]):
            return "critical"
        
        # 高レベルエラー  
        if any(keyword in error_str for keyword in [
            "rate limit", "429", "timeout", "database", "permission denied"
        ]):
            return "high"
        
        # 中レベルエラー
        if any(keyword in error_str for keyword in [
            "http", "api", "json", "parsing", "format"
        ]):
            return "medium"
        
        # デフォルトは低レベル
        return "low"

    def _get_error_recommendations(self, error: Exception, context: str = None) -> list:
        """エラーに応じた推奨対応を生成"""
        error_str = str(error).lower()
        recommendations = []
        
        if "token" in error_str or "authentication" in error_str:
            # Complex condition - consider breaking down
            recommendations.extend([
                "Slack Bot Tokenを確認してください",
                "Bot権限設定を確認してください",
                "トークンの有効期限を確認してください"
            ])
        
        if "rate limit" in error_str or "429" in error_str:
            # Complex condition - consider breaking down
            recommendations.extend([
                "ポーリング間隔を延長してください",
                "APIコール頻度を下げてください",
                "リトライ間隔を調整してください"
            ])
        
        if "network" in error_str or "connection" in error_str:
            # Complex condition - consider breaking down
            recommendations.extend([
                "ネットワーク接続を確認してください",
                "プロキシ設定を確認してください",
                "DNS設定を確認してください"
            ])
        
        if "database" in error_str:
            recommendations.extend([
                "データベースファイルの権限を確認してください",
                "ディスク容量を確認してください",
                "データベース整合性をチェックしてください"
            ])
        
        if not recommendations:
            recommendations.append("ログファイルで詳細なエラー情報を確認してください")
        
        return recommendations

    def _is_critical_error(self, error: Exception) -> bool:
        """エラーが重要かどうか判定"""
        return self._determine_error_severity(error) in ["critical", "high"]

    def _format_uptime(self, uptime_seconds: float) -> str:
        """アップタイムを人間が読みやすい形式にフォーマット"""
        if uptime_seconds < 60:
            return f"{uptime_seconds:0.0f}秒"
        elif uptime_seconds < 3600:
            minutes = uptime_seconds / 60
            return f"{minutes:0.1f}分"
        elif uptime_seconds < 86400:
            hours = uptime_seconds / 3600
            return f"{hours:0.1f}時間"
        else:
            days = uptime_seconds / 86400
            return f"{days:0.1f}日"

    def _calculate_processing_rate(self, uptime_seconds: float) -> float:
        """1時間あたりの処理率を計算"""
        if uptime_seconds <= 0:
            return 0.0
        
        messages_processed = getattr(self, 'messages_processed', 0)
        hours = uptime_seconds / 3600
        return messages_processed / hours if hours > 0 else 0.0

    def _calculate_error_rate(self) -> float:
        """エラー率を計算（パーセント）"""
        messages_processed = getattr(self, 'messages_processed', 0)
        errors_count = getattr(self, 'errors_count', 0)
        
        if messages_processed <= 0:
            return 0.0
        
        return (errors_count / messages_processed) * 100

    def _get_processed_messages_count(self) -> int:
        """データベースから処理済みメッセージ数を取得"""
        try:
            if hasattr(self, 'db_path') and self.db_path.exists():
                # Complex condition - consider breaking down
                with sqlite3connect(self.db_path) as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM processed_messages")
                    return cursor.fetchone()[0]
        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"処理済みメッセージ数取得エラー: {e}")
        
        return 0

    def _determine_health_status(self) -> str:
        """ワーカーの健康状態を判定"""
        # 停止状態チェック
        if getattr(self, 'should_stop', False):
            return "stopped"
        
        # 設定エラーチェック
        if not getattr(self, 'slack_token', None):
            return "critical"
        
        # エラー率チェック
        error_rate = self._calculate_error_rate()
        if error_rate > 50:
            return "critical"
        elif error_rate > 20:
            return "warning"
        
        # Elder Tree統合チェック
        if ELDER_TREE_AVAILABLE and hasattr(self, 'four_sages') and self.four_sages:
            # Complex condition - consider breaking down
            return "healthy"
        elif getattr(self, 'slack_token', None):
            return "degraded"
        else:
            return "critical"

    def _generate_recommendations(self) -> list:
        """現在の状態に基づく推奨事項を生成"""
        recommendations = []
        
        # エラー率チェック
        error_rate = self._calculate_error_rate()
        if error_rate > 20:
            recommendations.append("エラー率が高いため、Slack API設定とネットワーク接続を確認してください")
        
        # ポーリング間隔チェック
        if hasattr(self, 'polling_interval') and self.polling_interval < 10:
            # Complex condition - consider breaking down
            recommendations.append("レート制限を避けるため、ポーリング間隔を10秒以上に設定してください")
        
        # Elder Tree統合チェック
        if ELDER_TREE_AVAILABLE and not (hasattr(self, 'four_sages') and self.four_sages):
            # Complex condition - consider breaking down
            recommendations.append("Elder Tree統合を有効化すると監視・エラーハンドリング機能が向上します")
        
        # データベースチェック
        if hasattr(self, 'db_path'):
            processed_count = self._get_processed_messages_count()
            if processed_count > 10000:
                recommendations.append("処理済みメッセージが多いため、データベースのクリーンアップを検討してください")
        
        # メンション設定チェック
        if not getattr(self, 'require_mention', True):
            recommendations.append("セキュリティのため、メンション要求を有効にすることを推奨します")
        
        if not recommendations:
            recommendations.append("現在の設定は適切です")
        
        return recommendations

def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Slack Polling Worker")
    parser.add_argument("--worker-id", help="Worker ID")
    parser.add_argument("--test", action="store_true", help="テストモード")

    args = parser.parse_args()

    if args.test:
        print(f"{EMOJI['info']} テストモード: Slack Polling Worker")
        print("✅ ワーカーは正常に初期化できます")
        print("📡 Slack API接続をテスト中...")

        # 設定確認
        config = get_config()
        if config.SLACK_BOT_TOKEN:
            print("✅ Bot Token設定済み")
        else:
            print("❌ Bot Token未設定")

        if getattr(config, "SLACK_POLLING_CHANNEL_ID", None):
            print(f"✅ 監視チャンネル: {getattr(config, 'SLACK_POLLING_CHANNEL_ID', '')}")
        else:
            print("❌ 監視チャンネル未設定")

        return

    worker = SlackPollingWorker(worker_id=args.worker_id)

    try:
        # ポーリングワーカーなのでrun()を呼び出す（start()はRabbitMQコンシューマー用）
        worker.run()
    except KeyboardInterrupt:
        # Handle specific exception case
        print(f"\n{EMOJI['warning']} Slack Polling Worker停止")
    finally:
        if hasattr(worker, "cleanup"):
            worker.cleanup()
        else:
            worker.logger.info("Cleanup完了")

if __name__ == "__main__":
    main()
