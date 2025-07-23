#!/usr/bin/env python3
"""Test simple A2A Server startup"""

from flask import Flask
from python_a2a import A2AServer, Message
import asyncio

class TestAgent(A2AServer):
    def __init__(self):
        super().__init__(name="test_agent", description="Test agent")
    
    async def handle_message(self, message: Message):
        print(f"Received message: {message}")
        return {"status": "ok", "echo": str(message)}

# Flask app
app = Flask(__name__)

# Create agent
agent = TestAgent()

# Setup routes
agent.setup_routes(app)

if __name__ == "__main__":
    print("Starting test agent on port 5000...")
    app.run(host="0.0.0.0", port=5000)