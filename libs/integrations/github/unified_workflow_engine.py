#!/usr/bin/env python3
"""
🏗️ Auto Issue Processor A2A Unified Workflow Engine
アーキテクチャ統合・ワークフロー再設計システム

Issue #189対応: 実行パス統合とコンポーネント再設計
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union
from contextlib import asynccontextmanager

logger = logging.getLogger("UnifiedWorkflowEngine")


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ComponentType(Enum):
    ELDER_FLOW = "elder_flow"
    A2A_PROCESSOR = "a2a_processor"
    SECURITY_MANAGER = "security_manager"
    GIT_OPERATIONS = "git_operations"
    PR_CREATOR = "pr_creator"
    QUALITY_GATE = "quality_gate"


@dataclass
class WorkflowContext:
    """ワークフロー実行コンテキスト"""
    workflow_id: str
    issue_number: int
    issue_title: str
    issue_body: str
    labels: List[str]
    priority: str
    execution_mode: str  # "elder_flow" or "a2a"
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentResult:
    """コンポーネント実行結果"""
    component_type: ComponentType
    status: WorkflowStatus
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    """ワークフロー実行結果"""
    workflow_id: str
    status: WorkflowStatus
    components: List[ComponentResult] = field(default_factory=list)
    final_result: Dict[str, Any] = field(default_factory=dict)
    total_execution_time: float = 0.0
    error: Optional[str] = None


class WorkflowComponent(ABC):
    """ワークフローコンポーネント基底クラス"""
    
    def __init__(self, component_type: ComponentType):
        self.component_type = component_type
        self.dependencies: List[ComponentType] = []
        self.is_required = True
    
    @abstractmethod
    async def execute(
        self,
        context: WorkflowContext,
        previous_results: List[ComponentResult]
    ) -> ComponentResult:
        """コンポーネント実行"""
        pass
    
    def get_dependencies(self) -> List[ComponentType]:
        """依存関係取得"""
        return self.dependencies
    
    def is_dependency_satisfied(self, completed_components: List[ComponentType]) -> boolreturn all(dep in completed_components for dep in self.dependencies):
    """存関係満足チェック"""

:
class SecurityValidationComponent(WorkflowComponent):
    """セキュリティ検証コンポーネント"""
    
    def __init__(self):
        super().__init__(ComponentType.SECURITY_MANAGER)
        self.is_required = True
    
    async def execute(
        self,
        context: WorkflowContext,
        previous_results: List[ComponentResult]
    ) -> ComponentResult:
        """セキュリティ検証実行"""
        start_time = time.time()
        
        try:
            from .security_manager import get_security_manager
            
            security_manager = get_security_manager()
            
            # 基本的なセキュリティチェック
            request_data = {
                "issue_number": context.issue_number,
                "issue_title": context.issue_title,
                "issue_body": context.issue_body,
                "labels": context.labels,
                "operation": "process_issue"
            }
            
            # 仮のセキュリティコンテキスト（実際は認証されたユーザー情報を使用）
            from .security_manager import SecurityContext, PermissionLevel, SecurityLevel
            
            # システムユーザーとして実行（自動処理のため）
            system_context = SecurityContext(
                user_id="system_a2a",
                session_id="auto_generated",
                permissions=[PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXECUTE],
                security_level=SecurityLevel.MEDIUM,
                expires_at=datetime.now(),
                mfa_verified=True
            )
            
            validation_result = security_manager.validate_request(request_data, system_context)
            
            if validation_result["valid"]:
                return ComponentResult(
                    component_type=self.component_type,
                    status=WorkflowStatus.COMPLETED,
                    data={
                        "validation_passed": True,
                        "security_level": validation_result["security_level"].value,
                        "sanitized_data": validation_result["sanitized_request"]
                    },
                    execution_time=time.time() - start_time
                )
            else:
                return ComponentResult(
                    component_type=self.component_type,
                    status=WorkflowStatus.FAILED,
                    error=f"Security validation failed: {validation_result['violations']}",
                    execution_time=time.time() - start_time
                )
        
        except Exception as e:
            logger.error(f"Security validation error: {str(e)}")
            return ComponentResult(
                component_type=self.component_type,
                status=WorkflowStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )


class ElderFlowComponent(WorkflowComponent):
    """Elder Flow実行コンポーネント"""
    
    def __init__(self):
        super().__init__(ComponentType.ELDER_FLOW)
        self.dependencies = [ComponentType.SECURITY_MANAGER]
    
    async def execute(
        self,
        context: WorkflowContext,
        previous_results: List[ComponentResult]
    ) -> ComponentResult:
        """Elder Flow実行"""
        start_time = time.time()
        
        try:
            # セキュリティ検証結果を取得
            security_result = next(
                (r for r in previous_results if r.component_type == ComponentType.SECURITY_MANAGER),
                None
            )
            
            if not security_result or security_result.status != WorkflowStatus.COMPLETED:
                return ComponentResult(
                    component_type=self.component_type,
                    status=WorkflowStatus.FAILED,
                    error="Security validation not completed",
                    execution_time=time.time() - start_time
                )
            
            # AutoIssueElderFlowEngineを使用
            from .auto_issue_processor import AutoIssueElderFlowEngine
            
            elder_flow_engine = AutoIssueElderFlowEngine()
            
            flow_request = {
                "task_name": f"Auto-fix Issue #{context.issue_number}: {context.issue_title}",
                "priority": context.priority,
                "context": {
                    "issue_number": context.issue_number,
                    "issue_title": context.issue_title,
                    "issue_body": context.issue_body,
                    "labels": context.labels,
                    "security_context": security_result.data
                }
            }
            
            elder_flow_result = await elder_flow_engine.execute_flow(flow_request)
            
            if elder_flow_result.get("status") == "success":
                return ComponentResult(
                    component_type=self.component_type,
                    status=WorkflowStatus.COMPLETED,
                    data=elder_flow_result,
                    execution_time=time.time() - start_time
                )
            else:
                return ComponentResult(
                    component_type=self.component_type,
                    status=WorkflowStatus.FAILED,
                    error=elder_flow_result.get("message", "Elder Flow execution failed"),
                    data=elder_flow_result,
                    execution_time=time.time() - start_time
                )
        
        except Exception as e:
            logger.error(f"Elder Flow execution error: {str(e)}")
            return ComponentResult(
                component_type=self.component_type,
                status=WorkflowStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )


class A2AProcessorComponent(WorkflowComponent):
    """A2A独立プロセッサーコンポーネント"""
    
    def __init__(self):
        super().__init__(ComponentType.A2A_PROCESSOR)
        self.dependencies = [ComponentType.SECURITY_MANAGER]
    
    async def execute(
        self,
        context: WorkflowContext,
        previous_results: List[ComponentResult]
    ) -> ComponentResult:
        """A2A処理実行"""
        start_time = time.time()
        
        try:
            # セキュリティ検証結果を取得
            security_result = next(
                (r for r in previous_results if r.component_type == ComponentType.SECURITY_MANAGER),
                None
            )
            
            if not security_result or security_result.status != WorkflowStatus.COMPLETED:
                return ComponentResult(
                    component_type=self.component_type,
                    status=WorkflowStatus.FAILED,
                    error="Security validation not completed",
                    execution_time=time.time() - start_time
                )
            
            # A2A独立プロセス実行
            from .auto_issue_processor import AutoIssueProcessor
            from github import Github
            from libs.env_manager import EnvManager
            
            # GitHub Issueオブジェクト作成
            github_token = EnvManager.get_github_token()
            repo_owner = EnvManager.get_github_repo_owner()
            repo_name = EnvManager.get_github_repo_name()
            
            github = Github(github_token)
            repo = github.get_repo(f"{repo_owner}/{repo_name}")
            issue = repo.get_issue(context.issue_number)
            
            processor = AutoIssueProcessor()
            a2a_result = await processor.process_issue_isolated(issue)
            
            if a2a_result.get("status") == "success":
                return ComponentResult(
                    component_type=self.component_type,
                    status=WorkflowStatus.COMPLETED,
                    data=a2a_result,
                    execution_time=time.time() - start_time
                )
            else:
                return ComponentResult(
                    component_type=self.component_type,
                    status=WorkflowStatus.FAILED,
                    error=a2a_result.get("message", "A2A processing failed"),
                    data=a2a_result,
                    execution_time=time.time() - start_time
                )
        
        except Exception as e:
            logger.error(f"A2A processing error: {str(e)}")
            return ComponentResult(
                component_type=self.component_type,
                status=WorkflowStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )


class QualityGateComponent(WorkflowComponent):
    """品質ゲートコンポーネント"""
    
    def __init__(self):
        super().__init__(ComponentType.QUALITY_GATE)
        self.dependencies = [ComponentType.ELDER_FLOW, ComponentType.A2A_PROCESSOR]
        self.is_required = False  # どちらか一つが成功すればOK
    
    async def execute(
        self,
        context: WorkflowContext,
        previous_results: List[ComponentResult]
    ) -> ComponentResult:
        """品質ゲート実行"""
        start_time = time.time()
        
        try:
            # 実行されたコンポーネントの結果を取得
            elder_flow_result = next(
                (r for r in previous_results if r.component_type == ComponentType.ELDER_FLOW),
                None
            )
            a2a_result = next(
                (r for r in previous_results if r.component_type == ComponentType.A2A_PROCESSOR),
                None
            )
            
            # 少なくとも一つのコンポーネントが成功している必要
            successful_component = None
            if elder_flow_result and elder_flow_result.status == WorkflowStatus.COMPLETED:
                successful_component = elder_flow_result
            elif a2a_result and a2a_result.status == WorkflowStatus.COMPLETED:
                successful_component = a2a_result
            
            if not successful_component:
                return ComponentResult(
                    component_type=self.component_type,
                    status=WorkflowStatus.FAILED,
                    error="No successful implementation component found",
                    execution_time=time.time() - start_time
                )
            
            # 品質チェック実行
            quality_score = await self._calculate_quality_score(successful_component, context)
            
            # 品質基準チェック
            quality_threshold = 0.7  # 70%以上で合格
            
            if quality_score >= quality_threshold:
                return ComponentResult(
                    component_type=self.component_type,
                    status=WorkflowStatus.COMPLETED,
                    data={
                        "quality_score": quality_score,
                        "threshold": quality_threshold,
                        "passed": True,
                        "successful_component": successful_component.component_type.value,
                        "implementation_data": successful_component.data
                    },
                    execution_time=time.time() - start_time
                )
            else:
                return ComponentResult(
                    component_type=self.component_type,
                    status=WorkflowStatus.FAILED,
                    error=f"Quality gate failed: score {quality_score} < threshold " \
                        "{quality_threshold}",
                    data={
                        "quality_score": quality_score,
                        "threshold": quality_threshold,
                        "passed": False
                    },
                    execution_time=time.time() - start_time
                )
        
        except Exception as e:
            logger.error(f"Quality gate error: {str(e)}")
            return ComponentResult(
                component_type=self.component_type,
                status=WorkflowStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _calculate_quality_score(
        self,
        component_result: ComponentResult,
        context: WorkflowContext
    ) -> float:
        """品質スコア計算"""
        score = 0.0
        
        # 基本成功スコア
        if component_result.status == WorkflowStatus.COMPLETED:
            score += 0.3
        
        # PR作成成功スコア
        if component_result.data.get("pr_url"):
            score += 0.3
        
        # 実装の存在スコア
        if "implementation" in component_result.data or "claude_result" in component_result.data:
            score += 0.2
        
        # エラーがないスコア
        if not component_result.error:
            score += 0.1
        
        # 実行時間スコア（短いほど良い）
        if component_result.execution_time < 60:  # 1分以内
            score += 0.1
        
        return min(score, 1.0)


class UnifiedWorkflowEngine:
    """統一ワークフローエンジン"""
    
    def __init__(self):
        self.components: Dict[ComponentType, WorkflowComponent] = {}
        self.execution_history: List[WorkflowResult] = []
        self.max_parallel_executions = 5  # 最大並列実行数
        self._register_components()
    
    def _register_components(self)self.components[ComponentType.SECURITY_MANAGER] = SecurityValidationComponent()
    """コンポーネント登録"""
        self.components[ComponentType.ELDER_FLOW] = ElderFlowComponent()
        self.components[ComponentType.A2A_PROCESSOR] = A2AProcessorComponent()
        self.components[ComponentType.QUALITY_GATE] = QualityGateComponent()
    
    async def execute_workflow(self, context: WorkflowContext) -> WorkflowResultstart_time = time.time():
    """一ワークフロー実行"""
        workflow_result = WorkflowResult(
            workflow_id=context.workflow_id,
            status=WorkflowStatus.RUNNING
        )
        :
        try:
            logger.info(f"Starting unified workflow for issue #{context.issue_number} (mode: {context.execution_mode})")
            
            # 実行計画作成
            execution_plan = self._create_execution_plan(context.execution_mode)
            
            # 段階的実行
            completed_components: List[ComponentType] = []
            component_results: List[ComponentResult] = []
            
            for stage in execution_plan:
                # 並列実行可能なコンポーネントを特定
                parallel_components = [
                    comp_type for comp_type in stage
                    if self.components[comp_type].is_dependency_satisfied(completed_components)
                ]
                
                if parallel_components:
                    # 並列実行
                    stage_results = await self._execute_components_parallel(
                        parallel_components, context, component_results
                    )
                    
                    component_results.extend(stage_results)
                    
                    # 成功したコンポーネントを記録
                    for result in stage_results:
                        if result.status == WorkflowStatus.COMPLETED:
                            completed_components.append(result.component_type)
                        elif self.components[result.component_type].is_required:
                            # 必須コンポーネントが失敗した場合はワークフロー停止
                            workflow_result.status = WorkflowStatus.FAILED
                            workflow_result.error = f"Required component failed: {result.component_type.value}" \
                                "Required component failed: {result.component_type.value}"
                            break
                
                if workflow_result.status == WorkflowStatus.FAILED:
                    break
            
            # 最終結果集計
            if workflow_result.status != WorkflowStatus.FAILED:
                workflow_result.status = WorkflowStatus.COMPLETED
                workflow_result.final_result = self._aggregate_results(component_results)
            
            workflow_result.components = component_results
            workflow_result.total_execution_time = time.time() - start_time
            
            # 実行履歴に記録
            self.execution_history.append(workflow_result)
            
            logger.info(f"Workflow completed for issue #{context.issue_number}: {workflow_result.status." \
                "value}")
            
            return workflow_result
        
        except Exception as e:
            logger.error(f"Workflow execution error: {str(e)}")
            workflow_result.status = WorkflowStatus.FAILED
            workflow_result.error = str(e)
            workflow_result.total_execution_time = time.time() - start_time
            return workflow_result
    
    def _create_execution_plan(self, execution_mode: str) -> List[List[ComponentType]]:
        """実行計画作成"""
        if execution_mode == "elder_flow":
            return [
                [ComponentType.SECURITY_MANAGER],
                [ComponentType.ELDER_FLOW],
                [ComponentType.QUALITY_GATE]
            ]
        elif execution_mode == "a2a":
            return [
                [ComponentType.SECURITY_MANAGER],
                [ComponentType.A2A_PROCESSOR],
                [ComponentType.QUALITY_GATE]
            ]
        else:  # hybrid mode
            return [
                [ComponentType.SECURITY_MANAGER],
                [ComponentType.ELDER_FLOW, ComponentType.A2A_PROCESSOR],  # 並列実行
                [ComponentType.QUALITY_GATE]
            ]
    
    async def _execute_components_parallel(
        self, 
        component_types: List[ComponentType], 
        context: WorkflowContext, 
        previous_results: List[ComponentResult]
    ) -> List[ComponentResult]:
        """コンポーネント並列実行"""
        tasks = []
        
        for comp_type in component_types:
            component = self.components[comp_type]
            task = asyncio.create_task(component.execute(context, previous_results))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 例外をComponentResultに変換
        component_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                component_results.append(ComponentResult(
                    component_type=component_types[i],
                    status=WorkflowStatus.FAILED,
                    error=str(result)
                ))
            else:
                component_results.append(result)
        
        return component_results
    
    def _aggregate_results(self, component_results: List[ComponentResult]) -> Dict[str, Any]:
        """結果集約"""
        aggregated = {
            "components_executed": len(component_results),
            "successful_components": len([r for r in component_results if r.status == WorkflowStatus.COMPLETED]),
            "failed_components": len([r for r in component_results if r.status == WorkflowStatus.FAILED]),
            "total_execution_time": sum(r.execution_time for r in component_results)
        }
        
        # 最終的な成果物を特定
        quality_gate_result = next(
            (r for r in component_results if r.component_type == ComponentType.QUALITY_GATE),
            None
        )
        
        if quality_gate_result and quality_gate_result.status == WorkflowStatus.COMPLETED:
            aggregated.update(quality_gate_result.data)
        
        return aggregated
    
    async def execute_auto_issue_workflow(self, issue_data: Dict[str, Any], execution_mode: str = "hybrid" \
        "hybrid") -> WorkflowResult:
        """Auto Issue用ワークフロー実行（外部API）"""
        context = WorkflowContext(
            workflow_id=f"auto_issue_{issue_data['number']}_{int(time.time())}",
            issue_number=issue_data["number"],
            issue_title=issue_data["title"],
            issue_body=issue_data.get("body", ""),
            labels=issue_data.get("labels", []),
            priority=issue_data.get("priority", "medium"),
            execution_mode=execution_mode,
            metadata={"source": "auto_issue_processor"}
        )
        
        return await self.execute_workflow(context)
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """実行統計取得"""
        if not self.execution_history:
            return {"total_executions": 0}
        
        successful = len([w for w in self.execution_history if w.status == WorkflowStatus.COMPLETED])
        failed = len([w for w in self.execution_history if w.status == WorkflowStatus.FAILED])
        
        avg_execution_time = sum(w.total_execution_time for w in self.execution_history) / len(self.execution_history)
        
        return {
            "total_executions": len(self.execution_history),
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": successful / len(self.execution_history) if self.execution_history else 0,
            "average_execution_time": avg_execution_time,
            "last_execution": self.execution_history[-1].workflow_id if self.execution_history else None
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """エンジン機能一覧取得"""
        return {
            "service": "UnifiedWorkflowEngine",
            "version": "1.0.0",
            "supported_modes": ["elder_flow", "a2a", "hybrid"],
            "components": [comp.value for comp in ComponentType],
            "max_parallel_executions": self.max_parallel_executions,
            "features": [
                "component_dependency_management",
                "execution_mode_switching", 
                "error_recovery_integration",
                "performance_optimization",
                "comprehensive_logging"
            ]
        }


# シングルトンインスタンス
_workflow_engine = None

def get_unified_workflow_engine() -> UnifiedWorkflowEngine:
    """統一ワークフローエンジンシングルトン取得"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = UnifiedWorkflowEngine()
    return _workflow_engine