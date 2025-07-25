#!/usr/bin/env python3
"""
イシューローダーのエラーハンドリングテスト
テンプレートエラーのリトライ動作を確認
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.integrations.github.auto_issue_processor import AutoIssueProcessor

from libs.auto_issue_processor_error_handling import ErrorType, AutoIssueProcessorErrorHandler, ErrorContext
from github import Github

# テスト用の壊れたテンプレートを作成

    """意図的に構文エラーのあるテンプレートを作成"""

\"\"\"

\"\"\"

class {{ class_name }}:
    def __init__(self):
        pass
    
    {% if something %}
    def method1(self):
        pass
    
    # Missing endif here!
    
    else:  # This else has no matching if in generated code
        def method2(self):
            pass
"""

    """テンプレートエラーのリトライ動作をテスト"""
    print("="*80)
    print("🧪 テンプレートエラーリトライテスト")
    print("="*80)
    
    # 壊れたテンプレートを作成

    # エラーハンドラーの初期化
    error_handler = AutoIssueProcessorErrorHandler()
    
    # リトライ回数をカウントするための変数
    retry_count = 0
    original_handle_error = error_handler.handle_error
    
    async def counting_handle_error(error, context, operation_func, *args, **kwargs):
        nonlocal retry_count
        """counting_handle_errorを処理"""
        print(f"\n🔄 リトライ {retry_count + 1}回目")
        retry_count += 1
        return await original_handle_error(error, context, operation_func, *args, **kwargs)
    
    # モックIssue作成
    mock_issue = MagicMock()
    mock_issue.number = 999
    mock_issue.title = "Test Issue for Error Handling"

    mock_issue.labels = []

    processor = AutoIssueProcessor()

    # エラーハンドラーをパッチ
    error_handler.handle_error = counting_handle_error
    
    # テンプレートマネージャーの技術スタック検出を強制的に壊れたテンプレートに向ける

    print("\n📋 テストケース: 壊れたテンプレートでコード生成")
    print(f"  - Issue番号: {mock_issue.number}")

    # get_max_retriesは静的メソッドなので、RetryStrategyから取得
    from libs.auto_issue_processor_error_handling import RetryStrategy

    start_time = time.time()
    
    try:
        # コンテキスト準備
        context = {
            'issue_number': mock_issue.number,
            'issue_title': mock_issue.title,
            'issue_body': mock_issue.body,
            'class_name': f'Issue{mock_issue.number}Implementation',
            'module_name': f'issue_{mock_issue.number}_solution',
            'something': True,  # if条件を満たす
            'requirements': {'imports': [], 'classes': [], 'functions': []}
        }
        
        # エラーコンテキスト
        error_context = ErrorContext(

            operation="generate_code",
            issue_number=mock_issue.number
        )
        
        # テンプレート生成を試行（エラーが発生するはず）
        async def generate_with_error():
            """generate_with_errorを生成"""

                context=context,
                use_enhanced=False
            )
        
        # エラーハンドラー経由で実行
        result = await error_handler.handle_error(

            error_context,
            generate_with_error
        )
        
        print(f"\n❌ 予期しない成功: {result}")
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n✅ 期待通りエラーが発生")
        print(f"  - エラータイプ: {type(e).__name__}")
        print(f"  - エラーメッセージ: {str(e)[:100]}...")
        print(f"  - 総リトライ回数: {retry_count}")
        print(f"  - 処理時間: {elapsed_time:0.2f}秒")
        
        # リトライ遅延の確認
        if retry_count > 1:
            avg_delay = elapsed_time / retry_count
            print(f"  - 平均リトライ間隔: {avg_delay:0.2f}秒")
    
    finally:
        # クリーンアップ
        import shutil

        print("\n🧹 テスト用テンプレートをクリーンアップ")
    
    # 結果サマリー
    print("\n" + "="*80)
    print("📊 テスト結果サマリー")
    print("="*80)
    print(f"  - 設定されたリトライ回数: 5")
    print(f"  - 実際のリトライ回数: {retry_count}")
    print(f"  - リトライ動作: {'✅ 正常' if retry_count > 0 else '❌ 異常'}")
    
    return {
        'configured_retries': 5,
        'actual_retries': retry_count,
        'success': retry_count > 0
    }

async def main():
    """メインテスト実行"""

    # 結果をJSON保存
    output_file = Path("error_handling_test_result.json")
    output_file.write_text(json.dumps(result, indent=2))
    print(f"\n📄 テスト結果保存: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())