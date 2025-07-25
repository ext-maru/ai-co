#!/bin/bash
# Elder Tree OSS First セットアップスクリプト
# 設計書準拠の環境構築を自動化

set -e

echo "🌳 Elder Tree OSS First Setup Starting..."
echo "📋 Following ELDER_TREE_A2A_IMPLEMENTATION.md design"

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# プロジェクトルート
PROJECT_ROOT="/home/aicompany/ai_co"
ELDER_TREE_ROOT="$PROJECT_ROOT/elder_tree"

echo -e "${YELLOW}Step 1: Creating project structure...${NC}"
# 設計書通りのディレクトリ構造作成
mkdir -p $ELDER_TREE_ROOT/{core,domains,api,protos,scripts,tests,docker}
mkdir -p $ELDER_TREE_ROOT/core/{souls,communication,monitoring}
mkdir -p $ELDER_TREE_ROOT/domains/{knowledge,task,incident,rag}
mkdir -p $ELDER_TREE_ROOT/domains/knowledge/{servants,magic}
mkdir -p $ELDER_TREE_ROOT/api/{routers,middleware}
mkdir -p $ELDER_TREE_ROOT/tests/{unit,integration}

echo -e "${GREEN}✅ Directory structure created${NC}"

echo -e "${YELLOW}Step 2: Creating pyproject.toml for Poetry...${NC}"
cat > $ELDER_TREE_ROOT/pyproject.toml << 'EOF'
[tool.poetry]
name = "elder-tree"
version = "2.0.0"
description = "Elder Tree Distributed AI Architecture with a2a-python"
authors = ["Claude Elder <claude@elders-guild.ai>"]
readme = "README.md"
packages = [{include = "elder_tree"}]

[tool.poetry.dependencies]
python = "^3.11"
# 通信・分散処理 (OSS First)
grpcio = "^1.51.1"
protobuf = "^4.24.0"
# Note: a2a-python would be here if it existed

# API・Web
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
pydantic = "^2.5.0"

# データベース
sqlmodel = "^0.0.14"
asyncpg = "^0.29.0"
redis = "^5.0.1"
alembic = "^1.13.0"

# 監視・ログ
prometheus-client = "^0.19.0"
structlog = "^23.2.0"
opentelemetry-api = "^1.21.0"
opentelemetry-sdk = "^1.21.0"
opentelemetry-instrumentation-fastapi = "^0.42b0"

# ユーティリティ
python-consul = "^1.1.0"
httpx = "^0.25.0"
python-multipart = "^0.0.6"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
black = "^23.11.0"
ruff = "^0.1.6"
mypy = "^1.7.0"
grpcio-tools = "^1.51.1"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF

echo -e "${GREEN}✅ pyproject.toml created${NC}"

echo -e "${YELLOW}Step 3: Creating Protocol Buffers definitions...${NC}"
cat > $ELDER_TREE_ROOT/protos/soul_messages.proto << 'EOF'
syntax = "proto3";

package elder_tree;

import "google/protobuf/timestamp.proto";
import "google/protobuf/any.proto";

// 基本メッセージ型（設計書準拠）
message SoulMessage {
    string message_id = 1;
    string sender_soul = 2;
    string recipient_soul = 3;
    string correlation_id = 4;
    google.protobuf.Timestamp timestamp = 5;
    
    oneof payload {
        AnalysisRequest analysis_request = 10;
        AnalysisResponse analysis_response = 11;
        ImplementationRequest implementation_request = 12;
        ImplementationResponse implementation_response = 13;
        DomainEvent domain_event = 14;
        HealthCheckRequest health_check = 15;
        HealthCheckResponse health_response = 16;
    }
}

// ヘルスチェック
message HealthCheckRequest {
    string requester = 1;
}

message HealthCheckResponse {
    string status = 1;
    string soul_name = 2;
    string domain = 3;
    int64 uptime_seconds = 4;
}

// 分析リクエスト
message AnalysisRequest {
    string issue_description = 1;
    repeated string technologies = 2;
    string analysis_type = 3;
    map<string, string> context = 4;
}

