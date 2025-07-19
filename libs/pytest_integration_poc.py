#!/usr/bin/env python3
"""
pytest統合テストPOC - OSS移行プロジェクト
既存のintegration_test_framework.pyをpytest + testcontainersで置き換える
"""
import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import psycopg2
import pytest
from testcontainers.compose import DockerCompose
from testcontainers.postgres import PostgresContainer

import docker


# 既存の列挙型を保持（互換性のため）
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
class ServiceInfo:
    """サービス情報（簡略化版）"""

    name: str
    url: str
    port: int
    status: ServiceStatus = ServiceStatus.STOPPED
    health_endpoint: Optional[str] = None
    container: Optional[Any] = None


class PytestIntegrationRunner:
    """pytest統合テストランナー"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.services: Dict[str, ServiceInfo] = {}
        self.containers = []

    async def start_service(
        self, service_name: str, config: Dict[str, Any]
    ) -> ServiceInfo:
        """サービス起動（testcontainersを使用）"""
        service_type = config.get("type", "generic")

        if service_type == "postgres":
            # PostgreSQLコンテナの起動
            postgres = PostgresContainer("postgres:15-alpine")
            postgres.start()
            self.containers.append(postgres)

            service = ServiceInfo(
                name=service_name,
                url=postgres.get_connection_url(),
                port=postgres.get_exposed_port(5432),
                status=ServiceStatus.RUNNING,
                container=postgres,
            )
        elif service_type == "http":
            # HTTPサービスの場合（docker-composeを使用）
            compose = DockerCompose(config.get("compose_file", "docker-compose.yml"))
            compose.start()
            self.containers.append(compose)

            service = ServiceInfo(
                name=service_name,
                url=config.get("url", f'http://localhost:{config.get("port", 8080)}'),
                port=config.get("port", 8080),
                status=ServiceStatus.RUNNING,
                health_endpoint=config.get("health_endpoint", "/health"),
                container=compose,
            )
        else:
            # 汎用コンテナ
            client = docker.from_env()
            container = client.containers.run(
                config.get("image", "alpine"),
                detach=True,
                ports=config.get("ports", {}),
                environment=config.get("environment", {}),
            )
            self.containers.append(container)

            service = ServiceInfo(
                name=service_name,
                url=config.get("url", f'http://localhost:{config.get("port", 8080)}'),
                port=config.get("port", 8080),
                status=ServiceStatus.RUNNING,
                container=container,
            )

        self.services[service_name] = service
        return service

    async def health_check(self, service: ServiceInfo, timeout: int = 30) -> bool:
        """ヘルスチェック"""
        if not service.health_endpoint:
            return True

        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < timeout:
                try:
                    async with session.get(
                        f"{service.url}{service.health_endpoint}"
                    ) as resp:
                        if resp.status == 200:
                            return True
                except Exception:
                    pass
                await asyncio.sleep(1)
        return False

    def cleanup(self):
        """クリーンアップ"""
        for container in self.containers:
            try:
                if hasattr(container, "stop"):
                    container.stop()
                elif hasattr(container, "stop_compose"):
                    container.stop_compose()
            except Exception as e:
                self.logger.error(f"Failed to stop container: {e}")


# pytestフィクスチャ
@pytest.fixture(scope="session")
def event_loop():
    """イベントループフィクスチャ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def integration_runner():
    """統合テストランナーフィクスチャ"""
    runner = PytestIntegrationRunner()
    yield runner
    runner.cleanup()


@pytest.fixture(scope="session")
async def postgres_service(integration_runner):
    """PostgreSQLサービスフィクスチャ"""
    service = await integration_runner.start_service("postgres", {"type": "postgres"})

    # ヘルスチェック
    assert service.status == ServiceStatus.RUNNING

    yield service


@pytest.fixture(scope="function")
async def test_database(postgres_service):
    """テスト用データベースフィクスチャ"""
    # データベース接続
    conn = psycopg2.connect(postgres_service.container.get_connection_url())
    cur = conn.cursor()

    # テストスキーマ作成
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS test_data (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()

    yield conn

    # クリーンアップ
    cur.execute("DROP TABLE IF EXISTS test_data")
    conn.commit()
    conn.close()


# マーカー定義
pytest.mark.integration = pytest.mark.mark(name="integration")
pytest.mark.database = pytest.mark.mark(name="database")
pytest.mark.api = pytest.mark.mark(name="api")


# ヘルパー関数
async def wait_for_service(url: str, timeout: int = 30) -> bool:
    """サービスの起動を待つ"""
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        while time.time() - start_time < timeout:
            try:
                async with session.get(url) as resp:
                    if resp.status < 500:
                        return True
            except Exception:
                pass
            await asyncio.sleep(1)
    return False


def assert_service_healthy(service: ServiceInfo):
    """サービスヘルスアサーション"""
    assert (
        service.status == ServiceStatus.RUNNING
    ), f"Service {service.name} is not running"
    assert service.container is not None, f"Service {service.name} has no container"


# 既存APIとの互換性レイヤー
class IntegrationTestFrameworkCompat:
    """既存のintegration_test_frameworkとの互換性レイヤー"""

    def __init__(self):
        self.runner = PytestIntegrationRunner()

    async def run_service_tests(self, services: Dict[str, Dict]) -> Dict[str, Any]:
        """既存APIとの互換性メソッド"""
        results = {
            "services": {},
            "tests": [],
            "summary": {"total": 0, "passed": 0, "failed": 0, "duration": 0},
        }

        start_time = time.time()

        # サービス起動
        for service_name, config in services.items():
            try:
                service = await self.runner.start_service(service_name, config)
                results["services"][service_name] = {
                    "status": service.status.value,
                    "url": service.url,
                    "port": service.port,
                }
            except Exception as e:
                results["services"][service_name] = {"status": "error", "error": str(e)}

        results["summary"]["duration"] = time.time() - start_time
        return results
