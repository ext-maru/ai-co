#!/usr/bin/env python3
"""
Elder Tree A2A + FastAPI クライアント側デモ
"""

import requests
import json
import time
from python_a2a import A2AClient, create_text_message

def test_rest_api():


"""FastAPI REST APIのテスト"""//localhost:8000/health")
    print(f"Health Check: {response.json()}")
    
    # チャット（A2A経由）
    chat_request = {
        "message": "Hello from Elder Tree client!",
        "sage_type": "knowledge"
    }
    
    response = requests.post(
        "http://localhost:8000/chat",
        json=chat_request
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"📝 Chat Response: {result['response']}")
        print(f"🧙‍♂️ Sage: {result['sage_name']}")
    else:
        print(f"❌ Error: {response.status_code}")

def test_a2a_direct():


"""A2A直接通信のテスト"""
        # A2Aクライアント作成
        client = A2AClient("http://localhost:5001/a2a")
        
        # メッセージ送信
        message = create_text_message("Direct A2A communication test")
        response = client.send_message(message)
        
        print(f"📨 A2A Response: {response.content.text}")
    
    except Exception as e:
        print(f"❌ A2A Direct failed: {e}")

if __name__ == "__main__":
    print("🏛️ Elder Tree A2A Client Demo")
    print("=" * 50)
    
    # REST API テスト
    test_rest_api()
    
    print("\n" + "=" * 50)
    
    # A2A直接通信テスト
    test_a2a_direct()