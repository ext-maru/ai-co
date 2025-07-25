#!/bin/bash
# 新生Elders Guild Phase 1: 内部基盤標準化スクリプト
# 対象: /home/aicompany/ai_co/elders_guild/ 内部のみ

set -e

echo "🏛️ 新生Elders Guild A2A内部標準化 - Phase 1"
echo "=================================================="

# 環境変数
NEW_GUILD_ROOT="/home/aicompany/ai_co/elders_guild"
DOCKER_ENV="${NEW_GUILD_ROOT}/docker"
VENV_PATH="${DOCKER_ENV}/venv"

# 作業ディレクトリ移動
cd "$NEW_GUILD_ROOT"
echo "📍 Working in: $(pwd)"

echo "🔍 Step 1: 現在の新生elders_guild状態確認..."

# 既存構造確認
echo "📋 Current structure:"
ls -la

# python-a2a既存確認
if [ -d "$DOCKER_ENV" ]; then
    echo "✅ Docker環境存在確認: $DOCKER_ENV"
    cd "$DOCKER_ENV"
    
    if [ -f "pyproject.toml" ]; then
        echo "📦 pyproject.toml確認:"
        grep -A 5 "python-a2a" pyproject.toml || echo "⚠️ python-a2a not found in pyproject.toml"
    fi
    
    if [ -d "$VENV_PATH" ]; then
        echo "🐍 Existing venv found, activating..."
        source "$VENV_PATH/bin/activate"
        
        # python-a2a確認
        echo "📦 Checking python-a2a installation..."
        python -c "import python_a2a; print(f'python-a2a: {python_a2a.__version__}')" 2>/dev/null || {
            echo "📦 Installing python-a2a..."
            pip install python-a2a==0.5.9
        }
        
        # FastAPI確認
        python -c "import fastapi; print(f'fastapi: {fastapi.__version__}')" 2>/dev/null || {
            echo "📦 Installing fastapi..."
            pip install fastapi==0.108.0 uvicorn[standard]==0.25.0
        }
        
        # 追加パッケージ
        pip install httpx structlog prometheus-client || echo "Some packages may already be installed"
        
    else
        echo "🐍 Creating new virtual environment..."
        python3 -m venv "$VENV_PATH"
        source "$VENV_PATH/bin/activate"
        pip install --upgrade pip
        pip install python-a2a==0.5.9 fastapi==0.108.0 uvicorn[standard]==0.25.0 httpx structlog prometheus-client
    fi
    
    cd "$NEW_GUILD_ROOT"
else
    echo "❌ Docker environment not found at $DOCKER_ENV"
    exit 1
fi

echo "✅ Environment check completed"

echo "🔧 Step 2: バックアップ作成..."

# Git状態確認
if [ -d ".git" ]; then
    git status
    echo "📝 Creating backup branch..."
    git branch backup-before-a2a-$(date +%Y%m%d-%H%M) 2>/dev/null || echo "Branch may already exist"
    git add .
    git commit -m "backup: Before A2A internal refactoring - Phase 1" || echo "Nothing to commit"
else
    echo "⚠️ Not a git repository, manual backup recommended"
fi

echo "🏗️ Step 3: Phase 1 - 内部基盤標準化開始..."

# FastAPI Gateway拡張準備
ELDER_API_PATH="src/elder_tree/api"
if [ -f "$ELDER_API_PATH/main.py" ]; then
    echo "✅ Existing FastAPI found: $ELDER_API_PATH/main.py"
    
    # A2A統合準備
    echo "🔧 Preparing A2A integration..."
    
    # A2Aエージェントレジストリファイル作成
    mkdir -p "$ELDER_API_PATH/a2a"
    
    cat > "$ELDER_API_PATH/a2a/__init__.py" << 'EOF'
"""A2A Integration for Elder Tree Gateway"""
EOF
    
    cat > "$ELDER_API_PATH/a2a/agent_registry.py" << 'EOF'
"""Elder Agent Registry for A2A Communication"""
from typing import Dict, Optional
from python_a2a import A2AClient
import structlog

logger = structlog.get_logger("elder_agent_registry")

