"""
Elder Flow Violation Types
違反タイプの定義と分類
"""

from enum import Enum
from typing import Dict, List, Optional


class ViolationSeverity(Enum):
    """違反の重要度"""

    CRITICAL = "致命的"  # 即座に修正が必要
    HIGH = "高"  # 本番投入前に修正必須
    MEDIUM = "中"  # 早期の修正を推奨
    LOW = "低"  # 改善の余地あり
    WARNING = "警告"  # 注意喚起


class ViolationCategory(Enum):
    """違反のカテゴリ"""

    IMPLEMENTATION = "実装"
    TESTING = "テスト"
    PERFORMANCE = "パフォーマンス"
    SECURITY = "セキュリティ"
    DOCUMENTATION = "ドキュメント"
    OPERATIONS = "運用"
    PROCESS = "プロセス"


class ViolationType(Enum):
    """違反の種類"""

    # 実装の不完全性
    MOCK_IN_PRODUCTION = "本番コードにモック残存"
    INCOMPLETE_IMPLEMENTATION = "実装が不完全"
    MISSING_ERROR_HANDLING = "エラーハンドリング欠如"
    NO_TIMEOUT_HANDLING = "タイムアウト処理未実装"

    # テスト不足
    INSUFFICIENT_TEST_COVERAGE = "テストカバレッジ不足"
    NO_INTEGRATION_TESTS = "統合テスト未実施"
    NO_PRODUCTION_VERIFICATION = "本番環境検証未実施"

    # パフォーマンス問題
    PERFORMANCE_BELOW_THRESHOLD = "パフォーマンス基準未達"
    EXCESSIVE_MEMORY_USAGE = "メモリ使用量超過"
    SLOW_RESPONSE_TIME = "レスポンスタイム遅延"

    # セキュリティ問題
    HARDCODED_CREDENTIALS = "認証情報のハードコード"
    SQL_INJECTION_RISK = "SQLインジェクションリスク"
    MISSING_INPUT_VALIDATION = "入力検証の欠如"
    NO_AUTHENTICATION = "認証機能未実装"
    NO_AUTHORIZATION = "認可機能未実装"

    # ドキュメント不足
    MISSING_DOCUMENTATION = "必須ドキュメント欠如"
    INCOMPLETE_API_DOCS = "API仕様書不完全"
    NO_DEPLOYMENT_GUIDE = "デプロイガイド未作成"

    # 運用準備不足
    NO_MONITORING_SETUP = "監視設定未実施"
    NO_LOGGING_CONFIGURED = "ログ設定未実施"
    NO_ALERTING_RULES = "アラートルール未設定"

    # プロセス違反
    PREMATURE_COMPLETION_CLAIM = "早すぎる完了宣言"
    SKIPPED_REVIEW_PROCESS = "レビュープロセススキップ"
    NO_ELDER_COUNCIL_APPROVAL = "エルダー評議会未承認"


class ViolationDefinition:
    """違反の詳細定義"""

    DEFINITIONS: Dict[ViolationType, Dict] = {
        ViolationType.MOCK_IN_PRODUCTION: {
            "severity": ViolationSeverity.CRITICAL,
            "description": "本番環境で動作するコードにモックオブジェクトが含まれている",
            "detection_patterns": ["Mock", "mock", "@mock", "MagicMock"],
            "remediation": "全てのモックを実際の実装に置き換える",
        },
        ViolationType.INCOMPLETE_IMPLEMENTATION: {
            "severity": ViolationSeverity.HIGH,
            "description": "機能の一部が未実装またはTODOコメントが残っている",
            "detection_patterns": [
                "TODO",
                "FIXME",
                "NotImplementedError",
                "pass # TODO",
            ],
            "remediation": "全ての機能を完全に実装する",
        },
        ViolationType.MISSING_ERROR_HANDLING: {
            "severity": ViolationSeverity.HIGH,
            "description": "適切なエラーハンドリングが実装されていない",
            "detection_patterns": [
                "bare except:",
                "except Exception:",
                "no try-except blocks",
            ],
            "remediation": "具体的な例外タイプを捕捉し、適切に処理する",
        },
        ViolationType.INSUFFICIENT_TEST_COVERAGE: {
            "severity": ViolationSeverity.HIGH,
            "description": "テストカバレッジが95%未満",
            "detection_patterns": ["coverage < 95%"],
            "remediation": "テストを追加してカバレッジを95%以上にする",
        },
        ViolationType.NO_PRODUCTION_VERIFICATION: {
            "severity": ViolationSeverity.CRITICAL,
            "description": "本番環境での動作検証が実施されていない",
            "detection_patterns": ["no production test results"],
            "remediation": "本番環境で全機能の動作を検証する",
        },
        ViolationType.HARDCODED_CREDENTIALS: {
            "severity": ViolationSeverity.CRITICAL,
            "description": "パスワードやAPIキーがコードに直接記述されている",
            "detection_patterns": ["password =", "api_key =", "secret =", "token ="],
            "remediation": "環境変数や設定ファイルから読み込むように変更",
        },
        ViolationType.PERFORMANCE_BELOW_THRESHOLD: {
            "severity": ViolationSeverity.HIGH,
            "description": "レスポンスタイムやリソース使用量が基準を超えている",
            "detection_patterns": ["response_time > 200ms", "memory > 512MB"],
            "remediation": "パフォーマンスを最適化して基準内に収める",
        },
    }

    @classmethod
    def get_severity(cls, violation_type: ViolationType) -> ViolationSeverity:
        """違反タイプの重要度を取得"""
        return cls.DEFINITIONS.get(violation_type, {}).get(
            "severity", ViolationSeverity.MEDIUM
        )

    @classmethod
    def get_description(cls, violation_type: ViolationType) -> str:
        """違反タイプの説明を取得"""
        return cls.DEFINITIONS.get(violation_type, {}).get(
            "description", "詳細な説明がありません"
        )

    @classmethod
    def get_remediation(cls, violation_type: ViolationType) -> str:
        """修正方法を取得"""
        return cls.DEFINITIONS.get(violation_type, {}).get(
            "remediation", "適切な修正を実施してください"
        )

    @classmethod
    def is_blocking(cls, violation_type: ViolationType) -> bool:
        """完了をブロックする違反かどうか"""
        severity = cls.get_severity(violation_type)
        return severity in [ViolationSeverity.CRITICAL, ViolationSeverity.HIGH]
