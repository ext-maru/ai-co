#!/usr/bin/env python3
"""
設定確認
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import configparser

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from commands.base_command import BaseCommand, CommandResult


class AIConfigCommand(BaseCommand):
    """設定確認コマンド"""

    def __init__(self):
        super().__init__(name="ai-config", description="設定確認", version="1.0.0")
        self.console = Console()
        self.config_dir = Path("/home/aicompany/ai_co/config")

    def setup_arguments(self):
        """引数設定"""
        self.parser.add_argument("file", nargs="?", help="表示する設定ファイル")
        self.parser.add_argument("--list", "-l", action="store_true", help="設定ファイル一覧")
        self.parser.add_argument("--get", "-g", help="特定の設定値を取得（例: slack.ENABLE_SLACK）")

    def execute(self, args) -> CommandResult:
        """実行"""
        if args.list:
            return self._list_configs()

        if args.get:
            return self._get_config_value(args.get)

        if args.file:
            return self._show_config_file(args.file)

        # 全設定の概要
        return self._show_all_configs()

    def _list_configs(self) -> CommandResult:
        """設定ファイル一覧"""
        config_files = list(self.config_dir.glob("*.conf"))

        table = Table(title="📋 設定ファイル一覧")
        table.add_column("ファイル名", style="cyan")
        table.add_column("サイズ", justify="right")
        table.add_column("最終更新", style="dim")

        from datetime import datetime

        for conf in sorted(config_files):
            stat = conf.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            table.add_row(conf.name, f"{stat.st_size:,} bytes", mtime)

        self.console.print(table)
        return CommandResult(success=True)

    def _show_config_file(self, filename: str) -> CommandResult:
        """設定ファイル表示"""
        if not filename.endswith(".conf"):
            filename += ".conf"

        config_path = self.config_dir / filename
        if not config_path.exists():
            return CommandResult(success=False, message=f"設定ファイルが見つかりません: {filename}")

        content = config_path.read_text()
        self.console.print(Panel(content, title=f"📄 {filename}", border_style="blue"))

        return CommandResult(success=True)

    def _show_all_configs(self) -> CommandResult:
        """全設定の概要"""
        configs = {}

        # 各設定ファイルを読み込み
        for conf_file in self.config_dir.glob("*.conf"):
            config_name = conf_file.stem
            configs[config_name] = {}

            with open(conf_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        # 機密情報はマスク
                        if any(
                            secret in key.upper()
                            for secret in ["TOKEN", "PASSWORD", "SECRET", "KEY"]
                        ):
                            value = "***" + value[-4:] if len(value) > 4 else "***"
                        configs[config_name][key] = value.strip('"')

        # テーブル表示
        for config_name, settings in configs.items():
            table = Table(title=f"⚙️  {config_name}.conf")
            table.add_column("設定項目", style="cyan")
            table.add_column("値", style="yellow")

            for key, value in settings.items():
                table.add_row(key, value)

            self.console.print(table)
            self.console.print()

        return CommandResult(success=True)

    def _get_config_value(self, key: str) -> CommandResult:
        """特定の設定値取得"""
        parts = key.split(".")
        if len(parts) != 2:
            return CommandResult(success=False, message="キーの形式: <ファイル名>.<設定項目>")

        filename, config_key = parts
        config_path = self.config_dir / f"{filename}.conf"

        if not config_path.exists():
            return CommandResult(
                success=False, message=f"設定ファイルが見つかりません: {filename}.conf"
            )

        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == config_key:
                        return CommandResult(success=True, message=v.strip().strip('"'))

        return CommandResult(success=False, message=f"設定項目が見つかりません: {config_key}")


def main():
    command = AIConfigCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
