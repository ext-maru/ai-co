"""
🌊 Flow Compliance Auditor - Elder Flow遵守監査魔法
Elder Flow 5段階フローの完全実行を監査し、プロセス遵守違反を検出する
"""

import asyncio
import json
import logging
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import sqlite3

# プロジェクトルートをパスに追加
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.base import AncientElderBase, AuditResult, ViolationSeverity


class FlowStage(str):
    """Elder Flow の5段階"""
    SAGE_COUNCIL = "sage_council"        # 4賢者会議
    SERVANT_EXECUTION = "servant_execution"  # エルダーサーバント実行
    QUALITY_GATE = "quality_gate"        # 品質ゲート
    COUNCIL_REPORT = "council_report"    # 評議会報告
    GIT_AUTOMATION = "git_automation"    # Git自動化


class FlowViolationType:
    """フロー遵守違反の種類"""
    INCOMPLETE_FLOW = "INCOMPLETE_FLOW"          # 不完全なフロー実行
    SKIPPED_SAGE_COUNCIL = "SKIPPED_SAGE_COUNCIL"    # 4賢者会議をスキップ
    BYPASSED_QUALITY_GATE = "BYPASSED_QUALITY_GATE"  # 品質ゲートをバイパス
    MISSING_SERVANT = "MISSING_SERVANT"          # サーバント実行なし
    NO_COUNCIL_REPORT = "NO_COUNCIL_REPORT"      # 評議会報告なし
    WRONG_EXECUTION_ORDER = "WRONG_EXECUTION_ORDER"  # 実行順序違反
    TIMEOUT_VIOLATION = "TIMEOUT_VIOLATION"      # タイムアウト違反


