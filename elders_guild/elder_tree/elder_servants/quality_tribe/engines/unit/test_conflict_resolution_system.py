#!/usr/bin/env python3
"""
🧪 Conflict Resolution System Tests
コンフリクト解決システムのTDDテスト

テスト対象:
- ImprovedConflictAnalyzer: コンフリクト分析エンジン
- BranchUpdater: ブランチ自動更新機能
- 統合テスト: 両機能の連携
"""

import pytest

import os
import git
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.integrations.github.improved_conflict_analyzer import (
    ImprovedConflictAnalyzer, ConflictType, ResolutionStrategy, 
    ConflictInfo, RiskLevel as ConflictRiskLevel
)
from libs.integrations.github.branch_updater import (
    BranchUpdater, UpdateStrategy, RiskLevel as UpdateRiskLevel,
    BranchStatus, UpdateAnalysis
)

class TestImprovedConflictAnalyzer:
    """改良版コンフリクト分析エンジンのテスト"""
    
    @pytest.fixture

        """テスト用の一時Gitリポジトリ"""

            # 初期コミット

            with open(test_file, 'w') as f:
                f.write("initial content\n")
            
            repo.index.add(['test.txt'])
            repo.index.commit("Initial commit")

    @pytest.fixture

        """テスト用アナライザー"""

    def test_no_conflicts_detected(self, analyzer):
        """コンフリクトがない場合のテスト"""
        # モック: unmerged_blobs が空
        analyzer.repo.index.unmerged_blobs = Mock(return_value={})
        
        result = analyzer.analyze_merge_conflicts()
        
        assert result["conflicts_found"] is False
        assert result["total_conflicts"] == 0
        assert result["conflicts"] == []
        assert result["auto_resolvable_count"] == 0
    
    def test_package_json_conflict_detection(self, analyzer):
        """package.jsonのコンフリクト検出テスト"""
        # モック: package.jsonのコンフリクト
        mock_blob = Mock()
        mock_blob.hexsha = "abc123"
        
        analyzer.repo.index.unmerged_blobs = Mock(return_value={
            "package.json": [
                (1, mock_blob),  # base
                (2, mock_blob),  # ours
                (3, mock_blob)   # theirs
            ]
        })
        
        # モック: blob内容取得
        analyzer._get_blob_content = Mock(return_value='{"dependencies": {}}')
        
        result = analyzer.analyze_merge_conflicts()
        
        assert result["conflicts_found"] is True
        assert result["total_conflicts"] == 1
        assert result["auto_resolvable_count"] == 1
        
        conflict = result["conflicts"][0]
        assert conflict["file_path"] == "package.json"
        assert conflict["conflict_type"] == ConflictType.DEPENDENCY_CONFLICT.value
        assert conflict["auto_resolvable"] is True
        assert conflict["resolution_strategy"] == ResolutionStrategy.MERGE_DEPENDENCIES.value
    
    def test_python_file_conflict_detection(self, analyzer):
        """Pythonファイルのコンフリクト検出テスト（手動対応必要）"""
        mock_blob = Mock()
        mock_blob.hexsha = "def456"
        
        analyzer.repo.index.unmerged_blobs = Mock(return_value={
            "main.py": [
                (1, mock_blob),
                (2, mock_blob),
                (3, mock_blob)
            ]
        })
        
        analyzer._get_blob_content = Mock(return_value='print("test")')
        analyzer._get_file_size = Mock(return_value=1000)
        analyzer._is_binary_file = Mock(return_value=False)
        
        result = analyzer.analyze_merge_conflicts()
        
        assert result["conflicts_found"] is True
        assert result["auto_resolvable_count"] == 0
        assert result["manual_required_count"] == 1
        
        conflict = result["conflicts"][0]
        assert conflict["file_path"] == "main.py"
        assert conflict["conflict_type"] == ConflictType.CODE_CONFLICT.value
        assert conflict["auto_resolvable"] is False
        assert conflict["resolution_strategy"] == ResolutionStrategy.MANUAL_REVIEW.value
    
    def test_changelog_conflict_resolution(self, analyzer):
        """CHANGELOG.mdの自動解決テスト"""
        mock_blob = Mock()
        mock_blob.hexsha = "ghi789"
        
        analyzer.repo.index.unmerged_blobs = Mock(return_value={
            "CHANGELOG.md": [
                (1, mock_blob),
                (2, mock_blob),
                (3, mock_blob)
            ]
        })
        
        analyzer._get_blob_content = Mock(return_value='# Changelog\n## v1.0.0\n')
        
        result = analyzer.analyze_merge_conflicts()
        
        conflict = result["conflicts"][0]
        assert conflict["conflict_type"] == ConflictType.CHANGELOG_CONFLICT.value
        assert conflict["auto_resolvable"] is True
        assert conflict["resolution_strategy"] == ResolutionStrategy.APPEND_CHANGELOG.value
        assert conflict["confidence"] > 0.8  # 高い信頼度
    
    def test_binary_file_conflict(self, analyzer):
        """バイナリファイルのコンフリクトテスト"""
        mock_blob = Mock()
        mock_blob.hexsha = "jkl012"
        
        analyzer.repo.index.unmerged_blobs = Mock(return_value={
            "image.png": [
                (1, mock_blob),
                (2, mock_blob),
                (3, mock_blob)
            ]
        })
        
        analyzer._is_binary_file = Mock(return_value=True)
        analyzer._get_file_size = Mock(return_value=50000)
        
        result = analyzer.analyze_merge_conflicts()
        
        conflict = result["conflicts"][0]
        assert conflict["auto_resolvable"] is False
        assert conflict["resolution_strategy"] == ResolutionStrategy.MANUAL_REVIEW.value
    
    def test_safe_conflict_resolution(self, analyzer):
        """安全なコンフリクト自動解決のテスト"""
        # package.jsonのコンフリクト情報
        conflict_info = ConflictInfo(
            file_path="package.json",
            conflict_type=ConflictType.DEPENDENCY_CONFLICT,
            stage_info={1: "base", 2: "ours", 3: "theirs"},
            auto_resolvable=True,
            resolution_strategy=ResolutionStrategy.TAKE_THEIRS,
            confidence=0.9,
            file_size=1000
        )
        
        # モック設定
        analyzer._get_blob_content = Mock(return_value='{"dependencies": {}}')
        analyzer.repo.index.add = Mock()
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = analyzer.auto_resolve_safe_conflicts([conflict_info])
        
        assert result["success"] is True
        assert result["resolved_files"] == ["package.json"]
        assert result["failed_files"] == []
        
        # ファイルが書き込まれたことを確認
        mock_file.write.assert_called_once()
        analyzer.repo.index.add.assert_called_with(["package.json"])
    
    def test_confidence_score_calculation(self, analyzer):
        """信頼度スコア計算のテスト"""
        # 安全なファイル
        confidence = analyzer._calculate_confidence_score(
            "package.json",
            ConflictType.DEPENDENCY_CONFLICT,
            auto_resolvable=True
        )
        assert confidence > 0.8
        
        # 危険なファイル
        confidence = analyzer._calculate_confidence_score(
            "main.py",
            ConflictType.CODE_CONFLICT,
            auto_resolvable=False
        )
        assert confidence < 0.5
    
    @patch('libs.integrations.github.improved_conflict_analyzer.THREE_MERGE_AVAILABLE', True)
    @patch('libs.integrations.github.improved_conflict_analyzer.three_way_merge')
    def test_three_way_merge_resolution(self, mock_merge, analyzer):
        """3-wayマージ解決のテスト"""
        # マージ成功をモック
        mock_merge.return_value = "merged content without conflicts"
        
        conflict_info = ConflictInfo(
            file_path="README.md",
            conflict_type=ConflictType.DOCUMENTATION_CONFLICT,
            stage_info={1: "base", 2: "ours", 3: "theirs"},
            auto_resolvable=True,
            resolution_strategy=ResolutionStrategy.THREE_WAY_MERGE,
            confidence=0.8,
            file_size=500
        )
        
        analyzer._get_blob_content = Mock(side_effect=[
            "base content",
            "our content",
            "their content"
        ])
        analyzer.repo.index.add = Mock()
        
        with patch('builtins.open', create=True):
            success = analyzer._three_way_merge_resolve(conflict_info)
        
        assert success is True
        mock_merge.assert_called_once_with("our content", "their content", "base content")

