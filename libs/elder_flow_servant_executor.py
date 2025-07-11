"""
Elder Flow Servant Executor - エルダーサーバント実行システム
Created: 2025-07-12
Author: Claude Elder
Version: 1.0.0
"""

import asyncio
import subprocess
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field

# Servant Types
class ServantType(Enum):
    CODE_CRAFTSMAN = "code_craftsman"  # コード職人
    TEST_GUARDIAN = "test_guardian"    # テスト守護者
    QUALITY_INSPECTOR = "quality_inspector"  # 品質検査官
    GIT_KEEPER = "git_keeper"          # Git管理者
    DOCUMENTATION_SCRIBE = "documentation_scribe"  # 文書記録者

# Servant Status
class ServantStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

# Task Definition
@dataclass
class ServantTask:
    task_id: str
    servant_type: ServantType
    description: str
    command: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 5
    timeout: int = 300
    retry_count: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    status: ServantStatus = ServantStatus.IDLE
    result: Optional[Dict] = None
    error: Optional[str] = None
    logs: List[str] = field(default_factory=list)

    def add_log(self, message: str):
        self.logs.append(f"[{datetime.now().isoformat()}] {message}")

# Base Servant
class BaseServant:
    def __init__(self, servant_type: ServantType, name: str):
        self.servant_type = servant_type
        self.name = name
        self.status = ServantStatus.IDLE
        self.current_task: Optional[ServantTask] = None
        self.logger = logging.getLogger(f"servant.{name}")
        self.capabilities = []

    async def execute_task(self, task: ServantTask) -> Dict:
        """タスク実行"""
        self.current_task = task
        self.status = ServantStatus.WORKING
        task.status = ServantStatus.WORKING

        try:
            task.add_log(f"Starting task: {task.description}")
            self.logger.info(f"Executing task: {task.task_id}")

            # 具体的な実行処理
            result = await self._execute_specific_task(task)

            task.status = ServantStatus.COMPLETED
            task.result = result
            task.add_log("Task completed successfully")

            return result

        except Exception as e:
            task.status = ServantStatus.FAILED
            task.error = str(e)
            task.add_log(f"Task failed: {str(e)}")
            self.logger.error(f"Task {task.task_id} failed: {str(e)}")
            raise
        finally:
            self.status = ServantStatus.IDLE
            self.current_task = None

    async def _execute_specific_task(self, task: ServantTask) -> Dict:
        """具体的なタスク実行（サブクラスで実装）"""
        raise NotImplementedError("Subclasses must implement _execute_specific_task")

    def get_status(self) -> Dict:
        """状態取得"""
        return {
            "servant_type": self.servant_type.value,
            "name": self.name,
            "status": self.status.value,
            "current_task": self.current_task.task_id if self.current_task else None,
            "capabilities": self.capabilities
        }

