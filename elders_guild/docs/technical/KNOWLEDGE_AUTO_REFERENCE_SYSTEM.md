# 🤖 Elders Guild ナレッジベース自動参照システム

## 📋 概要

Elders Guildのワーカーが、ナレッジベースを自動的に参照し、過去の知識を活用できるシステムです。これにより、既知の問題の自動解決や、ベストプラクティスの自動適用が可能になります。

## 🏗️ システム構成

### 主要コンポーネント

```
libs/
├── knowledge_base_manager.py    # ナレッジベース管理システム
└── knowledge_enhanced_task_worker.py  # TaskWorker拡張例

scripts/
├── setup_knowledge_system.py    # セットアップスクリプト
└── patch_pm_worker_knowledge.py # PMWorker統合パッチ

db/
└── knowledge_cache.json        # ナレッジベースのキャッシュ
```

## 🔧 実装詳細

### 1. KnowledgeBaseManager

ナレッジベースの管理・検索・キャッシュを担当。

```python
from libs.knowledge_base_manager import KnowledgeBaseManager

manager = KnowledgeBaseManager()

# トピックに関連するナレッジを取得
knowledge = manager.get_knowledge("test")

# ナレッジベース内を検索
results = manager.search_knowledge("エラー")

# 更新チェック
updates = manager.check_updates()
```

### 2. KnowledgeAwareMixin

ワーカーにナレッジベース参照機能を追加するミックスイン。

```python
from core import BaseWorker
from libs.knowledge_base_manager import KnowledgeAwareMixin

class NewWorker(BaseWorker, KnowledgeAwareMixin):
    def process_message(self, ch, method, properties, body):
        # ナレッジベースを参照
        knowledge = self.consult_knowledge('test')

        if knowledge:
            # ナレッジを活用した処理
            self.logger.info("Found relevant knowledge")
```

### 3. キーワードマッピング

トピックとナレッジファイルの対応：

```python
keyword_map = {
    "test": ["TEST_FRAMEWORK_KNOWLEDGE.md", "TEST_GUIDELINES.md"],
    "テスト": ["TEST_FRAMEWORK_KNOWLEDGE.md", "TEST_GUIDELINES.md"],
    "ai_command": ["AI_COMMAND_EXECUTOR_KNOWLEDGE.md"],
    "新機能": ["AI_COMPANY_NEW_FEATURES.md"],
    "core": ["AI_COMPANY_CORE_KNOWLEDGE.md"],
    "開発": ["DEVELOPER_PERSONALITY.md", "PROJECT_INSTRUCTIONS.md"]
}
```

## 🚀 セットアップ

### 自動セットアップ

```bash
chmod +x /home/aicompany/ai_co/setup_knowledge_auto_reference.sh
cd /home/aicompany/ai_co && ./setup_knowledge_auto_reference.sh
```

### 手動セットアップ

1. **KnowledgeBaseManagerの確認**
   ```bash
   python libs/knowledge_base_manager.py
   ```

2. **PMWorkerへの統合**
   ```bash
   python scripts/patch_pm_worker_knowledge.py
   ```

## 📊 活用例

### 1. エラーの自動解決

```python
# PMWorkerでの実装例
def process_message(self, ch, method, properties, body):
    error_message = body.get('error', '')

    # エラーに関するナレッジを検索
    knowledge = self.consult_knowledge('error')

    # 既知のエラーパターンをチェック
    if "ValueError: no option named '--skip-slow'" in error_message:
        # ナレッジから解決策を適用
        self._create_fix_task("python scripts/fix_conftest.py")
```

### 2. TaskWorkerでのプロンプト強化

```python
# Claude CLIに送るプロンプトにナレッジを含める
def _prepare_prompt_with_knowledge(self, original_prompt, task_type):
    knowledge = self.consult_knowledge(task_type)

    if knowledge:
        enhanced_prompt = f"""
{original_prompt}

---
📚 関連するナレッジベース情報:
{knowledge}

上記の情報を参考にして、ベストプラクティスに従って実装してください。
"""
        return enhanced_prompt

    return original_prompt
```

### 3. 定期的な更新チェック

```python
def _check_knowledge_updates_periodically(self):
    """5分ごとにナレッジベースの更新をチェック"""
    while self.running:
        updates = self.check_knowledge_updates()

        if updates['modified'] or updates['new']:
            self.logger.info("Knowledge base updated")
            # キャッシュをクリアして再読み込み

        time.sleep(300)
```

## 🎯 ベストプラクティス

### 1. ナレッジの追加

新しい問題と解決策を発見したら、対応するナレッジベースに追加：

```bash
# 例: テスト関連の新しい知識
echo "## 新しいエラーパターン" >> docs/TEST_FRAMEWORK_KNOWLEDGE.md
echo "..." >> docs/TEST_FRAMEWORK_KNOWLEDGE.md
```

### 2. キーワードの最適化

頻繁に参照されるトピックは、`keyword_map`に追加：

```python
# knowledge_base_manager.pyのkeyword_mapを更新
keyword_map = {
    # ...既存のマッピング...
    "新しいトピック": ["RELEVANT_KNOWLEDGE.md"],
}
```

### 3. パフォーマンス考慮

- キャッシュを活用してファイルI/Oを削減
- 大きなナレッジは要約版を用意
- Claude CLIに送る際はトークン制限を考慮

## 📈 効果測定

### メトリクス

- **問題解決率**: 自動解決できた既知エラーの割合
- **品質向上**: ベストプラクティス適用率
- **時間短縮**: 手動介入が不要になったタスクの時間

### ログ分析

```python
# ナレッジ参照の統計
grep "Consulting knowledge base" logs/pm_worker.log | wc -l
grep "Found relevant knowledge" logs/pm_worker.log | wc -l
```

## 🔒 注意事項

1. **トークン制限**: Claude CLIに送る際は、ナレッジのサイズに注意
2. **更新頻度**: 頻繁な更新チェックはパフォーマンスに影響
3. **キャッシュ管理**: 定期的にキャッシュをクリア

## 🚀 今後の拡張

### Phase 1: 自動学習
- タスク成功時に新しい知識を自動追加
- エラーパターンの自動認識

### Phase 2: 知識グラフ
- ナレッジ間の関連性を分析
- より賢い検索アルゴリズム

### Phase 3: 分散ナレッジ
- 複数のElders Guildインスタンス間で知識共有
- クラウドベースのナレッジリポジトリ

---

**🤖 このシステムにより、Elders Guildは過去の経験から学習し、より賢く動作するようになります**
