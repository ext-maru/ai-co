#!/usr/bin/env python3
"""
エルダーズギルド ドキュメント分類システム テストスイート
Iron Will準拠 - TDD実装

テスト対象:
- SecureDocumentClassifier
- セキュリティ機能
- 4賢者システム統合
- Iron Will基準遵守
"""

import pytest

import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# テスト対象のインポート
sys.path.insert(0, '/home/aicompany/ai_co')
sys.path.insert(0, '/home/aicompany/ai_co/scripts/docs')
from classify_documents_enhanced import (
    SecureDocumentClassifier, 
    DocumentInfo, 
    ClassificationResult,
    FORBIDDEN_PATTERNS,
    SECURITY_RISK_PATTERNS
)

class TestSecureDocumentClassifier:
    """セキュアドキュメント分類器テストクラス"""
    
    @pytest.fixture

        """テスト用一時ディレクトリ"""

    @pytest.fixture

        """テスト用分類器インスタンス"""
        with patch('scripts.docs.classify_documents_enhanced.FOUR_SAGES_AVAILABLE', False):

    @pytest.fixture

        """サンプルMarkdownファイル作成"""
        files = {}
        
        # 正常ファイル

        files['guide'].write_text("# User Guide\nThis is a basic user guide.")
        
        # 技術文書

        files['technical'].write_text("# System Architecture\nDetailed system design.")
        
        # レポート

        files['report'].write_text("# Completion Report\nProject completion analysis.")
        
        # セキュリティ違反ファイル

        files['security_risk'].write_text("# Risky File\neval('dangerous code')")
        
        # Iron Will違反ファイル

        return files

class TestSecurityValidation:
    """セキュリティ検証テスト"""

        """正常ファイルのセキュリティ検証"""

        normal_file.write_text("# Normal Document\nThis is safe content.")
        
        is_secure, violations, score = classifier.validate_security(
            normal_file,
            "# Normal Document\nThis is safe content."
        )
        
        assert is_secure is True
        assert len(violations) == 0
        assert score == 100.0

        """パストラバーサル攻撃検証"""

        is_secure, violations, score = classifier.validate_security(malicious_path, "safe content")
        
        assert is_secure is False
        assert any("パストラバーサル" in v for v in violations)
        assert score < 100.0

        """禁止文字検証"""

        bad_file.write_text("content")
        
        is_secure, violations, score = classifier.validate_security(bad_file, "content")
        
        assert is_secure is False
        assert any("禁止文字" in v for v in violations)

        """セキュリティリスクパターン検証"""
        risky_content = "# Dangerous\neval('malicious code')\nos.system('rm -rf /')"

        risky_file.write_text(risky_content)
        
        is_secure, violations, score = classifier.validate_security(risky_file, risky_content)
        
        assert is_secure is False
        assert len(violations) >= 2  # eval と os.system
        assert score < 70.0

        """Iron Will違反検証"""

        violation_file.write_text(iron_will_content)
        
        is_secure, violations, score = classifier.validate_security(violation_file, iron_will_content)
        
        iron_will_violations = [v for v in violations if "Iron Will" in v]

class TestSecurePathJoin:
    """セキュアパス結合テスト"""

        """正常パス結合"""

        assert result is not None

        assert "docs/guides/user-guide.md" in str(result)

        """パストラバーサル攻撃阻止"""

        assert result is None  # 攻撃を阻止

        """危険文字除去"""

        assert result is not None
        assert ".." not in str(result)
        assert "~" not in str(result)

        """URLデコード処理"""

        assert result is not None
        assert "docs" in str(result)
        assert "file name" in str(result)

