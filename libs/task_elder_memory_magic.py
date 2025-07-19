#!/usr/bin/env python3
"""
タスクエルダー記憶魔法システム
セッション情報を2日間保持し、会話の継続を可能にする
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.knowledge_base_manager import KnowledgeBaseManager
from libs.task_history_db import TaskHistoryDB


class TaskElderMemoryMagic:
    """タスクエルダーによるセッション記憶魔法"""

    def __init__(self):
        self.retention_days = 2  # 2日間保持
        self.memory_dir = PROJECT_ROOT / "knowledge_base" / "task_memories"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.task_db = TaskHistoryDB()
        self.kb_manager = KnowledgeBaseManager()

    def create_session_id(self, user_context: str = "") -> str:
        """セッションIDを生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if user_context:
            # ユーザーコンテキストからハッシュ生成
            context_hash = hashlib.md5(user_context.encode()).hexdigest()[:8]
            return f"sess_{timestamp}_{context_hash}"
        return f"sess_{timestamp}"

    def save_memory(self, session_data: Dict[str, Any]) -> str:
        """セッションメモリを保存"""
        session_id = session_data.get("session_id") or self.create_session_id()

        memory_snapshot = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "retention_until": (
                datetime.now() + timedelta(days=self.retention_days)
            ).isoformat(),
            "project": session_data.get("project", {}),
            "todos": session_data.get("todos", []),
            "key_decisions": session_data.get("key_decisions", []),
            "context_summary": session_data.get("context_summary", ""),
            "last_messages_summary": session_data.get("last_messages_summary", []),
            "working_directory": session_data.get("working_directory", os.getcwd()),
            "created_files": session_data.get("created_files", []),
            "magic_type": "task_elder_memory",
            "version": "1.0",
        }

        # JSONファイルとして保存
        memory_file = self.memory_dir / f"{session_id}.json"
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memory_snapshot, f, ensure_ascii=False, indent=2)

        print(f"🔮 記憶魔法発動: セッション {session_id} を保存しました")
        print(f"📅 保持期限: {memory_snapshot['retention_until']}")

        return session_id

    def recall_memory(self, trigger: str) -> Optional[Dict[str, Any]]:
        """トリガーフレーズから記憶を呼び出し"""
        # クリーンアップ（期限切れメモリ削除）
        self._cleanup_expired_memories()

        # トリガー解析
        if "前回の続き" in trigger or "セッション再開" in trigger:
            # 最新のセッションを取得
            return self._get_latest_memory()

        elif "プロジェクト" in trigger:
            # プロジェクト名で検索
            project_name = self._extract_project_name(trigger)
            return self._search_by_project(project_name)

        elif "sess_" in trigger:
            # セッションIDで直接検索
            session_id = self._extract_session_id(trigger)
            return self._load_memory_by_id(session_id)

        else:
            # 最新のメモリを返す
            return self._get_latest_memory()

    def _get_latest_memory(self) -> Optional[Dict[str, Any]]:
        """最新の有効なメモリを取得"""
        memory_files = sorted(self.memory_dir.glob("sess_*.json"), reverse=True)

        for memory_file in memory_files:
            memory = self._load_memory_file(memory_file)
            if memory and self._is_memory_valid(memory):
                return memory

        return None

    def _search_by_project(self, project_name: str) -> Optional[Dict[str, Any]]:
        """プロジェクト名でメモリを検索"""
        memory_files = sorted(self.memory_dir.glob("sess_*.json"), reverse=True)

        for memory_file in memory_files:
            memory = self._load_memory_file(memory_file)
            if memory and self._is_memory_valid(memory):
                if (
                    project_name.lower()
                    in memory.get("project", {}).get("name", "").lower()
                ):
                    return memory

        return None

    def _load_memory_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションIDでメモリを読み込み"""
        memory_file = self.memory_dir / f"{session_id}.json"
        if memory_file.exists():
            memory = self._load_memory_file(memory_file)
            if memory and self._is_memory_valid(memory):
                return memory
        return None

    def _load_memory_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """メモリファイルを読み込み"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ メモリ読み込みエラー: {e}")
            return None

    def _is_memory_valid(self, memory: Dict[str, Any]) -> bool:
        """メモリが有効期限内かチェック"""
        retention_until = datetime.fromisoformat(memory.get("retention_until", ""))
        return datetime.now() < retention_until

    def _cleanup_expired_memories(self):
        """期限切れメモリを削除"""
        memory_files = self.memory_dir.glob("sess_*.json")
        deleted_count = 0

        for memory_file in memory_files:
            memory = self._load_memory_file(memory_file)
            if memory and not self._is_memory_valid(memory):
                memory_file.unlink()
                deleted_count += 1

        if deleted_count > 0:
            print(f"🧹 期限切れメモリを {deleted_count} 件削除しました")

    def _extract_project_name(self, trigger: str) -> str:
        """トリガーからプロジェクト名を抽出"""
        # "プロジェクトA2Aの続き" -> "A2A"
        import re

        match = re.search(r"プロジェクト(.+?)の", trigger)
        if match:
            return match.group(1)
        return ""

    def _extract_session_id(self, trigger: str) -> str:
        """トリガーからセッションIDを抽出"""
        import re

        match = re.search(r"(sess_\d{8}_\d{6}(?:_\w{8})?)", trigger)
        if match:
            return match.group(1)
        return ""

    def display_memory(self, memory: Dict[str, Any]):
        """メモリ内容を表示"""
        print("\n🔮 タスクエルダーの記憶魔法 - セッション復元")
        print("=" * 60)
        print(f"セッションID: {memory['session_id']}")
        print(f"保存日時: {memory['timestamp']}")
        print(f"保持期限: {memory['retention_until']}")

        if memory.get("project"):
            print(f"\n📋 プロジェクト: {memory['project'].get('name', '不明')}")
            print(f"   フェーズ: {memory['project'].get('phase', '不明')}")
            print(f"   状態: {memory['project'].get('status', '不明')}")

        if memory.get("todos"):
            print("\n✅ Todo状態:")
            for todo in memory["todos"]:
                status_icon = "✅" if todo["status"] == "completed" else "🔄"
                print(f"   {status_icon} {todo['content']}")

        if memory.get("key_decisions"):
            print("\n🎯 重要な決定事項:")
            for decision in memory["key_decisions"]:
                print(f"   • {decision}")

        if memory.get("context_summary"):
            print(f"\n📝 文脈サマリー: {memory['context_summary']}")

        if memory.get("last_messages_summary"):
            print("\n💬 最近の会話:")
            for msg in memory["last_messages_summary"][-3:]:
                print(f"   • {msg}")

        print("=" * 60)
        print("✨ 記憶の復元が完了しました！続きから作業を再開できます。")


