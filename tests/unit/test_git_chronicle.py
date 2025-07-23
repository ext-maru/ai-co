#!/usr/bin/env python3
"""
📜 Git Chronicle Magic テストスイート
Git年代記魔法の完全テスト
"""

import asyncio
import json
import logging
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

import pytest

# プロジェクトルートをパスに追加
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.git_chronicle import (
    GitChronicle,
    GitBranchAnalyzer,
    GitCommitAnalyzer,
    GitWorkflowType,
    GitViolationType
)
from libs.ancient_elder.base import ViolationSeverity


class TestGitBranchAnalyzer(unittest.TestCase):
    """Gitブランチ戦略分析システムテスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.analyzer = GitBranchAnalyzer(self.project_root)
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_analyzer_initialization(self):
        """アナライザーの初期化テスト"""
        self.assertIsInstance(self.analyzer, GitBranchAnalyzer)
        self.assertEqual(self.analyzer.project_root, self.project_root)
        
        # ブランチ命名パターンが設定されていることを確認
        self.assertIn("feature", self.analyzer.branch_naming_patterns)
        self.assertIn("fix", self.analyzer.branch_naming_patterns)
        self.assertIn("hotfix", self.analyzer.branch_naming_patterns)
        
        # 保護されたブランチが設定されていることを確認
        self.assertIn("main", self.analyzer.protected_branches)
        self.assertIn("master", self.analyzer.protected_branches)
        
    def test_branch_naming_convention_validation(self):
        """ブランチ命名規約検証テスト"""
        test_branches = [
            ("feature/issue-123-user-auth", True, "feature"),
            ("fix/issue-456-login-bug", True, "fix"),
            ("hotfix/security-patch", True, "hotfix"),
            ("docs/update-readme", True, "docs"),
            ("feature-broken-naming", False, None),
            ("random-branch-name", False, None),
            ("main", False, None),  # 保護ブランチ（チェック対象外）
        ]
        
        for branch_name, should_be_valid, expected_type in test_branches:
            if branch_name in self.analyzer.protected_branches:
                continue  # 保護ブランチはスキップ
                
            is_valid = False
            detected_type = None
            
            for pattern_type, pattern in self.analyzer.branch_naming_patterns.items():
                if pattern.match(branch_name):
                    is_valid = True
                    detected_type = pattern_type
                    break
                    
            self.assertEqual(is_valid, should_be_valid, 
                           f"Branch '{branch_name}' validation failed")
            if should_be_valid:
                self.assertEqual(detected_type, expected_type,
                               f"Branch type detection failed for '{branch_name}'")
                
    def test_branch_naming_violations_detection(self):
        """ブランチ命名規約違反検出テスト"""
        mock_branch_info = {
            "local_branches": [
                "main",  # 保護ブランチ（違反対象外）
                "feature/issue-123-user-auth",  # 正常
                "fix/issue-456-login-bug",      # 正常
                "broken-branch-name",           # 違反
                "another_invalid_branch",       # 違反
                "hotfix/security-patch"         # 正常
            ]
        }
        
        violations = self.analyzer._check_branch_naming_conventions(mock_branch_info)
        
        # 2つの違反が検出されることを確認
        self.assertEqual(len(violations), 2)
        
        # 違反ブランチ名を確認
        violation_branches = [v["branch_name"] for v in violations]
        self.assertIn("broken-branch-name", violation_branches)
        self.assertIn("another_invalid_branch", violation_branches)
        
        # 違反タイプを確認
        for violation in violations:
            self.assertEqual(violation["type"], GitViolationType.BRANCH_NAMING_VIOLATION)
            self.assertEqual(violation["severity"], "MEDIUM")
            
    @patch('subprocess.run')
    def test_get_branch_information(self, mock_subprocess):
        """ブランチ情報取得テスト"""
        # モックレスポンス設定
        mock_subprocess.side_effect = [
            # git branch (ローカルブランチ)
            Mock(stdout="  main\n* feature/issue-123-auth\n  fix/issue-456-bug\n"),
            # git branch -r (リモートブランチ)
            Mock(stdout="  origin/main\n  origin/feature/issue-123-auth\n  origin/HEAD -> origin/main\n"),
            # git rev-parse --abbrev-ref HEAD (現在のブランチ)
            Mock(stdout="feature/issue-123-auth\n")
        ]
        
        branch_info = self.analyzer._get_branch_information()
        
        self.assertEqual(branch_info["current_branch"], "feature/issue-123-auth")
        self.assertIn("main", branch_info["local_branches"])
        self.assertIn("feature/issue-123-auth", branch_info["local_branches"])
        self.assertEqual(branch_info["total_branches"], 3)
        self.assertIn("main", branch_info["protected_branches_present"])
        
    @patch('subprocess.run')
    def test_protected_branch_violations_detection(self, mock_subprocess):
        """保護ブランチ違反検出テスト"""
        # 保護ブランチへの直接コミットがある場合のモック
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = """abc123|2025-01-20 10:00:00|Direct commit to main|developer
def456|2025-01-20 11:00:00|Another direct commit|developer"""
        
        violations = self.analyzer._check_protected_branch_violations(timedelta(days=7))
        
        # 違反が検出されることを確認
        self.assertGreater(len(violations), 0)
        
        # 違反タイプを確認
        for violation in violations:
            self.assertEqual(violation["type"], GitViolationType.DIRECT_MAIN_COMMIT)
            self.assertEqual(violation["severity"], "HIGH")
            self.assertIn("branch", violation)
            self.assertIn("commit_hash", violation)
            
    def test_workflow_type_detection(self):
        """ワークフロータイプ検出テスト"""
        # Git Flowパターン
        git_flow_branches = {
            "local_branches": ["main", "develop", "feature/new-feature", "release/v1.0.0"]
        }
        workflow_type = self.analyzer._detect_workflow_type(git_flow_branches)
        self.assertEqual(workflow_type, GitWorkflowType.GIT_FLOW)
        
        # Feature Branchパターン
        feature_branches = {
            "local_branches": ["main", "feature/user-auth", "feature/payment"]
        }
        workflow_type = self.analyzer._detect_workflow_type(feature_branches)
        self.assertEqual(workflow_type, GitWorkflowType.FEATURE_BRANCH)
        
        # GitHub Flowパターン（デフォルト）
        github_flow_branches = {
            "local_branches": ["main", "user-auth", "payment-fix"]
        }
        workflow_type = self.analyzer._detect_workflow_type(github_flow_branches)
        self.assertEqual(workflow_type, GitWorkflowType.GITHUB_FLOW)
        
    def test_branch_score_calculation(self):
        """ブランチスコア計算テスト"""
        # 違反なしのケース
                no_violations_score = \
            self.analyzer._calculate_branch_score([], [], {"feature_branch_usage": {"compliance_score": 90}})
        self.assertGreaterEqual(no_violations_score, 85.0)
        
        # 命名違反ありのケース
        naming_violations = [{"type": GitViolationType.BRANCH_NAMING_VIOLATION}] * 3
        naming_violation_score = self.analyzer._calculate_branch_score(
            naming_violations,
            [],
            {"feature_branch_usage": {"compliance_score": 80}}
        )
        self.assertLess(naming_violation_score, no_violations_score)
        
        # 保護ブランチ違反ありのケース
        protected_violations = [{"type": GitViolationType.DIRECT_MAIN_COMMIT}]
        protected_violation_score = self.analyzer._calculate_branch_score(
            [],
            protected_violations,
            {"feature_branch_usage": {"compliance_score": 80}}
        )
        self.assertLess(protected_violation_score, no_violations_score)


class TestGitCommitAnalyzer(unittest.TestCase):
    """Gitコミットメッセージ・規約分析システムテスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.analyzer = GitCommitAnalyzer(self.project_root)
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_analyzer_initialization(self):
        """アナライザーの初期化テスト"""
        self.assertIsInstance(self.analyzer, GitCommitAnalyzer)
        self.assertEqual(self.analyzer.project_root, self.project_root)
        
        # コミット規約パターンが設定されていることを確認
        self.assertIn("conventional_commits", self.analyzer.commit_conventions)
        self.assertIn("angular", self.analyzer.commit_conventions)
        self.assertIn("gitmoji", self.analyzer.commit_conventions)
        
    def test_commit_convention_detection(self):
        """コミット規約検出テスト"""
        test_messages = [
            ("feat: add user authentication", True, "conventional_commits"),
            ("fix(auth): resolve login bug", True, "conventional_commits"),
            ("docs: update README with installation guide", True, "conventional_commits"),
            ("chore: update dependencies", True, "conventional_commits"),
            ("🎉 Initial commit", True, "gitmoji"),
            ("✨ Add new feature", True, "gitmoji"),
            ("Random commit message", False, None),
            ("Add feature", False, None),
            ("FIX BUG", False, None),
        ]
        
        for message, should_match, expected_convention in test_messages:
            result = self.analyzer._check_commit_convention(message)
            
            self.assertEqual(result["compliant"], should_match, 
                           f"Convention check failed for: '{message}'")
            
            if should_match and expected_convention:
                self.assertTrue(result["matches"].get(expected_convention, False),
                              f"Expected {expected_convention} to match: '{message}'")
                
    def test_commit_quality_detection(self):
        """コミット品質検出テスト"""
        test_cases = [
            ("Fix", ["too_short"]),                      # 短すぎる（Fは大文字なのでno_capital_start対象外）
            ("fix bug", ["no_capital_start"]),           # 小文字始まり
            ("Fix bug.", ["ends_with_period"]),          # ピリオド終わり
            ("FIX BUG IN AUTH SYSTEM", ["all_caps"]),    # 全て大文字
            ("A" * 150, ["too_long"]),                   # 長すぎる
            ("Fix user authentication bug", []),         # 品質問題なし
        ]
        
        for message, expected_issues in test_cases:
            issues = self.analyzer._check_commit_quality(message)
            
            for expected_issue in expected_issues:
                self.assertIn(expected_issue, issues, 
                            f"Expected issue '{expected_issue}' not found in '{message}'")
                
    def test_individual_commit_score_calculation(self):
        """個別コミットスコア計算テスト"""
        # 高品質コミット
        high_quality_score = self.analyzer._calculate_individual_commit_score("Fix user authentication bug")
        self.assertGreaterEqual(high_quality_score, 90.0)
        
        # 低品質コミット（短い + 小文字始まり）
        low_quality_score = self.analyzer._calculate_individual_commit_score("fix")
        self.assertLessEqual(low_quality_score, 65.0)
        
        # 中品質コミット（小文字始まりで減点あり）
        medium_quality_score = self.analyzer._calculate_individual_commit_score("fix user authentication bug")
        self.assertGreater(medium_quality_score, low_quality_score)
        self.assertLess(medium_quality_score, high_quality_score)
        
    @patch.object(GitCommitAnalyzer, '_get_commit_history')
    def test_commit_quality_analysis(self, mock_get_commits):
        """コミット品質分析統合テスト"""
        # モックコミット履歴
        mock_get_commits.return_value = [
            {
                "hash": "abc123",
                "date": "2025-01-20",
                "message": "feat: add user auth",
                "author": "dev",
                "email": "dev@example.com"
            },
            {"hash": "def456", "date": "2025-01-20", "message": "fix bug", "author": "dev", "email": "dev@example.com"},
            {
                "hash": "ghi789",
                "date": "2025-01-20",
                "message": "Update readme",
                "author": "dev",
                "email": "dev@example.com"
            },
        ]
        
        result = self.analyzer.analyze_commit_quality()
        
        self.assertEqual(result["total_commits"], 3)
        self.assertIn("commit_analysis", result)
        self.assertIn("convention_compliance", result)
        self.assertIn("quality_violations", result)
        self.assertIn("overall_commit_score", result)
        
        # 規約遵守率の確認
        compliance = result["convention_compliance"]
        self.assertIn("compliance_rate", compliance)
        self.assertIn("compliant_commits", compliance)
        
    def test_convention_compliance_evaluation(self):
        """規約遵守状況評価テスト"""
        mock_analysis = [
            {"convention_match": {"compliant": True, "matches": {"conventional_commits": True}}},
            {"convention_match": {"compliant": False, "matches": {"conventional_commits": False}}},
            {"convention_match": {"compliant": True, "matches": {"conventional_commits": True}}},
        ]
        
        compliance = self.analyzer._evaluate_convention_compliance(mock_analysis)
        
        self.assertEqual(compliance["total_commits"], 3)
        self.assertEqual(compliance["compliant_commits"], 2)
        self.assertAlmostEqual(compliance["compliance_rate"], 66.67, places=1)
        
    def test_commit_quality_violations_detection(self):
        """コミット品質違反検出テスト"""
        mock_analysis = [
            {
                "hash": "abc123",
                "message": "feat: add auth",
                "convention_match": {"compliant": True},
                "quality_issues": []
            },
            {
                "hash": "def456", 
                "message": "fix",
                "convention_match": {"compliant": False},
                "quality_issues": ["too_short"]
            }
        ]
        
        violations = self.analyzer._detect_commit_quality_violations(mock_analysis)
        
        # 規約違反と品質違反が検出されることを確認
        violation_types = [v["type"] for v in violations]
        self.assertIn(GitViolationType.COMMIT_CONVENTION_VIOLATION, violation_types)
        self.assertIn(GitViolationType.POOR_COMMIT_MESSAGE, violation_types)


