#!/usr/bin/env python3
"""
🎯 Optimized Issue Orchestrator - 最適化イシュー処理オーケストレーター
エルダーズギルド自動化システムの統合処理フロー最適化

機能:
- イシュー処理優先順位付け
- 並列処理管理
- リソース使用量監視
- 処理完了追跡とレポート

作成者: クロードエルダー
作成日: 2025-07-19
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import psutil

# 既存モジュールのインポート
from libs.integrations.github.enhanced_auto_issue_processor import (
    EnhancedAutoIssueProcessor,
)
from libs.integrations.github.issue_completion_manager import (
    CompletionResult,
    IssueCompletionManager,
)

# GitHub APIインポート
try:
    from github import Github
    from github.Issue import Issue

    GITHUB_AVAILABLE = True
except ImportError:
    Github = None
    Issue = None
    GITHUB_AVAILABLE = False

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessingPriority(Enum):
    """処理優先度"""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class ResourceStatus(Enum):
    """リソース状況"""

    AVAILABLE = "available"
    BUSY = "busy"
    OVERLOAD = "overload"
    CRITICAL = "critical"


@dataclass
class ProcessingTask:
    """処理タスク"""

    issue: Issue
    priority: ProcessingPriority
    estimated_time: float
    retry_count: int
    scheduled_at: datetime
    metadata: Dict[str, Any]


@dataclass
class ResourceMetrics:
    """リソースメトリクス"""

    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_processes: int
    timestamp: datetime


class OptimizedIssueOrchestrator:
    """
    🎯 最適化イシュー処理オーケストレーター

    エルダーズギルドの全イシュー処理を統合管理し、
    最適な順序と並列度で処理を実行
    """

    def __init__(
        self, max_concurrent_tasks: int = 3, resource_check_interval: int = 30
    ):
        """オーケストレーターを初期化"""
        self.max_concurrent_tasks = max_concurrent_tasks
        self.resource_check_interval = resource_check_interval

        # 処理システム初期化
        self.processor = EnhancedAutoIssueProcessor()
        self.completion_manager = IssueCompletionManager()

        # GitHub API初期化
        if GITHUB_AVAILABLE:
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                self.github = Github(github_token)
                self.repo = self.github.get_repo(
                    f"{os.getenv(
                        'GITHUB_REPO_OWNER',
                        'ext-maru')}/{os.getenv('GITHUB_REPO_NAME',
                        'ai-co'
                    )}"
                )
            else:
                logger.error("GITHUB_TOKEN環境変数が設定されていません")
                self.github = None
                self.repo = None
        else:
            self.github = None
            self.repo = None

        # 処理状態管理
        self.active_tasks = {}
        self.task_queue = []
        self.processing_statistics = {
            "total_processed": 0,
            "successful_completions": 0,
            "failed_attempts": 0,
            "average_processing_time": 0.0,
            "start_time": datetime.now(),
        }

        # リソース監視
        self.resource_thresholds = {
            "cpu_max": 80.0,
            "memory_max": 85.0,
            "disk_max": 90.0,
        }

        logger.info("🎯 Optimized Issue Orchestrator 初期化完了")

    def get_resource_status(self) -> Tuple[ResourceStatus, ResourceMetrics]:
        """現在のリソース状況を取得"""
        try:
            # システムリソース取得
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            metrics = ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=(disk.used / disk.total) * 100,
                active_processes=len(self.active_tasks),
                timestamp=datetime.now(),
            )

            # 状況判定
            if (
                cpu_percent > 95
                or memory.percent > 95
                or metrics.disk_usage_percent > 95
            ):
                status = ResourceStatus.CRITICAL
            elif (
                cpu_percent > self.resource_thresholds["cpu_max"]
                or memory.percent > self.resource_thresholds["memory_max"]
                or metrics.disk_usage_percent > self.resource_thresholds["disk_max"]
            ):
                status = ResourceStatus.OVERLOAD
            elif len(self.active_tasks) >= self.max_concurrent_tasks:
                status = ResourceStatus.BUSY
            else:
                status = ResourceStatus.AVAILABLE

            return status, metrics

        except Exception as e:
            logger.error(f"❌ リソース状況取得エラー: {e}")
            return ResourceStatus.CRITICAL, ResourceMetrics(0, 0, 0, 0, datetime.now())

    def prioritize_issue(self, issue: Issue) -> ProcessingPriority:
        """イシューの優先度を決定"""
        try:
            priority_score = 0

            # ラベルベースの優先度
            label_priorities = {
                "critical": 10,
                "high": 8,
                "urgent": 8,
                "bug": 6,
                "feature": 4,
                "enhancement": 3,
                "documentation": 2,
                "question": 1,
            }

            for label in issue.labels:
                priority_score += label_priorities.get(label.name.lower(), 0)

            # 作成日からの経過時間（古いほど優先）
            age_days = (datetime.now() - issue.created_at.replace(tzinfo=None)).days
            if age_days > 7:
                priority_score += 3
            elif age_days > 3:
                priority_score += 2
            elif age_days > 1:
                priority_score += 1

            # コメント数（アクティブなイシューほど優先）
            if issue.comments > 5:
                priority_score += 2
            elif issue.comments > 2:
                priority_score += 1

            # アサイン状況
            if issue.assignee:
                priority_score += 1

            # 優先度分類
            if priority_score >= 12:
                return ProcessingPriority.CRITICAL
            elif priority_score >= 8:
                return ProcessingPriority.HIGH
            elif priority_score >= 4:
                return ProcessingPriority.MEDIUM
            else:
                return ProcessingPriority.LOW

        except Exception as e:
            logger.warning(f"優先度計算エラー: {e}")
            return ProcessingPriority.MEDIUM

    def estimate_processing_time(
        self, issue: Issue, priority: ProcessingPriority
    ) -> float:
        """処理時間を推定"""
        try:
            base_time = 300.0  # 5分ベース

            # 優先度による調整
            priority_multipliers = {
                ProcessingPriority.CRITICAL: 0.8,  # 高優先度は迅速処理
                ProcessingPriority.HIGH: 1.0,
                ProcessingPriority.MEDIUM: 1.2,
                ProcessingPriority.LOW: 1.5,
            }

            # イシューの複雑度による調整
            complexity_multiplier = 1.0

            # タイトルの長さ
            if len(issue.title) > 100:
                complexity_multiplier += 0.3
            elif len(issue.title) > 50:
                complexity_multiplier += 0.1

            # 本文の長さ
            if issue.body and len(issue.body) > 1000:
                complexity_multiplier += 0.5
            elif issue.body and len(issue.body) > 500:
                complexity_multiplier += 0.2

            # ラベル数
            if len(issue.labels) > 5:
                complexity_multiplier += 0.2

            estimated_time = (
                base_time * priority_multipliers[priority] * complexity_multiplier
            )

            # 最小・最大制限
            return max(60.0, min(1800.0, estimated_time))  # 1分〜30分

        except Exception as e:
            logger.warning(f"処理時間推定エラー: {e}")
            return 300.0

    async def scan_and_queue_issues(self) -> int:
        """イシューをスキャンしてキューに追加"""
        if not self.repo:
            logger.error("GitHubリポジトリが設定されていません")
            return 0

        try:
            logger.info("🔍 イシュースキャン開始")

            # オープンイシューを取得
            open_issues = list(self.repo.get_issues(state="open"))
            queued_count = 0

            for issue in open_issues:
                # 既に処理中またはキューに入っているかチェック
                if issue.number in self.active_tasks or any(
                    task.issue.number == issue.number for task in self.task_queue
                ):
                    continue

                # 完了管理システムで処理済みかチェック
                existing_record = self.completion_manager.get_issue_record(issue.number)
                if existing_record and existing_record.status.value in [
                    "completed",
                    "pr_created",
                ]:
                    continue

                # 処理タスクを作成
                priority = self.prioritize_issue(issue)
                estimated_time = self.estimate_processing_time(issue, priority)

                task = ProcessingTask(
                    issue=issue,
                    priority=priority,
                    estimated_time=estimated_time,
                    retry_count=existing_record.retry_count if existing_record else 0,
                    scheduled_at=datetime.now(),
                    metadata={
                        "labels": [label.name for label in issue.labels],
                        "created_at": issue.created_at.isoformat(),
                        "comments": issue.comments,
                        "assignee": issue.assignee.login if issue.assignee else None,
                    },
                )

                self.task_queue.append(task)
                queued_count += 1

            # 優先度順にソート
            self.task_queue.sort(key=lambda t: (t.priority.value, t.scheduled_at))

            logger.info(
                f"📋 イシュースキャン完了: {queued_count}件キュー追加, 総キュー数: {len(self.task_queue)}"
            )
            return queued_count

        except Exception as e:
            logger.error(f"❌ イシュースキャンエラー: {e}")
            return 0

    async def process_single_issue(self, task: ProcessingTask) -> bool:
        """単一イシューを処理"""
        issue_number = task.issue.number

        try:
            logger.info(f"🚀 イシュー処理開始: #{issue_number} (優先度: {task.priority.name})")
            start_time = time.time()

            # 完了管理システムに処理開始を記録
            self.completion_manager.start_issue_processing(
                issue_number, task.issue.title, task.metadata
            )

            # 拡張処理器で処理実行
            result = await self.processor.process_issue_with_pr(task.issue)

            processing_time = time.time() - start_time

            # 結果に基づいて完了記録
            if result.get("success", False):
                completion_result = CompletionResult.SUCCESS
                error_message = None

                # PR作成記録
                if result.get("pr_created", False):
                    self.completion_manager.record_pr_creation(
                        issue_number, result.get("pr_number"), result.get("pr_url")
                    )

                logger.info(f"✅ イシュー処理成功: #{issue_number} ({processing_time:0.2f}s)")

            else:
                completion_result = CompletionResult.FAILED
                error_message = result.get("error", "Unknown error")
                logger.warning(f"❌ イシュー処理失敗: #{issue_number} - {error_message}")

            # 完了記録
            self.completion_manager.complete_issue(
                issue_number, completion_result, error_message
            )

            # 統計更新
            self.processing_statistics["total_processed"] += 1
            if completion_result == CompletionResult.SUCCESS:
                self.processing_statistics["successful_completions"] += 1
            else:
                self.processing_statistics["failed_attempts"] += 1

            # 平均処理時間更新
            total_time = self.processing_statistics["average_processing_time"] * (
                self.processing_statistics["total_processed"] - 1
            )
            self.processing_statistics["average_processing_time"] = (
                total_time + processing_time
            ) / self.processing_statistics["total_processed"]

            return completion_result == CompletionResult.SUCCESS

        except Exception as e:
            logger.error(f"❌ イシュー処理例外: #{issue_number} - {e}")

            # エラー記録
            self.completion_manager.complete_issue(
                issue_number, CompletionResult.FAILED, str(e)
            )
            self.processing_statistics["failed_attempts"] += 1

            return False

        finally:
            # アクティブタスクから削除
            if issue_number in self.active_tasks:
                del self.active_tasks[issue_number]

    async def execute_processing_cycle(self) -> Dict[str, Any]cycle_start = time.time()logger.info("🔄 処理サイクル開始")
    """理サイクルを実行"""
:
        try:
            # イシュースキャン
            new_issues = await self.scan_and_queue_issues()

            # リソース状況確認
            resource_status, resource_metrics = self.get_resource_status()
            logger.info(
                (
                    f"f"💻 リソース状況: {resource_status.value} (CPU: {resource_metrics.cpu_percent:0.1f}%, Memory: "
                    f"{resource_metrics.memory_percent:0.1f}%)""
                )
            )

            # 処理可能かチェック
            if resource_status == ResourceStatus.CRITICAL:
                logger.warning("⚠️ リソース不足により処理を延期")
                return {
                    "status": "delayed",
                    "reason": "resource_critical",
                    "resource_metrics": resource_metrics.__dict__,
                }

            # 並列処理実行
            tasks_to_process = []
            available_slots = self.max_concurrent_tasks - len(self.active_tasks)

            # リソース状況に応じて並列度調整
            if resource_status == ResourceStatus.OVERLOAD:
                available_slots = min(available_slots, 1)
            elif resource_status == ResourceStatus.BUSY:
                available_slots = min(available_slots, 2)

            # タスクを並列実行のために準備
            for _ in range(min(available_slots, len(self.task_queue))):
                if not self.task_queue:
                    break

                task = self.task_queue.pop(0)
                self.active_tasks[task.issue.number] = task
                tasks_to_process.append(self.process_single_issue(task))

            # 並列実行
            if tasks_to_process:
                logger.info(f"⚡ 並列処理開始: {len(tasks_to_process)}タスク")
                results = await asyncio.gather(
                    *tasks_to_process, return_exceptions=True
                )
                successful_count = sum(1 for r in results if r is True)
                logger.info(f"📊 並列処理完了: {successful_count}/{len(results)}成功")

            cycle_time = time.time() - cycle_start

            return {
                "status": "completed",
                "new_issues_queued": new_issues,
                "tasks_processed": len(tasks_to_process),
                "successful_tasks": successful_count if tasks_to_process else 0,
                "cycle_time": cycle_time,
                "queue_size": len(self.task_queue),
                "active_tasks": len(self.active_tasks),
                "resource_status": resource_status.value,
                "resource_metrics": resource_metrics.__dict__,
            }

        except Exception as e:
            logger.error(f"❌ 処理サイクルエラー: {e}")
            return {
                "status": "error",
                "error": str(e),
                "cycle_time": time.time() - cycle_start,
            }

    async def run_continuous_processing(
        self, cycles: int = None, cycle_interval: int = 600
    ):
        """継続的処理を実行"""
        logger.info(f"🚀 継続的処理開始 (サイクル間隔: {cycle_interval}秒)")

        cycle_count = 0

        try:
            while cycles is None or cycle_count < cycles:
                cycle_result = await self.execute_processing_cycle()

                logger.info(f"📋 サイクル{cycle_count + 1}完了: {cycle_result['status']}")

                # 統計ログ
                if cycle_count % 10 == 0:  # 10サイクルごと
                    self.log_processing_statistics()

                cycle_count += 1

                # サイクル間隔待機
                if cycles is None or cycle_count < cycles:
                    await asyncio.sleep(cycle_interval)

        except KeyboardInterrupt:
            logger.info("⌨️ ユーザー中断: 継続的処理を停止")
        except Exception as e:
            logger.error(f"❌ 継続的処理エラー: {e}")

        logger.info(f"🏁 継続的処理終了 (総サイクル数: {cycle_count})")

    def log_processing_statistics(self):
        """処理統計をログ出力"""
        stats = self.processing_statistics
        uptime = datetime.now() - stats["start_time"]

        logger.info(
            f"""
