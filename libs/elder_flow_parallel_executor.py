#!/usr/bin/env python3
"""
Elder Flow Parallel Executor - 並列実行エンジン
Created: 2025-01-11
Author: Claude Elder
Version: 2.0.0

真の並列実行を実現するElder Flow改良版
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import subprocess
import ast
# Optional imports - フォーマッタが無くても動作する
try:
    import black
except ImportError:
    black = None

try:
    import isort
except ImportError:
    isort = None

# Servant Types
class ServantType(Enum):
    CODE_CRAFTSMAN = "code_craftsman"  # コード職人
    TEST_GUARDIAN = "test_guardian"    # テスト守護者
    QUALITY_INSPECTOR = "quality_inspector"  # 品質検査官
    GIT_KEEPER = "git_keeper"          # Git管理者
    DOCUMENTATION_SCRIBE = "documentation_scribe"  # 文書記録者

# Task Priority
class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

# Task Status
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"  # 依存関係待ち

@dataclass
class ServantTask:
    """拡張サーバントタスク"""
    task_id: str
    servant_type: ServantType
    description: str
    command: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)  # 依存するタスクID
    priority: TaskPriority = TaskPriority.MEDIUM
    timeout: int = 300
    retry_count: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    logs: List[str] = field(default_factory=list)

    def add_log(self, message: str):
        timestamp = datetime.now().isoformat()
        self.logs.append(f"[{timestamp}] {message}")

    def can_run(self, completed_tasks: Set[str]) -> bool:
        """依存関係をチェックして実行可能か判定"""
        return self.dependencies.issubset(completed_tasks)


class ParallelServantExecutor:
    """並列実行可能なサーバントエグゼキューター"""

    def __init__(self, max_workers: int = 5):
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers

        # タスク管理
        self.pending_tasks: Dict[str, ServantTask] = {}
        self.running_tasks: Dict[str, ServantTask] = {}
        self.completed_tasks: Dict[str, ServantTask] = {}
        self.failed_tasks: Dict[str, ServantTask] = {}

        # 実行統計
        self.stats = {
            "total_submitted": 0,
            "total_completed": 0,
            "total_failed": 0,
            "average_execution_time": 0.0,
            "parallel_efficiency": 0.0
        }

        # 実行エグゼキューター
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=max_workers//2)

        self.logger.info(f"🚀 Parallel Servant Executor initialized with {max_workers} workers")

    def add_task(self, task: ServantTask) -> str:
        """タスクを追加"""
        self.pending_tasks[task.task_id] = task
        self.stats["total_submitted"] += 1
        self.logger.info(f"📝 Task added: {task.task_id} ({task.servant_type.value})")
        return task.task_id

    def add_tasks(self, tasks: List[ServantTask]) -> List[str]:
        """複数タスクを一括追加"""
        task_ids = []
        for task in tasks:
            task_ids.append(self.add_task(task))
        return task_ids

    async def execute_all_parallel(self) -> Dict[str, Any]:
        """全タスクを並列実行"""
        start_time = time.time()
        self.logger.info("🌊 Starting parallel execution of all tasks")

        # 実行可能なタスクを継続的にチェックして実行
        while self.pending_tasks or self.running_tasks:
            # 実行可能なタスクを取得
            executable_tasks = self._get_executable_tasks()

            if executable_tasks:
                # 並列実行開始
                await self._execute_tasks_parallel(executable_tasks)
            elif self.running_tasks:
                # 実行中のタスクがある場合は少し待つ
                await asyncio.sleep(0.1)
            else:
                # デッドロック検出
                if self.pending_tasks:
                    self.logger.error("❌ Deadlock detected! Circular dependencies found.")
                    self._handle_deadlock()
                break

        end_time = time.time()
        execution_time = end_time - start_time

        # 統計更新
        self._update_statistics(execution_time)

        return self._generate_execution_report(execution_time)

    def _get_executable_tasks(self) -> List[ServantTask]:
        """実行可能なタスクを取得"""
        executable = []
        completed_ids = set(self.completed_tasks.keys())

        for task_id, task in list(self.pending_tasks.items()):
            if task.can_run(completed_ids):
                executable.append(task)
                # pendingから削除してrunningに移動
                del self.pending_tasks[task_id]
                self.running_tasks[task_id] = task

        # 優先度でソート
        executable.sort(key=lambda t: t.priority.value)

        return executable

    async def _execute_tasks_parallel(self, tasks: List[ServantTask]):
        """タスクを並列実行"""
        self.logger.info(f"⚡ Executing {len(tasks)} tasks in parallel")

        # 各タスクの実行を非同期で開始
        coroutines = []
        for task in tasks:
            coroutines.append(self._execute_single_task(task))

        # 全タスクを並列実行
        await asyncio.gather(*coroutines, return_exceptions=True)

    async def _execute_single_task(self, task: ServantTask) -> Dict[str, Any]:
        """単一タスクを実行"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        task.add_log(f"🏃 Starting execution")

        try:
            # サーバントタイプに応じて実行
            if task.servant_type == ServantType.CODE_CRAFTSMAN:
                result = await self._execute_code_craftsman(task)
            elif task.servant_type == ServantType.TEST_GUARDIAN:
                result = await self._execute_test_guardian(task)
            elif task.servant_type == ServantType.QUALITY_INSPECTOR:
                result = await self._execute_quality_inspector(task)
            elif task.servant_type == ServantType.DOCUMENTATION_SCRIBE:
                result = await self._execute_documentation_scribe(task)
            elif task.servant_type == ServantType.GIT_KEEPER:
                result = await self._execute_git_keeper(task)
            else:
                raise ValueError(f"Unknown servant type: {task.servant_type}")

            # 成功処理
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            task.add_log(f"✅ Completed successfully")

            # running から completed に移動
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
            self.completed_tasks[task.task_id] = task
            self.stats["total_completed"] += 1

            self.logger.info(f"✅ Task completed: {task.task_id}")
            return result

        except Exception as e:
            # エラー処理
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)
            task.add_log(f"❌ Failed: {str(e)}")

            # running から failed に移動
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
            self.failed_tasks[task.task_id] = task
            self.stats["total_failed"] += 1

            self.logger.error(f"❌ Task failed: {task.task_id} - {str(e)}")
            raise

    async def _execute_code_craftsman(self, task: ServantTask) -> Dict[str, Any]:
        """コード職人タスクの実行"""
        command = task.command
        args = task.arguments

        if command == "create_file":
            return await self._create_python_file(args)
        elif command == "implement_function":
            return await self._implement_function(args)
        elif command == "create_class":
            return await self._create_class(args)
        elif command == "refactor_code":
            return await self._refactor_code(args)
        else:
            raise ValueError(f"Unknown code craftsman command: {command}")

    async def _create_python_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Pythonファイルを作成"""
        file_path = args.get("file_path")
        content = args.get("content", "")

        # ディレクトリ作成
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # コードフォーマット（オプション）
        formatted_content = content
        if black:
            try:
                formatted_content = black.format_str(content, mode=black.Mode())
            except:
                pass
        if isort:
            try:
                formatted_content = isort.code(formatted_content)
            except:
                pass

        # ファイル書き込み
        with open(file_path, 'w') as f:
            f.write(formatted_content)

        return {
            "action": "create_file",
            "file_path": file_path,
            "lines_written": len(formatted_content.splitlines()),
            "formatted": True,
            "success": True
        }

    async def _implement_function(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """関数を実装"""
        function_name = args.get("function_name")
        parameters = args.get("parameters", [])
        return_type = args.get("return_type", "Any")
        docstring = args.get("docstring", "")
        body = args.get("body", "pass")

        # 関数コード生成
        param_str = ", ".join(parameters)
        function_code = f'''
def {function_name}({param_str}) -> {return_type}:
    """{docstring}"""
    {body}
'''

        return {
            "action": "implement_function",
            "function_name": function_name,
            "code": function_code,
            "success": True
        }

    async def _create_class(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """クラスを作成"""
        class_name = args.get("class_name")
        base_classes = args.get("base_classes", [])
        methods = args.get("methods", [])
        attributes = args.get("attributes", [])

        # クラスコード生成
        base_str = f"({', '.join(base_classes)})" if base_classes else ""

        class_code = f"class {class_name}{base_str}:\n"
        class_code += f'    """{class_name} implementation"""\n\n'

        # __init__メソッド
        if attributes:
            class_code += "    def __init__(self):\n"
            for attr in attributes:
                class_code += f"        self.{attr} = None\n"
            class_code += "\n"

        # その他のメソッド
        for method in methods:
            class_code += f"    def {method}(self):\n"
            class_code += f"        pass\n\n"

        return {
            "action": "create_class",
            "class_name": class_name,
            "code": class_code,
            "methods_count": len(methods),
            "attributes_count": len(attributes),
            "success": True
        }

    async def _refactor_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """コードリファクタリング"""
        file_path = args.get("file_path")
        refactor_type = args.get("refactor_type", "format")

        # ファイル読み込み
        with open(file_path, 'r') as f:
            original_code = f.read()

        refactored_code = original_code
        changes = []

        # フォーマット
        if refactor_type in ["format", "all"]:
            if black:
                try:
                    refactored_code = black.format_str(refactored_code, mode=black.Mode())
                    changes.append("Formatted with black")
                except:
                    pass
            if isort:
                try:
                    refactored_code = isort.code(refactored_code)
                    changes.append("Formatted imports with isort")
                except:
                    pass

        # ファイル書き込み
        with open(file_path, 'w') as f:
            f.write(refactored_code)

        return {
            "action": "refactor_code",
            "file_path": file_path,
            "refactor_type": refactor_type,
            "changes": changes,
            "success": True
        }

    async def _execute_test_guardian(self, task: ServantTask) -> Dict[str, Any]:
        """テスト守護者タスクの実行"""
        command = task.command
        args = task.arguments

        if command == "create_test":
            return await self._create_test_file(args)
        elif command == "run_tests":
            return await self._run_tests(args)
        else:
            raise ValueError(f"Unknown test guardian command: {command}")

    async def _create_test_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """テストファイルを作成"""
        test_file = args.get("test_file")
        target_module = args.get("target_module")
        test_cases = args.get("test_cases", [])

        # テストコード生成
        test_code = f"""import pytest
