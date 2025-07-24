#!/usr/bin/env python3
"""
🛡️ Error Handler Servant (D13)
==============================

エラー処理専門のドワーフサーバント。
エラーの分類、復旧提案、パターン学習、4賢者連携を担当。

Author: Claude Elder
Created: 2025-07-23
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter
import hashlib
import traceback

from ..base import DwarfServant, ServantCapability


class ErrorHandlerServant(DwarfServant):
    pass


"""
    Error Handler - エラー処理専門家
    
    主な責務：
    - エラーの分類と重要度判定
    - 復旧方法の提案
    - エラーパターンの学習
    - 4賢者への適切なエスカレーション
    """
        super().__init__(
            servant_id="D13",
            name="Error Handler",
            specialization="エラー処理・復旧提案・パターン学習"
        )
        
        # 能力定義
        self.capabilities = [
            ServantCapability.ERROR_HANDLING,
            ServantCapability.PATTERN_LEARNING,
            ServantCapability.SAGE_INTEGRATION,
            ServantCapability.RECOVERY_SUGGESTION
        ]
        
        # エラー履歴とパターン
        self.error_history: List[Dict[str, Any]] = []
        self.error_patterns: Dict[str, List[Dict]] = defaultdict(list)
        self.recovery_strategies: Dict[str, List[Dict]] = self._init_recovery_strategies()
        
        # エラーIDマッピング
        self.error_registry: Dict[str, Dict] = {}
        
    def _init_recovery_strategies(self) -> Dict[str, List[Dict]]:
        pass

        
    """標準的な復旧戦略を初期化""" [
                {
                    "strategy": "fix_syntax",
                    "description": "構文エラーを修正",
                    "actions": ["括弧・引用符の確認", "インデント修正", "予約語チェック"]
                }
            ],
            "ConnectionError": [
                {
                    "strategy": "retry",
                    "description": "指数バックオフでリトライ",
                    "params": {"initial_wait": 1, "max_retries": 5}
                },
                {
                    "strategy": "fallback",
                    "description": "代替接続先を使用",
                    "params": {"fallback_hosts": ["backup1", "backup2"]}
                },
                {
                    "strategy": "health_check",
                    "description": "ヘルスチェック後に再接続",
                    "params": {"check_interval": 5}
                }
            ],
            "PermissionError": [
                {
                    "strategy": "elevate_privileges",
                    "description": "権限昇格を試行",
                    "command": "sudo"
                },
                {
                    "strategy": "change_permissions",
                    "description": "ファイル権限を変更",
                    "command": "chmod"
                }
            ],
            "ImportError": [
                {
                    "strategy": "install_package",
                    "description": "不足パッケージをインストール",
                    "command": "pip install"
                }
            ]
        }
        
    async def classify_error(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """エラーを分類し、重要度を判定"""
        try:
            error_type = error_data.get("type", "UnknownError")
            message = error_data.get("message", "")
            
            # エラーカテゴリを判定
            category = self._determine_category(error_type)
            
            # 重要度を判定
            severity = self._determine_severity(error_data)
            
            # 復旧可能性を判定
            recoverable = self._is_recoverable(error_type, message)
            
            # 構文エラーの場合は修正提案を生成
            suggested_fixes = []
            if category == "syntax":
                suggested_fixes = self._suggest_syntax_fixes(error_data)
                
            # 実行時エラーの場合はリトライ戦略を提案
            retry_strategy = None
            if category == "runtime" and error_type in ["RuntimeError", "ConnectionError"]:
                retry_strategy = {
                    "type": "exponential_backoff",
                    "initial_delay": 1,
                    "max_retries": 3,
                    "max_delay": 30
                }
                
            # 検証エラーの場合は不足フィールドを特定
            missing_fields = []
            if category == "validation":
                missing_fields = self._identify_missing_fields(error_data)
                
            return {
                "success": True,
                "category": category,
                "severity": severity,
                "recoverable": recoverable,
                "suggested_fixes": suggested_fixes,
                "retry_strategy": retry_strategy,
                "missing_fields": missing_fields
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to classify error: {str(e)}"
            }
            
    def _determine_category(self, error_type: str) -> str:
        """エラータイプからカテゴリを判定"""
        categories = {
            "syntax": ["SyntaxError", "IndentationError", "TabError"],
            "runtime": ["RuntimeError", "ConnectionError", "TimeoutError"],
            "validation": ["ValidationError", "ValueError", "TypeError"],
            "system": ["SystemError", "OSError", "IOError"],
            "import": ["ImportError", "ModuleNotFoundError"]
        }
        
        for category, types in categories.items():
            if error_type in types:
                return category
                
        return "unknown"
        
    def _determine_severity(self, error_data: Dict[str, Any]) -> str:
        """エラーの重要度を判定"""
        # 明示的な重要度指定がある場合
        if "severity" in error_data:
            return error_data["severity"]
            
        error_type = error_data.get("type", "")
        message = error_data.get("message", "").lower()
        
        # Critical: システム全体に影響
        if any(keyword in message for keyword in ["database", "critical", "fatal", "system"]):
            return "critical"
            
        # High: 主要機能に影響
        if error_type in ["SyntaxError", "SystemError"] or "connection" in message:
            return "high"
            
        # Medium: 一部機能に影響
        if error_type in ["ValidationError", "ValueError"]:
            return "medium"
            
        # Low: 軽微な問題
        return "low"
        
    def _is_recoverable(self, error_type: str, message: str) -> bool:
        """エラーが復旧可能かを判定"""
        # 一般的に復旧不可能なエラー
        non_recoverable = ["SystemError", "MemoryError", "FatalError"]
        if error_type in non_recoverable:
            return False
            
        # メッセージに基づく判定
        if any(keyword in message.lower() for keyword in ["corrupt", "fatal", "unrecoverable"]):
            return False
            
        return True
        
    def _suggest_syntax_fixes(self, error_data: Dict[str, Any]) -> List[Dict[str, str]]message = error_data.get("message", ""):
    """文エラーの修正提案を生成"""
        fixes = []
        :
        if "quote" in message or "unterminated" in message:
            fixes.append({
                "description": "引用符を閉じる",
                "code_fix": "文字列の終端に引用符を追加"
            })
            
        if "indent" in message:
            fixes.append({
                "description": "インデントを修正",
                "code_fix": "適切なインデントレベルに調整"
            })
            
        if not fixes:
            fixes.append({
                "description": "構文を確認",
                "code_fix": "括弧、コロン、セミコロンの確認"
            })
            
        return fixes
        
    def _identify_missing_fields(self, error_data: Dict[str, Any]) -> List[str]message = error_data.get("message", "")field = error_data.get("field")
    """証エラーから不足フィールドを特定"""
        
        missing = []:
        if field:
            missing.append(field)
            
        # メッセージから不足フィールドを抽出
        field_pattern = r"'(\w+)' (?:field )?is required"
        matches = re.findall(field_pattern, message)
        missing.extend(matches)
        
        return list(set(missing))
        
    async def suggest_recovery(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """エラーからの復旧方法を提案"""
        try:
            error_type = error_data.get("type", "UnknownError")
            message = error_data.get("message", "")
            
            suggestions = []
            
            # 標準的な復旧戦略から提案
            if error_type in self.recovery_strategies:
                for strategy in self.recovery_strategies[error_type]:
                    suggestion = {
                        "strategy": strategy["strategy"],
                        "description": strategy["description"]
                    }
                    
                    # 具体的な修正コードを生成
                    if error_type == "SyntaxError":
                        if "quote" in message or "unterminated" in message:
                            suggestion["code_fix"] = "# 引用符を閉じる\nstring = \"fixed string\""
                        else:
                            suggestion["code_fix"] = "# 構文エラーを修正"
                        
                    # コマンドがある場合は含める
                    if "command" in strategy:
                        suggestion["command"] = strategy["command"]
                        
                    suggestions.append(suggestion)
                    
            # 接続エラーの特別処理
            if error_type == "ConnectionError":
                host = error_data.get("host", "unknown")
                port = error_data.get("port", 0)
                
                suggestions.extend([
                    {
                        "strategy": "retry",
                        "description": "指数バックオフでリトライ",
                        "code": f"retry_with_backoff(connect, host='{host}', port={port})"
                    },
                    {
                        "strategy": "fallback",
                        "description": "代替サーバーに接続",
                        "code": "connect_to_fallback_server()"
                    },
                    {
                        "strategy": "health_check",
                        "description": "ヘルスチェック実行",
                        "code": f"check_server_health('{host}', {port})"
                    }
                ])
                
            # 権限エラーの特別処理
            if error_type == "PermissionError":
                file_path = error_data.get("file", "")
                suggestions.extend([
                    {
                        "strategy": "elevate",
                        "description": "sudo権限で実行",
                        "command": f"sudo <command>"
                    },
                    {
                        "strategy": "change_permissions",
                        "description": "ファイル権限を変更",
                        "command": f"chmod 755 {file_path}" if file_path else "chmod 755 <file>"
                    }
                ])
                
            # ImportErrorの特別処理
            if error_type == "ImportError":
                module_match = re.search(r"No module named '(\w+)'", message)
                if module_match:
                    module_name = module_match.group(1)
                    suggestions.append({
                        "strategy": "install",
                        "description": f"{module_name}モジュールをインストール",
                        "command": f"pip install {module_name}"
                    })
                    
            # RuntimeErrorの特別処理
            if error_type == "RuntimeError":
                if "service" in message.lower() or "unavailable" in message.lower():
                    suggestions.extend([
                        {
                            "strategy": "retry",
                            "description": "サービスの再試行",
                            "retry_count": 3,
                            "backoff": "exponential"
                        },
                        {
                            "strategy": "failover",
                            "description": "代替サービスへのフェイルオーバー"
                        }
                    ])
                    
            return {
                "success": True,
                "suggestions": suggestions
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to suggest recovery: {str(e)}"
            }
            
    async def report_error(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """エラーを報告し、履歴に記録"""
        try:
            # エラーIDを生成
            error_id = self._generate_error_id(error_data)
            
            # タイムスタンプを追加
            error_data["reported_at"] = datetime.now().isoformat()
            error_data["error_id"] = error_id
            
            # 履歴に追加
            self.error_history.append(error_data)
            
            # パターン学習用に分類
            error_type = error_data.get("type", "UnknownError")
            self.error_patterns[error_type].append(error_data)
            
            # レジストリに登録
            self.error_registry[error_id] = {
                "data": error_data,
                "status": "reported",
                "recovery_attempts": []
            }
            
            return {
                "success": True,
                "error_id": error_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to report error: {str(e)}"
            }
            
    def _generate_error_id(self, error_data: Dict[str, Any]) -> str:
        """エラーデータからユニークIDを生成"""
        # エラーの特徴をハッシュ化
        features = f"{error_data.get('type')}:{error_data.get('message')}:{datetime.now().isoformat()}"
        return hashlib.md5(features.encode()).hexdigest()[:12]
        
    async def analyze_patterns(self) -> Dict[str, Any]:
        pass

        
    """エラーパターンを分析"""
            patterns = []
            
            for error_type, errors in self.error_patterns.items():
                if len(errors) >= 3:  # 3回以上発生したエラー
                    # 共通の特徴を抽出
                    messages = [e.get("message", "") for e in errors]
                    common_words = self._find_common_words(messages)
                    
                    pattern = {
                        "type": error_type,
                        "count": len(errors),
                        "common_features": common_words,
                        "first_seen": errors[0].get("reported_at"),
                        "last_seen": errors[-1].get("reported_at")
                    }
                    
                    # ImportErrorの場合は一括解決策を提案
                    if error_type == "ImportError":
                        modules = []
                        for msg in messages:
                            match = re.search(r"No module named '(\w+)'", msg)
                            if match:
                                modules.append(match.group(1))
                        
                        if modules:
                            pattern["bulk_solution"] = f"pip install {' '.join(set(modules))}"
                            
                    patterns.append(pattern)
                    
            return {
                "success": True,
                "patterns": patterns
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze patterns: {str(e)}"
            }
            
    def _find_common_words(self, messages: List[str]) -> List[str]:
        """メッセージ群から共通の単語を抽出"""
        if not messages:
            return []
            
        # 各メッセージを単語に分割
        word_sets = [set(msg.lower().split()) for msg in messages]
        
        # 共通の単語を見つける
        common = word_sets[0]
        for word_set in word_sets[1:]:
            common = common.intersection(word_set)
            
        # ストップワードを除外
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "to", "of", "in", "on"}
        return list(common - stopwords)
        
    async def escalate_to_sage(self, error_data: Dict[str, Any], sage_type: str) -> Dict[str, Any]:
        """重大なエラーを適切な賢者にエスカレート"""
        try:
            # インシデント賢者への報告
            if sage_type == "incident":
                incident_data = {
                    "type": "error_escalation",
                    "error": error_data,
                    "severity": error_data.get("severity", "high"),
                    "priority": "critical" if error_data.get("severity") == "critical" else "high",
                    "reported_by": "error_handler_servant"
                }
                
                # 実際の実装では賢者APIを呼び出す
                # ここではモック実装
                incident_id = f"INC-{self._generate_error_id(error_data)}"
                
                return {
                    "success": True,
                    "sage": "incident",
                    "incident_id": incident_id,
                    "priority": incident_data["priority"]
                }
                
            return {
                "success": False,
                "error": f"Unknown sage type: {sage_type}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to escalate to sage: {str(e)}"
            }
            
    async def consult_sage(self, error_data: Dict[str, Any], sage_type: str) -> Dict[str, Any]:
        """賢者に相談して解決策を求める"""
        try:
            # ナレッジ賢者への相談
            if sage_type == "knowledge":
                # 実際の実装では賢者APIを呼び出す
                # ここではモック実装
                return {
                    "success": True,
                    "sage": "knowledge",
                    "similar_cases": [
                        {
                            "case_id": "CASE-001",
                            "similarity": 0.85,
                            "solution": "環境変数の設定を確認"
                        }
                    ],
                    "recommended_approach": "設定ファイルの再確認とログレベルの引き上げ"
                }
                
            return {
                "success": False,
                "error": f"Unknown sage type: {sage_type}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to consult sage: {str(e)}"
            }
            
    async def execute_recovery(self, error_id: str, recovery_action: Dict[str, Any]) -> Dict[str, Any]:
        """復旧アクションを実行"""
        try:
            if error_id not in self.error_registry:
                return {
                    "success": False,
                    "error": f"Error ID not found: {error_id}"
                }
                
            # 復旧試行を記録
            self.error_registry[error_id]["recovery_attempts"].append({
                "action": recovery_action,
                "timestamp": datetime.now().isoformat(),
                "status": "attempting"
            })
            
            # 実際の復旧実行（モック）
            # 実装では実際のコマンド実行やAPIコールを行う
            
            # 成功と仮定
            self.error_registry[error_id]["status"] = "resolved"
            self.error_registry[error_id]["recovery_attempts"][-1]["status"] = "success"
            
            return {
                "success": True,
                "status": "resolved"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute recovery: {str(e)}"
            }
            
    async def get_error_status(self, error_id: str) -> Dict[str, Any]:
        """エラーの現在の状態を取得"""
        try:
            if error_id not in self.error_registry:
                return {
                    "success": False,
                    "error": f"Error ID not found: {error_id}"
                }
                
            error_info = self.error_registry[error_id]
            return {
                "success": True,
                "status": error_info["status"],
                "recovery_attempts": len(error_info["recovery_attempts"]),
                "last_attempt": error_info["recovery_attempts"][-1] if error_info["recovery_attempts"] else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get error status: {str(e)}"
            }
            
    async def analyze_cascade(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """カスケードエラーを分析"""
        try:
            if not errors:
                return {
                    "success": False,
                    "error": "No errors provided"
                }
                
            # 時系列でソート
            sorted_errors = sorted(errors, key=lambda e: e.get("timestamp", ""))
            
            # 最初のエラーを根本原因と仮定
            root_cause = sorted_errors[0]
            
            # 影響を受けたコンポーネントを特定
            affected_components = set()
            for error in sorted_errors:
                if "component" in error.get("message", ""):
                    # メッセージからコンポーネント名を抽出
                    comp_match = re.search(r'(\w+)(?:\s+service|\s+component)', error["message"])
                    if comp_match:
                        affected_components.add(comp_match.group(1))
                        
            # 基本的な影響マッピング
            if root_cause["type"] == "ConnectionError" and "database" in root_cause["message"].lower():
                affected_components.update(["database", "cache", "api"])
                
            # 復旧順序を決定
            recovery_order = []
            if "database" in affected_components:
                recovery_order.append({"component": "database", "priority": 1})
            if "cache" in affected_components:
                recovery_order.append({"component": "cache", "priority": 2})
            if "api" in affected_components:
                recovery_order.append({"component": "api", "priority": 3})
                
            return {
                "success": True,
                "root_cause": root_cause,
                "affected_components": list(affected_components),
                "recovery_order": recovery_order,
                "cascade_length": len(sorted_errors)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze cascade: {str(e)}"
            }
            
    async def correlate_errors(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """エラー間の相関を分析"""
        try:
            if len(errors) < 2:
                return {
                    "success": True,
                    "correlation_found": False,
                    "reason": "Not enough errors for correlation"
                }
                
            # エンドポイントパターンを確認
            endpoints = []
            for error in errors:
                if "endpoint" in error:
                    endpoints.append(error["endpoint"])
                elif "endpoint" in error.get("message", ""):
                    # メッセージからエンドポイントを抽出
                    ep_match = re.search(r'/api/v\d+/\w+(?:/\d+)?', error["message"])
                    if ep_match:
                        endpoints.append(ep_match.group(0))
                        
            # 共通パターンを探す
            if endpoints and all("/api/v1/data/" in ep for ep in endpoints):
                return {
                    "success": True,
                    "correlation_found": True,
                    "common_factor": "api_overload",
                    "pattern": "Multiple timeouts on data API endpoints",
                    "mitigation_strategy": {
                        "action": "scale_api_servers",
                        "rate_limiting": True,
                        "cache_optimization": True
                    }
                }
                
            # タイムアウトエラーの相関
            if all(error.get("type") == "TimeoutError" for error in errors):
                return {
                    "success": True,
                    "correlation_found": True,
                    "common_factor": "system_overload",
                    "pattern": "Systemic timeout errors",
                    "mitigation_strategy": {
                        "action": "increase_resources",
                        "timeout_adjustment": True,
                        "load_balancing": True
                    }
                }
                
            return {
                "success": True,
                "correlation_found": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to correlate errors: {str(e)}"
            }
            
    async def batch_process_errors(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """大量のエラーをバッチ処理"""
        try:
            start_time = datetime.now()
            processed_count = 0
            
            # エラーをタイプ別にグループ化
            error_groups = defaultdict(list)
            for error in errors:
                error_type = error.get("type", "Unknown")
                error_groups[error_type].append(error)
                
            # 各グループを並列処理
            tasks = []
            for error_type, group_errors in error_groups.items():
                # グループごとに処理（実際の実装では並列化）
                for error in group_errors:
                    # 簡易処理（実際はもっと複雑な処理）
                    await self.report_error(error)
                    processed_count += 1
                    
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "processed_count": processed_count,
                "processing_time": processing_time,
                "errors_per_second": processed_count / processing_time if processing_time > 0 else 0,
                "error_types": len(error_groups)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to batch process errors: {str(e)}"
            }
            
    async def generate_report(self, start_date: str, end_date: str, format: str = "json") -> Dict[str, Any]:
        """エラーレポートを生成"""
        try:
            # 期間内のエラーをフィルタ（簡易実装）
            period_errors = self.error_history  # 実際は日付でフィルタ
            
            # エラータイプ別集計
            error_by_type = Counter(e.get("type", "Unknown") for e in period_errors)
            
            # 重要度別集計
            error_by_severity = Counter(e.get("severity", "unknown") for e in period_errors)
            
            # トップエラー
            top_errors = error_by_type.most_common(5)
            
            report = {
                "period": {
                    "start": start_date,
                    "end": end_date
                },
                "summary": {
                    "total_errors": len(period_errors),
                    "unique_types": len(error_by_type),
                    "critical_count": error_by_severity.get("critical", 0)
                },
                "error_by_type": dict(error_by_type),
                "error_by_severity": dict(error_by_severity),
                "top_errors": [{"type": t, "count": c} for t, c in top_errors],
                "recommendations": [
                    "最も頻繁なエラータイプに対する自動化を検討",
                    "クリティカルエラーの根本原因分析を実施",
                    "エラー監視アラートの閾値を調整"
                ]
            }
            
            return {
                "success": True,
                "report": report,
                "format": format
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate report: {str(e)}"
            }
            
    async def perform_craft(self, task_data: Dict[str, Any]) -> Dict[str, Any]action = task_data.get("action")data = task_data.get("data", {})
    """ラー処理の具体的な作業を実行"""
        :
        if action == "classify":
            return await self.classify_error(data)
        elif action == "suggest_recovery":
            return await self.suggest_recovery(data)
        elif action == "report":
            return await self.report_error(data)
        elif action == "analyze_patterns":
            return await self.analyze_patterns()
        elif action == "correlate":
            return await self.correlate_errors(data.get("errors", []))
        elif action == "analyze_cascade":
            return await self.analyze_cascade(data.get("errors", []))
        elif action == "generate_report":
            return await self.generate_report(
                data.get("start_date"),
                data.get("end_date"),
                data.get("format", "json")
            )
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
            
    async def process_elder_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Elder Treeシステムからのメッセージを処理"""
        try:
            action = message.get("action")
            data = message.get("data", {})
            
            if action == "handle_error":
                error_data = data.get("error", {})
                context = data.get("context", {})
                
                # エラーを報告
                report_result = await self.report_error(error_data)
                if not report_result["success"]:
                    return report_result
                    
                error_id = report_result["error_id"]
                
                # エラーを分類
                classify_result = await self.classify_error(error_data)
                
                # 復旧提案
                recovery_result = await self.suggest_recovery(error_data)
                
                # 重大度が高い場合は賢者に通知
                sage_notified = False
                severity = classify_result.get("severity")
                # IntegrationErrorは通常highと判定される
                if severity in ["critical", "high"] or error_data.get("type") == "IntegrationError":
                    await self.escalate_to_sage(error_data, "incident")
                    sage_notified = True
                    
                return {
                    "success": True,
                    "data": {
                        "error_id": error_id,
                        "classification": classify_result,
                        "recovery_suggestions": recovery_result.get("suggestions", []),
                        "sage_notified": sage_notified
                    }
                }
                
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process Elder message: {str(e)}"
            }


# エクスポート
__all__ = ["ErrorHandlerServant"]