class ElderFlowTracer:
    """Elder Flow実行トレーサー"""
    
    def __init__(self, log_directory: Optional[Path] = None):
        self.log_directory = log_directory or Path("logs")
        self.logger = logging.getLogger("ElderFlowTracer")
        
        # フロー実行パターン
        self.flow_patterns = {
            FlowStage.SAGE_COUNCIL: [
                re.compile(r'sage.*council.*started', re.IGNORECASE),
                re.compile(r'4.*sage.*meeting', re.IGNORECASE),
                re.compile(r'consulting.*four.*sages', re.IGNORECASE),
                re.compile(r'elder.*flow.*sage.*phase', re.IGNORECASE),
            ],
            FlowStage.SERVANT_EXECUTION: [
                re.compile(r'elder.*servant.*execution', re.IGNORECASE),
                re.compile(r'servant.*executing', re.IGNORECASE),
                re.compile(r'code.*craftsman|test.*guardian|quality.*inspector', re.IGNORECASE),
                re.compile(r'elder.*flow.*servant.*phase', re.IGNORECASE),
            ],
            FlowStage.QUALITY_GATE: [
                re.compile(r'quality.*gate.*check', re.IGNORECASE),
                re.compile(r'elder.*flow.*quality.*gate', re.IGNORECASE),
                re.compile(r'quality.*validation.*started', re.IGNORECASE),
                re.compile(r'quality.*gatekeeper', re.IGNORECASE),
            ],
            FlowStage.COUNCIL_REPORT: [
                re.compile(r'council.*report.*generated', re.IGNORECASE),
                re.compile(r'elder.*flow.*report', re.IGNORECASE),
                re.compile(r'evaluation.*council.*submission', re.IGNORECASE),
                re.compile(r'elder.*flow.*council.*phase', re.IGNORECASE),
            ],
            FlowStage.GIT_AUTOMATION: [
                re.compile(r'git.*automation.*started', re.IGNORECASE),
                re.compile(r'elder.*flow.*git.*phase', re.IGNORECASE),
                re.compile(r'conventional.*commits.*created', re.IGNORECASE),
                re.compile(r'auto.*push.*completed', re.IGNORECASE),
            ]
        }
        
        # バイパスパターン
        self.bypass_patterns = [
            re.compile(r'bypassing.*quality.*gate', re.IGNORECASE),
            re.compile(r'skipping.*sage.*council', re.IGNORECASE),
            re.compile(r'force.*override', re.IGNORECASE),
            re.compile(r'emergency.*bypass', re.IGNORECASE),
            re.compile(r'--no-quality.*--no-sage', re.IGNORECASE),
        ]
        
    def trace_flow_execution(self, 
                           task_id: Optional[str] = None,
                           time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """フロー実行をトレース"""
        if time_window is None:
            time_window = timedelta(hours=24)  # デフォルトは24時間
            
        cutoff_time = datetime.now() - time_window
        
        # ログファイルを検索
        log_files = self._find_log_files(cutoff_time)
        
        # フロー実行を解析
        flow_executions = {}
        bypasses = []
        
        for log_file in log_files:
            try:
                executions, bypass_events = self._parse_log_file(log_file, task_id, cutoff_time)
                flow_executions.update(executions)
                bypasses.extend(bypass_events)
            except Exception as e:
                self.logger.warning(f"Failed to parse log file {log_file}: {e}")
                
        return {
            "flow_executions": flow_executions,
            "bypasses": bypasses,
            "trace_window": {
                "start": cutoff_time.isoformat(),
                "end": datetime.now().isoformat()
            },
            "logs_analyzed": len(log_files)
        }
        
    def _find_log_files(self, cutoff_time: datetime) -> List[Path]:
        """ログファイルを検索"""
        log_files = []
        
        if not self.log_directory.exists():
            return log_files
            
        # Elder Flow関連のログファイルパターン
        patterns = [
            "elder_flow*.log",
            "elder_*.log", 
            "sage_*.log",
            "servant_*.log",
            "quality_*.log",
            "*.log"  # 全ログファイル（最後に検索）
        ]
        
        for pattern in patterns:
            for log_file in self.log_directory.glob(pattern):
                if log_file.is_file():
                    try:
                        # ファイルの最終変更時刻をチェック
                        if datetime.fromtimestamp(log_file.stat().st_mtime) >= cutoff_time:
                            log_files.append(log_file)
                    except:
                        # アクセスできない場合はスキップ
                        pass
                        
        return log_files
        
    def _parse_log_file(self, 
                       log_file: Path, 
                       task_id: Optional[str], 
                       cutoff_time: datetime) -> Tuple[Dict, List]:
        """ログファイルを解析"""
        flow_executions = {}
        bypasses = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # タイムスタンプを抽出
                        timestamp = self._extract_timestamp(line)
                        if timestamp and timestamp < cutoff_time:
                            continue
                            
                        # タスクIDフィルタリング
                        if task_id and task_id not in line:
                            continue
                            
                        # フロー段階の検出
                        for stage, patterns in self.flow_patterns.items():
                            for pattern in patterns:
                                if pattern.search(line):
                                    execution_id = self._extract_execution_id(line, task_id)
                                    if execution_id not in flow_executions:
                                        flow_executions[execution_id] = {
                                            "stages": {},
                                            "task_id": task_id or "unknown",
                                            "start_time": timestamp or datetime.now(),
                                        }
                                    
                                    flow_executions[execution_id]["stages"][stage] = {
                                        "detected": True,
                                        "timestamp": timestamp or datetime.now(),
                                        "log_line": line.strip(),
                                        "log_file": str(log_file),
                                        "line_number": line_num
                                    }
                                    break
                                    
                        # バイパス検出
                        for pattern in self.bypass_patterns:
                            if pattern.search(line):
                                bypasses.append({
                                    "type": "bypass_detected",
                                    "timestamp": timestamp or datetime.now(),
                                    "log_line": line.strip(),
                                    "log_file": str(log_file),
                                    "line_number": line_num,
                                    "task_id": task_id or self._extract_execution_id(line)
                                })
                                break
                                
                    except Exception as e:
                        # 個別行の解析エラーは無視
                        pass
                        
        except Exception as e:
            self.logger.error(f"Failed to read log file {log_file}: {e}")
            
        return flow_executions, bypasses
        
    def _extract_timestamp(self, line: str) -> Optional[datetime]:
        """ログ行からタイムスタンプを抽出"""
        # 一般的なログタイムスタンプパターン
        patterns = [
            r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})',
            r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})',
            r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    timestamp_str = match.group(1)
                    # 複数のフォーマットを試行
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%m/%d/%Y %H:%M:%S']:
                        try:
                            return datetime.strptime(timestamp_str, fmt)
                        except:
                            continue
                except:
                    pass
                    
        return None
        
    def _extract_execution_id(self, line: str, task_id: Optional[str] = None) -> str:
        """実行IDを抽出"""
        if task_id:
            return task_id
            
        # ログから実行IDを抽出するパターン
        patterns = [
            r'task[_-]id[:\s]*([a-zA-Z0-9-]+)',
            r'execution[_-]id[:\s]*([a-zA-Z0-9-]+)',
            r'flow[_-]id[:\s]*([a-zA-Z0-9-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)
                
        # デフォルト: タイムスタンプベース
        timestamp = self._extract_timestamp(line)
        if timestamp:
            return f"flow_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
        return f"unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


class SageCouncilValidator:
    """4賢者会議検証エンジン"""
    
    def __init__(self):
        self.required_sages = ["knowledge", "task", "incident", "rag"]
        self.logger = logging.getLogger("SageCouncilValidator")
        
    def validate_sage_consultation(self, 
                                 flow_execution: Dict[str, Any],
                                 sage_logs: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """4賢者相談の妥当性を検証"""
        validation_result = {
            "is_valid": False,
            "consulted_sages": [],
            "missing_sages": [],
            "consultation_quality": {},
            "violations": []
        }
        
        # 基本的なログ解析
        if FlowStage.SAGE_COUNCIL in flow_execution.get("stages", {}):
            stage_info = flow_execution["stages"][FlowStage.SAGE_COUNCIL]
            log_line = stage_info.get("log_line", "")
            
            # 相談された賢者を検出
            consulted = self._detect_consulted_sages(log_line, sage_logs)
            validation_result["consulted_sages"] = consulted
            
            # 不足している賢者
            missing = [sage for sage in self.required_sages if sage not in consulted]
            validation_result["missing_sages"] = missing
            
            # 妥当性判定
            validation_result["is_valid"] = len(missing) == 0
            
            if missing:
                validation_result["violations"].append({
                    "type": FlowViolationType.SKIPPED_SAGE_COUNCIL,
                    "severity": "HIGH",
                    "description": f"Missing consultation with sages: {', '.join(missing)}",
                    "missing_sages": missing
                })
                
            # 相談品質の評価
            validation_result["consultation_quality"] = self._evaluate_consultation_quality(
                log_line, sage_logs, consulted
            )
            
        else:
            # 4賢者会議自体が実行されていない
            validation_result["missing_sages"] = self.required_sages
            validation_result["violations"].append({
                "type": FlowViolationType.SKIPPED_SAGE_COUNCIL,
                "severity": "CRITICAL",
                "description": "No sage council consultation detected",
                "missing_sages": self.required_sages
            })
            
        return validation_result
        
    def _detect_consulted_sages(self, 
                               log_line: str, 
                               sage_logs: Optional[List[Dict]] = None) -> List[str]:
        """相談された賢者を検出"""
        consulted = []
        
        # ログから賢者名を検出
        sage_patterns = {
            "knowledge": [r'knowledge.*sage', r'ナレッジ.*賢者', r'knowledge.*consulted'],
            "task": [r'task.*sage', r'タスク.*賢者', r'task.*consulted'],
            "incident": [r'incident.*sage', r'インシデント.*賢者', r'incident.*consulted'],
            "rag": [r'rag.*sage', r'RAG.*賢者', r'rag.*consulted']
        }
        
        for sage, patterns in sage_patterns.items():
            for pattern in patterns:
                if re.search(pattern, log_line, re.IGNORECASE):
                    consulted.append(sage)
                    break
                    
        # 追加のログ情報からも検出
        if sage_logs:
            for log_entry in sage_logs:
                sage_type = log_entry.get("sage_type", "")
                if sage_type in self.required_sages and sage_type not in consulted:
                    consulted.append(sage_type)
                    
        return list(set(consulted))  # 重複除去
        
    def _evaluate_consultation_quality(self, 
                                     log_line: str,
                                     sage_logs: Optional[List[Dict]], 
                                     consulted_sages: List[str]) -> Dict[str, Any]:
        """相談品質を評価"""
        quality = {
            "overall_score": 0,
            "sage_scores": {},
            "issues": []
        }
        
        if not consulted_sages:
            quality["overall_score"] = 0
            quality["issues"].append("No sages consulted")
            return quality
            
        total_score = 0
        for sage in consulted_sages:
            # 基本スコア（相談した = 25点）
            sage_score = 25
            
            # ログの詳細度評価
            if len(log_line) > 50:  # 詳細なログ
                sage_score += 10
                
            # 実際のレスポンスがある場合（sage_logsから）
            if sage_logs:
                sage_responses = [log for log in sage_logs if log.get("sage_type") == sage]
                if sage_responses:
                    sage_score += 15
                    # レスポンスの品質評価
                    for response in sage_responses:
                        if len(response.get("response", "")) > 100:
                            sage_score += 5  # 詳細なレスポンス
                            
            quality["sage_scores"][sage] = min(50, sage_score)  # 最大50点
            total_score += quality["sage_scores"][sage]
            
        # 全体スコア（4賢者すべてで200点満点）
        quality["overall_score"] = min(100, (total_score / len(self.required_sages)) * 2)
        
        # 品質問題の検出
        if quality["overall_score"] < 50:
            quality["issues"].append("Low consultation quality")
        if len(consulted_sages) < len(self.required_sages):
            quality["issues"].append("Incomplete sage consultation")
            
        return quality


class QualityGateMonitor:
    """品質ゲート監視システム"""
    
    def __init__(self):
        self.logger = logging.getLogger("QualityGateMonitor")
        
        # 品質ゲートのパターン
        self.quality_gate_patterns = [
            re.compile(r'quality.*gate.*passed', re.IGNORECASE),
            re.compile(r'quality.*gate.*failed', re.IGNORECASE),
            re.compile(r'quality.*check.*completed', re.IGNORECASE),
            re.compile(r'quality.*validation.*result', re.IGNORECASE),
        ]
        
        # バイパスパターン
        self.bypass_patterns = [
            re.compile(r'bypassing.*quality.*gate', re.IGNORECASE),
            re.compile(r'quality.*gate.*override', re.IGNORECASE),
            re.compile(r'--no-quality', re.IGNORECASE),
            re.compile(r'emergency.*bypass', re.IGNORECASE),
        ]
        
    def monitor_quality_gates(self, flow_execution: Dict[str, Any]) -> Dict[str, Any]:
        """品質ゲートを監視"""
        monitor_result = {
            "quality_gate_executed": False,
            "quality_gate_passed": None,
            "bypass_detected": False,
            "violations": [],
            "quality_metrics": {}
        }
        
        # 品質ゲート実行の確認
        if FlowStage.QUALITY_GATE in flow_execution.get("stages", {}):
            monitor_result["quality_gate_executed"] = True
            stage_info = flow_execution["stages"][FlowStage.QUALITY_GATE]
            log_line = stage_info.get("log_line", "")
            
            # 成功/失敗の判定
            if re.search(r'passed|success|ok', log_line, re.IGNORECASE):
                monitor_result["quality_gate_passed"] = True
            elif re.search(r'failed|error|failed', log_line, re.IGNORECASE):
                monitor_result["quality_gate_passed"] = False
                
            # バイパス検出
            for pattern in self.bypass_patterns:
                if pattern.search(log_line):
                    monitor_result["bypass_detected"] = True
                    monitor_result["violations"].append({
                        "type": FlowViolationType.BYPASSED_QUALITY_GATE,
                        "severity": "CRITICAL",
                        "description": "Quality gate bypass detected",
                        "log_evidence": log_line
                    })
                    break
                    
        else:
            # 品質ゲートが実行されていない
            monitor_result["violations"].append({
                "type": FlowViolationType.BYPASSED_QUALITY_GATE,
                "severity": "CRITICAL", 
                "description": "Quality gate not executed",
            })
            
        return monitor_result


class FlowComplianceAuditor(AncientElderBase):
    """
    🌊 Elder Flow遵守監査魔法
    
    Elder Flow 5段階フローの完全実行を監査し、
    プロセス遵守違反を検出する
    """
    
    def __init__(self, log_directory: Optional[Path] = None):
        super().__init__("FlowComplianceAuditor")
        
        # コンポーネント初期化
        self.flow_tracer = ElderFlowTracer(log_directory)
        self.sage_validator = SageCouncilValidator()
        self.quality_monitor = QualityGateMonitor()
        
        # 設定
        self.required_stages = [
            FlowStage.SAGE_COUNCIL,
            FlowStage.SERVANT_EXECUTION, 
            FlowStage.QUALITY_GATE,
            FlowStage.COUNCIL_REPORT,
            FlowStage.GIT_AUTOMATION
        ]
        
        self.stage_timeout = {
            FlowStage.SAGE_COUNCIL: timedelta(minutes=5),
            FlowStage.SERVANT_EXECUTION: timedelta(minutes=30),
            FlowStage.QUALITY_GATE: timedelta(minutes=10),
            FlowStage.COUNCIL_REPORT: timedelta(minutes=5),
            FlowStage.GIT_AUTOMATION: timedelta(minutes=5)
        }
        
    async def audit(self, target: Dict[str, Any]) -> AuditResult:
        """
        Elder Flow遵守監査を実行
        
        Args:
            target: 監査対象
                - type: "task", "flow_execution", "time_period"
                - task_id: タスクID（省略可）
                - time_window_hours: 監査対象時間（時間、デフォルト24）
                - execution_id: 特定の実行ID（省略可）
                
        Returns:
            AuditResult: 監査結果
        """
        result = AuditResult()
        result.auditor_name = self.name
        
        target_type = target.get("type", "time_period")
        task_id = target.get("task_id")
        time_window = timedelta(hours=target.get("time_window_hours", 24))
        
        try:
            # フロー実行をトレース
            trace_result = self.flow_tracer.trace_flow_execution(task_id, time_window)
            
            # 各フロー実行を監査
            flow_executions = trace_result.get("flow_executions", {})
            bypasses = trace_result.get("bypasses", [])
            
            if not flow_executions:
                result.add_violation(
                    severity=ViolationSeverity.HIGH,
                    title="No Elder Flow executions detected",
                    description=f"No Elder Flow executions found in the last {time_window}",
                    metadata={
                        "category": "process",
                        "violation_type": FlowViolationType.INCOMPLETE_FLOW,
                        "time_window": str(time_window)
                    }
                )
            else:
                # 各実行を詳細監査
                for execution_id, execution in flow_executions.items():
                    await self._audit_flow_execution(execution_id, execution, result)
                    
            # バイパス違反を処理
            for bypass in bypasses:
                result.add_violation(
                    severity=ViolationSeverity.CRITICAL,
                    title="Elder Flow bypass detected",
                    description=f"Unauthorized bypass: {bypass.get('log_line', '')}",
                    location=f"{bypass.get('log_file', '')}:{bypass.get('line_number', 0)}",
                    metadata={
                        "category": "process", 
                        "violation_type": FlowViolationType.BYPASSED_QUALITY_GATE,
                        "task_id": bypass.get("task_id"),
                        "timestamp": bypass.get("timestamp", datetime.now()).isoformat()
                    }
                )
                
            # メトリクスを計算
            self._calculate_compliance_metrics(result, trace_result)
            
        except Exception as e:
            result.add_violation(
                severity=ViolationSeverity.HIGH,
                title="Flow compliance audit failed",
                description=f"Audit execution failed: {str(e)}",
                metadata={"category": "process", "error": str(e)}
            )
            
        return result
        
    async def _audit_flow_execution(self, 
                                   execution_id: str, 
                                   execution: Dict[str, Any], 
                                   result: AuditResult):
        """個別のフロー実行を監査"""
        stages = execution.get("stages", {})
        task_id = execution.get("task_id", "unknown")
        
        # 必須段階の確認
        missing_stages = [stage for stage in self.required_stages if stage not in stages]
        
        if missing_stages:
            severity = ViolationSeverity.CRITICAL if len(missing_stages) > 2 else ViolationSeverity.HIGH
            result.add_violation(
                severity=severity,
                title="Incomplete Elder Flow execution",
                description=f"Missing stages: {', '.join(missing_stages)}",
                location=f"execution_id:{execution_id}",
                suggested_fix="Execute complete Elder Flow with all 5 stages",
                metadata={
                    "category": "process",
                    "violation_type": FlowViolationType.INCOMPLETE_FLOW,
                    "execution_id": execution_id,
                    "task_id": task_id,
                    "missing_stages": missing_stages,
                    "completed_stages": list(stages.keys())
                }
            )
            
        # 段階実行順序の確認
        self._check_execution_order(execution_id, stages, result)
        
        # 4賢者会議の詳細検証
        if FlowStage.SAGE_COUNCIL in stages:
            sage_validation = self.sage_validator.validate_sage_consultation(execution)
            for violation in sage_validation.get("violations", []):
                result.add_violation(
                    severity=ViolationSeverity.HIGH,
                    title="Sage council violation",
                    description=violation["description"],
                    location=f"execution_id:{execution_id}",
                    metadata={
                        "category": "process",
                        "violation_type": violation["type"],
                        "execution_id": execution_id,
                        "task_id": task_id,
                        "sage_details": sage_validation
                    }
                )
                
        # 品質ゲート監視
        if FlowStage.QUALITY_GATE in stages:
            quality_monitoring = self.quality_monitor.monitor_quality_gates(execution)
            for violation in quality_monitoring.get("violations", []):
                result.add_violation(
                    severity=ViolationSeverity.CRITICAL,
                    title="Quality gate violation",
                    description=violation["description"],
                    location=f"execution_id:{execution_id}",
                    metadata={
                        "category": "process",
                        "violation_type": violation["type"],
                        "execution_id": execution_id,
                        "task_id": task_id,
                        "quality_details": quality_monitoring
                    }
                )
                
        # タイムアウト確認
        self._check_stage_timeouts(execution_id, stages, result)
        
    def _check_execution_order(self, 
                              execution_id: str, 
                              stages: Dict[str, Any], 
                              result: AuditResult):
        """実行順序を確認"""
        if len(stages) < 2:
            return  # 順序チェックには最低2段階必要
            
        # タイムスタンプで段階をソート
        sorted_stages = sorted(
            [(stage, info) for stage, info in stages.items()],
            key=lambda x: x[1].get("timestamp", datetime.min)
        )
        
        # 期待される順序
        expected_order = [
            FlowStage.SAGE_COUNCIL,
            FlowStage.SERVANT_EXECUTION,
            FlowStage.QUALITY_GATE,
            FlowStage.COUNCIL_REPORT,
            FlowStage.GIT_AUTOMATION
        ]
        
        # 実際の順序
        actual_order = [stage for stage, _ in sorted_stages]
        
        # 順序違反をチェック
        for i, stage in enumerate(actual_order):
            if stage in expected_order:
                expected_index = expected_order.index(stage)
                for j in range(i + 1, len(actual_order)):
                    next_stage = actual_order[j]
                    if next_stage in expected_order:
                        next_expected_index = expected_order.index(next_stage)
                        if next_expected_index < expected_index:
                            result.add_violation(
                                severity=ViolationSeverity.MEDIUM,
                                title="Wrong execution order",
                                description=f"Stage '{next_stage}' executed after '{stage}' but should come before",
                                location=f"execution_id:{execution_id}",
                                metadata={
                                    "category": "process",
                                    "violation_type": FlowViolationType.WRONG_EXECUTION_ORDER,
                                    "execution_id": execution_id,
                                    "expected_order": expected_order,
                                    "actual_order": actual_order
                                }
                            )
                            break
                            
    def _check_stage_timeouts(self, 
                             execution_id: str, 
                             stages: Dict[str, Any], 
                             result: AuditResult):
        """段階のタイムアウトを確認"""
        for stage, info in stages.items():
            if stage in self.stage_timeout:
                timestamp = info.get("timestamp")
                if timestamp:
                    elapsed = datetime.now() - timestamp
                    max_duration = self.stage_timeout[stage]
                    
                    if elapsed > max_duration:
                        result.add_violation(
                            severity=ViolationSeverity.MEDIUM,
                            title="Stage timeout violation", 
                            description=f"Stage '{stage}' exceeded maximum duration: {elapsed} > {max_duration}",
                            location=f"execution_id:{execution_id}",
                            metadata={
                                "category": "process",
                                "violation_type": FlowViolationType.TIMEOUT_VIOLATION,
                                "execution_id": execution_id,
                                "stage": stage,
                                "elapsed_time": str(elapsed),
                                "max_duration": str(max_duration)
                            }
                        )
                        
    def _calculate_compliance_metrics(self, result: AuditResult, trace_result: Dict[str, Any]):
        """コンプライアンスメトリクスを計算"""
        flow_executions = trace_result.get("flow_executions", {})
        bypasses = trace_result.get("bypasses", [])
        
        total_executions = len(flow_executions)
        complete_executions = 0
        sage_compliance_rate = 0
        quality_gate_compliance_rate = 0
        
        if total_executions > 0:
            for execution in flow_executions.values():
                stages = execution.get("stages", {})
                
                # 完全実行の判定
                if len(stages) >= 4:  # 最低4段階必要
                    complete_executions += 1
                    
                # 4賢者相談率
                if FlowStage.SAGE_COUNCIL in stages:
                    sage_compliance_rate += 1
                    
                # 品質ゲート実行率
                if FlowStage.QUALITY_GATE in stages:
                    quality_gate_compliance_rate += 1
                    
            # 率を計算
            sage_compliance_rate = (sage_compliance_rate / total_executions) * 100
            quality_gate_compliance_rate = (quality_gate_compliance_rate / total_executions) * 100
            
        # 全体的なコンプライアンススコア
        compliance_score = 100.0
        compliance_score -= len(bypasses) * 20  # バイパス1回につき20点減点
        compliance_score -= (total_executions - complete_executions) * 10  # 不完全実行1回につき10点減点
        compliance_score = max(0, compliance_score)
        
        result.add_metric("compliance_score", compliance_score)
        result.add_metric("total_executions", total_executions)
        result.add_metric("complete_executions", complete_executions)
        result.add_metric("sage_compliance_rate", sage_compliance_rate)
        result.add_metric("quality_gate_compliance_rate", quality_gate_compliance_rate)
        result.add_metric("bypass_count", len(bypasses))
        result.add_metric("logs_analyzed", trace_result.get("logs_analyzed", 0))
        
    def get_audit_scope(self) -> Dict[str, Any]:
        """監査範囲を返す"""
        return {
            "scope": "elder_flow_compliance",
            "targets": [
                "Elder Flow execution logs",
                "4賢者会議の実施確認",
                "エルダーサーバント実行追跡",
                "品質ゲート監視",
                "評議会報告生成",
                "Git自動化プロセス"
            ],
            "required_stages": self.required_stages,
            "violation_types": [
                FlowViolationType.INCOMPLETE_FLOW,
                FlowViolationType.SKIPPED_SAGE_COUNCIL,
                FlowViolationType.BYPASSED_QUALITY_GATE,
                FlowViolationType.MISSING_SERVANT,
                FlowViolationType.NO_COUNCIL_REPORT,
                FlowViolationType.WRONG_EXECUTION_ORDER,
                FlowViolationType.TIMEOUT_VIOLATION
            ],
            "description": "Elder Flow遵守監査魔法 - 5段階フローの完全実行と品質ゲートバイパス防止"
        }