"""
Elders Guild MCP Wrapper
MCP風のインターフェースを提供
"""

class MCPServer:
    def __init__(self, name):
        self.name = name
        self.tools = {}
    
    def tool(self, name=None):
        def decorator(func):
            tool_name = name or func.__name__
            self.tools[tool_name] = func
            return func
        return decorator
    
    async def handle_request(self, request):
        tool_name = request.get("tool")
        args = request.get("arguments", {})
        
        if tool_name in self.tools:
            result = await self.tools[tool_name](**args)
            return {"status": "success", "result": result}
        else:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}
