#!/usr/bin/env python3
"""
4賢者監視・チェック体制システム
Elders Guild エルダーズによる統合監視システム

タスク賢者: 計画実行監視・進捗管理
インシデント賢者: リスク監視・緊急対応
ナレッジ賢者: 学習状況監視・品質管理
RAG賢者: 情報統合監視・最適化
"""

import os
import json
import subprocess
import logging
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import queue
import schedule


@dataclass
class MonitoringAlert:
    """監視アラート"""
    sage: str
    severity: str
    category: str
    message: str
    timestamp: datetime
    details: Dict[str, Any]


class TaskSageMonitor:
    """📋 タスク賢者監視システム"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.logger = logging.getLogger("TaskSage")
        self.monitoring_data = {
            "active_tasks": [],
            "completed_tasks": [],
            "failed_tasks": [],
            "performance_metrics": {}
        }
    
    def monitor_task_execution(self) -> List[MonitoringAlert]:
        """タスク実行の監視"""
        alerts = []
        
        try:
            # 1. GitHub Flow の遵守状況チェック
            git_status = self.check_github_flow_compliance()
            if not git_status["compliant"]:
                alerts.append(MonitoringAlert(
                    sage="TaskSage",
                    severity="HIGH",
                    category="GITHUB_FLOW_VIOLATION",
                    message=f"GitHub Flow違反: {git_status['issues']}",
                    timestamp=datetime.now(),
                    details=git_status
                ))
            
            # 2. タスク進捗の監視
            progress_status = self.check_task_progress()
            if progress_status["delayed_tasks"]:
                alerts.append(MonitoringAlert(
                    sage="TaskSage",
                    severity="MEDIUM",
                    category="TASK_DELAY",
                    message=f"遅延タスク: {len(progress_status['delayed_tasks'])}件",
                    timestamp=datetime.now(),
                    details=progress_status
                ))
            
            # 3. 品質メトリクスの監視
            quality_status = self.check_quality_metrics()
            if quality_status["quality_score"] < 0.8:
                alerts.append(MonitoringAlert(
                    sage="TaskSage",
                    severity="MEDIUM",
                    category="QUALITY_DEGRADATION",
                    message=f"品質スコア低下: {quality_status['quality_score']:.2f}",
                    timestamp=datetime.now(),
                    details=quality_status
                ))
            
        except Exception as e:
            alerts.append(MonitoringAlert(
                sage="TaskSage",
                severity="HIGH",
                category="MONITORING_ERROR",
                message=f"タスク監視エラー: {e}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            ))
        
        return alerts
    
    def check_github_flow_compliance(self) -> Dict:
        """GitHub Flow遵守状況チェック"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            current_branch = result.stdout.strip()
            issues = []
            
            # 禁止ブランチチェック
            if current_branch == "master":
                issues.append("masterブランチの使用")
            
            # ブランチ命名規則チェック
            valid_prefixes = ["feature/", "fix/", "hotfix/", "docs/", "refactor/"]
            if current_branch not in ["main"] and not any(current_branch.startswith(prefix) for prefix in valid_prefixes):
                issues.append("不正なブランチ命名")
            
            return {
                "compliant": len(issues) == 0,
                "current_branch": current_branch,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "compliant": False,
                "current_branch": "unknown",
                "issues": [f"チェックエラー: {e}"]
            }
    
    def check_task_progress(self) -> Dict:
        """タスク進捗チェック"""
        # 簡易実装（実際はタスク管理システムと連携）
        return {
            "total_tasks": len(self.monitoring_data["active_tasks"]),
            "completed_tasks": len(self.monitoring_data["completed_tasks"]),
            "delayed_tasks": [],
            "progress_rate": 0.85
        }
    
    def check_quality_metrics(self) -> Dict:
        """品質メトリクスチェック"""
        # 簡易実装（実際はコード品質ツールと連携）
        return {
            "quality_score": 0.92,
            "test_coverage": 0.85,
            "code_complexity": 0.75,
            "documentation_coverage": 0.88
        }


