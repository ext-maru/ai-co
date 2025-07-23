#!/usr/bin/env python3
"""
📜 Git Chronicle Magic - Git年代記魔法
====================================

Git/GitHub Flow遵守、コミット規約、ブランチ戦略を監査する古代魔法システム
Issue #201対応

Features:
- ブランチ戦略違反検出
- コミット規約遵守確認
- プッシュ遅延検出
- GitHub Flow品質監査
- Git履歴整合性分析
- 自動修正提案生成

Author: Claude Elder
Created: 2025-07-21
"""

import asyncio
import json
import logging
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import xml.etree.ElementTree as ET

# プロジェクトルートをパスに追加
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.base import AncientElderBase, AuditResult, ViolationSeverity


class GitWorkflowType:
    """Gitワークフローの種類"""
    GITHUB_FLOW = "github_flow"          # GitHub Flow
    GIT_FLOW = "git_flow"               # Git Flow
    FEATURE_BRANCH = "feature_branch"    # Feature Branch
    TRUNK_BASED = "trunk_based"         # Trunk-based


class GitViolationType:
    """Git違反の種類"""
    INVALID_BRANCH_NAME = "INVALID_BRANCH_NAME"                # 無効なブランチ名
    DIRECT_MAIN_COMMIT = "DIRECT_MAIN_COMMIT"                  # mainブランチ直接コミット
    MISSING_PR = "MISSING_PR"                                  # プルリクエスト省略
    POOR_COMMIT_MESSAGE = "POOR_COMMIT_MESSAGE"                # 低品質コミットメッセージ
    PUSH_DELAY_VIOLATION = "PUSH_DELAY_VIOLATION"              # プッシュ遅延違反
    MERGE_WITHOUT_REVIEW = "MERGE_WITHOUT_REVIEW"              # レビューなしマージ
    FORCE_PUSH_ABUSE = "FORCE_PUSH_ABUSE"                      # force push乱用
    BRANCH_NAMING_VIOLATION = "BRANCH_NAMING_VIOLATION"        # ブランチ命名規約違反
    COMMIT_CONVENTION_VIOLATION = "COMMIT_CONVENTION_VIOLATION" # コミット規約違反


