# Elders Guild統合アーキテクチャ設計書
## ナレッジ・インシデント統合システム v1.0

### 📋 概要

Elders Guildの知識管理システムとインシデント管理システムを統合し、4賢者システムとの連携を強化する統一アーキテクチャです。

### 🎯 統合目標

1. **統一データモデル**: 知識・インシデント・履歴データの一元管理
2. **統合検索基盤**: RAG Managerによる横断的情報検索
3. **相互学習機能**: インシデントから知識への自動変換
4. **統一API**: 全システム間の標準化された通信インターフェース

---

## 🏗️ アーキテクチャ概要

### システム構成図
```
┌─────────────────────────────────────────────────────────────┐
│                    4賢者統合レイヤー                          │
├─────────────────────────────────────────────────────────────┤
│ ナレッジ賢者  │ タスク賢者   │ インシデント賢者 │ RAG賢者     │
│ Knowledge    │ Task Oracle │ Crisis Sage    │ Search     │
│ Sage         │             │                │ Mystic     │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
┌───────────────▼─┐  ┌──────▼─────┐  ┌──▼──────────────┐
│ 統合RAG Manager │  │ 統合API    │  │ 統合データベース │
│ Enhanced       │  │ Gateway    │  │ Unified DB      │
│ Search Engine  │  │            │  │                │
└───────────────┬─┘  └──────┬─────┘  └──┬──────────────┘
                │           │           │
        ┌───────┼───────────┼───────────┼───────┐
        │       │           │           │       │
┌───────▼─┐ ┌───▼───┐ ┌─────▼───┐ ┌─────▼─┐ ┌──▼───┐
│Knowledge│ │Task   │ │Incident │ │Worker │ │Legacy│
│Base     │ │History│ │Database │ │Status │ │Files │
│Files    │ │SQLite │ │SQLite   │ │SQLite │ │      │
└─────────┘ └───────┘ └─────────┘ └───────┘ └──────┘
```

---

## 📊 統合データモデル

### 1. 統一エンティティ構造

#### BaseEntity (基底エンティティ)
```json
{
  "id": "string",
  "type": "knowledge|incident|task|worker",
  "title": "string",
  "content": "string",
  "metadata": {
    "created_at": "datetime",
    "updated_at": "datetime",
    "created_by": "string",
    "tags": ["string"],
    "category": "string",
    "priority": "low|medium|high|critical",
    "status": "active|archived|deprecated"
  },
  "relationships": {
    "related_entities": ["entity_id"],
    "dependencies": ["entity_id"],
    "derived_from": "entity_id"
  },
  "search_metadata": {
    "keywords": ["string"],
    "embedding_vector": [float],
    "indexed_content": "string"
  }
}
```

#### KnowledgeEntity (知識エンティティ)
```json
{
  "base": "BaseEntity",
  "knowledge_specific": {
    "source_type": "document|experience|analysis|automated",
    "confidence_score": 0.95,
    "verification_status": "verified|pending|deprecated",
    "usage_count": 42,
    "effectiveness_rating": 4.5,
    "domain": "system|development|operations|incident"
  }
}
```

#### IncidentEntity (インシデントエンティティ)
```json
{
  "base": "BaseEntity",
  "incident_specific": {
    "severity": "low|medium|high|critical",
    "status": "open|investigating|resolved|closed",
    "affected_systems": ["system_name"],
    "resolution_steps": ["string"],
    "root_cause": "string",
    "lessons_learned": ["string"],
    "auto_generated_knowledge": "knowledge_entity_id"
  }
}
```

### 2. 統合データベーススキーマ

#### entities テーブル
```sql
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    metadata JSON,
    relationships JSON,
    search_metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_tags ON entities(json_extract(metadata, '$.tags'));
CREATE INDEX idx_entities_status ON entities(json_extract(metadata, '$.status'));
```

#### entity_relationships テーブル
```sql
CREATE TABLE entity_relationships (
    source_id TEXT,
    target_id TEXT,
    relationship_type TEXT,
    weight REAL DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_id, target_id, relationship_type)
);
```

#### search_index テーブル
```sql
CREATE TABLE search_index (
    entity_id TEXT PRIMARY KEY,
    content_vector BLOB,
    keywords TEXT,
    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);
```

---

## 🔍 統合検索システム

### EnhancedRAGManager 設計

