"""
Elder Flow違反検知エンジン
"""
import re
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import logging

from libs.elder_flow_violation_types import (
    ViolationType,
    ViolationSeverity,
    ViolationCategory,
    ViolationRule,
    ELDER_FLOW_VIOLATION_RULES
)


logger = logging.getLogger(__name__)


@dataclass
class ViolationDetectionContext:
    """違反検知のコンテキスト"""
    command: Optional[str] = None
    file_path: Optional[str] = None
    content: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ViolationRecord:
    """違反記録"""
    violation_type: ViolationType
    category: ViolationCategory
    severity: ViolationSeverity
    description: str
    context: ViolationDetectionContext
    detected_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    auto_fixed: bool = False
    auto_fixable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "violation_type": self.violation_type.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "auto_fixed": self.auto_fixed,
            "auto_fixable": self.auto_fixable,
            "context": {
                "command": self.context.command,
                "file_path": self.context.file_path,
                "timestamp": self.context.timestamp.isoformat()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ViolationRecord':
        """辞書から復元"""
        context = ViolationDetectionContext(
            command=data["context"].get("command"),
            file_path=data["context"].get("file_path"),
            timestamp=datetime.fromisoformat(data["context"]["timestamp"])
        )

        return cls(
            violation_type=ViolationType(data["violation_type"]),
            category=ViolationCategory(data["category"]),
            severity=ViolationSeverity(data["severity"]),
            description=data["description"],
            context=context,
            detected_at=datetime.fromisoformat(data["detected_at"]),
            resolved_at=datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None,
            resolution_notes=data.get("resolution_notes"),
            auto_fixed=data.get("auto_fixed", False),
            auto_fixable=data.get("auto_fixable", False)
        )


@dataclass
class ViolationDetectionResult:
    """違反検知結果"""
    violations: List[ViolationRecord] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        """違反があるか"""
        return len(self.violations) > 0

    @property
    def critical_violations(self) -> List[ViolationRecord]:
        """重大な違反のみ取得"""
        return [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]

    @property
    def auto_fixable_violations(self) -> List[ViolationRecord]:
        """自動修正可能な違反のみ取得"""
        return [v for v in self.violations if v.auto_fixable]


class ElderFlowViolationDetector:
    """Elder Flow違反検知エンジン"""

    def __init__(self, history_file: Optional[Path] = None):
        """初期化"""
        self.violation_rules = ELDER_FLOW_VIOLATION_RULES
        self.violation_history: List[ViolationRecord] = []
        self.history_file = history_file or Path("data/elder_flow_violations.json")

        # 履歴を読み込み
        self.load_violation_history()

    def detect_violations(self, context: ViolationDetectionContext) -> ViolationDetectionResult:
        """違反を検知"""
        result = ViolationDetectionResult()

        # 各ルールに対してチェック
        for rule in self.violation_rules:
            if self._check_violation(rule, context):
                record = ViolationRecord(
                    violation_type=rule.violation_type,
                    category=rule.category,
                    severity=rule.severity,
                    description=rule.description,
                    context=context,
                    auto_fixable=rule.auto_fixable
                )
                result.violations.append(record)
                logger.warning(f"Elder Flow違反検知: {rule.name} - {rule.description}")

        return result

    def _check_violation(self, rule: ViolationRule, context: ViolationDetectionContext) -> bool:
        """特定のルールに対して違反をチェック"""
        # チェック対象のテキストを収集
        texts_to_check = []

        if context.command:
            texts_to_check.append(context.command)

        if context.content:
            texts_to_check.append(context.content)

        # パターンマッチング
        for text in texts_to_check:
            for pattern in rule.detection_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True

        return False

    def add_to_history(self, violation: ViolationRecord) -> None:
        """違反を履歴に追加"""
        self.violation_history.append(violation)
        self.save_violation_history()

    def get_violation_stats(self) -> Dict[str, Any]:
        """違反統計を取得"""
        stats = {
            "total_violations": len(self.violation_history),
            "active_violations": len(self.get_active_violations()),
            "by_severity": {},
            "by_category": {},
            "by_type": {}
        }

        # 重要度別集計
        for severity in ViolationSeverity:
            count = len([v for v in self.violation_history if v.severity == severity])
            stats["by_severity"][severity.value] = count

        # カテゴリ別集計
        for category in ViolationCategory:
            count = len([v for v in self.violation_history if v.category == category])
            stats["by_category"][category.value] = count

        # タイプ別集計
        for violation_type in ViolationType:
            count = len([v for v in self.violation_history if v.violation_type == violation_type])
            if count > 0:
                stats["by_type"][violation_type.value] = count

        return stats

    def get_auto_fix_suggestion(self, violation: ViolationRecord) -> Optional[str]:
        """自動修正の提案を取得"""
        if not violation.auto_fixable:
            return None

        # 違反タイプごとの修正提案
        suggestions = {
            ViolationType.DOCKER_PERMISSION_VIOLATION: "sg docker -c \"{}\"",
            ViolationType.GITHUB_FLOW_COMMIT_MISSING: "git add . && git commit -m \"feat: {}\"",
            ViolationType.IDENTITY_VIOLATION: "私はClaude Elder、エルダーズギルド開発実行責任者です"
        }

        suggestion_template = suggestions.get(violation.violation_type)
        if suggestion_template and violation.context.command:
            return suggestion_template.format(violation.context.command)
        elif suggestion_template:
            return suggestion_template.format("適切な内容")

        return None

    def resolve_violation(self, violation: ViolationRecord, resolution_notes: str) -> bool:
        """違反を解決済みにする"""
        try:
            violation.resolved_at = datetime.now()
            violation.resolution_notes = resolution_notes
            self.save_violation_history()
            logger.info(f"違反解決: {violation.violation_type.value}")
            return True
        except Exception as e:
            logger.error(f"違反解決エラー: {e}")
            return False

    def get_active_violations(self) -> List[ViolationRecord]:
        """アクティブな（未解決の）違反を取得"""
        return [v for v in self.violation_history if v.resolved_at is None]

    def save_violation_history(self) -> bool:
        """違反履歴を保存"""
        try:
            # ディレクトリを作成
            self.history_file.parent.mkdir(parents=True, exist_ok=True)

            # 履歴を辞書形式に変換
            history_data = [v.to_dict() for v in self.violation_history]

            # JSONファイルに保存
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            logger.error(f"違反履歴保存エラー: {e}")
            return False

    def load_violation_history(self) -> bool:
        """違反履歴を読み込み"""
        try:
            if not self.history_file.exists():
                return False

            with open(self.history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)

            # 履歴を復元
            self.violation_history = [
                ViolationRecord.from_dict(data) for data in history_data
            ]

            logger.info(f"違反履歴を読み込みました: {len(self.violation_history)}件")
            return True
        except Exception as e:
            logger.error(f"違反履歴読み込みエラー: {e}")
            return False

    def generate_violation_report(self) -> str:
        """違反レポートを生成"""
        stats = self.get_violation_stats()
        active_violations = self.get_active_violations()

        report = f"""
# Elder Flow違反レポート

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 統計サマリー
- 総違反数: {stats['total_violations']}
- アクティブな違反: {stats['active_violations']}

### 重要度別
"""

        for severity, count in stats['by_severity'].items():
            report += f"- {severity}: {count}件\n"

        report += "\n### カテゴリ別\n"
        for category, count in stats['by_category'].items():
            report += f"- {category}: {count}件\n"

        if active_violations:
            report += "\n## アクティブな違反\n"
            for violation in active_violations[:10]:  # 最新10件
                report += f"""
### {violation.violation_type.value}
- 重要度: {violation.severity.value}
- 検知日時: {violation.detected_at.strftime('%Y-%m-%d %H:%M:%S')}
- 説明: {violation.description}
"""
                if violation.auto_fixable:
                    suggestion = self.get_auto_fix_suggestion(violation)
                    if suggestion:
                        report += f"- 修正提案: `{suggestion}`\n"

        return report
