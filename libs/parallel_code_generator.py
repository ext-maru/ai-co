#!/usr/bin/env python3
"""
Parallel Code Generator
複数ファイルを同時生成する並列コード生成エンジン

⚡ nWo Instant Reality Engine - Parallel Code Generation
Think it, Rule it, Own it - 瞬間実装システム
"""

import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import shutil
import tempfile


class GenerationMode(Enum):
    """生成モード"""

    SEQUENTIAL = "sequential"  # 逐次生成
    PARALLEL = "parallel"  # 並列生成
    BATCH = "batch"  # バッチ生成
    STREAM = "stream"  # ストリーミング生成


class FileType(Enum):
    """ファイルタイプ"""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    SHELL = "shell"
    CONFIG = "config"


@dataclass
class FileSpec:
    """ファイル仕様"""

    path: str
    content: str
    file_type: FileType
    dependencies: List[str]
    priority: int = 1
    template_data: Optional[Dict] = None
    post_process: Optional[str] = None


@dataclass
class GenerationTask:
    """生成タスク"""

    task_id: str
    files: List[FileSpec]
    mode: GenerationMode
    output_dir: str
    created_at: str
    dependencies: Dict[str, List[str]]
    metadata: Dict[str, Any]


@dataclass
class GenerationResult:
    """生成結果"""

    task_id: str
    success: bool
    created_files: List[str]
    failed_files: List[str]
    generation_time: float
    file_count: int
    total_lines: int
    errors: List[str]
    warnings: List[str]


