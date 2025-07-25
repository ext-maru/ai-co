#!/usr/bin/env python3
"""
エルダーズギルド永続呪文保存スクリプト
Script to eternalize critical Elder spells in PostgreSQL
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

# データベースURL
DB_URL = "postgresql://aicompany@localhost:5432/ai_company_grimoire"


def escape_content(content):
    """SQLインジェクション防止のためのエスケープ"""
    return content.replace("'", "''")


def save_spell_to_postgresql(spell_data):
    """単一の呪文をPostgreSQLに保存"""
    current_time = datetime.now().isoformat()

    # エスケープ処理
    content_escaped = escape_content(spell_data["content"])

    # タグをSQL配列形式に
    tags_sql = "ARRAY[" + ",".join([f"'{tag}'" for tag in spell_data["tags"]]) + "]"

    # 進化履歴
    evolution_history = json.dumps(
        [
            {
                "version": 1,
                "date": current_time,
                "author": "Claude Elder",
                "reason": f"Eternal preservation of {spell_data['spell_name']}",
            }
        ]
    )

    # 既存エントリをチェック
    check_sql = f"SELECT id FROM knowledge_grimoire WHERE spell_name = '{spell_data['spell_name']}' LIMIT 1;"
    check_result = subprocess.run(
        ["psql", DB_URL, "-t", "-A", "-c", check_sql], capture_output=True, text=True
    )

    if check_result.returncode == 0 and check_result.stdout.strip():
        # 更新
        existing_id = check_result.stdout.strip()
        sql = f"""
        UPDATE knowledge_grimoire
        SET content = '{content_escaped}',
            spell_type = '{spell_data['spell_type']}',
            magic_school = '{spell_data['magic_school']}',
            tags = {tags_sql},
            power_level = {spell_data['power_level']},
            is_eternal = {spell_data['is_eternal']},
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
            '{spell_data['spell_name']}',
            '{content_escaped}',
            '{spell_data['spell_type']}',
            '{spell_data['magic_school']}',
            {tags_sql},
            {spell_data['power_level']},
            {spell_data['is_eternal']},
            '{evolution_history}'::jsonb,
            '{current_time}',
            '{current_time}'
        );
        """

    result = subprocess.run(["psql", DB_URL, "-c", sql], capture_output=True, text=True)

    if result.returncode == 0:
        print(
            f"✅ {spell_data['spell_name']} 永続化成功 (Power: {spell_data['power_level']})"
        )
        return True
    else:
        print(f"❌ {spell_data['spell_name']} 永続化失敗: {result.stderr}")
        return False


def load_file_content(file_path):
    """ファイルからコンテンツを読み込む"""
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def eternalize_elder_spells():
    """エルダーズギルドの永続呪文を保存"""
    print("🏛️ エルダーズギルド永続呪文の保存開始")
    print("=" * 60)

    project_root = Path(__file__).resolve().parent.parent
    kb_path = project_root / "knowledge_base"

    # 永続化すべき呪文のリスト
    eternal_spells = [
        # エルダー魔法 (Power Level 10)
        {
            "spell_name": "Grand_Elder_Maru_Hierarchy",
            "file_path": kb_path / "GRAND_ELDER_MARU_HIERARCHY.md",
            "spell_type": "governance",
            "magic_school": "elder_magic",
            "power_level": 10,
            "is_eternal": "true",
            "tags": ["hierarchy", "grand-elder", "governance", "critical", "maru"],
        },
        {
            "spell_name": "Claude_Elder_Identity_Core",
            "file_path": project_root / "CLAUDE.md",
            "spell_type": "identity",
            "magic_school": "elder_magic",
            "power_level": 10,
            "is_eternal": "true",
            "tags": ["claude-elder", "identity", "responsibilities", "critical"],
        },
        {
            "spell_name": "AI_Company_Unified_Standards_2025",
            "file_path": kb_path / "AI_COMPANY_UNIFIED_STANDARDS_2025.0.md",
            "spell_type": "standards",
            "magic_school": "elder_magic",
            "power_level": 10,
            "is_eternal": "true",
            "tags": ["standards", "unified", "2025", "critical", "terminology"],
        },
        # 開発魔法 (Power Level 10)
        {
            "spell_name": "TDD_Mandatory_Rule",
            "file_path": kb_path / "CLAUDE_TDD_GUIDE.md",
            "spell_type": "development",
            "magic_school": "development_magic",
            "power_level": 10,
            "is_eternal": "true",
            "tags": ["tdd", "development", "mandatory", "quality", "testing"],
        },
        {
            "spell_name": "Incident_Sage_Consultation_Rule",
            "content": """# インシデント賢者相談義務ルール

