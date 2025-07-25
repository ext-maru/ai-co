#!/usr/bin/env python3
"""
Elder Flow Core Enhancement
エルダーフローコア強化システム - 記録・監視・品質保証の統合

エルダーズギルド評議会承認 - 2025年7月11日
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import subprocess


class FlowPhase(Enum):
    """Elder Flowフェーズ"""

    SAGE_CONSULTATION = "sage_consultation"  # 4賢者相談
    SERVANT_EXECUTION = "servant_execution"  # サーバント実行
    QUALITY_GATE = "quality_gate"  # 品質ゲート
    COUNCIL_REPORT = "council_report"  # 評議会報告
    GIT_AUTOMATION = "git_automation"  # Git自動化


class FlowStatus(Enum):
    """フロー状態"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class FlowExecution:
    """フロー実行記録"""

    execution_id: str
    task_name: str
    priority: str
    phase: FlowPhase
    status: FlowStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    quality_score: Optional[float]
    violations_found: int
    violations_fixed: int
    sage_recommendations: List[Dict[str, Any]]
    servant_results: List[Dict[str, Any]]
    git_commits: List[str]
    error_log: List[str]
    metadata: Dict[str, Any]


class ElderFlowCoreEnhancement:
    """Elder Flowコア強化システム"""

    def __init__(self):
        """初期化メソッド"""
        self.logger = self._setup_logger()
        self.db_path = Path("data/elder_flow_core.db")
        self.flow_log = Path("logs/elder_flow_executions.log")
        self.metrics_file = Path("data/elder_flow_metrics.json")
        self._init_database()
        self._init_metrics()

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("elder_flow_core_enhancement")
        logger.setLevel(logging.INFO)

        # コンソールハンドラ
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            "%(asctime)s - Elder Flow Core - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # ファイルハンドラ
        self.flow_log.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(self.flow_log, mode="a")
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)

        return logger

    def _init_database(self):
        """データベース初期化"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        # フロー実行テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS flow_executions (
                execution_id TEXT PRIMARY KEY,
                task_name TEXT NOT NULL,
                priority TEXT NOT NULL,
                phase TEXT NOT NULL,
                status TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_seconds REAL,
                quality_score REAL,
                violations_found INTEGER DEFAULT 0,
                violations_fixed INTEGER DEFAULT 0,
                sage_recommendations TEXT,
                servant_results TEXT,
                git_commits TEXT,
                error_log TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # フェーズ履歴テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS phase_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                status TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                details TEXT,
                FOREIGN KEY (execution_id) REFERENCES flow_executions(execution_id)
            )
        """
        )

        # 品質メトリクステーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                threshold REAL,
                passed BOOLEAN,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (execution_id) REFERENCES flow_executions(execution_id)
            )
        """
        )

        # 違反記録テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS violation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                violation_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                location TEXT,
                description TEXT,
                fixed BOOLEAN DEFAULT FALSE,
                fix_details TEXT,
                detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                fixed_at TEXT,
                FOREIGN KEY (execution_id) REFERENCES flow_executions(execution_id)
            )
        """
        )

        conn.commit()
        conn.close()

        self.logger.info("✅ Elder Flow Core データベース初期化完了")

    def _init_metrics(self):
        """メトリクス初期化"""
        if not self.metrics_file.exists():
            initial_metrics = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "average_quality_score": 0.0,
                "total_violations_found": 0,
                "total_violations_fixed": 0,
                "average_execution_time": 0.0,
                "phase_success_rates": {phase.value: 0.0 for phase in FlowPhase},
                "last_updated": datetime.now().isoformat(),
            }

            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metrics_file, "w") as f:
                json.dump(initial_metrics, f, indent=2)

    def generate_execution_id(self, task_name: str) -> str:
        """実行ID生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_input = f"{task_name}_{timestamp}".encode()
        hash_value = hashlib.md5(hash_input).hexdigest()[:8]
        return f"EF_{timestamp}_{hash_value}"

    async def start_flow_execution(
        self, task_name: str, priority: str = "normal"
    ) -> str:
        """フロー実行開始"""
        execution_id = self.generate_execution_id(task_name)

        self.logger.info(f"🚀 Elder Flow実行開始: {execution_id} - {task_name}")

        # 実行記録作成
        execution = FlowExecution(
            execution_id=execution_id,
            task_name=task_name,
            priority=priority,
            phase=FlowPhase.SAGE_CONSULTATION,
            status=FlowStatus.IN_PROGRESS,
            start_time=datetime.now(),
            end_time=None,
            duration_seconds=None,
            quality_score=None,
            violations_found=0,
            violations_fixed=0,
            sage_recommendations=[],
            servant_results=[],
            git_commits=[],
            error_log=[],
            metadata={"priority": priority},
        )

        # データベース記録
        await self._record_execution_start(execution)

        return execution_id

    async def _record_execution_start(self, execution: FlowExecution):
        """実行開始記録"""
        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO flow_executions (
                execution_id, task_name, priority, phase, status,
                start_time, sage_recommendations, servant_results,
                git_commits, error_log, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                execution.execution_id,
                execution.task_name,
                execution.priority,
                execution.phase.value,
                execution.status.value,
                execution.start_time.isoformat(),
                json.dumps(execution.sage_recommendations),
                json.dumps(execution.servant_results),
                json.dumps(execution.git_commits),
                json.dumps(execution.error_log),
                json.dumps(execution.metadata),
            ),
        )

        conn.commit()
        conn.close()

    async def record_phase_transition(
        self,
        execution_id: str,
        from_phase: FlowPhase,
        to_phase: FlowPhase,
        details: Dict[str, Any] = None,
    ):
        """フェーズ遷移記録"""
        self.logger.info(f"🔄 フェーズ遷移: {from_phase.value} → {to_phase.value}")

        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        # 前フェーズ終了
        cursor.execute(
            """
            UPDATE phase_history
            SET end_time = ?, status = 'completed'
            WHERE execution_id = ? AND phase = ? AND end_time IS NULL
        """,
            (datetime.now().isoformat(), execution_id, from_phase.value),
        )

        # 新フェーズ開始
        cursor.execute(
            """
            INSERT INTO phase_history (execution_id, phase, status, start_time, details)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                execution_id,
                to_phase.value,
                FlowStatus.IN_PROGRESS.value,
                datetime.now().isoformat(),
                json.dumps(details) if details else None,
            ),
        )

        # メイン実行記録更新
        cursor.execute(
            """
            UPDATE flow_executions
            SET phase = ?
            WHERE execution_id = ?
        """,
            (to_phase.value, execution_id),
        )

        conn.commit()
        conn.close()

    async def record_sage_recommendation(
        self, execution_id: str, sage_name: str, recommendation: Dict[str, Any]
    ):
        """賢者推奨記録"""
        self.logger.info(f"🧙‍♂️ {sage_name}からの推奨記録")

        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        # 現在の推奨を取得
        cursor.execute(
            """
            SELECT sage_recommendations FROM flow_executions
            WHERE execution_id = ?
        """,
            (execution_id,),
        )

        result = cursor.fetchone()
        if result:
            recommendations = json.loads(result[0]) if result[0] else []
            recommendations.append(
                {
                    "sage": sage_name,
                    "recommendation": recommendation,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            cursor.execute(
                """
                UPDATE flow_executions
                SET sage_recommendations = ?
                WHERE execution_id = ?
            """,
                (json.dumps(recommendations), execution_id),
            )

            conn.commit()

        conn.close()

    async def record_violation(
        self,
        execution_id: str,
        violation_type: str,
        severity: str,
        location: str,
        description: str,
    ):
        """違反記録"""
        self.logger.warning(f"⚠️ 違反検出: {violation_type} ({severity})")

        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO violation_records (
                execution_id, violation_type, severity, location, description
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (execution_id, violation_type, severity, location, description),
        )

        # 違反数更新
        cursor.execute(
            """
            UPDATE flow_executions
            SET violations_found = violations_found + 1
            WHERE execution_id = ?
        """,
            (execution_id,),
        )

        conn.commit()
        conn.close()

    async def record_violation_fix(
        self, execution_id: str, violation_id: int, fix_details: str
    ):
        """違反修正記録"""
        self.logger.info(f"✅ 違反修正: ID {violation_id}")

        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE violation_records
            SET fixed = TRUE, fix_details = ?, fixed_at = ?
            WHERE id = ? AND execution_id = ?
        """,
            (fix_details, datetime.now().isoformat(), violation_id, execution_id),
        )

        # 修正数更新
        cursor.execute(
            """
            UPDATE flow_executions
            SET violations_fixed = violations_fixed + 1
            WHERE execution_id = ?
        """,
            (execution_id,),
        )

        conn.commit()
        conn.close()

    async def record_quality_metric(
        self,
        execution_id: str,
        metric_name: str,
        metric_value: float,
        threshold: float = None,
    ):
        """品質メトリクス記録"""
        passed = metric_value >= threshold if threshold else True

        self.logger.info(
            f"📊 品質メトリクス: {metric_name} = {metric_value} "
            f"({'PASS' if passed else 'FAIL'})"
        )

        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO quality_metrics (
                execution_id, metric_name, metric_value, threshold, passed
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (execution_id, metric_name, metric_value, threshold, passed),
        )

        conn.commit()
        conn.close()

    async def complete_flow_execution(
        self,
        execution_id: str,
        status: FlowStatus,
        quality_score: float,
        git_commits: List[str] = None,
    ):
        """フロー実行完了"""
        end_time = datetime.now()

        self.logger.info(f"🏁 Elder Flow実行完了: {execution_id} - {status.value}")

        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        # 開始時刻取得
        cursor.execute(
            """
            SELECT start_time FROM flow_executions
            WHERE execution_id = ?
        """,
            (execution_id,),
        )

        result = cursor.fetchone()
        if result:
            start_time = datetime.fromisoformat(result[0])
            duration = (end_time - start_time).total_seconds()

            cursor.execute(
                """
                UPDATE flow_executions
                SET status = ?, end_time = ?, duration_seconds = ?,
                    quality_score = ?, git_commits = ?
                WHERE execution_id = ?
            """,
                (
                    status.value,
                    end_time.isoformat(),
                    duration,
                    quality_score,
                    json.dumps(git_commits) if git_commits else None,
                    execution_id,
                ),
            )

            conn.commit()

        conn.close()

        # メトリクス更新
        await self._update_global_metrics()

    async def _update_global_metrics(self):
        """グローバルメトリクス更新"""
        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        # 統計取得
        cursor.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                AVG(quality_score) as avg_quality,
                SUM(violations_found) as total_violations_found,
                SUM(violations_fixed) as total_violations_fixed,
                AVG(duration_seconds) as avg_duration
            FROM flow_executions
            WHERE end_time IS NOT NULL
        """
        )

        stats = cursor.fetchone()

        if stats:
            metrics = {
                "total_executions": stats[0] or 0,
                "successful_executions": stats[1] or 0,
                "failed_executions": stats[2] or 0,
                "average_quality_score": round(stats[3] or 0, 2),
                "total_violations_found": stats[4] or 0,
                "total_violations_fixed": stats[5] or 0,
                "average_execution_time": round(stats[6] or 0, 2),
                "phase_success_rates": await self._calculate_phase_success_rates(
                    cursor
                ),
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.metrics_file, "w") as f:
                json.dump(metrics, f, indent=2)

        conn.close()

    async def _calculate_phase_success_rates(self, cursor) -> Dict[str, float]:
        """フェーズ成功率計算"""
        rates = {}

        for phase in FlowPhase:
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful
                FROM phase_history
                WHERE phase = ?
            """,
                (phase.value,),
            )

            result = cursor.fetchone()
            if result and result[0] > 0:
                rates[phase.value] = round((result[1] / result[0]) * 100, 2)
            else:
                rates[phase.value] = 0.0

        return rates

    async def generate_execution_report(self, execution_id: str) -> str:
        """実行レポート生成"""
        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        # 実行情報取得
        cursor.execute(
            """
            SELECT * FROM flow_executions
            WHERE execution_id = ?
        """,
            (execution_id,),
        )

        execution = cursor.fetchone()
        if not execution:
            return "実行記録が見つかりません"

        # フェーズ履歴取得
        cursor.execute(
            """
            SELECT phase, status, start_time, end_time
            FROM phase_history
            WHERE execution_id = ?
            ORDER BY start_time
        """,
            (execution_id,),
        )

        phases = cursor.fetchall()

        # 違反記録取得
        cursor.execute(
            """
            SELECT violation_type, severity, fixed
            FROM violation_records
            WHERE execution_id = ?
        """,
            (execution_id,),
        )

        violations = cursor.fetchall()

        # 品質メトリクス取得
        cursor.execute(
            """
            SELECT metric_name, metric_value, threshold, passed
            FROM quality_metrics
            WHERE execution_id = ?
        """,
            (execution_id,),
        )

        metrics = cursor.fetchall()

        conn.close()

        # レポート生成
        report = f"""
# Elder Flow実行レポート
## 実行ID: {execution_id}

### 📋 基本情報
- **タスク名**: {execution[1]}
- **優先度**: {execution[2]}
- **ステータス**: {execution[4]}
- **開始時刻**: {execution[5]}
- **終了時刻**: {execution[6] or 'N/A'}
- **実行時間**: {execution[7] or 0:0.2f}秒
- **品質スコア**: {execution[8] or 0:0.2f}/100

### 🔄 フェーズ進行
"""

        for phase in phases:
            report += (
                f"- **{phase[0]}**: {phase[1]} ({phase[2]} → {phase[3] or '進行中'})\n"
            )

        report += f"""
### ⚠️ 違反記録
- **発見数**: {execution[9]}
- **修正数**: {execution[10]}

違反詳細:
"""

        for violation in violations:
            status = "✅ 修正済" if violation[2] else "❌ 未修正"
            report += f"- {violation[0]} ({violation[1]}): {status}\n"

        report += "\n### 📊 品質メトリクス\n"

        for metric in metrics:
            status = "✅" if metric[3] else "❌"
            report += (
                f"- **{metric[0]}**: {metric[1]} / {metric[2] or 'N/A'} {status}\n"
            )

        # 賢者推奨
        if execution[11]:
            recommendations = json.loads(execution[11])
            report += f"\n### 🧙‍♂️ 賢者推奨 ({len(recommendations)}件)\n"
            for rec in recommendations:
                report += f"- **{rec['sage']}**: {rec['recommendation'].get('summary', 'N/A')}\n"

        # Gitコミット
        if execution[13]:
            commits = json.loads(execution[13])
            report += f"\n### 📤 Gitコミット ({len(commits)}件)\n"
            for commit in commits:
                report += f"- {commit}\n"

        return report

    async def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """実行履歴取得"""
        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT execution_id, task_name, status, quality_score,
                   start_time, end_time, duration_seconds
            FROM flow_executions
            ORDER BY start_time DESC
            LIMIT ?
        """,
            (limit,),
        )

        history = []
        for row in cursor.fetchall():
            history.append(
                {
                    "execution_id": row[0],
                    "task_name": row[1],
                    "status": row[2],
                    "quality_score": row[3],
                    "start_time": row[4],
                    "end_time": row[5],
                    "duration": row[6],
                }
            )

        conn.close()
        return history

    async def monitor_active_flows(self) -> List[Dict[str, Any]]:
        """アクティブフロー監視"""
        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT execution_id, task_name, phase, start_time
            FROM flow_executions
            WHERE status = 'in_progress'
            ORDER BY start_time DESC
        """
        )

        active_flows = []
        for row in cursor.fetchall():
            duration = (datetime.now() - datetime.fromisoformat(row[3])).total_seconds()
            active_flows.append(
                {
                    "execution_id": row[0],
                    "task_name": row[1],
                    "current_phase": row[2],
                    "duration_seconds": duration,
                }
            )

        conn.close()
        return active_flows


# CLI実行
async def main():
    """メイン実行"""
    system = ElderFlowCoreEnhancement()

    print("🌊 Elder Flow Core Enhancement System")
    print("=" * 50)

    # テスト実行
    execution_id = await system.start_flow_execution("Test Task", "high")
    print(f"✅ 実行開始: {execution_id}")

    # フェーズ遷移
    await system.record_phase_transition(
        execution_id, FlowPhase.SAGE_CONSULTATION, FlowPhase.SERVANT_EXECUTION
    )

    # 賢者推奨記録
    await system.record_sage_recommendation(
        execution_id,
        "ナレッジ賢者",
        {"summary": "TDD実装推奨", "details": "テストファースト開発"},
    )

    # 違反記録
    await system.record_violation(
        execution_id,
        "abstract_method",
        "critical",
        "workers/test_worker.py",
        "validate_config未実装",
    )

    # 品質メトリクス
    await system.record_quality_metric(execution_id, "coverage", 85.5, 80.0)
    await system.record_quality_metric(execution_id, "complexity", 15.2, 20.0)

    # 実行完了
    await system.complete_flow_execution(
        execution_id, FlowStatus.COMPLETED, 85.5, ["feat: test implementation"]
    )

    # レポート生成
    report = await system.generate_execution_report(execution_id)
    print("\n" + report)

    # 履歴表示
    print("\n📊 実行履歴:")
    history = await system.get_execution_history(5)
    for h in history:
        print(f"- {h['execution_id']}: {h['task_name']} ({h['status']})")


if __name__ == "__main__":
    asyncio.run(main())
