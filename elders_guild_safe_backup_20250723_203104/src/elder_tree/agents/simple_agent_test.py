#!/usr/bin/env python3
"""
Simple test to understand python-a2a A2AServer pattern
"""

from python_a2a import A2AServer, Message
from flask import Flask, jsonify, request
import asyncio
import os

class SimpleTestAgent(A2AServer):


"""シンプルなテストエージェント"""
        super().__init__(name="simple_test", description="Simple test agent")
        self.port = port
        
    async def handle_message(self, message: Message):
        """メッセージハンドラー"""
        print(f"Received message: {message}")
        
        # Messageオブジェクトの内容を辞書として扱う
        if hasattr(message, 'content'):
            content = message.content
            if isinstance(content, dict):
                return {"status": "ok", "echo": content}
        
        return {"status": "ok", "echo": str(message)}
    
    def create_app(self):

    
    """Flask appを作成"""
            return jsonify({"status": "healthy", "agent": "simple_test"})
        
        # メッセージ受信エンドポイント
        @app.route('/message', methods=['POST'])
        async def receive_message():

        
        """receive_messageメソッド"""
    """メイン実行"""
    port = int(os.getenv("PORT", 5000))
    agent = SimpleTestAgent(port=port)
    app = agent.create_app()
    
    print(f"Starting simple test agent on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    main()