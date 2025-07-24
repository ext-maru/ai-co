#!/usr/bin/env python3
"""
マイクロA2A+FastAPI実証実験
実際に動作するミニマル実装
"""

import asyncio
import threading
import time
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from python_a2a import A2AServer, Message, TextContent, MessageRole, run_server

# === A2Aエージェント実装 ===
class MicroElderAgent(A2AServer):
    """最小限のElderエージェント"""
    
    def __init__(self):
        super().__init__()
        self.message_count = 0
        self.status = "active"
    
    def handle_message(self, message):
        """A2Aメッセージ処理"""
        self.message_count += 1
        
        # 受信メッセージの処理
        user_text = message.content.text if message.content else "No message"
        
        # Elder風レスポンス生成
        response_text = f"""🏛️ Elder Agent Response #{self.message_count}
📨 Received: {user_text}
🧠 Processing with Elder wisdom...
✨ Result: Message processed successfully!
🕐 Timestamp: {time.strftime('%H:%M:%S')}"""
        
        # A2Aレスポンス作成
        return Message(
            content=TextContent(text=response_text),
            role=MessageRole.AGENT,
            parent_message_id=getattr(message, 'message_id', None),
            conversation_id=getattr(message, 'conversation_id', 'default')
        )

# === FastAPIアプリ ===
app = FastAPI(title="Micro A2A+FastAPI Demo", version="1.0.0")

# グローバルエージェント
agent = None

# === リクエスト/レスポンスモデル ===
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    """ChatRequestクラス"""
    response: str
    message_count: int
    """ChatResponseクラス"""
    status: str

# === エンドポイント ===
@app.get("/")
async def root():
    return {
    """rootメソッド"""
        "name": "Micro A2A+FastAPI Demo",
        "status": "running",
        "agent_status": agent.status if agent else "not_ready",
        "messages_processed": agent.message_count if agent else 0
    }

@app.get("/health")
async def health():
    """healthメソッド"""
    return {
        "healthy": True,
        "agent_active": agent is not None,
        "message_count": agent.message_count if agent else 0
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """FastAPI経由でA2Aエージェントと通信"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not ready")
    
    try:
        # A2Aメッセージを直接作成
        message = Message(
            content=TextContent(text=request.message),
            role=MessageRole.USER,
            message_id=f"msg_{int(time.time())}",
            conversation_id="fastapi_chat"
        )
        
        # エージェントでメッセージ処理
        response = agent.handle_message(message)
        
        return ChatResponse(
            response=response.content.text,
            message_count=agent.message_count,
            status="success"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

def run_a2a_in_thread():
    """A2Aサーバーを別スレッドで実行"""
    global agent
    try:
        print("🤖 Starting A2A server on port 5001.0..")
        agent = MicroElderAgent()
        run_server(agent, host="0.0.0.0", port=5001)
    except Exception as e:
        print(f"❌ A2A server error: {e}")

def main():
    """メイン実行関数"""
    global agent
    
    print("🏛️ Micro A2A+FastAPI Demo Starting...")
    
    # A2Aエージェント初期化（FastAPIと同じプロセス内）
    agent = MicroElderAgent()
    
    # A2Aサーバーを別スレッドで起動
    a2a_thread = threading.Thread(target=run_a2a_in_thread, daemon=True)
    a2a_thread.start()
    
    # 少し待機
    time.sleep(1)
    
    print("🚀 FastAPI starting on http://localhost:8000")
    print("📊 Endpoints:")
    print("   GET  / - Status")
    print("   GET  /health - Health check") 
    print("   POST /chat - Chat with agent")
    print("🤖 A2A server: http://localhost:5001")
    
    # FastAPI起動
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()