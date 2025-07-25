"""
🏛️ Quality Pipeline Orchestrator - 3サーバント統合オーケストレータ
python-a2aクライアントとして3サーバントを呼び出し、品質パイプラインを実行
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import httpx

from python_a2a import A2AClient, Message, TextContent, MessageRole

logger = logging.getLogger(__name__)


class QualityPipelineOrchestrator:
    """
    品質パイプラインオーケストレータ
    
    3つのサーバントを順次呼び出し、統合品質評価を実施
    Block A → Block B → Block C の順序で実行
    """
    
    def __init__(self):
        """オーケストレータ初期化"""
        self.name = "quality-pipeline-orchestrator"
        
        # サーバント接続情報
        self.servants = {
            "quality-watcher": {
                "url": "http://localhost:8810",
                "command": "analyze_static_quality",
                "block": "A"
            },
            "test-forge": {
                "url": "http://localhost:8811", 
                "command": "verify_test_quality",
                "block": "B"
            },
            "comprehensive-guardian": {
                "url": "http://localhost:8812",
                "command": "assess_comprehensive_quality",
                "block": "C"
            }
        }
        
        # 実行統計
        self.total_pipelines = 0
        self.successful_pipelines = 0
        self.failed_pipelines = 0
        
        logger.info("Quality Pipeline Orchestrator initialized")
    
    async def execute_pipeline(self, target_path: str) -> Dict[str, Any]:
        """
        完全品質パイプライン実行
        
        Args:
            target_path: 評価対象のパス
            
        Returns:
            パイプライン実行結果
        """
        self.total_pipelines += 1
        pipeline_id = f"QP-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{self.total_pipelines:04d}"
        
        logger.info(f"Starting quality pipeline {pipeline_id} for: {target_path}")
        
        pipeline_start = datetime.now()
        results = {
            "pipeline_id": pipeline_id,
            "target_path": target_path,
            "start_time": pipeline_start.isoformat(),
            "blocks": {},
            "overall_status": "IN_PROGRESS"
        }
        
        try:
            # Block A: 静的解析
            block_a_result = await self._execute_block_a(target_path)
            results["blocks"]["A"] = block_a_result
            
            if block_a_result["verdict"] != "APPROVED":
                results["overall_status"] = "FAILED_AT_BLOCK_A"
                results["failure_reason"] = "Static analysis quality standards not met"
                self.failed_pipelines += 1
                return self._finalize_results(results, pipeline_start)
            
            # Block B: テスト品質
            block_b_result = await self._execute_block_b(target_path)
            results["blocks"]["B"] = block_b_result
            
            if block_b_result["verdict"] != "APPROVED":
                results["overall_status"] = "FAILED_AT_BLOCK_B"
                results["failure_reason"] = "Test quality standards not met"
                self.failed_pipelines += 1
                return self._finalize_results(results, pipeline_start)
            
            # Block C: 包括品質
            block_c_result = await self._execute_block_c(target_path)
            results["blocks"]["C"] = block_c_result
            
            if block_c_result["verdict"] != "APPROVED":
                results["overall_status"] = "FAILED_AT_BLOCK_C"
                results["failure_reason"] = "Comprehensive quality standards not met"
                self.failed_pipelines += 1
                return self._finalize_results(results, pipeline_start)
            
            # すべてのブロックが承認
            results["overall_status"] = "APPROVED"
            results["quality_certificate"] = await self._generate_quality_certificate(results)
            self.successful_pipelines += 1
            
            logger.info(f"Pipeline {pipeline_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Pipeline {pipeline_id} failed with error: {e}")
            results["overall_status"] = "ERROR"
            results["error"] = str(e)
            self.failed_pipelines += 1
        
        return self._finalize_results(results, pipeline_start)
    
    async def _execute_block_a(self, target_path: str) -> Dict[str, Any]:
        """Block A: 静的解析実行"""
        logger.info("Executing Block A: Static Analysis")
        
        try:
            result = await self._call_servant(
                "quality-watcher",
                {"target_path": target_path}
            )
            
            # 結果の検証
            if "verdict" not in result:
                raise ValueError("Invalid response from QualityWatcher")
            
            return {
                "servant": "quality-watcher",
                "verdict": result["verdict"],
                "quality_score": result.get("quality_score", 0),
                "iron_will_compliance": result.get("iron_will_compliance", 0),
                "certification": result.get("certification", "NONE"),
                "details": result.get("details", {}),
                "timestamp": result.get("timestamp", datetime.now().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Block A execution failed: {e}")
            return {
                "servant": "quality-watcher",
                "verdict": "ERROR",
                "error": str(e)
            }
    
    async def _execute_block_b(self, target_path: str) -> Dict[str, Any]:
        """Block B: テスト品質実行"""
        logger.info("Executing Block B: Test Quality")
        
        try:
            result = await self._call_servant(
                "test-forge",
                {"target_path": target_path}
            )
            
            # 結果の検証
            if "verdict" not in result:
                raise ValueError("Invalid response from TestForge")
            
            return {
                "servant": "test-forge",
                "verdict": result["verdict"],
                "coverage": result.get("coverage", 0),
                "tdd_score": result.get("tdd_score", 0),
                "tdd_compliant": result.get("tdd_compliant", False),
                "certification": result.get("certification", "NONE"),
                "details": result.get("details", {}),
                "timestamp": result.get("timestamp", datetime.now().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Block B execution failed: {e}")
            return {
                "servant": "test-forge",
                "verdict": "ERROR",
                "error": str(e)
            }
    
    async def _execute_block_c(self, target_path: str) -> Dict[str, Any]:
        """Block C: 包括品質実行"""
        logger.info("Executing Block C: Comprehensive Quality")
        
        try:
            result = await self._call_servant(
                "comprehensive-guardian",
                {"target_path": target_path}
            )
            
            # 結果の検証
            if "verdict" not in result:
                raise ValueError("Invalid response from ComprehensiveGuardian")
            
            return {
                "servant": "comprehensive-guardian",
                "verdict": result["verdict"],
                "overall_score": result.get("overall_score", 0),
                "certification": result.get("certification", "NONE"),
                "breakdown": result.get("breakdown", {}),
                "achievements": result.get("achievements", []),
                "timestamp": result.get("timestamp", datetime.now().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Block C execution failed: {e}")
            return {
                "servant": "comprehensive-guardian",
                "verdict": "ERROR",
                "error": str(e)
            }
    
    async def _call_servant(self, servant_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        サーバントへのHTTP呼び出し
        
        Note: 実際のpython-a2a実装では、A2AClientを使用してメッセージングを行う
        ここでは簡易的にHTTP直接呼び出しを示す
        """
        servant_info = self.servants[servant_name]
        url = f"{servant_info['url']}/skills/{servant_info['command']}"
        
        async with httpx.AsyncClient() as client:
            try:
                # python-a2a形式のメッセージ作成
                message = {
                    "content": {
                        "type": "text",
                        "text": json.dumps(data)
                    },
                    "role": "user"
                }
                
                response = await client.post(
                    url,
                    json=message,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                # レスポンスからデータ抽出
                if isinstance(result.get("content"), dict):
                    content_text = result["content"].get("text", "{}")
                else:
                    content_text = "{}"
                
                return json.loads(content_text)
                
            except httpx.TimeoutException:
                raise TimeoutError(f"Servant {servant_name} timeout")
            except httpx.HTTPError as e:
                raise RuntimeError(f"HTTP error calling {servant_name}: {e}")
            except Exception as e:
                raise RuntimeError(f"Error calling {servant_name}: {e}")
    
    async def _generate_quality_certificate(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """統合品質証明書の生成"""
        return {
            "certificate_type": "UNIFIED_QUALITY_CERTIFICATE",
            "pipeline_id": results["pipeline_id"],
            "issued_date": datetime.now().isoformat(),
            "issuer": "Quality Pipeline Orchestrator - Elder Council",
            "blocks_approved": {
                "A": results["blocks"]["A"]["certification"],
                "B": results["blocks"]["B"]["certification"],
                "C": results["blocks"]["C"]["certification"]
            },
            "overall_grade": self._calculate_overall_grade(results),
            "validity": {
                "valid_for_days": 30,
                "conditions": [
                    "No major code changes",
                    "All tests continue to pass",
                    "Dependencies remain secure"
                ]
            }
        }
    
    def _calculate_overall_grade(self, results: Dict[str, Any]) -> str:
        """総合グレードの計算"""
        certifications = [
            results["blocks"]["A"]["certification"],
            results["blocks"]["B"]["certification"],
            results["blocks"]["C"]["certification"]
        ]
        
        if all(cert in ["ELDER_GRADE", "TDD_MASTER", "COMPREHENSIVE_EXCELLENCE"] 
               for cert in certifications):
            return "PLATINUM_EXCELLENCE"
        elif all(cert != "NONE" for cert in certifications):
            return "GOLD_STANDARD"
        else:
            return "SILVER_QUALITY"
    
    def _finalize_results(self, results: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """結果の最終処理"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = duration
        results["success"] = results["overall_status"] == "APPROVED"
        
        # 統計情報追加
        results["orchestrator_stats"] = {
            "total_pipelines": self.total_pipelines,
            "successful": self.successful_pipelines,
            "failed": self.failed_pipelines,
            "success_rate": (
                self.successful_pipelines / self.total_pipelines * 100
                if self.total_pipelines > 0 else 0
            )
        }
        
        return results
    
    async def check_servants_health(self) -> Dict[str, Any]:
        """全サーバントのヘルスチェック"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "servants": {}
        }
        
        for servant_name, servant_info in self.servants.items():
            try:
                result = await self._call_servant_health(servant_name)
                health_status["servants"][servant_name] = {
                    "status": result.get("status", "unknown"),
                    "port": servant_info["url"].split(":")[-1],
                    "metrics": result.get("metrics", {})
                }
            except Exception as e:
                health_status["servants"][servant_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        health_status["all_healthy"] = all(
            s["status"] == "healthy" 
            for s in health_status["servants"].values()
        )
        
        return health_status
    
    async def _call_servant_health(self, servant_name: str) -> Dict[str, Any]:
        """サーバントヘルスチェック呼び出し"""
        servant_info = self.servants[servant_name]
        url = f"{servant_info['url']}/skills/health_check"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"content": {"type": "text", "text": "{}"}, "role": "user"},
                timeout=5.0
            )
            response.raise_for_status()
            result = response.json()
            
            content_text = result.get("content", {}).get("text", "{}")
            return json.loads(content_text)


# === CLI実行スクリプト ===

async def main():
    """Quality Pipeline Orchestrator CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Quality Pipeline Orchestrator")
    parser.add_argument("command", choices=["run", "health", "stats"])
    parser.add_argument("--path", default=".", help="Target path for quality check")
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    orchestrator = QualityPipelineOrchestrator()
    
    if args.command == "run":
        print(f"🚀 Starting quality pipeline for: {args.path}")
        result = await orchestrator.execute_pipeline(args.path)
        
        print(f"\n📊 Pipeline Result: {result['overall_status']}")
        if result["success"]:
            print(f"✅ All quality checks passed!")
            print(f"🏆 Certificate: {result['quality_certificate']['overall_grade']}")
        else:
            print(f"❌ Pipeline failed at: {result.get('failure_reason', 'Unknown')}")
        
        print(f"\n⏱️ Duration: {result['duration_seconds']:.2f} seconds")
        
    elif args.command == "health":
        print("🏥 Checking servants health...")
        health = await orchestrator.check_servants_health()
        
        print(f"\n{'✅' if health['all_healthy'] else '❌'} Overall Health: "
              f"{'All servants healthy' if health['all_healthy'] else 'Some servants unhealthy'}")
        
        for servant, status in health["servants"].items():
            emoji = "✅" if status["status"] == "healthy" else "❌"
            print(f"{emoji} {servant}: {status['status']}")
    
    elif args.command == "stats":
        print(f"📊 Orchestrator Statistics:")
        print(f"Total Pipelines: {orchestrator.total_pipelines}")
        print(f"Successful: {orchestrator.successful_pipelines}")
        print(f"Failed: {orchestrator.failed_pipelines}")
        if orchestrator.total_pipelines > 0:
            success_rate = orchestrator.successful_pipelines / orchestrator.total_pipelines * 100
            print(f"Success Rate: {success_rate:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())