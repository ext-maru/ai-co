#!/usr/bin/env python3
"""
Simplified Command Executor MCP Server
"""

import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper
from libs.mcp_wrapper import MCPServer


class ExecutorMCPServer:
    def __init__(self):
        self.server = MCPServer("executor")
        self.helper = AICommandHelper()
        self.setup_tools()

    def setup_tools(self):
        @self.server.tool()
        async def execute_command(command: str, task_name: str = None):
            if not task_name:
                task_name = f"mcp_cmd_{int(asyncio.get_event_loop().time())}"

            # Use AI Command Helper
            command_id = self.helper.create_bash_command(command, task_name)

            return {
                "status": "scheduled",
                "task_name": task_name,
                "command_id": command_id,
                "message": "Command scheduled for execution",
            }

        @self.server.tool()
        async def check_result(task_name: str):
            result = self.helper.check_results(task_name)
            return result if result else {"status": "not_found"}

    async def process_request(self, request_json):
        request = json.loads(request_json)
        return await self.server.handle_request(request)


if __name__ == "__main__":
    import asyncio

    server = ExecutorMCPServer()
    request = input()
    result = asyncio.run(server.process_request(request))
    print(json.dumps(result))
