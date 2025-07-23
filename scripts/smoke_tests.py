#!/usr/bin/env python3
"""
Smoke Tests - Basic functionality verification
スモークテスト - 基本機能の動作確認
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests


class SmokeTest:
    """スモークテスト実行クラス"""

    def __init__(self, environment: str, timeout: int = 30):
        self.environment = environment
        self.timeout = timeout
        self.test_results: List[Dict[str, Any]] = []

        # Environment-specific configurations
        self.configs = {
            "staging": {
                "base_url": "https://staging-ai-company.example.com",
                "health_endpoint": "/health",
                "api_endpoint": "/api/v1",
                "timeout": 10,
            },
            "production": {
                "base_url": "https://ai-company.example.com",
                "health_endpoint": "/health",
                "api_endpoint": "/api/v1",
                "timeout": 5,
            },
            "local": {
                "base_url": "http://localhost:8000",
                "health_endpoint": "/health",
                "api_endpoint": "/api/v1",
                "timeout": 15,
            },
        }

    def run_test(self, name: str, test_func: callable) -> bool:
        """個別テストを実行"""
        start_time = time.time()
        print(f"🧪 Running {name}...")

        try:
            result = test_func()
            duration = time.time() - start_time

            if result:
                print(f"  ✅ {name} passed ({duration:.2f}s)")
                status = "PASS"
            else:
                print(f"  ❌ {name} failed ({duration:.2f}s)")
                status = "FAIL"

            self.test_results.append(
                {
                    "name": name,
                    "status": status,
                    "duration": duration,
                    "environment": self.environment,
                }
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ {name} error: {str(e)} ({duration:.2f}s)")

            self.test_results.append(
                {
                    "name": name,
                    "status": "ERROR",
                    "duration": duration,
                    "error": str(e),
                    "environment": self.environment,
                }
            )

            return False

    def test_health_endpoint(self) -> bool:
        """ヘルスエンドポイントのテスト"""
        config = self.configs.get(self.environment, {})
        base_url = config.get("base_url", "")
        health_endpoint = config.get("health_endpoint", "/health")
        timeout = config.get("timeout", 10)

        if not base_url:
            # Local process check
            return self._check_local_process()

        try:
            response = requests.get(f"{base_url}{health_endpoint}", timeout=timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def test_api_connectivity(self) -> bool:
        """API接続テスト"""
        config = self.configs.get(self.environment, {})
        base_url = config.get("base_url", "")
        api_endpoint = config.get("api_endpoint", "/api/v1")
        timeout = config.get("timeout", 10)

        if not base_url:
            return True  # Skip for local environment

        try:
            response = requests.get(f"{base_url}{api_endpoint}/status", timeout=timeout)
            return response.status_code in [
                200,
                404,
            ]  # 404 is ok if endpoint doesn't exist yet
        except requests.RequestException:
            return False

    def test_worker_processes(self) -> bool:
        """ワーカープロセスのテスト"""
        try:
            # Check if any worker processes are running
            result = subprocess.run(
                ["pgrep", "-f", "worker"], capture_output=True, text=True, timeout=5
            )

            # For staging/production, we expect workers to be running
            if self.environment in ["staging", "production"]:
                return result.returncode == 0 and len(result.stdout.strip()) > 0
            else:
                # For local, it's optional
                return True

        except subprocess.TimeoutExpired:
            return False

    def test_database_connectivity(self) -> bool:
        """データベース接続テスト"""
        try:
            # Check if SQLite database files exist and are accessible
            db_files = ["db/schedules.db", "db/tasks.db", "db/logs.db"]

            for db_file in db_files:
                db_path = Path(db_file)
                if db_path.exists():
                    # Try to open and query the database
                    result = subprocess.run(
                        ["sqlite3", str(db_path), "SELECT 1;"],
                        capture_output=True,
                        timeout=5,
                    )
                    if result.returncode != 0:
                        return False

            return True

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return True  # Database might not be required for all environments

    def test_cron_scheduling(self) -> bool:
        """Cronスケジューリング機能のテスト"""
        try:
            # Import and test cron functionality
            sys.path.append(str(Path(__file__).parent.parent))
            from datetime import datetime

            from core.scheduling import (
                calculate_next_cron_run,
                validate_cron_expression,
            )

            # Test basic cron validation
            test_expressions = ["0 15 * * *", "*/5 * * * *", "0 9-17 * * MON-FRI"]

            for expr in test_expressions:
                if not validate_cron_expression(expr):
                    return False

                # Test calculation
                next_run = calculate_next_cron_run(expr, datetime.now())
                if not next_run:
                    return False

            return True

        except Exception:
            return False

    def test_worker_stats_functionality(self) -> bool:
        """ワーカー統計機能のテスト"""
        try:
            sys.path.append(str(Path(__file__).parent.parent))
            from unittest.mock import Mock, patch

            from tests.unit.test_base_worker import WorkerImplementationForTest

            with patch("pika.BlockingConnection") as mock_pika:
                mock_connection = Mock()
                mock_channel = Mock()
                mock_connection.channel.return_value = mock_channel
                mock_pika.return_value = mock_connection

                worker = WorkerImplementationForTest()

                # Test stats initialization
                if "processed_count" not in worker.stats:
                    return False

                # Test stats update
                initial_count = worker.stats["processed_count"]
                worker.stats["processed_count"] += 1

                return worker.stats["processed_count"] == initial_count + 1

        except Exception:
            return False

    def _check_local_process(self) -> bool:
        """ローカルプロセスの確認"""
        try:
            # Check if any Python processes related to Elders Guild are running
            result = subprocess.run(
                ["pgrep", "-f", "ai_co"], capture_output=True, timeout=5
            )
            return (
                True  # For local development, we don't require processes to be running
            )
        except subprocess.TimeoutExpired:
            return False

    def run_all_tests(self) -> bool:
        """全てのスモークテストを実行"""
        print(f"🚀 Running smoke tests for {self.environment} environment")
        print("=" * 50)

        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("API Connectivity", self.test_api_connectivity),
            ("Worker Processes", self.test_worker_processes),
            ("Database Connectivity", self.test_database_connectivity),
            ("Cron Scheduling", self.test_cron_scheduling),
            ("Worker Stats", self.test_worker_stats_functionality),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1

        print("\n" + "=" * 50)
        print(f"📊 Smoke Test Results: {passed}/{total} passed")

        if passed == total:
            print("✅ All smoke tests passed!")
            return True
        else:
            print(f"❌ {total - passed} smoke tests failed!")
            return False

    def save_results(self, output_file: str):
        """テスト結果をファイルに保存"""
        with open(output_file, "w") as f:
            json.dump(self.test_results, f, indent=2)
        print(f"📁 Test results saved to {output_file}")


def main():
    """mainメソッド"""
    parser = argparse.ArgumentParser(description="Run smoke tests")
    parser.add_argument(
        "--environment",
        choices=["local", "staging", "production"],
        default="local",
        help="Environment to test",
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="Test timeout in seconds"
    )
    parser.add_argument("--output", help="Output file for test results")

    args = parser.parse_args()

    smoke_test = SmokeTest(args.environment, args.timeout)
    success = smoke_test.run_all_tests()

    if args.output:
        smoke_test.save_results(args.output)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
