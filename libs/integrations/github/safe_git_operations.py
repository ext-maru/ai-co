#!/usr/bin/env python3
"""
安全なGit操作ユーティリティ

unstaged changesエラーやブランチ作成の問題を回避するための
安全なGit操作を提供します。
"""

import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SafeGitOperations:
    """安全なGit操作を提供するクラス"""
    
    def __init__(self, repo_path: str = None):
        """
        初期化
        
        Args:
            repo_path: リポジトリパス（省略時はカレントディレクトリ）
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        
    def _run_git_command(self, cmd: list, check: bool = True) -> Dict[str, Any]:
        """
        Gitコマンドを実行
        
        Args:
            cmd: コマンドリスト
            check: エラーチェックを行うか
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        try:
            result = subprocess.run(
                ["git"] + cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=check
            )
            return {
                "success": True,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "stdout": e.stdout.strip() if e.stdout else "",
                "stderr": e.stderr.strip() if e.stderr else "",
                "returncode": e.returncode,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "returncode": -1
            }
    
    def stash_changes(self) -> Dict[str, Any]:
        """未コミットの変更を一時保存"""
        logger.info("Stashing uncommitted changes...")
        return self._run_git_command(["stash", "push", "-m", f"Auto-stash {datetime.now().isoformat()}"])
    
    def stash_pop(self) -> Dict[str, Any]:
        """一時保存した変更を復元"""
        logger.info("Restoring stashed changes...")
        return self._run_git_command(["stash", "pop"], check=False)
    
    def get_current_branch(self) -> str:
        """現在のブランチ名を取得"""
        result = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        return result["stdout"] if result["success"] else ""
    
    def checkout_branch(self, branch: str) -> Dict[str, Any]:
        """ブランチをチェックアウト"""
        logger.info(f"Checking out branch: {branch}")
        return self._run_git_command(["checkout", branch])
    
    def create_branch(self, branch_name: str, base_branch: str = "main") -> Dict[str, Any]:
        """新しいブランチを作成"""
        logger.info(f"Creating branch: {branch_name} from {base_branch}")
        
        # ベースブランチに切り替え
        checkout_result = self.checkout_branch(base_branch)
        if not checkout_result["success"]:
            return checkout_result
        
        # 最新を取得
        pull_result = self._run_git_command(["pull", "origin", base_branch])
        if not pull_result["success"]:
            logger.warning(f"Pull failed, continuing anyway: {pull_result.get('stderr')}")
        
        # ブランチ作成
        return self._run_git_command(["checkout", "-b", branch_name])
    
    def delete_branch(self, branch_name: str, force: bool = False) -> Dict[str, Any]:
        """ブランチを削除"""
        logger.info(f"Deleting branch: {branch_name}")
        cmd = ["branch", "-D" if force else "-d", branch_name]
        return self._run_git_command(cmd, check=False)
    
    def commit_changes(self, message: str, files: list = None) -> Dict[str, Any]:
        """変更をコミット"""
        # ファイルを追加
        if files:
            for file in files:
                add_result = self._run_git_command(["add", file])
                if not add_result["success"]:
                    return add_result
        else:
            add_result = self._run_git_command(["add", "-A"])
            if not add_result["success"]:
                return add_result
        
        # コミット
        return self._run_git_command(["commit", "-m", message])
    
    def push_branch(self, branch_name: str, force: bool = False) -> Dict[str, Any]:
        """ブランチをプッシュ"""
        logger.info(f"Pushing branch: {branch_name}")
        cmd = ["push", "-u", "origin", branch_name]
        if force:
            cmd.insert(1, "-f")
        return self._run_git_command(cmd)
    
    def has_uncommitted_changes(self) -> bool:
        """未コミットの変更があるかチェック"""
        result = self._run_git_command(["status", "--porcelain"])
        return bool(result["stdout"]) if result["success"] else False
    
    def create_pr_branch_workflow(
        self, 
        pr_title: str, 
        base_branch: str = "main",
        branch_prefix: str = "auto-fix"
    ) -> Dict[str, Any]:
        """
        PR作成のための完全なブランチワークフロー
        
        Args:
            pr_title: PRタイトル
            base_branch: ベースブランチ
            branch_prefix: ブランチプレフィックス
            
        Returns:
            Dict[str, Any]: 処理結果
        """
        original_branch = self.get_current_branch()
        stashed = False
        
        try:
            # 1. 未コミットの変更を一時保存
            if self.has_uncommitted_changes():
                stash_result = self.stash_changes()
                if not stash_result["success"]:
                    return {
                        "success": False,
                        "error": f"Failed to stash changes: {stash_result.get('stderr')}",
                        "action": "stash_failed"
                    }
                stashed = True
            
            # 2. ブランチ名を生成（Issue番号を抽出）
            import re
            issue_match = re.search(r'#(\d+)', pr_title)
            issue_number = issue_match.group(1) if issue_match else "unknown"
            branch_name = f"{branch_prefix}-issue-{issue_number}"
            
            # 3. 既存ブランチを削除（存在する場合）
            self.delete_branch(branch_name, force=True)
            # リモートブランチも削除を試みる
            self._run_git_command(["push", "origin", "--delete", branch_name], check=False)
            
            # 4. 新しいブランチを作成
            create_result = self.create_branch(branch_name, base_branch)
            if not create_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to create branch: {create_result.get('stderr')}",
                    "action": "create_branch_failed"
                }
            
            return {
                "success": True,
                "branch_name": branch_name,
                "original_branch": original_branch,
                "stashed": stashed,
                "action": "branch_created"
            }
            
        except Exception as e:
            logger.error(f"Error in create_pr_branch_workflow: {e}")
            # エラー時は元のブランチに戻る
            self.checkout_branch(original_branch)
            if stashed:
                self.stash_pop()
            return {
                "success": False,
                "error": str(e),
                "action": "exception"
            }
    
    def restore_original_branch(self, original_branch: str, pop_stash: bool = True) -> Dict[str, Any]:
        """
        元のブランチに戻る
        
        Args:
            original_branch: 元のブランチ名
            pop_stash: スタッシュを復元するか
            
        Returns:
            Dict[str, Any]: 処理結果
        """
        try:
            # 元のブランチに戻る
            checkout_result = self.checkout_branch(original_branch)
            if not checkout_result["success"]:
                return checkout_result
            
            # スタッシュを復元
            if pop_stash:
                # スタッシュリストを確認
                stash_list = self._run_git_command(["stash", "list"])
                if stash_list["success"] and stash_list["stdout"]:
                    self.stash_pop()
            
            return {
                "success": True,
                "action": "restored",
                "branch": original_branch
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action": "restore_failed"
            }
    
    def auto_commit_if_changes(self, commit_message: str) -> Dict[str, Any]:
        """
        変更がある場合のみ自動コミット
        
        Args:
            commit_message: コミットメッセージ
            
        Returns:
            Dict[str, Any]: 処理結果
        """
        if not self.has_uncommitted_changes():
            return {
                "success": True,
                "action": "no_changes",
                "message": "No changes to commit"
            }
        
        # すべての変更を追加してコミット
        commit_result = self.commit_changes(commit_message)
        if commit_result["success"]:
            return {
                "success": True,
                "action": "committed",
                "message": "Changes committed successfully"
            }
        else:
            # pre-commit hookで変更された場合の再試行
            if "files were modified by this hook" in commit_result.get("stderr", ""):
                logger.info("Pre-commit hook modified files, retrying...")
                # 再度追加してコミット
                self._run_git_command(["add", "-A"])
                retry_result = self._run_git_command(["commit", "-m", commit_message])
                if retry_result["success"]:
                    return {
                        "success": True,
                        "action": "committed_after_hook",
                        "message": "Changes committed after pre-commit hook"
                    }
            
            return {
                "success": False,
                "error": commit_result.get("stderr", "Unknown error"),
                "action": "commit_failed"
            }
    
    def push_branch_safely(self, branch_name: str) -> Dict[str, Any]:
        """
        ブランチを安全にプッシュ
        
        Args:
            branch_name: ブランチ名
            
        Returns:
            Dict[str, Any]: 処理結果
        """
        push_result = self.push_branch(branch_name)
        if push_result["success"]:
            return {
                "success": True,
                "action": "pushed",
                "branch": branch_name
            }
        else:
            # プッシュ失敗時の詳細エラー
            error_msg = push_result.get("stderr", "")
            if "rejected" in error_msg:
                return {
                    "success": False,
                    "error": "Push rejected - branch may be protected or behind remote",
                    "action": "push_rejected",
                    "details": error_msg
                }
            else:
                return {
                    "success": False,
                    "error": error_msg or "Unknown push error",
                    "action": "push_failed"
                }