# 便利な関数
def save_current_session(
    project_name: str,
    todos: List[Dict],
    key_decisions: List[str],
    context: str,
    messages: List[str],
) -> str:
    """現在のセッションを保存する便利関数"""
    magic = TaskElderMemoryMagic()

    session_data = {
        "project": {"name": project_name, "phase": "実装中", "status": "in_progress"},
        "todos": todos,
        "key_decisions": key_decisions,
        "context_summary": context,
        "last_messages_summary": messages,
        "working_directory": os.getcwd(),
    }

    return magic.save_memory(session_data)


def recall_session(trigger: str = "前回の続きから") -> Optional[Dict[str, Any]]:
    """セッションを復元する便利関数"""
    magic = TaskElderMemoryMagic()
    memory = magic.recall_memory(trigger)

    if memory:
        magic.display_memory(memory)
        return memory
    else:
        print("⚠️ 復元可能なセッションが見つかりませんでした")
        return None


if __name__ == "__main__":
    # テスト実行
    print("🧪 タスクエルダー記憶魔法のテスト")

    # サンプルセッション保存
    session_id = save_current_session(
        project_name="プロジェクトA2A",
        todos=[
            {"id": "memory-magic-impl-4", "content": "記憶魔法実装", "status": "in_progress"},
            {"id": "project-a2a-1", "content": "A2A計画立案", "status": "pending"},
        ],
        key_decisions=["タスクエルダーが記憶魔法を担当", "2日間（48時間）の保持期間", "ミニマム保持レベルを採用"],
        context="グランドエルダーmaruとプロジェクトA2Aについて議論中",
        messages=["記憶魔法を先に実装することに決定", "保持期間を2日間に設定"],
    )

    print(f"\n✅ テストセッション保存完了: {session_id}")

    # セッション復元テスト
    print("\n📖 セッション復元テスト...")
    recall_session("前回の続きから")
