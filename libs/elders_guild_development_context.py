"""
Elders Guild Development Context System
開発精度向上のためのコンテキスト管理システム
Created: 2025-07-12
Author: Claude Elder
"""

import json
import os
import asyncio
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import ast
import aiofiles
import git

from anthropic import Anthropic
from .elders_guild_event_bus import ElderGuildEventBus, EventType

@dataclass
class CodebaseSnapshot:
    """コードベースの現在状態"""
    total_files: int
    file_types: Dict[str, int]
    recent_changes: List[Dict[str, Any]]
    dependencies: Dict[str, List[str]]
    known_issues: List[Dict[str, Any]]
    directory_structure: Dict[str, Any]

@dataclass
class ImpactAnalysis:
    """変更の影響分析結果"""
    direct_dependencies: List[str]
    indirect_dependencies: List[str]
    affected_tests: List[str]
    database_impacts: List[str]
    api_impacts: List[str]
    estimated_risk_level: str

class EldersDevelopmentContext:
    """
    エルダーズギルド開発コンテキスト管理
    Claudeに渡す完全なコンテキストを構築
    """

    def __init__(self, project_root: str = "/home/aicompany/ai_co"):
        self.project_root = Path(project_root)
        self.claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.knowledge_base = self._load_project_knowledge()
        self._file_cache = {}

    def _load_project_knowledge(self) -> Dict[str, Any]:
        """プロジェクト固有知識をロード"""
        knowledge_path = self.project_root / "knowledge_base" / "ELDERS_GUILD_PROJECT_KNOWLEDGE.json"
        try:
            with open(knowledge_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load project knowledge: {e}")
            return {}

    async def analyze_codebase(self) -> CodebaseSnapshot:
        """コードベース全体の現在状態を分析"""
        file_types = {}
        total_files = 0
        directory_structure = {}

        # ファイル構造の分析
        for root, dirs, files in os.walk(self.project_root):
            # 除外ディレクトリ
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}]

            rel_path = Path(root).relative_to(self.project_root)
            current_dir = directory_structure

            for part in rel_path.parts:
                if part not in current_dir:
                    current_dir[part] = {}
                current_dir = current_dir[part]

            for file in files:
                total_files += 1
                ext = Path(file).suffix
                file_types[ext] = file_types.get(ext, 0) + 1

        # Git履歴の分析
        recent_changes = await self._analyze_git_history()

        # 依存関係の分析
        dependencies = await self._analyze_dependencies()

        # 既知の問題
        known_issues = await self._collect_known_issues()

        return CodebaseSnapshot(
            total_files=total_files,
            file_types=file_types,
            recent_changes=recent_changes,
            dependencies=dependencies,
            known_issues=known_issues,
            directory_structure=directory_structure
        )

    async def _analyze_git_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """最近のGit履歴を分析"""
        try:
            repo = git.Repo(self.project_root)
            commits = []

            for commit in repo.iter_commits(max_count=50):
                commit_data = {
                    "hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": datetime.fromtimestamp(commit.committed_date).isoformat(),
                    "files_changed": len(commit.stats.files),
                    "insertions": commit.stats.total["insertions"],
                    "deletions": commit.stats.total["deletions"]
                }
                commits.append(commit_data)

            return commits
        except Exception:
            return []

    async def _analyze_dependencies(self) -> Dict[str, List[str]]:
        """プロジェクトの依存関係を分析"""
        dependencies = {
            "python": [],
            "system": [],
            "external_services": []
        }

        # Python依存関係
        requirements_path = self.project_root / "requirements.txt"
        if requirements_path.exists():
            async with aiofiles.open(requirements_path, 'r') as f:
                content = await f.read()
                dependencies["python"] = [
                    line.strip() for line in content.splitlines()
                    if line.strip() and not line.startswith('#')
                ]

        # 外部サービス
        dependencies["external_services"] = [
            "PostgreSQL 16",
            "Redis 7",
            "Anthropic Claude API",
            "OpenAI Embeddings API"
        ]

        return dependencies

    async def _collect_known_issues(self) -> List[Dict[str, Any]]:
        """既知の問題を収集"""
        # TODO: GitHub Issues APIと連携
        # 現在はハードコード
        return [
            {
                "type": "performance",
                "description": "Large document processing can be slow",
                "severity": "medium",
                "workaround": "Implement chunking for documents > 100KB"
            },
            {
                "type": "compatibility",
                "description": "Some imports fail in Python 3.12",
                "severity": "low",
                "workaround": "Use Python 3.11"
            }
        ]

    async def analyze_file_impact(self, file_path: str) -> ImpactAnalysis:
        """特定ファイルの変更影響を分析"""
        file_path = Path(file_path)
        if not file_path.is_absolute():
            file_path = self.project_root / file_path

        direct_deps = set()
        indirect_deps = set()
        affected_tests = set()

        # Pythonファイルの場合、importを分析
        if file_path.suffix == '.py':
            # このファイルをimportしているファイルを探す
            module_name = self._get_module_name(file_path)

            for py_file in self.project_root.rglob("*.py"):
                if py_file == file_path:
                    continue

                try:
                    content = py_file.read_text(encoding='utf-8')
                    if module_name in content:
                        if 'test_' in py_file.name:
                            affected_tests.add(str(py_file.relative_to(self.project_root)))
                        else:
                            direct_deps.add(str(py_file.relative_to(self.project_root)))
                except Exception:
                    continue

        # データベース影響
        database_impacts = []
        if 'model' in str(file_path) or 'schema' in str(file_path):
            database_impacts.append("Database schema may need migration")

        # API影響
        api_impacts = []
        if 'api' in str(file_path) or 'endpoint' in str(file_path):
            api_impacts.append("API endpoints may change")

        # リスクレベルの評価
        risk_level = self._evaluate_risk_level(
            len(direct_deps),
            len(affected_tests),
            len(database_impacts),
            len(api_impacts)
        )

        return ImpactAnalysis(
            direct_dependencies=list(direct_deps),
            indirect_dependencies=list(indirect_deps),
            affected_tests=list(affected_tests),
            database_impacts=database_impacts,
            api_impacts=api_impacts,
            estimated_risk_level=risk_level
        )

    def _get_module_name(self, file_path: Path) -> str:
        """ファイルパスからモジュール名を取得"""
        try:
            rel_path = file_path.relative_to(self.project_root)
            parts = list(rel_path.parts)
            if parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            return '.'.join(parts)
        except Exception:
            return ""

    def _evaluate_risk_level(self, direct_deps: int, tests: int,
                           db_impacts: int, api_impacts: int) -> str:
        """変更のリスクレベルを評価"""
        score = (
            direct_deps * 2 +
            tests * 1 +
            db_impacts * 3 +
            api_impacts * 3
        )

        if score >= 10:
            return "high"
        elif score >= 5:
            return "medium"
        else:
            return "low"

    async def generate_implementation_context(self,
                                           feature_request: str,
                                           target_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        実装に必要な完全なコンテキストを生成
        """
        # コードベースの現在状態
        codebase_snapshot = await self.analyze_codebase()

        # 関連ファイルの内容
        relevant_code = {}
        if target_files:
            for file in target_files:
                file_path = self.project_root / file
                if file_path.exists():
                    async with aiofiles.open(file_path, 'r') as f:
                        relevant_code[file] = await f.read()

        # 影響分析
        impact_analyses = {}
        if target_files:
            for file in target_files:
                impact_analyses[file] = await self.analyze_file_impact(file)

        # プロジェクトルールとパターン
        project_rules = self.knowledge_base.get("absolute_rules", [])
        code_patterns = self.knowledge_base.get("code_patterns", {})
        naming_conventions = self.knowledge_base.get("naming_conventions", {})

        # 類似実装の検索
        similar_implementations = await self._find_similar_implementations(feature_request)

        # チェックリストの生成
        checklist = self._generate_checklist(feature_request)

        # 完全なコンテキストを構築
        context = {
            "feature_request": feature_request,
            "timestamp": datetime.now().isoformat(),
            "codebase_state": {
                "total_files": codebase_snapshot.total_files,
                "recent_changes": codebase_snapshot.recent_changes[:10],
                "dependencies": codebase_snapshot.dependencies
            },
            "relevant_code": relevant_code,
            "impact_analysis": impact_analyses,
            "project_rules": {
                "absolute_rules": project_rules,
                "naming_conventions": naming_conventions,
                "code_patterns": code_patterns
            },
            "similar_implementations": similar_implementations,
            "implementation_checklist": checklist,
            "technical_stack": self.knowledge_base.get("technical_decisions", {}),
            "common_issues": self.knowledge_base.get("common_issues_and_solutions", {})
        }

        return context

    async def _find_similar_implementations(self, feature_request: str) -> List[Dict[str, str]]:
        """類似の実装を検索"""
        similar = []

        # キーワード抽出
        keywords = feature_request.lower().split()

        # 簡易的な類似実装検索
        patterns = {
            "auth": ["libs/elders_guild_api_spec.py", "Authentication implementation"],
            "oauth": ["libs/elders_guild_api_spec.py", "OAuth integration example"],
            "database": ["libs/elders_guild_db_manager.py", "Database operations"],
            "api": ["libs/elders_guild_api_spec.py", "API endpoint patterns"],
            "test": ["tests/unit/", "Test implementation examples"],
            "event": ["libs/elders_guild_event_bus.py", "Event handling patterns"]
        }

        for keyword in keywords:
            for pattern_key, (file_path, description) in patterns.items():
                if keyword in pattern_key:
                    similar.append({
                        "file": file_path,
                        "description": description,
                        "relevance": "high"
                    })

        return similar

    def _generate_checklist(self, feature_request: str) -> Dict[str, List[str]]:
        """実装チェックリストを生成"""
        return {
            "before_implementation": [
                "既存の類似実装を確認",
                "影響範囲を分析",
                "必要な依存関係を確認",
                "セキュリティ要件を確認"
            ],
            "during_implementation": [
                "TDDでテストを先に書く",
                "型ヒントを必ず追加",
                "エラーハンドリングを実装",
                "ログ出力を適切に配置"
            ],
            "after_implementation": [
                "すべてのテストが通ることを確認",
                "カバレッジが95%以上",
                "型チェック (mypy) が通る",
                "セキュリティスキャンが通る"
            ],
            "documentation": [
                "関数/クラスのdocstring",
                "APIドキュメントの更新",
                "変更履歴の記録",
                "使用例の追加"
            ]
        }

    async def validate_implementation(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """実装の検証"""
        validation_results = {
            "syntax": True,
            "style": True,
            "security": True,
            "performance": True,
            "issues": []
        }

        # 構文チェック
        try:
            ast.parse(code)
        except SyntaxError as e:
            validation_results["syntax"] = False
            validation_results["issues"].append(f"Syntax error: {e}")

        # プロジェクトルールのチェック
        for rule in self.knowledge_base.get("absolute_rules", []):
            if "テストなし" in rule and "def test_" not in code:
                validation_results["issues"].append("テストが含まれていません")
            if "型ヒント" in rule and "->" not in code:
                validation_results["issues"].append("型ヒントが不足している可能性")

        # セキュリティパターンのチェック
        security_issues = []
        if "password" in code.lower() and "plain" in code.lower():
            security_issues.append("平文パスワードの可能性")
        if "eval(" in code or "exec(" in code:
            security_issues.append("危険な関数の使用")

        if security_issues:
            validation_results["security"] = False
            validation_results["issues"].extend(security_issues)

        return validation_results


class ClaudeContextBuilder:
    """
    Claude用のコンテキスト構築専門クラス
    """

    def __init__(self, dev_context: EldersDevelopmentContext):
        self.dev_context = dev_context
        self.claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def build_claude_prompt(self, request: str, context: Dict[str, Any]) -> str:
        """
        Claudeに最適化されたプロンプトを構築
        """
        prompt = f"""
あなたはエルダーズギルドのClaudeエルダーとして、以下の開発タスクを実行してください。

# リクエスト
{request}

# プロジェクトコンテキスト
プロジェクト: {context.get('codebase_state', {}).get('total_files', 0)}個のファイルを含むElders Guild Platform

## 技術スタック
{json.dumps(context.get('technical_stack', {}), indent=2, ensure_ascii=False)}

## 絶対的ルール
{chr(10).join(f"- {rule}" for rule in context.get('project_rules', {}).get('absolute_rules', []))}

## 影響分析
{json.dumps(context.get('impact_analysis', {}), indent=2, ensure_ascii=False)}

## 類似実装
{chr(10).join(f"- {impl['file']}: {impl['description']}" for impl in context.get('similar_implementations', []))}

## 実装チェックリスト
{json.dumps(context.get('implementation_checklist', {}), indent=2, ensure_ascii=False)}

## 既知の問題と解決策
{json.dumps(context.get('common_issues', {}), indent=2, ensure_ascii=False)}

# 実装要件
1. 上記のコンテキストをすべて考慮してください
2. エルダーズツリー階層を守ってください
3. TDDで実装してください（テストを先に書く）
4. 型ヒントとdocstringは必須です
5. エラーハンドリングを適切に実装してください

# 出力形式
1. 実装計画の説明
2. テストコード
3. 実装コード
4. 使用例
5. 追加の推奨事項
"""
        return prompt

    async def request_claude_implementation(self, request: str) -> Dict[str, Any]:
        """
        Claudeに実装を依頼
        """
        # コンテキスト生成
        context = await self.dev_context.generate_implementation_context(request)

        # プロンプト構築
        prompt = await self.build_claude_prompt(request, context)

        # Claude APIコール
        response = await self.claude.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # レスポンスの解析と検証
        implementation = response.content[0].text
        validation = await self.dev_context.validate_implementation(implementation, context)

        return {
            "request": request,
            "context": context,
            "implementation": implementation,
            "validation": validation,
            "timestamp": datetime.now().isoformat()
        }


# 使用例
async def main():
    """開発コンテキストシステムの使用例"""

    # 初期化
    dev_context = EldersDevelopmentContext()
    claude_builder = ClaudeContextBuilder(dev_context)

    # 開発リクエスト
    request = "OAuth2.0認証をFastAPIに追加して、GoogleとGitHubプロバイダーに対応させてください"

    # Claudeに実装を依頼
    result = await claude_builder.request_claude_implementation(request)

    print(f"実装が完了しました:")
    print(f"検証結果: {result['validation']}")
    print(f"実装コード:\n{result['implementation'][:500]}...")


if __name__ == "__main__":
    asyncio.run(main())
