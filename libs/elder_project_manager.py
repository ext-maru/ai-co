#!/usr/bin/env python3
"""
Elder階層プロジェクト管理システム
Elders Guild Elder Hierarchy Project Manager

🏛️ Elder階層に対応したプロジェクト一覧・概要管理機能
- プロジェクト自動検索・索引化
- Elder権限別アクセス制御
- 概要・ステータス・進捗管理
- 検索・フィルタリング機能
"""

import asyncio
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.elder_aware_base_worker import ElderTaskContext
from libs.unified_auth_provider import AuthSession, ElderRole, SageType, User


class ProjectStatus(Enum):
    """プロジェクトステータス"""

    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class ProjectPriority(Enum):
    """プロジェクト優先度"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ProjectInfo:
    """プロジェクト情報"""

    id: str
    name: str
    path: str
    description: str
    status: ProjectStatus
    priority: ProjectPriority
    owner: str
    elder_role: ElderRole
    created_at: datetime
    updated_at: datetime
    file_count: int
    size_mb: float
    tags: List[str]
    dependencies: List[str]
    progress: float  # 0.0 - 1.0
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        # Enumと日時を文字列に変換
        data["status"] = self.status.value
        data["priority"] = self.priority.value
        data["elder_role"] = self.elder_role.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.estimated_completion:
            data["estimated_completion"] = self.estimated_completion.isoformat()
        if self.actual_completion:
            data["actual_completion"] = self.actual_completion.isoformat()
        return data


class ElderProjectManager:
    """Elder階層プロジェクト管理システム"""

    def __init__(self, auth_provider=None):
        self.auth_provider = auth_provider
        self.projects_root = Path("/home/aicompany/ai_co/projects")
        self.project_index_file = Path("/home/aicompany/ai_co/data/project_index.json")
        self.project_metadata_dir = Path("/home/aicompany/ai_co/data/project_metadata")

        # ディレクトリ作成
        self.projects_root.mkdir(exist_ok=True)
        self.project_index_file.parent.mkdir(exist_ok=True)
        self.project_metadata_dir.mkdir(exist_ok=True)

        # プロジェクト索引
        self.project_index: Dict[str, ProjectInfo] = {}
        self.load_project_index()

    def load_project_index(self):
        """プロジェクト索引をロード"""
        if self.project_index_file.exists():
            try:
                with open(self.project_index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for project_id, project_data in data.items():
                    # 文字列をEnumと日時に変換
                    project_data["status"] = ProjectStatus(project_data["status"])
                    project_data["priority"] = ProjectPriority(project_data["priority"])
                    project_data["elder_role"] = ElderRole(project_data["elder_role"])
                    project_data["created_at"] = datetime.fromisoformat(
                        project_data["created_at"]
                    )
                    project_data["updated_at"] = datetime.fromisoformat(
                        project_data["updated_at"]
                    )

                    if project_data.get("estimated_completion"):
                        project_data["estimated_completion"] = datetime.fromisoformat(
                            project_data["estimated_completion"]
                        )
                    if project_data.get("actual_completion"):
                        project_data["actual_completion"] = datetime.fromisoformat(
                            project_data["actual_completion"]
                        )

                    self.project_index[project_id] = ProjectInfo(**project_data)
            except Exception as e:
                print(f"プロジェクト索引の読み込みエラー: {e}")

    def save_project_index(self):
        """プロジェクト索引を保存"""
        try:
            data = {
                project_id: project_info.to_dict()
                for project_id, project_info in self.project_index.items()
            }

            with open(self.project_index_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"プロジェクト索引の保存エラー: {e}")

    def scan_projects(self) -> List[ProjectInfo]:
        """プロジェクトディレクトリをスキャンして更新"""
        scanned_projects = []

        for project_dir in self.projects_root.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith("."):
                project_info = self._analyze_project_directory(project_dir)
                if project_info:
                    scanned_projects.append(project_info)
                    self.project_index[project_info.id] = project_info

        # 削除されたプロジェクトを索引から除去
        existing_ids = {p.id for p in scanned_projects}
        to_remove = [
            pid for pid in self.project_index.keys() if pid not in existing_ids
        ]
        for pid in to_remove:
            del self.project_index[pid]

        self.save_project_index()
        return scanned_projects

    def _analyze_project_directory(self, project_dir: Path) -> Optional[ProjectInfo]:
        """プロジェクトディレクトリを分析"""
        try:
            project_id = project_dir.name

            # README.mdから情報を取得
            readme_path = project_dir / "README.md"
            description = "No description available"
            if readme_path.exists():
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 最初の段落を説明として使用
                    lines = content.split("\n")
                    for line in lines:
                        if line.strip() and not line.startswith("#"):
                            description = line.strip()
                            break

            # ファイル数とサイズを計算
            file_count = sum(1 for _ in project_dir.rglob("*") if _.is_file())
            size_bytes = sum(
                f.stat().st_size for f in project_dir.rglob("*") if f.is_file()
            )
            size_mb = size_bytes / (1024 * 1024)

            # プロジェクトメタデータを取得
            metadata_file = self.project_metadata_dir / f"{project_id}.json"
            metadata = self._load_project_metadata(metadata_file)

            # 統計情報
            stats = project_dir.stat()
            created_at = datetime.fromtimestamp(stats.st_ctime)
            updated_at = datetime.fromtimestamp(stats.st_mtime)

            return ProjectInfo(
                id=project_id,
                name=metadata.get("name", project_id),
                path=str(project_dir),
                description=description,
                status=ProjectStatus(metadata.get("status", "development")),
                priority=ProjectPriority(metadata.get("priority", "medium")),
                owner=metadata.get("owner", "unknown"),
                elder_role=ElderRole(metadata.get("elder_role", "servant")),
                created_at=created_at,
                updated_at=updated_at,
                file_count=file_count,
                size_mb=round(size_mb, 2),
                tags=metadata.get("tags", []),
                dependencies=metadata.get("dependencies", []),
                progress=metadata.get("progress", 0.0),
                estimated_completion=metadata.get("estimated_completion"),
                actual_completion=metadata.get("actual_completion"),
            )

        except Exception as e:
            print(f"プロジェクト分析エラー ({project_dir}): {e}")
            return None

    def _load_project_metadata(self, metadata_file: Path) -> Dict[str, Any]:
        """プロジェクトメタデータをロード"""
        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def register_project(self, project_info: ProjectInfo):
        """プロジェクトを登録"""
        self.project_index[project_info.id] = project_info

        # メタデータファイルを作成
        metadata_file = self.project_metadata_dir / f"{project_info.id}.json"
        metadata = {
            "name": project_info.name,
            "status": project_info.status.value,
            "priority": project_info.priority.value,
            "owner": project_info.owner,
            "elder_role": project_info.elder_role.value,
            "tags": project_info.tags,
            "dependencies": project_info.dependencies,
            "progress": project_info.progress,
            "estimated_completion": (
                project_info.estimated_completion.isoformat()
                if project_info.estimated_completion
                else None
            ),
            "actual_completion": (
                project_info.actual_completion.isoformat()
                if project_info.actual_completion
                else None
            ),
        }

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        self.save_project_index()

    def get_project_list(
        self, user: User, filters: Dict[str, Any] = None
    ) -> List[ProjectInfo]:
        """プロジェクト一覧を取得（Elder権限フィルタ付き）"""
        projects = list(self.project_index.values())

        # Elder権限による表示制限
        if user.elder_role == ElderRole.SERVANT:
            # Servantは自分のプロジェクトのみ
            projects = [p for p in projects if p.owner == user.username]
        elif user.elder_role == ElderRole.SAGE:
            # Sageは自分の専門分野 + 自分のプロジェクト
            projects = [
                p
                for p in projects
                if p.owner == user.username
                or p.elder_role in [ElderRole.SERVANT, ElderRole.SAGE]
            ]
        # Claude Elder, Grand Elderは全プロジェクト表示可能

        # フィルタリング
        if filters:
            if "status" in filters:
                projects = [p for p in projects if p.status.value == filters["status"]]
            if "priority" in filters:
                projects = [
                    p for p in projects if p.priority.value == filters["priority"]
                ]
            if "owner" in filters:
                projects = [p for p in projects if p.owner == filters["owner"]]
            if "tag" in filters:
                projects = [p for p in projects if filters["tag"] in p.tags]
            if "search" in filters:
                search_term = filters["search"].lower()
                projects = [
                    p
                    for p in projects
                    if search_term in p.name.lower()
                    or search_term in p.description.lower()
                ]

        # ソート（更新日時で降順）
        projects.sort(key=lambda p: p.updated_at, reverse=True)

        return projects

    def get_project_details(self, project_id: str, user: User) -> Optional[ProjectInfo]:
        """プロジェクト詳細を取得"""
        if project_id not in self.project_index:
            return None

        project = self.project_index[project_id]

        # 権限チェック
        if user.elder_role == ElderRole.SERVANT and project.owner != user.username:
            return None
        elif user.elder_role == ElderRole.SAGE:
            if project.owner != user.username and project.elder_role not in [
                ElderRole.SERVANT,
                ElderRole.SAGE,
            ]:
                return None

        return project

    def update_project_status(
        self, project_id: str, status: ProjectStatus, user: User
    ) -> bool:
        """プロジェクトステータスを更新"""
        if project_id not in self.project_index:
            return False

        project = self.project_index[project_id]

        # 権限チェック
        if user.elder_role == ElderRole.SERVANT and project.owner != user.username:
            return False

        project.status = status
        project.updated_at = datetime.now()

        if status == ProjectStatus.COMPLETED:
            project.actual_completion = datetime.now()
            project.progress = 1.0

        self.register_project(project)
        return True

    def search_projects(self, query: str, user: User) -> List[ProjectInfo]:
        """プロジェクト検索"""
        return self.get_project_list(user, {"search": query})

    def get_project_statistics(self, user: User) -> Dict[str, Any]:
        """プロジェクト統計情報を取得"""
        projects = self.get_project_list(user)

        total_count = len(projects)
        status_counts = {}
        priority_counts = {}
        elder_role_counts = {}

        total_size = 0
        completed_count = 0

        for project in projects:
            # ステータス別カウント
            status_counts[project.status.value] = (
                status_counts.get(project.status.value, 0) + 1
            )

            # 優先度別カウント
            priority_counts[project.priority.value] = (
                priority_counts.get(project.priority.value, 0) + 1
            )

            # Elder権限別カウント
            elder_role_counts[project.elder_role.value] = (
                elder_role_counts.get(project.elder_role.value, 0) + 1
            )

            # 合計サイズ
            total_size += project.size_mb

            # 完了プロジェクト数
            if project.status == ProjectStatus.COMPLETED:
                completed_count += 1

        completion_rate = (
            (completed_count / total_count * 100) if total_count > 0 else 0
        )

        return {
            "total_projects": total_count,
            "completed_projects": completed_count,
            "completion_rate": round(completion_rate, 1),
            "total_size_mb": round(total_size, 2),
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "elder_role_distribution": elder_role_counts,
            "user_role": user.elder_role.value,
        }


# CLI インターフェース
class ElderProjectCLI:
    """Elder階層プロジェクト管理CLI"""

    def __init__(self, auth_provider=None):
        self.manager = ElderProjectManager(auth_provider)
        self.auth_provider = auth_provider

    def format_project_list(
        self, projects: List[ProjectInfo], show_details: bool = False
    ) -> str:
        """プロジェクト一覧をフォーマット"""
        if not projects:
            return "📭 プロジェクトが見つかりません"

        output = []
        output.append(f"📋 プロジェクト一覧 ({len(projects)}件)")
        output.append("=" * 60)

        for project in projects:
            # ステータス絵文字
            status_emoji = {
                "planning": "📋",
                "development": "⚡",
                "testing": "🧪",
                "staging": "🚀",
                "production": "🌟",
                "completed": "✅",
                "archived": "📦",
                "cancelled": "❌",
            }

            # 優先度絵文字
            priority_emoji = {
                "critical": "🚨",
                "high": "⚠️",
                "medium": "📊",
                "low": "📋",
            }

            # Elder権限絵文字
            elder_emoji = {
                "grand_elder": "🌟",
                "claude_elder": "🤖",
                "sage": "🧙‍♂️",
                "servant": "🧝‍♂️",
            }

            status_icon = status_emoji.get(project.status.value, "❓")
            priority_icon = priority_emoji.get(project.priority.value, "❓")
            elder_icon = elder_emoji.get(project.elder_role.value, "❓")

            # 基本情報
            output.append(f"{status_icon} **{project.name}** ({project.id})")
            output.append(
                f"   {priority_icon} {project.priority.value.upper()} | {elder_icon} {project.elder_role.value}"
            )
            output.append(f"   📝 {project.description}")
            output.append(
                f"   👤 {project.owner} | 📅 {project.updated_at.strftime('%Y-%m-%d %H:%M')}"
            )

            if show_details:
                output.append(
                    f"   📁 {project.file_count} files | 💾 {project.size_mb} MB"
                )
                output.append(f"   📊 進捗: {project.progress*100:.1f}%")
                if project.tags:
                    output.append(f"   🏷️ {', '.join(project.tags)}")
                output.append(f"   📂 {project.path}")

            output.append("")

        return "\n".join(output)

    def format_project_details(self, project: ProjectInfo) -> str:
        """プロジェクト詳細をフォーマット"""
        output = []
        output.append(f"🏛️ プロジェクト詳細: {project.name}")
        output.append("=" * 60)

        # 基本情報
        output.append(f"📋 **プロジェクトID**: {project.id}")
        output.append(f"📝 **説明**: {project.description}")
        output.append(f"📊 **ステータス**: {project.status.value}")
        output.append(f"⚡ **優先度**: {project.priority.value}")
        output.append(f"👤 **所有者**: {project.owner}")
        output.append(f"🏛️ **Elder権限**: {project.elder_role.value}")
        output.append("")

        # 日時情報
        output.append("📅 **日時情報**")
        output.append(f"   作成日: {project.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"   更新日: {project.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if project.estimated_completion:
            output.append(
                f"   予定完了: {project.estimated_completion.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        if project.actual_completion:
            output.append(
                f"   実際完了: {project.actual_completion.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        output.append("")

        # ファイル情報
        output.append("📁 **ファイル情報**")
        output.append(f"   ファイル数: {project.file_count}")
        output.append(f"   サイズ: {project.size_mb} MB")
        output.append(f"   パス: {project.path}")
        output.append("")

        # 進捗情報
        output.append("📊 **進捗情報**")
        progress_bar = "█" * int(project.progress * 20) + "░" * (
            20 - int(project.progress * 20)
        )
        output.append(f"   進捗: [{progress_bar}] {project.progress*100:.1f}%")
        output.append("")

        # タグと依存関係
        if project.tags:
            output.append(f"🏷️ **タグ**: {', '.join(project.tags)}")
        if project.dependencies:
            output.append(f"🔗 **依存関係**: {', '.join(project.dependencies)}")

        return "\n".join(output)

    def format_statistics(self, stats: Dict[str, Any]) -> str:
        """統計情報をフォーマット"""
        output = []
        output.append("📊 プロジェクト統計情報")
        output.append("=" * 60)

        # 基本統計
        output.append(f"📋 **総プロジェクト数**: {stats['total_projects']}")
        output.append(f"✅ **完了プロジェクト**: {stats['completed_projects']}")
        output.append(f"📈 **完了率**: {stats['completion_rate']}%")
        output.append(f"💾 **総サイズ**: {stats['total_size_mb']} MB")
        output.append(f"🏛️ **あなたの権限**: {stats['user_role']}")
        output.append("")

        # ステータス分布
        output.append("📊 **ステータス分布**")
        for status, count in stats["status_distribution"].items():
            output.append(f"   {status}: {count}件")
        output.append("")

        # 優先度分布
        output.append("⚡ **優先度分布**")
        for priority, count in stats["priority_distribution"].items():
            output.append(f"   {priority}: {count}件")
        output.append("")

        # Elder権限分布
        output.append("🏛️ **Elder権限分布**")
        for role, count in stats["elder_role_distribution"].items():
            output.append(f"   {role}: {count}件")

        return "\n".join(output)


# CLI 実行関数
def run_elder_project_cli():
    """Elder階層プロジェクト管理CLI実行"""
    from libs.unified_auth_provider import create_demo_auth_system

    # 認証システム初期化
    auth_system = create_demo_auth_system()
    cli = ElderProjectCLI(auth_system)

    # プロジェクトスキャン
    projects = cli.manager.scan_projects()

    print("🏛️ Elder階層プロジェクト管理システム")
    print("=" * 60)
    print(f"📋 スキャン完了: {len(projects)}個のプロジェクトを発見")
    print("")

    # 利用可能なコマンド
    print("📋 利用可能なコマンド:")
    print("elder-project-list          - プロジェクト一覧表示")
    print("elder-project-list --detail - プロジェクト詳細一覧")
    print("elder-project-show <id>     - プロジェクト詳細表示")
    print("elder-project-search <query> - プロジェクト検索")
    print("elder-project-stats         - プロジェクト統計")
    print("elder-project-scan          - プロジェクト再スキャン")

    return cli


if __name__ == "__main__":
    cli = run_elder_project_cli()
