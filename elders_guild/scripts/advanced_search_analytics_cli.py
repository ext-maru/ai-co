#!/usr/bin/env python3
"""
Advanced Search & Analytics CLI
高度検索・分析プラットフォーム CLI インターフェース

使用例:
python3 scripts/advanced_search_analytics_cli.py --hybrid-search "4賢者システム" --limit 10
python3 scripts/advanced_search_analytics_cli.py --analytics statistical "PostgreSQL MCP"
python3 scripts/advanced_search_analytics_cli.py --personalized-search user123 "データベース統合"
python3 scripts/advanced_search_analytics_cli.py --dashboard
"""

import sys
import argparse
import asyncio
import json
from pathlib import Path
from datetime import datetime

# パス設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.advanced_search_analytics_platform import (
    AdvancedSearchAnalyticsPlatform,
    SearchQuery,
    SearchType,
    AnalyticsType,
)


class AdvancedSearchAnalyticsCLI:
    """高度検索・分析CLI"""

    def __init__(self):
        self.platform = AdvancedSearchAnalyticsPlatform()
        self.initialized = False

    async def initialize(self):
        """初期化"""
        if not self.initialized:
            init_result = await self.platform.initialize_platform()
            if init_result["success"]:
                self.initialized = True
                print("✅ 高度検索・分析プラットフォーム初期化完了")
            else:
                print(f"❌ 初期化失敗: {init_result.get('error', 'Unknown error')}")
                return False
        return True

    async def hybrid_search(
        self,
        query: str,
        search_type: str = "hybrid",
        limit: int = 10,
        similarity_threshold: float = 0.7,
        filters: dict = None,
        context: str = None,
    ):
        """ハイブリッド検索実行"""
        if not await self.initialize():
            return

        print(f"🔍 {search_type.upper()}検索: '{query}'")
        print("-" * 60)

        try:
            # 検索クエリ構築
            search_query = SearchQuery(
                query=query,
                search_type=SearchType(search_type),
                filters=filters or {},
                limit=limit,
                similarity_threshold=similarity_threshold,
                context=context,
            )

            # 検索実行
            result = await self.platform.hybrid_search(search_query)

            # 結果表示
            if result.get("results"):
                print(f"✅ 検索完了: {result['total_found']}件発見")
                print(f"🕐 検索時間: {result.get('search_time', 0):0.3f}秒")

                for i, item in enumerate(result["results"][:10]):
                    print(f"\n{i+1}. {item.get('title', 'タイトルなし')}")
                    print(f"   ID: {item.get('id', 'N/A')}")
                    print(f"   類似度: {item.get('similarity', 0):0.3f}")
                    print(f"   ソース: {item.get('source', 'N/A')}")
                    print(f"   内容: {item.get('content', '')[:100]}...")

                    if item.get("tags"):
                        print(f"   タグ: {', '.join(item['tags'])}")

                    if item.get("highlights"):
                        print(f"   ハイライト: {', '.join(item['highlights'])}")

                if result["total_found"] > 10:
                    print(f"\n... 他 {result['total_found'] - 10} 件")

            else:
                print(f"❌ 検索失敗: {result.get('error', '結果なし')}")

        except Exception as e:
            print(f"❌ 検索エラー: {e}")

    async def advanced_analytics(
        self, analytics_type: str, data_query: str, context: dict = None
    ):
        """高度分析実行"""
        if not await self.initialize():
            return

        print(f"📊 {analytics_type.upper()}分析: '{data_query}'")
        print("-" * 60)

        try:
            # 分析実行
            result = await self.platform.advanced_analytics(
                AnalyticsType(analytics_type), data_query, context
            )

            # 結果表示
            print(f"✅ 分析完了")
            print(f"📈 分析タイプ: {result.analytics_type.value}")
            print(f"🎯 信頼度: {result.confidence:0.2f}")
            print(f"🕐 分析時刻: {result.timestamp}")

            # サマリー表示
            if result.summary:
                print(f"\n📋 サマリー:")
                for key, value in result.summary.items():
                    print(f"   {key}: {value}")

            # 洞察表示
            if result.insights:
                print(f"\n💡 洞察:")
                for insight in result.insights:
                    print(f"   • {insight}")

            # 推奨事項表示
            if result.recommendations:
                print(f"\n🔧 推奨事項:")
                for rec in result.recommendations:
                    print(f"   • {rec}")

            # 詳細データ表示（オプション）
            if result.details and len(str(result.details)) < 500:
                print(f"\n📊 詳細データ:")
                for key, value in result.details.items():
                    print(f"   {key}: {value}")

        except Exception as e:
            print(f"❌ 分析エラー: {e}")

    async def personalized_search(
        self, user_id: str, query: str, search_history: list = None
    ):
        """パーソナライズド検索実行"""
        if not await self.initialize():
            return

        print(f"👤 パーソナライズド検索 (User: {user_id})")
        print(f"🔍 クエリ: '{query}'")
        print("-" * 60)

        try:
            # パーソナライズド検索実行
            result = await self.platform.personalized_search(
                user_id, query, search_history
            )

            # 結果表示
            if result.get("results"):
                print(f"✅ 検索完了: {result['total_found']}件発見")
                print(
                    f"🎯 パーソナライズ: {result.get('personalization_applied', False)}"
                )

                # ユーザープロファイル表示
                if result.get("user_profile"):
                    profile = result["user_profile"]
                    print(f"\n👤 ユーザープロファイル:")
                    print(f"   興味分野: {', '.join(profile.get('interests', []))}")
                    print(
                        f"   検索パターン: {profile.get('search_patterns', {}).get('frequent_terms', [])}"
                    )

                # 結果表示
                for i, item in enumerate(result["results"][:5]):
                    print(f"\n{i+1}. {item.get('title', 'タイトルなし')}")
                    print(f"   類似度: {item.get('similarity', 0):0.3f}")
                    if "personalization_score" in item:
                        print(
                            f"   パーソナライズスコア: {item['personalization_score']:0.3f}"
                        )
                    print(f"   内容: {item.get('content', '')[:100]}...")

            else:
                print(f"❌ 検索失敗: {result.get('error', '結果なし')}")

        except Exception as e:
            print(f"❌ パーソナライズド検索エラー: {e}")

    async def show_dashboard(self):
        """リアルタイム分析ダッシュボード表示"""
        if not await self.initialize():
            return

        print("📊 リアルタイム分析ダッシュボード")
        print("=" * 60)

        try:
            # ダッシュボードデータ取得
            dashboard = await self.platform.real_time_analytics_dashboard()

            # ダッシュボード表示
            print(f"🟢 ステータス: {dashboard.get('status', 'unknown')}")
            print(f"🕐 最終更新: {dashboard.get('last_updated', 'N/A')}")

            # 検索トレンド
            if dashboard.get("search_trends"):
                trends = dashboard["search_trends"]
                print(f"\n🔍 検索トレンド:")
                print(f"   人気クエリ: {', '.join(trends.get('top_queries', []))}")
                print(f"   検索増加率: {trends.get('query_growth', 0)*100:0.1f}%")
                print(
                    f"   人気カテゴリ: {', '.join(trends.get('popular_categories', []))}"
                )

            # コンテンツ統計
            if dashboard.get("content_statistics"):
                stats = dashboard["content_statistics"]
                print(f"\n📚 コンテンツ統計:")
                print(f"   総文書数: {stats.get('total_documents', 0):,}")
                print(f"   平均品質: {stats.get('average_quality', 0):0.2f}")
                print(f"   最近の追加: {stats.get('recent_additions', 0)}件")

                if stats.get("content_types"):
                    print(f"   コンテンツタイプ:")
                    for content_type, count in stats["content_types"].items():
                        print(f"     {content_type}: {count}")

            # ユーザー行動
            if dashboard.get("user_behavior"):
                behavior = dashboard["user_behavior"]
                print(f"\n👥 ユーザー行動:")
                print(f"   アクティブユーザー: {behavior.get('active_users', 0)}")
                print(
                    f"   平均セッション時間: {behavior.get('average_session_duration', 0):0.1f}分"
                )
                print(f"   離脱率: {behavior.get('bounce_rate', 0)*100:0.1f}%")
                print(f"   エンゲージメント: {behavior.get('engagement_score', 0):0.2f}")

            # パフォーマンス指標
            if dashboard.get("performance_metrics"):
                perf = dashboard["performance_metrics"]
                print(f"\n⚡ パフォーマンス指標:")
                print(f"   平均応答時間: {perf.get('average_response_time', 0):0.2f}秒")
                print(f"   検索成功率: {perf.get('search_success_rate', 0)*100:0.1f}%")
                print(f"   システム稼働率: {perf.get('system_uptime', 0)*100:0.3f}%")
                print(
                    f"   キャッシュヒット率: {perf.get('cache_hit_rate', 0)*100:0.1f}%"
                )

            # 4賢者統合状況
            if dashboard.get("sages_integration"):
                sages = dashboard["sages_integration"]
                print(f"\n🧙‍♂️ 4賢者統合状況:")
                if sages.get("integration_status"):
                    integration = sages["integration_status"]
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

        except Exception as e:
            print(f"❌ ダッシュボード表示エラー: {e}")

    async def show_platform_status(self):
        """プラットフォーム状況表示"""
        if not await self.initialize():
            return

        print("📊 プラットフォーム状況")
        print("=" * 60)

        try:
            # 基本情報
            print(f"🏗️ プラットフォーム: Advanced Search & Analytics Platform")
            print(f"🔧 初期化状況: {'✅ 完了' if self.initialized else '❌ 未完了'}")
            print(f"🕐 確認時刻: {datetime.now().isoformat()}")

            # 利用可能な機能
            print(f"\n🛠️ 利用可能な機能:")
            functions = [
                "ハイブリッド検索 (ベクトル+全文検索)",
                "高度分析 (統計・パターン・トレンド・予測・分類・クラスタリング)",
                "パーソナライズド検索",
                "リアルタイム分析ダッシュボード",
                "4賢者システム統合",
                "キャッシュ機能",
                "パフォーマンス監視",
            ]

            for func in functions:
                print(f"   ✅ {func}")

            # 検索タイプ
            print(f"\n🔍 対応検索タイプ:")
            search_types = [
                "vector (ベクトル検索)",
                "fulltext (全文検索)",
                "hybrid (ハイブリッド検索)",
                "semantic (セマンティック検索)",
                "fuzzy (あいまい検索)",
                "contextual (コンテキスト検索)",
            ]

            for search_type in search_types:
                print(f"   🎯 {search_type}")

            # 分析タイプ
            print(f"\n📊 対応分析タイプ:")
            analytics_types = [
                "statistical (統計分析)",
                "pattern_recognition (パターン認識)",
                "trend_analysis (トレンド分析)",
                "predictive (予測分析)",
                "classification (分類分析)",
                "clustering (クラスタリング分析)",
            ]

            for analytics_type in analytics_types:
                print(f"   📈 {analytics_type}")

        except Exception as e:
            print(f"❌ 状況表示エラー: {e}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="高度検索・分析プラットフォーム CLI")

    # 検索コマンド
    parser.add_argument("--hybrid-search", type=str, help="ハイブリッド検索実行")
    parser.add_argument(
        "--search-type",
        choices=["vector", "fulltext", "hybrid", "semantic", "fuzzy", "contextual"],
        default="hybrid",
        help="検索タイプ",
    )
    parser.add_argument("--limit", type=int, default=10, help="検索結果上限")
    parser.add_argument(
        "--similarity-threshold", type=float, default=0.7, help="類似度閾値"
    )
    parser.add_argument("--context", type=str, help="検索コンテキスト")

    # 分析コマンド
    parser.add_argument(
        "--analytics",
        choices=[
            "statistical",
            "pattern_recognition",
            "trend_analysis",
            "predictive",
            "classification",
            "clustering",
        ],
        help="分析タイプ",
    )
    parser.add_argument("data_query", nargs="?", help="分析対象データクエリ")

    # パーソナライズド検索
    parser.add_argument("--personalized-search", type=str, help="ユーザーID")
    parser.add_argument("--user-query", type=str, help="パーソナライズド検索クエリ")

    # ダッシュボード・状況表示
    parser.add_argument(
        "--dashboard", action="store_true", help="リアルタイム分析ダッシュボード表示"
    )
    parser.add_argument(
        "--status", action="store_true", help="プラットフォーム状況表示"
    )

    # フィルタ・オプション
    parser.add_argument("--filters", type=str, help="検索フィルタ（JSON形式）")
    parser.add_argument("--search-history", type=str, help="検索履歴（JSON形式）")

    args = parser.parse_args()

    # CLIインスタンス作成
    cli = AdvancedSearchAnalyticsCLI()

    async def run_cli():
        """run_cliを実行"""
        try:
            if args.status:
                await cli.show_platform_status()
            elif args.dashboard:
                await cli.show_dashboard()
            elif args.hybrid_search:
                filters = json.loads(args.filters) if args.filters else None
                await cli.hybrid_search(
                    args.hybrid_search,
                    args.search_type,
                    args.limit,
                    args.similarity_threshold,
                    filters,
                    args.context,
                )
            elif args.analytics and args.data_query:
                context = json.loads(args.context) if args.context else None
                await cli.advanced_analytics(args.analytics, args.data_query, context)
            elif args.personalized_search and args.user_query:
                history = (
                    json.loads(args.search_history) if args.search_history else None
                )
                await cli.personalized_search(
                    args.personalized_search, args.user_query, history
                )
            else:
                parser.print_help()
                print("\n💡 使用例:")
                print("   python3 scripts/advanced_search_analytics_cli.py --status")
                print("   python3 scripts/advanced_search_analytics_cli.py --dashboard")
                print(
                    "   python3 scripts/advanced_search_analytics_cli.py --hybrid-search '4賢者システム' --limit 5"
                )
                print(
                    "   python3 scripts/advanced_search_analytics_cli.py --analytics statistical 'PostgreSQL MCP'"
                )
                print(
                    "   python3 scripts/advanced_search_analytics_cli.py --personalized-search \
                        user123 --user-query 'データベース'"
                )

        except KeyboardInterrupt:
            print("\n⚠️ 処理が中断されました")
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")

    # 非同期実行
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
