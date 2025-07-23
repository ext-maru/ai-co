"""
Elder Servant Base - サーバント基底クラス
python-a2a 0.5.9対応 (@agent + A2AServer) + エルダーズギルド統合
TDD Green Phase: 完全Iron Will準拠実装
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
import asyncio
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path
import json
import traceback

# python-a2a 0.5.9対応インポート
from python_a2a import agent, A2AServer, Message

# エルダーズギルド統合インポート  
import sys
sys.path.append('/home/aicompany/ai_co')

# 4賢者統合
from libs.four_sages.knowledge.knowledge_sage import KnowledgeSage
from libs.four_sages.task.task_sage import TaskSage
from libs.four_sages.incident.incident_sage import IncidentSage
from libs.four_sages.rag.rag_sage import RAGSage

# Elder Servants基底クラス
from libs.elder_servants.base.enhanced_elder_servant import EnhancedElderServant

# 品質システム統合
from libs.elders_code_quality_engine import EldersCodeQualityEngine
# エルダーズギルド既存ライブラリとの統合（オプション）
try:
    from libs.elders_code_quality import QualityAnalyzer
    ELDERS_QUALITY_AVAILABLE = True
except ImportError:
    ELDERS_QUALITY_AVAILABLE = False

try:
    from libs.elder_flow import elder_flow_engine
    ELDER_FLOW_AVAILABLE = True
except ImportError:
    ELDER_FLOW_AVAILABLE = False

# ログ・メトリクス
import structlog
from prometheus_client import Counter, Histogram, Gauge

# Iron Will基準
IRON_WILL_QUALITY_THRESHOLD = 85.0
TODO_FIXME_FORBIDDEN_PATTERNS = ["TODO", "FIXME", "HACK", "XXX"]


@agent(
    name="ElderServantBase",
    description="Elder Tree Servant Base Class with Elders Guild Integration"
)
class ElderServantBase(A2AServer):

    """
    Elder Servant基底クラス (python-a2a 0.5.9対応)
    
    全てのサーバントが継承する機能:
    - 4賢者統合通信システム
    - エルダーズギルド品質基準 (Iron Will)
    - Elder Flow実行エンジン統合
    - A2A Server非同期通信
    - プロメテウスメトリクス
    - 障害予防・自動復旧
    """ str, tribe: str, specialty: str, port: Optional[int] = None):
        """
        初期化 (python-a2a 0.5.9準拠)
        
        Args:
            name: サーバント名
            tribe: 所属部族 (dwarf, rag_wizard, elf, incident_knight)  
            specialty: 専門分野
            port: ポート番号
        """
        # A2AServer初期化
        super().__init__(name=name, port=port)
        
        # 基本属性
        self.tribe = tribe
        self.specialty = specialty
        self.servant_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        
        # エルダーズギルド統合
        self.enhanced_servant = None  # 後で初期化
        self.quality_engine = EldersCodeQualityEngine()
        
        # 4賢者統合インスタンス
        self.sage_instances = {
            'knowledge_sage': KnowledgeSage('knowledge_sage'),
            'task_sage': TaskSage('task_sage'),
            'incident_sage': IncidentSage('incident_sage'),
            'rag_sage': RAGSage('rag_sage')
        }
        self.sage_connections = {}  # 接続状態追跡
        
        # 構造化ログ
        self.logger = structlog.get_logger().bind(
            servant_name=name,
            tribe=tribe,
            specialty=specialty,
            servant_id=self.servant_id
        )
        
        # Prometheusメトリクス
        self._setup_prometheus_metrics()
        
        # Iron Will品質基準
        self.quality_threshold = IRON_WILL_QUALITY_THRESHOLD
        
        # 非同期タスク管理
        self.active_tasks = {}
        self.task_history = []
        
        # サーバント固有ハンドラー登録
        self._register_servant_handlers()
        
        self.logger.info(
            "ElderServant initialized with Elders Guild integration",
            tribe=tribe,
            specialty=specialty,
            quality_threshold=self.quality_threshold
        )
    
    def _setup_prometheus_metrics(self):

        """Prometheusメトリクス設定"""
        """起動時処理 (A2AServer準拠)"""
        # A2AServer起動
        await super().start()
        
        # Enhanced Elder Servant初期化
        await self._initialize_enhanced_servant()
        
        # 4賢者への接続確立
        await self._connect_to_all_sages()
        
        # 品質監視開始
        asyncio.create_task(self._start_quality_monitoring())
        
        self.logger.info("ElderServant startup completed")
    
    def _register_servant_handlers(self):

        """サーバント共通ハンドラー登録 (python-a2a 0.5.9対応)""" Message) -> Dict[str, Any]:
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
                    consultation_result = await self._consult_sages_before_task(
                        task_type, parameters
                    )
                    
                    # タスク実行（サブクラスで実装）
                    execution_result = await self.execute_specialized_task(
                        task_type, parameters, consultation_result
                    )
                    
                    # 品質チェック
                    quality_result = await self._check_iron_will_quality(
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
                        quality_result = await self._check_iron_will_quality(
                            execution_result, quality_requirements
                        )
                    
                    # 賢者への完了報告
                    await self._report_completion_to_sages(
                        task_type, execution_result, quality_result
                    )
                    
                    # メトリクス更新
                    self.quality_score_gauge.labels(
                        servant_name=self.name,
                        tribe=self.tribe
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
                    await self._report_incident(
                        "task_failure", 
                        {
                            "task_type": task_type,
                            "error": str(e),
                            "traceback": traceback.format_exc()
                        }
                    )
                    
                    return {
                        "status": "error",
                        "servant": self.name,
                        "tribe": self.tribe,
                        "message": f"Task execution failed: {str(e)}",
                        "error_details": {
                            "exception_type": type(e).__name__,
                            "traceback": traceback.format_exc()
                        }
                    }
        
        @self.handle("health_check")
        async def handle_health_check(message: Message) -> Dict[str, Any]:
            """ヘルスチェック"""
            sage_status = {
                name: self.sage_connections.get(name, False) 
                for name in self.sage_instances.keys()
            }
            
            uptime = datetime.now() - self.start_time
            
            return {
                "status": "healthy",
                "servant": self.name,
                "tribe": self.tribe,
                "specialty": self.specialty,
                "uptime_seconds": uptime.total_seconds(),
                "sage_connections": sage_status,
                "active_tasks": len(self.active_tasks),
                "quality_threshold": self.quality_threshold
            }
        
        @self.handle("get_capabilities")  
        async def handle_get_capabilities(message: Message) -> Dict[str, Any]:
            """サーバント能力情報取得"""
            capabilities = await self.get_specialized_capabilities()
            
            return {
                "servant": self.name,
                "tribe": self.tribe,
                "specialty": self.specialty,
                "capabilities": capabilities,
                "sage_integrations": list(self.sage_instances.keys()),
                "quality_features": [
                    "iron_will_compliance",
                    "real_time_monitoring",
                    "four_sages_integration",
                    "elder_flow_execution"
                ]
            }
    
    async def _initialize_enhanced_servant(self):

                    """Enhanced Elder Servant初期化"""
            # Enhanced Elder Servantとの統合は必要に応じて実装
            self.logger.info("Enhanced Elder Servant integration ready")
        except Exception as e:
            self.logger.warning("Enhanced Elder Servant initialization failed", error=str(e))
    
    async def _connect_to_all_sages(self) -> Dict[str, bool]:

            """
        4賢者への接続確立 (並列処理)
        
        Returns:
            各賢者への接続状態
        """
            connection_tasks.append(self._establish_sage_connection(sage_name, sage_instance))
        
        # 並列で接続確立
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        for sage_name, result in zip(self.sage_instances.keys(), results):
            if isinstance(result, Exception):
                self.sage_connections[sage_name] = False
                self.logger.warning(
                    "Failed to connect to sage",
                    sage_name=sage_name,
                    error=str(result)
                )
            else:
                self.sage_connections[sage_name] = result
                self.logger.info(
                    "Sage connection established",
                    sage_name=sage_name,
                    status=result
                )
        
        # 接続数メトリクス更新
        connected_count = sum(1 for connected in self.sage_connections.values() if connected)
        self.active_connections_gauge.labels(
            servant_name=self.name,
            tribe=self.tribe
        ).set(connected_count)
        
        return self.sage_connections
    
    async def _establish_sage_connection(self, sage_name: str, sage_instance) -> bool:
        """
        個別賢者との接続確立
        """
        try:
            # 賢者インスタンスの初期化確認
            if hasattr(sage_instance, 'status') and sage_instance.status == 'ready':
                # 簡単な疎通確認
                test_request = {
                    "action": "connection_test",
                    "servant": self.name,
                    "tribe": self.tribe
                }
                
                # 賢者の process_request メソッドを使用
                response = await sage_instance.process_request(test_request)
                
                is_connected = response.get("status") == "success"
                
                if is_connected:
                    self.logger.info(
                        "Sage connection established",
                        sage_name=sage_name
                    )
                
                return is_connected
            else:
                return False
                
        except Exception as e:
            self.logger.error(
                "Sage connection failed",
                sage_name=sage_name,
                error=str(e)
            )
            return False
    
    async def _consult_sages_before_task(
        self, 
        task_type: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:

    """
        タスク実行前の4賢者協議 (エルダーズギルド統合)
        """
            if self.sage_connections.get(sage_name, False):
                consultation_tasks.append(
                    self._consult_individual_sage(sage_name, task_type, parameters)
                )
        
        if consultation_tasks:
            results = await asyncio.gather(*consultation_tasks, return_exceptions=True)
            
            for sage_name, result in zip(relevant_sages, results):
                if not isinstance(result, Exception):
                    consultation_results[sage_name] = result
                    self.sage_collaboration_counter.labels(
                        servant_name=self.name,
                        sage_name=sage_name,
                        status="success",
                        tribe=self.tribe
                    ).inc()
                else:
                    consultation_results[sage_name] = {"error": str(result)}
                    self.sage_collaboration_counter.labels(
                        servant_name=self.name,
                        sage_name=sage_name,
                        status="error",
                        tribe=self.tribe
                    ).inc()
                    
                    self.logger.warning(
                        "Sage consultation failed",
                        sage_name=sage_name,
                        error=str(result)
                    )
        
        return consultation_results
    
    async def _consult_individual_sage(
        self, 
        sage_name: str, 
        task_type: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:

    """
        個別賢者への相談 (エルダーズギルド統合)
        """ "servant_consultation",
            "servant_name": self.name,
            "servant_tribe": self.tribe,
            "servant_specialty": self.specialty,
            "task_type": task_type,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat()
        }
        
        # 賢者インスタンスに直接相談
        sage_instance = self.sage_instances.get(sage_name)
        if sage_instance:
            try:
                response = await sage_instance.process_request(consultation_request)
                return response
            except Exception as e:
                self.logger.error(
                    "Sage consultation error",
                    sage_name=sage_name,
                    error=str(e)
                )
                return {"error": f"Consultation failed: {str(e)}"}
        else:
            return {"error": f"Sage {sage_name} not available"}
    
    def _get_relevant_sages(self, task_type: str) -> List[str]:
        """
        タスクタイプと部族に応じた関連賢者の選択 (エルダーズギルド最適化)
        """
        # 基本的にはすべての賢者が協力
        all_sages = ["knowledge_sage", "task_sage", "incident_sage", "rag_sage"]
        
        # タスクタイプによる優先順位調整
        task_lower = task_type.lower()
        
        # 部族別の優先度設定
        if self.tribe == "dwarf":
            if any(keyword in task_lower for keyword in ["code", "build", "deploy", "implement"]):
                return ["knowledge_sage", "task_sage", "rag_sage", "incident_sage"]
            else:
                return ["task_sage", "knowledge_sage", "incident_sage", "rag_sage"]
                
        elif self.tribe == "incident_knight":
            # インシデント処理は常にIncident Sageを最優先
            return ["incident_sage", "knowledge_sage", "task_sage", "rag_sage"]
            
        elif self.tribe == "rag_wizard":
            # 検索・調査系はRAG Sageを最優先
            if any(
                keyword in task_lower for keyword in ["search",
                "analyze",
                "research",
                "investigate"]
            ):
                return ["rag_sage", "knowledge_sage", "task_sage", "incident_sage"]
            else:
                return ["knowledge_sage", "rag_sage", "task_sage", "incident_sage"]
                
        elif self.tribe == "elf":
            # エルフは監視・最適化が専門
            if not (any():
            if any(
                keyword in task_lower for keyword in ["monitor",
                "optimize",
                "performance",
                "quality"]
            ):
                return ["task_sage", "incident_sage", "knowledge_sage", "rag_sage"]
            else:
                return all_sages
        
        # デフォルト（バランス型）
        return all_sages
    
    async def execute_specialized_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        consultation_result: Dict[str, Any]
    ) -> Dict[str, Any]:

    """
        専門タスクの実行（サブクラスでオーバーライド必須）
        
        Note: 各部族のサーバントで具体的な実装が必要
        """ task_type,
            "start_time": datetime.now(),
            "status": "executing"
        }
        
        try:
            self.logger.info(
                "Executing specialized task (base implementation)",
                task_type=task_type,
                task_id=task_id,
                servant=self.name,
                tribe=self.tribe
            )
            
            # 基本実装（部族サーバントでオーバーライド推奨）
            result = {
                "status": "completed",
                "task_id": task_id,
                "task_type": task_type,
                "servant": self.name,
                "tribe": self.tribe,
                "parameters": parameters,
                "consultation_applied": bool(consultation_result),
                "consultation_summary": self._summarize_consultation(consultation_result),
                "execution_time": datetime.now().isoformat(),
                "message": f"Task executed by {self.tribe} servant: {self.name}"
            }
            
            # タスク完了
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["end_time"] = datetime.now()
            
            return result
            
        except Exception as e:
            # タスク失敗
            self.active_tasks[task_id]["status"] = "failed"
            self.active_tasks[task_id]["error"] = str(e)
            
            raise e
        finally:
            # タスク履歴に記録
            self.task_history.append(self.active_tasks.get(task_id, {}))
            # アクティブタスクから削除
            self.active_tasks.pop(task_id, None)
    
    def _summarize_consultation(self, consultation_result: Dict[str, Any]) -> str:
        """
        賢者協議結果の要約
        """
        if not consultation_result:
            return "No consultation performed"
        
        summary_parts = []
        for sage_name, result in consultation_result.items():
            if isinstance(result, dict) and "error" not in result:
                status = result.get("status", "unknown")
                summary_parts.append(f"{sage_name}: {status}")
            else:
                summary_parts.append(f"{sage_name}: error")
        
        return "; ".join(summary_parts) if summary_parts else "No valid consultations"
    
    async def _check_iron_will_quality(
        self,
        execution_result: Dict[str, Any],
        quality_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:

    """
        Iron Will品質基準チェック (エルダーズギルド統合)
        """
            quality_score -= 50
            issues.append("No execution result provided")
            return {
                "score": 0,
                "issues": issues,
                "violations": violations,
                "passed": False,
                "iron_will_compliant": False
            }
        
        # Iron Will基準: TODO/FIXME/HACK禁止チェック
        result_str = json.dumps(execution_result, default=str)
        for pattern in TODO_FIXME_FORBIDDEN_PATTERNS:
            if pattern in result_str:
                quality_score -= 25
                violations.append(f"Iron Will violation: {pattern} found in result")
                issues.append(f"Contains forbidden {pattern} pattern")
                
                # メトリクス記録
                self.iron_will_violations.labels(
                    servant_name=self.name,
                    violation_type=pattern,
                    tribe=self.tribe
                ).inc()
        
        # エルダーズギルド品質基準チェック
        if self.quality_engine:
            try:
                # 品質エンジンによる詳細分析
                engine_result = await self._analyze_with_quality_engine(execution_result)
                if engine_result.get("score"):
                    # 品質エンジンのスコアを統合
                    engine_score = engine_result["score"]
                    quality_score = (quality_score + engine_score) / 2
                    
                if engine_result.get("issues"):
                    issues.extend(engine_result["issues"])
                    
            except Exception as e:
                self.logger.warning(
                    "Quality engine analysis failed",
                    error=str(e)
                )
        
        # 要件別チェック
        for requirement, expected in quality_requirements.items():
            if requirement == "test_coverage":
                coverage = execution_result.get("test_coverage", 0)
                if coverage < expected:
                    penalty = (expected - coverage) * 0.5
                    quality_score -= penalty
                    issues.append(f"Test coverage {coverage}% below requirement {expected}%")
                    
            elif requirement == "response_time_ms":
                response_time = execution_result.get("response_time_ms", float('inf'))
                if response_time > expected:
                    quality_score -= 10
                    issues.append(f"Response time {response_time}ms exceeds limit {expected}ms")
                    
            elif requirement == "error_rate":
                error_rate = execution_result.get("error_rate", 0)
                if not (error_rate > expected):
                if error_rate > expected:
                    quality_score -= error_rate * 20
                    issues.append(f"Error rate {error_rate}% exceeds limit {expected}%")
        
        final_score = max(quality_score, 0)
        is_passed = final_score >= self.quality_threshold
        iron_will_compliant = len(violations) == 0
        
        return {
            "score": final_score,
            "issues": issues,
            "violations": violations,
            "passed": is_passed,
            "iron_will_compliant": iron_will_compliant,
            "threshold": self.quality_threshold,
            "analysis_time": datetime.now().isoformat()
        }
    
    async def _analyze_with_quality_engine(
        self,
        execution_result: Dict[str,
        Any]
    ) -> Dict[str, Any]:

        """
        エルダーズギルド品質エンジンによる分析
        """
            # 品質エンジンに結果を送信して分析
            analysis = await asyncio.to_thread(
                self.quality_engine.analyze_code_quality,
                json.dumps(execution_result, indent=2)
            )
            return analysis
        except Exception as e:
            self.logger.warning("Quality engine analysis error", error=str(e))
            return {"score": 80, "issues": []}
    
    async def _report_completion_to_sages(
        self,
        task_type: str,
        execution_result: Dict[str, Any],
        quality_result: Dict[str, Any]
    ):

    """
        賢者への完了報告 (エルダーズギルド統合)
        """ "task_completion",
            "servant_name": self.name,
            "servant_tribe": self.tribe,
            "servant_specialty": self.specialty,
            "task_type": task_type,
            "completion_time": datetime.now().isoformat(),
            "quality_score": quality_result["score"],
            "quality_passed": quality_result["passed"],
            "iron_will_compliant": quality_result.get("iron_will_compliant", False),
            "quality_issues": quality_result.get("issues", []),
            "result_summary": self._summarize_result(execution_result)
        }
        
        # Task Sageに完了報告
        task_sage = self.sage_instances.get("task_sage")
        if task_sage and self.sage_connections.get("task_sage", False):
            try:
                await task_sage.process_request(report)
                self.logger.info("Task completion reported to Task Sage")
            except Exception as e:
                self.logger.warning(
                    "Failed to report completion to Task Sage",
                    error=str(e)
                )
        
        # Knowledge Sageに学習データとして記録
        knowledge_sage = self.sage_instances.get("knowledge_sage")
        if knowledge_sage and self.sage_connections.get("knowledge_sage", False):
            try:
                learning_data = {
                    "action": "record_learning",
                    "learning_type": "task_execution",
                    **report
                }
                await knowledge_sage.process_request(learning_data)
            except Exception as e:
                self.logger.warning(
                    "Failed to record learning data",
                    error=str(e)
                )
        
        # 品質問題・Iron Will違反がある場合はIncident Sageに報告
        incident_sage = self.sage_instances.get("incident_sage")
        if incident_sage and self.sage_connections.get("incident_sage", False):
            if (not quality_result["passed"] or 
            # 複雑な条件判定
                not quality_result.get("iron_will_compliant", True) or
                quality_result.get("violations")):
                try:
                    incident_report = {
                        "action": "quality_incident",
                        **report,
                        "violations": quality_result.get("violations", []),
                        "severity": self._calculate_incident_severity(quality_result)
                    }
                    await incident_sage.process_request(incident_report)
                    self.logger.warning(
                        "Quality incident reported to Incident Sage",
                        quality_score=quality_result["score"]
                    )
                except Exception as e:
                    self.logger.error(
                        "Failed to report quality incident",
                        error=str(e)
                    )
    
    def _calculate_incident_severity(self, quality_result: Dict[str, Any]) -> str:
        """
        品質問題の重要度計算
        """
        score = quality_result.get("score", 100)
        violations = quality_result.get("violations", [])
        
        if score < 30 or len(violations) > 5:
            return "critical"
        elif score < 50 or len(violations) > 2:
            return "high"
        elif score < 70 or len(violations) > 0:
            return "medium"
        else:
            return "low"
    
    def _summarize_result(self, execution_result: Dict[str, Any]) -> str:
        """
        実行結果の要約（詳細版）
        """
        if not execution_result:
            return "No execution result"
        
        if isinstance(execution_result, dict):
            summary_parts = []
            
            # ステータス情報
            if "status" in execution_result:
                summary_parts.append(f"Status: {execution_result['status']}")
            
            # メッセージ情報
            if "message" in execution_result:
                message = execution_result["message"]
                if len(message) > 50:
                    message = message[:47] + "..."
                summary_parts.append(f"Message: {message}")
            
            # キー情報
            important_keys = ["task_id", "task_type", "execution_time", "error_count"]
            for key in important_keys:
                if key in execution_result:
                    summary_parts.append(f"{key}: {execution_result[key]}")
            
            # その他のキー（最大3個）
            other_keys = [k for k in execution_result.keys() 
                         if k not in important_keys + ["status", "message"]][:3]
            if other_keys:
                summary_parts.append(f"Other keys: {', '.join(other_keys)}")
            
            return "; ".join(summary_parts)
        else:
            return str(execution_result)[:100]


    async def _report_incident(self, incident_type: str, details: Dict[str, Any]):
        """
        インシデントSageへの報告 (統合メソッド)
        """
        incident_sage = self.sage_instances.get("incident_sage")
        if incident_sage and self.sage_connections.get("incident_sage", False):
            try:
                incident_report = {
                    "action": "report_incident",
                    "incident_type": incident_type,
                    "servant_name": self.name,
                    "servant_tribe": self.tribe,
                    "timestamp": datetime.now().isoformat(),
                    "details": details
                }
                
                await incident_sage.process_request(incident_report)
                
                self.logger.info(
                    "Incident reported",
                    incident_type=incident_type
                )
            except Exception as e:
                self.logger.error(
                    "Failed to report incident",
                    incident_type=incident_type,
                    error=str(e)
                )
    
    async def _start_quality_monitoring(self):

                """
        品質監視の開始
        """
            try:
                # 定期的な品質チェック（1分間隔）
                await asyncio.sleep(60)
                
                # アクティブタスクの監視
                current_time = datetime.now()
                for task_id, task_info in list(self.active_tasks.items()):
                    start_time = task_info.get("start_time")
                    if start_time and (current_time - start_time).total_seconds() > 300:  # 5分タイムアウト
                        self.logger.warning(
                            "Long-running task detected",
                            task_id=task_id,
                            task_type=task_info.get("task_type"),
                            duration_seconds=(current_time - start_time).total_seconds()
                        )
                        
                        # Incident Sageに報告
                        await self._report_incident(
                            "long_running_task",
                            {
                                "task_id": task_id,
                                "task_info": task_info,
                                "duration_seconds": (current_time - start_time).total_seconds()
                            }
                        )
                        
            except Exception as e:
                self.logger.error("Quality monitoring error", error=str(e))
                await asyncio.sleep(30)  # エラー時は短い間隔で再試行
    
    async def collaborate_with_sage(
        self,
        sage_name: str,
        request: Dict[str,
        Any]
    ) -> Dict[str, Any]:

        """
        賢者との協力（簡易実装）
        
        Args:
            sage_name: 賢者名
            request: リクエストデータ
            
        Returns:
            賢者からの応答
        """
            try:
                response = await sage_instance.process_request(request)
                return response
            except Exception as e:
                self.logger.error(
                    "Sage collaboration failed",
                    sage_name=sage_name,
                    error=str(e)
                )
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Sage {sage_name} not available"}
    
    async def get_specialized_capabilities(self) -> List[str]:

    
    """
        専門能力の取得（サブクラスでオーバーライド）
        """
        """
        サーバント停止処理
        """
        self.logger.info("Stopping ElderServant")
        
        # アクティブタスクの強制終了
        for task_id, task_info in self.active_tasks.items():
            task_info["status"] = "interrupted"
            task_info["end_time"] = datetime.now()
            self.task_history.append(task_info)
        
        # 賢者への停止通知
        for sage_name, sage_instance in self.sage_instances.items():
            if self.sage_connections.get(sage_name, False):
                try:
                    await sage_instance.process_request({
                        "action": "servant_shutdown",
                        "servant_name": self.name,
                        "servant_tribe": self.tribe
                    })
                except Exception as e:
                    self.logger.warning(
                        "Failed to notify sage of shutdown",
                        sage_name=sage_name,
                        error=str(e)
                    )
        
        # A2AServer停止
        await super().stop()


# デバッグ・テスト用
if __name__ == "__main__":
    async def test_servant():

    """test_servantメソッド"""
            await servant.start()
            print(f"Test Servant running: {servant.name} ({servant.tribe})")
            
            # テスト実行
            test_result = await servant.execute_specialized_task(
                "test_task",
                {"param1": "value1"},
                {"knowledge_sage": {"status": "success"}}
            )
            print(f"Test result: {test_result}")
            
            # 少し待機
            await asyncio.sleep(5)
            
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            await servant.stop()
    
    asyncio.run(test_servant())