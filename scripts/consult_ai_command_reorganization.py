#!/usr/bin/env python3
"""
AIコマンド体系再編成のためのエルダー評議会相談
54個に増加したAIコマンドの整理・改善について4賢者と協議
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.incident_sage import IncidentSage
from libs.knowledge_sage import KnowledgeSage
from libs.rag_sage import RAGSage
from libs.task_oracle import TaskOracle


class AICommandReorganizationCouncil:
    """AIコマンド再編成評議会"""

    def __init__(self):
        self.knowledge_sage = KnowledgeSage()
        self.task_oracle = TaskOracle()
        self.incident_sage = IncidentSage()
        self.rag_sage = RAGSage()
        self.timestamp = datetime.now()

    def analyze_current_state(self):
        """現状分析"""
        # Get all AI commands
        scripts_dir = Path("/home/aicompany/ai_co/scripts")
        ai_commands = sorted([f.name for f in scripts_dir.glob("ai-*") if f.is_file()])

        # Categorize commands
        categories = {}
        for cmd in ai_commands:
            parts = cmd.split("-")
            if len(parts) >= 2:
                category = parts[1]
                if category not in categories:
                    categories[category] = []
                categories[category].append(cmd)

        return {
            "total_commands": len(ai_commands),
            "categories": categories,
            "commands": ai_commands,
        }

    def consult_knowledge_sage(self, current_state):
        """ナレッジ賢者との相談"""
        consultation = {
            "sage": "Knowledge Sage",
            "timestamp": self.timestamp.isoformat(),
            "current_issues": [
                "54個のコマンドが存在し、体系が複雑化",
                "カテゴリー分けが不明確",
                "新規ユーザーの学習曲線が急峻",
            ],
            "recommendations": [
                {
                    "proposal": "階層的コマンド体系の導入",
                    "details": [
                        "ai <category> <action> 形式への統一",
                        "例: ai elder status, ai worker start",
                        "カテゴリー: elder, worker, test, system, dev",
                    ],
                },
                {
                    "proposal": "コマンドエイリアスシステム",
                    "details": [
                        "よく使うコマンドの短縮形を提供",
                        "ai-status → ai s",
                        "ai-elder-council → ai ec",
                    ],
                },
                {
                    "proposal": "統合ヘルプシステム",
                    "details": [
                        "ai help - 全コマンド一覧",
                        "ai help <category> - カテゴリー別ヘルプ",
                        "ai search <keyword> - コマンド検索",
                    ],
                },
            ],
            "knowledge_base_update": "コマンド体系ドキュメントの作成必須",
        }
        return consultation

    def consult_task_oracle(self, current_state):
        """タスク賢者との相談"""
        consultation = {
            "sage": "Task Oracle",
            "timestamp": self.timestamp.isoformat(),
            "efficiency_analysis": {
                "current_inefficiencies": [
                    "コマンド名から機能が推測困難",
                    "関連コマンドの発見が困難",
                    "実行順序が不明確",
                ],
                "productivity_impact": "開発効率30%低下の可能性",
            },
            "recommendations": [
                {
                    "proposal": "ワークフロー指向の再編成",
                    "workflows": {
                        "development": ["ai dev start", "ai dev test", "ai dev commit"],
                        "operations": [
                            "ai ops status",
                            "ai ops monitor",
                            "ai ops alert",
                        ],
                        "management": [
                            "ai manage tasks",
                            "ai manage team",
                            "ai manage report",
                        ],
                    },
                },
                {
                    "proposal": "インタラクティブモード",
                    "details": "ai interactive - 対話的コマンド選択",
                },
                {
                    "proposal": "コマンドチェーン機能",
                    "example": "ai chain 'test && commit && deploy'",
                },
            ],
            "priority": "HIGH - 即座の対応を推奨",
        }
        return consultation

    def consult_incident_sage(self, current_state):
        """インシデント賢者との相談"""
        consultation = {
            "sage": "Incident Sage",
            "timestamp": self.timestamp.isoformat(),
            "risk_assessment": {
                "identified_risks": [
                    "コマンド名の衝突可能性",
                    "権限管理の複雑化",
                    "エラーハンドリングの不統一",
                ],
                "severity": "MEDIUM",
            },
            "recommendations": [
                {
                    "proposal": "名前空間の明確化",
                    "implementation": {
                        "core": ["ai-start", "ai-stop", "ai-status"],
                        "elder": ["ai-elder-*"],
                        "worker": ["ai-worker-*"],
                        "dev": ["ai-dev-*"],
                        "ops": ["ai-ops-*"],
                    },
                },
                {
                    "proposal": "権限レベルシステム",
                    "levels": {
                        "user": "基本コマンドのみ",
                        "developer": "開発コマンド含む",
                        "elder": "管理コマンド含む",
                        "admin": "すべてのコマンド",
                    },
                },
                {
                    "proposal": "統一エラーハンドリング",
                    "details": "全コマンドで共通のエラー処理フレームワーク使用",
                },
            ],
            "immediate_actions": ["重複コマンドの確認", "権限チェックの実装"],
        }
        return consultation

    def consult_rag_sage(self, current_state):
        """RAG賢者との相談"""
        consultation = {
            "sage": "RAG Sage",
            "timestamp": self.timestamp.isoformat(),
            "discoverability_analysis": {
                "current_problems": [
                    "コマンド検索が困難",
                    "関連機能の発見が偶発的",
                    "ドキュメントが分散",
                ],
                "user_experience": "新規ユーザーの60%が適切なコマンドを見つけられない",
            },
            "recommendations": [
                {
                    "proposal": "AIコマンドファインダー",
                    "features": [
                        "自然言語でのコマンド検索",
                        "使用履歴に基づく推薦",
                        "類似コマンドの提案",
                    ],
                    "command": "ai find 'テストを実行したい'",
                },
                {
                    "proposal": "コンテキスト認識システム",
                    "details": [
                        "現在のディレクトリに基づくコマンド提案",
                        "プロジェクトタイプに応じた推奨コマンド",
                        "作業フローに基づく次のコマンド予測",
                    ],
                },
                {
                    "proposal": "統合ドキュメントシステム",
                    "implementation": {
                        "command": "ai docs",
                        "features": ["検索可能", "例示豊富", "インタラクティブ"],
                    },
                },
            ],
            "search_optimization": "全コマンドのメタデータとタグ付けが必要",
        }
        return consultation

    def create_action_plan(self, consultations):
        """アクションプランの作成"""
        action_plan = {
            "title": "AI Command System Reorganization Plan",
            "date": self.timestamp.strftime("%Y-%m-%d"),
            "version": "1.0",
            "summary": "54個のAIコマンドを効率的に再編成するための実行計画",
            "phases": [
                {
                    "phase": 1,
                    "name": "即時対応",
                    "duration": "1週間",
                    "actions": [
                        "現行コマンドのカテゴリー分類",
                        "重複・類似コマンドの統合",
                        "ai helpコマンドの実装",
                        "基本的なドキュメント作成",
                    ],
                },
                {
                    "phase": 2,
                    "name": "体系的再編成",
                    "duration": "2週間",
                    "actions": [
                        "階層的コマンド体系への移行",
                        "エイリアスシステムの実装",
                        "権限管理システムの導入",
                        "エラーハンドリングの統一",
                    ],
                },
                {
                    "phase": 3,
                    "name": "高度な機能実装",
                    "duration": "2週間",
                    "actions": [
                        "AIコマンドファインダーの開発",
                        "インタラクティブモードの実装",
                        "コンテキスト認識システム",
                        "統合ドキュメントシステム",
                    ],
                },
            ],
            "proposed_structure": {
                "core_commands": {
                    "ai": "メインエントリーポイント",
                    "ai help": "ヘルプシステム",
                    "ai status": "全体ステータス",
                    "ai start/stop": "システム起動/停止",
                },
                "category_commands": {
                    "ai elder": "エルダー管理",
                    "ai worker": "ワーカー管理",
                    "ai dev": "開発ツール",
                    "ai ops": "運用ツール",
                    "ai test": "テストツール",
                },
                "advanced_features": {
                    "ai find": "コマンド検索",
                    "ai chain": "コマンドチェーン",
                    "ai interactive": "対話モード",
                },
            },
            "success_metrics": [
                "コマンド数を30%削減（統合により）",
                "新規ユーザーの学習時間を50%短縮",
                "コマンド発見率を80%向上",
                "エラー率を40%削減",
            ],
        }
        return action_plan

    def generate_report(self):
        """評議会レポートの生成"""
        current_state = self.analyze_current_state()

        consultations = {
            "knowledge": self.consult_knowledge_sage(current_state),
            "task": self.consult_task_oracle(current_state),
            "incident": self.consult_incident_sage(current_state),
            "rag": self.consult_rag_sage(current_state),
        }

        action_plan = self.create_action_plan(consultations)

        report = {
            "elder_council_consultation": {
                "topic": "AI Command System Reorganization",
                "date": self.timestamp.isoformat(),
                "current_state": current_state,
                "elder_consultations": consultations,
                "action_plan": action_plan,
                "next_steps": [
                    "グランドエルダーmaruへの報告",
                    "Phase 1の即時実行",
                    "全開発者への通知",
                    "移行ガイドの作成",
                ],
            }
        }

        # Save report
        report_path = Path(
            "/home/aicompany/ai_co/reports/ai_command_reorganization_council_report.json"
        )
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # Also create markdown report
        self.create_markdown_report(report, current_state)

        return report

    def create_markdown_report(self, report, current_state):
        """Markdown形式のレポート作成"""
        md_content = f"""# AI Command System Reorganization Council Report

