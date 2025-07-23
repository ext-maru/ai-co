#!/usr/bin/env python3
"""
Claude Elder Rule Enforcement System v1.0
クロードエルダーのルール遵守を強制するシステム

🧙‍♂️ 4賢者協議による設計:
- 📚 ナレッジ賢者: ルールパターンの学習と蓄積
- 📋 タスク賢者: ワークフロー強制と進捗管理
- 🚨 インシデント賢者: 違反検知と即座対応
- 🔍 RAG賢者: 最新のベストプラクティス適用
"""

import asyncio
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# エルダーズシステムのインポート
try:
    from .claude_elder_error_wrapper import get_error_wrapper, incident_aware
    from .claude_elder_incident_integration import get_incident_integration
    from .claude_task_tracker import ClaudeTaskTracker
    from .github_flow_manager import GitHubFlowManager
except ImportError:
    # フォールバック（直接実行時）
    sys.path.append(str(Path(__file__).parent))
    from claude_elder_error_wrapper import get_error_wrapper, incident_aware
    from claude_elder_incident_integration import get_incident_integration
    from claude_task_tracker import ClaudeTaskTracker
    from github_flow_manager import GitHubFlowManager

logger = logging.getLogger(__name__)


@dataclass
class RuleViolation:
    """ルール違反記録"""

    rule_id: str
    description: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    auto_fixable: bool = False
    fix_applied: bool = False


@dataclass
class RuleDefinition:
    """ルール定義"""

    rule_id: str
    name: str
    description: str
    category: str  # GITHUB_FLOW, INCIDENT_RESPONSE, TASK_MANAGEMENT, GENERAL
    severity: str
    auto_fix: Optional[Callable] = None
    validator: Optional[Callable] = None
    enabled: bool = True


