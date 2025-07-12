#!/usr/bin/env python3
"""
エルダーレジストリ - 動的エージェント管理システム
Elder Registry - Dynamic Agent Management System
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import signal


class AgentType(Enum):
    """エージェントタイプ"""
    GRAND_ELDER = "grand_elder"
    ELDER = "elder"
    SAGE = "sage"
    SERVANT = "servant"
    ELF = "elf"
    KNIGHT = "knight"
    COUNCIL = "council"


class AgentStatus(Enum):
    """エージェント状態"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class AgentDefinition:
    """エージェント定義"""
    agent_id: str
    name: str
    description: str
    agent_type: AgentType
    port: int
    script_path: str
    hierarchy_level: int
    capabilities: List[str]
    dependencies: List[str]
    auto_start: bool = True
    process_id: Optional[int] = None
    status: AgentStatus = AgentStatus.INACTIVE
    created_at: datetime = None
    last_updated: datetime = None
    metadata: Dict[str, Any] = None


class ElderRegistry:
    """
    エルダーレジストリ - 動的エージェント管理

    責務:
    - エージェントの動的登録・削除
    - プロセス管理とライフサイクル
    - 依存関係の解決
    - ポート自動割り当て
    """

    def __init__(self, registry_file: str = "data/elder_registry.json"):
        self.registry_file = Path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        self.agents: Dict[str, AgentDefinition] = {}
        self.port_allocator = PortAllocator()
        self.template_manager = AgentTemplateManager()

        # 起動済みプロセス管理
        self.processes: Dict[str, subprocess.Popen] = {}

        # 予約済みコアエージェント
        self.core_agents = {
            "grand_elder": {"port": 5000, "hierarchy": 1},
            "claude_elder": {"port": 5001, "hierarchy": 2},
            "knowledge_sage": {"port": 5002, "hierarchy": 3},
            "task_sage": {"port": 5003, "hierarchy": 3},
            "rag_sage": {"port": 5004, "hierarchy": 3},
            "incident_sage": {"port": 5005, "hierarchy": 3}
        }

    async def initialize(self):
        """レジストリ初期化"""
        await self._load_registry()
        await self._register_core_agents()
        await self._validate_registry()

    async def register_agent(self,
                           agent_id: str,
                           name: str,
                           description: str,
                           agent_type: AgentType,
                           capabilities: List[str],
                           dependencies: List[str] = None,
                           port: int = None,
                           auto_start: bool = True) -> AgentDefinition:
        """
        新エージェントの登録

        Args:
            agent_id: エージェント識別子
            name: 表示名
            description: 説明
            agent_type: エージェントタイプ
            capabilities: 機能リスト
            dependencies: 依存エージェント
            port: ポート番号（自動割り当て可能）
            auto_start: 自動起動設定

        Returns:
            AgentDefinition: 登録されたエージェント定義
        """
        if agent_id in self.agents:
            raise ValueError(f"Agent {agent_id} already exists")

        # ポート自動割り当て
        if port is None:
            port = await self.port_allocator.allocate_port(agent_type)

        # 階層レベル決定
        hierarchy_level = self._determine_hierarchy_level(agent_type)

        # スクリプトパス生成
        script_path = await self._generate_agent_script(agent_id, agent_type)

        # エージェント定義作成
        agent = AgentDefinition(
            agent_id=agent_id,
            name=name,
            description=description,
            agent_type=agent_type,
            port=port,
            script_path=script_path,
            hierarchy_level=hierarchy_level,
            capabilities=capabilities,
            dependencies=dependencies or [],
            auto_start=auto_start,
            created_at=datetime.now(),
            last_updated=datetime.now(),
            metadata={}
        )

        # 登録
        self.agents[agent_id] = agent
        await self._save_registry()

        print(f"✅ Registered new agent: {name} ({agent_id}) on port {port}")

        # 自動起動設定の場合は起動
        if auto_start:
            await self.start_agent(agent_id)

        return agent

    async def unregister_agent(self, agent_id: str):
        """エージェント登録解除"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self.agents[agent_id]

        # プロセス停止
        if agent.status == AgentStatus.ACTIVE:
            await self.stop_agent(agent_id)

        # ポート解放
        await self.port_allocator.release_port(agent.port)

        # スクリプトファイル削除
        script_path = Path(agent.script_path)
        if script_path.exists():
            script_path.unlink()

        # レジストリから削除
        del self.agents[agent_id]
        await self._save_registry()

        print(f"✅ Unregistered agent: {agent.name} ({agent_id})")

    async def start_agent(self, agent_id: str) -> bool:
        """エージェント起動"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self.agents[agent_id]

        if agent.status == AgentStatus.ACTIVE:
            print(f"ℹ️  Agent {agent_id} is already running")
            return True

        # 依存関係チェック
        if not await self._check_dependencies(agent):
            print(f"❌ Dependencies not met for {agent_id}")
            return False

        agent.status = AgentStatus.STARTING

        try:
            # プロセス起動
            process = await self._start_agent_process(agent)

            if process:
                self.processes[agent_id] = process
                agent.process_id = process.pid
                agent.status = AgentStatus.ACTIVE
                agent.last_updated = datetime.now()

                await self._save_registry()
                print(f"✅ Started agent: {agent.name} (PID: {process.pid})")
                return True
            else:
                agent.status = AgentStatus.ERROR
                return False

        except Exception as e:
            agent.status = AgentStatus.ERROR
            print(f"❌ Failed to start agent {agent_id}: {e}")
            return False

    async def stop_agent(self, agent_id: str) -> bool:
        """エージェント停止"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self.agents[agent_id]

        if agent.status != AgentStatus.ACTIVE:
            print(f"ℹ️  Agent {agent_id} is not running")
            return True

        agent.status = AgentStatus.STOPPING

        try:
            # プロセス停止
            if agent_id in self.processes:
                process = self.processes[agent_id]
                process.terminate()

                # 正常終了を待つ
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 強制終了
                    process.kill()
                    process.wait()

                del self.processes[agent_id]

            agent.process_id = None
            agent.status = AgentStatus.INACTIVE
            agent.last_updated = datetime.now()

            await self._save_registry()
            print(f"✅ Stopped agent: {agent.name}")
            return True

        except Exception as e:
            agent.status = AgentStatus.ERROR
            print(f"❌ Failed to stop agent {agent_id}: {e}")
            return False

    async def restart_agent(self, agent_id: str) -> bool:
        """エージェント再起動"""
        await self.stop_agent(agent_id)
        await asyncio.sleep(1)
        return await self.start_agent(agent_id)

    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """エージェント状態取得"""
        if agent_id not in self.agents:
            return {"error": "Agent not found"}

        agent = self.agents[agent_id]

        return {
            "agent_id": agent_id,
            "name": agent.name,
            "status": agent.status.value,
            "port": agent.port,
            "hierarchy_level": agent.hierarchy_level,
            "process_id": agent.process_id,
            "uptime": self._calculate_uptime(agent),
            "capabilities": agent.capabilities,
            "dependencies": agent.dependencies
        }

    async def list_agents(self, agent_type: AgentType = None) -> List[Dict[str, Any]]:
        """エージェント一覧取得"""
        agents = []

        for agent in self.agents.values():
            if agent_type is None or agent.agent_type == agent_type:
                agents.append({
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "type": agent.agent_type.value,
                    "status": agent.status.value,
                    "port": agent.port,
                    "hierarchy": agent.hierarchy_level
                })

        # 階層順にソート
        agents.sort(key=lambda x: x["hierarchy"])
        return agents

    async def auto_discover_agents(self, directory: str = "processes/") -> List[str]:
        """
        エージェント自動発見

        新しいエージェントスクリプトを自動検出して登録
        """
        discovered = []
        processes_dir = Path(directory)

        if not processes_dir.exists():
            return discovered

        for script_file in processes_dir.glob("*_process.py"):
            agent_id = script_file.stem.replace("_process", "")

            # 既存エージェントはスキップ
            if agent_id in self.agents:
                continue

            # スクリプト解析
            agent_info = await self._analyze_agent_script(script_file)

            if agent_info:
                # 自動登録
                await self.register_agent(
                    agent_id=agent_id,
                    name=agent_info.get("name", agent_id.replace("_", " ").title()),
                    description=agent_info.get("description", f"Auto-discovered {agent_id}"),
                    agent_type=AgentType(agent_info.get("type", "servant")),
                    capabilities=agent_info.get("capabilities", []),
                    dependencies=agent_info.get("dependencies", []),
                    auto_start=False  # 自動発見は手動起動
                )

                discovered.append(agent_id)

        return discovered

    # プライベートメソッド

    async def _load_registry(self):
        """レジストリ読み込み"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for agent_data in data.get('agents', []):
                    agent = AgentDefinition(
                        agent_id=agent_data['agent_id'],
                        name=agent_data['name'],
                        description=agent_data['description'],
                        agent_type=AgentType(agent_data['agent_type']),
                        port=agent_data['port'],
                        script_path=agent_data['script_path'],
                        hierarchy_level=agent_data['hierarchy_level'],
                        capabilities=agent_data['capabilities'],
                        dependencies=agent_data.get('dependencies', []),
                        auto_start=agent_data.get('auto_start', True),
                        status=AgentStatus(agent_data.get('status', 'inactive')),
                        metadata=agent_data.get('metadata', {})
                    )

                    if agent_data.get('created_at'):
                        agent.created_at = datetime.fromisoformat(agent_data['created_at'])
                    if agent_data.get('last_updated'):
                        agent.last_updated = datetime.fromisoformat(agent_data['last_updated'])

                    self.agents[agent.agent_id] = agent

                print(f"📋 Loaded {len(self.agents)} agents from registry")

            except Exception as e:
                print(f"❌ Failed to load registry: {e}")

    async def _save_registry(self):
        """レジストリ保存"""
        try:
            agents_data = []
            for agent in self.agents.values():
                agent_data = asdict(agent)
                agent_data['agent_type'] = agent.agent_type.value
                agent_data['status'] = agent.status.value

                if agent.created_at:
                    agent_data['created_at'] = agent.created_at.isoformat()
                if agent.last_updated:
                    agent_data['last_updated'] = agent.last_updated.isoformat()

                agents_data.append(agent_data)

            registry_data = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'total_agents': len(self.agents),
                'agents': agents_data
            }

            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"❌ Failed to save registry: {e}")

    async def _register_core_agents(self):
        """コアエージェント登録"""
        for agent_id, config in self.core_agents.items():
            if agent_id not in self.agents:
                # コアエージェントの自動登録
                await self._register_core_agent(agent_id, config)

    async def _register_core_agent(self, agent_id: str, config: Dict[str, Any]):
        """コアエージェント個別登録"""
        agent_types = {
            "grand_elder": AgentType.GRAND_ELDER,
            "claude_elder": AgentType.ELDER,
            "knowledge_sage": AgentType.SAGE,
            "task_sage": AgentType.SAGE,
            "rag_sage": AgentType.SAGE,
            "incident_sage": AgentType.SAGE
        }

        script_path = f"processes/{agent_id}_process.py"

        agent = AgentDefinition(
            agent_id=agent_id,
            name=agent_id.replace("_", " ").title(),
            description=f"Core {agent_types[agent_id].value}",
            agent_type=agent_types[agent_id],
            port=config["port"],
            script_path=script_path,
            hierarchy_level=config["hierarchy"],
            capabilities=["core_functionality"],
            dependencies=[],
            auto_start=True,
            created_at=datetime.now(),
            last_updated=datetime.now(),
            metadata={"core": True}
        )

        self.agents[agent_id] = agent

    def _determine_hierarchy_level(self, agent_type: AgentType) -> int:
        """階層レベル決定"""
        hierarchy_map = {
            AgentType.GRAND_ELDER: 1,
            AgentType.ELDER: 2,
            AgentType.SAGE: 3,
            AgentType.COUNCIL: 3,
            AgentType.SERVANT: 4,
            AgentType.KNIGHT: 4,
            AgentType.ELF: 5
        }
        return hierarchy_map.get(agent_type, 5)

    async def _generate_agent_script(self, agent_id: str, agent_type: AgentType) -> str:
        """エージェントスクリプト生成"""
        script_path = f"processes/{agent_id}_process.py"

        # テンプレートからスクリプト生成
        await self.template_manager.generate_agent_script(
            agent_id, agent_type, script_path
        )

        return script_path

    async def _check_dependencies(self, agent: AgentDefinition) -> bool:
        """依存関係チェック"""
        for dep_id in agent.dependencies:
            if dep_id not in self.agents:
                return False
            if self.agents[dep_id].status != AgentStatus.ACTIVE:
                return False
        return True

    async def _start_agent_process(self, agent: AgentDefinition) -> Optional[subprocess.Popen]:
        """エージェントプロセス起動"""
        script_path = Path(agent.script_path)

        if not script_path.exists():
            print(f"❌ Script not found: {script_path}")
            return None

        try:
            # ログファイル
            log_dir = Path("logs/elders")
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"{agent.agent_id}.log"

            # プロセス起動
            with open(log_file, 'a') as log:
                process = subprocess.Popen(
                    ["/usr/bin/python3", str(script_path)],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    cwd=str(Path.cwd()),
                    env={**subprocess.os.environ, 'PYTHONPATH': str(Path.cwd())}
                )

            # 起動確認
            await asyncio.sleep(1)
            if process.poll() is not None:
                print(f"❌ Process failed to start: {agent.agent_id}")
                return None

            return process

        except Exception as e:
            print(f"❌ Failed to start process: {e}")
            return None

    def _calculate_uptime(self, agent: AgentDefinition) -> float:
        """稼働時間計算"""
        if agent.status != AgentStatus.ACTIVE or not agent.last_updated:
            return 0.0
        return (datetime.now() - agent.last_updated).total_seconds()

    async def _analyze_agent_script(self, script_file: Path) -> Optional[Dict[str, Any]]:
        """エージェントスクリプト解析"""
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 簡易解析
            info = {}

            # クラス名からタイプ推定
            if "Sage" in content:
                info["type"] = "sage"
            elif "Servant" in content:
                info["type"] = "servant"
            elif "Elf" in content:
                info["type"] = "elf"
            else:
                info["type"] = "servant"

            # docstringから説明抽出
            import re
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if docstring_match:
                info["description"] = docstring_match.group(1).strip()

            return info

        except Exception as e:
            print(f"❌ Failed to analyze script {script_file}: {e}")
            return None

    async def _validate_registry(self):
        """レジストリ検証"""
        # ポート重複チェック
        ports = [agent.port for agent in self.agents.values()]
        if len(ports) != len(set(ports)):
            print("⚠️  Port conflicts detected in registry")

        # スクリプトファイル存在チェック
        for agent in self.agents.values():
            if not Path(agent.script_path).exists():
                print(f"⚠️  Script not found for {agent.agent_id}: {agent.script_path}")


