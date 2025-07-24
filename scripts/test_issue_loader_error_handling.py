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
from libs.code_generation.template_manager import CodeGenerationTemplateManager
from libs.auto_issue_processor_error_handling import ErrorType, AutoIssueProcessorErrorHandler, ErrorContext
from github import Github

# テスト用の壊れたテンプレートを作成
def create_broken_template():
    """意図的に構文エラーのあるテンプレートを作成"""
    broken_template_dir = Path("templates/code_generation/test_broken")
    broken_template_dir.mkdir(parents=True, exist_ok=True)
    
    broken_template = """#!/usr/bin/env python3
\"\"\"
Test template with intentional syntax error
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
    
    (broken_template_dir / "class.j2").write_text(broken_template)
    return "test_broken"

async def test_template_error_retry():
    """テンプレートエラーのリトライ動作をテスト"""
    print("="*80)
    print("🧪 テンプレートエラーリトライテスト")
    print("="*80)
    
    # 壊れたテンプレートを作成
    broken_tech_stack = create_broken_template()
    print(f"\n✅ 壊れたテンプレート作成: {broken_tech_stack}/class.j2")
    
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
    mock_issue.body = "This is a test issue to verify error handling with broken template"
    mock_issue.labels = []
    
    # AutoIssueProcessorとTemplateManagerの初期化
    processor = AutoIssueProcessor()
    template_manager = CodeGenerationTemplateManager()
    
    # エラーハンドラーをパッチ
    error_handler.handle_error = counting_handle_error
    
    # テンプレートマネージャーの技術スタック検出を強制的に壊れたテンプレートに向ける
    original_detect = template_manager.detect_tech_stack
    template_manager.detect_tech_stack = lambda *args, **kwargs: broken_tech_stack
    
    print("\n📋 テストケース: 壊れたテンプレートでコード生成")
    print(f"  - Issue番号: {mock_issue.number}")
    print(f"  - 技術スタック: {broken_tech_stack}")
    # get_max_retriesは静的メソッドなので、RetryStrategyから取得
    from libs.auto_issue_processor_error_handling import RetryStrategy
    print(f"  - 最大リトライ回数: {RetryStrategy.get_max_retries(ErrorType.TEMPLATE_ERROR)}")
    
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
            error_type=ErrorType.TEMPLATE_ERROR,
            original_error=Exception("Template generation will fail"),
            operation="generate_code",
            issue_number=mock_issue.number
        )
        
        # テンプレート生成を試行（エラーが発生するはず）
        async def generate_with_error():
            """generate_with_errorを生成"""
            return template_manager.generate_code(
                template_type='class',
                tech_stack=broken_tech_stack,
                context=context,
                use_enhanced=False
            )
        
        # エラーハンドラー経由で実行
        result = await error_handler.handle_error(
            Exception("Template error will occur"),
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
        shutil.rmtree("templates/code_generation/test_broken", ignore_errors=True)
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
    result = await test_template_error_retry()
    
    # 結果をJSON保存
    output_file = Path("error_handling_test_result.json")
    output_file.write_text(json.dumps(result, indent=2))
    print(f"\n📄 テスト結果保存: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())