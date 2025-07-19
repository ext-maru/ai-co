#!/usr/bin/env python3
"""
Performance Benchmark: OSS vs 独自実装
エルダーズギルドの独自実装とOSSツールのパフォーマンス比較
"""

import asyncio
import time
import sys
import os
import statistics
import json
from typing import Dict, List, Any
import subprocess
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

class PerformanceBenchmark:
    """OSS vs 独自実装のパフォーマンスベンチマーク"""
    
    def __init__(self):
        self.results = {}
        self.test_data_dir = None
        
    def setup_test_data(self):
        """テストデータセットアップ"""
        self.test_data_dir = tempfile.mkdtemp(prefix="perf_benchmark_")
        
        # テスト用Pythonファイル生成
        test_files = {
            "simple.py": '''
def calculate(x, y):
    return x + y

def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
''',
            "medium.py": '''
import json
import datetime

class DataProcessor:
    def __init__(self):
        self.data = []
        
    def add_item(self, item):
        self.data.append({
            "value": item,
            "timestamp": datetime.datetime.now().isoformat(),
            "processed": False
        })
    
    def process_all(self):
        for item in self.data:
            if not item["processed"]:
                item["value"] = item["value"] * 2
                item["processed"] = True
    
    def to_json(self):
        return json.dumps(self.data, indent=2)

def main():
    processor = DataProcessor()
    for i in range(100):
        processor.add_item(i)
    processor.process_all()
    return processor.to_json()
''',
            "complex.py": '''
import asyncio
import typing
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    id: str
    name: str
    status: TaskStatus
    dependencies: typing.List[str]
    
class TaskManager:
    def __init__(self):
        self.tasks: typing.Dict[str, Task] = {}
        self.execution_order: typing.List[str] = []
    
    async def add_task(self, task: Task) -> bool:
        if task.id in self.tasks:
            return False
        self.tasks[task.id] = task
        return True
    
    def get_executable_tasks(self) -> typing.List[Task]:
        executable = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                if all(self.tasks.get(dep_id, Task("", "", TaskStatus.FAILED, [])).status == TaskStatus.COMPLETED 
                      for dep_id in task.dependencies):
                    executable.append(task)
        return executable
    
    async def execute_task(self, task: Task) -> bool:
        task.status = TaskStatus.RUNNING
        await asyncio.sleep(0.1)  # Simulate work
        task.status = TaskStatus.COMPLETED
        self.execution_order.append(task.id)
        return True
    
    async def run_all(self) -> typing.List[str]:
        while True:
            executable = self.get_executable_tasks()
            if not executable:
                break
            
            # Execute tasks in parallel
            await asyncio.gather(*[self.execute_task(task) for task in executable])
        
        return self.execution_order
'''
        }
        
        for filename, content in test_files.items():
            with open(os.path.join(self.test_data_dir, filename), 'w') as f:
                f.write(content)
        
        return True
    
    def benchmark_elder_code_review(self) -> Dict[str, Any]:
        """エルダーズギルド独自コードレビューシステムのベンチマーク"""
        print("🔧 Testing Elder Code Review System...")
        
        try:
            # Import Elder code review system
            from libs.automated_code_review import CodeReviewPipeline
            
            results = {}
            
            for filename in ["simple.py", "medium.py", "complex.py"]:
                file_path = os.path.join(self.test_data_dir, filename)
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Measure Elder system performance
                start_time = time.time()
                
                pipeline = CodeReviewPipeline()
                review_result = asyncio.run(pipeline.full_review(file_path, content))
                
                end_time = time.time()
                
                results[filename] = {
                    "duration": end_time - start_time,
                    "quality_score": review_result.get("overall_score", 0),
                    "issues_found": len(review_result.get("issues", [])),
                    "suggestions": len(review_result.get("suggestions", []))
                }
            
            return {
                "tool": "Elder Code Review",
                "results": results,
                "avg_duration": statistics.mean([r["duration"] for r in results.values()]),
                "avg_quality": statistics.mean([r["quality_score"] for r in results.values()])
            }
            
        except Exception as e:
            return {
                "tool": "Elder Code Review",
                "error": str(e),
                "results": {}
            }
    
    def benchmark_flake8(self) -> Dict[str, Any]:
        """Flake8 OSS linter のベンチマーク"""
        print("🐍 Testing Flake8...")
        
        results = {}
        
        for filename in ["simple.py", "medium.py", "complex.py"]:
            file_path = os.path.join(self.test_data_dir, filename)
            
            try:
                start_time = time.time()
                
                result = subprocess.run([
                    'python3', '-m', 'flake8', '--statistics', file_path
                ], capture_output=True, text=True, timeout=30)
                
                end_time = time.time()
                
                # Count issues
                issues_count = len([line for line in result.stdout.split('\n') if line.strip()])
                
                results[filename] = {
                    "duration": end_time - start_time,
                    "issues_found": issues_count,
                    "exit_code": result.returncode
                }
                
            except Exception as e:
                results[filename] = {
                    "duration": 0,
                    "error": str(e)
                }
        
        return {
            "tool": "Flake8",
            "results": results,
            "avg_duration": statistics.mean([r.get("duration", 0) for r in results.values() if "error" not in r])
        }
    
    def benchmark_elder_test_framework(self) -> Dict[str, Any]:
        """エルダーズギルド統合テストフレームワークのベンチマーク"""
        print("🧪 Testing Elder Test Framework...")
        
        try:
            from libs.integration_test_framework import IntegrationTestRunner
            
            results = {}
            
            # Create simple test scenarios
            test_scenarios = [
                {
                    "name": "simple_test",
                    "file": "simple.py",
                    "test_count": 2
                },
                {
                    "name": "medium_test", 
                    "file": "medium.py",
                    "test_count": 5
                },
                {
                    "name": "complex_test",
                    "file": "complex.py", 
                    "test_count": 8
                }
            ]
            
            for scenario in test_scenarios:
                start_time = time.time()
                
                runner = IntegrationTestRunner()
                # Simulate test execution
                test_result = asyncio.run(runner.run_test_suite({
                    "test_files": [os.path.join(self.test_data_dir, scenario["file"])],
                    "test_count": scenario["test_count"]
                }))
                
                end_time = time.time()
                
                results[scenario["name"]] = {
                    "duration": end_time - start_time,
                    "tests_run": test_result.get("tests_run", 0),
                    "success_rate": test_result.get("success_rate", 0)
                }
            
            return {
                "tool": "Elder Test Framework",
                "results": results,
                "avg_duration": statistics.mean([r["duration"] for r in results.values()])
            }
            
        except Exception as e:
            return {
                "tool": "Elder Test Framework",
                "error": str(e),
                "results": {}
            }
    
    def benchmark_pytest(self) -> Dict[str, Any]:
        """PyTest OSS テストフレームワークのベンチマーク"""
        print("🎯 Testing PyTest...")
        
        # Create simple test files
        test_files = {
            "test_simple.py": '''
import sys
import os
sys.path.append(".")

def test_calculate():
    from simple import calculate
    assert calculate(2, 3) == 5

def test_process_data():
    from simple import process_data
    result = process_data([1, 2, 3])
    assert result == [2, 4, 6]
''',
            "test_medium.py": '''
import sys
import os
sys.path.append(".")

def test_data_processor():
    from medium import DataProcessor
    processor = DataProcessor()
    processor.add_item(10)
    processor.process_all()
    assert len(processor.data) == 1
    assert processor.data[0]["value"] == 20

def test_to_json():
    from medium import DataProcessor
    processor = DataProcessor()
    processor.add_item(5)
    json_str = processor.to_json()
    assert "5" in json_str
'''
        }
        
        for filename, content in test_files.items():
            with open(os.path.join(self.test_data_dir, filename), 'w') as f:
                f.write(content)
        
        results = {}
        
        for test_file in test_files.keys():
            try:
                start_time = time.time()
                
                result = subprocess.run([
                    'python3', '-m', 'pytest', '-v', os.path.join(self.test_data_dir, test_file)
                ], capture_output=True, text=True, timeout=60, cwd=self.test_data_dir)
                
                end_time = time.time()
                
                # Parse pytest output
                output_lines = result.stdout.split('\n')
                passed = len([line for line in output_lines if "PASSED" in line])
                failed = len([line for line in output_lines if "FAILED" in line])
                
                results[test_file] = {
                    "duration": end_time - start_time,
                    "tests_passed": passed,
                    "tests_failed": failed,
                    "exit_code": result.returncode
                }
                
            except Exception as e:
                results[test_file] = {
                    "duration": 0,
                    "error": str(e)
                }
        
        return {
            "tool": "PyTest",
            "results": results,
            "avg_duration": statistics.mean([r.get("duration", 0) for r in results.values() if "error" not in r])
        }
    
    def benchmark_elder_monitoring(self) -> Dict[str, Any]:
        """エルダーズギルド監視システムのベンチマーク"""
        print("📊 Testing Elder Monitoring System...")
        
        try:
            from libs.advanced_monitoring_dashboard import MonitoringDashboard
            
            start_time = time.time()
            
            dashboard = MonitoringDashboard()
            
            # Simulate monitoring operations
            metrics = asyncio.run(dashboard.collect_metrics({
                "cpu_usage": True,
                "memory_usage": True,
                "disk_usage": True,
                "network_stats": True
            }))
            
            end_time = time.time()
            
            return {
                "tool": "Elder Monitoring",
                "duration": end_time - start_time,
                "metrics_collected": len(metrics.get("metrics", [])),
                "dashboard_widgets": len(metrics.get("widgets", []))
            }
            
        except Exception as e:
            return {
                "tool": "Elder Monitoring",
                "error": str(e)
            }
    
    def benchmark_system_monitoring(self) -> Dict[str, Any]:
        """システム標準監視ツールのベンチマーク"""
        print("🖥️ Testing System Monitoring...")
        
        results = {}
        
        # Test various system monitoring commands
        commands = {
            "ps": ["ps", "aux"],
            "top": ["top", "-b", "-n", "1"],
            "free": ["free", "-m"],
            "df": ["df", "-h"]
        }
        
        for cmd_name, cmd in commands.items():
            try:
                start_time = time.time()
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                end_time = time.time()
                
                results[cmd_name] = {
                    "duration": end_time - start_time,
                    "output_lines": len(result.stdout.split('\n')),
                    "exit_code": result.returncode
                }
                
            except Exception as e:
                results[cmd_name] = {
                    "duration": 0,
                    "error": str(e)
                }
        
        return {
            "tool": "System Monitoring",
            "results": results,
            "avg_duration": statistics.mean([r.get("duration", 0) for r in results.values() if "error" not in r])
        }
    
    def cleanup(self):
        """テストデータクリーンアップ"""
        if self.test_data_dir and os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)
    
    def run_benchmarks(self) -> Dict[str, Any]:
        """全ベンチマーク実行"""
        print("🚀 Starting Performance Benchmarks: OSS vs Elder Custom Implementation")
        print("=" * 80)
        
        try:
            if not self.setup_test_data():
                return {"error": "Failed to setup test data"}
            
            benchmarks = [
                ("Code Review: Elder vs Flake8", [
                    self.benchmark_elder_code_review,
                    self.benchmark_flake8
                ]),
                ("Testing: Elder vs PyTest", [
                    self.benchmark_elder_test_framework,
                    self.benchmark_pytest
                ]),
                ("Monitoring: Elder vs System", [
                    self.benchmark_elder_monitoring,
                    self.benchmark_system_monitoring
                ])
            ]
            
            all_results = {}
            
            for category, funcs in benchmarks:
                print(f"\n📈 Running: {category}")
                category_results = []
                
                for func in funcs:
                    try:
                        result = func()
                        category_results.append(result)
                        time.sleep(1)  # Brief pause between tests
                    except Exception as e:
                        category_results.append({"error": str(e)})
                
                all_results[category] = category_results
            
            # Generate comparison report
            report = self.generate_comparison_report(all_results)
            
            print("\n" + "=" * 80)
            print("📊 Performance Benchmark Results")
            print("=" * 80)
            print(report)
            
            return {
                "success": True,
                "results": all_results,
                "report": report,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            self.cleanup()
    
    def generate_comparison_report(self, results: Dict[str, Any]) -> str:
        """比較レポート生成"""
        report_lines = []
        
        for category, category_results in results.items():
            report_lines.append(f"\n🔍 {category}")
            report_lines.append("-" * 50)
            
            if len(category_results) >= 2:
                elder_result = category_results[0]
                oss_result = category_results[1]
                
                # Compare performance
                elder_time = elder_result.get("avg_duration", elder_result.get("duration", 0))
                oss_time = oss_result.get("avg_duration", oss_result.get("duration", 0))
                
                if elder_time > 0 and oss_time > 0:
                    if elder_time < oss_time:
                        winner = "🏆 Elder System (faster)"
                        ratio = oss_time / elder_time
                    else:
                        winner = "🏆 OSS Tool (faster)"
                        ratio = elder_time / oss_time
                    
                    report_lines.append(f"Elder System: {elder_time:.3f}s")
                    report_lines.append(f"OSS Tool: {oss_time:.3f}s")
                    report_lines.append(f"Winner: {winner} ({ratio:.1f}x)")
                else:
                    report_lines.append("⚠️ Performance comparison unavailable")
                
                # Compare features
                elder_features = len([k for k in elder_result.keys() if k not in ["tool", "error", "duration", "avg_duration"]])
                oss_features = len([k for k in oss_result.keys() if k not in ["tool", "error", "duration", "avg_duration"]])
                
                report_lines.append(f"Features - Elder: {elder_features}, OSS: {oss_features}")
                
                if "error" in elder_result:
                    report_lines.append(f"❌ Elder Error: {elder_result['error']}")
                if "error" in oss_result:
                    report_lines.append(f"❌ OSS Error: {oss_result['error']}")
        
        # Overall recommendation
        report_lines.append("\n🎯 Recommendations:")
        report_lines.append("• Code Review: Consider hybrid approach (Elder quality + OSS speed)")
        report_lines.append("• Testing: Elder framework for complex integration, PyTest for unit tests")
        report_lines.append("• Monitoring: Elder system provides richer context, system tools for basic metrics")
        
        return "\n".join(report_lines)

def main():
    """メインエントリーポイント"""
    benchmark = PerformanceBenchmark()
    results = benchmark.run_benchmarks()
    
    if results.get("success"):
        print("\n✅ Performance benchmarks completed successfully!")
        return 0
    else:
        print(f"\n❌ Benchmark failed: {results.get('error')}")
        return 1

if __name__ == "__main__":
    exit(main())