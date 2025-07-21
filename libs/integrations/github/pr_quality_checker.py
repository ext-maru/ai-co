#!/usr/bin/env python3
"""
PR品質チェック・自動返却システム
PRの品質をチェックし、基準を満たさない場合は理由付きで返却
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from github import Github
from github.PullRequest import PullRequest

logger = logging.getLogger(__name__)


class PRQualityChecker:
    """PR品質チェック・返却システム"""
    
    # 品質チェック項目
    QUALITY_CHECKS = {
        "has_tests": {
            "description": "テストコードが含まれているか",
            "weight": 0.3,
            "required": True
        },
        "has_description": {
            "description": "PR説明が十分か（100文字以上）",
            "weight": 0.2,
            "required": True
        },
        "no_todos": {
            "description": "TODO/FIXMEコメントが含まれていないか",
            "weight": 0.2,
            "required": False
        },
        "reasonable_size": {
            "description": "変更量が適切か（500行以下）",
            "weight": 0.2,
            "required": False
        },
        "ci_passed": {
            "description": "CIチェックが通っているか",
            "weight": 0.1,
            "required": True
        }
    }
    
    def __init__(self, repo):
        self.repo = repo
        self.quality_history_file = Path("logs/pr_quality_history.json")
        self.quality_history_file.parent.mkdir(exist_ok=True)
    
    async def check_pr_quality(self, pr_number: int) -> Dict[str, Any]:
        """PRの品質をチェック"""
        try:
            pr = self.repo.get_pull(pr_number)
            
            results = {
                "pr_number": pr_number,
                "title": pr.title,
                "author": pr.user.login,
                "created_at": pr.created_at.isoformat(),
                "checks": {},
                "overall_score": 0.0,
                "passed": False,
                "required_failures": [],
                "suggestions": []
            }
            
            # 各品質項目をチェック
            total_weight = 0.0
            total_score = 0.0
            
            # 1. テストコードチェック
            has_tests = await self._check_has_tests(pr)
            results["checks"]["has_tests"] = has_tests
            if has_tests:
                total_score += self.QUALITY_CHECKS["has_tests"]["weight"]
            elif self.QUALITY_CHECKS["has_tests"]["required"]:
                results["required_failures"].append("テストコードが含まれていません")
                results["suggestions"].append("- 新機能・修正に対応するテストを追加してください")
            total_weight += self.QUALITY_CHECKS["has_tests"]["weight"]
            
            # 2. PR説明チェック
            has_description = len(pr.body or "") >= 100
            results["checks"]["has_description"] = has_description
            if has_description:
                total_score += self.QUALITY_CHECKS["has_description"]["weight"]
            elif self.QUALITY_CHECKS["has_description"]["required"]:
                results["required_failures"].append("PR説明が不十分です（100文字未満）")
                results["suggestions"].append("- 変更内容と理由を詳しく説明してください")
            total_weight += self.QUALITY_CHECKS["has_description"]["weight"]
            
            # 3. TODO/FIXMEチェック
            no_todos = await self._check_no_todos(pr)
            results["checks"]["no_todos"] = no_todos
            if no_todos:
                total_score += self.QUALITY_CHECKS["no_todos"]["weight"]
            else:
                results["suggestions"].append("- TODO/FIXMEコメントを解決してください")
            total_weight += self.QUALITY_CHECKS["no_todos"]["weight"]
            
            # 4. 変更量チェック
            reasonable_size = pr.additions + pr.deletions <= 500
            results["checks"]["reasonable_size"] = reasonable_size
            if reasonable_size:
                total_score += self.QUALITY_CHECKS["reasonable_size"]["weight"]
            else:
                results["suggestions"].append("- PRを小さく分割することを検討してください")
            total_weight += self.QUALITY_CHECKS["reasonable_size"]["weight"]
            
            # 5. CIチェック
            ci_passed = await self._check_ci_status(pr)
            results["checks"]["ci_passed"] = ci_passed
            if ci_passed:
                total_score += self.QUALITY_CHECKS["ci_passed"]["weight"]
            elif self.QUALITY_CHECKS["ci_passed"]["required"]:
                results["required_failures"].append("CIチェックが失敗しています")
                results["suggestions"].append("- CI失敗の原因を修正してください")
            total_weight += self.QUALITY_CHECKS["ci_passed"]["weight"]
            
            # 総合スコア計算
            results["overall_score"] = (total_score / total_weight) * 100 if total_weight > 0 else 0
            results["passed"] = len(results["required_failures"]) == 0 and results["overall_score"] >= 70
            
            # 履歴を記録
            await self._record_quality_check(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error checking PR quality: {e}")
            return {
                "pr_number": pr_number,
                "error": str(e),
                "passed": False
            }
    
    async def _check_has_tests(self, pr: PullRequest) -> bool:
        """テストファイルが含まれているかチェック"""
        try:
            files = pr.get_files()
            for file in files:
                if "test" in file.filename.lower() and file.additions > 0:
                    return True
            return False
        except:
            return False
    
    async def _check_no_todos(self, pr: PullRequest) -> bool:
        """TODO/FIXMEが含まれていないかチェック"""
        try:
            files = pr.get_files()
            for file in files:
                if file.patch:
                    if "TODO" in file.patch or "FIXME" in file.patch:
                        return False
            return True
        except:
            return True  # エラー時は通す
    
    async def _check_ci_status(self, pr: PullRequest) -> bool:
        """CI状態をチェック"""
        try:
            # コミットステータスをチェック
            last_commit = list(pr.get_commits())[-1]
            statuses = last_commit.get_statuses()
            
            for status in statuses:
                if status.state in ["error", "failure"]:
                    return False
            
            # チェックランをチェック
            check_runs = last_commit.get_check_runs()
            for check in check_runs:
                if check.conclusion in ["failure", "cancelled", "timed_out"]:
                    return False
            
            return True
        except:
            return True  # エラー時は通す
    
    async def return_pr_with_reason(self, pr_number: int, quality_result: Dict[str, Any]) -> bool:
        """品質基準を満たさないPRを理由付きで返却"""
        try:
            pr = self.repo.get_pull(pr_number)
            issue = self.repo.get_issue(pr.number)  # PRもIssueとして扱える
            
            # 返却コメントを作成
            comment_text = "🔄 **PR品質チェック失敗 - 返却**\n\n"
            comment_text += f"このPRは品質基準を満たしていないため返却されました。\n\n"
            
            comment_text += f"**品質スコア**: {quality_result['overall_score']:.1f}/100 (合格基準: 70)\n\n"
            
            if quality_result['required_failures']:
                comment_text += "**必須項目の失敗**:\n"
                for failure in quality_result['required_failures']:
                    comment_text += f"- ❌ {failure}\n"
                comment_text += "\n"
            
            comment_text += "**品質チェック結果**:\n"
            for check_name, passed in quality_result['checks'].items():
                check_info = self.QUALITY_CHECKS[check_name]
                status = "✅" if passed else "❌"
                required = " (必須)" if check_info['required'] else ""
                comment_text += f"- {status} {check_info['description']}{required}\n"
            
            if quality_result['suggestions']:
                comment_text += "\n**改善提案**:\n"
                for suggestion in quality_result['suggestions']:
                    comment_text += f"{suggestion}\n"
            
            comment_text += "\n**次のステップ**:\n"
            comment_text += "1. 上記の問題を修正してください\n"
            comment_text += "2. 修正後、PRを更新してください\n"
            comment_text += "3. 品質チェックが自動的に再実行されます\n"
            
            # コメントを追加
            issue.create_comment(comment_text)
            
            # ラベルを追加
            issue.add_to_labels("needs-work", "quality-check-failed")
            
            # PRをドラフトに変換（可能な場合）
            try:
                pr.edit(draft=True)
                logger.info(f"PR #{pr_number} converted to draft due to quality issues")
            except:
                pass  # ドラフト変換できない場合は無視
            
            return True
            
        except Exception as e:
            logger.error(f"Error returning PR: {e}")
            return False
    
    async def _record_quality_check(self, result: Dict[str, Any]):
        """品質チェック結果を記録"""
        result["timestamp"] = datetime.now().isoformat()
        
        history = []
        if self.quality_history_file.exists():
            try:
                with open(self.quality_history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        history.append(result)
        
        # 最新100件のみ保持
        history = history[-100:]
        
        with open(self.quality_history_file, 'w') as f:
            json.dump(history, f, indent=2)