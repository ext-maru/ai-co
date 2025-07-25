#!/usr/bin/env python3
"""
🏗️ プロジェクトビルダーウィザード
インタラクティブな対話形式でプロジェクト要件を収集し、
フル機能実装済みのプロジェクトを自動生成

エルダーズギルド品質基準準拠
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_council_summoner import ElderCouncilSummoner
from scripts.project_scaffolder import ProjectScaffolder

console = Console()


class ProjectBuilderWizard:
    """プロジェクト構築ウィザード"""

    def __init__(self):
        self.console = console
        self.project_config = {}
        self.summoner = ElderCouncilSummoner()

    async def run(self):
        """ウィザード実行"""
        self.console.print(
            Panel(
                "🎯 プロジェクト構築ウィザードへようこそ\n"
                "エルダーズギルド品質基準に準拠したプロジェクトを作成します",
                title="🏗️ Project Builder",
                border_style="bright_blue",
            )
        )

        # プロジェクト基本情報収集
        await self.collect_basic_info()

        # 技術スタック選択
        await self.select_tech_stack()

        # 機能要件収集
        await self.collect_features()

        # エルダーズギルド統合設定
        await self.configure_elders_integration()

        # 確認と生成
        await self.confirm_and_generate()

    async def collect_basic_info(self):
        """基本情報収集"""
        self.console.print("\n📋 [bold cyan]プロジェクト基本情報[/bold cyan]")

        # プロジェクト名
        self.project_config["name"] = await questionary.text(
            "プロジェクト名:", default="upload-image-manager"
        ).ask_async()

        # プロジェクトタイプ
        self.project_config["type"] = await questionary.select(
            "プロジェクトタイプ:",
            choices=[
                {
                    "name": "📤 Upload Service - ファイルアップロード特化",
                    "value": "upload-service",
                },
                {
                    "name": "🌐 Web Application - フルスタックWebアプリ",
                    "value": "web-app",
                },
                {"name": "🔌 API Service - RESTful API", "value": "api-service"},
                {
                    "name": "📊 Dashboard - 監視・分析ダッシュボード",
                    "value": "dashboard",
                },
                {"name": "🔧 Microservice - マイクロサービス", "value": "microservice"},
            ],
        ).ask_async()

        # 説明
        self.project_config["description"] = await questionary.text(
            "プロジェクトの説明:", default="画像アップロード管理システム"
        ).ask_async()

    async def select_tech_stack(self):
        """技術スタック選択"""
        self.console.print("\n💻 [bold cyan]技術スタック選択[/bold cyan]")

        # バックエンド
        self.project_config["backend"] = await questionary.select(
            "バックエンドフレームワーク:",
            choices=[
                {
                    "name": "⚡ FastAPI - 高速・型安全・自動ドキュメント",
                    "value": "fastapi",
                },
                {"name": "🌶️ Flask - 軽量・柔軟", "value": "flask"},
                {"name": "🟩 Node.js + Express", "value": "nodejs"},
                {"name": "🚀 Go + Gin", "value": "go"},
            ],
            default="fastapi",
        ).ask_async()

        # フロントエンド
        self.project_config["frontend"] = await questionary.select(
            "フロントエンドフレームワーク:",
            choices=[
                {
                    "name": "⚛️ React + TypeScript - 型安全・コンポーネント指向",
                    "value": "react-ts",
                },
                {"name": "🔺 Next.js - SSR/SSG対応", "value": "nextjs"},
                {"name": "🟢 Vue.js 3 + TypeScript", "value": "vue3"},
                {"name": "🅰️ Angular", "value": "angular"},
                {"name": "❌ なし（APIのみ）", "value": "none"},
            ],
            default="react-ts",
        ).ask_async()

        # データベース
        self.project_config["database"] = await questionary.select(
            "データベース:",
            choices=[
                {"name": "🐘 PostgreSQL - 高機能RDBMS", "value": "postgresql"},
                {"name": "🐬 MySQL", "value": "mysql"},
                {"name": "🍃 MongoDB", "value": "mongodb"},
                {"name": "📝 SQLite（開発用）", "value": "sqlite"},
            ],
            default="postgresql",
        ).ask_async()

    async def collect_features(self):
        """機能要件収集"""
        self.console.print("\n✨ [bold cyan]機能要件[/bold cyan]")

        if self.project_config["type"] == "upload-service":
            # アップロードサービス特有の機能
            features = await questionary.checkbox(
                "含める機能を選択してください:",
                choices=[
                    {
                        "name": "📤 マルチファイルアップロード",
                        "value": "multi-upload",
                        "checked": True,
                    },
                    {
                        "name": "🖼️ 画像プレビュー・サムネイル生成",
                        "value": "image-preview",
                        "checked": True,
                    },
                    {
                        "name": "📊 アップロード進捗表示",
                        "value": "progress-tracking",
                        "checked": True,
                    },
                    {
                        "name": "🔐 ユーザー認証・権限管理",
                        "value": "auth",
                        "checked": True,
                    },
                    {
                        "name": "👤 管理者承認フロー",
                        "value": "approval-flow",
                        "checked": True,
                    },
                    {
                        "name": "☁️ クラウドストレージ統合",
                        "value": "cloud-storage",
                        "checked": True,
                    },
                    {
                        "name": "🔄 自動画像最適化",
                        "value": "image-optimization",
                        "checked": True,
                    },
                    {
                        "name": "📱 レスポンシブUI",
                        "value": "responsive",
                        "checked": True,
                    },
                    {"name": "🌍 多言語対応", "value": "i18n"},
                    {"name": "📧 メール通知", "value": "email-notification"},
                    {"name": "📈 分析ダッシュボード", "value": "analytics"},
                ],
            ).ask_async()
        else:
            # 汎用機能
            features = await questionary.checkbox(
                "含める機能を選択してください:",
                choices=[
                    {"name": "🔐 認証・認可", "value": "auth", "checked": True},
                    {"name": "📝 CRUD API", "value": "crud", "checked": True},
                    {
                        "name": "📱 レスポンシブUI",
                        "value": "responsive",
                        "checked": True,
                    },
                    {"name": "🔍 検索・フィルタリング", "value": "search"},
                    {"name": "📊 データ可視化", "value": "visualization"},
                    {"name": "🔄 リアルタイム更新", "value": "realtime"},
                    {"name": "📧 通知システム", "value": "notification"},
                ],
            ).ask_async()

        self.project_config["features"] = features

        # クラウドストレージ選択（必要な場合）
        if "cloud-storage" in features:
            self.project_config["storage"] = await questionary.select(
                "クラウドストレージ:",
                choices=[
                    {"name": "☁️ Google Drive", "value": "google-drive"},
                    {"name": "📦 AWS S3", "value": "s3"},
                    {"name": "🔷 Azure Blob Storage", "value": "azure"},
                    {"name": "💾 ローカルストレージ", "value": "local"},
                ],
                default="google-drive",
            ).ask_async()

    async def configure_elders_integration(self):
        """エルダーズギルド統合設定"""
        self.console.print("\n🏛️ [bold cyan]エルダーズギルド統合設定[/bold cyan]")

        # デフォルトで全て有効
        integration = await questionary.checkbox(
            "エルダーズギルド機能:",
            choices=[
                {"name": "🧪 TDD（テスト駆動開発）", "value": "tdd", "checked": True},
                {
                    "name": "🧙‍♂️ 4賢者システム統合",
                    "value": "four-sages",
                    "checked": True,
                },
                {
                    "name": "📊 品質監視ダッシュボード",
                    "value": "quality-dashboard",
                    "checked": True,
                },
                {"name": "🔄 CI/CDパイプライン", "value": "cicd", "checked": True},
                {
                    "name": "📈 自動パフォーマンス最適化",
                    "value": "performance",
                    "checked": True,
                },
                {
                    "name": "🚨 インシデント自動対応",
                    "value": "incident",
                    "checked": True,
                },
                {
                    "name": "📚 ナレッジベース統合",
                    "value": "knowledge",
                    "checked": True,
                },
                {"name": "🔍 RAG検索システム", "value": "rag", "checked": True},
            ],
        ).ask_async()

        self.project_config["elders_integration"] = integration

        # Docker設定
        self.project_config["docker"] = await questionary.confirm(
            "Docker化しますか？", default=True
        ).ask_async()

        # デプロイ設定
        self.project_config["deployment"] = await questionary.select(
            "デプロイ先:",
            choices=[
                {"name": "🐳 Docker Compose（ローカル）", "value": "docker-compose"},
                {"name": "☸️ Kubernetes", "value": "k8s"},
                {"name": "☁️ AWS ECS", "value": "ecs"},
                {"name": "🔷 Azure Container", "value": "azure"},
                {"name": "🚀 Heroku", "value": "heroku"},
            ],
            default="docker-compose",
        ).ask_async()

    async def confirm_and_generate(self):
        """確認と生成"""
        self.console.print("\n📋 [bold cyan]プロジェクト設定確認[/bold cyan]")

        # 設定内容表示
        self.console.print(
            Panel(
                f"プロジェクト名: {self.project_config['name']}\n"
                f"タイプ: {self.project_config['type']}\n"
                f"バックエンド: {self.project_config['backend']}\n"
                f"フロントエンド: {self.project_config['frontend']}\n"
                f"データベース: {self.project_config['database']}\n"
                f"機能数: {len(self.project_config['features'])}個\n"
                f"エルダーズ統合: {len(self.project_config['elders_integration'])}個",
                title="設定内容",
                border_style="green",
            )
        )

        # 確認
        confirm = await questionary.confirm(
            "この設定でプロジェクトを生成しますか？", default=True
        ).ask_async()

        if not confirm:
            self.console.print("[yellow]キャンセルされました[/yellow]")
            return

        # プロジェクト生成
        await self.generate_project()

    async def generate_project(self):
        """プロジェクト生成"""
        self.console.print("\n🚀 [bold green]プロジェクト生成開始[/bold green]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=self.console,
        ) as progress:
            # エルダー評議会への報告
            task = progress.add_task("エルダー評議会への報告...", total=None)
            await self.report_to_elders()
            progress.advance(task)

            # プロジェクト生成
            task = progress.add_task("プロジェクト構造生成...", total=None)
            scaffolder = ProjectScaffolder()
            project_path = await scaffolder.create_project(self.project_config)
            progress.advance(task)

            # PDCA記録初期化
            task = progress.add_task("PDCA機構セットアップ...", total=None)
            await self.initialize_pdca(project_path)
            progress.advance(task)

        # 完了メッセージ
        self.console.print(
            Panel(
                f"✅ プロジェクト '{self.project_config['name']}' が正常に作成されました！\n\n"
                f"📁 場所: {project_path}\n\n"
                f"🚀 開始方法:\n"
                f"  cd {project_path}\n"
                f"  docker-compose up\n\n"
                f"📊 PDCA分析:\n"
                f"  ai-project pdca {self.project_config['name']}",
                title="🎉 生成完了",
                border_style="bright_green",
            )
        )

    async def report_to_elders(self):
        """エルダー評議会への報告"""
        report = {
            "type": "project_creation",
            "timestamp": datetime.now().isoformat(),
            "project": self.project_config,
            "creator": "ProjectBuilderWizard",
            "quality_standards": {
                "tdd": "tdd" in self.project_config["elders_integration"],
                "four_sages": "four-sages" in self.project_config["elders_integration"],
                "coverage_target": 95,
            },
        }

        # 評議会へ報告
        if hasattr(self.summoner, "report_project_creation"):
            await self.summoner.report_project_creation(report)

    async def initialize_pdca(self, project_path: Path):
        """PDCA機構の初期化"""
        pdca_dir = project_path / ".pdca"
        pdca_dir.mkdir(exist_ok=True)

        # 初期PDCA記録
        pdca_record = {
            "project_name": self.project_config["name"],
            "created_at": datetime.now().isoformat(),
            "initial_config": self.project_config,
            "cycles": [],
            "improvements": [],
            "metrics": {
                "quality_score": 100,
                "test_coverage": 0,
                "performance_score": 0,
                "user_satisfaction": 0,
            },
        }

        with open(pdca_dir / "pdca_history.json", "w", encoding="utf-8") as f:
            json.dump(pdca_record, f, indent=2, ensure_ascii=False)


async def main():
    """メインエントリポイント"""
    wizard = ProjectBuilderWizard()
    await wizard.run()


if __name__ == "__main__":
    asyncio.run(main())