**制定日**: 2025年7月8日
**制定者**: エルダー評議会
**承認者**: グランドエルダーmaru

## 必須ルール

クロードエルダーは、すべてのコード作成前に必ずインシデント賢者に相談しなければならない。

### 理由
- エラー予防の徹底
- 品質保証の強化
- インシデント発生の未然防止

### 実施方法
1.0 コード実装前にインシデント賢者を召喚
2.0 潜在的リスクの分析を依頼
3.0 推奨事項を受け取ってから実装開始

### 違反時の対応
- インシデント賢者からの自動警告
- エルダー評議会への報告

このルールは永続的であり、変更にはグランドエルダーmaruの承認が必要。""",
            "spell_type": "rule",
            "magic_school": "development_magic",
            "power_level": 9,
            "is_eternal": "true",
            "tags": ["consultation", "incident-sage", "error-prevention", "mandatory"],
        },
        {
            "spell_name": "Quality_First_Hierarchy_Order",
            "content": """# 品質第一×階層秩序

**グランドエルダーmaruの基本理念**

## 原則

### 品質第一
- すべての開発において品質を最優先する
- 99.999%の稼働率を目指す
- バグゼロを追求する

### 階層秩序
- グランドエルダーmaruを頂点とする明確な階層
- 各階層の責任と権限の明確化
- 上位者への敬意と下位者への配慮

## 実践方法
1.0 TDDによる品質保証
2.0 4賢者システムによる自律的品質管理
3.0 エルダー評議会による継続的監視
4.0 エルダーサーバントによる実行

この理念はElders Guild存続の根幹である。""",
            "spell_type": "philosophy",
            "magic_school": "development_magic",
            "power_level": 10,
            "is_eternal": "true",
            "tags": ["quality", "hierarchy", "philosophy", "grand-elder", "critical"],
        },
        # 賢者の知恵 (Power Level 9)
        {
            "spell_name": "Four_Sages_System_Definition",
            "content": """# 4賢者システム定義

## 概要
Elders Guildの中核を成す4つの賢者による自律的管理システム。

## 4賢者の構成

### 📚 ナレッジ賢者 (Knowledge Sage)
- 役割: 知識の蓄積と継承
- 場所: knowledge_base/
- 機能: 学習、進化、知恵の提供

### 📋 タスク賢者 (Task Oracle)
- 役割: プロジェクト進捗管理
- 場所: libs/claude_task_tracker.py
- 機能: 計画立案、優先順位判断

### 🚨 インシデント賢者 (Crisis Sage)
- 役割: 危機対応と品質保証
- 場所: libs/incident_manager.py
- 機能: エラー検知、自動復旧

### 🔍 RAG賢者 (Search Mystic)
- 役割: 情報探索と理解
- 場所: libs/rag_manager.py
- 機能: コンテキスト検索、最適解発見

## 協調の魔法
4賢者は相互に連携し、Elders Guildの自律的運営を実現する。""",
            "spell_type": "system",
            "magic_school": "sage_wisdom",
            "power_level": 9,
            "is_eternal": "true",
            "tags": ["four-sages", "system-core", "coordination", "autonomous"],
        },
        {
            "spell_name": "Four_Sages_Coordination_Magic",
            "file_path": kb_path / "four_sages_collaboration_magic.md",
            "spell_type": "magic",
            "magic_school": "sage_wisdom",
            "power_level": 9,
            "is_eternal": "true",
            "tags": ["four-sages", "coordination", "magic", "collaboration"],
        },
        # システム構造 (Power Level 8)
        {
            "spell_name": "Project_Structure_Definition",
            "content": """# Elders Guild プロジェクト構造

