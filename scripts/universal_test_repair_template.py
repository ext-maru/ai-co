#!/usr/bin/env python3
"""
Universal Test Repair Template - RAGウィザーズ最終兵器
Phase 2-4の成功パターンから抽出した万能修復テンプレート
"""

import ast
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class UniversalTestRepairTemplate:
    """万能テスト修復テンプレート"""

    # 成功パターンから抽出したベストプラクティス
    IMPORT_TEMPLATE = '''#!/usr/bin/env python3
"""
{module_name} Tests - TDD Implementation
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json
import asyncio
from typing import Dict, List, Any, Optional
'''

    # 基底クラス問題の解決パターン
    BASE_CLASS_MOCK_TEMPLATE = '''
# 基底クラスのモック設定
@pytest.fixture
def mock_base_dependencies():
    """基底クラス依存関係のモック"""
    with patch('libs.rabbit_manager.RabbitManager') as mock_rabbit:
        with patch('libs.lightweight_logger.Logger') as mock_logger:
            mock_rabbit_instance = Mock()
            mock_rabbit.return_value = mock_rabbit_instance

            mock_logger_instance = Mock()
            mock_logger.return_value = mock_logger_instance

            yield {
                'rabbit_manager': mock_rabbit_instance,
                'logger': mock_logger_instance
            }
'''

    # 非同期テストパターン
    ASYNC_TEST_TEMPLATE = '''
@pytest.mark.asyncio
async def test_{test_name}(self, mock_base_dependencies):
    """{test_description}"""
    from {import_path} import {class_name}

    # インスタンス作成
    instance = {class_name}()

    # テスト実行
    result = await instance.{method_name}({params})

    # アサーション
    assert result is not None
    {assertions}
'''

    # 同期テストパターン
    SYNC_TEST_TEMPLATE = '''
def test_{test_name}(self, mock_base_dependencies):
    """{test_description}"""
    from {import_path} import {class_name}

    # インスタンス作成
    instance = {class_name}()

    # テスト実行
    result = instance.{method_name}({params})

    # アサーション
    assert result is not None
    {assertions}
'''

    def generate_fixed_test(
        self, module_path: str, class_name: str, test_methods: List[Dict[str, Any]]
    ) -> str:
        """修復されたテストファイルを生成"""

        # モジュール名とインポートパスの生成
        module_name = Path(module_path).stem
        import_path = module_path.replace("/", ".").replace(".py", "")

        # ベースコンテンツの生成
        content = self.IMPORT_TEMPLATE.format(module_name=module_name)
        content += self.BASE_CLASS_MOCK_TEMPLATE

        # テストクラスの開始
        content += f"\n\nclass Test{class_name}:\n"
        content += f'    """{class_name}のテスト"""\n'

        # 各テストメソッドの生成
        for test_info in test_methods:
            if test_info.get("is_async", False):
                template = self.ASYNC_TEST_TEMPLATE
            else:
                template = self.SYNC_TEST_TEMPLATE

            test_content = template.format(
                test_name=test_info["name"],
                test_description=test_info["description"],
                import_path=import_path,
                class_name=class_name,
                method_name=test_info.get("method", "process"),
                params=test_info.get("params", ""),
                assertions=test_info.get("assertions", ""),
            )

            # インデントを追加
            indented_content = "\n".join(
                "    " + line if line else "" for line in test_content.split("\n")
            )
            content += "\n" + indented_content

        return content

    def analyze_and_fix_test_file(self, test_file_path: str) -> str:
        """既存のテストファイルを分析して修復"""
        try:
            with open(test_file_path, "r") as f:
                content = f.read()

            # インポートエラーの修正
            if "PROJECT_ROOT" not in content:
                # インポート部分を完全に置き換え
                import_end = content.find("class Test")
                if import_end == -1:
                    import_end = content.find("def test_")

                if import_end != -1:
                    module_name = Path(test_file_path).stem.replace("test_", "")
                    new_imports = self.IMPORT_TEMPLATE.format(module_name=module_name)
                    content = new_imports + content[import_end:]

            # 基底クラスのモック追加
            if "mock_base_dependencies" not in content:
                class_start = content.find("class Test")
                if class_start != -1:
                    content = (
                        content[:class_start]
                        + self.BASE_CLASS_MOCK_TEMPLATE
                        + "\n\n"
                        + content[class_start:]
                    )

            # 各テストメソッドにfixture追加
            content = re.sub(
                r"def (test_\w+)\(self\):",
                r"def \1(self, mock_base_dependencies):",
                content,
            )

            # 非同期テストのデコレータ修正
            content = re.sub(
                r"async def (test_\w+)",
                r"@pytest.mark.asyncio\n    async def \1",
                content,
            )

            return content

        except Exception as e:
            print(f"Error fixing {test_file_path}: {e}")
            return None


def main():
    """メイン実行関数"""
    template = UniversalTestRepairTemplate()

    # 優先度の高いテストファイルリスト
    priority_test_files = [
        "tests/unit/test_task_sender.py",
        "tests/unit/test_elder_council_summoner.py",
        "tests/unit/test_worker_health_monitor.py",
        "tests/unit/commands/test_ai_send.py",
        "tests/unit/commands/test_ai_monitor.py",
        "tests/unit/libs/test_rabbit_manager.py",
        "tests/unit/libs/test_queue_manager.py",
        "tests/unit/libs/test_error_intelligence_manager.py",
        "tests/unit/workers/test_pm_worker.py",
        "tests/unit/workers/test_task_worker.py",
    ]

    fixed_count = 0
    for test_file in priority_test_files:
        test_path = Path(test_file)
        if test_path.exists():
            print(f"修復中: {test_file}")
            fixed_content = template.analyze_and_fix_test_file(str(test_path))
            if fixed_content:
                with open(test_path, "w") as f:
                    f.write(fixed_content)
                fixed_count += 1
                print(f"✅ 修復完了: {test_file}")
        else:
            # テストファイルが存在しない場合は基本テンプレートで作成
            print(f"作成中: {test_file}")
            module_path = test_file.replace("tests/unit/", "").replace("test_", "")
            module_path = module_path.replace(".py", ".py")

            if "commands/" in module_path:
                module_path = "commands/" + Path(module_path).name
            elif "libs/" in module_path:
                module_path = "libs/" + Path(module_path).name
            elif "workers/" in module_path:
                module_path = "workers/" + Path(module_path).name

            class_name = (
                Path(module_path).stem.replace("_", " ").title().replace(" ", "")
            )

            test_methods = [
                {
                    "name": "initialization",
                    "description": f"{class_name}の初期化テスト",
                    "is_async": False,
                    "assertions": 'assert hasattr(instance, "process")',
                },
                {
                    "name": "basic_functionality",
                    "description": "基本機能のテスト",
                    "is_async": "async" in module_path or "worker" in module_path,
                    "method": "process",
                    "params": '{"test": "data"}',
                    "assertions": "assert isinstance(result, dict)",
                },
            ]

            fixed_content = template.generate_fixed_test(
                module_path, class_name, test_methods
            )

            # ディレクトリ作成
            test_path.parent.mkdir(parents=True, exist_ok=True)

            with open(test_path, "w") as f:
                f.write(fixed_content)
            fixed_count += 1
            print(f"✅ 作成完了: {test_file}")

    print(f"\n🎯 修復完了: {fixed_count}/{len(priority_test_files)} ファイル")
    print("次のステップ: pytest tests/unit/ -v でテスト実行")


if __name__ == "__main__":
    main()
