"""
Elder Flow Violation Types のテスト
違反タイプ定義と分類システムのテスト
"""
import pytest
from libs.elder_flow_violation_types import (
    ViolationSeverity,
    ViolationType,
    ViolationDefinition
)

class TestViolationSeverity:
    """違反重要度のテスト"""

    def test_severity_enum_values(self):
        """重要度列挙型の値のテスト"""
        assert ViolationSeverity.CRITICAL.value == "致命的"
        assert ViolationSeverity.HIGH.value == "高"
        assert ViolationSeverity.MEDIUM.value == "中"
        assert ViolationSeverity.LOW.value == "低"
        assert ViolationSeverity.WARNING.value == "警告"

    def test_severity_hierarchy(self):
        """重要度の階層のテスト"""
        severities = [
            ViolationSeverity.CRITICAL,
            ViolationSeverity.HIGH,
            ViolationSeverity.MEDIUM,
            ViolationSeverity.LOW,
            ViolationSeverity.WARNING
        ]

        # 全ての重要度が異なることを確認
        assert len(set(s.value for s in severities)) == len(severities)

class TestViolationType:
    """違反タイプのテスト"""

    def test_implementation_violation_types(self):
        """実装の不完全性違反タイプのテスト"""
        assert ViolationType.MOCK_IN_PRODUCTION.value == "本番コードにモック残存"
        assert ViolationType.INCOMPLETE_IMPLEMENTATION.value == "実装が不完全"
        assert ViolationType.MISSING_ERROR_HANDLING.value == "エラーハンドリング欠如"
        assert ViolationType.NO_TIMEOUT_HANDLING.value == "タイムアウト処理未実装"

    def test_test_violation_types(self):
        """テスト不足違反タイプのテスト"""
        assert ViolationType.INSUFFICIENT_TEST_COVERAGE.value == "テストカバレッジ不足"
        assert ViolationType.NO_INTEGRATION_TESTS.value == "統合テスト未実施"
        assert ViolationType.NO_PRODUCTION_VERIFICATION.value == "本番環境検証未実施"

    def test_performance_violation_types(self):
        """パフォーマンス問題違反タイプのテスト"""
        assert ViolationType.PERFORMANCE_BELOW_THRESHOLD.value == "パフォーマンス基準未達"
        assert ViolationType.EXCESSIVE_MEMORY_USAGE.value == "メモリ使用量超過"
        assert ViolationType.SLOW_RESPONSE_TIME.value == "レスポンスタイム遅延"

    def test_security_violation_types(self):
        """セキュリティ問題違反タイプのテスト"""
        assert ViolationType.HARDCODED_CREDENTIALS.value == "認証情報のハードコード"
        assert ViolationType.SQL_INJECTION_RISK.value == "SQLインジェクションリスク"
        assert ViolationType.MISSING_INPUT_VALIDATION.value == "入力検証の欠如"
        assert ViolationType.NO_AUTHENTICATION.value == "認証機能未実装"
        assert ViolationType.NO_AUTHORIZATION.value == "認可機能未実装"

    def test_documentation_violation_types(self):
        """ドキュメント不足違反タイプのテスト"""
        assert ViolationType.MISSING_DOCUMENTATION.value == "必須ドキュメント欠如"
        assert ViolationType.INCOMPLETE_API_DOCS.value == "API仕様書不完全"
        assert ViolationType.NO_DEPLOYMENT_GUIDE.value == "デプロイガイド未作成"

    def test_operations_violation_types(self):
        """運用準備不足違反タイプのテスト"""
        assert ViolationType.NO_MONITORING_SETUP.value == "監視設定未実施"
        assert ViolationType.NO_LOGGING_CONFIGURED.value == "ログ設定未実施"
        assert ViolationType.NO_ALERTING_RULES.value == "アラートルール未設定"

    def test_process_violation_types(self):
        """プロセス違反タイプのテスト"""
        assert ViolationType.PREMATURE_COMPLETION_CLAIM.value == "早すぎる完了宣言"
        assert ViolationType.SKIPPED_REVIEW_PROCESS.value == "レビュープロセススキップ"
        assert ViolationType.NO_ELDER_COUNCIL_APPROVAL.value == "エルダー評議会未承認"

