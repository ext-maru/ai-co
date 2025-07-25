"""
🧝‍♂️ QualityWatcher Servant - 静的解析統括サーバント
python-a2a統合による Block A 実装
One Servant, One Command: analyze_static_quality
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from python_a2a import A2AServer, skill, Message, TextContent, MessageRole

# 既存エンジンの活用
from elders_guild.elder_tree.elder_servants.quality_tribe.engines.static_analysis_engine import StaticAnalysisEngine

logger = logging.getLogger(__name__)


class QualityWatcherServant(A2AServer):
    """
    Block A: 静的解析統括サーバント
    
    責任範囲:
    - Black/isort/MyPy/Pylintの統合実行
    - 静的解析品質の専門判定
    - Iron Will基準の遵守確認
    - Elder Council向けレポート生成
    """
    
    def __init__(self, host: str = "localhost", port: int = 8810):
        """A2Aサーバント初期化"""
        super().__init__()
        
        # サーバント情報
        self.agent_name = "quality-watcher"
        self.description = "Static Analysis Quality Guardian - Block A"
        self.host = host
        self.port = port
        self.command = "analyze_static_quality"  # One Command
        
        # 静的解析エンジン
        self.static_engine = StaticAnalysisEngine()
        
        # メトリクス
        self.total_analyses = 0
        self.approval_count = 0
        self.rejection_count = 0
        
        logger.info(f"QualityWatcher Servant initialized on {host}:{port}")
    
    async def initialize(self) -> bool:
        """サーバント初期化"""
        try:
            # エンジン初期化
            await self.static_engine.initialize()
            logger.info("QualityWatcher Servant ready for duty")
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
    
    @skill(name="analyze_static_quality")
    async def analyze_static_quality(self, message: Message) -> Message:
        """
        統合静的解析コマンド - One Servant, One Command
        
        実行フロー:
        1. エンジンによる自動実行 (Black, isort, MyPy, Pylint)
        2. サーバントによる専門判定
        3. Elder Council向けレポート生成
        """
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            target_path = data.get("target_path", ".")
            
            self.total_analyses += 1
            logger.info(f"Analyzing static quality for: {target_path}")
            
            # エンジン実行（自動化）
            engine_result = await self.static_engine.execute_full_pipeline(target_path)
            
            # サーバント判定（専門性）
            verdict = self._judge_static_quality(engine_result)
            
            # メトリクス更新
            if verdict["verdict"] == "APPROVED":
                self.approval_count += 1
            else:
                self.rejection_count += 1
            
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
            logger.error(f"Error in analyze_static_quality: {e}")
            error_response = {
                "servant": self.agent_name,
                "command": self.command,
                "success": False,
                "error": str(e),
                "verdict": "ERROR"
            }
            return self._create_response_message(error_response)
    
    def _judge_static_quality(self, result) -> Dict[str, Any]:
        """
        純粋な判定ロジック - サーバントの専門性
        
        判定基準:
        - 95点以上: APPROVED (Elder Grade)
        - 85-94点: CONDITIONAL (改善必要)
        - 85点未満: REJECTED (大幅改善必要)
        """
        score = result.quality_score
        issues = result.issues_found
        
        # Iron Will基準チェック
        iron_will_compliance = self._check_iron_will_compliance(result)
        
        if score >= 95.0 and iron_will_compliance >= 90.0:
            return {
                "verdict": "APPROVED",
                "quality_score": score,
                "iron_will_compliance": iron_will_compliance,
                "certification": "ELDER_GRADE",
                "message": "Excellent code quality! Elder Council approved.",
                "details": {
                    "pylint_score": result.scores.get("pylint", 0),
                    "type_safety": result.scores.get("mypy", 100),
                    "format_compliance": result.scores.get("format", 100),
                    "import_order": result.scores.get("import", 100)
                }
            }
        elif score >= 85.0:
            improvements = self._get_improvement_requirements(result)
            return {
                "verdict": "CONDITIONAL",
                "quality_score": score,
                "iron_will_compliance": iron_will_compliance,
                "certification": "APPRENTICE_GRADE",
                "message": "Good quality, but improvements needed.",
                "requirements": improvements,
                "auto_fix_available": True,
                "command": f"{self.command} --auto-fix"
            }
        else:
            critical_issues = self._identify_critical_issues(result)
            return {
                "verdict": "REJECTED",
                "quality_score": score,
                "iron_will_compliance": iron_will_compliance,
                "certification": "NEEDS_TRAINING",
                "message": "Quality standards not met. Major improvements required.",
                "critical_issues": critical_issues,
                "mandatory_actions": [
                    "Run automatic formatting",
                    "Fix all type errors",
                    "Resolve pylint violations",
                    "Ensure Iron Will compliance"
                ],
                "command": f"{self.command} --emergency-fix"
            }
    
    def _check_iron_will_compliance(self, result) -> float:
        """Iron Will基準遵守チェック"""
        compliance_factors = {
            "no_todos": 0 if result.todo_count == 0 else -20,
            "no_fixmes": 0 if result.fixme_count == 0 else -20,
            "no_workarounds": 0 if result.workaround_count == 0 else -30,
            "no_hacks": 0 if result.hack_count == 0 else -30
        }
        
        base_compliance = 100.0
        for factor, penalty in compliance_factors.items():
            base_compliance += penalty
        
        return max(0.0, base_compliance)
    
    def _get_improvement_requirements(self, result) -> list:
        """改善要求事項の生成"""
        requirements = []
        
        if result.scores.get("pylint", 0) < 9.5:
            requirements.append({
                "area": "Pylint Score",
                "current": result.scores.get("pylint", 0),
                "target": 9.5,
                "action": "Fix pylint violations"
            })
        
        if result.scores.get("mypy", 100) < 100:
            requirements.append({
                "area": "Type Safety",
                "current": result.scores.get("mypy", 100),
                "target": 100,
                "action": "Add type annotations"
            })
        
        if result.todo_count > 0 or result.fixme_count > 0:
            requirements.append({
                "area": "Iron Will Compliance",
                "current": f"{result.todo_count} TODOs, {result.fixme_count} FIXMEs",
                "target": "0 TODOs, 0 FIXMEs",
                "action": "Remove all TODO/FIXME comments"
            })
        
        return requirements
    
    def _identify_critical_issues(self, result) -> list:
        """重大問題の特定"""
        critical = []
        
        if result.syntax_errors > 0:
            critical.append({
                "severity": "CRITICAL",
                "issue": "Syntax Errors",
                "count": result.syntax_errors,
                "impact": "Code will not execute"
            })
        
        if result.scores.get("pylint", 0) < 5.0:
            critical.append({
                "severity": "HIGH",
                "issue": "Very Low Pylint Score",
                "score": result.scores.get("pylint", 0),
                "impact": "Poor code quality"
            })
        
        if result.security_issues > 0:
            critical.append({
                "severity": "HIGH",
                "issue": "Security Vulnerabilities",
                "count": result.security_issues,
                "impact": "Security risks"
            })
        
        return critical
    
    @skill(name="get_analysis_report")
    async def get_analysis_report(self, message: Message) -> Message:
        """静的解析レポート生成スキル"""
        try:
            data = self._extract_data_from_message(message)
            target_path = data.get("target_path", ".")
            
            # 最新の解析結果を取得
            result = await self.static_engine.get_latest_result(target_path)
            
            if not result:
                return self._create_response_message({
                    "success": False,
                    "error": "No analysis results found"
                })
            
            # Elder Council向けレポート生成
            report = self._generate_elder_council_report(result)
            
            return self._create_response_message({
                "success": True,
                "report": report
            })
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return self._create_response_message({
                "success": False,
                "error": str(e)
            })
    
    def _generate_elder_council_report(self, result) -> Dict[str, Any]:
        """Elder Council向け詳細レポート生成"""
        return {
            "title": "Static Analysis Quality Report",
            "servant": "QualityWatcher",
            "timestamp": datetime.now().isoformat(),
            "executive_summary": {
                "quality_score": result.quality_score,
                "iron_will_compliance": self._check_iron_will_compliance(result),
                "recommendation": self._get_recommendation(result.quality_score)
            },
            "detailed_analysis": {
                "code_style": {
                    "black_compliance": result.scores.get("format", 100),
                    "import_order": result.scores.get("import", 100)
                },
                "code_quality": {
                    "pylint_score": result.scores.get("pylint", 0),
                    "complexity": result.complexity_score,
                    "maintainability": result.maintainability_index
                },
                "type_safety": {
                    "mypy_score": result.scores.get("mypy", 100),
                    "type_coverage": result.type_coverage_percentage
                },
                "compliance": {
                    "todos": result.todo_count,
                    "fixmes": result.fixme_count,
                    "workarounds": result.workaround_count
                }
            },
            "issues_summary": {
                "total": result.issues_found,
                "critical": result.critical_issues,
                "major": result.major_issues,
                "minor": result.minor_issues
            },
            "certification_status": self._determine_certification(result.quality_score)
        }
    
    def _get_recommendation(self, score: float) -> str:
        """スコアに基づく推奨事項"""
        if score >= 95:
            return "Ready for production. Maintain excellence."
        elif score >= 85:
            return "Good quality. Address minor issues before release."
        elif score >= 75:
            return "Acceptable. Significant improvements recommended."
        else:
            return "Not production ready. Major refactoring required."
    
    def _determine_certification(self, score: float) -> str:
        """認定レベル決定"""
        if score >= 95:
            return "ELDER_GRADE_CERTIFIED"
        elif score >= 85:
            return "APPRENTICE_GRADE"
        elif score >= 75:
            return "NOVICE_GRADE"
        else:
            return "TRAINING_REQUIRED"
    
    @skill(name="health_check")
    async def health_check(self, message: Message) -> Message:
        """ヘルスチェックスキル"""
        health_status = {
            "status": "healthy",
            "servant": self.agent_name,
            "port": self.port,
            "uptime": "operational",
            "metrics": {
                "total_analyses": self.total_analyses,
                "approvals": self.approval_count,
                "rejections": self.rejection_count,
                "approval_rate": (
                    self.approval_count / self.total_analyses * 100 
                    if self.total_analyses > 0 else 0
                )
            }
        }
        return self._create_response_message(health_status)
    
    async def shutdown(self):
        """サーバント終了処理"""
        logger.info(f"QualityWatcher Servant shutting down. Total analyses: {self.total_analyses}")


# === サーバント実行スクリプト ===

async def main():
    """QualityWatcher サーバント起動"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    servant = QualityWatcherServant()
    
    try:
        if await servant.initialize():
            print(f"🧝‍♂️ Starting QualityWatcher Servant on port {servant.port}...")
            # Note: 実際のpython-a2a実装では run_server を使用
            # ここではサンプルとして基本的な実装を示す
            await asyncio.Event().wait()  # Keep running
        else:
            print("❌ Failed to initialize QualityWatcher Servant")
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested")
    finally:
        await servant.shutdown()
        print("✅ QualityWatcher Servant stopped")


if __name__ == "__main__":
    asyncio.run(main())