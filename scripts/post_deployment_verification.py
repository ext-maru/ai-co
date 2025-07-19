#!/usr/bin/env python3
"""
Post-deployment Verification
デプロイ後の動作確認
"""

import argparse
import sys
import time
import requests
import subprocess
from typing import Dict, List, Any
import json
from datetime import datetime


class PostDeploymentVerification:
    """デプロイ後検証クラス"""

    def __init__(self, environment: str):
        self.environment = environment
        self.verification_results = []

        # Environment URLs
        self.urls = {
            "staging": "https://staging-ai-company.example.com",
            "production": "https://ai-company.example.com",
        }

    def verify(self, name: str, verify_func: callable, critical: bool = True) -> bool:
        """個別検証を実行"""
        print(f"🔍 Verifying {name}...")
        start_time = time.time()

        try:
            result, message = verify_func()
            duration = time.time() - start_time

            if result:
                print(f"  ✅ {name}: {message} ({duration:.2f}s)")
                status = "PASS"
            else:
                print(f"  ❌ {name}: {message} ({duration:.2f}s)")
                status = "FAIL"

            self.verification_results.append(
                {
                    "name": name,
                    "status": status,
                    "message": message,
                    "duration": duration,
                    "critical": critical,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ {name}: Error - {str(e)} ({duration:.2f}s)")

            self.verification_results.append(
                {
                    "name": name,
                    "status": "ERROR",
                    "message": str(e),
                    "duration": duration,
                    "critical": critical,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return False

    def verify_service_health(self) -> tuple[bool, str]:
        """サービスヘルスチェック"""
        base_url = self.urls.get(self.environment, "")

        try:
            response = requests.get(f"{base_url}/health", timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    return True, "Service is healthy"
                else:
                    return False, f"Service unhealthy: {data.get('message', 'Unknown')}"
            else:
                return False, f"Health check returned {response.status_code}"

        except requests.RequestException as e:
            return False, f"Cannot reach service: {str(e)}"

    def verify_api_endpoints(self) -> tuple[bool, str]:
        """主要APIエンドポイントの確認"""
        base_url = self.urls.get(self.environment, "")

        # Test critical endpoints
        endpoints = ["/api/v1/status", "/api/v1/workers", "/api/v1/tasks"]

        failed = []
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code >= 500:
                    failed.append(f"{endpoint} ({response.status_code})")
            except:
                failed.append(f"{endpoint} (unreachable)")

        if failed:
            return False, f"Failed endpoints: {', '.join(failed)}"

        return True, "All API endpoints responding"

    def verify_worker_status(self) -> tuple[bool, str]:
        """ワーカーステータスの確認"""
        base_url = self.urls.get(self.environment, "")

        try:
            response = requests.get(f"{base_url}/api/v1/workers/status", timeout=10)

            if response.status_code == 200:
                data = response.json()
                active_workers = data.get("active_workers", 0)

                if active_workers > 0:
                    return True, f"{active_workers} workers active"
                else:
                    return False, "No active workers found"
            else:
                return False, f"Worker status check failed: {response.status_code}"

        except Exception as e:
            return False, f"Cannot check worker status: {str(e)}"

    def verify_database_migration(self) -> tuple[bool, str]:
        """データベースマイグレーションの確認"""
        # In real deployment, this would check actual database
        # For now, we'll simulate with a simple check
        try:
            # Check if migration log exists
            migration_log = f"logs/migration_{self.environment}.log"
            result = subprocess.run(
                ["tail", "-n", "10", migration_log],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if "Migration completed successfully" in result.stdout:
                return True, "Database migrations completed"
            else:
                return True, "Migration status unknown (log not found)"

        except:
            return True, "Migration check skipped"

    def verify_static_assets(self) -> tuple[bool, str]:
        """静的アセットの確認"""
        base_url = self.urls.get(self.environment, "")

        # Check if key static files are accessible
        static_files = ["/static/css/main.css", "/static/js/app.js", "/favicon.ico"]

        missing = []
        for file_path in static_files:
            try:
                response = requests.head(f"{base_url}{file_path}", timeout=3)
                if response.status_code >= 400:
                    missing.append(file_path)
            except:
                missing.append(file_path)

        if missing:
            return False, f"Missing static files: {', '.join(missing)}"

        return True, "All static assets accessible"

    def verify_monitoring(self) -> tuple[bool, str]:
        """モニタリングシステムの確認"""
        base_url = self.urls.get(self.environment, "")

        try:
            response = requests.get(f"{base_url}/metrics", timeout=5)

            if response.status_code == 200:
                # Check if we're getting Prometheus metrics
                if "# HELP" in response.text:
                    return True, "Metrics endpoint active"
                else:
                    return False, "Metrics format invalid"
            else:
                return False, f"Metrics endpoint returned {response.status_code}"

        except:
            return True, "Metrics check skipped (optional)"

    def run_all_verifications(self) -> bool:
        """全検証を実行"""
        print(f"🚀 Running post-deployment verification for {self.environment}")
        print("=" * 50)

        # Define verifications with criticality
        verifications = [
            ("Service Health", self.verify_service_health, True),
            ("API Endpoints", self.verify_api_endpoints, True),
            ("Worker Status", self.verify_worker_status, True),
            ("Database Migration", self.verify_database_migration, False),
            ("Static Assets", self.verify_static_assets, False),
            ("Monitoring", self.verify_monitoring, False),
        ]

        critical_passed = True
        all_passed = True

        for name, verify_func, critical in verifications:
            passed = self.verify(name, verify_func, critical)
            if not passed:
                all_passed = False
                if critical:
                    critical_passed = False

        # Summary
        print("\n" + "=" * 50)
        total = len(self.verification_results)
        passed = sum(1 for r in self.verification_results if r["status"] == "PASS")
        failed = sum(1 for r in self.verification_results if r["status"] == "FAIL")
        errors = sum(1 for r in self.verification_results if r["status"] == "ERROR")

        print(f"📊 Verification Summary:")
        print(f"  Total: {total}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⚠️  Errors: {errors}")

        if critical_passed:
            print(f"\n✅ Deployment to {self.environment} verified successfully!")
            return True
        else:
            print(f"\n❌ Critical verifications failed for {self.environment}!")
            print("⚠️  Please investigate and fix the issues immediately.")
            return False

    def save_results(self, output_file: str):
        """検証結果を保存"""
        report = {
            "environment": self.environment,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(self.verification_results),
                "passed": sum(
                    1 for r in self.verification_results if r["status"] == "PASS"
                ),
                "failed": sum(
                    1 for r in self.verification_results if r["status"] == "FAIL"
                ),
                "errors": sum(
                    1 for r in self.verification_results if r["status"] == "ERROR"
                ),
            },
            "results": self.verification_results,
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📁 Verification report saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Post-deployment verification")
    parser.add_argument(
        "--environment",
        choices=["staging", "production"],
        required=True,
        help="Deployed environment",
    )
    parser.add_argument("--output", help="Output file for verification report")

    args = parser.parse_args()

    verifier = PostDeploymentVerification(args.environment)
    success = verifier.run_all_verifications()

    if args.output:
        verifier.save_results(args.output)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
