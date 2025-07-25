# 🗑️ レガシーファイル削除計画

**作成日**: 2025年7月24日  
**作成者**: Claude Elder  
**目的**: 旧A2A実装の削除と新python-a2a移行  

---

## 📋 削除対象ファイル一覧

### 🔴 優先度: 高（即座削除）

#### 1. **libs/a2a_communication.py**
- **理由**: RabbitMQベースの旧A2A実装
- **行数**: 760行
- **依存**: aio_pika, aioredis, jwt, cryptography
- **影響**: 新規開発での誤使用を防ぐため即座削除必要

### 🟡 優先度: 中（移行後削除）

#### 2. **libs/rabbitmq_*.py 関連**
```yaml
対象ファイル:
  - libs/rabbitmq_a2a_communication.py
  - libs/rabbitmq_mock.py
  - libs/rabbitmq_monitor.py
理由: RabbitMQベースの通信は廃止
```

#### 3. **旧A2A関連テスト**
```yaml
対象ファイル:
  - tests/test_a2a_communication.py
  - tests/integration/test_rabbitmq_*.py
理由: 旧実装のテストは不要
```

### 🟢 優先度: 低（確認後削除）

#### 4. **設定ファイル内のRabbitMQ参照**
```yaml
確認対象:
  - .env.example
  - docker-compose.yml
  - configs/*.yml
作業: RabbitMQ関連設定の削除
```

---

## 🔄 移行計画

### Phase 1: 影響調査（1日）
1. 削除対象ファイルの参照箇所を検索
2. 依存関係の確認
3. 代替実装の必要性評価

### Phase 2: 段階的削除（2-3日）
1. 高優先度ファイルの削除
2. テスト実行・動作確認
3. 中優先度ファイルの削除
4. 最終確認

### Phase 3: クリーンアップ（1日）
1. 設定ファイルの整理
2. ドキュメント更新
3. 最終テスト

---

## ⚠️ 注意事項

### 削除前チェックリスト
- [ ] 本番環境での使用確認
- [ ] バックアップ作成
- [ ] 依存関係の完全把握
- [ ] 代替実装の準備完了

### リスク軽減策
1. **段階的削除**: 一度にすべて削除せず段階的に実施
2. **Git履歴保持**: 削除コミットを明確に記録
3. **ロールバック計画**: 問題発生時の復旧手順準備

---

## 📊 削除効果

### コードベース改善
- **削減行数**: 約2,000行以上
- **依存関係**: 不要なライブラリ削除
- **保守性**: 混乱を招く旧実装の排除

### 開発効率向上
- **明確性**: 新規開発者の混乱防止
- **一貫性**: python-a2a統一実装
- **シンプル化**: アーキテクチャの簡素化

---

## 🚀 実行コマンド

```bash
# Phase 1: 影響調査
grep -r "a2a_communication" . --exclude-dir=.git
grep -r "rabbitmq" . --exclude-dir=.git

# Phase 2: 削除実行
git rm libs/a2a_communication.py
git rm libs/rabbitmq_*.py

# Phase 3: 確認
pytest tests/
```

---

**承認者**: グランドエルダーmaru（承認待ち）  
**実行予定**: 承認後即座に開始  