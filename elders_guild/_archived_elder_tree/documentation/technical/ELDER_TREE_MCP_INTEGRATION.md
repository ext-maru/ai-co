# 🌳 Elder Tree MCP統合設計書 - fastmcp実装

**Document Type**: MCP Integration Design Specification  
**Version**: 1.0.0  
**Created**: 2025年7月22日  
**Author**: Claude Elder (クロードエルダー)  
**Parent Documents**: 
- [ELDER_TREE_DISTRIBUTED_AI_ARCHITECTURE.md](./ELDER_TREE_DISTRIBUTED_AI_ARCHITECTURE.md)
- [ELDER_TREE_A2A_IMPLEMENTATION.md](./ELDER_TREE_A2A_IMPLEMENTATION.md)

---

## 📖 **目次**
1. [概要](#概要)
2. [MCP統合アーキテクチャ](#mcp統合アーキテクチャ)
3. [fastmcp実装設計](#fastmcp実装設計)
4. [魂とツールの関係設計](#魂とツールの関係設計)
5. [具体的実装例](#具体的実装例)
6. [デプロイメント構成](#デプロイメント構成)

---

## 🎯 **概要**

Elder Treeにおいて、**a2a-python**（魂間通信）と**MCP**（魂-ツール間通信）を組み合わせることで、完全な分散AI協調システムを実現します。`fastmcp`を活用することで、FastAPIベースの実装と完璧に統合できます。

### 💡 **アーキテクチャ思想**

```
🌳 Elder Tree = a2a（魂間協調） + MCP（専門ツール活用）

魂（Soul） ←→ 魂（Soul）: a2a-python (gRPC)
魂（Soul） ←→ ツール（Tool）: MCP via fastmcp
```

### 🎯 **fastmcpの利点**
- **FastAPI統合**: 既存のFastAPIアプリにMCPを簡単追加
- **非同期対応**: async/awaitネイティブサポート
- **型安全**: Pydanticによる厳密な型定義
- **自動ドキュメント**: OpenAPI/Swagger自動生成

---

## 🏗️ **MCP統合アーキテクチャ**

### 🌐 **通信レイヤー設計**

```
┌─────────────────────────────────────────────────┐
│                 外部クライアント                   │
└────────────────────┬───────────────────────────┘
                     │ HTTP/WebSocket
┌────────────────────▼───────────────────────────┐
│              FastAPI Gateway                    │
│              (fastmcp統合)                      │
└────────────────────┬───────────────────────────┘
                     │
┌────────────────────▼───────────────────────────┐
│                Elder Tree Core                  │
├─────────────────────────────────────────────────┤
│  魂層（Souls）      │        ツール層（Tools）    │
│                    │                            │
│  🧙‍♂️ Knowledge Sage │ ←MCP→ 📚 Tech Dictionary │
│      ↕ a2a         │        🔍 Code Analyzer   │
│  📋 Task Sage      │ ←MCP→ 📊 Project Planner │
│      ↕ a2a         │        ⏰ Schedule Tool   │
│  🚨 Incident Sage  │ ←MCP→ 🛡️ Security Scanner│
│      ↕ a2a         │        📈 Metrics Tool    │
│  🔍 RAG Sage       │ ←MCP→ 🔎 Vector Search   │
│                    │        🗃️ Doc Indexer     │
└────────────────────┴────────────────────────────┘
```

### 🔄 **通信フロー**

1. **外部リクエスト** → FastAPI Gateway（fastmcp）
2. **ルーティング** → 適切な魂へ
3. **魂の処理**:
   - MCPでツール呼び出し（専門処理）
   - a2aで他魂連携（必要時）
4. **結果統合** → クライアントへ返却

---

## 🚀 **fastmcp実装設計**

### 📦 **技術スタック追加**

```toml
# pyproject.toml 追加分
[tool.poetry.dependencies]
# MCP統合
fastmcp = "^0.2.0"              # FastAPI MCP統合
mcp = "^0.5.0"                   # MCP SDK
pydantic-settings = "^2.1.0"     # 設定管理
```

### 🧬 **FastMCPSoul基底クラス**

```python
# elder_tree/core/souls/fastmcp_soul.py
from fastapi import FastAPI
from fastmcp import FastMCP
from mcp import Tool, Resource
from elder_tree.core.souls.a2a_soul import A2ASoul
from typing import Dict, Any, List
import uvicorn

class FastMCPSoul(A2ASoul):
    """FastMCP + a2a対応魂基底クラス"""
    
    def __init__(self, soul_config: Dict[str, Any]):
        super().__init__(soul_config)
        
        # FastAPI app作成
        self.app = FastAPI(
            title=f"Elder Tree - {self.soul_name}",
            description=f"{self.domain} Domain Soul with MCP Tools"
        )
        
        # FastMCP統合
        self.mcp = FastMCP(self.app, prefix="/mcp")
        
        # ツール登録
        self._register_mcp_tools()
        
        # APIルート登録
        self._register_api_routes()
        
    def _register_mcp_tools(self):
        """MCPツール登録（サブクラスでオーバーライド）"""
        pass
        
    def _register_api_routes(self):
        """FastAPIルート登録"""
        
        @self.app.get("/health")
        async def health_check():
            """ヘルスチェック"""
            return {
                "status": "healthy",
                "soul": self.soul_name,
                "domain": self.domain,
                "mcp_tools": len(self.mcp.list_tools())
            }
            
        @self.app.post("/process")
        async def process_request(request: Dict[str, Any]):
            """汎用処理エンドポイント"""
            # MCPツール活用
            if request.get("use_tools"):
                tool_results = await self._execute_tools(
                    request["tools"]
                )
                request["tool_results"] = tool_results
                
            # a2a通信で他魂と連携
            if request.get("collaborate"):
                collab_results = await self._collaborate_with_souls(
                    request["collaborations"]
                )
                request["collaboration_results"] = collab_results
                
            # ドメイン固有処理
            result = await self.process_domain_request(request)
            
            return {
                "soul": self.soul_name,
                "result": result
            }
    
    async def _execute_tools(self, tool_requests: List[Dict]) -> List[Dict]:
        """MCPツール実行"""
        results = []
        for req in tool_requests:
            tool_name = req["tool"]
            params = req["params"]
            
            result = await self.mcp.call_tool(tool_name, **params)
            results.append({
                "tool": tool_name,
                "result": result
            })
            
        return results
        
    async def run_soul(self):
        """魂の実行（FastAPI + a2a）"""
        # a2aサーバー起動（別スレッド）
        import threading
        a2a_thread = threading.Thread(
            target=lambda: asyncio.run(self.run_forever())
        )
        a2a_thread.start()
        
        # FastAPIサーバー起動
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.soul_config.get("http_port", 8000)
        )
        server = uvicorn.Server(config)
        await server.serve()
```

---

## 🧙‍♂️ **魂とツールの関係設計**

### 📚 **Knowledge Sage + 専門ツール**

```python
# elder_tree/domains/knowledge/knowledge_sage_fastmcp.py
from elder_tree.core.souls.fastmcp_soul import FastMCPSoul
from fastmcp import tool, resource
from typing import Dict, List, Optional

class KnowledgeSageFastMCP(FastMCPSoul):
    """Knowledge Sage with FastMCP tools"""
    
    def __init__(self):
        super().__init__({
            "soul_name": "knowledge_sage",
            "domain": "knowledge",
            "port": 50051,  # a2a port
            "http_port": 8051  # FastAPI port
        })
        
    def _register_mcp_tools(self):
        """Knowledge Domain専用MCPツール"""
        
        # 技術辞書ツール
        @self.mcp.tool()
        async def tech_dictionary(
            term: str,
            include_examples: bool = False
        ) -> Dict[str, Any]:
            """技術用語の詳細情報を取得"""
            # 実際の辞書検索ロジック
            result = await self.tech_db.lookup(term)
            
            if include_examples:
                examples = await self.tech_db.get_examples(term)
                result["examples"] = examples
                
            return result
            
        # コード分析ツール
        @self.mcp.tool()
        async def analyze_code_quality(
            code: str,
            language: str = "python",
            metrics: List[str] = ["complexity", "maintainability"]
        ) -> Dict[str, Any]:
            """コード品質の詳細分析"""
            analysis = {
                "language": language,
                "metrics": {}
            }
            
            for metric in metrics:
                if metric == "complexity":
                    analysis["metrics"]["complexity"] = \
                        await self.complexity_analyzer.analyze(code)
                elif metric == "maintainability":
                    analysis["metrics"]["maintainability"] = \
                        await self.maintainability_checker.check(code)
                        
            # Iron Will違反チェック
            analysis["iron_will_violations"] = \
                await self.iron_will_checker.scan(code)
                
            return analysis
            
        # ドキュメント生成ツール
        @self.mcp.tool()
        async def generate_technical_docs(
            spec: Dict[str, Any],
            doc_type: str = "api",
            format: str = "markdown"
        ) -> str:
            """技術ドキュメント自動生成"""
            if doc_type == "api":
                doc = await self.api_doc_generator.generate(spec)
            elif doc_type == "architecture":
                doc = await self.arch_doc_generator.generate(spec)
            elif doc_type == "tutorial":
                doc = await self.tutorial_generator.generate(spec)
                
            if format == "html":
                doc = await self.markdown_to_html(doc)
                
            return doc
            
        # 技術スタック推奨ツール
        @self.mcp.tool()
        async def recommend_tech_stack(
            requirements: List[str],
            constraints: Optional[Dict] = None
        ) -> Dict[str, Any]:
            """要件に基づく技術スタック推奨"""
            # RAG Sageと連携して最新情報取得
            latest_trends = await self.call_soul(
                "rag_sage",
                "get_tech_trends",
                {"categories": ["web", "ai", "database"]}
            )
            
            recommendations = await self.stack_recommender.analyze(
                requirements,
                constraints,
                latest_trends
            )
            
            return recommendations
            
        # MCPリソース定義
        @self.mcp.resource("knowledge_base")
        async def get_knowledge_base_info() -> Dict:
            """ナレッジベース情報"""
            return {
                "total_entries": await self.kb.count(),
                "categories": await self.kb.get_categories(),
                "last_updated": await self.kb.last_update_time()
            }
```

### 🤖 **Code Craftsman Servant + 開発ツール**

```python
# elder_tree/domains/knowledge/servants/code_craftsman_fastmcp.py
class CodeCraftsmanFastMCP(FastMCPSoul):
    """Code Craftsman with development tools"""
    
    def _register_mcp_tools(self):
        """コード生成・開発ツール"""
        
        @self.mcp.tool()
        async def generate_tdd_code(
            feature_name: str,
            requirements: List[str],
            language: str = "python"
        ) -> Dict[str, str]:
            """TDD準拠のコード生成"""
            # 1. テスト生成
            test_code = await self.test_generator.create_tests(
                feature_name, requirements, language
            )
            
            # 2. 最小実装
            impl_code = await self.code_generator.create_minimal(
                feature_name, test_code, language
            )
            
            # 3. 品質チェック（Knowledge Sageに依頼）
            quality = await self.call_soul(
                "knowledge_sage",
                "analyze_code_quality",
                {"code": impl_code, "language": language}
            )
            
            # 4. リファクタリング
            if quality["score"] < 85:
                impl_code = await self.refactorer.improve(
                    impl_code, quality["suggestions"]
                )
                
            return {
                "test_file": test_code,
                "implementation_file": impl_code,
                "quality_score": quality["score"]
            }
            
        @self.mcp.tool()
        async def format_code(
            code: str,
            style: str = "black",
            language: str = "python"
        ) -> str:
            """コードフォーマット"""
            formatters = {
                "python": {"black": self.black_formatter},
                "javascript": {"prettier": self.prettier_formatter}
            }
            
            formatter = formatters.get(language, {}).get(style)
            if formatter:
                return await formatter.format(code)
            else:
                raise ValueError(f"Unsupported formatter: {style} for {language}")
                
        @self.mcp.tool()
        async def git_operations(
            operation: str,
            params: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Git操作ツール"""
            if operation == "commit":
                return await self.git_client.commit(
                    params["message"],
                    params.get("files", [])
                )
            elif operation == "branch":
                return await self.git_client.create_branch(
                    params["name"],
                    params.get("from_branch", "main")
                )
            elif operation == "pr":
                return await self.git_client.create_pr(
                    params["title"],
                    params["body"],
                    params.get("base", "main")
                )
```

---

## 🔧 **具体的実装例**

### 🌊 **Elder Flow統合例**

```python
# Elder Flow実行時のMCP活用
class ElderFlowExecutor:
    """Elder Flow with MCP tools integration"""
    
    async def execute_implementation_flow(self, issue_data: Dict):
        """実装フロー（MCP統合版）"""
        
        # 1. Knowledge Sageで技術分析（MCPツール活用）
        knowledge_response = await self.http_client.post(
            "http://knowledge-sage:8051/process",
            json={
                "action": "analyze_issue",
                "data": issue_data,
                "use_tools": True,
                "tools": [
                    {
                        "tool": "tech_dictionary",
                        "params": {"term": "FastAPI", "include_examples": True}
                    },
                    {
                        "tool": "recommend_tech_stack",
                        "params": {"requirements": issue_data["requirements"]}
                    }
                ]
            }
        )
        
        tech_analysis = knowledge_response.json()["result"]
        
        # 2. Task Sageで計画策定（a2a通信）
        task_sage = await self.get_soul_client("task_sage")
        implementation_plan = await task_sage.call_soul(
            "task_sage",
            "create_plan",
            {"tech_analysis": tech_analysis}
        )
        
        # 3. Code Craftsmanで実装（MCPツール活用）
        code_response = await self.http_client.post(
            "http://code-craftsman:8061/process",
            json={
                "action": "implement_feature",
                "data": implementation_plan,
                "use_tools": True,
                "tools": [
                    {
                        "tool": "generate_tdd_code",
                        "params": {
                            "feature_name": issue_data["title"],
                            "requirements": implementation_plan["requirements"]
                        }
                    },
                    {
                        "tool": "format_code",
                        "params": {"style": "black"}
                    }
                ]
            }
        )
        
        implementation = code_response.json()["result"]
        
        # 4. Git操作（MCPツール）
        git_response = await self.http_client.post(
            "http://code-craftsman:8061/mcp/tools/git_operations",
            json={
                "operation": "commit",
                "params": {
                    "message": f"feat: {issue_data['title']} (#Issue番号)",
                    "files": implementation["files"]
                }
            }
        )
        
        return {
            "issue": issue_data["number"],
            "tech_analysis": tech_analysis,
            "implementation": implementation,
            "git_result": git_response.json()
        }
```

### 🔄 **ハイブリッド通信例**

```python
# 魂内でのMCP + a2a併用
async def complex_analysis(self, project_data: Dict):
    """複雑な分析（MCP + a2a）"""
    
    # MCPツールで基礎分析
    code_quality = await self.mcp.call_tool(
        "analyze_code_quality",
        code=project_data["code"],
        metrics=["all"]
    )
    
    # 結果が不十分なら他魂に相談（a2a）
    if code_quality["confidence"] < 0.8:
        # RAG Sageに類似コード検索依頼
        similar_patterns = await self.call_soul(
            "rag_sage",
            "find_similar_code",
            {"code_snippet": project_data["code"]}
        )
        
        # Incident Sageにリスク評価依頼
        risk_assessment = await self.call_soul(
            "incident_sage",
            "assess_code_risks",
            {"code": project_data["code"], "quality": code_quality}
        )
        
    # MCPツールで最終レポート生成
    report = await self.mcp.call_tool(
        "generate_technical_docs",
        spec={
            "analysis": code_quality,
            "similar_patterns": similar_patterns,
            "risks": risk_assessment
        },
        doc_type="analysis_report"
    )
    
    return report
```

---

## 🐳 **デプロイメント構成**

### 📦 **Docker Compose with MCP**

```yaml
# docker-compose.elder-tree-mcp.yml
version: '3.8'

services:
  # Knowledge Sage（FastAPI + MCP + a2a）
  knowledge-sage:
    build:
      context: .
      dockerfile: docker/Dockerfile.fastmcp-soul
    environment:
      SOUL_NAME: knowledge_sage
      A2A_PORT: 50051
      HTTP_PORT: 8051
      MCP_TOOLS: "tech_dictionary,analyze_code,generate_docs"
    ports:
      - "8051:8051"  # FastAPI/MCP
      - "50051:50051"  # a2a
    volumes:
      - ./mcp_tools/knowledge:/app/tools
      - knowledge_data:/app/data
    networks:
      - elder-tree-network
      
  # Code Craftsman（FastAPI + MCP + a2a）
  code-craftsman:
    build:
      context: .
      dockerfile: docker/Dockerfile.fastmcp-soul
    environment:
      SOUL_NAME: code_craftsman
      A2A_PORT: 50061
      HTTP_PORT: 8061
      MCP_TOOLS: "generate_code,format_code,git_operations"
    ports:
      - "8061:8061"
      - "50061:50061"
    volumes:
      - ./mcp_tools/craftsman:/app/tools
      - code_workspace:/app/workspace
    networks:
      - elder-tree-network
      
  # API Gateway（FastAPIルーティング）
  api-gateway:
    build:
      context: .
      dockerfile: docker/Dockerfile.gateway
    ports:
      - "8000:8000"
    environment:
      SOUL_ENDPOINTS: |
        knowledge_sage=http://knowledge-sage:8051
        code_craftsman=http://code-craftsman:8061
    depends_on:
      - knowledge-sage
      - code-craftsman
    networks:
      - elder-tree-network

networks:
  elder-tree-network:
    driver: bridge

volumes:
  knowledge_data:
  code_workspace:
```

### 🔧 **Dockerfile for FastMCP Soul**

```dockerfile
# docker/Dockerfile.fastmcp-soul
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy application
COPY elder_tree/ ./elder_tree/
COPY mcp_tools/ ./mcp_tools/

# Set environment
ENV PYTHONPATH=/app

# Run soul
CMD ["python", "-m", "elder_tree.launcher", "--soul", "${SOUL_NAME}"]
```

---

## 📊 **監視・管理**

### 🔍 **MCP Tool メトリクス**

```python
# MCPツール使用状況の監視
@self.app.get("/mcp/metrics")
async def get_mcp_metrics():
    """MCPツール使用統計"""
    return {
        "tools": {
            tool_name: {
                "call_count": self.mcp.get_tool_calls(tool_name),
                "avg_duration": self.mcp.get_avg_duration(tool_name),
                "error_rate": self.mcp.get_error_rate(tool_name)
            }
            for tool_name in self.mcp.list_tools()
        },
        "total_calls": self.mcp.get_total_calls(),
        "uptime": self.mcp.get_uptime()
    }
```

---

## 🎯 **ベストプラクティス**

### ✅ **DO**
- MCPツールは**ステートレス**に保つ
- ツールの粒度は**単一責任**に
- エラーハンドリングを**明示的**に
- ツールのバージョニングを行う

### ❌ **DON'T**
- MCPツール内で他魂を呼ばない（a2aを使う）
- 長時間実行するツールを作らない
- ツール間で状態を共有しない

---

**🏛️ Elder Tree MCP Integration Guild**

**Integration Architect**: Claude Elder (クロードエルダー)  
**Document Version**: 1.0.0  
**Created**: 2025年7月22日 19:00 JST  
**Status**: MCP Integration Design Complete  

**Related Documents**:
- [Elder Tree分散AIアーキテクチャ](./ELDER_TREE_DISTRIBUTED_AI_ARCHITECTURE.md)
- [Elder Tree A2A実装設計](./ELDER_TREE_A2A_IMPLEMENTATION.md)
- [fastmcp公式ドキュメント](https://github.com/fastmcp/fastmcp)

---
*🤖 Generated with [Claude Code](https://claude.ai/code)*

*Co-Authored-By: Claude <noreply@anthropic.com>*