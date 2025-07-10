#!/usr/bin/env python3
"""
MCP Client Wrapper for Elders Guild
"""

import json
import subprocess
from pathlib import Path

class MCPClient:
    def __init__(self):
        self.servers = {
            "filesystem": "libs/mcp_wrapper/filesystem_server.py",
            "executor": "libs/mcp_wrapper/executor_server.py"
        }
    
    def call_tool(self, server_name: str, tool_name: str, arguments: dict):
        """Call an MCP tool"""
        if server_name not in self.servers:
            return {"error": f"Unknown server: {server_name}"}
        
        server_path = Path(__file__).parent.parent.parent / self.servers[server_name]
        
        request = {
            "tool": tool_name,
            "arguments": arguments
        }
        
        # Call server
        result = subprocess.run(
            ["python3", str(server_path)],
            input=json.dumps(request),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response", "output": result.stdout}
        else:
            return {"error": result.stderr}

# Example usage
if __name__ == "__main__":
    client = MCPClient()
    
    # Test filesystem server
    result = client.call_tool(
        "filesystem",
        "create_worker",
        {"name": "test", "worker_type": "demo"}
    )
    print("FileSystem result:", result)
    
    # Test executor server
    result = client.call_tool(
        "executor",
        "execute_command",
        {"command": "echo 'Hello from MCP!'", "task_name": "mcp_test"}
    )
    print("Executor result:", result)
