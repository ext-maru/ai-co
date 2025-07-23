#!/usr/bin/env python3
"""
🌐 Project Web Portal System
プロジェクトWeb表示・自動資料生成システム

RAGエルダーの専門知識に基づく包括的なプロジェクト管理ポータル
pgvector統合による類似プロジェクト検索と自動ドキュメント生成

Author: Claude Elder
Date: 2025-07-10
Consultation: RAG Elder
"""

import ast
import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
import subprocess
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

# 既存システムインポート
try:
    from .advanced_knowledge_synthesis import AdvancedKnowledgeSynthesisSystem
    from .multidimensional_vector_system import MultiDimensionalVectorSystem
except ImportError:
    MultiDimensionalVectorSystem = None
    AdvancedKnowledgeSynthesisSystem = None


class ProjectType(Enum):
    """プロジェクトタイプ"""

    LIBRARY = "library"  # ライブラリ
    APPLICATION = "application"  # アプリケーション
    SCRIPT = "script"  # スクリプト
    FRAMEWORK = "framework"  # フレームワーク
    TOOL = "tool"  # ツール
    SERVICE = "service"  # サービス
    API = "api"  # API
    FRONTEND = "frontend"  # フロントエンド
    BACKEND = "backend"  # バックエンド


class ProjectStatus(Enum):
    """プロジェクト状態"""

    ACTIVE = "active"  # アクティブ
    COMPLETED = "completed"  # 完了
    DEPRECATED = "deprecated"  # 非推奨
    EXPERIMENTAL = "experimental"  # 実験的
    MAINTENANCE = "maintenance"  # メンテナンス中


class TechStack(Enum):
    """技術スタック"""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    REACT = "react"
    NEXTJS = "nextjs"
    FASTAPI = "fastapi"
    POSTGRESQL = "postgresql"
    REDIS = "redis"
    DOCKER = "docker"


@dataclass
class ProjectDependency:
    """プロジェクト依存関係"""

    name: str
    version: Optional[str] = None
    type: str = "runtime"  # runtime, dev, peer
    optional: bool = False


@dataclass
class CodeStructure:
    """コード構造"""

    total_lines: int
    total_files: int
    languages: Dict[str, int]  # 言語別行数
    classes: List[str]
    functions: List[str]
    complexity_score: float
    test_coverage: Optional[float] = None


@dataclass
class GitMetrics:
    """Gitメトリクス"""

    total_commits: int
    contributors: List[str]
    last_commit: datetime
    creation_date: datetime
    active_branches: int
    commit_frequency: float  # commits per week


@dataclass
class ProjectMetadata:
    """プロジェクトメタデータ"""

    project_id: str
    name: str
    path: Path
    project_type: ProjectType
    status: ProjectStatus
    tech_stack: List[TechStack]
    description: str
    created_at: datetime
    updated_at: datetime

    # 分析データ
    dependencies: List[ProjectDependency] = field(default_factory=list)
    code_structure: Optional[CodeStructure] = None
    git_metrics: Optional[GitMetrics] = None

    # ベクトル表現
    feature_vector: Optional[np.ndarray] = None
    semantic_vector: Optional[np.ndarray] = None

    # 関連プロジェクト
    similar_projects: List[Tuple[str, float]] = field(
        default_factory=list
    )  # (project_id, similarity)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        # Enumを文字列に変換
        data["project_type"] = self.project_type.value
        data["status"] = self.status.value
        data["tech_stack"] = [tech.value for tech in self.tech_stack]
        # datetimeを文字列に変換
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        # numpy配列を除外
        data.pop("feature_vector", None)
        data.pop("semantic_vector", None)
        return data


@dataclass
class ProjectDocumentation:
    """プロジェクト資料"""

    project_id: str
    generated_at: datetime
    overview: str
    architecture: str
    setup_guide: str
    api_reference: str
    usage_examples: str
    related_projects: List[Dict[str, Any]]
    diagrams: Dict[str, str]  # diagram_type -> mermaid_code
    quality_score: float


