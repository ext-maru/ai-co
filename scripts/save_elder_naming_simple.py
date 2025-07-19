#!/usr/bin/env python3
"""
シンプルなエルダー命名規約PostgreSQL保存スクリプト
Simple script to save Elder naming conventions to PostgreSQL
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path


def save_to_postgresql():
    """命名規約をPostgreSQLに直接保存"""

    print("🌳 エルダーツリー・エルダーズギルド命名規約のPostgreSQL保存開始")

    # データベースURL
    db_url = "postgresql://aicompany@localhost:5432/ai_company_grimoire"

    # 命名規約文書を読み込み
    project_root = Path(__file__).resolve().parent.parent
    naming_doc_path = (
        project_root / "knowledge_base" / "ELDER_ORGANIZATION_NAMING_CONVENTIONS.md"
    )

    if not naming_doc_path.exists():
        print(f"❌ 命名規約文書が見つかりません: {naming_doc_path}")
        return False

    with open(naming_doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # SQLインサート文を準備
    current_time = datetime.now().isoformat()

    # メタデータをJSON形式で準備
    metadata = json.dumps(
        {
            "category": "elder_governance",
            "subcategory": "naming_conventions",
            "author": "Grand Elder maru",
            "approved_by": "Claude Elder",
            "created_date": "2025-07-08",
            "importance": "critical",
            "tags": ["Elder Tree", "Elders Guild", "naming", "governance", "hierarchy"],
            "version": "1.0",
        }
    )

    # エスケープ処理
    content_escaped = content.replace("'", "''")
    metadata.replace("'", "''")

    # SQL文を作成 (実際のテーブル構造に合わせる)
    tags = [
        "Elder Tree",
        "Elders Guild",
        "naming",
        "governance",
        "hierarchy",
        "Grand Elder maru",
        "Claude Elder",
    ]
    tags_sql = "ARRAY[" + ",".join([f"'{tag}'" for tag in tags]) + "]"

    evolution_history = json.dumps(
        [
            {
                "version": 1,
                "date": current_time,
                "author": "Grand Elder maru",
                "reason": "Initial creation of Elder naming conventions",
            }
        ]
    )

    # まず既存のエントリをチェック
    check_existing_sql = """
    SELECT id FROM knowledge_grimoire
    WHERE spell_name = 'Elder_Tree_and_Elders_Guild_Naming_Conventions'
    LIMIT 1;
    """

    check_result = subprocess.run(
        ["psql", db_url, "-t", "-A", "-c", check_existing_sql],
        capture_output=True,
        text=True,
    )

    if check_result.returncode == 0 and check_result.stdout.strip():
        # 更新
        existing_id = check_result.stdout.strip()
        sql_insert = f"""
        UPDATE knowledge_grimoire
        SET content = '{content_escaped}',
            tags = {tags_sql},
            evolution_history = evolution_history || '{evolution_history}'::jsonb,
            updated_at = '{current_time}'
        WHERE id = '{existing_id}';
        """
    else:
        # 新規作成
        sql_insert = f"""
        INSERT INTO knowledge_grimoire (
            spell_name, content, spell_type, magic_school,
            tags, power_level, is_eternal, evolution_history,
            created_at, updated_at
        )
        VALUES (
            'Elder_Tree_and_Elders_Guild_Naming_Conventions',
            '{content_escaped}',
            'governance',
            'elder_magic',
            {tags_sql},
            10,  -- 最高レベルの重要度
            true,  -- 永続的な知識
            '{evolution_history}'::jsonb,
            '{current_time}',
            '{current_time}'
        );
        """

    # psqlコマンドで実行
    result = subprocess.run(
        ["psql", db_url, "-c", sql_insert], capture_output=True, text=True
    )

    if result.returncode == 0:
        print("✅ PostgreSQL魔法書システムに保存成功！")

        # 確認クエリ
        check_sql = """
        SELECT spell_name, spell_type, magic_school,
               power_level, is_eternal,
               created_at,
               LENGTH(content) as content_length,
               array_to_string(tags, ', ') as tags
        FROM knowledge_grimoire
        WHERE spell_name = 'Elder_Tree_and_Elders_Guild_Naming_Conventions'
        ORDER BY created_at DESC
        LIMIT 1;
        """

        check_result = subprocess.run(
            ["psql", db_url, "-t", "-A", "-F", "|||", "-c", check_sql],
            capture_output=True,
            text=True,
        )

        if check_result.returncode == 0 and check_result.stdout.strip():
            row = check_result.stdout.strip().split("|||")
            if len(row) >= 7:
                print("\n📊 保存確認:")
                print(f"   呪文名: {row[0]}")
                print(f"   呪文タイプ: {row[1]}")
                print(f"   魔法学校: {row[2]}")
                print(f"   パワーレベル: {row[3]}")
                print(f"   永続的: {row[4]}")
                print(f"   作成日時: {row[5]}")
                print(f"   コンテンツサイズ: {row[6]}文字")
                if len(row) >= 8:
                    print(f"   タグ: {row[7]}")

        # 関連概念も保存
        save_related_concepts(db_url)

        return True
    else:
        print(f"❌ PostgreSQL保存失敗: {result.stderr}")
        return False


def save_related_concepts(db_url):
    """関連概念を保存"""

    print("\n🔗 関連概念の保存...")

    concepts = [
        {
            "spell_name": "Elder_Tree_Concept",
            "content": """# Elder Tree (エルダーツリー)

