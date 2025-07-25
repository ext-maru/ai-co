#!/usr/bin/env python3
"""
🌟 魂システム → 4賢者システム統合スクリプト
==========================================

Soul実装を4賢者システム（business_logic.py + a2a_agent.py）に統合

Author: Claude Elder
Created: 2025-07-23
"""

import os
import shutil
import re
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class MigrationTask:
    """移行タスク定義"""
    sage_name: str
    source_file: str
    target_business_logic: str
    target_a2a_agent: str
    backup_location: str

class SoulTo4SagesMigrator:
    """Soul → 4賢者システム移行ツール"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.backup_dir = self.project_root / "archives" / "soul_system_backup_20250723"
        
        # 4賢者システム
        self.sages = ["incident_sage", "knowledge_sage", "task_sage", "rag_sage"]
        
        # 移行タスク定義
        self.migration_tasks = [
            MigrationTask(
                sage_name=sage,
                source_file=f"{sage}/soul.py",
                target_business_logic=f"{sage}/business_logic.py",
                target_a2a_agent=f"{sage}/a2a_agent.py",
                backup_location=f"archives/soul_system_backup_20250723/{sage}_soul.py"
            )
            for sage in self.sages
        ]
    
    def create_backup(self) -> None:
        """Soul系ファイルのバックアップ作成"""
        print("💾 Soul系ファイルバックアップ作成中...")
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 4賢者Soul実装バックアップ
        for sage in self.sages:
            soul_file = self.project_root / sage / "soul.py"
            if soul_file.exists():
                backup_file = self.backup_dir / f"{sage}_soul.py"
                shutil.copy2(soul_file, backup_file)
                print(f"  ✅ {soul_file} → {backup_file}")
        
        # Soul基底クラスバックアップ
        soul_base_files = [
            "shared_libs/soul_base.py",
            "libs/base_soul.py"
        ]
        
        for soul_base in soul_base_files:
            source_path = self.project_root / soul_base
            if source_path.exists():
                backup_file = self.backup_dir / source_path.name
                shutil.copy2(source_path, backup_file)
                print(f"  ✅ {source_path} → {backup_file}")
        
        print(f"📁 バックアップ完了: {self.backup_dir}")
    
    def extract_business_logic(self, soul_content: str, sage_name: str) -> str:
        """Soul実装からビジネスロジックを抽出"""
        
        # クラス名変更パターン
        class_mapping = {
            "IncidentSageSoul": "IncidentSageLogic",
            "KnowledgeSage": "KnowledgeSageLogic", 
            "TaskSageSoul": "TaskSageLogic",
            "RAGSageSoul": "RAGSageLogic"
        }
        
        # Soul特有のimportを削除・置換
        content = re.sub(r'from shared_libs\.soul_base import BaseSoul\n', '', soul_content)
        content = re.sub(r'from libs\.base_soul import BaseSoul\n', '', soul_content)
        
        # クラス定義の変更
        for old_class, new_class in class_mapping.items():
            content = re.sub(
                rf'class {old_class}\(BaseSoul\):',
                f'class {new_class}:',
                content
            )
        
        # BaseSoulメソッドの削除・置換
        soul_specific_methods = [
            'soul_id', 'start_soul', 'stop_soul', 'soul_status'
        ]
        
        for method in soul_specific_methods:
            # メソッド定義とその本体を削除
            pattern = rf'    def {method}\(self[^\n]*\):[^\n]*\n(?:        [^\n]*\n)*'
            content = re.sub(pattern, '', content, flags=re.MULTILINE)
        
        # 4賢者システム標準import追加
        new_imports = f"""# 4賢者システム標準実装
from {sage_name}.abilities.{sage_name}_models import *
from {sage_name}.a2a_agent import {sage_name.title().replace('_', '')}Agent
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

