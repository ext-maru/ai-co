# 🚀 エルダーズギルド開発クイックリファレンス

## 📋 開発チェックリスト

### 🧪 新機能開発
```bash
# 1. テストファースト
ai-tdd new FeatureName "要件"

# 2. 実装
# RED → GREEN → REFACTOR

# 3. コミット
git commit -m "feat(scope): 機能説明"

# 4. PR作成
gh pr create --title "feat: 新機能" --body "CO-STAR形式で記述"
```

### 🔍 コードレビュー前チェック
- [ ] テストカバレッジ 90%以上
- [ ] 全テストパス
- [ ] ドキュメント更新
- [ ] 型ヒント追加
- [ ] セキュリティスキャン実行
- [ ] パフォーマンステスト完了

### 🚨 インシデント対応
```python
# 1. 自動報告（推奨）
from libs.claude_elder_error_wrapper import incident_aware

@incident_aware
def risky_function():
    # エラー時は自動的に4賢者会議招集
    pass

# 2. 手動対応
1. 即座に作業停止
2. インシデント賢者に報告
3. 4賢者会議で原因分析
4. 解決策の実装とテスト
5. knowledge_base/failures/に記録
```

## 🎯 品質基準早見表

| 指標 | 最小 | 目標 |
|------|------|------|
| テストカバレッジ | 90% | 100% |
| 複雑度 | <10 | <5 |
| 応答時間(p95) | 500ms | 200ms |
| コードレビュー | 2名 | 3名 |

## 🌿 ブランチ規則
```bash
# 機能開発
git checkout -b feature/elder-awesome-feature

# バグ修正
git checkout -b fix/sage-calculation-error

# 緊急修正（評議会承認必須）
git checkout -b hotfix/critical-security-patch
```

## 📝 コミットメッセージ
```bash
# 形式
<type>(<scope>): <subject>

# 例
feat(elder): 4賢者自動協調システム実装
fix(sage): メモリリーク修正
docs(api): エンドポイント仕様更新
perf(worker): バッチ処理を50%高速化
```

## 🧙‍♂️ 4賢者への相談方法

### ナレッジ賢者
```python
# ベストプラクティス検索
knowledge = KnowledgeSage.search("TDD best practices")
```

### タスク賢者
```python
# タスク優先順位取得
priority = TaskOracle.get_priority(task_list)
```

### インシデント賢者
```python
# 問題報告
CrisisSage.report_incident(error, context)
```

### RAG賢者
```python
# 技術調査
solution = SearchMystic.find_solution(problem)
```

## 🏆 パフォーマンス目標
- API応答: p50 < 50ms, p95 < 200ms
- 同時接続: 10,000
- 可用性: 99.99%

## 🔒 セキュリティ必須
- すべての通信をTLS 1.3で暗号化
- 入力検証を全エンドポイントで実施
- 最小権限原則の徹底
- 監査ログの完全記録

## 📊 週次KPI
- バグ密度: <0.1/KLOC
- リードタイム: <3日
- デプロイ頻度: >10回/日
- MTTR: <30分

---
**Remember: No Code Without Test! 🧪**
*詳細は ELDERS_GUILD_DEVELOPMENT_POLICY.md を参照*