class ParallelCodeGenerator:
    """Parallel Code Generator - 瞬間コード生成システム"""

    def __init__(self, max_workers: int = 8, use_process_pool: bool = False):
        """初期化メソッド"""
        self.max_workers = max_workers
        self.use_process_pool = use_process_pool

        self.logger = self._setup_logger()

        # テンプレートエンジン
        self.templates = self._load_templates()

        # 依存関係グラフ
        self.dependency_graph = {}

        # 生成履歴
        self.generation_history = []

        # パフォーマンス追跡
        self.performance_stats = {
            "total_files": 0,
            "total_time": 0.0,
            "avg_files_per_second": 0.0,
        }

        self.logger.info("⚡ Parallel Code Generator initialized")

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("parallel_code_generator")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - Parallel Generator - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_templates(self) -> Dict[FileType, str]:
        """テンプレート読み込み"""
        return {
            FileType.PYTHON: '''#!/usr/bin/env python3
"""
{description}
{metadata}
"""

{imports}

{content}

if __name__ == "__main__":
    {main_content}
''',
            FileType.JAVASCRIPT: """/**
 * {description}
 * {metadata}
 */

{imports}

{content}
""",
            FileType.JSON: """{content}""",
            FileType.YAML: """# {description}
{content}""",
            FileType.MARKDOWN: """# {title}

{description}

{content}""",
            FileType.HTML: """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body>
{content}
</body>
</html>""",
            FileType.CSS: """/* {description} */

{content}""",
            FileType.SQL: """-- {description}
-- Generated: {timestamp}

{content}""",
            FileType.SHELL: """#!/bin/bash
# {description}
# {metadata}

{content}""",
            FileType.CONFIG: """{content}""",
        }

    async def generate_files(
        self,
        file_specs: List[FileSpec],
        output_dir: str = "output",
        mode: GenerationMode = GenerationMode.PARALLEL,
    ) -> GenerationResult:
        """
        ファイル一括生成

        Args:
            file_specs: ファイル仕様リスト
            output_dir: 出力ディレクトリ
            mode: 生成モード

        Returns:
            GenerationResult: 生成結果
        """
        start_time = time.time()
        task_id = f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.logger.info(f"⚡ Starting parallel generation: {len(file_specs)} files")

        # 出力ディレクトリ作成
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 依存関係分析
        dependency_order = self._analyze_dependencies(file_specs)

        # 生成実行
        if mode == GenerationMode.SEQUENTIAL:
            result = await self._generate_sequential(file_specs, output_path, task_id)
        elif mode == GenerationMode.PARALLEL:
            result = await self._generate_parallel(
                file_specs, output_path, task_id, dependency_order
            )
        elif mode == GenerationMode.BATCH:
            result = await self._generate_batch(file_specs, output_path, task_id)
        else:  # STREAM
            result = await self._generate_stream(file_specs, output_path, task_id)

        # パフォーマンス統計更新
        generation_time = time.time() - start_time
        self._update_performance_stats(len(file_specs), generation_time)

        result.generation_time = generation_time

        # 履歴保存
        self.generation_history.append(result)

        self.logger.info(
            f"✅ Generation completed: {result.file_count} files in {generation_time:.2f}s"
        )

        return result

    def _analyze_dependencies(self, file_specs: List[FileSpec]) -> List[List[FileSpec]]:
        """依存関係分析と実行順序決定"""
        # 依存関係グラフ構築
        graph = {}
        files_by_path = {spec.path: spec for spec in file_specs}

        for spec in file_specs:
            graph[spec.path] = spec.dependencies

        # トポロジカルソート
        visited = set()
        temp_visited = set()
        order = []

        def visit(path):
            """visitメソッド"""
            if path in temp_visited:
                return  # 循環依存は無視
            if path in visited:
                return

            temp_visited.add(path)

            for dep in graph.get(path, []):
                if dep in files_by_path:
                    visit(dep)

            temp_visited.remove(path)
            visited.add(path)
            order.append(path)

        for spec in file_specs:
            if spec.path not in visited:
                visit(spec.path)

        # 依存関係順にファイルをグループ化
        dependency_levels = []
        current_level = []
        processed = set()

        for path in order:
            spec = files_by_path[path]

            # 依存関係がすべて処理済みかチェック
            deps_ready = all(
                dep in processed or dep not in files_by_path
                for dep in spec.dependencies
            )

            if deps_ready:
                current_level.append(spec)
                processed.add(path)
            else:
                # 新しいレベル開始
                if current_level:
                    dependency_levels.append(current_level)
                    current_level = [spec]
                    processed.add(path)

        if current_level:
            dependency_levels.append(current_level)

        return dependency_levels

    async def _generate_sequential(
        self, file_specs: List[FileSpec], output_path: Path, task_id: str
    ) -> GenerationResult:
        """逐次生成"""
        created_files = []
        failed_files = []
        errors = []
        warnings = []
        total_lines = 0

        for spec in file_specs:
            try:
                file_path = output_path / spec.path
                content = self._render_template(spec)

                # ファイル作成
                file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                created_files.append(str(file_path))
                total_lines += len(content.splitlines())

                self.logger.debug(f"📝 Created: {file_path}")

            except Exception as e:
                failed_files.append(spec.path)
                errors.append(f"{spec.path}: {str(e)}")
                self.logger.error(f"❌ Failed to create {spec.path}: {e}")

        return GenerationResult(
            task_id=task_id,
            success=len(failed_files) == 0,
            created_files=created_files,
            failed_files=failed_files,
            generation_time=0.0,  # 後で設定
            file_count=len(created_files),
            total_lines=total_lines,
            errors=errors,
            warnings=warnings,
        )

    async def _generate_parallel(
        self,
        file_specs: List[FileSpec],
        output_path: Path,
        task_id: str,
        dependency_order: List[List[FileSpec]],
    ) -> GenerationResult:
        """並列生成（依存関係順）"""
        created_files = []
        failed_files = []
        errors = []
        warnings = []
        total_lines = 0

        executor_class = (
            ProcessPoolExecutor if self.use_process_pool else ThreadPoolExecutor
        )

        # 依存関係レベルごとに並列実行
        for level_specs in dependency_order:
            if not level_specs:
                continue

            # 同一レベルのファイルを並列生成
            with executor_class(
                max_workers=min(self.max_workers, len(level_specs))
            ) as executor:
                tasks = []

                for spec in level_specs:
                    task = asyncio.get_event_loop().run_in_executor(
                        executor, self._create_single_file, spec, output_path
                    )
                    tasks.append(task)

                # 結果収集
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        spec = level_specs[i]
                        failed_files.append(spec.path)
                        errors.append(f"{spec.path}: {str(result)}")
                        self.logger.error(
                            f"❌ Parallel creation failed {spec.path}: {result}"
                        )
                    else:
                        file_path, lines = result
                        created_files.append(file_path)
                        total_lines += lines
                        self.logger.debug(f"⚡ Parallel created: {file_path}")

        return GenerationResult(
            task_id=task_id,
            success=len(failed_files) == 0,
            created_files=created_files,
            failed_files=failed_files,
            generation_time=0.0,
            file_count=len(created_files),
            total_lines=total_lines,
            errors=errors,
            warnings=warnings,
        )

    def _create_single_file(self, spec: FileSpec, output_path: Path) -> tuple:
        """単一ファイル作成（並列処理用）"""
        file_path = output_path / spec.path
        content = self._render_template(spec)

        # ディレクトリ作成
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # ファイル書き込み
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(file_path), len(content.splitlines())

    async def _generate_batch(
        self, file_specs: List[FileSpec], output_path: Path, task_id: str
    ) -> GenerationResult:
        """バッチ生成"""
        batch_size = min(50, len(file_specs))  # バッチサイズ
        created_files = []
        failed_files = []
        errors = []
        warnings = []
        total_lines = 0

        # バッチに分割して処理
        for i in range(0, len(file_specs), batch_size):
            batch = file_specs[i : i + batch_size]

            batch_result = await self._generate_parallel(
                batch,
                output_path,
                f"{task_id}_batch_{i//batch_size}",
                [[spec] for spec in batch],
            )

            created_files.extend(batch_result.created_files)
            failed_files.extend(batch_result.failed_files)
            errors.extend(batch_result.errors)
            warnings.extend(batch_result.warnings)
            total_lines += batch_result.total_lines

        return GenerationResult(
            task_id=task_id,
            success=len(failed_files) == 0,
            created_files=created_files,
            failed_files=failed_files,
            generation_time=0.0,
            file_count=len(created_files),
            total_lines=total_lines,
            errors=errors,
            warnings=warnings,
        )

    async def _generate_stream(
        self, file_specs: List[FileSpec], output_path: Path, task_id: str
    ) -> GenerationResult:
        """ストリーミング生成"""
        created_files = []
        failed_files = []
        errors = []
        warnings = []
        total_lines = 0

        # ストリーミング処理（非同期ジェネレータ）
        async for result in self._stream_generator(file_specs, output_path):
            if result["success"]:
                created_files.append(result["file_path"])
                total_lines += result["lines"]
            else:
                failed_files.append(result["spec_path"])
                errors.append(result["error"])

        return GenerationResult(
            task_id=task_id,
            success=len(failed_files) == 0,
            created_files=created_files,
            failed_files=failed_files,
            generation_time=0.0,
            file_count=len(created_files),
            total_lines=total_lines,
            errors=errors,
            warnings=warnings,
        )

    async def _stream_generator(self, file_specs: List[FileSpec], output_path: Path):
        """ストリーミングジェネレータ"""
        for spec in file_specs:
            try:
                file_path = output_path / spec.path
                content = self._render_template(spec)

                file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                yield {
                    "success": True,
                    "file_path": str(file_path),
                    "lines": len(content.splitlines()),
                    "spec_path": spec.path,
                }

                # 小さな遅延（ストリーミング効果）
                await asyncio.sleep(0.01)

            except Exception as e:
                yield {
                    "success": False,
                    "spec_path": spec.path,
                    "error": f"{spec.path}: {str(e)}",
                }

    def _render_template(self, spec: FileSpec) -> str:
        """テンプレートレンダリング"""
        template = self.templates.get(spec.file_type, self.templates[FileType.CONFIG])

        # テンプレートデータ準備
        template_data = {
            "content": spec.content,
            "description": f"Generated file: {spec.path}",
            "timestamp": datetime.now().isoformat(),
            "metadata": f"Priority: {spec.priority}, Dependencies: {len(spec.dependencies)}",
            "title": Path(spec.path).stem.replace("_", " ").title(),
            "imports": "",
            "main_content": "pass",
        }

        # カスタムデータ追加
        if spec.template_data:
            template_data.update(spec.template_data)

        # テンプレート適用
        try:
            rendered = template.format(**template_data)
        except KeyError as e:
            # キーが見つからない場合はそのまま返す
            self.logger.warning(f"Template key not found: {e}")
            rendered = spec.content

        return rendered

    def _update_performance_stats(self, file_count: int, generation_time: float):
        """パフォーマンス統計更新"""
        self.performance_stats["total_files"] += file_count
        self.performance_stats["total_time"] += generation_time

        if self.performance_stats["total_time"] > 0:
            self.performance_stats["avg_files_per_second"] = (
                self.performance_stats["total_files"]
                / self.performance_stats["total_time"]
            )

    def create_file_spec(
        self,
        path: str,
        content: str,
        file_type: FileType,
        dependencies: List[str] = None,
        priority: int = 1,
        template_data: Dict = None,
    ) -> FileSpec:
        """ファイル仕様作成ヘルパー"""
        return FileSpec(
            path=path,
            content=content,
            file_type=file_type,
            dependencies=dependencies or [],
            priority=priority,
            template_data=template_data,
        )

    def create_python_module(
        self,
        module_name: str,
        classes: List[str] = None,
        functions: List[str] = None,
        imports: List[str] = None,
    ) -> FileSpec:
        """Pythonモジュール作成"""
        imports_section = "\n".join(imports or [])
        classes_section = "\n\n".join(
            f"class {cls}:\n    pass" for cls in (classes or [])
        )
        functions_section = "\n\n".join(
            f"def {func}():\n    pass" for func in (functions or [])
        )

        content = (
            f"{imports_section}\n\n{classes_section}\n\n{functions_section}".strip()
        )

        return self.create_file_spec(
            path=f"{module_name}.py",
            content=content,
            file_type=FileType.PYTHON,
            template_data={
                "imports": imports_section,
                "description": f"Python module: {module_name}",
            },
        )

    def create_api_endpoint(
        self, endpoint_name: str, methods: List[str] = None
    ) -> FileSpec:
        """API エンドポイント作成"""
        methods = methods or ["GET", "POST"]

        content = f'''from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/{endpoint_name}', methods={methods})
def {endpoint_name}_handler():
    """Handle {endpoint_name} requests"""
    if request.method == 'GET':
        return jsonify({{"message": "GET {endpoint_name}"}})
    elif request.method == 'POST':
        data = request.get_json()
        return jsonify({{"message": "POST {endpoint_name}", "data": data}})

if __name__ == '__main__':
    app.run(debug=True)'''

        return self.create_file_spec(
            path=f"api/{endpoint_name}.py",
            content=content,
            file_type=FileType.PYTHON,
            template_data={
                "description": f"API endpoint: {endpoint_name}",
                "imports": "from flask import Flask, request, jsonify",
            },
        )

    def create_test_file(self, target_file: str) -> FileSpec:
        """テストファイル作成"""
        module_name = Path(target_file).stem

        content = f'''import pytest
from {module_name} import *

class Test{module_name.title()}:
    """Test class for {module_name}"""

    def test_basic_functionality(self):
        """Test basic functionality"""
        assert True

    def test_edge_cases(self):
        """Test edge cases"""
        assert True

    def test_error_handling(self):
        """Test error handling"""
        assert True'''

        return self.create_file_spec(
            path=f"tests/test_{module_name}.py",
            content=content,
            file_type=FileType.PYTHON,
            dependencies=[target_file],
            template_data={
                "imports": "import pytest",
                "description": f"Test file for {module_name}",
            },
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計取得"""
        return self.performance_stats.copy()

    def get_generation_history(self, limit: int = 10) -> List[GenerationResult]:
        """生成履歴取得"""
        return self.generation_history[-limit:]

    def optimize_generation_order(self, file_specs: List[FileSpec]) -> List[FileSpec]:
        """生成順序最適化"""
        # 優先度とファイルサイズを考慮してソート
        return sorted(
            file_specs,
            key=lambda spec: (spec.priority, len(spec.content)),
            reverse=True,
        )

    def validate_dependencies(self, file_specs: List[FileSpec]) -> bool:
        """依存関係妥当性チェック"""
        file_paths = {spec.path for spec in file_specs}

        for spec in file_specs:
            for dep in spec.dependencies:
                if dep not in file_paths:
                    self.logger.warning(f"Dependency not found: {dep} for {spec.path}")
                    return False

        return True


# 使用例とテスト用関数
async def demo_parallel_generator():
    """Parallel Code Generatorのデモ"""
    print("⚡ Parallel Code Generator Demo")
    print("=" * 50)

    generator = ParallelCodeGenerator(max_workers=4)

    # サンプルファイル仕様作成
    file_specs = [
        generator.create_python_module(
            "user_service",
            classes=["User", "UserManager"],
            functions=["create_user", "get_user"],
            imports=["from typing import Dict, List", "import uuid"],
        ),
        generator.create_python_module(
            "database",
            classes=["Database", "Connection"],
            functions=["connect", "execute_query"],
            imports=["import sqlite3", "from typing import Any"],
        ),
        generator.create_api_endpoint("users", ["GET", "POST", "PUT", "DELETE"]),
        generator.create_test_file("user_service.py"),
        generator.create_test_file("database.py"),
    ]

    # 依存関係設定
    file_specs[3].dependencies = ["user_service.py"]  # test depends on module
    file_specs[4].dependencies = ["database.py"]

    print(f"📁 Generating {len(file_specs)} files...")

    # 並列生成実行
    result = await generator.generate_files(
        file_specs, output_dir="demo_output", mode=GenerationMode.PARALLEL
    )

    print(f"\n✅ Generation Result:")
    print(f"   Success: {result.success}")
    print(f"   Files Created: {result.file_count}")
    print(f"   Total Lines: {result.total_lines}")
    print(f"   Generation Time: {result.generation_time:.3f}s")
    print(f"   Files/Second: {result.file_count / result.generation_time:.1f}")

    if result.errors:
        print(f"   Errors: {len(result.errors)}")
        for error in result.errors[:3]:
            print(f"     - {error}")

    # パフォーマンス統計
    stats = generator.get_performance_stats()
    print(f"\n📊 Performance Stats:")
    print(f"   Total Files: {stats['total_files']}")
    print(f"   Avg Files/Second: {stats['avg_files_per_second']:.1f}")

    print(f"\n📂 Created Files:")
    for file_path in result.created_files:
        print(f"   - {file_path}")


if __name__ == "__main__":
    asyncio.run(demo_parallel_generator())