class ClaudeElderRuleEnforcementSystem:
    """クロードエルダー ルール遵守強制システム"""

    def __init__(self, project_dir:
        """初期化メソッド"""
    str = "/home/aicompany/ai_co"):
        self.project_dir = Path(project_dir)
        self.rules_config = self.project_dir / "config" / "elder_rules.json"
        self.violation_log = self.project_dir / "logs" / "rule_violations.json"
        self.auto_fix_log = self.project_dir / "logs" / "auto_fixes.json"

        # 4賢者システム統合
        self.task_tracker = ClaudeTaskTracker()
        self.github_flow = GitHubFlowManager()
        self.incident_integration = get_incident_integration()
        self.error_wrapper = get_error_wrapper()

        # ルール定義
        self.rules = self._initialize_rules()
        self.violations = []
        self.monitoring_active = False

        # ログディレクトリ作成
        self.violation_log.parent.mkdir(exist_ok=True)

        logger.info("🛡️ Claude Elder Rule Enforcement System 初期化完了")

    def _initialize_rules(self) -> Dict[str, RuleDefinition]:
        """ルール定義の初期化"""
        rules = {}

        # GitHub Flow ルール
        rules["GITHUB_FLOW_001"] = RuleDefinition(
            rule_id="GITHUB_FLOW_001",
            name="機能実装後の即座コミット",
            description="機能実装完了後、5分以内にコミットを実行する",
            category="GITHUB_FLOW",
            severity="HIGH",
            auto_fix=self._auto_fix_commit,
            validator=self._validate_commit_timing,
        )

        rules["GITHUB_FLOW_002"] = RuleDefinition(
            rule_id="GITHUB_FLOW_002",
            name="コミット後の即座プッシュ",
            description="コミット後、2分以内にプッシュを実行する",
            category="GITHUB_FLOW",
            severity="HIGH",
            auto_fix=self._auto_fix_push,
            validator=self._validate_push_timing,
        )

        # インシデント対応ルール
        rules["INCIDENT_001"] = RuleDefinition(
            rule_id="INCIDENT_001",
            name="インシデント賢者への事前相談",
            description="コード変更前にインシデント賢者への相談を必須とする",
            category="INCIDENT_RESPONSE",
            severity="CRITICAL",
            auto_fix=self._auto_fix_incident_consultation,
            validator=self._validate_incident_consultation,
        )

        rules["INCIDENT_002"] = RuleDefinition(
            rule_id="INCIDENT_002",
            name="失敗時の4賢者会議招集",
            description="エラー発生時、5分以内に4賢者会議を招集する",
            category="INCIDENT_RESPONSE",
            severity="CRITICAL",
            auto_fix=self._auto_fix_sage_meeting,
            validator=self._validate_sage_meeting_timing,
        )

        # タスク管理ルール
        rules["TASK_001"] = RuleDefinition(
            rule_id="TASK_001",
            name="タスクエルダーとの定期連携",
            description="30分毎にタスクエルダーとの連携確認を実行する",
            category="TASK_MANAGEMENT",
            severity="MEDIUM",
            auto_fix=self._auto_fix_task_sync,
            validator=self._validate_task_sync,
        )

        return rules

    def start_monitoring(self):
        """監視開始"""
        self.monitoring_active = True
        logger.info("🔍 Claude Elder Rule Monitoring 開始")

        # 定期チェックを開始
        asyncio.create_task(self._periodic_rule_check())

    def stop_monitoring(self):
        """監視停止"""
        self.monitoring_active = False
        logger.info("⏹️ Claude Elder Rule Monitoring 停止")

    async def _periodic_rule_check(self):
        """定期的なルールチェック"""
        while self.monitoring_active:
            await self._check_all_rules()
            await asyncio.sleep(60)  # 1分間隔

    async def _check_all_rules(self):
        """すべてのルールをチェック"""
        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue

            try:
                if rule.validator:
                    is_valid = await self._safe_validate(rule.validator)
                    if not is_valid:
                        await self._handle_rule_violation(rule)
            except Exception as e:
                logger.error(f"ルール検証エラー {rule_id}: {e}")

    async def _safe_validate(self, validator: Callable) -> bool:
        """安全なバリデーション実行"""
        try:
            if asyncio.iscoroutinefunction(validator):
                return await validator()
            else:
                return validator()
        except Exception as e:
            logger.error(f"バリデーション実行エラー: {e}")
            return True  # エラー時は違反と見なさない

    async def _handle_rule_violation(self, rule: RuleDefinition):
        """ルール違反の処理"""
        violation = RuleViolation(
            rule_id=rule.rule_id,
            description=rule.description,
            severity=rule.severity,
            auto_fixable=rule.auto_fix is not None,
        )

        self.violations.append(violation)
        self._log_violation(violation)

        # 重要度に応じた対応
        if rule.severity == "CRITICAL":
            await self._critical_violation_response(rule, violation)
        elif rule.severity == "HIGH":
            await self._high_violation_response(rule, violation)
        else:
            await self._standard_violation_response(rule, violation)

    async def _critical_violation_response(
        self, rule: RuleDefinition, violation: RuleViolation
    ):
        """重要違反への対応"""
        logger.critical(f"🚨 重要ルール違反: {rule.name}")

        # 4賢者会議の緊急招集
        await self._emergency_sage_meeting(rule, violation)

        # 自動修正の試行
        if rule.auto_fix:
            await self._attempt_auto_fix(rule, violation)

    async def _high_violation_response(
        self, rule: RuleDefinition, violation: RuleViolation
    ):
        """高重要度違反への対応"""
        logger.warning(f"⚠️ 高重要度ルール違反: {rule.name}")

        # インシデント賢者への報告
        await self._report_to_incident_sage(rule, violation)

        # 自動修正の試行
        if rule.auto_fix:
            await self._attempt_auto_fix(rule, violation)

    async def _standard_violation_response(
        self, rule: RuleDefinition, violation: RuleViolation
    ):
        """標準違反への対応"""
        logger.info(f"📋 ルール違反: {rule.name}")

        # タスク賢者への通知
        self._notify_task_sage(rule, violation)

        # 自動修正の試行
        if rule.auto_fix:
            await self._attempt_auto_fix(rule, violation)

    async def _emergency_sage_meeting(
        self, rule: RuleDefinition, violation: RuleViolation
    ):
        """緊急4賢者会議招集"""
        meeting_data = {
            "type": "emergency_rule_violation",
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "violation_time": violation.timestamp.isoformat(),
            "severity": violation.severity,
            "context": violation.context,
        }

        # インシデント統合システムを通じて会議招集
        await self.incident_integration.summon_elder_council(meeting_data)
        logger.info("🏛️ 緊急4賢者会議を招集しました")

    async def _report_to_incident_sage(
        self, rule: RuleDefinition, violation: RuleViolation
    ):
        """インシデント賢者への報告"""
        report_data = {
            "type": "rule_violation_report",
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "violation_time": violation.timestamp.isoformat(),
            "severity": violation.severity,
            "auto_fix_attempted": False,
        }

        # インシデント統合システムを通じて報告
        try:
            await self.incident_integration.report_incident(
                "rule_violation", report_data
            )
            logger.info("🚨 インシデント賢者への報告完了")
        except Exception as e:
            logger.error(f"インシデント報告エラー: {e}")

    def _notify_task_sage(self, rule: RuleDefinition, violation: RuleViolation):
        """タスク賢者への通知"""
        try:
            self.task_tracker.update_progress(
                f"ルール違反検知: {rule.name}",
                files_affected=["rule_enforcement_system"],
            )
            logger.info("📋 タスク賢者への通知完了")
        except Exception as e:
            logger.error(f"タスク賢者通知エラー: {e}")

    async def _attempt_auto_fix(self, rule: RuleDefinition, violation: RuleViolation):
        """自動修正の試行"""
        if not rule.auto_fix:
            return

        try:
            logger.info(f"🔧 自動修正開始: {rule.name}")

            if asyncio.iscoroutinefunction(rule.auto_fix):
                success = await rule.auto_fix()
            else:
                success = rule.auto_fix()

            if success:
                violation.fix_applied = True
                self._log_auto_fix(rule, violation, success=True)
                logger.info(f"✅ 自動修正成功: {rule.name}")
            else:
                self._log_auto_fix(rule, violation, success=False)
                logger.warning(f"❌ 自動修正失敗: {rule.name}")

        except Exception as e:
            self._log_auto_fix(rule, violation, success=False, error=str(e))
            logger.error(f"自動修正エラー {rule.name}: {e}")

    def _log_violation(self, violation: RuleViolation):
        """違反ログの記録"""
        log_entry = {
            "rule_id": violation.rule_id,
            "description": violation.description,
            "severity": violation.severity,
            "timestamp": violation.timestamp.isoformat(),
            "context": violation.context,
            "auto_fixable": violation.auto_fixable,
            "fix_applied": violation.fix_applied,
        }

        # ログファイルに追記
        logs = []
        if self.violation_log.exists():
            try:
                with open(self.violation_log, "r") as f:
                    logs = json.load(f)
            except:
                logs = []

        logs.append(log_entry)

        with open(self.violation_log, "w") as f:
            json.dump(logs, f, indent=2)

    def _log_auto_fix(
        self,
        rule: RuleDefinition,
        violation: RuleViolation,
        success: bool,
        error: str = None,
    ):
        """自動修正ログの記録"""
        log_entry = {
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "violation_time": violation.timestamp.isoformat(),
            "fix_time": datetime.now().isoformat(),
            "success": success,
            "error": error,
        }

        # ログファイルに追記
        logs = []
        if self.auto_fix_log.exists():
            try:
                with open(self.auto_fix_log, "r") as f:
                    logs = json.load(f)
            except:
                logs = []

        logs.append(log_entry)

        with open(self.auto_fix_log, "w") as f:
            json.dump(logs, f, indent=2)

    # ===== バリデーション関数 =====

    def _validate_commit_timing(self) -> bool:
        """コミットタイミングの検証"""
        try:
            # Git作業ディレクトリに未コミットの変更があるかチェック
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_dir,
            )

            # 変更がある場合は違反と判定
            return len(result.stdout.strip()) == 0
        except:
            return True  # エラー時は違反と見なさない

    def _validate_push_timing(self) -> bool:
        """プッシュタイミングの検証"""
        try:
            # ローカルブランチが最新のリモートブランチと同期しているかチェック
            result = subprocess.run(
                ["git", "status", "-sb"],
                capture_output=True,
                text=True,
                cwd=self.project_dir,
            )

            # "ahead"がある場合は未プッシュのコミットがある
            return "ahead" not in result.stdout
        except:
            return True  # エラー時は違反と見なさない

    def _validate_incident_consultation(self) -> bool:
        """インシデント賢者相談の検証"""
        # 簡易実装: 最近のタスクトラッカー記録をチェック
        try:
            # タスクトラッカーの最新記録を確認
            if (
                hasattr(self.task_tracker, "current_task_id")
                and self.task_tracker.current_task_id
            ):
                return True  # タスクが記録されていれば相談済みと見なす
            return False
        except:
            return True

    def _validate_sage_meeting_timing(self) -> bool:
        """賢者会議タイミングの検証"""
        # 簡易実装: インシデント記録をチェック
        try:
            # 最近のインシデント記録があるかチェック
            incident_logs = self.project_dir / "logs" / "incidents.json"
            if incident_logs.exists():
                return True
            return False
        except:
            return True

    def _validate_task_sync(self) -> bool:
        """タスク同期の検証"""
        # 簡易実装: 最新のタスク更新時刻をチェック
        try:
            # タスクトラッカーの最新更新をチェック
            if (
                hasattr(self.task_tracker, "task_start_time")
                and self.task_tracker.task_start_time
            ):
                time_diff = datetime.now() - self.task_tracker.task_start_time
                return time_diff.total_seconds() < 1800  # 30分以内
            return False
        except:
            return True

    # ===== 自動修正関数 =====

    async def _auto_fix_commit(self) -> bool:
        """コミットの自動修正"""
        try:
            # GitHub Flow Managerを使用して自動コミット
            success = self.github_flow.commit_changes(
                message="auto: rule enforcement system triggered commit",
                use_best_practices=True,
            )
            return success
        except Exception as e:
            logger.error(f"自動コミットエラー: {e}")
            return False

    async def _auto_fix_push(self) -> bool:
        """プッシュの自動修正"""
        try:
            # GitHub Flow Managerを使用して自動プッシュ
            result = self.github_flow.run_git("push origin main")
            return result.returncode == 0
        except Exception as e:
            logger.error(f"自動プッシュエラー: {e}")
            return False

    async def _auto_fix_incident_consultation(self) -> bool:
        """インシデント賢者相談の自動修正"""
        try:
            # インシデント統合システムを通じて相談を実行
            consultation_data = {
                "type": "auto_consultation",
                "trigger": "rule_enforcement_system",
                "timestamp": datetime.now().isoformat(),
            }

            await self.incident_integration.report_incident(
                "auto_consultation", consultation_data
            )
            return True
        except Exception as e:
            logger.error(f"自動相談エラー: {e}")
            return False

    async def _auto_fix_sage_meeting(self) -> bool:
        """賢者会議の自動修正"""
        try:
            # 4賢者会議を自動招集
            meeting_data = {
                "type": "auto_sage_meeting",
                "trigger": "rule_enforcement_system",
                "timestamp": datetime.now().isoformat(),
            }

            await self.incident_integration.summon_elder_council(meeting_data)
            return True
        except Exception as e:
            logger.error(f"自動会議招集エラー: {e}")
            return False

    async def _auto_fix_task_sync(self) -> bool:
        """タスク同期の自動修正"""
        try:
            # タスクトラッカーとの同期を実行
            self.task_tracker.update_progress(
                "自動同期: ルール遵守システムによる定期更新",
                files_affected=["rule_enforcement_system"],
            )
            return True
        except Exception as e:
            logger.error(f"自動タスク同期エラー: {e}")
            return False

    # ===== 公開API =====

    def get_violation_summary(self) -> Dict[str, Any]:
        """違反サマリーの取得"""
        return {
            "total_violations": len(self.violations),
            "critical_violations": len(
                [v for v in self.violations if v.severity == "CRITICAL"]
            ),
            "high_violations": len(
                [v for v in self.violations if v.severity == "HIGH"]
            ),
            "auto_fixes_applied": len([v for v in self.violations if v.fix_applied]),
            "last_violation": (
                self.violations[-1].timestamp.isoformat() if self.violations else None
            ),
        }

    def enable_rule(self, rule_id: str):
        """ルールを有効化"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            logger.info(f"ルール有効化: {rule_id}")

    def disable_rule(self, rule_id: str):
        """ルールを無効化"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            logger.info(f"ルール無効化: {rule_id}")

    def get_active_rules(self) -> List[str]:
        """有効なルール一覧を取得"""
        return [rule_id for rule_id, rule in self.rules.items() if rule.enabled]


