"""
Elder Flow Git Automator - Git自動化システム
Created: 2025-07-12
Author: Claude Elder
Version: 1.0.0
"""

import subprocess
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
from pathlib import Path
import json
import re
from libs.elder_flow_pre_commit_handler import ElderFlowPreCommitHandler

# Git Operation Types
class GitOperation(Enum):
    STATUS = "status"
    ADD = "add"
    COMMIT = "commit"
    PUSH = "push"
    PULL = "pull"
    BRANCH = "branch"
    MERGE = "merge"
    TAG = "tag"
    DIFF = "diff"
    LOG = "log"

# Git Status
class GitStatus(Enum):
    CLEAN = "clean"
    MODIFIED = "modified"
    STAGED = "staged"
    UNTRACKED = "untracked"
    CONFLICTED = "conflicted"

# Commit Types (Conventional Commits)
class CommitType(Enum):
    FEAT = "feat"        # 新機能
    FIX = "fix"          # バグ修正
    DOCS = "docs"        # ドキュメント
    STYLE = "style"      # コードスタイル
    REFACTOR = "refactor" # リファクタリング
    PERF = "perf"        # パフォーマンス改善
    TEST = "test"        # テスト
    CHORE = "chore"      # 雑務
    CI = "ci"            # CI/CD
    BUILD = "build"      # ビルド

