# Enhanced Elder Servant Base Classes

Elder Tree分散AIアーキテクチャ用の統合基底クラス群

## 概要

このモジュールは、Elder Tree分散AIアーキテクチャの中核を成す32専門AIサーバント実装のための統合基底クラスを提供します。

## 主要コンポーネント

### 1. EnhancedElderServant（統合基底クラス）

Elder Tree分散実装の要件をすべて満たす統合基底クラス

**統合機能:**
- ✅ EldersLegacy品質基準とメトリクス
- ✅ BaseSoul A2A通信とプロセス管理  
- ✅ 4賢者システム連携インターフェース
- ✅ インシデント騎士団予防的デバッグ
- ✅ 分散処理・負荷分散・ヘルスチェック
- ✅ Iron Will品質ゲート自動検証
- ✅ 継続学習・自動進化システム
- ✅ リアルタイム監視・メトリクス収集

### 2. 専門特化サーバント基底クラス

#### DwarfWorkshopServant（🔨 開発・製作）
- コード実装・生成
- テスト作成・実行
- API設計・開発
- デプロイメント・CI/CD

#### RAGWizardServant（🧙‍♂️ 調査・研究）
- データマイニング・収集
- 技術調査・提案
- パターン解析
- 洞察生成・予測

#### ElfForestServant（🧝‍♂️ 監視・メンテナンス）
- 品質監視・保証
- パフォーマンス監視・最適化
- リソース最適化・管理
- 自動修復・ヒーリング

#### IncidentKnightServant（⚔️ 緊急対応）
- コマンド検証・実行前チェック
- 静的・動的解析
- 自動修復・問題解決
- インシデント対応

## 使用方法

### 基本的な使用例

```python
from libs.elder_servants.base.enhanced_elder_servant import (
    EnhancedElderServant,
    ServantSpecialization,
    ServantTier
)

class MyCustomServant(EnhancedElderServant[Dict[str, Any], Dict[str, Any]]):
    """カスタムサーバント実装例"""
    
    def __init__(self):
        super().__init__(
            servant_id="my_servant_001",
            servant_name="My Custom Servant",
            specialization=ServantSpecialization.IMPLEMENTATION,
            tier=ServantTier.EXPERT
        )
    
    async def _execute_specialized_task(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """専門タスク実装"""
        # あなたのロジックをここに実装
        return {"status": "completed", "result": "success"}
    
    def get_specialized_capabilities(self) -> List[str]:
        """専門能力定義"""
        return ["custom_implementation", "specialized_processing"]

# サーバント使用
servant = MyCustomServant()
result = await servant.process_request({"task": "example"})
```

### 専門特化サーバント使用例

```python
from libs.elder_servants.base.specialized_elder_servants import (
    SpecializedServantFactory,
    ServantSpecialization
)

# ドワーフ工房サーバント作成
dwarf_servant = SpecializedServantFactory.create_servant(
    servant_type="dwarf",
    servant_id="dwarf_001",
    servant_name="Code Crafter",
    specialization=ServantSpecialization.IMPLEMENTATION
)

# 成果物製作
craft_result = await dwarf_servant.craft_artifact({
    "type": "python_module",
    "requirements": ["high_performance", "secure"],
    "quality_target": 95.0
})
```

### A2A通信設定

```python
from libs.elder_servants.base.enhanced_elder_servant import A2ACommunication

a2a_config = A2ACommunication(
    host="localhost",
    port=8001,
    max_connections=100,
    timeout_seconds=30
)

servant = MyCustomServant(a2a_config=a2a_config)

# 他のサーバントにメッセージ送信
response = await servant.send_a2a_message(
    target_servant_id="target_servant_001",
    message={"type": "collaboration_request", "data": "hello"}
)
```

### 4賢者連携設定

```python
from libs.elder_servants.base.enhanced_elder_servant import SageCollaboration

sage_config = SageCollaboration(
    knowledge_sage_endpoint="localhost:8001",
    task_sage_endpoint="localhost:8002",
    incident_sage_endpoint="localhost:8003",
    rag_sage_endpoint="localhost:8004"
)

servant = MyCustomServant(sage_config=sage_config)
```

