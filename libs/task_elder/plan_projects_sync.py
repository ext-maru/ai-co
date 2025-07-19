#!/usr/bin/env python3
"""
🔄 計画書→Projects同期システム
Plan to Projects Synchronization System

計画書の変更を自動検出し、GitHub Projectsに同期するシステム
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging
from enum import Enum
import os

from task_elder.task_breakdown_engine import TaskBreakdownEngine
from task_elder.project_board_manager import ProjectBoardManager, BoardConfig, BoardTemplate
from task_elder.github_projects_client import GitHubProjectsClient

logger = logging.getLogger(__name__)

class SyncMode(Enum):
    """同期モード"""
    MANUAL = "manual"
    AUTO = "auto"
    SCHEDULED = "scheduled"

class ChangeType(Enum):
    """変更タイプ"""
    NEW_PLAN = "new_plan"
    UPDATED_PLAN = "updated_plan"
    DELETED_PLAN = "deleted_plan"
    TASK_ADDED = "task_added"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"

@dataclass
class PlanSnapshot:
    """計画書のスナップショット"""
    file_path: str
    content_hash: str
    last_modified: str
    task_count: int
    tasks_hash: str
    created_at: str
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class SyncEvent:
    """同期イベント"""
    event_id: str
    plan_file: str
    project_id: str
    change_type: ChangeType
    sync_mode: SyncMode
    timestamp: str
    success: bool
    details: Dict[str, Any]
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.event_id:
            self.event_id = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

@dataclass
class SyncSchedule:
    """同期スケジュール"""
    plan_file: str
    project_id: str
    schedule_type: str  # "interval", "cron", "watch"
    interval_hours: Optional[int] = None
    cron_expression: Optional[str] = None
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None

class PlanProjectsSync:
    """計画書→Projects同期システム"""
    
    def __init__(self, github_token: Optional[str] = None):
        self.base_path = Path("/home/aicompany/ai_co")
        self.plans_path = self.base_path / "docs" / "plans"
        self.data_path = self.base_path / "data" / "plan_sync"
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # コンポーネント
        self.task_engine = TaskBreakdownEngine()
        self.board_manager = ProjectBoardManager(github_token)
        self.github_client = GitHubProjectsClient(github_token)
        
        # データストレージ
        self.snapshots_file = self.data_path / "plan_snapshots.json"
        self.sync_events_file = self.data_path / "sync_events.json"
        self.schedules_file = self.data_path / "sync_schedules.json"
        
        # データ
        self.snapshots = self._load_snapshots()
        self.sync_events = self._load_sync_events()
        self.schedules = self._load_schedules()
        
        # 設定
        self.config = {
            "auto_sync_enabled": True,
            "sync_interval_minutes": 30,
            "max_sync_events": 1000,
            "change_detection_enabled": True,
            "notification_enabled": True
        }
        
        # 統計
        self.stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "plans_monitored": 0,
            "last_sync": None,
            "uptime_start": datetime.now().isoformat()
        }
    
    def _load_snapshots(self) -> Dict[str, PlanSnapshot]:
        """スナップショットを読み込み"""
        if not self.snapshots_file.exists():
            return {}
        
        try:
            with open(self.snapshots_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                snapshots = {}
                for key, value in data.items():
                    snapshots[key] = PlanSnapshot(**value)
                return snapshots
        except Exception as e:
            logger.error(f"スナップショット読み込みエラー: {e}")
            return {}
    
    def _save_snapshots(self):
        """スナップショットを保存"""
        try:
            data = {}
            for key, snapshot in self.snapshots.items():
                data[key] = asdict(snapshot)
            
            with open(self.snapshots_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"スナップショット保存エラー: {e}")
    
    def _load_sync_events(self) -> List[SyncEvent]:
        """同期イベントを読み込み"""
        if not self.sync_events_file.exists():
            return []
        
        try:
            with open(self.sync_events_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                events = []
                for item in data:
                    try:
                        item['change_type'] = ChangeType(item['change_type'])
                        item['sync_mode'] = SyncMode(item['sync_mode'])
                        events.append(SyncEvent(**item))
                    except Exception as e:
                        logger.warning(f"同期イベント読み込みエラー: {e}")
                        continue
                return events
        except Exception as e:
            logger.error(f"同期イベント読み込みエラー: {e}")
            return []
    
    def _save_sync_events(self):
        """同期イベントを保存"""
        try:
            # 最新のイベントのみを保持
            events_to_save = self.sync_events[-self.config['max_sync_events']:]
            
            data = []
            for event in events_to_save:
                event_dict = asdict(event)
                event_dict['change_type'] = event.change_type.value
                event_dict['sync_mode'] = event.sync_mode.value
                data.append(event_dict)
            
            with open(self.sync_events_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"同期イベント保存エラー: {e}")
    
    def _load_schedules(self) -> List[SyncSchedule]:
        """スケジュールを読み込み"""
        if not self.schedules_file.exists():
            return []
        
        try:
            with open(self.schedules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                schedules = []
                for item in data:
                    schedules.append(SyncSchedule(**item))
                return schedules
        except Exception as e:
            logger.error(f"スケジュール読み込みエラー: {e}")
            return []
    
    def _save_schedules(self):
        """スケジュールを保存"""
        try:
            data = []
            for schedule in self.schedules:
                data.append(asdict(schedule))
            
            with open(self.schedules_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"スケジュール保存エラー: {e}")
    
    async def create_plan_snapshot(self, plan_file: str) -> Optional[PlanSnapshot]:
        """計画書のスナップショットを作成"""
        plan_path = self.plans_path / plan_file
        
        if not plan_path.exists():
            logger.warning(f"計画書が見つかりません: {plan_file}")
            return None
        
        try:
            # ファイル内容を読み込み
            with open(plan_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ハッシュを計算
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # タスクを抽出
            tasks = await self.task_engine.extract_tasks_from_plan(str(plan_path))
            task_count = len(tasks)
            
            # タスクのハッシュを計算
            tasks_str = json.dumps([{
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "category": task.category
            } for task in tasks], sort_keys=True)
            tasks_hash = hashlib.sha256(tasks_str.encode()).hexdigest()
            
            # 最終更新日時を取得
            stat = os.stat(plan_path)
            last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            snapshot = PlanSnapshot(
                file_path=plan_file,
                content_hash=content_hash,
                last_modified=last_modified,
                task_count=task_count,
                tasks_hash=tasks_hash,
                created_at=datetime.now().isoformat()
            )
            
            return snapshot
            
        except Exception as e:
            logger.error(f"スナップショット作成エラー: {plan_file} - {e}")
            return None
    
    async def detect_changes(self, plan_file: str) -> List[ChangeType]:
        """計画書の変更を検出"""
        current_snapshot = await self.create_plan_snapshot(plan_file)
        if not current_snapshot:
            return []
        
        previous_snapshot = self.snapshots.get(plan_file)
        changes = []
        
        if not previous_snapshot:
            # 新規計画書
            changes.append(ChangeType.NEW_PLAN)
        else:
            # 内容の変更をチェック
            if current_snapshot.content_hash != previous_snapshot.content_hash:
                changes.append(ChangeType.UPDATED_PLAN)
            
            # タスクの変更をチェック
            if current_snapshot.tasks_hash != previous_snapshot.tasks_hash:
                if current_snapshot.task_count > previous_snapshot.task_count:
                    changes.append(ChangeType.TASK_ADDED)
                elif current_snapshot.task_count < previous_snapshot.task_count:
                    changes.append(ChangeType.TASK_DELETED)
                else:
                    changes.append(ChangeType.TASK_UPDATED)
        
        # スナップショットを更新
        self.snapshots[plan_file] = current_snapshot
        self._save_snapshots()
        
        return changes
    
    async def sync_plan_changes(self, plan_file: str, project_id: str, 
                                changes: List[ChangeType], 
                                sync_mode: SyncMode = SyncMode.AUTO) -> SyncEvent:
        """計画書の変更を同期"""
        event_id = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        print(f"🔄 計画書変更同期開始: {plan_file}")
        print(f"   📊 プロジェクトID: {project_id}")
        print(f"   🔄 変更タイプ: {[c.value for c in changes]}")
        print(f"   ⚙️  同期モード: {sync_mode.value}")
        
        try:
            # 変更に応じて同期を実行
            sync_results = []
            
            if ChangeType.NEW_PLAN in changes:
                # 新規プロジェクトボードの作成
                board_config = BoardConfig(template=BoardTemplate.KANBAN)
                board = await self.board_manager.create_board_from_plan(
                    plan_file, f"計画書: {plan_file}", board_config
                )
                if board:
                    sync_results.append(f"新規プロジェクトボード作成: {board.title}")
                
            if any(change in changes for change in [
                ChangeType.UPDATED_PLAN, ChangeType.TASK_ADDED, 
                ChangeType.TASK_UPDATED, ChangeType.TASK_DELETED
            ]):
                # 既存プロジェクトボードの更新
                result = await self.board_manager.sync_plan_to_board(plan_file, project_id)
                if result.get("success"):
                    sync_result = result["sync_result"]
                    sync_results.append(f"同期完了: 新規{len(sync_result.get('created_items', []))}, 更新{len(sync_result.get('updated_items', []))}")
                else:
                    sync_results.append(f"同期エラー: {result.get('error')}")
            
            # 同期イベントを作成
            sync_event = SyncEvent(
                event_id=event_id,
                plan_file=plan_file,
                project_id=project_id,
                change_type=changes[0] if changes else ChangeType.UPDATED_PLAN,
                sync_mode=sync_mode,
                timestamp=datetime.now().isoformat(),
                success=True,
                details={
                    "changes": [c.value for c in changes],
                    "sync_results": sync_results
                }
            )
            
            # 統計を更新
            self.stats["total_syncs"] += 1
            self.stats["successful_syncs"] += 1
            self.stats["last_sync"] = datetime.now().isoformat()
            
            print(f"✅ 同期完了: {len(sync_results)}件の操作")
            
        except Exception as e:
            logger.error(f"同期エラー: {e}")
            
            sync_event = SyncEvent(
                event_id=event_id,
                plan_file=plan_file,
                project_id=project_id,
                change_type=changes[0] if changes else ChangeType.UPDATED_PLAN,
                sync_mode=sync_mode,
                timestamp=datetime.now().isoformat(),
                success=False,
                details={"changes": [c.value for c in changes]},
                error_message=str(e)
            )
            
            # 統計を更新
            self.stats["total_syncs"] += 1
            self.stats["failed_syncs"] += 1
            
            print(f"❌ 同期失敗: {e}")
        
        # イベントを記録
        self.sync_events.append(sync_event)
        self._save_sync_events()
        
        return sync_event
    
    async def scan_all_plans(self) -> Dict[str, List[ChangeType]]:
        """すべての計画書をスキャンして変更を検出"""
        print("🔍 全計画書スキャン開始")
        
        if not self.plans_path.exists():
            logger.warning("計画書ディレクトリが見つかりません")
            return {}
        
        plan_changes = {}
        plan_files = list(self.plans_path.glob("*.md"))
        
        for plan_file in plan_files:
            relative_path = plan_file.name
            changes = await self.detect_changes(relative_path)
            
            if changes:
                plan_changes[relative_path] = changes
                print(f"   📋 変更検出: {relative_path} - {[c.value for c in changes]}")
        
        print(f"✅ スキャン完了: {len(plan_changes)}件の変更")
        return plan_changes
    
    async def auto_sync_all_changes(self) -> Dict:
        """すべての変更を自動同期"""
        print("🤖 自動同期開始")
        
        # 変更を検出
        plan_changes = await self.scan_all_plans()
        
        sync_summary = {
            "timestamp": datetime.now().isoformat(),
            "total_plans_scanned": len(list(self.plans_path.glob("*.md"))),
            "plans_with_changes": len(plan_changes),
            "sync_events": [],
            "successful_syncs": 0,
            "failed_syncs": 0
        }
        
        # 各変更に対して同期を実行
        for plan_file, changes in plan_changes.items():
            # 対応するプロジェクトIDを検索
            project_id = await self._find_project_id_for_plan(plan_file)
            
            if project_id:
                sync_event = await self.sync_plan_changes(
                    plan_file, project_id, changes, SyncMode.AUTO
                )
                sync_summary["sync_events"].append(asdict(sync_event))
                
                if sync_event.success:
                    sync_summary["successful_syncs"] += 1
                else:
                    sync_summary["failed_syncs"] += 1
            else:
                logger.warning(f"プロジェクトIDが見つかりません: {plan_file}")
        
        print(f"✅ 自動同期完了")
        print(f"   📊 変更のある計画書: {sync_summary['plans_with_changes']}")
        print(f"   ✅ 成功: {sync_summary['successful_syncs']}")
        print(f"   ❌ 失敗: {sync_summary['failed_syncs']}")
        
        return sync_summary
    
    async def _find_project_id_for_plan(self, plan_file: str) -> Optional[str]:
        """計画書に対応するプロジェクトIDを検索"""
        # プロジェクトボードマネージャーの同期マッピングを確認
        for mapping in self.board_manager.sync_mappings.values():
            if mapping.plan_file == plan_file:
                return mapping.project_id
        
        return None
    
    async def create_sync_schedule(self, plan_file: str, project_id: str, 
                                   schedule_type: str = "interval", 
                                   interval_hours: int = 24) -> bool:
        """同期スケジュールを作成"""
        schedule = SyncSchedule(
            plan_file=plan_file,
            project_id=project_id,
            schedule_type=schedule_type,
            interval_hours=interval_hours,
            enabled=True
        )
        
        # 次回実行時刻を計算
        if schedule_type == "interval" and interval_hours:
            next_run = datetime.now() + timedelta(hours=interval_hours)
            schedule.next_run = next_run.isoformat()
        
        self.schedules.append(schedule)
        self._save_schedules()
        
        logger.info(f"同期スケジュール作成: {plan_file} -> {project_id}")
        return True
    
    async def run_scheduled_syncs(self) -> Dict:
        """スケジュールされた同期を実行"""
        print("⏰ スケジュール同期実行")
        
        current_time = datetime.now()
        executed_schedules = []
        
        for schedule in self.schedules:
            if not schedule.enabled:
                continue
            
            should_run = False
            
            if schedule.schedule_type == "interval" and schedule.next_run:
                next_run_time = datetime.fromisoformat(schedule.next_run)
                if current_time >= next_run_time:
                    should_run = True
            
            if should_run:
                try:
                    # 変更を検出
                    changes = await self.detect_changes(schedule.plan_file)
                    
                    if changes:
                        # 同期を実行
                        sync_event = await self.sync_plan_changes(
                            schedule.plan_file, schedule.project_id, 
                            changes, SyncMode.SCHEDULED
                        )
                        executed_schedules.append({
                            "schedule": asdict(schedule),
                            "sync_event": asdict(sync_event)
                        })
                    
                    # 次回実行時刻を更新
                    if schedule.interval_hours:
                        next_run = current_time + timedelta(hours=schedule.interval_hours)
                        schedule.next_run = next_run.isoformat()
                    
                    schedule.last_run = current_time.isoformat()
                    
                except Exception as e:
                    logger.error(f"スケジュール同期エラー: {schedule.plan_file} - {e}")
        
        # スケジュールを保存
        self._save_schedules()
        
        print(f"✅ スケジュール同期完了: {len(executed_schedules)}件実行")
        
        return {
            "timestamp": current_time.isoformat(),
            "executed_schedules": executed_schedules,
            "total_schedules": len(self.schedules),
            "enabled_schedules": len([s for s in self.schedules if s.enabled])
        }
    
    async def get_sync_status(self) -> Dict:
        """同期状況を取得"""
        recent_events = self.sync_events[-10:] if len(self.sync_events) >= 10 else self.sync_events
        
        return {
            "stats": self.stats,
            "config": self.config,
            "monitored_plans": len(self.snapshots),
            "active_schedules": len([s for s in self.schedules if s.enabled]),
            "recent_events": [asdict(event) for event in recent_events],
            "health_status": self._calculate_health_status()
        }
    
    def _calculate_health_status(self) -> str:
        """システムの健全性を計算"""
        if self.stats["total_syncs"] == 0:
            return "初期状態"
        
        success_rate = (self.stats["successful_syncs"] / self.stats["total_syncs"]) * 100
        
        if success_rate >= 95:
            return "健全"
        elif success_rate >= 80:
            return "注意"
        else:
            return "警告"
    
    async def enable_continuous_sync(self, interval_minutes: int = 30):
        """継続的同期を有効化"""
        print(f"🔄 継続的同期開始（{interval_minutes}分間隔）")
        
        while True:
            try:
                # 自動同期を実行
                await self.auto_sync_all_changes()
                
                # スケジュール同期を実行
                await self.run_scheduled_syncs()
                
                # 指定された間隔で待機
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"継続的同期エラー: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機

# 使用例
async def main():
    """メイン実行関数"""
    sync_system = PlanProjectsSync()
    
    # システム状況を確認
    status = await sync_system.get_sync_status()
    print(f"🔄 計画書同期システム状況:")
    print(f"   📊 総同期数: {status['stats']['total_syncs']}")
    print(f"   ✅ 成功率: {status['stats']['successful_syncs']}/{status['stats']['total_syncs']}")
    print(f"   📋 監視中の計画書: {status['monitored_plans']}")
    print(f"   ⏰ アクティブスケジュール: {status['active_schedules']}")
    print(f"   🏥 健全性: {status['health_status']}")
    
    # 全計画書をスキャン
    changes = await sync_system.scan_all_plans()
    if changes:
        print(f"\n🔍 変更検出: {len(changes)}件")
        for plan_file, change_types in changes.items():
            print(f"   📋 {plan_file}: {[c.value for c in change_types]}")

if __name__ == "__main__":
    asyncio.run(main())