```python
class UnifiedRAGManager:
    """統合RAG検索エンジン"""
    
    def __init__(self):
        self.vector_store = VectorStoreManager()
        self.entity_db = UnifiedEntityDatabase()
        self.search_preprocessor = SearchPreprocessor()
        self.context_assembler = ContextAssembler()
    
    async def unified_search(self, query: str, filters: Dict = None) -> SearchResult:
        """統合検索機能"""
        # 1. クエリ前処理
        processed_query = self.search_preprocessor.process(query)
        
        # 2. ベクトル検索
        vector_results = await self.vector_store.similarity_search(
            processed_query.embedding, 
            filters=filters
        )
        
        # 3. 関係性検索
        related_entities = await self.entity_db.find_related_entities(
            vector_results, 
            relationship_types=['derived_from', 'related_to']
        )
        
        # 4. コンテキスト組み立て
        context = self.context_assembler.assemble(
            vector_results, 
            related_entities,
            processed_query.intent
        )
        
        return SearchResult(
            primary_results=vector_results,
            related_entities=related_entities,
            assembled_context=context,
            confidence_score=self._calculate_confidence(context)
        )
```

### 検索機能仕様

#### 1. 横断検索
- **知識ベース**: ファイルベース知識の全文検索
- **インシデント履歴**: 過去の問題・解決策検索
- **タスク履歴**: 実行されたタスクの検索
- **ワーカー状態**: 現在のシステム状態検索

#### 2. 関係性検索
- **原因-結果関係**: インシデント→解決策→知識の追跡
- **類似性検索**: 類似問題・解決策の発見
- **時系列追跡**: 時間軸での関連性発見

#### 3. 意図理解検索
- **問題解決**: 「〜でエラーが出る」→解決策提示
- **知識獲得**: 「〜について教えて」→関連知識提示
- **履歴参照**: 「前回の〜」→過去の記録検索

---

## 🚀 統合API設計

### APIエンドポイント構成

#### 1. Entity Management API
```
POST   /api/v1/entities                    # エンティティ作成
GET    /api/v1/entities/{id}               # エンティティ取得
PUT    /api/v1/entities/{id}               # エンティティ更新
DELETE /api/v1/entities/{id}               # エンティティ削除
GET    /api/v1/entities                    # エンティティ一覧
```

#### 2. Search API
```
POST   /api/v1/search/unified              # 統合検索
POST   /api/v1/search/knowledge            # 知識検索
POST   /api/v1/search/incidents            # インシデント検索
POST   /api/v1/search/relationships        # 関係性検索
```

#### 3. Knowledge API
```
POST   /api/v1/knowledge/create            # 知識作成
POST   /api/v1/knowledge/from-incident     # インシデントから知識生成
GET    /api/v1/knowledge/recommendations   # 知識推薦
```

#### 4. Incident API
```
POST   /api/v1/incidents/create            # インシデント作成
POST   /api/v1/incidents/{id}/resolve      # インシデント解決
POST   /api/v1/incidents/{id}/learn        # 学習データ抽出
```

### API認証・認可
```python
class UnifiedAPIAuth:
    """統合API認証システム"""
    
    def __init__(self):
        self.sage_permissions = {
            'knowledge_sage': ['knowledge:*', 'search:*'],
            'task_oracle': ['tasks:*', 'entities:read'],
            'crisis_sage': ['incidents:*', 'alerts:*'],
            'search_mystic': ['search:*', 'relationships:*']
        }
    
    def authorize_sage(self, sage_type: str, action: str) -> bool:
        """4賢者システムの認可チェック"""
        permissions = self.sage_permissions.get(sage_type, [])
        return any(self._match_permission(perm, action) for perm in permissions)
```

---

## 🔄 相互学習システム

### 1. インシデント→知識変換

```python
class IncidentToKnowledgeConverter:
    """インシデントから知識への自動変換"""
    
    async def convert_incident(self, incident: IncidentEntity) -> KnowledgeEntity:
        """インシデントを知識エンティティに変換"""
        
        # 1. 解決パターン抽出
        resolution_pattern = self._extract_resolution_pattern(incident)
        
        # 2. 一般化可能性評価
        generalizability = self._evaluate_generalizability(incident)
        
        # 3. 知識品質スコア算出
        quality_score = self._calculate_knowledge_quality(
            incident, resolution_pattern, generalizability
        )
        
        if quality_score > 0.7:  # 閾値以上で知識化
            knowledge = KnowledgeEntity(
                title=f"解決策: {incident.title}",
                content=self._generate_knowledge_content(incident),
                knowledge_specific={
                    'source_type': 'automated',
                    'confidence_score': quality_score,
                    'domain': 'incident',
                    'verification_status': 'pending'
                }
            )
            
            # 関係性設定
            knowledge.relationships['derived_from'] = incident.id
            
            return knowledge
        
        return None
```

