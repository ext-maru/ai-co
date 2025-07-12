"""
Elder Flow Violation Detector のテスト
グランドエルダーmaruの完了基準を厳格に適用するシステムのテスト
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
from pathlib import Path
import json
import tempfile
import os

from libs.elder_flow_violation_detector import (
    ElderFlowViolationDetector,
    ElderFlowViolation,
    CompletionCriteria,
    TaskCompletionStatus
)


class TestCompletionCriteria:
    """完了基準クラスのテスト"""

    def test_completion_criteria_initialization(self):
        """初期化のテスト"""
        criteria = CompletionCriteria()

        # 全ての基準が初期状態でFalseであることを確認
        assert not criteria.unit_tests_pass
        assert not criteria.integration_tests_pass
        assert not criteria.production_ready
        assert not criteria.performance_verified
        assert not criteria.security_audited
        assert not criteria.error_handling_complete
        assert not criteria.documentation_complete
        assert not criteria.monitoring_configured
        assert not criteria.is_complete()

    def test_is_complete_all_true(self):
        """全ての基準を満たした場合のテスト"""
        criteria = CompletionCriteria()

        # 全ての基準をTrueに設定
        criteria.unit_tests_pass = True
        criteria.integration_tests_pass = True
        criteria.production_ready = True
        criteria.performance_verified = True
        criteria.security_audited = True
        criteria.error_handling_complete = True
        criteria.documentation_complete = True
        criteria.monitoring_configured = True

        assert criteria.is_complete()

    def test_is_complete_partial(self):
        """一部の基準のみ満たした場合のテスト"""
        criteria = CompletionCriteria()

        # 一部の基準のみTrueに設定
        criteria.unit_tests_pass = True
        criteria.integration_tests_pass = True

        assert not criteria.is_complete()

    def test_get_missing_criteria(self):
        """未達成基準の取得テスト"""
        criteria = CompletionCriteria()

        # 一部の基準のみ満たす
        criteria.unit_tests_pass = True
        criteria.production_ready = True

        missing = criteria.get_missing_criteria()

        assert "ユニットテスト" not in missing
        assert "本番環境準備" not in missing
        assert "統合テスト" in missing
        assert "パフォーマンス検証" in missing
        assert "セキュリティ監査" in missing
        assert "エラーハンドリング" in missing
        assert "ドキュメント" in missing
        assert "監視設定" in missing


class TestElderFlowViolationDetector:
    """Elder Flow Violation Detector のテスト"""

    @pytest.fixture
    def detector(self):
        """テスト用のDetectorインスタンス"""
        with tempfile.TemporaryDirectory() as temp_dir:
            detector = ElderFlowViolationDetector()
            detector.violation_log_path = Path(temp_dir) / "violations"
            yield detector

    @pytest.fixture
    def sample_test_results(self):
        """サンプルテスト結果"""
        return {
            "unit_test_coverage": 98,
            "integration_tests_passed": True,
            "performance_tests_passed": True
        }

    @pytest.fixture
    def sample_production_verification(self):
        """サンプル本番環境検証結果"""
        return {
            "all_features_working": True,
            "performance_metrics": {
                "response_time_ms": 150,
                "memory_usage_mb": 256
            },
            "error_rate": 0.01
        }

    def test_detector_initialization(self, detector):
        """初期化のテスト"""
        assert detector.violation_log_path.exists()
        assert isinstance(detector.knowledge_sage_criteria, dict)
        assert isinstance(detector.incident_patterns, list)
        assert "required_test_coverage" in detector.knowledge_sage_criteria
        assert detector.knowledge_sage_criteria["required_test_coverage"] == 95

    @pytest.mark.asyncio
    async def test_successful_validation(self, detector, sample_test_results, sample_production_verification):
        """成功する検証のテスト"""
        with patch.object(detector, '_analyze_code_quality', return_value=[]), \
             patch.object(detector, '_security_audit', return_value=[]), \
             patch.object(detector, '_check_documentation', return_value=[]):

            result = await detector.validate_completion_claim(
                task_id="TEST-001",
                implementation_path="libs/test_feature.py",
                test_results=sample_test_results,
                production_verification=sample_production_verification
            )

            assert result["approved"] is True
            assert "verification_record" in result
            assert result["verification_record"]["status"] == TaskCompletionStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_validation_with_low_coverage(self, detector, sample_production_verification):
        """カバレッジ不足での検証テスト"""
        low_coverage_results = {
            "unit_test_coverage": 80,  # 95%未満
            "integration_tests_passed": True
        }

        with pytest.raises(ElderFlowViolation) as exc_info:
            await detector.validate_completion_claim(
                task_id="TEST-002",
                implementation_path="libs/test_feature.py",
                test_results=low_coverage_results,
                production_verification=sample_production_verification
            )

        assert "ユニットテストカバレッジ不足" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_without_production_verification(self, detector, sample_test_results):
        """本番環境検証なしでの検証テスト"""
        with pytest.raises(ElderFlowViolation) as exc_info:
            await detector.validate_completion_claim(
                task_id="TEST-003",
                implementation_path="libs/test_feature.py",
                test_results=sample_test_results,
                production_verification=None
            )

        assert "本番環境での動作検証が未実施" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_with_poor_performance(self, detector, sample_test_results):
        """パフォーマンス不足での検証テスト"""
        poor_performance_verification = {
            "all_features_working": True,
            "performance_metrics": {
                "response_time_ms": 500,  # 200ms超過
                "memory_usage_mb": 256
            }
        }

        with pytest.raises(ElderFlowViolation) as exc_info:
            await detector.validate_completion_claim(
                task_id="TEST-004",
                implementation_path="libs/test_feature.py",
                test_results=sample_test_results,
                production_verification=poor_performance_verification
            )

        assert "パフォーマンス基準を満たしていない" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_code_quality_analysis(self, detector):
        """コード品質分析のテスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            # モックオブジェクトを含むコード
            tmp_file.write("""
import mock
from unittest.mock import Mock

# TODO: この機能を実装する
def test_function():
    pass
""")
            tmp_file.flush()

            try:
                issues = await detector._analyze_code_quality(tmp_file.name)

                # モック使用とTODOコメントが検出されることを確認
                assert any("モックオブジェクト" in issue for issue in issues)
                assert any("TODO/FIXME" in issue for issue in issues)
            finally:
                os.unlink(tmp_file.name)

    @pytest.mark.asyncio
    async def test_code_quality_analysis_with_try_except(self, detector):
        """エラーハンドリング有りのコード品質分析テスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write("""