"""
        
        content = new_imports + content
        
        return content
    
    def extract_a2a_logic(self, soul_content: str, sage_name: str) -> str:
        """Soul実装からA2A通信ロジックを抽出"""
        
        agent_class_name = sage_name.title().replace('_', '') + "Agent"

'''
{sage_name.title().replace('_', ' ')} A2A Communication Agent
A2A (Agent to Agent) 通信エージェント

Author: Claude Elder (migrated from Soul system)
Created: 2025-07-23
'''

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class {agent_class_name}:
    '''
    {sage_name.title().replace('_', ' ')} A2A通信エージェント
    
    他の賢者との通信を管理
    '''
    
    def __init__(self, sage_name: str = "{sage_name}"):
        self.sage_name = sage_name
        self.message_queue = []
        self.connection_status = {{}}
        
    async def send_message(self, target_sage: str, message: Dict[str, Any]) -> bool:
        '''他の賢者にメッセージ送信'''
        try:
            message_data = {{
                "from": self.sage_name,
                "to": target_sage,
                "timestamp": datetime.now().isoformat(),
                "data": message
            }}
            
            # A2Aメッセージ送信ロジック

            logger.info(f"{{self.sage_name}} → {{target_sage}}: {{message}}")
            
            return True
            
        except Exception as e:
            logger.error(f"A2A送信エラー: {{e}}")
            return False
    
    async def receive_message(self) -> Optional[Dict[str, Any]]:
        '''メッセージ受信'''
        try:
            # A2Aメッセージ受信ロジック

            if self.message_queue:
                return self.message_queue.pop(0)
            return None
            
        except Exception as e:
            logger.error(f"A2A受信エラー: {{e}}")
            return None
    
    async def broadcast_status(self, status_data: Dict[str, Any]) -> None:
        '''ステータス情報のブロードキャスト'''
        try:
            status_message = {{
                "type": "status_update",
                "sage": self.sage_name,
                "status": status_data,
                "timestamp": datetime.now().isoformat()
            }}
            
            # 全賢者にブロードキャスト
            other_sages = ["incident_sage", "knowledge_sage", "task_sage", "rag_sage"]
            other_sages.remove(self.sage_name)
            
            for target_sage in other_sages:
                await self.send_message(target_sage, status_message)
                
        except Exception as e:
            logger.error(f"ステータスブロードキャストエラー: {{e}}")
    
    def get_connection_status(self) -> Dict[str, str]:
        '''接続状況取得'''
        return self.connection_status.copy()
"""

    def migrate_sage(self, task: MigrationTask) -> Tuple[bool, str]:
        '''個別賢者の移行実行'''
        try:
            source_path = self.project_root / task.source_file
            if not source_path.exists():
                return False, f"ソースファイルが存在しません: {source_path}"
            
            # Soul実装読み込み
            with open(source_path, 'r', encoding='utf-8') as f:
                soul_content = f.read()
            
            # Business Logic抽出・生成
            business_logic_content = self.extract_business_logic(soul_content, task.sage_name)
            business_logic_path = self.project_root / task.target_business_logic
            
            # 既存business_logic.pyがある場合は統合
            if business_logic_path.exists():
                print(f"  ⚠️ 既存 {business_logic_path} を統合モードで更新")

                business_logic_path = business_logic_path.with_suffix('.py.soul_migrated')
            
            with open(business_logic_path, 'w', encoding='utf-8') as f:
                f.write(business_logic_content)
            
            # A2A Agent生成
            a2a_content = self.extract_a2a_logic(soul_content, task.sage_name)
            a2a_path = self.project_root / task.target_a2a_agent
            
            with open(a2a_path, 'w', encoding='utf-8') as f:
                f.write(a2a_content)
            
            return True, f"移行成功: {task.sage_name}"
            
        except Exception as e:
            return False, f"移行エラー {task.sage_name}: {e}"
    
    def execute_migration(self) -> None:
        '''全体移行実行'''
        print("🌟 Soul → 4賢者システム移行開始")
        print("="*50)
        
        # Step 1: バックアップ作成
        self.create_backup()
        print()
        
        # Step 2: 各賢者の移行
        print("🔄 各賢者システム移行中...")
        migration_results = []
        
        for task in self.migration_tasks:
            print(f"  📊 {task.sage_name} 移行中...")
            success, message = self.migrate_sage(task)
            migration_results.append((task.sage_name, success, message))
            
            if success:
                print(f"    ✅ {message}")
            else:
                print(f"    ❌ {message}")
        
        # Step 3: 結果サマリー
        print("\n" + "="*50)
        print("🎉 移行完了サマリー")
        print("="*50)
        
        successful_migrations = [r for r in migration_results if r[1]]
        failed_migrations = [r for r in migration_results if not r[1]]
        
        print(f"✅ 成功: {len(successful_migrations)}/{len(migration_results)}")
        print(f"❌ 失敗: {len(failed_migrations)}/{len(migration_results)}")
        
        if successful_migrations:
            print("\n📁 生成されたファイル:")
            for sage_name, _, _ in successful_migrations:
                print(f"  - {sage_name}/business_logic.py (または .soul_migrated)")
                print(f"  - {sage_name}/a2a_agent.py")
        
        if failed_migrations:
            print("\n⚠️ 失敗した移行:")
            for sage_name, _, message in failed_migrations:
                print(f"  - {sage_name}: {message}")
        
        print(f"\n💾 バックアップ場所: {self.backup_dir}")
        print("\n🚀 次のステップ:")
        print("1.0 生成されたファイルの動作確認")
        print("2.0 テスト実行・統合確認")
        print("3.0 Soul系ファイルの段階的削除")
        print("="*50)

def main():
    '''メイン実行'''
    migrator = SoulTo4SagesMigrator()
    migrator.execute_migration()

if __name__ == "__main__":
    main()