#!/usr/bin/env python3
"""
🚨 Incident Sage A2A Agent - A2A通信エージェント
====================================

Elder Loop Phase 2: Knowledge Sageパターン適用
python-a2aを使用したIncident Sage A2A通信エージェント

Author: Claude Elder
Created: 2025-07-23
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from python_a2a import A2AServer, skill, Message, TextContent, MessageRole

# Incident Sage Business Logic
from .business_logic import IncidentProcessor


class IncidentSageAgent(A2AServer):


"""
    Incident Sage A2A通信エージェント
    
    Knowledge Sageパターン適用:
    - python-a2aを使用した分散通信
    - ビジネスロジックとA2A通信の分離
    - 16スキル実装（インシデント対応特化）
    - Elder Loop対応
    """ str = "localhost", port: int = 8810):
        """Incident Sage Agent初期化"""
        super().__init__(
            agent_name="incident_sage_agent",
            host=host,
            port=port
        )
        
        # ビジネスロジックプロセッサ
        self.incident_processor = None
        self.logger = logging.getLogger("incident_sage_a2a")
        
        # 初期化フラグ
        self.initialized = False
    
    async def initialize(self) -> bool:

        """エージェント初期化"""
            self.logger.info("Initializing Incident Sage A2A Agent...")
            
            # ビジネスロジックプロセッサ初期化
            self.incident_processor = IncidentProcessor()
            
            self.initialized = True
            self.logger.info("Incident Sage A2A Agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Incident Sage Agent: {e}")
            return False
    
    async def shutdown(self):

            """エージェントシャットダウン"""
            self.logger.info("Shutting down Incident Sage A2A Agent...")
            
            # リソースクリーンアップ
            if self.incident_processor:
                # 必要に応じてプロセッサのクリーンアップ
                pass
            
            self.initialized = False
            self.logger.info("Incident Sage A2A Agent shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    # === Core Incident Management Skills ===
    
    @skill(name="detect_incident")
    async def detect_incident_skill(self, message: Message) -> Message:
        """インシデント検知スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("detect_incident", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in detect_incident skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="register_incident")
    async def register_incident_skill(self, message: Message) -> Message:
        """インシデント登録スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("register_incident", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in register_incident skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="respond_to_incident")
    async def respond_to_incident_skill(self, message: Message) -> Message:
        """インシデント対応スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("respond_to_incident", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in respond_to_incident skill: {e}")
            return self._create_error_message(e)
    
    # === Quality Management Skills ===
    
    @skill(name="assess_quality")
    async def assess_quality_skill(self, message: Message) -> Message:
        """品質評価スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("assess_quality", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in assess_quality skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="register_quality_standard")
    async def register_quality_standard_skill(self, message: Message) -> Message:
        """品質基準登録スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("register_quality_standard", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in register_quality_standard skill: {e}")
            return self._create_error_message(e)
    
    # === Alert Management Skills ===
    
    @skill(name="create_alert_rule")
    async def create_alert_rule_skill(self, message: Message) -> Message:
        """アラートルール作成スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("create_alert_rule", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in create_alert_rule skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="evaluate_alert_rules")
    async def evaluate_alert_rules_skill(self, message: Message) -> Message:
        """アラートルール評価スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("evaluate_alert_rules", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in evaluate_alert_rules skill: {e}")
            return self._create_error_message(e)
    
    # === Monitoring Management Skills ===
    
    @skill(name="register_monitoring_target")
    async def register_monitoring_target_skill(self, message: Message) -> Message:
        """監視対象登録スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("register_monitoring_target", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in register_monitoring_target skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="check_target_health")
    async def check_target_health_skill(self, message: Message) -> Message:
        """監視対象ヘルスチェックスキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("check_target_health", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in check_target_health skill: {e}")
            return self._create_error_message(e)
    
    # === Analysis & Learning Skills ===
    
    @skill(name="learn_incident_patterns")
    async def learn_incident_patterns_skill(self, message: Message) -> Message:
        """インシデントパターン学習スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("learn_incident_patterns", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in learn_incident_patterns skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="analyze_correlations")
    async def analyze_correlations_skill(self, message: Message) -> Message:
        """インシデント相関分析スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("analyze_correlations", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in analyze_correlations skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="search_similar_incidents")
    async def search_similar_incidents_skill(self, message: Message) -> Message:
        """類似インシデント検索スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("search_similar_incidents", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in search_similar_incidents skill: {e}")
            return self._create_error_message(e)
    
    # === Remediation Skills ===
    
    @skill(name="attempt_automated_remediation")
    async def attempt_automated_remediation_skill(self, message: Message) -> Message:
        """自動修復試行スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("attempt_automated_remediation", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in attempt_automated_remediation skill: {e}")
            return self._create_error_message(e)
    
    # === Statistics & Monitoring Skills ===
    
    @skill(name="get_statistics")
    async def get_statistics_skill(self, message: Message) -> Message:
        """統計情報取得スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("get_statistics", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in get_statistics skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="get_operational_metrics")
    async def get_operational_metrics_skill(self, message: Message) -> Message:
        """運用メトリクス取得スキル"""
        try:
            if not self.initialized:
                return self._create_error_message("Agent not initialized")
            
            data = self._extract_data_from_message(message)
            result = await self.incident_processor.process_action("get_operational_metrics", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in get_operational_metrics skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="health_check")
    async def health_check_skill(self, message: Message) -> Message:
        """ヘルスチェックスキル"""
        try:
            # エージェント自体のヘルスチェック（初期化不要）
            health_data = {
                "status": "healthy" if self.initialized else "initializing",
                "agent_name": "Incident Sage Agent",
                "initialized": self.initialized,
                "timestamp": datetime.now().isoformat()
            }
            
            # プロセッサが初期化済みの場合は詳細情報も取得
            if self.initialized and self.incident_processor:
                data = self._extract_data_from_message(message)
                result = await self.incident_processor.process_action("health_check", data)
                
                if result.get("success"):
                    health_data.update(result.get("data", {}))
            
            return self._create_response_message({
                "success": True,
                "data": health_data
            })
            
        except Exception as e:
            self.logger.error(f"Error in health_check skill: {e}")
            return self._create_error_message(e)
    
    # === Utility Methods ===
    
    def _extract_data_from_message(self, message: Message) -> Dict[str, Any]:
        """メッセージからデータ抽出"""
        try:
            # メッセージの内容をJSONとして解析
            if hasattr(message, 'content') and hasattr(message.content, 'text'):
                content_text = message.content.text
                
                # JSON形式の場合はパース
                try:
                    data = json.loads(content_text)
                    if isinstance(data, dict):
                        return data
                except json.JSONDecodeError:
                    pass
                
                # プレーンテキストの場合はqueryとして扱う
                return {"query": content_text}
            
            # デフォルト
            return {}
            
        except Exception as e:
            self.logger.warning(f"Failed to extract data from message: {e}")
            return {}
    
    def _create_response_message(self, result: Dict[str, Any]) -> Message:
        """レスポンスメッセージ作成"""
        try:
            response_content = json.dumps(result, ensure_ascii=False, default=str)
            
            return Message(
                role=MessageRole.ASSISTANT,
                content=TextContent(text=response_content)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create response message: {e}")
            return self._create_error_message(e)
    
    def _create_error_message(self, error) -> Message:

            """エラーメッセージ作成"""
            error_response = {
                "success": False,
                "error": str(error),
                "timestamp": datetime.now().isoformat(),
                "agent": "incident_sage_agent"
            }
            
            error_content = json.dumps(error_response, ensure_ascii=False)
            
            return Message(
                role=MessageRole.ASSISTANT,
                content=TextContent(text=error_content)
            )
            
        except Exception as e:
            # フォールバック
            fallback_content = f'{{"success": false, "error": "Internal error: {str(e)}"}}'
            return Message(
                role=MessageRole.ASSISTANT,
                content=TextContent(text=fallback_content)
            )
    
    def get_skills_info(self) -> Dict[str, Any]:

            """スキル情報取得""" "detect_incident", "category": "incident_management", "description": "Detect and analyze anomalies to create incidents"},
            {"name": "register_incident", "category": "incident_management", "description": "Register new incidents in the system"},
            {"name": "respond_to_incident", "category": "incident_management", "description": "Execute automated incident response procedures"},
            
            # Quality Management
            {"name": "assess_quality", "category": "quality_management", "description": "Assess component quality against standards"},
            {"name": "register_quality_standard", "category": "quality_management", "description": "Register new quality standards"},
            
            # Alert Management
            {"name": "create_alert_rule", "category": "alert_management", "description": "Create new alert rules for monitoring"},
            {"name": "evaluate_alert_rules", "category": "alert_management", "description": "Evaluate alert rules against current metrics"},
            
            # Monitoring Management
            {"name": "register_monitoring_target", "category": "monitoring", "description": "Register new monitoring targets"},
            {"name": "check_target_health", "category": "monitoring", "description": "Perform health checks on monitoring targets"},
            
            # Analysis & Learning
            {"name": "learn_incident_patterns", "category": "analysis", "description": "Learn patterns from historical incidents"},
            {"name": "analyze_correlations", "category": "analysis", "description": "Analyze correlations between incidents"},
            {"name": "search_similar_incidents", "category": "analysis", "description": "Search for similar historical incidents"},
            
            # Remediation
            {"name": "attempt_automated_remediation", "category": "remediation", "description": "Attempt automated incident remediation"},
            
            # Statistics & Monitoring
            {"name": "get_statistics", "category": "statistics", "description": "Get comprehensive incident and quality statistics"},
            {"name": "get_operational_metrics", "category": "statistics", "description": "Get operational metrics and KPIs"},
            {"name": "health_check", "category": "system", "description": "Check agent and processor health status"}
        ]
        
        return {
            "agent_name": "Incident Sage Agent",
            "total_skills": len(skills),
            "skills": skills,
            "categories": {
                "incident_management": 3,
                "quality_management": 2,
                "alert_management": 2,
                "monitoring": 2,
                "analysis": 3,
                "remediation": 1,
                "statistics": 2,
                "system": 1
            },
            "description": "Incident response and quality monitoring specialist with automated remediation capabilities"
        }


# 後方互換性のためのエイリアス
IncidentSage = IncidentSageAgent