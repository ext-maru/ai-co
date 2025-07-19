#!/usr/bin/env python3
"""
🚀 GitHub Projects API クライアント
GitHub Projects API Client

GitHub Projects v2 APIを使用してプロジェクトボードを管理するクライアント
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging
import aiohttp
from enum import Enum

logger = logging.getLogger(__name__)

class ProjectItemStatus(Enum):
    """プロジェクトアイテムのステータス"""
    TODO = "Todo"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    BLOCKED = "Blocked"
    REVIEW = "Review"

class ProjectItemPriority(Enum):
    """プロジェクトアイテムの優先度"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"

@dataclass
class ProjectItem:
    """プロジェクトアイテム"""
    id: Optional[str] = None
    title: str = ""
    body: str = ""
    status: ProjectItemStatus = ProjectItemStatus.TODO
    priority: ProjectItemPriority = ProjectItemPriority.MEDIUM
    assignees: List[str] = None
    labels: List[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.assignees is None:
            self.assignees = []
        if self.labels is None:
            self.labels = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class ProjectBoard:
    """プロジェクトボード"""
    id: Optional[str] = None
    number: Optional[int] = None
    title: str = ""
    description: str = ""
    owner: str = ""
    url: Optional[str] = None
    items: List[ProjectItem] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class GitHubProjectsClient:
    """GitHub Projects API クライアント"""
    
    def __init__(self, token: Optional[str] = None, owner: str = "aicompany", repo: str = "ai_co"):
        self.base_url = "https://api.github.com"
        self.graphql_url = "https://api.github.com/graphql"
        self.owner = owner
        self.repo = repo
        
        # GitHub Token
        self.token = token or self._get_token_from_env()
        if not self.token:
            logger.warning("GitHub tokenが設定されていません。dry_runモードで動作します")
            self.dry_run = True
        else:
            self.dry_run = False
        
        # HTTPセッション
        self.session = None
        
        # データストレージ
        self.base_path = Path("/home/aicompany/ai_co")
        self.data_path = self.base_path / "data" / "github_projects"
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # キャッシュ
        self.projects_cache = {}
        self.items_cache = {}
        
    def _get_token_from_env(self) -> Optional[str]:
        """環境変数からトークンを取得"""
        import os
        return os.getenv("GITHUB_TOKEN")
    
    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        if not self.dry_run:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                }
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        if self.session:
            await self.session.close()
    
    async def _make_graphql_request(self, query: str, variables: Dict = None) -> Dict:
        """GraphQL リクエストを実行"""
        if self.dry_run:
            logger.info(f"DRY RUN: GraphQL query: {query[:100]}...")
            return {"data": {}}
        
        if not self.session:
            raise RuntimeError("セッションが初期化されていません")
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            async with self.session.post(self.graphql_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if "errors" in result:
                        logger.error(f"GraphQL errors: {result['errors']}")
                        raise Exception(f"GraphQL errors: {result['errors']}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"GraphQL request failed: {response.status} - {error_text}")
                    raise Exception(f"GraphQL request failed: {response.status}")
        except Exception as e:
            logger.error(f"GraphQL request error: {e}")
            raise
    
    async def get_organization_projects(self, org: Optional[str] = None) -> List[ProjectBoard]:
        """組織のプロジェクトを取得"""
        org = org or self.owner
        
        query = """
        query($org: String!, $first: Int!) {
            organization(login: $org) {
                projectsV2(first: $first) {
                    nodes {
                        id
                        number
                        title
                        shortDescription
                        url
                        createdAt
                        updatedAt
                    }
                }
            }
        }
        """
        
        variables = {
            "org": org,
            "first": 50
        }
        
        try:
            result = await self._make_graphql_request(query, variables)
            
            if self.dry_run:
                # Dry run用のダミーデータ
                return [
                    ProjectBoard(
                        id="PVT_001",
                        number=1,
                        title="エルダーズギルド開発プロジェクト",
                        description="エルダーズギルドの開発管理",
                        owner=org,
                        url="https://github.com/orgs/aicompany/projects/1"
                    )
                ]
            
            projects = []
            for node in result["data"]["organization"]["projectsV2"]["nodes"]:
                project = ProjectBoard(
                    id=node["id"],
                    number=node["number"],
                    title=node["title"],
                    description=node.get("shortDescription", ""),
                    owner=org,
                    url=node["url"],
                    created_at=node["createdAt"],
                    updated_at=node["updatedAt"]
                )
                projects.append(project)
            
            return projects
            
        except Exception as e:
            logger.error(f"プロジェクト取得エラー: {e}")
            return []
    
    async def get_project_items(self, project_id: str) -> List[ProjectItem]:
        """プロジェクトのアイテムを取得"""
        if self.dry_run:
            logger.info(f"DRY RUN: プロジェクト {project_id} のアイテム取得")
            return []
        
        query = """
        query($projectId: ID!, $first: Int!) {
            node(id: $projectId) {
                ... on ProjectV2 {
                    items(first: $first) {
                        nodes {
                            id
                            content {
                                ... on Issue {
                                    title
                                    body
                                    state
                                    createdAt
                                    updatedAt
                                }
                                ... on DraftIssue {
                                    title
                                    body
                                    createdAt
                                    updatedAt
                                }
                            }
                            fieldValues(first: 10) {
                                nodes {
                                    ... on ProjectV2ItemFieldSingleSelectValue {
                                        name
                                        field {
                                            ... on ProjectV2SingleSelectField {
                                                name
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "projectId": project_id,
            "first": 100
        }
        
        try:
            result = await self._make_graphql_request(query, variables)
            
            items = []
            for node in result["data"]["node"]["items"]["nodes"]:
                content = node.get("content", {})
                
                # ステータスと優先度を抽出
                status = ProjectItemStatus.TODO
                priority = ProjectItemPriority.MEDIUM
                
                for field_value in node.get("fieldValues", {}).get("nodes", []):
                    field_name = field_value.get("field", {}).get("name", "")
                    value_name = field_value.get("name", "")
                    
                    if field_name == "Status":
                        try:
                            status = ProjectItemStatus(value_name)
                        except ValueError:
                            pass
                    elif field_name == "Priority":
                        try:
                            priority = ProjectItemPriority(value_name)
                        except ValueError:
                            pass
                
                item = ProjectItem(
                    id=node["id"],
                    title=content.get("title", ""),
                    body=content.get("body", ""),
                    status=status,
                    priority=priority,
                    created_at=content.get("createdAt"),
                    updated_at=content.get("updatedAt")
                )
                items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"プロジェクトアイテム取得エラー: {e}")
            return []
    
    async def create_project_item(self, project_id: str, title: str, body: str = "", 
                                  status: ProjectItemStatus = ProjectItemStatus.TODO,
                                  priority: ProjectItemPriority = ProjectItemPriority.MEDIUM) -> Optional[ProjectItem]:
        """プロジェクトアイテムを作成"""
        if self.dry_run:
            logger.info(f"DRY RUN: プロジェクトアイテム作成 - {title}")
            return ProjectItem(
                id=f"DRAFT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=title,
                body=body,
                status=status,
                priority=priority
            )
        
        # まずドラフトアイテムを作成
        create_mutation = """
        mutation($projectId: ID!, $title: String!, $body: String!) {
            addProjectV2DraftIssue(input: {
                projectId: $projectId
                title: $title
                body: $body
            }) {
                projectItem {
                    id
                    content {
                        ... on DraftIssue {
                            title
                            body
                            createdAt
                            updatedAt
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "projectId": project_id,
            "title": title,
            "body": body
        }
        
        try:
            result = await self._make_graphql_request(create_mutation, variables)
            
            project_item = result["data"]["addProjectV2DraftIssue"]["projectItem"]
            content = project_item["content"]
            
            item = ProjectItem(
                id=project_item["id"],
                title=content["title"],
                body=content["body"],
                status=status,
                priority=priority,
                created_at=content["createdAt"],
                updated_at=content["updatedAt"]
            )
            
            # ステータスと優先度を設定
            await self._update_item_fields(project_id, item.id, status, priority)
            
            return item
            
        except Exception as e:
            logger.error(f"プロジェクトアイテム作成エラー: {e}")
            return None
    
    async def _update_item_fields(self, project_id: str, item_id: str, 
                                  status: ProjectItemStatus, priority: ProjectItemPriority):
        """アイテムのフィールドを更新"""
        if self.dry_run:
            logger.info(f"DRY RUN: アイテムフィールド更新 - {item_id}")
            return
        
        # フィールドIDを取得（簡単のため固定値を使用）
        # 実際の実装では、プロジェクトのフィールド設定を動的に取得する必要がある
        
        # ステータス更新
        if status != ProjectItemStatus.TODO:
            status_mutation = """
            mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
                updateProjectV2ItemFieldValue(input: {
                    projectId: $projectId
                    itemId: $itemId
                    fieldId: $fieldId
                    value: $value
                }) {
                    projectV2Item {
                        id
                    }
                }
            }
            """
            
            # フィールドIDはプロジェクトごとに異なるため、実際の実装では動的に取得
            logger.info(f"ステータス更新: {item_id} -> {status.value}")
    
    async def update_project_item(self, project_id: str, item_id: str, 
                                  title: Optional[str] = None, body: Optional[str] = None,
                                  status: Optional[ProjectItemStatus] = None,
                                  priority: Optional[ProjectItemPriority] = None) -> Optional[ProjectItem]:
        """プロジェクトアイテムを更新"""
        if self.dry_run:
            logger.info(f"DRY RUN: プロジェクトアイテム更新 - {item_id}")
            return ProjectItem(
                id=item_id,
                title=title or "Updated Title",
                body=body or "Updated Body",
                status=status or ProjectItemStatus.IN_PROGRESS,
                priority=priority or ProjectItemPriority.MEDIUM
            )
        
        # 実際の実装では、GraphQL mutationでアイテムを更新
        logger.info(f"プロジェクトアイテム更新: {item_id}")
        
        # フィールドの更新
        if status:
            await self._update_item_fields(project_id, item_id, status, priority or ProjectItemPriority.MEDIUM)
        
        return None
    
    async def delete_project_item(self, project_id: str, item_id: str) -> bool:
        """プロジェクトアイテムを削除"""
        if self.dry_run:
            logger.info(f"DRY RUN: プロジェクトアイテム削除 - {item_id}")
            return True
        
        delete_mutation = """
        mutation($projectId: ID!, $itemId: ID!) {
            deleteProjectV2Item(input: {
                projectId: $projectId
                itemId: $itemId
            }) {
                deletedItemId
            }
        }
        """
        
        variables = {
            "projectId": project_id,
            "itemId": item_id
        }
        
        try:
            await self._make_graphql_request(delete_mutation, variables)
            logger.info(f"プロジェクトアイテム削除完了: {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"プロジェクトアイテム削除エラー: {e}")
            return False
    
    async def sync_plan_to_project(self, project_id: str, plan_name: str, tasks: List[Dict]) -> Dict:
        """計画書をプロジェクトに同期"""
        if self.dry_run:
            logger.info(f"DRY RUN: 計画書同期 - {plan_name} -> {project_id}")
        
        sync_results = {
            "project_id": project_id,
            "plan_name": plan_name,
            "total_tasks": len(tasks),
            "created_items": [],
            "updated_items": [],
            "failed_items": [],
            "sync_timestamp": datetime.now().isoformat()
        }
        
        # 既存のアイテムを取得
        existing_items = await self.get_project_items(project_id)
        existing_titles = {item.title: item for item in existing_items}
        
        for task in tasks:
            task_title = task.get("title", "")
            task_body = task.get("description", "")
            
            # 優先度をマップ
            priority_map = {
                "low": ProjectItemPriority.LOW,
                "medium": ProjectItemPriority.MEDIUM,
                "high": ProjectItemPriority.HIGH,
                "urgent": ProjectItemPriority.URGENT
            }
            priority = priority_map.get(task.get("priority", "medium"), ProjectItemPriority.MEDIUM)
            
            try:
                if task_title in existing_titles:
                    # 既存アイテムの更新
                    existing_item = existing_titles[task_title]
                    updated_item = await self.update_project_item(
                        project_id, existing_item.id, 
                        title=task_title, body=task_body, priority=priority
                    )
                    if updated_item:
                        sync_results["updated_items"].append(task_title)
                else:
                    # 新規アイテムの作成
                    new_item = await self.create_project_item(
                        project_id, task_title, task_body, 
                        ProjectItemStatus.TODO, priority
                    )
                    if new_item:
                        sync_results["created_items"].append(task_title)
                        
            except Exception as e:
                logger.error(f"タスク同期エラー: {task_title} - {e}")
                sync_results["failed_items"].append({
                    "title": task_title,
                    "error": str(e)
                })
        
        # 同期結果を保存
        await self._save_sync_results(sync_results)
        
        return sync_results
    
    async def _save_sync_results(self, results: Dict):
        """同期結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.data_path / f"sync_results_{timestamp}.json"
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"同期結果保存: {results_file}")
        except Exception as e:
            logger.error(f"同期結果保存エラー: {e}")
    
    async def get_sync_history(self) -> List[Dict]:
        """同期履歴を取得"""
        sync_files = list(self.data_path.glob("sync_results_*.json"))
        sync_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        history = []
        for file_path in sync_files[:10]:  # 最新10件
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    history.append(data)
            except Exception as e:
                logger.error(f"同期履歴読み込みエラー: {e}")
        
        return history
    
    async def get_project_overview(self, project_id: str) -> Dict:
        """プロジェクトの概要を取得"""
        if self.dry_run:
            return {
                "project_id": project_id,
                "total_items": 10,
                "status_counts": {
                    "Todo": 3,
                    "In Progress": 4,
                    "Done": 2,
                    "Blocked": 1
                },
                "priority_counts": {
                    "Low": 2,
                    "Medium": 5,
                    "High": 2,
                    "Urgent": 1
                },
                "last_updated": datetime.now().isoformat()
            }
        
        items = await self.get_project_items(project_id)
        
        status_counts = {}
        priority_counts = {}
        
        for item in items:
            status = item.status.value
            priority = item.priority.value
            
            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return {
            "project_id": project_id,
            "total_items": len(items),
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "last_updated": datetime.now().isoformat()
        }

# 使用例
async def main():
    """メイン実行関数"""
    async with GitHubProjectsClient() as client:
        # プロジェクト一覧を取得
        projects = await client.get_organization_projects()
        print(f"📋 プロジェクト数: {len(projects)}")
        
        for project in projects:
            print(f"  🚀 {project.title} (#{project.number})")
            
            # プロジェクトの概要を取得
            overview = await client.get_project_overview(project.id)
            print(f"    📊 アイテム数: {overview['total_items']}")
            print(f"    📈 ステータス: {overview['status_counts']}")

if __name__ == "__main__":
    asyncio.run(main())