### 2. 知識有効性フィードバック

```python
class KnowledgeEffectivenessTracker:
    """知識の有効性追跡システム"""
    
    def track_usage(self, knowledge_id: str, context: Dict):
        """知識使用時の追跡"""
        self.usage_db.record_usage(
            knowledge_id=knowledge_id,
            context=context,
            timestamp=datetime.now()
        )
    
    def update_effectiveness(self, knowledge_id: str, outcome: bool):
        """知識の有効性更新"""
        current_rating = self.get_effectiveness_rating(knowledge_id)
        new_rating = self._calculate_new_rating(current_rating, outcome)
        
        self.entity_db.update_knowledge_effectiveness(
            knowledge_id, new_rating
        )
        
        # 低有効性知識の自動非推奨化
        if new_rating < 0.3:
            self._deprecate_knowledge(knowledge_id)
```

---

## 🔧 実装フェーズ

### Phase 1: 基盤構築 (1-2週間)

#### 1.1 統合データベース構築
- [ ] 統一エンティティスキーマ実装
- [ ] データマイグレーションスクリプト作成
- [ ] バックアップ・復元機能実装

#### 1.2 統合APIゲートウェイ
- [ ] 基本API構造実装
- [ ] 認証・認可システム実装
- [ ] APIドキュメント生成

#### 1.3 基本検索機能
- [ ] ベクトル検索基盤構築
- [ ] 基本的な統合検索実装
- [ ] 検索インデックス構築

### Phase 2: コア統合 (2-3週間)

#### 2.1 4賢者システム統合
- [ ] 各賢者の統合API接続
- [ ] 賢者間通信プロトコル実装
- [ ] 統合意思決定メカニズム

#### 2.2 高度検索機能
- [ ] 関係性検索実装
- [ ] 意図理解機能追加
- [ ] コンテキスト組み立て機能

#### 2.3 相互学習システム
- [ ] インシデント→知識変換実装
- [ ] 知識有効性追跡システム
- [ ] 自動改善メカニズム

### Phase 3: 高度機能 (3-4週間)

#### 3.1 インテリジェント機能
- [ ] 予測的問題検出
- [ ] 自動知識推薦
- [ ] 学習パターン分析

#### 3.2 統合ダッシュボード
- [ ] リアルタイム統合ビュー
- [ ] 知識・インシデント分析画面
- [ ] システム健全性監視

#### 3.3 最適化・チューニング
- [ ] パフォーマンス最適化
- [ ] インデックス最適化
- [ ] キャッシュ戦略実装

---

## 📊 成功指標

### 技術指標
- **検索精度**: 85%以上の関連結果返却
- **応答時間**: 検索レスポンス500ms以下
- **システム統合率**: 既存システム95%以上統合
- **データ整合性**: 99.9%以上のデータ一貫性

### ビジネス指標
- **問題解決時間**: 50%短縮
- **知識再利用率**: 70%以上
- **インシデント再発率**: 30%削減
- **システム稼働率**: 99.5%以上

### 品質指標
- **知識品質スコア**: 平均4.0以上
- **有効性検証率**: 90%以上
- **自動化率**: 80%以上の処理自動化

---

## 🛡️ リスク管理

### 技術リスク
1. **データ移行リスク**: 段階的移行、ロールバック戦略
2. **パフォーマンスリスク**: 負荷テスト、キャパシティ計画
3. **互換性リスク**: 後方互換性維持、段階的移行

### 運用リスク
1. **サービス停止リスク**: 無停止デプロイ、フェイルオーバー
2. **データ損失リスク**: リアルタイムバックアップ、冗長化
3. **学習精度リスク**: 人間による検証、フィードバックループ

---

## 🎯 期待効果

### 短期効果 (1-3ヶ月)
- システム間データ統合完了
- 検索機能の大幅改善
- インシデント対応時間短縮

### 中期効果 (3-6ヶ月)
- 自動学習システム稼働
- 知識蓄積の加速
- 予測的問題検出開始

### 長期効果 (6ヶ月以上)
- 自律的システム進化
- 人工知能的問題解決
- 運用コスト大幅削減

---

## 📚 参考資料

- [4賢者システム仕様](../libs/four_sages_integration.py)
- [既存RAG Manager](../libs/rag_manager.py)
- [インシデント管理システム](../libs/incident_manager.py)
- [現在の知識ベース構造](../knowledge_base/)

---

**最終更新**: 2025年7月6日  
**設計者**: Claude Code Assistant  
**承認者**: Elders Guild Elders Council  
**バージョン**: 1.0  