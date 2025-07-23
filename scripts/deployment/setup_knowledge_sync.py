#!/usr/bin/env python3
"""
知識同期システムのセットアップと自動化
PROJECT_KNOWLEDGE.mdの自動配置・同期・管理
"""

import asyncio
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging

from libs.knowledge_base_manager import KnowledgeBaseManager
from libs.task_history_db import TaskHistoryDB


class KnowledgeSyncSystem:
    """知識同期システム"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.knowledge_manager = KnowledgeBaseManager()
        self.task_db = TaskHistoryDB()

        # ロガー設定
        self.logger = logging.getLogger("knowledge_sync")
        self.logger.setLevel(logging.INFO)

        # コンソールハンドラー設定
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # プロジェクトナレッジテンプレート
        self.template_path = (
            PROJECT_ROOT / "projects" / "sample-project" / "PROJECT_KNOWLEDGE.md"
        )

        # 設定ファイル
        self.config_file = PROJECT_ROOT / ".knowledge_sync_config.json"
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """設定読み込み"""
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "sync_interval_hours": 24,
            "elevation_threshold": 3,  # 3回再利用で昇華候補
            "auto_sync": True,
            "projects": [],
        }

    def save_config(self):
        """設定保存"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    async def setup_all_projects(self):
        """全プロジェクトのPROJECT_KNOWLEDGE.md配置"""
        self.logger.info("🏛️ PROJECT_KNOWLEDGE.md 自動配置開始...")

        # 対象プロジェクトの検出
        target_projects = self.find_all_projects()
        created_count = 0

        for project_path in target_projects:
            knowledge_file = project_path / "PROJECT_KNOWLEDGE.md"

            if not knowledge_file.exists():
                # テンプレートから作成
                self.create_project_knowledge(project_path)
                created_count += 1
                self.logger.info(f"✅ 作成: {project_path.name}/PROJECT_KNOWLEDGE.md")
            else:
                self.logger.info(f"📋 既存: {project_path.name}/PROJECT_KNOWLEDGE.md")

        # 設定に登録
        self.config["projects"] = [str(p) for p in target_projects]
        self.save_config()

        self.logger.info(f"🎉 完了: {created_count}個の新規ファイル作成")
        return created_count

    def find_all_projects(self) -> List[Path]:
        """プロジェクトディレクトリの検出"""
        projects = []

        # メインプロジェクト
        main_projects = [
            self.project_root / "ai-company-web",
            self.project_root / "ai-elder-project",
            self.project_root / "codeflow",
            self.project_root / "frontend",
            self.project_root / "api",
        ]

        for project in main_projects:
            if project.exists() and project.is_dir():
                projects.append(project)

        # projects/配下のサブプロジェクト
        projects_dir = self.project_root / "projects"
        if projects_dir.exists():
            for item in projects_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    # .gitやキャッシュディレクトリを除外
                    if (
                        (item / ".git").exists()
                        or (item / "package.json").exists()
                        or (item / "setup.py").exists()
                    ):
                        projects.append(item)

        return projects

    def create_project_knowledge(self, project_path: Path):
        """PROJECT_KNOWLEDGE.mdの作成"""
        knowledge_file = project_path / "PROJECT_KNOWLEDGE.md"

        # プロジェクト情報の自動検出
        project_info = self.analyze_project(project_path)

        # テンプレートをカスタマイズ
        content = f"""# 📚 {project_path.name} 専用ナレッジ

## 🎯 プロジェクト概要
- **目的**: {project_info.get('purpose', '[プロジェクトの目的を記載]')}
- **特徴**: {project_info.get('features', '[主な特徴を記載]')}
- **使用技術スタック**: {', '.join(project_info.get('tech_stack', ['[技術スタック]']))}
- **主要な設計判断**: {project_info.get('design_decisions', '[設計判断を記載]')}

## 🛠️ 技術固有知識

### {project_info.get('main_tech', '[主要技術]')}
- **特有のパターン**:
  - [パターン1]
  - [パターン2]

- **最適化手法**:
  - [最適化1]
  - [最適化2]

- **トラブルシューティング**:
  - [問題と解決策]

## 📋 プロジェクト固有のベストプラクティス

### コーディング規約
- [規約を記載]

### テストパターン
- [テストパターンを記載]

### デプロイメント手順
1. [手順を記載]

## 🚨 よくある問題と解決策

### プロジェクト特有のエラー
- [エラーと解決策を記載]

### パフォーマンス問題
- [問題と対策を記載]

### セキュリティ考慮事項
- [セキュリティ項目を記載]

## 🔄 中央知識ベースとの連携

### 参照している共通パターン
- TDD開発手法
- エラーハンドリング標準
- [その他の共通パターン]

### 貢献した共通知識
- [このプロジェクトから生まれた知識]

### 同期状況
- 最終同期: {datetime.now().strftime('%Y年%m月%d日')}
- 次回同期: 自動（毎週）
- 昇華待ち: [昇華待ち項目]

## 📈 メトリクス・統計

### コード品質
- テストカバレッジ: [%]
- その他指標: [値]

### パフォーマンス
- [指標と値]

---

**最終更新**: {datetime.now().strftime('%Y年%m月%d日')}
**管理者**: ナレッジ賢者 + {project_path.name}チーム
**次回レビュー**: {(datetime.now() + timedelta(days=7)).strftime('%Y年%m月%d日')}
"""

        knowledge_file.write_text(content, encoding="utf-8")

    def analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """プロジェクトの自動分析"""
        info = {
            "purpose": "",
            "features": "",
            "tech_stack": [],
            "design_decisions": "",
            "main_tech": "",
        }

        # package.json分析（Node.js/フロントエンド）
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 技術スタック検出
                deps = list(data.get("dependencies", {}).keys())
                dev_deps = list(data.get("devDependencies", {}).keys())

                if "react" in deps:
                    info["tech_stack"].append("React")
                    info["main_tech"] = "React"
                if "vue" in deps:
                    info["tech_stack"].append("Vue.js")
                    info["main_tech"] = "Vue.js"
                if "typescript" in dev_deps:
                    info["tech_stack"].append("TypeScript")
                if "express" in deps:
                    info["tech_stack"].append("Express")
                if "fastify" in deps:
                    info["tech_stack"].append("Fastify")

                info["purpose"] = data.get("description", "")
            except:
                pass

        # requirements.txt分析（Python）
        requirements = project_path / "requirements.txt"
        if requirements.exists():
            try:
                content = requirements.read_text()
                if "flask" in content.lower():
                    info["tech_stack"].append("Flask")
                    info["main_tech"] = "Flask"
                if "django" in content.lower():
                    info["tech_stack"].append("Django")
                    info["main_tech"] = "Django"
                if "fastapi" in content.lower():
                    info["tech_stack"].append("FastAPI")
                    info["main_tech"] = "FastAPI"
                if "pytest" in content.lower():
                    info["tech_stack"].append("pytest")
            except:
                pass

        # setup.py分析
        setup_py = project_path / "setup.py"
        if setup_py.exists():
            info["tech_stack"].append("Python")
            if not info["main_tech"]:
                info["main_tech"] = "Python"

        # Dockerfile分析
        dockerfile = project_path / "Dockerfile"
        if dockerfile.exists():
            info["tech_stack"].append("Docker")
            info["features"] = "コンテナ化対応"

        # デフォルト値
        if not info["tech_stack"]:
            info["tech_stack"] = ["[技術スタックを検出できませんでした]"]
        if not info["main_tech"]:
            info["main_tech"] = (
                info["tech_stack"][0] if info["tech_stack"] else "[主要技術]"
            )

        return info

    async def sync_knowledge_base(self):
        """知識ベースの同期実行"""
        self.logger.info("🔄 知識ベース同期開始...")

        sync_results = {"synced": 0, "elevated": 0, "errors": 0, "candidates": []}

        # 繰り返し処理
        for project_str in self.config.get("projects", []):
            project_path = Path(project_str)
            knowledge_file = project_path / "PROJECT_KNOWLEDGE.md"

            if knowledge_file.exists():
                # 知識の分析と昇華候補の検出
                candidates = await self.analyze_knowledge_patterns(knowledge_file)

                for candidate in candidates:
                    if candidate["usage_count"] >= self.config["elevation_threshold"]:
                        sync_results["candidates"].append(
                            {
                                "project": project_path.name,
                                "pattern": candidate["pattern"],
                                "usage_count": candidate["usage_count"],
                                "recommendation": "中央知識ベースへの昇華を推奨",
                            }
                        )
                        sync_results["elevated"] += 1

                sync_results["synced"] += 1

        # 同期レポート生成
        await self.generate_sync_report(sync_results)

        return sync_results

    async def analyze_knowledge_patterns(
        self, knowledge_file: Path
    ) -> List[Dict[str, Any]]:
        """知識パターンの分析"""
        # 簡易的な実装（実際にはより高度な分析が必要）
        patterns = []

        try:
            content = knowledge_file.read_text(encoding="utf-8")

            # パターン検出ロジック（仮実装）
            # 実際には機械学習やルールベースのパターン検出を実装
            if "WebSocket" in content:
                patterns.append(
                    {"pattern": "WebSocket通信パターン", "usage_count": 4}
                )  # 仮の値

            if "エラーハンドリング" in content:
                patterns.append(
                    {"pattern": "エラーハンドリングパターン", "usage_count": 5}
                )

        except Exception as e:
            self.logger.error(f"パターン分析エラー: {e}")

        return patterns

    async def generate_sync_report(self, sync_results: Dict[str, Any]):
        """同期レポートの生成"""
        report_path = (
            PROJECT_ROOT
            / "knowledge_base"
            / "sync_reports"
            / f"sync_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        report_content = f"""# 📊 知識ベース同期レポート

**実行日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}