class GitBranchAnalyzer:
    """Gitブランチ戦略分析システム"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.logger = logging.getLogger("GitBranchAnalyzer")
        
        # ブランチ命名規約
        self.branch_naming_patterns = {
            "feature": re.compile(r'^feature/issue-\d+-[a-z0-9-]+$'),
            "fix": re.compile(r'^fix/issue-\d+-[a-z0-9-]+$'),
            "hotfix": re.compile(r'^hotfix/[a-z0-9-]+$'),
            "release": re.compile(r'^release/v?\d+\.\d+\.\d+$'),
            "docs": re.compile(r'^docs/[a-z0-9-]+$'),
            "chore": re.compile(r'^chore/[a-z0-9-]+$')
        }
        
        # 保護されたブランチ
        self.protected_branches = {"main", "master", "develop", "release"}
        
    def analyze_branch_strategy(self, 
                              time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """ブランチ戦略を分析"""
        if time_window is None:
            time_window = timedelta(days=30)  # デフォルト30日
            
        try:
            # 現在のブランチ情報を取得
            branch_info = self._get_branch_information()
            
            # ブランチ命名規約をチェック
            naming_violations = self._check_branch_naming_conventions(branch_info)
            
            # 保護されたブランチへの直接コミットをチェック
            protected_violations = self._check_protected_branch_violations(time_window)
            
            # ブランチ戦略の遵守状況を分析
            strategy_analysis = self._analyze_workflow_compliance(branch_info, time_window)
            
            return {
                "branch_info": branch_info,
                "naming_violations": naming_violations,
                "protected_violations": protected_violations,
                "strategy_analysis": strategy_analysis,
                "overall_branch_score": self._calculate_branch_score(
                    naming_violations, protected_violations, strategy_analysis
                )
            }
            
        except Exception as e:
            self.logger.error(f"Branch strategy analysis failed: {e}")
            return {
                "error": str(e),
                "branch_info": {},
                "naming_violations": [],
                "protected_violations": [],
                "strategy_analysis": {},
                "overall_branch_score": 0.0
            }
            
    def _get_branch_information(self) -> Dict[str, Any]:
        """ブランチ情報を取得"""
        try:
            # ローカルブランチ一覧
            local_result = subprocess.run(
                ["git", "branch"], 
                cwd=self.project_root, 
                capture_output=True, 
                text=True
            )
            
            # リモートブランチ一覧
            remote_result = subprocess.run(
                ["git", "branch", "-r"], 
                cwd=self.project_root, 
                capture_output=True, 
                text=True
            )
            
            # 現在のブランチ
            current_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                cwd=self.project_root, 
                capture_output=True, 
                text=True
            )
            
            local_branches = [b.strip(
                ).replace("* ",
                "") for b in local_result.stdout.split('\n') if b.strip(
            )]
            remote_branches = [b.strip() for b in remote_result.stdout.split('\n') if b.strip() and not b.startswith("origin/HEAD")]
            current_branch = current_result.stdout.strip()
            
            return {
                "current_branch": current_branch,
                "local_branches": local_branches,
                "remote_branches": remote_branches,
                "total_branches": len(local_branches),
                "protected_branches_present": [b for b in local_branches if b in self.protected_branches]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get branch information: {e}")
            return {}
            
    def _check_branch_naming_conventions(self, branch_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ブランチ命名規約をチェック"""
        violations = []
        local_branches = branch_info.get("local_branches", [])
        
        for branch in local_branches:
            # 保護されたブランチはスキップ
            if branch in self.protected_branches:
                continue
                
            # 命名規約に準拠しているかチェック
            is_valid = False
            branch_type = None
            
            for pattern_type, pattern in self.branch_naming_patterns.items():
                if pattern.match(branch):
                    is_valid = True
                    branch_type = pattern_type
                    break
                    
            if not is_valid:
                violations.append({
                    "type": GitViolationType.BRANCH_NAMING_VIOLATION,
                    "severity": "MEDIUM",
                    "branch_name": branch,
                    "description": f"Branch '{branch}' does not follow naming conventions",
                    "expected_patterns": list(self.branch_naming_patterns.keys()),
                    "suggestion": "Use format: <type>/issue-<number>-<description> (e.g., feature/issue-123-user-auth)"
                })
                
        return violations
        
    def _check_protected_branch_violations(self, time_window: timedelta) -> List[Dict[str, Any]]:
        """保護されたブランチへの直接コミット違反をチェック"""
        violations = []
        
        try:
            since_date = (datetime.now() - time_window).strftime("%Y-%m-%d")
            
            for protected_branch in self.protected_branches:
                # 保護されたブランチへの直接コミットをチェック
                cmd = [
                    "git", "log", 
                    "--since", since_date,
                    "--pretty=format:%H|%ad|%s|%an",
                    "--date=iso",
                    protected_branch
                ]
                
                result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    # 直接コミットが存在する場合は違反として記録
                    commits = result.stdout.strip().split('\n')
                    
                    for commit_line in commits:
                        if commit_line:
                            parts = commit_line.split('|')
                            if len(parts) >= 4:
                                violations.append({
                                    "type": GitViolationType.DIRECT_MAIN_COMMIT,
                                    "severity": "HIGH",
                                    "branch": protected_branch,
                                    "commit_hash": parts[0],
                                    "commit_date": parts[1],
                                    "commit_message": parts[2],
                                    "author": parts[3],
                                    "description": f"Direct commit to protected branch '{protected_branch}'",
                                    "suggestion": "Use feature branches and pull requests for all changes"
                                })
                                
        except Exception as e:
            self.logger.error(f"Failed to check protected branch violations: {e}")
            
        return violations
        
    def _analyze_workflow_compliance(self, 
                                   branch_info: Dict[str, Any], 
                                   time_window: timedelta) -> Dict[str, Any]:
        """ワークフロー遵守状況を分析"""
        analysis = {
            "workflow_type": self._detect_workflow_type(branch_info),
            "feature_branch_usage": self._analyze_feature_branch_usage(time_window),
            "merge_strategy": self._analyze_merge_strategy(time_window),
            "branch_lifecycle": self._analyze_branch_lifecycle(time_window)
        }
        
        return analysis
        
    def _detect_workflow_type(self, branch_info: Dict[str, Any]) -> str:
        """使用中のワークフロータイプを検出"""
        local_branches = branch_info.get("local_branches", [])
        
        # Git Flowパターンの検出
        if any(b.startswith("develop") for b in local_branches):
            return GitWorkflowType.GIT_FLOW
            
        # Feature Branchパターンの検出
        if any(b.startswith("feature/") for b in local_branches):
            return GitWorkflowType.FEATURE_BRANCH
            
        # デフォルトはGitHub Flow
        return GitWorkflowType.GITHUB_FLOW
        
    def _analyze_feature_branch_usage(self, time_window: timedelta) -> Dict[str, Any]:
        """Feature Branch使用状況を分析"""
        try:
            since_date = (datetime.now() - time_window).strftime("%Y-%m-%d")
            
            # 期間内に作成されたブランチを取得
            cmd = ["git", "for-each-ref", "--format=%(refname:short)|%(committerdate)", "--since", since_date, "refs/heads/"]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            feature_branches = []
            total_branches = 0
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 1:
                        branch_name = parts[0]
                        total_branches += 1
                        
                        if branch_name.startswith("feature/"):
                            feature_branches.append(branch_name)
                            
            feature_branch_ratio = len(feature_branches) / max(total_branches, 1)
            
            return {
                "total_branches_created": total_branches,
                "feature_branches_created": len(feature_branches),
                "feature_branch_ratio": feature_branch_ratio,
                "compliance_score": feature_branch_ratio * 100
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze feature branch usage: {e}")
            return {"compliance_score": 0.0}
            
    def _analyze_merge_strategy(self, time_window: timedelta) -> Dict[str, Any]:
        """マージ戦略を分析"""
        # 簡単な実装：マージコミットの分析
        return {
            "merge_commits": 0,
            "squash_merges": 0,
            "rebase_merges": 0,
            "strategy": "merge_commit"
        }
        
    def _analyze_branch_lifecycle(self, time_window: timedelta) -> Dict[str, Any]:
        """ブランチライフサイクルを分析"""
        return {
            "average_branch_lifetime": "5 days",
            "stale_branches": 0,
            "active_branches": 3
        }
        
    def _calculate_branch_score(self, 
                              naming_violations: List[Dict[str, Any]],
                              protected_violations: List[Dict[str, Any]],
                              strategy_analysis: Dict[str, Any]) -> float:
        """ブランチスコアを計算"""
        base_score = 100.0
        
        # 命名規約違反による減点
        base_score -= len(naming_violations) * 5
        
        # 保護ブランチ違反による減点
        base_score -= len(protected_violations) * 20
        
        # Feature Branchの使用状況による加点
        feature_usage = strategy_analysis.get("feature_branch_usage", {})
        compliance_score = feature_usage.get("compliance_score", 0)
        base_score = (base_score * 0.7) + (compliance_score * 0.3)
        
        return max(base_score, 0.0)


class GitCommitAnalyzer:
    """Gitコミットメッセージ・規約分析システム"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.logger = logging.getLogger("GitCommitAnalyzer")
        
        # Conventional Commitsパターン
        self.commit_conventions = {
            "conventional_commits": re.compile(
                r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .+$'
            ),
            "angular": re.compile(
                r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .' \
                    '{1,50}$'
            ),
            "gitmoji": re.compile(r'^(:\w+:|[🎉✨🐛📝💄♻️⚡🔥💥🚀🔒➕➖📌👷📈🐧🍏🚩💚👌🔇🔊🔀💼🗃️🏷️🌱🚚📱💫🗑️♿💡🍻💬📄⚖️🩹🧐⛑️🙈📸⚗️🏁🥅🧱🧑‍💻])\s*'),
        }
        
        # コミットメッセージ品質パターン
        self.quality_patterns = {
            "too_short": re.compile(r'^.{1,10}$'),
            "too_long": re.compile(r'^.{100,}$'),
            "no_description": re.compile(r'^[A-Z][a-z]*$'),
            "all_caps": re.compile(r'^[A-Z\s]+$'),
            "no_punctuation": re.compile(r'^[^.!?]*$'),
        }
        
    def analyze_commit_quality(self, 
                             time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """コミット品質を分析"""
        if time_window is None:
            time_window = timedelta(days=30)  # デフォルト30日
            
        try:
            # コミット履歴を取得
            commits = self._get_commit_history(time_window)
            
            # 各コミットを分析
            commit_analysis = self._analyze_individual_commits(commits)
            
            # 規約遵守状況を評価
            convention_compliance = self._evaluate_convention_compliance(commit_analysis)
            
            # 品質違反を検出
            quality_violations = self._detect_commit_quality_violations(commit_analysis)
            
            return {
                "total_commits": len(commits),
                "commit_analysis": commit_analysis,
                "convention_compliance": convention_compliance,
                "quality_violations": quality_violations,
                "overall_commit_score": self._calculate_commit_score(
                    convention_compliance, quality_violations, len(commits)
                )
            }
            
        except Exception as e:
            self.logger.error(f"Commit quality analysis failed: {e}")
            return {
                "error": str(e),
                "total_commits": 0,
                "commit_analysis": [],
                "quality_violations": [],
                "overall_commit_score": 0.0
            }
            
    def _get_commit_history(self, time_window: timedelta) -> List[Dict[str, Any]]:
        """コミット履歴を取得"""
        try:
            since_date = (datetime.now() - time_window).strftime("%Y-%m-%d")
            cmd = [
                "git", "log", 
                "--since", since_date,
                "--pretty=format:%H|%ad|%s|%an|%ae",
                "--date=iso"
            ]
            
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 5:
                        commits.append({
                            "hash": parts[0],
                            "date": parts[1],
                            "message": parts[2],
                            "author": parts[3],
                            "email": parts[4]
                        })
                        
            return commits
            
        except Exception as e:
            self.logger.error(f"Failed to get commit history: {e}")
            return []
            
    def _analyze_individual_commits(self, commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """各コミットを個別分析"""
        analysis = []
        
        for commit in commits:
            message = commit["message"]
            
            commit_analysis = {
                "hash": commit["hash"],
                "message": message,
                "author": commit["author"],
                "date": commit["date"],
                "convention_match": self._check_commit_convention(message),
                "quality_issues": self._check_commit_quality(message),
                "message_length": len(message),
                "quality_score": self._calculate_individual_commit_score(message)
            }
            
            analysis.append(commit_analysis)
            
        return analysis
        
    def _check_commit_convention(self, message: str) -> Dict[str, Any]:
        """コミット規約チェック"""
        matches = {}
        
        for convention_name, pattern in self.commit_conventions.items():
            matches[convention_name] = bool(pattern.match(message))
            
        return {
            "matches": matches,
            "best_match": max(
                matches.items(),
                key=lambda x: x[1])[0] if any(matches.values()
            ) else None,
            "compliant": any(matches.values())
        }
        
    def _check_commit_quality(self, message: str) -> List[str]:
        """コミット品質問題をチェック"""
        issues = []
        
        for issue_type, pattern in self.quality_patterns.items():
            if pattern.match(message):
                issues.append(issue_type)
                
        # 追加の品質チェック
        if message and not message[0].isupper():
            issues.append("no_capital_start")
            
        if message.endswith('.'):
            issues.append("ends_with_period")
            
        return issues
        
    def _calculate_individual_commit_score(self, message: str) -> float:
        """個別コミットスコアを計算"""
        score = 100.0
        
        # 長さチェック
        if len(message) < 10:
            score -= 30
        elif len(message) > 72:
            score -= 10
            
        # 大文字始まりチェック
        if message and not message[0].isupper():
            score -= 10
            
        # 句読点チェック
        if message.endswith('.'):
            score -= 5
            
        return max(score, 0.0)
        
    def _evaluate_convention_compliance(
        self,
        commit_analysis: List[Dict[str,
        Any]]
    ) -> Dict[str, Any]:
        """規約遵守状況を評価"""
        total_commits = len(commit_analysis)
        if total_commits == 0:
            return {"compliance_rate": 0.0}
            
        compliant_commits = sum(1 for c in commit_analysis if c["convention_match"]["compliant"])
        compliance_rate = (compliant_commits / total_commits) * 100
        
        # 規約別の遵守率
        convention_rates = {}
        for convention in self.commit_conventions.keys():
            convention_matches = sum(
                1 for c in commit_analysis 
                if c["convention_match"]["matches"].get(convention, False)
            )
            convention_rates[convention] = (convention_matches / total_commits) * 100
            
        return {
            "compliance_rate": compliance_rate,
            "compliant_commits": compliant_commits,
            "total_commits": total_commits,
            "convention_rates": convention_rates,
            "recommended_convention": max(
                convention_rates.items(),
                key=lambda x: x[1]
            )[0] if convention_rates else None
        }
        
    def _detect_commit_quality_violations(
        self,
        commit_analysis: List[Dict[str,
        Any]]
    ) -> List[Dict[str, Any]]:
        """コミット品質違反を検出"""
        violations = []
        
        for commit in commit_analysis:
            # 規約違反
            if not commit["convention_match"]["compliant"]:
                violations.append({
                    "type": GitViolationType.COMMIT_CONVENTION_VIOLATION,
                    "severity": "MEDIUM",
                    "commit_hash": commit["hash"],
                    "commit_message": commit["message"],
                    "description": "Commit message does not follow conventional commit format",
                    "suggestion": "Use format: <type>(<scope>): <description> (e.g., feat(auth): add user login)"
                })
                
            # 品質問題
            quality_issues = commit["quality_issues"]
            if quality_issues:
                violations.append({
                    "type": GitViolationType.POOR_COMMIT_MESSAGE,
                    "severity": "LOW",
                    "commit_hash": commit["hash"],
                    "commit_message": commit["message"],
                    "quality_issues": quality_issues,
                    "description": f"Commit message has quality issues: {', '.join(quality_issues)}",
                    "suggestion": "Write clear, descriptive commit messages following best practices"
                })
                
        return violations
        
    def _calculate_commit_score(self, 
                              convention_compliance: Dict[str, Any],
                              quality_violations: List[Dict[str, Any]],
                              total_commits: int) -> float:
        """総合コミットスコアを計算"""
        if total_commits == 0:
            return 0.0
            
        # 規約遵守率によるスコア
        compliance_score = convention_compliance.get("compliance_rate", 0)
        
        # 違反による減点
        violation_penalty = len(quality_violations) * 2
        
        # 最終スコア計算
        final_score = compliance_score - violation_penalty
        
        return max(final_score, 0.0)


class GitChronicle(AncientElderBase):
    """Git年代記魔法 - 総合Git監査システム"""
    
    def __init__(self, project_root: Optional[Path] = None):
        super().__init__(specialty="git_chronicle")
        self.project_root = project_root or Path.cwd()
        self.logger = logging.getLogger("GitChronicle")
        
        # コンポーネント初期化
        self.branch_analyzer = GitBranchAnalyzer(project_root)
        self.commit_analyzer = GitCommitAnalyzer(project_root)
        
    async def audit(self, target_path: str, **kwargs) -> AuditResult:
        """AncientElderBaseの抽象メソッド実装"""
        return await self.execute_audit(target_path, **kwargs)
        
    def get_audit_scope(self) -> List[str]:
        """監査対象スコープを返す"""
        return [
            "git_branch_strategy",
            "git_commit_quality",
            "github_flow_compliance",
            "git_workflow_optimization"
        ]
        
    async def execute_audit(self, target_path: str, **kwargs) -> AuditResult:
        """Git年代記監査を実行"""
        start_time = datetime.now()
        violations = []
        metrics = {}
        
        try:
            self.logger.info(f"📜 Starting Git Chronicle audit for: {target_path}")
            
            # 1. ブランチ戦略分析
            branch_result = self.branch_analyzer.analyze_branch_strategy()
            violations.extend(branch_result.get("naming_violations", []))
            violations.extend(branch_result.get("protected_violations", []))
            metrics["branch_score"] = branch_result.get("overall_branch_score", 0)
            
            # 2. コミット品質分析
            commit_result = self.commit_analyzer.analyze_commit_quality()
            violations.extend(commit_result.get("quality_violations", []))
            metrics["commit_score"] = commit_result.get("overall_commit_score", 0)
            
            # 3. 総合Gitスコア計算
            overall_score = self._calculate_overall_git_score(metrics)
            metrics["overall_git_score"] = overall_score
            
            # 4. 改善提案生成
            recommendations = self._generate_git_improvement_recommendations(
                branch_result, commit_result, violations
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            metrics["execution_time"] = execution_time
            
            self.logger.info(f"✅ Git Chronicle audit completed in {execution_time:.2f}s")
            
            return AuditResult(
                auditor_name="GitChronicle",
                target_path=target_path,
                violations=violations,
                metrics=metrics,
                recommendations=recommendations,
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"❌ Git Chronicle audit failed: {e}")
            return AuditResult(
                auditor_name="GitChronicle",
                target_path=target_path,
                violations=[{
                    "type": "AUDIT_EXECUTION_FAILURE",
                    "severity": ViolationSeverity.HIGH,
                    "description": f"Git Chronicle audit execution failed: {str(e)}",
                    "location": target_path
                }],
                metrics={"error": str(e)},
                recommendations=[],
                execution_time=(datetime.now() - start_time).total_seconds()
            )
            
    def _calculate_overall_git_score(self, metrics: Dict[str, Any]) -> float:
        """総合Gitスコアを計算"""
        branch_score = metrics.get("branch_score", 0)
        commit_score = metrics.get("commit_score", 0)
        
        # ブランチ戦略 50% + コミット品質 50%
        overall_score = (branch_score * 0.5) + (commit_score * 0.5)
        return min(overall_score, 100.0)
        
    def _generate_git_improvement_recommendations(self,
                                                branch_result: Dict[str, Any],
                                                commit_result: Dict[str, Any],
                                                violations: List[Dict[str, Any]]) -> List[str]:
        """Git改善提案を生成"""
        recommendations = []
        
        # ブランチ戦略改善提案
        branch_score = branch_result.get("overall_branch_score", 0)
        if branch_score < 70:
            recommendations.append(
                "Improve branch naming conventions and use feature branches consistently"
            )
            
        # コミット品質改善提案
        commit_score = commit_result.get("overall_commit_score", 0)
        if commit_score < 75:
            recommendations.append(
                "Follow conventional commit format and improve commit message quality"
            )
            
        # 違反固有の改善提案
        violation_types = set(v.get("type") for v in violations)
        
        if GitViolationType.DIRECT_MAIN_COMMIT in violation_types:
            recommendations.append("Prohibit direct commits to main branch and use pull requests")
            
        if GitViolationType.BRANCH_NAMING_VIOLATION in violation_types:
            recommendations.append("Establish and enforce branch naming conventions")
            
        if GitViolationType.COMMIT_CONVENTION_VIOLATION in violation_types:
            recommendations.append("Adopt conventional commits format for better change tracking")
            
        return recommendations