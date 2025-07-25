#!/usr/bin/env python3
"""
Pre-deployment Health Check
デプロイ前のヘルスチェック
"""

import argparse
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any

class PreDeploymentCheck:
    """デプロイ前チェッククラス"""

    def __init__(self, environment: str):
        self.environment = environment
        self.checks_passed = []
        self.checks_failed = []

    def run_check(self, name: str, check_func: callable) -> bool:
        """個別チェックを実行"""
        print(f"🔍 Checking {name}...")
        try:
            result, message = check_func()
            if result:
                print(f"  ✅ {name}: {message}")
                self.checks_passed.append(name)
                return True
            else:
                print(f"  ❌ {name}: {message}")
                self.checks_failed.append(name)
                return False
        except Exception as e:
            print(f"  ❌ {name}: Error - {str(e)}")
            self.checks_failed.append(name)
            return False

    def check_dependencies(self) -> tuple[bool, str]:
        """依存関係のチェック"""
        try:
            # Check Python version
            result = subprocess.run(
                ["python3", "--version"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return False, "Python3 not found"

            # Check required packages
            result = subprocess.run(["pip", "check"], capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Dependency issues: {result.stdout}"

            return True, "All dependencies satisfied"
        except Exception as e:
            return False, str(e)

    def check_configuration(self) -> tuple[bool, str]:
        """設定ファイルのチェック"""
        required_configs = [
            "config/config.json",
            "config/system.conf",
            "config/worker.json",
        ]

        missing = []
        for config in required_configs:
            if not Path(config).exists():
                missing.append(config)

        if missing:
            return False, f"Missing config files: {', '.join(missing)}"

        # Validate JSON configs
        json_configs = ["config/config.json", "config/worker.json"]
        for config_file in json_configs:
            try:
                with open(config_file, "r") as f:
                    json.load(f)
            except json.JSONDecodeError:
                return False, f"Invalid JSON in {config_file}"

        return True, "All configurations valid"

    def check_database(self) -> tuple[bool, str]:
        """データベース接続チェック"""
        try:
            # Check if database files exist
            db_files = [
                "data/tasks.db",
                "data/unified_entities.db",
                "data/unified_tasks.db",
            ]

            missing = []
            for db_file in db_files:
                if not Path(db_file).exists():
                    missing.append(db_file)

            if missing:
                return False, f"Missing database files: {', '.join(missing)}"

            # Test database connectivity
            for db_file in db_files:
                result = subprocess.run(
                    ["sqlite3", db_file, "SELECT 1;"], capture_output=True, timeout=5
                )
                if result.returncode != 0:
                    return False, f"Cannot access database: {db_file}"

            return True, "All databases accessible"
        except Exception as e:
            return False, str(e)

    def check_services(self) -> tuple[bool, str]:
        """必要なサービスのチェック"""
        if self.environment == "production":
            # Check if RabbitMQ is accessible
            try:
                result = subprocess.run(
                    ["rabbitmqctl", "status"], capture_output=True, timeout=10
                )
                if result.returncode != 0:
                    return False, "RabbitMQ is not running"
            except:
                return False, "Cannot check RabbitMQ status"

        return True, "All services operational"

    def check_disk_space(self) -> tuple[bool, str]:
        """ディスク容量チェック"""
        try:
            result = subprocess.run(["df", "-h", "."], capture_output=True, text=True)

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    # Parse available space
                    parts = lines[1].split()
                    if len(parts) >= 4:
                        avail = parts[3]
                        # Simple check: ensure at least 1GB available
                        if not ("G" in avail):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if "G" in avail:
                            gb_avail = float(avail.replace("G", ""))
                            if not (gb_avail < 1.0):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if gb_avail < 1.0:
                                return False, f"Low disk space: {avail} available"
                        elif "M" in avail:
                            mb_avail = float(avail.replace("M", ""))
                            if not (mb_avail < 1000):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if mb_avail < 1000:
                                return False, f"Low disk space: {avail} available"

            return True, "Sufficient disk space available"
        except Exception as e:
            return False, str(e)

    def check_permissions(self) -> tuple[bool, str]:
        """ファイル権限チェック"""
        # Check write permissions for key directories

        for dir_name in dirs_to_check:
            dir_path = Path(dir_name)
            if dir_path.exists():
                test_file = dir_path / ".permission_test"
                try:
                    test_file.touch()
                    test_file.unlink()
                except:
                    return False, f"No write permission for {dir_name}/"

        return True, "All permissions correct"

    def run_all_checks(self) -> bool:
        """全チェックを実行"""
        print(f"🚀 Running pre-deployment checks for {self.environment}")
        print("=" * 50)

        checks = [
            ("Dependencies", self.check_dependencies),
            ("Configuration", self.check_configuration),
            ("Database", self.check_database),
            ("Services", self.check_services),
            ("Disk Space", self.check_disk_space),
            ("Permissions", self.check_permissions),
        ]

        all_passed = True
        for check_name, check_func in checks:
            if not self.run_check(check_name, check_func):
                all_passed = False

        print("\n" + "=" * 50)
        print(f"✅ Passed: {len(self.checks_passed)}")
        print(f"❌ Failed: {len(self.checks_failed)}")

        if all_passed:
            print("\n🎉 All pre-deployment checks passed!")
            print(f"Ready to deploy to {self.environment}")
            return True
        else:
            print("\n⚠️  Pre-deployment checks failed!")
            print("Please fix the issues before deploying.")
            return False

def main():
    """mainメソッド"""
    parser = argparse.ArgumentParser(description="Pre-deployment health check")
    parser.add_argument(
        "--environment",
        choices=["staging", "production"],
        required=True,
        help="Target environment",
    )

    args = parser.parse_args()

    checker = PreDeploymentCheck(args.environment)
    success = checker.run_all_checks()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