class TestBranchUpdater:
    """ブランチ自動更新機能のテスト"""
    
    @pytest.fixture
    def mock_repo(self):
        """モックGitリポジトリ"""
        mock_repo = Mock(spec=git.Repo)
        mock_repo.is_dirty.return_value = False
        mock_repo.active_branch.name = "feature/test"
        
        # リモート設定
        mock_remote = Mock()
        mock_remote.fetch = Mock()
        mock_repo.remotes.origin = mock_remote
        
        # Git操作モック
        mock_repo.git = Mock()
        
        return mock_repo
    
    @pytest.fixture
    def updater(self, mock_repo):
        """テスト用アップデーター"""
        with patch('git.Repo', return_value=mock_repo):
            updater = BranchUpdater("/fake/path")
            updater.repo = mock_repo
            return updater
    
    @pytest.mark.asyncio
    async def test_fast_forward_possible(self, updater, mock_repo):
        """ファストフォワード可能な場合のテスト"""
        # ブランチ状態設定
        mock_repo.commit = Mock(side_effect=lambda ref: Mock())
        mock_repo.merge_base = Mock(return_value=[Mock(hexsha="abc123")])
        mock_repo.iter_commits = Mock(side_effect=[
            [],      # 0 commits ahead
            [Mock()] * 5  # 5 commits behind
        ])
        
        analysis = await updater.analyze_branch_update("feature/test", "main")
        
        assert analysis.branch_status.fast_forward_possible is True
        assert analysis.branch_status.diverged is False
        assert analysis.recommended_strategy == UpdateStrategy.FAST_FORWARD
        assert analysis.risk_level == UpdateRiskLevel.SAFE
        assert analysis.confidence_score > 0.8
    
    @pytest.mark.asyncio
    async def test_diverged_branch_analysis(self, updater, mock_repo):
        """分岐したブランチの分析テスト"""
        # 分岐状態設定
        mock_repo.commit = Mock(side_effect=lambda ref: Mock())
        mock_repo.merge_base = Mock(return_value=[Mock(hexsha="def456")])
        mock_repo.iter_commits = Mock(side_effect=[
            [Mock()] * 3,   # 3 commits ahead
            [Mock()] * 8    # 8 commits behind
        ])
        
        # 差分ファイル設定
        mock_repo.git.diff = Mock(return_value="file1.0.py\nfile2.0.js\nREADME.md")
        
        analysis = await updater.analyze_branch_update("feature/test", "main")
        
        assert analysis.branch_status.diverged is True
        assert analysis.branch_status.fast_forward_possible is False
        assert analysis.recommended_strategy == UpdateStrategy.REBASE
        assert analysis.risk_level in [UpdateRiskLevel.LOW, UpdateRiskLevel.MEDIUM]
    
    @pytest.mark.asyncio
    async def test_high_risk_detection(self, updater, mock_repo):
        """高リスク状態の検出テスト"""
        # 大規模な分岐
        mock_repo.commit = Mock(side_effect=lambda ref: Mock())
        mock_repo.merge_base = Mock(return_value=[Mock(hexsha="ghi789")])
        mock_repo.iter_commits = Mock(side_effect=[
            [Mock()] * 20,  # 20 commits ahead
            [Mock()] * 60   # 60 commits behind (limit超過)
        ])
        
        # 多くのファイル変更
        mock_repo.git.diff = Mock(return_value="\n".join([f"file{i}.py" for i in range(30)]))
        
        analysis = await updater.analyze_branch_update("feature/test", "main")
        
        assert analysis.recommended_strategy == UpdateStrategy.MANUAL_REQUIRED
        assert analysis.risk_level in [UpdateRiskLevel.HIGH, UpdateRiskLevel.CRITICAL]
        assert analysis.confidence_score < 0.5
        assert not analysis.safety_checks["size_limits_ok"]
    
    @pytest.mark.asyncio
    async def test_safety_checks(self, updater, mock_repo):
        """安全性チェックのテスト"""
        # ブランチ存在チェック
        mock_repo.commit = Mock(side_effect=lambda ref: Mock())
        
        # リポジトリクリーンチェック
        mock_repo.is_dirty.return_value = False
        
        # 権限チェック
        with patch('os.access', return_value=True):
            branch_status = BranchStatus(
                branch_name="feature/test",
                commits_behind=5,
                commits_ahead=0,
                last_common_commit="abc123",
                diverged=False,
                fast_forward_possible=True
            )
            
            safety_checks = await updater._perform_safety_checks(
                "feature/test", "main", branch_status
            )
        
        assert safety_checks["branches_exist"] is True
        assert safety_checks["repo_clean"] is True
        assert safety_checks["sufficient_permissions"] is True
        assert safety_checks["size_limits_ok"] is True
    
    @pytest.mark.asyncio
    async def test_execute_fast_forward_update(self, updater, mock_repo):
        """ファストフォワード更新実行のテスト"""
        analysis = UpdateAnalysis(
            branch_status=BranchStatus(
                branch_name="feature/test",
                commits_behind=5,
                commits_ahead=0,
                last_common_commit="abc123",
                diverged=False,
                fast_forward_possible=True
            ),
            recommended_strategy=UpdateStrategy.FAST_FORWARD,
            risk_level=UpdateRiskLevel.SAFE,
            confidence_score=0.9,
            estimated_conflicts=0,
            affected_files=[],
            safety_checks={k: True for k in [
                "branches_exist", "repo_clean", "branch_protection_safe",
                "backup_possible", "sufficient_permissions", "size_limits_ok"
            ]}
        )
        
        # 実行
        result = await updater.execute_safe_update(analysis, dry_run=False)
        
        assert result["success"] is True
        assert result["strategy"] == "fast_forward"
        
        # Git操作の確認
        mock_repo.git.checkout.assert_called_with("feature/test")
        mock_repo.git.pull.assert_called_with('origin', "feature/test", '--ff-only')
    
    @pytest.mark.asyncio
    async def test_dry_run_mode(self, updater):
        """ドライランモードのテスト"""
        analysis = UpdateAnalysis(
            branch_status=BranchStatus(
                branch_name="feature/test",
                commits_behind=5,
                commits_ahead=0,
                last_common_commit="abc123",
                diverged=False,
                fast_forward_possible=True
            ),
            recommended_strategy=UpdateStrategy.FAST_FORWARD,
            risk_level=UpdateRiskLevel.SAFE,
            confidence_score=0.9,
            estimated_conflicts=0,
            affected_files=[],
            safety_checks={k: True for k in [
                "branches_exist", "repo_clean", "branch_protection_safe",
                "backup_possible", "sufficient_permissions", "size_limits_ok"
            ]}
        )
        
        result = await updater.execute_safe_update(analysis, dry_run=True)
        
        assert result["success"] is True
        assert result["dry_run"] is True
        assert "実際の更新は実行されませんでした" in result["message"]
    
    @pytest.mark.asyncio
    async def test_high_risk_rejection(self, updater):
        """高リスク更新の拒否テスト"""
        analysis = UpdateAnalysis(
            branch_status=BranchStatus(
                branch_name="feature/test",
                commits_behind=100,
                commits_ahead=50,
                last_common_commit="abc123",
                diverged=True,
                fast_forward_possible=False
            ),
            recommended_strategy=UpdateStrategy.MANUAL_REQUIRED,
            risk_level=UpdateRiskLevel.CRITICAL,
            confidence_score=0.2,
            estimated_conflicts=20,
            affected_files=["critical.py"] * 30,
            safety_checks={}
        )
        
        result = await updater.execute_safe_update(analysis)
        
        assert result["success"] is False
        assert result["reason"] == "risk_too_high"
        assert "リスクが高すぎる" in result["message"]
    
    def test_confidence_score_calculation(self, updater):
        """信頼度スコア計算のテスト"""
        # ファストフォワード可能
        branch_status = BranchStatus(
            branch_name="test",
            commits_behind=3,
            commits_ahead=0,
            last_common_commit="abc",
            diverged=False,
            fast_forward_possible=True
        )
        
        confidence = updater._calculate_confidence_score(
            branch_status, UpdateRiskLevel.SAFE
        )
        assert confidence > 0.8
        
        # 大規模分岐
        branch_status.diverged = True
        branch_status.commits_ahead = 50
        branch_status.commits_behind = 100
        branch_status.fast_forward_possible = False
        
        confidence = updater._calculate_confidence_score(
            branch_status, UpdateRiskLevel.HIGH
        )
        assert confidence < 0.3

