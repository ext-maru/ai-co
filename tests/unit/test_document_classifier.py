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
import tempfile
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
    def temp_base_dir(self):
        """テスト用一時ディレクトリ"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def classifier(self, temp_base_dir):
        """テスト用分類器インスタンス"""
        with patch('scripts.docs.classify_documents_enhanced.FOUR_SAGES_AVAILABLE', False):
            return SecureDocumentClassifier(str(temp_base_dir))
    
    @pytest.fixture
    def sample_md_files(self, temp_base_dir):
        """サンプルMarkdownファイル作成"""
        files = {}
        
        # 正常ファイル
        files['guide'] = temp_base_dir / "user-guide.md"
        files['guide'].write_text("# User Guide\nThis is a basic user guide.")
        
        # 技術文書
        files['technical'] = temp_base_dir / "system-architecture.md"
        files['technical'].write_text("# System Architecture\nDetailed system design.")
        
        # レポート
        files['report'] = temp_base_dir / "completion-report.md"
        files['report'].write_text("# Completion Report\nProject completion analysis.")
        
        # セキュリティ違反ファイル
        files['security_risk'] = temp_base_dir / "risky-file.md"
        files['security_risk'].write_text("# Risky File\neval('dangerous code')")
        
        # Iron Will違反ファイル
        files['iron_will_violation'] = temp_base_dir / "todo-file.md"
        files['iron_will_violation'].write_text("# TODO File\nTODO: Fix this later\nFIXME: Bug here")
        
        return files

class TestSecurityValidation:
    """セキュリティ検証テスト"""
    
    def test_validate_security_normal_file(self, classifier, temp_base_dir):
        """正常ファイルのセキュリティ検証"""
        normal_file = temp_base_dir / "normal.md"
        normal_file.write_text("# Normal Document\nThis is safe content.")
        
        is_secure, violations, score = classifier.validate_security(
            normal_file,
            "# Normal Document\nThis is safe content."
        )
        
        assert is_secure is True
        assert len(violations) == 0
        assert score == 100.0
    
    def test_validate_security_path_traversal(self, classifier, temp_base_dir):
        """パストラバーサル攻撃検証"""
        malicious_path = temp_base_dir / "../../../etc/passwd.md"
        
        is_secure, violations, score = classifier.validate_security(malicious_path, "safe content")
        
        assert is_secure is False
        assert any("パストラバーサル" in v for v in violations)
        assert score < 100.0
    
    def test_validate_security_forbidden_chars(self, classifier, temp_base_dir):
        """禁止文字検証"""
        bad_file = temp_base_dir / "bad..file~.md"
        bad_file.write_text("content")
        
        is_secure, violations, score = classifier.validate_security(bad_file, "content")
        
        assert is_secure is False
        assert any("禁止文字" in v for v in violations)
    
    def test_validate_security_risk_patterns(self, classifier, temp_base_dir):
        """セキュリティリスクパターン検証"""
        risky_content = "# Dangerous\neval('malicious code')\nos.system('rm -rf /')"
        risky_file = temp_base_dir / "risky.md"
        risky_file.write_text(risky_content)
        
        is_secure, violations, score = classifier.validate_security(risky_file, risky_content)
        
        assert is_secure is False
        assert len(violations) >= 2  # eval と os.system
        assert score < 70.0
    
    def test_validate_security_iron_will_violations(self, classifier, temp_base_dir):
        """Iron Will違反検証"""
        iron_will_content = "# Document\nTODO: Fix this\nFIXME: Bug here\nHACK: Temporary solution"
        violation_file = temp_base_dir / "violations.md"
        violation_file.write_text(iron_will_content)
        
        is_secure, violations, score = classifier.validate_security(violation_file, iron_will_content)
        
        iron_will_violations = [v for v in violations if "Iron Will" in v]
        assert len(iron_will_violations) == 3  # TODO, FIXME, HACK

class TestSecurePathJoin:
    """セキュアパス結合テスト"""
    
    def test_secure_path_join_normal(self, classifier, temp_base_dir):
        """正常パス結合"""
        result = classifier.secure_path_join(temp_base_dir, "docs", "guides", "user-guide.md")
        
        assert result is not None
        assert str(result).startswith(str(temp_base_dir))
        assert "docs/guides/user-guide.md" in str(result)
    
    def test_secure_path_join_traversal_attack(self, classifier, temp_base_dir):
        """パストラバーサル攻撃阻止"""
        result = classifier.secure_path_join(temp_base_dir, "..", "..", "etc", "passwd")
        
        assert result is None  # 攻撃を阻止
    
    def test_secure_path_join_dangerous_chars(self, classifier, temp_base_dir):
        """危険文字除去"""
        result = classifier.secure_path_join(temp_base_dir, "docs", "file..with~danger.md")
        
        assert result is not None
        assert ".." not in str(result)
        assert "~" not in str(result)
    
    def test_secure_path_join_url_decode(self, classifier, temp_base_dir):
        """URLデコード処理"""
        result = classifier.secure_path_join(temp_base_dir, "docs%2Fguides", "file%20name.md")
        
        assert result is not None
        assert "docs" in str(result)
        assert "file name" in str(result)

class TestDocumentClassification:
    """ドキュメント分類テスト"""
    
    def test_classify_guide_document(self, classifier, temp_base_dir):
        """ガイドドキュメント分類"""
        guide_file = temp_base_dir / "quickstart-guide.md"
        guide_file.write_text("# Quickstart Guide\nGetting started quickly.")
        
        doc_info = classifier.classify_document(guide_file)
        
        assert doc_info is not None
        assert doc_info.category == "guides"
        assert doc_info.subcategory == "user-guides"
        assert doc_info.sage_assignment == "knowledge_sage"
    
    def test_classify_technical_document(self, classifier, temp_base_dir):
        """技術文書分類"""
        tech_file = temp_base_dir / "system-architecture.md"
        tech_file.write_text("# System Architecture\nTechnical design overview.")
        
        doc_info = classifier.classify_document(tech_file)
        
        assert doc_info is not None
        assert doc_info.category == "technical"
        assert doc_info.subcategory == "architecture"
        assert doc_info.sage_assignment == "rag_sage"
    
    def test_classify_report_document(self, classifier, temp_base_dir):
        """レポート分類"""
        report_file = temp_base_dir / "completion-report.md"
        report_file.write_text("# Completion Report\nProject completion analysis.")
        
        doc_info = classifier.classify_document(report_file)
        
        assert doc_info is not None
        assert doc_info.category == "reports"
        assert doc_info.sage_assignment == "task_sage"
    
    def test_classify_policy_document(self, classifier, temp_base_dir):
        """ポリシー文書分類"""
        policy_file = temp_base_dir / "coding-standards.md"
        policy_file.write_text("# Coding Standards\nDevelopment policies and standards.")
        
        doc_info = classifier.classify_document(policy_file)
        
        assert doc_info is not None
        assert doc_info.category == "technical"  # patterns不一致のため
        assert doc_info.sage_assignment == "rag_sage"
    
    def test_classify_security_violation_document(self, classifier, temp_base_dir):
        """セキュリティ違反文書分類"""
        risky_file = temp_base_dir / "dangerous-file.md"
        risky_content = "# Dangerous\neval('malicious')\nTODO: Fix security"
        risky_file.write_text(risky_content)
        
        doc_info = classifier.classify_document(risky_file)
        
        assert doc_info is not None
        assert doc_info.status == "security_review"
        assert doc_info.security_score < 70.0
        assert doc_info.iron_will_compliant is False

class TestFileOperations:
    """ファイル操作テスト"""
    
    def test_secure_move_file_success(self, classifier, temp_base_dir):
        """正常なファイル移動"""
        source = temp_base_dir / "source.md"
        source.write_text("# Source\nContent")
        
        dest_dir = temp_base_dir / "dest"
        dest_dir.mkdir()
        destination = dest_dir / "moved.md"
        
        success = classifier.secure_move_file(source, destination)
        
        assert success is True
        assert not source.exists()
        assert destination.exists()
        assert destination.read_text() == "# Source\nContent"
    
    def test_secure_move_file_duplicate_handling(self, classifier, temp_base_dir):
        """重複ファイル名処理"""
        source = temp_base_dir / "source.md"
        source.write_text("# Source\nContent")
        
        dest_dir = temp_base_dir / "dest"
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
    
    def test_secure_move_file_nonexistent_source(self, classifier, temp_base_dir):
        """存在しないファイルの移動"""
        nonexistent = temp_base_dir / "nonexistent.md"
        destination = temp_base_dir / "dest.md"
        
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
    
    def test_full_classification_workflow(self, classifier, temp_base_dir):
        """完全な分類ワークフロー"""
        # サンプルファイル作成
        files = {
            'guide': temp_base_dir / "user-guide.md",
            'tech': temp_base_dir / "architecture-design.md",
            'report': temp_base_dir / "completion-report.md"
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
    
    def test_security_violation_handling(self, classifier, temp_base_dir):
        """セキュリティ違反処理"""
        # セキュリティ違反ファイル
        risky_file = temp_base_dir / "risky-document.md"
        risky_content = "# Risky\neval('dangerous')\nTODO: Fix this\nos.system('rm -rf')"
        risky_file.write_text(risky_content)
        
        result = classifier.classify_and_move_secure(dry_run=True)
        
        assert result.security_violations > 0
        assert result.iron_will_violations > 0

class TestFourSagesIntegration:
    """4賢者システム統合テスト"""
    
    @patch('scripts.docs.classify_documents_enhanced.FOUR_SAGES_AVAILABLE', True)
    def test_sage_assignment(self, temp_base_dir):
        """賢者割り当てテスト"""
        with patch('scripts.docs.classify_documents_enhanced.KnowledgeSage') as mock_sage:
            mock_sage.return_value = Mock()
            classifier = SecureDocumentClassifier(str(temp_base_dir))
            
            guide_file = temp_base_dir / "user-guide.md"
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
    
    def test_large_file_handling(self, classifier, temp_base_dir):
        """大容量ファイル処理"""
        large_file = temp_base_dir / "large-file.md"
        large_content = "# Large File\n" + "x" * (10 * 1024 * 1024)  # 10MB
        large_file.write_text(large_content)
        
        # セキュリティ検証でサイズ制限に引っかかることを確認
        is_secure, violations, score = classifier.validate_security(large_file, large_content)
        
        assert is_secure is False
        assert any("ファイルサイズ超過" in v for v in violations)
    
    def test_batch_processing_performance(self, classifier, temp_base_dir):
        """バッチ処理性能"""
        import time
        
        # 100個のサンプルファイル作成
        files = []
        for i in range(100):
            file_path = temp_base_dir / f"test-file-{i:03d}.md"
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