#!/usr/bin/env python3
"""
4賢者PostgreSQL MCP統合 CLI インターフェース
コマンドラインから4賢者の統合機能を操作

使用例:
python3 scripts/four_sages_mcp_cli.py --sage knowledge --search "4賢者システム"
python3 scripts/four_sages_mcp_cli.py --sage task --manage "新規タスク"
python3 scripts/four_sages_mcp_cli.py --sage incident --monitor "システム異常"
python3 scripts/four_sages_mcp_cli.py --sage rag --enhance-search "PostgreSQL"
python3 scripts/four_sages_mcp_cli.py --collaborative-analysis "統合評価"
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

from libs.four_sages_postgres_mcp_integration import FourSagesPostgresMCPIntegration

class FourSagesMCPCLI:
    """4賢者MCP統合CLI"""

    def __init__(self):
        self.four_sages = FourSagesPostgresMCPIntegration()
        self.initialized = False

    async def initialize(self):
        """初期化"""
        if not self.initialized:
            init_result = await self.four_sages.initialize_mcp_integration()
            if init_result['success']:
                self.initialized = True
                print("✅ 4賢者MCP統合システム初期化完了")
            else:
                print(f"❌ 初期化失敗: {init_result.get('error', 'Unknown error')}")
                return False
        return True

    async def knowledge_sage_search(self, query: str, limit: int = 10):
        """ナレッジ賢者検索"""
        if not await self.initialize():
            return

        print(f"📚 ナレッジ賢者による検索: '{query}'")
        print("-" * 50)

        result = await self.four_sages.knowledge_sage_search(query, limit)

        if result['status'] == 'success':
            print(f"✅ 検索完了: {result['total_found']}件発見")

            for i, item in enumerate(result['results'][:5]):
                print(f"\n{i+1}. {item['title']}")
                print(f"   タイプ: {item['type']}")
                print(f"   内容: {item['content'][:100]}...")
                if 'similarity' in item:
                    print(f"   類似度: {item['similarity']:.3f}")

            if result['pattern_analysis']:
                print(f"\n📊 パターン分析:")
                print(f"   共通テーマ: {result['pattern_analysis']['common_themes']}")
                print(f"   推奨事項: {result['pattern_analysis']['recommendations']}")
        else:
            print(f"❌ 検索失敗: {result['message']}")

    async def task_sage_management(self, task_description: str, priority: str = 'normal'):
        """タスク賢者管理"""
        if not await self.initialize():
            return

        print(f"📋 タスク賢者による管理: '{task_description}'")
        print("-" * 50)

        task_request = {
            'id': f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'title': task_description,
            'type': 'cli_request',
            'priority': priority,
            'description': task_description,
            'created_at': datetime.now().isoformat()
        }

        result = await self.four_sages.task_sage_management(task_request)

        if result['status'] == 'success':
            print(f"✅ タスク管理完了")
            print(f"   保存状況: {'成功' if result['task_stored'] else '失敗'}")

            if result['task_analysis']:
                print(f"\n📊 タスク分析:")
                print(f"   複雑度: {result['task_analysis']['complexity_assessment']}")
                print(f"   推定時間: {result['task_analysis']['estimated_duration']}")

            if result['recommendations']:
                print(f"\n💡 推奨事項:")
                for rec in result['recommendations']:
                    print(f"   - {rec}")
        else:
            print(f"❌ タスク管理失敗: {result['message']}")

    async def incident_sage_monitoring(self, incident_description: str, severity: str = 'normal'):
        """インシデント賢者監視"""
        if not await self.initialize():
            return

        print(f"🚨 インシデント賢者による監視: '{incident_description}'")
        print("-" * 50)

        incident_data = {
            'id': f"incident_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'type': 'cli_report',
            'severity': severity,
            'description': incident_description,
            'timestamp': datetime.now().isoformat()
        }

        result = await self.four_sages.incident_sage_monitoring(incident_data)

        if result['status'] == 'success':
            print(f"✅ インシデント監視完了")
            print(f"   記録状況: {'成功' if result['incident_stored'] else '失敗'}")

            if result['urgency_assessment']:
                print(f"\n⚡ 緊急度評価:")
                print(f"   レベル: {result['urgency_assessment']['level']}")
                print(f"   対応時間: {result['urgency_assessment']['response_time']}")

            if result['recommended_actions']:
                print(f"\n🔧 推奨対応:")
                for action in result['recommended_actions']:
                    print(f"   - {action}")
        else:
            print(f"❌ インシデント監視失敗: {result['message']}")

    async def rag_sage_enhanced_search(self, query: str, context: str = None):
        """RAG賢者拡張検索"""
        if not await self.initialize():
            return

        print(f"🔍 RAG賢者による拡張検索: '{query}'")
        if context:
            print(f"   コンテキスト: '{context}'")
        print("-" * 50)

        result = await self.four_sages.rag_sage_enhanced_search(query, context)

        if result['status'] == 'success':
            print(f"✅ 拡張検索完了: {result['total_found']}件発見")
            print(f"   検索戦略: {result['search_strategies_used']}種類")

            for i, item in enumerate(result['results'][:5]):
                print(f"\n{i+1}. {item['title']}")
                print(f"   内容: {item['content'][:100]}...")
                if 'similarity' in item:
                    print(f"   類似度: {item['similarity']:.3f}")

            if result['relevance_analysis']:
                print(f"\n📊 関連性分析:")
                print(f"   平均関連度: {result['relevance_analysis']['average_relevance']:.3f}")
                print(f"   カバレッジ: {result['relevance_analysis']['query_coverage']}")
        else:
            print(f"❌ 拡張検索失敗: {result['message']}")

    async def collaborative_analysis(self, analysis_topic: str):
        """4賢者協調分析"""
        if not await self.initialize():
            return

        print(f"🧙‍♂️ 4賢者協調分析: '{analysis_topic}'")
        print("=" * 60)

        analysis_request = {
            'title': analysis_topic,
            'query': analysis_topic,
            'context': 'CLI経由の協調分析',
            'task_data': {
                'id': f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'title': f"分析: {analysis_topic}",
                'type': 'analysis',
                'priority': 'high'
            },
            'incident_data': {
                'id': f"check_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'type': 'analysis_check',
                'severity': 'low',
                'description': f"分析対象: {analysis_topic}"
            }
        }

        result = await self.four_sages.four_sages_collaborative_analysis(analysis_request)

        if result['status'] == 'success':
            print(f"✅ 協調分析完了")
            print(f"   分析保存: {'成功' if result['analysis_stored'] else '失敗'}")

            # 各賢者の分析結果
            print(f"\n🧙‍♂️ 各賢者の分析結果:")
            for sage_name, analysis in result['individual_analyses'].items():
                if analysis and analysis.get('status') == 'success':
                    print(f"   ✅ {sage_name}: 分析完了")
                else:
                    print(f"   ❌ {sage_name}: 分析失敗")

            # コンセンサス結果
            if result['consensus_result']:
                print(f"\n🏛️ コンセンサス結果:")
                print(f"   合意達成: {result['consensus_result']['consensus_reached']}")
                print(f"   参加賢者: {len(result['consensus_result']['participating_sages'])}")
                print(f"   信頼度: {result['consensus_result']['confidence_score']:.2f}")
                print(f"   最終推奨: {result['consensus_result']['final_recommendation']}")
        else:
            print(f"❌ 協調分析失敗: {result['message']}")

    async def show_status(self):
        """統合状況表示"""
        if not await self.initialize():
            return

        print("📊 4賢者PostgreSQL MCP統合状況")
        print("=" * 60)

        status = await self.four_sages.get_integration_status()

        # 統合状況
        integration_status = status['integration_status']
        print(f"🔗 MCP接続: {'✅ 接続済み' if integration_status['mcp_connected'] else '❌ 未接続'}")
        print(f"🧙‍♂️ 賢者統合: {'✅ 完了' if integration_status['sages_integrated'] else '❌ 未完了'}")
        print(f"📚 保存済み知識: {integration_status['total_knowledge_stored']}件")
        print(f"🔍 検索実行数: {integration_status['total_searches_performed']}回")

        if integration_status['last_sync']:
            print(f"🕐 最終同期: {integration_status['last_sync']}")

        # MCP統計
        if status.get('mcp_stats'):
            mcp_stats = status['mcp_stats']
            print(f"\n📊 MCP統計:")
            if 'basic_stats' in mcp_stats:
                basic = mcp_stats['basic_stats']
                print(f"   総文書数: {basic['total_documents']}")
                print(f"   文書タイプ: {basic['unique_types']}")
                print(f"   平均文字数: {basic['avg_content_length']:.0f}")

        # MCP健康状態
        if status.get('mcp_health'):
            mcp_health = status['mcp_health']
            print(f"\n💊 MCP健康状態:")
            print(f"   接続: {mcp_health['connection']}")
            print(f"   総文書: {mcp_health['total_documents']}")
            print(f"   DBサイズ: {mcp_health['database_size']:,} bytes")

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='4賢者PostgreSQL MCP統合 CLI')

    # 賢者別オプション
    parser.add_argument('--sage', choices=['knowledge', 'task', 'incident', 'rag'],
                       help='使用する賢者を選択')

    # 機能別オプション
    parser.add_argument('--search', type=str, help='検索クエリ')
    parser.add_argument('--manage', type=str, help='管理するタスク')
    parser.add_argument('--monitor', type=str, help='監視するインシデント')
    parser.add_argument('--enhance-search', type=str, help='拡張検索クエリ')
    parser.add_argument('--collaborative-analysis', type=str, help='協調分析トピック')

    # オプション
    parser.add_argument('--priority', choices=['low', 'normal', 'high', 'critical'],
                       default='normal', help='優先度')
    parser.add_argument('--severity', choices=['low', 'medium', 'high', 'critical'],
                       default='normal', help='重要度')
    parser.add_argument('--context', type=str, help='検索コンテキスト')
    parser.add_argument('--limit', type=int, default=10, help='検索結果上限')

    # システム操作
    parser.add_argument('--status', action='store_true', help='統合状況表示')

    args = parser.parse_args()

    # CLIインスタンス作成
    cli = FourSagesMCPCLI()

    async def run_cli():
        try:
            if args.status:
                await cli.show_status()
            elif args.collaborative_analysis:
                await cli.collaborative_analysis(args.collaborative_analysis)
            elif args.sage == 'knowledge' and args.search:
                await cli.knowledge_sage_search(args.search, args.limit)
            elif args.sage == 'task' and args.manage:
                await cli.task_sage_management(args.manage, args.priority)
            elif args.sage == 'incident' and args.monitor:
                await cli.incident_sage_monitoring(args.monitor, args.severity)
            elif args.sage == 'rag' and args.enhance_search:
                await cli.rag_sage_enhanced_search(args.enhance_search, args.context)
            else:
                parser.print_help()
                print("\n💡 使用例:")
                print("   python3 scripts/four_sages_mcp_cli.py --status")
                print("   python3 scripts/four_sages_mcp_cli.py --sage knowledge --search '4賢者'")
                print("   python3 scripts/four_sages_mcp_cli.py --collaborative-analysis 'システム統合'")

        except KeyboardInterrupt:
            print("\n⚠️ 処理が中断されました")
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")

    # 非同期実行
    asyncio.run(run_cli())

if __name__ == "__main__":
    main()