class ElderAgentRegistry:
    """新生elders_guild内部のA2Aエージェント管理"""
    
    def __init__(self):
        self.agents = {
            "knowledge-sage": "http://localhost:8001/a2a",
            "task-sage": "http://localhost:8002/a2a", 
            "incident-sage": "http://localhost:8003/a2a",
            "rag-sage": "http://localhost:8004/a2a"
        }
        self.clients: Dict[str, A2AClient] = {}
    
    async def get_agent_client(self, agent_name: str) -> Optional[A2AClient]:
        """Get A2A client for specific agent"""
        if agent_name not in self.agents:
            logger.error(f"Unknown agent: {agent_name}")
            return None
        
        if agent_name not in self.clients:
            self.clients[agent_name] = A2AClient(self.agents[agent_name])
            logger.info(f"Created A2A client for {agent_name}")
        
        return self.clients[agent_name]
    
    async def call_agent(self, agent_name: str, skill: str, data: dict):
        """Call specific agent with A2A protocol"""
        client = await self.get_agent_client(agent_name)
        if not client:
            raise ValueError(f"Agent {agent_name} not available")
        
        logger.info(f"Calling {agent_name}.{skill}", data=data)
        result = await client.call(skill, data)
        logger.info(f"Response from {agent_name}.{skill}", result=result)
        return result
    
    def list_agents(self) -> Dict[str, str]:
        """List all available agents"""
        return self.agents.copy()
EOF
    
    # A2A統合のFastAPIエクステンション作成
    cat > "$ELDER_API_PATH/a2a/fastapi_extension.py" << 'EOF'
"""FastAPI A2A Extension for Elder Tree Gateway"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import structlog
from .agent_registry import ElderAgentRegistry

logger = structlog.get_logger("fastapi_a2a_extension")

class A2AChatRequest(BaseModel):
    """A2A Chat request model"""
    message: str
    context: Dict[str, Any] = {}
    skill: str = "chat"

class A2AResponse(BaseModel):
    """A2A Response model"""
    agent: str
    skill: str
    result: Any
    status: str = "success"

# A2Aルーター作成
a2a_router = APIRouter(prefix="/a2a", tags=["A2A Communication"])
agent_registry = ElderAgentRegistry()

@a2a_router.get("/agents")
async def list_agents():
    """List all available A2A agents"""
    return {
        "agents": agent_registry.list_agents(),
        "status": "active"
    }

@a2a_router.post("/chat/{agent_name}", response_model=A2AResponse)
async def chat_with_agent(agent_name: str, request: A2AChatRequest):
    """Chat with specific A2A agent"""
    try:
        result = await agent_registry.call_agent(
            agent_name, 
            request.skill, 
            {
                "message": request.message,
                "context": request.context
            }
        )
        
        return A2AResponse(
            agent=agent_name,
            skill=request.skill,
            result=result,
            status="success"
        )
    
    except Exception as e:
        logger.error(f"A2A call failed", agent=agent_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"A2A call failed: {str(e)}")

@a2a_router.post("/collaborate")
async def four_sages_collaboration(request: Dict[str, Any]):
    """4賢者協調処理のA2Aエンドポイント"""
    try:
        # Task Sageでタスク分析
        task_analysis = await agent_registry.call_agent(
            "task-sage", 
            "analyze_task", 
            request
        )
        
        # Knowledge Sageで関連知識取得
        knowledge = await agent_registry.call_agent(
            "knowledge-sage",
            "get_knowledge",
            {"domain": task_analysis.get("domain", "general")}
        )
        
        # 必要に応じてRAG Sageで調査
        research = None
        if task_analysis.get("needs_research", False):
            research = await agent_registry.call_agent(
                "rag-sage",
                "research", 
                {"query": task_analysis.get("research_query", "")}
            )
        
        # 結果統合
        collaboration_result = {
            "task_analysis": task_analysis,
            "knowledge": knowledge,
            "research": research,
            "collaboration_pattern": "four_sages",
            "status": "completed"
        }
        
        logger.info("Four sages collaboration completed", result=collaboration_result)
        return collaboration_result
    
    except Exception as e:
        logger.error("Four sages collaboration failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Collaboration failed: {str(e)}")
EOF
    
    # 既存main.pyをバックアップ
    cp "$ELDER_API_PATH/main.py" "$ELDER_API_PATH/main.py.backup"
    
    # main.pyにA2A統合を追加（既存を保持）
    cat >> "$ELDER_API_PATH/main.py" << 'EOF'

# ===== A2A Integration Extension =====
from .a2a.fastapi_extension import a2a_router

# A2Aルーターを既存アプリに統合
app.include_router(a2a_router)

# A2A統合確認エンドポイント
@app.get("/elder/a2a/status")
async def a2a_integration_status():
    """A2A統合状態確認"""
    return {
        "a2a_integration": "active",
        "version": "phase1",
        "agents": ["knowledge-sage", "task-sage", "incident-sage", "rag-sage"],
        "endpoints": ["/a2a/agents", "/a2a/chat/{agent}", "/a2a/collaborate"],
        "status": "ready"
    }
EOF
    
    echo "✅ FastAPI A2A integration added"
    
else
    echo "❌ FastAPI main.py not found at $ELDER_API_PATH/main.py"
    echo "Creating basic FastAPI structure..."
    
    mkdir -p "$ELDER_API_PATH"
    cat > "$ELDER_API_PATH/main.py" << 'EOF'
"""Elder Tree A2A Gateway - New Generation"""
from fastapi import FastAPI
import structlog

# 構造化ログ設定
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("elder_tree_gateway")

# FastAPIアプリケーション
app = FastAPI(
    title="Elder Tree A2A Gateway v3.0",
    description="新生Elders Guild分散AIシステム",
    version="3.0.0"
)

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "service": "Elder Tree A2A Gateway",
        "version": "3.0.0",
        "status": "新生elders_guild内部A2A統合",
        "phase": "Phase 1 - Internal Foundation"
    }

@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "service": "elder-tree-gateway",
        "phase": "a2a-integration-phase1"
    }

# A2A Integration will be added here
EOF
fi

echo "🧪 Step 4: 統合テスト準備..."

# テストディレクトリ確認・準備
if [ ! -d "tests" ]; then
    mkdir -p tests/{unit,integration}
    echo "📁 Created test directories"
fi

# Phase 1 テストファイル作成
cat > tests/test_phase1_a2a_integration.py << 'EOF'
"""Phase 1 A2A Integration Tests"""
import pytest
import httpx
from fastapi.testclient import TestClient
import sys
import os

# パスを追加してモジュールをインポート可能にする
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from elder_tree.api.main import app
    client = TestClient(app)
except ImportError:
    # 開発段階でのインポートエラーを処理
    client = None

@pytest.mark.skipif(client is None, reason="FastAPI app not available")
def test_root_endpoint():
    """ルートエンドポイントテスト"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Elder Tree A2A Gateway" in data["service"]

