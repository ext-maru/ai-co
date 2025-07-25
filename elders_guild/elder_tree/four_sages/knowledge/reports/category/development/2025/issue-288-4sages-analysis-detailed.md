# 🧙‍♂️ Issue #288: 4賢者システム移行 - Phase 1: 現状分析とマッピング

Parent Issue: [#258](https://github.com/ext-maru/ai-co/issues/258)

## 🎯 概要
既存4賢者システム（knowledge_base/、libs/配下）をElder Tree v2アーキテクチャに移行するため、現状の機能を詳細分析しElder Tree APIとのマッピングを実施。

## 🔍 現状システム詳細分析

### 1. ナレッジ賢者 (Knowledge Sage)
**現在の場所**: `knowledge_base/` ディレクトリ

#### 既存機能マトリクス
| 機能 | 現在の実装 | データ形式 | 更新頻度 | 重要度 |
|------|-----------|-----------|----------|-------|
| 核心教義 | CLAUDE.md | Markdown | 高 | Critical |
| TDDガイド | CLAUDE_TDD_GUIDE.md | Markdown | 中 | High |
| 失敗学習記録 | failures/ | Markdown + JSON | 高 | High |
| 実装サマリ | IMPLEMENTATION_SUMMARY_2025_07.md | Markdown | 低 | Medium |
| OSS調査記録 | 未実装 | - | 低 | Medium |

#### Elder Tree v2 マッピング計画
```python
# Elder Tree API統合
class KnowledgeSageV2(Elder TreeAgent):
    def __init__(self):
        super().__init__("knowledge_sage")
        self.knowledge_db = SQLModel_Knowledge_Base()
        self.vector_store = ChromaDB_Embeddings()
    
    async def store_knowledge(self, content: str, category: str, tags: List[str]):
        """知識をベクトル化して保存"""
        embedding = await self.generate_embedding(content)
        await self.knowledge_db.create({
            "content": content,
            "category": category, 
            "tags": tags,
            "embedding": embedding,
            "created_at": datetime.now()
        })
    
    async def query_knowledge(self, query: str, limit: int = 10):
        """セマンティック検索による知識取得"""
        query_embedding = await self.generate_embedding(query)
        return await self.vector_store.similarity_search(query_embedding, limit)
```

### 2. タスク賢者 (Task Oracle)  
**現在の場所**: `libs/claude_task_tracker.py`

#### 既存機能分析
```python
# 現在の実装（分析結果）
class ClaudeTaskTracker:
    def __init__(self):
        self.db_path = "task_history.db"
        self.tasks = []
    
    # 主要メソッド分析
    def add_task(self, task_data):     # SQLite INSERT
        pass
    def update_task(self, task_id):    # SQLite UPDATE  
        pass
    def get_task_status(self, task_id): # SQLite SELECT
        pass
    def generate_report(self):         # 進捗レポート生成
        pass
```

#### Elder Tree v2 統合設計
```python
class TaskOracleV2(ElderTreeAgent):
    def __init__(self):
        super().__init__("task_oracle")
        self.task_db = SQLModel_Tasks()
        self.dependency_graph = NetworkX_Graph()
    
    async def plan_execution_order(self, tasks: List[Task]):
        """依存関係分析による最適実行順序決定"""
        graph = self.build_dependency_graph(tasks)
        return topological_sort(graph)
    
    async def estimate_workload(self, task: Task):
        """過去データベース分析による工数見積もり"""
        similar_tasks = await self.find_similar_tasks(task)
        return calculate_weighted_average_duration(similar_tasks)
    
    async def monitor_progress(self, task_id: str):
        """リアルタイム進捗監視"""
        return await self.task_db.get_with_metrics(task_id)
```

### 3. インシデント賢者 (Crisis Sage)
**現在の場所**: `libs/incident_manager.py`

#### 現状機能解析
```python
# 既存実装パターン分析
class IncidentManager:
    def detect_incident(self, error):      # エラー検知
        pass
    def escalate_incident(self, incident): # エスカレーション
        pass
    def generate_report(self, incident):   # インシデント報告
        pass
    def learn_from_failure(self, incident): # 失敗学習
        pass
```

#### Elder Tree v2 高度化設計
```python
class CrisisSageV2(ElderTreeAgent):
    def __init__(self):
        super().__init__("crisis_sage")
        self.incident_db = SQLModel_Incidents() 
        self.ml_predictor = IncidentPredictor()  # ML予測モデル
        self.alert_system = PrometheusAlerter()
    
    async def predict_incident_probability(self, context: Dict):
        """機械学習による障害予測"""
        features = extract_features(context)
        return await self.ml_predictor.predict_probability(features)
    
    async def auto_remediation(self, incident: Incident):
        """既知パターンの自動修復"""
        remediation_plan = await self.find_remediation_pattern(incident)
        if remediation_plan.confidence > 0.8:
            return await self.execute_remediation(remediation_plan)
        else:
            return await self.escalate_to_human(incident)
```

### 4. RAG賢者 (Search Mystic)
**現在の場所**: `libs/enhanced_rag_manager.py`

#### 既存アーキテクチャ分析
```python
# 現在の実装分析
class EnhancedRAGManager:
    def __init__(self):
        self.vector_store = None  # 未実装？
        self.embedding_model = None
    
    def search_documents(self, query):    # ドキュメント検索
        pass
    def generate_answer(self, context):   # 回答生成
        pass
```

#### Elder Tree v2 強化設計
```python
class SearchMysticV2(ElderTreeAgent):
    def __init__(self):
        super().__init__("search_mystic")
        self.vector_db = ChromaDB()
        self.hybrid_search = BM25_ElasticSearch()  # ハイブリッド検索
        self.reranker = CrossEncoder_Reranker()
    
    async def hybrid_search(self, query: str, filters: Dict):
        """ベクトル検索 + キーワード検索のハイブリッド"""
        vector_results = await self.vector_search(query)
        keyword_results = await self.keyword_search(query, filters)
        
        # 結果のマージ・リランキング
        merged_results = merge_search_results(vector_results, keyword_results)
        return await self.reranker.rerank(query, merged_results)
    
    async def context_aware_generation(self, query: str, search_results: List):
        """コンテキスト理解型回答生成"""
        context = build_context_window(search_results)
        return await self.llm.generate(
            prompt=f"Context: {context}\\n\\nQuestion: {query}\\n\\nAnswer:",
            max_tokens=1000
        )
```

## 🗺️ データ移行マッピング表

### ナレッジベース移行マッピング
| 現在のファイル | 移行先テーブル | 処理方法 | 優先度 |
|--------------|-------------|---------|-------|
| CLAUDE.md | knowledge_base.core_teachings | パース後構造化 | P0 |
| failures/*.md | incidents.failure_logs | Markdown→JSON | P1 |
| *.md (ガイド類) | knowledge_base.guides | カテゴリ分類 | P2 |
| 未構造化テキスト | knowledge_base.unstructured | 埋め込み化 | P3 |

### タスクデータ移行マッピング
```sql
-- 既存 SQLite → PostgreSQL移行SQL例
INSERT INTO elder_tree.tasks (
    id, title, description, status, priority, 
    created_at, updated_at, assigned_sage
)
SELECT 
    task_id, task_title, task_desc, task_status, priority_level,
    created_date, modified_date, 'task_oracle'
FROM legacy_tasks.claude_tasks;
```

## 🔧 インターフェース設計仕様

### 統一API仕様
```python
# 全賢者共通のベースインターフェース
class ElderSageInterface(ABC):
    @abstractmethod
    async def process_request(self, request: SageRequest) -> SageResponse:
        """賢者への要求処理"""
        pass
    
    @abstractmethod  
    async def collaborate_with_sages(self, other_sages: List[ElderSage]) -> CollaborationResult:
        """他の賢者との協調処理"""
        pass
    
    @abstractmethod
    async def update_knowledge(self, learning_data: Dict) -> bool:
        """学習データによる知識更新"""
        pass
```

### Elder Tree統合エンドポイント
```python
# FastAPI統合例
@app.post("/api/v2/sages/consult")
async def consult_four_sages(request: ConsultationRequest):
    \"\"\"4賢者への一括相談API\"\"\"
    results = await asyncio.gather(
        knowledge_sage.process_request(request),
        task_oracle.process_request(request),
        crisis_sage.process_request(request), 
        search_mystic.process_request(request)
    )
    
    return FourSagesResponse(
        knowledge_insight=results[0],
        task_recommendation=results[1],
        risk_assessment=results[2],
        search_results=results[3],
        synthesized_advice=synthesize_advice(results)
    )
```

## 📊 移行実装計画

### Phase 1.1: データ構造解析（4時間）
- [ ] 既存4賢者の全機能・データ構造詳細分析
- [ ] Elder Tree v2 APIスペック詳細設計
- [ ] データ互換性検証・変換仕様策定
- [ ] 移行リスク評価・対策立案

### Phase 1.2: プロトタイプ実装（8時間）
- [ ] 各賢者のElderTreeAgent基底クラス継承版実装
- [ ] データ移行スクリプト作成・テスト
- [ ] API統合テスト実装
- [ ] パフォーマンステスト実施

### Phase 1.3: 統合テスト（4時間）
- [ ] 4賢者協調動作テスト
- [ ] 既存機能互換性テスト  
- [ ] データ整合性検証
- [ ] ロールバック手順確認

## 🧪 テスト戦略

### 機能互換性テスト
```python
@pytest.mark.migration
class TestFourSagesMigration:
    
    async def test_knowledge_sage_compatibility(self):
        \"\"\"ナレッジ賢者の既存機能互換性\"\"\"
        legacy_sage = KnowledgeSageLegacy()
        new_sage = KnowledgeSageV2()
        
        # 同一クエリで同等結果が得られるか
        query = "TDD開発手法について"
        legacy_result = legacy_sage.search(query)
        new_result = await new_sage.query_knowledge(query)
        
        assert semantic_similarity(legacy_result, new_result) > 0.8
    
    async def test_task_oracle_migration(self):
        \"\"\"タスク賢者のデータ移行検証\"\"\"
        # レガシーDBからの移行完全性検証
        legacy_count = get_legacy_task_count()
        migrated_count = await new_task_oracle.get_task_count()
        
        assert legacy_count == migrated_count
```

### パフォーマンステスト
```python
@pytest.mark.performance
async def test_four_sages_response_time():
    \"\"\"4賢者協調処理のレスポンス時間\"\"\"
    start_time = time.time()
    
    result = await consult_four_sages(ConsultationRequest(
        query="緊急バグ修正のタスク計画立案",
        priority="high"
    ))
    
    response_time = time.time() - start_time
    assert response_time < 3.0  # 3秒以内の応答
    assert result.synthesized_advice is not None
```

## 📋 成果物チェックリスト

### ドキュメント成果物
- [ ] 4賢者機能比較マトリクス完成版
- [ ] Elder Tree API仕様書 v2.0
- [ ] データ移行仕様書・手順書
- [ ] 互換性テストレポート

### 実装成果物  
- [ ] 各賢者のElderTreeAgent継承実装
- [ ] データ移行スクリプト一式
- [ ] API統合テストスイート
- [ ] パフォーマンスベンチマーク結果

## 🚨 リスク要因と対策

### 高リスク要因
| リスク | 発生確率 | 影響度 | 対策 |
|-------|---------|-------|------|
| データ移行失敗 | 中 | 高 | バックアップ必須、段階移行 |
| API互換性問題 | 高 | 中 | 後方互換性保持、並行稼働期間 |
| パフォーマンス劣化 | 中 | 高 | ベンチマーク基準設定、最適化 |

### 対策詳細
```bash
# データバックアップスクリプト例
./scripts/backup-legacy-sages.sh
./scripts/migrate-sages-data.sh --dry-run  # テスト移行
./scripts/migrate-sages-data.sh --execute  # 本移行
./scripts/verify-migration.sh             # 検証
```

## 📈 成功基準

### 機能面
- 既存4賢者機能の100%互換性確保
- Elder Tree APIとの完全統合
- 協調動作パターンの3倍向上

### 性能面  
- 応答速度: 現状維持（レスポンス3秒以内）
- メモリ使用量: 20%削減（統合効果）
- 同時処理性能: 5倍向上（非同期化効果）

**工数**: 16時間  
**期間**: 3日間  
**担当**: クロードエルダー  
**レビュアー**: グランドエルダーmaru