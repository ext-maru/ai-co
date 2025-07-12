#!/usr/bin/env python3
"""
Learning Data Collection System v0.1
過去の指示と実行結果をペアで収集・学習

🎯 nWo Learning Data Collector Implementation
Collect and learn from maru様's commands and results
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import logging
import hashlib

from libs.mind_reading_core import IntentResult, IntentType
from libs.intent_parser import ParsedCommand, CommandType


class ExecutionStatus(Enum):
    """実行ステータス"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"
    CANCELLED = "cancelled"


class DataQuality(Enum):
    """データ品質"""
    HIGH = "high"         # 成功＋詳細なフィードバック
    MEDIUM = "medium"     # 成功またはフィードバックあり
    LOW = "low"           # 失敗または最小限の情報
    UNVERIFIED = "unverified"  # 未検証


@dataclass
class CommandExecution:
    """コマンド実行記録"""
    execution_id: str
    original_text: str
    intent_result: Dict[str, Any]  # IntentResultのJSON表現
    parsed_command: Dict[str, Any]  # ParsedCommandのJSON表現
    executed_command: str
    execution_time: float
    status: ExecutionStatus
    output: str
    error: Optional[str]
    feedback: Optional[Dict[str, Any]]
    quality: DataQuality
    timestamp: str


@dataclass
class LearningPattern:
    """学習パターン"""
    pattern_id: str
    intent_type: str
    command_type: str
    success_count: int
    failure_count: int
    avg_execution_time: float
    common_parameters: Dict[str, Any]
    best_practices: List[str]
    common_errors: List[str]
    last_updated: str


@dataclass
class InsightReport:
    """洞察レポート"""
    report_id: str
    period: str
    total_executions: int
    success_rate: float
    avg_confidence: float
    top_intents: List[Tuple[str, int]]
    top_commands: List[Tuple[str, int]]
    improvement_suggestions: List[str]
    generated_at: str


