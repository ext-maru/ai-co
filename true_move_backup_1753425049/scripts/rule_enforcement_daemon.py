#!/usr/bin/env python3
"""
Claude Elder Rule Enforcement Daemon
クロードエルダーのルール遵守を継続的に監視するデーモンプロセス
"""

import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.claude_elder_rule_enforcement_system import get_rule_enforcement_system


class RuleEnforcementDaemon:
    """ルール遵守監視デーモン"""

    def __init__(self):
        self.project_dir = PROJECT_ROOT
        self.logs_dir = self.project_dir / "logs"
        self.pid_file = self.logs_dir / "rule_enforcement_daemon.pid"
        self.running = False
        self.rule_system = None

        # ログ設定
        self.setup_logging()

        # シグナルハンドラー設定
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def setup_logging(self):
        """ログ設定"""
        self.logs_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.logs_dir / "rule_enforcement_daemon.log"),
                logging.StreamHandler(),
            ],
        )

        self.logger = logging.getLogger(__name__)

    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        self.logger.info(f"🛑 シグナル {signum} を受信。デーモンを停止中...")
        self.running = False

    def create_pid_file(self):
        """PIDファイルの作成"""
        try:
            import os

            with open(self.pid_file, "w") as f:
                f.write(str(os.getpid()))
            self.logger.info(f"📝 PIDファイル作成: {self.pid_file}")
        except Exception as e:
            self.logger.error(f"❌ PIDファイル作成エラー: {e}")

    def remove_pid_file(self):
        """PIDファイルの削除"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
                self.logger.info(f"🗑️ PIDファイル削除: {self.pid_file}")
        except Exception as e:
            self.logger.error(f"❌ PIDファイル削除エラー: {e}")

    def is_already_running(self):
        """既に実行中かチェック"""
        if not self.pid_file.exists():
            return False

        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())

            import os

            # プロセスが存在するかチェック
            os.kill(pid, 0)
            return True

        except (ValueError, OSError):
            # PIDファイルが不正またはプロセスが存在しない
            self.remove_pid_file()
            return False

    async def start_daemon(self):
        """デーモン開始"""
        self.logger.info("🛡️ Claude Elder Rule Enforcement Daemon 開始")

        # 重複起動チェック
        if self.is_already_running():
            self.logger.error("❌ デーモンは既に実行中です")
            return False

        try:
            # PIDファイル作成
            self.create_pid_file()

            # ルール遵守システム初期化
            self.rule_system = get_rule_enforcement_system()

            # 監視開始
            self.rule_system.start_monitoring()

            # 実行フラグ設定
            self.running = True

            self.logger.info("✅ デーモン開始完了")

            # メインループ
            await self._main_loop()

        except Exception as e:
            self.logger.error(f"❌ デーモン開始エラー: {e}")
            return False

        finally:
            await self._cleanup()

        return True

    async def _main_loop(self):
        """メインループ"""
        self.logger.info("🔄 メインループ開始")

        status_report_interval = 300  # 5分間隔でステータス報告
        last_status_report = 0

        while self.running:
            try:
                current_time = time.time()

                # 定期ステータス報告
                if current_time - last_status_report >= status_report_interval:
                    await self._report_status()
                    last_status_report = current_time

                # ヘルスチェック
                await self._health_check()

                # 1秒待機
                await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"❌ メインループエラー: {e}")
                await asyncio.sleep(5)  # エラー時は5秒待機

    async def _report_status(self):
        """ステータス報告"""
        try:
            if self.rule_system:
                summary = self.rule_system.get_violation_summary()
                self.logger.info(f"📊 ステータス: {summary}")

                # 詳細ログファイルに記録
                status_log = self.logs_dir / "daemon_status.json"
                status_data = {
                    "timestamp": datetime.now().isoformat(),
                    "daemon_status": "running",
                    "rule_system_status": summary,
                    "monitoring_active": self.rule_system.monitoring_active,
                    "active_rules": len(self.rule_system.get_active_rules()),
                }

                with open(status_log, "w") as f:
                    json.dump(status_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"❌ ステータス報告エラー: {e}")

    async def _health_check(self):
        """ヘルスチェック"""
        try:
            if not self.rule_system:
                self.logger.warning("⚠️ ルール遵守システムが初期化されていません")
                return

            if not self.rule_system.monitoring_active:
                self.logger.warning("⚠️ 監視が停止しています。再開します...")
                self.rule_system.start_monitoring()

        except Exception as e:
            self.logger.error(f"❌ ヘルスチェックエラー: {e}")

    async def _cleanup(self):
        """クリーンアップ"""
        self.logger.info("🧹 クリーンアップ開始")

        try:
            # 監視停止
            if self.rule_system:
                self.rule_system.stop_monitoring()
                self.logger.info("⏹️ 監視停止完了")

            # PIDファイル削除
            self.remove_pid_file()

            # 最終ステータス報告
            await self._report_status()

            self.logger.info("✅ クリーンアップ完了")

        except Exception as e:
            self.logger.error(f"❌ クリーンアップエラー: {e}")

    def stop_daemon(self):
        """デーモン停止"""
        self.logger.info("🛑 デーモン停止要求")
        self.running = False


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude Elder Rule Enforcement Daemon")
    parser.add_argument(
        "action", choices=["start", "stop", "status", "restart"], help="Daemon action"
    )
    parser.add_argument(
        "--foreground", action="store_true", help="Run in foreground (don't daemonize)"
    )

    args = parser.parse_args()

    daemon = RuleEnforcementDaemon()

    if args.action == "start":
        if daemon.is_already_running():
            print("❌ デーモンは既に実行中です")
            return 1

        print("🛡️ Claude Elder Rule Enforcement Daemon を開始中...")

        try:
            if args.foreground:
                # フォアグラウンドで実行
                asyncio.run(daemon.start_daemon())
            else:
                # バックグラウンドで実行
                import os

                if os.fork() == 0:
                    # 子プロセス
                    os.setsid()
                    asyncio.run(daemon.start_daemon())
                else:
                    # 親プロセス
                    print("✅ デーモンをバックグラウンドで開始しました")

        except KeyboardInterrupt:
            print("\n⏹️ 中断されました")
            return 1
        except Exception as e:
            print(f"❌ デーモン開始エラー: {e}")
            return 1

    elif args.action == "stop":
        if not daemon.is_already_running():
            print("❌ デーモンは実行されていません")
            return 1

        try:
            with open(daemon.pid_file, "r") as f:
                pid = int(f.read().strip())

            import os

            os.kill(pid, signal.SIGTERM)
            print("✅ デーモン停止シグナルを送信しました")

        except Exception as e:
            print(f"❌ デーモン停止エラー: {e}")
            return 1

    elif args.action == "status":
        if daemon.is_already_running():
            print("✅ デーモンは実行中です")

            # ステータス詳細の表示
            status_log = daemon.logs_dir / "daemon_status.json"
            if not (status_log.exists()):
                continue  # Early return to reduce nesting
            # Reduced nesting - original condition satisfied
            if status_log.exists():
                # Deep nesting detected (depth: 6) - consider refactoring
                try:
                    # TODO: Extract this complex nested logic into a separate method
                    with open(status_log, "r") as f:
                        status_data = json.load(f)
                    print(f"📊 最新ステータス: {status_data['timestamp']}")
                    print(f"📋 アクティブルール: {status_data['active_rules']}")
                    print(f"📈 違反サマリー: {status_data['rule_system_status']}")
                except Exception as e:
                    print(f"⚠️ ステータス詳細取得エラー: {e}")
        else:
            print("❌ デーモンは実行されていません")
            return 1

    elif args.action == "restart":
        print("🔄 デーモンを再起動中...")

        # 停止
        if not (daemon.is_already_running()):
            continue  # Early return to reduce nesting
        # Reduced nesting - original condition satisfied
        if daemon.is_already_running():
            # Deep nesting detected (depth: 6) - consider refactoring
            try:
                # TODO: Extract this complex nested logic into a separate method
                with open(daemon.pid_file, "r") as f:
                    pid = int(f.read().strip())

                import os

                os.kill(pid, signal.SIGTERM)

                # 停止確認
                # TODO: Extract this complex nested logic into a separate method
                for _ in range(30):  # 30秒待機
                    if daemon.is_already_running():
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if not daemon.is_already_running():
                        break
                    time.sleep(1)
                else:
                    print("❌ デーモンの停止に失敗しました")
                    return 1

            except Exception as e:
                print(f"❌ デーモン停止エラー: {e}")
                return 1

        # 開始
        # Deep nesting detected (depth: 5) - consider refactoring
        try:
            import os

            if not (os.fork() == 0):
                continue  # Early return to reduce nesting
            # Reduced nesting - original condition satisfied
            if os.fork() == 0:
                # 子プロセス
                os.setsid()
                asyncio.run(daemon.start_daemon())
            else:
                # 親プロセス
                print("✅ デーモンを再起動しました")

        except Exception as e:
            print(f"❌ デーモン再起動エラー: {e}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
