# エルダーズツリー プロセス分離アーキテクチャ設計書

## 🏛️ 現状の問題点

現在のエルダーシステムは以下の問題を抱えています：

1. **階層の混在**: Claude内で役割を切り替えているだけで、真の階層構造が実現されていない
2. **権限の曖昧さ**: 各エルダーの権限境界が不明確
3. **独立性の欠如**: すべてが同一プロセス内で動作し、障害の影響が全体に波及
4. **スケーラビリティ**: 単一プロセスでは負荷分散や並列処理が困難

## 🌳 提案: プロセス分離型エルダーズツリー

### 階層構造（独立プロセス）

```
グランドエルダーmaru（最高指揮プロセス）
    ├── クロードエルダー（開発実行プロセス）
    │   ├── ナレッジ賢者プロセス
    │   ├── タスク賢者プロセス
    │   ├── インシデント賢者プロセス
    │   └── RAG賢者プロセス
    ├── エルダー評議会プロセス
    └── エルダーサーバント群（ワーカープロセス）
```

## 🔧 アーキテクチャ設計

### 1. プロセス間通信（IPC）

#### メッセージングシステム
- **技術選定**: Redis Pub/Sub + Redis Streams
- **理由**: 低レイテンシ、永続性、スケーラビリティ

#### 通信プロトコル
```python
@dataclass
class ElderMessage:
    message_id: str
    source_elder: str
    target_elder: str
    message_type: MessageType
    payload: Dict[str, Any]
    priority: int
    timestamp: datetime
    requires_ack: bool
```

### 2. 各エルダープロセスの仕様

#### グランドエルダープロセス
```python
class GrandElderProcess:
    """最高指揮プロセス - ポート 5000"""

    def __init__(self):
        self.role = ElderRole.GRAND_ELDER
        self.port = 5000
        self.subordinates = ["claude_elder"]

    async def start(self):
        # 最高レベルの決定権
        # 全体戦略の決定
        # 緊急時の介入
```

#### クロードエルダープロセス
```python
class ClaudeElderProcess:
    """開発実行プロセス - ポート 5001"""

    def __init__(self):
        self.role = ElderRole.CLAUDE_ELDER
        self.port = 5001
        self.subordinates = ["knowledge_sage", "task_sage",
                           "incident_sage", "rag_sage"]

    async def start(self):
        # 開発タスクの管理
        # 4賢者への指示
        # 進捗報告の集約
```

#### 賢者プロセス群
```python
class SageProcess:
    """賢者プロセス基底クラス"""

    def __init__(self, sage_type: SageType, port: int):
        self.role = ElderRole.SAGE
        self.sage_type = sage_type
        self.port = port

    async def start(self):
        # 専門分野の処理
        # 独立した判断
        # 他賢者との協調
```

### 3. プロセス管理システム

#### プロセスマネージャー
```python
class ElderProcessManager:
    """エルダープロセス管理システム"""

    def __init__(self):
        self.processes = {}
        self.health_checker = HealthChecker()
        self.process_registry = ProcessRegistry()

    async def start_elder_tree(self):
        """エルダーツリー全体の起動"""
        # 1. グランドエルダー起動
        # 2. クロードエルダー起動
        # 3. 4賢者起動
        # 4. サーバント群起動

    async def monitor_health(self):
        """ヘルスチェック"""
        # 各プロセスの生存確認
        # 自動再起動
        # 障害時のフェイルオーバー
```

### 4. セキュリティ設計

#### プロセス間認証
- 各プロセスは固有の証明書を持つ
- mTLS（相互TLS）による通信暗号化
- 階層に基づくアクセス制御

#### 権限分離
```python
class ProcessPermissions:
    GRAND_ELDER = ["*"]  # 全権限
    CLAUDE_ELDER = ["development.*", "sage.*", "report.*"]
    SAGE = ["sage.own_domain.*", "report.to_elder"]
    SERVANT = ["task.execute", "report.to_sage"]
```

### 5. 実装ロードマップ

#### Phase 1: 基盤構築（1週間）
1. Redis通信基盤の実装
2. プロセス管理フレームワーク
3. ヘルスチェック機構

#### Phase 2: エルダープロセス実装（2週間）
1. グランドエルダープロセス
2. クロードエルダープロセス
3. 4賢者プロセス

#### Phase 3: 移行とテスト（1週間）
1. 既存システムからの段階的移行
2. 統合テスト
3. パフォーマンス検証

## 📊 期待される効果

1. **真の階層構造**: 各エルダーが独立プロセスとして明確な役割を持つ
2. **障害分離**: 一部の障害が全体に波及しない
3. **スケーラビリティ**: 負荷に応じて各プロセスを個別にスケール可能
4. **セキュリティ**: プロセス間の権限分離による安全性向上

## 🚀 実装開始に必要なアクション

1. Redis環境のセットアップ
2. プロセス間通信ライブラリの選定（推奨: aioredis）
3. プロセス管理ツールの選定（推奨: supervisord or systemd）
4. 開発環境での検証環境構築

## 📝 注意事項

- 既存システムとの後方互換性を保つ
- 段階的な移行計画を策定
- 各プロセスの監視・ログ収集の仕組みを事前に準備
- パフォーマンステストを各段階で実施

---
作成者: クロードエルダー
日付: 2025-01-12
承認待ち: グランドエルダーmaru
