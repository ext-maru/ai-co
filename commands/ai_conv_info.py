#!/usr/bin/env python3
"""
会話詳細
"""
import sys
import argparse
import json
import sqlite3
from pathlib import Path
from datetime import datetime
sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult

class AIConvInfoCommand(BaseCommand):
    """会話詳細"""
    
    def __init__(self):
        super().__init__(
            name="ai-conv-info",
            description="会話詳細",
            version="1.0.0"
        )
    
    def add_arguments(self, parser: argparse.ArgumentParser):
        """引数定義"""
        parser.add_argument(
            '--conversation-id', '-c',
            type=str,
            required=True,
            help='会話ID'
        )
        parser.add_argument(
            '--format', '-f',
            choices=['text', 'json', 'detailed'],
            default='text',
            help='表示形式'
        )
        parser.add_argument(
            '--include-messages', '-m',
            action='store_true',
            help='メッセージ内容を含める'
        )
        parser.add_argument(
            '--limit', '-l',
            type=int,
            default=50,
            help='表示するメッセージ数の上限'
        )
    
    def execute(self, args) -> CommandResult:
        """実行"""
        try:
            # データベースから会話情報を取得
            conv_info = self._get_conversation_info(args.conversation_id)
            if not conv_info:
                return CommandResult(
                    success=False,
                    message=f"会話ID '{args.conversation_id}' が見つかりません"
                )
            
            # メッセージ情報を取得（必要な場合）
            messages = []
            if args.include_messages:
                messages = self._get_conversation_messages(args.conversation_id, args.limit)
            
            # 形式に応じた出力
            if args.format == 'json':
                return self._format_json(conv_info, messages)
            elif args.format == 'detailed':
                return self._format_detailed(conv_info, messages)
            else:
                return self._format_text(conv_info, messages)
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"会話詳細取得エラー: {str(e)}"
            )
    
    def _get_conversation_info(self, conversation_id: str) -> dict:
        """会話基本情報を取得"""
        db_path = Path('/home/aicompany/ai_co/data/conversation.db')
        if not db_path.exists():
            # PostgreSQL接続を試行
            return self._get_conversation_from_postgres(conversation_id)
        
        # SQLite接続
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM conversations WHERE conversation_id = ?",
                    (conversation_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception:
            return None
    
    def _get_conversation_from_postgres(self, conversation_id: str) -> dict:
        """PostgreSQLから会話情報を取得"""
        try:
            from libs.postgresql_conversation_db import PostgreSQLConversationDB
            db = PostgreSQLConversationDB()
            return db.get_conversation(conversation_id)
        except ImportError:
            return None
    
    def _get_conversation_messages(self, conversation_id: str, limit: int) -> list:
        """会話メッセージを取得"""
        db_path = Path('/home/aicompany/ai_co/data/conversation.db')
        if not db_path.exists():
            return self._get_messages_from_postgres(conversation_id, limit)
        
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """SELECT * FROM messages 
                       WHERE conversation_id = ? 
                       ORDER BY timestamp DESC LIMIT ?""",
                    (conversation_id, limit)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def _get_messages_from_postgres(self, conversation_id: str, limit: int) -> list:
        """PostgreSQLからメッセージを取得"""
        try:
            from libs.postgresql_conversation_db import PostgreSQLConversationDB
            db = PostgreSQLConversationDB()
            return db.get_messages(conversation_id, limit)
        except ImportError:
            return []
    
    def _format_text(self, conv_info: dict, messages: list) -> CommandResult:
        """テキスト形式で出力"""
        lines = []
        lines.append(f"会話ID: {conv_info.get('conversation_id', 'N/A')}")
        lines.append(f"タイトル: {conv_info.get('title', 'N/A')}")
        lines.append(f"作成日時: {conv_info.get('created_at', 'N/A')}")
        lines.append(f"最終更新: {conv_info.get('updated_at', 'N/A')}")
        lines.append(f"メッセージ数: {conv_info.get('message_count', len(messages))}")
        
        if conv_info.get('status'):
            lines.append(f"ステータス: {conv_info['status']}")
        
        if messages:
            lines.append("\n--- メッセージ ---")
            for i, msg in enumerate(messages[:10], 1):
                lines.append(f"{i}. [{msg.get('timestamp', 'N/A')}] {msg.get('role', 'unknown')}: {msg.get('content', '')[:100]}...")
        
        return CommandResult(
            success=True,
            message='\n'.join(lines)
        )
    
    def _format_json(self, conv_info: dict, messages: list) -> CommandResult:
        """JSON形式で出力"""
        data = {
            'conversation': conv_info,
            'messages': messages
        }
        return CommandResult(
            success=True,
            message=json.dumps(data, indent=2, ensure_ascii=False, default=str)
        )
    
    def _format_detailed(self, conv_info: dict, messages: list) -> CommandResult:
        """詳細形式で出力"""
        lines = []
        lines.append("=" * 50)
        lines.append(f"  会話詳細情報")
        lines.append("=" * 50)
        lines.append(f"会話ID: {conv_info.get('conversation_id', 'N/A')}")
        lines.append(f"タイトル: {conv_info.get('title', 'N/A')}")
        lines.append(f"作成日時: {conv_info.get('created_at', 'N/A')}")
        lines.append(f"最終更新: {conv_info.get('updated_at', 'N/A')}")
        lines.append(f"参加者: {conv_info.get('participants', 'N/A')}")
        lines.append(f"メッセージ数: {conv_info.get('message_count', len(messages))}")
        lines.append(f"ステータス: {conv_info.get('status', 'active')}")
        
        if conv_info.get('tags'):
            lines.append(f"タグ: {', '.join(conv_info['tags'])}")
        
        if messages:
            lines.append("\n" + "=" * 50)
            lines.append("  メッセージ履歴")
            lines.append("=" * 50)
            for i, msg in enumerate(messages, 1):
                lines.append(f"\n[{i}] {msg.get('timestamp', 'N/A')}")
                lines.append(f"送信者: {msg.get('role', 'unknown')}")
                lines.append(f"内容: {msg.get('content', '')}")
                if msg.get('metadata'):
                    lines.append(f"メタデータ: {msg['metadata']}")
                lines.append("-" * 30)
        
        return CommandResult(
            success=True,
            message='\n'.join(lines)
        )

def main():
    command = AIConvInfoCommand()
    sys.exit(command.run())

if __name__ == "__main__":
    main()