## ディレクトリ構造
```
/home/aicompany/ai_co/
├── workers/          # ワーカー実装
├── libs/            # ライブラリ（4賢者含む）
├── tests/           # テスト（TDD必須）
├── knowledge_base/  # ナレッジベース
├── commands/        # コマンド群
├── templates/       # テンプレート
├── scripts/         # スクリプト
└── web/            # Webインターフェース
```

## 主要コンポーネント
- RabbitMQ: メッセージキュー
- Claude API: AI処理
- Slack: 通知システム
- SQLite/PostgreSQL: データ永続化

この構造は慎重に設計されており、変更には十分な検討が必要。""",
            "spell_type": "architecture",
            "magic_school": "system_architecture",
            "power_level": 8,
            "is_eternal": "true",
            "tags": ["architecture", "structure", "components", "directories"],
        },
        {
            "spell_name": "Elder_Servants_Organization",
            "file_path": kb_path / "elder_servants_system_definition.md",
            "spell_type": "organization",
            "magic_school": "system_architecture",
            "power_level": 8,
            "is_eternal": "true",
            "tags": ["workers", "servants", "organization", "fantasy"],
        },
        {
            "spell_name": "Fantasy_Classification_System",
            "file_path": kb_path / "fantasy_task_classification_system.md",
            "spell_type": "classification",
            "magic_school": "system_architecture",
            "power_level": 8,
            "is_eternal": "true",
            "tags": ["fantasy", "classification", "tasks", "incidents"],
        },
    ]

    success_count = 0
    failed_count = 0

    for spell in eternal_spells:
        print(f"\n📜 処理中: {spell['spell_name']}")

        # コンテンツの取得
        if "content" not in spell:
            if "file_path" in spell and spell["file_path"]:
                content = load_file_content(spell["file_path"])
                if content:
                    spell["content"] = content
                else:
                    print(f"⚠️  ファイルが見つかりません: {spell['file_path']}")
                    # 代替コンテンツを使用
                    spell["content"] = (
                        f"# {spell['spell_name']}\n\n[Content to be loaded from file: {spell['file_path']}]"
                    )

        # PostgreSQLに保存
        if save_spell_to_postgresql(spell):
            success_count += 1
        else:
            failed_count += 1

    # 最終統計
    print("\n" + "=" * 60)
    print("📊 永続化結果統計:")
    print(f"   ✅ 成功: {success_count} 呪文")
    print(f"   ❌ 失敗: {failed_count} 呪文")

    # 永続化された呪文の確認
    print("\n🔍 永続化された呪文の確認中...")
    check_sql = """
    SELECT spell_name, magic_school, power_level, is_eternal,
           array_to_string(tags, ', ') as tags
    FROM knowledge_grimoire
    WHERE is_eternal = true
    ORDER BY power_level DESC, magic_school, spell_name;
    """

    check_result = subprocess.run(
        ["psql", DB_URL, "-c", check_sql], capture_output=True, text=True
    )

    if check_result.returncode == 0:
        print("\n📚 現在の永続呪文一覧:")
        print(check_result.stdout)

    return success_count, failed_count


if __name__ == "__main__":
    print("🏛️ エルダーズギルド永続呪文システム")
    print("🔮 これらの呪文は永遠に保存され、Elders Guildの礎となります")
    print()

    success, failed = eternalize_elder_spells()

    if failed == 0:
        print("\n🎉 すべての永続呪文が正常に保存されました！")
        print("✨ エルダーズギルドの知恵は永遠に継承されます")
    else:
        print(f"\n⚠️  一部の呪文の保存に失敗しました（{failed}件）")
        print("📝 ログを確認して再実行してください")