class TestIntegration:
    """統合テスト"""
    
    @pytest.mark.asyncio
    async def test_full_conflict_resolution_flow(self):
        """完全なコンフリクト解決フローのテスト"""

            # テストリポジトリ作成

            # ファイル作成

            with open(package_json, 'w') as f:
                f.write('{"name": "test", "version": "1.0.0"}')
            
            repo.index.add(['package.json'])
            repo.index.commit("Initial commit")
            
            # アナライザーとアップデーター初期化

            # モック設定
            analyzer.repo.index.unmerged_blobs = Mock(return_value={
                "package.json": [(1, Mock()), (2, Mock()), (3, Mock())]
            })
            
            # コンフリクト分析
            conflicts = analyzer.analyze_merge_conflicts()
            assert conflicts["conflicts_found"] is True
            assert conflicts["auto_resolvable_count"] > 0
            
            # ブランチ更新分析
            with patch.object(updater, '_get_branch_status') as mock_status:
                mock_status.return_value = BranchStatus(
                    branch_name="feature/test",
                    commits_behind=5,
                    commits_ahead=2,
                    last_common_commit="abc123",
                    diverged=True,
                    fast_forward_possible=False
                )
                
                with patch.object(updater, '_predict_conflicts') as mock_predict:
                    mock_predict.return_value = (1, ["package.json"])
                    
                    analysis = await updater.analyze_branch_update("feature/test")
                    
                    assert analysis.estimated_conflicts == 1
                    assert "package.json" in analysis.affected_files

# 実行用
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])