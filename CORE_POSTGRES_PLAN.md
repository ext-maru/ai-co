# 🐘 CorePostgres計画 - エルダーズギルド知識統合プロジェクト

## 📋 プロジェクト概要

### ミッション
エルダーズギルドの膨大な知識を PostgreSQL MCP に統合し、コンテキストロストを防ぎながら、知識の永続化・検索性・学習性を実現する

### ビジョン
「すべての知識が生き、つながり、進化する」統合知識管理システム

### 成功指標
- 知識検索時間: 90%削減
- コンテキスト保持率: 100%
- 新人オンボーディング: 2週間→3日
- 知識の自動進化: 月10件以上

## 🎯 フェーズ別実装計画

### Phase 0: 準備・環境構築（Week 1）

#### 0.1 PostgreSQL MCP環境準備
```bash
# 必要な環境
- PostgreSQL 15以上
- pgvector拡張
- pg_trgm（日本語全文検索）
- MCP接続ライブラリ
```

#### 0.2 スキーマ設計
```sql
-- コアスキーマ
CREATE SCHEMA elders_guild;
CREATE SCHEMA knowledge_base;
CREATE SCHEMA task_management;
CREATE SCHEMA incident_tracking;
CREATE SCHEMA rag_system;
```

#### 0.3 4賢者統合準備
- 各賢者のMCP接続インターフェース実装
- エラーハンドリング機構
- フォールバック（SQLite）準備

### Phase 1: 基礎知識移行（Week 2-3）

