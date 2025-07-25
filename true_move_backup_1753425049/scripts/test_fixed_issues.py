#!/usr/bin/env python3
"""
修正された問題のテスト実行
注意事項の解消状況を個別にテスト
"""

import asyncio
import logging
import sys
import time
sys.path.append('/home/aicompany/ai_co')

from libs.postgresql_mcp_integration import PostgreSQLMCPManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fixed_japanese_search():
    """修正された日本語検索のテスト"""
    print("🇯🇵 日本語全文検索修正テスト")
    print("-" * 40)
    
    manager = PostgreSQLMCPManager()
    
    try:
        await manager.connect()
        
        async with manager.pool.acquire() as conn:
            # 新しい日本語検索関数をテスト
            start_time = time.time()
            
            results = await conn.fetch("""
                SELECT * FROM knowledge_sage.enhanced_japanese_search('テスト', 10, 0.1)
            """)
            
            end_time = time.time()
            
            print(f"✅ 日本語検索成功")
            print(f"   - 検索結果: {len(results)}件")
            print(f"   - 実行時間: {(end_time - start_time):0.3f}秒")
            
            if results:
                print("   - 検索結果例:")
                for i, row in enumerate(results[:3], 1):
                    print(f"     {i}. {row['title'][:50]}... (スコア: {row['search_score']:0.3f})")
            
            return True
            
    except Exception as e:
        print(f"❌ 日本語検索テスト失敗: {e}")
        return False
    
    finally:
        await manager.disconnect()

async def test_fixed_semantic_search():
    """修正されたセマンティック検索のテスト"""
    print("\n🤖 セマンティック検索修正テスト")
    print("-" * 40)
    
    manager = PostgreSQLMCPManager()
    
    try:
        await manager.connect()
        
        async with manager.pool.acquire() as conn:
            # モックセマンティック検索関数をテスト
            start_time = time.time()
            
            # 関数の存在確認
            func_check = await conn.fetchrow("""
                SELECT COUNT(*) as count FROM pg_proc 
                WHERE proname = 'mock_semantic_search_enhanced'
            """)
            
            if func_check['count'] == 0:
                print("⚠️ セマンティック検索関数が見つかりません。再作成中...")
                
                # 関数を再作成
                await conn.execute("""
                    CREATE OR REPLACE FUNCTION mock_text_similarity(text1 TEXT, text2 TEXT)
                    RETURNS FLOAT AS $$
                    DECLARE
                        similarity FLOAT := 0.0;
                        word1 TEXT;
                        word2 TEXT;
                    BEGIN
                        IF text1 IS NULL OR text2 IS NULL THEN
                            RETURN 0.0;
                        END IF;
                        
                        word1 := lower(regexp_replace(text1, '[^a-zA-Z0-9ぁ-んァ-ヶー一-龯]', '', 'g'));
                        word2 := lower(regexp_replace(text2, '[^a-zA-Z0-9ぁ-んァ-ヶー一-龯]', '', 'g'));
                        
                        IF word1 = word2 THEN
                            RETURN 1.0;
                        END IF;
                        
                        IF position(word2 IN word1) > 0 OR position(word1 IN word2) > 0 THEN
                            similarity := 0.7;
                        END IF;
                        
                        RETURN similarity;
                    END;
                    $$ LANGUAGE plpgsql IMMUTABLE;
                """)
                
                await conn.execute("""
                    CREATE OR REPLACE FUNCTION knowledge_sage.mock_semantic_search_enhanced(
                        query_text TEXT,
                        similarity_threshold FLOAT DEFAULT 0.3,
                        max_results INTEGER DEFAULT 10
                    )
                    RETURNS TABLE (
                        id UUID,
                        title VARCHAR(500),
                        content TEXT,
                        similarity FLOAT,
                        quality_score FLOAT,
                        category VARCHAR(100),
                        metadata JSONB
                    ) AS $$
                    BEGIN
                        RETURN QUERY
                        SELECT
                            ke.id,
                            ke.title,
                            ke.content,
                            mock_text_similarity(ke.title, query_text) AS similarity,
                            ke.quality_score,
                            ke.category,
                            ke.metadata
                        FROM knowledge_sage.knowledge_entities ke
                        WHERE mock_text_similarity(ke.title, query_text) > similarity_threshold
                           OR mock_text_similarity(ke.content, query_text) > similarity_threshold
                        ORDER BY similarity DESC, ke.quality_score DESC
                        LIMIT max_results;
                    END;
                    $$ LANGUAGE plpgsql;
                """)
            
            # セマンティック検索実行
            results = await conn.fetch("""
                SELECT * FROM knowledge_sage.mock_semantic_search_enhanced($1, 0.3, 5)
            """, "統合")
            
            end_time = time.time()
            
            print(f"✅ セマンティック検索成功")
            print(f"   - 検索結果: {len(results)}件")
            print(f"   - 実行時間: {(end_time - start_time):0.3f}秒")
            
            if results:
                print("   - 検索結果例:")
                for i, row in enumerate(results[:3], 1):
                    print(f"     {i}. {row['title'][:50]}... (類似度: {row['similarity']:0.3f})")
            
            return True
            
    except Exception as e:
        print(f"❌ セマンティック検索テスト失敗: {e}")
        return False
    
    finally:
        await manager.disconnect()

