#!/usr/bin/env python3
"""
実証実験用テストクライアント
実際のHTTP通信でテスト
"""

import requests
import json
import time
import sys

def test_server_health():
    pass


"""サーバーのヘルスチェック"""
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server healthy: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_server_status():
    pass

        """サーバー状態確認"""
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Server status: {json.dumps(data, indent}")
            return True
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status request failed: {e}")
        return False

def test_chat_functionality():
    pass

        """チャット機能のテスト"""
        print(f"\n📤 Test {i}: Sending '{message}'")
        try:
            response = requests.post(
                "http://localhost:8000/chat",
                json={"message": message},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"📥 Response:")
                print(f"   Status: {data['status']}")
                print(f"   Message count: {data['message_count']}")
                print(f"   Content: {data['response'][:100]}...")
            else:
                print(f"❌ Chat failed: {response.status_code} - {response.text}")
        
        except Exception as e:
            print(f"❌ Chat request failed: {e}")
        
        time.sleep(1)  # 1秒待機

def run_comprehensive_test():
    pass

        
        """包括的なテスト実行""" サーバー接続テスト
    if not test_server_health():
        print("❌ Server not accessible. Make sure micro_a2a_server.py is running.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # Step 2: 状態確認
    if not test_server_status():
        print("❌ Server status check failed.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # Step 3: チャット機能テスト
    test_chat_functionality()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    run_comprehensive_test()