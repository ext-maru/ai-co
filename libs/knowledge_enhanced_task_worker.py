#!/usr/bin/env python3
"""
TaskWorkerへのナレッジベース統合
Claude CLIにナレッジを含めて実行する
"""
import json
from pathlib import Path
from typing import Optional, Dict

class KnowledgeEnhancedTaskWorker:
    """ナレッジベースを活用するTaskWorkerの拡張例"""
    
    def _prepare_prompt_with_knowledge(self, original_prompt: str, task_type: str) -> str:
        """プロンプトにナレッジベースの情報を追加"""
        from libs.knowledge_base_manager import KnowledgeBaseManager
        
        manager = KnowledgeBaseManager()
        
        # タスクタイプに応じたナレッジを取得
        knowledge_topics = {
            "test": ["test", "テスト"],
            "worker": ["core", "worker"],
            "feature": ["新機能", "feature"],
            "fix": ["error", "fix", "修正"]
        }
        
        relevant_knowledge = []
        for topic in knowledge_topics.get(task_type, [task_type]):
            knowledge = manager.get_knowledge(topic)
            if knowledge:
                relevant_knowledge.append(knowledge)
        
        if not relevant_knowledge:
            return original_prompt
        
        # ナレッジを含めたプロンプトを構築
        enhanced_prompt = f"""
{original_prompt}

---
📚 関連するナレッジベース情報:

{chr(10).join(relevant_knowledge[:1])}  # 最初の1つだけ含める（トークン制限考慮）

---
上記のナレッジベースの情報を参考にして、ベストプラクティスに従って実装してください。
特に以下の点に注意してください:
- テストフレームワークの規約に従う
- エラーハンドリングを適切に実装
- ログ出力はプロフェッショナルに
"""
        
        return enhanced_prompt
    
    def _execute_claude_cli_with_knowledge(self, task_data: Dict) -> str:
        """ナレッジベースを含めてClaude CLIを実行"""
        original_prompt = task_data.get('prompt', '')
        task_type = task_data.get('task_type', 'general')
        
        # プロンプトにナレッジを追加
        enhanced_prompt = self._prepare_prompt_with_knowledge(original_prompt, task_type)
        
        # タスクデータを更新
        enhanced_task_data = task_data.copy()
        enhanced_task_data['prompt'] = enhanced_prompt
        
        # 通常のClaude CLI実行
        return self._execute_claude_cli(enhanced_task_data)

# 使用例を示すスクリプト
def demonstrate_knowledge_enhanced_execution():
    """ナレッジベース統合の実例"""
    
    print("🤖 ナレッジベース統合TaskWorkerのデモ")
    print("=" * 50)
    
    # サンプルタスク
    sample_tasks = [
        {
            "task_id": "test_001",
            "task_type": "test",
            "prompt": "TaskWorkerのテストを作成してください"
        },
        {
            "task_id": "fix_001",
            "task_type": "fix",
            "prompt": "conftest.pyの--skip-slowエラーを修正してください"
        }
    ]
    
    worker = KnowledgeEnhancedTaskWorker()
    
    for task in sample_tasks:
        print(f"\n📋 タスク: {task['task_id']}")
        print(f"   タイプ: {task['task_type']}")
        print(f"   元のプロンプト: {task['prompt'][:50]}...")
        
        # ナレッジを含めたプロンプトを準備
        enhanced_prompt = worker._prepare_prompt_with_knowledge(
            task['prompt'], 
            task['task_type']
        )
        
        print(f"   強化されたプロンプト: {len(enhanced_prompt)} 文字")
        
        # ナレッジが含まれているか確認
        if "関連するナレッジベース情報" in enhanced_prompt:
            print("   ✓ ナレッジベースが含まれています")
        else:
            print("   ⚠️  ナレッジベースが見つかりませんでした")

if __name__ == "__main__":
    demonstrate_knowledge_enhanced_execution()
