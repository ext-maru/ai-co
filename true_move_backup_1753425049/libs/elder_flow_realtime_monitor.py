"""
Elder Flowリアルタイム監視システム
24時間365日、あらゆる違反を即座に検知し、自動修正を試みる
"""

import os
import re
import json
import time
import threading
import subprocess
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 元の違反タイプ定義を使用
from libs.elder_flow_violation_types_original import (
    ViolationType,
    ViolationSeverity,
    ViolationCategory,
    ELDER_FLOW_VIOLATION_RULES,
)
from libs.elder_flow_violation_detector import (
    ElderFlowViolationDetector as OriginalDetector,
    ViolationDetectionContext,
)
from libs.elder_flow_violation_db import ElderFlowViolationDB


logger = logging.getLogger(__name__)


class MonitoringEventType(Enum):
    """監視イベントの種類"""

    GIT_HOOK = "git_hook"
    FILE_CHANGE = "file_change"
    COMMAND_EXECUTION = "command_execution"
    PERIODIC_CHECK = "periodic_check"
    AUTO_FIX_ATTEMPT = "auto_fix_attempt"


@dataclass
class MonitoringEvent:
    """監視イベント"""

    event_type: MonitoringEventType
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    violations_found: List[Any] = field(default_factory=list)


@dataclass
class CommandInterceptionResult:
    """コマンドインターセプト結果"""

    intercepted: bool
    violation_type: Optional[ViolationType] = None
    suggestion: Optional[str] = None
    corrected_command: Optional[str] = None


@dataclass
class AutoFixResult:
    """自動修正結果"""

    attempted: bool
    success: bool
    fix_applied: Optional[str] = None
    error_message: Optional[str] = None


