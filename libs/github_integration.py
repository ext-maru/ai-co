#!/usr/bin/env python3
"""
GitHub連携マネージャー（修正版）
"""
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


class GitHubIntegrationManager:
    def __init__(self, repo_url: str = None, token: str = None):
        self.repo_url = repo_url or self._get_repo_url()
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.api_base = "https://api.github.com"

        if self.repo_url:
            self._parse_repo_info()

    def _get_repo_url(self) -> Optional[str]:
        """現在のリポジトリURLを取得"""
        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

    def _parse_repo_info(self):
        """リポジトリ情報を解析"""
        if "github.com" in self.repo_url:
            if self.repo_url.startswith("git@"):
                parts = self.repo_url.split(":")[1].replace(".git", "").split("/")
            else:
                parts = (
                    self.repo_url.split("github.com/")[1].replace(".git", "").split("/")
                )

            self.owner = parts[0]
            self.repo = parts[1]
            self.api_repo_url = f"{self.api_base}/repos/{self.owner}/{self.repo}"
        else:
            self.owner = None
            self.repo = None
            self.api_repo_url = None

    def get_repository_structure(self, path: str = "") -> List[Dict]:
        """リポジトリの構造を取得（改善版）"""
        if not self.api_repo_url:
            logger.error("リポジトリ情報が設定されていません")
            return []

        headers = {"Authorization": f"token {self.token}"} if self.token else {}

        try:
            # Git Tree APIを使用（大量ファイル対応）
            # まず最新のコミットSHAを取得
            branch_url = f"{self.api_repo_url}/branches/master"
            branch_response = requests.get(branch_url, headers=headers)

            if branch_response.status_code != 200:
                logger.error(f"ブランチ情報取得エラー: {branch_response.status_code}")
                return []

            commit_sha = branch_response.json()["commit"]["sha"]

            # Tree APIでファイル一覧を取得
            tree_url = f"{self.api_repo_url}/git/trees/{commit_sha}?recursive=1"
            tree_response = requests.get(tree_url, headers=headers)

            if tree_response.status_code != 200:
                logger.error(f"Tree API エラー: {tree_response.status_code}")
                return []

            tree_data = tree_response.json()
            files = []

            # 指定されたパスでフィルタリング
            for item in tree_data.get("tree", []):
                if item["type"] == "blob":  # ファイルのみ
                    item_path = item["path"]
                    if path and not item_path.startswith(path + "/"):
                        continue

                    # venvなどの不要なディレクトリを除外
                    if any(
                        skip in item_path for skip in ["venv/", "__pycache__/", ".pyc"]
                    ):
                        continue

                    files.append(
                        {
                            "name": os.path.basename(item_path),
                            "path": item_path,
                            "type": "file",
                            "sha": item["sha"],
                            "size": item.get("size", 0),
                        }
                    )

            return files

        except Exception as e:
            logger.error(f"リポジトリ構造取得エラー: {e}")
            return []

    def get_file_content(self, file_path: str) -> Optional[str]:
        """ファイルの内容を取得（改善版）"""
        headers = {"Authorization": f"token {self.token}"} if self.token else {}

        try:
            # 直接Blob APIを使用する代わりに、raw contentを取得
            raw_url = f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/master/{file_path}"
            response = requests.get(raw_url, headers=headers)

            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"ファイル取得エラー: {file_path} - {response.status_code}")

        except Exception as e:
            logger.error(f"ファイル内容取得エラー: {e}")

        return None

    def analyze_codebase(self, target_dirs: List[str] = ["libs", "workers"]) -> Dict:
        """コードベースを分析（改善版）"""
        analysis = {
            "total_files": 0,
            "file_types": {},
            "key_modules": [],
            "dependencies": set(),
            "structure": {},
        }

        # Tree APIを使用してファイル一覧を取得
        all_files = self.get_repository_structure()

        for target_dir in target_dirs:
            # ディレクトリ内のファイルをフィルタ
            dir_files = [f for f in all_files if f["path"].startswith(target_dir + "/")]

            for file_info in dir_files:
                if file_info["path"].endswith(".py"):
                    analysis["total_files"] += 1

                    # ファイルタイプ統計
                    ext = Path(file_info["name"]).suffix
                    analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1

                    # 内容を分析
                    content = self.get_file_content(file_info["path"])
                    if content:
                        # インポート分析
                        imports = self._extract_imports(content)
                        analysis["dependencies"].update(imports)

                        # 主要モジュール
                        if any(keyword in content for keyword in ["class", "def"]):
                            analysis["key_modules"].append(
                                {
                                    "path": file_info["path"],
                                    "name": file_info["name"],
                                    "size": len(content),
                                }
                            )

        analysis["dependencies"] = list(analysis["dependencies"])
        return analysis

    # 以下、既存のメソッドは変更なし...
    def _extract_imports(self, content: str) -> set:
        imports = set()
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("import "):
                module = line.split()[1].split(".")[0]
                imports.add(module)
            elif line.startswith("from "):
                parts = line.split()
                if len(parts) > 1:
                    module = parts[1].split(".")[0]
                    imports.add(module)
        return imports

    def create_enhanced_commit(
        self, task_id: str, files_changed: List[str], task_summary: str
    ) -> bool:
        change_summary = self._analyze_changes(files_changed)
        commit_message = f"🤖 AI Task #{task_id}: {task_summary}\n\n"
        commit_message += "📝 Changes:\n"
        for category, files in change_summary.items():
            if files:
                commit_message += f"- {category}: {', '.join(files)}\n"
        commit_message += f"\n🔧 Task ID: {task_id}\n"
        commit_message += f"⏰ Timestamp: {datetime.now().isoformat()}\n"
        try:
            subprocess.run(["git", "add"] + files_changed, check=True)
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            logger.info("強化コミット成功")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"コミットエラー: {e}")
            return False

    def _analyze_changes(self, files: List[str]) -> Dict[str, List[str]]:
        categories = {
            "workers": [],
            "libs": [],
            "scripts": [],
            "config": [],
            "other": [],
        }
        for file in files:
            if "workers/" in file:
                categories["workers"].append(Path(file).name)
            elif "libs/" in file:
                categories["libs"].append(Path(file).name)
            elif "scripts/" in file:
                categories["scripts"].append(Path(file).name)
            elif "config/" in file:
                categories["config"].append(Path(file).name)
            else:
                categories["other"].append(Path(file).name)
        return categories

    def get_code_context_for_ai(self, relevant_paths: List[str]) -> str:
        context = "【関連コード情報】\n\n"
        for path in relevant_paths:
            content = self.get_file_content(path)
            if content:
                important_parts = self._extract_important_parts(content)
                context += f"📄 {path}:\n"
                context += f"```python\n{important_parts}\n```\n\n"
        analysis = self.analyze_codebase()
        context += f"\n【コードベース概要】\n"
        context += f"- 総ファイル数: {analysis['total_files']}\n"
        context += f"- 主要モジュール: {len(analysis['key_modules'])}個\n"
        context += f"- 依存関係: {', '.join(analysis['dependencies'][:10])}\n"
        return context

    def _extract_important_parts(self, content: str, max_lines: int = 50) -> str:
        lines = content.split("\n")
        important_lines = []
        in_class = False
        in_function = False
        for i, line in enumerate(lines):
            if line.strip().startswith("class "):
                in_class = True
                important_lines.append(line)
            elif line.strip().startswith("def "):
                in_function = True
                important_lines.append(line)
                if i + 1 < len(lines) and '"""' in lines[i + 1]:
                    j = i + 1
                    while j < len(lines) and j < i + 10:
                        important_lines.append(lines[j])
                        if lines[j].strip().endswith('"""') and j > i + 1:
                            break
                        j += 1
            if len(important_lines) >= max_lines:
                break
        return "\n".join(important_lines[:max_lines])

    def get_recent_commits(self, limit: int = 10) -> List[Dict]:
        if not self.api_repo_url:
            return []
        url = f"{self.api_repo_url}/commits"
        headers = {"Authorization": f"token {self.token}"} if self.token else {}
        params = {"per_page": limit}
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                commits = response.json()
                return [
                    {
                        "sha": c["sha"][:7],
                        "message": c["commit"]["message"].split("\n")[0],
                        "author": c["commit"]["author"]["name"],
                        "date": c["commit"]["author"]["date"],
                    }
                    for c in commits
                ]
        except Exception as e:
            logger.error(f"コミット取得エラー: {e}")
        return []

    def create_pull_request(
        self, title: str, body: str, base: str = "main", head: str = None
    ) -> Optional[Dict]:
        if not all([self.api_repo_url, self.token]):
            logger.error("GitHub API認証情報が不足")
            return None
        if not head:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
            )
            head = result.stdout.strip() if result.returncode == 0 else None
        if not head or head == base:
            logger.error("PRを作成するには別ブランチが必要です")
            return None
        url = f"{self.api_repo_url}/pulls"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        data = {"title": title, "body": body, "head": head, "base": base}
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 201:
                pr_data = response.json()
                logger.info(f"PR作成成功: #{pr_data['number']}")
                return pr_data
            else:
                logger.error(f"PR作成失敗: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"PR作成エラー: {e}")
            return None
