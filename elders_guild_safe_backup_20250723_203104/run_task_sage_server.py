#!/usr/bin/env python3
"""
📋 Task Sage A2A Server - 実際のサーバー起動
python-a2a標準のrun_serverで起動

Knowledge Sageパターンを適用したTask Sage専用サーバー
"""

import asyncio
import logging
from python_a2a import run_server
from task_sage.a2a_agent import TaskSageAgent

def main():


"""Task Sage A2A Server起動"""
        return await agent.initialize()
    
    init_result = asyncio.run(init_agent())
    if not init_result:
        print("❌ Agent initialization failed")
        return
    
    print(f"✅ Agent initialized: {agent.agent_name}")
    print(f"🌐 Starting Flask server on port 8808...")
    
    try:
        # python-a2a標準のrun_serverでサーバー起動
        run_server(agent, host="localhost", port=8808, debug=False)
        
    except KeyboardInterrupt:
        print("\n🛑 Server shutdown requested")
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("✅ Task Sage A2A Server stopped")

if __name__ == "__main__":
    main()