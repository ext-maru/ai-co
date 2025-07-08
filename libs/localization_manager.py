#!/usr/bin/env python3
"""
LocalizationManager - 多言語対応管理システム

言語設定とメッセージの多言語化を管理する
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime
import pytz

from core.config import get_config


class LocalizationManager:
    """多言語対応管理クラス"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Args:
            config_dir: 設定ディレクトリ（未指定時はデフォルト）
        """
        self.config = get_config()
        self.config_dir = config_dir or self.config.paths['config']
        self.locales_dir = self.config_dir / 'locales'
        
        # 言語設定
        self.current_language = self.config.language.default_language
        self.supported_languages = self.config.language.supported_languages
        
        # メッセージ辞書
        self._messages: Dict[str, Dict[str, str]] = {}
        
        # 言語ファイルの読み込み
        self._load_locale_files()
    
    def _load_locale_files(self):
        """言語ファイルの読み込み"""
        if not self.locales_dir.exists():
            self.locales_dir.mkdir(parents=True, exist_ok=True)
            # デフォルト言語ファイルを作成
            self._create_default_locale_files()
        
        for lang in self.supported_languages:
            locale_file = self.locales_dir / f'{lang}.json'
            if locale_file.exists():
                try:
                    with open(locale_file, 'r', encoding='utf-8') as f:
                        self._messages[lang] = json.load(f)
                except Exception as e:
                    print(f"言語ファイルの読み込みエラー {lang}.json: {e}")
                    self._messages[lang] = {}
            else:
                self._messages[lang] = {}
    
    def _create_default_locale_files(self):
        """デフォルト言語ファイルの作成"""
        # 日本語メッセージ
        ja_messages = {
            "system": {
                "startup": "AI Company システムを開始しています...",
                "shutdown": "AI Company システムを終了しています...",
                "error": "エラーが発生しました",
                "success": "正常に完了しました",
                "warning": "警告",
                "info": "情報"
            },
            "worker": {
                "started": "ワーカーを開始しました",
                "stopped": "ワーカーを停止しました",
                "task_received": "タスクを受信しました",
                "task_completed": "タスクが完了しました",
                "task_failed": "タスクが失敗しました",
                "timeout": "タスクがタイムアウトしました"
            },
            "slack": {
                "notification_sent": "Slack通知を送信しました",
                "notification_failed": "Slack通知の送信に失敗しました",
                "webhook_error": "WebhookのURLが設定されていません",
                "channel_not_found": "指定されたチャンネルが見つかりません"
            },
            "config": {
                "loaded": "設定を読み込みました",
                "saved": "設定を保存しました",
                "validation_error": "設定の検証エラー",
                "file_not_found": "設定ファイルが見つかりません"
            },
            "rabbitmq": {
                "connected": "RabbitMQに接続しました",
                "disconnected": "RabbitMQから切断しました",
                "connection_failed": "RabbitMQへの接続に失敗しました",
                "queue_declared": "キューを宣言しました"
            },
            "pm": {
                "task_created": "プロジェクト管理タスクを作成しました",
                "task_assigned": "タスクを割り当てました",
                "status_updated": "ステータスを更新しました",
                "deadline_approaching": "締切が近づいています"
            }
        }
        
        # 英語メッセージ
        en_messages = {
            "system": {
                "startup": "Starting AI Company system...",
                "shutdown": "Shutting down AI Company system...",
                "error": "An error occurred",
                "success": "Completed successfully",
                "warning": "Warning",
                "info": "Information"
            },
            "worker": {
                "started": "Worker started",
                "stopped": "Worker stopped",
                "task_received": "Task received",
                "task_completed": "Task completed",
                "task_failed": "Task failed",
                "timeout": "Task timed out"
            },
            "slack": {
                "notification_sent": "Slack notification sent",
                "notification_failed": "Failed to send Slack notification",
                "webhook_error": "Webhook URL is not configured",
                "channel_not_found": "Specified channel not found"
            },
            "config": {
                "loaded": "Configuration loaded",
                "saved": "Configuration saved",
                "validation_error": "Configuration validation error",
                "file_not_found": "Configuration file not found"
            },
            "rabbitmq": {
                "connected": "Connected to RabbitMQ",
                "disconnected": "Disconnected from RabbitMQ",
                "connection_failed": "Failed to connect to RabbitMQ",
                "queue_declared": "Queue declared"
            },
            "pm": {
                "task_created": "Project management task created",
                "task_assigned": "Task assigned",
                "status_updated": "Status updated",
                "deadline_approaching": "Deadline is approaching"
            }
        }
        
        # ファイルに保存
        for lang, messages in [('ja', ja_messages), ('en', en_messages)]:
            locale_file = self.locales_dir / f'{lang}.json'
            with open(locale_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
    
    def set_language(self, language: str) -> bool:
        """
        言語を設定
        
        Args:
            language: 言語コード（ja, en等）
            
        Returns:
            設定成功フラグ
        """
        if language not in self.supported_languages:
            return False
        
        self.current_language = language
        return True
    
    def get_message(self, key_path: str, **kwargs) -> str:
        """
        メッセージの取得
        
        Args:
            key_path: メッセージキーパス（例: "system.startup"）
            **kwargs: フォーマット用の引数
            
        Returns:
            ローカライズされたメッセージ
        """
        # 現在の言語でメッセージを取得
        message = self._get_nested_message(self.current_language, key_path)
        
        # 見つからない場合はデフォルト言語（日本語）で試行
        if not message and self.current_language != 'ja':
            message = self._get_nested_message('ja', key_path)
        
        # それでも見つからない場合は英語で試行
        if not message and self.current_language != 'en':
            message = self._get_nested_message('en', key_path)
        
        # 最終的に見つからない場合はキーをそのまま返す
        if not message:
            message = key_path
        
        # フォーマット処理
        try:
            if kwargs:
                message = message.format(**kwargs)
        except Exception:
            pass  # フォーマットエラーの場合は元のメッセージを返す
        
        return message
    
    def _get_nested_message(self, language: str, key_path: str) -> Optional[str]:
        """ネストされたメッセージキーから値を取得"""
        if language not in self._messages:
            return None
        
        keys = key_path.split('.')
        current = self._messages[language]
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    def format_datetime(self, dt: datetime, format_type: str = 'full') -> str:
        """
        日時のフォーマット
        
        Args:
            dt: 日時オブジェクト
            format_type: フォーマットタイプ（full, date, time）
            
        Returns:
            フォーマットされた日時文字列
        """
        # タイムゾーンの設定
        tz = pytz.timezone(self.config.language.timezone)
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        else:
            dt = dt.astimezone(tz)
        
        # フォーマットの選択
        if format_type == 'date':
            format_str = self.config.language.date_format
        elif format_type == 'time':
            format_str = self.config.language.time_format
        else:  # full
            format_str = f"{self.config.language.date_format} {self.config.language.time_format}"
        
        return dt.strftime(format_str)
    
    def add_message(self, language: str, key_path: str, message: str) -> bool:
        """
        メッセージの追加
        
        Args:
            language: 言語コード
            key_path: メッセージキーパス
            message: メッセージ内容
            
        Returns:
            追加成功フラグ
        """
        if language not in self.supported_languages:
            return False
        
        if language not in self._messages:
            self._messages[language] = {}
        
        # ネストされた辞書構造を作成
        keys = key_path.split('.')
        current = self._messages[language]
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = message
        return True
    
    def save_locale_file(self, language: str) -> bool:
        """
        言語ファイルの保存
        
        Args:
            language: 言語コード
            
        Returns:
            保存成功フラグ
        """
        if language not in self._messages:
            return False
        
        locale_file = self.locales_dir / f'{language}.json'
        
        try:
            with open(locale_file, 'w', encoding='utf-8') as f:
                json.dump(self._messages[language], f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def get_supported_languages(self) -> list:
        """サポートされている言語のリストを取得"""
        return self.supported_languages.copy()
    
    def get_current_language(self) -> str:
        """現在の言語を取得"""
        return self.current_language


# グローバルインスタンス（シングルトン）
_global_localization: Optional[LocalizationManager] = None


def get_localization() -> LocalizationManager:
    """グローバルローカライゼーションインスタンスの取得"""
    global _global_localization
    
    if _global_localization is None:
        _global_localization = LocalizationManager()
    
    return _global_localization


def t(key_path: str, **kwargs) -> str:
    """
    メッセージの翻訳（ショートカット関数）
    
    Args:
        key_path: メッセージキーパス
        **kwargs: フォーマット用の引数
        
    Returns:
        翻訳されたメッセージ
    """
    return get_localization().get_message(key_path, **kwargs)


def set_language(language: str) -> bool:
    """
    言語設定（ショートカット関数）
    
    Args:
        language: 言語コード
        
    Returns:
        設定成功フラグ
    """
    return get_localization().set_language(language)


if __name__ == "__main__":
    # テスト実行
    loc = get_localization()
    
    print("多言語対応テスト:")
    print(f"現在の言語: {loc.get_current_language()}")
    print(f"サポート言語: {loc.get_supported_languages()}")
    
    # 日本語メッセージのテスト
    print(f"\n日本語: {t('system.startup')}")
    print(f"日本語: {t('worker.task_completed')}")
    
    # 英語に切り替え
    set_language('en')
    print(f"\n英語: {t('system.startup')}")
    print(f"英語: {t('worker.task_completed')}")
    
    # 日時フォーマットのテスト
    set_language('ja')
    now = datetime.now()
    print(f"\n日時フォーマット: {loc.format_datetime(now)}")