class IncidentSageMonitor:
    """🚨 インシデント賢者監視システム"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.logger = logging.getLogger("IncidentSage")
        self.risk_thresholds = {
            "error_rate": 0.05,
            "response_time": 5.0,
            "system_load": 0.8,
            "disk_usage": 0.9
        }
    
    def monitor_system_health(self) -> List[MonitoringAlert]:
        """システム健全性の監視"""
        alerts = []
        
        try:
            # 1. Git リポジトリの健全性チェック
            repo_health = self.check_repository_health()
            if not repo_health["healthy"]:
                alerts.append(MonitoringAlert(
                    sage="IncidentSage",
                    severity="CRITICAL",
                    category="REPOSITORY_CORRUPTION",
                    message=f"リポジトリ異常: {repo_health['issues']}",
                    timestamp=datetime.now(),
                    details=repo_health
                ))
            
            # 2. システムリソースの監視
            resource_status = self.check_system_resources()
            if resource_status["disk_usage"] > self.risk_thresholds["disk_usage"]:
                alerts.append(MonitoringAlert(
                    sage="IncidentSage",
                    severity="HIGH",
                    category="HIGH_DISK_USAGE",
                    message=f"ディスク使用量: {resource_status['disk_usage']:.1%}",
                    timestamp=datetime.now(),
                    details=resource_status
                ))
            
            # 3. セキュリティリスクの監視
            security_status = self.check_security_risks()
            if security_status["risk_level"] > 0.7:
                alerts.append(MonitoringAlert(
                    sage="IncidentSage",
                    severity="HIGH",
                    category="SECURITY_RISK",
                    message=f"セキュリティリスク: {security_status['risks']}",
                    timestamp=datetime.now(),
                    details=security_status
                ))
            
        except Exception as e:
            alerts.append(MonitoringAlert(
                sage="IncidentSage",
                severity="CRITICAL",
                category="MONITORING_ERROR",
                message=f"インシデント監視エラー: {e}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            ))
        
        return alerts
    
    def check_repository_health(self) -> Dict:
        """リポジトリ健全性チェック"""
        try:
            # Git fsck実行
            result = subprocess.run(
                ["git", "fsck", "--full"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            issues = []
            if result.returncode != 0:
                issues.append("リポジトリ破損検出")
            
            # 保護ブランチの存在確認
            branch_result = subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", "refs/heads/main"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            if branch_result.returncode != 0:
                issues.append("mainブランチが存在しない")
            
            return {
                "healthy": len(issues) == 0,
                "issues": issues,
                "fsck_output": result.stderr
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "issues": [f"チェックエラー: {e}"],
                "fsck_output": ""
            }
    
    def check_system_resources(self) -> Dict:
        """システムリソースチェック"""
        try:
            # ディスク使用量
            disk_result = subprocess.run(
                ["df", "-h", str(self.project_dir)],
                capture_output=True,
                text=True
            )
            
            disk_usage = 0.0
            if disk_result.returncode == 0:
                lines = disk_result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 5:
                        usage_str = parts[4].rstrip('%')
                        disk_usage = float(usage_str) / 100.0
            
            return {
                "disk_usage": disk_usage,
                "memory_usage": 0.5,  # 簡易実装
                "cpu_usage": 0.3      # 簡易実装
            }
            
        except Exception as e:
            return {
                "disk_usage": 0.0,
                "memory_usage": 0.0,
                "cpu_usage": 0.0,
                "error": str(e)
            }
    
    def check_security_risks(self) -> Dict:
        """セキュリティリスクチェック"""
        risks = []
        risk_level = 0.0
        
        try:
            # 機密ファイルの存在チェック
            sensitive_patterns = [".env", "*.key", "*.pem", "password*"]
            for pattern in sensitive_patterns:
                files = list(self.project_dir.glob(pattern))
                if files:
                    risks.append(f"機密ファイル検出: {pattern}")
                    risk_level += 0.3
            
            # 権限設定チェック
            git_dir = self.project_dir / ".git"
            if git_dir.exists():
                stat = git_dir.stat()
                if stat.st_mode & 0o077:  # 他者に読み書き権限がある
                    risks.append(".gitディレクトリの権限設定")
                    risk_level += 0.2
            
            return {
                "risk_level": min(risk_level, 1.0),
                "risks": risks
            }
            
        except Exception as e:
            return {
                "risk_level": 1.0,
                "risks": [f"セキュリティチェックエラー: {e}"]
            }


class KnowledgeSageMonitor:
    """📚 ナレッジ賢者監視システム"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.logger = logging.getLogger("KnowledgeSage")
        self.knowledge_base_dir = project_dir / "knowledge_base"
    
    def monitor_knowledge_quality(self) -> List[MonitoringAlert]:
        """ナレッジ品質の監視"""
        alerts = []
        
        try:
            # 1. ドキュメント品質の監視
            doc_quality = self.check_documentation_quality()
            if doc_quality["quality_score"] < 0.8:
                alerts.append(MonitoringAlert(
                    sage="KnowledgeSage",
                    severity="MEDIUM",
                    category="DOC_QUALITY_LOW",
                    message=f"ドキュメント品質低下: {doc_quality['quality_score']:.2f}",
                    timestamp=datetime.now(),
                    details=doc_quality
                ))
            
            # 2. 学習データの整合性監視
            learning_status = self.check_learning_consistency()
            if learning_status["inconsistencies"]:
                alerts.append(MonitoringAlert(
                    sage="KnowledgeSage",
                    severity="MEDIUM",
                    category="LEARNING_INCONSISTENCY",
                    message=f"学習データ不整合: {len(learning_status['inconsistencies'])}件",
                    timestamp=datetime.now(),
                    details=learning_status
                ))
            
            # 3. ナレッジベースの更新状況監視
            update_status = self.check_knowledge_updates()
            if update_status["days_since_update"] > 7:
                alerts.append(MonitoringAlert(
                    sage="KnowledgeSage",
                    severity="LOW",
                    category="KNOWLEDGE_STALE",
                    message=f"ナレッジベース更新なし: {update_status['days_since_update']}日",
                    timestamp=datetime.now(),
                    details=update_status
                ))
            
        except Exception as e:
            alerts.append(MonitoringAlert(
                sage="KnowledgeSage",
                severity="HIGH",
                category="MONITORING_ERROR",
                message=f"ナレッジ監視エラー: {e}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            ))
        
        return alerts
    
    def check_documentation_quality(self) -> Dict:
        """ドキュメント品質チェック"""
        try:
            if not self.knowledge_base_dir.exists():
                return {"quality_score": 0.0, "issues": ["ナレッジベースが存在しない"]}
            
            md_files = list(self.knowledge_base_dir.glob("**/*.md"))
            total_files = len(md_files)
            
            if total_files == 0:
                return {"quality_score": 0.0, "issues": ["ドキュメントファイルが存在しない"]}
            
            # 品質指標の計算
            quality_metrics = {
                "file_count": total_files,
                "average_length": 0,
                "has_headers": 0,
                "has_examples": 0
            }
            
            for md_file in md_files:
                try:
                    content = md_file.read_text(encoding='utf-8')
                    quality_metrics["average_length"] += len(content)
                    
                    if content.count('#') > 0:
                        quality_metrics["has_headers"] += 1
                    
                    if 'example' in content.lower() or '例' in content:
                        quality_metrics["has_examples"] += 1
                        
                except Exception:
                    continue
            
            if total_files > 0:
                quality_metrics["average_length"] /= total_files
                header_ratio = quality_metrics["has_headers"] / total_files
                example_ratio = quality_metrics["has_examples"] / total_files
                
                # 品質スコア計算
                quality_score = (header_ratio * 0.4 + example_ratio * 0.3 + 
                               min(quality_metrics["average_length"] / 1000, 1.0) * 0.3)
                
                return {
                    "quality_score": quality_score,
                    "metrics": quality_metrics,
                    "issues": []
                }
            
            return {"quality_score": 0.0, "issues": ["計算エラー"]}
            
        except Exception as e:
            return {"quality_score": 0.0, "issues": [f"品質チェックエラー: {e}"]}
    
    def check_learning_consistency(self) -> Dict:
        """学習データ整合性チェック"""
        return {
            "consistent": True,
            "inconsistencies": [],
            "last_check": datetime.now()
        }
    
    def check_knowledge_updates(self) -> Dict:
        """ナレッジベース更新状況チェック"""
        try:
            if not self.knowledge_base_dir.exists():
                return {"days_since_update": 999, "last_update": None}
            
            # 最新の更新日を取得
            latest_mtime = 0
            for file in self.knowledge_base_dir.glob("**/*.md"):
                mtime = file.stat().st_mtime
                latest_mtime = max(latest_mtime, mtime)
            
            if latest_mtime > 0:
                last_update = datetime.fromtimestamp(latest_mtime)
                days_since = (datetime.now() - last_update).days
                
                return {
                    "days_since_update": days_since,
                    "last_update": last_update
                }
            
            return {"days_since_update": 999, "last_update": None}
            
        except Exception as e:
            return {"days_since_update": 999, "last_update": None, "error": str(e)}


class RAGSageMonitor:
    """🔍 RAG賢者監視システム"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.logger = logging.getLogger("RAGSage")
    
    def monitor_information_integration(self) -> List[MonitoringAlert]:
        """情報統合の監視"""
        alerts = []
        
        try:
            # 1. 検索精度の監視
            search_accuracy = self.check_search_accuracy()
            if search_accuracy["accuracy"] < 0.8:
                alerts.append(MonitoringAlert(
                    sage="RAGSage",
                    severity="MEDIUM",
                    category="SEARCH_ACCURACY_LOW",
                    message=f"検索精度低下: {search_accuracy['accuracy']:.2f}",
                    timestamp=datetime.now(),
                    details=search_accuracy
                ))
            
            # 2. 情報統合品質の監視
            integration_quality = self.check_integration_quality()
            if integration_quality["quality_score"] < 0.75:
                alerts.append(MonitoringAlert(
                    sage="RAGSage",
                    severity="MEDIUM",
                    category="INTEGRATION_QUALITY_LOW",
                    message=f"統合品質低下: {integration_quality['quality_score']:.2f}",
                    timestamp=datetime.now(),
                    details=integration_quality
                ))
            
            # 3. 最適化状況の監視
            optimization_status = self.check_optimization_status()
            if not optimization_status["optimized"]:
                alerts.append(MonitoringAlert(
                    sage="RAGSage",
                    severity="LOW",
                    category="OPTIMIZATION_NEEDED",
                    message="最適化が必要な状況を検出",
                    timestamp=datetime.now(),
                    details=optimization_status
                ))
            
        except Exception as e:
            alerts.append(MonitoringAlert(
                sage="RAGSage",
                severity="HIGH",
                category="MONITORING_ERROR",
                message=f"RAG監視エラー: {e}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            ))
        
        return alerts
    
    def check_search_accuracy(self) -> Dict:
        """検索精度チェック"""
        # 簡易実装（実際は検索システムと連携）
        return {
            "accuracy": 0.85,
            "total_queries": 100,
            "successful_queries": 85,
            "failed_queries": 15
        }
    
    def check_integration_quality(self) -> Dict:
        """情報統合品質チェック"""
        # 簡易実装（実際は統合システムと連携）
        return {
            "quality_score": 0.78,
            "integration_success_rate": 0.9,
            "relevance_score": 0.85,
            "completeness_score": 0.75
        }
    
    def check_optimization_status(self) -> Dict:
        """最適化状況チェック"""
        # 簡易実装（実際は最適化システムと連携）
        return {
            "optimized": True,
            "performance_score": 0.88,
            "bottlenecks": [],
            "improvement_suggestions": []
        }


class FourSagesMonitoringSystem:
    """4賢者統合監視システム"""
    
    def __init__(self, project_dir: str = "/home/aicompany/ai_co"):
        self.project_dir = Path(project_dir)
        self.config_file = self.project_dir / ".four_sages_monitoring.json"
        self.log_file = self.project_dir / "logs" / "four_sages_monitoring.log"
        self.alerts_file = self.project_dir / "logs" / "monitoring_alerts.json"
        
        self.setup_logging()
        self.config = self.load_config()
        self.alert_queue = queue.Queue()
        
        # 4賢者監視インスタンス
        self.task_sage = TaskSageMonitor(self.project_dir)
        self.incident_sage = IncidentSageMonitor(self.project_dir)
        self.knowledge_sage = KnowledgeSageMonitor(self.project_dir)
        self.rag_sage = RAGSageMonitor(self.project_dir)
        
        self.monitoring_active = False
        self.monitoring_thread = None
    
    def setup_logging(self):
        """ログシステムの設定"""
        self.log_file.parent.mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("FourSagesMonitoring")
    
    def load_config(self) -> Dict:
        """設定ファイルの読み込み"""
        default_config = {
            "monitoring_enabled": True,
            "check_intervals": {
                "task_sage": 300,      # 5分
                "incident_sage": 60,   # 1分
                "knowledge_sage": 1800, # 30分
                "rag_sage": 600        # 10分
            },
            "alert_thresholds": {
                "CRITICAL": 0,
                "HIGH": 2,
                "MEDIUM": 5,
                "LOW": 10
            },
            "notification_settings": {
                "immediate_notify": ["CRITICAL", "HIGH"],
                "batch_notify": ["MEDIUM", "LOW"],
                "batch_interval": 3600  # 1時間
            },
            "escalation_rules": {
                "auto_escalate": True,
                "escalation_timeout": 1800,  # 30分
                "max_escalation_level": 3
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                self.logger.error(f"設定ファイル読み込みエラー: {e}")
        
        return default_config
    
    def save_config(self):
        """設定ファイルの保存"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"設定ファイル保存エラー: {e}")
    
    def collect_all_alerts(self) -> List[MonitoringAlert]:
        """全4賢者からアラートを収集"""
        all_alerts = []
        
        try:
            # タスク賢者からのアラート
            task_alerts = self.task_sage.monitor_task_execution()
            all_alerts.extend(task_alerts)
            
            # インシデント賢者からのアラート
            incident_alerts = self.incident_sage.monitor_system_health()
            all_alerts.extend(incident_alerts)
            
            # ナレッジ賢者からのアラート
            knowledge_alerts = self.knowledge_sage.monitor_knowledge_quality()
            all_alerts.extend(knowledge_alerts)
            
            # RAG賢者からのアラート
            rag_alerts = self.rag_sage.monitor_information_integration()
            all_alerts.extend(rag_alerts)
            
        except Exception as e:
            self.logger.error(f"アラート収集エラー: {e}")
            all_alerts.append(MonitoringAlert(
                sage="System",
                severity="CRITICAL",
                category="MONITORING_SYSTEM_ERROR",
                message=f"監視システムエラー: {e}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            ))
        
        return all_alerts
    
    def process_alerts(self, alerts: List[MonitoringAlert]):
        """アラートの処理"""
        try:
            # 重要度別にアラートを分類
            critical_alerts = [a for a in alerts if a.severity == "CRITICAL"]
            high_alerts = [a for a in alerts if a.severity == "HIGH"]
            medium_alerts = [a for a in alerts if a.severity == "MEDIUM"]
            low_alerts = [a for a in alerts if a.severity == "LOW"]
            
            # 即座に通知すべきアラート
            immediate_alerts = critical_alerts + high_alerts
            if immediate_alerts:
                self.send_immediate_notifications(immediate_alerts)
            
            # バッチ通知すべきアラート
            batch_alerts = medium_alerts + low_alerts
            if batch_alerts:
                self.queue_batch_notifications(batch_alerts)
            
            # アラートをファイルに保存
            self.save_alerts(alerts)
            
            # 4賢者による統合判定
            consensus = self.four_sages_consensus(alerts)
            if consensus["action_required"]:
                self.execute_consensus_action(consensus)
            
        except Exception as e:
            self.logger.error(f"アラート処理エラー: {e}")
    
    def four_sages_consensus(self, alerts: List[MonitoringAlert]) -> Dict:
        """4賢者による統合判定"""
        try:
            # 賢者別のアラート数を集計
            sage_alerts = {}
            for alert in alerts:
                sage = alert.sage
                if sage not in sage_alerts:
                    sage_alerts[sage] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
                sage_alerts[sage][alert.severity] += 1
            
            # 各賢者の懸念レベルを計算
            concern_levels = {}
            for sage, counts in sage_alerts.items():
                concern_level = (counts["CRITICAL"] * 4 + counts["HIGH"] * 3 + 
                               counts["MEDIUM"] * 2 + counts["LOW"] * 1)
                concern_levels[sage] = concern_level
            
            # 統合判定
            total_concern = sum(concern_levels.values())
            max_concern = max(concern_levels.values()) if concern_levels else 0
            
            action_required = False
            action_type = "none"
            
            if total_concern >= 10 or max_concern >= 6:
                action_required = True
                if max_concern >= 8:
                    action_type = "emergency_response"
                elif total_concern >= 15:
                    action_type = "coordinated_response"
                else:
                    action_type = "standard_response"
            
            return {
                "action_required": action_required,
                "action_type": action_type,
                "total_concern": total_concern,
                "max_concern": max_concern,
                "sage_concerns": concern_levels,
                "consensus_confidence": min(1.0, total_concern / 20.0)
            }
            
        except Exception as e:
            self.logger.error(f"4賢者合意判定エラー: {e}")
            return {
                "action_required": True,
                "action_type": "emergency_response",
                "error": str(e)
            }
    
    def execute_consensus_action(self, consensus: Dict):
        """合意されたアクションの実行"""
        try:
            action_type = consensus["action_type"]
            
            if action_type == "emergency_response":
                self.logger.critical("緊急対応を実行中")
                self.trigger_emergency_response()
            
            elif action_type == "coordinated_response":
                self.logger.warning("協調対応を実行中")
                self.trigger_coordinated_response()
            
            elif action_type == "standard_response":
                self.logger.info("標準対応を実行中")
                self.trigger_standard_response()
            
        except Exception as e:
            self.logger.error(f"合意アクション実行エラー: {e}")
    
    def trigger_emergency_response(self):
        """緊急対応の実行"""
        try:
            # 緊急対応システムの呼び出し
            emergency_script = self.project_dir / "scripts" / "emergency_response_system.py"
            if emergency_script.exists():
                subprocess.run([
                    "python3", str(emergency_script)
                ], cwd=self.project_dir)
            
        except Exception as e:
            self.logger.error(f"緊急対応実行エラー: {e}")
    
    def trigger_coordinated_response(self):
        """協調対応の実行"""
        try:
            # GitHub Flow保護システムの実行
            protection_script = self.project_dir / "scripts" / "github_flow_protection.py"
            if protection_script.exists():
                subprocess.run([
                    "python3", str(protection_script)
                ], cwd=self.project_dir)
            
        except Exception as e:
            self.logger.error(f"協調対応実行エラー: {e}")
    
    def trigger_standard_response(self):
        """標準対応の実行"""
        try:
            # ログ記録と通知のみ
            self.logger.info("標準対応: 監視継続")
            
        except Exception as e:
            self.logger.error(f"標準対応実行エラー: {e}")
    
    def send_immediate_notifications(self, alerts: List[MonitoringAlert]):
        """即座の通知送信"""
        for alert in alerts:
            self.logger.critical(f"即座通知: {alert.sage} - {alert.message}")
    
    def queue_batch_notifications(self, alerts: List[MonitoringAlert]):
        """バッチ通知のキューイング"""
        for alert in alerts:
            self.alert_queue.put(alert)
    
    def save_alerts(self, alerts: List[MonitoringAlert]):
        """アラートをファイルに保存"""
        try:
            alert_data = []
            for alert in alerts:
                alert_data.append({
                    "sage": alert.sage,
                    "severity": alert.severity,
                    "category": alert.category,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "details": alert.details
                })
            
            # 既存のアラートを読み込み
            existing_alerts = []
            if self.alerts_file.exists():
                with open(self.alerts_file, 'r') as f:
                    existing_alerts = json.load(f)
            
            # 新しいアラートを追加
            existing_alerts.extend(alert_data)
            
            # 最新1000件のみ保持
            if len(existing_alerts) > 1000:
                existing_alerts = existing_alerts[-1000:]
            
            # ファイルに保存
            with open(self.alerts_file, 'w') as f:
                json.dump(existing_alerts, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"アラート保存エラー: {e}")
    
    def run_monitoring_cycle(self):
        """監視サイクルの実行"""
        try:
            # アラート収集
            alerts = self.collect_all_alerts()
            
            # アラート処理
            if alerts:
                self.process_alerts(alerts)
                self.logger.info(f"監視サイクル完了: {len(alerts)}件のアラート処理")
            else:
                self.logger.debug("監視サイクル完了: アラートなし")
            
        except Exception as e:
            self.logger.error(f"監視サイクルエラー: {e}")
    
    def start_monitoring(self):
        """監視システムの開始"""
        try:
            if self.monitoring_active:
                self.logger.warning("監視システムは既に動作中です")
                return
            
            self.monitoring_active = True
            self.logger.info("4賢者監視システムを開始します")
            
            # スケジュール設定
            schedule.every(1).minutes.do(self.run_monitoring_cycle)
            
            # 監視ループ
            while self.monitoring_active:
                schedule.run_pending()
                time.sleep(10)  # 10秒間隔でスケジュールをチェック
                
        except KeyboardInterrupt:
            self.logger.info("ユーザーによって監視システムが停止されました")
        except Exception as e:
            self.logger.error(f"監視システムエラー: {e}")
        finally:
            self.monitoring_active = False
    
    def stop_monitoring(self):
        """監視システムの停止"""
        self.monitoring_active = False
        self.logger.info("監視システムを停止します")
    
    def get_monitoring_status(self) -> Dict:
        """監視システムの状態取得"""
        try:
            # 最近のアラート統計
            recent_alerts = []
            if self.alerts_file.exists():
                with open(self.alerts_file, 'r') as f:
                    all_alerts = json.load(f)
                    
                    # 過去24時間のアラート
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    recent_alerts = [
                        alert for alert in all_alerts
                        if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
                    ]
            
            return {
                "monitoring_active": self.monitoring_active,
                "recent_alerts_count": len(recent_alerts),
                "last_check": datetime.now().isoformat(),
                "config": self.config
            }
            
        except Exception as e:
            self.logger.error(f"状態取得エラー: {e}")
            return {
                "monitoring_active": self.monitoring_active,
                "error": str(e)
            }


def main():
    """メイン実行関数"""
    print("🧙‍♂️ Elders Guild 4賢者監視システム")
    print("📋 タスク賢者 🚨 インシデント賢者 📚 ナレッジ賢者 🔍 RAG賢者")
    print("=" * 60)
    
    monitoring_system = FourSagesMonitoringSystem()
    
    try:
        import sys
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "start":
                monitoring_system.start_monitoring()
            elif command == "status":
                status = monitoring_system.get_monitoring_status()
                print(json.dumps(status, indent=2, ensure_ascii=False))
            elif command == "test":
                # 単発実行（テスト用）
                monitoring_system.run_monitoring_cycle()
                print("✅ 監視サイクルテスト完了")
            else:
                print(f"不明なコマンド: {command}")
                print("使用法: python four_sages_monitoring.py [start|status|test]")
        else:
            # デフォルトは単発実行
            monitoring_system.run_monitoring_cycle()
            print("✅ 4賢者監視システムが正常に完了しました")
            
    except KeyboardInterrupt:
        print("\n🛑 ユーザーによって中断されました")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False
    
    return True


if __name__ == "__main__":
    main()