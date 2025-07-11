#!/usr/bin/env python3
"""
pgvector 完全セットアップ＆動作確認スクリプト
知識のコア部分 - ベクトル検索基盤の完全実装
"""

import os
import sys
import asyncio
import asyncpg
import numpy as np
from datetime import datetime
import json

# OpenAI APIキーの確認
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY が設定されていません")
    print("   source /home/aicompany/ai_co/.env を実行してください")
    sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

async def setup_pgvector():
    """pgvector セットアップと動作確認"""

    print("🐘 pgvector 完全セットアップ開始")
    print("=" * 60)

    # データベース接続
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        database='elders_knowledge',
        user='elders_guild',
        password='elders_2025'
    )

    try:
        # 1. pgvector拡張機能の作成を試みる
        print("📦 pgvector拡張機能の有効化...")
        try:
            await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
            print("✅ pgvector拡張機能を有効化しました")
        except Exception as e:
            print(f"❌ pgvector有効化エラー: {e}")
            print("\n⚠️  以下のコマンドを実行してください:")
            print("cd /tmp/pgvector_install/pgvector")
            print("sudo make install")
            print("その後、このスクリプトを再実行してください")
            return False

        # 2. ベクトル検索用テーブルの作成
        print("\n📋 知識ベーステーブル作成中...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_base.vector_documents (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                embedding vector(1536),  -- OpenAI ada-002の次元数
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # インデックスの作成
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_vector_documents_embedding
            ON knowledge_base.vector_documents
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """)

        print("✅ ベクトル検索テーブルを作成しました")

        # 3. OpenAI APIでembedding生成テスト
        print("\n🤖 OpenAI embedding生成テスト...")
        test_texts = [
            "エルダーズギルドは4賢者システムで構成される",
            "TDD（テスト駆動開発）はRed-Green-Refactorサイクル",
            "pgvectorは高速なベクトル検索を可能にする"
        ]

        embeddings = []
        for text in test_texts:
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            embedding = response.data[0].embedding
            embeddings.append(embedding)
            print(f"✅ Embedding生成成功: {text[:30]}... (次元: {len(embedding)})")

        # 4. データベースへの保存
        print("\n💾 ベクトルデータ保存中...")
        for i, (text, embedding) in enumerate(zip(test_texts, embeddings)):
            await conn.execute("""
                INSERT INTO knowledge_base.vector_documents
                (title, content, embedding, metadata)
                VALUES ($1, $2, $3::vector, $4)
            """,
                f"テストドキュメント{i+1}",
                text,
                str(embedding),  # リストを文字列に変換
                json.dumps({"test": True, "index": i})
            )
        print("✅ 3件のテストデータを保存しました")

        # 5. ベクトル検索テスト
        print("\n🔍 ベクトル検索テスト...")
        query_text = "4賢者について教えて"

        # クエリのembedding生成
        query_response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=query_text
        )
        query_embedding = query_response.data[0].embedding

        # 類似検索実行
        results = await conn.fetch("""
            SELECT
                id,
                title,
                content,
                1 - (embedding <=> $1::vector) as similarity
            FROM knowledge_base.vector_documents
            ORDER BY embedding <=> $1::vector
            LIMIT 3
        """, str(query_embedding))

        print(f"\nクエリ: '{query_text}'")
        print("検索結果:")
        for row in results:
            print(f"  - {row['title']} (類似度: {row['similarity']:.4f})")
            print(f"    内容: {row['content'][:60]}...")

        # 6. 統計情報
        count = await conn.fetchval("""
            SELECT COUNT(*) FROM knowledge_base.vector_documents
        """)

        print(f"\n📊 統計情報:")
        print(f"  - 総ドキュメント数: {count}")
        print(f"  - インデックスタイプ: IVFFlat")
        print(f"  - ベクトル次元数: 1536")

        print("\n🎉 pgvector完全動作確認成功！")
        print("=" * 60)

        # 結果をファイルに保存
        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "pgvector_enabled": True,
            "test_documents": count,
            "embedding_model": "text-embedding-ada-002",
            "vector_dimension": 1536,
            "search_results": [
                {
                    "title": row['title'],
                    "similarity": float(row['similarity'])
                } for row in results
            ]
        }

        with open('pgvector_setup_result.json', 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await conn.close()

async def main():
    """メイン処理"""
    success = await setup_pgvector()

    if success:
        print("\n✅ 知識のコア部分（ベクトル検索）が完全に動作しています！")
        print("\n📝 次のステップ:")
        print("1. CLAUDE.mdなどの重要ドキュメントの移行")
        print("2. 4賢者システムとの統合")
        print("3. 本格的な知識ベース構築")
    else:
        print("\n⚠️  セットアップが未完了です")
        print("上記の指示に従って、pgvectorをインストールしてください")

if __name__ == "__main__":
    asyncio.run(main())
