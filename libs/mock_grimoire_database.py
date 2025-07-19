#!/usr/bin/env python3
"""
Mock Grimoire Database - PostgreSQLが利用できない環境用のモックデータベース
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class MockGrimoireDatabase:
    """ファイルベースのモックGrimoireデータベース"""

    def __init__(self, database_url: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.database_url = database_url or "mock://localhost/grimoire"

        # モックデータベースディレクトリ
        self.db_path = Path("/home/aicompany/ai_co/data/mock_grimoire_db")
        self.db_path.mkdir(parents=True, exist_ok=True)

        # データファイル
        self.spells_file = self.db_path / "spells.json"
        self.index_file = self.db_path / "index.json"

        # メモリキャッシュ
        self.spells_cache = {}
        self.index_cache = {}

        # 初期化
        self._initialize_database()

        self.logger.info(
            "🎭 Mock Grimoire Database initialized (PostgreSQL alternative)"
        )

    def _initialize_database(self):
        """データベースの初期化"""
        # spells.json
        if not self.spells_file.exists():
            self.spells_file.write_text(json.dumps({}, ensure_ascii=False, indent=2))
        else:
            with open(self.spells_file, "r", encoding="utf-8") as f:
                self.spells_cache = json.load(f)

        # index.json
        if not self.index_file.exists():
            self.index_file.write_text(json.dumps({}, ensure_ascii=False, indent=2))
        else:
            with open(self.index_file, "r", encoding="utf-8") as f:
                self.index_cache = json.load(f)

    def _save_database(self):
        """データベースをファイルに保存"""
        with open(self.spells_file, "w", encoding="utf-8") as f:
            json.dump(self.spells_cache, f, ensure_ascii=False, indent=2)

        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.index_cache, f, ensure_ascii=False, indent=2)

    def _generate_id(self, content: str) -> str:
        """コンテンツからIDを生成"""
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def add_spell(
        self,
        spell_name: str,
        content: str,
        spell_type: str = "knowledge",
        magic_school: str = "general",
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """呪文（知識）を追加"""
        spell_id = self._generate_id(f"{spell_name}_{content}")

        spell = {
            "id": spell_id,
            "spell_name": spell_name,
            "content": content,
            "spell_type": spell_type,
            "magic_school": magic_school,
            "tags": tags or [],
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "power_level": 1,
            "casting_frequency": 0,
        }

        # 保存
        self.spells_cache[spell_id] = spell

        # インデックス更新
        for word in spell_name.split() + content.split()[:20]:
            word_lower = word.lower()
            if word_lower not in self.index_cache:
                self.index_cache[word_lower] = []
            if spell_id not in self.index_cache[word_lower]:
                self.index_cache[word_lower].append(spell_id)

        self._save_database()
        return spell_id

    def search_spells(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """呪文を検索（簡易テキスト検索）"""
        results = []
        seen_ids = set()

        # クエリを単語に分割
        query_words = query.lower().split()

        # インデックスから検索
        for word in query_words:
            if word in self.index_cache:
                for spell_id in self.index_cache[word]:
                    if spell_id not in seen_ids and spell_id in self.spells_cache:
                        spell = self.spells_cache[spell_id].copy()
                        # 簡易スコア（出現回数）
                        score = sum(
                            1 for w in query_words if w in spell["content"].lower()
                        )
                        spell["similarity_score"] = min(1.0, score / len(query_words))
                        results.append(spell)
                        seen_ids.add(spell_id)

        # スコアでソート
        results.sort(key=lambda x: x["similarity_score"], reverse=True)

        return results[:limit]

    def get_spell(self, spell_id: str) -> Optional[Dict[str, Any]]:
        """IDで呪文を取得"""
        return self.spells_cache.get(spell_id)

    def update_spell(self, spell_id: str, updates: Dict[str, Any]) -> bool:
        """呪文を更新"""
        if spell_id in self.spells_cache:
            self.spells_cache[spell_id].update(updates)
            self.spells_cache[spell_id]["updated_at"] = datetime.now().isoformat()
            self._save_database()
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        total_spells = len(self.spells_cache)

        # 魔法学校別の統計
        school_stats = {}
        for spell in self.spells_cache.values():
            school = spell.get("magic_school", "general")
            school_stats[school] = school_stats.get(school, 0) + 1

        return {
            "total_spells": total_spells,
            "school_distribution": school_stats,
            "index_size": len(self.index_cache),
            "database_type": "mock_file_based",
        }

    def close(self):
        """データベース接続を閉じる（互換性のため）"""
        self._save_database()
        self.logger.info("Mock Grimoire Database closed")


class MockGrimoireVectorSearch:
    """ベクトル検索のモック実装"""

    def __init__(self, database: MockGrimoireDatabase):
        self.database = database
        self.logger = logging.getLogger(__name__)

    async def search(
        self, query: str, limit: int = 10, threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """ベクトル検索のモック（実際はテキスト検索）"""
        results = self.database.search_spells(query, limit)

        # しきい値でフィルタリング
        filtered_results = [
            r for r in results if r.get("similarity_score", 0) >= threshold
        ]

        return filtered_results

    async def add_embedding(self, spell_id: str, embedding: List[float]) -> bool:
        """埋め込みベクトルの追加（モックなので何もしない）"""
        self.logger.debug(f"Mock: Adding embedding for spell {spell_id}")
        return True


# PostgreSQL互換のファクトリー関数
def create_mock_grimoire_connection(database_url: str) -> MockGrimoireDatabase:
    """モックGrimoireデータベース接続を作成"""
    return MockGrimoireDatabase(database_url)
