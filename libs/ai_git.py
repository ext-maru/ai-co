#!/usr/bin/env python3
"""
AI-Driven Git Automation System
エルダーズギルド AI駆動Git自動化システム

Created by Claude Elder
Version: 1.0.0
"""

import os
import subprocess
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re

logger = logging.getLogger(__name__)


@dataclass
class GitStatus:
    """Git状態情報"""

    is_repo: bool
    has_changes: bool
    staged_files: List[str]
    unstaged_files: List[str]
    untracked_files: List[str]
    branch: str
    commit_hash: str
    remote_ahead: int = 0
    remote_behind: int = 0


@dataclass
class CommitAnalysis:
    """コミット分析結果"""

    commit_type: str
    scope: Optional[str]
    description: str
    breaking_change: bool
    files_changed: List[str]
    confidence: float


class AIGitManager:
    """AI駆動Git自動化システム"""

    COMMIT_TYPES = {
        "feat": "A new feature",
        "fix": "A bug fix",
        "docs": "Documentation only changes",
        "style": "Changes that do not affect the meaning of the code",
        "refactor": "A code change that neither fixes a bug nor adds a feature",
        "perf": "A code change that improves performance",
        "test": "Adding missing tests or correcting existing tests",
        "build": "Changes that affect the build system or external dependencies",
        "ci": "Changes to our CI configuration files and scripts",
        "chore": "Other changes that do not modify src or test files",
        "revert": "Reverts a previous commit",
    }

    def __init__(self, repo_path: str = "."):
        """初期化メソッド"""
        self.repo_path = Path(repo_path)
        self.logger = logging.getLogger(__name__)

    def get_git_status(self) -> GitStatus:
        """Git状態を詳細取得"""
        try:
            # リポジトリかどうか確認
            is_repo = self._is_git_repo()
            if not is_repo:
                return GitStatus(
                    is_repo=False,
                    has_changes=False,
                    staged_files=[],
                    unstaged_files=[],
                    untracked_files=[],
                    branch="",
                    commit_hash="",
                )

            # ブランチ取得
            branch = self._get_current_branch()

            # コミットハッシュ取得
            commit_hash = self._get_current_commit()

            # ファイル状態取得
            staged, unstaged, untracked = self._get_file_status()

            # リモートとの差分
            ahead, behind = self._get_remote_diff()

            return GitStatus(
                is_repo=True,
                has_changes=bool(staged or unstaged or untracked),
                staged_files=staged,
                unstaged_files=unstaged,
                untracked_files=untracked,
                branch=branch,
                commit_hash=commit_hash,
                remote_ahead=ahead,
                remote_behind=behind,
            )

        except Exception as e:
            self.logger.error(f"Git status check failed: {e}")
            return GitStatus(
                is_repo=False,
                has_changes=False,
                staged_files=[],
                unstaged_files=[],
                untracked_files=[],
                branch="",
                commit_hash="",
            )

    def _is_git_repo(self) -> bool:
        """Gitリポジトリかどうか確認"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
            )
            return result.returncode == 0
        except:
            return False

    def _get_current_branch(self) -> str:
        """現在のブランチ取得"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except:
            return "unknown"

    def _get_current_commit(self) -> str:
        """現在のコミットハッシュ取得"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()[:8]  # 短縮形
        except:
            return "unknown"

    def _get_file_status(self) -> Tuple[List[str], List[str], List[str]]:
        """ファイル状態取得（staged, unstaged, untracked）"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            staged, unstaged, untracked = [], [], []

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                status = line[:2]
                filename = line[3:]

                if status[0] != " " and status[0] != "?":
                    staged.append(filename)
                if status[1] != " " and status[1] != "?":
                    unstaged.append(filename)
                if status.startswith("??"):
                    untracked.append(filename)

            return staged, unstaged, untracked

        except:
            return [], [], []

    def _get_remote_diff(self) -> Tuple[int, int]:
        """リモートとの差分（ahead, behind）"""
        try:
            result = subprocess.run(
                ["git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                ahead, behind = map(int, result.stdout.strip().split())
                return ahead, behind
        except:
            pass
        return 0, 0

    def analyze_changes_for_commit(self, files: List[str] = None) -> CommitAnalysis:
        """変更内容を分析してコミットタイプを推定"""
        if not files:
            status = self.get_git_status()
            files = status.staged_files + status.unstaged_files

        # ファイル別分析
        file_types = self._categorize_files(files)

        # 変更内容分析
        diff_analysis = self._analyze_diff(files)

        # コミットタイプ決定
        commit_type, confidence = self._determine_commit_type(file_types, diff_analysis)

        # スコープ推定
        scope = self._estimate_scope(files, file_types)

        # 説明生成
        description = self._generate_description(commit_type, files, diff_analysis)

        # 破壊的変更検出
        breaking_change = self._detect_breaking_change(diff_analysis)

        return CommitAnalysis(
            commit_type=commit_type,
            scope=scope,
            description=description,
            breaking_change=breaking_change,
            files_changed=files,
            confidence=confidence,
        )

    def _categorize_files(self, files: List[str]) -> Dict[str, List[str]]:
        """ファイルをカテゴリ別に分類"""
        categories = {
            "source": [],
            "test": [],
            "docs": [],
            "config": [],
            "build": [],
            "ci": [],
            "other": [],
        }

        for file in files:
            file_lower = file.lower()

            if file_lower.endswith((".py", ".js", ".ts", ".java", ".cpp", ".c", ".go")):
                if "test" in file_lower or file_lower.startswith("test_"):
                    categories["test"].append(file)
                else:
                    categories["source"].append(file)
            elif file_lower.endswith((".md", ".rst", ".txt", ".pdf")):
                categories["docs"].append(file)
            elif file_lower in (
                "dockerfile",
                "requirements.txt",
                "package.json",
                "cargo.toml",
            ):
                categories["build"].append(file)
            elif file_lower.endswith((".yml", ".yaml")) and (
                "ci" in file_lower or ".github" in file
            ):
                categories["ci"].append(file)
            elif file_lower.endswith(
                (".json", ".toml", ".yaml", ".yml", ".ini", ".cfg")
            ):
                categories["config"].append(file)
            else:
                categories["other"].append(file)

        return categories

    def _analyze_diff(self, files: List[str]) -> Dict[str, Any]:
        """差分内容を分析"""
        analysis = {
            "total_lines_added": 0,
            "total_lines_removed": 0,
            "functions_added": [],
            "functions_removed": [],
            "has_new_imports": False,
            "has_api_changes": False,
        }

        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--numstat"] + files,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        added = int(parts[0]) if parts[0] != "-" else 0
                        removed = int(parts[1]) if parts[1] != "-" else 0
                        analysis["total_lines_added"] += added
                        analysis["total_lines_removed"] += removed
        except:
            pass

        return analysis

    def _determine_commit_type(
        self, file_types: Dict[str, List[str]], diff_analysis: Dict[str, Any]
    ) -> Tuple[str, float]:
        """コミットタイプを決定"""
        scores = {}

        # ファイルタイプベースの判定
        if file_types["test"]:
            scores["test"] = 0.8
        if file_types["docs"]:
            scores["docs"] = 0.7
        if file_types["build"] or file_types["ci"]:
            scores["build"] = 0.6
        if file_types["config"]:
            scores["chore"] = 0.5

        # 差分内容ベースの判定
        total_changes = (
            diff_analysis["total_lines_added"] + diff_analysis["total_lines_removed"]
        )
        if total_changes > 100:
            if file_types["source"]:
                scores["feat"] = scores.get("feat", 0) + 0.6
        else:
            if file_types["source"]:
                scores["fix"] = scores.get("fix", 0) + 0.7

        # 最高スコアのタイプを選択
        if not scores:
            return "chore", 0.3

        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]

        return best_type, confidence

    def _estimate_scope(
        self, files: List[str], file_types: Dict[str, List[str]]
    ) -> Optional[str]:
        """スコープを推定"""
        # よくあるスコープパターン
        scopes = []

        for file in files:
            parts = file.split("/")
            if len(parts) > 1:
                if parts[0] in ["libs", "workers", "commands", "tests"]:
                    scopes.append(parts[0])
                elif len(parts) > 2 and parts[1] in ["elder", "sage", "flow"]:
                    scopes.append(parts[1])

        # 最も頻繁なスコープを返す
        if scopes:
            return max(set(scopes), key=scopes.count)

        return None

    def _generate_description(
        self, commit_type: str, files: List[str], diff_analysis: Dict[str, Any]
    ) -> str:
        """説明文を生成"""
        if len(files) == 1:
            file_name = Path(files[0]).stem
            return f"{commit_type} {file_name}"
        elif len(files) <= 3:
            file_names = [Path(f).stem for f in files]
            return f"{commit_type} {', '.join(file_names)}"
        else:
            total_changes = (
                diff_analysis["total_lines_added"]
                + diff_analysis["total_lines_removed"]
            )
            return f"{commit_type} {len(files)} files ({total_changes} lines changed)"

    def _detect_breaking_change(self, diff_analysis: Dict[str, Any]) -> bool:
        """破壊的変更を検出"""
        # 大量の削除は破壊的変更の可能性
        if diff_analysis["total_lines_removed"] > 50:
            return True

        # API変更の検出は今後実装
        return False

    def create_smart_commit(
        self, message: str = None, auto_add: bool = True
    ) -> Dict[str, Any]:
        """AI分析に基づくスマートコミット"""
        try:
            status = self.get_git_status()

            if not status.is_repo:
                return {"success": False, "message": "Not a git repository"}

            if not status.has_changes:
                return {"success": False, "message": "No changes to commit"}

            # 自動ステージング
            if auto_add and (status.unstaged_files or status.untracked_files):
                subprocess.run(["git", "add", "."], cwd=self.repo_path)
                status = self.get_git_status()  # 再取得

            if not status.staged_files:
                return {"success": False, "message": "No staged changes"}

            # 変更分析
            analysis = self.analyze_changes_for_commit(status.staged_files)

            # メッセージ生成
            if not message:
                from libs.commit_message_generator import generate_conventional_commit

                message = generate_conventional_commit(analysis)

            # コミット実行
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": message,
                    "commit_hash": self._get_current_commit(),
                    "files_committed": status.staged_files,
                    "analysis": analysis,
                }
            else:
                return {"success": False, "message": f"Commit failed: {result.stderr}"}

        except Exception as e:
            self.logger.error(f"Smart commit failed: {e}")
            return {"success": False, "message": f"Error: {e}"}


