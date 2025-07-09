# 🏛️ Session Context Manager 設計仕様書

**仕様書ID**: SCM_DESIGN_SPEC_20250708  
**承認**: 4賢者評議会承認済み  
**実装期間**: Week 1-2 (Phase A)  
**目標**: 80%コストカット実現の核心機能

---

## 🎯 **設計承認内容**

### **アーキテクチャ承認**
- **レイヤー構造**: API → Logic → Storage → Integration の4層設計
- **統合方式**: 4賢者システムとの完全統合
- **データ構造**: SessionContext dataclass + 多層ストレージ

### **技術スタック承認**
- **言語**: Python 3.8+
- **ストレージ**: SQLite + JSON + Vector (FAISS)
- **セキュリティ**: AES-256-GCM暗号化
- **監視**: Prometheus + Grafana

## 📚 **ナレッジ賢者承認事項**

### **知識永続化戦略**
```
P0 (最重要): タスク実行結果、エラー解決パターン、成功事例
P1 (重要): ユーザー設定、プロジェクト理解、頻繁参照知識
P2 (標準): コード断片、分析結果、中間成果物
```

### **データ構造設計**
```python
@dataclass
class SessionContext:
    session_id: str
    created_at: datetime
    updated_at: datetime
    user_id: str
    project_path: str
    
    # 構造化データ
    tasks: List[Dict[str, Any]]
    knowledge_graph: Dict[str, Any]
    error_patterns: List[Dict[str, Any]]
    success_patterns: List[Dict[str, Any]]
    
    # 4賢者データ
    sage_interactions: Dict[str, int]
    performance_metrics: Dict[str, float]
    
    # 圧縮・要約
    summary: str
    key_insights: List[str]
    vector_embeddings: Optional[List[float]]
```

## 📋 **タスク賢者承認事項**

### **実装スケジュール**
```
Week 1:
- Day 1-2: 基本データモデルとストレージ層（TDD）
- Day 3-4: CRUD API実装と基本テスト
- Day 5: 4賢者統合インターフェース

Week 2:
- Day 1-2: 圧縮・要約機能実装
- Day 3-4: RAG統合とベクトル検索
- Day 5: パフォーマンス最適化と統合テスト
```

### **品質保証基準**
```yaml
quality_gates:
  unit_test_coverage: 95%
  integration_test_coverage: 85%
  performance_benchmarks:
    create_session: < 100ms
    search_latency_p95: < 500ms
    memory_per_session: < 10MB
```

## 🚨 **インシデント賢者承認事項**

### **セキュリティ設計**
```python
class SecurityLayer:
    # AES-256-GCM暗号化
    def encrypt_sensitive_data(self, data: Dict) -> bytes
    
    # RBACベース権限チェック
    def check_permissions(self, user_id: str, session_id: str) -> bool
    
    # 改ざん防止監査ログ
    def audit_log(self, action: str, user_id: str, details: Dict)
```

### **監視・アラート設計**
```python
ALERTS = {
    'high_corruption_rate': 'rate(context_corruption_total[5m]) > 0.01',
    'memory_pressure': 'memory_usage_mb > 1000',
    'slow_queries': 'histogram_quantile(0.95, search_query_time) > 1.0',
}
```

## 🔍 **RAG賢者承認事項**

### **ベクトル化戦略**
```python
class ContextRAG:
    def vectorize_context(self, context: SessionContext) -> np.ndarray:
        text_vector = self.embedder.encode(context.summary)
        task_vector = self.encode_tasks(context.tasks)
        pattern_vector = self.encode_patterns(context.patterns)
        
        # 重み付き結合: text(40%) + task(30%) + pattern(30%)
        return np.concatenate([
            text_vector * 0.4,
            task_vector * 0.3,
            pattern_vector * 0.3
        ])
```

### **圧縮戦略**
```python
# 段階的圧縮: 80-90%圧縮率目標
strategies = [
    self.remove_redundant_data,
    self.summarize_conversations, 
    self.extract_key_decisions,
    self.compress_code_snippets,
]
```

