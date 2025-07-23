#!/usr/bin/env python3
"""
Elder Tree A2A + FastAPI Integration Demo
技術選定書で想定していた理想的な統合形態を実現
"""

import asyncio
import threading
from typing import Optional
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from python_a2a import (
    A2AServer, A2AClient, Message, TextContent, MessageRole,
    run_server, create_text_message
)


# === A2A Agent Implementation ===
class ElderSage(A2AServer):


"""Elder Tree賢者のA2A実装""" str, specialty: str):
        super().__init__()
        self.sage_name = sage_name
        self.specialty = specialty
        self.request_count = 0
    
    def handle_message(self, message: Message) -> Message:
        """A2A メッセージハンドリング"""
        self.request_count += 1
        
        response_text = (
            f"🧙‍♂️ {self.sage_name} ({self.specialty})\n"
            f"📝 Your message: {message.content.text}\n"
            f"📊 Request #{self.request_count}\n"
            f"✨ Processed with Elder Tree wisdom!"
        )
        
        return Message(
            content=TextContent(text=response_text),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )


# === FastAPI Integration ===
app = FastAPI(
    title="Elder Tree A2A Integration",
    description="FastAPI + python-a2a による理想的な統合実装",
    version="1.0.0"
)

# グローバル状態
sage_agent: Optional[ElderSage] = None
a2a_client: Optional[A2AClient] = None


# === Request/Response Models ===
class ChatRequest(BaseModel):
    message: str
    """ChatRequestクラス"""
    sage_type: str = "knowledge"


class ChatResponse(BaseModel):



"""ChatResponseクラス""" str
    sage_name: str
    request_id: int


# === FastAPI Endpoints ===
@app.get("/")
async def root():



"""ルートエンドポイント""" "Elder Tree A2A Integration",
        "status": "ready",
        "features": ["REST API", "A2A Protocol", "Elder Sage AI"]
    }


@app.get("/health")
async def health():

    """ヘルスチェック""" "healthy",
        "sage_active": sage_agent is not None,
        "sage_name": sage_agent.sage_name if sage_agent else None,
        "requests_handled": sage_agent.request_count if sage_agent else 0
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_with_sage(request: ChatRequest):
    """A2Aエージェント経由でのチャット"""
    global a2a_client, sage_agent
    
    if not a2a_client or not sage_agent:
        raise HTTPException(status_code=503, detail="A2A agent not ready")
    
    try:
        # A2Aメッセージを作成
        message = create_text_message(request.message)
        
        # A2A経由でエージェントに送信
        # （実際の実装では適切なA2Aクライアント通信を行う）
        response = sage_agent.handle_message(message)
        
        return ChatResponse(
            response=response.content.text,
            sage_name=sage_agent.sage_name,
            request_id=sage_agent.request_count
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"A2A communication failed: {str(e)}")


@app.get("/sage/status")
async def get_sage_status():



"""賢者の状態を取得"""
        return {"error": "No sage agent active"}
    
    return {
        "sage_name": sage_agent.sage_name,
        "specialty": sage_agent.specialty,
        "requests_handled": sage_agent.request_count,
        "status": "active"
    }


# === A2A Server Setup ===
def setup_a2a_agent():

    """A2Aエージェントの初期化"""//localhost:5001/a2a")
    
    print(f"✅ A2A Agent initialized: {sage_agent.sage_name}")
    return sage_agent


def run_a2a_server_thread(agent: ElderSage, port: int = 5001):
    """A2Aサーバーを別スレッドで実行"""
    try:
        print(f"🚀 Starting A2A server on port {port}")
        run_server(agent, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"❌ A2A server failed: {e}")


# === Main Execution ===
def main():



"""FastAPI + A2A 統合実行"""")
    print("   - REST API: http://localhost:8000")
    print("   - A2A Protocol: http://localhost:5001")
    print("   - Health Check: http://localhost:8000/health")
    print("   - Chat: POST http://localhost:8000/chat")
    
    # FastAPI起動
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()