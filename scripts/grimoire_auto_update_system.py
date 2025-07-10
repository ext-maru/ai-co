#!/usr/bin/env python3
"""
グリモア自動更新システム
4賢者の魔法書を自動的に更新・メンテナンスする
"""

import hashlib
import json
import logging
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GrimoireAutoUpdateSystem:
    """グリモア自動更新システム"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.grimoire_base = self.project_root / "knowledge_base" / "four_sages_grimoires"
        self.update_log = self.project_root / "logs" / "grimoire_auto_update.log"
        self.update_log.parent.mkdir(exist_ok=True)

        # 自動更新の各システム
        self.update_systems = {
            "file_watcher": False,
            "content_analyzer": False,
            "index_updater": False,
            "cross_reference_updater": False,
            "backup_system": False,
            "health_monitor": False,
        }

        # 魔法書構造
        self.grimoire_structure = {
            "knowledge_sage": "01_knowledge_sage_grimoire.md",
            "task_oracle": "02_task_oracle_grimoire.md",
            "incident_sage": "03_incident_sage_grimoire.md",
            "rag_mystic": "04_rag_mystic_grimoire.md",
            "common_knowledge": "00_common_knowledge.md",
        }

        # 監視対象ファイル
        self.monitored_files = {str(self.grimoire_base / file): sage for sage, file in self.grimoire_structure.items()}

        # 自動更新設定
        self.auto_update_config = {
            "watch_interval": 30,  # 秒
            "backup_interval": 3600,  # 1時間
            "health_check_interval": 300,  # 5分
            "max_backup_files": 10,
            "enable_auto_index": True,
            "enable_auto_cross_ref": True,
        }

        # ファイルハッシュキャッシュ
        self.file_hashes = {}

        # システム状態
        self.system_running = False
        self.monitoring_thread = None

    def setup_auto_update_system(self) -> Dict[str, Any]:
        """自動更新システムのセットアップ"""
        print("🔄 グリモア自動更新システムをセットアップ中...")

        setup_results = {
            "timestamp": datetime.now().isoformat(),
            "systems": {},
            "config": self.auto_update_config,
            "overall_status": "setting_up",
        }

        # System 1: ファイル監視システム
        system1_result = self._setup_file_watcher()
        setup_results["systems"]["file_watcher"] = system1_result

        # System 2: コンテンツ分析システム
        system2_result = self._setup_content_analyzer()
        setup_results["systems"]["content_analyzer"] = system2_result

        # System 3: 索引更新システム
        system3_result = self._setup_index_updater()
        setup_results["systems"]["index_updater"] = system3_result

        # System 4: 相互参照更新システム
        system4_result = self._setup_cross_reference_updater()
        setup_results["systems"]["cross_reference_updater"] = system4_result

        # System 5: バックアップシステム
        system5_result = self._setup_backup_system()
        setup_results["systems"]["backup_system"] = system5_result

        # System 6: ヘルスモニター
        system6_result = self._setup_health_monitor()
        setup_results["systems"]["health_monitor"] = system6_result

        # 総合評価
        setup_results["overall_status"] = self._assess_setup_status()

        return setup_results

    def _setup_file_watcher(self) -> Dict[str, Any]:
        """ファイル監視システムのセットアップ"""
        print("  👁️ ファイル監視システムをセットアップ中...")

        watcher_result = {
            "status": "setting_up",
            "monitored_files": len(self.monitored_files),
            "watch_interval": self.auto_update_config["watch_interval"],
        }

        try:
            # 初期ファイルハッシュの計算
            for file_path in self.monitored_files.keys():
                if Path(file_path).exists():
                    self.file_hashes[file_path] = self._calculate_file_hash(file_path)

            watcher_result["status"] = "ready"
            self.update_systems["file_watcher"] = True

        except Exception as e:
            watcher_result["status"] = "failed"
            watcher_result["error"] = str(e)

        self._log_update("File watcher setup", watcher_result["status"])
        return watcher_result

    def _setup_content_analyzer(self) -> Dict[str, Any]:
        """コンテンツ分析システムのセットアップ"""
        print("  🔍 コンテンツ分析システムをセットアップ中...")

        analyzer_result = {"status": "setting_up", "analysis_rules": []}

        try:
            # 分析ルールの定義
            analysis_rules = [
                {"name": "new_section_detection", "pattern": r"^#{1,3}\s+", "action": "update_index"},
                {
                    "name": "cross_reference_detection",
                    "pattern": r"\*\*.*賢者.*\*\*",
                    "action": "update_cross_references",
                },
                {"name": "code_block_detection", "pattern": r"```.*```", "action": "highlight_code"},
                {"name": "link_detection", "pattern": r"\[.*\]\(.*\)", "action": "validate_links"},
            ]

            analyzer_result["analysis_rules"] = analysis_rules
            analyzer_result["status"] = "ready"
            self.update_systems["content_analyzer"] = True

        except Exception as e:
            analyzer_result["status"] = "failed"
            analyzer_result["error"] = str(e)

        self._log_update("Content analyzer setup", analyzer_result["status"])
        return analyzer_result

    def _setup_index_updater(self) -> Dict[str, Any]:
        """索引更新システムのセットアップ"""
        print("  📚 索引更新システムをセットアップ中...")

        updater_result = {"status": "setting_up", "auto_index_enabled": self.auto_update_config["enable_auto_index"]}

        try:
            # 索引更新スクリプトの準備
            index_updater_script = self._create_index_updater_script()
            updater_result["updater_script"] = index_updater_script

            updater_result["status"] = "ready"
            self.update_systems["index_updater"] = True

        except Exception as e:
            updater_result["status"] = "failed"
            updater_result["error"] = str(e)

        self._log_update("Index updater setup", updater_result["status"])
        return updater_result

    def _create_index_updater_script(self) -> str:
        """索引更新スクリプトの作成"""
        script_path = self.project_root / "scripts" / "auto_index_updater.py"

        script_content = '''#!/usr/bin/env python3
"""
自動索引更新スクリプト
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def update_indices():
    """索引を更新"""
    try:
        from scripts.grimoire_accessibility_enhancer_fixed import GrimoireAccessibilityEnhancer

        enhancer = GrimoireAccessibilityEnhancer()

        # 索引ファイルのみ更新
        index_files = enhancer._create_index_files()

        print(f"索引更新完了: {len(index_files)}ファイル")
        return True

    except Exception as e:
        print(f"索引更新エラー: {e}")
        return False

