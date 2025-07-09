#!/usr/bin/env python3
"""
Elder階層統合 Slack Polling Worker v2.0
AI Company Elder Hierarchy Integrated Slack Message Monitoring

エルダーズ評議会承認済み統合認証対応Slackメッセージ監視ワーカー
Elder階層別チャンネル監視・権限管理機能付き
"""

import sys
import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
import requests
import pika

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Elder階層システム統合
from core.elder_aware_base_worker import (
    ElderAwareBaseWorker,
    ElderTaskContext,
    ElderTaskResult,
    WorkerExecutionMode,
    ElderTaskPriority,
    elder_worker_required,
    SecurityError
)

# 統合認証システム
from libs.unified_auth_provider import (
    UnifiedAuthProvider,
    ElderRole,
    SageType,
    User,
    AuthSession
)

# 既存システム統合
from core import BaseWorker, get_config, EMOJI
from libs.env_config import get_config
from libs.slack_notifier import SlackNotifier

# Elder階層専用絵文字
ELDER_SLACK_EMOJI = {
    **EMOJI,
    'slack': '💬',
    'polling': '📡',
    'mention': '@',
    'council': '🏛️',
    'sage': '🧙‍♂️',
    'crown': '👑',
    'shield': '🛡️',
    'elder': '⚡',
    'secure': '🔒',
    'filter': '🔍',
    'authority': '🔱'
}


