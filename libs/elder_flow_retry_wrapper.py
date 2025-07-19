#!/usr/bin/env python3
"""
Elder Flow Retry Wrapper - リトライ機能付きElder Flow実行ラッパー
================================

PIDロック検出時に自動的にリトライを行うElder Flow実行ラッパー。
タスクが既に実行中の場合、ユーザーに明確な指示を出し、
必要に応じて自動リトライを実行します。

Author: Claude Elder
Created: 2025-01-19
"""

import asyncio
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.elder_system.flow.elder_flow_engine import ElderFlowEngine
from core.lightweight_logger import get_logger

logger = get_logger("elder_flow_retry")


class ElderFlowRetryWrapper:
    """リトライ機能付きElder Flowラッパー"""
    
    def __init__(self):
        self.engine = ElderFlowEngine()
        
    async def execute_with_retry(
        self,
        task_name: str,
        priority: str = "medium",
        max_retries: int = 3,
        retry_interval: int = 5,
        auto_retry: bool = False,
        interactive: bool = True
    ) -> Dict[str, Any]:
        """
        リトライ機能付きでElder Flowを実行
        
        Args:
            task_name: 実行するタスク名
            priority: 優先度 (high/medium/low)
            max_retries: 最大リトライ回数
            retry_interval: リトライ間隔（秒）
            auto_retry: 自動リトライを有効にするか
            interactive: 対話的モードか（ユーザー入力を求める）
            
        Returns:
            実行結果の辞書
        """
        attempt = 0
        
        while attempt <= max_retries:
            try:
                # Elder Flow実行を試みる
                result = await self.engine.execute_elder_flow({
                    "task_name": task_name,
                    "priority": priority
                })
                
                # エラーチェック
                if result.get("error") == "Task already running":
                    # タスクが既に実行中
                    pid = result.get("running_pid")
                    started_at = result.get("started_at")
                    
                    print(f"\n⚠️  タスク '{task_name}' は既に実行中です！")
                    print(f"   実行中のPID: {pid}")
                    print(f"   開始時刻: {started_at}")
                    print(f"   {result.get('retry_message', '')}")
                    
                    if attempt >= max_retries:
                        print(f"\n❌ 最大リトライ回数（{max_retries}回）に達しました。")
                        print("   以下のいずれかの方法で対処してください：")
                        print(f"   1. しばらく待ってから再実行: elder-flow execute \"{task_name}\"")
                        print(f"   2. 実行中のタスクの完了を確認: elder-flow status")
                        print(f"   3. 古いロックをクリーンアップ: elder-flow cleanup")
                        return result
                    
                    if auto_retry:
                        # 自動リトライモード
                        print(f"\n🔄 {retry_interval}秒後に自動リトライします... (試行 {attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_interval)
                        attempt += 1
                        continue
                    elif interactive:
                        # 対話的モード
                        print(f"\n🤔 どうしますか？")
                        print("   [R] リトライ（待機してから再実行）")
                        print("   [W] 待機（プロセスの完了を監視）")
                        print("   [C] キャンセル（実行を中止）")
                        print("   [F] 強制実行（古いロックをクリーンアップして実行）")
                        
                        choice = input("\n選択してください [R/W/C/F]: ").strip().upper()
                        
                        if choice == 'R':
                            print(f"\n⏳ {retry_interval}秒待機します...")
                            await asyncio.sleep(retry_interval)
                            attempt += 1
                            continue
                        elif choice == 'W':
                            await self._wait_for_task_completion(task_name, pid)
                            attempt += 1
                            continue
                        elif choice == 'F':
                            print("\n🧹 古いロックをクリーンアップします...")
                            cleanup_result = await self.engine.cleanup_stale_locks()
                            print(f"   {cleanup_result['cleaned_locks']}個のロックをクリーンアップしました")
                            attempt += 1
                            continue
                        else:
                            print("\n🚫 実行をキャンセルしました")
                            return result
                    else:
                        # 非対話的モード
                        return result
                else:
                    # 成功またはその他のエラー
                    return result
                    
            except Exception as e:
                logger.error(f"Elder Flow実行エラー: {e}")
                if attempt >= max_retries:
                    raise
                attempt += 1
                
        # ここに到達することはないはずだが、念のため
        return {"error": "Unexpected end of retry loop"}
        
    async def _wait_for_task_completion(self, task_name: str, pid: int, check_interval: int = 2):
        """
        タスクの完了を待機
        
        Args:
            task_name: 監視するタスク名
            pid: 監視するプロセスID
            check_interval: チェック間隔（秒）
        """
        print(f"\n⏳ タスク '{task_name}' (PID: {pid}) の完了を待機しています...")
        print("   Ctrl+C で中断できます")
        
        try:
            while True:
                # アクティブタスクをチェック
                active_tasks = await self.engine.get_active_tasks()
                
                # タスクがまだアクティブか確認
                is_active = any(
                    task['task_id'] == task_name and task['pid'] == pid
                    for task in active_tasks.get('active_tasks', [])
                )
                
                if not is_active:
                    print(f"\n✅ タスク '{task_name}' が完了しました！")
                    break
                    
                # プログレス表示
                print(".", end="", flush=True)
                await asyncio.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n🚫 待機を中断しました")
            raise
            
    async def get_status_with_retry_info(self) -> Dict[str, Any]:
        """リトライ情報を含むステータスを取得"""
        status = await self.engine.get_status()
        
        # ロックされたタスクがある場合、リトライ推奨情報を追加
        if status.get('locked_tasks', 0) > 0:
            status['retry_recommendations'] = []
            
            for task in status.get('locked_tasks_list', []):
                status['retry_recommendations'].append({
                    'task_id': task['task_id'],
                    'command': f'elder-flow execute --retry "{task["task_id"]}"',
                    'alternative': f'elder-flow execute --wait-for-pid {task["pid"]} "{task["task_id"]}"'
                })
                
        return status


# CLI用のヘルパー関数
async def execute_elder_flow_with_retry(
    task_name: str,
    priority: str = "medium",
    auto_retry: bool = False,
    max_retries: int = 3,
    retry_interval: int = 5
) -> Dict[str, Any]:
    """
    Elder Flowをリトライ機能付きで実行（CLI用）
    
    Args:
        task_name: 実行するタスク名
        priority: 優先度
        auto_retry: 自動リトライの有効/無効
        max_retries: 最大リトライ回数
        retry_interval: リトライ間隔（秒）
        
    Returns:
        実行結果
    """
    wrapper = ElderFlowRetryWrapper()
    
    return await wrapper.execute_with_retry(
        task_name=task_name,
        priority=priority,
        max_retries=max_retries,
        retry_interval=retry_interval,
        auto_retry=auto_retry,
        interactive=not auto_retry  # 自動リトライが無効なら対話的モード
    )


# テスト用メイン関数
async def main():
    """テスト実行"""
    import sys
    
    if len(sys.argv) > 1:
        task_name = " ".join(sys.argv[1:])
        result = await execute_elder_flow_with_retry(
            task_name=task_name,
            auto_retry=False
        )
        print(f"\n実行結果: {result}")
    else:
        print("使用法: python elder_flow_retry_wrapper.py <task_name>")


if __name__ == "__main__":
    asyncio.run(main())