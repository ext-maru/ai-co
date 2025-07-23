#!/usr/bin/env python3
"""
再オープンされたIssueを追跡・管理するシステム
Auto Issue Processorの拡張機能
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from github import Github
from github.Issue import Issue

logger = logging.getLogger(__name__)


class ReopenedIssueTracker:
    """再オープンされたIssueを追跡・管理するクラス"""
    
    def __init__(self, repo):
        self.repo = repo
        self.reopened_history_file = Path("logs/reopened_issues_history.json")
        self.reopened_history_file.parent.mkdir(exist_ok=True)
        
    async def get_issue_timeline(self, issue_number: int) -> List[Dict[str, Any]]:
        """Issueのタイムラインイベントを取得"""
        try:
            issue = self.repo.get_issue(issue_number)
            timeline = issue.get_timeline()
            
            events = []
            for event in timeline:
                if hasattr(event, 'event'):
                    events.append({
                        'event': event.event,
                        'created_at': event.created_at.isoformat(
                            ) if hasattr(event,
                            'created_at'
                        ) else None,
                        'actor': event.actor.login if hasattr(
                            event,
                            'actor'
                        ) and event.actor else None,
                        'commit_id': event.commit_id if hasattr(event, 'commit_id') else None,
                    })
            
            return events
        except Exception as e:
            logger.error(f"Error getting timeline for issue #{issue_number}: {e}")
            return []
    
    async def check_if_reopened(self, issue_number: int) -> Dict[str, Any]:
        """Issueが再オープンされたかチェック"""
        timeline = await self.get_issue_timeline(issue_number)
        
        # reopenedイベントを探す
        reopened_events = [e for e in timeline if e['event'] == 'reopened']
        closed_events = [e for e in timeline if e['event'] == 'closed']
        
        if reopened_events:
            last_reopened = reopened_events[-1]
            last_closed = closed_events[-1] if closed_events else None
            
            # 最後のクローズより後に再オープンされているか確認
            if not last_closed or last_reopened['created_at'] > last_closed['created_at']:
                return {
                    'is_reopened': True,
                    'reopened_at': last_reopened['created_at'],
                    'reopened_by': last_reopened['actor'],
                    'reopen_count': len(reopened_events)
                }
        
        return {'is_reopened': False}
    
    async def get_processing_history(self, issue_number: int) -> Dict[str, Any]:
        """Issueの処理履歴を取得"""
        history = {
            'issue_number': issue_number,
            'prs': [],
            'processing_attempts': []
        }
        
        # 関連するPRを検索
        try:
            pulls = self.repo.get_pulls(state='all')
            for pr in pulls:
                if pr.body and f"#{issue_number}" in pr.body:
                    history['prs'].append({
                        'pr_number': pr.number,
                        'state': pr.state,
                        'merged': pr.merged,
                        'created_at': pr.created_at.isoformat(),
                        'merged_at': pr.merged_at.isoformat() if pr.merged_at else None,
                        'title': pr.title
                    })
                
                # タイトルにもissue番号が含まれる場合
                if f"#{issue_number}" in pr.title:
                    history['prs'].append({
                        'pr_number': pr.number,
                        'state': pr.state,
                        'merged': pr.merged,
                        'created_at': pr.created_at.isoformat(),
                        'merged_at': pr.merged_at.isoformat() if pr.merged_at else None,
                        'title': pr.title
                    })
        except Exception as e:
            logger.error(f"Error getting PRs for issue #{issue_number}: {e}")
        
        # 処理履歴ファイルから情報取得
        if self.reopened_history_file.exists():
            try:
                with open(self.reopened_history_file, 'r') as f:
                    all_history = json.load(f)
                    issue_history = [h for h in all_history if h.get('issue_number') == issue_number]
                    history['processing_attempts'] = issue_history
            except Exception as e:
                logger.error(f"Error reading reopened history: {e}")
        
        return history
    
    async def should_reprocess(self, issue_number: int) -> Dict[str, Any]:
        """再処理が必要かどうかを判定"""
        reopened_info = await self.check_if_reopened(issue_number)
        processing_history = await self.get_processing_history(issue_number)
        
        decision = {
            'should_process': False,
            'reason': None,
            'recommendation': None
        }
        
        if not reopened_info['is_reopened']:
            decision['reason'] = 'Issue is not reopened'
            return decision
        
        # 最後の処理後に再オープンされているか確認
        last_pr = None
        if processing_history['prs']:
            # 重複を除去してから最新を取得
            unique_prs = {pr['pr_number']: pr for pr in processing_history['prs']}.values()
            last_pr = max(unique_prs, key=lambda x: x['created_at'])
        
        if last_pr and reopened_info['reopened_at'] > last_pr['created_at']:
            decision['should_process'] = True
            decision['reason'] = f"Issue was reopened after PR #{last_pr['pr_number']}"
            
            # 再オープン回数に基づく推奨事項
            if reopened_info['reopen_count'] >= 3:
                decision['recommendation'] = 'escalate_to_human'
                decision['reason'] += ' - Multiple reopens detected, human review recommended'
            else:
                decision['recommendation'] = 'auto_process_with_caution'
                
        return decision
    
    async def record_reprocessing(self, issue_number: int, result: Dict[str, Any]):
        """再処理の記録を保存"""
        record = {
            'issue_number': issue_number,
            'timestamp': datetime.now().isoformat(),
            'type': 'reprocessing',
            'result': result
        }
        
        history = []
        if self.reopened_history_file.exists():
            try:
                with open(self.reopened_history_file, 'r') as f:
                    history = json.load(f)
            except Exception as e:
                logger.error(f"Error reading reopened history for writing: {e}")
                history = []
        
        history.append(record)
        
        # 古い記録を削除（30日以上前）
        cutoff = datetime.now() - timedelta(days=30)
        history = [h for h in history if datetime.fromisoformat(h['timestamp']) > cutoff]
        
        with open(self.reopened_history_file, 'w') as f:
            json.dump(history, f, indent=2)
            
        logger.info(f"Recorded reprocessing for issue #{issue_number}")