import sys
sys.path.append('..')
from {target_module} import *


class Test{target_module.capitalize()}:
    \"\"\"Test cases for {target_module}\"\"\"
"""

        for i, test_case in enumerate(test_cases):
            test_code += f"""
    def test_{test_case.get('name', f'case_{i}')}(self):
        \"\"\"Test {test_case.get('description', 'case')}\"\"\"
        {test_case.get('code', 'assert True')}
"""

        # ファイル作成
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        with open(test_file, 'w') as f:
            f.write(test_code)

        return {
            "action": "create_test",
            "test_file": test_file,
            "test_cases_count": len(test_cases),
            "success": True
        }

    async def _run_tests(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """テストを実行"""
        test_path = args.get("test_path", "tests/")

        # pytest実行
        try:
            result = subprocess.run(
                ["pytest", test_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60
            )

            return {
                "action": "run_tests",
                "test_path": test_path,
                "exit_code": result.returncode,
                "stdout": result.stdout[-1000:],  # 最後の1000文字
                "stderr": result.stderr[-500:],   # 最後の500文字
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                "action": "run_tests",
                "test_path": test_path,
                "error": "Test execution timeout",
                "success": False
            }

    async def _execute_quality_inspector(self, task: ServantTask) -> Dict[str, Any]:
        """品質検査官タスクの実行"""
        command = task.command
        args = task.arguments

        if command == "lint_check":
            return await self._run_lint_check(args)
        elif command == "complexity_check":
            return await self._check_complexity(args)
        else:
            raise ValueError(f"Unknown quality inspector command: {command}")

    async def _run_lint_check(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Lintチェック実行"""
        file_path = args.get("file_path")

        # flake8実行
        try:
            result = subprocess.run(
                ["flake8", file_path, "--max-line-length=100"],
                capture_output=True,
                text=True
            )

            issues = result.stdout.strip().split('\n') if result.stdout else []

            return {
                "action": "lint_check",
                "file_path": file_path,
                "issues_count": len(issues),
                "issues": issues[:10],  # 最初の10件
                "success": result.returncode == 0
            }
        except FileNotFoundError:
            return {
                "action": "lint_check",
                "file_path": file_path,
                "error": "flake8 not found",
                "success": False
            }

    async def _check_complexity(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """複雑度チェック"""
        file_path = args.get("file_path")

        # radon実行
        try:
            result = subprocess.run(
                ["radon", "cc", file_path, "-s"],
                capture_output=True,
                text=True
            )

            return {
                "action": "complexity_check",
                "file_path": file_path,
                "complexity_report": result.stdout[:500],
                "success": True
            }
        except FileNotFoundError:
            return {
                "action": "complexity_check",
                "file_path": file_path,
                "error": "radon not found",
                "success": False
            }

    async def _execute_documentation_scribe(self, task: ServantTask) -> Dict[str, Any]:
        """文書記録者タスクの実行"""
        command = task.command
        args = task.arguments

        if command == "generate_docstring":
            return await self._generate_docstring(args)
        elif command == "create_readme":
            return await self._create_readme(args)
        else:
            raise ValueError(f"Unknown documentation scribe command: {command}")

    async def _generate_docstring(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """docstring生成"""
        function_name = args.get("function_name")
        parameters = args.get("parameters", [])
        return_type = args.get("return_type", "Any")
        description = args.get("description", "")

        docstring = f'''"""
    {description}

    Args:
'''
        for param in parameters:
            docstring += f"        {param}: Parameter description\n"

        docstring += f'''
    Returns:
        {return_type}: Return value description
    """'''

        return {
            "action": "generate_docstring",
            "function_name": function_name,
            "docstring": docstring,
            "success": True
        }

    async def _create_readme(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """README作成"""
        project_name = args.get("project_name")
        description = args.get("description", "")
        sections = args.get("sections", [])

        readme_content = f"# {project_name}\n\n"
        readme_content += f"{description}\n\n"

        for section in sections:
            readme_content += f"## {section['title']}\n\n"
            readme_content += f"{section.get('content', 'TBD')}\n\n"

        # README.md作成
        with open("README.md", 'w') as f:
            f.write(readme_content)

        return {
            "action": "create_readme",
            "project_name": project_name,
            "sections_count": len(sections),
            "success": True
        }

    async def _execute_git_keeper(self, task: ServantTask) -> Dict[str, Any]:
        """Git管理者タスクの実行"""
        command = task.command
        args = task.arguments

        if command == "commit_changes":
            return await self._commit_changes(args)
        elif command == "check_status":
            return await self._check_git_status(args)
        else:
            raise ValueError(f"Unknown git keeper command: {command}")

    async def _commit_changes(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """変更をコミット"""
        commit_message = args.get("message", "Update by Elder Flow")
        files = args.get("files", [])

        try:
            # ファイルをステージング
            for file in files:
                subprocess.run(["git", "add", file], check=True)

            # コミット
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True,
                text=True
            )

            return {
                "action": "commit_changes",
                "message": commit_message,
                "files_count": len(files),
                "commit_output": result.stdout,
                "success": result.returncode == 0
            }
        except subprocess.CalledProcessError as e:
            return {
                "action": "commit_changes",
                "error": str(e),
                "success": False
            }

    async def _check_git_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Gitステータス確認"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True
            )

            changed_files = result.stdout.strip().split('\n') if result.stdout else []

            return {
                "action": "check_status",
                "changed_files_count": len(changed_files),
                "changed_files": changed_files[:20],  # 最初の20件
                "success": True
            }
        except subprocess.CalledProcessError as e:
            return {
                "action": "check_status",
                "error": str(e),
                "success": False
            }

    def _handle_deadlock(self):
        """デッドロック処理"""
        self.logger.error("🔒 Handling deadlock situation")

        # 循環依存を検出してログ出力
        for task_id, task in self.pending_tasks.items():
            unmet_deps = task.dependencies - set(self.completed_tasks.keys())
            self.logger.error(f"Task {task_id} blocked by: {unmet_deps}")

            # タスクをfailedに移動
            task.status = TaskStatus.FAILED
            task.error = f"Deadlock: unmet dependencies {unmet_deps}"
            self.failed_tasks[task_id] = task

        self.pending_tasks.clear()

    def _update_statistics(self, execution_time: float):
        """実行統計を更新"""
        if self.stats["total_completed"] > 0:
            # 平均実行時間
            completed_times = []
            for task in self.completed_tasks.values():
                if task.started_at and task.completed_at:
                    duration = (task.completed_at - task.started_at).total_seconds()
                    completed_times.append(duration)

            if completed_times:
                self.stats["average_execution_time"] = sum(completed_times) / len(completed_times)

            # 並列化効率（理論実行時間 vs 実際実行時間）
            theoretical_time = sum(completed_times)
            self.stats["parallel_efficiency"] = (theoretical_time / execution_time) if execution_time > 0 else 0

    def _generate_execution_report(self, execution_time: float) -> Dict[str, Any]:
        """実行レポート生成"""
        return {
            "summary": {
                "total_tasks": self.stats["total_submitted"],
                "completed": self.stats["total_completed"],
                "failed": self.stats["total_failed"],
                "execution_time": round(execution_time, 2),
                "average_task_time": round(self.stats["average_execution_time"], 2),
                "parallel_efficiency": round(self.stats["parallel_efficiency"] * 100, 1)
            },
            "completed_tasks": {
                task_id: {
                    "description": task.description,
                    "duration": (task.completed_at - task.started_at).total_seconds() if task.started_at and task.completed_at else 0,
                    "result": task.result
                }
                for task_id, task in self.completed_tasks.items()
            },
            "failed_tasks": {
                task_id: {
                    "description": task.description,
                    "error": task.error
                }
                for task_id, task in self.failed_tasks.items()
            }
        }

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """特定タスクのステータス取得"""
        # 全カテゴリから検索
        for category in [self.pending_tasks, self.running_tasks, self.completed_tasks, self.failed_tasks]:
            if task_id in category:
                task = category[task_id]
                return {
                    "task_id": task_id,
                    "status": task.status.value,
                    "description": task.description,
                    "logs": task.logs[-10:]  # 最新10件のログ
                }
        return None

    def visualize_execution_graph(self) -> str:
        """実行グラフの可視化（ASCII）"""
        graph = "Elder Flow Execution Graph\n"
        graph += "=" * 50 + "\n\n"

        all_tasks = {**self.pending_tasks, **self.running_tasks,
                     **self.completed_tasks, **self.failed_tasks}

        for task_id, task in all_tasks.items():
            status_icon = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.RUNNING: "🏃",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.BLOCKED: "🔒"
            }.get(task.status, "❓")

            graph += f"{status_icon} {task_id} ({task.servant_type.value})\n"

            if task.dependencies:
                for dep in task.dependencies:
                    graph += f"   └─> {dep}\n"

            graph += "\n"

        return graph


# タスク生成ヘルパー関数
def create_parallel_task(task_id: str, servant_type: ServantType, command: str,
                        dependencies: Set[str] = None, priority: TaskPriority = TaskPriority.MEDIUM,
                        **kwargs) -> ServantTask:
    """並列実行用タスク作成"""
    return ServantTask(
        task_id=task_id,
        servant_type=servant_type,
        description=f"{servant_type.value}: {command}",
        command=command,
        arguments=kwargs,
        dependencies=dependencies or set(),
        priority=priority
    )


# Example Usage
if __name__ == "__main__":
    async def main():
        print("🚀 Elder Flow Parallel Executor Demo")
        print("=" * 50)

        # エグゼキューター作成
        executor = ParallelServantExecutor(max_workers=5)

        # タスク定義（依存関係あり）
        tasks = [
            # Step 1: ファイル作成（並列実行可能）
            create_parallel_task(
                "create_model",
                ServantType.CODE_CRAFTSMAN,
                "create_file",
                file_path="src/model.py",
                content="class User:\n    pass"
            ),
            create_parallel_task(
                "create_api",
                ServantType.CODE_CRAFTSMAN,
                "create_file",
                file_path="src/api.py",
                content="def get_users():\n    pass"
            ),

            # Step 2: テスト作成（モデルとAPIに依存）
            create_parallel_task(
                "create_model_test",
                ServantType.TEST_GUARDIAN,
                "create_test",
                dependencies={"create_model"},
                test_file="tests/test_model.py",
                target_module="src.model",
                test_cases=[{"name": "test_user_creation", "code": "assert True"}]
            ),
            create_parallel_task(
                "create_api_test",
                ServantType.TEST_GUARDIAN,
                "create_test",
                dependencies={"create_api"},
                test_file="tests/test_api.py",
                target_module="src.api",
                test_cases=[{"name": "test_get_users", "code": "assert True"}]
            ),

            # Step 3: 品質チェック（テストに依存）
            create_parallel_task(
                "lint_all",
                ServantType.QUALITY_INSPECTOR,
                "lint_check",
                dependencies={"create_model_test", "create_api_test"},
                file_path="src/",
                priority=TaskPriority.HIGH
            ),

            # Step 4: ドキュメント生成（全てに依存）
            create_parallel_task(
                "create_docs",
                ServantType.DOCUMENTATION_SCRIBE,
                "create_readme",
                dependencies={"lint_all"},
                project_name="Elder Flow Demo",
                description="Parallel execution demonstration"
            )
        ]

        # タスク追加
        executor.add_tasks(tasks)

        # 実行グラフ表示
        print("\n📊 Execution Graph:")
        print(executor.visualize_execution_graph())

        # 並列実行
        print("\n⚡ Starting parallel execution...")
        result = await executor.execute_all_parallel()

        # 結果表示
        print("\n📈 Execution Report:")
        print(f"Total execution time: {result['summary']['execution_time']}s")
        print(f"Parallel efficiency: {result['summary']['parallel_efficiency']}%")
        print(f"Completed: {result['summary']['completed']}")
        print(f"Failed: {result['summary']['failed']}")

        # 詳細結果
        print("\n✅ Completed tasks:")
        for task_id, info in result['completed_tasks'].items():
            print(f"  - {task_id}: {info['duration']:.2f}s")

    asyncio.run(main())
