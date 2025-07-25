"""
Elder Flow違反タイプ定義
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

class ViolationSeverity(Enum):
    """違反の重要度"""

    CRITICAL = "critical"  # 即座の対応が必要
    HIGH = "high"  # 重要な違反
    MEDIUM = "medium"  # 中程度の違反
    LOW = "low"  # 軽微な違反

class ViolationCategory(Enum):
    """違反カテゴリ"""

    PROCESS = "process"  # 開発プロセス違反
    HIERARCHY = "hierarchy"  # 階層・権限違反
    TECHNICAL = "technical"  # 技術的違反
    QUALITY = "quality"  # 品質・ドキュメント違反

class ViolationType(Enum):
    """Elder Flow違反タイプ"""

    # 開発プロセス違反
    FOUR_SAGES_CONSULTATION_MISSING = "four_sages_consultation_missing"
    FOUR_SAGES_MEETING_MISSING = "four_sages_meeting_missing"
    GITHUB_FLOW_COMMIT_MISSING = "github_flow_commit_missing"
    GITHUB_FLOW_PUSH_MISSING = "github_flow_push_missing"
    TDD_TEST_FIRST_VIOLATION = "tdd_test_first_violation"
    TDD_CYCLE_VIOLATION = "tdd_cycle_violation"
    COVERAGE_THRESHOLD_VIOLATION = "coverage_threshold_violation"

    # 階層・権限違反
    HIERARCHY_VIOLATION = "hierarchy_violation"
    IDENTITY_VIOLATION = "identity_violation"
    UNAUTHORIZED_DECISION = "unauthorized_decision"

    # 技術的違反
    DOCKER_PERMISSION_VIOLATION = "docker_permission_violation"
    ENVIRONMENT_PROTECTION_VIOLATION = "environment_protection_violation"

    # 品質・ドキュメント違反
    COSTAR_FRAMEWORK_MISSING = "costar_framework_missing"
    KNOWLEDGE_BASE_UPDATE_MISSING = "knowledge_base_update_missing"
    FAILURE_LEARNING_MISSING = "failure_learning_missing"

@dataclass
class ViolationRule:
    """違反ルール定義"""

    violation_type: ViolationType
    name: str
    description: str
    category: ViolationCategory
    severity: ViolationSeverity
    detection_patterns: List[str]  # 検知パターン（正規表現など）
    auto_fixable: bool = False  # 自動修正可能か

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "violation_type": self.violation_type.value,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "severity": self.severity.value,
            "detection_patterns": self.detection_patterns,
            "auto_fixable": self.auto_fixable,
        }

# Elder Flow違反ルール定義
ELDER_FLOW_VIOLATION_RULES = [
    # 4賢者相談違反
    ViolationRule(
        violation_type=ViolationType.FOUR_SAGES_CONSULTATION_MISSING,
        name="4賢者相談忘れ",
        description="新機能実装前にインシデント賢者への相談がありません",
        category=ViolationCategory.PROCESS,
        severity=ViolationSeverity.CRITICAL,
        detection_patterns=[
            r"新機能.*実装",
            r"implement.*feature",
            r"add.*functionality",
        ],
        auto_fixable=False,
    ),
    # GitHub Flow違反
    ViolationRule(
        violation_type=ViolationType.GITHUB_FLOW_COMMIT_MISSING,
        name="即座のコミット忘れ",
        description="機能完了後に即座のコミットが行われていません",
        category=ViolationCategory.PROCESS,
        severity=ViolationSeverity.HIGH,
        detection_patterns=[
            r"機能.*完了",
            r"implementation.*complete",
            r"feature.*done",
        ],
        auto_fixable=True,
    ),
    # TDD違反
    ViolationRule(
        violation_type=ViolationType.TDD_TEST_FIRST_VIOLATION,
        name="テストファースト違反",
        description="テスト作成前にコードが実装されています",
        category=ViolationCategory.PROCESS,
        severity=ViolationSeverity.HIGH,
        detection_patterns=[
            r"実装.*テスト.*前",
            r"code.*before.*test",
            r"implementation.*without.*test",
        ],
        auto_fixable=False,
    ),
    # Docker権限違反
    ViolationRule(
        violation_type=ViolationType.DOCKER_PERMISSION_VIOLATION,
        name="Docker権限違反",
        description="sg docker -cを使用せずにDockerコマンドを実行しています",
        category=ViolationCategory.TECHNICAL,
        severity=ViolationSeverity.HIGH,
        detection_patterns=[r"^docker\s+(?!.*sg\s+docker\s+-c)", r"sudo\s+docker"],
        auto_fixable=True,
    ),
    # アイデンティティ違反
    ViolationRule(
        violation_type=ViolationType.IDENTITY_VIOLATION,
        name="アイデンティティ違反",
        description="Claude Elderとしての正しいアイデンティティが保たれていません",
        category=ViolationCategory.HIERARCHY,
        severity=ViolationSeverity.HIGH,
        detection_patterns=[
            r"ただのAI",
            r"just.*AI.*assistant",
            r"私はClaude(?!.*Elder)",
            r"I am Claude(?!.*Elder)",
        ],
        auto_fixable=True,
    ),
    # CO-STAR違反
    ViolationRule(
        violation_type=ViolationType.COSTAR_FRAMEWORK_MISSING,
        name="CO-STARフレームワーク未使用",
        description="開発時にCO-STARフレームワークが使用されていません",
        category=ViolationCategory.QUALITY,
        severity=ViolationSeverity.MEDIUM,
        detection_patterns=[
            r"開発.*CO-STAR.*なし",
            r"implement.*without.*COSTAR",
            r"missing.*context.*objective",
        ],
        auto_fixable=False,
    ),
]

def get_violation_rule(violation_type: ViolationType) -> Optional[ViolationRule]:
    """指定された違反タイプのルールを取得"""
    for rule in ELDER_FLOW_VIOLATION_RULES:
        if rule.violation_type == violation_type:
            return rule
    return None

def get_rules_by_category(category: ViolationCategory) -> List[ViolationRule]:
    """指定されたカテゴリのルールを取得"""
    return [rule for rule in ELDER_FLOW_VIOLATION_RULES if rule.category == category]

def get_rules_by_severity(severity: ViolationSeverity) -> List[ViolationRule]:
    """指定された重要度のルールを取得"""
    return [rule for rule in ELDER_FLOW_VIOLATION_RULES if rule.severity == severity]
