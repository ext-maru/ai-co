#!/usr/bin/env python3
"""
pytest統合テストフレームワーク - OSS移行版
既存のintegration_test_framework.pyをpytest + testcontainersで置き換え
"""
import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import pytest
from testcontainers.compose import DockerCompose
from testcontainers.postgres import PostgresContainer
import docker


class TestStatus(Enum):
    """テストステータス"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class ServiceStatus(Enum):
    """サービスステータス"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    UNHEALTHY = "unhealthy"
    STOPPING = "stopping"


@dataclass
class TestResult:
    """テスト結果"""
    name: str
    status: TestStatus
    duration: float = 0.0
    output: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class ServiceConfig:
    """サービス設定"""
    name: str
    image: str
    ports: Dict[str, int] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: Dict[str, str] = field(default_factory=dict)
    command: Optional[str] = None
    health_check: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)


class PytestIntegrationFramework:
    """pytest統合テストフレームワーク"""
    
    def __init__(self, project_name:
        """初期化メソッド"""
    str = "integration_test"):
        self.project_name = project_name
        self.logger = logging.getLogger(f"pytest_integration.{project_name}")
        self.containers = {}
        self.services = {}
        self.test_results = []
        self.docker_client = docker.from_env()
        
    def create_postgres_container(self, 
                                 db_name: str = "testdb",
                                 username: str = "testuser",
                                 password: str = "testpass") -> PostgresContainer:
        """PostgreSQLコンテナ作成"""
        container = PostgresContainer(
            "postgres:13",
            dbname=db_name,
            username=username,
            password=password
        )
        self.containers["postgres"] = container
        return container
    
    def create_compose_environment(self, compose_file: str) -> DockerCompose:
        """Docker Compose環境作成"""
        compose = DockerCompose(
            filepath=".",
            compose_file_name=compose_file,
            pull=True
        )
        self.containers["compose"] = compose
        return compose
    
    def setup_test_environment(self, services: List[ServiceConfig]):
        """テスト環境セットアップ"""
        self.logger.info(f"Setting up test environment with {len(services)} services")
        
        for service in services:
            self.services[service.name] = service
            self.logger.debug(f"Configured service: {service.name}")
    
    async def start_services(self) -> bool:
        """サービス起動"""
        try:
            for name, container in self.containers.items():
                self.logger.info(f"Starting container: {name}")
                container.start()
                
                # ヘルスチェック
                if hasattr(container, 'get_connection_url'):
                    connection_url = container.get_connection_url()
                    self.logger.info(f"Container {name} available at: {connection_url}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start services: {e}")
            return False
    
    async def stop_services(self):
        """サービス停止"""
        for name, container in self.containers.items():
            try:
                self.logger.info(f"Stopping container: {name}")
                container.stop()
            except Exception as e:
                self.logger.error(f"Failed to stop container {name}: {e}")
    
    def run_test_suite(self, test_path: str, 
                      pytest_args: List[str] = None) -> List[TestResult]:
        """pytest テストスイート実行"""
        if pytest_args is None:
            pytest_args = ['-v', '--tb=short']
        
        self.logger.info(f"Running pytest on: {test_path}")
        
        # pytest実行
        args = [test_path] + pytest_args
        result = pytest.main(args)
        
        # 結果記録
        test_result = TestResult(
            name=f"pytest_suite_{os.path.basename(test_path)}",
            status=TestStatus.PASSED if result == 0 else TestStatus.FAILED,
            duration=0.0,  # pytest自体で測定
            output=f"pytest exit code: {result}",
            metadata={"pytest_args": args}
        )
        
        self.test_results.append(test_result)
        return self.test_results
    
    def create_pytest_fixtures(self) -> str:
        """pytest fixtures生成"""
        fixtures_code = '''# Auto-generated pytest fixtures
import pytest

'''
        
        for name, container in self.containers.items():
            if name == "postgres":
                fixtures_code += f'''
@pytest.fixture(scope="session")
def {name}_container():
    """PostgreSQL container fixture"""
    with PostgresContainer("postgres:13") as postgres:
        yield postgres

@pytest.fixture
def {name}_connection({name}_container):
    """PostgreSQL connection fixture"""
    import psycopg2
    conn = psycopg2.connect({name}_container.get_connection_url())
    yield conn
    conn.close()
'''
        
        return fixtures_code
    
    def generate_test_report(self) -> Dict[str, Any]:
        """テストレポート生成"""
        total_tests = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.test_results if r.status == TestStatus.FAILED)
        
        return {
            "framework": "pytest_integration",
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
            "results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "duration": r.duration,
                    "error": r.error
                }
                for r in self.test_results
            ]
        }
    
    def cleanup(self):
        """リソースクリーンアップ"""
        self.logger.info("Cleaning up test environment")
        
        # コンテナ停止
        for name, container in self.containers.items():
            try:
                container.stop()
                self.logger.debug(f"Stopped container: {name}")
            except Exception as e:
                self.logger.error(f"Failed to stop container {name}: {e}")
        
        self.containers.clear()
        self.services.clear()


