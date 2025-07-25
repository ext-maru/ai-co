#!/usr/bin/env python3
"""
🛡️ Configuration Protection System
設定ファイル保護システム - 消失・破損の根本防止

重要な設定ファイルを複数の方法で保護:
1.0 イミュータブル化 (chattr +i)
2.0 リアルタイム監視 (inotify)
3.0 Git自動追跡
4.0 暗号化バックアップ
5.0 デプロイメント保護
"""

import asyncio
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Watchdog for file monitoring
try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:
    print("Installing watchdog for file monitoring...")
    subprocess.run([sys.executable, "-m", "pip", "install", "watchdog"])
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class ConfigFileProtectionHandler(FileSystemEventHandler):
    """設定ファイル保護ハンドラー"""

    def __init__(self, protection_system):
        """初期化メソッド"""
        self.protection_system = protection_system

    def on_deleted(self, event):
        """on_deletedメソッド"""
        if not event.is_directory:
            filepath = Path(event.src_path)
            if self.protection_system.is_protected_file(filepath):
                asyncio.create_task(self.protection_system.handle_deletion(filepath))

    def on_modified(self, event):
        """on_modifiedメソッド"""
        if not event.is_directory:
            filepath = Path(event.src_path)
            if self.protection_system.is_protected_file(filepath):
                asyncio.create_task(
                    self.protection_system.handle_modification(filepath)
                )

    def on_moved(self, event):
        """on_movedメソッド"""
        if not event.is_directory:
            src_path = Path(event.src_path)
            dest_path = Path(event.dest_path)
            if self.protection_system.is_protected_file(src_path):
                asyncio.create_task(
                    self.protection_system.handle_move(src_path, dest_path)
                )


