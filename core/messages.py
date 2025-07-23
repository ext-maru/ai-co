#!/usr/bin/env python3
"""
Elders Guild メッセージ管理システム
言語切り替え可能なメッセージ定義
"""

import json
from pathlib import Path
from typing import Any, Dict


class Messages:
    """多言語対応メッセージ管理"""

    def __init__(self, lang: str = "ja"):
        """初期化メソッド"""
        self.lang = lang
        self._messages = self._load_messages()

    def _load_messages(self) -> Dict[str, Dict[str, str]]:
        """メッセージ定義"""
        return {
            "ja": {
                # ワーカー共通
                "worker_started": "ワーカー開始: {worker_type} (PID: {pid})",
                "worker_stopped": "ワーカー停止: {worker_type}",
                "worker_error": "ワーカーエラー: {error}",
                # タスク処理
                "task_started": "タスク開始: {task_id} (種別: {task_type})",
                "task_completed": "タスク完了: {task_id} | 処理時間: {duration:.2f}秒 | ファイル数: {files}",
                "task_failed": "タスク失敗: {task_id} - {error_type}: {error_msg}",
                "task_processing": "タスク処理中: {task_id}",
                # ファイル操作
                "file_created": "ファイル作成: {path}",
                "file_updated": "ファイル更新: {path}",
                "file_deployed": "ファイル配置: {path}",
                "file_error": "ファイルエラー: {path} - {error}",
                # Git操作
                "git_commit": "Git コミット: {message}",
                "git_push": "Git プッシュ完了: {branch}",
                "git_merge": "Git マージ: {source} → {target}",
                # Slack通知
                "slack_task_complete": "✅ タスク完了\nID: {task_id}\n種別: {task_type}\n処理時間: {duration:.2f}秒",
                "slack_task_failed": "❌ タスク失敗\nID: {task_id}\nエラー: {error}",
                "slack_system_info": "📊 システム情報\n{info}",
                # エラーメッセージ
                "connection_error": "接続エラー: {service}",
                "timeout_error": "タイムアウト: {operation} ({timeout}秒)",
                "validation_error": "検証エラー: {field} - {reason}",
                "permission_error": "権限エラー: {path}",
                # ステータス
                "status_running": "実行中",
                "status_completed": "完了",
                "status_failed": "失敗",
                "status_pending": "待機中",
                "status_processing": "処理中",
                # 汎用
                "success": "成功",
                "failed": "失敗",
                "error": "エラー",
                "warning": "警告",
                "info": "情報",
                "starting": "開始中...",
                "stopping": "停止中...",
                "completed": "完了しました",
                "canceled": "キャンセルされました",
            },
            "en": {
                # 英語版（オプション）
                "worker_started": "Worker started: {worker_type} (PID: {pid})",
                "worker_stopped": "Worker stopped: {worker_type}",
                "task_started": "Task started: {task_id} (type: {task_type})",
                "task_completed": "Task completed: {task_id} | Duration: {duration:.2f}s | Files: {files}",
                "task_failed": "Task failed: {task_id} - {error_type}: {error_msg}",
                # ... 省略
            },
        }

    def get(self, key: str, **kwargs) -> str:
        """メッセージ取得"""
        if key not in self._messages.get(self.lang, {}):
            # フォールバック: キーをそのまま返す
            return key

        message = self._messages[self.lang][key]

        # パラメータ置換
        if kwargs:
            try:
                return message.format(**kwargs)
            except:
                return message

        return message

    def set_lang(self, lang: str):
        """言語切り替え"""
        if lang in self._messages:
            self.lang = lang

    @classmethod
    def from_config(cls):
        """設定から言語を読み込んで初期化"""
        try:
            config_path = Path(__file__).parent.parent / "config" / "system.json"
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
                    lang = config.get("language", "ja")
                    return cls(lang)
        except:
            pass
        return cls("ja")  # デフォルト日本語


# グローバルインスタンス
messages = Messages.from_config()


# 便利な関数
def msg(key: str, **kwargs) -> str:
    """メッセージ取得のショートカット"""
    return messages.get(key, **kwargs)
