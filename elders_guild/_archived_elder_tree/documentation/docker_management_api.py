#!/usr/bin/env python3
"""
Docker Management API Foundation

Provides RESTful API for Docker container lifecycle management
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import docker

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.env_config import get_config
from libs.shared_enums import ProjectType, RuntimeEnvironment, SecurityLevel

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Elders Guild Docker Management API",
    description="Docker コンテナライフサイクル管理API",
    version="1.0.0",
)

class ContainerStatus(str, Enum):
    """コンテナステータス"""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    RESTARTING = "restarting"
    REMOVING = "removing"
    EXITED = "exited"
    DEAD = "dead"

class ContainerAction(str, Enum):
    """コンテナアクション"""

    START = "start"
    STOP = "stop"
    RESTART = "restart"
    PAUSE = "pause"
    UNPAUSE = "unpause"
    REMOVE = "remove"
    LOGS = "logs"

# Pydantic Models
class ContainerCreateRequest(BaseModel):
    """コンテナ作成リクエスト"""

    name: str = Field(..., description="コンテナ名")
    project_type: ProjectType = Field(..., description="プロジェクトタイプ")
    security_level: SecurityLevel = Field(
        SecurityLevel.SANDBOX, description="セキュリティレベル"
    )
    runtime: RuntimeEnvironment = Field(
        RuntimeEnvironment.PYTHON_39, description="ランタイム環境"
    )
    ports: Optional[List[str]] = Field(
        default=[], description="ポートマッピング (例: '8080:80')"
    )
    volumes: Optional[List[str]] = Field(default=[], description="ボリュームマッピング")
    environment: Optional[Dict[str, str]] = Field(default={}, description="環境変数")

class ContainerActionRequest(BaseModel):
    """コンテナアクションリクエスト"""

    action: ContainerAction = Field(..., description="実行するアクション")

class ContainerInfo(BaseModel):
    """コンテナ情報"""

    id: str
    name: str
    status: str
    image: str
    created: str
    ports: Dict[str, Any]
    labels: Dict[str, str]

class ContainerStats(BaseModel):
    """コンテナ統計情報"""

    cpu_percent: float
    memory_usage_mb: float
    memory_limit_mb: float
    memory_percent: float
    network_rx_mb: float
    network_tx_mb: float

@dataclass
class DockerManager:
    """Docker管理クラス"""

    def __init__(self):
        """初期化メソッド"""
        self.client = docker.from_env()

        self.containers_info: Dict[str, Dict[str, Any]] = {}

    def create_container(self, request: ContainerCreateRequest) -> ContainerInfo:
        """コンテナを作成"""
        try:
            # テンプレートからDockerfile生成

                project_type=request.project_type,
                runtime=request.runtime,
                security_level=request.security_level,
            )

            # プロジェクトディレクトリ作成
            project_dir = PROJECT_ROOT / "docker_projects" / request.name
            project_dir.mkdir(parents=True, exist_ok=True)

            # Dockerfileとdocker-compose.yml生成

                project_name=request.name,
                project_dir=str(project_dir),

            )

            # イメージビルド
            image_name = f"ai-company/{request.name}:latest"
            self.client.images.build(path=str(project_dir), tag=image_name, rm=True)

            # コンテナ作成
            container = self.client.containers.create(
                image=image_name,
                name=f"ai-company-{request.name}",
                ports=(
                    {p.split(":")[1]: p.split(":")[0] for p in request.ports}
                    if request.ports
                    else None
                ),
                volumes=request.volumes,
                environment=request.environment,
                labels={
                    "ai.company.project_type": request.project_type.value,
                    "ai.company.security_level": request.security_level.value,
                    "ai.company.runtime": request.runtime.value,
                    "ai.company.created_at": datetime.now().isoformat(),
                },
                detach=True,
            )

            # コンテナ情報保存
            self.containers_info[container.id] = {
                "name": request.name,
                "project_type": request.project_type.value,
                "security_level": request.security_level.value,
                "created_at": datetime.now().isoformat(),
            }

            return self._container_to_info(container)

        except Exception as e:
            logger.error(f"Container creation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def list_containers(self, all: bool = False) -> List[ContainerInfo]:
        """コンテナ一覧を取得"""
        try:
            containers = self.client.containers.list(all=all)
            return [
                self._container_to_info(c)
                for c in containers
                if c.labels.get("ai.company.project_type")
            ]
        except Exception as e:
            logger.error(f"Failed to list containers: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_container(self, container_id: str) -> ContainerInfo:
        """コンテナ情報を取得"""
        try:
            container = self.client.containers.get(container_id)
            return self._container_to_info(container)
        except docker.errors.NotFound:
            raise HTTPException(status_code=404, detail="Container not found")
        except Exception as e:
            logger.error(f"Failed to get container: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def execute_action(
        self, container_id: str, action: ContainerAction
    ) -> Dict[str, Any]:
        """コンテナアクションを実行"""
        try:
            container = self.client.containers.get(container_id)

            if action == ContainerAction.START:
                container.start()
                return {"status": "started", "container_id": container_id}

            elif action == ContainerAction.STOP:
                container.stop(timeout=30)
                return {"status": "stopped", "container_id": container_id}

            elif action == ContainerAction.RESTART:
                container.restart(timeout=30)
                return {"status": "restarted", "container_id": container_id}

            elif action == ContainerAction.PAUSE:
                container.pause()
                return {"status": "paused", "container_id": container_id}

            elif action == ContainerAction.UNPAUSE:
                container.unpause()
                return {"status": "unpaused", "container_id": container_id}

            elif action == ContainerAction.REMOVE:
                container.remove(force=True)
                if container_id in self.containers_info:
                    del self.containers_info[container_id]
                return {"status": "removed", "container_id": container_id}

            elif action == ContainerAction.LOGS:
                logs = container.logs(tail=100).decode("utf-8")
                return {"logs": logs, "container_id": container_id}

            else:
                raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

        except docker.errors.NotFound:
            raise HTTPException(status_code=404, detail="Container not found")
        except Exception as e:
            logger.error(f"Failed to execute action: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_container_stats(self, container_id: str) -> ContainerStats:
        """コンテナ統計情報を取得"""
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)

            # CPU使用率計算
            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )
            cpu_percent = (
                (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
            )

            # メモリ使用率計算
            memory_usage = stats["memory_stats"]["usage"] / 1024 / 1024  # MB
            memory_limit = stats["memory_stats"]["limit"] / 1024 / 1024  # MB
            memory_percent = (
                (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0.0
            )

            # ネットワーク統計
            network_rx = (
                sum(net["rx_bytes"] for net in stats["networks"].values()) / 1024 / 1024
            )  # MB
            network_tx = (
                sum(net["tx_bytes"] for net in stats["networks"].values()) / 1024 / 1024
            )  # MB

            return ContainerStats(
                cpu_percent=round(cpu_percent, 2),
                memory_usage_mb=round(memory_usage, 2),
                memory_limit_mb=round(memory_limit, 2),
                memory_percent=round(memory_percent, 2),
                network_rx_mb=round(network_rx, 2),
                network_tx_mb=round(network_tx, 2),
            )

        except docker.errors.NotFound:
            raise HTTPException(status_code=404, detail="Container not found")
        except Exception as e:
            logger.error(f"Failed to get container stats: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def _container_to_info(self, container) -> ContainerInfo:
        """Dockerコンテナオブジェクトを情報モデルに変換"""
        return ContainerInfo(
            id=container.short_id,
            name=container.name,
            status=container.status,
            image=(
                container.image.tags[0]
                if container.image.tags
                else container.image.short_id
            ),
            created=container.attrs["Created"],
            ports=container.attrs.get("NetworkSettings", {}).get("Ports", {}),
            labels=container.labels,
        )

# グローバルマネージャーインスタンス
docker_manager = DockerManager()

# API エンドポイント

@app.get("/", tags=["Health"])
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "service": "Docker Management API", "version": "1.0.0"}

@app.post("/containers", response_model=ContainerInfo, tags=["Containers"])
async def create_container(request: ContainerCreateRequest):
    """新しいコンテナを作成"""
    return docker_manager.create_container(request)

@app.get("/containers", response_model=List[ContainerInfo], tags=["Containers"])
async def list_containers(all: bool = False):
    """コンテナ一覧を取得"""
    return docker_manager.list_containers(all=all)

@app.get(
    "/containers/{container_id}", response_model=ContainerInfo, tags=["Containers"]
)
async def get_container(container_id: str):
    """特定のコンテナ情報を取得"""
    return docker_manager.get_container(container_id)

@app.post("/containers/{container_id}/actions", tags=["Container Actions"])
async def execute_container_action(container_id: str, request: ContainerActionRequest):
    """コンテナアクションを実行"""
    return docker_manager.execute_action(container_id, request.action)

@app.get(
    "/containers/{container_id}/stats",
    response_model=ContainerStats,
    tags=["Container Stats"],
)
async def get_container_stats(container_id: str):
    """コンテナ統計情報を取得"""
    return docker_manager.get_container_stats(container_id)

@app.delete("/containers/{container_id}", tags=["Containers"])
async def remove_container(container_id: str):
    """コンテナを削除"""
    return docker_manager.execute_action(container_id, ContainerAction.REMOVE)

# 4賢者システム統合エンドポイント

@app.get("/sages/status", tags=["4 Sages Integration"])
async def get_sages_container_status():
    """4賢者システムのコンテナステータスを取得"""
    sage_containers = {
        "knowledge_sage": None,
        "task_sage": None,
        "incident_sage": None,
        "rag_sage": None,
    }

    containers = docker_manager.list_containers(all=True)
    for container in containers:
        if "knowledge" in container.name.lower():
            sage_containers["knowledge_sage"] = container.dict()
        elif "task" in container.name.lower():
            sage_containers["task_sage"] = container.dict()
        elif "incident" in container.name.lower():
            sage_containers["incident_sage"] = container.dict()
        elif "rag" in container.name.lower():
            sage_containers["rag_sage"] = container.dict()

    return {"sages": sage_containers, "timestamp": datetime.now().isoformat()}

# CLI実行用
def main():
    """スタンドアロン実行"""
    port = int(os.getenv("DOCKER_API_PORT", "8080"))
    host = os.getenv("DOCKER_API_HOST", "0.0.0.0")

    logger.info(f"Starting Docker Management API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
