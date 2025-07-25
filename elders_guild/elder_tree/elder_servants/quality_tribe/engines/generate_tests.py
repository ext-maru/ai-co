#!/usr/bin/env python3
"""
Elders Guild 自動テスト生成ツール
新規ワーカー/マネージャー作成時に自動的にテストを生成
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import EMOJI

class TestGenerator:
    """テスト自動生成クラス"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.tests_dir = self.project_root / "tests"
        self.unit_tests_dir = self.tests_dir / "unit"
        self.integration_tests_dir = self.tests_dir / "integration"

    def generate_worker_test(self, worker_file_path: Path):
        """ワーカーのテストを生成"""
        # ワーカーファイルを解析
        worker_info = self._parse_worker_file(worker_file_path)

        # テストコードを生成
        test_code = self._generate_unit_test_code(worker_info)

        # テストファイルを作成
        test_file_path = self._get_test_file_path(worker_file_path, "unit")
        test_file_path.parent.mkdir(parents=True, exist_ok=True)
        test_file_path.write_text(test_code)

        print(f"{EMOJI['success']} テストを生成しました: {test_file_path}")

        # 統合テストに追加
        self._add_to_integration_test(worker_info)

        return test_file_path

    def _parse_worker_file(self, file_path: Path) -> dict:
        """ワーカーファイルを解析して情報を抽出"""
        content = file_path.read_text()

        # クラス名を抽出
        class_match = re.search(r"class\s+(\w+)\s*\(", content)
        class_name = class_match.group(1) if class_match else "UnknownWorker"

        # ワーカータイプを推測
        if "BaseWorker" in content:
            base_class = "BaseWorker"
            component_type = "worker"
        elif "BaseManager" in content:
            base_class = "BaseManager"
            component_type = "manager"
        else:
            base_class = "object"
            component_type = "unknown"

        # worker_typeを抽出
        worker_type_match = re.search(r'worker_type\s*=\s*[\'"](\w+)[\'"]', content)
        worker_type = worker_type_match.group(1) if worker_type_match else "unknown"

        return {
            "file_path": file_path,
            "class_name": class_name,
            "base_class": base_class,
            "component_type": component_type,
            "worker_type": worker_type,
            "module_path": self._get_module_path(file_path),
        }

    def _get_module_path(self, file_path: Path) -> str:
        """ファイルパスからモジュールパスを生成"""
        relative_path = file_path.relative_to(self.project_root)
        module_path = str(relative_path.with_suffix("")).replace(os.sep, ".")
        return module_path

    def _get_test_file_path(self, source_file_path: Path, test_type: str) -> Path:
        """テストファイルのパスを生成"""
        relative_path = source_file_path.relative_to(self.project_root)
        test_dir = (
            self.unit_tests_dir if test_type == "unit" else self.integration_tests_dir
        )

        # ディレクトリ構造を保持
        if "workers" in relative_path.parts:
            test_subdir = test_dir / "workers"
        elif "libs" in relative_path.parts:
            test_subdir = test_dir / "libs"
        elif "core" in relative_path.parts:
            test_subdir = test_dir / "core"
        else:
            test_subdir = test_dir

        test_file_name = f"test_{source_file_path.stem}.py"
        return test_subdir / test_file_name

    def _generate_unit_test_code(self, worker_info: dict) -> str:
        """ユニットテストコードを生成"""