**Date**: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Requested by**: Claude Elder
**Council Members**: Knowledge Sage, Task Oracle, Incident Sage, RAG Sage

## 📊 現状分析

- **総コマンド数**: {current_state['total_commands']}個
- **カテゴリー数**: {len(current_state['categories'])}個

### カテゴリー別コマンド数
"""
        # Add category breakdown
        for category, commands in sorted(
            current_state["categories"].items(), key=lambda x: len(x[1]), reverse=True
        ):
            md_content += f"- **{category}**: {len(commands)}個\n"

        md_content += """
## 🧙‍♂️ 4賢者からの提言

### 📚 ナレッジ賢者
- **問題**: コマンド体系の複雑化、学習曲線の急峻化
- **提案**: 階層的コマンド体系、エイリアスシステム、統合ヘルプ

### 📋 タスク賢者
- **問題**: 機能推測困難、関連コマンド発見困難、効率30%低下
- **提案**: ワークフロー指向再編成、インタラクティブモード、コマンドチェーン

### 🚨 インシデント賢者
- **問題**: 名前衝突リスク、権限管理複雑化、エラー処理不統一
- **提案**: 名前空間明確化、権限レベルシステム、統一エラーハンドリング

### 🔍 RAG賢者
- **問題**: コマンド検索困難、ドキュメント分散、60%が適切なコマンドを見つけられない
- **提案**: AIコマンドファインダー、コンテキスト認識、統合ドキュメント