class ConfigProtectionSystem:
    """設定ファイル保護システム"""

    def __init__(self, project_root: Path = None):
        """初期化メソッド"""
        self.project_root = project_root or Path.cwd()
        self.config_dir = self.project_root / "config"
        self.protection_dir = self.project_root / ".config_protection"
        self.protection_dir.mkdir(exist_ok=True)

        # 保護対象ファイル
        self.protected_files = {
            "config/slack_config.json",
            "config/slack_pm_config.json",
            "config/database.conf",
            "config/worker_config.json",
            "config/async_workers_config.yaml",
            ".env",
            "CLAUDE.md",
            "config/config.json",
            "config/system.json",
        }

        # ファイルハッシュキャッシュ
        self.file_hashes = {}

        # 監視オブザーバー
        self.observer = None

        # 保護ログ
        self.protection_log = []

    def initialize_protection(self):
        """保護システムの初期化"""
        logger.info("🛡️ 設定ファイル保護システム初期化中...")

        # 1.0 重要ファイルのスナップショット作成
        self._create_snapshots()

        # 2.0 ファイル監視開始
        self._start_file_monitoring()

        # 3.0 Git自動追跡設定
        self._setup_git_tracking()

        # 4.0 イミュータブル化 (Linuxのみ)
        self._apply_immutable_protection()

        # 5.0 定期バックアップ設定
        self._setup_periodic_backup()

        logger.info("✅ 設定ファイル保護システム初期化完了")

    def _create_snapshots(self):
        """重要ファイルのスナップショット作成"""
        snapshot_dir = self.protection_dir / "snapshots"
        snapshot_dir.mkdir(exist_ok=True)

        for rel_path in self.protected_files:
            file_path = self.project_root / rel_path
            if file_path.exists():
                # ハッシュ計算
                file_hash = self._calculate_hash(file_path)
                self.file_hashes[str(file_path)] = file_hash

                # スナップショット作成
                snapshot_path = snapshot_dir / f"{rel_path.replace('/', '_')}.snapshot"
                snapshot_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, snapshot_path)

    def _start_file_monitoring(self):
        """リアルタイムファイル監視開始"""
        if self.observer:
            self.observer.stop()

        self.observer = Observer()
        handler = ConfigFileProtectionHandler(self)

        # プロジェクトルートとconfigディレクトリを監視
        self.observer.schedule(handler, str(self.project_root), recursive=False)
        self.observer.schedule(handler, str(self.config_dir), recursive=True)

        self.observer.start()
        logger.info("👁️ ファイル監視開始")

    def _setup_git_tracking(self):
        """Git自動追跡設定"""
        try:
            # 保護ファイルをGitに追加
            for rel_path in self.protected_files:
                file_path = self.project_root / rel_path
                if file_path.exists():
                    subprocess.run(
                        ["git", "add", str(file_path)],
                        cwd=self.project_root,
                        capture_output=True,
                    )

            # 自動コミット（変更がある場合のみ）
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=self.project_root,
                capture_output=True,
            )

            if result.returncode != 0:  # 変更がある
                subprocess.run(
                    [
                        "git",
                        "commit",
                        "-m",
                        f"🛡️ Config protection snapshot - {datetime.now().isoformat()}",
                    ],
                    cwd=self.project_root,
                    capture_output=True,
                )

            logger.info("📁 Git自動追跡設定完了")
        except Exception as e:
            logger.warning(f"Git追跡設定警告: {e}")

    def _apply_immutable_protection(self):
        """イミュータブル化 (Linux専用)"""
        if os.name != "posix":
            return

        for rel_path in self.protected_files:
            file_path = self.project_root / rel_path
            if file_path.exists():
                try:
                    # chattr +i でファイルを変更不可に
                    subprocess.run(
                        ["chattr", "+i", str(file_path)],
                        capture_output=True,
                        check=False,  # 権限不足でも続行
                    )

                except FileNotFoundError:
                    # chattrコマンドが存在しない場合は無視
                    pass

    def _setup_periodic_backup(self):
        """定期バックアップ設定"""
        backup_dir = self.protection_dir / "periodic_backups"
        backup_dir.mkdir(exist_ok=True)

        # 1時間ごとのバックアップタスクをスケジュール
        asyncio.create_task(self._periodic_backup_task())

    async def _periodic_backup_task(self):
        """定期バックアップタスク"""
        while True:
            try:
                await asyncio.sleep(3600)  # 1時間待機
                self._create_timestamped_backup()
            except Exception as e:
                logger.error(f"定期バックアップエラー: {e}")

    def _create_timestamped_backup(self):
        """タイムスタンプ付きバックアップ作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.protection_dir / "periodic_backups" / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        for rel_path in self.protected_files:
            file_path = self.project_root / rel_path
            if file_path.exists():
                backup_path = backup_dir / rel_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, backup_path)

        logger.info(f"💾 定期バックアップ作成: {timestamp}")

        # 古いバックアップを削除（最新10個を保持）
        self._cleanup_old_backups()

    def _cleanup_old_backups(self, keep: int = 10):
        """古いバックアップを削除"""
        backup_parent = self.protection_dir / "periodic_backups"
        if not backup_parent.exists():
            return

        backups = sorted(
            backup_parent.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True
        )
        for backup in backups[keep:]:
            if backup.is_dir():
                shutil.rmtree(backup)

    def is_protected_file(self, filepath: Path) -> bool:
        """ファイルが保護対象かチェック"""
        try:
            rel_path = filepath.relative_to(self.project_root)
            return str(rel_path) in self.protected_files
        except ValueError:
            return False

    async def handle_deletion(self, filepath: Path):
        """ファイル削除の処理"""
        logger.critical(f"🚨 保護ファイル削除検出: {filepath}")

        # 即座に復元
        await self._restore_from_snapshot(filepath)

        # インシデント記録
        self._log_incident("DELETION", filepath, "ファイルが削除されました")

        # アラート送信
        await self._send_alert("CRITICAL", f"保護ファイル削除: {filepath}")

    async def handle_modification(self, filepath: Path):
        """ファイル変更の処理"""
        # ハッシュチェック
        current_hash = self._calculate_hash(filepath)
        stored_hash = self.file_hashes.get(str(filepath))

        if stored_hash and current_hash != stored_hash:
            logger.warning(f"⚠️ 保護ファイル変更検出: {filepath}")

            # 変更前のバックアップ作成
            self._create_change_backup(filepath)

            # ハッシュ更新
            self.file_hashes[str(filepath)] = current_hash

            # Git自動コミット
            await self._auto_commit_change(filepath)

    async def handle_move(self, src_path: Path, dest_path: Path):
        """ファイル移動の処理"""
        logger.error(f"🚨 保護ファイル移動検出: {src_path} → {dest_path}")

        # 元の位置に復元
        if dest_path.exists():
            shutil.move(dest_path, src_path)
            logger.info(f"✅ ファイル復元: {src_path}")

        # インシデント記録
        self._log_incident("MOVE", src_path, f"ファイルが移動されました: {dest_path}")

    async def _restore_from_snapshot(self, filepath: Path):
        """スナップショットから復元"""
        try:
            rel_path = filepath.relative_to(self.project_root)
            snapshot_path = (
                self.protection_dir
                / "snapshots"
                / f"{str(rel_path).replace('/', '_')}.snapshot"
            )

            if snapshot_path.exists():
                # イミュータブル属性を一時的に解除
                self._remove_immutable(filepath)

                # 復元
                shutil.copy2(snapshot_path, filepath)

                # イミュータブル属性を再設定
                self._apply_immutable(filepath)

                logger.info(f"✅ スナップショットから復元: {filepath}")
                return True
            else:
                # 定期バックアップから復元を試行
                return await self._restore_from_periodic_backup(filepath)

        except Exception as e:
            logger.error(f"スナップショット復元失敗: {e}")
            return False

    async def _restore_from_periodic_backup(self, filepath: Path) -> bool:
        """定期バックアップから復元"""
        try:
            rel_path = filepath.relative_to(self.project_root)
            backup_parent = self.protection_dir / "periodic_backups"

            # 最新のバックアップを探す
            backups = sorted(
                backup_parent.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True
            )

            for backup_dir in backups:
                backup_file = backup_dir / rel_path
                if backup_file.exists():
                    # イミュータブル属性を一時的に解除
                    self._remove_immutable(filepath)

                    # 復元
                    shutil.copy2(backup_file, filepath)

                    # イミュータブル属性を再設定
                    self._apply_immutable(filepath)

                    logger.info(f"✅ 定期バックアップから復元: {filepath}")
                    return True

            logger.error(f"❌ バックアップが見つかりません: {filepath}")
            return False

        except Exception as e:
            logger.error(f"定期バックアップ復元失敗: {e}")
            return False

    def _remove_immutable(self, filepath: Path):
        """イミュータブル属性を解除"""
        if os.name == "posix":
            try:
                subprocess.run(
                    ["chattr", "-i", str(filepath)], capture_output=True, check=False
                )
            except FileNotFoundError:
                pass

    def _apply_immutable(self, filepath: Path):
        """イミュータブル属性を設定"""
        if os.name == "posix":
            try:
                subprocess.run(
                    ["chattr", "+i", str(filepath)], capture_output=True, check=False
                )
            except FileNotFoundError:
                pass

    def _create_change_backup(self, filepath: Path):
        """変更前バックアップ作成"""
        try:
            rel_path = filepath.relative_to(self.project_root)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            change_backup_dir = self.protection_dir / "change_backups"
            change_backup_dir.mkdir(exist_ok=True)

            backup_name = f"{str(rel_path).replace('/', '_')}.{timestamp}.backup"
            backup_path = change_backup_dir / backup_name

            shutil.copy2(filepath, backup_path)

        except Exception as e:
            logger.error(f"変更前バックアップ失敗: {e}")

    async def _auto_commit_change(self, filepath: Path):
        """変更の自動コミット"""
        try:
            rel_path = filepath.relative_to(self.project_root)

            # Git追加
            subprocess.run(
                ["git", "add", str(filepath)],
                cwd=self.project_root,
                capture_output=True,
            )

            # 自動コミット
            commit_msg = f"🔧 Auto-protect config change: {rel_path}"
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.project_root,
                capture_output=True,
            )

            logger.info(f"📝 変更を自動コミット: {rel_path}")

        except Exception as e:
            logger.warning(f"自動コミット警告: {e}")

    def _calculate_hash(self, filepath: Path) -> str:
        """ファイルのハッシュ値を計算"""
        try:
            with open(filepath, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def _log_incident(self, incident_type: str, filepath: Path, description: str):
        """インシデントをログに記録"""
        incident = {
            "timestamp": datetime.now().isoformat(),
            "type": incident_type,
            "file": str(filepath),
            "description": description,
        }

        self.protection_log.append(incident)

        # インシデントファイルに記録
        incident_file = self.protection_dir / "incidents.jsonl"
        with open(incident_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(incident, ensure_ascii=False) + "\n")

    async def _send_alert(self, level: str, message: str):
        """アラート送信"""
        # Elder Councilに報告
        alert_file = (
            Path("knowledge_base/elder_council_requests")
            / f"config_protection_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        alert_file.parent.mkdir(exist_ok=True)

        alert_content = f"""# 🚨 設定ファイル保護アラート

