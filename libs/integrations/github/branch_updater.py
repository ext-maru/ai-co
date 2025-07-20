#!/usr/bin/env python3
"""
🌿 Branch Updater
ブランチ自動更新機能 - behind状態の安全な解決

機能:
- ファストフォワード可能性の検証
- 安全なブランチ更新
- コンフリクトリスク評価
- 自動リベース・マージ
"""

import logging
import os
import subprocess
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import git
from pathlib import Path

logger = logging.getLogger(__name__)


class UpdateStrategy(Enum):
    """更新戦略"""
    FAST_FORWARD = "fast_forward"
    MERGE_COMMIT = "merge_commit"
    REBASE = "rebase"
    MANUAL_REQUIRED = "manual_required"


class RiskLevel(Enum):
    """リスクレベル"""
    SAFE = "safe"           # 完全に安全
    LOW = "low"             # 低リスク
    MEDIUM = "medium"       # 中リスク - 注意必要
    HIGH = "high"           # 高リスク - 手動推奨
    CRITICAL = "critical"   # 非常に危険


@dataclass
class BranchStatus:
    """ブランチ状態情報"""
    branch_name: str
    commits_behind: int
    commits_ahead: int
    last_common_commit: str
    diverged: bool
    fast_forward_possible: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_name": self.branch_name,
            "commits_behind": self.commits_behind,
            "commits_ahead": self.commits_ahead,
            "last_common_commit": self.last_common_commit,
            "diverged": self.diverged,
            "fast_forward_possible": self.fast_forward_possible
        }


@dataclass
class UpdateAnalysis:
    """更新分析結果"""
    branch_status: BranchStatus
    recommended_strategy: UpdateStrategy
    risk_level: RiskLevel
    confidence_score: float
    estimated_conflicts: int
    affected_files: List[str]
    safety_checks: Dict[str, bool]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_status": self.branch_status.to_dict(),
            "recommended_strategy": self.recommended_strategy.value,
            "risk_level": self.risk_level.value,
            "confidence_score": self.confidence_score,
            "estimated_conflicts": self.estimated_conflicts,
            "affected_files": self.affected_files,
            "safety_checks": self.safety_checks
        }


