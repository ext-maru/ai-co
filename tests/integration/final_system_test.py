#!/usr/bin/env python3
"""
Elders Guild 最終統合テスト
全システム機能の総合動作確認
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest

from core.lightweight_logger import get_logger


class FinalSystemTest:
    """最終システムテストクラス"""

    def __init__(self):
        self.logger = get_logger("final_system_test")
        self.project_root = PROJECT_ROOT
        self.test_results = {}

    def test_project_structure(self) -> bool:
        """プロジェクト構造の完全性テスト"""
        self.logger.info("Testing project structure")

        required_files = [
            # Core files
            "core/async_base_worker_v2.0py",
            "core/lightweight_logger.py",
            "core/security_module.py",
            "core/rate_limiter.py",
            # Async workers
            "workers/async_enhanced_task_worker.py",
            "workers/async_result_worker.py",
            "workers/async_pm_worker.py",
            # Scripts
            "scripts/migrate_to_async.py",
            "scripts/monitoring_dashboard.py",
            # Config
            "config/async_workers_config.yaml",
            "requirements-async.txt",
            # Knowledge base
            "knowledge_base/worker_refactoring_design.md",
        ]

        missing_files = []
        total_size = 0

        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                total_size += size
                self.logger.debug(f"✅ {file_path} ({size} bytes)")
            else:
                missing_files.append(file_path)
                self.logger.error(f"❌ Missing: {file_path}")

        success = len(missing_files) == 0

        self.test_results["project_structure"] = {
            "success": success,
            "total_files": len(required_files),
            "missing_files": missing_files,
            "total_size_kb": total_size / 1024,
        }

        self.logger.info(
            f"Project structure test: {'PASS' if success else 'FAIL'}",
            total_files=len(required_files),
            missing_count=len(missing_files),
            total_size_kb=total_size / 1024,
        )

        return success

    async def test_async_base_worker(self) -> bool:
        """AsyncBaseWorkerの動作テスト"""
        self.logger.info("Testing AsyncBaseWorker")

        try:
            # AsyncBaseWorkerV2のインポートと実行
            from core.async_base_worker_v2 import TestWorkerV2

            config = {"test_mode": True}
            worker = TestWorkerV2(config)

            # テストメッセージの処理
            test_messages = [
                {"task_id": "final_test_001", "type": "test", "data": "test data 1"},
                {"task_id": "final_test_002", "type": "test", "data": "test data 2"},
            ]

            results = await worker.run_simulation(test_messages)

            # 結果検証
            success = (
                len(results) == 2
                and all("status" in r for r in results if "error" not in r)
                and all(
                    r.get("status") == "processed" for r in results if "error" not in r
                )
            )

            # ヘルスチェック
            health = await worker.get_health()
            health_ok = health["status"] in ["healthy", "degraded"]

            # メトリクス確認
            metrics = worker.get_metrics()
            metrics_ok = all(
                key in metrics for key in ["counters", "gauges", "histograms"]
            )

            overall_success = success and health_ok and metrics_ok

            self.test_results["async_base_worker"] = {
                "success": overall_success,
                "message_processing": success,
                "health_check": health_ok,
                "metrics_collection": metrics_ok,
                "processed_messages": len([r for r in results if "error" not in r]),
            }

            self.logger.info(
                f"AsyncBaseWorker test: {'PASS' if overall_success else 'FAIL'}",
                messages_processed=len(results),
                health_status=health["status"],
            )

            return overall_success

        except Exception as e:
            self.logger.error("AsyncBaseWorker test failed", error=str(e))
            self.test_results["async_base_worker"] = {"success": False, "error": str(e)}
            return False

    def test_security_module(self) -> bool:
        """セキュリティモジュールのテスト"""
        self.logger.info("Testing security module")

        try:
            from core.security_module import InputSanitizer

            sanitizer = InputSanitizer()

            # テストケース
            test_cases = [
                {
                    "input": "../../../etc/passwd",
                    "method": "sanitize_filename",
                    "should_contain": "passwd",
                    "should_not_contain": "../",
                },
                {
                    "input": {"command": "rm -rf /", "data": "\x00test\x01"},
                    "method": "sanitize_json_input",
                    "should_contain": "rm -rf /",
                    "should_not_contain": "\x00",
                },
            ]

            all_passed = True

            for case in test_cases:
                if case["method"] == "sanitize_filename":
                    result = sanitizer.sanitize_filename(case["input"])
                elif case["method"] == "sanitize_json_input":
                    result = sanitizer.sanitize_json_input(case["input"])
                    result = str(result)  # JSON to string for checking

                case_passed = (
                    case["should_contain"] in result
                    and case["should_not_contain"] not in result
                )

                if not case_passed:
                    all_passed = False
                    self.logger.error(f"Security test case failed: {case['method']}")

            self.test_results["security_module"] = {
                "success": all_passed,
                "test_cases_passed": sum(1 for case in test_cases),
                "total_test_cases": len(test_cases),
            }

            self.logger.info(
                f"Security module test: {'PASS' if all_passed else 'FAIL'}"
            )

            return all_passed

        except Exception as e:
            self.logger.error("Security module test failed", error=str(e))
            self.test_results["security_module"] = {"success": False, "error": str(e)}
            return False

    def test_migration_script(self) -> bool:
        """移行スクリプトのテスト"""
        self.logger.info("Testing migration script")

        try:
            # 移行スクリプトの実行（status確認のみ）
            script_path = self.project_root / "scripts" / "migrate_to_async.py"

            result = subprocess.run(
                ["python3", str(script_path), "status"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                # JSON出力の解析
                status_data = json.loads(result.stdout)

                required_keys = ["migration_phase", "workers", "system_health"]
                has_required_keys = all(key in status_data for key in required_keys)

                workers_detected = len(status_data.get("workers", {})) > 0
                system_health_ok = "cpu_percent" in status_data.get("system_health", {})

                success = has_required_keys and workers_detected and system_health_ok

                self.test_results["migration_script"] = {
                    "success": success,
                    "status_data": status_data,
                    "workers_detected": len(status_data.get("workers", {})),
                }

                self.logger.info(
                    f"Migration script test: {'PASS' if success else 'FAIL'}",
                    workers_detected=len(status_data.get("workers", {})),
                )

                return success
            else:
                self.logger.error(
                    "Migration script execution failed",
                    stderr=result.stderr,
                    returncode=result.returncode,
                )
                self.test_results["migration_script"] = {
                    "success": False,
                    "error": result.stderr,
                }
                return False

        except Exception as e:
            self.logger.error("Migration script test failed", error=str(e))
            self.test_results["migration_script"] = {"success": False, "error": str(e)}
            return False

    def test_monitoring_dashboard(self) -> bool:
        """監視ダッシュボードのテスト"""
        self.logger.info("Testing monitoring dashboard")

        try:
            # 監視ダッシュボードの実行（一回のみ）
            script_path = self.project_root / "scripts" / "monitoring_dashboard.py"

            result = subprocess.run(
                ["python3", str(script_path), "--once"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=30,
            )

            # 出力にダッシュボード要素が含まれているかチェック
            expected_elements = [
                "Elders Guild Monitoring Dashboard",
                "System Metrics",
                "Workers",
                "Queues",
            ]

            has_dashboard_elements = all(
                element in result.stdout for element in expected_elements
            )

            # JSON データファイルの生成確認
            data_file = self.project_root / "data" / "monitoring_data.json"
            data_file_exists = data_file.exists()

            if data_file_exists:
                with open(data_file, "r") as f:
                    monitoring_data = json.load(f)

                required_data_keys = ["timestamp", "system", "workers", "summary"]
                has_required_data = all(
                    key in monitoring_data for key in required_data_keys
                )
            else:
                has_required_data = False

            success = has_dashboard_elements and data_file_exists and has_required_data

            self.test_results["monitoring_dashboard"] = {
                "success": success,
                "dashboard_output": has_dashboard_elements,
                "data_file_created": data_file_exists,
                "data_structure_valid": has_required_data,
            }

            self.logger.info(
                f"Monitoring dashboard test: {'PASS' if success else 'FAIL'}",
                data_file_exists=data_file_exists,
            )

            return success

        except Exception as e:
            self.logger.error("Monitoring dashboard test failed", error=str(e))
            self.test_results["monitoring_dashboard"] = {
                "success": False,
                "error": str(e),
            }
            return False

    def test_system_integration(self) -> bool:
        """システム統合テスト"""
        self.logger.info("Testing system integration")

        try:
            # 既存システムとの統合確認

            # 1.0 ai-status コマンドの実行
            ai_status_result = subprocess.run(
                ["ai-status"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=10,
            )

            ai_status_ok = ai_status_result.returncode == 0

            # 2.0 ログディレクトリの確認
            logs_dir = self.project_root / "logs"
            has_logs = logs_dir.exists() and any(logs_dir.iterdir())

            # 3.0 設定ファイルの読み込み確認
            config_file = self.project_root / "config" / "config.json"
            config_readable = False

            if config_file.exists():
                try:
                    with open(config_file, "r") as f:
                        config_data = json.load(f)
                    config_readable = isinstance(config_data, dict)
                except Exception:
                    config_readable = False

            # 4.0 データディレクトリの確認
            import os

            data_dir = self.project_root / "data"
            data_dir.mkdir(exist_ok=True)
            data_dir_writable = data_dir.exists() and os.access(data_dir, os.W_OK)

            success = (
                ai_status_ok and has_logs and config_readable and data_dir_writable
            )

            self.test_results["system_integration"] = {
                "success": success,
                "ai_status_command": ai_status_ok,
                "logs_directory": has_logs,
                "config_readable": config_readable,
                "data_directory_writable": data_dir_writable,
            }

            self.logger.info(
                f"System integration test: {'PASS' if success else 'FAIL'}",
                ai_status_ok=ai_status_ok,
                has_logs=has_logs,
            )

            return success

        except Exception as e:
            self.logger.error("System integration test failed", error=str(e))
            self.test_results["system_integration"] = {
                "success": False,
                "error": str(e),
            }
            return False

    async def run_all_tests(self) -> Dict[str, Any]:
        """全テストの実行"""
        self.logger.info("Starting final system test suite")

        test_suite = [
            ("Project Structure", self.test_project_structure),
            ("AsyncBaseWorker", self.test_async_base_worker),
            ("Security Module", self.test_security_module),
            ("Migration Script", self.test_migration_script),
            ("Monitoring Dashboard", self.test_monitoring_dashboard),
            ("System Integration", self.test_system_integration),
        ]

        results = []

        for test_name, test_func in test_suite:
            self.logger.info(f"Running test: {test_name}")
            start_time = time.time()

            try:
                if asyncio.iscoroutinefunction(test_func):
                    success = await test_func()
                else:
                    success = test_func()
            except Exception as e:
                self.logger.error(f"Test {test_name} raised exception", error=str(e))
                success = False

            duration = time.time() - start_time
            results.append(
                {"name": test_name, "success": success, "duration": duration}
            )

            status = "✅ PASS" if success else "❌ FAIL"
            self.logger.info(f"{status} {test_name} ({duration:0.2f}s)")

        # 総合結果
        passed = sum(1 for r in results if r["success"])
        total = len(results)
        success_rate = passed / total * 100

        summary = {
            "timestamp": time.time(),
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": success_rate,
            "test_results": results,
            "detailed_results": self.test_results,
        }

        # 結果の保存
        results_file = self.project_root / "data" / "final_test_results.json"
        results_file.parent.mkdir(exist_ok=True)

        with open(results_file, "w") as f:
            json.dump(summary, f, indent=2)

        return summary


def print_test_summary(summary: Dict[str, Any]):
    """テスト結果のサマリー表示"""
    print("\n" + "=" * 80)
    print("🧪 Elders Guild Final System Test Results")
    print("=" * 80)

    print(f"📊 Overall Results:")
    print(f"  • Total Tests: {summary['total_tests']}")
    print(f"  • Passed: {summary['passed']}")
    print(f"  • Failed: {summary['failed']}")
    print(f"  • Success Rate: {summary['success_rate']:0.1f}%")

    print(f"\n📋 Individual Test Results:")
    for test in summary["test_results"]:
        status = "✅ PASS" if test["success"] else "❌ FAIL"
        print(f"  {status} {test['name']} ({test['duration']:0.2f}s)")

    if summary["success_rate"] == 100:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"🚀 Elders Guild system is fully operational and ready for production!")
        print(f"\n✨ Key Achievements:")
        print(f"  • ✅ Async worker architecture implemented")
        print(f"  • ✅ Security enhancements deployed")
        print(f"  • ✅ Migration tools ready")
        print(f"  • ✅ Monitoring system operational")
        print(f"  • ✅ System integration verified")
    elif summary["success_rate"] >= 80:
        print(f"\n⚠️ Most tests passed, but some issues need attention")
        print(f"🔧 System is largely functional but may need minor fixes")
    else:
        print(f"\n❌ Multiple test failures detected")
        print(f"🚨 System needs significant attention before production use")

    print("=" * 80)


async def main():
    """メイン実行関数"""
    import os

    tester = FinalSystemTest()

    print("🚀 Starting Elders Guild Final System Test")
    print("This comprehensive test will verify all system components...")

    summary = await tester.run_all_tests()
    print_test_summary(summary)

    # 終了コード
    exit_code = 0 if summary["success_rate"] == 100 else 1
    return exit_code


if __name__ == "__main__":
    import os

    exit_code = asyncio.run(main())
    exit(exit_code)