# グローバルインスタンス
ai_git_manager = AIGitManager()


# 便利な関数
def get_git_status() -> GitStatus:
    """Git状態取得"""
    return ai_git_manager.get_git_status()


def analyze_for_commit(files: List[str] = None) -> CommitAnalysis:
    """変更分析"""
    return ai_git_manager.analyze_changes_for_commit(files)


def smart_commit(message: str = None, auto_add: bool = True) -> Dict[str, Any]:
    """スマートコミット"""
    return ai_git_manager.create_smart_commit(message, auto_add)


if __name__ == "__main__":
    print("🤖 AI-Driven Git Automation System")
    print("=" * 50)

    # 状態確認
    status = get_git_status()
    print(f"Git Repository: {status.is_repo}")
    print(f"Current Branch: {status.branch}")
    print(f"Has Changes: {status.has_changes}")
    print(f"Staged Files: {len(status.staged_files)}")
    print(f"Unstaged Files: {len(status.unstaged_files)}")
    print(f"Untracked Files: {len(status.untracked_files)}")

    if status.has_changes:
        print("\n🔍 Analyzing changes...")
        analysis = analyze_for_commit()
        print(f"Commit Type: {analysis.commit_type}")
        print(f"Scope: {analysis.scope}")
        print(f"Confidence: {analysis.confidence:.2f}")
        print(f"Description: {analysis.description}")
