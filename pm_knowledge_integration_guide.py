#!/usr/bin/env python3
"""
PMWorkerへのナレッジベース統合ガイド
既存のPMWorkerにナレッジベース参照機能を追加する方法
"""
import sys
from pathlib import Path

def generate_integration_guide():
    """統合ガイドを生成"""
    
    guide = """
# 🤖 PMWorkerへのナレッジベース統合ガイド

## 📋 概要

PMWorkerがナレッジベースを自動参照できるようにする方法です。

## 🔧 実装方法

### 1. PMWorkerの修正

`workers/pm_worker.py`の先頭に以下を追加：

```python
from libs.knowledge_base_manager import KnowledgeAwareMixin

# クラス定義を修正
class PMWorker(BaseWorker, KnowledgeAwareMixin):
    def __init__(self, worker_id=None):
        super().__init__(worker_type='pm', worker_id=worker_id)
        # 既存の初期化コード...
```

### 2. メッセージ処理での活用

```python
def process_message(self, ch, method, properties, body):
    task_data = json.loads(body)
    
    # タスクタイプに応じてナレッジを参照
    if task_data.get('task_type') == 'test':
        # テストに関するナレッジを参照
        test_knowledge = self.consult_knowledge('test')
        if test_knowledge:
            self.logger.info("Found test framework knowledge")
            # ナレッジを活用した処理
    
    # 既存の処理...
```

### 3. 定期的な更新チェック

```python
def _check_knowledge_updates_periodically(self):
    \"\"\"定期的にナレッジベースの更新をチェック\"\"\"
    while self.running:
        updates = self.check_knowledge_updates()
        if updates['modified'] or updates['new']:
            self.logger.info("Knowledge base updated, reloading...")
            # 必要に応じて再読み込み
        
        time.sleep(300)  # 5分ごとにチェック
```

## 🎯 活用例

### テスト関連タスクでの自動参照

```python
# タスク: "テストが失敗しました"
if "test" in task_data.get('prompt', '').lower():
    knowledge = self.consult_knowledge('test')
    if knowledge:
        # ナレッジから解決策を抽出
        if "ValueError: no option named '--skip-slow'" in error_message:
            solution = "python scripts/fix_conftest.py を実行"
            self._create_fix_task(solution)
```

### 新機能実装時の参照

```python
# タスク: "新しいワーカーを作成"
if "worker" in task_data.get('prompt', ''):
    knowledge = self.consult_knowledge('core')
    # BaseWorkerの実装方法を参照
```

## 📊 効果

1. **自動問題解決**: テストエラーなどの既知の問題を自動解決
2. **品質向上**: ベストプラクティスを自動適用
3. **学習効果**: 過去の知識を活用して改善

## 🚀 即座に適用

```bash
# PMWorkerにパッチを適用
python scripts/patch_pm_worker_knowledge.py

# または手動で編集
vim workers/pm_worker.py
# KnowledgeAwareMixinを追加
```
"""
    
    print(guide)
    
    # 統合パッチスクリプトも生成
    patch_script = '''#!/usr/bin/env python3
"""
PMWorkerにナレッジベース機能を追加するパッチ
"""
import re
from pathlib import Path

def patch_pm_worker():
    pm_worker_path = Path("/home/aicompany/ai_co/workers/pm_worker.py")
    
    if not pm_worker_path.exists():
        print("❌ pm_worker.pyが見つかりません")
        return False
    
    with open(pm_worker_path, 'r') as f:
        content = f.read()
    
    # すでにパッチ済みかチェック
    if "KnowledgeAwareMixin" in content:
        print("✓ すでにナレッジベース機能が追加されています")
        return True
    
    # インポート追加
    import_line = "from libs.knowledge_base_manager import KnowledgeAwareMixin\\n"
    content = content.replace(
        "from core import BaseWorker",
        f"from core import BaseWorker\\n{import_line}"
    )
    
    # クラス定義修正
    content = re.sub(
        r'class PMWorker\\(BaseWorker\\):',
        'class PMWorker(BaseWorker, KnowledgeAwareMixin):',
        content
    )
    
    # ナレッジ参照の例を追加（コメントとして）
    example = """
        # ナレッジベース参照の例
        # knowledge = self.consult_knowledge('test')
        # updates = self.check_knowledge_updates()
"""
    
    # process_messageメソッドにコメントを追加
    content = re.sub(
        r'(def process_message.*?:.*?\\n)',
        f'\\1{example}',
        content,
        flags=re.DOTALL
    )
    
    # ファイルに書き戻し
    with open(pm_worker_path, 'w') as f:
        f.write(content)
    
    print("✅ PMWorkerにナレッジベース機能を追加しました")
    return True

if __name__ == "__main__":
    patch_pm_worker()
'''
    
    # パッチスクリプトを保存
    patch_path = Path("/home/aicompany/ai_co/scripts/patch_pm_worker_knowledge.py")
    with open(patch_path, 'w') as f:
        f.write(patch_script)
    
    print(f"\n📝 パッチスクリプトを作成しました: {patch_path}")
    print("\n実行方法:")
    print("  python scripts/patch_pm_worker_knowledge.py")

if __name__ == "__main__":
    generate_integration_guide()
