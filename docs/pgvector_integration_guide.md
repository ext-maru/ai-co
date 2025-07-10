# pgvector統合ガイド - Elders Guild A2Aセマンティック分析

## 🚀 概要

Elders GuildのA2A（Agent-to-Agent）通信システムにpgvectorを統合し、リアルタイムセマンティック分析を実現しました。

### 主な機能
- 🔍 **セマンティック検索**: OpenAI埋め込みを使用した類似通信の検索
- 🚨 **異常検出**: ベクトル類似度による異常パターンの自動検出
- 📊 **エージェント行動分析**: エージェントの通信パターン分析
- ⏰ **時系列分析**: 通信トレンドとスパイク検出
- 🎯 **パターンマッチング**: 特定の通信パターンの発見

## 📦 セットアップ手順

### 1. 依存関係のインストール
```bash
source venv/bin/activate
pip install psycopg2-binary pgvector scikit-learn openai
```

### 2. PostgreSQLのセットアップ
```bash
# PostgreSQLのインストール（Ubuntu/Debian）
sudo apt update
sudo apt install postgresql postgresql-contrib

# pgvector拡張のインストール
sudo apt install postgresql-15-pgvector

# データベースの作成
sudo -u postgres createuser aicompany
sudo -u postgres createdb ai_company_db -O aicompany
```

### 3. 環境変数の設定
```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=ai_company_db
export PGUSER=aicompany
export PGPASSWORD=your_password
export OPENAI_API_KEY=your_openai_api_key
```

### 4. データベースセットアップ
```bash
python scripts/setup_pgvector_database.py
```

### 5. データ移行
```bash
python scripts/migrate_a2a_to_pgvector.py
```

## 🔧 使用方法

### セマンティック分析の実行
```bash
# デモ分析
python scripts/pgvector_a2a_integration.py --demo

# 類似通信検索
python scripts/pgvector_a2a_integration.py \
  --query "system overload error" \
  --type similarity_search \
  --limit 10

# 異常検出
python scripts/pgvector_a2a_integration.py \
  --type anomaly_detection \
  --limit 20

# エージェント行動分析
python scripts/pgvector_a2a_integration.py \
  --type agent_behavior \
  --agent "system-monitor"
```

### Pythonでの使用例
```python
from scripts.pgvector_a2a_integration import PgVectorA2AAnalyzer, SemanticQuery, AnalysisType

# アナライザーの初期化
analyzer = PgVectorA2AAnalyzer()
analyzer.connect()
analyzer.setup_openai()

# セマンティック検索
query = SemanticQuery(
    query_text="critical system failure",
    query_type=AnalysisType.SIMILARITY_SEARCH,
    limit=5,
    threshold=0.8
)

result = analyzer.execute_analysis(query)
for comm in result.results:
    print(f"{comm['sender']} → {comm['receiver']}: {comm['content']}")
    print(f"Similarity: {comm['similarity']:.3f}")
```

## 📊 データベーススキーマ

### a2a.communications
- `id`: シリアルID
- `timestamp`: タイムスタンプ
- `sender`: 送信エージェント
- `receiver`: 受信エージェント
- `message_type`: メッセージタイプ
- `content`: メッセージ内容
- `metadata`: JSONBメタデータ
- `embedding`: vector(1536) - OpenAI埋め込み

### a2a.anomaly_patterns
- `id`: シリアルID
- `pattern_name`: パターン名
- `pattern_type`: パターンタイプ
- `severity`: 重要度
- `description`: 説明
- `detection_rules`: 検出ルール（JSONB）
- `embedding`: vector(1536)
- `occurrence_count`: 発生回数

### a2a.agents
- `id`: シリアルID
- `agent_name`: エージェント名（ユニーク）
- `agent_type`: エージェントタイプ
- `status`: ステータス
- `capabilities`: 能力（JSONB）
- `performance_metrics`: パフォーマンス（JSONB）
- `embedding`: vector(1536)

## 🎯 分析タイプ

### 1. Similarity Search（類似検索）
- 指定したテキストに類似した通信を検索
- コサイン類似度による順位付け
- 閾値とフィルターによる絞り込み

### 2. Anomaly Detection（異常検出）
- 既知の異常パターンとの照合
- リアルタイム異常検出
- 重要度別の分類

### 3. Pattern Matching（パターンマッチング）
- 繰り返し発生する通信パターンの発見
- 統計的な出現頻度分析
- サンプル通信の提供

### 4. Agent Behavior（エージェント行動分析）
- エージェント別の通信統計
- インタラクションパターン
- 異常な行動の検出

### 5. Temporal Analysis（時系列分析）
- 時間帯別の通信量分析
- トレンド検出
- スパイク（異常値）の特定

## 🔍 サンプルクエリ

### 類似通信の検索
```sql
SELECT * FROM a2a.find_similar_communications(
    (SELECT embedding FROM a2a.communications ORDER BY timestamp DESC LIMIT 1),
    10
);
```

### 異常パターンの類似検索
```sql
SELECT 
    a1.pattern_name,
    a1.severity,
    1 - (a1.embedding <=> a2.embedding) as similarity
FROM a2a.anomaly_patterns a1
CROSS JOIN a2a.anomaly_patterns a2
WHERE a2.pattern_name = 'system-overload'
  AND a1.pattern_name != a2.pattern_name
ORDER BY similarity DESC
LIMIT 5;
```

### エージェント通信統計
```sql
SELECT 
    sender,
    receiver,
    message_type,
    COUNT(*) as message_count,
    MAX(timestamp) as last_communication
FROM a2a.communications
GROUP BY sender, receiver, message_type
ORDER BY message_count DESC;
```

## 🚀 パフォーマンス最適化

### インデックス
- **HNSW Index**: ベクトル検索の高速化
  - m = 16, ef_construction = 64
- **B-tree Index**: タイムスタンプ、エージェント名
- **GIN Index**: JSONBメタデータ

### ベストプラクティス
1. バッチ処理での埋め込み生成
2. 検索結果のキャッシング（TTL: 5分）
3. 時間窓フィルターの活用
4. 適切な類似度閾値の設定

## 📈 モニタリング

### 主要メトリクス
- クエリ実行時間
- 埋め込み生成数
- キャッシュヒット率
- エラー率

### ログファイル
- `/logs/pgvector_integration_prep.log` - 準備ログ
- `/logs/pgvector_setup_*.json` - セットアップレポート
- `/logs/pgvector_migration_*.json` - 移行レポート

## 🔐 セキュリティ

### APIキー管理
- 環境変数でのOpenAI APIキー管理
- データベースパスワードの安全な保管

### アクセス制御
- PostgreSQLロールベースアクセス
- 最小権限の原則

## 🛠️ トラブルシューティング

### pgvector拡張が見つからない
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### OpenAI APIエラー
- APIキーの確認
- レート制限の確認
- ネットワーク接続の確認

### メモリ不足
- バッチサイズの調整
- PostgreSQL設定の最適化

## 📚 参考資料

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)

---

**最終更新**: 2025年7月10日
**バージョン**: 1.0.0