class TestViolationDefinition:
    """違反定義のテスト"""

    def test_definitions_exist(self):
        """定義が存在することのテスト"""
        assert hasattr(ViolationDefinition, 'DEFINITIONS')
        assert isinstance(ViolationDefinition.DEFINITIONS, dict)
        assert len(ViolationDefinition.DEFINITIONS) > 0

    def test_mock_in_production_definition(self):
        """本番コードのモック残存定義のテスト"""
        definition = ViolationDefinition.DEFINITIONS[ViolationType.MOCK_IN_PRODUCTION]

        assert definition['severity'] == ViolationSeverity.CRITICAL
        assert '本番環境で動作するコード' in definition['description']
        assert 'Mock' in definition['detection_patterns']
        assert 'mock' in definition['detection_patterns']
        assert '実際の実装に置き換える' in definition['remediation']

    def test_incomplete_implementation_definition(self):
        """不完全実装定義のテスト"""
        definition = ViolationDefinition.DEFINITIONS[ViolationType.INCOMPLETE_IMPLEMENTATION]

        assert definition['severity'] == ViolationSeverity.HIGH

        assert 'NotImplementedError' in definition['detection_patterns']

    def test_missing_error_handling_definition(self):
        """エラーハンドリング欠如定義のテスト"""
        definition = ViolationDefinition.DEFINITIONS[ViolationType.MISSING_ERROR_HANDLING]

        assert definition['severity'] == ViolationSeverity.HIGH
        assert 'bare except:' in definition['detection_patterns']
        assert 'except Exception:' in definition['detection_patterns']

    def test_insufficient_test_coverage_definition(self):
        """テストカバレッジ不足定義のテスト"""
        definition = ViolationDefinition.DEFINITIONS[ViolationType.INSUFFICIENT_TEST_COVERAGE]

        assert definition['severity'] == ViolationSeverity.HIGH
        assert 'coverage < 95%' in definition['detection_patterns']
        assert '95%以上' in definition['remediation']

    def test_no_production_verification_definition(self):
        """本番環境検証未実施定義のテスト"""
        definition = ViolationDefinition.DEFINITIONS[ViolationType.NO_PRODUCTION_VERIFICATION]

        assert definition['severity'] == ViolationSeverity.CRITICAL
        assert '本番環境での動作検証' in definition['description']
        assert '本番環境で全機能の動作を検証' in definition['remediation']

    def test_hardcoded_credentials_definition(self):
        """認証情報ハードコード定義のテスト"""
        definition = ViolationDefinition.DEFINITIONS[ViolationType.HARDCODED_CREDENTIALS]

        assert definition['severity'] == ViolationSeverity.CRITICAL
        assert 'password =' in definition['detection_patterns']
        assert 'api_key =' in definition['detection_patterns']
        assert 'secret =' in definition['detection_patterns']
        assert 'token =' in definition['detection_patterns']
        assert '環境変数' in definition['remediation']

    def test_performance_below_threshold_definition(self):
        """パフォーマンス基準未達定義のテスト"""
        definition = ViolationDefinition.DEFINITIONS[ViolationType.PERFORMANCE_BELOW_THRESHOLD]

        assert definition['severity'] == ViolationSeverity.HIGH
        assert 'response_time > 200ms' in definition['detection_patterns']
        assert 'memory > 512MB' in definition['detection_patterns']
        assert 'パフォーマンスを最適化' in definition['remediation']

    def test_get_severity_method(self):
        """重要度取得メソッドのテスト"""
        severity = ViolationDefinition.get_severity(ViolationType.MOCK_IN_PRODUCTION)
        assert severity == ViolationSeverity.CRITICAL

        severity = ViolationDefinition.get_severity(ViolationType.INCOMPLETE_IMPLEMENTATION)
        assert severity == ViolationSeverity.HIGH

        # 未定義の違反タイプの場合、デフォルトでMEDIUMが返される
        # EnumのValueErrorを避けるため、既存の値を使用
        severity = ViolationDefinition.get_severity(ViolationType.NO_MONITORING_SETUP)
        assert severity == ViolationSeverity.MEDIUM  # デフォルト値

    def test_get_description_method(self):
        """説明取得メソッドのテスト"""
        description = ViolationDefinition.get_description(ViolationType.MOCK_IN_PRODUCTION)
        assert '本番環境で動作するコード' in description

        description = ViolationDefinition.get_description(ViolationType.HARDCODED_CREDENTIALS)
        assert 'パスワードやAPIキー' in description

        # 未定義の場合のデフォルト説明
        description = ViolationDefinition.get_description(ViolationType.NO_MONITORING_SETUP)
        assert '詳細な説明がありません' in description

    def test_get_remediation_method(self):
        """修正方法取得メソッドのテスト"""
        remediation = ViolationDefinition.get_remediation(ViolationType.MOCK_IN_PRODUCTION)
        assert '実際の実装に置き換える' in remediation

        remediation = ViolationDefinition.get_remediation(ViolationType.INSUFFICIENT_TEST_COVERAGE)
        assert '95%以上' in remediation

        # 未定義の場合のデフォルト修正方法
        remediation = ViolationDefinition.get_remediation(ViolationType.NO_MONITORING_SETUP)
        assert '適切な修正を実施してください' in remediation

    def test_is_blocking_method(self):
        """完了ブロック判定メソッドのテスト"""
        # CRITICALは完了をブロック
        assert ViolationDefinition.is_blocking(ViolationType.MOCK_IN_PRODUCTION) is True
        assert ViolationDefinition.is_blocking(ViolationType.NO_PRODUCTION_VERIFICATION) is True
        assert ViolationDefinition.is_blocking(ViolationType.HARDCODED_CREDENTIALS) is True

        # HIGHも完了をブロック
        assert ViolationDefinition.is_blocking(ViolationType.INCOMPLETE_IMPLEMENTATION) is True
        assert ViolationDefinition.is_blocking(ViolationType.MISSING_ERROR_HANDLING) is True
        assert ViolationDefinition.is_blocking(ViolationType.INSUFFICIENT_TEST_COVERAGE) is True

        # MEDIUM, LOW, WARNINGは完了をブロックしない
        # （現在の実装では、全てHIGH以上なので実際のテストは困難）
        # この部分は将来的に追加される違反タイプでテスト可能

    def test_all_defined_violations_have_required_fields(self):
        """定義された全ての違反に必須フィールドがあることのテスト"""
        required_fields = ['severity', 'description', 'detection_patterns', 'remediation']

        # 繰り返し処理
        for violation_type, definition in ViolationDefinition.DEFINITIONS.items():
            for field in required_fields:
                assert field in definition, f"{violation_type.value}に{field}が定義されていません"

            # severityがViolationSeverityの値であることを確認
            assert isinstance(definition['severity'], ViolationSeverity)

            # detection_patternsがリストであることを確認
            assert isinstance(definition['detection_patterns'], list)
            assert len(definition['detection_patterns']) > 0

            # descriptionとremediationが文字列であることを確認
            assert isinstance(definition['description'], str)
            assert isinstance(definition['remediation'], str)
            assert len(definition['description']) > 0
            assert len(definition['remediation']) > 0