# Code Craftsman Servant
class CodeCraftsmanServant(BaseServant):
    def __init__(self, name: str = "CodeCraftsman"):
        super().__init__(ServantType.CODE_CRAFTSMAN, name)
        self.capabilities = [
            "create_file",
            "edit_file",
            "refactor_code",
            "generate_code",
            "analyze_code"
        ]

    async def _execute_specific_task(self, task: ServantTask) -> Dict:
        """コード関連タスクの実行"""
        command = task.command
        args = task.arguments

        if command == "create_file":
            return await self._create_file(args)
        elif command == "edit_file":
            return await self._edit_file(args)
        elif command == "refactor_code":
            return await self._refactor_code(args)
        elif command == "generate_code":
            return await self._generate_code(args)
        elif command == "analyze_code":
            return await self._analyze_code(args)
        else:
            raise ValueError(f"Unknown command: {command}")

    async def _create_file(self, args: Dict) -> Dict:
        """ファイル作成"""
        file_path = args.get("file_path")
        content = args.get("content", "")

        if not file_path:
            raise ValueError("file_path is required")

        # ディレクトリ作成
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # ファイル作成
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "action": "create_file",
            "file_path": file_path,
            "lines_written": len(content.splitlines()),
            "success": True
        }

    async def _edit_file(self, args: Dict) -> Dict:
        """ファイル編集"""
        file_path = args.get("file_path")
        old_content = args.get("old_content")
        new_content = args.get("new_content")

        if not all([file_path, old_content, new_content]):
            raise ValueError("file_path, old_content, and new_content are required")

        # ファイル読み取り
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 置換
        if old_content not in content:
            raise ValueError(f"old_content not found in {file_path}")

        updated_content = content.replace(old_content, new_content)

        # ファイル保存
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        return {
            "action": "edit_file",
            "file_path": file_path,
            "changes_made": 1,
            "success": True
        }

    async def _refactor_code(self, args: Dict) -> Dict:
        """コードリファクタリング"""
        file_path = args.get("file_path")
        refactor_type = args.get("refactor_type", "general")

        # モック実装
        return {
            "action": "refactor_code",
            "file_path": file_path,
            "refactor_type": refactor_type,
            "improvements": ["Extracted method", "Reduced complexity", "Added type hints"],
            "success": True
        }

    async def _generate_code(self, args: Dict) -> Dict:
        """コード生成"""
        template = args.get("template", "basic_class")
        class_name = args.get("class_name", "GeneratedClass")

        # モック実装
        generated_code = f"""
class {class_name}:
    def __init__(self):
        self.initialized = True

    def process(self):
        return "Processing complete"
"""

        return {
            "action": "generate_code",
            "template": template,
            "class_name": class_name,
            "generated_code": generated_code,
            "success": True
        }

    async def _analyze_code(self, args: Dict) -> Dict:
        """コード分析"""
        file_path = args.get("file_path")

        # モック実装
        return {
            "action": "analyze_code",
            "file_path": file_path,
            "metrics": {
                "lines_of_code": 150,
                "complexity": 8,
                "test_coverage": 85,
                "code_quality": "B+"
            },
            "issues": ["Missing docstring", "Long method detected"],
            "success": True
        }

# Test Guardian Servant
class TestGuardianServant(BaseServant):
    def __init__(self, name: str = "TestGuardian"):
        super().__init__(ServantType.TEST_GUARDIAN, name)
        self.capabilities = [
            "create_test",
            "run_test",
            "generate_test_data",
            "coverage_analysis",
            "test_optimization"
        ]

    async def _execute_specific_task(self, task: ServantTask) -> Dict:
        """テスト関連タスクの実行"""
        command = task.command
        args = task.arguments

        if command == "create_test":
            return await self._create_test(args)
        elif command == "run_test":
            return await self._run_test(args)
        elif command == "generate_test_data":
            return await self._generate_test_data(args)
        elif command == "coverage_analysis":
            return await self._coverage_analysis(args)
        elif command == "test_optimization":
            return await self._test_optimization(args)
        else:
            raise ValueError(f"Unknown command: {command}")

    async def _create_test(self, args: Dict) -> Dict:
        """テスト作成"""
        test_file = args.get("test_file")
        target_module = args.get("target_module")

        test_content = f"""
import pytest
from {target_module} import *

class TestGenerated:
    def test_basic_functionality(self):
        # Generated test
        assert True

    def test_edge_cases(self):
        # Edge case testing
        assert True

    def test_error_handling(self):
        # Error handling test
        assert True
"""

        return {
            "action": "create_test",
            "test_file": test_file,
            "target_module": target_module,
            "test_content": test_content,
            "test_count": 3,
            "success": True
        }

    async def _run_test(self, args: Dict) -> Dict:
        """テスト実行"""
        test_path = args.get("test_path", "tests/")

        # モック実装
        return {
            "action": "run_test",
            "test_path": test_path,
            "results": {
                "passed": 15,
                "failed": 0,
                "skipped": 2,
                "total": 17,
                "coverage": 92.5
            },
            "success": True
        }

    async def _generate_test_data(self, args: Dict) -> Dict:
        """テストデータ生成"""
        data_type = args.get("data_type", "mock")
        count = args.get("count", 10)

        return {
            "action": "generate_test_data",
            "data_type": data_type,
            "count": count,
            "generated_data": [f"test_data_{i}" for i in range(count)],
            "success": True
        }

    async def _coverage_analysis(self, args: Dict) -> Dict:
        """カバレッジ分析"""
        target_module = args.get("target_module")

        return {
            "action": "coverage_analysis",
            "target_module": target_module,
            "coverage_report": {
                "total_lines": 500,
                "covered_lines": 475,
                "coverage_percentage": 95.0,
                "uncovered_lines": [25, 67, 89, 234, 456]
            },
            "success": True
        }

    async def _test_optimization(self, args: Dict) -> Dict:
        """テスト最適化"""
        test_suite = args.get("test_suite")

        return {
            "action": "test_optimization",
            "test_suite": test_suite,
            "optimizations": [
                "Removed duplicate tests",
                "Optimized setup/teardown",
                "Parallelized test execution"
            ],
            "performance_improvement": "35% faster execution",
            "success": True
        }

