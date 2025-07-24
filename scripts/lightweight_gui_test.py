#!/usr/bin/env python3
"""
Lightweight GUI Testing Alternative
API-based testing without browser dependencies for WSL2 environments
"""

import json
import logging
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import requests


class LightweightGUITester:
    """API-based GUI testing without browser dependencies"""

    def __init__(self, base_url="http://localhost:5555"):
        self.base_url = base_url
        self.test_results = []
        self.logger = logging.getLogger(__name__)

    def test_api_endpoints(self):
        """Test all API endpoints that the GUI depends on"""
        endpoints = [
            ("/", "GET", "Dashboard home page"),
            ("/api/status", "GET", "System status API"),
            ("/api/elders/assembly", "GET", "Elder assembly status"),
            ("/api/servants/status", "GET", "Servant status"),
            ("/api/coordination/active", "GET", "Active coordination"),
            ("/api/tasks/elder-approved", "GET", "Elder approved tasks"),
            ("/api/logs/recent", "GET", "Recent logs"),
            ("/api/health", "GET", "Health check"),
        ]

        results = []
        for endpoint, method, description in endpoints:
            result = self._test_endpoint(endpoint, method, description)
            results.append(result)

        return results

    def _test_endpoint(self, endpoint, method, description):
        """Test individual endpoint"""
        result = {
            "endpoint": endpoint,
            "method": method,
            "description": description,
            "status": "failed",
            "response_time": 0,
            "status_code": 0,
            "message": "",
            "timestamp": datetime.now().isoformat(),
        }

        try:
            start_time = time.time()

            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", timeout=10)
            else:
                response = requests.request(
                    method, f"{self.base_url}{endpoint}", timeout=10
                )

            end_time = time.time()

            result["response_time"] = round((end_time - start_time) * 1000, 2)  # ms
            result["status_code"] = response.status_code

            if response.status_code == 200:
                result["status"] = "passed"
                result["message"] = f"OK - Response time: {result['response_time']}ms"

                # Try to parse JSON if possible
                try:
                    data = response.json()
                    if isinstance(data, dict) and len(data) > 0:
                        result["message"] += f" - JSON data: {len(data)} fields"
                except:
                    result[
                        "message"
                    ] += f" - Content length: {len(response.text)} chars"

            elif response.status_code == 404:
                result["status"] = "skipped"
                result["message"] = "Endpoint not implemented"
            else:
                result["message"] = f"HTTP {response.status_code} - {response.reason}"

        except requests.exceptions.ConnectionError:
            result["message"] = "Connection failed - Server not running"
        except requests.exceptions.Timeout:
            result["message"] = "Request timeout"
        except Exception as e:
            result["message"] = f"Error: {str(e)}"

        return result

    def test_html_structure(self):
        """Test HTML structure without browser rendering"""
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code != 200:
                return {
                    "test": "html_structure",
                    "status": "failed",
                    "message": f"HTTP {response.status_code}",
                }

            html = response.text.lower()

            # Check for essential HTML elements
            checks = [
                (
                    "<!doctype html" in html or "<html" in html,
                    "HTML document structure",
                ),
                ("<title>" in html and "ai company" in html, "Page title"),
                ("<body>" in html, "Body element"),
                ("dashboard" in html, "Dashboard content"),
                ("<script>" in html or "src=" in html, "JavaScript presence"),
                ("css" in html or "style" in html, "CSS styling"),
            ]

            passed = sum(1 for check, _ in checks if check)
            total = len(checks)

            return {
                "test": "html_structure",
                "status": "passed" if passed >= total * 0.8 else "partial",
                "message": f"HTML structure check: {passed}/{total} elements found",
                "details": [desc for check, desc in checks if check],
            }

        except Exception as e:
            return {
                "test": "html_structure",
                "status": "failed",
                "message": f"Error: {str(e)}",
            }

    def test_static_resources(self):
        """Test static resource availability"""
        static_paths = [
            "/static/css/style.css",
            "/static/js/main.js",
            "/static/js/dashboard.js",
            "/static/images/logo.png",
            "/favicon.ico",
        ]

        results = []
        for path in static_paths:
            try:
                response = requests.head(f"{self.base_url}{path}", timeout=5)
                if response.status_code == 200:
                    results.append(f"✅ {path}")
                elif response.status_code == 404:
                    results.append(f"⏭️ {path} (not found)")
                else:
                    results.append(f"⚠️ {path} (HTTP {response.status_code})")
            except:
                results.append(f"❌ {path} (failed)")

        available = len([r for r in results if "✅" in r])

        return {
            "test": "static_resources",
            "status": "passed" if available > 0 else "failed",
            "message": f"Static resources: {available}/{len(static_paths)} available",
            "details": results,
        }

    def test_javascript_apis(self):
        """Test JavaScript API endpoints"""
        js_api_endpoints = [
            "/api/dashboard/widgets",
            "/api/realtime/status",
            "/api/notifications/latest",
            "/api/user/session",
        ]

        available_apis = []
        for endpoint in js_api_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code in [200, 401, 403]:  # API exists
                    available_apis.append(endpoint)
            except:
                pass

        return {
            "test": "javascript_apis",
            "status": "passed" if available_apis else "skipped",
            "message": f"JavaScript APIs: {len(available_apis)} endpoints available",
            "details": available_apis,
        }

    def run_all_tests(self):
        """Run comprehensive lightweight GUI tests"""
        self.logger.info("🧪 Starting Lightweight GUI Tests (No Browser Required)")

        all_results = []

        # Test API endpoints
        self.logger.info("Testing API endpoints...")
        api_results = self.test_api_endpoints()
        all_results.extend(api_results)

        # Test HTML structure
        self.logger.info("Testing HTML structure...")
        html_result = self.test_html_structure()
        all_results.append(html_result)

        # Test static resources
        self.logger.info("Testing static resources...")
        static_result = self.test_static_resources()
        all_results.append(static_result)

        # Test JavaScript APIs
        self.logger.info("Testing JavaScript APIs...")
        js_result = self.test_javascript_apis()
        all_results.append(js_result)

        # Generate summary
        total_tests = len(all_results)
        passed_tests = len([r for r in all_results if r.get("status") == "passed"])
        failed_tests = len([r for r in all_results if r.get("status") == "failed"])
        skipped_tests = len([r for r in all_results if r.get("status") == "skipped"])

        summary = {
            "framework": "Lightweight API Testing",
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "success_rate": round((passed_tests / total_tests) * 100, 1)
            if total_tests > 0
            else 0,
            "results": all_results,
            "timestamp": datetime.now().isoformat(),
        }

        return summary