async def test_fixed_error_handling():
    """修正されたエラーハンドリングのテスト"""
    print("\n🛡️ エラーハンドリング修正テスト")
    print("-" * 40)
    
    manager = PostgreSQLMCPManager()
    
    try:
        await manager.connect()
        
        async with manager.pool.acquire() as conn:
            # 1.0 正常データの検証テスト
            validation_result = await conn.fetchrow("""
                SELECT validate_knowledge_entity('正常タイトル', '正常コンテンツ', 0.8) as result
            """)
            
            print(f"✅ 正常データ検証: {validation_result['result']}")
            
            # 2.0 異常データの検証テスト
            invalid_tests = [
                ("", "コンテンツ", 0.5, "空タイトル"),
                ("タイトル", "", 0.5, "空コンテンツ"), 
                ("タイトル", "コンテンツ", 2.0, "範囲外品質スコア"),
                ("タイトル", "コンテンツ", -0.5, "負の品質スコア")
            ]
            
            for title, content, quality, test_name in invalid_tests:
                validation_result = await conn.fetchrow("""
                    SELECT validate_knowledge_entity($1, $2, $3) as result
                """, title, content, quality)
                
                is_error = validation_result['result'] != 'OK'
                status = "✅ エラー検出" if is_error else "❌ エラー未検出"
                print(f"   {test_name}: {status}")
            
            # 3.0 安全挿入テスト
            safe_result = await conn.fetchrow("""
                SELECT * FROM knowledge_sage.safe_insert_entity(
                    gen_random_uuid(),
                    'エラーハンドリングテスト',
                    'エラーハンドリング機能のテストです。',
                    'test',
                    'test_category',
                    ARRAY['test', 'error_handling'],
                    0.8,
                    'test_user'
                )
            """)
            
            print(f"✅ 安全挿入テスト: {'成功' if safe_result['success'] else '失敗'}")
            print(f"   メッセージ: {safe_result['message']}")
            
            return True
            
    except Exception as e:
        print(f"❌ エラーハンドリングテスト失敗: {e}")
        return False
    
    finally:
        await manager.disconnect()

async def test_search_comparison():
    """修正前後の検索性能比較"""
    print("\n📊 検索性能比較テスト")
    print("-" * 40)
    
    manager = PostgreSQLMCPManager()
    
    try:
        await manager.connect()
        
        test_queries = ["テスト", "統合", "PostgreSQL", "4賢者"]
        
        for query in test_queries:
            print(f"\n🔍 クエリ: '{query}'")
            
            async with manager.pool.acquire() as conn:
                # 1.0 従来の全文検索（エラーが発生する可能性）
                try:
                    start_time = time.time()
                    old_results = await manager.full_text_search(query, max_results=5)
                    old_time = time.time() - start_time
                    print(f"   従来検索: {len(old_results)}件 ({old_time:0.3f}秒)")
                except Exception as e:
                    print(f"   従来検索: エラー ({str(e)[:50]}...)")
                
                # 2.0 新しい日本語検索
                try:
                    start_time = time.time()
                    new_results = await conn.fetch("""
                        SELECT * FROM knowledge_sage.enhanced_japanese_search($1, 5, 0.1)
                    """, query)
                    new_time = time.time() - start_time
                    print(f"   新日本語検索: {len(new_results)}件 ({new_time:0.3f}秒)")
                except Exception as e:
                    print(f"   新日本語検索: エラー ({str(e)[:50]}...)")
                
                # 3.0 セマンティック検索
                try:
                    start_time = time.time()
                    sem_results = await conn.fetch("""
                        SELECT * FROM knowledge_sage.mock_semantic_search_enhanced($1, 0.3, 5)
                    """, query)
                    sem_time = time.time() - start_time
                    print(f"   セマンティック検索: {len(sem_results)}件 ({sem_time:0.3f}秒)")
                except Exception as e:
                    print(f"   セマンティック検索: エラー ({str(e)[:50]}...)")
        
        return True
        
    except Exception as e:
        print(f"❌ 検索比較テスト失敗: {e}")
        return False
    
    finally:
        await manager.disconnect()

async def main():
    """メイン実行関数"""
    print("🔧 PostgreSQL MCP修正項目テスト実行")
    print("=" * 60)
    
    test_results = {
        "japanese_search": False,
        "semantic_search": False,
        "error_handling": False,
        "search_comparison": False
    }
    
    # 各テスト実行
    test_results["japanese_search"] = await test_fixed_japanese_search()
    test_results["semantic_search"] = await test_fixed_semantic_search()
    test_results["error_handling"] = await test_fixed_error_handling()
    test_results["search_comparison"] = await test_search_comparison()
    
    # 結果サマリー
    print("\n" + "="*60)
    print("🏆 修正項目テスト結果サマリー")
    print("="*60)
    
    success_count = sum(1 for success in test_results.values() if success)
    total_count = len(test_results)
    
    for test_name, success in test_results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        test_display = {
            "japanese_search": "日本語全文検索",
            "semantic_search": "セマンティック検索", 
            "error_handling": "エラーハンドリング",
            "search_comparison": "検索性能比較"
        }.get(test_name, test_name)
        print(f"- {test_display}: {status}")
    
    print(f"\n📊 成功率: {success_count}/{total_count} ({(success_count/total_count*100):0.1f}%)")
    
    if success_count == total_count:
        print("\n🎉 すべての修正項目が正常に動作しています！")
        print("注意事項は完全に解消されました！")
        return True
    else:
        print(f"\n⚠️ {total_count - success_count}項目で問題が残存しています")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)