class PortAllocator:
    """ポート自動割り当て"""

    def __init__(self):
        self.port_ranges = {
            AgentType.GRAND_ELDER: (5000, 5000),  # 固定
            AgentType.ELDER: (5001, 5099),
            AgentType.SAGE: (5100, 5199),
            AgentType.COUNCIL: (5500, 5599),
            AgentType.SERVANT: (6000, 6999),
            AgentType.KNIGHT: (7000, 7999),
            AgentType.ELF: (8000, 8999)
        }
        self.allocated_ports = set()

    async def allocate_port(self, agent_type: AgentType) -> int:
        """ポート割り当て"""
        start_port, end_port = self.port_ranges[agent_type]

        for port in range(start_port, end_port + 1):
            if port not in self.allocated_ports and self._is_port_available(port):
                self.allocated_ports.add(port)
                return port

        raise RuntimeError(f"No available ports for {agent_type}")

    async def release_port(self, port: int):
        """ポート解放"""
        self.allocated_ports.discard(port)

    def _is_port_available(self, port: int) -> bool:
        """ポート利用可能性確認"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('localhost', port))
                return True
        except:
            return False


class AgentTemplateManager:
    """エージェントテンプレート管理"""

    async def generate_agent_script(self, agent_id: str, agent_type: AgentType, script_path: str):
        """エージェントスクリプト生成"""
        template = self._get_template(agent_type)

        # テンプレート変数置換
        script_content = template.format(
            agent_id=agent_id,
            agent_class=self._to_class_name(agent_id),
            agent_name=agent_id.replace("_", " ").title(),
            port="{port}"  # 後で設定
        )

        # ファイル書き込み
        script_file = Path(script_path)
        script_file.parent.mkdir(parents=True, exist_ok=True)

        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)

        print(f"✅ Generated agent script: {script_path}")

    def _get_template(self, agent_type: AgentType) -> str:
        """テンプレート取得"""
        return '''#!/usr/bin/env python3
"""
{agent_name} Process - Auto-generated agent
Elder Tree Soul - A2A Architecture
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from libs.elder_process_base import (
    ElderProcessBase,
    ElderRole,
    SageType,
    ElderMessage,
    MessageType
)