## 📈 同期結果サマリー

- **同期プロジェクト数**: {sync_results['synced']}
- **昇華候補数**: {sync_results['elevated']}
- **エラー数**: {sync_results['errors']}

## 🌟 昇華候補パターン

"""

        if sync_results["candidates"]:
            for candidate in sync_results["candidates"]:
                report_content += f"""### {candidate['project']} - {candidate['pattern']}
- **使用回数**: {candidate['usage_count']}回
- **推奨**: {candidate['recommendation']}

"""
        else:
            report_content += "現在、昇華候補となるパターンはありません。\n"

        report_content += """
## 🚀 次のアクション

1. 昇華候補パターンの中央知識ベースへの統合検討
2. 各プロジェクトのPROJECT_KNOWLEDGE.md更新確認
3. 次回同期スケジュールの確認

---

**生成者**: ナレッジ賢者
**承認者**: エルダー評議会
"""

        report_path.write_text(report_content, encoding="utf-8")
        self.logger.info(f"📄 同期レポート生成: {report_path}")

    async def setup_cron_job(self):
        """cronジョブの設定（実装ガイド）"""
        cron_content = """# 知識ベース自動同期（毎日午前6時）
0 6 * * * cd /home/aicompany/ai_co && python3 setup_knowledge_sync.py --sync