# グローバルインスタンス
_rule_enforcement_system = None


def get_rule_enforcement_system() -> ClaudeElderRuleEnforcementSystem:
    """グローバルルール遵守システムの取得"""
    global _rule_enforcement_system
    if _rule_enforcement_system is None:
        _rule_enforcement_system = ClaudeElderRuleEnforcementSystem()
    return _rule_enforcement_system


def rule_enforced(func: Callable):
    """ルール遵守デコレータ"""

    @wraps(func)
    @incident_aware
    async def async_wrapper(*args, **kwargs):
        """async_wrapperメソッド"""
        rule_system = get_rule_enforcement_system()
        if not rule_system.monitoring_active:
            rule_system.start_monitoring()
        return await func(*args, **kwargs)

    @wraps(func)
    @incident_aware
    def sync_wrapper(*args, **kwargs):
        """sync_wrapperメソッド"""
        rule_system = get_rule_enforcement_system()
        if not rule_system.monitoring_active:
            rule_system.start_monitoring()
        return func(*args, **kwargs)

    # 関数が非同期かどうかで適切なラッパーを返す
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


# 使用例とテスト
if __name__ == "__main__":
    import time

    async def test_rule_enforcement_system():
        """ルール遵守システムのテスト"""
        print("🛡️ Claude Elder Rule Enforcement System テスト開始")

        # システム初期化
        rule_system = get_rule_enforcement_system()

        # 監視開始
        rule_system.start_monitoring()

        # 2分間監視
        print("📊 2分間の監視を開始...")
        await asyncio.sleep(120)

        # 監視停止
        rule_system.stop_monitoring()

        # 結果表示
        summary = rule_system.get_violation_summary()
        print(f"📋 監視結果: {summary}")

        print("✅ テスト完了")

    # テスト実行
    asyncio.run(test_rule_enforcement_system())
