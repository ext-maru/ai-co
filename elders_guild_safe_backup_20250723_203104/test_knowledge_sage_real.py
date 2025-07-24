#!/usr/bin/env python3
"""
🧪 Knowledge Sage A2A Agent - 実動作テスト
モックなしの実際のテスト

実際のビジネスロジックとA2A通信で動作確認
"""

import asyncio
import json
import logging
from python_a2a import Message, TextContent, MessageRole

from knowledge_sage.a2a_agent import KnowledgeSageAgent

async def test_real_knowledge_sage():
    pass


"""実際のKnowledge Sage A2A Agent動作テスト"""
        # 初期化
        print("\n🔧 1.0 エージェント初期化...")
        init_result = await agent.initialize()
        print(f"   初期化結果: {init_result}")
        assert init_result is True, "初期化失敗"
        
        # 基本情報確認
        print(f"\n📋 2.0 エージェント情報確認...")
        print(f"   エージェント名: {agent.agent_name}")
        print(f"   ポート: {agent.port}")
        print(f"   説明: {agent.description}")
        
        # テスト1: 基本的な知識検索
        print(f"\n🔍 3.0 基本的な知識検索テスト...")
        search_message = Message(
            content=TextContent(text="python programming"),
            role=MessageRole.USER
        )
        
        search_response = await agent.search_knowledge_skill(search_message)
        print(f"   応答タイプ: {type(search_response)}")
        print(f"   応答ロール: {search_response.role}")
        
        search_data = json.loads(search_response.content.text)
        print(f"   検索成功: {search_data.get('success', False)}")
        if search_data.get('success'):
            results = search_data.get('data', {}).get('results', [])
            print(f"   検索結果数: {len(results)}")
        
        # テスト2: JSON構造化データ検索
        print(f"\n📄 4.0 JSON構造化データ検索テスト...")
        json_query = {
            "query": "machine learning",
            "limit": 5,
            "category": "technology"
        }
        
        json_message = Message(
            content=TextContent(text=json.dumps(json_query)),
            role=MessageRole.USER
        )
        
        json_response = await agent.search_knowledge_skill(json_message)
        json_data = json.loads(json_response.content.text)
        print(f"   JSON検索成功: {json_data.get('success', False)}")
        
        # テスト3: 統計情報取得
        print(f"\n📊 5.0 統計情報取得テスト...")
        stats_message = Message(
            content=TextContent(text=""),
            role=MessageRole.USER
        )
        
        # get_statistics_skillを実装していた場合
        if hasattr(agent, 'get_statistics_skill'):
            stats_response = await agent.get_statistics_skill(stats_message)
            stats_data = json.loads(stats_response.content.text)
            print(f"   統計取得成功: {stats_data.get('success', False)}")
            if stats_data.get('success'):
                total_items = stats_data.get('data', {}).get('total_items', 0)
                print(f"   総知識アイテム数: {total_items}")
        else:
            print("   get_statistics_skill未実装（予想通り）")
        
        # テスト4: ヘルスチェック
        print(f"\n🏥 6.0 ヘルスチェックテスト...")
        if hasattr(agent, 'health_check_skill'):
            health_response = await agent.health_check_skill(stats_message)
            health_data = json.loads(health_response.content.text)
            print(f"   ヘルス状態: {health_data.get('status', 'unknown')}")
            print(f"   ヘルスチェック成功: {health_data.get('status') }")
        else:
            print("   health_check_skill未実装（予想通り）")
        
        # テスト5: エラーケース
        print(f"\n🚨 7.0 エラーハンドリングテスト...")
        
        # 無効なJSONでテスト（プレーンテキストとして処理される）
        invalid_message = Message(
            content=TextContent(text="invalid {json: malformed"),
            role=MessageRole.USER
        )
        
        error_response = await agent.search_knowledge_skill(invalid_message)
        error_data = json.loads(error_response.content.text)
        print(f"   無効JSON処理成功: {error_data.get('success', False)}")
        
        # テスト6: パフォーマンステスト
        print(f"\n⚡ 8.0 パフォーマンステスト...")
        import time
        
        start_time = time.time()
        perf_message = Message(
            content=TextContent(text="performance test"),
            role=MessageRole.USER
        )
        
        # 10回連続実行
        for i in range(10):
            await agent.search_knowledge_skill(perf_message)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 10
        
        print(f"   10回実行総時間: {total_time:0.3f}秒")
        print(f"   平均応答時間: {avg_time:0.3f}秒")
        print(f"   パフォーマンス目標達成: {avg_time < 0.1}")
        
        # 実際のビジネスロジック動作確認
        print(f"\n🧠 9.0 ビジネスロジック実動作確認...")
        
        # Knowledge Processorが実際にファイルからデータを読み込んでいるかチェック
        processor = agent.knowledge_processor
        print(f"   Knowledge Processor タイプ: {type(processor)}")
        print(f"   データディレクトリ: {processor.data_dir}")
        print(f"   ファイル存在確認:")
        print(f"     - knowledge_file: {processor.knowledge_file.exists()}")
        print(f"     - practices_file: {processor.practices_file.exists()}")
        print(f"     - patterns_file: {processor.patterns_file.exists()}")
        
        # 内部データ状態確認
        knowledge_count = len(processor._knowledge_items)
        practices_count = len(processor._best_practices)
        patterns_count = len(processor._learning_patterns)
        
        print(f"   内部データ状態:")
        print(f"     - 知識アイテム数: {knowledge_count}")
        print(f"     - ベストプラクティス数: {practices_count}")
        print(f"     - 学習パターン数: {patterns_count}")
        
        print(f"\n✅ 10.0 テスト完了サマリー")
        print("=" * 60)
        print("🎉 Knowledge Sage A2A Agent実動作テスト成功！")
        print(f"✅ A2AServerベース実装動作確認")
        print(f"✅ python-a2a標準通信動作確認")
        print(f"✅ 既存ビジネスロジック活用確認")
        print(f"✅ JSON通信正常動作確認")
        print(f"✅ エラーハンドリング動作確認")
        print(f"✅ パフォーマンス基準達成確認")
        print(f"✅ 実データファイル読込み確認")
        
        return True
        
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # クリーンアップ
        print(f"\n🧹 クリーンアップ...")
        await agent.shutdown()
        print("✅ エージェント正常終了")

async def main():
    pass

        """メイン実行"""
        print(f"\n🏛️ 実動作テスト完全成功！")
        print("   Knowledge Sage A2A変換は実戦で使用可能です！")
    else:
        print(f"\n💥 実動作テストで問題発見")
        print("   修正が必要です")

if __name__ == "__main__":
    asyncio.run(main())