#!/usr/bin/env python3
"""
Knowledge Sage Enhanced - 知識ベース検索強化テスト
TDDで知識賢者の検索機能を改善

Elder Flow TDD:
1. 🔴 Red: 失敗するテストを作成
2. 🟢 Green: 最小限のコードで成功
3. 🔵 Refactor: コード改善
"""

import pytest
import json
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import time

# プロジェクトルートをパスに追加
import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestKnowledgeSageEnhanced:
    """知識賢者強化テスト"""

    @pytest.fixture
    def temp_knowledge_base(self):
        """テスト用一時知識ベース"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_path = Path(tmpdir) / "knowledge_base"
            kb_path.mkdir()
            
            # テスト用知識ファイル作成
            (kb_path / "test_knowledge1.md").write_text("""
# Test Knowledge 1
Tags: #python #testing #tdd

## Overview
This is a test knowledge document about TDD practices.

### Key Concepts
- Red-Green-Refactor cycle
- Test-first development
- Continuous testing
""")
            
            (kb_path / "test_knowledge2.md").write_text("""
# Test Knowledge 2
Tags: #elder #guild #architecture

## Elder System Architecture
Description of the elder system and its components.

### Components
- Grand Elder
- Claude Elder
- Four Sages
- Elder Servants
""")
            
            (kb_path / "test_knowledge3.json").write_text(json.dumps({
                "title": "Configuration Guide",
                "tags": ["config", "setup", "deployment"],
                "content": "Configuration best practices for deployment"
            }))
            
            yield kb_path

    @pytest.fixture
    def knowledge_sage(self, temp_knowledge_base):
        """テスト用知識賢者インスタンス"""
        from libs.knowledge_sage_enhanced import KnowledgeSageEnhanced
        sage = KnowledgeSageEnhanced(knowledge_base_path=temp_knowledge_base)
        return sage

    # ========== 基本機能テスト ==========

    def test_initialization(self, knowledge_sage):
        """初期化テスト"""
        assert knowledge_sage is not None
        assert knowledge_sage.knowledge_base_path.exists()
        assert knowledge_sage.index is not None
        assert knowledge_sage.search_cache is not None

    def test_index_building(self, knowledge_sage):
        """インデックス構築テスト"""
        knowledge_sage.build_index()
        
        # インデックスが構築されているか確認
        assert len(knowledge_sage.index) > 0
        assert "test_knowledge1.md" in knowledge_sage.index
        assert "test_knowledge2.md" in knowledge_sage.index
        assert "test_knowledge3.json" in knowledge_sage.index

    def test_search_by_keyword(self, knowledge_sage):
        """キーワード検索テスト"""
        knowledge_sage.build_index()
        
        # TDD関連の検索
        results = knowledge_sage.search("TDD")
        assert len(results) > 0
        assert any("test_knowledge1.md" in r["path"] for r in results)
        
        # Elder関連の検索
        results = knowledge_sage.search("Elder")
        assert len(results) > 0
        assert any("test_knowledge2.md" in r["path"] for r in results)

    def test_search_by_tags(self, knowledge_sage):
        """タグ検索テスト"""
        knowledge_sage.build_index()
        
        # Pythonタグ検索
        results = knowledge_sage.search_by_tags(["python"])
        assert len(results) > 0
        assert all("python" in r.get("tags", []) for r in results)
        
        # 複数タグ検索
        results = knowledge_sage.search_by_tags(["elder", "guild"])
        assert len(results) > 0

    def test_fuzzy_search(self, knowledge_sage):
        """曖昧検索テスト"""
        knowledge_sage.build_index()
        
        # タイポを含む検索
        results = knowledge_sage.fuzzy_search("developmnt")  # development のタイポ
        assert len(results) > 0
        assert any("development" in r["content"].lower() for r in results)

    def test_semantic_search(self, knowledge_sage):
        """意味検索テスト"""
        knowledge_sage.build_index()
        
        # 意味的に関連する検索
        results = knowledge_sage.semantic_search("testing methodology")
        assert len(results) > 0
        assert any("tdd" in r["content"].lower() for r in results)

    # ========== キャッシュ機能テスト ==========

    def test_search_caching(self, knowledge_sage):
        """検索キャッシュテスト"""
        knowledge_sage.build_index()
        
        # 初回検索
        start_time = time.time()
        results1 = knowledge_sage.search("TDD")
        first_search_time = time.time() - start_time
        
        # 2回目検索（キャッシュ使用）
        start_time = time.time()
        results2 = knowledge_sage.search("TDD")
        cached_search_time = time.time() - start_time
        
        # キャッシュの方が高速
        assert cached_search_time < first_search_time
        assert results1 == results2

    def test_cache_invalidation(self, knowledge_sage):
        """キャッシュ無効化テスト"""
        knowledge_sage.build_index()
        
        # 検索してキャッシュ作成
        results1 = knowledge_sage.search("TDD")
        
        # 新しいファイル追加
        new_file = knowledge_sage.knowledge_base_path / "new_knowledge.md"
        new_file.write_text("# New Knowledge\nTDD is important")
        
        # インデックス再構築
        knowledge_sage.build_index()
        
        # キャッシュがクリアされて新しい結果が返る
        results2 = knowledge_sage.search("TDD")
        assert len(results2) > len(results1)

    # ========== 高度な検索機能テスト ==========

    def test_relevance_scoring(self, knowledge_sage):
        """関連性スコアリングテスト"""
        knowledge_sage.build_index()
        
        results = knowledge_sage.search("Elder", include_scores=True)
        
        # スコアが付いているか確認
        assert all("score" in r for r in results)
        
        # スコア順にソートされているか確認
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_filters(self, knowledge_sage):
        """検索フィルタテスト"""
        knowledge_sage.build_index()
        
        # ファイルタイプフィルタ
        results = knowledge_sage.search("test", file_types=[".md"])
        assert all(r["path"].endswith(".md") for r in results)
        
        # 日付フィルタ
        results = knowledge_sage.search("test", modified_after=datetime.now())
        assert len(results) == 0  # 未来の日付なので結果なし

    def test_search_pagination(self, knowledge_sage):
        """検索ページネーションテスト"""
        knowledge_sage.build_index()
        
        # ページサイズ指定
        page1 = knowledge_sage.search("test", page=1, page_size=2)
        page2 = knowledge_sage.search("test", page=2, page_size=2)
        
        # ページが異なること
        assert page1 != page2
        assert len(page1) <= 2
        assert len(page2) <= 2

    def test_search_highlighting(self, knowledge_sage):
        """検索結果ハイライトテスト"""
        knowledge_sage.build_index()
        
        results = knowledge_sage.search("TDD", highlight=True)
        
        # ハイライトが含まれているか確認
        assert any("<mark>TDD</mark>" in r.get("highlighted", "") for r in results)

    # ========== パフォーマンステスト ==========

    def test_large_index_performance(self, temp_knowledge_base):
        """大規模インデックスパフォーマンステスト"""
        # 1000個のファイルを作成
        for i in range(1000):
            file_path = temp_knowledge_base / f"knowledge_{i}.md"
            file_path.write_text(f"# Knowledge {i}\nContent about topic {i % 10}")
        
        from libs.knowledge_sage_enhanced import KnowledgeSageEnhanced
        sage = KnowledgeSageEnhanced(knowledge_base_path=temp_knowledge_base)
        
        # インデックス構築時間測定
        start_time = time.time()
        sage.build_index()
        build_time = time.time() - start_time
        
        # 1000ファイルを5秒以内でインデックス化
        assert build_time < 5.0
        assert len(sage.index) >= 1000

    def test_concurrent_search(self, knowledge_sage):
        """並行検索テスト"""
        import threading
        
        knowledge_sage.build_index()
        results = []
        errors = []
        
        def search_worker(query):
            try:
                result = knowledge_sage.search(query)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # 10個の並行検索
        threads = []
        for i in range(10):
            t = threading.Thread(target=search_worker, args=(f"test{i % 3}",))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # エラーなく完了
        assert len(errors) == 0
        assert len(results) == 10

    # ========== エラーハンドリングテスト ==========

    def test_invalid_query_handling(self, knowledge_sage):
        """無効なクエリ処理テスト"""
        knowledge_sage.build_index()
        
        # 空のクエリ
        results = knowledge_sage.search("")
        assert results == []
        
        # None クエリ
        results = knowledge_sage.search(None)
        assert results == []
        
        # 特殊文字のみ
        results = knowledge_sage.search("!@#$%")
        assert isinstance(results, list)

    def test_corrupted_file_handling(self, knowledge_sage):
        """破損ファイル処理テスト"""
        # バイナリファイルを追加
        binary_file = knowledge_sage.knowledge_base_path / "corrupted.bin"
        binary_file.write_bytes(b'\x00\x01\x02\x03')
        
        # インデックス構築でエラーにならない
        knowledge_sage.build_index()
        
        # 検索も正常に動作
        results = knowledge_sage.search("test")
        assert isinstance(results, list)

    # ========== 統合テスト ==========

    def test_full_text_extraction(self, knowledge_sage):
        """フルテキスト抽出テスト"""
        knowledge_sage.build_index()
        
        # Markdownファイルの内容抽出
        md_content = knowledge_sage.extract_text(
            knowledge_sage.knowledge_base_path / "test_knowledge1.md"
        )
        assert "TDD practices" in md_content
        assert "Red-Green-Refactor" in md_content
        
        # JSONファイルの内容抽出
        json_content = knowledge_sage.extract_text(
            knowledge_sage.knowledge_base_path / "test_knowledge3.json"
        )
        assert "Configuration Guide" in json_content

    def test_metadata_extraction(self, knowledge_sage):
        """メタデータ抽出テスト"""
        knowledge_sage.build_index()
        
        # 各ファイルのメタデータ確認
        for file_path, metadata in knowledge_sage.index.items():
            assert "title" in metadata
            assert "tags" in metadata
            assert "modified" in metadata
            assert "size" in metadata

    def test_search_result_ranking(self, knowledge_sage):
        """検索結果ランキングテスト"""
        knowledge_sage.build_index()
        
        # より関連性の高い結果が上位に
        results = knowledge_sage.search("Elder System")
        
        # "Elder System Architecture" を含むファイルが最上位
        assert "test_knowledge2.md" in results[0]["path"]

    def test_api_compatibility(self, knowledge_sage):
        """API互換性テスト"""
        # 基本的なAPIメソッドが存在
        assert hasattr(knowledge_sage, 'search')
        assert hasattr(knowledge_sage, 'build_index')
        assert hasattr(knowledge_sage, 'search_by_tags')
        assert hasattr(knowledge_sage, 'fuzzy_search')
        assert hasattr(knowledge_sage, 'semantic_search')
        
        # メソッドが呼び出し可能
        assert callable(knowledge_sage.search)
        assert callable(knowledge_sage.build_index)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])