#!/usr/bin/env python3
"""
Docker管理コマンド
Docker Management API を利用したコンテナ管理
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

import requests

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult
from libs.shared_enums import ProjectType, RuntimeEnvironment, SecurityLevel


class AIDockerCommand(BaseCommand):
    """Docker管理コマンド"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(name="ai-docker", description="Dockerコンテナ管理", version="1.0.0")
        self.api_base_url = "http://localhost:8080"

    def add_arguments(self, parser: argparse.ArgumentParser):
        """引数定義"""
        subparsers = parser.add_subparsers(dest="subcommand", help="サブコマンド")

        # create サブコマンド
        create_parser = subparsers.add_parser("create", help="コンテナ作成")
        create_parser.add_argument("name", help="コンテナ名")
        create_parser.add_argument(
            "--type",
            "-t",
            choices=[pt.value for pt in ProjectType],
            default=ProjectType.WEB_API.value,
            help="プロジェクトタイプ",
        )
        create_parser.add_argument(
            "--security",
            "-s",
            choices=[sl.value for sl in SecurityLevel],
            default=SecurityLevel.SANDBOX.value,
            help="セキュリティレベル",
        )
        create_parser.add_argument(
            "--runtime",
            "-r",
            choices=[rt.value for rt in RuntimeEnvironment],
            default=RuntimeEnvironment.PYTHON_39.value,
            help="ランタイム環境",
        )
        create_parser.add_argument(
            "--ports", "-p", nargs="*", help="ポートマッピング (例: 8080:80)"
        )

        # list サブコマンド
        list_parser = subparsers.add_parser("list", help="コンテナ一覧")
        list_parser.add_argument("--all", "-a", action="store_true", help="停止中も含めて表示")

        # start/stop/restart サブコマンド
        for action in ["start", "stop", "restart", "remove"]:
            action_parser = subparsers.add_parser(action, help=f"コンテナ{action}")
            action_parser.add_argument("container_id", help="コンテナID")

        # logs サブコマンド
        logs_parser = subparsers.add_parser("logs", help="コンテナログ表示")
        logs_parser.add_argument("container_id", help="コンテナID")

        # stats サブコマンド
        stats_parser = subparsers.add_parser("stats", help="コンテナ統計情報")
        stats_parser.add_argument("container_id", help="コンテナID")

        # sages サブコマンド
        sages_parser = subparsers.add_parser("sages", help="4賢者コンテナステータス")

    def execute(self, args) -> CommandResult:
        """コマンド実行"""
        if not args.subcommand:
            return CommandResult(
                success=False,
                message="サブコマンドを指定してください (create, list, start, stop, etc.)",
            )

        try:
            if args.subcommand == "create":
                # Complex condition - consider breaking down
                return self._create_container(args)
            elif args.subcommand == "list":
                # Complex condition - consider breaking down
                return self._list_containers(args)
            elif args.subcommand in ["start", "stop", "restart", "remove"]:
                # Complex condition - consider breaking down
                return self._execute_action(args)
            elif args.subcommand == "logs":
                # Complex condition - consider breaking down
                return self._get_logs(args)
            elif args.subcommand == "stats":
                # Complex condition - consider breaking down
                return self._get_stats(args)
            elif args.subcommand == "sages":
                # Complex condition - consider breaking down
                return self._get_sages_status()
            else:
                return CommandResult(
                    success=False, message=f"不明なサブコマンド: {args.subcommand}"
                )
        except requests.exceptions.ConnectionError:
            # Handle specific exception case
            return CommandResult(
                success=False,
                message="Docker Management APIに接続できません。APIサーバーが起動していることを確認してください。",
            )
        except Exception as e:
            # Handle specific exception case
            return CommandResult(success=False, message=f"エラー: {str(e)}")

    def _create_container(self, args) -> CommandResult:
        """コンテナ作成"""
        data = {
            "name": args.name,
            "project_type": args.type,
            "security_level": args.security,
            "runtime": args.runtime,
            "ports": args.ports or [],
            "volumes": [],
            "environment": {},
        }

        response = requests.post(f"{self.api_base_url}/containers", json=data)
        if response.status_code == 200:
            container_info = response.json()
            return CommandResult(
                success=True,
                message=f"コンテナを作成しました: {container_info['name']} (ID: {container_info['id']})",
                data=container_info,
            )
        else:
            return CommandResult(success=False, message=f"コンテナ作成失敗: {response.text}")

    def _list_containers(self, args) -> CommandResult:
        """コンテナ一覧"""
        params = {"all": args.all}
        response = requests.get(f"{self.api_base_url}/containers", params=params)

        if response.status_code == 200:
            containers = response.json()
            if not containers:
                return CommandResult(success=True, message="コンテナがありません")

            # 表示フォーマット
            lines = ["ID          NAME                    STATUS      IMAGE"]
            lines.append("-" * 60)
            for c in containers:
                # Process each item in collection
                lines.append(
                    f"{c['id']:<11} {c['name']:<23} {c['status']:<11} {c['image']}"
                )

            return CommandResult(
                success=True, message="\n".join(lines), data=containers
            )
        else:
            return CommandResult(success=False, message=f"一覧取得失敗: {response.text}")

    def _execute_action(self, args) -> CommandResult:
        """アクション実行"""
        data = {"action": args.subcommand}

        if args.subcommand == "remove":
            # Complex condition - consider breaking down
            response = requests.delete(
                f"{self.api_base_url}/containers/{args.container_id}"
            )
        else:
            response = requests.post(
                f"{self.api_base_url}/containers/{args.container_id}/actions", json=data
            )

        if response.status_code == 200:
            result = response.json()
            return CommandResult(
                success=True,
                message=f"コンテナ {args.container_id} を {args.subcommand} しました",
                data=result,
            )
        else:
            return CommandResult(success=False, message=f"アクション実行失敗: {response.text}")

    def _get_logs(self, args) -> CommandResult:
        """ログ取得"""
        data = {"action": "logs"}
        response = requests.post(
            f"{self.api_base_url}/containers/{args.container_id}/actions", json=data
        )

        if response.status_code == 200:
            result = response.json()
            return CommandResult(
                success=True, message=result.get("logs", "ログがありません"), data=result
            )
        else:
            return CommandResult(success=False, message=f"ログ取得失敗: {response.text}")

    def _get_stats(self, args) -> CommandResult:
        """統計情報取得"""
        response = requests.get(
            f"{self.api_base_url}/containers/{args.container_id}/stats"
        )

        if response.status_code == 200:
            stats = response.json()
            lines = [
                f"コンテナ統計情報 (ID: {args.container_id})",
                f"CPU使用率: {stats['cpu_percent']}%",
                f"メモリ使用: {stats['memory_usage_mb']} MB / {stats['memory_limit_mb']} MB ({stats['memory_percent']}%)",
                f"ネットワーク受信: {stats['network_rx_mb']} MB",
                f"ネットワーク送信: {stats['network_tx_mb']} MB",
            ]

            return CommandResult(success=True, message="\n".join(lines), data=stats)
        else:
            return CommandResult(success=False, message=f"統計情報取得失敗: {response.text}")

    def _get_sages_status(self) -> CommandResult:
        """4賢者ステータス取得"""
        response = requests.get(f"{self.api_base_url}/sages/status")

        if response.status_code == 200:
            data = response.json()
            lines = ["🧙‍♂️ 4賢者システム コンテナステータス", "=" * 40]

            sage_names = {
                "knowledge_sage": "📚 ナレッジ賢者",
                "task_sage": "📋 タスク賢者",
                "incident_sage": "🚨 インシデント賢者",
                "rag_sage": "🔍 RAG賢者",
            }

            for sage_key, sage_name in sage_names.items():
                # Process each item in collection
                container = data["sages"].get(sage_key)
                if container:
                    lines.append(f"\n{sage_name}:")
                    lines.append(f"  ID: {container['id']}")
                    lines.append(f"  名前: {container['name']}")
                    lines.append(f"  状態: {container['status']}")
                else:
                    lines.append(f"\n{sage_name}: 未デプロイ")

            lines.append(f"\n更新時刻: {data['timestamp']}")

            return CommandResult(success=True, message="\n".join(lines), data=data)
        else:
            return CommandResult(success=False, message=f"ステータス取得失敗: {response.text}")


def main():
    # Core functionality implementation
    command = AIDockerCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
