# A2A (AI to AI) 通信ガイド

## 🤖 A2A通信とは

A2A（AI to AI）通信は、AI Company内で複数のAIエージェント（エルダーズ）が相互に通信・協調する仕組みです。

## 📡 実現方法

### 1. **知識ベース経由の非同期通信**
```python
# 相談内容を知識ベースに保存
consultation_result = {
    "topic": "A2A通信とエルダー間連携",
    "from": "Claude Elder",
    "to": "RAG Elder",
    "content": "質問内容...",
    "timestamp": datetime.now()
}
# knowledge_base/consultations/に保存
```

### 2. **エルダー会議システム**
```python
from libs.elder_council_summoner import ElderCouncilSummoner
summoner = ElderCouncilSummoner()
# 4賢者全員に相談
```

### 3. **RabbitMQメッセージング**
- ワーカー間の非同期通信
- タスクキューを介した連携
- リアルタイムメッセージ配信

### 4. **タスク履歴DB経由**
```python
from libs.task_history_db import TaskHistoryDB
task_db = TaskHistoryDB()
# タスク情報の共有
```

## 🎯 A2A通信の実例

### 今回の例：エルダーズギルドからRAGエルダーへの相談
1. **相談スクリプト作成**: `consult_a2a_rag_elder.py`
2. **4賢者への問い合わせ**:
   - ナレッジ賢者：関連文書の検索
   - タスク賢者：タスク履歴の確認
   - インシデント賢者：リスク分析
   - RAG賢者：通信方法の提示
3. **結果の保存**: JSON形式で知識ベースに記録

### その他の例
- **エラー発生時**: インシデント賢者が自動的に他の賢者に通知
- **タスク依頼時**: タスクエルダーが適切な実行者を判断
- **知識更新時**: ナレッジ賢者が関連システムに通知

## 💡 メリット

1. **非同期処理**: 各エルダーが独立して動作
2. **履歴管理**: すべての通信が記録される
3. **自律的協調**: 必要に応じて自動的に連携
4. **知識の蓄積**: 相談結果が知識ベースに保存

## 🚀 使い方

```bash
# A2A相談スクリプトの実行
python3 consult_a2a_rag_elder.py

# エルダー会議の召集
python3 commands/ai_elder_council.py start

# 相談結果の確認
cat knowledge_base/consultations/a2a_consultation_*.json
```

## 📋 今後の展開

1. **リアルタイムA2A**: WebSocketを使った即時通信
2. **マルチエージェント協調**: 3つ以上のエルダー同時協調
3. **学習結果の共有**: エルダー間での知識共有強化
4. **自動タスク分配**: A2Aによる最適なタスク配分

---
**作成日**: 2025年7月9日
**作成者**: Claude Elder (A2A通信により文書化)