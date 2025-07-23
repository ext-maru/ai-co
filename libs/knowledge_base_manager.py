#!/usr/bin/env python3
"""
Elders Guild ナレッジベース管理システム
ワーカーがナレッジベースを自動参照できるようにする
"""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class KnowledgeBaseManager:
    """ナレッジ賢者 (Knowledge Sage) - 4賢者システム統合

    Elders Guildの4賢者システムの一翼を担う、過去の英智を蓄積・継承する賢者。
    学習による知恵の進化、ファイルベース知識管理、英智の継承を行う。
    """

    def __init__(self):
        """初期化メソッド"""
        self.project_root = Path("/home/aicompany/ai_co")
        self.knowledge_dir = self.project_root / "docs"
        self.index_file = self.knowledge_dir / "KNOWLEDGE_INDEX.md"
        self.cache_file = self.project_root / "db" / "knowledge_cache.json"
        self._cache = self._load_cache()

        # 4賢者システム統合
        self.sage_type = "Knowledge Sage"
        self.wisdom_level = "knowledge_inheritance"
        self.collaboration_mode = True
        self.knowledge_evolution_active = True

        import logging

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"📚 {self.sage_type} 初期化完了 - 知識継承システムアクティブ")

    def _load_cache(self) -> Dict:
        """キャッシュをロード"""
        if self.cache_file.exists():
            with open(self.cache_file, "r") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        """キャッシュを保存"""
        self.cache_file.parent.mkdir(exist_ok=True)
        with open(self.cache_file, "w") as f:
            json.dump(self._cache, f, indent=2)

    def get_knowledge(self, topic: str) -> Optional[str]:
        """トピックに関連するナレッジを取得"""
        # キーワードマッピング
        keyword_map = {
            "test": ["TEST_FRAMEWORK_KNOWLEDGE.md", "TEST_GUIDELINES.md"],
            "テスト": ["TEST_FRAMEWORK_KNOWLEDGE.md", "TEST_GUIDELINES.md"],
            "ai_command": ["AI_COMMAND_EXECUTOR_KNOWLEDGE.md"],
            "新機能": ["AI_COMPANY_NEW_FEATURES.md"],
            "core": ["AI_COMPANY_CORE_KNOWLEDGE.md"],
            "開発": ["DEVELOPER_PERSONALITY.md", "PROJECT_INSTRUCTIONS.md"],
        }

        # トピックに関連するファイルを検索
        relevant_files = []
        for keyword, files in keyword_map.items():
            if keyword in topic.lower():
                relevant_files.extend(files)

        # ナレッジを読み込み
        knowledge_content = []
        for filename in set(relevant_files):
            filepath = self.knowledge_dir / filename
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    knowledge_content.append(f"## 📚 {filename}\n\n{content}")

        return "\n\n---\n\n".join(knowledge_content) if knowledge_content else None

    def get_all_knowledge_files(self) -> List[Dict]:
        """全てのナレッジファイル情報を取得"""
        knowledge_files = []

        for md_file in self.knowledge_dir.glob("*.md"):
            stat = md_file.stat()
            knowledge_files.append(
                {
                    "filename": md_file.name,
                    "path": str(md_file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "hash": self._get_file_hash(md_file),
                }
            )

        return knowledge_files

    def _get_file_hash(self, filepath: Path) -> str:
        """ファイルのハッシュを取得"""
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def check_updates(self) -> Dict[str, List[str]]:
        """更新されたナレッジファイルをチェック"""
        current_files = self.get_all_knowledge_files()
        updates = {"new": [], "modified": [], "deleted": []}

        current_hashes = {f["filename"]: f["hash"] for f in current_files}
        cached_hashes = self._cache.get("file_hashes", {})

        # 新規・更新ファイルチェック
        for filename, hash_val in current_hashes.items():
            if filename not in cached_hashes:
                updates["new"].append(filename)
            elif cached_hashes[filename] != hash_val:
                updates["modified"].append(filename)

        # 削除ファイルチェック
        for filename in cached_hashes:
            if filename not in current_hashes:
                updates["deleted"].append(filename)

        # キャッシュ更新
        self._cache["file_hashes"] = current_hashes
        self._cache["last_check"] = datetime.now().isoformat()
        self._save_cache()

        return updates

    def search_knowledge(self, query: str) -> List[Dict]:
        """ナレッジベース内を検索"""
        results = []

        # 繰り返し処理
        for md_file in self.knowledge_dir.glob("*.md"):
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

                for i, line in enumerate(lines):
                    if query.lower() in line.lower():
                        # コンテキストを含めて結果を保存
                        context_start = max(0, i - 2)
                        context_end = min(len(lines), i + 3)
                        context = "\n".join(lines[context_start:context_end])

                        results.append(
                            {
                                "file": md_file.name,
                                "line": i + 1,
                                "context": context,
                                "match": line.strip(),
                            }
                        )

        return results


# ワーカー用のミックスイン
class KnowledgeAwareMixin:
    """ナレッジベースを参照できるワーカーミックスイン"""

    def __init__(self, *args, **kwargs):
        """初期化メソッド"""
        super().__init__(*args, **kwargs)
        self.knowledge_manager = KnowledgeBaseManager()

    def consult_knowledge(self, topic: str) -> Optional[str]:
        """ナレッジベースを参照"""
        self.logger.info(f"Consulting knowledge base for: {topic}")
        knowledge = self.knowledge_manager.get_knowledge(topic)

        if knowledge:
            self.logger.info(f"Found relevant knowledge for: {topic}")
            return knowledge
        else:
            self.logger.warning(f"No knowledge found for: {topic}")
            return None

    def check_knowledge_updates(self):
        """ナレッジベースの更新をチェック"""
        updates = self.knowledge_manager.check_updates()

        if any(updates.values()):
            self.logger.info("Knowledge base updates detected:")
            for update_type, files in updates.items():
                if files:
                    self.logger.info(f"  {update_type}: {', '.join(files)}")

        return updates


if __name__ == "__main__":
    # テスト実行
    manager = KnowledgeBaseManager()

    print("🔍 ナレッジベース管理システムテスト")
    print("=" * 50)

    # 全ファイル表示
    print("\n📚 登録されているナレッジファイル:")
    for file_info in manager.get_all_knowledge_files():
        print(f"  - {file_info['filename']} ({file_info['size']} bytes)")

    # テスト検索
    print("\n🔎 'test'に関するナレッジ検索:")
    test_knowledge = manager.get_knowledge("test")
    if test_knowledge:
        print(f"  見つかりました！（{len(test_knowledge)} 文字）")

    # 更新チェック
    print("\n📊 更新チェック:")
    updates = manager.check_updates()
    print(f"  新規: {len(updates['new'])}")
    print(f"  更新: {len(updates['modified'])}")
    print(f"  削除: {len(updates['deleted'])}")
