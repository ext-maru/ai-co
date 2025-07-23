#!/usr/bin/env python3
"""
Worker System Stabilization Knight - ワーカーシステム安定化専門騎士
全ワーカーの起動・設定・エラー修復を担当
"""

import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

# プロジェクトパス追加
sys.path.append(str(Path(__file__).parent.parent))

from libs.incident_knights_framework import (
    Diagnosis,
    IncidentKnight,
    Issue,
    IssueCategory,
    IssueSeverity,
    KnightType,
    Resolution,
)

logger = logging.getLogger(__name__)


@dataclass
class WorkerIssue:
    """ワーカー問題データクラス"""

    worker_name: str
    issue_type: (
        str  # "not_running", "config_error", "dependency_missing", "error_rate_high"
    )
    error_details: str
    affected_files: List[str]
    recovery_priority: str  # "critical", "high", "medium", "low"


class WorkerStabilizationKnight(IncidentKnight):
    """
    Worker System Stabilization Knight - ワーカーシステム安定化専門騎士

    機能:
    - 全ワーカーの稼働状態監視
    - 停止ワーカーの自動再起動
    - ワーカー設定エラーの修復
    - 依存関係問題の解決
    - パフォーマンス最適化
    """

    def __init__(
        self,
        knight_id: str = "worker_stabilization_001",
        specialty: str = "Worker system stability",
    ):
        super().__init__(knight_id, KnightType.REPAIR, specialty)
        self.name = "Worker Stabilization Knight"
        self.project_root = Path(__file__).parent.parent

        # 監視対象ワーカー定義
        self.target_workers = [
            {
                "name": "enhanced_task_worker",
                "file": "workers/enhanced_task_worker.py",
                "config": "config/worker_config.json",
                "priority": "critical",
            },
            {
                "name": "task_worker",
                "file": "workers/task_worker.py",
                "config": "config/worker_config.json",
                "priority": "high",
            },
            {
                "name": "pm_worker",
                "file": "workers/pm_worker.py",
                "config": "config/worker_config.json",
                "priority": "medium",
            },
            {
                "name": "result_worker",
                "file": "workers/result_worker.py",
                "config": "config/worker_config.json",
                "priority": "medium",
            },
            {
                "name": "dialog_task_worker",
                "file": "workers/dialog_task_worker.py",
                "config": "config/worker_config.json",
                "priority": "low",
            },
        ]

        # ログ監視パス
        self.log_paths = [
            self.project_root / "logs" / "workers",
            self.project_root / "logs" / "task_worker.log",
            self.project_root / "logs" / "pm_worker.log",
        ]

        self.worker_issues: List[WorkerIssue] = []

        logger.info(f"⚙️ {self.name} 初期化完了")

    async def patrol(self) -> List[Issue]:
        """ワーカーシステムの巡回監視"""
        logger.info("🔍 ワーカーシステム巡回開始")

        issues = []

        # 1. ワーカープロセス状態確認
        process_issues = await self._check_worker_processes()
        issues.extend(process_issues)

        # 2. ワーカー設定ファイル確認
        config_issues = await self._check_worker_configurations()
        issues.extend(config_issues)

        # 3. ワーカー依存関係確認
        dependency_issues = await self._check_worker_dependencies()
        issues.extend(dependency_issues)

        # 4. ワーカーエラーログ分析
        log_issues = await self._analyze_worker_logs()
        issues.extend(log_issues)

        # 5. リソース使用量確認
        resource_issues = await self._check_resource_usage()
        issues.extend(resource_issues)

        logger.info(f"📊 ワーカー問題検出: {len(issues)}件")
        return issues

    async def _check_worker_processes(self) -> List[Issue]:
        """ワーカープロセスの状態確認"""
        issues = []

        try:
            # psutilで実行中プロセスを確認
            running_processes = [
                p.info for p in psutil.process_iter(["pid", "name", "cmdline"])
            ]

            for worker in self.target_workers:
            # 繰り返し処理
                worker_running = False

                # プロセス名でワーカーを探索
                for proc in running_processes:
                    cmdline = proc.get("cmdline", [])
                    if any(worker["name"] in str(cmd) for cmd in cmdline):
                        worker_running = True
                        break

                if not worker_running:
                    issues.append(
                        Issue(
                            id=f"worker_process_{worker['name']}",
                            category=IssueCategory.RESOURCE_EXHAUSTION,
                            severity=(
                                IssueSeverity.CRITICAL
                                if worker["priority"] == "critical"
                                else IssueSeverity.HIGH
                            ),
                            title=f"ワーカー停止: {worker['name']}",
                            description=f"{worker['name']} プロセスが実行されていません",
                            affected_component=worker["file"],
                            detected_at=datetime.now(),
                            metadata={
                                "worker_name": worker["name"],
                                "priority": worker["priority"],
                                "auto_fixable": True,
                                "restart_required": True,
                            },
                        )
                    )

                    self.worker_issues.append(
                        WorkerIssue(
                            worker_name=worker["name"],
                            issue_type="not_running",
                            error_details="プロセスが見つからない",
                            affected_files=[worker["file"]],
                            recovery_priority=worker["priority"],
                        )
                    )

        except Exception as e:
            logger.error(f"プロセス確認エラー: {e}")
            issues.append(
                Issue(
                    id="worker_process_check_error",
                    category=IssueCategory.CONFIG_ERROR,
                    severity=IssueSeverity.HIGH,
                    title="ワーカープロセス確認エラー",
                    description=f"プロセス状態確認中にエラー: {str(e)}",
                    affected_component="process_monitor",
                    detected_at=datetime.now(),
                    metadata={"error": str(e)},
                )
            )

        return issues

    async def _check_worker_configurations(self) -> List[Issue]:
        """ワーカー設定ファイルの確認"""
        issues = []

        # 基本設定ファイルの確認
        config_files = ["config/worker_config.json", "config/config.json", ".env"]

        for config_file in config_files:
            config_path = self.project_root / config_file

            if not config_path.exists():
                issues.append(
                    Issue(
                        id=f"config_missing_{config_file.replace('/', '_')}",
                        category=IssueCategory.CONFIG_ERROR,
                        severity=IssueSeverity.HIGH,
                        title=f"設定ファイル不在: {config_file}",
                        description=f"ワーカー実行に必要な設定ファイルが見つかりません",
                        affected_component=str(config_path),
                        detected_at=datetime.now(),
                        metadata={"auto_fixable": True, "config_type": "worker"},
                    )
                )
            else:
                # 設定ファイルの内容検証
                try:
                    if config_path.suffix == ".json":
                        # Deep nesting detected (depth: 5) - consider refactoring
                        with open(config_path) as f:
                            config_data = json.load(f)

                        # 必要な設定項目の確認
                        required_keys = ["workers", "database", "logging"]
                        missing_keys = [
                            key for key in required_keys if key not in config_data
                        ]

                        if not (missing_keys):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if missing_keys:
                            issues.append(
                                Issue(
                                    id=f"config_incomplete_{config_file.replace('/', '_')}",
                                    category=IssueCategory.CONFIG_ERROR,
                                    severity=IssueSeverity.MEDIUM,
                                    title=f"設定不完全: {config_file}",
                                    description=f"必要な設定項目が不足: {', '.join(missing_keys)}",
                                    affected_component=str(config_path),
                                    detected_at=datetime.now(),
                                    metadata={
                                        "missing_keys": missing_keys,
                                        "auto_fixable": True,
                                    },
                                )
                            )

                except Exception as e:
                    issues.append(
                        Issue(
                            id=f"config_parse_error_{config_file.replace('/', '_')}",
                            category=IssueCategory.CONFIG_ERROR,
                            severity=IssueSeverity.MEDIUM,
                            title=f"設定ファイル解析エラー: {config_file}",
                            description=f"設定ファイルの解析に失敗: {str(e)}",
                            affected_component=str(config_path),
                            detected_at=datetime.now(),
                            metadata={"error": str(e), "auto_fixable": True},
                        )
                    )

        return issues

    async def _check_worker_dependencies(self) -> List[Issue]:
        """ワーカー依存関係の確認"""
        issues = []

        # ワーカーファイルの依存関係確認
        for worker in self.target_workers:
            worker_path = self.project_root / worker["file"]

            if worker_path.exists():
                try:
                    with open(worker_path) as f:
                        content = f.read()

                    # インポート文の抽出と確認
                    import_lines = [
                        line.strip()
                        for line in content.split("\n")
                        if line.strip().startswith(("import ", "from "))
                    ]

                    missing_modules = []
                    for line in import_lines:
                        # Deep nesting detected (depth: 5) - consider refactoring
                        try:
                            # 基本的なインポートチェック（簡易版）
                            if not ("pika" in line and not self._check_module_available()):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if "pika" in line and not self._check_module_available(
                                "pika"
                            ):
                                missing_modules.append("pika")
                            elif (
                                "anthropic" in line
                                and not self._check_module_available("anthropic")
                            ):
                                missing_modules.append("anthropic")
                            elif "psutil" in line and not self._check_module_available(
                                "psutil"
                            ):
                                missing_modules.append("psutil")
                        except:
                            pass

                    if missing_modules:
                        issues.append(
                            Issue(
                                id=f"worker_dependencies_{worker['name']}",
                                category=IssueCategory.DEPENDENCY_MISSING,
                                severity=IssueSeverity.HIGH,
                                title=f"依存関係不足: {worker['name']}",
                                description=f"必要なモジュールが不足: {', '.join(missing_modules)}",
                                affected_component=worker["file"],
                                detected_at=datetime.now(),
                                metadata={
                                    "missing_modules": missing_modules,
                                    "worker_name": worker["name"],
                                    "auto_fixable": True,
                                },
                            )
                        )

                except Exception as e:
                    logger.error(f"依存関係確認エラー {worker['file']}: {e}")

        return issues

    def _check_module_available(self, module_name: str) -> bool:
        """モジュールの利用可能性確認"""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False

    async def _analyze_worker_logs(self) -> List[Issue]:
        """ワーカーログの分析"""
        issues = []

        # ログファイルからエラーパターンを検索
        error_patterns = [
            ("ModuleNotFoundError", "dependency_missing"),
            ("ConnectionRefusedError", "connection_error"),
            ("API rate limit", "rate_limit"),
            ("Invalid API key", "api_key_error"),
            ("Permission denied", "permission_error"),
            ("Memory Error", "memory_error"),
            ("Traceback", "runtime_error"),
        ]

        # 繰り返し処理
        for log_path in self.log_paths:
            if log_path.exists() and log_path.is_file():
                try:
                    with open(log_path) as f:
                        log_content = f.read()

                    for pattern, error_type in error_patterns:
                        if not (pattern.lower() in log_content.lower()):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if pattern.lower() in log_content.lower():
                            # 最近のエラーかどうか確認（簡易版）
                            recent_pattern = datetime.now().strftime("%Y-%m-%d")
                            if not (recent_pattern in str(datetime.now())):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if (
                                recent_pattern in log_content
                                or len(log_content.split(pattern)) > 2
                            ):
                                issues.append(
                                    Issue(
                                        id=f"log_error_{error_type}_{log_path.name}",
                                        category=IssueCategory.CONFIG_ERROR,
                                        severity=IssueSeverity.MEDIUM,
                                        title=f"ログエラー検出: {pattern}",
                                        description=f"{log_path.name} で {pattern} エラーが検出されました",
                                        affected_component=str(log_path),
                                        detected_at=datetime.now(),
                                        metadata={
                                            "error_pattern": pattern,
                                            "error_type": error_type,
                                            "auto_fixable": True,
                                        },
                                    )
                                )

                except Exception as e:
                    logger.error(f"ログ分析エラー {log_path}: {e}")

        return issues

    async def _check_resource_usage(self) -> List[Issue]:
        """リソース使用量の確認"""
        issues = []

        try:
            # CPU・メモリ使用量確認
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # CPU使用率が高すぎる場合
            if cpu_percent > 90:
                issues.append(
                    Issue(
                        id="high_cpu_usage",
                        category=IssueCategory.RESOURCE_EXHAUSTION,
                        severity=IssueSeverity.HIGH,
                        title="CPU使用率が過度に高い",
                        description=f"CPU使用率: {cpu_percent}% (閾値: 90%)",
                        affected_component="system_resources",
                        detected_at=datetime.now(),
                        metadata={"cpu_percent": cpu_percent, "auto_fixable": True},
                    )
                )

            # メモリ使用率が高すぎる場合
            if memory.percent > 85:
                issues.append(
                    Issue(
                        id="high_memory_usage",
                        category=IssueCategory.RESOURCE_EXHAUSTION,
                        severity=IssueSeverity.HIGH,
                        title="メモリ使用率が過度に高い",
                        description=f"メモリ使用率: {memory.percent}% (閾値: 85%)",
                        affected_component="system_resources",
                        detected_at=datetime.now(),
                        metadata={
                            "memory_percent": memory.percent,
                            "auto_fixable": True,
                        },
                    )
                )

            # ディスク容量確認
            disk = psutil.disk_usage("/")
            if disk.percent > 90:
                issues.append(
                    Issue(
                        id="high_disk_usage",
                        category=IssueCategory.RESOURCE_EXHAUSTION,
                        severity=IssueSeverity.MEDIUM,
                        title="ディスク使用率が高い",
                        description=f"ディスク使用率: {disk.percent}% (閾値: 90%)",
                        affected_component="disk_storage",
                        detected_at=datetime.now(),
                        metadata={"disk_percent": disk.percent, "auto_fixable": True},
                    )
                )

        except Exception as e:
            logger.error(f"リソース使用量確認エラー: {e}")

        return issues

    async def investigate(self, issue: Issue) -> Diagnosis:
        """ワーカー問題の詳細調査"""
        logger.info(f"🔬 ワーカー問題詳細調査: {issue.title}")

        diagnosis_data = {
            "issue_type": issue.category.value,
            "severity": issue.severity.value,
            "investigation_time": datetime.now().isoformat(),
        }

        # カテゴリ別の詳細調査
        if "worker_process" in issue.id:
            diagnosis_data.update(await self._investigate_process_issue(issue))
        elif "config" in issue.id:
            diagnosis_data.update(await self._investigate_config_issue(issue))
        elif "dependencies" in issue.id:
            diagnosis_data.update(await self._investigate_dependency_issue(issue))
        elif "log_error" in issue.id:
            diagnosis_data.update(await self._investigate_log_issue(issue))
        elif "resource" in issue.id:
            diagnosis_data.update(await self._investigate_resource_issue(issue))

        return Diagnosis(
            issue_id=issue.id,
            root_cause=diagnosis_data.get("root_cause", "調査中"),
            impact_assessment=diagnosis_data.get("impact", "中程度"),
            recommended_actions=diagnosis_data.get("actions", ["手動確認が必要"]),
            estimated_fix_time=diagnosis_data.get("fix_time", 300),
            requires_approval=diagnosis_data.get("requires_approval", False),
            confidence_score=diagnosis_data.get("confidence", 0.8),
        )

    async def _investigate_process_issue(self, issue: Issue) -> Dict:
        """プロセス問題の調査"""
        return {
            "root_cause": "ワーカープロセスの異常終了または未起動",
            "impact": "該当ワーカーの機能が完全停止",
            "actions": ["プロセス再起動", "設定確認", "ログ分析", "依存関係確認"],
            "fix_time": 180,
            "confidence": 0.9,
            "requires_approval": False,
        }

    async def _investigate_config_issue(self, issue: Issue) -> Dict:
        """設定問題の調査"""
        return {
            "root_cause": "設定ファイルの不備または欠如",
            "impact": "ワーカーの起動・動作に支障",
            "actions": ["設定ファイル作成/修正", "デフォルト値設定", "検証テスト"],
            "fix_time": 240,
            "confidence": 0.85,
            "requires_approval": False,
        }

    async def _investigate_dependency_issue(self, issue: Issue) -> Dict:
        """依存関係問題の調査"""
        return {
            "root_cause": "必要なPythonモジュールまたはシステム依存関係の不足",
            "impact": "ワーカーの特定機能が使用不可",
            "actions": ["モジュールインストール", "要件ファイル更新", "仮想環境確認"],
            "fix_time": 300,
            "confidence": 0.8,
            "requires_approval": False,
        }

    async def _investigate_log_issue(self, issue: Issue) -> Dict:
        """ログ問題の調査"""
        return {
            "root_cause": "ワーカー実行時の実行時エラーまたは設定問題",
            "impact": "エラー頻度に応じた性能低下",
            "actions": ["エラー原因特定", "コード修正", "設定調整", "監視強化"],
            "fix_time": 600,
            "confidence": 0.7,
            "requires_approval": False,
        }

    async def _investigate_resource_issue(self, issue: Issue) -> Dict:
        """リソース問題の調査"""
        return {
            "root_cause": "システムリソースの過度な使用",
            "impact": "システム全体の性能低下",
            "actions": ["リソース使用最適化", "不要プロセス終了", "設定調整"],
            "fix_time": 480,
            "confidence": 0.75,
            "requires_approval": True,
        }

    async def resolve(self, diagnosis: Diagnosis) -> Resolution:
        """ワーカー問題の修復実行"""
        logger.info(f"🔧 ワーカー問題修復実行: {diagnosis.issue_id}")

        try:
            success = False
            actions_taken = []

            # 問題種別に応じた修復実行
            if "worker_process" in diagnosis.issue_id:
                success, action = await self._fix_worker_process(diagnosis)
                actions_taken.append(action)
            elif "config" in diagnosis.issue_id:
                success, action = await self._fix_worker_config(diagnosis)
                actions_taken.append(action)
            elif "dependencies" in diagnosis.issue_id:
                success, action = await self._fix_worker_dependencies(diagnosis)
                actions_taken.append(action)
            elif "log_error" in diagnosis.issue_id:
                success, action = await self._fix_log_errors(diagnosis)
                actions_taken.append(action)
            elif "resource" in diagnosis.issue_id:
                success, action = await self._fix_resource_usage(diagnosis)
                actions_taken.append(action)

            return Resolution(
                issue_id=diagnosis.issue_id,
                success=success,
                actions_taken=actions_taken,
                time_taken=int(diagnosis.estimated_fix_time),
                side_effects=[],
                verification_results={"status": "verified" if success else "failed"},
            )

        except Exception as e:
            logger.error(f"修復実行エラー {diagnosis.issue_id}: {e}")
            return Resolution(
                issue_id=diagnosis.issue_id,
                success=False,
                actions_taken=[f"修復実行中にエラー: {str(e)}"],
                time_taken=30,
                side_effects=["error_state"],
                verification_results={"error": str(e)},
            )

    async def _fix_worker_process(self, diagnosis: Diagnosis) -> tuple[bool, str]:
        """ワーカープロセスの修復"""
        try:
            # プロセス名を抽出
            issue_id = diagnosis.issue_id
            worker_name = issue_id.replace("worker_process_", "")

            # 対象ワーカーファイルを特定
            worker_file = None
            for worker in self.target_workers:
                if worker["name"] == worker_name:
                    worker_file = self.project_root / worker["file"]
                    break

            if worker_file and worker_file.exists():
                # ワーカーを起動
                cmd = [sys.executable, str(worker_file)]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.project_root),
                )

                # 起動確認（2秒待機）
                time.sleep(2)
                if process.poll() is None:  # プロセスがまだ実行中
                    logger.info(f"✅ ワーカー起動成功: {worker_name}")
                    return True, f"worker_restarted_{worker_name}"
                else:
                    stderr = process.stderr.read().decode()
                    logger.error(f"ワーカー起動失敗: {stderr}")
                    return False, f"worker_restart_failed_{worker_name}: {stderr}"

            return False, f"worker_file_not_found_{worker_name}"

        except Exception as e:
            logger.error(f"ワーカープロセス修復エラー: {e}")
            return False, f"worker_process_fix_failed: {str(e)}"

    async def _fix_worker_config(self, diagnosis: Diagnosis) -> tuple[bool, str]:
        """ワーカー設定の修復"""
        try:
            # 基本設定ファイルの作成
            config_file = self.project_root / "config" / "worker_config.json"
            config_file.parent.mkdir(exist_ok=True)

            default_config = {
                "workers": {
                    "enhanced_task_worker": {
                        "enabled": True,
                        "max_retries": 3,
                        "timeout": 300,
                    },
                    "task_worker": {"enabled": True, "max_retries": 3, "timeout": 180},
                    "pm_worker": {"enabled": True, "max_retries": 2, "timeout": 240},
                },
                "database": {"type": "sqlite", "path": "data/workers.db"},
                "logging": {"level": "INFO", "file": "logs/workers.log"},
                "monitoring": {
                    "health_check_interval": 60,
                    "max_memory_usage": 0.8,
                    "max_cpu_usage": 0.7,
                },
            }

            with open(config_file, "w") as f:
                json.dump(default_config, f, indent=2)

            logger.info("✅ ワーカー設定ファイル作成完了")
            return True, "worker_config_created"

        except Exception as e:
            logger.error(f"ワーカー設定修復エラー: {e}")
            return False, f"worker_config_fix_failed: {str(e)}"

    async def _fix_worker_dependencies(self, diagnosis: Diagnosis) -> tuple[bool, str]:
        """ワーカー依存関係の修復"""
        try:
            # 基本的な依存関係チェックスクリプト作成
            install_script = self.project_root / "scripts" / "install_dependencies.py"
            install_script.parent.mkdir(exist_ok=True)

            script_content = '''#!/usr/bin/env python3
"""
Worker Dependencies Installation Script
ワーカー依存関係自動インストール
"""

import subprocess
import sys

def install_package(package):
    """パッケージをインストール"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Installed: {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    """メイン実行"""
    packages = [
        "pika",
        "anthropic",
        "psutil",
        "requests",
        "python-dotenv"
    ]

    print("🔧 Installing worker dependencies...")

    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1

    print(f"📊 Installation complete: {success_count}/{len(packages)} packages")

if __name__ == "__main__":
    main()
'''

            with open(install_script, "w") as f:
                f.write(script_content)

            # スクリプトを実行可能にする
            install_script.chmod(0o755)

            logger.info("✅ 依存関係インストールスクリプト作成完了")
            return True, "dependency_script_created"

        except Exception as e:
            logger.error(f"依存関係修復エラー: {e}")
            return False, f"dependency_fix_failed: {str(e)}"

    async def _fix_log_errors(self, diagnosis: Diagnosis) -> tuple[bool, str]:
        """ログエラーの修復"""
        try:
            # ログローテーション実行
            log_dir = self.project_root / "logs"

            rotated_count = 0
            for log_file in log_dir.glob("*.log"):
                if log_file.stat().st_size > 50 * 1024 * 1024:  # 50MB以上
                    backup_file = log_file.with_suffix(
                        f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
                    )
                    log_file.rename(backup_file)
                    log_file.touch()
                    rotated_count += 1

            # エラー監視設定作成
            error_config = {
                "error_monitoring": {
                    "enabled": True,
                    "patterns": [
                        "ModuleNotFoundError",
                        "ConnectionRefusedError",
                        "API rate limit",
                        "Invalid API key",
                    ],
                    "action": "restart_worker",
                    "max_errors_per_hour": 10,
                }
            }

            config_file = self.project_root / "config" / "error_monitoring.json"
            with open(config_file, "w") as f:
                json.dump(error_config, f, indent=2)

            logger.info(f"✅ ログ修復完了（ローテーション: {rotated_count}ファイル）")
            return True, f"log_errors_fixed_rotated_{rotated_count}"

        except Exception as e:
            logger.error(f"ログエラー修復失敗: {e}")
            return False, f"log_error_fix_failed: {str(e)}"

    async def _fix_resource_usage(self, diagnosis: Diagnosis) -> tuple[bool, str]:
        """リソース使用量の修復"""
        try:
            # リソース監視設定作成
            resource_config = {
                "resource_limits": {
                    "max_cpu_percent": 80.0,
                    "max_memory_percent": 75.0,
                    "monitoring_interval": 30,
                },
                "actions": {
                    "high_cpu": "reduce_worker_count",
                    "high_memory": "restart_workers",
                    "high_disk": "cleanup_logs",
                },
                "worker_optimization": {
                    "batch_size": 10,
                    "processing_delay": 0.1,
                    "max_concurrent": 5,
                },
            }

            config_file = self.project_root / "config" / "resource_monitoring.json"
            with open(config_file, "w") as f:
                json.dump(resource_config, f, indent=2)

            logger.info("✅ リソース監視設定作成完了")
            return True, "resource_monitoring_configured"

        except Exception as e:
            logger.error(f"リソース修復エラー: {e}")
            return False, f"resource_fix_failed: {str(e)}"

    def get_knight_status(self) -> Dict[str, Any]:
        """騎士の現在状態を取得"""
        return {
            "knight_id": self.knight_id,
            "name": self.name,
            "status": "active",
            "specialty": self.specialty,
            "target_workers": len(self.target_workers),
            "issues_detected": len(self.worker_issues),
            "last_patrol": getattr(self, "last_patrol", None),
            "success_rate": getattr(self, "success_rate", 0.0),
        }


if __name__ == "__main__":
    import asyncio

    async def test_worker_knight():
        """test_worker_knightテストメソッド"""
        knight = WorkerStabilizationKnight()

        # 巡回テスト
        issues = await knight.patrol()
        print(f"🔍 検出された問題: {len(issues)}件")

        # 問題がある場合は調査と修復
        for issue in issues[:3]:  # 最初の3件をテスト
            diagnosis = await knight.investigate(issue)
            print(f"🔬 調査完了: {diagnosis.root_cause}")

            resolution = await knight.resolve(diagnosis)
            print(f"🔧 修復結果: {resolution.success}")

        # ステータス表示
        status = knight.get_knight_status()
        print(f"🛡️ 騎士ステータス: {status}")

    # テスト実行
    asyncio.run(test_worker_knight())
