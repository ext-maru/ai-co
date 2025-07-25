#!/usr/bin/env python3
"""
統合システムデバッグ
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


async def debug_integration():
    """デバッグ実行"""
    print("🔍 統合システムデバッグ開始\n")
    
    # インポートテスト
    print("1️⃣ インポートテスト")
    try:
        from elders_guild.elder_tree.four_sages.knowledge.enhanced_knowledge_sage import EnhancedKnowledgeSage
        print("   ✅ EnhancedKnowledgeSage")
    except Exception as e:
        print(f"   ❌ EnhancedKnowledgeSage: {e}")
        
    try:
        from elders_guild.elder_tree.four_sages.task.task_sage import TaskSage
        print("   ✅ TaskSage")
    except Exception as e:
        print(f"   ❌ TaskSage: {e}")
        
    try:
        from elders_guild.elder_tree.four_sages.incident.incident_sage import IncidentSage
        print("   ✅ IncidentSage")
    except Exception as e:
        print(f"   ❌ IncidentSage: {e}")
        
    try:
        from elders_guild.elder_tree.four_sages.rag.rag_sage import RAGSage
        print("   ✅ RAGSage")
    except Exception as e:
        print(f"   ❌ RAGSage: {e}")
    
    # 個別初期化テスト
    print("\n2️⃣ 個別初期化テスト")
    
    try:
        sage = EnhancedKnowledgeSage()
        print("   ✅ EnhancedKnowledgeSage初期化成功")
    except Exception as e:
        print(f"   ❌ EnhancedKnowledgeSage初期化失敗: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        sage = TaskSage()
        print("   ✅ TaskSage初期化成功")
    except Exception as e:
        print(f"   ❌ TaskSage初期化失敗: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        sage = IncidentSage()
        print("   ✅ IncidentSage初期化成功")
    except Exception as e:
        print(f"   ❌ IncidentSage初期化失敗: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        sage = RAGSage()
        print("   ✅ RAGSage初期化成功")
    except Exception as e:
        print(f"   ❌ RAGSage初期化失敗: {e}")
        import traceback
        traceback.print_exc()
    
    # 統合システムテスト
    print("\n3️⃣ 統合システムテスト")
    try:
        from elders_guild.elder_tree.four_sages_integration_complete import FourSagesIntegrationComplete
        print("   ✅ FourSagesIntegrationCompleteインポート成功")
        
        system = FourSagesIntegrationComplete()
        print("   ✅ インスタンス作成成功")
        
        result = await system.initialize()
        print(f"   ℹ️ 初期化結果: {result}")
        
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_integration())