## 🏛️ **4賢者統合設計**

### **協調フロー**
```python
async def process_with_four_sages(self, context: SessionContext):
    # 1. ナレッジ賢者: 知識抽出・保存
    knowledge = await self.knowledge_sage.extract_insights(context)
    
    # 2. タスク賢者: タスク管理・優先順位  
    tasks = await self.task_oracle.analyze_tasks(context)
    
    # 3. インシデント賢者: リスク分析・対策
    risks = await self.crisis_sage.assess_risks(context)
    
    # 4. RAG賢者: 関連情報検索・統合
    related = await self.search_mystic.find_related(context)
    
    return context
```

## 🚀 **API設計仕様**

### **RESTful API**
```python
# セッション管理
POST   /api/sessions                    # 新規作成
GET    /api/sessions/{id}              # 取得
PUT    /api/sessions/{id}              # 更新
DELETE /api/sessions/{id}              # 削除

# 高度な操作
POST   /api/sessions/{id}/compress     # 圧縮
POST   /api/sessions/merge             # マージ
GET    /api/sessions/search            # 検索
POST   /api/sessions/{id}/evolve       # 知識進化

# 4賢者統合
POST   /api/sessions/{id}/sync-knowledge    # ナレッジ同期
POST   /api/sessions/{id}/analyze-incidents # インシデント分析
GET    /api/sessions/{id}/similar           # 類似検索
```

### **Python API**
```python
class SessionContextManager:
    # 基本操作
    async def create_session(self, user_id: str, project_path: str) -> SessionContext
    async def load_session(self, session_id: str) -> SessionContext
    async def save_session(self, context: SessionContext) -> bool
    
    # 知識統合
    async def merge_contexts(self, contexts: List[SessionContext]) -> SessionContext
    async def extract_patterns(self, context: SessionContext) -> Dict[str, Any]
    async def evolve_knowledge(self, context: SessionContext) -> None
    
    # 4賢者統合
    async def sync_with_knowledge_base(self, context: SessionContext) -> None
    async def update_task_tracker(self, context: SessionContext) -> None
    async def analyze_incidents(self, context: SessionContext) -> List[Dict]
```

## 📁 **実装ファイル構成**

```
libs/session_management/
├── __init__.py
├── session_context_manager.py      # メインクラス
├── models.py                       # データモデル
├── storage.py                      # ストレージ層
├── compression.py                  # 圧縮・要約
├── security.py                     # セキュリティ層
├── rag_integration.py              # RAG統合
└── four_sages_integration.py       # 4賢者統合

tests/unit/session_management/
├── test_session_context_manager.py # メインテスト
├── test_models.py                  # データモデルテスト
├── test_storage.py                 # ストレージテスト
├── test_compression.py             # 圧縮テスト
├── test_security.py                # セキュリティテスト
├── test_rag_integration.py         # RAG統合テスト
└── test_four_sages_integration.py  # 4賢者統合テスト
```

## ✅ **評議会承認確認**

- [x] **技術設計**: 4賢者総合承認
- [x] **実装計画**: Week 1-2スケジュール承認
- [x] **品質基準**: 95%テストカバレッジ・パフォーマンス基準承認
- [x] **セキュリティ**: AES-256暗号化・RBAC承認
- [x] **統合方式**: 4賢者システム統合方式承認

## 🎯 **次回セッション継続ポイント**

1. **Week 1 Day 1実装開始**: データモデル・ストレージ層実装
2. **TDD環境準備**: テスト自動化・CI/CD設定
3. **4賢者統合テスト**: 既存システムとの統合確認
4. **Auto Context Compressor設計**: 次期機能の4賢者相談

---

**🏛️ エルダー評議会最終承認済み**  
**🧙‍♂️ 4賢者技術仕様確定済み**  
**🚀 実装開始準備完了**  
**文書ID**: SCM_DESIGN_SPEC_20250708