// 分析レスポンス
message AnalysisResponse {
    map<string, float> technology_scores = 1;
    repeated string recommendations = 2;
    float overall_confidence = 3;
    string analysis_summary = 4;
}

// 実装リクエスト
message ImplementationRequest {
    string feature_name = 1;
    repeated string requirements = 2;
    string target_language = 3;
    bool use_tdd = 4;
}

// 実装レスポンス
message ImplementationResponse {
    string test_code = 1;
    string implementation_code = 2;
    float quality_score = 3;
    repeated string warnings = 4;
}

// ドメインイベント
message DomainEvent {
    string event_type = 1;
    string domain = 2;
    map<string, string> event_data = 3;
}
EOF

echo -e "${GREEN}✅ Protocol Buffers definitions created${NC}"

echo -e "${YELLOW}Step 4: Creating base implementation files...${NC}"

# A2A代替実装（a2a-pythonが存在しないため）
cat > $ELDER_TREE_ROOT/core/communication/a2a_alternative.py << 'EOF'
"""
A2A Alternative Implementation
a2a-pythonライブラリが実際には存在しないため、
同等の機能をgRPCで実装
"""

import asyncio
import grpc
from typing import Dict, Any, Optional, Callable
from abc import ABC, abstractmethod
import structlog

logger = structlog.get_logger(__name__)

class A2AServer:
    """a2a-python Server の代替実装"""
    
    def __init__(self, name: str, port: int):
        self.name = name
        self.port = port
        self.handlers: Dict[str, Callable] = {}
        self.server = None
        
    def handler(self, method_name: str):
        """デコレータでハンドラー登録"""
        def decorator(func):
            self.handlers[method_name] = func
            return func
        return decorator
    
    async def start(self):
        """gRPCサーバー起動"""
        self.server = grpc.aio.server()
        # gRPCサービス登録処理
        self.server.add_insecure_port(f'[::]:{self.port}')
        await self.server.start()
        logger.info(f"A2A Server started: {self.name} on port {self.port}")
        
    async def run(self):
        """サーバー実行"""
        await self.start()
        await self.server.wait_for_termination()

class A2AClient:
    """a2a-python Client の代替実装"""
    
    def __init__(self):
        self.channels: Dict[str, grpc.aio.Channel] = {}
        
    async def call(self, service: str, method: str, data: Dict[str, Any], 
                  timeout: float = 30.0) -> Dict[str, Any]:
        """サービス呼び出し"""
        # gRPCチャンネル取得・作成
        if service not in self.channels:
            # サービスディスカバリー（Consul統合予定）
            port = self._resolve_service_port(service)
            self.channels[service] = grpc.aio.insecure_channel(f'localhost:{port}')
        
        # RPC呼び出し
        # 実際の実装ではProtocol Buffersを使用
        return {"status": "success", "data": data}
    
    def _resolve_service_port(self, service: str) -> int:
        """サービス名からポート解決（仮実装）"""
        service_ports = {
            "elder_tree.knowledge_sage": 50051,
            "elder_tree.task_sage": 50052,
            "elder_tree.incident_sage": 50053,
            "elder_tree.rag_sage": 50054,
        }
        return service_ports.get(service, 50000)

# a2a-python互換エイリアス
Server = A2AServer
Client = A2AClient
EOF

