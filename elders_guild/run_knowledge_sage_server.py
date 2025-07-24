#!/usr/bin/env python3
"""
🚀 Knowledge Sage A2A Server - 実際のサーバー起動
python-a2a標準のrun_serverで起動
"""

import asyncio
import logging
from python_a2a import run_server
from knowledge_sage.a2a_agent import KnowledgeSageAgent

def main():
    """Knowledge Sage A2A Server起動"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🏛️ Knowledge Sage A2A Server Starting...")
    
    # エージェント作成
    agent = KnowledgeSageAgent(host="localhost", port=8807)
    
    # 初期化
    async def init_agent():
        return await agent.initialize()
    
    init_result = asyncio.run(init_agent())
    if not init_result:
        print("❌ Agent initialization failed")
        return
    
    print(f"✅ Agent initialized: {agent.agent_name}")
    print(f"🌐 Starting Flask server on port 8807.0..")
    
    try:
        # python-a2a標準のrun_serverでサーバー起動
        run_server(agent, host="localhost", port=8807, debug=False)
        
    except KeyboardInterrupt:
        print("\n🛑 Server shutdown requested")
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("✅ Knowledge Sage A2A Server stopped")

if __name__ == "__main__":
    main()