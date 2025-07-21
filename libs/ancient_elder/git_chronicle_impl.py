"""
📚 Git Chronicle Implementation - Git履歴品質監査の実装
"""

import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class GitChronicleImpl:
    """Git履歴品質監査の実装クラス"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        
        # Conventional Commitsのパターン
        self.conventional_patterns = {
            "feat": re.compile(r"^feat(\(.+\))?!?:\s*.+"),
            "fix": re.compile(r"^fix(\(.+\))?!?:\s*.+"),
            "docs": re.compile(r"^docs(\(.+\))?!?:\s*.+"),
            "style": re.compile(r"^style(\(.+\))?!?:\s*.+"),
            "refactor": re.compile(r"^refactor(\(.+\))?!?:\s*.+"),
            "test": re.compile(r"^test(\(.+\))?!?:\s*.+"),
            "chore": re.compile(r"^chore(\(.+\))?!?:\s*.+"),
            "perf": re.compile(r"^perf(\(.+\))?!?:\s*.+"),
        }
        
        # ブランチ命名規則
        self.branch_patterns = {
            "feature": re.compile(r"^feature/[\w-]+"),
            "fix": re.compile(r"^fix/[\w-]+"),
            "docs": re.compile(r"^docs/[\w-]+"),
            "chore": re.compile(r"^chore/[\w-]+"),
            "hotfix": re.compile(r"^hotfix/[\w-]+"),
        }
        
    def analyze_commit_messages(self, days: int = 30) -> Dict[str, Any]:
        """コミットメッセージの品質を分析"""
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        try:
            # Gitログを取得
            cmd = ['git', 'log', '--oneline', f'--since={since}', '--format=%H|%s|%an|%ai']
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                logger.error(f"Git log failed: {result.stderr}")
                return {"error": "Git log failed", "violations": []}
            
            commits = []
            violations = []
            conventional_count = 0
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                parts = line.split('|', 3)
                if len(parts) >= 4:
                    hash_id, message, author, date = parts
                    
                    # Conventional Commits準拠チェック
                    is_conventional = False
                    for pattern_type, pattern in self.conventional_patterns.items():
                        if pattern.match(message):
                            is_conventional = True
                            conventional_count += 1
                            break
                    
                    if not is_conventional:
                        violations.append({
                            "type": "NON_CONVENTIONAL_COMMIT",
                            "severity": "MEDIUM",
                            "description": f"Non-conventional commit message: {message[:50]}...",
                            "location": hash_id[:8],
                            "author": author,
                            "suggested_fix": "Use conventional commit format: type(scope): description"
                        })
                    
                    # メッセージ長チェック
                    if len(message) > 72:
                        violations.append({
                            "type": "LONG_COMMIT_MESSAGE",
                            "severity": "LOW",
                            "description": f"Commit message too long ({len(message)} chars)",
                            "location": hash_id[:8],
                            "suggested_fix": "Keep commit messages under 72 characters"
                        })
                    
                    commits.append({
                        "hash": hash_id,
                        "message": message,
                        "author": author,
                        "date": date,
                        "is_conventional": is_conventional
                    })
            
            return {
                "total_commits": len(commits),
                "conventional_commits": conventional_count,
                "conventional_rate": conventional_count / max(1, len(commits)),
                "violations": violations
            }
            
        except Exception as e:
            logger.error(f"Commit analysis failed: {e}")
            return {"error": str(e), "violations": []}
    
    def analyze_branch_strategy(self) -> Dict[str, Any]:
        """ブランチ戦略の分析"""
        try:
            # ブランチ一覧を取得
            cmd = ['git', 'branch', '-r']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                return {"error": "Git branch failed", "violations": []}
            
            branches = []
            violations = []
            valid_branches = 0
            
            for line in result.stdout.strip().split('\n'):
                branch = line.strip()
                if not branch or 'HEAD' in branch:
                    continue
                
                # origin/を除去
                if branch.startswith('origin/'):
                    branch_name = branch[7:]
                else:
                    branch_name = branch
                
                # ブランチ命名規則チェック
                is_valid = False
                for pattern_type, pattern in self.branch_patterns.items():
                    if pattern.match(branch_name) or branch_name in ['main', 'master', 'develop']:
                        is_valid = True
                        valid_branches += 1
                        break
                
                if not is_valid and branch_name not in ['main', 'master', 'develop']:
                    violations.append({
                        "type": "INVALID_BRANCH_NAME",
                        "severity": "LOW",
                        "description": f"Non-standard branch name: {branch_name}",
                        "location": branch_name,
                        "suggested_fix": "Use standard naming: feature/*, fix/*, docs/*, etc."
                    })
                
                branches.append({
                    "name": branch_name,
                    "is_valid": is_valid
                })
            
            return {
                "total_branches": len(branches),
                "valid_branches": valid_branches,
                "compliance_rate": valid_branches / max(1, len(branches)),
                "violations": violations
            }
            
        except Exception as e:
            logger.error(f"Branch analysis failed: {e}")
            return {"error": str(e), "violations": []}
    
    def check_merge_conflicts(self) -> Dict[str, Any]:
        """マージコンフリクトの検出"""
        try:
            # コンフリクトマーカーを含むファイルを検索
            cmd = ['git', 'grep', '-l', '^<<<<<<<\\|^=======$\\|^>>>>>>>']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            violations = []
            if result.returncode == 0 and result.stdout:
                for file_path in result.stdout.strip().split('\n'):
                    if file_path:
                        violations.append({
                            "type": "UNRESOLVED_CONFLICT",
                            "severity": "CRITICAL",
                            "description": f"Unresolved merge conflict in {file_path}",
                            "location": file_path,
                            "suggested_fix": "Resolve the merge conflict and remove conflict markers"
                        })
            
            return {
                "has_conflicts": len(violations) > 0,
                "conflict_files": len(violations),
                "violations": violations
            }
            
        except Exception as e:
            logger.error(f"Conflict check failed: {e}")
            return {"error": str(e), "violations": []}
    
    def analyze_commit_frequency(self, days: int = 30) -> Dict[str, Any]:
        """コミット頻度の分析"""
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        try:
            # 日別コミット数を取得
            cmd = ['git', 'log', f'--since={since}', '--format=%ai']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                return {"error": "Git log failed", "violations": []}
            
            # 日別にカウント
            daily_commits = {}
            for line in result.stdout.strip().split('\n'):
                if line:
                    date = line.split()[0]  # YYYY-MM-DD部分を取得
                    daily_commits[date] = daily_commits.get(date, 0) + 1
            
            # 統計情報
            commit_counts = list(daily_commits.values())
            total_commits = sum(commit_counts)
            active_days = len(commit_counts)
            
            violations = []
            
            # 大量コミットの検出
            for date, count in daily_commits.items():
                if count > 50:  # 1日50コミット以上は異常
                    violations.append({
                        "type": "EXCESSIVE_COMMITS",
                        "severity": "MEDIUM",
                        "description": f"Excessive commits on {date}: {count} commits",
                        "location": date,
                        "suggested_fix": "Consider squashing related commits"
                    })
            
            return {
                "total_commits": total_commits,
                "active_days": active_days,
                "average_commits_per_day": total_commits / max(1, days),
                "max_commits_in_day": max(commit_counts) if commit_counts else 0,
                "violations": violations
            }
            
        except Exception as e:
            logger.error(f"Frequency analysis failed: {e}")
            return {"error": str(e), "violations": []}