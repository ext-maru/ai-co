#!/usr/bin/env python3
"""
Docker Permission Management System
エルダーズギルド Docker権限管理システム

Created by Claude Elder
Version: 1.0.0
"""

import os
import subprocess
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DockerStatus:
    """Docker状態情報"""

    is_running: bool
    permission_ok: bool
    user_in_group: bool
    group_exists: bool
    socket_accessible: bool
    error_message: Optional[str] = None


class DockerPermissionManager:
    """Docker権限管理システム"""

    def __init__(self):
        self.user = os.getenv("USER", "unknown")
        self.docker_socket = "/var/run/docker.sock"
        self.logger = logging.getLogger(__name__)

    def get_docker_status(self) -> DockerStatus:
        """Docker状態を詳細取得"""
        try:
            # Docker グループ存在確認
            group_exists = self._check_docker_group_exists()

            # ユーザーがDockerグループにいるか確認
            user_in_group = self._check_user_in_docker_group()

            # Docker ソケットアクセス可能か確認
            socket_accessible = self._check_socket_accessible()

            # Docker デーモン稼働確認
            is_running = self._check_docker_running()

            # 権限OK判定
            permission_ok = user_in_group and socket_accessible and is_running

            return DockerStatus(
                is_running=is_running,
                permission_ok=permission_ok,
                user_in_group=user_in_group,
                group_exists=group_exists,
                socket_accessible=socket_accessible,
            )

        except Exception as e:
            self.logger.error(f"Docker status check failed: {e}")
            return DockerStatus(
                is_running=False,
                permission_ok=False,
                user_in_group=False,
                group_exists=False,
                socket_accessible=False,
                error_message=str(e),
            )

    def _check_docker_group_exists(self) -> bool:
        """dockerグループ存在確認"""
        try:
            result = subprocess.run(
                ["getent", "group", "docker"], capture_output=True, text=True
            )
            return result.returncode == 0
        except:
            return False

    def _check_user_in_docker_group(self) -> bool:
        """ユーザーがdockerグループにいるか確認"""
        try:
            result = subprocess.run(
                ["groups", self.user], capture_output=True, text=True
            )
            return "docker" in result.stdout
        except:
            return False

    def _check_socket_accessible(self) -> bool:
        """Docker ソケットアクセス可能か確認"""
        try:
            return os.access(self.docker_socket, os.R_OK | os.W_OK)
        except:
            return False

    def _check_docker_running(self) -> bool:
        """Docker デーモン稼働確認"""
        try:
            result = subprocess.run(["docker", "info"], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def fix_permissions(self) -> Dict[str, Any]:
        """Docker権限問題を自動修正"""
        status = self.get_docker_status()
        fixes_applied = []

        if status.permission_ok:
            return {
                "success": True,
                "message": "Docker permissions already OK",
                "fixes_applied": [],
            }

        # dockerグループが存在しない場合は作成
        if not status.group_exists:
            try:
                subprocess.run(["sudo", "groupadd", "docker"], check=True)
                fixes_applied.append("created_docker_group")
                self.logger.info("Docker group created")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to create docker group: {e}")
                return {
                    "success": False,
                    "message": f"Failed to create docker group: {e}",
                    "fixes_applied": fixes_applied,
                }

        # ユーザーをdockerグループに追加
        if not status.user_in_group:
            try:
                subprocess.run(
                    ["sudo", "usermod", "-aG", "docker", self.user], check=True
                )
                fixes_applied.append("added_user_to_docker_group")
                self.logger.info(f"Added {self.user} to docker group")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to add user to docker group: {e}")
                return {
                    "success": False,
                    "message": f"Failed to add user to docker group: {e}",
                    "fixes_applied": fixes_applied,
                }

        # Docker ソケット権限修正
        if not status.socket_accessible:
            try:
                subprocess.run(["sudo", "chmod", "666", self.docker_socket], check=True)
                fixes_applied.append("fixed_socket_permissions")
                self.logger.info("Docker socket permissions fixed")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to fix socket permissions: {e}")
                return {
                    "success": False,
                    "message": f"Failed to fix socket permissions: {e}",
                    "fixes_applied": fixes_applied,
                }

        return {
            "success": True,
            "message": "Docker permissions fixed successfully",
            "fixes_applied": fixes_applied,
            "note": "You may need to log out and log back in for group changes to take effect",
        }

    def run_with_docker_group(self, command: str) -> subprocess.CompletedProcess:
        """sg docker -c でコマンド実行"""
        try:
            full_command = f'sg docker -c "{command}"'
            result = subprocess.run(
                full_command, shell=True, capture_output=True, text=True
            )
            return result
        except Exception as e:
            self.logger.error(f"Failed to run command with docker group: {e}")
            raise


# グローバルインスタンス
docker_manager = DockerPermissionManager()


# 便利な関数
def get_docker_status() -> DockerStatus:
    """Docker状態取得"""
    return docker_manager.get_docker_status()


def fix_docker_permissions() -> Dict[str, Any]:
    """Docker権限修正"""
    return docker_manager.fix_permissions()


def run_docker_command(command: str) -> subprocess.CompletedProcess:
    """Docker コマンドを適切な権限で実行"""
    return docker_manager.run_with_docker_group(command)


if __name__ == "__main__":
    print("🐳 Docker Permission Management System")
    print("=" * 50)

    # 状態確認
    status = get_docker_status()
    print(f"Docker Running: {status.is_running}")
    print(f"Permissions OK: {status.permission_ok}")
    print(f"User in Group: {status.user_in_group}")
    print(f"Group Exists: {status.group_exists}")
    print(f"Socket Accessible: {status.socket_accessible}")

    if status.error_message:
        print(f"Error: {status.error_message}")

    # 権限修正が必要な場合
    if not status.permission_ok:
        print("\n🔧 Fixing Docker permissions...")
        result = fix_docker_permissions()
        print(f"Result: {result}")
