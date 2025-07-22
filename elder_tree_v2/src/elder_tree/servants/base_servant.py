"""
Elder Servant Base - サーバント基底クラス
TDD Green Phase: python-a2aを使用した実装
"""

from typing import Dict, Any, List, Optional, Tuple
import asyncio
from datetime import datetime
from elder_tree.agents.base_agent import ElderTreeAgent
from python_a2a import Message
import structlog
from prometheus_client import Counter, Histogram, Gauge
import json


class ElderServantBase(ElderTreeAgent):
    """
    Elder Servant基底クラス
    
    全てのサーバントが継承する基本機能:
    - 4賢者との通信機能
    - タスク実行・レポート機能
    - 品質保証機能
    - メトリクス収集
    """
    
    def __init__(self, name: str, tribe: str, specialty: str, port: Optional[int] = None):
        """
        初期化
        
        Args:
            name: サーバント名
            tribe: 所属部族 (dwarf, rag_wizard, elf, incident_knight)
            specialty: 専門分野
            port: ポート番号
        """
        super().__init__(
            name=name,
            domain=f"servant.{tribe}",
            port=port
        )
        
        self.tribe = tribe
        self.specialty = specialty
        self.sage_connections = {}  # 賢者との接続状態
        
        # 追加メトリクス
        self.task_execution_time = Histogram(
            'servant_task_execution_seconds',
            'Task execution time',
            ['servant_name', 'task_type']
        )
        
        self.sage_collaboration_counter = Counter(
            'servant_sage_collaborations_total',
            'Collaborations with sages',
            ['servant_name', 'sage_name', 'status']
        )
        
        self.quality_score_gauge = Gauge(
            'servant_quality_score',
            'Current quality score',
            ['servant_name']
        )
        
        # 品質基準（Iron Will）
        self.quality_threshold = 85.0
        
        # サーバント固有ハンドラー登録
        self._register_servant_handlers()
        
        self.logger.info(
            "ElderServant initialized",
            tribe=tribe,
            specialty=specialty
        )
    
    async def start(self):
        """起動時処理"""
        await super().start()
        # 4賢者への接続テスト
        await self.connect_to_sages()
    
    def _register_servant_handlers(self):
        """サーバント共通ハンドラー登録"""
        
        @self.on_message("execute_task")
        async def handle_execute_task(message: Message) -> Dict[str, Any]:
            """
            タスク実行リクエスト
            
            Input:
                - task_type: タスク種別
                - parameters: タスクパラメータ
                - quality_requirements: 品質要件
            """
            with self.task_execution_time.labels(
                servant_name=self.name,
                task_type=message.data.get("task_type", "unknown")
            ).time():
                
                task_type = message.data.get("task_type")
                parameters = message.data.get("parameters", {})
                quality_requirements = message.data.get("quality_requirements", {})
                
                try:
                    # タスク実行前の4賢者協議
                    consultation_result = await self.consult_sages_before_task(
                        task_type, parameters
                    )
                    
                    # タスク実行（サブクラスで実装）
                    execution_result = await self.execute_specialized_task(
                        task_type, parameters, consultation_result
                    )
                    
                    # 品質チェック
                    quality_result = await self.check_quality(
                        execution_result, quality_requirements
                    )
                    
                    # 品質基準を満たさない場合は再実行
                    if quality_result["score"] < self.quality_threshold:
                        self.logger.warning(
                            "Quality threshold not met, retrying",
                            score=quality_result["score"],
                            threshold=self.quality_threshold
                        )
                        
                        # Incident Sageに品質問題を報告
                        await self.collaborate_with_sage(
                            "incident_sage",
                            {
                                "action": "quality_issue",
                                "servant": self.name,
                                "task_type": task_type,
                                "quality_score": quality_result["score"]
                            }
                        )
                        
                        # 再実行（改善策を適用）
                        execution_result = await self.execute_specialized_task(
                            task_type, 
                            parameters, 
                            {**consultation_result, "retry": True}
                        )
                        quality_result = await self.check_quality(
                            execution_result, quality_requirements
                        )
                    
                    # 賢者への完了報告
                    await self.report_completion_to_sages(
                        task_type, execution_result, quality_result
                    )
                    
                    # メトリクス更新
                    self.quality_score_gauge.labels(
                        servant_name=self.name
                    ).set(quality_result["score"])
                    
                    return {
                        "status": "success",
                        "servant": self.name,
                        "tribe": self.tribe,
                        "task_type": task_type,
                        "result": execution_result,
                        "quality": quality_result,
                        "consultation": consultation_result
                    }
                    
                except Exception as e:
                    self.logger.error(
                        "Task execution failed",
                        task_type=task_type,
                        error=str(e)
                    )
                    
                    # エラーをIncident Sageに報告
                    await self.collaborate_with_sage(
                        "incident_sage",
                        {
                            "action": "task_failure",
                            "servant": self.name,
                            "task_type": task_type,
                            "error": str(e)
                        }
                    )
                    
                    return {
                        "status": "error",
                        "servant": self.name,
                        "message": f"Task execution failed: {str(e)}"
                    }
    
    async def connect_to_sages(self) -> Dict[str, bool]:
        """
        4賢者への接続テスト（実装）
        
        Returns:
            各賢者への接続状態
        """
        sages = ["knowledge_sage", "task_sage", "incident_sage", "rag_sage"]
        connection_tasks = []
        
        for sage in sages:
            connection_tasks.append(self._test_sage_connection(sage))
        
        # 並列で接続テスト
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        for sage, result in zip(sages, results):
            if isinstance(result, Exception):
                self.sage_connections[sage] = False
                self.logger.warning(
                    f"Failed to connect to {sage}",
                    error=str(result)
                )
            else:
                self.sage_connections[sage] = result
                self.logger.info(f"Connected to {sage}: {result}")
        
        return self.sage_connections
    
    async def _test_sage_connection(self, sage_name: str) -> bool:
        """
        個別賢者への接続テスト
        """
        try:
            response = await self.send_message(
                target=sage_name,
                message_type="health_check",
                data={"requester": self.name},
                timeout=5.0
            )
            
            return response.data.get("status") == "healthy"
            
        except Exception as e:
            self.logger.error(
                f"Connection test failed for {sage_name}",
                error=str(e)
            )
            return False
    
    async def consult_sages_before_task(
        self, 
        task_type: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        タスク実行前の4賢者協議
        """
        consultation_results = {}
        
        # タスクタイプに応じて関連賢者を選択
        relevant_sages = self._get_relevant_sages(task_type)
        
        consultation_tasks = []
        for sage in relevant_sages:
            if self.sage_connections.get(sage, False):
                consultation_tasks.append(
                    self._consult_sage(sage, task_type, parameters)
                )
        
        if consultation_tasks:
            results = await asyncio.gather(*consultation_tasks, return_exceptions=True)
            
            for sage, result in zip(relevant_sages, results):
                if not isinstance(result, Exception):
                    consultation_results[sage] = result
                    self.sage_collaboration_counter.labels(
                        servant_name=self.name,
                        sage_name=sage,
                        status="success"
                    ).inc()
                else:
                    self.sage_collaboration_counter.labels(
                        servant_name=self.name,
                        sage_name=sage,
                        status="error"
                    ).inc()
        
        return consultation_results
    
    async def _consult_sage(
        self, 
        sage_name: str, 
        task_type: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        個別賢者への相談
        """
        consultation_request = {
            "action": "consultation",
            "servant": self.name,
            "task_type": task_type,
            "parameters": parameters,
            "tribe": self.tribe,
            "specialty": self.specialty
        }
        
        response = await self.send_message(
            target=sage_name,
            message_type="servant_consultation",
            data=consultation_request
        )
        
        return response.data
    
    def _get_relevant_sages(self, task_type: str) -> List[str]:
        """
        タスクタイプに応じた関連賢者の選択
        """
        # デフォルトでは全賢者が関連
        relevant_sages = ["knowledge_sage", "task_sage", "incident_sage", "rag_sage"]
        
        # タスクタイプや部族による特別なルール
        if self.tribe == "dwarf" and "code" in task_type.lower():
            # ドワーフのコード関連タスク
            relevant_sages = ["knowledge_sage", "task_sage", "rag_sage"]
        elif self.tribe == "incident_knight":
            # インシデントナイトは常にIncident Sageを優先
            relevant_sages = ["incident_sage", "task_sage", "knowledge_sage"]
        elif self.tribe == "rag_wizard":
            # RAGウィザードはRAG Sageを優先
            relevant_sages = ["rag_sage", "knowledge_sage", "task_sage"]
        elif self.tribe == "elf":
            # エルフはバランスよく全賢者
            pass  # デフォルトのまま
        
        return relevant_sages
    
    async def execute_specialized_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        consultation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        専門タスクの実行（サブクラスでオーバーライド）
        """
        # 基本実装（サブクラスで具体的な実装を行う）
        self.logger.info(
            "Executing specialized task",
            task_type=task_type,
            servant=self.name
        )
        
        return {
            "message": "Task executed by base servant",
            "task_type": task_type,
            "parameters": parameters,
            "consultation_applied": bool(consultation_result)
        }
    
    async def check_quality(
        self,
        execution_result: Dict[str, Any],
        quality_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        品質チェック（Iron Will基準）
        """
        quality_score = 100.0  # 基本スコア
        issues = []
        
        # 基本的な品質チェック
        if not execution_result:
            quality_score -= 50
            issues.append("No execution result")
        
        # 要件ごとのチェック
        for requirement, expected in quality_requirements.items():
            if requirement == "no_todos":
                # TODO/FIXMEのチェック
                result_str = json.dumps(execution_result)
                if "TODO" in result_str or "FIXME" in result_str:
                    quality_score -= 20
                    issues.append("Contains TODO/FIXME comments")
            
            elif requirement == "test_coverage":
                # テストカバレッジ要件
                coverage = execution_result.get("test_coverage", 0)
                if coverage < expected:
                    quality_score -= (expected - coverage) * 0.5
                    issues.append(f"Test coverage {coverage}% below requirement {expected}%")
        
        return {
            "score": max(quality_score, 0),
            "issues": issues,
            "passed": quality_score >= self.quality_threshold
        }
    
    async def report_completion_to_sages(
        self,
        task_type: str,
        execution_result: Dict[str, Any],
        quality_result: Dict[str, Any]
    ):
        """
        賢者への完了報告
        """
        report = {
            "servant": self.name,
            "tribe": self.tribe,
            "task_type": task_type,
            "completion_time": datetime.now().isoformat(),
            "quality_score": quality_result["score"],
            "quality_passed": quality_result["passed"],
            "result_summary": self._summarize_result(execution_result)
        }
        
        # Task Sageに完了報告
        if self.sage_connections.get("task_sage", False):
            try:
                await self.send_message(
                    target="task_sage",
                    message_type="task_completed",
                    data=report
                )
            except Exception as e:
                self.logger.warning(
                    "Failed to report completion to Task Sage",
                    error=str(e)
                )
        
        # 品質問題がある場合はIncident Sageにも報告
        if not quality_result["passed"] and self.sage_connections.get("incident_sage", False):
            try:
                await self.send_message(
                    target="incident_sage",
                    message_type="quality_alert",
                    data={
                        **report,
                        "quality_issues": quality_result["issues"]
                    }
                )
            except Exception as e:
                self.logger.warning(
                    "Failed to report quality issue to Incident Sage",
                    error=str(e)
                )
    
    def _summarize_result(self, execution_result: Dict[str, Any]) -> str:
        """
        実行結果の要約
        """
        # シンプルな要約実装
        if isinstance(execution_result, dict):
            keys = list(execution_result.keys())[:5]  # 最初の5キー
            return f"Result with keys: {', '.join(keys)}"
        else:
            return str(execution_result)[:100]  # 最初の100文字


# 単体テスト用
async def main():
    servant = ElderServantBase(
        name="test_servant",
        tribe="test",
        specialty="testing",
        port=60001
    )
    
    await servant.start()
    print(f"Test Servant running on port {servant.port}")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await servant.stop()


if __name__ == "__main__":
    asyncio.run(main())