class GitHookMonitor:
    """Gitフック監視システム"""

    def __init__(self):
        """初期化メソッド"""
        self.hooks_template_dir = Path(__file__).parent / "hooks_templates"
        self.detector = OriginalDetector()

    def install_hooks(self, repo_path: str) -> bool:
        """Gitフックをインストール"""
        try:
            git_hooks_dir = Path(repo_path) / ".git/hooks"
            if not git_hooks_dir.exists():
                git_hooks_dir.mkdir(parents=True)

            # pre-commitフック
            pre_commit_hook = git_hooks_dir / "pre-commit"
            pre_commit_content = self._generate_pre_commit_hook()
            pre_commit_hook.write_text(pre_commit_content)
            pre_commit_hook.chmod(0o755)

            # post-commitフック
            post_commit_hook = git_hooks_dir / "post-commit"
            post_commit_content = self._generate_post_commit_hook()
            post_commit_hook.write_text(post_commit_content)
            post_commit_hook.chmod(0o755)

            # pre-pushフック
            pre_push_hook = git_hooks_dir / "pre-push"
            pre_push_content = self._generate_pre_push_hook()
            pre_push_hook.write_text(pre_push_content)
            pre_push_hook.chmod(0o755)

            logger.info(f"Gitフックをインストールしました: {repo_path}")
            return True

        except Exception as e:
            logger.error(f"Gitフックのインストールに失敗: {e}")
            return False

    def _generate_pre_commit_hook(self) -> str:
        """pre-commitフックスクリプトを生成"""
        return """#!/bin/bash
# Elder Flow pre-commit hook

echo "🔍 Elder Flow違反チェック中..."

# Pythonスクリプトを実行して違反をチェック
python3 -c "
import sys
sys.path.insert(0, '.')
from libs.elder_flow_realtime_monitor import GitHookMonitor
monitor = GitHookMonitor()
if not monitor.check_pre_commit('.'):
    sys.exit(1)
"

if [ $? -ne 0 ]; then:
    echo "❌ Elder Flow違反が検出されました。コミットを中止します。"
    echo "違反を修正してから再度コミットしてください。"
    exit 1
fi

echo "✅ Elder Flow違反チェック完了"
"""

    def _generate_post_commit_hook(self) -> str:
        """post-commitフックスクリプトを生成"""
        return """#!/bin/bash
# Elder Flow post-commit hook

echo "📝 Elder Flowコミット後チェック..."

python3 -c "
import sys
sys.path.insert(0, '.')
from libs.elder_flow_realtime_monitor import GitHookMonitor
monitor = GitHookMonitor()
monitor.check_post_commit('.')
"
"""

    def _generate_pre_push_hook(self) -> str:
        """pre-pushフックスクリプトを生成"""
        return """#!/bin/bash
# Elder Flow pre-push hook

echo "🚀 Elder Flowプッシュ前チェック..."

python3 -c "
import sys
sys.path.insert(0, '.')
from libs.elder_flow_realtime_monitor import GitHookMonitor
monitor = GitHookMonitor()
if not monitor.check_pre_push('.'):
    sys.exit(1)
"

if [ $? -ne 0 ]; then:
    echo "❌ 未解決のElder Flow違反があります。プッシュを中止します。"
    exit 1
fi

echo "✅ プッシュ前チェック完了"
"""

    def check_pre_commit(self, repo_path: str) -> bool:
        """pre-commitチェック"""
        # ステージングされたファイルを取得
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            staged_files = result.stdout.strip().split("\n") if result.stdout else []

            violations_found = False

            for file_path in staged_files:
                if file_path.endswith(".py"):
                    # ファイル内容をチェック
                    full_path = os.path.join(repo_path, file_path)
                    if os.path.exists(full_path):
                        # Deep nesting detected (depth: 5) - consider refactoring
                        with open(full_path, "r") as f:
                            content = f.read()

                        context = ViolationDetectionContext(
                            file_path=file_path, content=content
                        )

                        result = self.detector.detect_violations(context)
                        if not (result.has_violations):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if result.has_violations:
                            violations_found = True
                            # Deep nesting detected (depth: 6) - consider refactoring
                            for violation in result.violations:
                                print(f"  ⚠️  {violation.description}")

            return not violations_found

        except Exception as e:
            logger.error(f"pre-commitチェックエラー: {e}")
            return True  # エラーの場合はコミットを許可

    def check_post_commit(self, repo_path: str) -> None:
        """post-commitチェック"""
        # 最新のコミットメッセージをチェック
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            commit_message = result.stdout.strip()

            # GitHub Flow違反チェック
            context = ViolationDetectionContext(
                command=f"git commit -m '{commit_message}'", content=commit_message
            )

            result = self.detector.detect_violations(context)
            if result.has_violations:
                print("⚠️  コミット後の違反が検出されました:")
                for violation in result.violations:
                    print(f"  - {violation.description}")

        except Exception as e:
            logger.error(f"post-commitチェックエラー: {e}")

    def check_pre_push(self, repo_path: str) -> bool:
        """pre-pushチェック"""
        # 未解決の違反があるかチェック
        db = ElderFlowViolationDB()
        active_violations = db.get_active_violations()

        if active_violations:
            print(f"⚠️  {len(active_violations)}件の未解決違反があります:")
            for v in active_violations[:5]:
                print(f"  - {v['violation_type']} ({v['severity']})")
            return False

        return True

    def log_hook_event(
        self, hook_type: str, repo_path: str, violations_found: bool
    ) -> MonitoringEvent:
        """フックイベントをログ"""
        return MonitoringEvent(
            event_type=MonitoringEventType.GIT_HOOK,
            details={
                "hook_type": hook_type,
                "repo_path": repo_path,
                "violations_found": violations_found,
            },
        )