# 週次レポート生成（毎週月曜日午前9時）
0 9 * * 1 cd /home/aicompany/ai_co && python3 setup_knowledge_sync.py --weekly-report

# 月次統合レビュー（毎月1日午前10時）
0 10 1 * * cd /home/aicompany/ai_co && python3 setup_knowledge_sync.py --monthly-review
"""

        cron_file = PROJECT_ROOT / "knowledge_sync.cron"
        cron_file.write_text(cron_content, encoding="utf-8")

        self.logger.info(
            f"""
🕐 cronジョブ設定ファイルを生成しました: {cron_file}

以下のコマンドでcronに登録してください:
crontab {cron_file}

現在のcron設定を確認:
crontab -l
"""
        )


async def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="知識同期システムセットアップ")
    parser.add_argument("--install", action="store_true", help="初期セットアップ実行")
    parser.add_argument("--sync", action="store_true", help="知識同期実行")
    parser.add_argument("--weekly-report", action="store_true", help="週次レポート生成")
    parser.add_argument(
        "--monthly-review", action="store_true", help="月次レビュー実行"
    )
    parser.add_argument("--cron", action="store_true", help="cron設定生成")

    args = parser.parse_args()

    sync_system = KnowledgeSyncSystem()

    if args.install:
        print("🏛️ エルダーズギルド 知識同期システム セットアップ")
        print("=" * 60)

        # PROJECT_KNOWLEDGE.md配置
        created = await sync_system.setup_all_projects()

        # 初回同期実行
        if created > 0:
            print("\n📊 初回同期を実行中...")
            await sync_system.sync_knowledge_base()

        # cron設定
        await sync_system.setup_cron_job()

        print("\n✅ セットアップ完了！")

    elif args.sync:
        # 定期同期実行
        results = await sync_system.sync_knowledge_base()
        print(f"同期完了: {results['synced']}プロジェクト処理")

    elif args.weekly_report:
        # 週次レポート（実装予定）
        print("週次レポート生成中...")

    elif args.monthly_review:
        # 月次レビュー（実装予定）
        print("月次レビュー実行中...")

    elif args.cron:
        # cron設定のみ
        await sync_system.setup_cron_job()

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
