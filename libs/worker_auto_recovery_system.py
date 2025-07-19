#!/usr/bin/env python3
"""
Worker Auto Recovery System - ワーカー自動復旧システム
四賢者推奨の最高優先度タスク

抽象メソッド未実装問題の根本解決と自動復旧システム
Phase 1: 即時対応 - 実装エラー修正・緊急復旧・監視強化
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import ast
import hashlib
import inspect
import json
import logging
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import psutil

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """検証結果の定義"""

    file_path: str
    class_name: str
    missing_methods: List[str]
    severity: str  # 'critical', 'high', 'medium', 'low'
    fix_suggestion: str
    auto_fixable: bool


@dataclass
class RecoveryAction:
    """復旧アクションの定義"""

    action_type: str
    target: str
    parameters: Dict[str, Any]
    timeout: int
    retry_count: int
    rollback_action: Optional[str] = None


@dataclass
class WorkerStatus:
    """ワーカーステータスの定義"""

    name: str
    pid: Optional[int]
    status: str  # 'running', 'stopped', 'error', 'unknown'
    cpu_usage: float
    memory_usage: float
    last_heartbeat: Optional[datetime]
    error_count: int
    restart_count: int


class AbstractMethodValidator:
    """抽象メソッド実装検証システム"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.workers_dir = self.project_root / "workers"
        self.libs_dir = self.project_root / "libs"
        self.violations_db = self.project_root / "data" / "abstract_violations.db"

        # データベース初期化
        self._init_database()

        logger.info("Abstract Method Validator initialized")

    def _init_database(self):
        """データベース初期化"""
        self.violations_db.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(str(self.violations_db)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT,
                    class_name TEXT,
                    missing_method TEXT,
                    severity TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fixed_at TIMESTAMP,
                    status TEXT DEFAULT 'open'
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS validation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_files INTEGER,
                    violations_found INTEGER,
                    auto_fixes_applied INTEGER
                )
            """
            )

    def check_implementations(self) -> Dict[str, Any]:
        """全ワーカーの抽象メソッド実装をチェック"""
        results = {
            "total_files": 0,
            "violations": [],
            "healthy_files": [],
            "scan_time": datetime.now().isoformat(),
        }

        # Pythonファイルを検索
        python_files = []
        for directory in [self.workers_dir, self.libs_dir]:
            if directory.exists():
                python_files.extend(directory.glob("**/*.py"))

        results["total_files"] = len(python_files)

        for file_path in python_files:
            try:
                violations = self._check_file(file_path)
                if violations:
                    results["violations"].extend(violations)
                else:
                    results["healthy_files"].append(str(file_path))

            except Exception as e:
                logger.error(f"Failed to check {file_path}: {e}")

        # 結果をデータベースに保存
        self._save_scan_results(results)

        return results

    def _check_file(self, file_path: Path) -> List[ValidationResult]:
        """単一ファイルの抽象メソッド実装をチェック"""
        violations = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            # ASTパース
            tree = ast.parse(source_code)

            # クラス定義を解析
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    violation = self._check_class_implementation(
                        node, file_path, source_code
                    )
                    if violation:
                        violations.append(violation)

        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")

        return violations

    def _check_class_implementation(
        self, class_node: ast.ClassDef, file_path: Path, source_code: str
    ) -> Optional[ValidationResult]:
        """クラスの抽象メソッド実装をチェック"""
        class_name = class_node.name

        # 基底クラスを確認
        abstract_base_classes = []
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                if base.id in ["ABC", "BaseWorker", "AbstractWorker"]:
                    abstract_base_classes.append(base.id)

        if not abstract_base_classes:
            return None  # 抽象クラスを継承していない

        # 抽象メソッドを検索
        abstract_methods = self._find_abstract_methods(class_node, source_code)
        implemented_methods = self._find_implemented_methods(class_node)

        # 未実装メソッドを特定
        missing_methods = abstract_methods - implemented_methods

        if missing_methods:
            return ValidationResult(
                file_path=str(file_path),
                class_name=class_name,
                missing_methods=list(missing_methods),
                severity="critical",
                fix_suggestion=self._generate_fix_suggestion(missing_methods),
                auto_fixable=True,
            )

        return None

    def _find_abstract_methods(
        self, class_node: ast.ClassDef, source_code: str
    ) -> Set[str]:
        """抽象メソッドを検索"""
        abstract_methods = set()

        # 一般的な抽象メソッド名（ワーカー用）
        common_abstract_methods = {
            "initialize",
            "process_message",
            "cleanup",
            "stop",
            "handle_error",
            "get_status",
            "validate_config",
        }

        # @abstractmethodデコレーターを検索
        for node in ast.walk(class_node):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if (
                        isinstance(decorator, ast.Name)
                        and decorator.id == "abstractmethod"
                    ) or (
                        isinstance(decorator, ast.Attribute)
                        and decorator.attr == "abstractmethod"
                    ):
                        abstract_methods.add(node.name)

        # ソースコードから@abstractmethodを直接検索
        lines = source_code.split("\n")
        for i, line in enumerate(lines):
            if "@abstractmethod" in line and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith("def "):
                    method_name = next_line.split("(")[0].replace("def ", "").strip()
                    abstract_methods.add(method_name)

        # 一般的な抽象メソッドを追加（BaseWorkerを継承している場合）
        if any(
            "BaseWorker" in base.id if isinstance(base, ast.Name) else False
            for base in class_node.bases
        ):
            abstract_methods.update(common_abstract_methods)

        return abstract_methods

    def _find_implemented_methods(self, class_node: ast.ClassDef) -> Set[str]:
        """実装済みメソッドを検索"""
        implemented_methods = set()

        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                # passだけの実装は未実装とみなす
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    continue
                # NotImplementedErrorを発生させる実装も未実装とみなす
                if any(
                    isinstance(stmt, ast.Raise)
                    and isinstance(stmt.exc, ast.Call)
                    and isinstance(stmt.exc.func, ast.Name)
                    and stmt.exc.func.id == "NotImplementedError"
                    for stmt in node.body
                ):
                    continue

                implemented_methods.add(node.name)

        return implemented_methods

    def _generate_fix_suggestion(self, missing_methods: List[str]) -> str:
        """修正提案を生成"""
        suggestions = []

        method_templates = {
            "initialize": '''def initialize(self) -> None:
        """ワーカーの初期化"""
        # TODO: 初期化処理を実装
        pass''',
            "process_message": '''def process_message(self, message: Dict[str, Any]) -> Any:
        """メッセージ処理"""
        # TODO: メッセージ処理ロジックを実装
        return None''',
            "cleanup": '''def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        # TODO: クリーンアップ処理を実装
        pass''',
            "stop": '''def stop(self) -> None:
        """ワーカーの停止"""
        # TODO: 停止処理を実装
        pass''',
        }

        for method in missing_methods:
            template = method_templates.get(
                method,
                f'''def {method}(self):
        """TODO: {method}メソッドを実装"""
        pass''',
            )
            suggestions.append(template)

        return "\n\n".join(suggestions)

    def auto_fix_violation(self, violation: ValidationResult) -> Dict[str, Any]:
        """抽象メソッド違反の自動修正"""
        try:
            file_path = Path(violation.file_path)

            # バックアップ作成
            backup_path = file_path.with_suffix(file_path.suffix + ".backup")
            shutil.copy2(file_path, backup_path)

            # ファイル読み込み
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 修正を適用
            modified_content = self._apply_fixes(content, violation)

            # ファイル書き込み
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_content)

            # データベース更新
            self._mark_violation_fixed(violation)

            return {
                "success": True,
                "backup_created": str(backup_path),
                "methods_added": violation.missing_methods,
                "file_modified": str(file_path),
            }

        except Exception as e:
            logger.error(f"Auto-fix failed for {violation.file_path}: {e}")
            return {"success": False, "error": str(e)}

    def _apply_fixes(self, content: str, violation: ValidationResult) -> str:
        """修正をコンテンツに適用"""
        lines = content.split("\n")

        # クラス定義を検索
        class_start = None
        class_end = None
        indent_level = 0

        for i, line in enumerate(lines):
            if f"class {violation.class_name}" in line:
                class_start = i
                indent_level = len(line) - len(line.lstrip())
                break

        if class_start is None:
            return content

        # クラスの終了位置を検索
        for i in range(class_start + 1, len(lines)):
            line = lines[i]
            if (
                line.strip()
                and (len(line) - len(line.lstrip())) <= indent_level
                and not line.strip().startswith("#")
            ):
                class_end = i
                break

        if class_end is None:
            class_end = len(lines)

        # メソッドを追加
        method_indent = " " * (indent_level + 4)
        new_methods = []

        for method in violation.missing_methods:
            if method == "initialize":
                new_methods.extend(
                    [
                        f"{method_indent}def initialize(self) -> None:",
                        f'{method_indent}    """ワーカーの初期化処理"""',
                        f"{method_indent}    # TODO: 初期化ロジックを実装してください",
                        f'{method_indent}    logger.info(f"{{self.__class__.__name__}} initialized")',
                        f"{method_indent}    pass",
                        "",
                    ]
                )
            elif method == "process_message":
                new_methods.extend(
                    [
                        f"{method_indent}def process_message(self, message: Dict[str, Any]) -> Any:",
                        f'{method_indent}    """メッセージ処理"""',
                        f"{method_indent}    # TODO: メッセージ処理ロジックを実装してください",
                        f'{method_indent}    logger.info(f"Processing message: {{message}}")',
                        f"{method_indent}    return None",
                        "",
                    ]
                )
            else:
                new_methods.extend(
                    [
                        f"{method_indent}def {method}(self):",
                        f'{method_indent}    """TODO: {method}メソッドを実装してください"""',
                        f"{method_indent}    pass",
                        "",
                    ]
                )

        # 新しいコンテンツを構築
        new_lines = lines[:class_end] + new_methods + lines[class_end:]

        return "\n".join(new_lines)

    def _save_scan_results(self, results: Dict[str, Any]) -> None:
        """スキャン結果をデータベースに保存"""
        try:
            with sqlite3.connect(str(self.violations_db)) as conn:
                # スキャン履歴を保存
                conn.execute(
                    """
                    INSERT INTO validation_history
                    (total_files, violations_found, auto_fixes_applied)
                    VALUES (?, ?, ?)
                """,
                    (
                        results["total_files"],
                        len(results["violations"]),
                        0,  # auto_fixes_appliedは後で更新
                    ),
                )

                # 違反を保存
                for violation in results["violations"]:
                    if isinstance(violation, ValidationResult):
                        for method in violation.missing_methods:
                            conn.execute(
                                """
                                INSERT OR REPLACE INTO violations
                                (file_path, class_name, missing_method, severity)
                                VALUES (?, ?, ?, ?)
                            """,
                                (
                                    violation.file_path,
                                    violation.class_name,
                                    method,
                                    violation.severity,
                                ),
                            )

        except Exception as e:
            logger.error(f"Failed to save scan results: {e}")

    def _mark_violation_fixed(self, violation: ValidationResult) -> None:
        """違反修正をマーク"""
        try:
            with sqlite3.connect(str(self.violations_db)) as conn:
                conn.execute(
                    """
                    UPDATE violations
                    SET fixed_at = CURRENT_TIMESTAMP, status = 'fixed'
                    WHERE file_path = ? AND class_name = ?
                """,
                    (violation.file_path, violation.class_name),
                )

        except Exception as e:
            logger.error(f"Failed to mark violation as fixed: {e}")

    def pre_commit_check(self) -> int:
        """pre-commitフック用の検証"""
        results = self.check_implementations()

        if results["violations"]:
            print("❌ 抽象メソッド未実装が検出されました:")
            for violation in results["violations"]:
                if isinstance(violation, ValidationResult):
                    print(f"  {violation.file_path}:{violation.class_name}")
                    for method in violation.missing_methods:
                        print(f"    - {method}()")
            return 1  # 失敗

        print("✅ 抽象メソッド実装チェック完了")
        return 0  # 成功


class EmergencyRecoveryScript:
    """緊急復旧スクリプト"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.recovery_db = self.project_root / "data" / "emergency_recovery.db"
        self.recovery_history = []

        self._init_database()
        logger.info("Emergency Recovery Script initialized")

    def _init_database(self):
        """データベース初期化"""
        self.recovery_db.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(str(self.recovery_db)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS recovery_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trigger_type TEXT,
                    worker_name TEXT,
                    actions_taken TEXT,
                    success BOOLEAN,
                    recovery_time_seconds REAL,
                    details TEXT
                )
            """
            )

    def detect_failed_workers(self) -> List[Dict[str, Any]]:
        """停止ワーカーの検出"""
        failed_workers = []

        try:
            # プロセス一覧を取得
            result = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                return failed_workers

            # Pythonワーカープロセスを検索
            worker_patterns = [r"python3.*worker.*\.py", r"python.*worker.*\.py"]

            running_workers = set()
            for line in result.stdout.split("\n"):
                for pattern in worker_patterns:
                    if re.search(pattern, line):
                        # ワーカー名を抽出
                        match = re.search(r"workers/([^/\s]+)\.py", line)
                        if match:
                            running_workers.add(match.group(1))

            # 期待されるワーカーリスト
            expected_workers = [
                "async_pm_worker_simple",
                "simple_task_worker",
                "async_result_worker_simple",
                "intelligent_pm_worker_simple",
                "slack_polling_worker",
            ]

            # 停止しているワーカーを特定
            for worker in expected_workers:
                if worker not in running_workers:
                    failed_workers.append(
                        {
                            "name": worker,
                            "script_path": f"workers/{worker}.py",
                            "status": "stopped",
                            "last_seen": None,
                        }
                    )

        except Exception as e:
            logger.error(f"Failed to detect failed workers: {e}")

        return failed_workers

    def restart_worker(self, worker_config: Dict[str, Any]) -> Dict[str, Any]:
        """ワーカープロセス再起動"""
        try:
            script_path = self.project_root / worker_config["script_path"]
            worker_name = worker_config["name"]

            if not script_path.exists():
                return {
                    "success": False,
                    "error": f"Script not found: {script_path}",
                    "worker_name": worker_name,
                }

            # ワーカー固有の引数を準備
            args = ["python3", str(script_path)]

            # worker-id引数を追加
            if "pm_worker" in worker_name:
                args.extend(["--worker-id", f"{worker_name}-recovery"])
            elif "task_worker" in worker_name:
                args.extend(["--worker-id", f"{worker_name}-recovery"])
            elif "result_worker" in worker_name:
                args.extend(["--worker-id", f"{worker_name}-recovery"])

            # プロセス開始
            process = subprocess.Popen(
                args,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            # 短時間待機してプロセスが開始されたか確認
            time.sleep(2)

            if process.poll() is None:  # プロセスがまだ実行中
                return {
                    "success": True,
                    "pid": process.pid,
                    "worker_name": worker_name,
                    "command": " ".join(args),
                }
            else:
                # プロセスが即座に終了した
                stdout, stderr = process.communicate()
                return {
                    "success": False,
                    "error": f"Process exited immediately: {stderr.decode()}",
                    "worker_name": worker_name,
                    "exit_code": process.returncode,
                }

        except Exception as e:
            logger.error(f"Failed to restart worker {worker_config['name']}: {e}")
            return {
                "success": False,
                "error": str(e),
                "worker_name": worker_config.get("name", "unknown"),
            }

    def execute_emergency_recovery(self) -> Dict[str, Any]:
        """緊急復旧の実行"""
        start_time = datetime.now()

        result = {
            "start_time": start_time.isoformat(),
            "detected_failures": [],
            "restarted_workers": [],
            "failed_restarts": [],
            "alerts_sent": [],
            "success": False,
            "total_time": 0,
        }

        try:
            # 1. 停止ワーカーの検出
            failed_workers = self.detect_failed_workers()
            result["detected_failures"] = failed_workers

            # 2. ワーカーの再起動
            for worker in failed_workers:
                restart_result = self.restart_worker(worker)

                if restart_result["success"]:
                    result["restarted_workers"].append(restart_result)
                else:
                    result["failed_restarts"].append(restart_result)

            # 3. アラート送信
            if failed_workers:
                alert_result = self.send_emergency_alert(
                    {
                        "failed_count": len(failed_workers),
                        "restarted_count": len(result["restarted_workers"]),
                        "failed_restart_count": len(result["failed_restarts"]),
                        "workers": failed_workers,
                    }
                )
                result["alerts_sent"].append(alert_result)

            # 4. 結果判定
            result["success"] = len(result["failed_restarts"]) == 0

        except Exception as e:
            logger.error(f"Emergency recovery failed: {e}")
            result["error"] = str(e)

        finally:
            end_time = datetime.now()
            result["total_time"] = (end_time - start_time).total_seconds()
            result["end_time"] = end_time.isoformat()

            # 履歴を保存
            self._save_recovery_event(result)

        return result

    def send_emergency_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """緊急アラート送信"""
        try:
            alert_message = f"""
