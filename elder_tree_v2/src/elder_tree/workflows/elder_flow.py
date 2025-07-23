"""
Elder Flow - 5段階自動化ワークフロー
TDD Green Phase: 完全実装
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json
import subprocess
import os
from pathlib import Path
import structlog
from python_a2a import agent, A2AServer, Message
from prometheus_client import Counter, Histogram, Gauge
import redis.asyncio as redis
from sqlmodel import SQLModel, Field as SQLField, Session, create_engine, select


class StageStatus(str, Enum):
    """Stageステータス"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Stage:
    """Elder Flowステージ"""
    name: str
    status: StageStatus = StageStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def completed(self) -> bool:
        return self.status == StageStatus.COMPLETED
    
    @property
    def duration_seconds(self) -> float:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0


@dataclass
class ElderFlowResult:
    """Elder Flow実行結果"""
    flow_id: str
    status: str
    stages: List[Stage]
    total_duration_seconds: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def stages_completed(self) -> int:
        return sum(1 for stage in self.stages if stage.completed)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "flow_id": self.flow_id,
            "status": self.status,
            "stages": [
                {
                    "name": stage.name,
                    "status": stage.status,
                    "duration_seconds": stage.duration_seconds,
                    "result": stage.result,
                    "error": stage.error
                }
                for stage in self.stages
            ],
            "total_duration_seconds": self.total_duration_seconds,
            "stages_completed": self.stages_completed,
            "metadata": self.metadata
        }


# SQLModel FlowRecord定義
class FlowRecord(SQLModel, table=True):
    """Elder Flow実行記録"""
    __tablename__ = "elder_flow_records"
    
    id: Optional[int] = SQLField(default=None, primary_key=True)
    flow_id: str = SQLField(index=True, unique=True)
    task_type: str
    priority: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    stages_completed: int = 0
    result_json: str = SQLField(default="{}")  # JSON形式で保存