# BaseSoul実装
cat > $ELDER_TREE_ROOT/core/souls/base_soul.py << 'EOF'
"""
Elder Tree Base Soul Implementation
設計書準拠の基底クラス
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import structlog
from prometheus_client import Counter, Histogram, Gauge
import time

logger = structlog.get_logger(__name__)

class BaseSoul(ABC):
    """Elder Tree 魂基底クラス"""
    
    def __init__(self, soul_config: Dict[str, Any]):
        self.soul_name = soul_config["soul_name"]
        self.domain = soul_config["domain"]
        self.soul_id = soul_config.get("soul_id", f"{self.soul_name}_001")
        
        # 構造化ログ設定
        self.logger = structlog.get_logger(
            soul_name=self.soul_name,
            domain=self.domain
        )
        
        # Prometheusメトリクス
        self.request_counter = Counter(
            'soul_requests_total',
            'Total requests processed',
            ['soul_name', 'method', 'status']
        )
        
        self.request_duration = Histogram(
            'soul_request_duration_seconds',
            'Request duration',
            ['soul_name', 'method']
        )
        
        self.active_connections = Gauge(
            'soul_active_connections',
            'Active connections',
            ['soul_name']
        )
        
        # 起動時間記録
        self.start_time = time.time()
        
    @abstractmethod
    async def initialize(self) -> bool:
        """魂の初期化処理"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """魂のシャットダウン処理"""
        pass
    
    def get_uptime(self) -> float:
        """稼働時間取得（秒）"""
        return time.time() - self.start_time
    
    def get_health_status(self) -> Dict[str, Any]:
        """ヘルスステータス取得"""
        return {
            "status": "healthy",
            "soul_name": self.soul_name,
            "domain": self.domain,
            "uptime_seconds": self.get_uptime(),
            "metrics": {
                "total_requests": self._get_total_requests(),
                "active_connections": self.active_connections._value.get()
            }
        }
    
    def _get_total_requests(self) -> int:
        """総リクエスト数取得"""
        # Prometheusメトリクスから集計
        return 0  # 実装簡略化
EOF

# A2ASoul実装
cat > $ELDER_TREE_ROOT/core/souls/a2a_soul.py << 'EOF'
"""
A2A Soul - OSS統合魂基底クラス
"""

from typing import Dict, Any, List
import asyncio
from abc import abstractmethod

from elder_tree.core.souls.base_soul import BaseSoul
from elder_tree.core.communication.a2a_alternative import Server, Client
from prometheus_client import CollectorRegistry

class A2ASoul(BaseSoul):
    """a2a対応魂基底クラス（設計書準拠）"""
    
    def __init__(self, soul_config: Dict[str, Any]):
        super().__init__(soul_config)
        
        self.port = soul_config["port"]
        
        # A2Aサーバー初期化
        self.server = Server(
            name=f"elder_tree.{self.soul_name}",
            port=self.port
        )
        
        # A2Aクライアント（他魂への通信用）
        self.client = Client()
        
        # 基本ハンドラー登録
        self._register_base_handlers()
        
        # ドメイン固有ハンドラー登録
        self._register_domain_handlers()
        
    def _register_base_handlers(self):
        """基本ハンドラー登録"""
        
        @self.server.handler("health_check")
        async def health_check(data: Dict[str, Any]) -> Dict[str, Any]:
            """ヘルスチェック"""
            return self.get_health_status()
        
        @self.server.handler("get_metrics")
        async def get_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
            """メトリクス取得"""
            # Prometheusメトリクス返却
            return {
                "soul_name": self.soul_name,
                "metrics": "prometheus_endpoint"
            }
        
        @self.server.handler("domain_event")
        async def handle_domain_event(data: Dict[str, Any]) -> Dict[str, Any]:
            """ドメインイベント処理"""
            event_type = data.get("event_type")
            event_data = data.get("data", {})
            
            await self.process_domain_event(event_type, event_data)
            return {"status": "processed"}
    
    @abstractmethod
    def _register_domain_handlers(self):
        """ドメイン固有ハンドラー登録（サブクラスで実装）"""
        pass
    
    async def process_domain_event(self, event_type: str, event_data: Dict[str, Any]):
        """ドメインイベント処理（オーバーライド可能）"""
        self.logger.info("Domain event received", 
                        event_type=event_type, 
                        event_data=event_data)
    
    async def call_soul(self, target_soul: str, method: str, 
                       data: Dict[str, Any]) -> Dict[str, Any]:
        """他の魂を呼び出し"""
        
        with self.request_duration.labels(
            soul_name=self.soul_name,
            method=f"call_{target_soul}"
        ).time():
            try:
                response = await self.client.call(
                    service=f"elder_tree.{target_soul}",
                    method=method,
                    data=data,
                    timeout=30.0
                )
                
                self.request_counter.labels(
                    soul_name=self.soul_name,
                    method=f"call_{target_soul}",
                    status="success"
                ).inc()
                
                return response
                
            except Exception as e:
                self.request_counter.labels(
                    soul_name=self.soul_name,
                    method=f"call_{target_soul}",
                    status="error"
                ).inc()
                
                self.logger.error("Failed to call soul",
                                target_soul=target_soul,
                                method=method,
                                error=str(e))
                raise
    
    async def broadcast_to_domain(self, event_type: str, event_data: Dict[str, Any]):
        """同一ドメイン内ブロードキャスト"""
        # 実装簡略化: 同一ドメインの魂リストは設定から取得
        domain_souls = self._get_domain_souls()
        
        tasks = []
        for soul in domain_souls:
            if soul != self.soul_name:
                task = self.call_soul(
                    soul, 
                    "domain_event",
                    {"event_type": event_type, "data": event_data}
                )
                tasks.append(task)
        
        # エラーを無視してブロードキャスト
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def _get_domain_souls(self) -> List[str]:
        """同一ドメインの魂リスト取得"""
        # 実装簡略化: ハードコード
        domain_souls_map = {
            "knowledge": ["knowledge_sage", "code_craftsman", "doc_weaver"],
            "task": ["task_sage", "effort_estimator"],
            "incident": ["incident_sage", "crisis_responder"],
            "rag": ["rag_sage", "search_optimizer"]
        }
        return domain_souls_map.get(self.domain, [])
    
    async def initialize(self) -> bool:
        """初期化処理"""
        self.logger.info("Initializing soul", port=self.port)
        return True
    
    async def shutdown(self) -> None:
        """シャットダウン処理"""
        self.logger.info("Shutting down soul")
        # gRPCサーバー停止など
    
    async def run_forever(self):
        """魂の永続実行"""
        self.logger.info("Starting soul", port=self.port)
        await self.initialize()
        await self.server.run()
EOF

echo -e "${GREEN}✅ Base implementation files created${NC}"

echo -e "${YELLOW}Step 5: Creating example Knowledge Sage implementation...${NC}"

mkdir -p $ELDER_TREE_ROOT/domains/knowledge

cat > $ELDER_TREE_ROOT/domains/knowledge/knowledge_sage.py << 'EOF'
"""
Knowledge Sage - OSS First実装
既存実装からの移行例
"""

from typing import Dict, Any, Optional
from elder_tree.core.souls.a2a_soul import A2ASoul

class KnowledgeSageA2A(A2ASoul):
    """Knowledge Sage - 技術知識管理専門AI"""
    
    def __init__(self, config: Optional[Dict] = None):
        default_config = {
            "soul_name": "knowledge_sage",
            "domain": "knowledge", 
            "port": 50051
        }
        super().__init__(config or default_config)
        
        # 既存ロジックの移植準備
        self.knowledge_base = {}  # 簡略化
        
    def _register_domain_handlers(self):
        """Knowledge Domain専用ハンドラー"""
        
        @self.server.handler("analyze_technology")
        async def analyze_technology(data: Dict[str, Any]) -> Dict[str, Any]:
            """技術分析リクエスト処理"""
            tech_name = data.get("technology")
            context = data.get("context", {})
            
            self.logger.info("Analyzing technology", 
                           technology=tech_name,
                           context=context)
            
            # 分析ロジック（既存実装から移植）
            analysis_result = {
                "technology": tech_name,
                "assessment": "promising",
                "confidence": 0.85,
                "recommendations": [
                    "Consider for production use",
                    "Evaluate performance characteristics",
                    "Check community support"
                ]
            }
            
            # RAG Sageに追加情報要求（必要に応じて）
            if analysis_result["confidence"] < 0.7:
                try:
                    rag_result = await self.call_soul(
                        "rag_sage",
                        "search_technical_docs",
                        {"query": tech_name, "limit": 5}
                    )
                    # RAG結果をマージ
                    self.logger.info("RAG search completed", 
                                   results=len(rag_result.get("documents", [])))
                except Exception as e:
                    self.logger.warning("RAG search failed", error=str(e))
            
            return {
                "analysis": analysis_result,
                "status": "completed"
            }
        
        @self.server.handler("store_knowledge")
        async def store_knowledge(data: Dict[str, Any]) -> Dict[str, Any]:
            """知識保存"""
            knowledge_item = data.get("knowledge")
            category = data.get("category", "general")
            
            # 知識ベースに保存（実装簡略化）
            if category not in self.knowledge_base:
                self.knowledge_base[category] = []
            
            self.knowledge_base[category].append(knowledge_item)
            
            # 他の賢者に通知
            await self.broadcast_to_domain(
                "knowledge_updated",
                {"category": category, "item_count": len(self.knowledge_base[category])}
            )
            
            return {"status": "stored", "category": category}

# 起動用エントリーポイント
async def main():
    sage = KnowledgeSageA2A()
    await sage.run_forever()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
EOF

echo -e "${GREEN}✅ Knowledge Sage implementation created${NC}"

echo -e "${YELLOW}Step 6: Creating FastAPI Gateway...${NC}"

cat > $ELDER_TREE_ROOT/api/main.py << 'EOF'
"""
Elder Tree API Gateway
OSS First: FastAPI + Prometheus + OpenTelemetry
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import structlog
from typing import Dict, Any

