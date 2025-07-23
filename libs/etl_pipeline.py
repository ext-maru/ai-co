#!/usr/bin/env python3
"""
ETLデータパイプライン実装
エルダーズギルドのデータ収集・変換・ロード処理

設計: RAGエルダー × クロードエルダー
承認: エルダーズ評議会
実装日: 2025年7月10日
"""

import asyncio
import hashlib
import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

import aiofiles
import numpy as np
import pandas as pd

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSource(Enum):
    """データソース種別"""

    LOG_FILES = "log_files"
    DATABASE = "database"
    API_ENDPOINTS = "api_endpoints"
    KNOWLEDGE_BASE = "knowledge_base"
    METRICS_STREAM = "metrics_stream"


@dataclass
class ETLJob:
    """ETLジョブ定義"""

    job_id: str
    source: DataSource
    target: str
    transform_rules: Dict[str, Any]
    schedule: Optional[str] = None
    status: str = "pending"
    created_at: datetime = None

    def __post_init__(self):
        """__post_init__特殊メソッド"""
        if self.created_at is None:
            self.created_at = datetime.now()


class DataExtractor:
    """データ抽出エンジン"""

    def __init__(self, project_root:
        """初期化メソッド"""
    Path):
        self.project_root = Path(project_root)
        self.cache_dir = self.project_root / ".etl_cache"
        self.cache_dir.mkdir(exist_ok=True)

    async def extract_from_logs(
        self, log_pattern: str = "*.log"
    ) -> AsyncIterator[Dict]:
        """ログファイルからデータ抽出"""
        logs_dir = self.project_root / "logs"

        async for log_file in self._async_glob(logs_dir, log_pattern):
            async with aiofiles.open(log_file, "r", encoding="utf-8") as f:
                content = await f.read()

            for line in content.splitlines():
                if not line.strip():
                    continue

                parsed = self._parse_log_line(line)
                if parsed:
                    yield {
                        "source": str(log_file),
                        "timestamp": parsed.get("timestamp", datetime.now()),
                        "data": parsed,
                    }

    async def extract_from_database(self, query: str, db_path: Path) -> pd.DataFrame:
        """データベースからデータ抽出"""
        try:
            conn = sqlite3.connect(str(db_path))
            df = pd.read_sql_query(query, conn)
            conn.close()

            logger.info(f"✅ データベースから{len(df)}件のレコードを抽出")
            return df

        except Exception as e:
            logger.error(f"❌ データベース抽出エラー: {e}")
            return pd.DataFrame()

    async def extract_from_api(self, endpoint: str, params: Dict = None) -> Dict:
        """APIエンドポイントからデータ抽出"""
        # 実際のAPI実装ではaiohttp等を使用
        # ここではモック実装
        mock_data = {
            "endpoint": endpoint,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "metrics": {
                    "requests_per_second": 45.2,
                    "error_rate": 0.02,
                    "average_response_time": 120,
                }
            },
        }
        return mock_data

    async def extract_from_knowledge_base(self, pattern: str = "*.md") -> List[Dict]:
        """ナレッジベースからデータ抽出"""
        kb_dir = self.project_root / "knowledge_base"
        documents = []

        async for doc_file in self._async_glob(kb_dir, pattern):
            async with aiofiles.open(doc_file, "r", encoding="utf-8") as f:
                content = await f.read()

            metadata = self._extract_document_metadata(content)
            documents.append(
                {
                    "file": str(doc_file),
                    "metadata": metadata,
                    "content_hash": hashlib.md5(content.encode()).hexdigest(),
                    "size": len(content),
                    "extracted_at": datetime.now(),
                }
            )

        return documents

    async def _async_glob(self, directory: Path, pattern: str) -> AsyncIterator[Path]:
        """非同期ファイル検索"""
        for file_path in directory.glob(pattern):
            yield file_path

    def _parse_log_line(self, line: str) -> Optional[Dict]:
        """ログ行のパース"""
        # 簡易パーサー実装
        import re

        # タイムスタンプとレベルを抽出
        pattern = r"\[(\w+)\]\s+(.+)"
        match = re.match(pattern, line)

        if match:
            return {"level": match.group(1), "message": match.group(2), "raw": line}
        return None

    def _extract_document_metadata(self, content: str) -> Dict:
        """ドキュメントメタデータ抽出"""
        metadata = {"title": None, "author": None, "date": None, "tags": []}

        lines = content.split("\n")
        for line in lines[:10]:  # 最初の10行をチェック
            if line.startswith("# "):
                metadata["title"] = line[2:].strip()
            elif "作成者:" in line or "Author:" in line:
                metadata["author"] = line.split(":")[1].strip()
            elif "日付:" in line or "Date:" in line:
                metadata["date"] = line.split(":")[1].strip()

        return metadata


