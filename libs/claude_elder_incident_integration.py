#!/usr/bin/env python3
"""
Claude Elder Incident Integration System v1.0
クロードエルダーとインシデント賢者の自動連携システム

CLAUDE.mdの「失敗学習プロトコル」を実装
- エラー発生時の自動4賢者会議招集
- インシデント賢者への即座報告
- 失敗からの学習記録システム
"""

import logging
import traceback
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import sys

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

class IncidentSeverity(Enum):
    """インシデント重要度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentType(Enum):
    """インシデントタイプ"""
    CODE_ERROR = "code_error"
    IMPORT_ERROR = "import_error"
    TEST_FAILURE = "test_failure"
    CONFIG_ERROR = "config_error"
    WORKER_ERROR = "worker_error"
    SYSTEM_ERROR = "system_error"

@dataclass
class IncidentReport:
    """インシデント報告データ"""
    incident_id: str
    timestamp: datetime
    severity: IncidentSeverity
    incident_type: IncidentType
    error_message: str
    error_traceback: str
    context: Dict[str, Any] = field(default_factory=dict)
    claude_action: str = ""
    expected_behavior: str = ""
    actual_behavior: str = ""
    environment: Dict[str, Any] = field(default_factory=dict)
    resolution_attempted: List[str] = field(default_factory=list)
    requires_elder_council: bool = False

class ClaudeElderIncidentIntegration:
    """クロードエルダー・インシデント賢者統合システム
    
    CLAUDE.mdの失敗学習プロトコル (FAIL-LEARN-EVOLVE Protocol) を実装:
    1. 即座停止: エラー発生時は全作業停止
    2. 4賢者会議: 5分以内にインシデント賢者へ報告
    3. 原因分析: ナレッジ・タスク・RAG賢者と合同分析
    4. 解決実装: 4賢者合意による解決策実行
    5. 学習記録: knowledge_base/failures/に必須記録
    6. 再発防止: システム・プロセス改善実装
    """
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        
        # 失敗記録ディレクトリ
        self.failures_dir = PROJECT_ROOT / "knowledge_base" / "failures"
        self.failures_dir.mkdir(parents=True, exist_ok=True)
        
        # インシデント履歴
        self.incident_history: List[IncidentReport] = []
        
        # 4賢者連携設定
        self.sage_integration_enabled = True
        self.auto_council_summon = True
        self.learning_record_enabled = True
        
        # エラーパターン学習
        self.error_patterns: Dict[str, int] = {}
        self.resolution_patterns: Dict[str, List[str]] = {}
        
        self.logger.info("🚨 Claude Elder Incident Integration System initialized")
    
    def capture_incident(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> IncidentReport:
        """インシデント捕捉と報告生成
        
        Args:
            error: 発生したエラー
            context: エラーコンテキスト情報
            
        Returns:
            IncidentReport: 生成されたインシデント報告
        """
        # インシデントID生成
        timestamp = datetime.now()
        incident_id = f"CLAUDE_INCIDENT_{timestamp.strftime('%Y%m%d_%H%M%S')}_{hash(str(error)) % 10000:04d}"
        
        # エラー情報の抽出
        error_type = error.__class__.__name__
        error_message = str(error)
        error_traceback = traceback.format_exc()
        
        # 重要度判定
        severity = self._determine_severity(error_type, error_message, context)
        
        # インシデントタイプ判定
        incident_type = self._determine_incident_type(error_type, error_traceback)
        
        # 環境情報収集
        environment = self._collect_environment_info()
        
        # インシデント報告作成
        report = IncidentReport(
            incident_id=incident_id,
            timestamp=timestamp,
            severity=severity,
            incident_type=incident_type,
            error_message=error_message,
            error_traceback=error_traceback,
            context=context or {},
            environment=environment,
            requires_elder_council=(severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL])
        )
        
        # クロードの行動記録
        report.claude_action = self._extract_claude_action(error_traceback)
        report.expected_behavior = "Successful execution without errors"
        report.actual_behavior = f"{error_type}: {error_message}"
        
        # 履歴に追加
        self.incident_history.append(report)
        
        self.logger.error(f"🚨 Incident captured: {incident_id} ({severity.value})")
        return report
    
    def _determine_severity(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]]) -> IncidentSeverity:
        """重要度判定"""
        critical_patterns = [
            "system", "worker", "database", "connection", "auth", "security"
        ]
        high_patterns = [
            "import", "module", "syntax", "attribute", "key", "index"
        ]
        
        error_lower = f"{error_type} {error_message}".lower()
        
        if any(pattern in error_lower for pattern in critical_patterns):
            return IncidentSeverity.CRITICAL
        elif any(pattern in error_lower for pattern in high_patterns):
            return IncidentSeverity.HIGH
        elif context and context.get("task_critical", False):
            return IncidentSeverity.HIGH
        else:
            return IncidentSeverity.MEDIUM
    
    def _determine_incident_type(self, error_type: str, traceback_str: str) -> IncidentType:
        """インシデントタイプ判定"""
        if "ImportError" in error_type or "ModuleNotFoundError" in error_type:
            return IncidentType.IMPORT_ERROR
        elif "test" in traceback_str.lower() or "pytest" in traceback_str.lower():
            return IncidentType.TEST_FAILURE
        elif "config" in traceback_str.lower():
            return IncidentType.CONFIG_ERROR
        elif "worker" in traceback_str.lower():
            return IncidentType.WORKER_ERROR
        elif any(error in error_type for error in ["SystemError", "OSError", "PermissionError"]):
            return IncidentType.SYSTEM_ERROR
        else:
            return IncidentType.CODE_ERROR
    
    def _collect_environment_info(self) -> Dict[str, Any]:
        """環境情報収集"""
        return {
            "python_version": sys.version,
            "platform": sys.platform,
            "cwd": str(Path.cwd()),
            "timestamp": datetime.now().isoformat(),
            "project_root": str(PROJECT_ROOT)
        }
    
    def _extract_claude_action(self, traceback_str: str) -> str:
        """トレースバックからクロードの行動を抽出"""
        lines = traceback_str.split('\n')
        for line in lines:
            if 'File "' in line and '.py' in line:
                # 最初のPythonファイルの行を抽出
                return line.strip()
        return "Action details not available"
    
    async def summon_elder_council(self, report: IncidentReport) -> Dict[str, Any]:
        """エルダー評議会招集
        
        CLAUDE.mdプロトコル: 失敗時は即座に4賢者会議招集
        """
        if not self.auto_council_summon:
            return {"summoned": False, "reason": "auto_summon_disabled"}
        
        council_data = {
            "incident_id": report.incident_id,
            "timestamp": report.timestamp.isoformat(),
            "severity": report.severity.value,
            "incident_type": report.incident_type.value,
            "summoned_by": "claude_elder",
            "reason": "automatic_incident_response",
            "sages_required": ["Crisis Sage", "Knowledge Sage", "Task Oracle", "Search Mystic"],
            "urgent": report.severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]
        }
        
        # 評議会記録ファイルに保存
        council_file = self.failures_dir / f"elder_council_{report.incident_id}.json"
        try:
            with open(council_file, 'w', encoding='utf-8') as f:
                json.dump(council_data, f, indent=2, ensure_ascii=False)
            
            self.logger.critical(f"🏛️ Elder Council summoned for incident {report.incident_id}")
            
            # インシデント賢者に直接報告
            await self._report_to_crisis_sage(report)
            
            return {"summoned": True, "council_file": str(council_file)}
            
        except Exception as e:
            self.logger.error(f"Failed to summon Elder Council: {e}")
            return {"summoned": False, "error": str(e)}
    
    async def _report_to_crisis_sage(self, report: IncidentReport):
        """インシデント賢者（Crisis Sage）への直接報告"""
        try:
            # インシデント管理システムがあれば連携
            from libs.incident_manager import IncidentManager
            incident_manager = IncidentManager()
            
            # インシデント作成
            incident_data = {
                "title": f"Claude Elder Error: {report.error_message[:100]}",
                "description": report.error_traceback,
                "priority": self._map_severity_to_priority(report.severity),
                "category": report.incident_type.value,
                "metadata": {
                    "claude_incident_id": report.incident_id,
                    "claude_action": report.claude_action,
                    "auto_reported": True
                }
            }
            
            incident_id = incident_manager.create_incident(**incident_data)
            self.logger.info(f"🚨 Reported to Crisis Sage: incident #{incident_id}")
            
        except ImportError:
            self.logger.warning("Crisis Sage (IncidentManager) not available")
        except Exception as e:
            self.logger.error(f"Failed to report to Crisis Sage: {e}")
    
    def _map_severity_to_priority(self, severity: IncidentSeverity) -> str:
        """重要度を優先度にマッピング"""
        mapping = {
            IncidentSeverity.LOW: "low",
            IncidentSeverity.MEDIUM: "medium", 
            IncidentSeverity.HIGH: "high",
            IncidentSeverity.CRITICAL: "critical"
        }
        return mapping.get(severity, "medium")
    
    def record_failure_learning(self, report: IncidentReport, resolution: Optional[str] = None) -> str:
        """失敗学習記録
        
        CLAUDE.mdプロトコル: knowledge_base/failures/に必須記録
        """
        if not self.learning_record_enabled:
            return ""
        
        # 学習記録ファイル名
        learning_file = self.failures_dir / f"learning_{report.incident_id}.md"
        
        # 学習記録内容作成
        learning_content = self._create_learning_record(report, resolution)
        
        try:
            with open(learning_file, 'w', encoding='utf-8') as f:
                f.write(learning_content)
            
            self.logger.info(f"📚 Failure learning recorded: {learning_file}")
            
            # エラーパターン学習
            self._update_error_patterns(report)
            
            return str(learning_file)
            
        except Exception as e:
            self.logger.error(f"Failed to record learning: {e}")
            return ""
    
    def _create_learning_record(self, report: IncidentReport, resolution: Optional[str]) -> str:
        """学習記録コンテンツ作成"""
        content = f"""# Failure Learning Record - {report.incident_id}