def good_function():
    try:
        result = risky_operation()
        return result
    except ValueError as e:
        print(f"Error: {e}")
        return None
""")
            tmp_file.flush()

            try:
                issues = await detector._analyze_code_quality(tmp_file.name)

                # エラーハンドリングが実装されているので、関連する問題は検出されない
                assert not any("エラーハンドリング" in issue for issue in issues)
            finally:
                os.unlink(tmp_file.name)

    @pytest.mark.asyncio
    async def test_security_audit(self, detector):
        """セキュリティ監査のテスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write("""
# セキュリティ問題のあるコード
password = "secret123"
api_key = "sk-1234567890"
query = f"SELECT * FROM users WHERE id = {user_id}"
""")
            tmp_file.flush()

            try:
                issues = await detector._security_audit(tmp_file.name)

                # セキュリティ問題が検出されることを確認
                assert any("パスワード" in issue for issue in issues)
                assert any("APIキー" in issue for issue in issues)
                assert any("SQLインジェクション" in issue for issue in issues)
            finally:
                os.unlink(tmp_file.name)

    def test_check_documentation(self, detector):
        """ドキュメントチェックのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("# test file")

            # 必須ドキュメントが存在しない場合
            issues = detector._check_documentation(str(test_file))

            # 4つの必須ドキュメントすべてが不足していることを確認
            assert len(issues) == 4
            assert any("README.md" in issue for issue in issues)
            assert any("API_DOCUMENTATION.md" in issue for issue in issues)
            assert any("DEPLOYMENT_GUIDE.md" in issue for issue in issues)
            assert any("TROUBLESHOOTING.md" in issue for issue in issues)

    def test_check_documentation_with_existing_docs(self, detector):
        """既存ドキュメントありのドキュメントチェック"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("# test file")

            # 必須ドキュメントを作成
            (Path(temp_dir) / "README.md").write_text("# README")
            (Path(temp_dir) / "API_DOCUMENTATION.md").write_text("# API")
            (Path(temp_dir) / "DEPLOYMENT_GUIDE.md").write_text("# Deploy")
            (Path(temp_dir) / "TROUBLESHOOTING.md").write_text("# Troubleshoot")

            issues = detector._check_documentation(str(test_file))

            # ドキュメントが存在するので問題なし
            assert len(issues) == 0

    def test_generate_verification_id(self, detector):
        """検証ID生成のテスト"""
        verification_id = detector._generate_verification_id()

        assert verification_id.startswith("ELDER_VERIFY_")
        assert len(verification_id.split("_")) == 3

    def test_log_violation(self, detector):
        """違反ログのテスト"""
        violations = ["テストカバレッジ不足", "本番環境未検証"]
        warnings = ["ドキュメント不完全"]

        detector._log_violation("TEST-LOG", violations, warnings)

        # ログファイルが作成されることを確認
        log_files = list(detector.violation_log_path.glob("violation_TEST-LOG_*.json"))
        assert len(log_files) == 1

        # ログ内容を確認
        with open(log_files[0], 'r') as f:
            log_data = json.load(f)

        assert log_data["task_id"] == "TEST-LOG"
        assert log_data["violations"] == violations
        assert log_data["warnings"] == warnings
        assert log_data["status"] == TaskCompletionStatus.REJECTED.value

    def test_save_verification_record(self, detector):
        """承認記録保存のテスト"""
        record = {
            "task_id": "TEST-SAVE",
            "verification_id": "ELDER_VERIFY_20231201_120000",
            "status": TaskCompletionStatus.COMPLETED.value,
            "timestamp": datetime.now().isoformat()
        }

        detector._save_verification_record(record)

        # 承認記録ファイルが作成されることを確認
        verification_path = Path("knowledge_base/elder_flow_verifications/")
        verification_files = list(verification_path.glob("verification_ELDER_VERIFY_*.json"))
        assert len(verification_files) >= 1

        # 最新のファイル内容を確認
        with open(verification_files[-1], 'r') as f:
            saved_data = json.load(f)

        assert saved_data["task_id"] == "TEST-SAVE"
        assert saved_data["verification_id"] == "ELDER_VERIFY_20231201_120000"


