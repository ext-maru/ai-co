#!/usr/bin/env python3
"""
エルダーの魂強制実行システム
Elder Soul Enforcement System

すべての新役割とプロセスが必ずエルダーの魂を使用するようにする強制機構
"""

import os
import sys
import json
import inspect
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
from datetime import datetime
import asyncio

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_registry import ElderRegistry, AgentType


class EnforcementError(Exception):
    """強制実行違反エラー"""

    pass


class ElderTreeEnforcement:
    """
    エルダーの魂 強制実行システム

    機能:
    - 新しいプロセス/役割の自動検出
    - エルダーの魂への強制登録
    - 非準拠プロセスの警告・停止
    - 開発者への教育メッセージ
    """

    def __init__(self):
        """初期化メソッド"""
        self.registry = ElderRegistry()
        self.logger = self._setup_logger()

        # 強制実行設定
        self.enforcement_config = {
            "auto_register": True,  # 自動登録
            "strict_mode": True,  # 厳格モード
            "education_mode": True,  # 教育モード
            "grace_period": 300,  # 猶予期間（秒）
            "violations_log": "data/violations.json",
        }

        # 除外パターン
        self.exclusions = {
            "system_processes": ["systemd", "init", "kernel"],
            "development_tools": ["python", "node", "npm", "git"],
            "existing_legacy": ["old_workers", "legacy_scripts"],
        }

        # 違反記録
        self.violations: List[Dict[str, Any]] = []
        self.warned_processes: Dict[str, datetime] = {}

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("elder_enforcement")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # ファイルハンドラー
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(log_dir / "elder_enforcement.log")

            # コンソールハンドラー
            console_handler = logging.StreamHandler()

            # フォーマッター
            formatter = logging.Formatter(
                "%(asctime)s - ElderEnforcement - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    async def initialize(self):
        """強制実行システム初期化"""
        await self.registry.initialize()
        await self._load_violations()
        await self._setup_enforcement_rules()

        self.logger.info("🛡️ Elder Tree Enforcement System initialized")

    async def enforce_elder_tree_usage(self):
        """エルダーの魂使用を強制"""
        self.logger.info("🔍 Scanning for non-compliant processes...")

        # 新しいプロセス/役割の検出
        violations = await self._detect_violations()

        if violations:
            self.logger.warning(f"⚠️ Found {len(violations)} violations")

            for violation in violations:
                await self._handle_violation(violation)
        else:
            self.logger.info("✅ All processes are Elder Tree compliant")

    async def register_new_role(
        self, role_info: Dict[str, Any], auto_approve: bool = False
    ) -> bool:
        """
        新役割の登録

        Args:
            role_info: 役割情報
            auto_approve: 自動承認フラグ

        Returns:
            bool: 登録成功フラグ
        """
        self.logger.info(f"📋 Registering new role: {role_info.get('name', 'Unknown')}")

        # 必須フィールドチェック
        required_fields = ["name", "description", "type", "capabilities"]
        missing_fields = [field for field in required_fields if field not in role_info]

        if missing_fields:
            raise EnforcementError(f"Missing required fields: {missing_fields}")

        # エルダーの魂への自動登録
        try:
            agent = await self.registry.register_agent(
                agent_id=role_info.get(
                    "id", role_info["name"].lower().replace(" ", "_")
                ),
                name=role_info["name"],
                description=role_info["description"],
                agent_type=AgentType(role_info["type"]),
                capabilities=role_info["capabilities"],
                dependencies=role_info.get("dependencies", []),
                auto_start=role_info.get("auto_start", True),
            )

            self.logger.info(f"✅ Successfully registered: {agent.name}")

            # 開発者への教育メッセージ
            if self.enforcement_config["education_mode"]:
                await self._send_education_message(role_info, agent)

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to register role: {e}")
            return False

    async def validate_process_compliance(self, process_info: Dict[str, Any]) -> bool:
        """プロセスの準拠性検証"""
        process_name = process_info.get("name", "unknown")

        # 除外チェック
        if await self._is_excluded_process(process_info):
            return True

        # エルダーツリー登録チェック
        agent_id = self._extract_agent_id(process_info)
        if agent_id and agent_id in self.registry.agents:
            return True

        # 準拠パターンチェック
        if await self._matches_elder_pattern(process_info):
            return True

        # 違反として記録
        await self._record_violation(process_info)
        return False

    # デコレーター
    def require_elder_registration(self, agent_type: AgentType = AgentType.SERVANT):
        """
        エルダー登録必須デコレーター

        使用例:
        @require_elder_registration(AgentType.SERVANT)
        def my_new_function():
            pass
        """

        def decorator(func:
            """decoratorメソッド"""
        Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                """wrapperメソッド"""
                # 関数の情報を取得
                func_info = {
                    "name": func.__name__,
                    "module": func.__module__,
                    "file": inspect.getfile(func),
                    "type": agent_type.value,
                }

                # 自動登録
                if self.enforcement_config["auto_register"]:
                    await self._auto_register_function(func_info, agent_type)

                # 厳格モードでの検証
                if self.enforcement_config["strict_mode"]:
                    if not await self._verify_function_compliance(func_info):
                        raise EnforcementError(
                            f"Function {func.__name__} is not registered with Elder Soul. "
                            f"Please register using: elder-tree-soul register {func.__name__}"
                        )

                return (
                    await func(*args, **kwargs)
                    if asyncio.iscoroutinefunction(func)
                    else func(*args, **kwargs)
                )

            return wrapper

        return decorator

    # プライベートメソッド

    async def _detect_violations(self) -> List[Dict[str, Any]]:
        """違反の検出"""
        violations = []

        # 1. プロセススキャン
        process_violations = await self._scan_processes()
        violations.extend(process_violations)

        # 2. ファイルスキャン
        file_violations = await self._scan_files()
        violations.extend(file_violations)

        # 3. ポートスキャン
        port_violations = await self._scan_ports()
        violations.extend(port_violations)

        return violations

    async def _scan_processes(self) -> List[Dict[str, Any]]:
        """プロセススキャン"""
        violations = []

        try:
            import psutil

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    process_info = proc.info

                    # エルダー関連プロセスかチェック
                    if await self._is_potential_elder_process(process_info):
                        if not await self.validate_process_compliance(process_info):
                            violations.append(
                                {
                                    "type": "process",
                                    "process": process_info,
                                    "reason": "Unregistered elder-like process",
                                }
                            )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except ImportError:
            self.logger.warning("psutil not available for process scanning")

        return violations

    async def _scan_files(self) -> List[Dict[str, Any]]:
        """ファイルスキャン"""
        violations = []

        # プロジェクト内のPythonファイルをスキャン
        for py_file in Path(PROJECT_ROOT).rglob("*.py"):
            if await self._is_potential_elder_file(py_file):
                file_info = await self._analyze_file(py_file)

                if not await self._is_file_compliant(file_info):
                    violations.append(
                        {
                            "type": "file",
                            "file": str(py_file),
                            "info": file_info,
                            "reason": "Non-compliant elder file",
                        }
                    )

        return violations

    async def _scan_ports(self) -> List[Dict[str, Any]]:
        """ポートスキャン"""
        violations = []

        # エルダーポート範囲のスキャン
        elder_port_ranges = [
            (5000, 5999),  # エルダー・賢者ポート
            (6000, 6999),  # サーバントポート
            (7000, 7999),  # 騎士団ポート
            (8000, 8999),  # エルフポート
        ]

        for start_port, end_port in elder_port_ranges:
            for port in range(start_port, end_port + 1):
                if await self._is_port_used_by_unregistered_process(port):
                    violations.append(
                        {
                            "type": "port",
                            "port": port,
                            "reason": "Port used by unregistered process",
                        }
                    )

        return violations

    async def _handle_violation(self, violation: Dict[str, Any]):
        """違反処理"""
        violation_type = violation["type"]

        self.logger.warning(f"🚨 Violation detected: {violation['reason']}")

        if violation_type == "process":
            await self._handle_process_violation(violation)
        elif violation_type == "file":
            await self._handle_file_violation(violation)
        elif violation_type == "port":
            await self._handle_port_violation(violation)

        # 違反記録
        await self._record_violation(violation)

    async def _handle_process_violation(self, violation: Dict[str, Any]):
        """プロセス違反処理"""
        process_info = violation["process"]
        process_name = process_info.get("name", "unknown")

        # 警告期間チェック
        if process_name in self.warned_processes:
            warning_time = self.warned_processes[process_name]
            elapsed = (datetime.now() - warning_time).total_seconds()

            if elapsed > self.enforcement_config["grace_period"]:
                # 猶予期間経過 - 強制処理
                await self._force_process_compliance(process_info)
            else:
                # 猶予期間内 - 再警告
                self.logger.warning(
                    f"Grace period remaining for {process_name}: "
                    f"{self.enforcement_config['grace_period'] - elapsed:.0f}s"
                )
        else:
            # 初回警告
            await self._warn_process(process_info)

    async def _handle_file_violation(self, violation: Dict[str, Any]):
        """ファイル違反処理"""
        file_path = violation["file"]
        file_info = violation["info"]

        # 自動修正を試行
        if self.enforcement_config["auto_register"]:
            await self._auto_fix_file(file_path, file_info)
        else:
            await self._warn_file_violation(file_path, file_info)

    async def _handle_port_violation(self, violation: Dict[str, Any]):
        """ポート違反処理"""
        port = violation["port"]

        # ポート使用プロセスを特定
        using_process = await self._identify_port_user(port)

        if using_process:
            self.logger.warning(
                f"🔌 Port {port} used by unregistered process: {using_process}"
            )

            # プロセス情報として処理
            await self._handle_process_violation(
                {
                    "type": "process",
                    "process": using_process,
                    "reason": f"Using elder port {port} without registration",
                }
            )

    async def _force_process_compliance(self, process_info: Dict[str, Any]):
        """プロセス準拠の強制"""
        process_name = process_info.get("name", "unknown")
        pid = process_info.get("pid")

        if self.enforcement_config["strict_mode"]:
            self.logger.error(
                f"🛑 FORCE STOPPING non-compliant process: {process_name} (PID: {pid})"
            )

            # プロセス終了
            try:
                import psutil

                proc = psutil.Process(pid)
                proc.terminate()

                # 教育メッセージ表示
                await self._show_compliance_education(process_info)

            except Exception as e:
                self.logger.error(f"Failed to terminate process {pid}: {e}")
        else:
            self.logger.warning(
                f"⚠️ Would terminate {process_name} (strict mode disabled)"
            )

    async def _warn_process(self, process_info: Dict[str, Any]):
        """プロセス警告"""
        process_name = process_info.get("name", "unknown")

        warning_msg = f"""
🚨 ELDER TREE SOUL VIOLATION DETECTED 🚨

Process: {process_name}
PID: {process_info.get('pid')}
Command: {' '.join(process_info.get('cmdline', []))}

⚠️ This process appears to be an Elder-like service but is not registered
   with the Elder Soul system.

🔧 To fix this violation:
   1. Register with Elder Soul: elder-tree-soul register {process_name}
   2. Or modify your code to use the Elder Soul framework

⏰ Grace period: {self.enforcement_config['grace_period']} seconds
   After this period, the process will be automatically terminated.

📚 Documentation: {PROJECT_ROOT}/docs/elder_soul_plan.md
"""

        print(warning_msg)
        self.logger.warning(f"Warned process: {process_name}")

        # 警告時刻記録
        self.warned_processes[process_name] = datetime.now()

    async def _show_compliance_education(self, process_info: Dict[str, Any]):
        """準拠教育メッセージ"""
        education_msg = f"""
🌲 ELDER TREE SOUL EDUCATION 🌲

Your process has been terminated because it violated Elder Soul policies.

📋 What happened:
   Your process appeared to be an Elder-like service but was not properly
   registered with the Elder Soul system.

🎯 Why this matters:
   - Elder Soul ensures proper A2A communication
   - Maintains system hierarchy and order
   - Provides automatic monitoring and management
   - Enables dynamic scaling and fault tolerance

🔧 How to fix:
   1. Use the Elder Soul framework for all new roles
   2. Register existing processes: elder-tree-soul register <name>
   3. Follow the Elder Soul development guidelines

💡 Example:
   # Register a new agent
   elder-tree-soul register my_agent --type servant --auto-start

   # Check compliance
   elder-tree-soul health

📚 Learn more:
   - Documentation: {PROJECT_ROOT}/docs/
   - Examples: {PROJECT_ROOT}/processes/
   - Help: elder-tree-soul --help

🌲 Remember: "Every Role, Every Process, Every Connection"
"""

        print(education_msg)

    async def _auto_register_function(
        self, func_info: Dict[str, Any], agent_type: AgentType
    ):
        """関数の自動登録"""
        # 関数情報からエージェント情報を生成
        agent_info = {
            "id": func_info["name"],
            "name": func_info["name"].replace("_", " ").title(),
            "description": f"Auto-registered from {func_info['module']}",
            "type": agent_type.value,
            "capabilities": ["auto_generated"],
            "dependencies": [],
            "auto_start": False,
        }

        try:
            await self.register_new_role(agent_info, auto_approve=True)
            self.logger.info(f"✅ Auto-registered function: {func_info['name']}")
        except Exception as e:
            self.logger.error(
                f"❌ Failed to auto-register function {func_info['name']}: {e}"
            )

    async def _verify_function_compliance(self, func_info: Dict[str, Any]) -> bool:
        """関数の準拠性検証"""
        agent_id = func_info["name"]
        return agent_id in self.registry.agents

    async def _is_excluded_process(self, process_info: Dict[str, Any]) -> bool:
        """除外プロセスチェック"""
        process_name = process_info.get("name", "").lower()
        cmdline = " ".join(process_info.get("cmdline", [])).lower()

        # システムプロセス除外
        for pattern in self.exclusions["system_processes"]:
            if pattern in process_name or pattern in cmdline:
                return True

        # 開発ツール除外
        for pattern in self.exclusions["development_tools"]:
            if pattern in process_name or pattern in cmdline:
                return True

        # レガシープロセス除外
        for pattern in self.exclusions["existing_legacy"]:
            if pattern in cmdline:
                return True

        return False

    async def _is_potential_elder_process(self, process_info: Dict[str, Any]) -> bool:
        """エルダープロセス候補チェック"""
        cmdline = " ".join(process_info.get("cmdline", [])).lower()

        # エルダー関連キーワード
        elder_keywords = [
            "elder",
            "sage",
            "servant",
            "elf",
            "knight",
            "agent",
            "worker",
            "process",
            "daemon",
            "a2a",
            "soul",
        ]

        for keyword in elder_keywords:
            if keyword in cmdline:
                return True

        # ポートパターンチェック
        elder_ports = ["500", "600", "700", "800"]  # エルダーポート範囲
        for port_prefix in elder_ports:
            if f"port {port_prefix}" in cmdline or f":{port_prefix}" in cmdline:
                return True

        return False

    async def _is_potential_elder_file(self, file_path: Path) -> bool:
        """エルダーファイル候補チェック"""
        # ファイル名チェック
        filename = file_path.name.lower()
        elder_patterns = [
            "_process.py",
            "_agent.py",
            "_worker.py",
            "_servant.py",
            "_sage.py",
            "_elder.py",
        ]

        for pattern in elder_patterns:
            if filename.endswith(pattern):
                return True

        # ディレクトリチェック
        if "processes" in file_path.parts or "agents" in file_path.parts:
            return True

        return False

    async def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """ファイル分析"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # クラス・関数抽出
            import ast

            tree = ast.parse(content)

            classes = [
                node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
            ]
            functions = [
                node.name
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef)
            ]

            return {
                "path": str(file_path),
                "classes": classes,
                "functions": functions,
                "size": len(content),
                "elder_indicators": self._find_elder_indicators(content),
            }

        except Exception as e:
            return {"path": str(file_path), "error": str(e)}

    def _find_elder_indicators(self, content: str) -> List[str]:
        """エルダー指標検出"""
        indicators = []

        elder_patterns = [
            "ElderProcessBase",
            "AgentType",
            "ElderMessage",
            "elder_name",
            "elder_role",
            "A2A",
            "elder_tree",
        ]

        for pattern in elder_patterns:
            if pattern in content:
                indicators.append(pattern)

        return indicators

    async def _is_file_compliant(self, file_info: Dict[str, Any]) -> bool:
        """ファイル準拠性チェック"""
        # エルダー指標があるかチェック
        if file_info.get("elder_indicators"):
            # エルダーファイルとして認識 - 登録チェック
            file_path = Path(file_info["path"])
            agent_id = file_path.stem.replace("_process", "").replace("_agent", "")

            return agent_id in self.registry.agents

        # 非エルダーファイルは準拠とみなす
        return True

    async def _auto_fix_file(self, file_path: str, file_info: Dict[str, Any]):
        """ファイルの自動修正"""
        self.logger.info(f"🔧 Auto-fixing file: {file_path}")

        # ファイルからエージェント情報を推定
        path_obj = Path(file_path)
        agent_id = path_obj.stem.replace("_process", "").replace("_agent", "")

        # 自動登録を試行
        agent_info = {
            "id": agent_id,
            "name": agent_id.replace("_", " ").title(),
            "description": f"Auto-discovered from {file_path}",
            "type": "servant",  # デフォルト
            "capabilities": ["auto_discovered"],
            "dependencies": [],
            "auto_start": False,
        }

        await self.register_new_role(agent_info, auto_approve=True)

    async def _warn_file_violation(self, file_path: str, file_info: Dict[str, Any]):
        """ファイル違反警告"""
        self.logger.warning(f"📄 File violation: {file_path}")

    async def _is_port_used_by_unregistered_process(self, port: int) -> bool:
        """未登録プロセスによるポート使用チェック"""
        # 登録済みエージェントポートチェック
        for agent in self.registry.agents.values():
            if agent.port == port:
                return False  # 登録済み

        # ポートが使用されているかチェック
        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(("localhost", port))
                return result == 0  # 使用されている
        except:
            return False

    async def _identify_port_user(self, port: int) -> Optional[Dict[str, Any]]:
        """ポート使用プロセス特定"""
        try:
            import psutil

            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    try:
                        proc = psutil.Process(conn.pid)
                        return {
                            "pid": conn.pid,
                            "name": proc.name(),
                            "cmdline": proc.cmdline(),
                        }
                    except psutil.NoSuchProcess:
                        continue
        except ImportError:
            pass

        return None

    def _extract_agent_id(self, process_info: Dict[str, Any]) -> Optional[str]:
        """プロセス情報からエージェントID抽出"""
        cmdline = " ".join(process_info.get("cmdline", []))

        # _process.py パターン
        import re

        match = re.search(r"(\w+)_process\.py", cmdline)
        if match:
            return match.group(1)

        return None

    async def _matches_elder_pattern(self, process_info: Dict[str, Any]) -> bool:
        """エルダーパターンマッチング"""
        cmdline = " ".join(process_info.get("cmdline", [])).lower()

        # 既知のエルダーパターン
        elder_patterns = [
            "elder_soul",
            "elder-tree-soul",
            "elder_process_base",
            "run_elder_process",
        ]

        for pattern in elder_patterns:
            if pattern in cmdline:
                return True

        return False

    async def _record_violation(self, violation: Dict[str, Any]):
        """違反記録"""
        violation_record = {
            "timestamp": datetime.now().isoformat(),
            "violation": violation,
            "action_taken": "warned",
            "resolved": False,
        }

        self.violations.append(violation_record)
        await self._save_violations()

    async def _load_violations(self):
        """違反記録読み込み"""
        violations_file = Path(self.enforcement_config["violations_log"])
        if violations_file.exists():
            try:
                with open(violations_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.violations = data.get("violations", [])
            except Exception as e:
                self.logger.error(f"Failed to load violations: {e}")

    async def _save_violations(self):
        """違反記録保存"""
        violations_file = Path(self.enforcement_config["violations_log"])
        violations_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(violations_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "violations": self.violations,
                        "last_updated": datetime.now().isoformat(),
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            self.logger.error(f"Failed to save violations: {e}")

    async def _setup_enforcement_rules(self):
        """強制実行ルール設定"""
        # 環境変数からの設定オーバーライド
        if os.getenv("ELDER_TREE_STRICT_MODE"):
            self.enforcement_config["strict_mode"] = True

        if os.getenv("ELDER_TREE_AUTO_REGISTER"):
            self.enforcement_config["auto_register"] = True

        # 設定ファイルからの読み込み
        config_file = Path("elder_tree_enforcement.json")
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    config_override = json.load(f)
                    self.enforcement_config.update(config_override)
            except Exception as e:
                self.logger.error(f"Failed to load enforcement config: {e}")

    async def _send_education_message(self, role_info: Dict[str, Any], agent: Any):
        """教育メッセージ送信"""
        if not self.enforcement_config["education_mode"]:
            return

        education_msg = f"""
🎉 SUCCESS: Role registered with Elder Soul!

Role: {agent.name}
Type: {agent.agent_type.value}
Port: {agent.port}

✅ Your role is now part of the Elder Soul system and will benefit from:
   - Automatic A2A communication
   - Built-in monitoring and health checks
   - Dynamic scaling capabilities
   - Hierarchical management

📚 Next steps:
   1. Start your agent: elder-tree-soul start {agent.agent_id}
   2. Check status: elder-tree-soul status
   3. Monitor logs: elder-tree-soul logs {agent.agent_id}

🌲 Welcome to the Elder Soul ecosystem!
"""

        print(education_msg)


# グローバルインスタンス
_enforcement_instance: Optional[ElderTreeEnforcement] = None


async def get_enforcement() -> ElderTreeEnforcement:
    """強制実行システム取得"""
    global _enforcement_instance

    if _enforcement_instance is None:
        _enforcement_instance = ElderTreeEnforcement()
        await _enforcement_instance.initialize()

    return _enforcement_instance


# 便利な関数
async def enforce_elder_tree():
    """エルダーツリー強制実行"""
    enforcement = await get_enforcement()
    await enforcement.enforce_elder_tree_usage()


def require_elder_registration(agent_type: AgentType = AgentType.SERVANT):
    """エルダー登録必須デコレーター"""

    async def async_decorator(func):
        """async_decoratorメソッド"""
        enforcement = await get_enforcement()
        return enforcement.require_elder_registration(agent_type)(func)

    # 同期版対応
    def sync_decorator(func):
        """sync_decoratorメソッド"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            """wrapperメソッド"""
            # 非同期での登録チェックを同期的に実行
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                enforcement = loop.run_until_complete(get_enforcement())
                decorated = enforcement.require_elder_registration(agent_type)(func)
                return decorated(*args, **kwargs)
            finally:
                loop.close()

        return wrapper

    return sync_decorator


# コマンドライン実行
async def main():
    """メイン実行"""
    enforcement = await get_enforcement()
    await enforcement.enforce_elder_tree_usage()


if __name__ == "__main__":
    asyncio.run(main())