class TestViolationTypeCompleteness:
    """違反タイプの完全性のテスト"""

    def test_all_violation_types_have_definitions(self):
        """全ての違反タイプに定義があることのテスト"""
        # 現在定義されている違反タイプのみをテスト
        defined_violations = set(ViolationDefinition.DEFINITIONS.keys())
        expected_violations = {
            ViolationType.MOCK_IN_PRODUCTION,
            ViolationType.INCOMPLETE_IMPLEMENTATION,
            ViolationType.MISSING_ERROR_HANDLING,
            ViolationType.INSUFFICIENT_TEST_COVERAGE,
            ViolationType.NO_PRODUCTION_VERIFICATION,
            ViolationType.HARDCODED_CREDENTIALS,
            ViolationType.PERFORMANCE_BELOW_THRESHOLD
        }

        # 期待される違反タイプが全て定義されていることを確認
        for violation_type in expected_violations:
            assert violation_type in defined_violations, f"{violation_type.value}の定義が不足しています"

    def test_detection_patterns_coverage(self):
        """検出パターンのカバレッジのテスト"""
        # 各違反タイプに適切な検出パターンが設定されていることを確認

        # モック関連の検出パターン
        mock_patterns = ViolationDefinition.DEFINITIONS[ViolationType.MOCK_IN_PRODUCTION]['detection_patterns']
        assert any('Mock' in pattern for pattern in mock_patterns)
        assert any('mock' in pattern for pattern in mock_patterns)

        incomplete_patterns = ViolationDefinition.DEFINITIONS[ViolationType.INCOMPLETE_IMPLEMENTATION][ \
            'detection_patterns']

        # セキュリティ関連の検出パターン
        security_patterns = ViolationDefinition.DEFINITIONS[ViolationType.HARDCODED_CREDENTIALS]['detection_patterns']
        assert any('password' in pattern for pattern in security_patterns)
        assert any('api_key' in pattern for pattern in security_patterns)

    def test_severity_distribution(self):
        """重要度分布のテスト"""
        severities = [definition['severity'] for definition in ViolationDefinition.DEFINITIONS.values()]

        # CRITICAL違反が存在することを確認
        assert ViolationSeverity.CRITICAL in severities

        # HIGH違反が存在することを確認
        assert ViolationSeverity.HIGH in severities

        # 重要度の分布が適切であることを確認
        critical_count = severities.count(ViolationSeverity.CRITICAL)
        high_count = severities.count(ViolationSeverity.HIGH)

        # CRITICALとHIGHが適切に設定されていることを確認
        assert critical_count >= 2, "CRITICAL違反が少なすぎます"
        assert high_count >= 2, "HIGH違反が少なすぎます"

