#!/usr/bin/env python3
"""
統一Auto Issue Processorコア
5つの既存実装を統合し、一貫性のある処理フローを提供
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path

from github import Github
from github.Issue import Issue
from github.GithubException import GithubException

from ..core.config import ProcessorConfig, get_default_config
from ..utils.locking import ProcessLock
from ..features.error_recovery import ErrorRecoveryHandler
from ..features.pr_creation import PullRequestManager
from ..features.parallel_processing import ParallelProcessor
from ..features.four_sages import FourSagesIntegration

logger = logging.getLogger(__name__)


class AutoIssueProcessor:
    """統一Auto Issue Processor
    
    既存の5つの実装を統合:
    1. auto_issue_processor.py (基本実装)
    2. advanced_issue_processor.py (高度機能)
    3. enhanced_auto_issue_processor.py (拡張版)
    4. auto_issue_processor_a2a.py (A2A版)
    5. advanced_issue_orchestrator.py (オーケストレーター)
    """
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """初期化
        
        Args:
            config: プロセッサー設定（指定しない場合はデフォルト設定）
        """
        self.config = config or get_default_config()
        
        # 設定検証
        if not self.config.validate():
            raise ValueError("Invalid configuration")
        
        # GitHubクライアント初期化
        self._github = None
        self._repo = None
        
        # ロックマネージャー初期化
        self.lock_manager = ProcessLock(
            backend=self.config.lock.backend,
            lock_dir=self.config.lock.lock_dir
        )
        
        # 機能モジュール初期化
        self.error_recovery = None
        self.pr_manager = None
        self.parallel_processor = None
        self.four_sages = None
        
        self._init_features()
        
        # 処理統計
        self.stats = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "locked": 0,
            "start_time": None,
            "end_time": None
        }
    
    def _init_features(self):
        """機能モジュールを初期化"""
        if self.config.features.error_recovery:
            from ..features.error_recovery import ErrorRecoveryHandler
            self.error_recovery = ErrorRecoveryHandler(self.config)
        
        if self.config.features.pr_creation:
            from ..features.pr_creation import PullRequestManager
            self.pr_manager = PullRequestManager(self.config)
        
        if self.config.features.parallel_processing:
            from ..features.parallel_processing import ParallelProcessor
            self.parallel_processor = ParallelProcessor(self.config)
        
        if self.config.features.four_sages_integration:
            from ..features.four_sages import FourSagesIntegration
            self.four_sages = FourSagesIntegration(self.config)
    
    @property
    def github(self) -> Github:
        """GitHubクライアントを取得（遅延初期化）"""
        if not self._github:
            if not self.config.github.token:
                raise ValueError("GitHub token not configured")
            self._github = Github(self.config.github.token)
        return self._github
    
    @property
    def repo(self):
        """リポジトリオブジェクトを取得（遅延初期化）"""
        if not self._repo:
            repo_full = f"{self.config.github.owner}/{self.config.github.repo}"
            self._repo = self.github.get_repo(repo_full)
        return self._repo
    
    async def process_issues(self, issue_numbers: Optional[List[int]] = None) -> Dict[str, Any]:
        """Issueを処理
        
        Args:
            issue_numbers: 処理するIssue番号のリスト（指定しない場合は自動選択）
            
        Returns:
            処理結果の辞書
        """
        self.stats["start_time"] = datetime.now()
        logger.info("🚀 Starting Auto Issue Processor (Unified Version)")
        
        try:
            # 処理対象のIssueを取得
            issues = await self._get_issues_to_process(issue_numbers)
            
            if not issues:
                logger.info("No issues to process")
                return self._create_result()
            
            logger.info(f"Found {len(issues)} issues to process")
            
            # 並列処理の判定
            if self.config.features.parallel_processing and len(issues) > 1:
                results = await self._process_parallel(issues)
            else:
                results = await self._process_sequential(issues)
            
            # 結果を集計
            for result in results:
                if result["success"]:
                    self.stats["success"] += 1
                elif result.get("locked"):
                    self.stats["locked"] += 1
                elif result.get("skipped"):
                    self.stats["skipped"] += 1
                else:
                    self.stats["failed"] += 1
            
            self.stats["processed"] = len(results)
            
        except Exception as e:
            logger.error(f"Fatal error in process_issues: {e}", exc_info=True)
            if self.error_recovery:
                await self.error_recovery.handle_fatal_error(e)
        
        finally:
            self.stats["end_time"] = datetime.now()
            await self._cleanup()
        
        return self._create_result()
    
    async def _get_issues_to_process(self, issue_numbers: Optional[List[int]] = None) -> List[Issue]:
        """処理対象のIssueを取得"""
        issues = []
        
        if issue_numbers:
            # 指定されたIssue番号を処理
            for num in issue_numbers:
                try:
                    issue = self.repo.get_issue(num)
                    if await self._should_process_issue(issue):
                        issues.append(issue)
                except Exception as e:
                    logger.error(f"Failed to get issue #{num}: {e}")
        else:
            # 自動選択（優先度順）
            for priority in self.config.processing.priorities:
                label_issues = self.repo.get_issues(
                    state="open",
                    labels=[priority]
                )
                
                for issue in label_issues:
                    if await self._should_process_issue(issue):
                        issues.append(issue)
                        if len(issues) >= self.config.processing.max_issues_per_run:
                            break
                
                if len(issues) >= self.config.processing.max_issues_per_run:
                    break
        
        return issues[:self.config.processing.max_issues_per_run]
    
    async def _should_process_issue(self, issue: Issue) -> bool:
        """Issueを処理すべきか判定"""
        # プルリクエストは除外
        if issue.pull_request:
            return False
        
        # スキップラベルチェック
        issue_labels = [label.name for label in issue.labels]
        for skip_label in self.config.processing.skip_labels:
            if skip_label in issue_labels:
                logger.debug(f"Issue #{issue.number} has skip label: {skip_label}")
                return False
        
        # 必須ラベルチェック
        if self.config.processing.required_labels:
            has_required = any(
                label in issue_labels 
                for label in self.config.processing.required_labels
            )
            if not has_required:
                logger.debug(f"Issue #{issue.number} missing required labels")
                return False
        
        # ロックチェック
        lock_key = f"issue_{issue.number}"
        if await self.lock_manager.is_locked(lock_key):
            lock_info = await self.lock_manager.get_lock_info(lock_key)
            logger.info(f"Issue #{issue.number} is locked (PID: {lock_info.pid}, TTL: {lock_info.remaining_ttl:.0f}s)")
            return False
        
        return True
    
    async def _process_sequential(self, issues: List[Issue]) -> List[Dict[str, Any]]:
        """Issueを順次処理"""
        results = []
        
        for issue in issues:
            result = await self._process_single_issue(issue)
            results.append(result)
            
            # エラー時の処理継続判定
            if not result["success"] and not self.config.features.error_recovery:
                logger.warning("Stopping due to error (error recovery disabled)")
                break
        
        return results
    
    async def _process_parallel(self, issues: List[Issue]) -> List[Dict[str, Any]]:
        """Issueを並列処理"""
        if not self.parallel_processor:
            logger.warning("Parallel processing not available, falling back to sequential")
            return await self._process_sequential(issues)
        
        return await self.parallel_processor.process_batch(issues, self._process_single_issue)
    
    async def _process_single_issue(self, issue: Issue) -> Dict[str, Any]:
        """単一のIssueを処理"""
        logger.info(f"📋 Processing Issue #{issue.number}: {issue.title}")
        
        result = {
            "issue_number": issue.number,
            "title": issue.title,
            "success": False,
            "error": None,
            "locked": False,
            "skipped": False,
            "artifacts": {},
            "pr_created": False,
            "pr_number": None
        }
        
        # ロック取得
        lock_key = f"issue_{issue.number}"
        lock_acquired = await self.lock_manager.acquire(
            lock_key,
            ttl=self.config.processing.processing_timeout,
            metadata={
                "processor": "unified",
                "started_at": datetime.now().isoformat()
            }
        )
        
        if not lock_acquired:
            result["locked"] = True
            logger.warning(f"Could not acquire lock for Issue #{issue.number}")
            return result
        
        try:
            # 4賢者統合による前処理
            if self.four_sages:
                sage_analysis = await self.four_sages.analyze_issue(issue)
                if sage_analysis.get("skip"):
                    result["skipped"] = True
                    result["skip_reason"] = sage_analysis.get("reason")
                    logger.info(f"4 Sages recommended skipping: {result['skip_reason']}")
                    return result
                result["sage_analysis"] = sage_analysis
            
            # メイン処理
            if self.config.dry_run:
                logger.info("DRY RUN: Simulating issue processing")
                result["success"] = True
                result["dry_run"] = True
            else:
                # 実際の処理実装
                process_result = await self._execute_issue_processing(issue)
                result.update(process_result)
            
            # PR作成
            if result["success"] and self.config.features.pr_creation and self.pr_manager:
                pr_result = await self.pr_manager.create_pr_for_issue(issue, result["artifacts"])
                if pr_result["success"]:
                    result["pr_created"] = True
                    result["pr_number"] = pr_result["pr_number"]
            
            # 成功時の後処理
            if result["success"]:
                await self._post_process_success(issue, result)
            
        except Exception as e:
            logger.error(f"Error processing Issue #{issue.number}: {e}", exc_info=True)
            result["error"] = str(e)
            
            # エラーリカバリー
            if self.error_recovery:
                recovery_result = await self.error_recovery.handle_processing_error(issue, e)
                if recovery_result["recovered"]:
                    result["success"] = True
                    result["recovery_applied"] = recovery_result
        
        finally:
            # ロック解放
            await self.lock_manager.release(lock_key)
        
        return result
    
    async def _execute_issue_processing(self, issue: Issue) -> Dict[str, Any]:
        """Issueの実際の処理を実行
        
        TODO: ここに実際のコード生成、テスト作成などの処理を実装
        現在は基本的な枠組みのみ
        """
        result = {
            "success": False,
            "artifacts": {}
        }
        
        try:
            # Issue内容の解析
            analysis = await self._analyze_issue_content(issue)
            
            # 実装計画の生成
            implementation_plan = await self._create_implementation_plan(issue, analysis)
            
            # コード生成
            generated_code = await self._generate_code(issue, implementation_plan)
            result["artifacts"]["code"] = generated_code
            
            # テスト生成
            generated_tests = await self._generate_tests(issue, generated_code)
            result["artifacts"]["tests"] = generated_tests
            
            # 検証
            validation_result = await self._validate_artifacts(result["artifacts"])
            if validation_result["valid"]:
                result["success"] = True
            else:
                result["validation_errors"] = validation_result["errors"]
            
        except Exception as e:
            logger.error(f"Error in execute_issue_processing: {e}")
            result["error"] = str(e)
        
        return result
    
    async def _analyze_issue_content(self, issue: Issue) -> Dict[str, Any]:
        """Issue内容を解析"""
        # TODO: 実装
        return {
            "type": "feature",
            "complexity": "medium",
            "requirements": []
        }
    
    async def _create_implementation_plan(self, issue: Issue, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """実装計画を作成"""
        # TODO: 実装
        return {
            "steps": [],
            "estimated_time": 30
        }
    
    async def _generate_code(self, issue: Issue, plan: Dict[str, Any]) -> Dict[str, str]:
        """コードを生成"""
        # TODO: 実装
        return {
            "main.py": "# Generated code for Issue #" + str(issue.number)
        }
    
    async def _generate_tests(self, issue: Issue, code: Dict[str, str]) -> Dict[str, str]:
        """テストを生成"""
        # TODO: 実装
        return {
            "test_main.py": "# Generated tests for Issue #" + str(issue.number)
        }
    
    async def _validate_artifacts(self, artifacts: Dict[str, Any]) -> Dict[str, Any]:
        """生成物を検証"""
        # TODO: 実装
        return {
            "valid": True,
            "errors": []
        }
    
    async def _post_process_success(self, issue: Issue, result: Dict[str, Any]):
        """成功時の後処理"""
        try:
            # 処理完了コメント
            comment = f"""