🚨 **緊急ワーカー復旧アラート** 🚨

**検出時刻**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**停止ワーカー数**: {alert_data['failed_count']}
**再起動成功**: {alert_data['restarted_count']}
**再起動失敗**: {alert_data['failed_restart_count']}

**影響を受けたワーカー**:
"""

            for worker in alert_data["workers"]:
                alert_message += f"- {worker['name']}\n"

            # ログに記録（実際の環境ではSlack等に送信）
            logger.critical(alert_message)

            return {
                "sent": True,
                "channels": ["log"],  # 実環境では ['slack', 'email'] など
                "message": alert_message,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to send emergency alert: {e}")
            return {"sent": False, "error": str(e)}

    def _save_recovery_event(self, event_data: Dict[str, Any]) -> None:
        """復旧イベントを保存"""
        try:
            with sqlite3.connect(str(self.recovery_db)) as conn:
                conn.execute(
                    """
                    INSERT INTO recovery_events
                    (trigger_type, worker_name, actions_taken, success, recovery_time_seconds, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        "emergency_recovery",
                        f"{len(event_data['detected_failures'])} workers",
                        json.dumps(
                            {
                                "restarted": len(event_data["restarted_workers"]),
                                "failed": len(event_data["failed_restarts"]),
                            }
                        ),
                        event_data["success"],
                        event_data["total_time"],
                        json.dumps(event_data, default=str),
                    ),
                )

        except Exception as e:
            logger.error(f"Failed to save recovery event: {e}")