#### 1.1 最重要ドキュメント移行
優先順位：
1. CLAUDE.md（憲法）
2. TDD_GUIDE.md
3. COSTAR_FRAMEWORK.md
4. fantasy_classification_system.md
5. incident_management/*.md

#### 1.2 知識構造の実装
```sql
-- 基本テーブル
CREATE TABLE knowledge_base.documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT[],
    priority INTEGER DEFAULT 5,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    search_vector tsvector
);

-- メタデータ
CREATE TABLE knowledge_base.metadata (
    document_id INTEGER REFERENCES documents(id),
    key VARCHAR(100),
    value JSONB,
    PRIMARY KEY (document_id, key)
);

-- 関連性
CREATE TABLE knowledge_base.relations (
    source_id INTEGER REFERENCES documents(id),
    target_id INTEGER REFERENCES documents(id),
    relation_type VARCHAR(50),
    strength FLOAT DEFAULT 0.5,
    discovered_at TIMESTAMP DEFAULT NOW()
);
```

#### 1.3 移行スクリプト開発
```python
# libs/knowledge_migration.py
class KnowledgeMigrator:
    def __init__(self, mcp_connection):
        self.mcp = mcp_connection
        self.stats = MigrationStats()

    async def migrate_markdown_files(self, directory: str):
        """Markdownファイルを段階的に移行"""
        pass

    async def validate_migration(self):
        """移行データの整合性チェック"""
        pass
```

### Phase 2: 4賢者統合（Week 4-5）

#### 2.1 ナレッジ賢者の統合
```python
# libs/knowledge_sage_mcp.py
class KnowledgeSageMCP:
    async def store_knowledge(self, content, metadata):
        """知識の永続化"""

    async def retrieve_context(self, task_description):
        """タスクに関連する知識の取得"""

    async def update_knowledge_graph(self):
        """知識グラフの自動更新"""
```

#### 2.2 タスク賢者の統合
```python
# libs/task_sage_mcp.py
class TaskSageMCP:
    async def create_task_with_context(self, task_data):
        """コンテキスト付きタスク作成"""

    async def get_task_knowledge(self, task_id):
        """タスクに必要な知識を自動取得"""
```

#### 2.3 インシデント賢者の統合
```python
# libs/incident_sage_mcp.py
class IncidentSageMCP:
    async def record_incident_with_context(self, incident):
        """インシデントと関連知識の記録"""

    async def get_resolution_patterns(self, error_pattern):
        """過去の解決パターンを検索"""
```

#### 2.4 RAG賢者の統合
```python
# libs/rag_sage_mcp.py
class RAGSageMCP:
    async def semantic_search(self, query, limit=10):
        """pgvectorを使った意味検索"""

    async def generate_embeddings(self, text):
        """テキストの埋め込みベクトル生成"""
```

### Phase 3: 検索・分析基盤（Week 6-7）

#### 3.1 全文検索の実装
```sql
-- 日本語対応全文検索
CREATE INDEX idx_documents_search
ON knowledge_base.documents
USING gin(search_vector);

-- 検索関数
CREATE FUNCTION search_knowledge(query TEXT, limit_count INT DEFAULT 10)
RETURNS TABLE(id INT, title TEXT, content TEXT, rank FLOAT)
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.title,
        d.content,
        ts_rank(d.search_vector, plainto_tsquery('japanese', query)) as rank
    FROM knowledge_base.documents d
    WHERE d.search_vector @@ plainto_tsquery('japanese', query)
    ORDER BY rank DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
```

#### 3.2 ベクトル検索の実装
```sql
-- pgvector設定
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE knowledge_base.documents
ADD COLUMN embedding vector(1536);

CREATE INDEX idx_documents_embedding
ON knowledge_base.documents
USING ivfflat (embedding vector_cosine_ops);
```

#### 3.3 ハイブリッド検索
```python
class HybridSearch:
    async def search(self, query: str, use_semantic=True, use_keyword=True):
        """キーワード検索とセマンティック検索の組み合わせ"""
        results = []

        if use_keyword:
            keyword_results = await self.keyword_search(query)
            results.extend(keyword_results)

        if use_semantic:
            semantic_results = await self.semantic_search(query)
            results.extend(semantic_results)

        return self.merge_and_rank(results)
```

### Phase 4: 自動化・学習システム（Week 8-9）

#### 4.1 知識の自動更新
```python
# libs/knowledge_evolution_mcp.py
class KnowledgeEvolution:
    async def detect_outdated_knowledge(self):
        """古い知識の検出"""

    async def suggest_updates(self, document_id):
        """更新提案の生成"""

    async def auto_link_related_knowledge(self):
        """関連知識の自動リンク"""
```

#### 4.2 使用パターン学習
```sql
-- 使用履歴記録
CREATE TABLE knowledge_base.usage_history (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    user_id VARCHAR(100),
    action VARCHAR(50),
    context JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- 人気度スコア計算
CREATE VIEW knowledge_base.popularity_scores AS
SELECT
    document_id,
    COUNT(*) as view_count,
    AVG(CASE WHEN action = 'helpful' THEN 1 ELSE 0 END) as helpfulness
FROM usage_history
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY document_id;
```

#### 4.3 知識品質管理
```python
class KnowledgeQualityManager:
    async def assess_quality(self, document_id):
        """知識の品質評価"""
        criteria = {
            'completeness': self.check_completeness,
            'accuracy': self.check_accuracy,
            'relevance': self.check_relevance,
            'clarity': self.check_clarity
        }

    async def auto_improve(self, document_id):
        """AIによる自動改善提案"""
```

### Phase 5: UI/UX・ツール統合（Week 10-11）

#### 5.1 CLI統合
```bash
# 新しいコマンド
ai-knowledge search "TDD best practices"
ai-knowledge add "新しい知識" --category "testing"
ai-knowledge relate doc1 doc2 --type "prerequisite"
ai-knowledge stats --last-7-days
```

#### 5.2 VSCode拡張
```typescript
// VSCode拡張機能
class ElderGuildKnowledgeExtension {
    async provideCompletionItems(document, position) {
        // コーディング中に関連知識をサジェスト
        const context = this.getContext(document, position);
        const suggestions = await this.mcp.getSuggestions(context);
        return this.formatCompletions(suggestions);
    }
}
```

#### 5.3 Web ダッシュボード
```python
# web/knowledge_dashboard.py
class KnowledgeDashboard:
    def __init__(self):
        self.routes = [
            ('/search', self.search_page),
            ('/graph', self.knowledge_graph),
            ('/analytics', self.usage_analytics),
            ('/quality', self.quality_metrics)
        ]
```

### Phase 6: 監視・最適化（Week 12）

#### 6.1 パフォーマンス監視
```sql
-- スロークエリ監視
CREATE TABLE monitoring.slow_queries (
    id SERIAL PRIMARY KEY,
    query TEXT,
    duration_ms INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- インデックス使用状況
CREATE VIEW monitoring.index_usage AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

#### 6.2 自動最適化
```python
class PerformanceOptimizer:
    async def analyze_query_patterns(self):
        """クエリパターンの分析"""

    async def suggest_indexes(self):
        """インデックス提案"""

    async def optimize_table_structure(self):
        """テーブル構造の最適化"""
```

## 📊 リスク管理計画

### 技術リスク
| リスク | 影響度 | 対策 |
|--------|--------|------|
| MCP接続障害 | 高 | SQLiteフォールバック実装 |
| データ移行失敗 | 高 | 段階的移行・ロールバック準備 |
| パフォーマンス劣化 | 中 | インデックス最適化・キャッシュ |
| セキュリティ脆弱性 | 高 | 権限管理・暗号化実装 |

### 組織リスク
| リスク | 影響度 | 対策 |
|--------|--------|------|
| SQL学習抵抗 | 中 | 研修実施・ラッパーツール提供 |
| 過度な依存 | 中 | ベストプラクティス文書化 |
| 知識の形式化疲れ | 低 | 自動化ツール提供 |

## 🎯 成功基準

### 定量的指標
- 知識検索レスポンス: < 0.5秒
- システム稼働率: > 99.9%
- 知識カバレッジ: > 95%
- ユーザー満足度: > 90%

### 定性的指標
- チーム全員がMCPを日常的に使用
- 新人が3日で独立して作業可能
- 知識の自発的な追加・更新が発生
- 他プロジェクトからの利用要望

## 📅 マイルストーン

| Phase | 期間 | 成果物 | 完了基準 |
|-------|------|--------|----------|
| 0 | Week 1 | 環境構築完了 | MCP接続成功 |
| 1 | Week 2-3 | 基礎知識移行 | 50文書以上移行 |
| 2 | Week 4-5 | 4賢者統合 | 全賢者MCP対応 |
| 3 | Week 6-7 | 検索基盤 | 検索精度90%以上 |
| 4 | Week 8-9 | 自動化 | 日次自動更新稼働 |
| 5 | Week 10-11 | ツール統合 | CLI/VSCode対応 |
| 6 | Week 12 | 最適化 | 性能目標達成 |

## 🚀 開始条件チェックリスト

- [ ] PostgreSQL 15以上のMCP環境準備完了
- [ ] pgvector拡張インストール可能
- [ ] バックアップ・リカバリ体制確立
- [ ] チーム全員への計画説明完了
- [ ] Phase 0の詳細タスク分解完了
- [ ] リスク対策の事前準備完了

## 📝 次のアクション

1. このプランのレビューと承認
2. PostgreSQL MCP環境の調達
3. Phase 0の詳細設計書作成
4. キックオフミーティングの開催
5. 週次進捗レビュー体制の確立

---

*CorePostgres計画 - エルダーズギルドの知識を永遠に*
