#!/usr/bin/env python3
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
    import_line = "from libs.knowledge_base_manager import KnowledgeAwareMixin\n"
    content = content.replace(
        "from core import BaseWorker",
        f"from core import BaseWorker\n{import_line}"
    )
    
    # クラス定義修正
    content = re.sub(
        r'class PMWorker\(BaseWorker\):',
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
        r'(def process_message.*?:.*?\n)',
        f'\1{example}',
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