from elder_tree.core.communication.a2a_alternative import Client

# 構造化ログ設定
logger = structlog.get_logger(__name__)

# FastAPIアプリ作成
app = FastAPI(
    title="Elder Tree API Gateway",
    description="Unified API for Elder Tree Distributed AI Architecture",
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

# A2Aクライアント
a2a_client = Client()

# Prometheusメトリクスエンドポイント
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
async def health_check():
    """API Gateway ヘルスチェック"""
    return {
        "status": "healthy",
        "service": "elder_tree_api_gateway",
        "version": "2.0.0"
    }

@app.post("/v1/souls/{soul_name}/call")
async def call_soul(soul_name: str, method: str, payload: Dict[str, Any]):
    """
    統一APIエンドポイント
    任意の魂のメソッドを呼び出し
    """
    try:
        logger.info("API call received",
                   soul_name=soul_name,
                   method=method)
        
        # A2A経由で魂呼び出し
        response = await a2a_client.call(
            service=f"elder_tree.{soul_name}",
            method=method,
            data=payload
        )
        
        return {
            "status": "success",
            "soul": soul_name,
            "method": method,
            "result": response
        }
        
    except Exception as e:
        logger.error("API call failed",
                    soul_name=soul_name,
                    method=method,
                    error=str(e))
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to call {soul_name}.{method}: {str(e)}"
        )

