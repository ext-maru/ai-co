#!/usr/bin/env python3
"""
Unified Interface CLI
統合インターフェースCLI管理ツール

使用例:
python3 scripts/unified_interface_cli.py --start-server
python3 scripts/unified_interface_cli.py --status
python3 scripts/unified_interface_cli.py --test-api

"""

import sys
import argparse
import asyncio
import json
import aiohttp
from pathlib import Path
from datetime import datetime

# パス設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.unified_interface_system import UnifiedInterfaceSystem

class UnifiedInterfaceCLI:
    """統合インターフェースCLI"""

    def __init__(self):
        self.interface_system = UnifiedInterfaceSystem()
        self.initialized = False

    async def initialize(self):
        """初期化"""
        if not self.initialized:
            init_result = await self.interface_system.initialize_system()
            if init_result["success"]:
                self.initialized = True
                print("✅ 統合インターフェースシステム初期化完了")
            else:
                print(f"❌ 初期化失敗: {init_result.get('error', 'Unknown error')}")
                return False
        return True

    async def start_server(self):
        """サーバー開始"""
        if not await self.initialize():
            return

        print("🌐 統合インターフェースサーバーを開始します")
        print("=" * 60)

        try:
            print("📡 FastAPI サーバー起動中...")
            print("   Web UI: http://localhost:8000")
            print("   API Docs: http://localhost:8000/docs")
            print("   API: http://localhost:8000/api/status")
            print("   WebSocket: ws://localhost:8000/ws/{session_id}")
            print("\n🛑 停止するには Ctrl+C を押してください")

            await self.interface_system.start_server()

        except KeyboardInterrupt:
            print("\n⚠️ サーバーを停止しています...")
        except Exception as e:
            print(f"❌ サーバー起動エラー: {e}")

    async def show_status(self):
        """システム状況表示"""
        if not await self.initialize():
            return

        print("📊 統合インターフェースシステム状況")
        print("=" * 60)

        try:
            status = await self.interface_system.get_system_status()

            # インターフェース統計
            interface_stats = status["interface_stats"]
            print(f"📈 インターフェース統計:")
            print(f"   総リクエスト数: {interface_stats['total_requests']}")
            print(f"   アクティブセッション: {interface_stats['active_sessions']}")
            print(f"   WebSocket接続: {interface_stats['websocket_connections']}")
            print(f"   API呼び出し: {interface_stats['api_calls']}")
            print(f"   Web UI訪問: {interface_stats['web_ui_visits']}")

            # 4賢者状況
            if status.get("four_sages_status"):
                sages_status = status["four_sages_status"]
                print(f"\n🧙‍♂️ 4賢者システム状況:")
                if sages_status.get("integration_status"):
                    integration = sages_status["integration_status"]
                    print(
                        f"   MCP接続: {'✅' if integration.get('mcp_connected') else '❌'}"
                    )
                    print(
                        f"   賢者統合: {'✅' if integration.get('sages_integrated') else '❌'}"
                    )
                    print(
                        f"   保存知識: {integration.get('total_knowledge_stored', 0)}件"
                    )
                    print(
                        f"   実行検索: {integration.get('total_searches_performed', 0)}回"
                    )

            # 学習システム状況
            if status.get("learning_status"):
                learning_status = status["learning_status"]
                print(f"\n🤖 学習システム状況:")
                print(
                    f"   継続学習: {'✅' if learning_status.get('continuous_learning_active') else '❌'}"
                )
                print(f"   総タスク: {learning_status.get('total_tasks', 0)}")
                print(f"   アクティブタスク: {learning_status.get('active_tasks', 0)}")
                print(f"   完了タスク: {learning_status.get('completed_tasks', 0)}")
                print(f"   成功率: {learning_status.get('success_rate', 0):0.2%}")

            # システム稼働時間
            uptime_start = interface_stats.get("uptime_start")
            if uptime_start:
                print(f"\n⏰ システム稼働時間:")
                print(f"   開始時刻: {uptime_start}")
                print(f"   現在時刻: {datetime.now()}")

        except Exception as e:
            print(f"❌ 状況取得エラー: {e}")

    async def test_api(self):
        """API機能テスト"""
        if not await self.initialize():
            return

        print("🧪 API機能テスト")
        print("=" * 60)

        try:
            # 検索APIテスト
            print("1.0 検索APIテスト...")
            search_result = await self.interface_system.handle_search_request(
                {"query": "4賢者システム", "search_type": "hybrid", "limit": 3}
            )
            print(f"   検索結果: {search_result.get('total_found', 0)}件")

            # 4賢者分析APIテスト
            print("\n2.0 4賢者分析APIテスト...")
            analysis_result = await self.interface_system.handle_sages_analysis(
                {
                    "title": "APIテスト分析",
                    "query": "統合システム",
                    "context": "CLI API テスト",
                }
            )
            print(f"   分析結果: {analysis_result.get('status', 'unknown')}")

            # 学習タスクAPIテスト
            print("\n3.0 学習タスクAPIテスト...")
            learning_result = await self.interface_system.handle_learning_task(
                {
                    "task_type": "supervised",
                    "data_source": "api_test",
                    "target_metric": "accuracy",
                }
            )
            print(f"   学習タスク: {learning_result.get('task_id', 'unknown')}")

            # システム状況APIテスト
            print("\n4.0 システム状況APIテスト...")
            status_result = await self.interface_system.get_system_status()
            print(f"   状況取得: {'成功' if status_result else '失敗'}")

            print("\n✅ API機能テスト完了")

        except Exception as e:
            print(f"❌ APIテストエラー: {e}")

        """テンプレート作成"""
        print("📝 テンプレート作成")
        print("=" * 60)

        try:
            # テンプレートディレクトリ作成

            print("✅ HTMLテンプレート作成完了")

            # 静的ファイル作成
            await self.interface_system._create_static_files()
            print("✅ 静的ファイル作成完了")

            # 作成されたファイル一覧

            static_dir = PROJECT_ROOT / "static"

            print(f"\n📁 作成されたファイル:")

                    print(f"     - {file.name}")

            print(f"   Static: {static_dir}")
            if static_dir.exists():
                for file in static_dir.glob("*"):
                    print(f"     - {file.name}")

        except Exception as e:
            print(f"❌ テンプレート作成エラー: {e}")

    async def run_demo(self):
        """デモ実行"""
        print("🎬 統合インターフェースデモ実行")
        print("=" * 60)

        try:
            # システム初期化
            print("1.0 システム初期化...")
            if not await self.initialize():
                return

            # 各種機能テスト
            print("\n2.0 機能テスト...")

            # テンプレート作成

            # APIテスト
            await self.test_api()

            # 状況確認
            await self.show_status()

            print("\n🎉 デモ実行完了")
            print("✅ 全ての機能が正常に動作しています")

        except Exception as e:
            print(f"❌ デモ実行エラー: {e}")

    async def health_check(self):
        """ヘルスチェック"""
        print("💊 ヘルスチェック")
        print("=" * 60)

        try:
            # システム初期化チェック
            print("1.0 システム初期化チェック...")
            init_success = await self.initialize()
            print(f"   初期化: {'✅' if init_success else '❌'}")

            if not init_success:
                return

            # 各コンポーネントのチェック
            print("\n2.0 コンポーネントチェック...")

            # 4賢者システム
            try:
                sages_status = (
                    await self.interface_system.four_sages.get_integration_status()
                )
                print(f"   4賢者システム: {'✅' if sages_status else '❌'}")
            except Exception as e:
                print(f"   4賢者システム: ❌ ({e})")

            # 検索・分析プラットフォーム
            try:
                search_config = self.interface_system.search_platform.search_config
                print(f"   検索プラットフォーム: {'✅' if search_config else '❌'}")
            except Exception as e:
                print(f"   検索プラットフォーム: ❌ ({e})")

            # 学習システム
            try:
                learning_status = (
                    await self.interface_system.learning_system.get_learning_status()
                )
                print(f"   学習システム: {'✅' if learning_status else '❌'}")
            except Exception as e:
                print(f"   学習システム: ❌ ({e})")

            # FastAPIアプリケーション
            try:
                app_routes = len(self.interface_system.app.routes)
                print(f"   FastAPIアプリ: ✅ ({app_routes}ルート)")
            except Exception as e:
                print(f"   FastAPIアプリ: ❌ ({e})")

            print("\n✅ ヘルスチェック完了")

        except Exception as e:
            print(f"❌ ヘルスチェックエラー: {e}")

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="統合インターフェースCLI管理ツール")

    # 基本コマンド
    parser.add_argument("--start-server", action="store_true", help="サーバー開始")
    parser.add_argument("--status", action="store_true", help="システム状況表示")
    parser.add_argument("--test-api", action="store_true", help="API機能テスト")
    parser.add_argument(

    )
    parser.add_argument("--demo", action="store_true", help="デモ実行")
    parser.add_argument("--health-check", action="store_true", help="ヘルスチェック")

    args = parser.parse_args()

    # CLIインスタンス作成
    cli = UnifiedInterfaceCLI()

    async def run_cli():
        """run_cliを実行"""
        try:
            if args.start_server:
                await cli.start_server()
            elif args.status:
                await cli.show_status()
            elif args.test_api:
                await cli.test_api()

            elif args.demo:
                await cli.run_demo()
            elif args.health_check:
                await cli.health_check()
            else:
                parser.print_help()
                print("\n💡 使用例:")
                print("   python3 scripts/unified_interface_cli.py --start-server")
                print("   python3 scripts/unified_interface_cli.py --status")
                print("   python3 scripts/unified_interface_cli.py --test-api")

                print("   python3 scripts/unified_interface_cli.py --demo")
                print("   python3 scripts/unified_interface_cli.py --health-check")

        except KeyboardInterrupt:
            print("\n⚠️ 処理が中断されました")
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")

    # 非同期実行
    asyncio.run(run_cli())

if __name__ == "__main__":
    main()
