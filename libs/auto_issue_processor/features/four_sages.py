#!/usr/bin/env python3
"""
4賢者統合機能
ナレッジ賢者、タスク賢者、インシデント賢者、RAG賢者との連携
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from github.Issue import Issue

from ..core.config import ProcessorConfig

logger = logging.getLogger(__name__)


class KnowledgeSage:
    """ナレッジ賢者 - 過去の知識と経験を管理"""
    
    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        self.knowledge_base = Path(knowledge_base_path)
        self.patterns_file = self.knowledge_base / "issue_patterns.json"
        self.solutions_file = self.knowledge_base / "known_solutions.json"
        self._load_knowledge()
    
    def _load_knowledge(self):
        """知識ベースを読み込み"""
        self.patterns = {}
        self.solutions = {}
        
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r') as f:
                self.patterns = json.load(f)
        
        if self.solutions_file.exists():
            with open(self.solutions_file, 'r') as f:
                self.solutions = json.load(f)
    
    async def analyze_issue(self, issue: Issue) -> Dict[str, Any]:
        """Issueを分析して既知のパターンと照合"""
        analysis = {
            "known_pattern": False,
            "pattern_match": None,
            "suggested_solution": None,
            "confidence": 0.0
        }
        
        # タイトルとボディからキーワードを抽出
        keywords = self._extract_keywords(issue)
        
        # パターンマッチング
        for pattern_id, pattern in self.patterns.items():
            match_score = self._calculate_match_score(keywords, pattern["keywords"])
            if match_score > 0.7:
                analysis["known_pattern"] = True
                analysis["pattern_match"] = pattern_id
                analysis["confidence"] = match_score
                
                # 既知の解決策を検索
                if pattern_id in self.solutions:
                    analysis["suggested_solution"] = self.solutions[pattern_id]
                
                break
        
        return analysis
    
    def _extract_keywords(self, issue: Issue) -> List[str]:
        """Issueからキーワードを抽出"""
        text = f"{issue.title} {issue.body or ''}"
        # 簡易的なキーワード抽出（実際はより高度な処理が必要）
        words = text.lower().split()
        return [w for w in words if len(w) > 3]
    
    def _calculate_match_score(self, keywords1: List[str], keywords2: List[str]) -> float:
        """キーワードの一致度を計算"""
        if not keywords1 or not keywords2:
            return 0.0
        
        common = set(keywords1) & set(keywords2)
        return len(common) / max(len(keywords1), len(keywords2))
    
    async def learn_from_result(self, issue: Issue, result: Dict[str, Any]):
        """処理結果から学習"""
        if result.get("success"):
            # 成功パターンを記録
            pattern_id = f"pattern_{issue.number}"
            self.patterns[pattern_id] = {
                "keywords": self._extract_keywords(issue),
                "issue_type": self._classify_issue_type(issue),
                "success_rate": 1.0,
                "last_seen": datetime.now().isoformat()
            }
            
            # 解決策を保存
            if "artifacts" in result:
                self.solutions[pattern_id] = {
                    "approach": "auto_generated",
                    "artifacts": list(result["artifacts"].keys()),
                    "metrics": result.get("_metrics", {})
                }
            
            self._save_knowledge()


class TaskSage:
    """タスク賢者 - タスクの優先順位と実行管理"""
    
    def __init__(self, db_path: str = "task_history.db"):
        self.db_path = db_path
        self.task_queue: List[Dict[str, Any]] = []
        self.execution_history: List[Dict[str, Any]] = []
    
    async def prioritize_issues(self, issues: List[Issue]) -> List[Issue]:
        """Issueの優先順位を決定"""
        scored_issues = []
        
        for issue in issues:
            score = await self._calculate_priority_score(issue)
            scored_issues.append((score, issue))
        
        # スコア順にソート（降順）
        scored_issues.sort(key=lambda x: x[0], reverse=True)
        
        return [issue for _, issue in scored_issues]
    
    async def _calculate_priority_score(self, issue: Issue) -> float:
        """優先度スコアを計算"""
        score = 0.0
        
        # ラベルによる重み付け
        label_weights = {
            "critical": 100,
            "high": 50,
            "medium": 20,
            "low": 10,
            "bug": 30,
            "security": 40,
            "performance": 25
        }
        
        for label in issue.labels:
            score += label_weights.get(label.name.lower(), 0)
        
        # 古いIssueは優先度を上げる
        age_days = (datetime.now() - issue.created_at.replace(tzinfo=None)).days
        score += min(age_days * 0.5, 20)  # 最大20ポイント
        
        # コメント数（関心度）
        score += min(issue.comments, 10) * 2
        
        # 👍 リアクション数
        if hasattr(issue, 'reactions') and '+1' in issue.reactions:
            score += issue.reactions['+1'] * 3
        
        return score
    
    async def record_execution(self, issue: Issue, result: Dict[str, Any]):
        """実行結果を記録"""
        execution_record = {
            "issue_number": issue.number,
            "timestamp": datetime.now().isoformat(),
            "success": result.get("success", False),
            "duration": result.get("_metrics", {}).get("processing_time", 0),
            "priority_score": await self._calculate_priority_score(issue)
        }
        
        self.execution_history.append(execution_record)
        
        # 統計を更新
        await self._update_statistics()
    
    async def _update_statistics(self):
        """実行統計を更新"""
        if len(self.execution_history) < 10:
            return
        
        recent = self.execution_history[-100:]  # 直近100件
        
        success_rate = sum(1 for r in recent if r["success"]) / len(recent)
        avg_duration = sum(r["duration"] for r in recent) / len(recent)
        
        logger.info(f"Task statistics - Success rate: {success_rate:.1%}, "
                   f"Avg duration: {avg_duration:.1f}s")


class IncidentSage:
    """インシデント賢者 - エラーと問題の検出・対応"""
    
    def __init__(self):
        self.incident_log: List[Dict[str, Any]] = []
        self.alert_thresholds = {
            "error_rate": 0.3,  # 30%以上のエラー率
            "processing_time": 300,  # 5分以上の処理時間
            "memory_usage": 1024  # 1GB以上のメモリ使用
        }
    
    async def pre_check(self, issue: Issue) -> Dict[str, Any]:
        """Issue処理前のチェック"""
        warnings = []
        
        # 危険なキーワードチェック
        dangerous_keywords = ["delete", "drop", "remove all", "clear all", "reset"]
        text = f"{issue.title} {issue.body or ''}".lower()
        
        for keyword in dangerous_keywords:
            if keyword in text:
                warnings.append(f"Dangerous keyword detected: {keyword}")
        
        # 大規模変更の検出
        if "refactor" in text or "restructure" in text:
            warnings.append("Large-scale changes detected")
        
        return {
            "safe": len(warnings) == 0,
            "warnings": warnings,
            "risk_level": self._calculate_risk_level(warnings)
        }
    
    def _calculate_risk_level(self, warnings: List[str]) -> str:
        """リスクレベルを計算"""
        if not warnings:
            return "low"
        elif len(warnings) == 1:
            return "medium"
        else:
            return "high"
    
    async def monitor_execution(self, issue_number: int, metrics: Dict[str, Any]):
        """実行中の監視"""
        # 閾値チェック
        alerts = []
        
        if metrics.get("processing_time", 0) > self.alert_thresholds["processing_time"]:
            alerts.append(f"Processing time exceeded: {metrics['processing_time']}s")
        
        if metrics.get("memory_delta_mb", 0) > self.alert_thresholds["memory_usage"]:
            alerts.append(f"High memory usage: {metrics['memory_delta_mb']}MB")
        
        if alerts:
            await self._raise_incident(issue_number, alerts)
    
    async def _raise_incident(self, issue_number: int, alerts: List[str]):
        """インシデントを発生"""
        incident = {
            "issue_number": issue_number,
            "timestamp": datetime.now().isoformat(),
            "alerts": alerts,
            "severity": "high" if len(alerts) > 1 else "medium"
        }
        
        self.incident_log.append(incident)
        logger.warning(f"Incident raised for Issue #{issue_number}: {alerts}")
    
    async def post_mortem(self, issue: Issue, error: Exception) -> Dict[str, Any]:
        """エラー後の事後分析"""
        analysis = {
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "recommendations": []
        }
        
        # エラータイプ別の推奨事項
        if isinstance(error, MemoryError):
            analysis["recommendations"].append("Reduce batch size or increase memory")
        elif isinstance(error, TimeoutError):
            analysis["recommendations"].append("Increase timeout or optimize processing")
        elif "rate limit" in str(error).lower():
            analysis["recommendations"].append("Implement rate limit handling")
        
        return analysis


class RAGSage:
    """RAG賢者 - 検索と情報統合"""
    
    def __init__(self):
        self.vector_store = None  # 実際はベクトルDBを使用
        self.search_history: List[Dict[str, Any]] = []
    
    async def search_similar_issues(self, issue: Issue) -> List[Dict[str, Any]]:
        """類似のIssueを検索"""
        # 簡易実装（実際はベクトル検索を使用）
        similar = []
        
        # タイトルの類似性チェック
        keywords = set(issue.title.lower().split())
        
        # TODO: 実際のデータベース検索を実装
        # ここではダミーデータを返す
        if "bug" in keywords:
            similar.append({
                "issue_number": 100,
                "title": "Similar bug fixed",
                "similarity": 0.85,
                "solution": "Applied patch X"
            })
        
        return similar
    
    async def aggregate_knowledge(self, issue: Issue) -> Dict[str, Any]:
        """関連知識を集約"""
        aggregated = {
            "similar_issues": await self.search_similar_issues(issue),
            "related_docs": await self._search_documentation(issue),
            "code_examples": await self._search_code_examples(issue)
        }
        
        return aggregated
    
    async def _search_documentation(self, issue: Issue) -> List[str]:
        """関連ドキュメントを検索"""
        # TODO: 実装
        return []
    
    async def _search_code_examples(self, issue: Issue) -> List[Dict[str, str]]:
        """関連コード例を検索"""
        # TODO: 実装
        return []


class FourSagesIntegration:
    """4賢者統合システム"""
    
    def __init__(self, config: ProcessorConfig):
        self.config = config
        
        # 各賢者を初期化
        self.knowledge_sage = KnowledgeSage()
        self.task_sage = TaskSage()
        self.incident_sage = IncidentSage()
        self.rag_sage = RAGSage()
        
        logger.info("Four Sages Integration initialized")
    
    async def analyze_issue(self, issue: Issue) -> Dict[str, Any]:
        """4賢者による総合分析"""
        logger.info(f"🧙‍♂️ Four Sages analyzing Issue #{issue.number}")
        
        # 並列で各賢者の分析を実行
        tasks = [
            self.knowledge_sage.analyze_issue(issue),
            self.incident_sage.pre_check(issue),
            self.rag_sage.aggregate_knowledge(issue)
        ]
        
        results = await asyncio.gather(*tasks)
        
        knowledge_analysis = results[0]
        incident_check = results[1]
        rag_knowledge = results[2]
        
        # 総合判定
        should_skip = False
        skip_reason = None
        
        # インシデント賢者が高リスクと判定
        if incident_check["risk_level"] == "high":
            should_skip = True
            skip_reason = "High risk detected by Incident Sage"
        
        # ナレッジ賢者が既知の失敗パターンと判定
        elif knowledge_analysis.get("known_pattern") and knowledge_analysis.get("confidence", 0) < 0.5:
            should_skip = True
            skip_reason = "Known failure pattern detected"
        
        return {
            "skip": should_skip,
            "reason": skip_reason,
            "knowledge": knowledge_analysis,
            "incident": incident_check,
            "rag": rag_knowledge,
            "summary": self._create_summary(knowledge_analysis, incident_check, rag_knowledge)
        }
    
    def _create_summary(self, knowledge: Dict, incident: Dict, rag: Dict) -> str:
        """分析結果のサマリーを作成"""
        summary_parts = []
        
        if knowledge.get("known_pattern"):
            summary_parts.append(f"Known pattern detected (confidence: {knowledge['confidence']:.0%})")
        
        if incident.get("warnings"):
            summary_parts.append(f"Warnings: {', '.join(incident['warnings'])}")
        
        if rag.get("similar_issues"):
            summary_parts.append(f"Found {len(rag['similar_issues'])} similar issues")
        
        return " | ".join(summary_parts) if summary_parts else "No significant findings"
    
    async def report_critical_error(self, error: Exception, context: Dict[str, Any]):
        """重大エラーを4賢者に報告"""
        logger.critical("🚨 Reporting critical error to Four Sages")
        
        # 各賢者に通知
        await asyncio.gather(
            self._notify_knowledge_sage(error, context),
            self._notify_incident_sage(error, context),
            self._notify_task_sage(error, context),
            return_exceptions=True
        )
    
    async def _notify_knowledge_sage(self, error: Exception, context: Dict[str, Any]):
        """ナレッジ賢者に通知"""
        # エラーパターンを学習
        error_pattern = {
            "error_type": error.__class__.__name__,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        # TODO: 知識ベースに保存
    
    async def _notify_incident_sage(self, error: Exception, context: Dict[str, Any]):
        """インシデント賢者に通知"""
        await self.incident_sage.post_mortem(
            context.get("issue"),
            error
        )
    
    async def _notify_task_sage(self, error: Exception, context: Dict[str, Any]):
        """タスク賢者に通知"""
        # 失敗を記録
        if "issue" in context:
            await self.task_sage.record_execution(
                context["issue"],
                {"success": False, "error": str(error)}
            )
    
    async def optimize_processing_order(self, issues: List[Issue]) -> List[Issue]:
        """4賢者の知見を元に処理順序を最適化"""
        # タスク賢者による優先順位付け
        prioritized = await self.task_sage.prioritize_issues(issues)
        
        # インシデント賢者によるリスクチェック
        safe_issues = []
        for issue in prioritized:
            check = await self.incident_sage.pre_check(issue)
            if check["risk_level"] != "high":
                safe_issues.append(issue)
            else:
                logger.warning(f"Issue #{issue.number} skipped due to high risk")
        
        return safe_issues