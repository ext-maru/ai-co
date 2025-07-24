#!/usr/bin/env python3
"""
Playwright GUI Test Framework for Elders Guild WebUI
RAG賢者推奨 - 最新のPlaywrightベースGUIテストフレームワーク
"""

import json
import logging
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests

try:
    from playwright.sync_api import (
        Browser,
        BrowserContext,
        Page,
        Playwright,
        expect,
        sync_playwright,
    )

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

    # フォールバック用のダミークラス
    class DummyPlaywright:
        """DummyPlaywrightクラス"""
        def __init__(self):
            """初期化メソッド"""
            pass

    Page = Browser = BrowserContext = Playwright = DummyPlaywright


class PlaywrightGUITestFramework:
    """Playwright ベースの高機能GUIテストフレームワーク"""

    def __init__(self, base_url: str = "http://localhost:5555", headless: bool = True):
        """初期化メソッド"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not installed. Run: pip install playwright && playwright install"
            )

        self.base_url = base_url
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.test_results = []
        self.logger = logging.getLogger(__name__)

        # 設定
        self.timeout = 30000  # 30秒
        self.screenshot_dir = Path("test_screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)

    def start(self):
        """Playwrightセッション開始"""
        self.playwright = sync_playwright().start()

        # ブラウザ起動（Chrome）
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )

        # ブラウザコンテキスト作成
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
        )

        # ページ作成
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout)

        self.logger.info("Playwright session started")

    def stop(self):
        """Playwrightセッション終了"""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

        self.logger.info("Playwright session stopped")

    def navigate_to(self, path: str = "/") -> bool:
        """指定パスに移動（自動待機付き）"""
        try:
            url = f"{self.base_url}{path}"
            self.page.goto(url, wait_until="networkidle")
            return True
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False

    def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> bool:
        """セレクターの要素を待機"""
        try:
            wait_timeout = timeout * 1000 if timeout else self.timeout
            self.page.wait_for_selector(selector, timeout=wait_timeout)
            return True
        except Exception as e:
            self.logger.error(f"Element not found: {selector}, {e}")
            return False

    def click(self, selector: str) -> bool:
        """要素をクリック（自動待機付き）"""
        try:
            self.page.click(selector)
            return True
        except Exception as e:
            self.logger.error(f"Click failed: {selector}, {e}")
            return False

    def fill(self, selector: str, text: str) -> bool:
        """入力フィールドにテキスト入力"""
        try:
            self.page.fill(selector, text)
            return True
        except Exception as e:
            self.logger.error(f"Fill failed: {selector}, {e}")
            return False

    def get_text(self, selector: str) -> str:
        """要素のテキストを取得"""
        try:
            return self.page.text_content(selector) or ""
        except Exception as e:
            self.logger.error(f"Get text failed: {selector}, {e}")
            return ""

    def is_visible(self, selector: str) -> bool:
        """要素の表示状態確認"""
        try:
            return self.page.is_visible(selector)
        except Exception as e:
            self.logger.error(f"Visibility check failed: {selector}, {e}")
            return False

    def screenshot(self, name: str) -> str:
        """スクリーンショット撮影"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{name}_{timestamp}.png"
        filepath = self.screenshot_dir / filename

        try:
            self.page.screenshot(path=str(filepath), full_page=True)
            self.logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return ""

    def expect_text(self, selector: str, expected_text: str) -> bool:
        """テキスト内容の検証"""
        try:
            locator = self.page.locator(selector)
            expect(locator).to_have_text(expected_text)
            return True
        except Exception as e:
            self.logger.error(f"Text expectation failed: {e}")
            return False

    def expect_visible(self, selector: str) -> bool:
        """要素の表示状態検証"""
        try:
            locator = self.page.locator(selector)
            expect(locator).to_be_visible()
            return True
        except Exception as e:
            self.logger.error(f"Visibility expectation failed: {e}")
            return False


