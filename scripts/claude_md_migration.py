#!/usr/bin/env python3
"""
CLAUDE.md移行スクリプト
CorePostgres Phase 1 - 最重要ドキュメントの移行
"""

import os
import sys
import asyncio
import asyncpg
import json
from datetime import datetime
import re

# OpenAI設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY が設定されていません")
    sys.exit(1)

from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)


class CLAUDEMDMigrator:
    """CLAUDE.md移行システム"""

    def __init__(self):
        self.conn = None

    async def connect(self):
        """データベース接続"""
        self.conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database="elders_knowledge",
            user="elders_guild",
            password="elders_2025",
        )

    async def setup_migration_table(self):
        """移行用テーブル作成"""
        await self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_base.core_documents (
                id SERIAL PRIMARY KEY,
                file_path VARCHAR(500) NOT NULL,
                section_title VARCHAR(255),
                section_content TEXT NOT NULL,
                section_type VARCHAR(100),
                priority INTEGER DEFAULT 5,
                tags TEXT[],
                embedding vector(1536),
                search_vector tsvector,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """
        )

        # インデックス作成
        await self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_core_docs_embedding
            ON knowledge_base.core_documents
            USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
        """
        )

        await self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_core_docs_search
            ON knowledge_base.core_documents
            USING gin(search_vector)
        """
        )

        print("✅ 移行用テーブル作成完了")

    def parse_claude_md(self, content: str):
        """CLAUDE.mdをセクション別に解析"""
        sections = []
        current_section = None
        current_content = []

        lines = content.split("\n")

        for line in lines:
            # ヘッダー行の検出
            if line.startswith("#"):
                # 前のセクションを保存
                if current_section:
                    sections.append(
                        {
                            "title": current_section,
                            "content": "\n".join(current_content).strip(),
                            "level": current_section.count("#"),
                        }
                    )

                # 新しいセクション開始
                current_section = line
                current_content = []
            else:
                current_content.append(line)

        # 最後のセクション
        if current_section:
            sections.append(
                {
                    "title": current_section,
                    "content": "\n".join(current_content).strip(),
                    "level": current_section.count("#"),
                }
            )

        return sections

    def categorize_section(self, title: str, content: str):
        """セクションの分類"""
        title_lower = title.lower()
        content_lower = content.lower()

        if "4賢者" in title or "賢者" in title:
            return "sages_system"
        elif "tdd" in title_lower or "テスト" in title:
            return "development_practice"
        elif "エルダーズギルド" in title or "elders guild" in title_lower:
            return "guild_overview"
        elif "コマンド" in title or "command" in title_lower:
            return "commands"
        elif "ガイド" in title or "guide" in title_lower:
            return "guides"
        elif "プロジェクト" in title or "project" in title_lower:
            return "project_structure"
        else:
            return "general"

    def extract_tags(self, title: str, content: str):
        """タグ抽出"""
        tags = []

        # タイトルからタグ抽出
        if "4賢者" in title:
            tags.extend(["4賢者", "エルダーズギルド"])
        if "TDD" in title:
            tags.extend(["TDD", "テスト駆動開発"])
        if "コマンド" in title:
            tags.extend(["CLI", "コマンド"])

        # コンテンツからキーワード抽出
        keywords = [
            "ナレッジ賢者",
            "タスク賢者",
            "インシデント賢者",
            "RAG賢者",
            "PostgreSQL",
            "pgvector",
            "CorePostgres",
            "グランドエルダー",
            "クロードエルダー",
        ]

        for keyword in keywords:
            if keyword in content:
                tags.append(keyword)

        return list(set(tags))  # 重複削除

    async def create_embeddings_with_context(
        self, title: str, content: str, category: str
    ):
        """コンテキスト付きembedding生成"""
        # 高精度embedding用のテキスト準備
        context_text = f"""
        ドキュメント分類: {category}
        セクションタイトル: {title}

        内容: {content}

        関連キーワード: エルダーズギルド 4賢者 ナレッジ賢者 タスク賢者 インシデント賢者 RAG賢者 CorePostgres
        """

        response = client.embeddings.create(
            model="text-embedding-ada-002", input=context_text
        )

        return response.data[0].embedding

    async def migrate_section(self, file_path: str, section: dict):
        """セクションの移行"""
        category = self.categorize_section(section["title"], section["content"])
        tags = self.extract_tags(section["title"], section["content"])

        # 高精度embedding生成
        embedding = await self.create_embeddings_with_context(
            section["title"], section["content"], category
        )

        # 全文検索用テキスト
        search_text = f"{section['title']} {section['content']}"

        # データベースに挿入
        await self.conn.execute(
            """
            INSERT INTO knowledge_base.core_documents
            (file_path, section_title, section_content, section_type,
             priority, tags, embedding, search_vector, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7::vector, to_tsvector('english', $8), $9)
        """,
            file_path,
            section["title"],
            section["content"],
            category,
            10 - section["level"],  # レベルが高いほど優先度高
            tags,
            str(embedding),
            search_text,
            json.dumps(
                {
                    "migration_date": datetime.now().isoformat(),
                    "original_level": section["level"],
                    "word_count": len(section["content"].split()),
                }
            ),
        )


async def migrate_claude_md():
    """CLAUDE.md移行実行"""

    print("📚 CLAUDE.md移行開始")
    print("=" * 60)

    migrator = CLAUDEMDMigrator()
    await migrator.connect()

    try:
        # テーブルセットアップ
        await migrator.setup_migration_table()

        # 既存データクリア
        await migrator.conn.execute("TRUNCATE knowledge_base.core_documents")

        # CLAUDE.mdファイルの読み込み
        claude_md_paths = [
            "/home/aicompany/ai_co/CLAUDE.md",
            "/home/aicompany/CLAUDE.md",
        ]

        for path in claude_md_paths:
            if os.path.exists(path):
                print(f"📖 {path} を読み込み中...")

                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                # セクション解析
                sections = migrator.parse_claude_md(content)
                print(f"✅ {len(sections)}個のセクションを検出")

                # 各セクションを移行
                for i, section in enumerate(sections):
                    if (
                        len(section["content"].strip()) > 50
                    ):  # 短すぎるセクションはスキップ
                        await migrator.migrate_section(path, section)
                        print(f"  📝 移行完了: {section['title'][:50]}...")

                break
        else:
            print("❌ CLAUDE.mdファイルが見つかりません")
            return False

        # 移行結果確認
        count = await migrator.conn.fetchval(
            """
            SELECT COUNT(*) FROM knowledge_base.core_documents
        """
        )

        categories = await migrator.conn.fetch(
            """
            SELECT section_type, COUNT(*) as count
            FROM knowledge_base.core_documents
            GROUP BY section_type
            ORDER BY count DESC
        """
        )

        print(f"\n📊 移行結果:")
        print(f"  総セクション数: {count}")
        print(f"  カテゴリ別:")
        for cat in categories:
            print(f"    {cat['section_type']}: {cat['count']}件")

        # 検索テスト
        print(f"\n🔍 検索テスト実行...")

        test_queries = [
            "4賢者システムについて",
            "TDDの方法",
            "エルダーズギルドとは",
            "コマンドの使い方",
        ]

        for query in test_queries:
            response = client.embeddings.create(
                model="text-embedding-ada-002", input=f"質問: {query}"
            )
            query_embedding = response.data[0].embedding

            results = await migrator.conn.fetch(
                """
                SELECT
                    section_title,
                    section_type,
                    1 - (embedding <=> $1::vector) as similarity
                FROM knowledge_base.core_documents
                ORDER BY embedding <=> $1::vector
                LIMIT 3
            """,
                str(query_embedding),
            )

            if results:
                top_result = results[0]
                print(
                    f"  '{query}' → {top_result['section_title'][:40]}... (類似度: {top_result['similarity']:.3f})"
                )

        print(f"\n🎉 CLAUDE.md移行完了！")
        return True

    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if migrator.conn:
            await migrator.conn.close()


if __name__ == "__main__":
    success = asyncio.run(migrate_claude_md())
    print(f"\n{'✅ 移行成功' if success else '❌ 移行失敗'}")