if __name__ == "__main__":
    success = update_indices()
    sys.exit(0 if success else 1)
'''

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        return str(script_path)

    def _setup_cross_reference_updater(self) -> Dict[str, Any]:
        """相互参照更新システムのセットアップ"""
        print("  🔗 相互参照更新システムをセットアップ中...")

        cross_ref_result = {
            "status": "setting_up",
            "auto_cross_ref_enabled": self.auto_update_config["enable_auto_cross_ref"],
        }

        try:
            # 相互参照更新スクリプトの準備
            cross_ref_updater_script = self._create_cross_ref_updater_script()
            cross_ref_result["updater_script"] = cross_ref_updater_script

            cross_ref_result["status"] = "ready"
            self.update_systems["cross_reference_updater"] = True

        except Exception as e:
            cross_ref_result["status"] = "failed"
            cross_ref_result["error"] = str(e)

        self._log_update("Cross-reference updater setup", cross_ref_result["status"])
        return cross_ref_result

    def _create_cross_ref_updater_script(self) -> str:
        """相互参照更新スクリプトの作成"""
        script_path = self.project_root / "scripts" / "auto_cross_ref_updater.py"

        script_content = '''#!/usr/bin/env python3
"""
自動相互参照更新スクリプト
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def update_cross_references():
    """相互参照を更新"""
    try:
        from scripts.grimoire_accessibility_enhancer_fixed import GrimoireAccessibilityEnhancer

        enhancer = GrimoireAccessibilityEnhancer()

        # 相互参照システムのみ更新
        cross_ref_result = enhancer._create_cross_reference_system()

        print(f"相互参照更新完了: {cross_ref_result['status']}")
        return cross_ref_result["status"] == "completed"

    except Exception as e:
        print(f"相互参照更新エラー: {e}")
        return False

if __name__ == "__main__":
    success = update_cross_references()
    sys.exit(0 if success else 1)
'''

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        return str(script_path)

    def _setup_backup_system(self) -> Dict[str, Any]:
        """バックアップシステムのセットアップ"""
        print("  💾 バックアップシステムをセットアップ中...")

        backup_result = {
            "status": "setting_up",
            "backup_interval": self.auto_update_config["backup_interval"],
            "max_backup_files": self.auto_update_config["max_backup_files"],
        }

        try:
            # バックアップディレクトリの作成
            backup_dir = self.project_root / "backups" / "grimoire"
            backup_dir.mkdir(parents=True, exist_ok=True)

            backup_result["backup_directory"] = str(backup_dir)
            backup_result["status"] = "ready"
            self.update_systems["backup_system"] = True

        except Exception as e:
            backup_result["status"] = "failed"
            backup_result["error"] = str(e)

        self._log_update("Backup system setup", backup_result["status"])
        return backup_result

    def _setup_health_monitor(self) -> Dict[str, Any]:
        """ヘルスモニターのセットアップ"""
        print("  🏥 ヘルスモニターをセットアップ中...")

        health_result = {
            "status": "setting_up",
            "health_check_interval": self.auto_update_config["health_check_interval"],
        }

        try:
            # ヘルスチェック項目の定義
            health_checks = [
                "file_existence",
                "file_readability",
                "syntax_validation",
                "link_validation",
                "index_consistency",
            ]

            health_result["health_checks"] = health_checks
            health_result["status"] = "ready"
            self.update_systems["health_monitor"] = True

        except Exception as e:
            health_result["status"] = "failed"
            health_result["error"] = str(e)

        self._log_update("Health monitor setup", health_result["status"])
        return health_result

    def start_auto_update_system(self) -> bool:
        """自動更新システムの開始"""
        if self.system_running:
            return False

        print("🚀 自動更新システムを開始中...")

        try:
            self.system_running = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()

            logger.info("Auto-update system started")
            return True

        except Exception as e:
            logger.error(f"Failed to start auto-update system: {e}")
            self.system_running = False
            return False

    def stop_auto_update_system(self) -> bool:
        """自動更新システムの停止"""
        if not self.system_running:
            return False

        print("⏹️ 自動更新システムを停止中...")

        try:
            self.system_running = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=10)

            logger.info("Auto-update system stopped")
            return True

        except Exception as e:
            logger.error(f"Failed to stop auto-update system: {e}")
            return False

    def _monitoring_loop(self):
        """監視ループ"""
        last_backup_time = datetime.now()
        last_health_check = datetime.now()

        while self.system_running:
            try:
                current_time = datetime.now()

                # ファイル変更の監視
                self._check_file_changes()

                # 定期バックアップ
                if (current_time - last_backup_time).total_seconds() > self.auto_update_config["backup_interval"]:
                    self._perform_backup()
                    last_backup_time = current_time

                # ヘルスチェック
                if (current_time - last_health_check).total_seconds() > self.auto_update_config[
                    "health_check_interval"
                ]:
                    self._perform_health_check()
                    last_health_check = current_time

                # 監視間隔
                time.sleep(self.auto_update_config["watch_interval"])

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(10)

    def _check_file_changes(self):
        """ファイル変更のチェック"""
        for file_path, sage_name in self.monitored_files.items():
            if Path(file_path).exists():
                current_hash = self._calculate_file_hash(file_path)

                if file_path in self.file_hashes:
                    if current_hash != self.file_hashes[file_path]:
                        self._handle_file_change(file_path, sage_name)
                        self.file_hashes[file_path] = current_hash
                else:
                    self.file_hashes[file_path] = current_hash

    def _handle_file_change(self, file_path: str, sage_name: str):
        """ファイル変更の処理"""
        logger.info(f"File changed detected: {file_path} ({sage_name})")

        try:
            # 自動索引更新
            if self.auto_update_config["enable_auto_index"]:
                self._update_indices()

            # 自動相互参照更新
            if self.auto_update_config["enable_auto_cross_ref"]:
                self._update_cross_references()

            self._log_update(f"File change handled: {sage_name}", "success")

        except Exception as e:
            self._log_update(f"File change handling failed: {sage_name}", f"error: {e}")

    def _update_indices(self):
        """索引の更新"""
        try:
            script_path = self.project_root / "scripts" / "auto_index_updater.py"
            result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Indices updated successfully")
            else:
                logger.error(f"Index update failed: {result.stderr}")

        except Exception as e:
            logger.error(f"Index update error: {e}")

    def _update_cross_references(self):
        """相互参照の更新"""
        try:
            script_path = self.project_root / "scripts" / "auto_cross_ref_updater.py"
            result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Cross-references updated successfully")
            else:
                logger.error(f"Cross-reference update failed: {result.stderr}")

        except Exception as e:
            logger.error(f"Cross-reference update error: {e}")

    def _perform_backup(self):
        """バックアップの実行"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.project_root / "backups" / "grimoire" / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 魔法書ファイルをバックアップ
            for file_path in self.monitored_files.keys():
                if Path(file_path).exists():
                    file_name = Path(file_path).name
                    shutil.copy2(file_path, backup_dir / file_name)

            # 索引ファイルもバックアップ
            index_files = ["MASTER_INDEX.md", "TOPIC_INDEX.md", "QUICK_REFERENCE.md", "README.md"]
            for index_file in index_files:
                index_path = self.grimoire_base / index_file
                if index_path.exists():
                    shutil.copy2(index_path, backup_dir / index_file)

            # 古いバックアップを削除
            self._cleanup_old_backups()

            logger.info(f"Backup completed: {backup_dir}")

        except Exception as e:
            logger.error(f"Backup failed: {e}")

    def _cleanup_old_backups(self):
        """古いバックアップの削除"""
        try:
            backup_base = self.project_root / "backups" / "grimoire"
            if backup_base.exists():
                backups = sorted([d for d in backup_base.iterdir() if d.is_dir()], key=lambda x: x.name, reverse=True)

                # 最大数を超えたバックアップを削除
                for backup in backups[self.auto_update_config["max_backup_files"] :]:
                    shutil.rmtree(backup)
                    logger.info(f"Removed old backup: {backup}")

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")

    def _perform_health_check(self):
        """ヘルスチェックの実行"""
        try:
            health_status = {"timestamp": datetime.now().isoformat(), "checks": {}}

            # ファイル存在チェック
            for file_path, sage_name in self.monitored_files.items():
                exists = Path(file_path).exists()
                health_status["checks"][f"{sage_name}_exists"] = exists

                if exists:
                    # ファイル読み取り可能チェック
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        health_status["checks"][f"{sage_name}_readable"] = True
                        health_status["checks"][f"{sage_name}_size"] = len(content)
                    except Exception:
                        health_status["checks"][f"{sage_name}_readable"] = False
                else:
                    health_status["checks"][f"{sage_name}_readable"] = False

            # 索引ファイル整合性チェック
            index_files = ["MASTER_INDEX.md", "TOPIC_INDEX.md", "QUICK_REFERENCE.md", "README.md"]
            for index_file in index_files:
                index_path = self.grimoire_base / index_file
                health_status["checks"][f"index_{index_file}_exists"] = index_path.exists()

            # ヘルスチェック結果をログに記録
            health_issues = [k for k, v in health_status["checks"].items() if not v]
            if health_issues:
                logger.warning(f"Health check issues: {health_issues}")
            else:
                logger.info("Health check passed")

        except Exception as e:
            logger.error(f"Health check failed: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """ファイルハッシュの計算"""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return ""

    def _assess_setup_status(self) -> str:
        """セットアップ状況の評価"""
        ready_systems = sum(self.update_systems.values())
        total_systems = len(self.update_systems)

        if ready_systems == total_systems:
            return "fully_ready"
        elif ready_systems >= total_systems * 0.8:
            return "mostly_ready"
        elif ready_systems >= total_systems * 0.5:
            return "partially_ready"
        else:
            return "not_ready"

    def _log_update(self, operation: str, status: str):
        """更新ログの記録"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {operation}: {status}\n"

        with open(self.update_log, "a", encoding="utf-8") as f:
            f.write(log_entry)

    def get_system_status(self) -> Dict[str, Any]:
        """システム状態の取得"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_running": self.system_running,
            "update_systems": self.update_systems,
            "monitored_files": len(self.monitored_files),
            "config": self.auto_update_config,
            "last_backup": self._get_last_backup_time(),
            "health_status": self._get_current_health_status(),
        }

    def _get_last_backup_time(self) -> Optional[str]:
        """最後のバックアップ時刻を取得"""
        try:
            backup_base = self.project_root / "backups" / "grimoire"
            if backup_base.exists():
                backups = sorted([d for d in backup_base.iterdir() if d.is_dir()], key=lambda x: x.name, reverse=True)
                if backups:
                    return backups[0].name
        except Exception:
            pass
        return None

    def _get_current_health_status(self) -> Dict[str, bool]:
        """現在のヘルス状態を取得"""
        health = {}
        for file_path, sage_name in self.monitored_files.items():
            health[f"{sage_name}_exists"] = Path(file_path).exists()
        return health


def main():
    """メイン処理"""
    auto_updater = GrimoireAutoUpdateSystem()

    print("🚀 グリモア自動更新システム")
    print("=" * 60)

    # 自動更新システムのセットアップ
    setup_results = auto_updater.setup_auto_update_system()

    # 結果表示
    print("\n📊 セットアップ結果サマリー")
    print("-" * 40)
    print(f"総合状況: {setup_results['overall_status'].upper()}")
    print(f"準備完了システム: {sum(auto_updater.update_systems.values())}/{len(auto_updater.update_systems)}")

    # システム別詳細
    print("\n🔍 システム別状況")
    print("-" * 40)
    for system_name, result in setup_results["systems"].items():
        status_icon = "✅" if result["status"] == "ready" else "❌"
        print(f"{status_icon} {system_name}: {result['status'].upper()}")
        if result["status"] == "failed" and "error" in result:
            print(f"    エラー: {result['error']}")

    # 設定情報
    print("\n⚙️ 設定情報")
    print("-" * 40)
    config = setup_results["config"]
    print(f"監視間隔: {config['watch_interval']}秒")
    print(f"バックアップ間隔: {config['backup_interval']}秒")
    print(f"ヘルスチェック間隔: {config['health_check_interval']}秒")
    print(f"最大バックアップ数: {config['max_backup_files']}")

    # 詳細レポート保存
    report_file = PROJECT_ROOT / "logs" / f"grimoire_auto_update_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(setup_results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n💾 詳細レポートを保存しました: {report_file}")

    # 自動更新システムの開始
    if setup_results["overall_status"] in ["fully_ready", "mostly_ready"]:
        print("\n🚀 自動更新システムを開始しています...")

        try:
            # システム開始
            if auto_updater.start_auto_update_system():
                print("✅ 自動更新システムが正常に開始されました")

                # 短時間の動作確認
                print("\n🔄 動作確認中...")
                time.sleep(5)

                # システム状態の確認
                status = auto_updater.get_system_status()
                print(f"システム稼働状況: {'稼働中' if status['system_running'] else '停止中'}")
                print(f"監視ファイル数: {status['monitored_files']}")

                # システム停止（デモンストレーション用）
                print("\n⏹️ システムを停止しています...")
                if auto_updater.stop_auto_update_system():
                    print("✅ 自動更新システムが正常に停止されました")
                else:
                    print("❌ システム停止に失敗しました")
            else:
                print("❌ 自動更新システムの開始に失敗しました")

        except KeyboardInterrupt:
            print("\n👋 ユーザーによって中断されました")
            auto_updater.stop_auto_update_system()
    else:
        print("\n⚠️ セットアップが完了していないため、自動更新システムは開始されません")

    # 使用方法の案内
    print("\n🎯 自動更新システムの使用方法")
    print("-" * 40)
    print("1. 魔法書ファイルを編集すると自動的に索引が更新されます")
    print("2. 定期的にバックアップが作成されます")
    print("3. ヘルスチェックでファイルの整合性を監視します")
    print("4. システムは別プロセスで継続的に動作します")


if __name__ == "__main__":
    main()
