import os
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any
from libs.github_flow_manager import GitHubFlowManager

class PMGitIntegration:
    """PMWorker用のGit統合機能（GitHub Flow対応版）"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.git_manager = GitHubFlowManager()
        self.project_dir = Path(__file__).parent.parent
        
    def handle_task_completion(self, task_id: str, result_data: Dict[str, Any]):
        """タスク完了時のGit処理"""
        try:
            # ファイル変更を検出
            files_created = result_data.get('files_created', [])
            files_updated = result_data.get('files_updated', [])
            all_files = files_created + files_updated
            
            if not all_files:
                return
            
            # タスクの要約を取得
            summary = result_data.get('summary', 'Task completion')
            
            # GitHub Flow処理
            self.git_manager.auto_commit_task_result(task_id, all_files, summary)
            
        except Exception as e:
            self.logger.error(f"Git integration error: {e}")
    
    def check_and_release(self):
        """定期的なリリースチェック（GitHub Flow）"""
        try:
            status = self.git_manager.get_status()
            
            # mainブランチでのリリースタグ作成を推奨
            if status.get('current_branch') == 'main':
                # GitHub Flowでは継続的にmainにマージされるため
                # 必要に応じてリリースタグを作成
                self.logger.info("📋 Consider creating a release tag on main")
        except Exception as e:
            self.logger.error(f"Release check error: {e}")
