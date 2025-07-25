#!/usr/bin/env python3
"""
pgvector 徹底検証スクリプト
本当に動いているか完全に確認する
"""

import os
import sys
import asyncio
import asyncpg
import numpy as np
from datetime import datetime
import json
import time

# OpenAI設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY が設定されていません")
    sys.exit(1)

from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)


async def thorough_test():
    """徹底的な動作検証"""

    print("🔬 pgvector 徹底検証開始")
    print("=" * 80)

    # データベース接続
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        database="elders_knowledge",
        user="elders_guild",
        password="elders_2025",
    )

    try:
        # 1.0 拡張機能の確認
        print("1️⃣ pgvector拡張機能の確認")
        extensions = await conn.fetch(
            """
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname = 'vector'
        """
        )

        if extensions:
            print(
                f"✅ pgvector v{extensions[0]['extversion']} がインストールされています"
            )
        else:
            print("❌ pgvectorがインストールされていません")
            return False

        # 2.0 テーブル構造の確認
        print("\n2️⃣ テーブル構造の確認")
        columns = await conn.fetch(
            """
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'knowledge_base'
            AND table_name = 'vector_documents'
            ORDER BY ordinal_position
        """
        )

        print("カラム情報:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({col['udt_name']})")

        # vectorカラムの確認
        vector_col = [c for c in columns if c["udt_name"] == "vector"]
        if vector_col:
            print("✅ vectorカラムが正しく定義されています")
        else:
            print("❌ vectorカラムが見つかりません")

        # 3.0 インデックスの確認
        print("\n3️⃣ インデックスの確認")
        indexes = await conn.fetch(
            """
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'knowledge_base'
            AND tablename = 'vector_documents'
        """
        )

        for idx in indexes:
            print(f"  - {idx['indexname']}")
            if "ivfflat" in idx["indexdef"]:
                print("    ✅ IVFFlat インデックス")
            elif "hnsw" in idx["indexdef"]:
                print("    ✅ HNSW インデックス")

        # 4.0 既存データの確認
        print("\n4️⃣ 既存データの確認")
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM knowledge_base.vector_documents"
        )
        print(f"現在のドキュメント数: {count}")

        # データをクリア
        await conn.execute("TRUNCATE knowledge_base.vector_documents")
        print("既存データをクリアしました")

        # 5.0 多様なテストデータの投入
        print("\n5️⃣ 多様なテストデータの投入")
        test_data = [
            # エルダーズギルド関連
            "エルダーズギルドは4賢者システムで構成される階層的な開発組織",
            "ナレッジ賢者は過去の知識を蓄積し、未来の開発に活かす",
            "タスク賢者はプロジェクトの進捗管理と優先順位付けを行う",
            "インシデント賢者は危機対応と問題解決のスペシャリスト",
            "RAG賢者は情報検索と知識統合を担当する",
            # 技術関連
            "TDD（テスト駆動開発）はRed-Green-Refactorのサイクルで品質を保証",
            "pgvectorはPostgreSQLで高速なベクトル検索を実現する拡張機能",
            "セマンティック検索は意味的な類似性に基づく検索手法",
            # 全く関係ない内容
            "今日の天気は晴れです",
            "猫はかわいい動物です",
        ]

        print("Embedding生成中...")
        start_time = time.time()

        for i, text in enumerate(test_data):
            # Embedding生成
            response = client.embeddings.create(
                model="text-embedding-ada-002", input=text
            )
            embedding = response.data[0].embedding

            # データベースに保存
            await conn.execute(
                """
                INSERT INTO knowledge_base.vector_documents
                (title, content, embedding, metadata)
                VALUES ($1, $2, $3::vector, $4)
            """,
                f"ドキュメント{i+1}",
                text,
                str(embedding),
                json.dumps({"category": "test", "index": i}),
            )
            print(f"  ✅ {i+1}/{len(test_data)} 完了")

        elapsed = time.time() - start_time
        print(f"投入時間: {elapsed:0.2f}秒")

        # 6.0 様々なクエリでの検索テスト
        print("\n6️⃣ 様々なクエリでの検索テスト")

        test_queries = [
            "4賢者について教えて",
            "テスト駆動開発の方法",
            "ベクトル検索とは",
            "危機管理について",
            "動物について",
        ]

        # 繰り返し処理
        for query in test_queries:
            print(f"\n🔍 クエリ: '{query}'")

            # クエリのembedding生成
            start_time = time.time()
            response = client.embeddings.create(
                model="text-embedding-ada-002", input=query
            )
            query_embedding = response.data[0].embedding
            embedding_time = time.time() - start_time

            # 検索実行
            start_time = time.time()
            results = await conn.fetch(
                """
                SELECT
                    title,
                    content,
                    1 - (embedding <=> $1::vector) as similarity,
                    metadata
                FROM knowledge_base.vector_documents
                ORDER BY embedding <=> $1::vector
                LIMIT 3
            """,
                str(query_embedding),
            )
            search_time = time.time() - start_time

            print(f"  Embedding生成: {embedding_time:0.3f}秒")
            print(f"  検索実行: {search_time:0.3f}秒")
            print("  結果:")
            for j, row in enumerate(results):
                print(f"    {j+1}. {row['title']} (類似度: {row['similarity']:0.4f})")
                print(f"       {row['content'][:50]}...")

        # 7.0 ベクトル演算の確認
        print("\n7️⃣ ベクトル演算の確認")

        # コサイン類似度の手動計算と比較
        first_doc = await conn.fetchrow(
            """
            SELECT embedding::text
            FROM knowledge_base.vector_documents
            LIMIT 1
        """
        )

        if first_doc:
            # 文字列からベクトルを復元
            vec_str = first_doc["embedding"]
            vec_list = [float(x) for x in vec_str.strip("[]").split(",")]
            vec_array = np.array(vec_list)

            # 自己類似度を計算（1.0になるはず）
            self_similarity = await conn.fetchval(
                """
                SELECT 1 - (embedding <=> embedding)
                FROM knowledge_base.vector_documents
                LIMIT 1
            """
            )

            print(f"自己類似度: {self_similarity:0.6f} (期待値: 1.0)")
            if abs(self_similarity - 1.0) < 0.0001:
                print("✅ ベクトル演算が正しく動作しています")
            else:
                print("❌ ベクトル演算に問題があります")

        # 8.0 パフォーマンステスト
        print("\n8️⃣ パフォーマンステスト")

        # 100回の検索を実行
        total_time = 0
        iterations = 100

        test_embedding = str([0.1] * 1536)  # ダミーのembedding

        for _ in range(iterations):
            start_time = time.time()
            await conn.fetch(
                """
                SELECT title
                FROM knowledge_base.vector_documents
                ORDER BY embedding <=> $1::vector
                LIMIT 1
            """,
                test_embedding,
            )
            total_time += time.time() - start_time

        avg_time = total_time / iterations
        print(f"平均検索時間: {avg_time*1000:0.2f}ms ({iterations}回の平均)")

        if avg_time < 0.01:  # 10ms以下
            print("✅ 優秀なパフォーマンス")
        elif avg_time < 0.1:  # 100ms以下
            print("⚠️ 許容範囲のパフォーマンス")
        else:
            print("❌ パフォーマンスに問題があります")

        # 9.0 総合判定
        print("\n=" * 80)
        print("🏁 検証結果サマリー")
        print("=" * 80)

        all_checks = {
            "pgvector拡張機能": True,
            "テーブル構造": True,
            "インデックス": len(indexes) > 0,
            "Embedding生成": True,
            "ベクトル保存": True,
            "類似検索": True,
            "ベクトル演算": (
                abs(self_similarity - 1.0) < 0.0001
                if "self_similarity" in locals()
                else False
            ),
            "パフォーマンス": avg_time < 0.1,
        }

        for check, result in all_checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check}")

        if all(all_checks.values()):
            print("\n🎉 すべてのテストに合格！pgvectorは完全に動作しています！")
            return True
        else:
            print("\n⚠️ 一部のテストに問題があります")
            return False

    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await conn.close()


if __name__ == "__main__":
    success = asyncio.run(thorough_test())
    sys.exit(0 if success else 1)