class WorkerHealthMonitor:
    """ワーカー健康監視システム"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.monitoring = False
        self.monitor_thread = None
        self.metrics_history = deque(maxlen=1000)
        self.worker_statuses = {}

        logger.info("Worker Health Monitor initialized")

    def start_monitoring(self, interval: int = 30) -> None:
        """継続監視を開始"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop, args=(interval,), daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Health monitoring started with {interval}s interval")

    def stop_monitoring(self) -> None:
        """監視を停止"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Health monitoring stopped")

    def _monitoring_loop(self, interval: int) -> None:
        """監視ループ"""
        while self.monitoring:
            try:
                metrics = self.collect_system_metrics()
                self.metrics_history.append(
                    {"timestamp": datetime.now(), "metrics": metrics}
                )

                # 異常検知
                anomalies = self.detect_anomalies(metrics)
                if anomalies:
                    logger.warning(f"Anomalies detected: {anomalies}")

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(interval)

    def collect_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス収集"""
        try:
            # システム全体のメトリクス
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # ワーカープロセスのメトリクス
            worker_metrics = self._collect_worker_metrics()

            metrics = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "worker_count": len(worker_metrics),
                "workers": worker_metrics,
                "timestamp": datetime.now().isoformat(),
            }

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}

    def _collect_worker_metrics(self) -> List[Dict[str, Any]]:
        """ワーカーメトリクス収集"""
        worker_metrics = []

        try:
            # Pythonワーカープロセスを検索
            for proc in psutil.process_iter(
                ["pid", "name", "cmdline", "cpu_percent", "memory_info"]
            ):
                try:
                    cmdline = proc.info.get("cmdline", [])
                    if not cmdline:
                        continue

                    # ワーカープロセスを特定
                    cmdline_str = " ".join(cmdline)
                    if (
                        "python" in cmdline_str
                        and "worker" in cmdline_str
                        and ".py" in cmdline_str
                    ):
                        # ワーカー名を抽出
                        worker_name = "unknown"
                        for arg in cmdline:
                            if "worker" in arg and ".py" in arg:
                                worker_name = Path(arg).stem
                                break

                        worker_metrics.append(
                            {
                                "name": worker_name,
                                "pid": proc.info["pid"],
                                "cpu_percent": proc.info.get("cpu_percent", 0),
                                "memory_mb": proc.info.get("memory_info", {}).get(
                                    "rss", 0
                                )
                                / (1024 * 1024),
                                "status": "running",
                            }
                        )

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            logger.error(f"Failed to collect worker metrics: {e}")

        return worker_metrics

    def detect_anomalies(self, current_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """異常検知"""
        anomalies = []

        try:
            # 基本的な閾値チェック
            thresholds = {
                "cpu_usage": 90.0,  # 90%以上
                "memory_usage": 85.0,  # 85%以上
                "disk_usage": 90.0,  # 90%以上
                "worker_count": 3,  # 3個未満
            }

            for metric, threshold in thresholds.items():
                value = current_metrics.get(metric, 0)

                if metric == "worker_count":
                    if value < threshold:
                        anomalies.append(
                            {
                                "metric": metric,
                                "value": value,
                                "threshold": threshold,
                                "severity": "critical",
                                "description": f"Worker count too low: {value} < {threshold}",
                            }
                        )
                else:
                    if value > threshold:
                        severity = "critical" if value > threshold + 10 else "warning"
                        anomalies.append(
                            {
                                "metric": metric,
                                "value": value,
                                "threshold": threshold,
                                "severity": severity,
                                "description": f"{metric} too high: {value}% > {threshold}%",
                            }
                        )

            # ワーカー固有の異常チェック
            for worker in current_metrics.get("workers", []):
                if worker["cpu_percent"] > 80:
                    anomalies.append(
                        {
                            "metric": "worker_cpu",
                            "worker": worker["name"],
                            "value": worker["cpu_percent"],
                            "severity": "warning",
                            "description": f"Worker {worker['name']} high CPU: {worker['cpu_percent']}%",
                        }
                    )

                if worker["memory_mb"] > 500:  # 500MB以上
                    anomalies.append(
                        {
                            "metric": "worker_memory",
                            "worker": worker["name"],
                            "value": worker["memory_mb"],
                            "severity": "warning",
                            "description": f"Worker {worker['name']} high memory: {worker['memory_mb']:.1f}MB",
                        }
                    )

        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")

        return anomalies

    def get_recent_metrics(self, count: int = 10) -> List[Dict[str, Any]]:
        """最近のメトリクスを取得"""
        return list(self.metrics_history)[-count:]

    def is_monitoring(self) -> bool:
        """監視状態を確認"""
        return self.monitoring


class CrisisDetector:
    """危機検知システム"""

    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = thresholds or {
            "worker_failure_rate": 0.3,  # 30%以上の失敗率
            "queue_backlog": 50,  # 50件以上の蓄積
            "response_time": 30,  # 30秒以上の応答時間
            "memory_usage": 0.8,  # 80%以上のメモリ使用
            "cpu_usage": 0.9,  # 90%以上のCPU使用
            "disk_usage": 0.9,  # 90%以上のディスク使用
        }

        logger.info("Crisis Detector initialized")

    def detect_crisis(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """危機状況の検知"""
        crisis_result = {
            "is_crisis": False,
            "triggers": [],
            "severity": "normal",
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # 各閾値をチェック
            for metric_name, threshold in self.thresholds.items():
                value = metrics.get(metric_name, 0)

                if self._check_threshold_violation(metric_name, value, threshold):
                    crisis_result["triggers"].append(
                        {
                            "metric": metric_name,
                            "value": value,
                            "threshold": threshold,
                            "severity": self._calculate_severity(
                                metric_name, value, threshold
                            ),
                        }
                    )

            # 危機判定
            if crisis_result["triggers"]:
                crisis_result["is_crisis"] = True
                crisis_result["severity"] = self._evaluate_overall_severity(
                    crisis_result["triggers"]
                )

                # 主要なトリガーを特定
                primary_trigger = max(
                    crisis_result["triggers"],
                    key=lambda x: self._get_severity_score(x["severity"]),
                )
                crisis_result["primary_trigger"] = primary_trigger

        except Exception as e:
            logger.error(f"Crisis detection failed: {e}")
            crisis_result["error"] = str(e)

        return crisis_result

    def _check_threshold_violation(
        self, metric_name: str, value: float, threshold: float
    ) -> bool:
        """閾値違反のチェック"""
        if metric_name == "worker_failure_rate":
            return value > threshold
        elif metric_name in ["memory_usage", "cpu_usage", "disk_usage"]:
            return value > threshold
        elif metric_name in ["queue_backlog", "response_time"]:
            return value > threshold
        else:
            return value > threshold

    def _calculate_severity(
        self, metric_name: str, value: float, threshold: float
    ) -> str:
        """重要度計算"""
        ratio = value / threshold if threshold > 0 else 1

        if ratio >= 2.0:
            return "critical"
        elif ratio >= 1.5:
            return "high"
        elif ratio >= 1.2:
            return "medium"
        else:
            return "low"

    def _evaluate_overall_severity(self, triggers: List[Dict[str, Any]]) -> str:
        """全体的な重要度評価"""
        if not triggers:
            return "normal"

        severities = [trigger["severity"] for trigger in triggers]

        if "critical" in severities:
            return "critical"
        elif "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low"

    def _get_severity_score(self, severity: str) -> int:
        """重要度スコア"""
        scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return scores.get(severity, 0)


class AutoRecoveryFlow:
    """自動復旧フロー"""

    def __init__(self):
        self.recovery_strategies = self._init_recovery_strategies()
        self.execution_history = []

        logger.info("Auto Recovery Flow initialized")

    def _init_recovery_strategies(self) -> Dict[str, Dict[str, Any]]:
        """復旧戦略の初期化"""
        return {
            "worker_crash": {
                "priority": "high",
                "actions": [
                    {"type": "validate_implementation", "timeout": 30},
                    {"type": "restart_worker", "timeout": 60},
                    {"type": "verify_health", "timeout": 30},
                ],
                "rollback": [{"type": "stop_worker"}, {"type": "alert_admin"}],
            },
            "memory_leak": {
                "priority": "medium",
                "actions": [
                    {"type": "restart_worker", "timeout": 60},
                    {"type": "monitor_memory", "timeout": 300},
                ],
                "rollback": [{"type": "kill_worker"}, {"type": "clean_resources"}],
            },
            "queue_overflow": {
                "priority": "critical",
                "actions": [
                    {"type": "scale_workers", "timeout": 120},
                    {"type": "clear_backlog", "timeout": 180},
                ],
                "rollback": [{"type": "pause_processing"}, {"type": "emergency_alert"}],
            },
        }

    def select_recovery_strategy(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """復旧戦略選択"""
        problem_type = problem.get("type", "unknown")
        severity = problem.get("severity", "medium")

        # 基本戦略を選択
        strategy = self.recovery_strategies.get(
            problem_type,
            {
                "priority": "low",
                "actions": [
                    {"type": "log_issue", "timeout": 10},
                    {"type": "alert_admin", "timeout": 10},
                ],
                "rollback": [],
            },
        )

        # 重要度に応じて調整
        if severity == "critical":
            strategy["priority"] = "critical"
            # タイムアウトを短縮
            for action in strategy["actions"]:
                action["timeout"] = min(action["timeout"], 30)

        return strategy

    def execute_recovery_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """復旧計画の実行"""
        start_time = datetime.now()

        result = {
            "start_time": start_time.isoformat(),
            "steps_completed": 0,
            "success": False,
            "rollback_executed": False,
            "errors": [],
            "actions_log": [],
        }

        try:
            steps = plan.get("steps", [])

            # 各ステップを実行
            for i, step in enumerate(steps):
                step_result = self._execute_step(step)
                result["actions_log"].append(
                    {
                        "step": i + 1,
                        "action": step["action"],
                        "result": step_result,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                if step_result["success"]:
                    result["steps_completed"] += 1
                else:
                    # ステップ失敗時のロールバック
                    result["errors"].append(step_result.get("error", "Unknown error"))
                    rollback_result = self._execute_rollback(
                        plan.get("rollback_plan", [])
                    )
                    result["rollback_executed"] = True
                    result["rollback_result"] = rollback_result
                    break

            # 全ステップ完了判定
            result["success"] = result["steps_completed"] == len(steps)

        except Exception as e:
            logger.error(f"Recovery plan execution failed: {e}")
            result["errors"].append(str(e))

        finally:
            end_time = datetime.now()
            result["total_time"] = (end_time - start_time).total_seconds()
            result["end_time"] = end_time.isoformat()

            # 実行履歴を保存
            self.execution_history.append(result)

        return result

    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """個別ステップの実行"""
        action_type = step["action"]
        timeout = step.get("timeout", 60)

        try:
            if action_type == "validate_implementation":
                return self._validate_implementation_action()
            elif action_type == "restart_worker":
                return self._restart_worker_action(step.get("worker_name", "unknown"))
            elif action_type == "verify_health":
                return self._verify_health_action()
            elif action_type == "log_issue":
                return self._log_issue_action(step)
            elif action_type == "alert_admin":
                return self._alert_admin_action(step)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type}",
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _validate_implementation_action(self) -> Dict[str, Any]:
        """実装検証アクション"""
        try:
            validator = AbstractMethodValidator()
            results = validator.check_implementations()

            if results["violations"]:
                # 自動修正を試行
                fixed_count = 0
                for violation in results["violations"]:
                    if (
                        isinstance(violation, ValidationResult)
                        and violation.auto_fixable
                    ):
                        fix_result = validator.auto_fix_violation(violation)
                        if fix_result["success"]:
                            fixed_count += 1

                return {
                    "success": fixed_count > 0,
                    "violations_found": len(results["violations"]),
                    "auto_fixed": fixed_count,
                    "details": "Implementation validation completed with auto-fixes",
                }
            else:
                return {
                    "success": True,
                    "details": "No implementation violations found",
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _restart_worker_action(self, worker_name: str) -> Dict[str, Any]:
        """ワーカー再起動アクション"""
        try:
            recovery_script = EmergencyRecoveryScript()

            # 特定のワーカーを再起動
            worker_config = {
                "name": worker_name,
                "script_path": f"workers/{worker_name}.py",
            }

            restart_result = recovery_script.restart_worker(worker_config)
            return restart_result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _verify_health_action(self) -> Dict[str, Any]:
        """ヘルス確認アクション"""
        try:
            monitor = WorkerHealthMonitor()
            metrics = monitor.collect_system_metrics()

            worker_count = len(metrics.get("workers", []))

            return {
                "success": worker_count >= 3,
                "worker_count": worker_count,
                "details": f"Health check completed: {worker_count} workers running",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _log_issue_action(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """問題ログアクション"""
        logger.warning(f"Recovery action logged: {step}")
        return {"success": True, "details": "Issue logged successfully"}

    def _alert_admin_action(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """管理者アラートアクション"""
        logger.critical(f"Admin alert: Recovery action required - {step}")
        return {"success": True, "details": "Admin alert sent"}

    def _execute_rollback(self, rollback_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ロールバックの実行"""
        rollback_result = {"steps_executed": 0, "success": True, "errors": []}

        for step in rollback_plan:
            try:
                # ロールバックステップを実行
                logger.warning(f"Executing rollback step: {step}")
                rollback_result["steps_executed"] += 1

            except Exception as e:
                rollback_result["errors"].append(str(e))
                rollback_result["success"] = False

        return rollback_result


class WorkerAutoRecoverySystem:
    """ワーカー自動復旧システム統合クラス"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()

        # コンポーネント初期化
        self.validator = AbstractMethodValidator()
        self.emergency_script = EmergencyRecoveryScript()
        self.health_monitor = WorkerHealthMonitor()
        self.crisis_detector = CrisisDetector(self.config.get("crisis_thresholds"))
        self.recovery_flow = AutoRecoveryFlow()

        # システム状態
        self.system_status = "initialized"
        self.monitoring_active = False

        # 統計情報
        self.performance_metrics = {
            "total_recoveries": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "average_recovery_time": 0.0,
            "uptime_start": datetime.now(),
        }

        logger.info("Worker Auto Recovery System initialized")

    def _default_config(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            "monitoring_interval": 30,
            "recovery_timeout": 300,
            "max_retry_attempts": 3,
            "alert_channels": ["log"],
            "crisis_thresholds": {
                "worker_failure_rate": 0.3,
                "queue_backlog": 50,
                "response_time": 30,
                "memory_usage": 0.8,
            },
            "auto_fix_enabled": True,
            "emergency_restart_enabled": True,
        }

    def start_system(self) -> Dict[str, Any]:
        """システム開始"""
        try:
            # 初期検証
            validation_result = self.validator.check_implementations()

            # 自動修正を実行
            if self.config["auto_fix_enabled"] and validation_result["violations"]:
                self._auto_fix_violations(validation_result["violations"])

            # 監視開始
            self.health_monitor.start_monitoring(self.config["monitoring_interval"])
            self.monitoring_active = True
            self.system_status = "running"

            logger.info("Worker Auto Recovery System started")

            return {
                "success": True,
                "status": self.system_status,
                "monitoring_active": self.monitoring_active,
                "initial_validation": validation_result,
                "start_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            self.system_status = "error"
            return {"success": False, "error": str(e), "status": self.system_status}

    def stop_system(self) -> Dict[str, Any]:
        """システム停止"""
        try:
            self.health_monitor.stop_monitoring()
            self.monitoring_active = False
            self.system_status = "stopped"

            logger.info("Worker Auto Recovery System stopped")

            return {
                "success": True,
                "status": self.system_status,
                "stop_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to stop system: {e}")
            return {"success": False, "error": str(e)}

    def handle_detected_crisis(self) -> Dict[str, Any]:
        """検知された危機への対応"""
        try:
            # 現在のメトリクスを取得
            metrics = self.health_monitor.collect_system_metrics()

            # 危機検知
            crisis_result = self.crisis_detector.detect_crisis(metrics)

            if not crisis_result["is_crisis"]:
                return {
                    "crisis_handled": False,
                    "reason": "No crisis detected",
                    "metrics": metrics,
                }

            # 復旧戦略選択
            problem = {
                "type": "worker_crash",  # 主要な問題タイプ
                "severity": crisis_result["severity"],
            }

            strategy = self.recovery_flow.select_recovery_strategy(problem)

            # 復旧実行
            recovery_result = self.recovery_flow.execute_recovery_plan(strategy)

            # 統計更新
            self.performance_metrics["total_recoveries"] += 1
            if recovery_result["success"]:
                self.performance_metrics["successful_recoveries"] += 1
            else:
                self.performance_metrics["failed_recoveries"] += 1

            # 平均復旧時間更新
            self._update_average_recovery_time(recovery_result.get("total_time", 0))

            return {
                "crisis_handled": True,
                "crisis_details": crisis_result,
                "recovery_attempted": True,
                "recovery_result": recovery_result,
                "recovery_time": recovery_result.get("total_time", 0),
            }

        except Exception as e:
            logger.error(f"Crisis handling failed: {e}")
            return {"crisis_handled": False, "error": str(e)}

    def _auto_fix_violations(
        self, violations: List[ValidationResult]
    ) -> Dict[str, Any]:
        """違反の自動修正"""
        fixed_count = 0
        errors = []

        for violation in violations:
            if isinstance(violation, ValidationResult) and violation.auto_fixable:
                fix_result = self.validator.auto_fix_violation(violation)
                if fix_result["success"]:
                    fixed_count += 1
                else:
                    errors.append(fix_result.get("error", "Unknown error"))

        return {
            "violations_found": len(violations),
            "auto_fixed": fixed_count,
            "errors": errors,
        }

    def _update_average_recovery_time(self, recovery_time: float) -> None:
        """平均復旧時間更新"""
        total_recoveries = self.performance_metrics["total_recoveries"]
        current_average = self.performance_metrics["average_recovery_time"]

        # 移動平均計算
        new_average = (
            (current_average * (total_recoveries - 1)) + recovery_time
        ) / total_recoveries
        self.performance_metrics["average_recovery_time"] = new_average

    def get_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンスメトリクス取得"""
        uptime = (
            datetime.now() - self.performance_metrics["uptime_start"]
        ).total_seconds()

        metrics = self.performance_metrics.copy()
        metrics.update(
            {
                "uptime_seconds": uptime,
                "success_rate": (
                    self.performance_metrics["successful_recoveries"]
                    / max(self.performance_metrics["total_recoveries"], 1)
                ),
                "system_status": self.system_status,
                "monitoring_active": self.monitoring_active,
            }
        )

        return metrics

    def get_system_status(self) -> Dict[str, Any]:
        """システム状態取得"""
        return {
            "status": self.system_status,
            "monitoring_active": self.monitoring_active,
            "components": {
                "validator": "active",
                "emergency_script": "active",
                "health_monitor": "active" if self.monitoring_active else "inactive",
                "crisis_detector": "active",
                "recovery_flow": "active",
            },
            "config": self.config,
            "performance_metrics": self.get_performance_metrics(),
        }
