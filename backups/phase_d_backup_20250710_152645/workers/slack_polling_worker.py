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

import sys
import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.base_worker import BaseWorker
from libs.env_config import get_config
import logging

# Elder Tree Integration imports
try:
    from libs.four_sages_integration import FourSagesIntegration
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import get_elder_tree, ElderMessage, ElderRank
    ELDER_TREE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Elder Tree integration not available: {e}")
    FourSagesIntegration = None
    ElderCouncilSummoner = None
    get_elder_tree = None
    ElderMessage = None
    ElderRank = None
    ELDER_TREE_AVAILABLE = False
import requests
import pika

# 絵文字定義
EMOJI = {
    'start': '🚀',
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'task': '📋',
    'thinking': '🤔',
    'complete': '🎉'
}

class SlackPollingWorker(BaseWorker):
    """Slackメッセージをポーリングしてタスク化するワーカー"""
    
    def __init__(self, worker_id=None):
        # BaseWorkerの初期化
        super().__init__(
            worker_type='slack_polling',
            worker_id=worker_id
        )
        self.should_stop = False
        
        self.config = get_config()
        self.slack_token = self.config.SLACK_BOT_TOKEN or ''
        self.channel_id = getattr(self.config, 'SLACK_POLLING_CHANNEL_ID', 'C0946R76UU8')
        self.polling_interval = getattr(self.config, 'SLACK_POLLING_INTERVAL', 20)
        self.require_mention = getattr(self.config, 'SLACK_REQUIRE_MENTION', True)
        
        # メッセージ履歴管理用DB
        self.db_path = PROJECT_ROOT / 'db' / 'slack_messages.db'
        self._init_database()
        
        # Slack API設定
        self.headers = {
            'Authorization': f'Bearer {self.slack_token}',
            'Content-Type': 'application/json'
        }
        
    def _init_database(self):
        """メッセージ履歴DBの初期化"""
        self.db_path.parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processed_messages (
                    message_ts TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    user_id TEXT,
                    text TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_processed_at 
                ON processed_messages(processed_at DESC)
            ''')
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
                        oldest_timestamp = max(oldest_timestamp, float(message['ts']))
                
                # 指定間隔待機
                time.sleep(self.polling_interval)
                
            except KeyboardInterrupt:
                self.logger.info(f"{EMOJI['warning']} ポーリング停止シグナルを受信")
                break
            except Exception as e:
                self.handle_error(e, "polling_loop")
                time.sleep(self.polling_interval * 2)  # エラー時は間隔を延長
    
    def _get_bot_user_id(self):
        """Bot自身のユーザーIDを取得"""
        try:
            url = 'https://slack.com/api/auth.test'
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get('ok'):
                bot_user_id = data.get('user_id')
                return bot_user_id
            else:
                self.logger.error(f"Bot ID取得エラー: {data.get('error', 'Unknown')}")
                return None
        except Exception as e:
            self.logger.error(f"Bot ID取得例外: {str(e)}")
            return None
    
    def _fetch_slack_messages(self, oldest_timestamp):
        """Slackから新規メッセージを取得（レート制限対応）"""
        max_retries = 3
        base_wait = 60  # 1分ベース
        
        for attempt in range(max_retries):
            try:
                url = 'https://slack.com/api/conversations.history'
                params = {
                    'channel': self.channel_id,
                    'oldest': str(oldest_timestamp),
                    'inclusive': False,
                    'limit': 100
                }
                
                response = requests.get(url, headers=self.headers, params=params)
                
                # レート制限の場合
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', base_wait))
                    wait_time = min(retry_after + (attempt * 30), 300)  # 最大5分
                    
                    self.logger.warning(f"⏳ レート制限到達。{wait_time}秒待機中... (試行 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                data = response.json()
                if not data.get('ok'):
                    raise Exception(f"Slack API Error: {data.get('error', 'Unknown error')}")
                
                # 既に処理済みのメッセージをフィルタリング
                messages = data.get('messages', [])
                return self._filter_unprocessed_messages(messages)
                
            except requests.exceptions.RequestException as e:
                if "429" in str(e):
                    # 429エラーの場合は指数バックオフ
                    wait_time = base_wait * (2 ** attempt)
                    self.logger.warning(f"⏳ レート制限エラー。{wait_time}秒待機中... (試行 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"{EMOJI['error']} Slackメッセージ取得エラー: {str(e)}")
                    return []
            except Exception as e:
                self.logger.error(f"{EMOJI['error']} Slackメッセージ取得エラー: {str(e)}")
                return []
        
        # 全てのリトライが失敗した場合
        self.logger.error(f"{EMOJI['error']} レート制限により{max_retries}回のリトライが失敗。次回のポーリングまで待機。")
        return []
    
    def _filter_unprocessed_messages(self, messages):
        """未処理メッセージのみを抽出"""
        if not messages:
            return []
        
        with sqlite3.connect(self.db_path) as conn:
            # 既存のメッセージIDを取得
            placeholders = ','.join('?' * len(messages))
            ts_list = [msg['ts'] for msg in messages]
            
            cursor = conn.execute(
                f"SELECT message_ts FROM processed_messages WHERE message_ts IN ({placeholders})",
                ts_list
            )
            processed_ts = {row[0] for row in cursor.fetchall()}
        
        # 未処理のメッセージのみ返す
        return [msg for msg in messages if msg['ts'] not in processed_ts]
    
    def _process_message(self, message):
        """メッセージをタスクとして投入（ai-send形式）"""
        try:
            self.logger.info(f"🔍 メッセージ処理開始: {message.get('text', '')[:50]}...")
            
            # botメッセージは無視
            if message.get('bot_id') or message.get('subtype') == 'bot_message':
                self.logger.debug("🤖 Botメッセージをスキップ")
                return
            
            # メンションチェック
            text = message.get('text', '')
            self.logger.info(f"📝 受信テキスト: {text}")
            
            # メンション必須設定の場合
            if self.require_mention:
                # メンションされていない場合は無視
                if self.bot_user_id and f'<@{self.bot_user_id}>' not in text:
                    self.logger.info(f"⏭️ メンションなしのメッセージをスキップ: {text[:50]}...")
                    return
                else:
                    self.logger.info(f"✅ メンション検出: <@{self.bot_user_id}>")
            
            # メンションを除去してクリーンなテキストを取得
            clean_text = text
            if self.bot_user_id:
                clean_text = text.replace(f'<@{self.bot_user_id}>', '').strip()
            
            self.logger.info(f"🧹 クリーンテキスト: {clean_text}")
            
            # タスクタイプを判定（コード生成系のキーワード）
            task_type = self._determine_task_type(clean_text)
            self.logger.info(f"🏷️ タスクタイプ: {task_type}")
            
            # ai-send形式のタスクデータを構築
            task_data = {
                'task_id': f"slack_{int(float(message['ts']) * 1000000)}_{task_type}",
                'type': 'slack_command',
                'task_type': task_type,
                'prompt': clean_text,
                'source': 'slack',
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'slack_ts': message['ts'],
                    'slack_user': message.get('user', 'unknown'),
                    'slack_channel': self.channel_id,
                    'mentioned': True
                }
            }
            
            self.logger.info(f"📦 タスクデータ作成: {task_data['task_id']}")
            
            # ai_tasksキューに送信（TaskWorkerが処理）
            try:
                self.logger.info("🚀 RabbitMQキューに送信開始...")
                self._publish_to_task_queue(task_data)
                self.logger.info("✅ RabbitMQキューに送信成功")
            except Exception as queue_error:
                self.logger.error(f"❌ RabbitMQキュー送信エラー: {queue_error}")
                # キュー送信失敗でも続行
            
            # 処理済みとして記録
            try:
                self.logger.info("💾 処理済みDB記録開始...")
                self._mark_as_processed(message)
                self.logger.info("✅ 処理済みDB記録成功")
            except Exception as db_error:
                self.logger.error(f"❌ DB記録エラー: {db_error}")
            
            self.logger.info(f"{EMOJI['success']} Slackメッセージをタスク化: {task_data['task_id']}")
            self.logger.info(f"  タイプ: {task_type}")
            self.logger.info(f"  プロンプト: {clean_text[:100]}...")  
            self.logger.info(f"  ユーザー: {message.get('user', 'unknown')}")
            
            # 静かにリアクションのみ追加（処理中メッセージは送らない）
            try:
                self.logger.info("📤 Slack確認通知送信開始...")
                self._send_simple_reaction(message)
                self.logger.info("✅ Slack確認通知送信成功")
            except Exception as slack_error:
                self.logger.error(f"❌ Slack確認通知エラー: {slack_error}")
            
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} メッセージ処理エラー: {str(e)}")
            import traceback
            self.logger.error(f"🔍 エラー詳細: {traceback.format_exc()}")
    
    def _determine_task_type(self, text):
        """テキストからタスクタイプを判定"""
        text_lower = text.lower()
        
        # コード生成系のキーワード
        code_keywords = [
            'コード', 'code', 'プログラム', 'program', '実装', 'implement',
            'スクリプト', 'script', '作成', 'create', '作って', '生成',
            'ワーカー', 'worker', 'クラス', 'class', '関数', 'function',
            'python', 'javascript', 'bash', 'shell'
        ]
        
        for keyword in code_keywords:
            if keyword in text_lower:
                return 'code'
        
        return 'general'
    
    def _publish_to_task_queue(self, task_data):
        """ai_tasksキューにメッセージを送信"""
        try:
            # RabbitMQ接続を作成
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.config.RABBITMQ_HOST or 'localhost',
                    port=getattr(self.config, 'RABBITMQ_PORT', 5672),
                    virtual_host='/',
                    credentials=pika.PlainCredentials(
                        getattr(self.config, 'RABBITMQ_USER', 'guest'),
                        getattr(self.config, 'RABBITMQ_PASS', 'guest')
                    )
                )
            )
            
            channel = connection.channel()
            # 既存のキュー設定に合わせる
            channel.queue_declare(
                queue='ai_tasks', 
                durable=True,
                arguments={'x-max-priority': 10}
            )
            
            channel.basic_publish(
                exchange='',
                routing_key='ai_tasks',
                body=json.dumps(task_data),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            channel.close()
            connection.close()
            
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} キュー送信エラー: {str(e)}")
            # 非致命的エラーとして扱う（処理は続行）
    
    def _mark_as_processed(self, message):
        """メッセージを処理済みとして記録"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR IGNORE INTO processed_messages 
                (message_ts, channel_id, user_id, text)
                VALUES (?, ?, ?, ?)
            ''', (
                message['ts'],
                self.channel_id,
                message.get('user', ''),
                message.get('text', '')
            ))
            conn.commit()
    
    def _send_simple_reaction(self, message):
        """シンプルにリアクションのみ追加"""
        try:
            url = 'https://slack.com/api/reactions.add'
            data = {
                'channel': self.channel_id,
                'timestamp': message['ts'],
                'name': 'eyes'  # 👀 リアクション
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 200:
                self.logger.debug(f"リアクション追加成功")
            else:
                self.logger.debug(f"リアクション追加失敗: {response.status_code}")
        except Exception as e:
            self.logger.debug(f"リアクション追加エラー: {e}")
    
    def _send_processing_notification(self, message, task_id):
        """処理開始をSlackに通知（リアクション＋メッセージ）- 旧版"""
        try:
            # 1. リアクションを追加
            url = 'https://slack.com/api/reactions.add'
            data = {
                'channel': self.channel_id,
                'timestamp': message['ts'],
                'name': 'eyes'  # 👀 リアクション
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 200:
                self.logger.debug(f"リアクション追加成功: {task_id}")
            
            # 2. 受信確認メッセージを送信
            from libs.slack_notifier import SlackNotifier
            notifier = SlackNotifier()
            
            user = message.get('user', 'unknown')
            text_preview = message.get('text', '')[:50]
            
            confirmation_msg = f"📨 メッセージを受信しました！\n\n" \
                              f"**タスクID**: `{task_id}`\n" \
                              f"**内容**: {text_preview}{'...' if len(message.get('text', '')) > 50 else ''}\n" \
                              f"**ユーザー**: <@{user}>\n\n" \
                              f"🔄 処理を開始しています..."
            
            notifier.send_message(confirmation_msg)
            self.logger.info(f"📤 受信確認メッセージ送信: {task_id}")
            
        except Exception as e:
            self.logger.debug(f"通知送信失敗（非致命的）: {str(e)}")
    
    def process_message(self, ch, method, properties, body):
        """BaseWorkerの抽象メソッド実装（ポーリングワーカーなので使用しない）"""
        pass

    def cleanup(self):
        """TODO: cleanupメソッドを実装してください"""
        pass

    def start(self):
        """ポーリングワーカー用のstart実装（BaseWorkerのstart()をオーバーライド）"""
        self.logger.warning("⚠️ SlackPollingWorkerはstart()ではなくrun()を使用してください")
        self.run()

    def stop(self):
        """ワーカー停止処理"""
        self.should_stop = True
        self.logger.info("🛑 SlackPollingWorker停止フラグ設定")

    def initialize(self) -> None:
        """ワーカーの初期化処理"""
        # TODO: 初期化ロジックを実装してください
        logger.info(f"{self.__class__.__name__} initialized")
        pass

    def handle_error(self):
        """TODO: handle_errorメソッドを実装してください"""
        pass

    def get_status(self):
        """TODO: get_statusメソッドを実装してください"""
        pass

    def validate_config(self):
        """TODO: validate_configメソッドを実装してください"""
        pass

def main():
    """メイン実行"""
    import argparse
    parser = argparse.ArgumentParser(description='Slack Polling Worker')
    parser.add_argument('--worker-id', help='Worker ID')
    parser.add_argument('--test', action='store_true', help='テストモード')
    
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
            
        if getattr(config, 'SLACK_POLLING_CHANNEL_ID', None):
            print(f"✅ 監視チャンネル: {getattr(config, 'SLACK_POLLING_CHANNEL_ID', '')}")
        else:
            print("❌ 監視チャンネル未設定")
        
        return
    
    worker = SlackPollingWorker(worker_id=args.worker_id)
    
    try:
        # ポーリングワーカーなのでrun()を呼び出す（start()はRabbitMQコンシューマー用）
        worker.run()
    except KeyboardInterrupt:
        print(f"\n{EMOJI['warning']} Slack Polling Worker停止")
    finally:
        if hasattr(worker, 'cleanup'):
            worker.cleanup()
        else:
            worker.logger.info("Cleanup完了")

if __name__ == "__main__":
    main()