"""
{class_name}のユニットテスト
自動生成日時: {timestamp}
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
import json

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from {module_path} import {class_name}

class Test{class_name}:
    """{class_name}のテストクラス"""

    @pytest.fixture
    def mock_dependencies(self):
        """依存関係のモック"""
        with patch('pika.BlockingConnection') as mock_conn, \
                patch('{module_path}.get_config') as mock_config:

            # 設定のモック
            mock_config.return_value = MagicMock(
                worker=MagicMock(
                    default_model='claude-sonnet-4-20250514',
                    timeout=300
                )
            )

            yield {{
                'connection': mock_conn,
                'config': mock_config
            }}

    @pytest.fixture
    def {instance_name}(self, mock_dependencies):
        """テスト用{component_type}インスタンス"""
        instance = {class_name}()
        return instance

    def test_initialization(self, mock_dependencies):
        """初期化が正常に行われることを確認"""
        # 実行
        instance = {class_name}()

        # 検証
        assert instance is not None
        {worker_type_assertion}

    def test_process_message_success(self, {instance_name}):
        """メッセージ処理が成功することを確認"""
        # テストデータ
        test_body = json.dumps({{
            'task_id': 'test_123',
            'data': 'test data'
        }})

        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag='test-tag')
        mock_properties = MagicMock()

        # 実行
        {instance_name}.process_message(
            mock_channel, mock_method, mock_properties, test_body
        )

        # 検証
        mock_channel.basic_ack.assert_called_with(delivery_tag='test-tag')

    def test_error_handling(self, {instance_name}):
        """エラーハンドリングが適切に動作することを確認"""
        # 不正なデータ
        invalid_body = "Invalid JSON {{"

        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag='test-tag')

        # エラーが適切に処理されることを確認
        {instance_name}.process_message(
            mock_channel, mock_method, None, invalid_body
        )

        # エラーでもACKが送信されることを確認
        mock_channel.basic_ack.assert_called()

    @patch('libs.slack_notifier.SlackNotifier')
    def test_slack_notification(self, mock_slack, {instance_name}):
        """Slack通知が送信されることを確認"""
        mock_slack_instance = MagicMock()
        mock_slack.return_value = mock_slack_instance

        # 処理実行（実装に応じて調整）
        # {instance_name}.some_method_that_sends_slack()

        # 必要に応じてSlack通知の検証を追加
        pass

    def test_health_check(self, {instance_name}):
        """ヘルスチェックが正しい情報を返すことを確認"""
        # 実行
        health = {instance_name}.health_check()

        # 検証
        assert health['status'] == 'healthy'
        assert 'worker_type' in health
        assert 'stats' in health

    # - 特定のビジネスロジックのテスト
    # - 外部サービス連携のテスト
    # - パフォーマンステスト
    # - エッジケースのテスト

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''

        # テンプレート変数を置換
        worker_type_assertion = (
            f"assert instance.worker_type == '{worker_info['worker_type']}'"
            if worker_info["worker_type"] != "unknown"

        )

        instance_name = worker_info["class_name"].lower()
        if instance_name.endswith("worker"):
            instance_name = instance_name[:-6] + "_instance"
        elif instance_name.endswith("manager"):
            instance_name = instance_name[:-7] + "_instance"
        else:
            instance_name = instance_name + "_instance"

            class_name=worker_info["class_name"],
            timestamp=datetime.now().isoformat(),
            module_path=worker_info["module_path"],
            instance_name=instance_name,
            component_type=worker_info["component_type"],
            worker_type_assertion=worker_type_assertion,
        )

    def _add_to_integration_test(self, worker_info: dict):
        """統合テストに新しいワーカーのテストを追加"""
        integration_file = self.integration_tests_dir / "test_worker_chain.py"

        if not integration_file.exists():
            # 統合テストファイルを作成
            self._create_integration_test_file(integration_file)

        print(
            f"{EMOJI['info']} 統合テストへの追加は手動で行ってください: {integration_file}"
        )

    def _create_integration_test_file(self, file_path: Path):
        """統合テストファイルを作成"""
        content = '''#!/usr/bin/env python3
"""
ワーカーチェーンの統合テスト
"""

import pytest
import json
from unittest.mock import patch, MagicMock

# テストコードのテンプレート
'''
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

    def scan_and_generate_missing_tests(self):
        """プロジェクト内のワーカー/マネージャーをスキャンして欠落しているテストを生成"""
        print(f"{EMOJI['search']} テストが欠落しているファイルを検索中...")

        # ワーカーディレクトリをスキャン
        workers_dir = self.project_root / "workers"
        for worker_file in workers_dir.glob("*_worker.py"):
            test_file = self._get_test_file_path(worker_file, "unit")
            if not test_file.exists():
                print(f"{EMOJI['warning']} テストが見つかりません: {worker_file.name}")
                self.generate_worker_test(worker_file)

        # マネージャーディレクトリをスキャン
        libs_dir = self.project_root / "libs"
        for manager_file in libs_dir.glob("*_manager.py"):
            test_file = self._get_test_file_path(manager_file, "unit")
            if not test_file.exists():
                print(f"{EMOJI['warning']} テストが見つかりません: {manager_file.name}")
                self.generate_worker_test(manager_file)

def main():
    """メイン関数"""
    generator = TestGenerator()

    if len(sys.argv) > 1:
        # 特定のファイルのテストを生成
        file_path = Path(sys.argv[1])
        if file_path.exists():
            generator.generate_worker_test(file_path)
        else:
            print(f"{EMOJI['error']} ファイルが見つかりません: {file_path}")
    else:
        # 欠落しているテストをすべて生成
        generator.scan_and_generate_missing_tests()

    print(f"\n{EMOJI['rocket']} テスト生成が完了しました！")
    print(f"{EMOJI['info']} 生成されたテストを実行: pytest tests/")

if __name__ == "__main__":
    main()