class LearningDataCollector:
    """Learning Data Collector - 指示と結果のペア収集・学習"""

    def __init__(self, db_path: str = "data/learning_data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger = self._setup_logger()

        # データベース初期化
        self._init_database()

        # メモリキャッシュ
        self.execution_cache: Dict[str, CommandExecution] = {}
        self.pattern_cache: Dict[str, LearningPattern] = {}

        self.logger.info("🎯 Learning Data Collector v0.1 initialized")

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("learning_data_collector")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - Learning Collector - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _init_database(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # コマンド実行履歴テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_executions (
                execution_id TEXT PRIMARY KEY,
                original_text TEXT NOT NULL,
                intent_result TEXT NOT NULL,
                parsed_command TEXT NOT NULL,
                executed_command TEXT NOT NULL,
                execution_time REAL NOT NULL,
                status TEXT NOT NULL,
                output TEXT,
                error TEXT,
                feedback TEXT,
                quality TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # 学習パターンテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_patterns (
                pattern_id TEXT PRIMARY KEY,
                intent_type TEXT NOT NULL,
                command_type TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                avg_execution_time REAL DEFAULT 0.0,
                common_parameters TEXT,
                best_practices TEXT,
                common_errors TEXT,
                last_updated TEXT NOT NULL
            )
        """)

        # 洞察レポートテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insight_reports (
                report_id TEXT PRIMARY KEY,
                period TEXT NOT NULL,
                total_executions INTEGER NOT NULL,
                success_rate REAL NOT NULL,
                avg_confidence REAL NOT NULL,
                top_intents TEXT NOT NULL,
                top_commands TEXT NOT NULL,
                improvement_suggestions TEXT NOT NULL,
                generated_at TEXT NOT NULL
            )
        """)

        # インデックス作成
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON command_executions(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_intent_type ON learning_patterns(intent_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_command_type ON learning_patterns(command_type)")

        conn.commit()
        conn.close()

    async def record_execution(
        self,
        original_text: str,
        intent_result: IntentResult,
        parsed_command: ParsedCommand,
        executed_command: str,
        execution_time: float,
        status: ExecutionStatus,
        output: str = "",
        error: Optional[str] = None,
        feedback: Optional[Dict[str, Any]] = None
    ) -> CommandExecution:
        """
        コマンド実行の記録

        Args:
            original_text: 元の入力テキスト
            intent_result: 意図理解結果
            parsed_command: パース済みコマンド
            executed_command: 実際に実行されたコマンド
            execution_time: 実行時間（秒）
            status: 実行ステータス
            output: 実行出力
            error: エラー情報
            feedback: フィードバック情報

        Returns:
            CommandExecution: 記録された実行情報
        """
        # 実行IDの生成
        execution_id = self._generate_execution_id(original_text, executed_command)

        # データ品質の判定
        quality = self._assess_data_quality(status, output, feedback)

        # IntentResultとParsedCommandをJSON形式に変換
        intent_dict = asdict(intent_result)
        intent_dict["intent_type"] = intent_result.intent_type.value
        intent_dict["confidence_level"] = intent_result.confidence_level.value

        command_dict = asdict(parsed_command)
        command_dict["command_type"] = parsed_command.command_type.value

        # 実行記録の作成
        execution = CommandExecution(
            execution_id=execution_id,
            original_text=original_text,
            intent_result=intent_dict,
            parsed_command=command_dict,
            executed_command=executed_command,
            execution_time=execution_time,
            status=status,
            output=output[:5000],  # 最大5000文字
            error=error,
            feedback=feedback,
            quality=quality,
            timestamp=datetime.now().isoformat()
        )

        # データベースに保存
        await self._save_execution(execution)

        # パターン更新
        await self._update_patterns(execution)

        # キャッシュ更新
        self.execution_cache[execution_id] = execution

        self.logger.info(f"📝 Recorded execution: {execution_id} ({status.value})")

        return execution

    def _generate_execution_id(self, original_text: str, command: str) -> str:
        """実行IDの生成"""
        content = f"{original_text}:{command}:{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _assess_data_quality(
        self,
        status: ExecutionStatus,
        output: str,
        feedback: Optional[Dict]
    ) -> DataQuality:
        """データ品質の評価"""
        if status == ExecutionStatus.SUCCESS:
            if feedback and len(output) > 100:
                return DataQuality.HIGH
            else:
                return DataQuality.MEDIUM
        elif status == ExecutionStatus.PARTIAL:
            return DataQuality.MEDIUM
        else:
            return DataQuality.LOW

    async def _save_execution(self, execution: CommandExecution):
        """実行記録の保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO command_executions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution.execution_id,
                execution.original_text,
                json.dumps(execution.intent_result, ensure_ascii=False),
                json.dumps(execution.parsed_command, ensure_ascii=False),
                execution.executed_command,
                execution.execution_time,
                execution.status.value,
                execution.output,
                execution.error,
                json.dumps(execution.feedback, ensure_ascii=False) if execution.feedback else None,
                execution.quality.value,
                execution.timestamp
            ))

            conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save execution: {e}")
        finally:
            conn.close()

    async def _update_patterns(self, execution: CommandExecution):
        """学習パターンの更新"""
        intent_type = execution.intent_result["intent_type"]
        command_type = execution.parsed_command["command_type"]
        pattern_id = f"{intent_type}_{command_type}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 既存パターンの取得
            cursor.execute("""
                SELECT * FROM learning_patterns WHERE pattern_id = ?
            """, (pattern_id,))

            existing = cursor.fetchone()

            if existing:
                # 更新
                success_count = existing[3]
                failure_count = existing[4]
                avg_time = existing[5]

                if execution.status == ExecutionStatus.SUCCESS:
                    success_count += 1
                else:
                    failure_count += 1

                # 実行時間の更新（移動平均）
                total_count = success_count + failure_count
                avg_time = (avg_time * (total_count - 1) + execution.execution_time) / total_count

                cursor.execute("""
                    UPDATE learning_patterns
                    SET success_count = ?, failure_count = ?, avg_execution_time = ?, last_updated = ?
                    WHERE pattern_id = ?
                """, (success_count, failure_count, avg_time, datetime.now().isoformat(), pattern_id))
            else:
                # 新規作成
                cursor.execute("""
                    INSERT INTO learning_patterns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern_id,
                    intent_type,
                    command_type,
                    1 if execution.status == ExecutionStatus.SUCCESS else 0,
                    0 if execution.status == ExecutionStatus.SUCCESS else 1,
                    execution.execution_time,
                    json.dumps({}),
                    json.dumps([]),
                    json.dumps([]),
                    datetime.now().isoformat()
                ))

            conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to update patterns: {e}")
        finally:
            conn.close()

    async def get_similar_executions(
        self,
        intent_type: IntentType,
        command_type: CommandType,
        limit: int = 10
    ) -> List[CommandExecution]:
        """
        類似した実行履歴の取得

        Args:
            intent_type: 意図タイプ
            command_type: コマンドタイプ
            limit: 取得件数上限

        Returns:
            List[CommandExecution]: 類似実行履歴
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM command_executions
                WHERE json_extract(intent_result, '$.intent_type') = ?
                AND json_extract(parsed_command, '$.command_type') = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (intent_type.value, command_type.value, limit))

            rows = cursor.fetchall()
            executions = []

            for row in rows:
                execution = CommandExecution(
                    execution_id=row[0],
                    original_text=row[1],
                    intent_result=json.loads(row[2]),
                    parsed_command=json.loads(row[3]),
                    executed_command=row[4],
                    execution_time=row[5],
                    status=ExecutionStatus(row[6]),
                    output=row[7] or "",
                    error=row[8],
                    feedback=json.loads(row[9]) if row[9] else None,
                    quality=DataQuality(row[10]),
                    timestamp=row[11]
                )
                executions.append(execution)

            return executions

        except Exception as e:
            self.logger.error(f"Failed to get similar executions: {e}")
            return []
        finally:
            conn.close()

    async def get_success_patterns(self, intent_type: Optional[IntentType] = None) -> List[LearningPattern]:
        """
        成功パターンの取得

        Args:
            intent_type: フィルタする意図タイプ（省略時は全て）

        Returns:
            List[LearningPattern]: 成功率の高いパターン
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if intent_type:
                cursor.execute("""
                    SELECT * FROM learning_patterns
                    WHERE intent_type = ? AND success_count > failure_count
                    ORDER BY (success_count * 1.0 / (success_count + failure_count)) DESC
                """, (intent_type.value,))
            else:
                cursor.execute("""
                    SELECT * FROM learning_patterns
                    WHERE success_count > failure_count
                    ORDER BY (success_count * 1.0 / (success_count + failure_count)) DESC
                """)

            rows = cursor.fetchall()
            patterns = []

            for row in rows:
                pattern = LearningPattern(
                    pattern_id=row[0],
                    intent_type=row[1],
                    command_type=row[2],
                    success_count=row[3],
                    failure_count=row[4],
                    avg_execution_time=row[5],
                    common_parameters=json.loads(row[6]),
                    best_practices=json.loads(row[7]),
                    common_errors=json.loads(row[8]),
                    last_updated=row[9]
                )
                patterns.append(pattern)

            return patterns

        except Exception as e:
            self.logger.error(f"Failed to get success patterns: {e}")
            return []
        finally:
            conn.close()

    async def generate_insights(self, period_days: int = 7) -> InsightReport:
        """
        洞察レポートの生成

        Args:
            period_days: 分析期間（日数）

        Returns:
            InsightReport: 生成された洞察レポート
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 期間の計算
            start_date = (datetime.now() - timedelta(days=period_days)).isoformat()

            # 基本統計
            cursor.execute("""
                SELECT COUNT(*),
                       SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END),
                       AVG(json_extract(intent_result, '$.confidence'))
                FROM command_executions
                WHERE timestamp > ?
            """, (start_date,))

            total, success_count, avg_confidence = cursor.fetchone()
            success_rate = success_count / total if total > 0 else 0.0

            # トップ意図
            cursor.execute("""
                SELECT json_extract(intent_result, '$.intent_type'), COUNT(*) as cnt
                FROM command_executions
                WHERE timestamp > ?
                GROUP BY json_extract(intent_result, '$.intent_type')
                ORDER BY cnt DESC
                LIMIT 5
            """, (start_date,))

            top_intents = cursor.fetchall()

            # トップコマンド
            cursor.execute("""
                SELECT json_extract(parsed_command, '$.command_type'), COUNT(*) as cnt
                FROM command_executions
                WHERE timestamp > ?
                GROUP BY json_extract(parsed_command, '$.command_type')
                ORDER BY cnt DESC
                LIMIT 5
            """, (start_date,))

            top_commands = cursor.fetchall()

            # 改善提案の生成
            improvement_suggestions = self._generate_improvement_suggestions(
                success_rate, avg_confidence, top_intents, top_commands
            )

            # レポート作成
            report = InsightReport(
                report_id=f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                period=f"{period_days}_days",
                total_executions=total or 0,
                success_rate=success_rate,
                avg_confidence=avg_confidence or 0.0,
                top_intents=top_intents,
                top_commands=top_commands,
                improvement_suggestions=improvement_suggestions,
                generated_at=datetime.now().isoformat()
            )

            # レポート保存
            await self._save_insight_report(report)

            return report

        except Exception as e:
            self.logger.error(f"Failed to generate insights: {e}")
            # エラー時のデフォルトレポート
            return InsightReport(
                report_id="error_report",
                period=f"{period_days}_days",
                total_executions=0,
                success_rate=0.0,
                avg_confidence=0.0,
                top_intents=[],
                top_commands=[],
                improvement_suggestions=["データ取得エラーが発生しました"],
                generated_at=datetime.now().isoformat()
            )
        finally:
            conn.close()

    def _generate_improvement_suggestions(
        self,
        success_rate: float,
        avg_confidence: float,
        top_intents: List[Tuple[str, int]],
        top_commands: List[Tuple[str, int]]
    ) -> List[str]:
        """改善提案の生成"""
        suggestions = []

        # 成功率に基づく提案
        if success_rate < 0.7:
            suggestions.append("成功率が70%未満です。失敗パターンを分析し、エラーハンドリングを改善してください。")

        # 信頼度に基づく提案
        if avg_confidence < 0.6:
            suggestions.append("平均信頼度が低いです。より明確な指示パターンを学習させることを検討してください。")

        # 意図の偏りチェック
        if top_intents and top_intents[0][1] > sum(count for _, count in top_intents) * 0.5:
            suggestions.append(f"{top_intents[0][0]}の使用が多すぎます。他の機能も活用してバランスを取りましょう。")

        # コマンドの多様性チェック
        if len(top_commands) < 3:
            suggestions.append("使用されているコマンドタイプが少ないです。より多様な操作を試してみてください。")

        # デフォルト提案
        if not suggestions:
            suggestions.append("順調に稼働しています。現在の使用パターンを継続してください。")

        return suggestions

    async def _save_insight_report(self, report: InsightReport):
        """洞察レポートの保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO insight_reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.report_id,
                report.period,
                report.total_executions,
                report.success_rate,
                report.avg_confidence,
                json.dumps(report.top_intents),
                json.dumps(report.top_commands),
                json.dumps(report.improvement_suggestions, ensure_ascii=False),
                report.generated_at
            ))

            conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save insight report: {e}")
        finally:
            conn.close()

    async def export_training_data(self, output_path: str, quality_threshold: DataQuality = DataQuality.MEDIUM):
        """
        トレーニングデータのエクスポート

        Args:
            output_path: 出力ファイルパス
            quality_threshold: 品質閾値
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 品質基準を満たすデータを取得
            quality_values = {
                DataQuality.HIGH: ["high"],
                DataQuality.MEDIUM: ["high", "medium"],
                DataQuality.LOW: ["high", "medium", "low"],
                DataQuality.UNVERIFIED: ["high", "medium", "low", "unverified"]
            }

            placeholders = ",".join("?" * len(quality_values[quality_threshold]))
            cursor.execute(f"""
                SELECT original_text, intent_result, parsed_command,
                       executed_command, status, output
                FROM command_executions
                WHERE quality IN ({placeholders})
                AND status = 'success'
            """, quality_values[quality_threshold])

            rows = cursor.fetchall()

            # トレーニングデータ形式に変換
            training_data = []
            for row in rows:
                data = {
                    "input": row[0],
                    "intent": json.loads(row[1]),
                    "command": json.loads(row[2]),
                    "execution": row[3],
                    "output": row[5]
                }
                training_data.append(data)

            # ファイルに保存
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w') as f:
                json.dump(training_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Exported {len(training_data)} training samples to {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to export training data: {e}")
        finally:
            conn.close()

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報の取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            stats = {}

            # 総実行数
            cursor.execute("SELECT COUNT(*) FROM command_executions")
            stats["total_executions"] = cursor.fetchone()[0]

            # ステータス別カウント
            cursor.execute("""
                SELECT status, COUNT(*) FROM command_executions
                GROUP BY status
            """)
            stats["status_counts"] = dict(cursor.fetchall())

            # 品質別カウント
            cursor.execute("""
                SELECT quality, COUNT(*) FROM command_executions
                GROUP BY quality
            """)
            stats["quality_counts"] = dict(cursor.fetchall())

            # パターン数
            cursor.execute("SELECT COUNT(*) FROM learning_patterns")
            stats["total_patterns"] = cursor.fetchone()[0]

            # 平均実行時間
            cursor.execute("SELECT AVG(execution_time) FROM command_executions")
            stats["avg_execution_time"] = cursor.fetchone()[0] or 0.0

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}
        finally:
            conn.close()


# デモと使用例
async def demo_learning_collector():
    """Learning Data Collector デモ"""
    print("🎯 Learning Data Collector v0.1 Demo")
    print("=" * 50)

    from libs.mind_reading_core import MindReadingCore
    from libs.intent_parser import IntentParser

    # 初期化
    mind_reader = MindReadingCore()
    parser = IntentParser()
    collector = LearningDataCollector()

    # テスト実行
    test_text = "OAuth2.0認証システムを実装してください"

    # 意図理解とパース
    intent_result = await mind_reader.understand_intent(test_text)
    parsed_command = await parser.parse_intent(intent_result, test_text)
    command = await parser.generate_command(parsed_command)

    # 実行記録（シミュレーション）
    execution = await collector.record_execution(
        original_text=test_text,
        intent_result=intent_result,
        parsed_command=parsed_command,
        executed_command=command,
        execution_time=2.5,
        status=ExecutionStatus.SUCCESS,
        output="OAuth2.0 authentication system implemented successfully",
        feedback={"accuracy": 0.9, "usefulness": "high"}
    )

    print(f"\n📝 Recorded execution: {execution.execution_id}")
    print(f"Status: {execution.status.value}")
    print(f"Quality: {execution.quality.value}")

    # 統計情報
    stats = collector.get_statistics()
    print(f"\n📊 Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 洞察レポート生成
    report = await collector.generate_insights(period_days=7)
    print(f"\n🔍 Insight Report:")
    print(f"Total executions: {report.total_executions}")
    print(f"Success rate: {report.success_rate:.2%}")
    print(f"Average confidence: {report.avg_confidence:.2f}")
    print(f"Suggestions: {', '.join(report.improvement_suggestions)}")


if __name__ == "__main__":
    asyncio.run(demo_learning_collector())