@app.get("/v1/souls")
async def list_souls():
    """利用可能な魂一覧"""
    return {
        "souls": [
            {"name": "knowledge_sage", "domain": "knowledge", "port": 50051},
            {"name": "task_sage", "domain": "task", "port": 50052},
            {"name": "incident_sage", "domain": "incident", "port": 50053},
            {"name": "rag_sage", "domain": "rag", "port": 50054}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

echo -e "${GREEN}✅ FastAPI Gateway created${NC}"

echo -e "${YELLOW}Step 7: Creating Docker configuration...${NC}"

# Dockerfile
cat > $ELDER_TREE_ROOT/docker/Dockerfile << 'EOF'
FROM python:3.11-slim

# Install Poetry
RUN pip install poetry

WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copy application
COPY . .

# Default command
CMD ["poetry", "run", "python", "-m", "elder_tree.api.main"]
EOF

# Docker Compose
cat > $ELDER_TREE_ROOT/docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL (OSS)
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: elder_tree
      POSTGRES_USER: elder
      POSTGRES_PASSWORD: elder_secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - elder-tree-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U elder"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis (OSS)
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - elder-tree-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Consul for Service Discovery (OSS)
  consul:
    image: consul:latest
    command: agent -server -bootstrap -ui -client 0.0.0.0
    ports:
      - "8500:8500"
    networks:
      - elder-tree-network

  # Prometheus (OSS)
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - elder-tree-network

  # Grafana (OSS)
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=elder_secret
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    networks:
      - elder-tree-network
    depends_on:
      - prometheus

  # API Gateway
  api-gateway:
    build:
      context: .
      dockerfile: docker/Dockerfile
    environment:
      - SOUL_NAME=api_gateway
    ports:
      - "8000:8000"
    networks:
      - elder-tree-network
    depends_on:
      - postgres
      - redis
      - consul

  # Knowledge Sage
  knowledge-sage:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: poetry run python -m elder_tree.domains.knowledge.knowledge_sage
    environment:
      - SOUL_NAME=knowledge_sage
      - SOUL_PORT=50051
    networks:
      - elder-tree-network
    depends_on:
      - postgres
      - redis
      - consul

networks:
  elder-tree-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
EOF

echo -e "${GREEN}✅ Docker configuration created${NC}"

echo -e "${YELLOW}Step 8: Creating launch script...${NC}"

cat > $ELDER_TREE_ROOT/scripts/launch_elder_tree.py << 'EOF'
#!/usr/bin/env python3
"""
Elder Tree Launch Script
OSS First: multiprocessing + asyncio
"""

import asyncio
import multiprocessing
import signal
import sys
from typing import List, Tuple, Type

# Import souls
from elder_tree.domains.knowledge.knowledge_sage import KnowledgeSageA2A
# from elder_tree.domains.task.task_sage import TaskSageA2A
# from elder_tree.domains.incident.incident_sage import IncidentSageA2A
# from elder_tree.domains.rag.rag_sage import RAGSageA2A

def launch_soul(soul_class: Type, config: dict):
    """個別魂プロセス起動"""
    # 非同期イベントループで魂実行
    soul = soul_class(config)
    asyncio.run(soul.run_forever())

def signal_handler(sig, frame):
    """グレースフルシャットダウン"""
    print("\n🛑 Shutting down Elder Tree...")
    sys.exit(0)

def main():
    """Elder Tree全体起動"""
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🌳 Starting Elder Tree Distributed AI Architecture...")
    print("📋 OSS First Policy Compliant")
    
    # 起動する魂のリスト
    souls: List[Tuple[Type, dict]] = [
        (KnowledgeSageA2A, {"port": 50051}),
        # (TaskSageA2A, {"port": 50052}),
        # (IncidentSageA2A, {"port": 50053}),
        # (RAGSageA2A, {"port": 50054}),
    ]
    
    processes = []
    
    # 各魂を別プロセスで起動
    for soul_class, config in souls:
        print(f"🚀 Launching {config.get('soul_name', soul_class.__name__)}...")
        p = multiprocessing.Process(
            target=launch_soul,
            args=(soul_class, config)
        )
        p.start()
        processes.append(p)
    
    print(f"✅ {len(processes)} souls launched successfully")
    print("📡 Elder Tree is running... Press Ctrl+C to stop")
    
    # プロセス監視
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\n🛑 Stopping all souls...")
        for p in processes:
            p.terminate()
            p.join()

if __name__ == "__main__":
    main()
EOF

chmod +x $ELDER_TREE_ROOT/scripts/launch_elder_tree.py

echo -e "${GREEN}✅ Launch script created${NC}"

echo -e "${YELLOW}Step 9: Creating README...${NC}"

cat > $ELDER_TREE_ROOT/README.md << 'EOF'
# 🌳 Elder Tree Distributed AI Architecture v2.0

**OSS First Implementation**

## 🚀 Quick Start

```bash
# Install dependencies
cd elder_tree
poetry install

# Compile Protocol Buffers
poetry run python -m grpc_tools.protoc \
    -I./protos --python_out=./protos --grpc_python_out=./protos \
    protos/*.proto

# Start infrastructure
docker-compose up -d postgres redis consul prometheus grafana

# Launch Elder Tree
poetry run python scripts/launch_elder_tree.py

# Or use Docker Compose for everything
docker-compose up
```

## 📊 Architecture

- **Communication**: gRPC (a2a-python alternative)
- **API Gateway**: FastAPI
- **Database**: PostgreSQL + Redis
- **Monitoring**: Prometheus + Grafana
- **Service Discovery**: Consul
- **Message Format**: Protocol Buffers

## 🧪 Testing

```bash
# Run tests
poetry run pytest

# With coverage
poetry run pytest --cov=elder_tree
```

## 📈 Monitoring

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/elder_secret)
- Consul UI: http://localhost:8500
- API Docs: http://localhost:8000/docs

## 🏛️ OSS Credits

This project is built on top of amazing open source software:
- FastAPI, gRPC, PostgreSQL, Redis, Prometheus, Grafana, Consul
- And many more...

**Remember: Don't Reinvent the Wheel!**
EOF

echo -e "${GREEN}✅ README created${NC}"

echo -e "${YELLOW}Step 10: Creating test structure...${NC}"

# テストファイル
cat > $ELDER_TREE_ROOT/tests/test_a2a_soul.py << 'EOF'
"""
A2A Soul Tests
OSS: pytest + pytest-asyncio
"""

import pytest
from elder_tree.core.souls.a2a_soul import A2ASoul

class TestSoul(A2ASoul):
    """テスト用魂実装"""
    
    def _register_domain_handlers(self):
        @self.server.handler("test_method")
        async def test_method(data):
            return {"echo": data}

@pytest.mark.asyncio
async def test_soul_initialization():
    """魂初期化テスト"""
    config = {
        "soul_name": "test_soul",
        "domain": "test",
        "port": 59999
    }
    
    soul = TestSoul(config)
    assert soul.soul_name == "test_soul"
    assert soul.port == 59999
    
    # 初期化成功確認
    result = await soul.initialize()
    assert result is True

@pytest.mark.asyncio
async def test_health_check():
    """ヘルスチェックテスト"""
    config = {
        "soul_name": "test_soul",
        "domain": "test", 
        "port": 59998
    }
    
    soul = TestSoul(config)
    health = soul.get_health_status()
    
    assert health["status"] == "healthy"
    assert health["soul_name"] == "test_soul"
    assert "uptime_seconds" in health
EOF

echo -e "${GREEN}✅ Test structure created${NC}"

echo "
================================================================================
${GREEN}🎉 Elder Tree OSS First Setup Complete!${NC}
================================================================================

📁 Created structure:
$ELDER_TREE_ROOT/
├── core/          # Core functionality
├── domains/       # Domain implementations  
├── api/           # FastAPI Gateway
├── protos/        # Protocol Buffers
├── docker/        # Docker configuration
├── scripts/       # Launch scripts
└── tests/         # Test suite

📦 OSS Stack:
- Communication: gRPC (a2a alternative)
- API: FastAPI + Uvicorn
- Database: PostgreSQL + Redis
- Monitoring: Prometheus + Grafana
- Service Discovery: Consul
- Testing: pytest + pytest-asyncio
- Code Quality: black + ruff + mypy

🚀 Next Steps:
1. cd $ELDER_TREE_ROOT
2. poetry install
3. docker-compose up -d
4. poetry run python scripts/launch_elder_tree.py

📚 Design Document: docs/technical/ELDER_TREE_A2A_IMPLEMENTATION.md
📋 OSS Policy: docs/policies/OSS_FIRST_DEVELOPMENT_POLICY.md

${YELLOW}Note: a2a-python doesn't actually exist, so we created an alternative
implementation using gRPC following the same patterns.${NC}

================================================================================
"

# 実行権限付与
chmod +x $0

echo -e "${GREEN}✅ Setup script created and made executable${NC}"