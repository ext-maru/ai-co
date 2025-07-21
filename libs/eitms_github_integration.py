#!/usr/bin/env python3
"""
EITMS GitHub統合システム
GitHub Issues・PRと統一タスクシステムの双方向同期

Author: クロードエルダー（Claude Elder）
Created: 2025/07/22
Version: 1.0.0 - Full Integration
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import aiohttp
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GitHubIssue:
    """GitHub Issue データ構造"""
    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: str = "open"
    labels: List[str] = field(default_factory=list)
    assignees: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    html_url: str = ""

    @classmethod
    def from_dict(cls, data: Dict) -> 'GitHubIssue':
        """辞書からGitHubIssueオブジェクト作成"""
        return cls(
            id=data.get('id', 0),
            number=data.get('number', 0),
            title=data.get('title', ''),
            body=data.get('body'),
            state=data.get('state', 'open'),
            labels=[label.get('name', '') for label in data.get('labels', [])],
            assignees=[assignee.get('login', '') for assignee in data.get('assignees', [])],
            created_at=datetime.fromisoformat(data.get('created_at', '').replace('Z', '+00:00')) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data.get('updated_at', '').replace('Z', '+00:00')) if data.get('updated_at') else None,
            html_url=data.get('html_url', '')
        )

class GitHubClient:
    """GitHub API クライアント"""
    
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "EITMS-Integration/1.0"
        }
    
    async def get_issues(self, state: str = "all") -> List[GitHubIssue]:
        """Issues一覧取得"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"
        params = {
            "state": state,
            "per_page": 100
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        issues = [GitHubIssue.from_dict(issue) for issue in data if not issue.get('pull_request')]
                        logger.info(f"📥 GitHub Issues取得: {len(issues)}件")
                        return issues
                    else:
                        logger.error(f"❌ GitHub API エラー: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ GitHub Issues取得失敗: {e}")
            return []
    
    async def get_issue(self, issue_number: int) -> Optional[GitHubIssue]:
        """特定Issue取得"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues/{issue_number}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return GitHubIssue.from_dict(data)
                    else:
                        logger.error(f"❌ Issue #{issue_number} 取得失敗: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"❌ Issue取得エラー: {e}")
            return None
    
    async def create_issue(self, title: str, body: Optional[str] = None, 
                          labels: List[str] = None, assignees: List[str] = None) -> Optional[GitHubIssue]:
        """Issue作成"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"
        data = {
            "title": title,
            "body": body or "",
            "labels": labels or [],
            "assignees": assignees or []
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=data) as response:
                    if response.status == 201:
                        result = await response.json()
                        issue = GitHubIssue.from_dict(result)
                        logger.info(f"✅ GitHub Issue作成: #{issue.number} - {title}")
                        return issue
                    else:
                        logger.error(f"❌ Issue作成失敗: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"❌ Issue作成エラー: {e}")
            return None
    
    async def update_issue(self, issue_number: int, title: Optional[str] = None,
                          body: Optional[str] = None, state: Optional[str] = None,
                          labels: Optional[List[str]] = None) -> Optional[GitHubIssue]:
        """Issue更新"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues/{issue_number}"
        data = {}
        
        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if state is not None:
            data["state"] = state
        if labels is not None:
            data["labels"] = labels
        
        if not data:
            logger.warning("⚠️ 更新データが空です")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=self.headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        issue = GitHubIssue.from_dict(result)
                        logger.info(f"✅ GitHub Issue更新: #{issue.number}")
                        return issue
                    else:
                        logger.error(f"❌ Issue更新失敗: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"❌ Issue更新エラー: {e}")
            return None

class EitmsGitHubIntegration:
    """EITMS GitHub統合システム"""
    
    def __init__(self, unified_manager):
        self.unified_manager = unified_manager
        
        # 環境変数から設定読み込み
        self.token = os.getenv('GITHUB_TOKEN', '')
        self.owner = os.getenv('GITHUB_REPO_OWNER', '')
        self.repo = os.getenv('GITHUB_REPO_NAME', '')
        
        if not all([self.token, self.owner, self.repo]):
            logger.warning("⚠️ GitHub設定が不完全です")
            self.enabled = False
        else:
            self.client = GitHubClient(self.token, self.owner, self.repo)
            self.enabled = True
            logger.info(f"🔗 GitHub統合初期化: {self.owner}/{self.repo}")
        
        # 同期マッピング
        self.priority_mapping = {
            'low': ['enhancement', 'documentation'],
            'medium': ['feature', 'improvement'],
            'high': ['bug', 'urgent'],
            'critical': ['critical', 'security']
        }
        
        self.status_mapping = {
            'created': 'open',
            'in_progress': 'open',
            'blocked': 'open',
            'completed': 'closed'
        }
    
    async def sync_from_github(self) -> Dict[str, int]:
        """GitHubからEITMSへの同期"""
        if not self.enabled:
            logger.warning("⚠️ GitHub統合が無効です")
            return {'synced': 0, 'created': 0, 'updated': 0}
        
        logger.info("🔄 GitHub → EITMS 同期開始")
        
        issues = await self.client.get_issues()
        stats = {'synced': 0, 'created': 0, 'updated': 0}
        
        for github_issue in issues:
            try:
                # 既存タスク確認
                existing_task = await self._find_task_by_github_issue(github_issue.number)
                
                if existing_task:
                    # 既存タスク更新
                    if await self._update_task_from_issue(existing_task.id, github_issue):
                        stats['updated'] += 1
                else:
                    # 新規タスク作成
                    if await self._create_task_from_issue(github_issue):
                        stats['created'] += 1
                
                stats['synced'] += 1
                
            except Exception as e:
                logger.error(f"❌ Issue #{github_issue.number} 同期失敗: {e}")
        
        logger.info(f"✅ GitHub同期完了: {stats}")
        return stats
    
    async def sync_to_github(self, task_id: str) -> bool:
        """EITMSからGitHubへの同期"""
        if not self.enabled:
            logger.warning("⚠️ GitHub統合が無効です")
            return False
        
        try:
            task = await self.unified_manager.db.get_task(task_id)
            if not task:
                logger.error(f"❌ タスクが見つかりません: {task_id}")
                return False
            
            # GitHub Issue番号確認
            github_issue_number = getattr(task, 'github_issue_number', None)
            
            if github_issue_number:
                # 既存Issue更新
                return await self._update_issue_from_task(github_issue_number, task)
            else:
                # 新規Issue作成
                return await self._create_issue_from_task(task)
                
        except Exception as e:
            logger.error(f"❌ タスク → GitHub 同期失敗: {e}")
            return False
    
    async def _find_task_by_github_issue(self, issue_number: int):
        """GitHub Issue番号でタスク検索"""
        try:
            # SQLクエリで検索（実際の実装は統一データモデルに依存）
            tasks = await self.unified_manager.db.list_tasks()
            for task in tasks:
                if getattr(task, 'github_issue_number', None) == issue_number:
                    return task
            return None
        except Exception as e:
            logger.error(f"❌ タスク検索失敗: {e}")
            return None
    
    async def _create_task_from_issue(self, github_issue: GitHubIssue) -> bool:
        """GitHub IssueからEITMSタスク作成"""
        try:
            # 優先度マッピング
            priority = self._map_labels_to_priority(github_issue.labels)
            
            # ステータスマッピング
            status = 'completed' if github_issue.state == 'closed' else 'created'
            
            # タスク作成
            task_id = await self.unified_manager.create_task(
                title=github_issue.title,
                task_type='issue',
                priority=priority,
                status=status,
                description=github_issue.body or '',
                github_issue_number=github_issue.number,
                assigned_to=github_issue.assignees[0] if github_issue.assignees else None
            )
            
            if task_id:
                logger.info(f"✅ GitHub Issue → EITMS: #{github_issue.number} → {task_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Issue → タスク変換失敗: {e}")
            return False
    
    async def _update_task_from_issue(self, task_id: str, github_issue: GitHubIssue) -> bool:
        """GitHub IssueからEITMSタスク更新"""
        try:
            # ステータス更新
            status = 'completed' if github_issue.state == 'closed' else 'in_progress'
            await self.unified_manager.update_task_status(task_id, status)
            
            logger.info(f"✅ タスク更新: {task_id} ← GitHub #{github_issue.number}")
            return True
            
        except Exception as e:
            logger.error(f"❌ タスク更新失敗: {e}")
            return False
    
    async def _create_issue_from_task(self, task) -> bool:
        """EITMSタスクからGitHub Issue作成"""
        try:
            # ラベル生成
            labels = self._map_priority_to_labels(task.priority)
            if task.task_type == 'issue':
                labels.append('eitms-issue')
            
            # Issue作成
            github_issue = await self.client.create_issue(
                title=task.title,
                body=getattr(task, 'description', '') or f"EITMS Task ID: {task.id}",
                labels=labels,
                assignees=[getattr(task, 'assigned_to', None)] if getattr(task, 'assigned_to', None) else []
            )
            
            if github_issue:
                # タスクにGitHub Issue番号を記録
                # 実際の実装は統一データモデルの拡張が必要
                logger.info(f"✅ EITMS → GitHub Issue: {task.id} → #{github_issue.number}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ タスク → Issue変換失敗: {e}")
            return False
    
    async def _update_issue_from_task(self, issue_number: int, task) -> bool:
        """EITMSタスクからGitHub Issue更新"""
        try:
            # ステータスマッピング
            state = self.status_mapping.get(task.status, 'open')
            
            # Issue更新
            github_issue = await self.client.update_issue(
                issue_number=issue_number,
                title=task.title,
                body=getattr(task, 'description', '') or f"EITMS Task ID: {task.id}",
                state=state
            )
            
            if github_issue:
                logger.info(f"✅ GitHub Issue更新: #{issue_number} ← {task.id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Issue更新失敗: {e}")
            return False
    
    def _map_labels_to_priority(self, labels: List[str]) -> str:
        """ラベルから優先度マッピング"""
        for priority, priority_labels in self.priority_mapping.items():
            if any(label in labels for label in priority_labels):
                return priority
        return 'medium'  # デフォルト
    
    def _map_priority_to_labels(self, priority: str) -> List[str]:
        """優先度からラベルマッピング"""
        priority_labels = {
            'low': ['enhancement'],
            'medium': ['feature'],
            'high': ['bug'],
            'critical': ['critical']
        }
        return priority_labels.get(priority, ['feature'])
    
    async def setup_webhook(self, webhook_url: str, secret: str) -> bool:
        """GitHub Webhook設定"""
        if not self.enabled:
            return False
        
        url = f"{self.client.base_url}/repos/{self.owner}/{self.repo}/hooks"
        data = {
            "name": "web",
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "secret": secret
            },
            "events": ["issues", "issue_comment"],
            "active": True
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.client.headers, json=data) as response:
                    if response.status == 201:
                        logger.info("✅ GitHub Webhook設定完了")
                        return True
                    else:
                        logger.error(f"❌ Webhook設定失敗: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Webhook設定エラー: {e}")
            return False

# テスト実行用
async def main():
    """テスト実行"""
    # モック統一管理システム
    class MockUnifiedManager:
        def __init__(self):
            self.tasks = {}
        
        async def create_task(self, **kwargs):
            task_id = f"github-sync-{len(self.tasks)}"
            self.tasks[task_id] = kwargs
            return task_id
        
        async def update_task_status(self, task_id, status):
            if task_id in self.tasks:
                self.tasks[task_id]['status'] = status
                return True
            return False
        
        @property
        def db(self):
            return type('MockDB', (), {
                'get_task': lambda self, task_id: type('Task', (), {
                    'id': task_id,
                    'title': 'テストタスク',
                    'task_type': 'issue',
                    'priority': 'medium',
                    'status': 'created'
                })() if task_id in self.tasks else None,
                'list_tasks': lambda self: []
            })()
    
    # テスト実行
    manager = MockUnifiedManager()
    github_integration = EitmsGitHubIntegration(manager)
    
    if github_integration.enabled:
        logger.info("🔄 GitHub統合テスト開始")
        
        # GitHub → EITMS同期テスト
        stats = await github_integration.sync_from_github()
        logger.info(f"📊 同期統計: {stats}")
    else:
        logger.warning("⚠️ GitHub統合が無効（設定を確認してください）")

if __name__ == "__main__":
    asyncio.run(main())