🎉 Auto Issue Processor successfully completed!

**Summary:**
- Processing time: {datetime.now() - self.stats['start_time']}
- Generated artifacts: {len(result.get('artifacts', {}))}
"""
            
            if result.get("pr_created"):
                comment += f"- Pull Request: #{result['pr_number']}\n"
            
            if self.config.features.four_sages_integration and "sage_analysis" in result:
                comment += f"\n**4 Sages Analysis:**\n{result['sage_analysis'].get('summary', 'N/A')}\n"
            
            if not self.config.dry_run:
                issue.create_comment(comment)
            
        except Exception as e:
            logger.error(f"Error in post-processing: {e}")
    
    async def _cleanup(self):
        """クリーンアップ処理"""
        try:
            # 期限切れロックのクリーンアップ
            cleaned = await self.lock_manager.cleanup_expired()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired locks")
            
            # 統計情報の保存
            await self._save_stats()
            
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
    
    async def _save_stats(self):
        """統計情報を保存"""
        stats_file = Path("logs/auto_issue_processor_stats.json")
        stats_file.parent.mkdir(exist_ok=True)
        
        try:
            # 既存の統計を読み込み
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    all_stats = json.load(f)
            else:
                all_stats = []
            
            # 現在の実行統計を追加
            current_stats = self.stats.copy()
            current_stats["start_time"] = current_stats["start_time"].isoformat() if current_stats["start_time"] else None
            current_stats["end_time"] = current_stats["end_time"].isoformat() if current_stats["end_time"] else None
            
            all_stats.append(current_stats)
            
            # 直近100件のみ保持
            all_stats = all_stats[-100:]
            
            # 保存
            with open(stats_file, 'w') as f:
                json.dump(all_stats, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
    
    def _create_result(self) -> Dict[str, Any]:
        """最終結果を作成"""
        duration = None
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        return {
            "success": self.stats["failed"] == 0,
            "stats": self.stats,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }


async def main():
    """CLIエントリーポイント"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified Auto Issue Processor")
    parser.add_argument("issues", nargs="*", type=int, help="Issue numbers to process")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--parallel", action="store_true", help="Enable parallel processing")
    
    args = parser.parse_args()
    
    # 設定をロード
    config = ProcessorConfig.load(args.config)
    
    # CLIオプションで上書き
    if args.dry_run:
        config.dry_run = True
    if args.parallel:
        config.features.parallel_processing = True
    
    # プロセッサー実行
    processor = AutoIssueProcessor(config)
    result = await processor.process_issues(args.issues or None)
    
    # 結果表示
    print(f"\n{'='*60}")
    print(f"Auto Issue Processor Results:")
    print(f"{'='*60}")
    print(f"Processed: {result['stats']['processed']}")
    print(f"Success: {result['stats']['success']}")
    print(f"Failed: {result['stats']['failed']}")
    print(f"Skipped: {result['stats']['skipped']}")
    print(f"Locked: {result['stats']['locked']}")
    if result.get("duration_seconds"):
        print(f"Duration: {result['duration_seconds']:.1f} seconds")
    print(f"{'='*60}\n")
    
    # 失敗があれば非ゼロで終了
    exit_code = 0 if result["success"] else 1
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)