#!/usr/bin/env python3
"""
エルダーツリーとエルダーズギルド命名規約をPostgreSQLに保存するスクリプト
Save Elder Tree and Elders Guild naming conventions to PostgreSQL
"""

import os
import subprocess
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from libs.knowledge_grimoire_adapter import KnowledgeGrimoireAdapter


def save_elder_naming_conventions():
    """エルダー命名規約をPostgreSQLに保存"""

    print("🌳 エルダーツリー・エルダーズギルド命名規約のPostgreSQL保存開始")

    # Knowledge Grimoire Adapterを初期化
    adapter = KnowledgeGrimoireAdapter(grimoire_enabled=True)

    # 命名規約文書を読み込み
    naming_doc_path = (
        project_root / "knowledge_base" / "ELDER_ORGANIZATION_NAMING_CONVENTIONS.md"
    )

    if not naming_doc_path.exists():
        print(f"❌ 命名規約文書が見つかりません: {naming_doc_path}")
        return False

    with open(naming_doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # メタデータを準備
    metadata = {
        "category": "elder_governance",
        "subcategory": "naming_conventions",
        "author": "Grand Elder maru",
        "approved_by": "Claude Elder",
        "created_date": "2025-07-08",
        "importance": "critical",
        "tags": ["Elder Tree", "Elders Guild", "naming", "governance", "hierarchy"],
        "version": "1.0",
    }

    # PostgreSQLに保存
    print("📝 PostgreSQLへの保存を実行中...")

    result = adapter.add_knowledge(
        spell_name="Elder_Tree_and_Elders_Guild_Naming_Conventions",
        content=content,
        metadata=metadata,
        save_to_legacy=True,  # レガシーシステムにも保存
    )

    if result["grimoire_saved"]:
        print("✅ PostgreSQL魔法書システムに保存成功！")
        print(f"   Spell ID: {result['spell_id']}")

        # 直接PostgreSQLで確認
        try:
            db_url = os.getenv(
                "GRIMOIRE_DATABASE_URL",
                "postgresql://aicompany@localhost:5432/ai_company_grimoire",
            )

            # psqlコマンドで確認
            sql_query = """
                SELECT spell_name, category, metadata->>'importance' as importance,
                       created_at, LENGTH(content) as content_length
                FROM knowledge_grimoire
                WHERE spell_name = 'Elder_Tree_and_Elders_Guild_Naming_Conventions'
                ORDER BY created_at DESC
                LIMIT 1;
            """

            result = subprocess.run(
                ["psql", db_url, "-t", "-A", "-F", "|||", "-c", sql_query],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0 and result.stdout.strip():
                row = result.stdout.strip().split("|||")
                if len(row) >= 5:
                    print("\n📊 保存確認:")
                    print(f"   呪文名: {row[0]}")
                    print(f"   カテゴリ: {row[1]}")
                    print(f"   重要度: {row[2]}")
                    print(f"   作成日時: {row[3]}")
                    print(f"   コンテンツサイズ: {row[4]}文字")

        except Exception as e:
            print(f"⚠️  PostgreSQL直接確認でエラー: {e}")

    else:
        print(f"❌ PostgreSQL保存失敗: {result.get('error', 'Unknown error')}")

    if result["legacy_saved"]:
        print("✅ レガシーシステムにもバックアップ保存完了")

    # 追加で関連概念も保存
    print("\n🔗 関連概念の保存...")

    # Elder Tree概念
    elder_tree_content = """# Elder Tree (エルダーツリー)

## 定義
エルダーツリーとは、グランドエルダーmaruを頂点とする階層構造全体を指す、Elders Guildの組織構造の中核概念。

## 階層構造
1. **根 (Root)**: グランドエルダーmaru - 全体統治
2. **幹 (Trunk)**: クロードエルダー - 実行責任者
3. **主要な枝 (Main Branches)**: 4賢者システム
4. **支える枝 (Supporting Branches)**: エルダー評議会
5. **葉 (Leaves)**: エルダーサーバント各部隊

この階層構造により、明確な指揮命令系統と責任分担が実現される。
"""

    elder_tree_result = adapter.add_knowledge(
        spell_name="Elder_Tree_Concept",
        content=elder_tree_content,
        metadata={
            "category": "elder_governance",
            "subcategory": "organizational_structure",
            "parent_concept": "Elder_Tree_and_Elders_Guild_Naming_Conventions",
            "importance": "high",
        },
    )

    if elder_tree_result["grimoire_saved"]:
        print("✅ Elder Tree概念保存成功")

    # Elders Guild概念
    elders_guild_content = """# Elders Guild (エルダーズギルド)

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
- ギルドメンバー: エルダーサーバント
"""

    elders_guild_result = adapter.add_knowledge(
        spell_name="Elders_Guild_Concept",
        content=elders_guild_content,
        metadata={
            "category": "elder_governance",
            "subcategory": "organizational_identity",
            "parent_concept": "Elder_Tree_and_Elders_Guild_Naming_Conventions",
            "importance": "high",
        },
    )

    if elders_guild_result["grimoire_saved"]:
        print("✅ Elders Guild概念保存成功")

    print("\n🎉 エルダー命名規約のPostgreSQL保存プロセス完了！")

    # システム状態を確認
    status = adapter.get_system_status()
    print("\n📊 システム状態:")
    print(
        f"   魔法書システム: {'有効' if status['grimoire_system']['enabled'] else '無効'}"
    )
    print(
        f"   利用可能: {'はい' if status['grimoire_system']['available'] else 'いいえ'}"
    )
    print(f"   タイプ: {status['grimoire_system'].get('type', 'unknown')}")

    return True


if __name__ == "__main__":
    # 実行
    success = save_elder_naming_conventions()

    if success:
        print("\n✅ すべての処理が正常に完了しました")
        print("📚 エルダーツリーとエルダーズギルドの概念がPostgreSQLに永続化されました")
    else:
        print("\n❌ 処理中にエラーが発生しました")
        sys.exit(1)
