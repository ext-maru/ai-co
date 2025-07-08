#!/usr/bin/env python3
from pathlib import Path
"""
RAGマネージャーに検索機能を統合
"""
import sys
sys.path.append(str(Path(__file__).parent.parent))

# RAGマネージャーを拡張するコード
enhanced_rag_code = '''
# libs/rag_manager.py に追加する機能

def build_context_with_search(self, prompt: str, include_similar: bool = True) -> str:
    """検索結果も含めたコンテキスト構築"""
    # 既存のRAGコンテキスト
    base_context = self.build_context_prompt(prompt, include_history=True)
    
    if include_similar:
        # AI学習インターフェースから類似タスク情報を取得
        from libs.ai_learning_interface import AILearningInterface
        ai_interface = AILearningInterface()
        learning_data = ai_interface.learn_from_similar_tasks(prompt)
        
        if learning_data['suggested_approach']:
            base_context += f"\\n\\n【参考情報】\\n{learning_data['suggested_approach']}"
    
    return base_context
'''

print("RAGマネージャーに検索機能を統合するには、上記のコードを追加してください")
print("\n実装済み機能:")
print("✅ 会話履歴からの学習")
print("✅ 類似タスクの自動検索")
print("✅ AI向け分析レポート")