"📊" 処理統計サマリー:
   - 稼働時間: {uptime}
   - 総処理数: {stats['total_processed']}
   - 成功数: {stats['successful_completions']}
   - 失敗数: {stats['failed_attempts']}
   - 成功率: {(stats['successful_completions'] / max(stats['total_processed'], 1)) * 100:0.1f}%
   - 平均処理時間: {stats['average_processing_time']:0.2f}秒
   - キュー数: {len(self.task_queue)}
   - アクティブ: {len(self.active_tasks)}
        """
        )

    def get_status_report(self) -> Dict[str, Any]resource_status, resource_metrics = self.get_resource_status():
    """テータスレポートを取得"""

        return {:
            "orchestrator_status": {
                "active_tasks": len(self.active_tasks),
                "queued_tasks": len(self.task_queue),
                "max_concurrent": self.max_concurrent_tasks,
            },
            "processing_statistics": self.processing_statistics.copy(),
            "resource_status": {
                "status": resource_status.value,
                "metrics": resource_metrics.__dict__,
                "thresholds": self.resource_thresholds,
            },
            "completion_statistics": self.completion_manager.get_completion_statistics(
                1
            ),  # 直近24時間
            "timestamp": datetime.now().isoformat(),
        }


# メイン実行関数
async def main()logger.info("🎯 Optimized Issue Orchestrator テスト開始")
"""メイン実行関数"""

    orchestrator = OptimizedIssueOrchestrator(max_concurrent_tasks=2)

    # 単一サイクルテスト
    result = await orchestrator.execute_processing_cycle()
    logger.info(f"📋 処理サイクル結果: {result}")

    # ステータスレポート
    status = orchestrator.get_status_report()
    logger.info(f"📊 ステータス: {status}")

    logger.info("🏁 Optimized Issue Orchestrator テスト完了")


if __name__ == "__main__":
    asyncio.run(main())