@agent(name="ElderFlow", description="Elder Tree 5-stage automation workflow")
class ElderFlow(A2AServer):
    """
    Elder Flow - 5段階自動化ワークフロー
    
    1. 賢者協議 (Sage Consultation)
    2. サーバント実行 (Servant Execution)
    3. 品質ゲート (Quality Gate)
    4. 評議会報告 (Council Report)
    5. Git自動化 (Git Automation)
    """
    
    def __init__(self, 
                 """初期化メソッド"""
                 db_url: str = "sqlite:///elder_flow.db",
                 redis_url: str = "redis://localhost:6379",
                 port: int = 50100):
        super().__init__(name="elder_flow", port=port)
        
        self.logger = structlog.get_logger(__name__)
        self.stages = [
            "sage_consultation",
            "servant_execution",
            "quality_gate",
            "council_report",
            "git_automation"
        ]
        
        # データベース初期化
        self.engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)
        
        # Redis接続
        self.redis_url = redis_url
        self.redis_client = None
        
        # メトリクス
        self.flow_counter = Counter(
            'elder_flow_executions_total',
            'Total flow executions',
            ['task_type', 'status']
        )
        
        self.stage_duration = Histogram(
            'elder_flow_stage_duration_seconds',
            'Stage execution duration',
            ['stage_name']
        )
        
        self.active_flows = Gauge(
            'elder_flow_active_flows',
            'Currently active flows'
        )
        
        # ハンドラー登録
        self._register_handlers()
    
    async def start(self):
        """起動時処理"""
        await super().start()
        self.redis_client = await redis.from_url(self.redis_url)
        self.logger.info("Elder Flow started")
    
    async def stop(self):
        """停止時処理"""
        if self.redis_client:
            await self.redis_client.close()
        await super().stop()
    
    def _register_handlers(self):
        """Elder Flowハンドラー登録"""
        
        @self.on_message("execute_flow")
        async def handle_execute_flow(message: Message) -> Dict[str, Any]:
            """
            Elder Flow実行リクエスト
            """
            data = message.data
            task_type = data.get("task_type")
            requirements = data.get("requirements", [])
            priority = data.get("priority", "medium")
            
            result = await self.execute(
                task_type=task_type,
                requirements=requirements,
                priority=priority
            )
            
            return result.to_dict()
    
    async def execute(
        self,
        task_type: str,
        requirements: List[str],
        priority: str = "medium",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ElderFlowResult:
        """
        Elder Flow実行
        
        Args:
            task_type: タスク種別
            requirements: 要件リスト
            priority: 優先度
            metadata: 追加メタデータ
            
        Returns:
            ElderFlowResult: 実行結果
        """
        flow_id = f"FLOW-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        start_time = datetime.now()
        stages = [Stage(name=stage_name) for stage_name in self.stages]
        
        # アクティブフロー数を増やす
        self.active_flows.inc()
        
        # Redisにステータス保存
        if self.redis_client:
            await self.redis_client.setex(
                f"flow:{flow_id}:status",
                3600,  # 1時間TTL
                "running"
            )
        
        # データベースに記録
        with Session(self.engine) as session:
            flow_record = FlowRecord(
                flow_id=flow_id,
                task_type=task_type,
                priority=priority,
                status="running",
                started_at=start_time,
                stages_completed=0
            )
            session.add(flow_record)
            session.commit()
        
        try:
            # Stage 1: Sage Consultation
            stages[0] = await self._execute_stage(
                stages[0], 
                self._sage_consultation,
                task_type, requirements, priority
            )
            
            # Stage 2: Servant Execution
            stages[1] = await self._execute_stage(
                stages[1],
                self._servant_execution,
                task_type, requirements, stages[0].result
            )
            
            # Stage 3: Quality Gate
            stages[2] = await self._execute_stage(
                stages[2],
                self._quality_gate,
                stages[1].result
            )
            
            # Stage 4: Council Report
            stages[3] = await self._execute_stage(
                stages[3],
                self._council_report,
                task_type, stages[:3]
            )
            
            # Stage 5: Git Automation
            stages[4] = await self._execute_stage(
                stages[4],
                self._git_automation,
                task_type, stages[1].result
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # 成功終了
            flow_result = ElderFlowResult(
                flow_id=flow_id,
                status="completed",
                stages=stages,
                total_duration_seconds=duration,
                metadata=metadata or {}
            )
            
            # メトリクス更新
            self.flow_counter.labels(
                task_type=task_type,
                status="completed"
            ).inc()
            
        except Exception as e:
            self.logger.error("Elder Flow failed", error=str(e), flow_id=flow_id)
            
            # 失敗したステージを特定
            for i, stage in enumerate(stages):
                if stage.status == StageStatus.RUNNING:
                    stage.status = StageStatus.FAILED
                    stage.error = str(e)
                    stage.completed_at = datetime.now()
                elif stage.status == StageStatus.PENDING:
                    stage.status = StageStatus.SKIPPED
            
            duration = (datetime.now() - start_time).total_seconds()
            
            flow_result = ElderFlowResult(
                flow_id=flow_id,
                status="failed",
                stages=stages,
                total_duration_seconds=duration,
                metadata=metadata or {}
            )
            
            # メトリクス更新
            self.flow_counter.labels(
                task_type=task_type,
                status="failed"
            ).inc()
            
            # Incident Sageに報告
            await self._report_failure_to_incident_sage(flow_id, flow_result)
        
        finally:
            # アクティブフロー数を減らす
            self.active_flows.dec()
            
            # Redisステータス更新
            if self.redis_client:
                await self.redis_client.setex(
                    f"flow:{flow_id}:status",
                    3600,
                    flow_result.status
                )
                await self.redis_client.setex(
                    f"flow:{flow_id}:result",
                    3600,
                    json.dumps(flow_result.to_dict())
                )
            
            # データベース更新
            with Session(self.engine) as session:
                statement = select(FlowRecord).where(FlowRecord.flow_id == flow_id)
                record = session.exec(statement).first()
                if record:
                    record.status = flow_result.status
                    record.completed_at = datetime.now()
                    record.total_duration_seconds = flow_result.total_duration_seconds
                    record.stages_completed = flow_result.stages_completed
                    record.result_json = json.dumps(flow_result.to_dict())
                    session.add(record)
                    session.commit()
        
        return flow_result
    
    async def _execute_stage(
        self,
        stage: Stage,
        stage_func,
        *args
    ) -> Stage:
        """個別ステージ実行"""
        stage.status = StageStatus.RUNNING
        stage.started_at = datetime.now()
        
        try:
            with self.stage_duration.labels(stage_name=stage.name).time():
                stage.result = await stage_func(*args)
            
            stage.status = StageStatus.COMPLETED
            stage.completed_at = datetime.now()
            
            self.logger.info(
                f"Stage completed: {stage.name}",
                duration=stage.duration_seconds
            )
            
        except Exception as e:
            stage.status = StageStatus.FAILED
            stage.error = str(e)
            stage.completed_at = datetime.now()
            raise
        
        return stage
    
    async def _sage_consultation(
        self,
        task_type: str,
        requirements: List[str],
        priority: str
    ) -> Dict[str, Any]:
        """ステージ1: 賢者協議"""
        self.logger.info("Stage 1: Sage Consultation")
        
        # 4賢者への並列相談
        consultation_tasks = [
            self._consult_sage("knowledge_sage", task_type, requirements),
            self._consult_sage("task_sage", task_type, requirements),
            self._consult_sage("incident_sage", task_type, requirements),
            self._consult_sage("rag_sage", task_type, requirements)
        ]
        
        results = await asyncio.gather(*consultation_tasks, return_exceptions=True)
        
        consultation_result = {
            "consultation_complete": True,
            "timestamp": datetime.now().isoformat(),
            "sages_consulted": {}
        }
        
        sage_names = ["knowledge_sage", "task_sage", "incident_sage", "rag_sage"]
        for sage_name, result in zip(sage_names, results):
            if isinstance(result, Exception):
                consultation_result["sages_consulted"][sage_name] = {
                    "status": "error",
                    "error": str(result)
                }
            else:
                consultation_result["sages_consulted"][sage_name] = result
        
        # 統合推奨事項の抽出
        recommendations = []
        estimated_hours = 0
        
        for sage_name, sage_result in consultation_result["sages_consulted"].items():
            if isinstance(sage_result, dict) and sage_result.get("status") != "error":
                if "recommendations" in sage_result:
                    recommendations.extend(sage_result["recommendations"])
                if "estimated_hours" in sage_result:
                    estimated_hours = max(estimated_hours, sage_result["estimated_hours"])
        
        consultation_result["recommendations"] = list(set(recommendations))  # 重複除去
        consultation_result["estimated_hours"] = estimated_hours
        
        return consultation_result
    
    async def _consult_sage(
        self,
        sage_name: str,
        task_type: str,
        requirements: List[str]
    ) -> Dict[str, Any]:
        """個別賢者への相談"""
        try:
            response = await self.send_message(
                target=sage_name,
                message_type="elder_flow_consultation",
                data={
                    "task_type": task_type,
                    "requirements": requirements,
                    "requester": "elder_flow"
                },
                timeout=10.0
            )
            
            return response.data
            
        except Exception as e:
            self.logger.warning(f"Failed to consult {sage_name}", error=str(e))
            raise
    
    async def _servant_execution(
        self,
        task_type: str,
        requirements: List[str],
        consultation_result: Dict[str,
        Any]
    ) -> Dict[str, Any]:
        """ステージ2: サーバント実行"""
        self.logger.info("Stage 2: Servant Execution")
        
        # タスクタイプに応じたサーバント選択
        servant = self._select_servant(task_type)
        
        if not servant:
            raise ValueError(f"No suitable servant found for task type: {task_type}")
        
        # サーバントにタスク実行依頼
        response = await self.send_message(
            target=servant,
            message_type="execute_task",
            data={
                "task_type": task_type,
                "parameters": {
                    "requirements": requirements,
                    "consultation": consultation_result
                },
                "quality_requirements": {
                    "no_todos": True,
                    "test_coverage": 85
                }
            },
            timeout=300.0  # 5分タイムアウト
        )
        
        result = response.data
        
        # 実行結果の検証
        if result.get("status") != "success":
            raise Exception(f"Servant execution failed: {result.get('message', 'Unknown error')}")
        
        return {
            "execution_complete": True,
            "servant": servant,
            "result": result.get("result", {}),
            "quality": result.get("quality", {}),
            "files_created": result.get("result", {}).get("files_created", [])
        }
    
    def _select_servant(self, task_type: str) -> Optional[str]:
        """タスクタイプに応じたサーバント選択"""
        servant_mapping = {
            "code_generation": "code_crafter",
            "feature_implementation": "code_crafter",
            "research": "research_wizard",
            "documentation": "research_wizard",
            "quality_check": "quality_guardian",
            "optimization": "quality_guardian",
            "incident_response": "crisis_responder",
            "emergency_fix": "crisis_responder"
        }
        
        # キーワードマッチング
        for keyword, servant in servant_mapping.items():
            if keyword in task_type.lower():
                return servant
        
        # デフォルト
        return "code_crafter"
    
    async def _quality_gate(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """ステージ3: 品質ゲート"""
        self.logger.info("Stage 3: Quality Gate")
        
        quality_score = execution_result.get("quality", {}).get("score", 0)
        quality_passed = execution_result.get("quality", {}).get("passed", False)
        
        # 追加の品質チェック
        additional_checks = await self._perform_quality_checks(execution_result)
        
        # 総合判定
        all_checks_passed = quality_passed and all(
            check.get("passed", False) for check in additional_checks.values()
        )
        
        # Iron Will基準チェック
        iron_will_score = min(
            quality_score,
            additional_checks.get("iron_will", {}).get("score", 100)
        )
        
        return {
            "quality_passed": all_checks_passed,
            "quality_score": quality_score,
            "iron_will_score": iron_will_score,
            "issues_found": sum(
                len(check.get("issues", [])) for check in additional_checks.values()
            ),
            "detailed_checks": additional_checks
        }
    
    async def _perform_quality_checks(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """追加品質チェック"""
        checks = {}
        
        # Iron Willチェック（TODO/FIXMEなど）
        files_created = execution_result.get("files_created", [])
        iron_will_issues = []
        
        for file_path in files_created:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    if "TODO" in content or "FIXME" in content:
                        iron_will_issues.append(f"Found TODO/FIXME in {file_path}")
        
        checks["iron_will"] = {
            "passed": len(iron_will_issues) == 0,
            "score": 100 if len(iron_will_issues) == 0 else 70,
            "issues": iron_will_issues
        }
        
        # セキュリティチェック（簡易版）
        security_issues = []
        for file_path in files_created:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    # 危険なパターンのチェック
                    if "eval(" in content or "exec(" in content:
                        security_issues.append(f"Dangerous function found in {file_path}")
                    if "password" in content.lower() and "=" in content:
                        security_issues.append(f"Potential hardcoded password in {file_path}")
        
        checks["security"] = {
            "passed": len(security_issues) == 0,
            "score": 100 if len(security_issues) == 0 else 50,
            "issues": security_issues
        }
        
        return checks
    
    async def _council_report(
        self,
        task_type: str,
        completed_stages: List[Stage]
    ) -> Dict[str, Any]:
        """ステージ4: 評議会報告"""
        self.logger.info("Stage 4: Council Report")
        
        report_id = f"REPORT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # レポート作成
        report = {
            "report_id": report_id,
            "task_type": task_type,
            "timestamp": datetime.now().isoformat(),
            "stages_summary": [
                {
                    "name": stage.name,
                    "status": stage.status,
                    "duration_seconds": stage.duration_seconds,
                    "key_results": self._extract_key_results(stage)
                }
                for stage in completed_stages
            ],
            "overall_status": "success" if all(s.completed for s in completed_stages) else "partial",
            "recommendations": self._generate_recommendations(completed_stages)
        }
        
        # レポートをRedisに保存
        if self.redis_client:
            await self.redis_client.setex(
                f"report:{report_id}",
                86400,  # 24時間TTL
                json.dumps(report)
            )
        
        # Knowledge Sageに学習データとして送信
        try:
            await self.send_message(
                target="knowledge_sage",
                message_type="store_elder_flow_report",
                data=report
            )
        except Exception as e:
            self.logger.warning("Failed to send report to Knowledge Sage", error=str(e))
        
        return {
            "report_generated": True,
            "report_id": report_id,
            "summary": f"Elder Flow completed with {len([s for s in completed_stages if s.completed])} successful stages"
        }
    
    def _extract_key_results(self, stage: Stage) -> List[str]:
        """ステージから主要結果を抽出"""
        key_results = []
        
        if stage.result:
            if stage.name == "sage_consultation":
                if "recommendations" in stage.result:
                    key_results.append(f"Received {len(stage.result['recommendations'])} recommendations")
                if "estimated_hours" in stage.result:
                    key_results.append(f"Estimated effort: {stage.result['estimated_hours']} hours")
            
            elif stage.name == "servant_execution":
                if "files_created" in stage.result:
                    key_results.append(f"Created {len(stage.result['files_created'])} files")
                if "quality" in stage.result:
                    score = stage.result["quality"].get("score", 0)
                    key_results.append(f"Quality score: {score}")
            
            elif stage.name == "quality_gate":
                if "quality_passed" in stage.result:
                    key_results.append(f"Quality gate: {'PASSED' if stage.result['quality_passed'] else 'FAILED'}")
                if "iron_will_score" in stage.result:
                    key_results.append(f"Iron Will score: {stage.result['iron_will_score']}")
        
        return key_results
    
    def _generate_recommendations(self, completed_stages: List[Stage]) -> List[str]:
        """完了ステージから推奨事項を生成"""
        recommendations = []
        
        # 品質ゲートの結果に基づく推奨
        quality_stage = next((s for s in completed_stages if s.name == "quality_gate"), None)
        if quality_stage and quality_stage.result:
            if not quality_stage.result.get("quality_passed", True):
                recommendations.append("Address quality issues before deployment")
            
            iron_will_score = quality_stage.result.get("iron_will_score", 100)
            if iron_will_score < 85:
                recommendations.append("Improve code quality to meet Iron Will standards")
        
        # 実行時間に基づく推奨
        total_duration = sum(s.duration_seconds for s in completed_stages)
        if total_duration > 300:  # 5分以上
            recommendations.append("Consider optimizing workflow for faster execution")
        
        return recommendations
    
    async def _git_automation(
        self,
        task_type: str,
        execution_result: Dict[str,
        Any]
    ) -> Dict[str, Any]:
        """ステージ5: Git自動化"""
        self.logger.info("Stage 5: Git Automation")
        
        files_created = execution_result.get("files_created", [])
        
        if not files_created:
            return {
                "git_operations_complete": True,
                "message": "No files to commit"
            }
        
        try:
            # Git操作
            branch_name = f"elder-flow/{task_type.lower(
                ).replace(' ',
                '-')}-{datetime.now().strftime('%Y%m%d%H%M%S'
            )}"
            
            # ブランチ作成
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)
            
            # ファイル追加
            for file_path in files_created:
                if os.path.exists(file_path):
                    subprocess.run(["git", "add", file_path], check=True)
            
            # コミット
            commit_message = f"feat: {task_type} - Elder Flow automated implementation\n\n🤖 Generated with " \
                "[Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude " \
                "<noreply@anthropic.com>"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            
            # コミットハッシュ取得
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True
            )
            commit_hash = result.stdout.strip()
            
            return {
                "git_operations_complete": True,
                "branch": branch_name,
                "commit_hash": commit_hash,
                "files_committed": files_created,
                "message": "Git operations completed successfully"
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error("Git operation failed", error=str(e))
            return {
                "git_operations_complete": False,
                "error": str(e),
                "message": "Git operations failed, manual intervention required"
            }
    
    async def _report_failure_to_incident_sage(self, flow_id: str, flow_result: ElderFlowResult):
        """失敗をIncident Sageに報告"""
        try:
            failed_stage = next(
                (s for s in flow_result.stages if s.status == StageStatus.FAILED),
                None
            )
            
            if failed_stage:
                await self.send_message(
                    target="incident_sage",
                    message_type="detect_incident",
                    data={
                        "title": f"Elder Flow Failed: {flow_id}",
                        "description": f"Stage '{failed_stage.name}' failed with error: {failed_stage.error}",
                        "severity": "high",
                        "affected_services": ["elder_flow", failed_stage.name],
                        "source": "elder_flow_automation"
                    }
                )
        except Exception as e:
            self.logger.error("Failed to report to Incident Sage", error=str(e))


# 単体実行用
async def main():
    flow = ElderFlow()
    await flow.start()
    print(f"Elder Flow running on port {flow.port}")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await flow.stop()


if __name__ == "__main__":
    asyncio.run(main())