### 品質ゲート設定

```python
from libs.elder_servants.base.enhanced_elder_servant import QualityGate

quality_config = QualityGate(
    iron_will_threshold=98.0,        # より厳しい品質基準
    test_coverage_minimum=95.0,
    auto_rejection=True,
    escalation_enabled=True
)

servant = MyCustomServant(quality_config=quality_config)
```

### 学習システム設定

```python
from libs.elder_servants.base.enhanced_elder_servant import LearningConfig

learning_config = LearningConfig(
    enabled=True,
    learning_rate=0.1,
    auto_adaptation=True,
    success_pattern_learning=True,
    failure_pattern_learning=True
)

servant = MyCustomServant(learning_config=learning_config)
```

## アーキテクチャ概要

### 統合処理フロー

1. **予防的品質チェック** - インシデント騎士団による事前検証
2. **4賢者事前相談** - 複雑タスクの場合の自動相談
3. **専門タスク実行** - 各サーバント固有の処理
4. **品質ゲート検証** - Iron Will基準による品質保証
5. **自動修復** - 品質問題の自動改善
6. **学習・適応** - 実行結果からの継続学習
7. **メトリクス更新** - 統計・監視データ更新

### 品質基準（Iron Will）

- **根本原因解決度**: 95%以上
- **依存関係完全性**: 100%必須
- **テストカバレッジ**: 95%最低
- **セキュリティスコア**: 90%以上
- **パフォーマンス**: 85%維持
- **保守性**: 80%以上

### メトリクス収集

自動的に以下のメトリクスを収集・追跡：

- タスク実行統計（成功率、実行時間）
- 品質スコア（Iron Will準拠率）
- A2A通信統計（メッセージ送受信）
- 4賢者連携統計（相談成功率）
- 学習統計（パターン学習、適応）
- システム統計（CPU、メモリ、稼働時間）

## テスト実行

```bash
# 基底クラステスト実行
pytest tests/unit/test_enhanced_elder_servant.py -v

# すべてのサーバントテスト実行
pytest tests/unit/test_*_servant.py -v

# カバレッジ付きテスト
pytest --cov=libs.elder_servants.base tests/unit/ --cov-report=html
```

## 設定ファイル例

### サーバント設定 (servant_config.json)

```json
{
  "servant_id": "dwarf_code_crafter_001",
  "servant_name": "Master Code Crafter",
  "specialization": "implementation",
  "tier": "master",
  "a2a_config": {
    "host": "localhost",
    "port": 8001,
    "max_connections": 100
  },
  "sage_config": {
    "knowledge_sage_endpoint": "localhost:8001",
    "task_sage_endpoint": "localhost:8002",
    "incident_sage_endpoint": "localhost:8003",
    "rag_sage_endpoint": "localhost:8004"
  },
  "quality_config": {
    "iron_will_threshold": 95.0,
    "auto_rejection": true
  },
  "learning_config": {
    "enabled": true,
    "auto_adaptation": true
  }
}
```

## 拡張ガイド

### カスタム専門分野追加

1. `ServantSpecialization` にenum追加
2. 専門特化基底クラスを継承
3. `_execute_specialized_task` 実装
4. `get_specialized_capabilities` 実装
5. 専門メトリクス定義

### カスタム品質基準追加

1. `_evaluate_iron_will_criteria` 拡張
2. 新基準用評価メソッド実装
3. 閾値設定の `_get_criteria_threshold` 更新

### カスタム学習アルゴリズム追加

1. `_learn_success_pattern` / `_learn_failure_pattern` 拡張
2. `_adapt_behavior` にカスタムロジック追加
3. 学習メトリクス追加

## 関連文書

- [Elder Tree分散AIアーキテクチャ仕様書](../../../docs/technical/ELDER_TREE_DISTRIBUTED_AI_ARCHITECTURE.md)
- [Issue #257: Elder Tree分散AIアーキテクチャ実装プロジェクト](../../../docs/issues/issue-257-elder-tree-distributed-ai-architecture.md)
- [CLAUDE.md](../../../CLAUDE.md)

## ライセンス

Elder Guild Development License v1.0