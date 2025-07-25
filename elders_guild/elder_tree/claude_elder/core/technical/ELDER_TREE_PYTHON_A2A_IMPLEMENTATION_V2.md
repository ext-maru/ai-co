# 🌳 Elder Tree Python-A2A実装設計書 v2.0

**Document Type**: Implementation Design Specification  
**Version**: 2.0.0  
**Created**: 2025年7月22日  
**Author**: Claude Elder (クロードエルダー)  
**Policy**: OSS First + TDD/XP First  
**Library**: python-a2a (0.5.9)

---

## 📖 **目次**
1. [概要](#概要)
2. [python-a2aライブラリ詳細](#python-a2aライブラリ詳細)
3. [OSS First + TDD/XP方針](#oss-first--tddxp方針)
4. [技術スタック](#技術スタック)
5. [実装アーキテクチャ](#実装アーキテクチャ)
6. [TDD実装計画](#tdd実装計画)
7. [プロジェクト構造](#プロジェクト構造)

---

## 🎯 **概要**

Elder Treeの分散AI通信基盤として、実在する`python-a2a`ライブラリ（v0.5.9）を採用。OSS FirstとTDD/XP開発手法を組み合わせた実装設計。

### 💡 **主要特徴**
- **実在のOSS**: python-a2a (MIT License)
- **MCP対応**: Model Context Protocol完全サポート
- **マルチLLM**: OpenAI, Anthropic, AWS Bedrock, LangChain統合
- **エンタープライズ対応**: 本番環境向け堅牢実装

---

## 📦 **python-a2aライブラリ詳細**

### 🔧 **基本情報**
```yaml
Package: python-a2a
Version: 0.5.9
Author: Manoj Desai
License: MIT
Repository: https://github.com/themanojdesai/python-a2a
PyPI: https://pypi.org/project/python-a2a/
Python: >=3.9
```

### 📋 **主要機能**
1. **Agent-to-Agent Protocol**: Google A2A完全実装
2. **Model Context Protocol (MCP)**: v2.0対応
3. **Agent Discovery**: エージェント自動発見
4. **Streaming Support**: リアルタイムストリーミング
5. **Workflow Engine**: 複雑なマルチエージェントワークフロー
6. **LangChain Integration**: シームレス統合

### 🚀 **インストール**
```bash
# 基本インストール（全機能）
pip install python-a2a

# 特定機能のみ
pip install "python-a2a[server]"    # Flaskサーバー
pip install "python-a2a[openai]"    # OpenAI統合
pip install "python-a2a[anthropic]" # Claude統合
pip install "python-a2a[mcp]"       # MCP機能
```

---

## 🏛️ **OSS First + TDD/XP方針**

### 📋 **開発原則**
1. **OSS First**: 既存OSSを最大限活用
2. **TDD必須**: Red→Green→Refactorサイクル厳守
3. **XP実践**: ペアプロ（AI-Human）、小規模リリース、継続的統合
4. **Iron Will**: 品質基準100%遵守

### 🔄 **開発フロー**
```
1. ユーザーストーリー作成
2. 受け入れテスト作成（失敗）
3. 最小実装（テスト通過）
4. リファクタリング
5. 統合・デプロイ
```

---

## 📊 **技術スタック（OSS活用）**

```yaml
# コア通信
python-a2a: "^0.5.9"          # Agent間通信の中核

# Web/API
fastapi: "^0.104.0"           # API Gateway
uvicorn: "^0.24.0"            # ASGIサーバー
pydantic: "^2.5.0"            # データ検証

# データベース
sqlmodel: "^0.0.14"           # ORM (Pydantic統合)
asyncpg: "^0.29.0"            # PostgreSQL非同期
redis: "^5.0.1"               # キャッシュ・セッション

# AI/LLM統合
anthropic: "^0.7.0"           # Claude API
openai: "^1.0.0"              # OpenAI API
langchain: "^0.1.0"           # LangChain統合

# 監視・ログ
prometheus-client: "^0.19.0"   # メトリクス
structlog: "^23.2.0"          # 構造化ログ
opentelemetry-api: "^1.21.0"  # 分散トレーシング

# 開発ツール
pytest: "^7.4.3"              # TDDフレームワーク
pytest-asyncio: "^0.21.1"     # 非同期テスト
pytest-cov: "^4.1.0"          # カバレッジ
black: "^23.11.0"             # フォーマッター
ruff: "^0.1.6"                # リンター
mypy: "^1.7.0"                # 型チェック
```

---

## 🏗️ **実装アーキテクチャ**

### 📁 **プロジェクト構造（TDD準拠）**

```
elder_tree/
├── tests/                        # テストファースト！
│   ├── unit/                     # ユニットテスト
│   │   ├── test_agents/          # エージェントテスト
│   │   ├── test_communication/   # 通信テスト
│   │   └── test_integration/     # 統合テスト
│   ├── acceptance/               # 受け入れテスト
│   │   └── test_user_stories.py  # ユーザーストーリー
│   └── conftest.py              # pytest設定
│
├── src/elder_tree/              # 実装（テスト後）
│   ├── agents/                  # python-a2a統合エージェント
│   │   ├── __init__.py
│   │   ├── base_agent.py        # 基底エージェント
│   │   ├── knowledge_sage.py    # Knowledge Sage
│   │   ├── task_sage.py         # Task Sage
│   │   ├── incident_sage.py     # Incident Sage
│   │   └── rag_sage.py          # RAG Sage
│   │
│   ├── protocols/               # プロトコル実装
│   │   ├── __init__.py
│   │   ├── a2a_protocol.py      # A2A拡張
│   │   └── mcp_integration.py   # MCP統合
│   │
│   ├── workflows/               # ワークフロー定義
│   │   ├── __init__.py
│   │   ├── elder_flow.py        # Elder Flow実装
│   │   └── sage_collaboration.py # 4賢者協調
│   │
│   ├── api/                     # FastAPI Gateway
│   │   ├── __init__.py
│   │   ├── main.py              # APIエントリーポイント
│   │   ├── routers/             # APIルーター
│   │   └── middleware/          # ミドルウェア
│   │
│   └── monitoring/              # 監視・ログ
│       ├── __init__.py
│       ├── metrics.py           # Prometheus
│       └── logging.py           # structlog
│
├── docs/                        # ドキュメント
│   ├── api/                     # API仕様
│   ├── architecture/            # アーキテクチャ
│   └── user_stories/            # ユーザーストーリー
│
├── scripts/                     # 実行スクリプト
│   ├── run_tests.sh            # テスト実行
│   ├── start_elder_tree.py     # システム起動
│   └── generate_coverage.sh    # カバレッジ生成
│
├── pyproject.toml              # Poetry設定
├── .gitlab-ci.yml              # CI/CD設定
└── README.md                   # プロジェクト説明
```

---

## 🧪 **TDD実装計画**

### Phase 1: 基盤テスト（Day 1）

#### 1.1 受け入れテスト作成
```python
# tests/acceptance/test_user_stories.py
import pytest
from python_a2a import Agent

class TestElderTreeUserStories:
    """ユーザーストーリーベースの受け入れテスト"""
    
    @pytest.mark.acceptance
    async def test_4_sages_can_communicate(self):
        """
        ユーザーストーリー: 4賢者が相互通信できる
        Given: 4つの賢者エージェントが起動している
        When: Knowledge SageがTask Sageにメッセージを送信
        Then: Task Sageが応答を返す
        """
        # Red: このテストは最初失敗する
        knowledge_sage = Agent(name="knowledge_sage")
        task_sage = Agent(name="task_sage")
        
        await knowledge_sage.start()
        await task_sage.start()
        
        response = await knowledge_sage.send_message(
            target="task_sage",
            message_type="estimate_task",
            data={"task": "implement_feature"}
        )
        
        assert response.status == "success"
        assert "estimation" in response.data
```

#### 1.2 ユニットテスト作成
```python
# tests/unit/test_agents/test_base_agent.py
import pytest
from elder_tree.agents.base_agent import ElderTreeAgent

class TestElderTreeAgent:
    """TDD: エージェント基底クラステスト"""
    
    def test_agent_initialization(self):
        """Red: エージェント初期化テスト"""
        agent = ElderTreeAgent(
            name="test_agent",
            domain="test"
        )
        assert agent.name == "test_agent"
        assert agent.domain == "test"
    
    @pytest.mark.asyncio
    async def test_agent_can_handle_messages(self):
        """Red: メッセージハンドリングテスト"""
        agent = ElderTreeAgent(
            name="test_agent",
            domain="test"
        )
        
        @agent.on_message("test_message")
        async def handle_test(message):
            return {"echo": message.data}
        
        result = await agent.process_message(
            message_type="test_message",
            data={"hello": "world"}
        )
        
        assert result["echo"]["hello"] == "world"
```

### Phase 2: エージェント実装（Day 2-3）

#### 2.1 基底エージェント実装（Green）
```python
# src/elder_tree/agents/base_agent.py
from python_a2a import Agent, Message
from typing import Dict, Any, Callable
import structlog

logger = structlog.get_logger()

class ElderTreeAgent(Agent):
    """Elder Tree用python-a2a統合エージェント"""
    
    def __init__(self, name: str, domain: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.domain = domain
        self.logger = logger.bind(agent=name, domain=domain)
        
        # Prometheusメトリクス
        self._setup_metrics()
        
        # 基本ハンドラー登録
        self._register_base_handlers()
    
    def _setup_metrics(self):
        """メトリクス設定"""
        from prometheus_client import Counter, Histogram
        
        self.message_counter = Counter(
            'agent_messages_total',
            'Total messages processed',
            ['agent_name', 'message_type', 'status']
        )
        
        self.message_duration = Histogram(
            'agent_message_duration_seconds',
            'Message processing duration',
            ['agent_name', 'message_type']
        )
    
    def _register_base_handlers(self):
        """基本ハンドラー登録"""
        
        @self.on_message("health_check")
        async def health_check(message: Message) -> Dict[str, Any]:
            """ヘルスチェック"""
            return {
                "status": "healthy",
                "agent": self.name,
                "domain": self.domain
            }
```

#### 2.2 Knowledge Sage実装（Green）
```python
# src/elder_tree/agents/knowledge_sage.py
from elder_tree.agents.base_agent import ElderTreeAgent
from typing import Dict, Any

class KnowledgeSage(ElderTreeAgent):
    """Knowledge Sage - 知識管理エージェント"""
    
    def __init__(self):
        super().__init__(
            name="knowledge_sage",
            domain="knowledge",
            port=50051
        )
        
        # ハンドラー登録
        self._register_domain_handlers()
    
    def _register_domain_handlers(self):
        """ドメイン固有ハンドラー"""
        
        @self.on_message("analyze_technology")
        async def analyze_technology(message) -> Dict[str, Any]:
            """技術分析（TDD実装）"""
            tech_name = message.data.get("technology")
            
            # 実装（テストが通るように）
            analysis = {
                "technology": tech_name,
                "assessment": "suitable",
                "confidence": 0.85
            }
            
            return {"analysis": analysis}
```

### Phase 3: ワークフロー実装（Day 4）

#### 3.1 Elder Flowテスト（Red）
```python
# tests/unit/test_workflows/test_elder_flow.py
import pytest
from elder_tree.workflows.elder_flow import ElderFlow

class TestElderFlow:
    """Elder Flow TDDテスト"""
    
    @pytest.mark.asyncio
    async def test_elder_flow_execution(self):
        """Red: Elder Flow実行テスト"""
        flow = ElderFlow()
        
        result = await flow.execute(
            task_type="implementation",
            requirements=["OAuth2.0認証"]
        )
        
        assert result.status == "completed"
        assert result.stages_completed == 5
```

#### 3.2 Elder Flow実装（Green）
```python
# src/elder_tree/workflows/elder_flow.py
from python_a2a import Workflow
from typing import List, Dict, Any

class ElderFlow(Workflow):
    """Elder Flow - 5段階自動化フロー"""
    
    def __init__(self):
        super().__init__(name="elder_flow")
        
        # ワークフロー定義
        self.add_stage("sage_consultation", self._consult_sages)
        self.add_stage("servant_execution", self._execute_servants)
        self.add_stage("quality_gate", self._quality_check)
        self.add_stage("council_report", self._report_to_council)
        self.add_stage("git_automation", self._git_operations)
    
    async def _consult_sages(self, context: Dict[str, Any]):
        """4賢者協議"""
        # 並列協議実装
        pass
```

### Phase 4: API Gateway（Day 5）

#### 4.1 APIテスト（Red）
```python
# tests/unit/test_api/test_main.py
from fastapi.testclient import TestClient
from elder_tree.api.main import app

client = TestClient(app)

def test_api_health_check():
    """Red: APIヘルスチェック"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_agent_call_endpoint():
    """Red: エージェント呼び出しAPI"""
    response = client.post(
        "/v1/agents/knowledge_sage/call",
        json={
            "method": "analyze_technology",
            "data": {"technology": "FastAPI"}
        }
    )
    assert response.status_code == 200
    assert "analysis" in response.json()
```

### Phase 5: 統合テスト（Day 6-7）

#### 5.1 エンドツーエンドテスト
```python
# tests/acceptance/test_e2e.py
import pytest
from elder_tree.agents import KnowledgeSage, TaskSage
from elder_tree.workflows import ElderFlow

class TestEndToEnd:
    """エンドツーエンド受け入れテスト"""
    
    @pytest.mark.e2e
    async def test_complete_elder_flow(self):
        """完全なElder Flow実行テスト"""
        # 全エージェント起動
        agents = [
            KnowledgeSage(),
            TaskSage(),
            # ... 他の賢者
        ]
        
        for agent in agents:
            await agent.start()
        
        # Elder Flow実行
        flow = ElderFlow()
        result = await flow.execute(
            task_type="feature_implementation",
            requirements=["新機能実装"]
        )
        
        assert result.status == "success"
        assert all(stage.completed for stage in result.stages)
```

---

## 🚀 **実装開始手順**

### 1. プロジェクト初期化
```bash
# Poetryプロジェクト作成
poetry new elder-tree
cd elder-tree

# 依存関係追加
poetry add python-a2a fastapi uvicorn sqlmodel asyncpg redis prometheus-client structlog
poetry add --dev pytest pytest-asyncio pytest-cov black ruff mypy
```

### 2. TDD開始
```bash
# テスト作成（Red）
poetry run pytest tests/ -v  # 失敗確認

# 実装（Green）
# 最小限の実装でテストを通す

# リファクタリング（Refactor）
# コード品質向上
```

### 3. 継続的統合
```bash
# テスト実行
poetry run pytest --cov=elder_tree

# 品質チェック
poetry run black .
poetry run ruff .
poetry run mypy .
```

---

## ✅ **成功基準**

1. **python-a2a完全活用**: 全通信がpython-a2a経由
2. **TDDカバレッジ**: 95%以上
3. **OSS活用率**: 90%以上
4. **XP実践**: 小規模リリース、継続的統合
5. **パフォーマンス**: レイテンシ < 100ms

---

## 📝 **まとめ**

- **OSS First**: python-a2a (実在のOSS) を中心に構築
- **TDD/XP First**: Red→Green→Refactorサイクル厳守
- **実用的実装**: MCP対応、LangChain統合、本番環境対応

**「車輪の再発明を避け、TDDで品質を保証し、実在のOSSで構築する」**