class BranchUpdater:
    """ブランチ自動更新システム"""
    
    def __init__(self, repo_path: str):
        """
        初期化
        
        Args:
            repo_path: Gitリポジトリのパス
        """
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)
        
        # 安全設定
        self.max_commits_behind = 50  # 最大遅れコミット数
        self.max_affected_files = 20  # 最大影響ファイル数
        self.safe_file_extensions = {'.md', '.txt', '.json', '.yml', '.yaml'}
        self.dangerous_paths = {'/', '/bin', '/etc', '/usr', '/var'}
    
    async def analyze_branch_update(
        self,
        head_branch: str,
        base_branch: str = "main"
    ) -> UpdateAnalysis:
        """
        ブランチ更新の分析
        
        Args:
            head_branch: 更新対象ブランチ
            base_branch: ベースブランチ
            
        Returns:
            UpdateAnalysis: 分析結果
        """
        try:
            # ブランチ状態を取得
            branch_status = await self._get_branch_status(head_branch, base_branch)
            
            # 更新戦略を決定
            strategy = self._determine_update_strategy(branch_status)
            
            # リスクレベルを評価
            risk_level = await self._evaluate_risk_level(branch_status, base_branch)
            
            # 信頼度スコアを算出
            confidence = self._calculate_confidence_score(branch_status, risk_level)
            
            # コンフリクト予測
            estimated_conflicts, affected_files = await self._predict_conflicts(
                head_branch, base_branch, branch_status
            )
            
            # 安全性チェック
            safety_checks = await self._perform_safety_checks(
                head_branch, base_branch, branch_status
            )
            
            return UpdateAnalysis(
                branch_status=branch_status,
                recommended_strategy=strategy,
                risk_level=risk_level,
                confidence_score=confidence,
                estimated_conflicts=estimated_conflicts,
                affected_files=affected_files,
                safety_checks=safety_checks
            )
            
        except Exception as e:
            logger.error(f"Branch update analysis failed: {e}")
            # エラー時は保守的な結果を返す
            return UpdateAnalysis(
                branch_status=BranchStatus(
                    branch_name=head_branch,
                    commits_behind=0,
                    commits_ahead=0,
                    last_common_commit="",
                    diverged=True,
                    fast_forward_possible=False
                ),
                recommended_strategy=UpdateStrategy.MANUAL_REQUIRED,
                risk_level=RiskLevel.CRITICAL,
                confidence_score=0.0,
                estimated_conflicts=999,
                affected_files=[],
                safety_checks={}
            )
    
    async def _get_branch_status(self, head_branch: str, base_branch: str) -> BranchStatus:
        """ブランチ状態の取得"""
        try:
            # リモートから最新情報を取得
            self.repo.remotes.origin.fetch()
            
            # ブランチ参照を取得
            head_ref = f"origin/{head_branch}"
            base_ref = f"origin/{base_branch}"
            
            try:
                head_commit = self.repo.commit(head_ref)
                base_commit = self.repo.commit(base_ref)
            except git.BadName as e:
                logger.error(f"Branch not found: {e}")
                raise
            
            # 共通祖先を見つける
            merge_base = self.repo.merge_base(head_commit, base_commit)
            if not merge_base:
                raise ValueError("No common ancestor found")
            
            common_commit = merge_base[0]
            
            # behind/ahead情報を計算
            commits_behind = len(list(self.repo.iter_commits(
                f"{common_commit}..{base_commit}"
            )))
            
            commits_ahead = len(list(self.repo.iter_commits(
                f"{common_commit}..{head_commit}"
            )))
            
            # 分岐しているかチェック
            diverged = commits_ahead > 0 and commits_behind > 0
            
            # ファストフォワード可能性
            fast_forward_possible = commits_ahead == 0 and commits_behind > 0
            
            return BranchStatus(
                branch_name=head_branch,
                commits_behind=commits_behind,
                commits_ahead=commits_ahead,
                last_common_commit=common_commit.hexsha,
                diverged=diverged,
                fast_forward_possible=fast_forward_possible
            )
            
        except Exception as e:
            logger.error(f"Failed to get branch status: {e}")
            raise
    
    def _determine_update_strategy(self, branch_status: BranchStatus) -> UpdateStrategy:
        """更新戦略の決定"""
        
        # ファストフォワード可能な場合
        if branch_status.fast_forward_possible:
            return UpdateStrategy.FAST_FORWARD
        
        # 分岐していない場合（すでに最新）
        if branch_status.commits_behind == 0:
            return UpdateStrategy.FAST_FORWARD  # 実質更新不要
        
        # 分岐している場合
        if branch_status.diverged:
            # 小さな変更の場合はリベース
            if branch_status.commits_ahead <= 3 and branch_status.commits_behind <= 10:
                return UpdateStrategy.REBASE
            # 大きな変更の場合はマージコミット
            elif branch_status.commits_ahead <= 10 and branch_status.commits_behind <= 20:
                return UpdateStrategy.MERGE_COMMIT
            else:
                # 大規模な分岐は手動対応
                return UpdateStrategy.MANUAL_REQUIRED
        
        # デフォルトは手動対応
        return UpdateStrategy.MANUAL_REQUIRED
    
    async def _evaluate_risk_level(
        self, 
        branch_status: BranchStatus, 
        base_branch: str
    ) -> RiskLevel:
        """リスクレベルの評価"""
        
        # 基本リスクの算出
        risk_score = 0.0
        
        # コミット数によるリスク
        if branch_status.commits_behind > self.max_commits_behind:
            risk_score += 0.4
        elif branch_status.commits_behind > 20:
            risk_score += 0.2
        elif branch_status.commits_behind > 10:
            risk_score += 0.1
        
        # 分岐によるリスク
        if branch_status.diverged:
            risk_score += 0.2
            if branch_status.commits_ahead > 10:
                risk_score += 0.2
        
        # 影響ファイル数によるリスク
        try:
            # 変更されたファイルを取得
            head_ref = f"origin/{branch_status.branch_name}"
            base_ref = f"origin/{base_branch}"
            
            diff = self.repo.git.diff('--name-only', f"{base_ref}..{head_ref}")
            changed_files = diff.split('\n') if diff else []
            
            if len(changed_files) > self.max_affected_files:
                risk_score += 0.3
            elif len(changed_files) > 10:
                risk_score += 0.1
            
            # 危険なファイルの変更
            dangerous_file_count = 0
            for file_path in changed_files:
                if any(file_path.startswith(path) for path in self.dangerous_paths):
                    dangerous_file_count += 1
                elif not any(file_path.endswith(ext) for ext in self.safe_file_extensions):
                    dangerous_file_count += 1
            
            if dangerous_file_count > 5:
                risk_score += 0.3
            elif dangerous_file_count > 0:
                risk_score += 0.1
                
        except Exception as e:
            logger.warning(f"Failed to evaluate file risks: {e}")
            risk_score += 0.2  # 不明な場合はリスクを追加
        
        # リスクレベルに変換
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.4:
            return RiskLevel.MEDIUM
        elif risk_score >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.SAFE
    
    def _calculate_confidence_score(
        self, 
        branch_status: BranchStatus, 
        risk_level: RiskLevel
    ) -> float:
        """信頼度スコアの算出"""
        
        confidence = 0.5  # ベーススコア
        
        # ファストフォワード可能性
        if branch_status.fast_forward_possible:
            confidence += 0.4
        
        # 分岐状況
        if not branch_status.diverged:
            confidence += 0.2
        elif branch_status.commits_ahead <= 3:
            confidence += 0.1
        else:
            confidence -= 0.1
        
        # コミット数
        if branch_status.commits_behind <= 5:
            confidence += 0.2
        elif branch_status.commits_behind <= 20:
            confidence += 0.1
        else:
            confidence -= 0.2
        
        # リスクレベル
        risk_adjustments = {
            RiskLevel.SAFE: 0.3,
            RiskLevel.LOW: 0.1,
            RiskLevel.MEDIUM: -0.1,
            RiskLevel.HIGH: -0.3,
            RiskLevel.CRITICAL: -0.5
        }
        confidence += risk_adjustments.get(risk_level, 0)
        
        return max(0.0, min(1.0, confidence))
    
    async def _predict_conflicts(
        self, 
        head_branch: str, 
        base_branch: str, 
        branch_status: BranchStatus
    ) -> Tuple[int, List[str]]:
        """コンフリクト予測"""
        
        try:
            if not branch_status.diverged:
                return 0, []
            
            # merge-tree を使用してコンフリクトを予測
            head_ref = f"origin/{head_branch}"
            base_ref = f"origin/{base_branch}"
            
            result = subprocess.run([
                'git', 'merge-tree', 
                branch_status.last_common_commit,
                head_ref,
                base_ref
            ], cwd=self.repo_path, capture_output=True, text=True, check=False)
            
            if result.returncode != 0 or not result.stdout:
                return 0, []
            
            # 結果を解析してコンフリクトファイルを抽出
            conflict_files = []
            lines = result.stdout.split('\n')
            
            for line in lines:
                if line.startswith('<<<<<<'):
                    # コンフリクトマーカーを検出
                    continue
                elif 'changed in both' in line.lower():
                    # ファイルパスを抽出（簡略化）
                    parts = line.split()
                    if parts:
                        conflict_files.append(parts[-1])
            
            return len(conflict_files), conflict_files
            
        except Exception as e:
            logger.warning(f"Failed to predict conflicts: {e}")
            return 1, []  # 不明な場合は保守的に1個のコンフリクトを想定
    
    async def _perform_safety_checks(
        self, 
        head_branch: str, 
        base_branch: str, 
        branch_status: BranchStatus
    ) -> Dict[str, bool]:
        """安全性チェック"""
        
        checks = {}
        
        try:
            # ブランチ存在チェック
            checks["branches_exist"] = self._check_branches_exist(head_branch, base_branch)
            
            # リポジトリクリーンチェック
            checks["repo_clean"] = not self.repo.is_dirty()
            
            # ブランチ保護チェック
            checks["branch_protection_safe"] = await self._check_branch_protection(base_branch)
            
            # バックアップ可能性チェック
            checks["backup_possible"] = self._check_backup_possible()
            
            # 権限チェック
            checks["sufficient_permissions"] = self._check_permissions()
            
            # サイズ制限チェック
            checks["size_limits_ok"] = branch_status.commits_behind <= self.max_commits_behind
            
        except Exception as e:
            logger.error(f"Safety checks failed: {e}")
            # エラー時は全て失敗とする
            return {key: False for key in [
                "branches_exist", "repo_clean", "branch_protection_safe",
                "backup_possible", "sufficient_permissions", "size_limits_ok"
            ]}
        
        return checks
    
    def _check_branches_exist(self, head_branch: str, base_branch: str) -> bool:
        """ブランチ存在チェック"""
        try:
            self.repo.commit(f"origin/{head_branch}")
            self.repo.commit(f"origin/{base_branch}")
            return True
        except git.BadName:
            return False
    
    async def _check_branch_protection(self, branch: str) -> bool:
        """ブランチプロテクションチェック（簡略化）"""
        # 実際の実装では GitHub API を使用してブランチプロテクション設定を確認
        # ここでは簡略化してmainブランチは保護されていると仮定
        return branch != "main"
    
    def _check_backup_possible(self) -> bool:
        """バックアップ可能性チェック"""
        try:
            # 現在のブランチをバックアップできるかチェック
            current_branch = self.repo.active_branch.name
            backup_name = f"backup-{current_branch}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # 同名のバックアップブランチが存在しないかチェック
            existing_branches = [ref.name for ref in self.repo.refs]
            return backup_name not in existing_branches
            
        except Exception:
            return False
    
    def _check_permissions(self) -> bool:
        """権限チェック"""
        try:
            # リポジトリディレクトリへの書き込み権限をチェック
            return os.access(self.repo_path, os.W_OK)
        except Exception:
            return False
    
    async def execute_safe_update(
        self, 
        analysis: UpdateAnalysis,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """安全な更新の実行"""
        
        if analysis.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return {
                "success": False,
                "reason": "risk_too_high",
                "risk_level": analysis.risk_level.value,
                "message": "リスクが高すぎるため手動対応が必要です"
            }
        
        if analysis.confidence_score < 0.7:
            return {
                "success": False,
                "reason": "confidence_too_low",
                "confidence": analysis.confidence_score,
                "message": "信頼度が低いため手動対応が必要です"
            }
        
        # 安全性チェック
        if not all(analysis.safety_checks.values()):
            failed_checks = [k for k, v in analysis.safety_checks.items() if not v]
            return {
                "success": False,
                "reason": "safety_checks_failed",
                "failed_checks": failed_checks,
                "message": f"安全性チェックに失敗: {', '.join(failed_checks)}"
            }
        
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "strategy": analysis.recommended_strategy.value,
                "message": "ドライラン - 実際の更新は実行されませんでした"
            }
        
        # 実際の更新を実行
        try:
            if analysis.recommended_strategy == UpdateStrategy.FAST_FORWARD:
                result = await self._execute_fast_forward(analysis.branch_status)
            elif analysis.recommended_strategy == UpdateStrategy.MERGE_COMMIT:
                result = await self._execute_merge_commit(analysis.branch_status)
            elif analysis.recommended_strategy == UpdateStrategy.REBASE:
                result = await self._execute_rebase(analysis.branch_status)
            else:
                return {
                    "success": False,
                    "reason": "strategy_not_supported",
                    "strategy": analysis.recommended_strategy.value,
                    "message": "この更新戦略は自動実行できません"
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            return {
                "success": False,
                "reason": "execution_failed",
                "error": str(e),
                "message": "更新実行中にエラーが発生しました"
            }
    
    async def _execute_fast_forward(self, branch_status: BranchStatus) -> Dict[str, Any]:
        """ファストフォワード更新の実行"""
        try:
            # 現在のブランチに切り替え
            current_branch = branch_status.branch_name
            self.repo.git.checkout(current_branch)
            
            # ファストフォワード更新
            self.repo.git.pull('origin', current_branch, '--ff-only')
            
            return {
                "success": True,
                "strategy": "fast_forward",
                "message": f"ブランチ {current_branch} をファストフォワード更新しました"
            }
            
        except Exception as e:
            logger.error(f"Fast forward failed: {e}")
            return {
                "success": False,
                "strategy": "fast_forward",
                "error": str(e),
                "message": "ファストフォワード更新に失敗しました"
            }
    
    async def _execute_merge_commit(self, branch_status: BranchStatus) -> Dict[str, Any]:
        """マージコミット更新の実行"""
        try:
            current_branch = branch_status.branch_name
            self.repo.git.checkout(current_branch)
            
            # マージコミットで更新
            self.repo.git.merge(f'origin/main', '--no-ff', '-m', f'Merge main into {current_branch}')
            
            return {
                "success": True,
                "strategy": "merge_commit",
                "message": f"ブランチ {current_branch} にマージコミットで更新しました"
            }
            
        except Exception as e:
            logger.error(f"Merge commit failed: {e}")
            return {
                "success": False,
                "strategy": "merge_commit",
                "error": str(e),
                "message": "マージコミット更新に失敗しました"
            }
    
    async def _execute_rebase(self, branch_status: BranchStatus) -> Dict[str, Any]:
        """リベース更新の実行"""
        try:
            current_branch = branch_status.branch_name
            self.repo.git.checkout(current_branch)
            
            # リベース実行
            self.repo.git.rebase('origin/main')
            
            return {
                "success": True,
                "strategy": "rebase",
                "message": f"ブランチ {current_branch} をリベースで更新しました"
            }
            
        except Exception as e:
            logger.error(f"Rebase failed: {e}")
            return {
                "success": False,
                "strategy": "rebase",
                "error": str(e),
                "message": "リベース更新に失敗しました"
            }


# 使用例
async def example_usage():
    """使用例"""
    updater = BranchUpdater("/path/to/repo")
    
    # ブランチ更新分析
    analysis = await updater.analyze_branch_update("feature/new-feature", "main")
    
    print(f"Strategy: {analysis.recommended_strategy.value}")
    print(f"Risk: {analysis.risk_level.value}")
    print(f"Confidence: {analysis.confidence_score:.2f}")
    
    # 安全な更新実行
    if analysis.risk_level in [RiskLevel.SAFE, RiskLevel.LOW]:
        result = await updater.execute_safe_update(analysis)
        if result["success"]:
            print("Update successful!")
        else:
            print(f"Update failed: {result['message']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())