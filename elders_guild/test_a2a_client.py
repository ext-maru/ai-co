#!/usr/bin/env python3
"""
📡 Knowledge Sage A2A Client - 実際のA2A通信テスト
別プロセスのサーバーとA2A通信
"""

import asyncio
import json
import httpx
from python_a2a import A2AClient, Message, TextContent, MessageRole

async def test_a2a_communication():
    """実際のA2A通信テスト"""
    
    print("📡 Knowledge Sage A2A Client - 通信テスト開始")
    print("=" * 60)
    
    server_url = "http://localhost:8807"
    
    try:
        # 1. サーバー生存確認
        print(f"\n🔍 1. サーバー生存確認 ({server_url})...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{server_url}/", timeout=5.0)
                print(f"   HTTP応答: {response.status_code}")
                print(f"   応答内容: {response.text[:200]}...")
                
                if response.status_code == 200:
                    print("   ✅ サーバー応答正常")
                else:
                    print(f"   ⚠️ 予期しないステータス: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ サーバー接続失敗: {e}")
                return False
        
        # 2. A2Aエンドポイント確認
        print(f"\n🔗 2. A2Aエンドポイント確認...")
        
        async with httpx.AsyncClient() as client:
            # python-a2aのデフォルトエンドポイントを推測
            endpoints_to_test = [
                "/a2a",
                "/api/a2a", 
                "/agent",
                "/skills",
                "/message"
            ]
            
            working_endpoint = None
            
            for endpoint in endpoints_to_test:
                try:
                    response = await client.get(f"{server_url}{endpoint}", timeout=3.0)
                    print(f"   {endpoint}: {response.status_code}")
                    
                    if response.status_code in [200, 405]:  # 405 = Method Not Allowed (POSTが期待される)
                        working_endpoint = endpoint
                        break
                        
                except Exception as e:
                    print(f"   {endpoint}: エラー ({type(e).__name__})")
            
            if working_endpoint:
                print(f"   ✅ A2Aエンドポイント発見: {working_endpoint}")
            else:
                print("   ⚠️ A2Aエンドポイント未発見")
        
        # 3. スキル一覧取得試行
        print(f"\n📋 3. スキル一覧取得試行...")
        
        async with httpx.AsyncClient() as client:
            try:
                # GETリクエストでスキル情報取得試行
                response = await client.get(f"{server_url}/skills", timeout=5.0)
                
                if response.status_code == 200:
                    print(f"   ✅ スキル一覧取得成功:")
                    try:
                        skills_data = response.json()
                        print(f"   スキル数: {len(skills_data) if isinstance(skills_data, list) else 'N/A'}")
                        print(f"   応答: {json.dumps(skills_data, indent=2, ensure_ascii=False)[:300]}...")
                    except:
                        print(f"   応答テキスト: {response.text[:200]}...")
                else:
                    print(f"   ⚠️ スキル一覧取得失敗: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ スキル一覧取得エラー: {e}")
        
        # 4. 実際のメッセージ送信テスト
        print(f"\n💬 4. 実際のA2Aメッセージ送信テスト...")
        
        # テストメッセージ
        test_message = {
            "query": "python programming",
            "test": True
        }
        
        async with httpx.AsyncClient() as client:
            # 様々なエンドポイントとメソッドで試行
            test_cases = [
                ("POST", "/search_knowledge", test_message),
                ("POST", "/skills/search_knowledge", test_message), 
                ("POST", "/a2a/search_knowledge", test_message),
                ("POST", "/message", {
                    "skill": "search_knowledge",
                    "data": test_message
                }),
                ("POST", "/", {
                    "action": "search_knowledge",
                    "data": test_message
                })
            ]
            
            for method, endpoint, data in test_cases:
                try:
                    print(f"\n   試行: {method} {endpoint}")
                    
                    response = await client.request(
                        method,
                        f"{server_url}{endpoint}",
                        json=data,
                        timeout=10.0,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    print(f"     応答: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            print(f"     ✅ 成功応答:")
                            print(f"     {json.dumps(result, indent=4, ensure_ascii=False)[:400]}...")
                            
                            # 成功ケースが見つかったら詳細分析
                            if isinstance(result, dict) and result.get("success"):
                                print(f"\n🎉 A2A通信成功！エンドポイント: {endpoint}")
                                return True
                                
                        except json.JSONDecodeError:
                            print(f"     応答テキスト: {response.text[:200]}...")
                    else:
                        print(f"     ステータス: {response.status_code}")
                        if response.text:
                            print(f"     エラー: {response.text[:100]}...")
                        
                except Exception as e:
                    print(f"     ❌ エラー: {type(e).__name__}: {str(e)[:100]}")
        
        # 5. 結果サマリー
        print(f"\n📊 5. A2A通信テスト結果サマリー")
        print("=" * 60)
        print("⚠️ 直接的なA2A通信成功には至りませんでした")
        print("💡 可能な原因:")
        print("   - python-a2aのエンドポイント仕様要確認")
        print("   - A2Aメッセージフォーマット要調整")
        print("   - サーバー側のスキル登録方法要確認")
        print("✅ サーバー起動・HTTP通信は正常動作")
        
        return False
        
    except Exception as e:
        print(f"\n💥 テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メイン実行"""
    print("📡 Knowledge Sage A2A通信テスト開始")
    print("⚠️ 事前にサーバーを起動してください: python run_knowledge_sage_server.py")
    print()
    
    success = await test_a2a_communication()
    
    if success:
        print(f"\n🎉 A2A通信テスト完全成功！")
    else:
        print(f"\n🔧 A2A通信方式の調整が必要")
        print("   サーバー起動は成功、通信プロトコル要調査")

if __name__ == "__main__":
    asyncio.run(main())