#!/usr/bin/env python3
"""
Commit Message Generator
エルダーズギルド コミットメッセージ自動生成システム

Created by Claude Elder
Version: 1.0.0
"""

import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ConventionalCommitConfig:
    """Conventional Commits設定"""

    max_subject_length: int = 72
    max_body_length: int = 100
    include_body: bool = True
    include_footer: bool = True
    emoji_prefix: bool = False


class CommitMessageGenerator:
    """コミットメッセージ自動生成システム"""

    # 絵文字マッピング
    EMOJI_MAP = {
        "feat": "✨",
        "fix": "🐛",
        "docs": "📚",
        "style": "💄",
        "refactor": "♻️",
        "perf": "⚡",
        "test": "✅",
        "build": "🔧",
        "ci": "🤖",
        "chore": "🧹",
        "revert": "⏪",
        "security": "🔒",
        "deps": "⬆️",
    }

    # スコープ別絵文字
    SCOPE_EMOJI = {
        "elder-flow": "🌊",
        "docker": "🐳",
        "git": "🤖",
        "workers": "👷",
        "tests": "🧪",
        "libs": "📦",
        "commands": "⚡",
        "security": "🛡️",
        "sage": "🧙‍♂️",
        "a2a": "🐰",
    }

    def __init__(self, config: ConventionalCommitConfig = None):
        self.config = config or ConventionalCommitConfig()
        self.logger = logging.getLogger(__name__)

    def generate_conventional_commit(self, analysis) -> str:
        """Conventional Commits形式でメッセージ生成"""
        # commitオブジェクトから必要な情報を抽出
        if hasattr(analysis, "commit_type"):
            commit_type = analysis.commit_type
            scope = analysis.scope
            description = analysis.description
            breaking_change = analysis.breaking_change
            files_changed = analysis.files_changed
        else:
            # 辞書形式の場合
            commit_type = analysis.get("commit_type", "chore")
            scope = analysis.get("scope")
            description = analysis.get("description", "update files")
            breaking_change = analysis.get("breaking_change", False)
            files_changed = analysis.get("files_changed", [])

        # 基本形式: type(scope): description
        subject = self._build_subject(commit_type, scope, description, breaking_change)

        # 本文とフッター
        body = (
            self._build_body(files_changed, commit_type)
            if self.config.include_body
            else ""
        )
        footer = (
            self._build_footer(breaking_change, files_changed)
            if self.config.include_footer
            else ""
        )

        # 最終メッセージ組み立て
        parts = [subject]
        if body:
            parts.extend(["", body])
        if footer:
            parts.extend(["", footer])

        return "\n".join(parts)

    def _build_subject(
        self,
        commit_type: str,
        scope: Optional[str],
        description: str,
        breaking_change: bool,
    ) -> str:
        """サブジェクト行を構築"""
        # 絵文字プレフィックス
        emoji = ""
        if self.config.emoji_prefix:
            emoji = self.EMOJI_MAP.get(commit_type, "") + " "
            if scope and scope in self.SCOPE_EMOJI:
                emoji = self.SCOPE_EMOJI[scope] + " "

        # 破壊的変更の場合は!を追加
        type_str = commit_type
        if breaking_change:
            type_str += "!"

        # スコープ
        scope_str = f"({scope})" if scope else ""

        # 説明文を適切な長さに調整
        max_desc_length = (
            self.config.max_subject_length
            - len(emoji)
            - len(type_str)
            - len(scope_str)
            - 2
        )
        if len(description) > max_desc_length:
            description = description[: max_desc_length - 3] + "..."

        return f"{emoji}{type_str}{scope_str}: {description}"

    def _build_body(self, files_changed: List[str], commit_type: str) -> str:
        """本文を構築"""
        if not files_changed:
            return ""

        lines = []

        # 変更ファイル数が多い場合
        if len(files_changed) > 5:
            lines.append(f"Updated {len(files_changed)} files:")

            # ディレクトリ別に分類
            dirs = {}
            for file in files_changed:
                dir_name = file.split("/")[0] if "/" in file else "root"
                if dir_name not in dirs:
                    dirs[dir_name] = []
                dirs[dir_name].append(file.split("/")[-1])

            for dir_name, files in dirs.items():
                if len(files) <= 3:
                    lines.append(f"- {dir_name}/: {', '.join(files)}")
                else:
                    lines.append(
                        f"- {dir_name}/: {files[0]}, {files[1]} and {len(files)-2} more"
                    )
        else:
            lines.append("Changes:")
            for file in files_changed:
                lines.append(f"- {file}")

        return "\n".join(lines)

    def _build_footer(self, breaking_change: bool, files_changed: List[str]) -> str:
        """フッターを構築"""
        lines = []

        # 破壊的変更の説明
        if breaking_change:
            lines.append("BREAKING CHANGE: Major API or behavior changes included")

        # 自動生成マーク
        lines.append("🤖 Generated with [Claude Code](https://claude.ai/code)")
        lines.append("")
        lines.append("Co-Authored-By: Claude <noreply@anthropic.com>")

        return "\n".join(lines)

    def generate_smart_message(
        self, files: List[str], changes_summary: Dict[str, Any] = None
    ) -> str:
        """ファイル変更から自動的にメッセージ生成"""
        if not files:
            return "chore: update files"

        # ファイル分析
        analysis = self._analyze_files_for_commit(files, changes_summary)

        return self.generate_conventional_commit(analysis)

    def _analyze_files_for_commit(
        self, files: List[str], changes_summary: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """ファイル変更を分析してコミット情報を推定"""
        file_categories = {
            "source": [],
            "test": [],
            "docs": [],
            "config": [],
            "build": [],
            "ci": [],
            "other": [],
        }

        # ファイル分類
        for file in files:
            file_lower = file.lower()

            if file_lower.endswith((".py", ".js", ".ts", ".java", ".cpp", ".c", ".go")):
                if "test" in file_lower or file_lower.startswith("test_"):
                    file_categories["test"].append(file)
                else:
                    file_categories["source"].append(file)
            elif file_lower.endswith((".md", ".rst", ".txt")):
                file_categories["docs"].append(file)
            elif file_lower in ("dockerfile", "requirements.txt", "package.json"):
                file_categories["build"].append(file)
            elif file_lower.endswith((".yml", ".yaml")) and (
                "ci" in file_lower or ".github" in file
            ):
                file_categories["ci"].append(file)
            elif file_lower.endswith((".json", ".toml", ".yaml", ".yml", ".ini")):
                file_categories["config"].append(file)
            else:
                file_categories["other"].append(file)

        # コミットタイプ決定
        commit_type = "chore"
        confidence = 0.3

        if file_categories["test"]:
            commit_type = "test"
            confidence = 0.8
        elif file_categories["docs"]:
            commit_type = "docs"
            confidence = 0.7
        elif file_categories["build"] or file_categories["ci"]:
            commit_type = "build"
            confidence = 0.6
        elif file_categories["source"]:
            # 変更量で判定
            if changes_summary and changes_summary.get("total_lines_added", 0) > 50:
                commit_type = "feat"
                confidence = 0.6
            else:
                commit_type = "fix"
                confidence = 0.5

        # スコープ推定
        scope = None
        scopes = []
        for file in files:
            parts = file.split("/")
            if len(parts) > 1 and parts[0] in ["libs", "workers", "commands", "tests"]:
                scopes.append(parts[0])

        if scopes:
            scope = max(set(scopes), key=scopes.count)

        # 説明生成
        if len(files) == 1:
            description = f"update {files[0].split('/')[-1]}"
        elif len(files) <= 3:
            file_names = [f.split("/")[-1] for f in files]
            description = f"update {', '.join(file_names)}"
        else:
            description = f"update {len(files)} files"

        return {
            "commit_type": commit_type,
            "scope": scope,
            "description": description,
            "breaking_change": False,
            "files_changed": files,
            "confidence": confidence,
        }

    def suggest_message_improvements(self, message: str) -> Dict[str, Any]:
        """既存のコミットメッセージの改善提案"""
        suggestions = []
        score = 100

        # 長さチェック
        first_line = message.split("\n")[0]
        if len(first_line) > 72:
            suggestions.append("Subject line too long (>72 chars)")
            score -= 10

        # Conventional Commits形式チェック
        if not re.match(
            r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\(.+\))?: .+",
            first_line,
        ):
            suggestions.append("Consider using Conventional Commits format")
            score -= 15

        # 大文字チェック
        if first_line and first_line[0].isupper():
            suggestions.append("Use lowercase for subject line")
            score -= 5

        # 動詞チェック（英語）
        if not re.search(
            r"\b(add|fix|update|remove|refactor|implement|enhance|improve)\b",
            first_line.lower(),
        ):
            suggestions.append(
                "Consider using imperative mood (add, fix, update, etc.)"
            )
            score -= 10

        return {
            "score": max(0, score),
            "suggestions": suggestions,
            "is_conventional": bool(
                re.match(
                    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)",
                    first_line,
                )
            ),
        }


