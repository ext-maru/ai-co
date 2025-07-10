#!/usr/bin/env python3
"""
Slack通知機能 v2.0 - 進化したElders Guildに最適化
"""

import json
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class SlackNotifierV2:
    """進化したSlack通知クラス"""
    
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = Path("/root/ai_co/config/slack.conf")
        
        self.config = self._load_config(config_file)
        self.enabled = self.config.get('ENABLE_SLACK', 'false').lower() == 'true'
        self.webhook_url = self.config.get('SLACK_WEBHOOK_URL')
        
        # タスクタイプの絵文字マッピング
        self.task_type_emojis = {
            'analysis': '🔍',
            'code': '💻',
            'test': '🧪',
            'web_scraping': '🌐',
            'report_generation': '📊',
            'fix': '🔧',
            'general': '📋',
            'dialog': '💬',
            'evolution': '🧬'
        }
        
        # 優先度の表示
        self.priority_display = {
            1: '⭐ (低)',
            2: '⭐⭐ (中)',
            3: '⭐⭐⭐ (高)',
            4: '🔥 (緊急)',
            5: '🚨 (最優先)'
        }
        
    def _load_config(self, config_file):
        """設定ファイル読み込み"""
        config = {}
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"')
        except Exception as e:
            logger.error(f"Slack設定読み込み失敗: {e}")
        
        return config
    
    def _format_duration(self, seconds: float) -> str:
        """秒数を読みやすい形式に変換"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}分{secs}秒"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}時間{minutes}分"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """ファイルサイズを読みやすい形式に変換"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"
    
    def _truncate_text(self, text: str, max_length: int = 200) -> str:
        """テキストを適切な長さに切り詰め"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def send_enhanced_task_notification(self, task_data: Dict[str, Any]) -> bool:
        """拡張版タスク通知を送信"""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            # データ検証
            if not task_data or not isinstance(task_data, dict):
                logger.error("無効なタスクデータが渡されました")
                return False
            
            # データの抽出
            task_id = task_data.get('task_id', 'N/A')
            task_type = task_data.get('task_type', 'general')
            status = task_data.get('status', 'unknown')
            worker = task_data.get('worker', 'unknown')
            priority = task_data.get('priority', 2)
            
            # タイミング情報の安全な取得
            start_time = task_data.get('start_time')
            end_time = task_data.get('end_time')
            if not end_time:
                end_time = datetime.now()
            elif isinstance(end_time, str):
                try:
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                except ValueError:
                    end_time = datetime.now()
            
            queue_time = task_data.get('queue_time', 0)
            execution_time = task_data.get('execution_time', 0)
            
            # AI処理情報
            rag_applied = task_data.get('rag_applied', False)
            rag_count = task_data.get('rag_reference_count', 0)
            evolution_applied = task_data.get('evolution_applied', False)
            evolution_files = task_data.get('evolution_files', [])
            model_used = task_data.get('model', 'default')
            
            # コンテンツ
            prompt = task_data.get('prompt', '')
            response = task_data.get('response', '')
            error_message = task_data.get('error')
            
            # ファイル情報
            output_file = task_data.get('output_file')
            file_size = 0
            if output_file and os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
            
            # 絵文字とステータス
            status_emoji = '✅' if status == 'completed' else '❌'
            task_emoji = self.task_type_emojis.get(task_type, '📋')
            priority_str = self.priority_display.get(priority, '⭐⭐')
            
            # 時刻表示の安全な処理
            completion_time = end_time.strftime('%H:%M:%S') if isinstance(end_time, datetime) else 'N/A'
            completion_date = end_time.strftime('%Y-%m-%d') if isinstance(end_time, datetime) else 'N/A'
            
            # メッセージの構築
            divider = "━" * 40
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{status_emoji} Elders Guild タスク完了通知"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*📋 タスクID*\n`{task_id}`"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*{task_emoji} タイプ*\n{task_type}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*👷 ワーカー*\n{worker}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*優先度*\n{priority_str}"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*⏱️ 実行時間*\n{self._format_duration(execution_time)}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*⏳ 待機時間*\n{self._format_duration(queue_time)}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*🕐 完了時刻*\n{completion_time}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*📅 日付*\n{completion_date}"
                        }
                    ]
                }
            ]
            
            # AI処理情報セクション
            ai_info_text = f"*🧠 RAG適用:* {'✅' if rag_applied else '❌'}"
            if rag_applied:
                ai_info_text += f" ({rag_count}件の参照)"
            
            if evolution_applied and evolution_files:
                evolution_text = f"\n*🧬 自己進化:* ✅ ({len(evolution_files)}ファイル更新)"
            else:
                evolution_text = ""
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{ai_info_text}{evolution_text}\n*🤖 モデル:* {model_used}"
                }
            })
            
            # タスク内容セクション
            blocks.append({
                "type": "divider"
            })
            
            # プロンプトセクション
            prompt_preview = self._truncate_text(prompt, 300)
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📝 タスク内容*\n```{prompt_preview}```"
                }
            })
            
            # 応答またはエラー
            if status == 'completed':
                response_preview = self._truncate_text(response, 500)
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*💬 応答サマリー*\n{response_preview}"
                    }
                })
            elif error_message:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*❌ エラー*\n```{error_message}```"
                    }
                })
            
            # ファイル情報
            if output_file:
                file_info = f"*📁 出力ファイル*\n`{output_file}`"
                if file_size > 0:
                    file_info += f" ({self._format_file_size(file_size)})"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": file_info
                    }
                })
            
            # フッター
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Elders Guild RAG System | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            })
            
            # メッセージ送信
            message = {
                "blocks": blocks,
                "text": f"{status_emoji} タスク {task_id} が完了しました"  # フォールバック
            }
            
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"拡張版Slack通知送信成功: {task_id}")
                return True
            else:
                logger.error(f"Slack送信失敗: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Slack通知送信エラー: {e}")
            return False
    
    def send_simple_notification(self, message: str) -> bool:
        """シンプルなメッセージ送信（互換性維持）"""
        if not self.enabled or not self.webhook_url:
            return False
            
        try:
            payload = {
                'text': message,
                'username': self.config.get('SLACK_USERNAME', 'AI-Company-Bot'),
                'icon_emoji': self.config.get('SLACK_ICON', ':robot_face:')
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"シンプル通知送信エラー: {e}")
            return False