#!/usr/bin/env python3
"""Elder Flow自動適用メカニズムのテスト"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.elder_flow_task_integration import get_elder_flow_integration

async def test_auto_apply():
    """自動適用テスト"""
    integration = get_elder_flow_integration()
    
    test_cases = [
        # 実装系タスク
        ("OAuth2.0認証システムを実装してください", True, "implementation"),
        ("新機能：ユーザーダッシュボードを追加", True, "implementation"),
        
        # 修正系タスク
        ("ログインバグを修正してください", True, "fix"),
        ("エラー処理の問題を解決", True, "fix"),
        
        # 最適化系タスク
        ("データベースクエリを最適化", True, "optimization"),
        ("コードのリファクタリング実施", True, "optimization"),
        
        # セキュリティ系タスク
        ("セキュリティ脆弱性の対策実装", True, "security"),
        ("認証システムの強化", True, "security"),
        
        # 強制適用
        ("elder flowでユーザー管理機能を作成", True, "force"),
        ("エルダーフローでタスクを実行", True, "force"),
        
        # 適用されないケース
        ("ドキュメントを更新してください", False, "no_apply"),
        ("会議の資料を準備", False, "no_apply"),
    ]
    
    print("🧪 Elder Flow自動適用メカニズムテスト開始...")
    print("")
    
    passed = 0
    total = len(test_cases)
    
    for input_text, should_apply, category in test_cases:
        print(f"テスト: \"{input_text}\"")
        print(f"  カテゴリ: {category}")
        print(f"  期待: {'適用' if should_apply else '非適用'}")
        
        try:
            result = await integration.auto_apply_elder_flow(input_text)
            applied = result is not None
            
            if applied == should_apply:
                print(f"  結果: ✅ 成功 {'(タスクID: ' + result + ')' if result else ''}")
                passed += 1
            else:
                print(f"  結果: ❌ 失敗 (期待と異なる結果)")
        except Exception as e:
            print(f"  結果: ❌ エラー: {e}")
        
        print("")
    
    print(f"📊 テスト結果: {passed}/{total} 成功 ({passed/total*100:0.0f}%)")
    
    if passed == total:
        print("🎉 Elder Flow自動適用メカニズムは完璧に動作しています！")
    else:
        print("⚠️ いくつかのテストケースで問題が発生しました")

if __name__ == "__main__":
    asyncio.run(test_auto_apply())