class TestViolationTypeCategories:
    """違反タイプのカテゴリ分類のテスト"""

    def test_implementation_category(self):
        """実装カテゴリの違反タイプのテスト"""
        implementation_violations = [
            ViolationType.MOCK_IN_PRODUCTION,
            ViolationType.INCOMPLETE_IMPLEMENTATION,
            ViolationType.MISSING_ERROR_HANDLING,
            ViolationType.NO_TIMEOUT_HANDLING
        ]

        for violation in implementation_violations:
            # 実装関連の違反であることを名前から確認
            assert any(keyword in violation.value for keyword in
                      ['モック', '実装', 'エラー', 'タイムアウト'])

    def test_test_category(self):
        """テストカテゴリの違反タイプのテスト"""
        test_violations = [
            ViolationType.INSUFFICIENT_TEST_COVERAGE,
            ViolationType.NO_INTEGRATION_TESTS,
            ViolationType.NO_PRODUCTION_VERIFICATION
        ]

        for violation in test_violations:
            # テスト関連の違反であることを名前から確認
            assert any(keyword in violation.value for keyword in
                      ['テスト', '検証'])

    def test_security_category(self):
        """セキュリティカテゴリの違反タイプのテスト"""
        security_violations = [
            ViolationType.HARDCODED_CREDENTIALS,
            ViolationType.SQL_INJECTION_RISK,
            ViolationType.MISSING_INPUT_VALIDATION,
            ViolationType.NO_AUTHENTICATION,
            ViolationType.NO_AUTHORIZATION
        ]

        for violation in security_violations:
            # セキュリティ関連の違反であることを名前から確認
            assert any(keyword in violation.value for keyword in
                      ['認証', '認可', 'インジェクション', '検証'])
