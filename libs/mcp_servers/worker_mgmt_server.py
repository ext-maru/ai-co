#!/usr/bin/env python3
"""
Worker Management MCP Server
ワーカーの管理、監視、制御を行うMCPサーバー
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import psutil

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.mcp_wrapper import MCPServer


class WorkerManagementMCPServer:
    """ワーカー管理MCPサーバー"""

    def __init__(self):
        """初期化メソッド"""
        self.server = MCPServer("workers")
        self.workers_dir = PROJECT_ROOT / "workers"
        self.setup_tools()

    def setup_tools(self):
        """setup_toolsメソッド"""
        @self.server.tool()
        async def list_workers():
            """利用可能なワーカーをリスト"""
            workers = []

            for worker_file in self.workers_dir.glob("*_worker.py"):
                worker_name = worker_file.stem

                # ワーカーの情報を取得
                try:
                    content = worker_file.read_text()
                    # ワーカータイプを抽出
                    worker_type = "unknown"
                    if "worker_type=" in content:
                        import re

                        match = re.search(r"worker_type=['\"]([^'\"]+)['\"]", content)
                        if match:
                            worker_type = match.group(1)

                    workers.append(
                        {
                            "name": worker_name,
                            "file": worker_file.name,
                            "type": worker_type,
                            "path": str(worker_file),
                        }
                    )
                except Exception as e:
                    print(f"Error reading {worker_file}: {e}")

            return {"workers_count": len(workers), "workers": workers}

        @self.server.tool()
        async def check_worker_status(worker_name: str):
            """特定のワーカーの状態を確認"""
            # プロセスを検索
            running = False
            pid = None
            cpu_percent = 0
            memory_mb = 0

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = proc.info.get("cmdline", [])
                    if cmdline and f"{worker_name}_worker.py" in " ".join(cmdline):
                        running = True
                        pid = proc.info["pid"]
                        cpu_percent = proc.cpu_percent(interval=1)
                        memory_mb = proc.memory_info().rss / 1024 / 1024
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # ログファイルをチェック
            log_file = PROJECT_ROOT / "logs" / f"{worker_name}_worker.log"
            last_log_time = None
            last_log_lines = []

            if log_file.exists():
                try:
                    last_log_time = log_file.stat().st_mtime
                    with open(log_file, "r") as f:
                        lines = f.readlines()
                        last_log_lines = lines[-10:]  # 最後の10行
                except Exception as e:
                    print(f"Error reading log: {e}")

            return {
                "worker": worker_name,
                "running": running,
                "pid": pid,
                "cpu_percent": cpu_percent,
                "memory_mb": round(memory_mb, 2),
                "last_log_time": last_log_time,
                "recent_logs": last_log_lines,
            }

        @self.server.tool()
        async def restart_worker(worker_name: str):
            """ワーカーを再起動"""
            # まず停止
            stopped = False
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = proc.info.get("cmdline", [])
                    if cmdline and f"{worker_name}_worker.py" in " ".join(cmdline):
                        proc.terminate()
                        proc.wait(timeout=5)
                        stopped = True
                        break
                except Exception as e:
                    print(f"Error stopping worker: {e}")

            # 起動
            worker_file = self.workers_dir / f"{worker_name}_worker.py"
            if worker_file.exists():
                try:
                    subprocess.Popen(
                        ["python3", str(worker_file)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        start_new_session=True,
                    )

                    # 少し待って確認
                    await asyncio.sleep(2)

                    # 状態確認
                    status = await self.check_worker_status(worker_name)

                    return {
                        "worker": worker_name,
                        "stopped": stopped,
                        "started": status["running"],
                        "message": (
                            "Worker restarted successfully"
                            if status["running"]
                            else "Failed to start worker"
                        ),
                    }
                except Exception as e:
                    return {
                        "worker": worker_name,
                        "error": str(e),
                        "message": "Failed to restart worker",
                    }
            else:
                return {
                    "worker": worker_name,
                    "error": "Worker file not found",
                    "message": f"{worker_name}_worker.py not found",
                }

        @self.server.tool()
        async def get_worker_metrics():
            """全ワーカーのメトリクスを取得"""
            metrics = {
                "total_workers": 0,
                "running_workers": 0,
                "total_cpu_percent": 0,
                "total_memory_mb": 0,
                "workers": [],
            }

            # 全ワーカーをチェック
            workers = await self.list_workers()

            for worker_info in workers["workers"]:
                worker_name = worker_info["name"].replace("_worker", "")
                status = await self.check_worker_status(worker_name)

                metrics["total_workers"] += 1
                if status["running"]:
                    metrics["running_workers"] += 1
                    metrics["total_cpu_percent"] += status["cpu_percent"]
                    metrics["total_memory_mb"] += status["memory_mb"]

                metrics["workers"].append(
                    {
                        "name": worker_name,
                        "running": status["running"],
                        "cpu_percent": status["cpu_percent"],
                        "memory_mb": status["memory_mb"],
                    }
                )

            return metrics

    async def process_request(self, request_json):
        """process_request処理メソッド"""
        request = json.loads(request_json)
        return await self.server.handle_request(request)


# CLI interface
if __name__ == "__main__":
    import asyncio

    server = WorkerManagementMCPServer()

    # Read request from stdin
    request = input()

    # Process and return result
    result = asyncio.run(server.process_request(request))
    print(json.dumps(result))
