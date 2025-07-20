#!/usr/bin/env python3
"""
Safe Git Operations for PR Creation
PR作成時のGitエラーを防ぐ安全な操作を提供

Created: 2025-07-20
Author: Claude Elder
"""

import logging
import subprocess
import os
from typing import Dict, List, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class SafeGitOperations:
    """安全なGit操作を提供するクラス"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        logger.info(f"SafeGitOperations initialized for {self.repo_path}")
    
    def _run_git_command(self, command: List[str]) -> Tuple[bool, str, str]:
        """Gitコマンドの実行（安全版）"""
        try:
            result = subprocess.run(
                ["git"] + command,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.repo_path
            )
            
            success = result.returncode == 0
            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""
            
            if not success:
                logger.warning(f"Git command failed: git {' '.join(command)} - {stderr}")
            
            return success, stdout, stderr
        except subprocess.TimeoutExpired:
            logger.error(f"Git command timeout: git {' '.join(command)}")
            return False, "", "Command timed out"
        except Exception as e:
            logger.error(f"Git command error: git {' '.join(command)} - {e}")
            return False, "", str(e)

    def ensure_git_state_is_clean(self) -> Dict[str, Any]:
        """Git状態を確認してクリーンアップ"""
        try:
            # 1. 現在の状態を確認
            success, status_output, _ = self._run_git_command(["status", "--porcelain"])
            if not success:
                return {"success": False, "error": "Failed to check git status"}
            
            # 2. 変更がある場合は自動stash
            if status_output.strip():
                logger.info("Unstaged changes detected, stashing...")
                stash_success, _, stash_error = self._run_git_command([
                    "stash", "push", "-m", "Auto-stash before PR creation"
                ])
                if not stash_success:
                    return {"success": False, "error": f"Failed to stash changes: {stash_error}"}
                return {
                    "success": True, 
                    "action": "stashed", 
                    "message": "Changes stashed successfully"
                }
            
            return {"success": True, "action": "clean", "message": "Working directory is clean"}
            
        except Exception as e:
            logger.error(f"Error ensuring clean git state: {e}")
            return {"success": False, "error": str(e)}

    def safe_git_pull(self, remote: str = "origin", branch: str = "main") -> Dict[str, Any]:
        """安全なGit pull実行（rebaseエラーを回避）"""
        try:
            # 1. まずGit状態をクリーンアップ
            cleanup_result = self.ensure_git_state_is_clean()
            if not cleanup_result["success"]:
                return cleanup_result
            
            # 2. リモートから最新情報を取得
            fetch_success, _, fetch_error = self._run_git_command(["fetch", remote, branch])
            if not fetch_success:
                return {
                    "success": False, 
                    "error": f"Failed to fetch from {remote}/{branch}: {fetch_error}"
                }
            
            # 3. 現在のブランチを確認
            branch_success, current_branch, _ = self._run_git_command(["branch", "--show-current"])
            if not branch_success:
                return {"success": False, "error": "Failed to get current branch"}
            
            # 4. 対象ブランチにいない場合は切り替え
            if current_branch != branch:
                checkout_success, _, checkout_error = self._run_git_command(["checkout", branch])
                if not checkout_success:
                    return {
                        "success": False, 
                        "error": f"Failed to checkout {branch}: {checkout_error}"
                    }
            
            # 5. merge を使ってpull（rebaseを避ける）
            merge_success, merge_output, merge_error = self._run_git_command([
                "merge", f"{remote}/{branch}"
            ])
            if not merge_success:
                return {
                    "success": False, 
                    "error": f"Failed to merge {remote}/{branch}: {merge_error}"
                }
            
            return {
                "success": True, 
                "action": "pulled",
                "message": f"Successfully pulled from {remote}/{branch}",
                "cleanup_action": cleanup_result.get("action"),
                "merge_output": merge_output
            }
            
        except Exception as e:
            logger.error(f"Error during safe git pull: {e}")
            return {"success": False, "error": str(e)}

    def create_feature_branch_safely(self, branch_name: str, base_branch: str = "main") -> Dict[str, Any]:
        """安全なfeatureブランチ作成"""
        try:
            # 1. 既存のブランチを確認・削除
            branch_check_success, branch_list, _ = self._run_git_command(["branch", "-a"])
            if branch_check_success and branch_name in branch_list:
                logger.info(f"Branch {branch_name} already exists, deleting...")
                
                # ローカルブランチを削除
                local_delete_success, _, _ = self._run_git_command(["branch", "-D", branch_name])
                if local_delete_success:
                    logger.info(f"Local branch {branch_name} deleted")
                
                # リモートブランチを削除（エラーは無視）
                self._run_git_command(["push", "origin", "--delete", branch_name])
            
            # 2. ベースブランチに切り替え
            checkout_success, _, checkout_error = self._run_git_command(["checkout", base_branch])
            if not checkout_success:
                return {
                    "success": False, 
                    "error": f"Failed to checkout {base_branch}: {checkout_error}"
                }
            
            # 3. 最新状態に更新
            pull_result = self.safe_git_pull("origin", base_branch)
            if not pull_result["success"]:
                return pull_result
            
            # 4. 新しいブランチを作成
            create_success, _, create_error = self._run_git_command(["checkout", "-b", branch_name])
            if not create_success:
                return {
                    "success": False, 
                    "error": f"Failed to create branch {branch_name}: {create_error}"
                }
            
            return {
                "success": True,
                "branch_name": branch_name,
                "base_branch": base_branch,
                "message": f"Successfully created branch {branch_name} from {base_branch}"
            }
            
        except Exception as e:
            logger.error(f"Error creating feature branch: {e}")
            return {"success": False, "error": str(e)}

    def auto_commit_if_changes(self, message: str) -> Dict[str, Any]:
        """変更がある場合の自動コミット"""
        try:
            # 1. 変更を確認
            status_success, status_output, _ = self._run_git_command(["status", "--porcelain"])
            if not status_success:
                return {"success": False, "error": "Failed to check git status"}
            
            if not status_output.strip():
                return {"success": True, "action": "no_changes", "message": "No changes to commit"}
            
            # 2. 全ての変更をadd
            add_success, _, add_error = self._run_git_command(["add", "-A"])
            if not add_success:
                return {"success": False, "error": f"Failed to add changes: {add_error}"}
            
            # 3. コミット
            commit_message = (
                f"{message}\n\n"
                "🤖 Generated with [Claude Code](https://claude.ai/code)\n\n"
                "Co-Authored-By: Claude <noreply@anthropic.com>"
            )
            commit_success, commit_output, commit_error = self._run_git_command([
                "commit", "-m", commit_message
            ])
            if not commit_success:
                return {"success": False, "error": f"Failed to commit: {commit_error}"}
            
            return {
                "success": True,
                "action": "committed",
                "message": "Changes committed successfully",
                "commit_output": commit_output
            }
            
        except Exception as e:
            logger.error(f"Error in auto commit: {e}")
            return {"success": False, "error": str(e)}

    def push_branch_safely(self, branch_name: str, remote: str = "origin") -> Dict[str, Any]:
        """安全なブランチプッシュ"""
        try:
            # upstream を設定してプッシュ
            push_success, push_output, push_error = self._run_git_command([
                "push", "-u", remote, branch_name
            ])
            
            if not push_success:
                return {
                    "success": False, 
                    "error": f"Failed to push branch {branch_name}: {push_error}"
                }
            
            return {
                "success": True,
                "message": f"Branch {branch_name} pushed successfully to {remote}",
                "push_output": push_output
            }
            
        except Exception as e:
            logger.error(f"Error pushing branch: {e}")
            return {"success": False, "error": str(e)}

    def get_current_branch(self) -> Dict[str, Any]:
        """現在のブランチを取得"""
        try:
            success, branch_name, error = self._run_git_command(["branch", "--show-current"])
            if not success:
                return {"success": False, "error": f"Failed to get current branch: {error}"}
            
            return {"success": True, "branch": branch_name}
        except Exception as e:
            logger.error(f"Error getting current branch: {e}")
            return {"success": False, "error": str(e)}

    def restore_original_branch(self, original_branch: str) -> Dict[str, Any]:
        """元のブランチに戻る"""
        try:
            if not original_branch:
                return {"success": True, "message": "No original branch to restore"}
            
            checkout_success, _, checkout_error = self._run_git_command(["checkout", original_branch])
            if not checkout_success:
                return {
                    "success": False, 
                    "error": f"Failed to restore to {original_branch}: {checkout_error}"
                }
            
            return {
                "success": True,
                "message": f"Successfully restored to branch {original_branch}"
            }
            
        except Exception as e:
            logger.error(f"Error restoring branch: {e}")
            return {"success": False, "error": str(e)}

    def create_pr_branch_workflow(
        self, 
        pr_title: str, 
        base_branch: str = "main",
        branch_prefix: str = "auto-fix"
    ) -> Dict[str, Any]:
        """PR作成のための完全ワークフロー"""
        try:
            # 1. 現在のブランチを保存
            current_branch_result = self.get_current_branch()
            original_branch = (
                current_branch_result.get("branch") 
                if current_branch_result["success"] 
                else None
            )
            
            # 2. ブランチ名を生成
            import re
            from datetime import datetime
            safe_title = re.sub(r'[^a-zA-Z0-9\-_]', '-', pr_title.lower())
            safe_title = re.sub(r'-+', '-', safe_title).strip('-')[:50]
            timestamp = datetime.now().strftime("%m%d-%H%M")
            branch_name = f"{branch_prefix}/{safe_title}-{timestamp}"
            
            # 3. 安全にブランチを作成
            branch_result = self.create_feature_branch_safely(branch_name, base_branch)
            if not branch_result["success"]:
                # 失敗時は元のブランチに戻る
                self.restore_original_branch(original_branch)
                return {
                    "success": False,
                    "error": f"Failed to create branch: {branch_result['error']}",
                    "original_branch": original_branch
                }
            
            # 4. 変更をコミット
            commit_result = self.auto_commit_if_changes(f"fix: {pr_title}")
            
            # 5. ブランチをプッシュ
            push_result = self.push_branch_safely(branch_name)
            if not push_result["success"]:
                # 失敗時は元のブランチに戻る
                self.restore_original_branch(original_branch)
                return {
                    "success": False,
                    "error": f"Failed to push branch: {push_result['error']}",
                    "branch_name": branch_name,
                    "original_branch": original_branch
                }
            
            return {
                "success": True,
                "branch_name": branch_name,
                "base_branch": base_branch,
                "original_branch": original_branch,
                "branch_result": branch_result,
                "commit_result": commit_result,
                "push_result": push_result,
                "message": f"PR branch workflow completed successfully for {branch_name}"
            }
            
        except Exception as e:
            logger.error(f"Error in PR branch workflow: {e}")
            # エラー時は元のブランチに戻る
            if 'original_branch' in locals():
                self.restore_original_branch(original_branch)
            return {"success": False, "error": str(e)}


# Global instance for easy use
safe_git = SafeGitOperations()


# Helper functions
def ensure_clean_git_state() -> Dict[str, Any]:
    """Git状態をクリーンにする"""
    return safe_git.ensure_git_state_is_clean()


def safe_pull(remote: str = "origin", branch: str = "main") -> Dict[str, Any]:
    """安全なGit pull"""
    return safe_git.safe_git_pull(remote, branch)


def create_pr_branch(title: str, base: str = "main") -> Dict[str, Any]:
    """PR用ブランチ作成の完全ワークフロー"""
    return safe_git.create_pr_branch_workflow(title, base)


def restore_branch(branch_name: str) -> Dict[str, Any]:
    """指定ブランチに戻る"""
    return safe_git.restore_original_branch(branch_name)


if __name__ == "__main__":
    # テスト実行
    def test_safe_git_operations():
        print("🧪 Testing SafeGitOperations...")
        
        # Git状態確認
        clean_result = ensure_clean_git_state()
        print(f"Clean state: {clean_result}")
        
        # 現在のブランチ確認
        current_result = safe_git.get_current_branch()
        print(f"Current branch: {current_result}")
        
        print("SafeGitOperations test completed!")
    
    test_safe_git_operations()