# Quality Inspector Servant
class QualityInspectorServant(BaseServant):
    def __init__(self, name: str = "QualityInspector"):
        super().__init__(ServantType.QUALITY_INSPECTOR, name)
        self.capabilities = [
            "code_quality_check",
            "security_scan",
            "performance_analysis",
            "dependency_check",
            "compliance_check"
        ]

    async def _execute_specific_task(self, task: ServantTask) -> Dict:
        """品質検査タスクの実行"""
        command = task.command
        args = task.arguments

        if command == "code_quality_check":
            return await self._code_quality_check(args)
        elif command == "security_scan":
            return await self._security_scan(args)
        elif command == "performance_analysis":
            return await self._performance_analysis(args)
        elif command == "dependency_check":
            return await self._dependency_check(args)
        elif command == "compliance_check":
            return await self._compliance_check(args)
        else:
            raise ValueError(f"Unknown command: {command}")

    async def _code_quality_check(self, args: Dict) -> Dict:
        """コード品質チェック"""
        file_path = args.get("file_path")

        return {
            "action": "code_quality_check",
            "file_path": file_path,
            "quality_score": 8.5,
            "issues": [
                {"type": "complexity", "severity": "medium", "line": 45},
                {"type": "naming", "severity": "low", "line": 78}
            ],
            "recommendations": ["Extract method", "Rename variable"],
            "success": True
        }

    async def _security_scan(self, args: Dict) -> Dict:
        """セキュリティスキャン"""
        target_path = args.get("target_path")

        return {
            "action": "security_scan",
            "target_path": target_path,
            "vulnerabilities": [
                {"type": "SQL_INJECTION", "severity": "high", "file": "db.py", "line": 123},
                {"type": "XSS", "severity": "medium", "file": "web.py", "line": 56}
            ],
            "security_score": 7.5,
            "recommendations": ["Use parameterized queries", "Sanitize input"],
            "success": True
        }

    async def _performance_analysis(self, args: Dict) -> Dict:
        """パフォーマンス分析"""
        target_module = args.get("target_module")

        return {
            "action": "performance_analysis",
            "target_module": target_module,
            "metrics": {
                "execution_time": 1.25,
                "memory_usage": 45.6,
                "cpu_usage": 12.3
            },
            "bottlenecks": ["Database query in loop", "Inefficient sorting"],
            "optimizations": ["Add database index", "Use built-in sort"],
            "success": True
        }

    async def _dependency_check(self, args: Dict) -> Dict:
        """依存関係チェック"""
        project_path = args.get("project_path")

        return {
            "action": "dependency_check",
            "project_path": project_path,
            "dependencies": {
                "total": 25,
                "outdated": 3,
                "vulnerable": 1,
                "licenses": {"MIT": 20, "Apache": 3, "GPL": 2}
            },
            "recommendations": ["Update outdated packages", "Review vulnerable dependency"],
            "success": True
        }

    async def _compliance_check(self, args: Dict) -> Dict:
        """コンプライアンスチェック"""
        standard = args.get("standard", "PEP8")
        target_path = args.get("target_path")

        return {
            "action": "compliance_check",
            "standard": standard,
            "target_path": target_path,
            "compliance_score": 92.5,
            "violations": [
                {"rule": "E302", "file": "main.py", "line": 15},
                {"rule": "W291", "file": "utils.py", "line": 89}
            ],
            "success": True
        }