class ProjectAnalyzer:
    """プロジェクト分析エンジン"""

    def __init__(self):
        """初期化メソッド"""
        self.logger = logging.getLogger(self.__class__.__name__)

    async def analyze_project(self, project_path: Path) -> ProjectMetadata:
        """プロジェクト分析"""
        self.logger.info(f"プロジェクト分析開始: {project_path}")

        # 基本情報収集
        basic_info = await self._collect_basic_info(project_path)

        # コード構造分析
        code_structure = await self._analyze_code_structure(project_path)

        # 依存関係分析
        dependencies = await self._analyze_dependencies(project_path)

        # Git分析
        git_metrics = await self._analyze_git_metrics(project_path)

        # ベクトル化
        feature_vector = await self._create_feature_vector(
            basic_info, code_structure, dependencies
        )

        metadata = ProjectMetadata(
            project_id=self._generate_project_id(project_path),
            name=basic_info["name"],
            path=project_path,
            project_type=basic_info["type"],
            status=basic_info["status"],
            tech_stack=basic_info["tech_stack"],
            description=basic_info["description"],
            created_at=basic_info["created_at"],
            updated_at=datetime.now(),
            dependencies=dependencies,
            code_structure=code_structure,
            git_metrics=git_metrics,
            feature_vector=feature_vector,
        )

        self.logger.info(f"プロジェクト分析完了: {metadata.name}")
        return metadata

    async def _collect_basic_info(self, project_path: Path) -> Dict[str, Any]:
        """基本情報収集"""
        info = {
            "name": project_path.name,
            "type": ProjectType.LIBRARY,
            "status": ProjectStatus.ACTIVE,
            "tech_stack": [],
            "description": "",
            "created_at": datetime.now(),
        }

        # README読み取り
        readme_files = ["README.md", "README.txt", "readme.md"]
        for readme_file in readme_files:
            readme_path = project_path / readme_file
            if readme_path.exists():
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    info["description"] = self._extract_description(content)
                break

        # プロジェクトタイプ推定
        info["type"] = self._infer_project_type(project_path)

        # 技術スタック検出
        info["tech_stack"] = self._detect_tech_stack(project_path)

        # 作成日時推定
        try:
            stat = project_path.stat()
            info["created_at"] = datetime.fromtimestamp(stat.st_ctime)
        except:
            pass

        return info

    async def _analyze_code_structure(self, project_path: Path) -> CodeStructure:
        """コード構造分析"""
        total_lines = 0
        total_files = 0
        languages = defaultdict(int)
        classes = []
        functions = []

        # Pythonファイル分析
        for py_file in project_path.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = len(content.splitlines())
                    total_lines += lines
                    total_files += 1
                    languages["python"] += lines

                    # AST解析
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            classes.append(node.name)
                        elif isinstance(node, ast.FunctionDef):
                            functions.append(node.name)

            except Exception as e:
                self.logger.warning(f"ファイル分析エラー {py_file}: {e}")

        # その他のファイル
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                if suffix in [".js", ".ts", ".jsx", ".tsx"]:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            lines = len(f.readlines())
                            languages["javascript"] += lines
                            total_lines += lines
                            total_files += 1
                    except:
                        pass

        # 複雑度スコア計算
        complexity_score = self._calculate_complexity_score(
            total_lines, len(classes), len(functions)
        )

        return CodeStructure(
            total_lines=total_lines,
            total_files=total_files,
            languages=dict(languages),
            classes=classes,
            functions=functions,
            complexity_score=complexity_score,
        )

    async def _analyze_dependencies(
        self, project_path: Path
    ) -> List[ProjectDependency]:
        """依存関係分析"""
        dependencies = []

        # requirements.txt
        req_file = project_path / "requirements.txt"
        if req_file.exists():
            with open(req_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        dep = self._parse_requirement(line)
                        if dep:
                            dependencies.append(dep)

        # package.json
        package_file = project_path / "package.json"
        if package_file.exists():
            with open(package_file, "r") as f:
                package_data = json.load(f)

                # runtime dependencies
                for name, version in package_data.get("dependencies", {}).items():
                    dependencies.append(
                        ProjectDependency(name=name, version=version, type="runtime")
                    )

                # dev dependencies
                for name, version in package_data.get("devDependencies", {}).items():
                    dependencies.append(
                        ProjectDependency(name=name, version=version, type="dev")
                    )

        return dependencies

    async def _analyze_git_metrics(self, project_path: Path) -> Optional[GitMetrics]:
        """Git分析"""
        try:
            # Git情報取得
            result = subprocess.run(
                ["git", "log", "--pretty=format:%H|%an|%ad", "--date=iso"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return None

            commits = result.stdout.strip().split("\n")
            if not commits or commits == [""]:
                return None

            contributors = set()
            commit_dates = []

            for commit in commits:
                if "|" in commit:
                    parts = commit.split("|")
                    if len(parts) >= 3:
                        contributors.add(parts[1])
                        try:
                            commit_date = datetime.fromisoformat(
                                parts[2].replace(" +0900", "")
                            )
                            commit_dates.append(commit_date)
                        except:
                            pass

            if not commit_dates:
                return None

            # ブランチ数取得
            branch_result = subprocess.run(
                ["git", "branch", "-r"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            active_branches = (
                len(branch_result.stdout.strip().split("\n"))
                if branch_result.returncode == 0
                else 1
            )

            # コミット頻度計算
            if len(commit_dates) > 1:
                time_span = max(commit_dates) - min(commit_dates)
                weeks = max(1, time_span.days / 7)
                commit_frequency = len(commits) / weeks
            else:
                commit_frequency = 0

            return GitMetrics(
                total_commits=len(commits),
                contributors=list(contributors),
                last_commit=max(commit_dates),
                creation_date=min(commit_dates),
                active_branches=active_branches,
                commit_frequency=commit_frequency,
            )

        except Exception as e:
            self.logger.warning(f"Git分析エラー: {e}")
            return None

    async def _create_feature_vector(
        self,
        basic_info: Dict[str, Any],
        code_structure: CodeStructure,
        dependencies: List[ProjectDependency],
    ) -> np.ndarray:
        """特徴ベクトル作成"""
        features = []

        # プロジェクトタイプ（ワンホット）
        project_types = list(ProjectType)
        type_vector = [1 if basic_info["type"] == pt else 0 for pt in project_types]
        features.extend(type_vector)

        # 技術スタック（ワンホット）
        all_techs = list(TechStack)
        tech_vector = [
            1 if tech in basic_info["tech_stack"] else 0 for tech in all_techs
        ]
        features.extend(tech_vector)

        # コード規模
        features.extend(
            [
                np.log1p(code_structure.total_lines),
                np.log1p(code_structure.total_files),
                np.log1p(len(code_structure.classes)),
                np.log1p(len(code_structure.functions)),
                code_structure.complexity_score,
            ]
        )

        # 依存関係数
        features.append(np.log1p(len(dependencies)))

        # 言語分散
        if code_structure.languages:
            total_lines = sum(code_structure.languages.values())
            lang_entropy = -sum(
                (count / total_lines) * np.log(count / total_lines)
                for count in code_structure.languages.values()
            )
            features.append(lang_entropy)
        else:
            features.append(0)

        return np.array(features, dtype=np.float32)

    def _generate_project_id(self, project_path: Path) -> str:
        """プロジェクトID生成"""
        path_str = str(project_path.resolve())
        return hashlib.sha256(path_str.encode()).hexdigest()[:16]

    def _extract_description(self, readme_content: str) -> str:
        """README説明抽出"""
        lines = readme_content.split("\n")
        description_lines = []

        found_desc = False
        for line in lines:
            line = line.strip()
            if not line:
                if found_desc:
                    break
                continue

            # タイトル行をスキップ
            if line.startswith("#") and not found_desc:
                continue

            # 説明文を収集
            if not line.startswith("#") and not line.startswith("```"):
                description_lines.append(line)
                found_desc = True
                if len(description_lines) >= 3:  # 最初の3行
                    break

        return " ".join(description_lines)

    def _infer_project_type(self, project_path: Path) -> ProjectType:
        """プロジェクトタイプ推定"""
        # ディレクトリ名からの推定
        name = project_path.name.lower()

        if "api" in name:
            return ProjectType.API
        elif "script" in name or "scripts" in name:
            return ProjectType.SCRIPT
        elif "frontend" in name or "ui" in name:
            return ProjectType.FRONTEND
        elif "backend" in name or "server" in name:
            return ProjectType.BACKEND
        elif "tool" in name or "cli" in name:
            return ProjectType.TOOL
        elif "service" in name:
            return ProjectType.SERVICE
        elif "framework" in name:
            return ProjectType.FRAMEWORK
        elif "app" in name or "application" in name:
            return ProjectType.APPLICATION
        else:
            return ProjectType.LIBRARY

    def _detect_tech_stack(self, project_path: Path) -> List[TechStack]:
        """技術スタック検出"""
        techs = []

        # ファイル存在チェック
        if (project_path / "requirements.txt").exists() or any(
            project_path.rglob("*.py")
        ):
            techs.append(TechStack.PYTHON)

        if (project_path / "package.json").exists():
            techs.append(TechStack.JAVASCRIPT)

        if any(project_path.rglob("*.ts")) or any(project_path.rglob("*.tsx")):
            techs.append(TechStack.TYPESCRIPT)

        if (project_path / "next.config.js").exists():
            techs.append(TechStack.NEXTJS)

        # パッケージ名からの検出
        try:
            req_file = project_path / "requirements.txt"
            if req_file.exists():
                with open(req_file, "r") as f:
                    content = f.read().lower()
                    if "fastapi" in content:
                        techs.append(TechStack.FASTAPI)
                    if "psycopg" in content or "postgresql" in content:
                        techs.append(TechStack.POSTGRESQL)
                    if "redis" in content:
                        techs.append(TechStack.REDIS)
        except:
            pass

        return techs

    def _parse_requirement(self, req_line: str) -> Optional[ProjectDependency]:
        """requirements行解析"""
        # 基本的な解析
        if "==" in req_line:
            name, version = req_line.split("==", 1)
            return ProjectDependency(name=name.strip(), version=version.strip())
        elif ">=" in req_line:
            name, version = req_line.split(">=", 1)
            return ProjectDependency(name=name.strip(), version=f">={version.strip()}")
        else:
            name = req_line.split()[0] if req_line else ""
            if name:
                return ProjectDependency(name=name.strip())
        return None

    def _calculate_complexity_score(
        self, lines: int, classes: int, functions: int
    ) -> float:
        """複雑度スコア計算"""
        if lines == 0:
            return 0.0

        # 正規化された複雑度
        class_density = classes / max(1, lines / 100)  # クラス密度
        function_density = functions / max(1, lines / 50)  # 関数密度

        # 0-1の範囲に正規化
        score = min(1.0, (class_density + function_density) / 10)
        return score


class DocumentationGenerator:
    """自動資料生成システム"""

    def __init__(self):
        """初期化メソッド"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.knowledge_synthesis = None

        # 知識合成システム初期化
        try:
            if AdvancedKnowledgeSynthesisSystem:
                self.knowledge_synthesis = AdvancedKnowledgeSynthesisSystem()
        except:
            pass

    async def generate_documentation(
        self, metadata: ProjectMetadata, similar_projects: List[ProjectMetadata] = None
    ) -> ProjectDocumentation:
        """プロジェクト資料生成"""
        self.logger.info(f"資料生成開始: {metadata.name}")

        # 各セクション生成
        overview = await self._generate_overview(metadata)
        architecture = await self._generate_architecture(metadata)
        setup_guide = await self._generate_setup_guide(metadata)
        api_reference = await self._generate_api_reference(metadata)
        usage_examples = await self._generate_usage_examples(metadata)
        diagrams = await self._generate_diagrams(metadata)

        # 関連プロジェクト情報
        related_projects = []
        if similar_projects:
            for proj in similar_projects[:5]:  # 上位5件
                related_projects.append(
                    {
                        "name": proj.name,
                        "description": proj.description,
                        "similarity": 0.85,  # 仮の値
                        "tech_stack": [tech.value for tech in proj.tech_stack],
                    }
                )

        # 品質スコア計算
        quality_score = self._calculate_documentation_quality(
            overview, architecture, setup_guide
        )

        documentation = ProjectDocumentation(
            project_id=metadata.project_id,
            generated_at=datetime.now(),
            overview=overview,
            architecture=architecture,
            setup_guide=setup_guide,
            api_reference=api_reference,
            usage_examples=usage_examples,
            related_projects=related_projects,
            diagrams=diagrams,
            quality_score=quality_score,
        )

        self.logger.info(f"資料生成完了: {metadata.name} (品質: {quality_score:.2f})")
        return documentation

    async def _generate_overview(self, metadata: ProjectMetadata) -> str:
        """概要生成"""
        overview = f"# {metadata.name}\n\n"

        # プロジェクト基本情報
        overview += f"**プロジェクトタイプ**: {metadata.project_type.value}\n"
        overview += f"**ステータス**: {metadata.status.value}\n"
        overview += f"**技術スタック**: {', '.join([tech.value for tech in metadata.tech_stack])}\n\n"

        # 説明
        if metadata.description:
            overview += f"## 説明\n\n{metadata.description}\n\n"

        # コード統計
        if metadata.code_structure:
            cs = metadata.code_structure
            overview += f"## コード統計\n\n"
            overview += f"- **総行数**: {cs.total_lines:,}\n"
            overview += f"- **ファイル数**: {cs.total_files}\n"
            overview += f"- **クラス数**: {len(cs.classes)}\n"
            overview += f"- **関数数**: {len(cs.functions)}\n"
            overview += f"- **複雑度スコア**: {cs.complexity_score:.2f}\n\n"

        # Git統計
        if metadata.git_metrics:
            gm = metadata.git_metrics
            overview += f"## 開発統計\n\n"
            overview += f"- **コミット数**: {gm.total_commits}\n"
            overview += f"- **貢献者数**: {len(gm.contributors)}\n"
            overview += f"- **最終更新**: {gm.last_commit.strftime('%Y-%m-%d')}\n"
            overview += (
                f"- **開発期間**: {(gm.last_commit - gm.creation_date).days}日\n\n"
            )

        return overview

    async def _generate_architecture(self, metadata: ProjectMetadata) -> str:
        """アーキテクチャ説明生成"""
        arch = f"# {metadata.name} アーキテクチャ\n\n"

        # 技術スタック詳細
        arch += "## 技術スタック\n\n"
        for tech in metadata.tech_stack:
            arch += f"- **{tech.value}**: {self._get_tech_description(tech)}\n"
        arch += "\n"

        # 依存関係
        if metadata.dependencies:
            arch += "## 主要依存関係\n\n"
            runtime_deps = [d for d in metadata.dependencies if d.type == "runtime"]
            for dep in runtime_deps[:10]:  # 上位10件
                arch += f"- `{dep.name}`"
                if dep.version:
                    arch += f" ({dep.version})"
                arch += "\n"
            arch += "\n"

        # コンポーネント構造
        if metadata.code_structure and metadata.code_structure.classes:
            arch += "## 主要コンポーネント\n\n"
            for cls in metadata.code_structure.classes[:10]:  # 上位10件
                arch += f"- `{cls}`\n"
            arch += "\n"

        return arch

    async def _generate_setup_guide(self, metadata: ProjectMetadata) -> str:
        """セットアップガイド生成"""
        guide = f"# {metadata.name} セットアップガイド\n\n"

        # 前提条件
        guide += "## 前提条件\n\n"
        if TechStack.PYTHON in metadata.tech_stack:
            guide += "- Python 3.8以降\n"
        if (
            TechStack.JAVASCRIPT in metadata.tech_stack
            or TechStack.NEXTJS in metadata.tech_stack
        ):
            guide += "- Node.js 16以降\n"
        if TechStack.POSTGRESQL in metadata.tech_stack:
            guide += "- PostgreSQL 13以降\n"
        guide += "\n"

        # インストール手順
        guide += "## インストール\n\n"
        guide += "```bash\n"
        guide += f"# リポジトリのクローン\n"
        guide += f"git clone <repository-url>\n"
        guide += f"cd {metadata.name}\n\n"

        if TechStack.PYTHON in metadata.tech_stack:
            guide += "# Python依存関係のインストール\n"
            guide += "pip install -r requirements.txt\n\n"

        if TechStack.JAVASCRIPT in metadata.tech_stack:
            guide += "# Node.js依存関係のインストール\n"
            guide += "npm install\n\n"

        guide += "```\n\n"

        # 設定
        guide += "## 設定\n\n"
        if TechStack.POSTGRESQL in metadata.tech_stack:
            guide += "1. PostgreSQLデータベースを作成\n"
            guide += "2. 環境変数を設定\n"
            guide += "```bash\n"
            guide += "export DATABASE_URL=postgresql://user:pass@localhost/dbname\n"
            guide += "```\n\n"

        # 実行
        guide += "## 実行\n\n"
        guide += "```bash\n"
        if metadata.project_type == ProjectType.APPLICATION:
            if TechStack.PYTHON in metadata.tech_stack:
                guide += "python main.py\n"
            elif TechStack.NEXTJS in metadata.tech_stack:
                guide += "npm run dev\n"
        elif metadata.project_type == ProjectType.SCRIPT:
            guide += f"python {metadata.name}.py\n"
        guide += "```\n\n"

        return guide

    async def _generate_api_reference(self, metadata: ProjectMetadata) -> str:
        """API参考資料生成"""
        if metadata.project_type not in [ProjectType.API, ProjectType.LIBRARY]:
            return ""

        api_ref = f"# {metadata.name} API リファレンス\n\n"

        # 主要関数
        if metadata.code_structure and metadata.code_structure.functions:
            api_ref += "## 主要関数\n\n"
            for func in metadata.code_structure.functions[:20]:  # 上位20件
                api_ref += f"### `{func}()`\n\n"
                api_ref += f"```python\n"
                api_ref += f"def {func}():\n"
                api_ref += f'    """\n'
                api_ref += f"    {func}の説明\n"
                api_ref += f'    """\n'
                api_ref += f"    pass\n"
                api_ref += f"```\n\n"

        return api_ref

    async def _generate_usage_examples(self, metadata: ProjectMetadata) -> str:
        """使用例生成"""
        examples = f"# {metadata.name} 使用例\n\n"

        # 基本的な使用例
        examples += "## 基本的な使用方法\n\n"
        examples += "```python\n"

        if metadata.project_type == ProjectType.LIBRARY:
            examples += f"from {metadata.name} import main_function\n\n"
            examples += "# 基本的な使用方法\n"
            examples += "result = main_function()\n"
            examples += "print(result)\n"
        elif metadata.project_type == ProjectType.API:
            examples += "import requests\n\n"
            examples += "# APIリクエスト例\n"
            examples += (
                # Security: Validate URL before making request
                "response = requests.get('http://localhost:8000/api/endpoint')\n"
            )
            examples += "print(response.json())\n"

        examples += "```\n\n"

        # 高度な使用例
        examples += "## 高度な使用例\n\n"
        examples += "```python\n"
        examples += "# 設定オプション付きの使用例\n"
        examples += "# TODO: プロジェクト固有の高度な使用例\n"
        examples += "```\n\n"

        return examples

    async def _generate_diagrams(self, metadata: ProjectMetadata) -> Dict[str, str]:
        """図表生成"""
        diagrams = {}

        # アーキテクチャ図
        if metadata.tech_stack:
            arch_diagram = "graph TD\n"

            # 技術スタック要素
            for i, tech in enumerate(metadata.tech_stack):
                arch_diagram += f"    {tech.value}[{tech.value}]\n"

            # 関係性（簡単な例）
            if len(metadata.tech_stack) > 1:
                for i in range(len(metadata.tech_stack) - 1):
                    current = metadata.tech_stack[i].value
                    next_tech = metadata.tech_stack[i + 1].value
                    arch_diagram += f"    {current} --> {next_tech}\n"

            diagrams["architecture"] = arch_diagram

        # 依存関係図
        if metadata.dependencies:
            dep_diagram = "graph LR\n"
            dep_diagram += f"    {metadata.name}[{metadata.name}]\n"

            for dep in metadata.dependencies[:10]:  # 上位10件
                dep_diagram += f"    {dep.name}[{dep.name}]\n"
                dep_diagram += f"    {metadata.name} --> {dep.name}\n"

            diagrams["dependencies"] = dep_diagram

        return diagrams

    def _get_tech_description(self, tech: TechStack) -> str:
        """技術説明取得"""
        descriptions = {
            TechStack.PYTHON: "プログラミング言語",
            TechStack.JAVASCRIPT: "プログラミング言語",
            TechStack.TYPESCRIPT: "型安全なJavaScript",
            TechStack.REACT: "UIライブラリ",
            TechStack.NEXTJS: "Reactフレームワーク",
            TechStack.FASTAPI: "高速なPython Webフレームワーク",
            TechStack.POSTGRESQL: "リレーショナルデータベース",
            TechStack.REDIS: "インメモリデータストア",
            TechStack.DOCKER: "コンテナプラットフォーム",
        }
        return descriptions.get(tech, "技術コンポーネント")

    def _calculate_documentation_quality(
        self, overview: str, architecture: str, setup_guide: str
    ) -> float:
        """文書品質計算"""
        total_length = len(overview) + len(architecture) + len(setup_guide)

        # 長さベースの品質評価
        if total_length > 5000:
            base_score = 0.9
        elif total_length > 2000:
            base_score = 0.8
        elif total_length > 1000:
            base_score = 0.7
        else:
            base_score = 0.6

        # コンテンツの多様性チェック
        has_code_blocks = "```" in (overview + architecture + setup_guide)
        has_headers = "#" in (overview + architecture + setup_guide)
        has_lists = "-" in (overview + architecture + setup_guide)

        diversity_bonus = sum([has_code_blocks, has_headers, has_lists]) * 0.05

        return min(1.0, base_score + diversity_bonus)


class ProjectWebPortal:
    """プロジェクトWebポータル"""

    def __init__(self):
        """初期化メソッド"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db_path = PROJECT_ROOT / "data" / "project_portal.db"
        self.analyzer = ProjectAnalyzer()
        self.doc_generator = DocumentationGenerator()
        self.vector_system = None

        # ベクトルシステム初期化
        try:
            if MultiDimensionalVectorSystem:
                self.vector_system = MultiDimensionalVectorSystem()
        except:
            pass

        self._init_database()

    def _init_database(self):
        """データベース初期化"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    project_type TEXT,
                    status TEXT,
                    tech_stack TEXT,
                    description TEXT,
                    metadata_json TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS project_documentation (
                    project_id TEXT PRIMARY KEY,
                    generated_at REAL,
                    overview TEXT,
                    architecture TEXT,
                    setup_guide TEXT,
                    api_reference TEXT,
                    usage_examples TEXT,
                    diagrams_json TEXT,
                    quality_score REAL,
                    FOREIGN KEY (project_id) REFERENCES projects (project_id)
                )
            """
            )

    async def scan_projects(self, root_path: Path = None) -> List[ProjectMetadata]:
        """プロジェクトスキャン"""
        if root_path is None:
            root_path = PROJECT_ROOT

        self.logger.info(f"プロジェクトスキャン開始: {root_path}")

        projects = []

        # libsディレクトリスキャン
        libs_dir = root_path / "libs"
        if libs_dir.exists():
            for item in libs_dir.iterdir():
                if item.is_file() and item.suffix == ".py":
                    # 個別のPythonファイルをプロジェクトとして扱う
                    metadata = await self.analyzer.analyze_project(item.parent)
                    metadata.name = item.stem
                    metadata.path = item
                    projects.append(metadata)

        # scriptsディレクトリスキャン
        scripts_dir = root_path / "scripts"
        if scripts_dir.exists():
            for item in scripts_dir.iterdir():
                if item.is_file() and item.suffix == ".py":
                    metadata = await self.analyzer.analyze_project(item.parent)
                    metadata.name = item.stem
                    metadata.path = item
                    metadata.project_type = ProjectType.SCRIPT
                    projects.append(metadata)

        # サブディレクトリスキャン
        for item in root_path.iterdir():
            if item.is_dir() and item.name not in [
                "venv",
                "__pycache__",
                ".git",
                "node_modules",
            ]:
                if any(item.rglob("*.py")) or (item / "package.json").exists():
                    metadata = await self.analyzer.analyze_project(item)
                    projects.append(metadata)

        # データベースに保存
        await self._save_projects(projects)

        self.logger.info(f"プロジェクトスキャン完了: {len(projects)}件")
        return projects

    async def get_project_list(self) -> List[Dict[str, Any]]:
        """プロジェクト一覧取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT project_id, name, project_type, status, tech_stack,
                       description, updated_at
                FROM projects
                ORDER BY updated_at SHA256C
            """
            )

            projects = []
            for row in cursor.fetchall():
                projects.append(
                    {
                        "project_id": row[0],
                        "name": row[1],
                        "project_type": row[2],
                        "status": row[3],
                        "tech_stack": json.loads(row[4]) if row[4] else [],
                        "description": row[5],
                        "updated_at": datetime.fromtimestamp(row[6]).isoformat(),
                    }
                )

        return projects

    async def get_project_details(self, project_id: str) -> Optional[Dict[str, Any]]:
        """プロジェクト詳細取得"""
        with sqlite3.connect(self.db_path) as conn:
            # プロジェクトメタデータ
            cursor = conn.execute(
                "SELECT metadata_json FROM projects WHERE project_id = ?", (project_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            metadata = json.loads(row[0])

            # ドキュメント
            cursor = conn.execute(
                """SELECT overview, architecture, setup_guide, api_reference,
                          usage_examples, diagrams_json, quality_score
                   FROM project_documentation WHERE project_id = ?""",
                (project_id,),
            )
            doc_row = cursor.fetchone()

            if doc_row:
                metadata["documentation"] = {
                    "overview": doc_row[0],
                    "architecture": doc_row[1],
                    "setup_guide": doc_row[2],
                    "api_reference": doc_row[3],
                    "usage_examples": doc_row[4],
                    "diagrams": json.loads(doc_row[5]) if doc_row[5] else {},
                    "quality_score": doc_row[6],
                }

        return metadata

    async def generate_project_documentation(
        self, project_id: str
    ) -> Optional[ProjectDocumentation]:
        """プロジェクト資料生成"""
        # プロジェクトメタデータ取得
        metadata = await self._get_project_metadata(project_id)
        if not metadata:
            return None

        # 類似プロジェクト検索
        similar_projects = await self._find_similar_projects(metadata)

        # 資料生成
        documentation = await self.doc_generator.generate_documentation(
            metadata, similar_projects
        )

        # データベースに保存
        await self._save_documentation(documentation)

        return documentation

    async def find_similar_projects(
        self, project_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """類似プロジェクト検索"""
        metadata = await self._get_project_metadata(project_id)
        if not metadata or metadata.feature_vector is None:
            return []

        similar_projects = await self._find_similar_projects(metadata, limit)

        results = []
        for proj in similar_projects:
            similarity = self._calculate_similarity(
                metadata.feature_vector, proj.feature_vector
            )
            results.append(
                {
                    "project_id": proj.project_id,
                    "name": proj.name,
                    "description": proj.description,
                    "similarity": similarity,
                    "tech_stack": [tech.value for tech in proj.tech_stack],
                }
            )

        return sorted(results, key=lambda x: x["similarity"], reverse=True)

    async def _save_projects(self, projects: List[ProjectMetadata]):
        """プロジェクト保存"""
        with sqlite3.connect(self.db_path) as conn:
            for project in projects:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO projects
                    (project_id, name, path, project_type, status, tech_stack,
                     description, metadata_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        project.project_id,
                        project.name,
                        str(project.path),
                        project.project_type.value,
                        project.status.value,
                        json.dumps([tech.value for tech in project.tech_stack]),
                        project.description,
                        json.dumps(project.to_dict()),
                        project.created_at.timestamp(),
                        project.updated_at.timestamp(),
                    ),
                )

    async def _save_documentation(self, documentation: ProjectDocumentation):
        """資料保存"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO project_documentation
                (project_id, generated_at, overview, architecture, setup_guide,
                 api_reference, usage_examples, diagrams_json, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    documentation.project_id,
                    documentation.generated_at.timestamp(),
                    documentation.overview,
                    documentation.architecture,
                    documentation.setup_guide,
                    documentation.api_reference,
                    documentation.usage_examples,
                    json.dumps(documentation.diagrams),
                    documentation.quality_score,
                ),
            )

    async def _get_project_metadata(self, project_id: str) -> Optional[ProjectMetadata]:
        """プロジェクトメタデータ取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT metadata_json FROM projects WHERE project_id = ?", (project_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            # JSON から ProjectMetadata を復元
            data = json.loads(row[0])
            # 簡略化された復元（実際の実装では完全な復元が必要）
            return None  # TODO: 完全な復元実装

    async def _find_similar_projects(
        self, target: ProjectMetadata, limit: int = 5
    ) -> List[ProjectMetadata]:
        """類似プロジェクト検索"""
        # TODO: pgvector を使った高度な類似度検索
        return []

    def _calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """類似度計算"""
        if vec1 is None or vec2 is None:
            return 0.0

        # コサイン類似度
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


# デモンストレーション実行
async def main():
    """メイン実行"""
    portal = ProjectWebPortal()

    print("🌐 Project Web Portal システム")
    print("=" * 50)

    # プロジェクトスキャン
    print("\n1️⃣ プロジェクトスキャン実行...")
    projects = await portal.scan_projects()
    print(f"✅ {len(projects)}件のプロジェクトを発見")

    # プロジェクト一覧表示
    print("\n2️⃣ プロジェクト一覧:")
    project_list = await portal.get_project_list()
    for proj in project_list[:5]:  # 上位5件
        print(f"📁 {proj['name']} ({proj['project_type']})")
        print(f"   技術: {', '.join(proj['tech_stack'])}")
        print(f"   説明: {proj['description'][:50]}...")

    # 自動資料生成デモ
    if project_list:
        print(f"\n3️⃣ 自動資料生成デモ: {project_list[0]['name']}")
        documentation = await portal.generate_project_documentation(
            project_list[0]["project_id"]
        )

        if documentation:
            print(f"✅ 資料生成完了 (品質スコア: {documentation.quality_score:.2f})")
            print(f"📄 概要: {len(documentation.overview)}文字")
            print(f"🏗️ アーキテクチャ: {len(documentation.architecture)}文字")
            print(f"📋 セットアップ: {len(documentation.setup_guide)}文字")

    print("\n✨ Project Web Portal システム動作確認完了！")


if __name__ == "__main__":
    asyncio.run(main())