class EldersGuildDashboardTest:
    """Elders Guild ダッシュボード専用テストクラス"""

    def __init__(self, framework: PlaywrightGUITestFramework):
        """初期化メソッド"""
        self.framework = framework
        self.logger = logging.getLogger(__name__)

    def test_dashboard_load(self) -> Dict[str, Any]:
        """ダッシュボード読み込みテスト"""
        result = {
            "test_name": "dashboard_load",
            "status": "failed",
            "message": "",
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # ダッシュボードに移動
            if not self.framework.navigate_to("/"):
                result["message"] = "Failed to navigate to dashboard"
                return result

            # タイトル確認（モダンな方法）
            if not self.framework.expect_text("title", "Elders Guild"):
                # フォールバック: ページ内のテキスト確認
                if not self.framework.wait_for_selector("h1:has-text('Elders Guild')"):
                    result["message"] = "Dashboard title not found"
                    return result

            # メインコンテンツ確認
            if not self.framework.expect_visible(
                ".dashboard-main, #dashboard-main, main"
            ):
                result["message"] = "Main dashboard content not found"
                return result

            result["status"] = "passed"
            result["message"] = "Dashboard loaded successfully"

        except Exception as e:
            result["message"] = f"Test failed: {str(e)}"
            self.framework.screenshot("dashboard_load_error")

        return result

    def test_system_status_display(self) -> Dict[str, Any]:
        """システムステータス表示テスト"""
        result = {
            "test_name": "system_status_display",
            "status": "failed",
            "message": "",
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # ステータス要素を探索（複数のセレクターを試行）
            status_selectors = [
                "#system-status",
                ".system-status",
                "[data-testid='system-status']",
                "div:has-text('Status')",
                "div:has-text('System')",
            ]

            status_found = False
            status_text = ""

            for selector in status_selectors:
                if self.framework.is_visible(selector):
                    status_text = self.framework.get_text(selector)
                    if status_text:
                        status_found = True
                        break

            if not status_found:
                result["message"] = "System status section not found"
                return result

            if not status_text.strip():
                result["message"] = "System status text is empty"
                return result

            result["status"] = "passed"
            result["message"] = f"System status displayed: {status_text[:50]}..."

        except Exception as e:
            result["message"] = f"Test failed: {str(e)}"
            self.framework.screenshot("system_status_error")

        return result

    def test_interactive_elements(self) -> Dict[str, Any]:
        """インタラクティブ要素テスト"""
        result = {
            "test_name": "interactive_elements",
            "status": "failed",
            "message": "",
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # ボタン・リンクの確認
            interactive_selectors = [
                "button",
                "a[href]",
                "input[type='button']",
                ".btn",
                "[role='button']",
            ]

            interactive_count = 0
            for selector in interactive_selectors:
                elements = self.framework.page.query_selector_all(selector)
                interactive_count += len(elements)

            if interactive_count == 0:
                result["message"] = "No interactive elements found"
                return result

            # 最初のボタンをテストクリック（安全な場合のみ）
            try:
                first_button = self.framework.page.query_selector(
                    "button:not([type='submit'])"
                )
                if first_button and first_button.is_visible():
                    first_button.click()
                    time.sleep(1)  # 反応を待つ
            except:
                pass  # クリックテストは失敗しても問題なし

            result["status"] = "passed"
            result["message"] = f"Found {interactive_count} interactive elements"

        except Exception as e:
            result["message"] = f"Test failed: {str(e)}"
            self.framework.screenshot("interactive_elements_error")

        return result


class PlaywrightTestRunner:
    """Playwright テストランナー"""

    def __init__(self, base_url: str = "http://localhost:5555", headless: bool = True):
        """初期化メソッド"""
        self.base_url = base_url
        self.headless = headless
        self.framework = None
        self.logger = logging.getLogger(__name__)

    def setup(self):
        """テストセットアップ"""
        self.framework = PlaywrightGUITestFramework(self.base_url, self.headless)
        self.framework.start()

    def teardown(self):
        """テスト終了処理"""
        if self.framework:
            self.framework.stop()

    def run_dashboard_tests(self) -> List[Dict[str, Any]]:
        """ダッシュボードテスト実行"""
        dashboard_test = EldersGuildDashboardTest(self.framework)

        tests = [
            dashboard_test.test_dashboard_load,
            dashboard_test.test_system_status_display,
            dashboard_test.test_interactive_elements,
        ]

        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
                self.logger.info(f"Test {result['test_name']}: {result['status']}")

                # 各テスト後にスクリーンショット（デバッグ用）
                if result["status"] == "passed":
                    self.framework.screenshot(f"{result['test_name']}_success")

            except Exception as e:
                error_result = {
                    "test_name": test.__name__,
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                results.append(error_result)
                self.logger.error(f"Test {test.__name__} failed: {e}")

        return results

    def run_all_tests(self) -> Dict[str, Any]:
        """全テスト実行"""
        start_time = datetime.now()

        try:
            self.setup()

            # サーバー起動確認
            if not self.check_server_running():
                return {
                    "status": "error",
                    "message": "Test server is not running",
                    "timestamp": start_time.isoformat(),
                }

            # テスト実行
            dashboard_results = self.run_dashboard_tests()

            # 結果集計
            total_tests = len(dashboard_results)
            passed_tests = sum(1 for r in dashboard_results if r["status"] == "passed")
            failed_tests = total_tests - passed_tests

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return {
                "status": "completed",
                "framework": "Playwright",
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "duration": duration,
                "results": dashboard_results,
                "timestamp": start_time.isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "framework": "Playwright",
                "message": str(e),
                "timestamp": start_time.isoformat(),
            }
        finally:
            self.teardown()

    def check_server_running(self) -> bool:
        """テストサーバーの起動確認"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False


class PlaywrightTestServerManager:
    """Playwright用テストサーバー管理"""

    def __init__(self, server_script: str = "web/dashboard_final.py"):
        """初期化メソッド"""
        self.server_script = server_script
        self.server_process = None
        self.logger = logging.getLogger(__name__)

    def start_server(self, port: int = 5555) -> bool:
        """テストサーバー起動"""
        try:
            import os
            import sys

            # サーバースクリプトの存在確認
            if not Path(self.server_script).exists():
                self.logger.error(f"Server script not found: {self.server_script}")
                return False

            # サーバー起動
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path.cwd())

            self.server_process = subprocess.Popen(
                [sys.executable, self.server_script],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # 起動待機
            time.sleep(5)  # Playwrightは少し長めに待機

            # 起動確認
            try:
                response = requests.get(f"http://localhost:{port}/", timeout=10)
                if response.status_code == 200:
                    self.logger.info(f"Test server started on port {port}")
                    return True
            except:
                pass

            self.logger.error("Failed to start test server")
            return False

        except Exception as e:
            self.logger.error(f"Server start failed: {e}")
            return False

    def stop_server(self):
        """テストサーバー停止"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait(timeout=10)
            self.server_process = None
            self.logger.info("Test server stopped")


def run_playwright_gui_tests(
    base_url: str = "http://localhost:5555", headless: bool = True
) -> Dict[str, Any]:
    """Playwright GUI テスト実行関数"""
    runner = PlaywrightTestRunner(base_url, headless)
    return runner.run_all_tests()


def install_playwright():
    """Playwright インストールヘルパー"""
    try:
        import subprocess
        import sys

        # playwright インストール
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])

        # ブラウザインストール
        subprocess.check_call(
            [sys.executable, "-m", "playwright", "install", "chromium"]
        )

        print("✅ Playwright installation completed!")
        return True

    except Exception as e:
        print(f"❌ Playwright installation failed: {e}")
        print("Manual installation: pip install playwright && playwright install")
        return False


if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Playwright利用可能性チェック
    if not PLAYWRIGHT_AVAILABLE:
        print("🚀 Installing Playwright...")
        if install_playwright():
            print("🔄 Please run the script again after installation.")
        exit(1)

    # GUI テスト実行
    print("🎭 Running Playwright GUI Tests...")
    results = run_playwright_gui_tests(headless=True)

    print(f"\n=== Playwright GUI Test Results ===")
    print(f"Framework: {results.get('framework', 'Playwright')}")
    print(f"Status: {results['status']}")

    if results["status"] == "completed":
        print(f"Total: {results['total_tests']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Duration: {results['duration']:0.2f}s")

        # 詳細結果
        for result in results["results"]:
            status_emoji = "✅" if result["status"] == "passed" else "❌"
            print(f"{status_emoji} {result['test_name']}: {result['message']}")
    else:
        print(f"Error: {results.get('message', 'Unknown error')}")

    print("\n🎭 Playwright GUI Tests completed!")
