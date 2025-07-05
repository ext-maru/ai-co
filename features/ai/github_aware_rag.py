#!/usr/bin/env python3
"""
GitHub情報を活用するRAG拡張
"""
import sys
sys.path.append('/root/ai_co')
from typing import List, Dict, Any  # 追加
from features.ai.rag_manager import RAGManager
from features.integration.github_integration import GitHubIntegrationManager

class GitHubAwareRAGManager(RAGManager):
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        super().__init__(model)
        self.github = GitHubIntegrationManager()
    
    def build_context_with_github(self, prompt: str, include_code: bool = True) -> str:
        """GitHub情報を含めたコンテキスト構築"""
        # 基本のRAGコンテキスト
        base_context = self.build_context_prompt(prompt, include_history=True)
        
        if include_code and self.github.api_repo_url:
            # プロンプトから関連ファイルを推測
            relevant_files = self._guess_relevant_files(prompt)
            
            if relevant_files:
                # GitHubからコード情報取得
                github_context = self.github.get_code_context_for_ai(relevant_files)
                base_context += "\n\n" + github_context
            
            # 最近のコミット情報も追加
            recent_commits = self.github.get_recent_commits(5)
            if recent_commits:
                base_context += "\n\n【最近の変更】\n"
                for commit in recent_commits:
                    base_context += f"- {commit['sha']}: {commit['message']} ({commit['author']})\n"
        
        return base_context
    
    def _guess_relevant_files(self, prompt: str) -> List[str]:
        """プロンプトから関連ファイルを推測"""
        prompt_lower = prompt.lower()
        files = []
        
        # キーワードマッピング
        keyword_map = {
            'worker': ['workers/task_worker.py', 'workers/pm_worker.py'],
            'rag': ['libs/rag_manager.py'],
            'slack': ['libs/slack_notifier.py'],
            'github': ['libs/github_integration.py'],
            'conversation': ['libs/conversation_manager.py'],
            'dialog': ['workers/dialog_task_worker.py'],
            'evolution': ['libs/self_evolution_manager.py']
        }
        
        for keyword, file_list in keyword_map.items():
            if keyword in prompt_lower:
                files.extend(file_list)
        
        return list(set(files))  # 重複除去
