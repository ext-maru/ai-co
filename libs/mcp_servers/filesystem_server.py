#!/usr/bin/env python3
"""
Elders Guild FileSystem MCP Server
プロジェクト構造を理解し、適切なファイル配置を行うMCPサーバー
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Elders Guildプロジェクトルート
PROJECT_ROOT = Path("/home/aicompany/ai_co")

# ファイル配置ルール
FILE_PLACEMENT_RULES = {
    r".*_worker\.py$": "workers",
    r".*_manager\.py$": "libs",
    r"ai-.*": "scripts",
    r".*\.sh$": "scripts",
    r".*\.conf$": "config",
    r".*\.json$": "config",
    r".*\.html$": "web",
    r"test_.*\.py$": "tests/unit",
}


class AICompanyFileSystemServer:
    """Elders Guild専用FileSystem MCPサーバー"""

    def __init__(self):
        """初期化メソッド"""
        self.server = Server("ai-company-filesystem")
        self.setup_tools()

    def setup_tools(self):
        """ツールの定義"""

        @self.server.tool()
        async def create_worker(name: str, worker_type: str, content: str) -> str:
            """新しいワーカーを作成"""
            file_path = PROJECT_ROOT / "workers" / f"{name}_worker.py"

            # ワーカーテンプレートを適用
            if not content:
                content = self._generate_worker_template(name, worker_type)

            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(content)

            # 実行権限を付与
            file_path.chmod(0o755)

            return f"Worker created: {file_path}"

        @self.server.tool()
        async def create_manager(name: str, content: str) -> str:
            """新しいマネージャーを作成"""
            file_path = PROJECT_ROOT / "libs" / f"{name}_manager.py"

            if not content:
                content = self._generate_manager_template(name)

            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(content)

            return f"Manager created: {file_path}"

        @self.server.tool()
        async def deploy_file(file_name: str, content: str) -> str:
            """ファイルを適切な場所に自動配置"""
            import re

            # ファイル名からディレクトリを判定
            target_dir = None
            for pattern, directory in FILE_PLACEMENT_RULES.items():
                if re.match(pattern, file_name):
                    target_dir = directory
                    break

            if not target_dir:
                target_dir = "output"  # デフォルト

            file_path = PROJECT_ROOT / target_dir / file_name
            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(content)

            # シェルスクリプトの場合は実行権限を付与
            if file_name.endswith(".sh"):
                file_path.chmod(0o755)

            return f"File deployed: {file_path}"

        @self.server.tool()
        async def get_project_structure() -> str:
            """プロジェクト構造を取得"""
            structure = []

            def scan_directory(path:
                """scan_directoryメソッド"""
            Path, prefix: str = ""):
                for item in sorted(path.iterdir()):
                    if item.name.startswith(".") and item.name not in [
                        ".env",
                        ".gitignore",
                    ]:
                        continue

                    if item.is_dir() and item.name not in [
                        "venv",
                        "__pycache__",
                        ".git",
                    ]:
                        structure.append(f"{prefix}📁 {item.name}/")
                        scan_directory(item, prefix + "  ")
                    elif item.is_file():
                        structure.append(f"{prefix}📄 {item.name}")

            scan_directory(PROJECT_ROOT)
            return "\n".join(structure)

        @self.server.tool()
        async def organize_files() -> str:
            """既存ファイルを整理"""
            import re

            moved_files = []

            # outputディレクトリのファイルをチェック
            output_dir = PROJECT_ROOT / "output"
            if output_dir.exists():
                for file_path in output_dir.iterdir():
                    if file_path.is_file():
                        for pattern, directory in FILE_PLACEMENT_RULES.items():
                            if re.match(pattern, file_path.name):
                                target_path = PROJECT_ROOT / directory / file_path.name
                                target_path.parent.mkdir(exist_ok=True)
                                file_path.rename(target_path)
                                moved_files.append(f"{file_path.name} → {directory}/")
                                break

            if moved_files:
                return f"Organized files:\n" + "\n".join(moved_files)
            else:
                return "No files to organize"

    def _generate_worker_template(self, name: str, worker_type: str) -> str:
        """ワーカーテンプレートを生成"""
        return f'''#!/usr/bin/env python3
"""
Elders Guild {name.title()} Worker
自動生成: MCP FileSystem Server
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseWorker, get_config, EMOJI
import logging


class {name.title()}Worker(BaseWorker):
    """
    {name.title()} ワーカー
    タイプ: {worker_type}
    """

    def __init__(self):
        super().__init__(worker_type='{worker_type}')
        self.config = get_config()
        self.logger.info(f"{{EMOJI['robot']}} {name.title()}Worker initialized")

    def process_message(self, ch, method, properties, body):
        """メッセージ処理"""
        task_id = body.get('task_id', 'unknown')

        try:
            self.logger.info(f"Processing task: {{task_id}}")

            # TODO: 実装
            result = self._process_task(body)

            # 成功通知
            self._notify_completion(task_id, result)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            self.handle_error(e, f"process_message for {{task_id}}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _process_task(self, body: dict) -> dict:
        """タスク処理のメインロジック"""
        # TODO: 実装
        return {{"status": "success"}}

    def _notify_completion(self, task_id: str, result: dict):
        """完了通知"""
        try:
            from libs.slack_notifier import SlackNotifier
            notifier = SlackNotifier()
            notifier.send_message(
                f"{{EMOJI['check']}} Task {{task_id}} completed: {{result.get('status')}}"
            )
        except Exception as e:
            self.logger.warning(f"Slack notification failed: {{e}}")


if __name__ == "__main__":
    worker = {name.title()}Worker()
    worker.run()
'''

    def _generate_manager_template(self, name: str) -> str:
        """マネージャーテンプレートを生成"""
        return f'''#!/usr/bin/env python3
"""
Elders Guild {name.title()} Manager
自動生成: MCP FileSystem Server
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager, get_config
import logging


class {name.title()}Manager(BaseManager):
    """
    {name.title()} マネージャー
    """

    def __init__(self):
        super().__init__(manager_type='{name}')
        self.config = get_config()
        self.logger = logging.getLogger(f'ai_company.{{name}}_manager')

    def initialize(self):
        """初期化処理"""
        self.logger.info(f"{{name.title()}}Manager initialized")

    # TODO: マネージャー固有のメソッドを実装


# シングルトンインスタンス
{name}_manager = {name.title()}Manager()
'''

    async def run(self):
        """サーバーを起動"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)


if __name__ == "__main__":
    server = AICompanyFileSystemServer()
    asyncio.run(server.run())