class DataTransformer:
    """データ変換エンジン"""

    def __init__(self):
        """初期化メソッド"""
        self.transformations = {
            "normalize": self._normalize,
            "aggregate": self._aggregate,
            "filter": self._filter,
            "enrich": self._enrich,
            "pivot": self._pivot,
        }

    async def transform(
        self, data: pd.DataFrame, rules: Dict[str, Any]
    ) -> pd.DataFrame:
        """ルールベースデータ変換"""
        result = data.copy()

        for transform_type, params in rules.items():
            if transform_type in self.transformations:
                transform_func = self.transformations[transform_type]
                result = await transform_func(result, params)
                logger.info(f"✅ {transform_type}変換を適用")

        return result

    async def _normalize(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """データ正規化"""
        columns = params.get("columns", [])
        method = params.get("method", "minmax")

        for col in columns:
            if col in df.columns and df[col].dtype in ["float64", "int64"]:
                if method == "minmax":
                    df[col] = (df[col] - df[col].min()) / (
                        df[col].max() - df[col].min()
                    )
                elif method == "zscore":
                    df[col] = (df[col] - df[col].mean()) / df[col].std()

        return df

    async def _aggregate(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """データ集約"""
        group_by = params.get("group_by", [])
        agg_funcs = params.get("functions", {"count": "size"})

        if group_by:
            return df.groupby(group_by).agg(agg_funcs).reset_index()
        return df

    async def _filter(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """データフィルタリング"""
        conditions = params.get("conditions", {})

        for column, condition in conditions.items():
            if column in df.columns:
                operator = condition.get("operator", "==")
                value = condition.get("value")

                if operator == "==":
                    df = df[df[column] == value]
                elif operator == ">":
                    df = df[df[column] > value]
                elif operator == "<":
                    df = df[df[column] < value]
                elif operator == "in":
                    df = df[df[column].isin(value)]

        return df

    async def _enrich(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """データエンリッチメント"""
        # 派生フィールド追加
        derived_fields = params.get("derived_fields", {})

        for field_name, expression in derived_fields.items():
            try:
                # セキュリティ修正: evalを使わない安全な実装
                # サポートする演算を制限
                if expression.startswith("df[") and "]" in expression:
                    # 単純なカラム参照
                    col_name = expression[3:expression.index("]")].strip("'\"")
                    df[field_name] = df[col_name]
                else:
                    logger.warning(f"⚠️ 派生フィールド{field_name}の式がサポートされていません: {expression}")
            except Exception as e:
                logger.warning(f"⚠️ 派生フィールド{field_name}の作成失敗: {e}")

        return df

    async def _pivot(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """ピボット変換"""
        index = params.get("index")
        columns = params.get("columns")
        values = params.get("values")

        if all([index, columns, values]):
            return df.pivot_table(index=index, columns=columns, values=values)
        return df


class DataLoader:
    """データロードエンジン"""

    def __init__(self, project_root:
        """初期化メソッド"""
    Path):
        self.project_root = Path(project_root)
        self.output_dir = self.project_root / "etl_output"
        self.output_dir.mkdir(exist_ok=True)

    async def load_to_database(self, df: pd.DataFrame, table_name: str, db_path: Path):
        """データベースへのロード"""
        try:
            conn = sqlite3.connect(str(db_path))
            df.to_sql(table_name, conn, if_exists="append", index=False)
            conn.close()

            logger.info(f"✅ {len(df)}件のレコードを{table_name}テーブルにロード")

        except Exception as e:
            logger.error(f"❌ データベースロードエラー: {e}")

    async def load_to_file(self, data: Any, filename: str, format: str = "json"):
        """ファイルへのロード"""
        output_path = self.output_dir / filename

        try:
            if format == "json":
                async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(data, indent=2, default=str))

            elif format == "csv" and isinstance(data, pd.DataFrame):
                data.to_csv(output_path, index=False)

            elif format == "parquet" and isinstance(data, pd.DataFrame):
                data.to_parquet(output_path, index=False)

            logger.info(f"✅ データを{output_path}に保存")

        except Exception as e:
            logger.error(f"❌ ファイルロードエラー: {e}")

    async def load_to_cache(self, data: Any, cache_key: str, ttl: int = 3600):
        """キャッシュへのロード"""
        cache_file = self.project_root / ".etl_cache" / f"{cache_key}.cache"

        cache_data = {"data": data, "timestamp": datetime.now().isoformat(), "ttl": ttl}

        async with aiofiles.open(cache_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(cache_data, default=str))


class ETLPipeline:
    """ETLパイプライン統合"""

    def __init__(self, project_root:
        """初期化メソッド"""
    Path):
        self.project_root = Path(project_root)
        self.extractor = DataExtractor(project_root)
        self.transformer = DataTransformer()
        self.loader = DataLoader(project_root)
        self.jobs: List[ETLJob] = []

    async def create_job(self, job_config: Dict) -> ETLJob:
        """ETLジョブ作成"""
        job = ETLJob(
            job_id=f"etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            source=DataSource(job_config["source"]),
            target=job_config["target"],
            transform_rules=job_config.get("transform_rules", {}),
            schedule=job_config.get("schedule"),
        )

        self.jobs.append(job)
        logger.info(f"🚀 ETLジョブ作成: {job.job_id}")

        return job

    async def execute_job(self, job: ETLJob) -> Dict[str, Any]:
        """ETLジョブ実行"""
        logger.info(f"▶️ ジョブ実行開始: {job.job_id}")
        job.status = "running"

        try:
            # Extract
            data = await self._extract_phase(job)

            # Transform
            if isinstance(data, pd.DataFrame) and job.transform_rules:
                data = await self.transformer.transform(data, job.transform_rules)

            # Load
            await self._load_phase(job, data)

            job.status = "completed"
            logger.info(f"✅ ジョブ完了: {job.job_id}")

            return {
                "job_id": job.job_id,
                "status": "success",
                "records_processed": len(data) if hasattr(data, "__len__") else 1,
                "completed_at": datetime.now(),
            }

        except Exception as e:
            job.status = "failed"
            logger.error(f"❌ ジョブ失敗: {job.job_id} - {e}")

            return {
                "job_id": job.job_id,
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now(),
            }

    async def _extract_phase(self, job: ETLJob) -> Any:
        """抽出フェーズ実行"""
        if job.source == DataSource.LOG_FILES:
            data = []
            async for record in self.extractor.extract_from_logs():
                data.append(record)
            return pd.DataFrame(data)

        elif job.source == DataSource.DATABASE:
            query = job.transform_rules.get("query", "SELECT * FROM commits")
            db_path = self.project_root / "elder_dashboard.db"
            return await self.extractor.extract_from_database(query, db_path)

        elif job.source == DataSource.API_ENDPOINTS:
            endpoint = job.transform_rules.get("endpoint", "/metrics")
            return await self.extractor.extract_from_api(endpoint)

        elif job.source == DataSource.KNOWLEDGE_BASE:
            return await self.extractor.extract_from_knowledge_base()

        else:
            raise ValueError(f"未対応のデータソース: {job.source}")

    async def _load_phase(self, job: ETLJob, data: Any):
        """ロードフェーズ実行"""
        target_parts = job.target.split(":")
        target_type = target_parts[0]

        if target_type == "database":
            table_name = target_parts[1] if len(target_parts) > 1 else "etl_output"
            db_path = self.project_root / "elder_dashboard.db"
            await self.loader.load_to_database(data, table_name, db_path)

        elif target_type == "file":
            filename = (
                target_parts[1] if len(target_parts) > 1 else f"{job.job_id}.json"
            )
            format = target_parts[2] if len(target_parts) > 2 else "json"
            await self.loader.load_to_file(data, filename, format)

        elif target_type == "cache":
            cache_key = target_parts[1] if len(target_parts) > 1 else job.job_id
            await self.loader.load_to_cache(data, cache_key)

        else:
            raise ValueError(f"未対応のターゲット: {target_type}")

    async def run_scheduled_jobs(self):
        """スケジュールジョブ実行"""
        # 簡易スケジューラー実装
        # 実際はAPScheduler等を使用
        while True:
            for job in self.jobs:
                if job.schedule and job.status == "pending":
                    # スケジュールチェックロジック
                    await self.execute_job(job)

            await asyncio.sleep(60)  # 1分ごとにチェック


# サンプル使用例
async def main():
    """ETLパイプラインサンプル実行"""
    pipeline = ETLPipeline(Path("/home/aicompany/ai_co"))

    # ログファイルからメトリクスを抽出してデータベースに保存
    job_config = {
        "source": "log_files",
        "target": "database:etl_metrics",
        "transform_rules": {
            "filter": {
                "conditions": {
                    "level": {"operator": "in", "value": ["ERROR", "WARNING"]}
                }
            },
            "aggregate": {
                "group_by": ["level"],
                "functions": {"count": "size", "timestamp": "max"},
            },
        },
    }

    job = await pipeline.create_job(job_config)
    result = await pipeline.execute_job(job)
    print(f"ETLジョブ結果: {result}")


if __name__ == "__main__":
    asyncio.run(main())