class PytestTestDataManager:
    """pytest テストデータ管理"""
    
    def __init__(self):
        """初期化メソッド"""
        self.test_data = {}
        self.logger = logging.getLogger("pytest_data_manager")
    
    def create_test_database(self, postgres_container: PostgresContainer,
                           schema_file: Optional[str] = None) -> str:
        """テストデータベース作成"""
        import psycopg2
        
        connection_url = postgres_container.get_connection_url()
        
        if schema_file and os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            conn = psycopg2.connect(connection_url)
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
            conn.commit()
            conn.close()
            
            self.logger.info(f"Applied schema from: {schema_file}")
        
        return connection_url
    
    def load_test_data(self, connection_url: str, 
                      data_files: List[str]) -> Dict[str, int]:
        """テストデータ読み込み"""
        import psycopg2
        
        loaded_counts = {}
        
        conn = psycopg2.connect(connection_url)
        
        for data_file in data_files:
            if os.path.exists(data_file):
                with open(data_file, 'r') as f:
                    if data_file.endswith('.sql'):
                        sql_data = f.read()
                        with conn.cursor() as cursor:
                            cursor.execute(sql_data)
                            loaded_counts[data_file] = cursor.rowcount
                    elif data_file.endswith('.json'):
                        # JSONデータ処理（テーブル別）
                        json_data = json.load(f)
                        for table, rows in json_data.items():
                            # 簡単なINSERT生成
                            if rows:
                                columns = list(rows[0].keys())
                                placeholders = ', '.join(['%s'] * len(columns))
                                insert_sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                                
                                with conn.cursor() as cursor:
                                    for row in rows:
                                        cursor.execute(insert_sql, list(row.values()))
                                
                                loaded_counts[f"{data_file}:{table}"] = len(rows)
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Loaded test data: {loaded_counts}")
        return loaded_counts


# 共通pytestフィクスチャ
@pytest.fixture(scope="session")
def integration_framework():
    """統合テストフレームワークフィクスチャ"""
    framework = PytestIntegrationFramework()
    yield framework
    framework.cleanup()


@pytest.fixture(scope="session")
def postgres_container():
    """PostgreSQLコンテナフィクスチャ"""
    with PostgresContainer("postgres:13") as postgres:
        yield postgres


@pytest.fixture
def test_data_manager():
    """テストデータ管理フィクスチャ"""
    return PytestTestDataManager()


# 統合テスト実行関数
async def run_integration_tests(test_directory: str, 
                               compose_file: Optional[str] = None,
                               pytest_args: List[str] = None) -> Dict[str, Any]:
    """統合テスト実行"""
    framework = PytestIntegrationFramework()
    
    try:
        # 環境セットアップ
        if compose_file:
            compose = framework.create_compose_environment(compose_file)
        else:
            postgres = framework.create_postgres_container()
        
        # サービス起動
        await framework.start_services()
        
        # テスト実行
        results = framework.run_test_suite(test_directory, pytest_args)
        
        # レポート生成
        report = framework.generate_test_report()
        
        return report
        
    finally:
        # クリーンアップ
        framework.cleanup()


if __name__ == "__main__":
    import sys
    
    # CLI実行
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        compose_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # テスト実行
        result = asyncio.run(run_integration_tests(test_path, compose_file))
        print(f"Integration Test Results: {result}")
    else:
        print("Usage: python pytest_integration_framework.py <test_path> [compose_file]")