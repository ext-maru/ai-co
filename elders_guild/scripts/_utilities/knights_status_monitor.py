#!/usr/bin/env python3
"""
Knights Status Monitor - 騎士団状況監視システム
GitHub Actions実行状況とローカル騎士団システムの統合監視
"""

import json
import subprocess
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import pika

# パス設定
sys.path.append(str(Path(__file__).parent.parent))


class KnightsStatusMonitor:
    """騎士団統合状況監視システム"""

    def __init__(self):
        self.status_report = {
            "timestamp": datetime.now().isoformat(),
            "github_actions": {},
            "local_knights": {},
            "workers": {},
            "rabbitmq": {},
            "overall_health": "unknown",
        }

    def check_github_actions_status(self):
        """GitHub Actions の実行状況をチェック"""
        try:
            # GitHub CLI を使用してワークフロー状況を確認
            result = subprocess.run(
                [
                    "gh",
                    "run",
                    "list",
                    "--workflow=incident-knights-autofix.yml",
                    "--limit",
                    "5",
                    "--json",
                    "status,conclusion,name,event,createdAt",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                runs = json.loads(result.stdout)
                self.status_report["github_actions"] = {
                    "status": "accessible",
                    "recent_runs": len(runs),
                    "latest_runs": runs[:3] if runs else [],
                    "last_check": datetime.now().isoformat(),
                }
            else:
                self.status_report["github_actions"] = {
                    "status": "cli_error",
                    "error": result.stderr,
                    "last_check": datetime.now().isoformat(),
                }

        except subprocess.TimeoutExpired:
            self.status_report["github_actions"] = {
                "status": "timeout",
                "error": "GitHub CLI command timed out",
                "last_check": datetime.now().isoformat(),
            }
        except FileNotFoundError:
            self.status_report["github_actions"] = {
                "status": "cli_not_found",
                "error": "GitHub CLI not installed or not authenticated",
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            self.status_report["github_actions"] = {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    def check_local_knights_script(self):
        """ローカル騎士団スクリプトの動作確認"""
        try:
            # 騎士団スクリプトのクイックヘルスチェック実行
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/knights-github-action.py",
                    "analyze",
                    "--output-format",
                    "json",
                    "--quick",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                try:
                    report = json.loads(result.stdout)
                    self.status_report["local_knights"] = {
                        "status": "operational",
                        "script_executable": True,
                        "dependencies_available": True,
                        "last_analysis": {
                            "total_issues": report.get("summary", {}).get(
                                "total_issues", 0
                            ),
                            "timestamp": report.get("timestamp", "unknown"),
                        },
                    }
                except json.JSONDecodeError:
                    self.status_report["local_knights"] = {
                        "status": "output_error",
                        "script_executable": True,
                        "dependencies_available": False,
                        "error": "Invalid JSON output",
                    }
            else:
                self.status_report["local_knights"] = {
                    "status": "execution_error",
                    "script_executable": False,
                    "error": result.stderr,
                    "stdout": result.stdout,
                }

        except subprocess.TimeoutExpired:
            self.status_report["local_knights"] = {
                "status": "timeout",
                "script_executable": False,
                "error": "Script execution timed out",
            }
        except Exception as e:
            self.status_report["local_knights"] = {
                "status": "error",
                "script_executable": False,
                "error": str(e),
            }

    def check_workers_status(self):
        """ワーカープロセスの状況確認"""
        worker_processes = {}

        # 実行中のプロセスを確認
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = " ".join(proc.info["cmdline"]) if proc.info["cmdline"] else ""

                # ワーカープロセスを検出
                if "worker.py" in cmdline or "worker" in proc.info["name"]:
                    if "python" in cmdline and "workers/" in cmdline:
                        # ワーカーファイル名を抽出
                        # Deep nesting detected (depth: 5) - consider refactoring
                        for part in proc.info["cmdline"]:
                            if not ("workers/" in part and ".py" in part):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if "workers/" in part and ".py" in part:
                                worker_name = Path(part).name
                                worker_processes[worker_name] = {
                                    "pid": proc.info["pid"],
                                    "status": "running",
                                    "cmdline": cmdline,
                                }
                                break

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 期待されるワーカーファイルをチェック
        expected_workers = [
            "enhanced_task_worker.py",
            "intelligent_pm_worker_simple.py",
            "async_result_worker_simple.py",
        ]

        for worker in expected_workers:
            if worker not in worker_processes:
                worker_processes[worker] = {"status": "stopped"}

        self.status_report["workers"] = {
            "total_expected": len(expected_workers),
            "running_count": len(
                [w for w in worker_processes.values() if w.get("status") == "running"]
            ),
            "processes": worker_processes,
        }

    def check_rabbitmq_status(self):
        """RabbitMQ接続と キュー状況確認"""
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
            channel = connection.channel()

            # 主要キューの状況確認
            queues = ["ai_tasks", "ai_pm", "ai_results", "dialog_task_queue"]
            queue_status = {}

            for queue_name in queues:
                try:
                    method = channel.queue_declare(queue=queue_name, passive=True)
                    queue_status[queue_name] = {
                        "exists": True,
                        "message_count": method.method.message_count,
                    }
                except Exception as e:
                    queue_status[queue_name] = {"exists": False, "error": str(e)}

            connection.close()

            self.status_report["rabbitmq"] = {
                "status": "connected",
                "queues": queue_status,
            }

        except Exception as e:
            self.status_report["rabbitmq"] = {
                "status": "connection_failed",
                "error": str(e),
            }

    def calculate_overall_health(self):
        """総合的な健康状態を判定"""
        issues = []

        # GitHub Actions 状況評価
        if self.status_report["github_actions"].get("status") not in ["accessible"]:
            issues.append("GitHub Actions not accessible")

        # ローカル騎士団評価
        if self.status_report["local_knights"].get("status") != "operational":
            issues.append("Local knights script not operational")

        # ワーカー評価
        workers = self.status_report["workers"]
        if workers["running_count"] < workers["total_expected"]:
            issues.append(
                f"Only {workers['running_count']}/{workers['total_expected']} workers running"
            )

        # RabbitMQ評価
        if self.status_report["rabbitmq"].get("status") != "connected":
            issues.append("RabbitMQ connection failed")

        # 総合判定
        if not issues:
            self.status_report["overall_health"] = "healthy"
        elif len(issues) <= 2:
            self.status_report["overall_health"] = "warning"
        else:
            self.status_report["overall_health"] = "critical"

        self.status_report["issues"] = issues

    def generate_report(self, format_type="json"):
        """状況レポートを生成"""
        # 各種チェックを実行
        self.check_github_actions_status()
        self.check_local_knights_script()
        self.check_workers_status()
        self.check_rabbitmq_status()
        self.calculate_overall_health()

        if format_type == "json":
            return json.dumps(self.status_report, indent=2)
        elif format_type == "text":
            return self.format_text_report()
        else:
            return self.status_report

    def format_text_report(self):
        """テキスト形式のレポート生成"""
        report = []

        # ヘッダー
        report.append("🛡️ Knights Status Monitor Report")
        report.append("=" * 50)
        report.append(f"Generated: {self.status_report['timestamp']}")
        report.append(f"Overall Health: {self.status_report['overall_health'].upper()}")
        report.append("")

        # GitHub Actions
        gh = self.status_report["github_actions"]
        report.append("📡 GitHub Actions:")
        report.append(f"  Status: {gh.get('status', 'unknown')}")
        if "recent_runs" in gh:
            report.append(f"  Recent runs: {gh['recent_runs']}")
        if "error" in gh:
            report.append(f"  Error: {gh['error']}")
        report.append("")

        # Local Knights
        lk = self.status_report["local_knights"]
        report.append("⚔️ Local Knights:")
        report.append(f"  Status: {lk.get('status', 'unknown')}")
        report.append(f"  Script executable: {lk.get('script_executable', False)}")
        if "last_analysis" in lk:
            report.append(
                f"  Last analysis: {lk['last_analysis']['total_issues']} issues found"
            )
        if "error" in lk:
            report.append(f"  Error: {lk['error']}")
        report.append("")

        # Workers
        w = self.status_report["workers"]
        report.append("👥 Workers:")
        report.append(f"  Running: {w['running_count']}/{w['total_expected']}")
        for worker, status in w["processes"].items():
            emoji = "✅" if status.get("status") == "running" else "❌"
            report.append(f"  {emoji} {worker}: {status.get('status', 'unknown')}")
        report.append("")

        # RabbitMQ
        rmq = self.status_report["rabbitmq"]
        report.append("🐰 RabbitMQ:")
        report.append(f"  Status: {rmq.get('status', 'unknown')}")
        if "queues" in rmq:
            for queue, info in rmq["queues"].items():
                if info.get("exists"):
                    report.append(
                        f"  📬 {queue}: {info.get('message_count', 0)} messages"
                    )
                else:
                    report.append(f"  ❌ {queue}: not found")
        report.append("")

        # Issues
        if self.status_report.get("issues"):
            report.append("⚠️ Issues Found:")
            for issue in self.status_report["issues"]:
                report.append(f"  • {issue}")
        else:
            report.append("✅ No issues detected")

        return "\n".join(report)


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Knights Status Monitor")
    parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )
    parser.add_argument("--save", help="Save report to file")

    args = parser.parse_args()

    monitor = KnightsStatusMonitor()
    report = monitor.generate_report(args.format)

    print(report)

    if args.save:
        with open(args.save, "w") as f:
            f.write(report)
        print(f"\n📄 Report saved to: {args.save}")


if __name__ == "__main__":
    main()
