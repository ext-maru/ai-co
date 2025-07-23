#!/usr/bin/env python3
"""
類似度向上テスト
より高い類似度を実現する方法を検証
"""

import os
import sys
import asyncio
import asyncpg
import numpy as np
from datetime import datetime
import json

# OpenAI設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY が設定されていません")
    sys.exit(1)

from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)


async def test_similarity_improvements():
    """類似度向上のテスト"""

    print("🔬 類似度向上テスト開始")
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
        # 既存データをクリア
        await conn.execute("TRUNCATE knowledge_base.vector_documents")

        # 1. より具体的で詳細なテキストでテスト
        print("1️⃣ 詳細なテキストでのテスト")

        detailed_texts = [
            # エルダーズギルド関連（より詳細に）
            """エルダーズギルドは4賢者システムで構成される階層的な開発組織です。
            4賢者とは、ナレッジ賢者（Knowledge Sage）、タスク賢者（Task Oracle）、
            インシデント賢者（Crisis Sage）、RAG賢者（Search Mystic）の4つの専門家システムです。
            これらの賢者はそれぞれ知識管理、タスク管理、危機対応、情報検索を担当します。""",
            """4賢者システムの中核となるナレッジ賢者は、過去の開発知識を蓄積し、
            将来の開発に活かすための知識管理を行います。CLAUDE.mdなどの重要文書を管理し、
            チーム全体の知識共有を促進する役割を持っています。""",
            """タスク賢者は4賢者の一員として、プロジェクトのタスク管理と進捗追跡を担当します。
            優先順位の判断、依存関係の分析、最適な実行順序の決定などを行い、
            エルダーズギルド全体の開発効率を最大化します。""",
            """インシデント賢者は4賢者システムの危機管理担当として、
            システムエラー、バグ、セキュリティ問題などのインシデントに即座に対応します。
            過去のインシデント履歴から学習し、予防的な対策も提案します。""",
            """RAG賢者（Retrieval-Augmented Generation Sage）は4賢者の情報検索専門家です。
            大量の文書から関連情報を高速に検索し、必要な知識を統合して提供します。
            pgvectorを活用したベクトル検索により、意味的に関連する情報を発見します。""",
        ]

        # Embeddingを生成して保存
        for i, text in enumerate(detailed_texts):
            response = client.embeddings.create(
                model="text-embedding-ada-002", input=text
            )
            embedding = response.data[0].embedding

            await conn.execute(
                """
                INSERT INTO knowledge_base.vector_documents
                (title, content, embedding, metadata)
                VALUES ($1, $2, $3::vector, $4)
            """,
                f"詳細ドキュメント{i+1}",
                text,
                str(embedding),
                json.dumps(
                    {
                        "type": "detailed",
                        "sage_type": (
                            ["knowledge", "task", "incident", "rag"][i]
                            if i < 4
                            else "general"
                        ),
                    }
                ),
            )

        # クエリテスト
        test_queries = [
            "4賢者について教えてください",
            "4賢者システムとは何ですか",
            "エルダーズギルドの4賢者について",
            "ナレッジ賢者、タスク賢者、インシデント賢者、RAG賢者について",
        ]

        print("\n詳細テキストでの検索結果:")
        for query in test_queries:
            response = client.embeddings.create(
                model="text-embedding-ada-002", input=query
            )
            query_embedding = response.data[0].embedding

            results = await conn.fetch(
                """
                SELECT
                    title,
                    substring(content, 1, 50) as content_preview,
                    1 - (embedding <=> $1::vector) as similarity
                FROM knowledge_base.vector_documents
                ORDER BY embedding <=> $1::vector
                LIMIT 1
            """,
                str(query_embedding),
            )

            if results:
                print(f"クエリ: '{query}'")
                print(f"  → 類似度: {results[0]['similarity']:.4f}")

        # 2. チャンク分割によるテスト
        print("\n\n2️⃣ チャンク分割によるテスト")

        # 長いテキストを小さなチャンクに分割
        long_text = """エルダーズギルドは革新的な開発組織です。
        その中核となるのが4賢者システムです。
        4賢者とは、ナレッジ賢者、タスク賢者、インシデント賢者、RAG賢者の4つです。
        各賢者は専門分野を持ち、協調して動作します。
        ナレッジ賢者は知識管理を担当します。
        タスク賢者はプロジェクト管理を担当します。
        インシデント賢者は問題解決を担当します。
        RAG賢者は情報検索を担当します。"""

        sentences = [s.strip() for s in long_text.split("。") if s.strip()]

        # 各文をembedding化
        for i, sentence in enumerate(sentences):
            response = client.embeddings.create(
                model="text-embedding-ada-002", input=sentence
            )
            embedding = response.data[0].embedding

            await conn.execute(
                """
                INSERT INTO knowledge_base.vector_documents
                (title, content, embedding, metadata)
                VALUES ($1, $2, $3::vector, $4)
            """,
                f"チャンク{i+1}",
                sentence,
                str(embedding),
                json.dumps({"type": "chunk", "chunk_index": i}),
            )

        # 同じクエリでテスト
        query = "4賢者とは"
        response = client.embeddings.create(model="text-embedding-ada-002", input=query)
        query_embedding = response.data[0].embedding

        results = await conn.fetch(
            """
            SELECT
                title,
                content,
                1 - (embedding <=> $1::vector) as similarity
            FROM knowledge_base.vector_documents
            WHERE metadata->>'type' = 'chunk'
            ORDER BY embedding <=> $1::vector
            LIMIT 3
        """,
            str(query_embedding),
        )

        print("\nチャンク分割での検索結果:")
        print(f"クエリ: '{query}'")
        for row in results:
            print(
                f"  {row['title']} (類似度: {row['similarity']:.4f}): {row['content']}"
            )

        # 3. 前処理による改善
        print("\n\n3️⃣ 前処理による改善テスト")

        # 正規化とキーワード強調
        def preprocess_text(text):
            """preprocess_textを処理"""
            # キーワードを強調
            keywords = [
                "4賢者",
                "エルダーズギルド",
                "ナレッジ賢者",
                "タスク賢者",
                "インシデント賢者",
                "RAG賢者",
            ]
            for keyword in keywords:
                text = text.replace(keyword, f"{keyword} {keyword}")  # 重要語を繰り返す
            return text

        preprocessed_text = preprocess_text(
            "エルダーズギルドの4賢者システムは、ナレッジ賢者、タスク賢者、インシデント賢者、RAG賢者で構成されています。"
        )

        response = client.embeddings.create(
            model="text-embedding-ada-002", input=preprocessed_text
        )
        embedding = response.data[0].embedding

        await conn.execute(
            """
            INSERT INTO knowledge_base.vector_documents
            (title, content, embedding, metadata)
            VALUES ($1, $2, $3::vector, $4)
        """,
            "前処理済みドキュメント",
            preprocessed_text,
            str(embedding),
            json.dumps({"type": "preprocessed"}),
        )

        # クエリも同じ前処理を適用
        preprocessed_query = preprocess_text("4賢者について")
        response = client.embeddings.create(
            model="text-embedding-ada-002", input=preprocessed_query
        )
        query_embedding = response.data[0].embedding

        results = await conn.fetch(
            """
            SELECT
                title,
                1 - (embedding <=> $1::vector) as similarity
            FROM knowledge_base.vector_documents
            WHERE metadata->>'type' = 'preprocessed'
            ORDER BY embedding <=> $1::vector
            LIMIT 1
        """,
            str(query_embedding),
        )

        if results:
            print("\n前処理による改善結果:")
            print(f"クエリ: '{preprocessed_query}'")
            print(f"  → 類似度: {results[0]['similarity']:.4f}")

        # 4. 最終的な類似度比較
        print("\n\n4️⃣ 最終比較")

        query = "4賢者システムについて教えてください"
        response = client.embeddings.create(model="text-embedding-ada-002", input=query)
        query_embedding = response.data[0].embedding

        all_results = await conn.fetch(
            """
            SELECT
                title,
                metadata->>'type' as doc_type,
                1 - (embedding <=> $1::vector) as similarity
            FROM knowledge_base.vector_documents
            ORDER BY embedding <=> $1::vector
            LIMIT 10
        """,
            str(query_embedding),
        )

        print(f"\n全体の類似度ランキング (クエリ: '{query}'):")
        for i, row in enumerate(all_results):
            print(
                f"{i+1}. {row['title']} (タイプ: {row['doc_type']}) - 類似度: {row['similarity']:.4f}"
            )

        # 最高類似度を確認
        max_similarity = all_results[0]["similarity"] if all_results else 0
        print(f"\n🎯 最高類似度: {max_similarity:.4f}")

        if max_similarity > 0.9:
            print("✅ 非常に高い類似度を達成しました！")
        elif max_similarity > 0.85:
            print("⭐ 高い類似度を達成しました")
        else:
            print("📈 さらなる改善の余地があります")

        return max_similarity

    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback

        traceback.print_exc()
        return 0

    finally:
        await conn.close()


if __name__ == "__main__":
    max_similarity = asyncio.run(test_similarity_improvements())
    print(f"\n最終的な最高類似度: {max_similarity:.4f}")