class ServerManager:
    """Manage test server for lightweight testing"""

    def __init__(self, server_script="web/dashboard_final.py"):
        self.server_script = server_script
        self.process = None

    def start(self):
        """Start the test server"""
        if not Path(self.server_script).exists():
            return False

        try:
            self.process = subprocess.Popen(
                ["python3", self.server_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(3)  # Wait for server to start
            return True
        except:
            return False

    def stop(self):
        """Stop the test server"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)


def main():
    """Main test runner"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Start server
    server = ServerManager()
    server_started = server.start()

    if not server_started:
        print("⚠️ Could not start test server automatically")
        print("Please start the dashboard manually: python3 web/dashboard_final.py")
        print("Then run: python3 lightweight_gui_test.py")
        return 1

    try:
        # Run tests
        tester = LightweightGUITester()
        results = tester.run_all_tests()

        # Display results
        print("\n" + "=" * 60)
        print("🧪 LIGHTWEIGHT GUI TEST RESULTS")
        print("=" * 60)
        print(f"Framework: {results['framework']}")
        print(f"Total Tests: {results['total_tests']}")
        print(f"✅ Passed: {results['passed']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"⏭️ Skipped: {results['skipped']}")
        print(f"📊 Success Rate: {results['success_rate']}%")

        print(f"\n📋 Detailed Results:")
        for result in results["results"]:
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "skipped": "⏭️",
                "partial": "⚠️",
            }.get(result.get("status"), "❓")

            if "endpoint" in result:
                print(f"{status_emoji} {result['endpoint']} - {result['message']}")
            else:
                print(f"{status_emoji} {result['test']} - {result['message']}")

        print(f"\n💡 Recommendations:")
        if results["success_rate"] >= 80:
            print("✅ GUI backend is working well - ready for browser testing")
        elif results["success_rate"] >= 60:
            print("⚠️ Some issues detected - check failed endpoints")
        else:
            print("❌ Significant issues - fix backend before GUI testing")

        print("🔧 To enable full browser testing:")
        print(
            "   1.0 Install system dependencies: sudo apt install chromium-browser libnss3"
        )
        print("   2.0 Use Docker: docker run --rm selenium/standalone-chrome")
        print("   3.0 Set up X11 forwarding for WSL2")

        return 0 if results["success_rate"] >= 60 else 1

    finally:
        server.stop()


if __name__ == "__main__":
    exit(main())