class ElderSlackPollingWorker(ElderAwareBaseWorker):
    """
    Elder階層統合Slackポーリングワーカー
    
    Elder階層システムと統合認証に対応したSlackメッセージ監視システム
    階層別チャンネル監視、権限に応じたメッセージフィルタリング
    """
    
    def __init__(self, worker_id: Optional[str] = None,
                 auth_provider: Optional[UnifiedAuthProvider] = None):
        # Elder階層BaseWorker初期化
        ElderAwareBaseWorker.__init__(
            self,
            auth_provider=auth_provider,
            required_elder_role=ElderRole.SERVANT,  # 基本的にサーバントでも利用可能
            required_sage_type=None
        )
        
        # ワーカー設定
        self.worker_type = 'slack_polling'
        self.worker_id = worker_id or f"elder_slack_polling_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.should_stop = False
        
        # Elder階層対応キュー設定
        self.input_queue = None  # ポーリングワーカーなので入力キューなし
        self.output_queue = 'ai_tasks_elder'  # Elder階層対応タスクキュー
        
        self.config = get_config()
        self.slack_token = self.config.SLACK_BOT_TOKEN or ''
        self.polling_interval = getattr(self.config, 'SLACK_POLLING_INTERVAL', 20)
        self.require_mention = getattr(self.config, 'SLACK_REQUIRE_MENTION', True)
        
        # Elder階層別チャンネル設定
        self.elder_channels = self._configure_elder_channels()
        
        # メッセージ履歴管理用DB
        self.db_path = PROJECT_ROOT / 'db' / 'elder_slack_messages.db'
        self._init_database()
        
        # Slack API設定
        self.headers = {
            'Authorization': f'Bearer {self.slack_token}',
            'Content-Type': 'application/json'
        }
        
        # Elder階層権限設定
        self.elder_permissions = self._configure_elder_permissions()
        
        # メッセージフィルター設定
        self.message_filters = self._configure_message_filters()
        
        self.logger.info(f"{ELDER_SLACK_EMOJI['council']} Elder Slack Polling Worker initialized - Required: {self.required_elder_role.value}")
    
    def _configure_elder_channels(self) -> Dict[ElderRole, List[str]]:
        """Elder階層別監視チャンネル設定"""
        default_channel = getattr(self.config, 'SLACK_POLLING_CHANNEL_ID', 'C0946R76UU8')
        
        return {
            ElderRole.GRAND_ELDER: [
                getattr(self.config, 'SLACK_ELDER_COUNCIL_CHANNEL', default_channel),
                getattr(self.config, 'SLACK_EMERGENCY_CHANNEL', default_channel),
                default_channel
            ],
            ElderRole.CLAUDE_ELDER: [
                getattr(self.config, 'SLACK_DEVELOPMENT_CHANNEL', default_channel),
                getattr(self.config, 'SLACK_SAGE_CHANNEL', default_channel),
                default_channel
            ],
            ElderRole.SAGE: [
                getattr(self.config, 'SLACK_SAGE_CHANNEL', default_channel),
                default_channel
            ],
            ElderRole.SERVANT: [
                default_channel
            ]
        }
    
    def _configure_elder_permissions(self) -> Dict[ElderRole, Dict[str, Any]]:
        """Elder階層別権限設定"""
        return {
            ElderRole.SERVANT: {
                'can_process_commands': True,
                'can_access_private_channels': False,
                'can_execute_system_commands': False,
                'max_message_priority': ElderTaskPriority.LOW,
                'allowed_keywords': ['help', 'status', 'info'],
                'forbidden_keywords': ['delete', 'admin', 'system', 'emergency']
            },
            ElderRole.SAGE: {
                'can_process_commands': True,
                'can_access_private_channels': True,
                'can_execute_system_commands': False,
                'max_message_priority': ElderTaskPriority.MEDIUM,
                'allowed_keywords': None,  # No restriction
                'forbidden_keywords': ['emergency', 'override']
            },
            ElderRole.CLAUDE_ELDER: {
                'can_process_commands': True,
                'can_access_private_channels': True,
                'can_execute_system_commands': True,
                'max_message_priority': ElderTaskPriority.HIGH,
                'allowed_keywords': None,
                'forbidden_keywords': []
            },
            ElderRole.GRAND_ELDER: {
                'can_process_commands': True,
                'can_access_private_channels': True,
                'can_execute_system_commands': True,
                'max_message_priority': ElderTaskPriority.CRITICAL,
                'allowed_keywords': None,
                'forbidden_keywords': []
            }
        }
    
    def _configure_message_filters(self) -> Dict[str, List[str]]:
        """メッセージフィルター設定"""
        return {
            'system_commands': ['!system', '!admin', '!elder', '!emergency'],
            'sage_commands': ['!sage', '!knowledge', '!task', '!incident', '!rag'],
            'development_keywords': ['デプロイ', 'deploy', '本番', 'production', 'リリース'],
            'sensitive_keywords': ['パスワード', 'password', 'token', 'secret', 'key']
        }
    
    def _init_database(self):
        """Elder階層対応メッセージ履歴DBの初期化"""
        self.db_path.parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS elder_processed_messages (
                    message_ts TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    user_id TEXT,
                    text TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    elder_role TEXT,
                    task_priority TEXT,
                    security_check TEXT
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_elder_processed_at 
                ON elder_processed_messages(processed_at DESC)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_elder_role 
                ON elder_processed_messages(elder_role)
            ''')
            conn.commit()
    
    async def run_with_elder_context(self, elder_context: ElderTaskContext):
        """Elder階層認証付きポーリングループの実行"""
        self.logger.info(f"{ELDER_SLACK_EMOJI['start']} Elder Slack Polling Worker開始")
        self.logger.info(f"{ELDER_SLACK_EMOJI['crown']} Elder Role: {elder_context.user.elder_role.value}")
        
        # Elder階層に応じた監視チャンネル取得
        channels_to_monitor = self.elder_channels.get(
            elder_context.user.elder_role, 
            self.elder_channels[ElderRole.SERVANT]
        )
        
        self.logger.info(f"{ELDER_SLACK_EMOJI['polling']} 監視チャンネル数: {len(channels_to_monitor)}")
        self.logger.info(f"⏱️  ポーリング間隔: {self.polling_interval}秒")
        self.logger.info(f"👤 メンション必須: {'ON' if self.require_mention else 'OFF'}")
        
        # Bot IDを取得
        self.bot_user_id = self._get_bot_user_id()
        if self.bot_user_id:
            self.logger.info(f"🤖 Bot User ID: {self.bot_user_id}")
            self.logger.info(f"📌 メンション形式: @pm-ai または <@{self.bot_user_id}>")
        
        # 初回は過去10分のメッセージから開始
        oldest_timestamp = (datetime.now() - timedelta(minutes=10)).timestamp()
        
        # Elder監査ログ
        self.audit_logger.log_elder_action(
            elder_context,
            "slack_polling_start",
            f"Starting Slack polling for channels: {channels_to_monitor}"
        )
        
        while not self.should_stop:
            try:
                # 各チャンネルからメッセージを取得
                for channel_id in channels_to_monitor:
                    new_messages = await self._fetch_slack_messages_with_auth(
                        channel_id, oldest_timestamp, elder_context
                    )
                    
                    if new_messages:
                        self.logger.info(
                            f"{ELDER_SLACK_EMOJI['task']} {len(new_messages)}件の新規メッセージを検出 "
                            f"(Channel: {channel_id})"
                        )
                        
                        for message in new_messages:
                            await self._process_message_with_elder_auth(
                                message, channel_id, elder_context
                            )
                            # 最新のタイムスタンプを更新
                            oldest_timestamp = max(oldest_timestamp, float(message['ts']))
                
                # 指定間隔待機
                await asyncio.sleep(self.polling_interval)
                
            except KeyboardInterrupt:
                self.logger.info(f"{ELDER_SLACK_EMOJI['warning']} ポーリング停止シグナルを受信")
                break
            except Exception as e:
                self.logger.error(f"Elder polling error: {e}")
                
                # エラー監査ログ
                self.audit_logger.log_security_event(
                    elder_context,
                    "slack_polling_error",
                    {"error": str(e), "timestamp": datetime.now().isoformat()}
                )
                
                await asyncio.sleep(self.polling_interval * 2)
    
    def _get_bot_user_id(self):
        """Bot自身のユーザーIDを取得"""
        try:
            url = 'https://slack.com/api/auth.test'
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get('ok'):
                return data.get('user_id')
            else:
                self.logger.error(f"Bot ID取得エラー: {data.get('error', 'Unknown')}")
                return None
        except Exception as e:
            self.logger.error(f"Bot ID取得例外: {str(e)}")
            return None
    
    async def _fetch_slack_messages_with_auth(self, channel_id: str, 
                                            oldest_timestamp: float,
                                            elder_context: ElderTaskContext) -> List[Dict]:
        """Elder階層認証付きSlackメッセージ取得"""
        # 権限チェック
        permissions = self.elder_permissions[elder_context.user.elder_role]
        
        # プライベートチャンネルアクセス権限チェック
        if channel_id.startswith('G') and not permissions['can_access_private_channels']:
            self.logger.warning(
                f"{ELDER_SLACK_EMOJI['shield']} Private channel access denied for {elder_context.user.elder_role.value}"
            )
            return []
        
        max_retries = 3
        base_wait = 60
        
        for attempt in range(max_retries):
            try:
                url = 'https://slack.com/api/conversations.history'
                params = {
                    'channel': channel_id,
                    'oldest': str(oldest_timestamp),
                    'inclusive': False,
                    'limit': 100
                }
                
                response = requests.get(url, headers=self.headers, params=params)
                
                # レート制限の場合
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', base_wait))
                    wait_time = min(retry_after + (attempt * 30), 300)
                    
                    self.logger.warning(
                        f"⏳ Rate limit reached. Waiting {wait_time}s... (Attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                data = response.json()
                if not data.get('ok'):
                    raise Exception(f"Slack API Error: {data.get('error', 'Unknown error')}")
                
                # 既に処理済みのメッセージをフィルタリング
                messages = data.get('messages', [])
                unprocessed = self._filter_unprocessed_messages(messages, channel_id)
                
                # Elder階層に応じたメッセージフィルタリング
                filtered = self._apply_elder_message_filters(unprocessed, elder_context)
                
                return filtered
                
            except Exception as e:
                self.logger.error(f"{ELDER_SLACK_EMOJI['error']} Slack message fetch error: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_wait * (2 ** attempt))
                    continue
                return []
        
        return []
    
    def _filter_unprocessed_messages(self, messages: List[Dict], channel_id: str) -> List[Dict]:
        """未処理メッセージのみを抽出"""
        if not messages:
            return []
        
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ','.join('?' * len(messages))
            ts_list = [msg['ts'] for msg in messages]
            
            cursor = conn.execute(
                f"SELECT message_ts FROM elder_processed_messages WHERE message_ts IN ({placeholders})",
                ts_list
            )
            processed_ts = {row[0] for row in cursor.fetchall()}
        
        return [msg for msg in messages if msg['ts'] not in processed_ts]
    
    def _apply_elder_message_filters(self, messages: List[Dict], 
                                   elder_context: ElderTaskContext) -> List[Dict]:
        """Elder階層に応じたメッセージフィルタリング"""
        permissions = self.elder_permissions[elder_context.user.elder_role]
        filtered_messages = []
        
        for msg in messages:
            text = msg.get('text', '').lower()
            
            # 禁止キーワードチェック
            if permissions['forbidden_keywords']:
                if any(keyword in text for keyword in permissions['forbidden_keywords']):
                    self.logger.info(
                        f"{ELDER_SLACK_EMOJI['filter']} Forbidden keyword detected, skipping message"
                    )
                    continue
            
            # 許可キーワードチェック（設定されている場合）
            if permissions['allowed_keywords'] is not None:
                if not any(keyword in text for keyword in permissions['allowed_keywords']):
                    self.logger.info(
                        f"{ELDER_SLACK_EMOJI['filter']} No allowed keyword found, skipping message"
                    )
                    continue
            
            # システムコマンドチェック
            if any(cmd in text for cmd in self.message_filters['system_commands']):
                if not permissions['can_execute_system_commands']:
                    self.logger.info(
                        f"{ELDER_SLACK_EMOJI['shield']} System command access denied"
                    )
                    continue
            
            filtered_messages.append(msg)
        
        return filtered_messages
    
    async def _process_message_with_elder_auth(self, message: Dict, channel_id: str,
                                             elder_context: ElderTaskContext):
        """Elder階層認証付きメッセージ処理"""
        try:
            self.logger.info(f"{ELDER_SLACK_EMOJI['slack']} Processing message: {message.get('text', '')[:50]}...")
            
            # botメッセージは無視
            if message.get('bot_id') or message.get('subtype') == 'bot_message':
                return
            
            text = message.get('text', '')
            
            # メンション必須設定の場合
            if self.require_mention:
                if self.bot_user_id and f'<@{self.bot_user_id}>' not in text:
                    return
            
            # メンションを除去してクリーンなテキストを取得
            clean_text = text
            if self.bot_user_id:
                clean_text = text.replace(f'<@{self.bot_user_id}>', '').strip()
            
            # セキュリティチェック
            security_check = await self._perform_security_check(clean_text, elder_context)
            if not security_check['passed']:
                self.logger.warning(
                    f"{ELDER_SLACK_EMOJI['secure']} Security check failed: {security_check['reason']}"
                )
                
                # セキュリティ違反を監査ログに記録
                self.audit_logger.log_security_event(
                    elder_context,
                    "slack_message_blocked",
                    {
                        "message": clean_text[:100],
                        "reason": security_check['reason'],
                        "user": message.get('user', 'unknown')
                    }
                )
                return
            
            # タスクタイプを判定
            task_type = self._determine_task_type_with_elder(clean_text, elder_context)
            
            # 優先度決定（Elder階層に基づく）
            priority = self._determine_priority(clean_text, elder_context)
            
            # Elder階層対応タスクデータ構築
            task_data = {
                'task_id': f"slack_elder_{int(float(message['ts']) * 1000000)}_{task_type}",
                'type': 'slack_command',
                'task_type': task_type,
                'prompt': clean_text,
                'source': 'slack',
                'timestamp': datetime.now().isoformat(),
                'elder_context': {
                    'processed_by': elder_context.user.username,
                    'elder_role': elder_context.user.elder_role.value,
                    'priority': priority.value
                },
                'metadata': {
                    'slack_ts': message['ts'],
                    'slack_user': message.get('user', 'unknown'),
                    'slack_channel': channel_id,
                    'mentioned': True,
                    'security_check': security_check
                }
            }
            
            # Elder階層タスクキューに送信
            await self._publish_to_elder_task_queue(task_data, elder_context)
            
            # 処理済みとして記録（Elder情報付き）
            self._mark_as_processed_with_elder(message, channel_id, elder_context, priority)
            
            # Elder監査ログ
            self.audit_logger.log_elder_action(
                elder_context,
                "slack_message_processed",
                f"Processed Slack message as task: {task_data['task_id']}"
            )
            
            # Slackリアクション（Elder階層に応じた絵文字）
            await self._send_elder_reaction(message, channel_id, elder_context)
            
            self.logger.info(
                f"{ELDER_SLACK_EMOJI['success']} Slack message processed: {task_data['task_id']} "
                f"(Priority: {priority.value})"
            )
            
        except Exception as e:
            self.logger.error(f"{ELDER_SLACK_EMOJI['error']} Message processing error: {str(e)}")
            
            self.audit_logger.log_security_event(
                elder_context,
                "slack_processing_error",
                {"error": str(e), "message_ts": message.get('ts')}
            )
    
    async def _perform_security_check(self, text: str, 
                                    elder_context: ElderTaskContext) -> Dict[str, Any]:
        """セキュリティチェック実行"""
        # センシティブキーワードチェック
        for keyword in self.message_filters['sensitive_keywords']:
            if keyword in text.lower():
                return {
                    'passed': False,
                    'reason': f'Sensitive keyword detected: {keyword}',
                    'severity': 'high'
                }
        
        # SQLインジェクション簡易チェック
        sql_patterns = ['drop table', 'delete from', 'update set', '; --']
        for pattern in sql_patterns:
            if pattern in text.lower():
                return {
                    'passed': False,
                    'reason': 'Potential SQL injection detected',
                    'severity': 'critical'
                }
        
        # Elder階層に応じた追加チェック
        permissions = self.elder_permissions[elder_context.user.elder_role]
        if elder_context.user.elder_role == ElderRole.SERVANT:
            # サーバントの場合、より厳しいチェック
            if len(text) > 500:
                return {
                    'passed': False,
                    'reason': 'Message too long for servant role',
                    'severity': 'low'
                }
        
        return {
            'passed': True,
            'reason': None,
            'severity': None
        }
    
    def _determine_task_type_with_elder(self, text: str, 
                                      elder_context: ElderTaskContext) -> str:
        """Elder階層を考慮したタスクタイプ判定"""
        text_lower = text.lower()
        
        # システムコマンド判定（Elder以上）
        if elder_context.user.elder_role in [ElderRole.GRAND_ELDER, ElderRole.CLAUDE_ELDER]:
            for cmd in self.message_filters['system_commands']:
                if cmd in text_lower:
                    return 'system_command'
        
        # 賢者コマンド判定（Sage以上）
        if elder_context.user.elder_role != ElderRole.SERVANT:
            for cmd in self.message_filters['sage_commands']:
                if cmd in text_lower:
                    return 'sage_command'
        
        # 開発関連判定
        for keyword in self.message_filters['development_keywords']:
            if keyword in text_lower:
                return 'development'
        
        # 通常のコード生成判定
        code_keywords = [
            'コード', 'code', 'プログラム', 'program', '実装', 'implement',
            'スクリプト', 'script', '作成', 'create', '作って', '生成'
        ]
        
        for keyword in code_keywords:
            if keyword in text_lower:
                return 'code'
        
        return 'general'
    
    def _determine_priority(self, text: str, 
                          elder_context: ElderTaskContext) -> ElderTaskPriority:
        """Elder階層に基づく優先度決定"""
        permissions = self.elder_permissions[elder_context.user.elder_role]
        max_priority = permissions['max_message_priority']
        
        # 緊急キーワードチェック
        if any(word in text.lower() for word in ['緊急', 'urgent', 'emergency', 'critical']):
            # Grand Elderのみ緊急優先度設定可能
            if elder_context.user.elder_role == ElderRole.GRAND_ELDER:
                return ElderTaskPriority.CRITICAL
            else:
                return max_priority
        
        # 重要キーワードチェック
        if any(word in text.lower() for word in ['重要', 'important', 'high priority']):
            if max_priority.value >= ElderTaskPriority.HIGH.value:
                return ElderTaskPriority.HIGH
            else:
                return max_priority
        
        # デフォルトはMEDIUM（権限内で）
        if max_priority.value >= ElderTaskPriority.MEDIUM.value:
            return ElderTaskPriority.MEDIUM
        
        return max_priority
    
    async def _publish_to_elder_task_queue(self, task_data: Dict, 
                                         elder_context: ElderTaskContext):
        """Elder階層対応タスクキューへの送信"""
        try:
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
            
            # Elder階層対応キュー宣言
            channel.queue_declare(
                queue=self.output_queue,
                durable=True,
                arguments={'x-max-priority': 10}
            )
            
            # 優先度設定
            priority_value = task_data['elder_context']['priority']
            priority_map = {
                'critical': 10,
                'high': 7,
                'medium': 5,
                'low': 3
            }
            
            channel.basic_publish(
                exchange='',
                routing_key=self.output_queue,
                body=json.dumps(task_data),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    priority=priority_map.get(priority_value, 5)
                )
            )
            
            channel.close()
            connection.close()
            
            self.logger.info(
                f"{ELDER_SLACK_EMOJI['success']} Task published to Elder queue with priority: {priority_value}"
            )
            
        except Exception as e:
            self.logger.error(f"{ELDER_SLACK_EMOJI['error']} Queue publish error: {str(e)}")
    
    def _mark_as_processed_with_elder(self, message: Dict, channel_id: str,
                                     elder_context: ElderTaskContext,
                                     priority: ElderTaskPriority):
        """Elder情報付きで処理済みとして記録"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR IGNORE INTO elder_processed_messages 
                (message_ts, channel_id, user_id, text, elder_role, task_priority, security_check)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                message['ts'],
                channel_id,
                message.get('user', ''),
                message.get('text', ''),
                elder_context.user.elder_role.value,
                priority.value,
                'passed'
            ))
            conn.commit()
    
    async def _send_elder_reaction(self, message: Dict, channel_id: str,
                                 elder_context: ElderTaskContext):
        """Elder階層に応じたリアクション追加"""
        try:
            # Elder階層に応じた絵文字選択
            reaction_map = {
                ElderRole.GRAND_ELDER: 'crown',      # 👑
                ElderRole.CLAUDE_ELDER: 'robot_face', # 🤖
                ElderRole.SAGE: 'mage',              # 🧙
                ElderRole.SERVANT: 'eyes'            # 👀
            }
            
            reaction = reaction_map.get(elder_context.user.elder_role, 'eyes')
            
            url = 'https://slack.com/api/reactions.add'
            data = {
                'channel': channel_id,
                'timestamp': message['ts'],
                'name': reaction
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 200:
                self.logger.debug(f"Elder reaction added: {reaction}")
            
        except Exception as e:
            self.logger.debug(f"Reaction error (non-critical): {e}")
    
    async def get_polling_statistics(self) -> Dict[str, Any]:
        """ポーリング統計情報取得"""
        with sqlite3.connect(self.db_path) as conn:
            # Elder階層別処理統計
            cursor = conn.execute('''
                SELECT elder_role, COUNT(*) as count 
                FROM elder_processed_messages 
                WHERE processed_at > datetime('now', '-24 hours')
                GROUP BY elder_role
            ''')
            elder_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 優先度別統計
            cursor = conn.execute('''
                SELECT task_priority, COUNT(*) as count 
                FROM elder_processed_messages 
                WHERE processed_at > datetime('now', '-24 hours')
                GROUP BY task_priority
            ''')
            priority_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 全体統計
            cursor = conn.execute('''
                SELECT COUNT(*) FROM elder_processed_messages 
                WHERE processed_at > datetime('now', '-24 hours')
            ''')
            total_24h = cursor.fetchone()[0]
        
        return {
            'total_messages_24h': total_24h,
            'elder_distribution': elder_stats,
            'priority_distribution': priority_stats,
            'bot_user_id': self.bot_user_id,
            'monitoring_channels': sum(len(ch) for ch in self.elder_channels.values())
        }
    
    @elder_worker_required(ElderRole.CLAUDE_ELDER)
    async def update_channel_configuration(self, elder_context: ElderTaskContext,
                                         config_data: Dict[str, Any]) -> Dict[str, Any]:
        """チャンネル設定の更新（Claude Elder以上）"""
        self.audit_logger.log_elder_action(
            elder_context,
            "channel_config_update",
            f"Updating channel configuration: {config_data}"
        )
        
        # チャンネル設定更新ロジック
        # 実装省略
        
        return {
            'status': 'updated',
            'updated_by': elder_context.user.username,
            'timestamp': datetime.now().isoformat()
        }

    def stop(self):
        """ワーカー停止処理"""
        self.should_stop = True
        self.logger.info(f"{ELDER_SLACK_EMOJI['stop']} Elder Slack Polling Worker停止フラグ設定")


# Elder階層ファクトリー関数
def create_elder_slack_polling_worker(auth_provider: Optional[UnifiedAuthProvider] = None) -> ElderSlackPollingWorker:
    """Elder階層Slackポーリングワーカー作成"""
    return ElderSlackPollingWorker(auth_provider=auth_provider)


# デモ実行関数
async def demo_elder_slack_polling():
    """Elder階層Slackポーリングワーカーのデモ実行"""
    from libs.unified_auth_provider import create_demo_auth_system, AuthRequest
    import asyncio
    
    print(f"{ELDER_SLACK_EMOJI['start']} Elder Slack Polling Worker Demo Starting...")
    
    # デモ認証システム
    auth = create_demo_auth_system()
    
    # Slackポーリングワーカー作成
    worker = create_elder_slack_polling_worker(auth_provider=auth)
    
    # 賢者として認証（Slackモニタリング権限）
    auth_request = AuthRequest(username="task_sage", password="task_password")
    result, session, user = auth.authenticate(auth_request)
    
    if result.value == "success":
        print(f"{ELDER_SLACK_EMOJI['success']} Authenticated as Task Sage: {user.username}")
        
        # ポーリングコンテキスト作成
        context = worker.create_elder_context(
            user=user,
            session=session,
            task_id="demo_slack_polling",
            priority=ElderTaskPriority.MEDIUM
        )
        
        # 統計情報表示
        print(f"\n{ELDER_SLACK_EMOJI['polling']} Polling Configuration:")
        print(f"  Elder Role: {user.elder_role.value}")
        print(f"  Channels: {worker.elder_channels[user.elder_role]}")
        permissions = worker.elder_permissions[user.elder_role]
        print(f"  Max Priority: {permissions['max_message_priority'].value}")
        print(f"  Private Channels: {'Yes' if permissions['can_access_private_channels'] else 'No'}")
        
        # デモメッセージ処理
        demo_message = {
            'ts': str(time.time()),
            'text': '<@BOT_ID> Create a new worker for data processing',
            'user': 'U123456'
        }
        
        print(f"\n{ELDER_SLACK_EMOJI['slack']} Processing demo message...")
        await worker._process_message_with_elder_auth(
            demo_message, 
            'C0946R76UU8',
            context
        )
        
        # 統計情報取得
        stats = await worker.get_polling_statistics()
        print(f"\n{ELDER_SLACK_EMOJI['info']} Polling Statistics:")
        print(f"  24h Messages: {stats['total_messages_24h']}")
        print(f"  Elder Distribution: {stats['elder_distribution']}")
        print(f"  Priority Distribution: {stats['priority_distribution']}")
        
    else:
        print(f"{ELDER_SLACK_EMOJI['error']} Authentication failed: {result}")


if __name__ == "__main__":
    # デモ実行
    import asyncio
    asyncio.run(demo_elder_slack_polling())