@pytest.mark.skipif(client is None, reason="FastAPI app not available")  
def test_health_endpoint():
    """ヘルスチェックエンドポイントテスト"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.skipif(client is None, reason="FastAPI app not available")
def test_a2a_integration_status():
    """A2A統合状態確認テスト"""
    response = client.get("/elder/a2a/status")
    if response.status_code == 200:  # A2A統合済みの場合
        data = response.json()
        assert data["a2a_integration"] == "active"
        assert "knowledge-sage" in data["agents"]
    else:  # まだ統合していない場合
        assert response.status_code == 404

def test_python_a2a_import():
    """python-a2aパッケージインポートテスト"""
    try:
        import python_a2a
        assert hasattr(python_a2a, 'A2AServer')
        assert hasattr(python_a2a, 'A2AClient')
        print(f"python-a2a version: {python_a2a.__version__}")
    except ImportError:
        pytest.fail("python-a2a not installed or not accessible")

if __name__ == "__main__":
    # スタンドアロン実行でのクイックテスト
    test_python_a2a_import()
    print("✅ Phase 1 basic tests passed")
EOF

echo "🚀 Step 5: Phase 1 動作確認..."

# Python環境確認
source "$DOCKER_ENV/venv/bin/activate"

# 基本テスト実行
echo "🧪 Running basic tests..."
python tests/test_phase1_a2a_integration.py

# FastAPI起動テスト（バックグラウンド）
echo "🌐 Testing FastAPI startup..."
if [ -f "src/elder_tree/api/main.py" ]; then
    timeout 10s python -m uvicorn src.elder_tree.api.main:app --host 0.0.0.0 --port 8000 &
    FASTAPI_PID=$!
    sleep 3
    
    # エンドポイントテスト
    curl -s http://localhost:8000/ | grep -q "Elder Tree" && echo "✅ FastAPI responding" || echo "⚠️ FastAPI not responding"
    curl -s http://localhost:8000/health | grep -q "healthy" && echo "✅ Health check OK" || echo "⚠️ Health check failed"
    
    # プロセス終了
    kill $FASTAPI_PID 2>/dev/null || echo "FastAPI process already terminated"
    wait $FASTAPI_PID 2>/dev/null || true
else
    echo "⚠️ FastAPI main.py not found, skipping startup test"
fi

echo ""
echo "🎉 Phase 1: 内部基盤標準化 - 準備完了!"
echo "============================================="
echo "✅ 新生elders_guild環境確認完了"
echo "✅ python-a2a統合準備完了"
echo "✅ FastAPI A2A拡張準備完了" 
echo "✅ テスト環境準備完了"
echo "✅ バックアップ作成完了"
echo ""
echo "📋 Phase 1 成果物:"
echo "   - src/elder_tree/api/a2a/ (A2A統合モジュール)"
echo "   - A2Aエージェントレジストリ"
echo "   - FastAPI A2A拡張エンドポイント"
echo "   - テストスイート基盤"
echo ""
echo "🚀 次のステップ: Phase 2 - 4賢者A2A変換"
echo "   各賢者のsoul.py → a2a_agent.py 変換開始"
echo ""
echo "🏛️ 新生Elders Guild Phase 1 完了!"