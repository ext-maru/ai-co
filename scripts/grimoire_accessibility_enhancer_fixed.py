#!/usr/bin/env python3
"""
グリモアアクセス性向上システム
4賢者の魔法書システムをより使いやすく、アクセスしやすくする
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GrimoireAccessibilityEnhancer:
    """グリモアアクセス性向上システム"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.grimoire_base = self.project_root / "knowledge_base" / "four_sages_grimoires"
        self.access_log = self.project_root / "logs" / "grimoire_accessibility.log"
        self.access_log.parent.mkdir(exist_ok=True)

        # アクセス性向上の各フェーズ
        self.enhancement_phases = {
            "index_generation": False,
            "cross_referencing": False,
            "search_optimization": False,
            "navigation_improvement": False,
            "quick_access_tools": False,
        }

        # 既存の魔法書構造
        self.grimoire_structure = {
            "knowledge_sage": "01_knowledge_sage_grimoire.md",
            "task_oracle": "02_task_oracle_grimoire.md",
            "incident_sage": "03_incident_sage_grimoire.md",
            "rag_mystic": "04_rag_mystic_grimoire.md",
            "common_knowledge": "00_common_knowledge.md",
        }

    def enhance_accessibility(self) -> Dict[str, Any]:
        """アクセス性向上の実行"""
        print("🔮 グリモアアクセス性向上を開始...")

        enhancement_results = {
            "timestamp": datetime.now().isoformat(),
            "phases": {},
            "improvements": [],
            "overall_status": "enhancing",
            "metrics": {},
        }

        # Phase 1: 索引生成
        phase1_result = self._generate_comprehensive_index()
        enhancement_results["phases"]["index_generation"] = phase1_result

        # Phase 2: 相互参照システム
        phase2_result = self._create_cross_reference_system()
        enhancement_results["phases"]["cross_referencing"] = phase2_result

        # Phase 3: 検索最適化
        phase3_result = self._optimize_search_functionality()
        enhancement_results["phases"]["search_optimization"] = phase3_result

        # Phase 4: ナビゲーション改善
        phase4_result = self._improve_navigation()
        enhancement_results["phases"]["navigation_improvement"] = phase4_result

        # Phase 5: クイックアクセスツール
        phase5_result = self._create_quick_access_tools()
        enhancement_results["phases"]["quick_access_tools"] = phase5_result

        # 総合評価
        enhancement_results["overall_status"] = self._assess_enhancement_status()
        enhancement_results["improvements"] = self._collect_improvements()
        enhancement_results["metrics"] = self._calculate_metrics()

        return enhancement_results

    def _generate_comprehensive_index(self) -> Dict[str, Any]:
        """包括的索引の生成"""
        print("  📚 包括的索引を生成中...")

        index_result = {"status": "generating", "master_index": {}, "topic_index": {}, "generated_files": []}

        try:
            # 索引ファイルの生成
            index_files = self._create_index_files()
            index_result["generated_files"] = index_files

            index_result["status"] = "completed"
            self.enhancement_phases["index_generation"] = True

        except Exception as e:
            index_result["status"] = "failed"
            index_result["error"] = str(e)

        self._log_enhancement("Index generation", index_result["status"])
        return index_result

    def _create_index_files(self) -> List[str]:
        """索引ファイルの作成"""
        generated_files = []

        # マスター索引ファイル
        master_index_path = self.grimoire_base / "MASTER_INDEX.md"
        master_content = self._generate_master_index_content()
        with open(master_index_path, "w", encoding="utf-8") as f:
            f.write(master_content)
        generated_files.append(str(master_index_path))

        # トピック別索引ファイル
        topic_index_path = self.grimoire_base / "TOPIC_INDEX.md"
        topic_content = self._generate_topic_index_content()
        with open(topic_index_path, "w", encoding="utf-8") as f:
            f.write(topic_content)
        generated_files.append(str(topic_index_path))

        # クイックリファレンスファイル
        quick_ref_path = self.grimoire_base / "QUICK_REFERENCE.md"
        quick_content = self._generate_quick_reference_content()
        with open(quick_ref_path, "w", encoding="utf-8") as f:
            f.write(quick_content)
        generated_files.append(str(quick_ref_path))

        return generated_files

    def _generate_master_index_content(self) -> str:
        """マスター索引コンテンツの生成"""
        content = f"""# 🏛️ 4賢者グリモア マスター索引

**最終更新**: {datetime.now().isoformat()}
**総エントリ数**: {len(self.grimoire_structure)}

## 📊 統計情報

### 賢者別グリモア
- **knowledge_sage**: 01_knowledge_sage_grimoire.md
- **task_oracle**: 02_task_oracle_grimoire.md
- **incident_sage**: 03_incident_sage_grimoire.md
- **rag_mystic**: 04_rag_mystic_grimoire.md
- **common_knowledge**: 00_common_knowledge.md

### カテゴリ別分布
- **error_handling**: エラー対応関連
- **testing**: TDD・テスト関連
- **performance**: パフォーマンス最適化
- **configuration**: 設定・セットアップ
- **general**: 一般的な知識

## 📚 グリモア詳細

### 📚 ナレッジ賢者
- 過去の英知を蓄積・継承
- 学習による知恵の進化
- 経験の蓄積と活用

### 📋 タスク賢者
- プロジェクト進捗管理
- 最適な実行順序の導出
- 優先順位付けと追跡

### 🚨 インシデント賢者
- 危機対応専門家
- 問題の即座感知・解決
- 予防策の立案

### 🔍 RAG賢者
- 情報探索と理解
- 膨大な知識から最適解発見
- 知識統合とコンテキスト理解

### 🌟 共通知識
- 4賢者共通の基本知識
- 階層構造とプロトコル
- 基本ルールと手順
"""
        return content

    def _generate_topic_index_content(self) -> str:
        """トピック別索引コンテンツの生成"""
        content = f"""# 🔍 4賢者グリモア トピック別索引

**生成日時**: {datetime.now().isoformat()}

## 📋 主要トピック一覧

### TDD・テスト
- テスト駆動開発の手法
- ユニットテストの実装
- テストカバレッジの向上

### パフォーマンス最適化
- システム性能の向上
- メモリ使用量の最適化
- 処理速度の改善

### エラー対応
- 例外処理の実装
- エラーログの分析
- 障害復旧手順

### データベース
- PostgreSQL活用
- SQLクエリ最適化
- データ整合性管理

### API設計
- RESTful API設計
- エンドポイント実装
- サービス間通信

### セキュリティ
- 認証・認可システム
- セキュリティ監査
- 脆弱性対策

### 設定・環境
- 環境変数管理
- 設定ファイル構造
- デプロイメント手順

### デプロイメント
- 本番環境への展開
- CI/CDパイプライン
- 監視とアラート
"""
        return content

    def _generate_quick_reference_content(self) -> str:
        """クイックリファレンスコンテンツの生成"""
        content = f"""# ⚡ 4賢者グリモア クイックリファレンス

**生成日時**: {datetime.now().isoformat()}

## 🚀 よく使用される項目

### エラー対応
- **例外処理**: インシデント賢者の専門分野
- **ログ分析**: RAG賢者による情報検索
- **復旧手順**: ナレッジ賢者の蓄積知識
- **予防策**: タスク賢者による計画的対応

### パフォーマンス最適化
- **メモリ最適化**: システム全体のメモリ使用量改善
- **処理速度向上**: アルゴリズムとデータ構造の最適化
- **データベース最適化**: クエリ性能とインデックス設計
- **キャッシュ戦略**: 効率的なキャッシュ実装

### TDD・テスト
- **テスト駆動開発**: RED-GREEN-REFACTORサイクル
- **ユニットテスト**: 個別機能のテスト実装
- **統合テスト**: システム全体の動作確認
- **テストカバレッジ**: コードカバレッジの向上

## 🔗 賢者間相互参照

- **ナレッジ賢者** ↔ **RAG賢者**: 知識検索と統合
- **タスク賢者** ↔ **インシデント賢者**: 問題対応と進捗管理
- **全賢者** ↔ **共通知識**: 基本プロトコルと階層構造

## 🎯 使用方法

1. **問題解決**: まずこのクイックリファレンスを確認
2. **詳細調査**: 該当する賢者のグリモアを参照
3. **横断検索**: トピック別索引で関連知識を検索
4. **包括検索**: マスター索引で全体から検索

## 📞 緊急時の対応

### 🚨 システム障害
1. インシデント賢者に即座に相談
2. 類似事例をRAG賢者で検索
3. 復旧手順をナレッジ賢者で確認
4. 進捗をタスク賢者で管理

### 🔧 開発問題
1. 該当分野の専門賢者に相談
2. 共通知識で基本手順を確認
3. 過去の解決事例を検索
4. 新しい知識として蓄積

---

**💡 ヒント**: 迷ったときは共通知識（00_common_knowledge.md）から始めよう！
"""
        return content

    def _create_cross_reference_system(self) -> Dict[str, Any]:
        """相互参照システムの作成"""
        print("  🔗 相互参照システムを構築中...")

        cross_ref_result = {"status": "creating", "references_added": 0}

        try:
            # 各魔法書に相互参照を追加
            for sage_name, grimoire_file in self.grimoire_structure.items():
                grimoire_path = self.grimoire_base / grimoire_file

                if grimoire_path.exists():
                    self._add_cross_references_to_grimoire(grimoire_path, sage_name)
                    cross_ref_result["references_added"] += 1

            cross_ref_result["status"] = "completed"
            self.enhancement_phases["cross_referencing"] = True

        except Exception as e:
            cross_ref_result["status"] = "failed"
            cross_ref_result["error"] = str(e)

        self._log_enhancement("Cross-reference system", cross_ref_result["status"])
        return cross_ref_result

    def _add_cross_references_to_grimoire(self, grimoire_path: Path, sage_name: str):
        """魔法書に相互参照を追加"""
        try:
            with open(grimoire_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 相互参照セクションがない場合は追加
            if "## 🔗 関連する賢者の知識" not in content:
                cross_ref_section = self._generate_cross_reference_section(sage_name)
                content += "\n\n" + cross_ref_section

                with open(grimoire_path, "w", encoding="utf-8") as f:
                    f.write(content)

        except Exception as e:
            logger.error(f"Error adding cross-references to {grimoire_path}: {e}")

    def _generate_cross_reference_section(self, sage_name: str) -> str:
        """相互参照セクションの生成"""
        cross_refs = {
            "knowledge_sage": [
                "📋 **タスク賢者**: 学習タスクの管理と進捗追跡",
                "🔍 **RAG賢者**: 知識検索と情報統合",
                "🚨 **インシデント賢者**: 学習失敗の記録と対策",
            ],
            "task_oracle": [
                "📚 **ナレッジ賢者**: タスク実行のための知識参照",
                "🔍 **RAG賢者**: タスク情報の検索と分析",
                "🚨 **インシデント賢者**: タスク失敗の対応と学習",
            ],
            "incident_sage": [
                "📚 **ナレッジ賢者**: インシデント対応の知識蓄積",
                "📋 **タスク賢者**: 復旧タスクの管理と追跡",
                "🔍 **RAG賢者**: 類似インシデントの検索と分析",
            ],
            "rag_mystic": [
                "📚 **ナレッジ賢者**: 検索結果の知識化と蓄積",
                "📋 **タスク賢者**: 検索タスクの効率化",
                "🚨 **インシデント賢者**: 検索失敗の分析と改善",
            ],
        }

        section = "## 🔗 関連する賢者の知識\n\n"

        if sage_name in cross_refs:
            for ref in cross_refs[sage_name]:
                section += f"- {ref}\n"

        section += "\n### 📊 共通プロトコル\n\n"
        section += "- **00_common_knowledge.md**: 4賢者共通の基本知識\n"
        section += "- **MASTER_INDEX.md**: 全魔法書の統合索引\n"
        section += "- **TOPIC_INDEX.md**: トピック別知識索引\n"
        section += "- **QUICK_REFERENCE.md**: よく使用される知識\n"

        return section

    def _optimize_search_functionality(self) -> Dict[str, Any]:
        """検索機能最適化"""
        print("  🔍 検索機能を最適化中...")

        search_result = {"status": "optimizing", "search_tools": []}

        try:
            # 検索ツールの作成
            search_tools = self._create_search_tools()
            search_result["search_tools"] = search_tools

            search_result["status"] = "completed"
            self.enhancement_phases["search_optimization"] = True

        except Exception as e:
            search_result["status"] = "failed"
            search_result["error"] = str(e)

        self._log_enhancement("Search optimization", search_result["status"])
        return search_result

    def _create_search_tools(self) -> List[str]:
        """検索ツールの作成"""
        tools = []

        # 検索設定ファイルの作成
        search_config_path = self.project_root / "config" / "grimoire_search_config.json"
        search_config_path.parent.mkdir(exist_ok=True)

        search_config = {
            "grimoire_paths": {sage: str(self.grimoire_base / file) for sage, file in self.grimoire_structure.items()},
            "search_options": {"case_sensitive": False, "whole_word": False, "regex_enabled": True, "max_results": 50},
            "index_files": {
                "master_index": str(self.grimoire_base / "MASTER_INDEX.md"),
                "topic_index": str(self.grimoire_base / "TOPIC_INDEX.md"),
                "quick_reference": str(self.grimoire_base / "QUICK_REFERENCE.md"),
            },
        }

        with open(search_config_path, "w", encoding="utf-8") as f:
            json.dump(search_config, f, indent=2, ensure_ascii=False)
        tools.append(str(search_config_path))

        return tools

    def _improve_navigation(self) -> Dict[str, Any]:
        """ナビゲーション改善"""
        print("  🧭 ナビゲーションを改善中...")

        nav_result = {"status": "improving", "navigation_files": []}

        try:
            # ナビゲーションファイルの作成
            nav_files = self._create_navigation_files()
            nav_result["navigation_files"] = nav_files

            nav_result["status"] = "completed"
            self.enhancement_phases["navigation_improvement"] = True

        except Exception as e:
            nav_result["status"] = "failed"
            nav_result["error"] = str(e)

        self._log_enhancement("Navigation improvement", nav_result["status"])
        return nav_result

    def _create_navigation_files(self) -> List[str]:
        """ナビゲーションファイルの作成"""
        nav_files = []

        # README.mdの作成
        readme_path = self.grimoire_base / "README.md"
        readme_content = self._generate_readme_content()
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        nav_files.append(str(readme_path))

        return nav_files

    def _generate_readme_content(self) -> str:
        """README.mdコンテンツの生成"""
        content = f"""# 🏛️ 4賢者グリモア - ナビゲーションガイド

**最終更新**: {datetime.now().isoformat()}

## 🧙‍♂️ 4賢者の魔法書

### 📚 **ナレッジ賢者 (Knowledge Sage)**
- **ファイル**: `01_knowledge_sage_grimoire.md`
- **役割**: 過去の英知を蓄積・継承、学習による知恵の進化
- **主な内容**: 学習パターン、知識統合、経験の蓄積

### 📋 **タスク賢者 (Task Oracle)**
- **ファイル**: `02_task_oracle_grimoire.md`
- **役割**: プロジェクト進捗管理、最適な実行順序の導出
- **主な内容**: タスク管理、優先順位付け、進捗追跡

### 🚨 **インシデント賢者 (Crisis Sage)**
- **ファイル**: `03_incident_sage_grimoire.md`
- **役割**: 危機対応専門家、問題の即座感知・解決
- **主な内容**: エラー対応、障害復旧、予防策

### 🔍 **RAG賢者 (Search Mystic)**
- **ファイル**: `04_rag_mystic_grimoire.md`
- **役割**: 情報探索と理解、膨大な知識から最適解発見
- **主な内容**: 検索技術、情報統合、知識発見

### 🌟 **共通知識**
- **ファイル**: `00_common_knowledge.md`
- **役割**: 4賢者共通の基本知識とプロトコル
- **主な内容**: 階層構造、基本ルール、共通手順

## 📖 索引・参照ファイル

### 📚 **MASTER_INDEX.md**
- 全魔法書の統合索引
- 賢者別・カテゴリ別エントリ一覧
- 詳細な内容プレビュー

### 🔍 **TOPIC_INDEX.md**
- トピック別知識索引
- 主要テーマごとの関連エントリ
- 横断的な知識参照

### ⚡ **QUICK_REFERENCE.md**
- よく使用される知識のクイックアクセス
- エラー対応、パフォーマンス最適化、TDD
- 賢者間の相互参照

## 🎯 使用方法

1. **問題解決**: まずQUICK_REFERENCE.mdを確認
2. **詳細調査**: 該当する賢者のグリモアを参照
3. **横断検索**: TOPIC_INDEX.mdでトピック別検索
4. **包括検索**: MASTER_INDEX.mdで全体から検索

## 🔗 賢者間の連携

- **問題発生時**: インシデント賢者 → 他賢者への相談
- **学習時**: ナレッジ賢者 → RAG賢者での情報収集
- **タスク実行時**: タスク賢者 → 各賢者の専門知識参照

---

**💡 ヒント**: 迷ったときは共通知識（00_common_knowledge.md）から始めよう！
"""
        return content

    def _create_quick_access_tools(self) -> Dict[str, Any]:
        """クイックアクセスツールの作成"""
        print("  ⚡ クイックアクセスツールを作成中...")

        tools_result = {"status": "creating", "tools": []}

        try:
            # クイックアクセススクリプトの作成
            tools = self._create_quick_access_scripts()
            tools_result["tools"] = tools

            tools_result["status"] = "completed"
            self.enhancement_phases["quick_access_tools"] = True

        except Exception as e:
            tools_result["status"] = "failed"
            tools_result["error"] = str(e)

        self._log_enhancement("Quick access tools", tools_result["status"])
        return tools_result

    def _create_quick_access_scripts(self) -> List[str]:
        """クイックアクセススクリプトの作成"""
        tools = []

        # クイックヘルプスクリプト
        help_script_path = self.project_root / "scripts" / "grimoire_help.py"
        help_content = self._generate_help_script_content()
        with open(help_script_path, "w", encoding="utf-8") as f:
            f.write(help_content)
        tools.append(str(help_script_path))

        return tools

    def _generate_help_script_content(self) -> str:
        """ヘルプスクリプトコンテンツの生成"""
        content = '''#!/usr/bin/env python3
"""
4賢者グリモア クイックヘルプ
"""

import sys
from pathlib import Path

def show_help(topic=None):
    """ヘルプ表示"""
    if topic is None:
        print("🏛️ 4賢者グリモア - クイックヘルプ")
        print("=" * 50)
        print("使用法: python grimoire_help.py [トピック]")
        print("")
        print("📚 利用可能なトピック:")
        print("- sages: 4賢者の概要")
        print("- files: グリモアファイル一覧")
        print("- search: 検索方法")
        print("- index: 索引ファイルの使い方")
        print("- navigation: ナビゲーション方法")
        print("")
        print("例: python grimoire_help.py sages")

    elif topic == "sages":
        print("🧙‍♂️ 4賢者の概要")
        print("=" * 30)
        print("📚 ナレッジ賢者: 知識の蓄積と継承")
        print("📋 タスク賢者: 進捗管理と実行順序")
        print("🚨 インシデント賢者: 問題対応と復旧")
        print("🔍 RAG賢者: 情報検索と統合")

    elif topic == "files":
        print("📁 グリモアファイル一覧")
        print("=" * 30)
        print("00_common_knowledge.md - 共通知識")
        print("01_knowledge_sage_grimoire.md - ナレッジ賢者")
        print("02_task_oracle_grimoire.md - タスク賢者")
        print("03_incident_sage_grimoire.md - インシデント賢者")
        print("04_rag_mystic_grimoire.md - RAG賢者")
        print("")
        print("📖 索引ファイル:")
        print("MASTER_INDEX.md - 統合索引")
        print("TOPIC_INDEX.md - トピック別索引")
        print("QUICK_REFERENCE.md - クイックリファレンス")
        print("README.md - ナビゲーションガイド")

    else:
        print(f"❌ 不明なトピック: {topic}")
        print("利用可能なトピック: sages, files, search, index, navigation")

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else None
    show_help(topic)
'''
        return content

    def _assess_enhancement_status(self) -> str:
        """改善状況の評価"""
        completed_phases = sum(self.enhancement_phases.values())
        total_phases = len(self.enhancement_phases)

        if completed_phases == total_phases:
            return "fully_enhanced"
        elif completed_phases >= total_phases * 0.8:
            return "mostly_enhanced"
        elif completed_phases >= total_phases * 0.5:
            return "partially_enhanced"
        else:
            return "needs_enhancement"

    def _collect_improvements(self) -> List[str]:
        """改善項目の収集"""
        improvements = []

        if self.enhancement_phases["index_generation"]:
            improvements.append("📚 統合索引システムの構築")

        if self.enhancement_phases["cross_referencing"]:
            improvements.append("🔗 賢者間相互参照システムの実装")

        if self.enhancement_phases["search_optimization"]:
            improvements.append("🔍 検索機能の最適化")

        if self.enhancement_phases["navigation_improvement"]:
            improvements.append("🧭 ナビゲーション機能の改善")

        if self.enhancement_phases["quick_access_tools"]:
            improvements.append("⚡ クイックアクセスツールの提供")

        return improvements

    def _calculate_metrics(self) -> Dict[str, Any]:
        """メトリクスの計算"""
        metrics = {
            "total_grimoires": len(self.grimoire_structure),
            "enhancement_completion": sum(self.enhancement_phases.values()) / len(self.enhancement_phases) * 100,
            "generated_files": 0,
        }

        # 生成されたファイル数をカウント
        generated_files = ["MASTER_INDEX.md", "TOPIC_INDEX.md", "QUICK_REFERENCE.md", "README.md"]

        for file_name in generated_files:
            file_path = self.grimoire_base / file_name
            if file_path.exists():
                metrics["generated_files"] += 1

        return metrics

    def _log_enhancement(self, phase_name: str, status: str):
        """改善ログの記録"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {phase_name}: {status}\n"

        with open(self.access_log, "a", encoding="utf-8") as f:
            f.write(log_entry)


def main():
    """メイン処理"""
    enhancer = GrimoireAccessibilityEnhancer()

    print("🚀 グリモアアクセス性向上システム")
    print("=" * 60)

    # アクセス性向上の実行
    enhancement_results = enhancer.enhance_accessibility()

    # 結果表示
    print("\n📊 改善結果サマリー")
    print("-" * 40)
    print(f"総合状況: {enhancement_results['overall_status'].upper()}")
    print(f"完了フェーズ: {sum(enhancer.enhancement_phases.values())}/{len(enhancer.enhancement_phases)}")
    print(f"改善完了率: {enhancement_results['metrics']['enhancement_completion']:.1f}%")

    # フェーズ別詳細
    print("\n🔍 フェーズ別状況")
    print("-" * 40)
    for phase_name, result in enhancement_results["phases"].items():
        status_icon = "✅" if result["status"] == "completed" else "❌"
        print(f"{status_icon} {phase_name}: {result['status'].upper()}")

    # 実装された改善項目
    print("\n💡 実装された改善項目")
    print("-" * 40)
    for i, improvement in enumerate(enhancement_results["improvements"], 1):
        print(f"{i}. {improvement}")

    # メトリクス
    metrics = enhancement_results["metrics"]
    print("\n📈 メトリクス")
    print("-" * 40)
    print(f"グリモア数: {metrics['total_grimoires']}")
    print(f"生成ファイル数: {metrics['generated_files']}")
    print(f"改善完了率: {metrics['enhancement_completion']:.1f}%")

    # 詳細レポート保存
    report_file = PROJECT_ROOT / "logs" / f"grimoire_accessibility_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(enhancement_results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n💾 詳細レポートを保存しました: {report_file}")

    # 使用方法の案内
    print("\n🎯 使用方法")
    print("-" * 40)
    print("1. README.md でナビゲーションガイドを確認")
    print("2. QUICK_REFERENCE.md でよく使用される知識をチェック")
    print("3. python scripts/grimoire_help.py でヘルプを表示")


if __name__ == "__main__":
    main()
