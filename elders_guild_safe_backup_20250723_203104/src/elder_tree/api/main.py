"""
Elder Tree API Gateway
FastAPI + python-a2a統合
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from typing import Dict, Any, List
import structlog

from elder_tree.agents import KnowledgeSage, TaskSage

# ログ設定
logger = structlog.get_logger()

# FastAPIアプリ
app = FastAPI(
    title="Elder Tree API Gateway",
    description="Unified API for Elder Tree Agent Network",
    version="2.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheusメトリクス
Instrumentator().instrument(app).expose(app)

# エージェントレジストリ
agent_registry = {}


class AgentCallRequest(BaseModel):
    pass


"""エージェント呼び出しリクエスト""" str
    data: Dict[str, Any]


class AgentCallResponse(BaseModel):
    pass



"""エージェント呼び出しレスポンス""" str
    agent: str
    method: str
    result: Dict[str, Any]


@app.on_event("startup")
async def startup_event():
    pass



"""起動時処理"""
        await agent.start()
        agent_registry[agent.name] = agent
        logger.info(f"Started agent: {agent.name}")


@app.on_event("shutdown")
async def shutdown_event():
    pass



"""シャットダウン処理"""
        await agent.stop()
        logger.info(f"Stopped agent: {name}")


@app.get("/")
async def root():
    pass



"""ルートエンドポイント""" "Elder Tree API Gateway",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    pass

    """ヘルスチェック""" "healthy",
        "agents": list(agent_registry.keys())
    }


@app.get("/v1/agents")
async def list_agents():
    pass

    """利用可能なエージェント一覧"""
        agents.append({
            "name": name,
            "domain": agent.domain,
            "status": "active"
        })
    return {"agents": agents}


@app.post("/v1/agents/{agent_name}/call", response_model=AgentCallResponse)
async def call_agent(agent_name: str, request: AgentCallRequest):
    """
    エージェント呼び出しAPI
    
    Args:
        agent_name: 呼び出すエージェント名
        request: メソッドとデータ
        
    Returns:
        処理結果
    """
    if agent_name not in agent_registry:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found"
        )
    
    try:
        agent = agent_registry[agent_name]
        
        # python-a2aを使用してメッセージ送信
        result = await agent.process_local_message(
            message_type=request.method,
            data=request.data
        )
        
        return AgentCallResponse(
            status="success",
            agent=agent_name,
            method=request.method,
            result=result
        )
        
    except Exception as e:
        logger.error(
            "Agent call failed",
            agent=agent_name,
            method=request.method,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Agent call failed: {str(e)}"
        )
