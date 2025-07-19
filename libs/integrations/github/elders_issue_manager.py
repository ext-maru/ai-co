"""
エルダーズギルド専用GitHub Issue管理システム
完全自動化されたIssue管理とElder Flow統合
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest

# エルダーズギルドシステムのインポート
from libs.four_sages.knowledge.knowledge_sage import KnowledgeSage
from libs.four_sages.task.task_sage import TaskSage
from libs.four_sages.incident.incident_sage import IncidentSage
from libs.four_sages.rag.rag_sage import RAGSage
from libs.elder_system.flow.elder_flow_executor import ElderFlowExecutor

logger = logging.getLogger(__name__)


class EldersIssueManager:
    """エルダーズギルド専用Issue管理システム"""
    
    def __init__(self, github_token: Optional[str] = None):
        """初期化
        
        Args:
            github_token: GitHubアクセストークン（環境変数からも取得可能）
        """
        self.token = github_token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required")
            
        self.github = Github(self.token)
        self.repo = None
        
        # 4賢者システムの初期化
        self.knowledge_sage = KnowledgeSage()
        self.task_sage = TaskSage()
        self.incident_sage = IncidentSage()
        self.rag_sage = RAGSage()
        
        # Elder Flowエグゼキューター
        self.elder_flow = ElderFlowExecutor()
        
        # 設定
        self.config = {
            'auto_close_keywords': ['fixes', 'closes', 'resolves', 'fixed', 'closed', 'resolved'],
            'progress_keywords': ['完了', '進行中', '開始', 'done', 'progress', 'complete', 'started'],
            'epic_labels': ['epic', 'master-issue', 'エピック'],
            'sub_issue_prefix': '[Sub]',
            'servant_assignments': {
                'bug': 'incident-knights',
                'feature': 'dwarf-workshop',
                'research': 'rag-wizards',
                'maintenance': 'elf-forest'
            }
        }
    
    def set_repository(self, repo_name: str):
        """リポジトリを設定
        
        Args:
            repo_name: リポジトリ名（owner/repo形式）
        """
        self.repo = self.github.get_repo(repo_name)
        logger.info(f"Repository set to: {repo_name}")
    
    async def create_sub_issues_from_epic(self, epic_issue: Issue) -> List[Issue]:
        """EpicからSub Issueを自動生成
        
        Args:
            epic_issue: Epic Issue
            
        Returns:
            作成されたSub Issueのリスト
        """
        if not epic_issue.body:
            return []
        
        # チェックリストを解析
        checklist_items = self._parse_checklist(epic_issue.body)
        if not checklist_items:
            return []
        
        created_issues = []
        
        for item in checklist_items:
            # 既にSub Issueが作成されているかチェック
            if self._is_sub_issue_created(epic_issue, item['text']):
                continue
            
            # Sub Issueを作成
            sub_issue = await self._create_sub_issue(epic_issue, item)
            if sub_issue:
                created_issues.append(sub_issue)
                
                # Epic Issueのチェックリストを更新
                await self._update_epic_checklist(epic_issue, item['text'], sub_issue.number)
        
        # 進捗を更新
        await self.update_progress_chart(epic_issue)
        
        return created_issues
    
    async def auto_assign_to_servants(self, issue: Issue):
        """エルダーサーバントへの自動アサイン
        
        Args:
            issue: アサイン対象のIssue
        """
        # ラベルから適切なサーバントを判定
        servant_type = None
        for label in issue.labels:
            if label.name in self.config['servant_assignments']:
                servant_type = self.config['servant_assignments'][label.name]
                break
        
        if not servant_type:
            # RAG賢者に相談して最適なサーバントを決定
            analysis = await self.rag_sage.process_request({
                'type': 'analyze',
                'content': f"Issue: {issue.title}\n{issue.body}",
                'task': 'servant_assignment'
            })
            
            servant_type = analysis.get('recommended_servant', 'dwarf-workshop')
        
        # サーバントラベルを追加
        issue.add_to_labels(servant_type)
        
        # コメントで通知
        issue.create_comment(
            f"🤖 **エルダーサーバント自動アサイン**\n\n"
            f"このIssueは `{servant_type}` に自動アサインされました。\n\n"
            f"担当サーバント部隊が間もなく作業を開始します。"
        )
        
        logger.info(f"Issue #{issue.number} assigned to {servant_type}")
    
    async def update_progress_chart(self, master_issue: Issue):
        """進捗チャートを自動更新
        
        Args:
            master_issue: Master Issue
        """
        # Sub Issueの進捗を集計
        progress_data = await self._calculate_progress(master_issue)
        
        # 進捗チャートを生成
        chart = self._generate_progress_chart(progress_data)
        
        # Issue本文を更新
        updated_body = self._update_issue_body_with_chart(master_issue.body, chart)
        master_issue.edit(body=updated_body)
        
        # 進捗ラベルを更新
        progress_label = f"progress:{progress_data['percentage']}%"
        
        # 既存の進捗ラベルを削除
        for label in master_issue.labels:
            if label.name.startswith('progress:'):
                master_issue.remove_from_labels(label.name)
        
        # 新しい進捗ラベルを追加
        master_issue.add_to_labels(progress_label)
        
        logger.info(f"Updated progress for Issue #{master_issue.number}: {progress_data['percentage']}%")
    
    async def handle_pr_merge(self, pr: PullRequest):
        """PRマージ時の自動処理
        
        Args:
            pr: マージされたPull Request
        """
        if not pr.body:
            return
        
        # 関連Issueを検出
        related_issues = self._extract_related_issues(pr.body)
        
        for issue_number in related_issues:
            try:
                issue = self.repo.get_issue(issue_number)
                
                # Issueをクローズ
                issue.edit(state='closed')
                
                # 完了コメントを追加
                issue.create_comment(
                    f"✅ **自動クローズ**\n\n"
                    f"PR #{pr.number} のマージにより、このIssueは自動的にクローズされました。\n\n"
                    f"🤖 Automated by Elders Guild Issue Management System"
                )
                
                # Elder Flowに通知
                await self.elder_flow.notify_completion(f"Issue #{issue_number}")
                
                logger.info(f"Auto-closed Issue #{issue_number} due to PR #{pr.number} merge")
                
            except Exception as e:
                logger.error(f"Failed to close Issue #{issue_number}: {e}")
    
    async def sync_with_four_sages(self, issue: Issue):
        """4賢者システムとの同期
        
        Args:
            issue: 同期対象のIssue
        """
        # ナレッジ賢者: Issue履歴から学習
        await self.knowledge_sage.process_request({
            'type': 'learn',
            'source': 'github_issue',
            'data': {
                'number': issue.number,
                'title': issue.title,
                'body': issue.body,
                'labels': [l.name for l in issue.labels],
                'state': issue.state,
                'created_at': issue.created_at.isoformat(),
                'updated_at': issue.updated_at.isoformat()
            }
        })
        
        # タスク賢者: タスクとして登録
        if issue.state == 'open':
            await self.task_sage.process_request({
                'type': 'create_task',
                'task': {
                    'id': f"issue-{issue.number}",
                    'title': issue.title,
                    'description': issue.body,
                    'priority': self._determine_priority(issue),
                    'labels': [l.name for l in issue.labels]
                }
            })
        
        # インシデント賢者: バグの場合は通知
        if any(label.name in ['bug', 'incident', 'critical'] for label in issue.labels):
            await self.incident_sage.process_request({
                'type': 'report_incident',
                'incident': {
                    'source': 'github_issue',
                    'issue_number': issue.number,
                    'title': issue.title,
                    'severity': self._determine_severity(issue),
                    'description': issue.body
                }
            })
        
        # RAG賢者: 類似Issue検索
        similar_issues = await self.rag_sage.process_request({
            'type': 'search_similar',
            'query': issue.title,
            'context': issue.body,
            'limit': 5
        })
        
        if similar_issues.get('results'):
            # 類似Issueをコメントで通知
            comment = "🔍 **類似Issue検出**\n\n以下の類似Issueが見つかりました：\n\n"
            for similar in similar_issues['results']:
                comment += f"- #{similar['issue_number']}: {similar['title']} (類似度: {similar['similarity']:.0%})\n"
            
            issue.create_comment(comment)
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        """日次レポートを生成
        
        Returns:
            レポートデータ
        """
        today = datetime.now().date()
        
        # 本日の活動を集計
        report = {
            'date': today.isoformat(),
            'summary': {
                'opened_issues': 0,
                'closed_issues': 0,
                'merged_prs': 0,
                'active_issues': 0,
                'progress_updates': 0
            },
            'highlights': [],
            'metrics': {
                'average_resolution_time': None,
                'completion_rate': 0,
                'velocity': 0
            }
        }
        
        # オープンIssueを取得
        open_issues = self.repo.get_issues(state='open')
        report['summary']['active_issues'] = open_issues.totalCount
        
        # 本日の活動を分析
        for issue in self.repo.get_issues(state='all', since=today):
            if issue.created_at.date() == today:
                report['summary']['opened_issues'] += 1
            
            if issue.state == 'closed' and issue.closed_at.date() == today:
                report['summary']['closed_issues'] += 1
        
        # メトリクスを計算
        if report['summary']['opened_issues'] > 0:
            report['metrics']['completion_rate'] = (
                report['summary']['closed_issues'] / 
                report['summary']['opened_issues'] * 100
            )
        
        # 4賢者からの洞察を追加
        insights = await self._gather_sage_insights()
        report['sage_insights'] = insights
        
        return report
    
    # ヘルパーメソッド
    def _parse_checklist(self, body: str) -> List[Dict[str, Any]]:
        """チェックリストを解析"""
        import re
        pattern = r'- \[([ x])\] (.+)'
        matches = re.findall(pattern, body)
        
        return [
            {'checked': match[0] == 'x', 'text': match[1]}
            for match in matches
        ]
    
    def _is_sub_issue_created(self, epic_issue: Issue, item_text: str) -> bool:
        """Sub Issueが既に作成されているかチェック"""
        # コメントからSub Issue作成記録を検索
        for comment in epic_issue.get_comments():
            if f"Sub Issue created for: {item_text}" in comment.body:
                return True
        return False
    
    async def _create_sub_issue(self, epic_issue: Issue, item: Dict[str, Any]) -> Optional[Issue]:
        """Sub Issueを作成"""
        try:
            title = f"{self.config['sub_issue_prefix']} {item['text']}"
            body = (
                f"This is a sub-issue of #{epic_issue.number}\n\n"
                f"**Task**: {item['text']}\n\n"
                f"**Parent Issue**: #{epic_issue.number} - {epic_issue.title}"
            )
            
            # ラベルを継承
            labels = [l.name for l in epic_issue.labels]
            labels.append('sub-issue')
            
            sub_issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=labels
            )
            
            # Epic Issueにコメントを追加
            epic_issue.create_comment(
                f"📋 Sub Issue created for: {item['text']}\n"
                f"→ #{sub_issue.number}"
            )
            
            return sub_issue
            
        except Exception as e:
            logger.error(f"Failed to create sub-issue: {e}")
            return None
    
    async def _update_epic_checklist(self, epic_issue: Issue, item_text: str, sub_issue_number: int):
        """Epic Issueのチェックリストを更新"""
        body = epic_issue.body
        old_item = f"- [ ] {item_text}"
        new_item = f"- [ ] {item_text} → #{sub_issue_number}"
        
        updated_body = body.replace(old_item, new_item)
        epic_issue.edit(body=updated_body)
    
    async def _calculate_progress(self, master_issue: Issue) -> Dict[str, Any]:
        """進捗を計算"""
        checklist_items = self._parse_checklist(master_issue.body)
        total = len(checklist_items)
        completed = sum(1 for item in checklist_items if item['checked'])
        
        return {
            'total': total,
            'completed': completed,
            'percentage': int((completed / total * 100) if total > 0 else 0)
        }
    
    def _generate_progress_chart(self, progress_data: Dict[str, Any]) -> str:
        """進捗チャートを生成"""
        percentage = progress_data['percentage']
        filled = int(percentage / 10)
        empty = 10 - filled
        
        bar = "█" * filled + "░" * empty
        
        return (
            f"## 📊 Progress: {percentage}%\n"
            f"[{bar}] {progress_data['completed']}/{progress_data['total']} completed"
        )
    
    def _update_issue_body_with_chart(self, body: str, chart: str) -> str:
        """Issue本文に進捗チャートを更新"""
        import re
        
        # 既存の進捗チャートを削除
        pattern = r'## 📊 Progress:.*?\n\[.*?\] \d+/\d+ completed'
        body = re.sub(pattern, '', body, flags=re.DOTALL)
        
        # 新しいチャートを追加
        return f"{chart}\n\n{body.strip()}"
    
    def _extract_related_issues(self, body: str) -> List[int]:
        """PR本文から関連Issueを抽出"""
        import re
        
        pattern = r'(?:closes?|fix(?:es)?|resolv(?:es)?)\s*#(\d+)'
        matches = re.findall(pattern, body, re.IGNORECASE)
        
        return [int(match) for match in matches]
    
    def _determine_priority(self, issue: Issue) -> str:
        """Issueの優先度を判定"""
        labels = [l.name.lower() for l in issue.labels]
        
        if any(l in ['critical', 'urgent', 'p0'] for l in labels):
            return 'critical'
        elif any(l in ['high', 'important', 'p1'] for l in labels):
            return 'high'
        elif any(l in ['medium', 'p2'] for l in labels):
            return 'medium'
        else:
            return 'low'
    
    def _determine_severity(self, issue: Issue) -> str:
        """Issueの重要度を判定"""
        labels = [l.name.lower() for l in issue.labels]
        
        if any(l in ['critical', 'blocker'] for l in labels):
            return 'critical'
        elif any(l in ['major', 'high'] for l in labels):
            return 'major'
        elif any(l in ['minor', 'medium'] for l in labels):
            return 'minor'
        else:
            return 'trivial'
    
    async def _gather_sage_insights(self) -> Dict[str, Any]:
        """4賢者からの洞察を収集"""
        insights = {}
        
        # 各賢者から洞察を取得
        insights['knowledge'] = await self.knowledge_sage.process_request({
            'type': 'get_insights',
            'topic': 'issue_management'
        })
        
        insights['task'] = await self.task_sage.process_request({
            'type': 'get_task_insights'
        })
        
        insights['incident'] = await self.incident_sage.process_request({
            'type': 'get_incident_summary'
        })
        
        insights['rag'] = await self.rag_sage.process_request({
            'type': 'get_trending_topics'
        })
        
        return insights


# CLIインターフェース
async def main():
    """CLIエントリーポイント"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Elders Guild Issue Manager')
    parser.add_argument('command', choices=['sync', 'report', 'auto-assign', 'create-subs'])
    parser.add_argument('--repo', required=True, help='Repository (owner/repo)')
    parser.add_argument('--issue', type=int, help='Issue number')
    
    args = parser.parse_args()
    
    # マネージャーを初期化
    manager = EldersIssueManager()
    manager.set_repository(args.repo)
    
    if args.command == 'sync':
        # 全Issueを4賢者と同期
        issues = manager.repo.get_issues(state='open')
        for issue in issues:
            await manager.sync_with_four_sages(issue)
            print(f"Synced Issue #{issue.number}")
    
    elif args.command == 'report':
        # 日次レポートを生成
        report = await manager.generate_daily_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    elif args.command == 'auto-assign' and args.issue:
        # 特定Issueを自動アサイン
        issue = manager.repo.get_issue(args.issue)
        await manager.auto_assign_to_servants(issue)
        print(f"Auto-assigned Issue #{args.issue}")
    
    elif args.command == 'create-subs' and args.issue:
        # EpicからSub Issueを作成
        epic = manager.repo.get_issue(args.issue)
        sub_issues = await manager.create_sub_issues_from_epic(epic)
        print(f"Created {len(sub_issues)} sub-issues from Epic #{args.issue}")


if __name__ == '__main__':
    asyncio.run(main())