## 定義
エルダーツリーとは、グランドエルダーmaruを頂点とする階層構造全体を指す、Elders Guildの組織構造の中核概念。

## 階層構造
1. **根 (Root)**: グランドエルダーmaru - 全体統治
2. **幹 (Trunk)**: クロードエルダー - 実行責任者
3. **主要な枝 (Main Branches)**: 4賢者システム
4. **支える枝 (Supporting Branches)**: エルダー評議会
5. **葉 (Leaves)**: エルダーサーバント各部隊

この階層構造により、明確な指揮命令系統と責任分担が実現される。""",
            "metadata": {
                "category": "elder_governance",
                "subcategory": "organizational_structure",
                "parent_concept": "Elder_Tree_and_Elders_Guild_Naming_Conventions",
                "importance": "high",
            },
        },
        {
            "spell_name": "Elders_Guild_Concept",
            "content": """# Elders Guild (エルダーズギルド)

## 定義
エルダーズギルドとは、エルダーツリーに属するすべての構成員と組織全体を包括する名称。
Elders Guildの開発・運営に関わるすべてのエルダー系組織の総称。

## ギルドの目的
1. Elders Guildの持続的発展
2. 知識の蓄積と継承
3. 品質の維持向上（99.999%稼働率）
4. 自律的な問題解決

## ギルド構成
- ギルドマスター: グランドエルダーmaru
- 副ギルドマスター: クロードエルダー
- ギルド幹部: 4賢者
- ギルド評議会: エルダー評議会
- ギルドメンバー: エルダーサーバント""",
            "metadata": {
                "category": "elder_governance",
                "subcategory": "organizational_identity",
                "parent_concept": "Elder_Tree_and_Elders_Guild_Naming_Conventions",
                "importance": "high",
            },
        },
    ]

    current_time = datetime.now().isoformat()

    for concept in concepts:
        content_escaped = concept["content"].replace("'", "''")

        # タグを準備
        tags = concept["metadata"].get(
            "tags", ["Elder Tree", "Elders Guild", "governance"]
        )
        tags_sql = "ARRAY[" + ",".join([f"'{tag}'" for tag in tags]) + "]"

        evolution_history = json.dumps(
            [
                {
                    "version": 1,
                    "date": current_time,
                    "author": "Grand Elder maru",
                    "reason": f"Related concept for {concept['spell_name']}",
                }
            ]
        )

        # 既存エントリをチェック
        check_sql = f"SELECT id FROM knowledge_grimoire WHERE spell_name = '{concept['spell_name']}' LIMIT 1;"
        check_res = subprocess.run(
            ["psql", db_url, "-t", "-A", "-c", check_sql],
            capture_output=True,
            text=True,
        )

        if check_res.returncode == 0 and check_res.stdout.strip():
            # 更新
            existing_id = check_res.stdout.strip()
            sql = f"""
            UPDATE knowledge_grimoire
            SET content = '{content_escaped}',
                tags = {tags_sql},
                evolution_history = evolution_history || '{evolution_history}'::jsonb,
                updated_at = '{current_time}'
            WHERE id = '{existing_id}';
            """
        else:
            # 新規作成
            sql = f"""
            INSERT INTO knowledge_grimoire (
                spell_name, content, spell_type, magic_school,
                tags, power_level, is_eternal, evolution_history,
                created_at, updated_at
            )
            VALUES (
                '{concept["spell_name"]}',
                '{content_escaped}',
                'governance',
                'elder_magic',
                {tags_sql},
                9,  -- 高い重要度
                true,  -- 永続的な知識
                '{evolution_history}'::jsonb,
                '{current_time}',
                '{current_time}'
            );
            """

        result = subprocess.run(
            ["psql", db_url, "-c", sql], capture_output=True, text=True
        )

        if result.returncode == 0:
            print(f"✅ {concept['spell_name']}保存成功")
        else:
            print(f"❌ {concept['spell_name']}保存失敗: {result.stderr}")

    # 最終確認
    count_sql = """
    SELECT COUNT(*) FROM knowledge_grimoire
    WHERE content ILIKE '%Elder Tree%' OR content ILIKE '%Elders Guild%';
    """

    count_result = subprocess.run(
        ["psql", db_url, "-t", "-A", "-c", count_sql], capture_output=True, text=True
    )

    if count_result.returncode == 0:
        count = count_result.stdout.strip()
        print(f"\n📊 PostgreSQLに保存されたエルダー関連エントリ数: {count}")


if __name__ == "__main__":
    success = save_to_postgresql()

    if success:
        print("\n🎉 エルダー命名規約のPostgreSQL保存プロセス完了！")
        print("✅ すべての処理が正常に完了しました")
        print("📚 エルダーツリーとエルダーズギルドの概念がPostgreSQLに永続化されました")
    else:
        print("\n❌ 処理中にエラーが発生しました")