class TestDocumentClassification:
    """ドキュメント分類テスト"""

        """ガイドドキュメント分類"""

        guide_file.write_text("# Quickstart Guide\nGetting started quickly.")
        
        doc_info = classifier.classify_document(guide_file)
        
        assert doc_info is not None
        assert doc_info.category == "guides"
        assert doc_info.subcategory == "user-guides"
        assert doc_info.sage_assignment == "knowledge_sage"

        """技術文書分類"""

        tech_file.write_text("# System Architecture\nTechnical design overview.")
        
        doc_info = classifier.classify_document(tech_file)
        
        assert doc_info is not None
        assert doc_info.category == "technical"
        assert doc_info.subcategory == "architecture"
        assert doc_info.sage_assignment == "rag_sage"

        """レポート分類"""

        report_file.write_text("# Completion Report\nProject completion analysis.")
        
        doc_info = classifier.classify_document(report_file)
        
        assert doc_info is not None
        assert doc_info.category == "reports"
        assert doc_info.sage_assignment == "task_sage"

        """ポリシー文書分類"""

        policy_file.write_text("# Coding Standards\nDevelopment policies and standards.")
        
        doc_info = classifier.classify_document(policy_file)
        
        assert doc_info is not None
        assert doc_info.category == "technical"  # patterns不一致のため
        assert doc_info.sage_assignment == "rag_sage"

        """セキュリティ違反文書分類"""

        risky_file.write_text(risky_content)
        
        doc_info = classifier.classify_document(risky_file)
        
        assert doc_info is not None
        assert doc_info.status == "security_review"
        assert doc_info.security_score < 70.0
        assert doc_info.iron_will_compliant is False

class TestFileOperations:
    """ファイル操作テスト"""

        """正常なファイル移動"""

        source.write_text("# Source\nContent")

        dest_dir.mkdir()
        destination = dest_dir / "moved.md"
        
        success = classifier.secure_move_file(source, destination)
        
        assert success is True
        assert not source.exists()
        assert destination.exists()
        assert destination.read_text() == "# Source\nContent"

        """重複ファイル名処理"""

        source.write_text("# Source\nContent")

        dest_dir.mkdir()
        existing = dest_dir / "target.md"
        existing.write_text("existing")
        
        destination = dest_dir / "target.md"
        success = classifier.secure_move_file(source, destination)
        
        assert success is True
        assert not source.exists()
        assert existing.exists()  # 既存ファイルはそのまま
        
        # 新しいファイルが別名で作成されている
        moved_files = list(dest_dir.glob("target*.md"))
        assert len(moved_files) == 2

        """存在しないファイルの移動"""

        success = classifier.secure_move_file(nonexistent, destination)
        
        assert success is False
        assert not destination.exists()

class TestMetadataGeneration:
    """メタデータ生成テスト"""
    
    def test_generate_metadata_complete(self, classifier):
        """完全なメタデータ生成"""
        doc_info = DocumentInfo(
            path=Path("/test/path.md"),
            category="guides",
            subcategory="user-guides",
            new_path=Path("/test/new-path.md"),
            title="Test Guide",
            audience="users",
            difficulty="beginner",
            status="approved",
            sage_assignment="knowledge_sage",
            security_score=95.0,
            iron_will_compliant=True
        )
        
        content = "# Test Guide\nThis is a test guide document."
        result = classifier.generate_metadata(doc_info, content)
        
        assert result.startswith("---\n")
        assert "title: Test Guide" in result
        assert "category: guides" in result
        assert "sage_assignment: knowledge_sage" in result
        assert "security_score: 95.0" in result
        assert "iron_will_compliant: true" in result
        assert content in result
    
    def test_extract_description_safe(self, classifier):
        """安全な説明抽出"""
        content = "# Title\nThis is a description with <script>alert('xss')</script> content."
        description = classifier._extract_description(content)
        
        assert "script" not in description  # 危険文字除去
        assert len(description) <= 200     # 長さ制限