# Git Automator
class ElderFlowGitAutomator:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.logger = logging.getLogger(__name__)

        # Pre-commitハンドラー初期化
        self.pre_commit_handler = ElderFlowPreCommitHandler(str(self.repo_path))

        # Git設定確認
        self._verify_git_repo()

    def _verify_git_repo(self):
        """Git リポジトリ確認"""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")

    def _run_git_command(self, command: List[str], capture_output: bool = True) -> Tuple[bool, str, str]:
        """Git コマンド実行"""
        full_command = ["git"] + command

        try:
            self.logger.debug(f"Running git command: {' '.join(full_command)}")

            result = subprocess.run(
                full_command,
                cwd=self.repo_path,
                capture_output=capture_output,
                text=True,
                timeout=60
            )

            success = result.returncode == 0
            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""

            if not success:
                self.logger.error(f"Git command failed: {stderr}")

            return success, stdout, stderr

        except subprocess.TimeoutExpired:
            self.logger.error("Git command timed out")
            return False, "", "Command timed out"
        except Exception as e:
            self.logger.error(f"Git command error: {str(e)}")
            return False, "", str(e)

    def get_status(self) -> Dict:
        """Git ステータス取得"""
        success, stdout, stderr = self._run_git_command(["status", "--porcelain"])

        if not success:
            return {"error": stderr}

        # ファイル状態解析
        modified_files = []
        staged_files = []
        untracked_files = []

        for line in stdout.split('\n'):
            if not line.strip():
                continue

            status_code = line[:2]
            filename = line[3:].strip()

            if status_code.startswith('M'):
                if status_code[0] == 'M':
                    staged_files.append(filename)
                if status_code[1] == 'M':
                    modified_files.append(filename)
            elif status_code.startswith('A'):
                staged_files.append(filename)
            elif status_code.startswith('D'):
                if status_code[0] == 'D':
                    staged_files.append(filename)
                if status_code[1] == 'D':
                    modified_files.append(filename)
            elif status_code.startswith('??'):
                untracked_files.append(filename)

        # ブランチ情報取得
        branch_success, branch_stdout, _ = self._run_git_command(["branch", "--show-current"])
        current_branch = branch_stdout if branch_success else "unknown"

        return {
            "current_branch": current_branch,
            "modified_files": modified_files,
            "staged_files": staged_files,
            "untracked_files": untracked_files,
            "is_clean": len(modified_files) == 0 and len(staged_files) == 0 and len(untracked_files) == 0,
            "total_changes": len(modified_files) + len(staged_files) + len(untracked_files)
        }

    def add_files(self, files: List[str] = None, add_all: bool = False) -> Dict:
        """ファイル追加"""
        if add_all:
            success, stdout, stderr = self._run_git_command(["add", "."])
        elif files:
            success, stdout, stderr = self._run_git_command(["add"] + files)
        else:
            return {"error": "No files specified and add_all is False"}

        if not success:
            return {"error": stderr}

        # 追加後のステータス確認
        status = self.get_status()

        return {
            "success": True,
            "added_files": files if files else "all files",
            "staged_files": status.get("staged_files", []),
            "message": f"Added {len(status.get('staged_files', []))} files to staging area"
        }

    def commit(self, message: str, commit_type: CommitType = None,
               scope: str = None, description: str = None, auto_fix: bool = True) -> Dict:
        """コミット実行（pre-commit自動修復付き）"""
        # コミットメッセージ生成
        if commit_type:
            formatted_message = self._format_commit_message(commit_type, scope, message, description)
        else:
            formatted_message = message

        # Pre-commit自動修復を有効にしてコミット実行
        if auto_fix:
            success, stdout, stderr = self.pre_commit_handler.run_with_auto_fix(
                ["git", "commit", "-m", formatted_message]
            )
        else:
            success, stdout, stderr = self._run_git_command(["commit", "-m", formatted_message])

        if not success:
            return {"error": stderr, "pre_commit_fixed": auto_fix}

        # コミット情報取得
        commit_hash_success, commit_hash, _ = self._run_git_command(["rev-parse", "HEAD"])
        commit_short_hash = commit_hash[:8] if commit_hash_success else "unknown"

        return {
            "success": True,
            "commit_hash": commit_hash if commit_hash_success else "unknown",
            "commit_short_hash": commit_short_hash,
            "message": formatted_message,
            "timestamp": datetime.now().isoformat(),
            "pre_commit_fixed": auto_fix
        }

    def _format_commit_message(self, commit_type: CommitType, scope: str,
                              message: str, description: str = None) -> str:
        """コミットメッセージフォーマット"""
        # Conventional Commits形式
        formatted = f"{commit_type.value}"

        if scope:
            formatted += f"({scope})"

        formatted += f": {message}"

        if description:
            formatted += f"\n\n{description}"

        # Claude Elder署名追加
        formatted += "\n\n🤖 Generated with Elder Flow\n\nCo-Authored-By: Claude Elder <elder@elders-guild.ai>"

        return formatted

    def push(self, remote: str = "origin", branch: str = None, auto_fix: bool = True) -> Dict:
        """プッシュ実行（pre-commit自動修復付き）"""
        if not branch:
            # 現在のブランチ取得
            success, current_branch, _ = self._run_git_command(["branch", "--show-current"])
            branch = current_branch if success else "main"

        # Pre-commit自動修復を有効にしてプッシュ実行
        if auto_fix:
            success, stdout, stderr = self.pre_commit_handler.run_with_auto_fix(
                ["git", "push", remote, branch]
            )
        else:
            success, stdout, stderr = self._run_git_command(["push", remote, branch])

        if not success:
            return {"error": stderr, "pre_commit_fixed": auto_fix}

        return {
            "success": True,
            "remote": remote,
            "branch": branch,
            "message": f"Successfully pushed to {remote}/{branch}",
            "pre_commit_fixed": auto_fix
        }

    def pull(self, remote: str = "origin", branch: str = None) -> Dict:
        """プル実行"""
        if not branch:
            # 現在のブランチ取得
            success, current_branch, _ = self._run_git_command(["branch", "--show-current"])
            branch = current_branch if success else "main"

        success, stdout, stderr = self._run_git_command(["pull", remote, branch])

        if not success:
            return {"error": stderr}

        return {
            "success": True,
            "remote": remote,
            "branch": branch,
            "output": stdout,
            "message": f"Successfully pulled from {remote}/{branch}"
        }

    def create_branch(self, branch_name: str, checkout: bool = True) -> Dict:
        """ブランチ作成"""
        # ブランチ作成
        success, stdout, stderr = self._run_git_command(["branch", branch_name])

        if not success:
            return {"error": stderr}

        # チェックアウト
        if checkout:
            checkout_success, checkout_stdout, checkout_stderr = self._run_git_command(["checkout", branch_name])
            if not checkout_success:
                return {"error": f"Branch created but checkout failed: {checkout_stderr}"}

        return {
            "success": True,
            "branch_name": branch_name,
            "checked_out": checkout,
            "message": f"Branch '{branch_name}' created" + (" and checked out" if checkout else "")
        }

    def get_diff(self, staged: bool = False, files: List[str] = None) -> Dict:
        """差分取得"""
        command = ["diff"]

        if staged:
            command.append("--cached")

        if files:
            command.extend(files)

        success, stdout, stderr = self._run_git_command(command)

        if not success:
            return {"error": stderr}

        return {
            "success": True,
            "diff": stdout,
            "staged": staged,
            "files": files or "all files"
        }

    def get_log(self, count: int = 10, oneline: bool = False) -> Dict:
        """ログ取得"""
        command = ["log", f"-{count}"]

        if oneline:
            command.append("--oneline")

        success, stdout, stderr = self._run_git_command(command)

        if not success:
            return {"error": stderr}

        return {
            "success": True,
            "log": stdout,
            "count": count,
            "oneline": oneline
        }

    def get_remote_info(self) -> Dict:
        """リモート情報取得"""
        success, stdout, stderr = self._run_git_command(["remote", "-v"])

        if not success:
            return {"error": stderr}

        remotes = {}
        for line in stdout.split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    remote_name = parts[0]
                    remote_url = parts[1]
                    remote_type = parts[2].strip('()')

                    if remote_name not in remotes:
                        remotes[remote_name] = {}
                    remotes[remote_name][remote_type] = remote_url

        return {
            "success": True,
            "remotes": remotes
        }

    def auto_commit_and_push(self, message: str, commit_type: CommitType = CommitType.FEAT,
                            scope: str = None, add_all: bool = True) -> Dict:
        """自動コミット&プッシュ"""
        results = {
            "steps": [],
            "success": False,
            "final_message": ""
        }

        try:
            # Step 1: ステータス確認
            status = self.get_status()
            results["steps"].append({"step": "status", "result": status})

            if status.get("is_clean", False):
                results["final_message"] = "No changes to commit"
                results["success"] = True
                return results

            # Step 2: ファイル追加
            add_result = self.add_files(add_all=add_all)
            results["steps"].append({"step": "add", "result": add_result})

            if not add_result.get("success", False):
                results["final_message"] = f"Failed to add files: {add_result.get('error', 'Unknown error')}"
                return results

            # Step 3: コミット
            commit_result = self.commit(message, commit_type, scope)
            results["steps"].append({"step": "commit", "result": commit_result})

            if not commit_result.get("success", False):
                results["final_message"] = f"Failed to commit: {commit_result.get('error', 'Unknown error')}"
                return results

            # Step 4: プッシュ
            push_result = self.push()
            results["steps"].append({"step": "push", "result": push_result})

            if not push_result.get("success", False):
                results["final_message"] = f"Failed to push: {push_result.get('error', 'Unknown error')}"
                return results

            # 成功
            results["success"] = True
            results["final_message"] = f"Successfully committed and pushed: {commit_result.get('commit_short_hash', 'unknown')}"
            results["commit_hash"] = commit_result.get("commit_hash", "unknown")

        except Exception as e:
            results["final_message"] = f"Unexpected error: {str(e)}"
            self.logger.error(f"Auto commit and push failed: {str(e)}")

        return results

    def validate_commit_message(self, message: str) -> Dict:
        """コミットメッセージ検証"""
        # Conventional Commits形式チェック
        conventional_pattern = r'^(feat|fix|docs|style|refactor|perf|test|chore|ci|build)(\(.+\))?: .{1,50}'

        is_conventional = bool(re.match(conventional_pattern, message))

        # 基本的な検証
        issues = []

        if len(message) < 10:
            issues.append("Commit message is too short")

        if len(message) > 72:
            issues.append("First line of commit message is too long")

        if not message[0].isupper() and not is_conventional:
            issues.append("Commit message should start with uppercase letter")

        if message.endswith('.'):
            issues.append("Commit message should not end with period")

        return {
            "valid": len(issues) == 0,
            "is_conventional": is_conventional,
            "issues": issues,
            "message": message
        }

    def get_repository_info(self) -> Dict:
        """リポジトリ情報取得"""
        info = {}

        # 現在のブランチ
        branch_success, branch, _ = self._run_git_command(["branch", "--show-current"])
        info["current_branch"] = branch if branch_success else "unknown"

        # 最新コミット
        commit_success, commit_hash, _ = self._run_git_command(["rev-parse", "HEAD"])
        info["latest_commit"] = commit_hash if commit_success else "unknown"

        # リモート情報
        remote_info = self.get_remote_info()
        info["remotes"] = remote_info.get("remotes", {})

        # ステータス
        status = self.get_status()
        info["status"] = status

        # 統計
        stats_success, stats, _ = self._run_git_command(["rev-list", "--count", "HEAD"])
        info["total_commits"] = int(stats) if stats_success and stats.isdigit() else 0

        return info

