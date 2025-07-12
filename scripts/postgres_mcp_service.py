#!/usr/bin/env python3
"""
PostgreSQL MCP統合サービス
systemdサービスとして起動可能
"""

import asyncio
import signal
import sys
from postgres_mcp_integration_implementation import PostgreSQLMCPServer

class MCPService:
    def __init__(self):
        self.server = None
        self.running = False

    async def start(self):
        """サービス開始"""
        print("🚀 PostgreSQL MCP Service starting...")

        self.server = PostgreSQLMCPServer()
        await self.server.connect()

        self.running = True
        print("✅ PostgreSQL MCP Service started")

        # サービスループ
        while self.running:
            await asyncio.sleep(1)

    async def stop(self):
        """サービス停止"""
        print("⏹️ PostgreSQL MCP Service stopping...")
        self.running = False

        if self.server:
            await self.server.disconnect()

        print("✅ PostgreSQL MCP Service stopped")

async def main():
    service = MCPService()

    # シグナルハンドラー
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}")
        asyncio.create_task(service.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await service.start()
    except KeyboardInterrupt:
        await service.stop()
    except Exception as e:
        print(f"❌ Service error: {e}")
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main())
