#!/usr/bin/env python3
"""PostgreSQL タスクテーブルのスキーマ確認"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.postgres_claude_task_tracker import create_postgres_task_tracker


async def check_schema():
    """テーブルスキーマを確認"""
    print("=== PostgreSQL task_sage テーブルスキーマ確認 ===\n")
    
    tracker = await create_postgres_task_tracker()
    
    try:
        async with tracker._get_connection() as conn:
            # テーブルのカラム情報を取得
            columns = await conn.fetch("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = 'task_sage'
                ORDER BY ordinal_position;
            """)
            
            print("task_sage テーブルのカラム:")
            print("-" * 60)
            for col in columns:
                print(f"{col['column_name']:20} | {col['data_type']:15} | NULL: {col['is_nullable']:3}")
            
            # 実際のデータを1件取得して確認
            print("\n\n実際のデータ例:")
            print("-" * 60)
            row = await conn.fetchrow("SELECT * FROM task_sage WHERE is_archived = FALSE LIMIT 1")
            
            if row:
                data = dict(row)
                for key, value in data.items():
                    if key in ['name', 'title', 'task_id', 'status']:
                        print(f"{key:20} | {str(value)[:50]}")
            else:
                print("データが見つかりません")
                
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tracker.close()


if __name__ == "__main__":
    asyncio.run(check_schema())