# Global automator instance
automator = ElderFlowGitAutomator()

# Helper functions
def auto_commit_and_push(message: str, commit_type: CommitType = CommitType.FEAT,
                        scope: str = None, add_all: bool = True) -> Dict:
    """自動コミット&プッシュ"""
    return automator.auto_commit_and_push(message, commit_type, scope, add_all)

def get_git_status() -> Dict:
    """Gitステータス取得"""
    return automator.get_status()

def validate_commit_message(message: str) -> Dict:
    """コミットメッセージ検証"""
    return automator.validate_commit_message(message)

def get_repository_info() -> Dict:
    """リポジトリ情報取得"""
    return automator.get_repository_info()

# Example usage
if __name__ == "__main__":
    def main():
        print("📤 Elder Flow Git Automator Test")

        # リポジトリ情報表示
        repo_info = get_repository_info()
        print(f"Current branch: {repo_info['current_branch']}")
        print(f"Total commits: {repo_info['total_commits']}")
        print(f"Status: {'Clean' if repo_info['status']['is_clean'] else 'Has changes'}")

        # ステータス表示
        status = get_git_status()
        print(f"Modified files: {len(status['modified_files'])}")
        print(f"Staged files: {len(status['staged_files'])}")
        print(f"Untracked files: {len(status['untracked_files'])}")

        # コミットメッセージ検証
        test_message = "feat(elder-flow): implement git automation system"
        validation = validate_commit_message(test_message)
        print(f"Message valid: {validation['valid']}")
        print(f"Is conventional: {validation['is_conventional']}")

        # Note: 実際のコミット&プッシュはテスト時は実行しない
        print("Git Automator initialized successfully!")

    main()