class TestExampleUsage:
    """使用例のテスト"""

    @pytest.mark.asyncio
    async def test_example_usage_success(self):
        """成功例の使用テスト"""
        detector = ElderFlowViolationDetector()

        test_results = {
            "unit_test_coverage": 98,
            "integration_tests_passed": True,
            "performance_tests_passed": True
        }

        production_verification = {
            "all_features_working": True,
            "performance_metrics": {
                "response_time_ms": 150,
                "memory_usage_mb": 256
            },
            "error_rate": 0.01
        }

        with patch.object(detector, '_analyze_code_quality', return_value=[]), \
             patch.object(detector, '_security_audit', return_value=[]), \
             patch.object(detector, '_check_documentation', return_value=[]):

            result = await detector.validate_completion_claim(
                task_id="EXAMPLE-SUCCESS",
                implementation_path="libs/example_feature.py",
                test_results=test_results,
                production_verification=production_verification
            )

            assert result["approved"] is True
            assert "完全な実装です" in result["message"]

    @pytest.mark.asyncio
    async def test_example_usage_failure(self):
        """失敗例の使用テスト"""
        detector = ElderFlowViolationDetector()

        test_results = {
            "unit_test_coverage": 70,  # 不足
            "integration_tests_passed": False
        }

        with pytest.raises(ElderFlowViolation) as exc_info:
            await detector.validate_completion_claim(
                task_id="EXAMPLE-FAIL",
                implementation_path="libs/example_feature.py",
                test_results=test_results,
                production_verification=None
            )

        error_message = str(exc_info.value)
        assert "完了報告は認められません" in error_message
        assert "違反事項:" in error_message


class TestTaskCompletionStatus:
    """タスク完了状態のテスト"""

    def test_status_enum_values(self):
        """ステータス列挙型の値のテスト"""
        assert TaskCompletionStatus.IN_DEVELOPMENT.value == "開発中"
        assert TaskCompletionStatus.IN_VERIFICATION.value == "検証中"
        assert TaskCompletionStatus.COMPLETED.value == "完了"
        assert TaskCompletionStatus.REJECTED.value == "却下"


class TestElderFlowViolationException:
    """Elder Flow Violation 例外のテスト"""

    def test_exception_creation(self):
        """例外作成のテスト"""
        message = "テスト違反です"
        exception = ElderFlowViolation(message)

        assert str(exception) == message
        assert isinstance(exception, Exception)

    def test_exception_raising(self):
        """例外発生のテスト"""
        with pytest.raises(ElderFlowViolation) as exc_info:
            raise ElderFlowViolation("テスト例外")

        assert str(exc_info.value) == "テスト例外"


@pytest.mark.asyncio
async def test_main_example():
    """メイン例のテスト"""
    # example_usage関数を直接テストする代わりに、同様の処理をテスト
    from libs.elder_flow_violation_detector import example_usage

    # 実際の実行はパッチで制御
    with patch('libs.elder_flow_violation_detector.ElderFlowViolationDetector') as mock_detector_class:
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector

        # 成功ケースをモック
        mock_detector.validate_completion_claim.return_value = {
            "approved": True,
            "message": "グランドエルダーmaruの基準を満たす完全な実装です。"
        }

        # example_usage を実行（出力を確認するため、標準出力をキャプチャ）
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            await example_usage()
            output = captured_output.getvalue()
            assert "完了承認" in output
        finally:
            sys.stdout = sys.__stdout__