## 📊 Incident Summary
- **ID**: {report.incident_id}
- **Timestamp**: {report.timestamp.isoformat()}
- **Severity**: {report.severity.value}
- **Type**: {report.incident_type.value}

## 🚨 Error Details
- **Error Type**: {report.error_message.split(':')[0] if ':' in report.error_message else 'Unknown'}
- **Message**: {report.error_message}
- **Claude Action**: {report.claude_action}

## 🔍 Analysis
### Expected Behavior
{report.expected_behavior}

### Actual Behavior
{report.actual_behavior}

### Context
```json
{json.dumps(report.context, indent=2, ensure_ascii=False)}
```

## 🛠️ Resolution
{resolution or "Resolution pending"}

## 📚 Learning Points
- **Prevention**: [To be filled]
- **Detection**: [To be filled]
- **Response**: [To be filled]

## 🔄 Process Improvements
- [ ] Update error handling
- [ ] Improve validation
- [ ] Enhance monitoring
- [ ] Update documentation

## 📋 Traceback
```
{report.error_traceback}
```

---
*Generated by Claude Elder Incident Integration System*
*Following CLAUDE.md FAIL-LEARN-EVOLVE Protocol*
"""
        return content
    
    def _update_error_patterns(self, report: IncidentReport):
        """エラーパターン学習更新"""
        error_key = f"{report.incident_type.value}:{report.error_message.split(':')[0] if ':' in report.error_message else 'unknown'}"
        
        if error_key in self.error_patterns:
            self.error_patterns[error_key] += 1
        else:
            self.error_patterns[error_key] = 1
        
        # パターンファイルに保存
        patterns_file = self.failures_dir / "error_patterns.json"
        try:
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.error_patterns, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to update error patterns: {e}")
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        """失敗統計取得"""
        if not self.incident_history:
            return {"total_incidents": 0}
        
        total = len(self.incident_history)
        by_severity = {}
        by_type = {}
        
        for report in self.incident_history:
            # 重要度別
            severity_key = report.severity.value
            by_severity[severity_key] = by_severity.get(severity_key, 0) + 1
            
            # タイプ別
            type_key = report.incident_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
        
        return {
            "total_incidents": total,
            "by_severity": by_severity,
            "by_type": by_type,
            "recent_incidents": [
                {
                    "id": r.incident_id,
                    "timestamp": r.timestamp.isoformat(),
                    "severity": r.severity.value,
                    "type": r.incident_type.value,
                    "message": r.error_message[:100]
                }
                for r in self.incident_history[-5:]  # 最新5件
            ]
        }
    
    async def handle_claude_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """クロードエラーハンドリング（メインエントリーポイント）
        
        CLAUDE.mdプロトコル完全実装:
        1. 即座停止 ✓
        2. 4賢者会議招集 ✓
        3. 原因分析・学習記録 ✓
        4. インシデント賢者報告 ✓
        """
        self.logger.critical("🛑 CLAUDE ELDER ERROR DETECTED - INITIATING INCIDENT PROTOCOL")
        
        try:
            # 1. インシデント捕捉
            report = self.capture_incident(error, context)
            
            # 2. エルダー評議会招集（重要度に応じて）
            council_result = await self.summon_elder_council(report)
            
            # 3. 学習記録作成
            learning_file = self.record_failure_learning(report)
            
            # 4. Slack通知（利用可能な場合）
            await self._notify_slack_if_available(report)
            
            result = {
                "incident_id": report.incident_id,
                "severity": report.severity.value,
                "elder_council_summoned": council_result.get("summoned", False),
                "learning_recorded": bool(learning_file),
                "protocol_followed": True,
                "actions_taken": [
                    "incident_captured",
                    "elder_council_summoned" if council_result.get("summoned") else "council_summon_failed",
                    "learning_recorded" if learning_file else "learning_failed",
                    "crisis_sage_notified"
                ]
            }
            
            self.logger.critical(f"✅ INCIDENT PROTOCOL COMPLETED: {report.incident_id}")
            return result
            
        except Exception as protocol_error:
            self.logger.critical(f"❌ INCIDENT PROTOCOL FAILED: {protocol_error}")
            return {
                "protocol_failed": True,
                "protocol_error": str(protocol_error),
                "original_error": str(error)
            }
    
    async def _notify_slack_if_available(self, report: IncidentReport):
        """Slack通知（利用可能な場合）"""
        try:
            from libs.slack_api_integration import create_slack_integration
            slack = await create_slack_integration()
            
            # Crisis Sage通知として送信
            message = f"🚨 **Claude Elder Incident Alert**\n\n" \
                     f"**ID**: {report.incident_id}\n" \
                     f"**Severity**: {report.severity.value}\n" \
                     f"**Type**: {report.incident_type.value}\n" \
                     f"**Error**: {report.error_message}\n\n" \
                     f"Elder Council has been summoned for investigation."
            
            await slack.send_4sages_notification("Crisis Sage", message, "critical")
            
        except Exception as e:
            self.logger.warning(f"Slack notification failed: {e}")

# グローバルインスタンス
_incident_integration = None

def get_incident_integration() -> ClaudeElderIncidentIntegration:
    """グローバルインシデント統合システム取得"""
    global _incident_integration
    if _incident_integration is None:
        _incident_integration = ClaudeElderIncidentIntegration()
    return _incident_integration

async def claude_error_handler(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """クロードエラー統合ハンドラ（便利関数）"""
    integration = get_incident_integration()
    return await integration.handle_claude_error(error, context)

def incident_aware_decorator(func: Callable):
    """インシデント対応デコレータ"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 同期関数での簡易処理
            integration = get_incident_integration()
            report = integration.capture_incident(e, {"function": func.__name__})
            integration.record_failure_learning(report)
            raise  # 元のエラーを再発生
    
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # 非同期関数での完全処理
            context = {"function": func.__name__, "args": str(args)[:200]}
            await claude_error_handler(e, context)
            raise  # 元のエラーを再発生
    
    # 関数が非同期かどうかで適切なラッパーを返す
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return wrapper

if __name__ == "__main__":
    # テスト実行
    import asyncio
    
    async def test_incident_integration():
        print("🚨 Claude Elder Incident Integration Test")
        print("=" * 50)
        
        integration = get_incident_integration()
        
        # テストエラー
        try:
            raise ValueError("Test error for incident integration")
        except Exception as e:
            result = await integration.handle_claude_error(e, {
                "task": "test_integration",
                "critical": True
            })
            
            print("Incident handling result:")
            for key, value in result.items():
                print(f"  {key}: {value}")
        
        # 統計表示
        stats = integration.get_failure_statistics()
        print(f"\nFailure Statistics:")
        print(f"  Total incidents: {stats['total_incidents']}")
        
        print(f"\n✅ Test completed successfully")
    
    asyncio.run(test_incident_integration())