class TestFilenameGeneration:
    """ファイル名生成テスト"""
    
    def test_generate_secure_filename_normal(self, classifier):
        """正常なファイル名生成"""
        result = classifier._generate_secure_filename("User Guide.md", "guides", "user-guides")
        
        assert result == "user-guide.md"
        assert not any(char in result for char in ['<', '>', ':', '"', '|', '?', '*', '\\'])
    
    def test_generate_secure_filename_dangerous_chars(self, classifier):
        """危険文字除去"""
        dangerous_name = "file<>:\"|?*\\.md"
        result = classifier._generate_secure_filename(dangerous_name, "guides", "user-guides")
        
        assert not any(char in result for char in ['<', '>', ':', '"', '|', '?', '*', '\\'])
        assert result.endswith('.md')
    
    def test_generate_secure_filename_length_limit(self, classifier):
        """長さ制限"""
        long_name = "very-" * 50 + "long-filename.md"  # 200文字以上
        result = classifier._generate_secure_filename(long_name, "guides", "user-guides")
        
        assert len(result) <= 103  # 100 + ".md"
    
    def test_generate_secure_filename_empty_fallback(self, classifier):
        """空の場合のフォールバック"""
        result = classifier._generate_secure_filename("....md", "guides", "user-guides")
        
        assert result.startswith("document-")
        assert result.endswith(".md")
        assert len(result) == 21  # "document-" + 8文字ハッシュ + ".md"

class TestIntegrationTests:
    """統合テスト"""

        """完全な分類ワークフロー"""
        # サンプルファイル作成
        files = {

        }
        
        for file_path in files.values():
            file_path.write_text(f"# {file_path.stem.title()}\nContent for {file_path.name}")
        
        # 分類実行（ドライラン）
        result = classifier.classify_and_move_secure(dry_run=True, add_metadata=False)
        
        assert result.total_files == 3
        assert result.processed_files == 3
        assert result.moved_files == 3
        assert result.error_files == 0
        assert result.security_violations == 0
        assert result.iron_will_violations == 0

        """セキュリティ違反処理"""
        # セキュリティ違反ファイル

        risky_file.write_text(risky_content)
        
        result = classifier.classify_and_move_secure(dry_run=True)
        
        assert result.security_violations > 0
        assert result.iron_will_violations > 0

class TestFourSagesIntegration:
    """4賢者システム統合テスト"""
    
    @patch('scripts.docs.classify_documents_enhanced.FOUR_SAGES_AVAILABLE', True)

        """賢者割り当てテスト"""
        with patch('scripts.docs.classify_documents_enhanced.KnowledgeSage') as mock_sage:
            mock_sage.return_value = Mock()

            guide_file.write_text("# User Guide\nBasic guide content.")
            
            doc_info = classifier.classify_document(guide_file)
            
            assert doc_info.sage_assignment == "knowledge_sage"
    
    def test_sage_notification(self, classifier):
        """賢者通知テスト"""
        mock_sage = Mock()
        mock_sage.notify_document_change = Mock()
        classifier.sages = {'knowledge_sage': mock_sage}
        
        doc_info = DocumentInfo(
            path=Path("/test.md"),
            category="guides",
            subcategory="user-guides", 
            new_path=Path("/new-test.md"),
            title="Test",
            audience="users",
            difficulty="beginner",
            status="approved",
            sage_assignment="knowledge_sage",
            security_score=100.0,
            iron_will_compliant=True
        )
        
        success = classifier.notify_four_sages(doc_info, "document_moved")
        
        assert success is True
        mock_sage.notify_document_change.assert_called_once()

class TestPerformance:
    """パフォーマンステスト"""

        """大容量ファイル処理"""

        large_content = "# Large File\n" + "x" * (10 * 1024 * 1024)  # 10MB
        large_file.write_text(large_content)
        
        # セキュリティ検証でサイズ制限に引っかかることを確認
        is_secure, violations, score = classifier.validate_security(large_file, large_content)
        
        assert is_secure is False
        assert any("ファイルサイズ超過" in v for v in violations)

        """バッチ処理性能"""
        import time
        
        # 100個のサンプルファイル作成
        files = []
        for i in range(100):

            file_path.write_text(f"# Test File {i}\nContent for file {i}")
            files.append(file_path)
        
        start_time = time.time()
        result = classifier.classify_and_move_secure(dry_run=True)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert result.total_files == 100
        assert processing_time < 10.0  # 10秒以内で完了
        assert result.processed_files > 90  # 90%以上成功

# TDDスタイルテストランナー
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])