# グローバルインスタンス
commit_generator = CommitMessageGenerator()


# 便利な関数
def generate_conventional_commit(analysis) -> str:
    """Conventional Commits形式メッセージ生成"""
    return commit_generator.generate_conventional_commit(analysis)


def generate_smart_message(
    files: List[str], changes_summary: Dict[str, Any] = None
) -> str:
    """スマートメッセージ生成"""
    return commit_generator.generate_smart_message(files, changes_summary)


def suggest_improvements(message: str) -> Dict[str, Any]:
    """メッセージ改善提案"""
    return commit_generator.suggest_message_improvements(message)


def create_elders_guild_commit(
    commit_type: str,
    scope: str = None,
    description: str = "",
    breaking_change: bool = False,
) -> str:
    """エルダーズギルド専用コミットメッセージ作成"""
    analysis = {
        "commit_type": commit_type,
        "scope": scope,
        "description": description,
        "breaking_change": breaking_change,
        "files_changed": [],
        "confidence": 1.0,
    }

    # 絵文字付きバージョンで生成
    generator = CommitMessageGenerator(ConventionalCommitConfig(emoji_prefix=True))
    return generator.generate_conventional_commit(analysis)


if __name__ == "__main__":
    print("📝 Commit Message Generator")
    print("=" * 50)

    # テスト用分析データ
    test_analysis = {
        "commit_type": "feat",
        "scope": "elder-flow",
        "description": "implement AI-driven git automation system",
        "breaking_change": False,
        "files_changed": ["libs/ai_git.py", "libs/commit_message_generator.py"],
        "confidence": 0.9,
    }

    # 標準メッセージ
    standard_msg = generate_conventional_commit(test_analysis)
    print("Standard message:")
    print(standard_msg)
    print()

    # エルダーズギルド形式
    elders_msg = create_elders_guild_commit(
        "feat", "git", "AI-driven automation system"
    )
    print("Elders Guild message:")
    print(elders_msg)
    print()

    # 改善提案
    improvements = suggest_improvements("Fixed a bug")
    print(f"Message score: {improvements['score']}/100")
    print(f"Suggestions: {improvements['suggestions']}")