class {agent_class}Process(ElderProcessBase):
    """
    {agent_name} - Auto-generated agent process

    責務:
    - TODO: Define specific responsibilities
    """

    def __init__(self):
        super().__init__(
            elder_name="{agent_id}",
            elder_role=ElderRole.SERVANT,  # TODO: Adjust as needed
            sage_type=None,
            port={port}
        )

    async def initialize(self):
        """初期化処理"""
        self.logger.info("🤖 Initializing {agent_name}...")
        # TODO: Add initialization logic
        self.logger.info("✅ {agent_name} initialized")

    async def process(self):
        """メイン処理"""
        # TODO: Add main processing logic
        pass

    async def handle_message(self, message: ElderMessage):
        """メッセージ処理"""
        self.logger.info(f"Received {{message.message_type.value}} from {{message.source_elder}}")

        if message.message_type == MessageType.COMMAND:
            await self._handle_command(message)
        elif message.message_type == MessageType.QUERY:
            await self._handle_query(message)
        elif message.message_type == MessageType.REPORT:
            await self._handle_report(message)

    def register_handlers(self):
        """追加のメッセージハンドラー登録"""
        pass

    async def on_cleanup(self):
        """クリーンアップ処理"""
        # TODO: Add cleanup logic
        pass

    # TODO: Add specific methods

    async def _handle_command(self, message: ElderMessage):
        """コマンド処理"""
        command = message.payload.get('command')
        # TODO: Implement command handling

    async def _handle_query(self, message: ElderMessage):
        """クエリ処理"""
        query_type = message.payload.get('query_type')
        # TODO: Implement query handling

    async def _handle_report(self, message: ElderMessage):
        """レポート処理"""
        report_type = message.payload.get('type')
        # TODO: Implement report handling


# プロセス起動
if __name__ == "__main__":
    from libs.elder_process_base import run_elder_process
    run_elder_process({agent_class}Process)
'''

    def _to_class_name(self, agent_id: str) -> str:
        """クラス名変換"""
        return ''.join(word.capitalize() for word in agent_id.split('_'))