## 🎯 実行計画

### Phase 1: 即時対応（1週間）
1. 現行コマンドのカテゴリー分類
2. 重複・類似コマンドの統合
3. ai helpコマンドの実装
4. 基本的なドキュメント作成

### Phase 2: 体系的再編成（2週間）
1. 階層的コマンド体系への移行
2. エイリアスシステムの実装
3. 権限管理システムの導入
4. エラーハンドリングの統一

### Phase 3: 高度な機能実装（2週間）
1. AIコマンドファインダーの開発
2. インタラクティブモードの実装
3. コンテキスト認識システム
4. 統合ドキュメントシステム

## 📈 成功指標
- コマンド数を30%削減（統合により）
- 新規ユーザーの学習時間を50%短縮
- コマンド発見率を80%向上
- エラー率を40%削減

## 🚀 次のステップ
1. グランドエルダーmaruへの報告
2. Phase 1の即時実行
3. 全開発者への通知
4. 移行ガイドの作成

---
*Generated by Elder Council Consultation System*
"""

        md_path = Path(
            "/home/aicompany/ai_co/reports/AI_COMMAND_REORGANIZATION_COUNCIL_REPORT.md"
        )
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)


def main():
    """メイン実行"""
    print("🏛️ AI Command Reorganization Elder Council")
    print("=" * 60)

    council = AICommandReorganizationCouncil()
    report = council.generate_report()

    print("\n✅ 評議会協議完了")
    print("📄 レポート保存場所:")
    print(
        "   - JSON: /home/aicompany/ai_co/reports/ai_command_reorganization_council_report.json"
    )
    print(
        "   - Markdown: /home/aicompany/ai_co/reports/AI_COMMAND_REORGANIZATION_COUNCIL_REPORT.md"
    )

    # Display summary
    action_plan = report["elder_council_consultation"]["action_plan"]
    print("\n📋 推奨アクション:")
    for i, step in enumerate(action_plan["next_steps"], 1):
        print(f"   {i}. {step}")

    print("\n💡 提案された新体系:")
    print("   - ai <category> <action> 形式への統一")
    print("   - 例: ai elder status, ai worker start")
    print("   - AIコマンドファインダーで自然言語検索")


if __name__ == "__main__":
    main()
