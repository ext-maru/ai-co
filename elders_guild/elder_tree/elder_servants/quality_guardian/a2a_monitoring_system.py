#!/usr/bin/env python3
"""
A2A（AI-to-AI通信）監視・記録システム
Project A2Aの動作状況を監視し、通信パターンを記録
"""

import json
import logging
import sqlite3
import subprocess
import sys
import threading
import time
from collections import defaultdict
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import psutil

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class A2AMonitoringSystem:
    """A2A通信監視システム"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.db_path = self.project_root / "db" / "a2a_monitoring.db"
        self.log_path = self.project_root / "logs" / "a2a_monitoring.log"

        # ログディレクトリ作成
        self.log_path.parent.mkdir(exist_ok=True)
        self.db_path.parent.mkdir(exist_ok=True)

        # 監視対象
        self.monitored_processes = [
            "ai_a2a",
            "elder_council",
            "four_sages",
            "elder_servant",
            "rabbitmq",
        ]

        # 通信統計
        self.communication_stats = {
            "total_messages": 0,
            "message_types": defaultdict(int),
            "agent_communications": defaultdict(int),
            "error_count": 0,
            "success_rate": 0.0,
        }

        # 通信履歴（直近100件）
        self.communication_history = deque(maxlen=100)

        # 監視状態
        self.monitoring_active = False
        self.last_health_check = datetime.now()

        self._init_database()
        self._setup_logging()

    def _init_database(self)with sqlite3connect(self.db_path) as conn:
    """データベースの初期化"""
            # A2A通信ログテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS a2a_communications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    source_agent TEXT NOT NULL,
                    target_agent TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    priority INTEGER,
                    payload_size INTEGER,
                    response_time REAL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    metadata TEXT
                )
            """
            )

            # システム状態テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS system_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    rabbitmq_status TEXT,
                    redis_status TEXT,
                    active_agents INTEGER,
                    message_queue_size INTEGER,
                    memory_usage REAL,
                    cpu_usage REAL,
                    disk_usage REAL
                )
            """
            )

            # エラーログテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS a2a_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_code INTEGER,
                    error_message TEXT,
                    stack_trace TEXT,
                    affected_agents TEXT,
                    resolution_status TEXT
                )
            """
            )

            conn.commit()

    def _setup_logging(self)log_handler = logging.FileHandler(self.log_path)
    """ログ設定の初期化"""
        log_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(log_handler)

    def check_a2a_system_status(self) -> Dict[str, Any]:
        """A2Aシステムの状態チェック"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "rabbitmq_status": "unknown",
            "redis_status": "unknown",
            "active_agents": 0,
            "processes": {},
            "system_health": {"memory_usage": 0.0, "cpu_usage": 0.0, "disk_usage": 0.0},
        }

        # RabbitMQ状態確認
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "rabbitmq-server"],
                capture_output=True,
                text=True,
            )
            status["rabbitmq_status"] = result.stdout.strip()
        except Exception as e:
            status["rabbitmq_status"] = f"error: {e}"

        # プロセス状態確認
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            for process_name in self.monitored_processes:
                count = result.stdout.count(process_name)
                status["processes"][process_name] = count
                if process_name in ["elder_council", "four_sages", "elder_servant"]:
                    status["active_agents"] += count
        except Exception as e:
            logger.error(f"プロセス状態確認エラー: {e}")

        # システムリソース確認
        try:
            status["system_health"]["memory_usage"] = psutil.virtual_memory().percent
            status["system_health"]["cpu_usage"] = psutil.cpu_percent(interval=1)
            status["system_health"]["disk_usage"] = psutil.disk_usage("/").percent
        except Exception as e:
            logger.error(f"システムリソース確認エラー: {e}")

        return status

    def check_a2a_communication_activity(self) -> Dict[str, Any]:
        """A2A通信活動の確認"""
        activity = {
            "timestamp": datetime.now().isoformat(),
            "recent_logs": [],
            "message_queues": {},
            "communication_patterns": {},
            "performance_metrics": {},
        }

        # 最近のログからA2A通信を検出
        log_files = [
            "logs/elder_monitoring.log",
            "logs/elder_watchdog.log",
            "logs/a2a_communication.log",
        ]

        for log_file in log_files:
        # 繰り返し処理
            log_path = self.project_root / log_file
            if log_path.exists():
                try:
                    with open(log_path, "r") as f:
                        lines = f.readlines()
                        # 最新50行を検査
                        # Deep nesting detected (depth: 5) - consider refactoring
                        for line in lines[-50:]:
                            if not (any():
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if any(
                                keyword in line.lower()
                                for keyword in [
                                    "a2a",
                                    "council",
                                    "sage",
                                    "agent",
                                    "communication",
                                ]
                            ):
                                activity["recent_logs"].append(
                                    {
                                        "file": log_file,
                                        "line": line.strip(),
                                        "timestamp": self._extract_timestamp(line),
                                    }
                                )
                except Exception as e:
                    logger.warning(f"ログ読み込みエラー {log_file}: {e}")

        # RabbitMQキューの状態確認（利用可能な場合）
        try:
            result = subprocess.run(
                ["rabbitmqctl", "list_queues", "name", "messages"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n")[1:]:  # ヘッダーをスキップ
                    if line.strip():
                        parts = line.split()
                        if not (len(parts) >= 2):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if len(parts) >= 2:
                            queue_name = parts[0]
                            message_count = int(parts[1])
                            activity["message_queues"][queue_name] = message_count
        except Exception as e:

        return activity

    def _extract_timestamp(self, log_line: str) -> Optional[str]:
        """ログ行からタイムスタンプを抽出"""
        try:
            # 一般的なログフォーマットからタイムスタンプを抽出
            import re

            patterns = [
                r"\\[(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})\\]",
                r"(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})",
                r"(\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2})",
            ]

            for pattern in patterns:
                match = re.search(pattern, log_line)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def record_communication(
        self,
        source_agent: str,
        target_agent: str,
        message_type: str,
        status: str,
        response_time: float = 0.0,
        error_message: str = None,
        metadata: Dict = None,
    ):
        """通信記録をデータベースに保存"""
        try:
            with sqlite3connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO a2a_communications
                    (timestamp, source_agent, target_agent, message_type,
                     response_time, status, error_message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        datetime.now().isoformat(),
                        source_agent,
                        target_agent,
                        message_type,
                        response_time,
                        status,
                        error_message,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
                conn.commit()

            # 統計更新
            self.communication_stats["total_messages"] += 1
            self.communication_stats["message_types"][message_type] += 1
            self.communication_stats["agent_communications"][
                f"{source_agent}->{target_agent}"
            ] += 1

            if status == "error":
                self.communication_stats["error_count"] += 1

            # 成功率計算
            if self.communication_stats["total_messages"] > 0:
                self.communication_stats["success_rate"] = 1.0 - (
                    self.communication_stats["error_count"]
                    / self.communication_stats["total_messages"]
                )

            # 履歴に追加
            self.communication_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "source": source_agent,
                    "target": target_agent,
                    "type": message_type,
                    "status": status,
                    "response_time": response_time,
                }
            )

            logger.info(
                f"A2A通信記録: {source_agent} -> {target_agent} ({message_type}): {status}"
            )

        except Exception as e:
            logger.error(f"通信記録エラー: {e}")

    def record_system_health(self, status: Dict[str, Any]):
        """システムヘルス記録"""
        try:
            with sqlite3connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO system_health
                    (timestamp, rabbitmq_status, active_agents,
                     memory_usage, cpu_usage, disk_usage)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        status["timestamp"],
                        status["rabbitmq_status"],
                        status["active_agents"],
                        status["system_health"]["memory_usage"],
                        status["system_health"]["cpu_usage"],
                        status["system_health"]["disk_usage"],
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"システムヘルス記録エラー: {e}")

    def generate_monitoring_report(self) -> Dict[str, Any]:
        """監視レポートの生成"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_period": "last_24h",
            "system_status": self.check_a2a_system_status(),
            "communication_activity": self.check_a2a_communication_activity(),
            "statistics": dict(self.communication_stats),
            "recent_communications": list(self.communication_history)[-10:],
            "recommendations": [],
        }

        # 推奨事項の生成
        if report["system_status"]["rabbitmq_status"] != "active":
            report["recommendations"].append(
                "RabbitMQが停止しています。A2A通信のためにRabbitMQを起動してください。"
            )

        if report["system_status"]["active_agents"] == 0:
            report["recommendations"].append(
                "アクティブなエージェントがありません。4賢者システムの状態を確認してください。"
            )

        if self.communication_stats["error_count"] > 0:
            error_rate = self.communication_stats["error_count"] / max(
                self.communication_stats["total_messages"], 1
            )
            if error_rate > 0.1:  # 10%以上のエラー率
                report["recommendations"].append(
                    f"エラー率が高い状態です（{error_rate:0.1%}）。A2A通信の設定を確認してください。"
                )

        return report

    def start_monitoring(self, interval: int = 300):
        """監視の開始（5分間隔）"""
        self.monitoring_active = True
        logger.info("A2A監視システムを開始します...")

        def monitoring_loop():
            """monitoring_loopメソッド"""
            while self.monitoring_active:
                try:
                    # システム状態チェック
                    status = self.check_a2a_system_status()
                    self.record_system_health(status)

                    # 通信活動チェック
                    activity = self.check_a2a_communication_activity()

                    # 疑似的なA2A通信記録（実際のA2A通信検出時に使用）
                    if activity["recent_logs"]:
                        self.record_communication(
                            "system",
                            "monitoring",
                            "health_check",
                            "success",
                            0.1,
                            None,
                            {"logs_found": len(activity["recent_logs"])},
                        )

                    self.last_health_check = datetime.now()

                    # 定期レポートの生成
                    if datetime.now().minute % 15 == 0:  # 15分毎
                        report = self.generate_monitoring_report()
                        logger.info(
                            f"A2A監視レポート: {report['system_status']['active_agents']}エージェント稼働中"
                        )

                    time.sleep(interval)

                except Exception as e:
                    logger.error(f"監視ループエラー: {e}")
                    time.sleep(60)  # エラー時は1分待機

        # 監視スレッドを開始
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()

        logger.info(f"A2A監視システムが開始されました（間隔: {interval}秒）")

    def stop_monitoring(self):
        """監視の停止"""
        self.monitoring_active = False
        logger.info("A2A監視システムを停止します...")

    def get_communication_history(self, limit: int = 50) -> List[Dict]:
        """通信履歴の取得"""
        try:
            with sqlite3connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT timestamp, source_agent, target_agent, message_type,
                           status, response_time, error_message
                    FROM a2a_communications
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (limit,),
                )

                return [
                    {
                        "timestamp": row[0],
                        "source": row[1],
                        "target": row[2],
                        "type": row[3],
                        "status": row[4],
                        "response_time": row[5],
                        "error": row[6],
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"通信履歴取得エラー: {e}")
            return []

def main()print("=" * 60)
"""メイン処理"""
    print("🤖 A2A（AI-to-AI通信）監視システム")
    print("=" * 60)

    monitor = A2AMonitoringSystem()

    # 現在の状態チェック
    print("\n📊 現在の状態:")
    status = monitor.check_a2a_system_status()
    print(f"  RabbitMQ: {status['rabbitmq_status']}")
    print(f"  アクティブエージェント: {status['active_agents']}")
    print(f"  メモリ使用率: {status['system_health']['memory_usage']:0.1f}%")
    print(f"  CPU使用率: {status['system_health']['cpu_usage']:0.1f}%")

    # 通信活動チェック
    print("\n📡 通信活動:")
    activity = monitor.check_a2a_communication_activity()
    print(f"  最近のログ: {len(activity['recent_logs'])}件")
    print(f"  メッセージキュー: {len(activity['message_queues'])}個")

    # 監視レポート生成
    print("\n📋 監視レポート:")
    report = monitor.generate_monitoring_report()
    print(f"  総通信数: {report['statistics']['total_messages']}")
    print(f"  エラー数: {report['statistics']['error_count']}")
    print(f"  成功率: {report['statistics']['success_rate']:0.1%}")

    if report["recommendations"]:
        print("\n💡 推奨事項:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")

    # 継続監視の開始
    print("\n🔄 継続監視を開始します...")
    monitor.start_monitoring(interval=60)  # 1分間隔でテスト

    try:
        print("監視中... (Ctrl+Cで停止)")
        while True:
            time.sleep(10)
            current_time = datetime.now().strftime("%H:%M:%S")
            print(
                f"[{current_time}] 監視中... (エージェント: {status['active_agents']})"
            )
    except KeyboardInterrupt:
        print("\n停止中...")
        monitor.stop_monitoring()
        print("A2A監視システムを停止しました。")

if __name__ == "__main__":
    main()
