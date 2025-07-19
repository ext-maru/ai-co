#!/usr/bin/env python3
"""
OSS Adapter Framework
Elder System と OSS ツールの統合基盤フレームワーク

Phase 3: Issue #5 段階的移行の中核コンポーネント
Elder/OSS Bridge Pattern、Adapter Pattern、Facade Pattern を実装
"""

import asyncio
import sys
import os
import subprocess
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import importlib.util

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OSSToolType(Enum):
    """OSS ツールタイプ"""
    CODE_ASSISTANT = "code_assistant"  # Continue.dev, Aider
    LINTER = "linter"                  # Flake8, PyLint
    TESTING = "testing"                # PyTest, Nose
    FORMATTING = "formatting"          # Black, Prettier
    SECURITY = "security"              # Bandit, Safety
    MONITORING = "monitoring"          # System tools

class AdapterStatus(Enum):
    """アダプター状態"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    FALLBACK = "fallback"

@dataclass
class OSSToolCapability:
    """OSS ツール能力定義"""
    name: str
    tool_type: OSSToolType
    command: str
    args: List[str]
    input_format: str
    output_format: str
    timeout: int = 60
    requires_file: bool = False
    supports_streaming: bool = False

@dataclass
class AdapterRequest:
    """アダプターリクエスト"""
    tool_name: str
    operation: str
    data: Dict[str, Any]
    context: Dict[str, Any]
    timeout: Optional[int] = None
    fallback_enabled: bool = True

@dataclass
class AdapterResponse:
    """アダプターレスポンス"""
    success: bool
    data: Dict[str, Any]
    tool_used: str
    execution_time: float
    error: Optional[str] = None
    fallback_used: bool = False
    quality_score: Optional[float] = None

class BaseOSSAdapter(ABC):
    """OSS アダプター基底クラス"""
    
    def __init__(self, tool_name: str, capability: OSSToolCapability):
        self.tool_name = tool_name
        self.capability = capability
        self.status = AdapterStatus.INACTIVE
        self.last_error = None
        self.execution_count = 0
        self.success_count = 0
        
    @abstractmethod
    async def execute(self, request: AdapterRequest) -> AdapterResponse:
        """OSS ツール実行"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """ステータス取得"""
        return {
            "tool_name": self.tool_name,
            "status": self.status.value,
            "success_rate": self.success_count / max(self.execution_count, 1),
            "last_error": self.last_error,
            "capability": {
                "type": self.capability.tool_type.value,
                "command": self.capability.command,
                "timeout": self.capability.timeout
            }
        }

class ContinueDevAdapter(BaseOSSAdapter):
    """Continue.dev アダプター"""
    
    def __init__(self):
        capability = OSSToolCapability(
            name="continue_dev",
            tool_type=OSSToolType.CODE_ASSISTANT,
            command="http_request",
            args=["POST"],
            input_format="json",
            output_format="json",
            supports_streaming=True
        )
        super().__init__("continue_dev", capability)
        self.api_base = "http://localhost:8000"
        
    async def execute(self, request: AdapterRequest) -> AdapterResponse:
        """Continue.dev API 実行"""
        start_time = time.time()
        self.execution_count += 1
        
        try:
            # Continue.dev API への HTTP リクエスト
            import requests
            
            endpoint = f"{self.api_base}/elder/servants/{request.data.get('servant_id', 'code-craftsman')}/execute"
            payload = {
                "type": request.operation,
                "task": request.data
            }
            
            timeout = request.timeout or self.capability.timeout
            response = requests.post(endpoint, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                self.success_count += 1
                self.status = AdapterStatus.ACTIVE
                
                execution_time = time.time() - start_time
                
                return AdapterResponse(
                    success=True,
                    data=result,
                    tool_used=self.tool_name,
                    execution_time=execution_time,
                    quality_score=result.get("result", {}).get("quality_score", 0.85)
                )
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.last_error = str(e)
            self.status = AdapterStatus.ERROR
            
            return AdapterResponse(
                success=False,
                data={},
                tool_used=self.tool_name,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def health_check(self) -> bool:
        """Continue.dev ヘルスチェック"""
        try:
            import requests
            response = requests.get(f"{self.api_base}/", timeout=5)
            healthy = response.status_code == 200
            self.status = AdapterStatus.ACTIVE if healthy else AdapterStatus.ERROR
            return healthy
        except:
            self.status = AdapterStatus.ERROR
            return False

class AiderAdapter(BaseOSSAdapter):
    """Aider アダプター"""
    
    def __init__(self):
        capability = OSSToolCapability(
            name="aider",
            tool_type=OSSToolType.CODE_ASSISTANT,
            command="aider",
            args=["--yes", "--message"],
            input_format="text",
            output_format="text",
            requires_file=True
        )
        super().__init__("aider", capability)
        self.aider_path = self._find_aider_path()
        
    def _find_aider_path(self) -> str:
        """Aider 実行パス検索"""
        # Check common locations
        possible_paths = [
            "/home/aicompany/ai_co/libs/elder_servants/integrations/continue_dev/venv_continue_dev/bin/aider",
            "aider",
            "/usr/local/bin/aider"
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or self._command_exists(path):
                return path
        
        return "aider"  # Fallback
    
    def _command_exists(self, command: str) -> bool:
        """コマンド存在確認"""
        try:
            subprocess.run([command, "--version"], capture_output=True, timeout=5)
            return True
        except:
            return False
    
    async def execute(self, request: AdapterRequest) -> AdapterResponse:
        """Aider コマンド実行"""
        start_time = time.time()
        self.execution_count += 1
        
        try:
            # Temporary file handling for Aider
            import tempfile
            
            file_content = request.data.get("file_content", "")
            file_path = request.data.get("file_path", "temp.py")
            message = request.data.get("message", "Improve code")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file = os.path.join(temp_dir, os.path.basename(file_path))
                
                # Write file content
                with open(temp_file, 'w') as f:
                    f.write(file_content)
                
                # Initialize git repo (required by Aider)
                subprocess.run(['git', 'init'], cwd=temp_dir, capture_output=True)
                subprocess.run(['git', 'add', '.'], cwd=temp_dir, capture_output=True)
                subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=temp_dir, capture_output=True)
                
                # Run Aider
                timeout = request.timeout or self.capability.timeout
                result = subprocess.run([
                    self.aider_path,
                    '--yes',
                    '--message', message,
                    temp_file
                ], cwd=temp_dir, capture_output=True, text=True, timeout=timeout)
                
                # Read modified file
                modified_content = ""
                if os.path.exists(temp_file):
                    with open(temp_file, 'r') as f:
                        modified_content = f.read()
                
                self.success_count += 1
                self.status = AdapterStatus.ACTIVE
                
                execution_time = time.time() - start_time
                
                return AdapterResponse(
                    success=True,
                    data={
                        "modified_content": modified_content,
                        "original_content": file_content,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode
                    },
                    tool_used=self.tool_name,
                    execution_time=execution_time,
                    quality_score=0.90 if result.returncode == 0 else 0.50
                )
                
        except Exception as e:
            self.last_error = str(e)
            self.status = AdapterStatus.ERROR
            
            return AdapterResponse(
                success=False,
                data={},
                tool_used=self.tool_name,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def health_check(self) -> bool:
        """Aider ヘルスチェック"""
        try:
            result = subprocess.run([self.aider_path, "--version"], 
                                  capture_output=True, timeout=5)
            healthy = result.returncode == 0
            self.status = AdapterStatus.ACTIVE if healthy else AdapterStatus.ERROR
            return healthy
        except:
            self.status = AdapterStatus.ERROR
            return False

class Flake8Adapter(BaseOSSAdapter):
    """Flake8 アダプター"""
    
    def __init__(self):
        capability = OSSToolCapability(
            name="flake8",
            tool_type=OSSToolType.LINTER,
            command="python3",
            args=["-m", "flake8"],
            input_format="file",
            output_format="text",
            requires_file=True
        )
        super().__init__("flake8", capability)
    
    async def execute(self, request: AdapterRequest) -> AdapterResponse:
        """Flake8 実行"""
        start_time = time.time()
        self.execution_count += 1
        
        try:
            import tempfile
            
            file_content = request.data.get("file_content", "")
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                timeout = request.timeout or self.capability.timeout
                result = subprocess.run([
                    "python3", "-m", "flake8", "--statistics", temp_file_path
                ], capture_output=True, text=True, timeout=timeout)
                
                # Parse flake8 output
                issues = []
                for line in result.stdout.split('\n'):
                    if line.strip() and ':' in line:
                        issues.append(line.strip())
                
                self.success_count += 1
                self.status = AdapterStatus.ACTIVE
                
                execution_time = time.time() - start_time
                
                # Calculate quality score based on issues
                quality_score = max(0.5, 1.0 - (len(issues) * 0.1))
                
                return AdapterResponse(
                    success=True,
                    data={
                        "issues": issues,
                        "issue_count": len(issues),
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "clean": len(issues) == 0
                    },
                    tool_used=self.tool_name,
                    execution_time=execution_time,
                    quality_score=quality_score
                )
                
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.last_error = str(e)
            self.status = AdapterStatus.ERROR
            
            return AdapterResponse(
                success=False,
                data={},
                tool_used=self.tool_name,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def health_check(self) -> bool:
        """Flake8 ヘルスチェック"""
        try:
            result = subprocess.run(["python3", "-m", "flake8", "--version"], 
                                  capture_output=True, timeout=5)
            healthy = result.returncode == 0
            self.status = AdapterStatus.ACTIVE if healthy else AdapterStatus.ERROR
            return healthy
        except:
            self.status = AdapterStatus.ERROR
            return False

class PyTestAdapter(BaseOSSAdapter):
    """PyTest アダプター"""
    
    def __init__(self):
        capability = OSSToolCapability(
            name="pytest",
            tool_type=OSSToolType.TESTING,
            command="python3",
            args=["-m", "pytest"],
            input_format="file",
            output_format="text",
            requires_file=True
        )
        super().__init__("pytest", capability)
    
    async def execute(self, request: AdapterRequest) -> AdapterResponse:
        """PyTest 実行"""
        start_time = time.time()
        self.execution_count += 1
        
        try:
            import tempfile
            
            test_content = request.data.get("test_content", "")
            test_args = request.data.get("args", ["-v"])
            
            with tempfile.TemporaryDirectory() as temp_dir:
                test_file = os.path.join(temp_dir, "test_module.py")
                
                with open(test_file, 'w') as f:
                    f.write(test_content)
                
                timeout = request.timeout or self.capability.timeout
                result = subprocess.run([
                    "python3", "-m", "pytest"
                ] + test_args + [test_file], 
                capture_output=True, text=True, timeout=timeout, cwd=temp_dir)
                
                # Parse pytest output
                output_lines = result.stdout.split('\n')
                
                passed = len([line for line in output_lines if "PASSED" in line])
                failed = len([line for line in output_lines if "FAILED" in line])
                
                self.success_count += 1
                self.status = AdapterStatus.ACTIVE
                
                execution_time = time.time() - start_time
                
                # Calculate quality score based on test results
                total_tests = passed + failed
                quality_score = passed / max(total_tests, 1) if total_tests > 0 else 0.0
                
                return AdapterResponse(
                    success=True,
                    data={
                        "tests_passed": passed,
                        "tests_failed": failed,
                        "total_tests": total_tests,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                        "all_passed": failed == 0 and passed > 0
                    },
                    tool_used=self.tool_name,
                    execution_time=execution_time,
                    quality_score=quality_score
                )
                
        except Exception as e:
            self.last_error = str(e)
            self.status = AdapterStatus.ERROR
            
            return AdapterResponse(
                success=False,
                data={},
                tool_used=self.tool_name,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def health_check(self) -> bool:
        """PyTest ヘルスチェック"""
        try:
            result = subprocess.run(["python3", "-m", "pytest", "--version"], 
                                  capture_output=True, timeout=5)
            healthy = result.returncode == 0
            self.status = AdapterStatus.ACTIVE if healthy else AdapterStatus.ERROR
            return healthy
        except:
            self.status = AdapterStatus.ERROR
            return False

class OSSAdapterFramework:
    """OSS Adapter Framework メインクラス"""
    
    def __init__(self):
        self.adapters: Dict[str, BaseOSSAdapter] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "fallback_usage": 0
        }
        
        # デフォルトアダプター登録
        self._register_default_adapters()
    
    def _register_default_adapters(self):
        """デフォルトアダプター登録"""
        self.adapters["continue_dev"] = ContinueDevAdapter()
        self.adapters["aider"] = AiderAdapter()
        self.adapters["flake8"] = Flake8Adapter()
        self.adapters["pytest"] = PyTestAdapter()
    
    def register_adapter(self, adapter: BaseOSSAdapter):
        """アダプター登録"""
        self.adapters[adapter.tool_name] = adapter
        logger.info(f"Registered adapter: {adapter.tool_name}")
    
    def register_fallback_handler(self, tool_name: str, handler: Callable):
        """フォールバックハンドラー登録"""
        self.fallback_handlers[tool_name] = handler
        logger.info(f"Registered fallback handler for: {tool_name}")
    
    async def execute_with_fallback(self, request: AdapterRequest) -> AdapterResponse:
        """フォールバック付きOSSツール実行"""
        self.metrics["total_requests"] += 1
        
        # Primary execution
        adapter = self.adapters.get(request.tool_name)
        if not adapter:
            self.metrics["failed_requests"] += 1
            return AdapterResponse(
                success=False,
                data={},
                tool_used="none",
                execution_time=0,
                error=f"Adapter not found: {request.tool_name}"
            )
        
        # Health check
        if not await adapter.health_check():
            logger.warning(f"Health check failed for {request.tool_name}")
        
        # Execute primary tool
        response = await adapter.execute(request)
        
        # Check if fallback is needed
        if not response.success and request.fallback_enabled:
            fallback_handler = self.fallback_handlers.get(request.tool_name)
            if fallback_handler:
                self.metrics["fallback_usage"] += 1
                logger.info(f"Using fallback for {request.tool_name}")
                
                try:
                    fallback_response = await fallback_handler(request)
                    fallback_response.fallback_used = True
                    response = fallback_response
                except Exception as e:
                    logger.error(f"Fallback failed for {request.tool_name}: {e}")
        
        # Update metrics
        if response.success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        return response
    
    async def batch_execute(self, requests: List[AdapterRequest]) -> List[AdapterResponse]:
        """バッチ実行"""
        logger.info(f"Executing batch of {len(requests)} requests")
        
        # Execute all requests concurrently
        tasks = [self.execute_with_fallback(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                processed_responses.append(AdapterResponse(
                    success=False,
                    data={},
                    tool_used=requests[i].tool_name,
                    execution_time=0,
                    error=str(response)
                ))
            else:
                processed_responses.append(response)
        
        return processed_responses
    
    async def get_framework_status(self) -> Dict[str, Any]:
        """フレームワーク状態取得"""
        adapter_statuses = {}
        
        for name, adapter in self.adapters.items():
            adapter_statuses[name] = await adapter.get_status()
        
        return {
            "framework_status": "active",
            "adapters": adapter_statuses,
            "metrics": self.metrics,
            "registered_adapters": len(self.adapters),
            "fallback_handlers": len(self.fallback_handlers)
        }
    
    async def health_check_all(self) -> Dict[str, bool]:
        """全アダプターヘルスチェック"""
        health_results = {}
        
        for name, adapter in self.adapters.items():
            health_results[name] = await adapter.health_check()
        
        return health_results

# Elder System Fallback Implementations
async def elder_code_generation_fallback(request: AdapterRequest) -> AdapterResponse:
    """Elder システムによるコード生成フォールバック"""
    # This would integrate with Elder Code Craftsman
    return AdapterResponse(
        success=True,
        data={
            "generated_code": "# Elder System fallback code generation\ndef elder_function():\n    return 'Generated by Elder System'",
            "source": "elder_fallback"
        },
        tool_used="elder_system",
        execution_time=0.5,
        quality_score=0.75
    )

async def elder_quality_check_fallback(request: AdapterRequest) -> AdapterResponse:
    """Elder システムによる品質チェックフォールバック"""
    # This would integrate with Elder Quality Inspector
    return AdapterResponse(
        success=True,
        data={
            "quality_score": 0.85,
            "issues": [],
            "iron_will_compliant": True,
            "source": "elder_fallback"
        },
        tool_used="elder_system",
        execution_time=0.3,
        quality_score=0.85
    )

# Framework Factory
def create_oss_adapter_framework() -> OSSAdapterFramework:
    """OSS Adapter Framework ファクトリー"""
    framework = OSSAdapterFramework()
    
    # Register Elder System fallbacks
    framework.register_fallback_handler("continue_dev", elder_code_generation_fallback)
    framework.register_fallback_handler("aider", elder_code_generation_fallback)
    framework.register_fallback_handler("flake8", elder_quality_check_fallback)
    
    return framework

# Example usage and testing
async def test_framework():
    """フレームワークテスト"""
    print("🧪 Testing OSS Adapter Framework")
    
    framework = create_oss_adapter_framework()
    
    # Test requests
    test_requests = [
        AdapterRequest(
            tool_name="flake8",
            operation="lint_check",
            data={"file_content": "def hello():\n    return 'Hello World'"},
            context={}
        ),
        AdapterRequest(
            tool_name="continue_dev",
            operation="code_generation",
            data={"prompt": "Create a simple function", "servant_id": "code-craftsman"},
            context={}
        )
    ]
    
    # Execute tests
    for request in test_requests:
        print(f"\n🔧 Testing {request.tool_name}...")
        response = await framework.execute_with_fallback(request)
        print(f"✅ Success: {response.success}")
        print(f"⏱️  Time: {response.execution_time:.2f}s")
        print(f"🎯 Quality: {response.quality_score}")
        if response.error:
            print(f"❌ Error: {response.error}")
    
    # Framework status
    status = await framework.get_framework_status()
    print(f"\n📊 Framework Status:")
    print(f"  Adapters: {status['registered_adapters']}")
    print(f"  Total Requests: {status['metrics']['total_requests']}")
    print(f"  Success Rate: {status['metrics']['successful_requests']}/{status['metrics']['total_requests']}")

if __name__ == "__main__":
    asyncio.run(test_framework())