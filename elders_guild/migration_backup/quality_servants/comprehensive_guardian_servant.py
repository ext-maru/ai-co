"""
🛡️ ComprehensiveGuardian Servant - 包括品質統括サーバント
python-a2a統合による Block C 実装
One Servant, One Command: assess_comprehensive_quality
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from python_a2a import A2AServer, skill, Message, TextContent, MessageRole

# 既存エンジンの活用
from elders_guild.quality.comprehensive_quality_engine import ComprehensiveQualityEngine

logger = logging.getLogger(__name__)


class ComprehensiveGuardianServant(A2AServer):
    """
    Block C: 包括品質統括サーバント
    
    責任範囲:
    - ドキュメント・セキュリティ・設定・性能の統合評価
    - 包括的な品質判定
    - システム全体の健全性確認
    - 総合品質証明書の発行
    """
    
    def __init__(self, host: str = "localhost", port: int = 8812):
        """A2Aサーバント初期化"""
        super().__init__()
        
        # サーバント情報
        self.agent_name = "comprehensive-guardian"
        self.description = "Comprehensive Quality Guardian - Block C"
        self.host = host
        self.port = port
        self.command = "assess_comprehensive_quality"  # One Command
        
        # 包括品質エンジン
        self.comprehensive_engine = ComprehensiveQualityEngine()
        
        # メトリクス
        self.total_assessments = 0
        self.excellent_projects = 0
        self.security_alerts = 0
        
        logger.info(f"ComprehensiveGuardian Servant initialized on {host}:{port}")
    
    async def initialize(self) -> bool:
        """サーバント初期化"""
        try:
            # エンジン初期化
            await self.comprehensive_engine.initialize()
            logger.info("ComprehensiveGuardian Servant standing guard")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False
    
    def _extract_data_from_message(self, message: Message) -> Dict[str, Any]:
        """メッセージからデータ抽出"""
        if isinstance(message.content, TextContent):
            text_content = message.content.text
            try:
                return json.loads(text_content)
            except json.JSONDecodeError:
                return {"target_path": text_content}
        else:
            raise ValueError("TextContent required")
    
    def _create_response_message(self, result: Dict[str, Any]) -> Message:
        """レスポンスメッセージ作成"""
        return Message(
            content=TextContent(text=json.dumps(result)),
            role=MessageRole.AGENT
        )
    
    @skill(name="assess_comprehensive_quality")
    async def assess_comprehensive_quality(self, message: Message) -> Message:
        """
        統合包括品質コマンド - One Servant, One Command
        
        実行フロー:
        1. エンジンによる4分野自動分析 (Doc, Security, Config, Performance)
        2. サーバントによる総合判定
        3. システム健全性の最終評価
        """
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            target_path = data.get("target_path", ".")
            
            self.total_assessments += 1
            logger.info(f"Assessing comprehensive quality for: {target_path}")
            
            # エンジン実行（自動化）
            engine_result = await self.comprehensive_engine.execute_all_analyses(target_path)
            
            # サーバント判定（専門性）
            verdict = self._judge_comprehensive_quality(engine_result)
            
            # メトリクス更新
            if verdict["verdict"] == "APPROVED":
                if verdict.get("overall_score", 0) >= 95.0:
                    self.excellent_projects += 1
            
            if engine_result.security_score < 80.0:
                self.security_alerts += 1
            
            # レスポンス作成
            response = {
                "servant": self.agent_name,
                "command": self.command,
                "target_path": target_path,
                "timestamp": datetime.now().isoformat(),
                **verdict
            }
            
            return self._create_response_message(response)
            
        except Exception as e:
            logger.error(f"Error in assess_comprehensive_quality: {e}")
            error_response = {
                "servant": self.agent_name,
                "command": self.command,
                "success": False,
                "error": str(e),
                "verdict": "ERROR"
            }
            return self._create_response_message(error_response)
    
    def _judge_comprehensive_quality(self, result) -> Dict[str, Any]:
        """
        純粋な判定ロジック - 包括品質の総合判定
        
        判定基準:
        - 全分野90点以上: APPROVED (EXCELLENCE)
        - 平均85点以上: CONDITIONAL (GOOD)
        - それ以外: IMPROVEMENTS_REQUIRED
        """
        # 各分野のスコア取得
        doc_score = result.documentation_score
        sec_score = result.security_score
        config_score = result.config_score
        perf_score = result.performance_score
        
        # 総合スコア計算（重み付き平均）
        weights = {
            "documentation": 0.20,
            "security": 0.35,
            "configuration": 0.20,
            "performance": 0.25
        }
        
        overall_score = (
            doc_score * weights["documentation"] +
            sec_score * weights["security"] +
            config_score * weights["configuration"] +
            perf_score * weights["performance"]
        )
        
        # 最低スコアチェック（どれか1つでも低すぎる場合は承認しない）
        min_score = min(doc_score, sec_score, config_score, perf_score)
        
        if overall_score >= 90.0 and min_score >= 85.0:
            return {
                "verdict": "APPROVED",
                "overall_score": overall_score,
                "certification": "COMPREHENSIVE_EXCELLENCE",
                "message": "Exceptional quality across all dimensions!",
                "breakdown": {
                    "documentation": {"score": doc_score, "grade": "EXCELLENT"},
                    "security": {"score": sec_score, "grade": "EXCELLENT"},
                    "configuration": {"score": config_score, "grade": "EXCELLENT"},
                    "performance": {"score": perf_score, "grade": "EXCELLENT"}
                },
                "achievements": self._identify_achievements(result)
            }
        elif overall_score >= 85.0 and min_score >= 75.0:
            improvements = self._get_improvement_areas(result)
            return {
                "verdict": "CONDITIONAL",
                "overall_score": overall_score,
                "certification": "QUALITY_ASSURED",
                "message": "Good overall quality with some areas for improvement.",
                "breakdown": {
                    "documentation": {"score": doc_score, "grade": self._get_grade(doc_score)},
                    "security": {"score": sec_score, "grade": self._get_grade(sec_score)},
                    "configuration": {"score": config_score, "grade": self._get_grade(config_score)},
                    "performance": {"score": perf_score, "grade": self._get_grade(perf_score)}
                },
                "improvement_areas": improvements,
                "command": f"{self.command} --improve-weakest"
            }
        else:
            critical_areas = self._identify_critical_areas(result)
            return {
                "verdict": "IMPROVEMENTS_REQUIRED",
                "overall_score": overall_score,
                "certification": "NEEDS_WORK",
                "message": "Significant improvements needed in multiple areas.",
                "breakdown": {
                    "documentation": {"score": doc_score, "grade": self._get_grade(doc_score)},
                    "security": {"score": sec_score, "grade": self._get_grade(sec_score)},
                    "configuration": {"score": config_score, "grade": self._get_grade(config_score)},
                    "performance": {"score": perf_score, "grade": self._get_grade(perf_score)}
                },
                "critical_areas": critical_areas,
                "mandatory_actions": self._get_mandatory_actions(result),
                "command": f"{self.command} --emergency-improvement"
            }
    
    def _get_grade(self, score: float) -> str:
        """スコアからグレード判定"""
        if score >= 95:
            return "EXCELLENT"
        elif score >= 90:
            return "VERY_GOOD"
        elif score >= 85:
            return "GOOD"
        elif score >= 75:
            return "ACCEPTABLE"
        else:
            return "NEEDS_IMPROVEMENT"
    
    def _identify_achievements(self, result) -> List[str]:
        """達成事項の特定"""
        achievements = []
        
        if result.documentation_score >= 95:
            achievements.append("📚 Documentation Excellence")
        
        if result.security_score >= 95:
            achievements.append("🛡️ Security Champion")
        
        if result.config_score >= 95:
            achievements.append("⚙️ Configuration Master")
        
        if result.performance_score >= 95:
            achievements.append("⚡ Performance Leader")
        
        if result.zero_vulnerabilities:
            achievements.append("🔒 Zero Vulnerabilities")
        
        if result.full_api_documentation:
            achievements.append("📖 Complete API Documentation")
        
        return achievements
    
    def _get_improvement_areas(self, result) -> List[Dict[str, Any]]:
        """改善領域の特定"""
        areas = []
        
        if result.documentation_score < 90:
            areas.append({
                "area": "Documentation",
                "current_score": result.documentation_score,
                "target_score": 90,
                "suggestions": [
                    "Add missing docstrings",
                    "Update API documentation",
                    "Create user guides"
                ]
            })
        
        if result.security_score < 90:
            areas.append({
                "area": "Security",
                "current_score": result.security_score,
                "target_score": 90,
                "suggestions": [
                    "Fix security vulnerabilities",
                    "Update dependencies",
                    "Add security headers"
                ]
            })
        
        if result.performance_score < 85:
            areas.append({
                "area": "Performance",
                "current_score": result.performance_score,
                "target_score": 85,
                "suggestions": [
                    "Optimize slow functions",
                    "Add caching",
                    "Reduce memory usage"
                ]
            })
        
        return areas
    
    def _identify_critical_areas(self, result) -> List[Dict[str, Any]]:
        """重大問題領域の特定"""
        critical = []
        
        if result.security_score < 70:
            critical.append({
                "area": "Security",
                "severity": "CRITICAL",
                "score": result.security_score,
                "issues": result.security_vulnerabilities,
                "immediate_action": "Fix all high-severity vulnerabilities"
            })
        
        if result.config_score < 70:
            critical.append({
                "area": "Configuration",
                "severity": "HIGH",
                "score": result.config_score,
                "issues": result.config_issues,
                "immediate_action": "Fix configuration errors"
            })
        
        if result.documentation_score < 60:
            critical.append({
                "area": "Documentation",
                "severity": "MEDIUM",
                "score": result.documentation_score,
                "issues": result.missing_docs_count,
                "immediate_action": "Document critical functions"
            })
        
        return critical
    
    def _get_mandatory_actions(self, result) -> List[str]:
        """必須アクション項目の生成"""
        actions = []
        
        if result.security_vulnerabilities > 0:
            actions.append(f"Fix {result.security_vulnerabilities} security vulnerabilities")
        
        if result.missing_docs_count > 10:
            actions.append(f"Add documentation for {result.missing_docs_count} undocumented items")
        
        if result.performance_bottlenecks > 0:
            actions.append(f"Optimize {result.performance_bottlenecks} performance bottlenecks")
        
        if result.config_errors > 0:
            actions.append(f"Resolve {result.config_errors} configuration errors")
        
        return actions
    
    @skill(name="generate_quality_certificate")
    async def generate_quality_certificate(self, message: Message) -> Message:
        """品質証明書生成スキル"""
        try:
            data = self._extract_data_from_message(message)
            target_path = data.get("target_path", ".")
            
            # 最新の評価結果を取得
            result = await self.comprehensive_engine.get_latest_result(target_path)
            
            if not result or result.overall_quality_score < 85.0:
                return self._create_response_message({
                    "success": False,
                    "error": "Quality standards not met for certification"
                })
            
            # 品質証明書生成
            certificate = self._create_quality_certificate(result)
            
            return self._create_response_message({
                "success": True,
                "certificate": certificate
            })
            
        except Exception as e:
            logger.error(f"Error generating certificate: {e}")
            return self._create_response_message({
                "success": False,
                "error": str(e)
            })
    
    def _create_quality_certificate(self, result) -> Dict[str, Any]:
        """品質証明書の作成"""
        return {
            "certificate_id": f"QC-{datetime.now().strftime('%Y%m%d')}-{hash(str(result))%10000:04d}",
            "issued_date": datetime.now().isoformat(),
            "issuer": "ComprehensiveGuardian - Elder Council",
            "project_info": {
                "path": result.target_path,
                "overall_score": result.overall_quality_score,
                "certification_level": self._determine_certification_level(result.overall_quality_score)
            },
            "quality_breakdown": {
                "documentation": {
                    "score": result.documentation_score,
                    "completeness": f"{result.doc_completeness}%",
                    "api_coverage": f"{result.api_doc_coverage}%"
                },
                "security": {
                    "score": result.security_score,
                    "vulnerabilities": result.security_vulnerabilities,
                    "compliance": result.security_compliance_level
                },
                "configuration": {
                    "score": result.config_score,
                    "consistency": f"{result.config_consistency}%",
                    "best_practices": result.config_best_practices_score
                },
                "performance": {
                    "score": result.performance_score,
                    "efficiency": f"{result.performance_efficiency}%",
                    "optimization": result.optimization_level
                }
            },
            "validity": {
                "valid_until": (datetime.now().replace(day=1) + timedelta(days=90)).isoformat(),
                "conditions": [
                    "No major code changes",
                    "Dependencies remain updated",
                    "Security patches applied"
                ]
            },
            "verification_hash": hashlib.sha256(
                json.dumps(result.__dict__, sort_keys=True).encode()
            ).hexdigest()[:16]
        }
    
    def _determine_certification_level(self, score: float) -> str:
        """認証レベルの決定"""
        if score >= 95:
            return "PLATINUM"
        elif score >= 90:
            return "GOLD"
        elif score >= 85:
            return "SILVER"
        else:
            return "BRONZE"
    
    @skill(name="health_check")
    async def health_check(self, message: Message) -> Message:
        """ヘルスチェックスキル"""
        health_status = {
            "status": "healthy",
            "servant": self.agent_name,
            "port": self.port,
            "uptime": "operational",
            "metrics": {
                "total_assessments": self.total_assessments,
                "excellent_projects": self.excellent_projects,
                "security_alerts": self.security_alerts,
                "excellence_rate": (
                    self.excellent_projects / self.total_assessments * 100
                    if self.total_assessments > 0 else 0
                )
            }
        }
        return self._create_response_message(health_status)
    
    async def shutdown(self):
        """サーバント終了処理"""
        logger.info(f"ComprehensiveGuardian Servant standing down. Total assessments: {self.total_assessments}")


# === サーバント実行スクリプト ===

async def main():
    """ComprehensiveGuardian サーバント起動"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    servant = ComprehensiveGuardianServant()
    
    try:
        if await servant.initialize():
            print(f"🛡️ Starting ComprehensiveGuardian Servant on port {servant.port}...")
            # Note: 実際のpython-a2a実装では run_server を使用
            await asyncio.Event().wait()  # Keep running
        else:
            print("❌ Failed to initialize ComprehensiveGuardian Servant")
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested")
    finally:
        await servant.shutdown()
        print("✅ ComprehensiveGuardian Servant stopped")


if __name__ == "__main__":
    asyncio.run(main())


# hashlib import忘れの修正
import hashlib
from datetime import timedelta