class TestGitChronicle(unittest.TestCase):
    """Git年代記魔法総合テスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.chronicle = GitChronicle(self.project_root)
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_chronicle_initialization(self):
        """Git年代記の初期化テスト"""
        self.assertIsInstance(self.chronicle, GitChronicle)
        self.assertEqual(self.chronicle.project_root, self.project_root)
        self.assertIsInstance(self.chronicle.branch_analyzer, GitBranchAnalyzer)
        self.assertIsInstance(self.chronicle.commit_analyzer, GitCommitAnalyzer)
        
    def test_get_audit_scope(self):
        """監査スコープ取得テスト"""
        scope = self.chronicle.get_audit_scope()
        
        self.assertIsInstance(scope, list)
        self.assertIn("git_branch_strategy", scope)
        self.assertIn("git_commit_quality", scope)
        self.assertIn("github_flow_compliance", scope)
        self.assertIn("git_workflow_optimization", scope)
        
    @patch.object(GitBranchAnalyzer, 'analyze_branch_strategy')
    @patch.object(GitCommitAnalyzer, 'analyze_commit_quality')
    async def test_execute_audit_success(self, mock_commit_analyzer, mock_branch_analyzer):
        """監査実行成功テスト"""
        # モックレスポンス設定
        mock_branch_analyzer.return_value = {
            "naming_violations": [],
            "protected_violations": [],
            "overall_branch_score": 85.0
        }
        
        mock_commit_analyzer.return_value = {
            "quality_violations": [],
            "overall_commit_score": 90.0
        }
        
        result = await self.chronicle.execute_audit("test_repo")
        
        self.assertEqual(result.auditor_name, "GitChronicle")
        self.assertEqual(result.target_path, "test_repo")
        self.assertIsInstance(result.violations, list)
        self.assertIsInstance(result.metrics, dict)
        self.assertIn("overall_git_score", result.metrics)
        self.assertGreater(result.metrics["overall_git_score"], 80.0)
        
    @patch.object(GitBranchAnalyzer, 'analyze_branch_strategy')
    @patch.object(GitCommitAnalyzer, 'analyze_commit_quality')
    async def test_execute_audit_with_violations(self, mock_commit_analyzer, mock_branch_analyzer):
        """違反検出時の監査実行テスト"""
        # 違反を含むモックレスポンス設定
        mock_branch_analyzer.return_value = {
            "naming_violations": [
                {
                    "type": GitViolationType.BRANCH_NAMING_VIOLATION,
                    "severity": "MEDIUM",
                    "branch_name": "invalid-branch"
                }
            ],
            "protected_violations": [
                {
                    "type": GitViolationType.DIRECT_MAIN_COMMIT,
                    "severity": "HIGH",
                    "branch": "main"
                }
            ],
            "overall_branch_score": 40.0
        }
        
        mock_commit_analyzer.return_value = {
            "quality_violations": [
                {
                    "type": GitViolationType.COMMIT_CONVENTION_VIOLATION,
                    "severity": "MEDIUM",
                    "commit_hash": "abc123"
                }
            ],
            "overall_commit_score": 50.0
        }
        
        result = await self.chronicle.execute_audit("test_repo")
        
        # 違反が適切に統合されることを確認
        self.assertEqual(len(result.violations), 3)
        self.assertLessEqual(result.metrics["overall_git_score"], 50.0)
        
    def test_overall_git_score_calculation(self):
        """総合Gitスコア計算テスト"""
        # 高スコアケース
        high_metrics = {
            "branch_score": 90.0,
            "commit_score": 85.0
        }
        
        score = self.chronicle._calculate_overall_git_score(high_metrics)
        expected_score = (90.0 * 0.5) + (85.0 * 0.5)  # 87.5
        self.assertAlmostEqual(score, expected_score, places=1)
        
        # 低スコアケース
        low_metrics = {
            "branch_score": 30.0,
            "commit_score": 40.0
        }
        
        score = self.chronicle._calculate_overall_git_score(low_metrics)
        expected_score = (30.0 * 0.5) + (40.0 * 0.5)  # 35.0
        self.assertAlmostEqual(score, expected_score, places=1)
        
    def test_git_improvement_recommendations(self):
        """Git改善提案生成テスト"""
        branch_result = {"overall_branch_score": 60.0}
        commit_result = {"overall_commit_score": 70.0}
        violations = [
            {
                "type": GitViolationType.DIRECT_MAIN_COMMIT
            },
            {
                "type": GitViolationType.BRANCH_NAMING_VIOLATION
            }
        ]
        
        recommendations = self.chronicle._generate_git_improvement_recommendations(
            branch_result, commit_result, violations
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0, "Should generate improvement recommendations")
        
        # ブランチ戦略改善の提案が含まれることを確認
        branch_recommendations = [r for r in recommendations if "branch" in r.lower()]
        self.assertGreater(len(branch_recommendations), 0)


class TestGitChronicleIntegration(unittest.TestCase):
    """Git年代記魔法統合テスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.chronicle = GitChronicle(self.project_root)
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    async def test_comprehensive_git_audit(self):
        """包括的Git監査テスト"""
        test_repo_path = "test_repository"
        
        # Git操作のモックを設定
        with patch('subprocess.run') as mock_subprocess:
            # ブランチ情報のモック
            mock_subprocess.side_effect = [
                Mock(stdout="  main\n* feature/issue-123-auth\n"),  # git branch
                Mock(stdout="  origin/main\n"),                     # git branch -r
                Mock(stdout="feature/issue-123-auth\n"),            # current branch
                Mock(returncode=0, stdout=""),                      # protected branch check
                Mock(stdout="abc123|2025-01-20|feat: add auth|dev|dev@example.com\n")  # commit history
            ]
            
            result = await self.chronicle.execute_audit(test_repo_path)
            
        # 結果検証
        self.assertEqual(result.auditor_name, "GitChronicle")
        self.assertIsInstance(result.violations, list)
        self.assertIsInstance(result.metrics, dict)
        self.assertIn("overall_git_score", result.metrics)
        self.assertIsInstance(result.recommendations, list)
        
    async def test_git_workflow_compliance_assessment(self):
        """Gitワークフロー遵守評価テスト"""
        test_repo_path = "workflow_test_repo"
        
        # GitHub Flow遵守不足のシナリオをテスト
        with patch.object(self.chronicle.branch_analyzer, 'analyze_branch_strategy') as mock_branch:
            with patch.object(self.chronicle.commit_analyzer, 'analyze_commit_quality') as mock_commit:
                
                # ワークフロー遵守不足のレスポンス設定
                mock_branch.return_value = {
                    "naming_violations": [],
                    "protected_violations": [
                        {
                            "type": GitViolationType.DIRECT_MAIN_COMMIT,
                            "severity": "HIGH",
                            "description": "Direct commit to main branch detected"
                        }
                    ],
                    "overall_branch_score": 45.0
                }
                
                mock_commit.return_value = {
                    "quality_violations": [
                        {
                            "type": GitViolationType.COMMIT_CONVENTION_VIOLATION,
                            "severity": "MEDIUM",
                            "description": "Non-conventional commit format"
                        }
                    ],
                    "overall_commit_score": 55.0
                }
                
                result = await self.chronicle.execute_audit(test_repo_path)
                
                # ワークフロー違反が検出されることを確認
                workflow_violations = [
                    v for v in result.violations 
                                        if \
                        v.get("type") in [GitViolationType.DIRECT_MAIN_COMMIT, GitViolationType.COMMIT_CONVENTION_VIOLATION]
                ]
                self.assertGreater(len(workflow_violations), 0)
                
                # 改善提案が生成されることを確認
                self.assertGreater(len(result.recommendations), 0)


if __name__ == "__main__":
    # 基本テスト実行
    unittest.main(verbosity=2)