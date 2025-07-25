#!/usr/bin/env python3
"""
RAG Sage メモリ効率改善テスト
メモリエラーを解決する軽量版実装のテスト
"""

import gc
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import psutil


class TestRAGSageMemoryFix(unittest.TestCase):
    """RAG Sageメモリ効率改善テスト"""

    def setUp(self):
        """テスト環境のセットアップ"""
        self.test_dir = tempfile.mkdtemp()
        self.test_kb_path = Path(self.test_dir) / "knowledge_base"
        self.test_kb_path.mkdir(exist_ok=True)

    def tearDown(self):
        """テスト環境のクリーンアップ"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        gc.collect()

    def test_lightweight_rag_sage_initialization(self):
        """軽量版RAG Sageの初期化テスト"""
        from libs.lightweight_rag_sage import LightweightRAGSage

        # メモリ使用量を記録
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        # 軽量版RAG Sageを初期化
        sage = LightweightRAGSage(knowledge_base_path=str(self.test_kb_path))

        # メモリ使用量を確認
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before

        # アサーション
        self.assertIsNotNone(sage)
        self.assertTrue(sage.is_initialized)
        # メモリ増加量が50MB未満であることを確認
        self.assertLess(mem_increase, 50, f"メモリ増加量が大きすぎます: {mem_increase:0.2f}MB")

    def test_lazy_database_initialization(self):
        """遅延データベース初期化のテスト"""
        from libs.lightweight_rag_sage import LightweightRAGSage

        sage = LightweightRAGSage(knowledge_base_path=str(self.test_kb_path))

        # 初期化直後はデータベース接続なし
        self.assertIsNone(sage._db_connection)

        # 最初のデータベース操作時に初期化
        sage.add_knowledge("テスト知識", "test_source", "test")

        # データベースが初期化されていることを確認
        self.assertIsNotNone(sage._db_connection)

    def test_memory_efficient_search(self):
        """メモリ効率的な検索のテスト"""
        from libs.lightweight_rag_sage import LightweightRAGSage

        sage = LightweightRAGSage(knowledge_base_path=str(self.test_kb_path))

        # テストデータを追加
        for i in range(100):
            sage.add_knowledge(f"テスト知識 {i}", f"source_{i}", "test")

        # メモリ使用量を記録
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024

        # 検索実行
        results = sage.search_knowledge("テスト", limit=10)

        mem_after = process.memory_info().rss / 1024 / 1024
        mem_increase = mem_after - mem_before

        # アサーション
        self.assertEqual(len(results), 10)
        # 検索でのメモリ増加が10MB未満
        self.assertLess(mem_increase, 10, f"検索時のメモリ増加が大きすぎます: {mem_increase:0.2f}MB")

    def test_cache_size_limitation(self):
        """キャッシュサイズ制限のテスト"""
        from libs.lightweight_rag_sage import LightweightRAGSage

        sage = LightweightRAGSage(
            knowledge_base_path=str(self.test_kb_path),
            max_cache_size=5
        )

        # 10個の異なる検索を実行
        for i in range(10):
            sage.search_knowledge(f"query_{i}")

        # キャッシュサイズが制限されていることを確認
        self.assertLessEqual(len(sage.search_cache), 5)

    def test_batch_processing(self):
        """バッチ処理のテスト"""
        from libs.lightweight_rag_sage import LightweightRAGSage

        sage = LightweightRAGSage(knowledge_base_path=str(self.test_kb_path))

        # バッチでデータを追加
        batch_data = [
            ("知識1", "source1", "test"),
            ("知識2", "source2", "test"),
            ("知識3", "source3", "test"),
        ]

        sage.add_knowledge_batch(batch_data)

        # データが追加されていることを確認
        results = sage.search_knowledge("知識", limit=10)
        self.assertEqual(len(results), 3)

    def test_resource_cleanup(self):
        """リソースクリーンアップのテスト"""
        from libs.lightweight_rag_sage import LightweightRAGSage

        sage = LightweightRAGSage(knowledge_base_path=str(self.test_kb_path))
        sage.add_knowledge("テスト", "source", "test")

        # データベースファイルが存在することを確認
        db_path = self.test_kb_path / "rag_knowledge_light.db"
        self.assertTrue(db_path.exists())

        # クリーンアップ
        sage.cleanup()

        # リソースが解放されていることを確認
        self.assertIsNone(sage._db_connection)

    def test_minimal_indexing(self):
        """最小限のインデックス作成テスト"""
        from libs.lightweight_rag_sage import LightweightRAGSage

        sage = LightweightRAGSage(knowledge_base_path=str(self.test_kb_path))

        # テスト用のMarkdownファイルを作成
        test_md = self.test_kb_path / "test.md"
        test_md.write_text("# Test Document\nThis is a test content.")

        # メモリ使用量を記録
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024

        # インデックス作成（最小限のメモリ使用）
        indexed = sage.index_knowledge_base(max_files=10)

        mem_after = process.memory_info().rss / 1024 / 1024
        mem_increase = mem_after - mem_before

        # アサーション
        self.assertEqual(indexed, 1)
        self.assertLess(mem_increase, 20, f"インデックス時のメモリ増加が大きすぎます: {mem_increase:0.2f}MB")

    def test_streaming_file_processing(self):
        """ストリーミングファイル処理のテスト"""
        from libs.lightweight_rag_sage import LightweightRAGSage

        sage = LightweightRAGSage(knowledge_base_path=str(self.test_kb_path))

        # 大きなファイルを作成
        large_file = self.test_kb_path / "large.md"
        content = "# Large Document\n" + ("This is a test line.\n" * 1000)
        large_file.write_text(content)

        # ストリーミング処理でメモリ効率的に読み込み
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024

        sage.process_file_streaming(large_file)

        mem_after = process.memory_info().rss / 1024 / 1024
        mem_increase = mem_after - mem_before

        # メモリ増加が最小限であることを確認
        self.assertLess(mem_increase, 10, f"ストリーミング処理のメモリ増加が大きすぎます: {mem_increase:0.2f}MB")

    def test_consultation_memory_efficiency(self):
        """相談機能のメモリ効率テスト"""
        from libs.lightweight_rag_sage import LightweightRAGSage

        sage = LightweightRAGSage(knowledge_base_path=str(self.test_kb_path))

        # テストデータを追加
        sage.add_knowledge("メモリ効率化の方法", "guide.md", "optimization")

        # 相談実行
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024

        result = sage.consult_on_issue(
            "メモリエラーの解決",
            "RAG Sageの初期化時にMemoryErrorが発生します"
        )

        mem_after = process.memory_info().rss / 1024 / 1024
        mem_increase = mem_after - mem_before

        # アサーション
        self.assertEqual(result["status"], "success")
        self.assertLess(mem_increase, 5, f"相談時のメモリ増加が大きすぎます: {mem_increase:0.2f}MB")

    def test_connection_pooling(self):
        """コネクションプーリングのテスト"""
        from libs.lightweight_rag_sage import LightweightRAGSage

        sage = LightweightRAGSage(
            knowledge_base_path=str(self.test_kb_path),
            enable_connection_pool=True
        )

        # 複数の操作を実行
        for i in range(10):
            sage.add_knowledge(f"知識{i}", f"source{i}", "test")
            sage.search_knowledge(f"知識{i}")

        # コネクションが再利用されていることを確認
        self.assertEqual(sage._connection_count, 1)


if __name__ == "__main__":
    unittest.main()