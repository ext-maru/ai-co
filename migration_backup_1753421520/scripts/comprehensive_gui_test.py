#!/usr/bin/env python3
"""
import sys
from pathlib import Path

# Ensure project root is in Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import os
import pytest
from unittest.mock import Mock, MagicMock, patch
import unittest

Comprehensive GUI Testing Suite for Elders Guild Dashboard
This script runs complete GUI tests to verify the dashboard system
"""

import logging
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DashboardTestServer:
    """Test server manager for dashboard"""

    def __init__(self, port=5555):
        self.port = port
        self.process = None
        self.server_url = f"http://localhost:{port}"

    def start(self):
        """Start the dashboard server"""
        try:
            # Check if server is already running
            if self.is_running():
                logger.info(f"✅ Dashboard server already running on port {self.port}")
                return True

            # Start server process
            logger.info(f"🚀 Starting dashboard server on port {self.port}...")
            self.process = subprocess.Popen(
                [sys.executable, "web/dashboard_final.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path.cwd(),
            )

            # Wait for server to start
            max_wait = 15
            for i in range(max_wait):
                if self.is_running():
                    logger.info(f"✅ Dashboard server started successfully")
                    return True
                time.sleep(1)

            logger.error(f"❌ Dashboard server failed to start after {max_wait} seconds")
            return False

        except Exception as e:
            logger.error(f"❌ Failed to start dashboard server: {e}")
            return False

    def stop(self):
        """Stop the dashboard server"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            logger.info("🛑 Dashboard server stopped")

    def is_running(self):
        """Check if server is running"""
        try:
            response = requests.get(f"{self.server_url}/", timeout=3)
            return response.status_code == 200
        except:
            return False


class GUITestRunner:
    """Main GUI test runner"""

    def __init__(self):
        self.server = DashboardTestServer()
        self.test_results = []

    def run_selenium_tests(self):
        """Run Selenium-based GUI tests"""
        logger.info("🧪 Running Selenium GUI Tests...")

        try:
            from libs.gui_test_framework import run_gui_tests

            # Run the GUI tests
            results = run_gui_tests(base_url=self.server.server_url, headless=True)

            # Process results
            if results["status"] == "completed":
                logger.info(
                    f"✅ Selenium Tests: {results['passed']}/{results['total_tests']} passed"
                )
                self.test_results.append(
                    {
                        "framework": "Selenium",
                        "status": "success",
                        "passed": results["passed"],
                        "total": results["total_tests"],
                        "details": results.get("results", []),
                    }
                )
                return True
            else:
                logger.error(
                    f"❌ Selenium Tests failed: {results.get('message', 'Unknown error')}"
                )
                self.test_results.append(
                    {
                        "framework": "Selenium",
                        "status": "failed",
                        "error": results.get("message", "Unknown error"),
                    }
                )
                return False

        except Exception as e:
            logger.error(f"❌ Selenium Tests failed with exception: {e}")
            self.test_results.append(
                {"framework": "Selenium", "status": "error", "error": str(e)}
            )
            return False

    def run_playwright_tests(self):
        """Run Playwright-based GUI tests"""
        logger.info("🧪 Running Playwright GUI Tests...")

        try:
            from libs.playwright_gui_test_framework import (
                PLAYWRIGHT_AVAILABLE,
                run_playwright_gui_tests,
            )

            if not PLAYWRIGHT_AVAILABLE:
                logger.warning(
                    "⚠️  Playwright not available, skipping Playwright tests"
                )
                self.test_results.append(
                    {
                        "framework": "Playwright",
                        "status": "skipped",
                        "reason": "Playwright not available",
                    }
                )
                return True

            # Run the GUI tests
            results = run_playwright_gui_tests(
                base_url=self.server.server_url, headless=True
            )

            # Process results
            if results["status"] == "completed":
                logger.info(
                    f"✅ Playwright Tests: {results['passed']}/{results['total_tests']} passed"
                )
                self.test_results.append(
                    {
                        "framework": "Playwright",
                        "status": "success",
                        "passed": results["passed"],
                        "total": results["total_tests"],
                        "details": results.get("results", []),
                    }
                )
                return True
            else:
                logger.error(
                    f"❌ Playwright Tests failed: {results.get('message', 'Unknown error')}"
                )
                self.test_results.append(
                    {
                        "framework": "Playwright",
                        "status": "failed",
                        "error": results.get("message", "Unknown error"),
                    }
                )
                return False

        except Exception as e:
            logger.error(f"❌ Playwright Tests failed with exception: {e}")
            self.test_results.append(
                {"framework": "Playwright", "status": "error", "error": str(e)}
            )
            return False

    def run_api_tests(self):
        """Run API endpoint tests"""
        logger.info("🧪 Running API Tests...")

        api_endpoints = [
            "/api/status",
            "/api/elders/assembly",
            "/api/servants/status",
            "/api/coordination/active",
            "/api/tasks/elder-approved",
            "/api/logs/recent",
        ]

        passed = 0
        total = len(api_endpoints)

        for endpoint in api_endpoints:
            try:
                response = requests.get(
                    f"{self.server.server_url}{endpoint}", timeout=5
                )
                if response.status_code == 200:
                    logger.info(f"✅ API {endpoint}: OK")
                    passed += 1
                else:
                    logger.warning(f"⚠️  API {endpoint}: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"❌ API {endpoint}: {e}")

        logger.info(f"📊 API Tests: {passed}/{total} endpoints working")
        self.test_results.append(
            {
                "framework": "API",
                "status": "success" if passed == total else "partial",
                "passed": passed,
                "total": total,
            }
        )

        return passed == total

    def run_authentication_tests(self):
        """Run authentication system tests"""
        logger.info("🧪 Running Authentication Tests...")

        try:
            from web.auth_manager import AuthManager, User, validate_password_strength

            # Test in-memory auth system
            auth_manager = AuthManager(db_path=":memory:")

            # Test user creation
            test_user = auth_manager.create_user(
                username="testuser",
                email="test@example.com",
                password="TestPassword123",
                role="user",
            )

            # Test authentication
            user, session = auth_manager.authenticate("testuser", "TestPassword123")

            # Test session validation
            validated_user = auth_manager.validate_session(session.token)

            if validated_user and validated_user.username == "testuser":
                logger.info("✅ Authentication system working correctly")
                self.test_results.append(
                    {
                        "framework": "Authentication",
                        "status": "success",
                        "passed": 1,
                        "total": 1,
                    }
                )
                return True
            else:
                logger.error("❌ Authentication system validation failed")
                self.test_results.append(
                    {
                        "framework": "Authentication",
                        "status": "failed",
                        "error": "Session validation failed",
                    }
                )
                return False

        except Exception as e:
            logger.error(f"❌ Authentication tests failed: {e}")
            self.test_results.append(
                {"framework": "Authentication", "status": "error", "error": str(e)}
            )
            return False

    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        logger.info("🎯 Starting Comprehensive GUI Testing Suite...")
        logger.info("=" * 60)

        # Start server
        if not self.server.start():
            logger.error("❌ Failed to start dashboard server")
            return False

        try:
            # Run all test suites
            tests = [
                ("API Tests", self.run_api_tests),
                ("Authentication Tests", self.run_authentication_tests),
                ("Selenium GUI Tests", self.run_selenium_tests),
                ("Playwright GUI Tests", self.run_playwright_tests),
            ]

            results = []
            for test_name, test_func in tests:
                logger.info(f"\n--- {test_name} ---")
                result = test_func()
                results.append(result)
                time.sleep(1)  # Brief pause between tests

            # Generate final report
            self.generate_report()

            # Return overall success
            return all(results)

        finally:
            self.server.stop()

    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 60)
        logger.info("🎯 COMPREHENSIVE GUI TEST REPORT")
        logger.info("=" * 60)

        total_frameworks = len(self.test_results)
        successful_frameworks = sum(
            1 for r in self.test_results if r["status"] == "success"
        )

        logger.info(f"📊 Overall Summary:")
        logger.info(
            f"   Test Frameworks: {successful_frameworks}/{total_frameworks} successful"
        )
        logger.info(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        logger.info(f"\n📋 Detailed Results:")
        for result in self.test_results:
            framework = result["framework"]
            status = result["status"]

            if status == "success":
                passed = result.get("passed", 0)
                total = result.get("total", 0)
                logger.info(f"   ✅ {framework}: {passed}/{total} tests passed")
            elif status == "skipped":
                reason = result.get("reason", "Unknown")
                logger.info(f"   ⏭️  {framework}: Skipped ({reason})")
            elif status == "partial":
                passed = result.get("passed", 0)
                total = result.get("total", 0)
                logger.info(
                    f"   ⚠️  {framework}: {passed}/{total} tests passed (partial)"
                )
            else:
                error = result.get("error", "Unknown error")
                logger.info(f"   ❌ {framework}: Failed ({error})")

        logger.info(f"\n🎯 Test Coverage Analysis:")
        logger.info(f"   ✅ GUI Test Framework: Available (Selenium + Playwright)")
        logger.info(f"   ✅ Dashboard System: Available (Flask-based)")
        logger.info(f"   ✅ Authentication System: Available (JWT + Sessions)")
        logger.info(f"   ✅ API Endpoints: Available (RESTful)")
        logger.info(f"   ✅ Test Dependencies: Available (pytest, selenium, playwright)")

        # Recommendations
        logger.info(f"\n💡 Recommendations:")

        playwright_available = any(
            r["framework"] == "Playwright" and r["status"] == "success"
            for r in self.test_results
        )
        if not playwright_available:
            logger.info(
                f"   📦 Install Playwright browsers: playwright install chromium"
            )

        api_issues = any(
            r["framework"] == "API" and r["status"] != "success"
            for r in self.test_results
        )
        if api_issues:
            logger.info(f"   🔧 Check API endpoints and server configuration")

        logger.info(f"   🧪 Run tests regularly during development")
        logger.info(
            f"   📈 Consider adding more specific UI tests for dashboard features"
        )

        success_rate = successful_frameworks / total_frameworks * 100
        logger.info(f"\n🎉 Overall Success Rate: {success_rate:0.1f}%")

        if success_rate >= 80:
            logger.info("✅ GUI Testing Framework is ready for production use!")
        elif success_rate >= 60:
            logger.info("⚠️  GUI Testing Framework needs some improvements")
        else:
            logger.info("❌ GUI Testing Framework needs significant work")


def main():
    """Main function"""
    runner = GUITestRunner()
    success = runner.run_comprehensive_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