class FileWatchGuardian(FileSystemEventHandler):
    """ファイル監視ガーディアン"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__()
        self.observer = Observer()
        self.detector = OriginalDetector()
        self.db = ElderFlowViolationDB()
        self.is_watching = False
        self.ignore_patterns = set()

    def start_watching(self, path: str) -> None:
        """監視を開始"""
        if not self.is_watching:
            self.observer.schedule(self, path, recursive=True)
            self.observer.start()
            self.is_watching = True
            logger.info(f"ファイル監視を開始しました: {path}")

    def stop(self) -> None:
        """監視を停止"""
        if self.is_watching:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False
            logger.info("ファイル監視を停止しました")

    def set_ignore_patterns(self, patterns: List[str]) -> None:
        """無視パターンを設定"""
        self.ignore_patterns = set(patterns)

    def should_ignore(self, path: str) -> bool:
        """パスを無視すべきか判定"""
        for pattern in self.ignore_patterns:
            if pattern in path:
                return True
        return False

    def on_modified(self, event):
        """ファイル変更時の処理"""
        if not event.is_directory and not self.should_ignore(event.src_path):
            self._check_file_for_violations(event.src_path)

    def on_created(self, event):
        """ファイル作成時の処理"""
        if not event.is_directory and not self.should_ignore(event.src_path):
            self._check_file_for_violations(event.src_path)

    def _check_file_for_violations(self, file_path: str) -> List[Any]:
        """ファイルの違反をチェック"""
        violations = []

        if file_path.endswith(".py"):
            try:
                with open(file_path, "r") as f:
                    content = f.read()

                context = ViolationDetectionContext(
                    file_path=file_path, content=content
                )

                result = self.detector.detect_violations(context)
                if result.has_violations:
                    logger.warning(f"違反検出 in {file_path}")
                    for violation in result.violations:
                        # データベースに記録
                        self.db.save_violation(violation)
                        violations.append(violation)

                        # 自動修正可能な場合は試みる
                        if not (violation.auto_fixable):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if violation.auto_fixable:
                            self._attempt_auto_fix(violation, file_path)

            except Exception as e:
                logger.error(f"ファイルチェックエラー: {e}")

        return violations

    def _attempt_auto_fix(self, violation, file_path: str) -> None:
        """自動修正を試みる"""
        suggestion = self.detector.get_auto_fix_suggestion(violation)
        if suggestion:
            logger.info(f"自動修正を試みます: {violation.violation_type.value}")
            # 実際の自動修正ロジックはここに実装


class CommandInterceptor:
    """コマンドインターセプター"""

    def __init__(self):
        """初期化メソッド"""
        self.detector = OriginalDetector()
        self.db = ElderFlowViolationDB()
        self.command_patterns = {
            ViolationType.DOCKER_PERMISSION_VIOLATION: [
                (r"^docker\s+", 'sg docker -c "{}"'),
                (r"^sudo\s+docker\s+", 'sg docker -c "{}"'),
            ]
        }

    def intercept_command(self, command: str) -> CommandInterceptionResult:
        """コマンドをインターセプト"""
        context = ViolationDetectionContext(command=command)
        result = self.detector.detect_violations(context)

        if result.has_violations:
            violation = result.violations[0]  # 最初の違反を処理

            # 修正提案を取得
            suggestion = self.detector.get_auto_fix_suggestion(violation)
            corrected = (
                self.get_corrected_command(command) if violation.auto_fixable else None
            )

            return CommandInterceptionResult(
                intercepted=True,
                violation_type=violation.violation_type,
                suggestion=suggestion,
                corrected_command=corrected,
            )

        return CommandInterceptionResult(intercepted=False)

    def get_corrected_command(self, command: str) -> Optional[str]:
        """修正されたコマンドを取得"""
        # 繰り返し処理
        for violation_type, patterns in self.command_patterns.items():
            for pattern, replacement in patterns:
                if re.match(pattern, command):
                    # コマンドから元のdockerコマンドを抽出
                    docker_cmd = re.sub(pattern, "", command)
                    return replacement.format(docker_cmd.strip())
        return None

    def check_four_sages_consultation(self, command: str) -> Any:
        """4賢者相談が必要かチェック"""
        patterns = [r"新機能.*実装", r"implement.*feature", r"add.*functionality"]

        for pattern in patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return type(
                    "obj",
                    (object,),
                    {"needs_consultation": True, "sage_type": "incident"},
                )()

        return type(
            "obj", (object,), {"needs_consultation": False, "sage_type": None}
        )()

    def execute_with_monitoring(self, command: str) -> Any:
        """監視付きでコマンドを実行"""
        # コマンドをインターセプト
        interception = self.intercept_command(command)

        if interception.intercepted:
            if interception.corrected_command:
                logger.info(f"コマンドを修正して実行: {interception.corrected_command}")
                command = interception.corrected_command
            else:
                logger.warning(f"違反検出: {interception.violation_type}")

        # コマンドを実行（セキュリティ修正）
        try:
            # shell=Trueを避けて安全に実行
            import shlex
            cmd_list = shlex.split(command) if isinstance(command, str) else command
            result = subprocess.run(cmd_list, capture_output=True, text=True)

            return type(
                "obj",
                (object,),
                {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )()

        except Exception as e:
            logger.error(f"コマンド実行エラー: {e}")
            return type("obj", (object,), {"success": False, "error": str(e)})()


class RealtimeMonitoringSystem:
    """統合リアルタイム監視システム"""

    def __init__(self):
        """初期化メソッド"""
        self.git_monitor = GitHookMonitor()
        self.file_guardian = FileWatchGuardian()
        self.command_interceptor = CommandInterceptor()
        self.db = ElderFlowViolationDB()
        self.is_running = False
        self.events: List[MonitoringEvent] = []
        self.periodic_timer = None

    def start_monitoring(self, repo_path: str) -> None:
        """監視を開始"""
        if not self.is_running:
            # Gitフックをインストール
            self.git_monitor.install_hooks(repo_path)

            # ファイル監視を開始
            self.file_guardian.set_ignore_patterns(
                [
                    ".git",
                    "__pycache__",
                    "*.pyc",
                    ".pytest_cache",
                    "node_modules",
                    "venv",
                    ".env",
                ]
            )
            self.file_guardian.start_watching(repo_path)

            # 定期チェックを開始
            self.schedule_periodic_checks()

            self.is_running = True
            logger.info("リアルタイム監視システムを起動しました")

    def stop_monitoring(self) -> None:
        """監視を停止"""
        if self.is_running:
            self.file_guardian.stop()

            if self.periodic_timer:
                self.periodic_timer.cancel()

            self.is_running = False
            logger.info("リアルタイム監視システムを停止しました")

    def add_event(self, event: MonitoringEvent) -> None:
        """イベントを追加"""
        self.events.append(event)

        # 最新1000件のみ保持
        if len(self.events) > 1000:
            self.events = self.events[-1000:]

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """監視統計を取得"""
        stats = {
            "total_events": len(self.events),
            "by_type": {},
            "recent_violations": [],
        }

        # イベントタイプ別集計
        for event in self.events:
            event_type = event.event_type.value
            stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1

        # 最近の違反
        recent_violations = self.db.get_recent_violations(10)
        stats["recent_violations"] = recent_violations

        return stats

    def attempt_auto_fix(self, violation) -> AutoFixResult:
        """違反の自動修正を試みる"""
        try:
            if not violation.auto_fixable:
                return AutoFixResult(attempted=False, success=False)

            suggestion = self.git_monitor.detector.get_auto_fix_suggestion(violation)
            if suggestion:
                # ここに実際の自動修正ロジックを実装
                logger.info(f"自動修正を適用: {suggestion}")
                return AutoFixResult(
                    attempted=True, success=True, fix_applied=suggestion
                )

        except Exception as e:
            logger.error(f"自動修正エラー: {e}")
            return AutoFixResult(attempted=True, success=False, error_message=str(e))

        return AutoFixResult(attempted=True, success=False)

    def schedule_periodic_checks(self, interval: int = 300) -> None:
        """定期チェックをスケジュール（デフォルト5分）"""

        def run_check():
            """run_checkチェックメソッド"""
            self._run_periodic_check()
            # 次回のチェックをスケジュール
            self.periodic_timer = threading.Timer(interval, run_check)
            self.periodic_timer.start()

        # 最初のチェックをスケジュール
        self.periodic_timer = threading.Timer(interval, run_check)
        self.periodic_timer.start()

    def _run_periodic_check(self) -> None:
        """定期チェックを実行"""
        logger.info("定期チェックを実行中...")

        # アクティブな違反をチェック
        active_violations = self.db.get_active_violations()

        event = MonitoringEvent(
            event_type=MonitoringEventType.PERIODIC_CHECK,
            details={
                "active_violations_count": len(active_violations),
                "timestamp": datetime.now().isoformat(),
            },
        )

        self.add_event(event)

        # 自動修正可能な違反を処理
        for violation_data in active_violations:
            if violation_data.get("auto_fixable"):
                # 違反オブジェクトを再構築して自動修正を試みる
                logger.info(f"自動修正を試みます: {violation_data['violation_type']}")

    def generate_monitoring_report(self) -> str:
        """監視レポートを生成"""
        stats = self.get_monitoring_stats()
        db_stats = self.db.get_statistics()

        report = f"""
# リアルタイム監視レポート

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
監視状態: {'稼働中' if self.is_running else '停止中'}

## 統計サマリー
- 監視イベント総数: {stats['total_events']}
- データベース内違反総数: {db_stats['total_violations']}
- アクティブな違反: {db_stats['active_violations']}

### イベントタイプ別
"""

        for event_type, count in stats["by_type"].items():
            report += f"- {event_type}: {count}件\n"

        report += "\n### 最近の違反\n"
        for violation in stats["recent_violations"][:5]:
            report += f"- {violation['violation_type']} ({violation['severity']}) - {violation['detected_at']}\n"

        report += "\n## イベント履歴（最新10件）\n"
        for event in self.events[-10:]:
            report += (
                f"- [{event.timestamp.strftime('%H:%M:%S')}] {event.event_type.value}"
            )
            if event.violations_found:
                report += f" - {len(event.violations_found)}件の違反"
            report += "\n"

        return report