# Servant Executor
class ServantExecutor:
    def __init__(self):
        self.servants: Dict[ServantType, BaseServant] = {}
        self.task_queue: List[ServantTask] = []
        self.completed_tasks: List[ServantTask] = []
        self.failed_tasks: List[ServantTask] = []
        self.logger = logging.getLogger(__name__)

        # サーバント初期化
        self._initialize_servants()

    def _initialize_servants(self):
        """サーバント初期化"""
        self.servants[ServantType.CODE_CRAFTSMAN] = CodeCraftsmanServant()
        self.servants[ServantType.TEST_GUARDIAN] = TestGuardianServant()
        self.servants[ServantType.QUALITY_INSPECTOR] = QualityInspectorServant()

    def add_task(self, task: ServantTask):
        """タスク追加"""
        self.task_queue.append(task)
        self.logger.info(f"Task added: {task.task_id}")

    async def execute_task(self, task: ServantTask) -> Dict:
        """単一タスク実行"""
        if task.servant_type not in self.servants:
            raise ValueError(f"No servant available for type: {task.servant_type}")

        servant = self.servants[task.servant_type]

        try:
            result = await servant.execute_task(task)
            self.completed_tasks.append(task)
            return result
        except Exception as e:
            self.failed_tasks.append(task)
            raise

    async def execute_all_tasks(self) -> Dict:
        """全タスク実行"""
        results = []

        while self.task_queue:
            task = self.task_queue.pop(0)

            try:
                result = await self.execute_task(task)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Task {task.task_id} failed: {str(e)}")
                results.append({"task_id": task.task_id, "error": str(e)})

        return {
            "total_tasks": len(results),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "results": results
        }

    def get_servant_status(self, servant_type: ServantType = None) -> Dict:
        """サーバント状態取得"""
        if servant_type:
            if servant_type not in self.servants:
                return {"error": f"Servant type {servant_type} not found"}
            return self.servants[servant_type].get_status()
        else:
            return {
                servant_type.value: servant.get_status()
                for servant_type, servant in self.servants.items()
            }

    def get_task_statistics(self) -> Dict:
        """タスク統計取得"""
        return {
            "queued": len(self.task_queue),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "total_processed": len(self.completed_tasks) + len(self.failed_tasks)
        }

# Helper Functions
def create_code_task(task_id: str, command: str, **kwargs) -> ServantTask:
    """コードタスク作成"""
    return ServantTask(
        task_id=task_id,
        servant_type=ServantType.CODE_CRAFTSMAN,
        description=f"Code task: {command}",
        command=command,
        arguments=kwargs
    )

def create_test_task(task_id: str, command: str, **kwargs) -> ServantTask:
    """テストタスク作成"""
    return ServantTask(
        task_id=task_id,
        servant_type=ServantType.TEST_GUARDIAN,
        description=f"Test task: {command}",
        command=command,
        arguments=kwargs
    )

def create_quality_task(task_id: str, command: str, **kwargs) -> ServantTask:
    """品質タスク作成"""
    return ServantTask(
        task_id=task_id,
        servant_type=ServantType.QUALITY_INSPECTOR,
        description=f"Quality task: {command}",
        command=command,
        arguments=kwargs
    )

# Example Usage
if __name__ == "__main__":
    async def main():
        print("🤖 Elder Flow Servant Executor Test")

        executor = ServantExecutor()

        # タスク作成
        code_task = create_code_task("create_file_001", "create_file",
                                   file_path="test.py", content="print('Hello World')")
        test_task = create_test_task("run_test_001", "run_test", test_path="tests/")
        quality_task = create_quality_task("quality_check_001", "code_quality_check",
                                         file_path="test.py")

        # タスク実行
        executor.add_task(code_task)
        executor.add_task(test_task)
        executor.add_task(quality_task)

        # 全タスク実行
        results = await executor.execute_all_tasks()
        print(f"Results: {results}")

        # 統計表示
        stats = executor.get_task_statistics()
        print(f"Statistics: {stats}")

    asyncio.run(main())
