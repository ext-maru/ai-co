#!/usr/bin/env python3
"""
🛡️ Deployment Safeguard System
デプロイメントセーフガードシステム - 重要ファイルの消失防止

デプロイやスクリプト実行時に重要ファイルを保護:
1.0 Pre-deployment validation
2.0 Critical file locking
3.0 Rollback preparation
4.0 Post-deployment verification
"""

import contextlib
import json
import logging
import shutil
import subprocess
import sys

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

class DeploymentSafeguard:
    """デプロイメントセーフガードシステム"""

    def __init__(self, project_root: Path = None):
        """初期化メソッド"""
        self.project_root = project_root or Path.cwd()
        self.safeguard_dir = self.project_root / ".deployment_safeguard"
        self.safeguard_dir.mkdir(exist_ok=True)

        # 絶対に消してはいけないファイル
        self.critical_files = {
            ".env",
            "CLAUDE.md",
            "config/slack_config.json",
            "config/slack_pm_config.json",
            "config/database.conf",
            "config/worker_config.json",
            "config/async_workers_config.yaml",
            "config/config.json",
            "config/system.json",
            "knowledge_base/README.md",
        }

        # 危険なパターン
        self.dangerous_patterns = [
            r"rm\s+-rf?\s+config/",
            r"rm\s+-rf?\s+\.env",
            r"rm\s+-rf?\s+\*\.json",
            r"rm\s+-rf?\s+knowledge_base/",
            r"find.*-delete",
            r"git\s+clean\s+-fd",
            r"docker\s+system\s+prune\s+-af",
            r">\s*config/.*\.json",
            r"mv\s+config/.*\s+/tmp",
            r"cp\s+/dev/null",
        ]

        self.deployment_log = []

    @contextlib.contextmanager
    def deployment_protection(self, operation_name: str = "deployment"):
        """デプロイメント保護コンテキスト"""
        logger.info(f"🛡️ デプロイメント保護開始: {operation_name}")

        # 1.0 Pre-deployment checks
        self._pre_deployment_checks()

        # 2.0 Create safety snapshot
        snapshot_id = self._create_safety_snapshot(operation_name)

        # 3.0 Lock critical files
        self._lock_critical_files()

        try:
            yield self

            # 4.0 Post-deployment verification
            self._post_deployment_verification()

            logger.info(f"✅ デプロイメント保護完了: {operation_name}")

        except Exception as e:
            logger.error(f"❌ デプロイメント中にエラー: {e}")

            # 5.0 Emergency rollback
            self._emergency_rollback(snapshot_id)
            raise

        finally:
            # 6.0 Unlock files
            self._unlock_critical_files()

    def _pre_deployment_checks(self):
        """デプロイメント前チェック"""
        checks = []

        # 重要ファイルの存在確認
        for rel_path in self.critical_files:
            file_path = self.project_root / rel_path
            if not file_path.exists():
                checks.append(f"❌ 重要ファイル不在: {rel_path}")
            else:
                checks.append(f"✅ ファイル確認: {rel_path}")

        # Git作業ディレクトリの状態確認
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.stdout.strip():
                checks.append("⚠️ 未コミットの変更あり")
                # 重要ファイルに変更がある場合は警告
                for line in result.stdout.strip().split("\n"):
                    if len(line) > 3:
                        file_path = line[3:]
                        if file_path in self.critical_files:
                            checks.append(
                                f"🚨 重要ファイルに未コミット変更: {file_path}"
                            )
            else:
                checks.append("✅ Git作業ディレクトリクリーン")

        except Exception as e:
            checks.append(f"⚠️ Git状態確認失敗: {e}")

        # ディスク容量確認
        try:
            disk_usage = shutil.disk_usage(self.project_root)
            free_gb = disk_usage.free / (1024**3)
            if free_gb < 1.0:
                checks.append(f"🚨 ディスク容量不足: {free_gb:0.1f}GB")
            else:
                checks.append(f"✅ ディスク容量: {free_gb:0.1f}GB利用可能")

        except Exception as e:
            checks.append(f"⚠️ ディスク容量確認失敗: {e}")

        # チェック結果をログ
        for check in checks:
            logger.info(check)

        # エラーがある場合は例外発生
        error_checks = [c for c in checks if c.startswith("❌") or c.startswith("🚨")]
        if error_checks:
            raise RuntimeError(
                f"Pre-deployment checks failed: {'; '.join(error_checks)}"
            )

    def _create_safety_snapshot(self, operation_name: str) -> str:
        """安全性スナップショット作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_id = f"{operation_name}_{timestamp}"
        snapshot_dir = self.safeguard_dir / "snapshots" / snapshot_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"📸 安全性スナップショット作成: {snapshot_id}")

        # 重要ファイルをバックアップ
        for rel_path in self.critical_files:
            file_path = self.project_root / rel_path
            if file_path.exists():
                backup_path = snapshot_dir / rel_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, backup_path)

        # スナップショット情報を記録
        snapshot_info = {
            "snapshot_id": snapshot_id,
            "operation_name": operation_name,
            "timestamp": timestamp,
            "files_backed_up": list(self.critical_files),
            "git_commit": self._get_current_git_commit(),
        }

        with open(snapshot_dir / "snapshot_info.json", "w") as f:
            json.dump(snapshot_info, f, indent=2)

        return snapshot_id

    def _lock_critical_files(self):
        """重要ファイルをロック"""
        logger.info("🔒 重要ファイルロック中...")

        for rel_path in self.critical_files:
            file_path = self.project_root / rel_path
            if file_path.exists():
                try:
                    # Linux: chattr +i でイミュータブル化
                    subprocess.run(
                        ["chattr", "+i", str(file_path)],
                        capture_output=True,
                        check=False,
                    )

                except FileNotFoundError:
                    # chattrコマンドが存在しない場合
                    # ファイル権限を読み取り専用に変更
                    file_path.chmod(0o444)

    def _unlock_critical_files(self):
        """重要ファイルのロック解除"""
        logger.info("🔓 重要ファイルロック解除中...")

        for rel_path in self.critical_files:
            file_path = self.project_root / rel_path
            if file_path.exists():
                try:
                    # Linux: chattr -i でイミュータブル解除
                    subprocess.run(
                        ["chattr", "-i", str(file_path)],
                        capture_output=True,
                        check=False,
                    )

                except FileNotFoundError:
                    # 権限を元に戻す
                    file_path.chmod(0o644)

    def _post_deployment_verification(self):
        """デプロイメント後検証"""
        logger.info("🔍 デプロイメント後検証中...")

        verification_results = []

        # 重要ファイルの存在確認
        for rel_path in self.critical_files:
            file_path = self.project_root / rel_path
            if file_path.exists():
                verification_results.append(f"✅ ファイル存在: {rel_path}")
            else:
                verification_results.append(f"❌ ファイル消失: {rel_path}")

        # 設定ファイルの内容検証
        try:
            from .unified_config_manager import health_check

            health_results = health_check()

            for namespace, result in health_results.items():
                if result["status"] == "healthy":
                    verification_results.append(f"✅ 設定正常: {namespace}")
                else:
                    verification_results.append(f"❌ 設定エラー: {namespace}")

        except Exception as e:
            verification_results.append(f"⚠️ 設定検証失敗: {e}")

        # 検証結果をログ
        for result in verification_results:
            logger.info(result)

        # エラーがある場合は例外発生
        error_results = [r for r in verification_results if r.startswith("❌")]
        if error_results:
            raise RuntimeError(
                f"Post-deployment verification failed: {'; '.join(error_results)}"
            )

    def _emergency_rollback(self, snapshot_id: str):
        """緊急ロールバック"""
        logger.critical(f"🚨 緊急ロールバック実行: {snapshot_id}")

        snapshot_dir = self.safeguard_dir / "snapshots" / snapshot_id
        if not snapshot_dir.exists():
            logger.error(f"❌ スナップショット不在: {snapshot_id}")
            return False

        rollback_success = True

        # 重要ファイルを復元
        for rel_path in self.critical_files:
            backup_path = snapshot_dir / rel_path
            if backup_path.exists():
                file_path = self.project_root / rel_path
                try:
                    # ロック解除
                    self._unlock_single_file(file_path)

                    # 復元
                    shutil.copy2(backup_path, file_path)
                    logger.info(f"✅ ファイル復元: {rel_path}")

                except Exception as e:
                    logger.error(f"❌ ファイル復元失敗: {rel_path} - {e}")
                    rollback_success = False

        if rollback_success:
            logger.info("✅ 緊急ロールバック完了")
        else:
            logger.error("❌ 緊急ロールバック部分失敗")

        return rollback_success

    def _unlock_single_file(self, file_path: Path):
        """単一ファイルのロック解除"""
        try:
            subprocess.run(
                ["chattr", "-i", str(file_path)], capture_output=True, check=False
            )
        except FileNotFoundError:
            try:
                file_path.chmod(0o644)
            except Exception:
                pass

    def _get_current_git_commit(self) -> str:
        """現在のGitコミットハッシュを取得"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    def validate_command(self, command: str) -> bool:
        """コマンドの安全性検証"""
        import re

        # 危険なパターンをチェック
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                logger.warning(f"🚨 危険なコマンド検出: {command}")
                logger.warning(f"   パターン: {pattern}")
                return False

        return True

    def safe_execute(
        self, command: str, operation_name: str = "command_execution"
    ) -> subprocess.CompletedProcess:
        """安全なコマンド実行"""
        # コマンド検証
        if not self.validate_command(command):
            raise ValueError(f"Dangerous command blocked: {command}")

        # デプロイメント保護下で実行
        with self.deployment_protection(operation_name):
            logger.info(f"🛡️ 保護下でコマンド実行: {command}")

            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.warning(
                    f"⚠️ コマンドエラー (code {result.returncode}): {result.stderr}"
                )
            else:
                logger.info(f"✅ コマンド成功: {command}")

            return result

    def get_safeguard_status(self) -> Dict:
        """セーフガードステータスを取得"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "critical_files_count": len(self.critical_files),
            "snapshots_count": 0,
            "recent_operations": [],
        }

        # スナップショット数を計算
        snapshots_dir = self.safeguard_dir / "snapshots"
        if snapshots_dir.exists():
            status["snapshots_count"] = len(list(snapshots_dir.iterdir()))

        # 重要ファイルの状態
        status["critical_files_status"] = {}
        for rel_path in self.critical_files:
            file_path = self.project_root / rel_path
            status["critical_files_status"][rel_path] = {
                "exists": file_path.exists(),
                "size": file_path.stat().st_size if file_path.exists() else 0,
                "writable": (
                    file_path.is_file() and os.access(file_path, os.W_OK)
                    if file_path.exists()
                    else False
                ),
            }

        return status

# グローバルインスタンス
deployment_safeguard = DeploymentSafeguard()

def safe_deployment(operation_name: str = "deployment"):
    """安全なデプロイメントコンテキスト"""
    return deployment_safeguard.deployment_protection(operation_name)

def safe_execute_command(command: str, operation_name: str = "command_execution"):
    """安全なコマンド実行"""
    return deployment_safeguard.safe_execute(command, operation_name)

def validate_command_safety(command: str) -> bool:
    """コマンドの安全性検証"""
    return deployment_safeguard.validate_command(command)

if __name__ == "__main__":
    import os

    logging.basicConfig(level=logging.INFO)

    # テスト
    print("🛡️ Deployment Safeguard Test")

    # 危険なコマンドのテスト
    dangerous_commands = [
        "rm -rf config/",
        "rm .env",
        "mv config/slack_config.json /tmp/",
        "echo '' > config/config.json",
    ]

    for cmd in dangerous_commands:
        is_safe = validate_command_safety(cmd)
        status = "✅ SAFE" if is_safe else "🚨 BLOCKED"
        print(f"{status}: {cmd}")

    # 安全なデプロイメントのテスト
    with safe_deployment("test_deployment"):
        print("✅ Safe deployment context test completed")