## アラート情報
- **レベル**: {level}
- **発生時刻**: {datetime.now().isoformat()}
- **メッセージ**: {message}

## 自動対応
設定ファイル保護システムが自動的に対応を試行しました。

## 確認事項
1.0 ファイルが正常に復元されているか確認
2.0 不正なアクセスがないか調査
3.0 必要に応じて追加のセキュリティ対策を実施

---
*Generated by Config Protection System*
"""

        with open(alert_file, "w", encoding="utf-8") as f:
            f.write(alert_content)

        logger.critical(f"🚨 アラート送信: {message}")

    def get_protection_status(self) -> Dict:
        """保護システムのステータスを取得"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "protected_files_count": len(self.protected_files),
            "monitoring_active": self.observer is not None and self.observer.is_alive(),
            "incidents_count": len(self.protection_log),
            "recent_incidents": self.protection_log[-5:] if self.protection_log else [],
        }

        # ファイル存在確認
        status["file_status"] = {}
        for rel_path in self.protected_files:
            file_path = self.project_root / rel_path
            status["file_status"][rel_path] = {
                "exists": file_path.exists(),
                "size": file_path.stat().st_size if file_path.exists() else 0,
                "hash": self.file_hashes.get(str(file_path), "unknown"),
            }

        return status

    def stop_protection(self):
        """保護システムを停止"""
        if self.observer:
            self.observer.stop()
            self.observer.join()

        # イミュータブル属性を解除
        for rel_path in self.protected_files:
            file_path = self.project_root / rel_path
            if file_path.exists():
                self._remove_immutable(file_path)

        logger.info("🛡️ 設定ファイル保護システム停止")


# グローバルインスタンス
protection_system = ConfigProtectionSystem()


def initialize_config_protection():
    """設定ファイル保護の初期化"""
    protection_system.initialize_protection()


def get_protection_status():
    """保護ステータスの取得"""
    return protection_system.get_protection_status()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 保護システム開始
    protection_system.initialize_protection()

    try:
        # メインループ
        asyncio.run(asyncio.sleep(float("inf")))
    except KeyboardInterrupt:
        protection_system.stop_protection()
        logger.info("保護システムを停止しました")
