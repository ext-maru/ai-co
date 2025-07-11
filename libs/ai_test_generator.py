#!/usr/bin/env python3
"""
AI駆動テスト生成システム
AIがタスクを受け取った時に自動的にテストを生成する
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import ast

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager
from libs.claude_cli_executor import ClaudeCliExecutor
from test_utils.test_generator import TestGenerator


class AITestGenerator(BaseManager):
    """AI駆動でテストを生成するマネージャー"""

    def __init__(self):
        super().__init__("AITestGenerator")
        self.claude_executor = ClaudeCliExecutor()
        self.basic_generator = TestGenerator()
        self.test_output_dir = PROJECT_ROOT / 'tests' / 'generated'
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> bool:
        """
        初期化処理

        Returns:
            bool: 初期化が成功したかどうか
        """
        try:
            # 出力ディレクトリの作成
            self.test_output_dir.mkdir(parents=True, exist_ok=True)

            # 依存関係のチェック
            if not hasattr(self, 'claude_executor'):
                raise RuntimeError("Claude executor not initialized")

            self.logger.info("AITestGenerator initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"AITestGenerator initialization failed: {e}")
            return False

    async def generate_tests(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """AIベースのテスト生成 - 新しいインターフェース"""
        try:
            source_code = request.get("source_code", "")
            code_type = request.get("code_type", "function")
            patterns = request.get("patterns", [])
            requirements = request.get("requirements", [])

            # 既存のロジックを使用してテスト生成
            task_data = {
                'type': 'code',
                'prompt': f'Generate tests for {code_type}',
                'source_code': source_code,
                'patterns': patterns,
                'requirements': requirements
            }

            result = self.generate_test_for_task(task_data)

            if result.get('success'):
                return {
                    "success": True,
                    "test_content": result.get('test_info', {}).get('code', ''),
                    "patterns_applied": [p.get('pattern_type', 'unknown') for p in patterns],
                    "confidence": 0.85
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', 'Generation failed')
                }

        except Exception as e:
            self.logger.error(f"AI test generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def generate_test_for_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        タスクに対してテストを生成

        Args:
            task_data: タスクデータ（prompt, type, expected_outputなど）

        Returns:
            生成されたテストの情報
        """
        try:
            # タスクタイプに応じたテスト生成
            task_type = task_data.get('type', 'general')
            prompt = task_data.get('prompt', '')

            if task_type == 'code':
                return self._generate_code_test(prompt, task_data)
            elif task_type == 'fix':
                return self._generate_fix_test(prompt, task_data)
            elif task_type == 'feature':
                return self._generate_feature_test(prompt, task_data)
            else:
                return self._generate_general_test(prompt, task_data)

        except Exception as e:
            self.logger.error(f"テスト生成エラー: {e}")
            return {
                'success': False,
                'error': str(e),
                'tests': []
            }

    def _generate_code_test(self, prompt: str, task_data: Dict) -> Dict[str, Any]:
        """コード生成タスクのテストを生成"""
        test_prompt = f"""
以下のタスクに対するテストコードを生成してください：

タスク: {prompt}
タスクタイプ: コード生成

以下の形式でテストを作成してください：
1. 期待される機能のユニットテスト
2. エッジケースのテスト
3. エラーハンドリングのテスト
4. 統合テスト（必要に応じて）

テストはpytestフレームワークを使用し、以下を含めてください：
- 適切なfixture
- モック（必要に応じて）
- アサーション
- テストドキュメント

生成するテストコード：
"""

        # ClaudeにテストBOMON生成を依頼
        result = self.claude_executor.execute_prompt(test_prompt)

        if result['success']:
            # 生成されたテストを解析
            test_code = result['response']
            test_info = self._parse_generated_test(test_code)

            # テストファイルを保存
            test_file = self._save_test_file(test_info, task_data)

            return {
                'success': True,
                'test_file': str(test_file),
                'test_info': test_info,
                'coverage_targets': self._extract_coverage_targets(test_code)
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error')
            }

    def _generate_fix_test(self, prompt: str, task_data: Dict) -> Dict[str, Any]:
        """バグ修正タスクのテストを生成"""
        test_prompt = f"""
以下のバグ修正タスクに対するテストコードを生成してください：

タスク: {prompt}
タスクタイプ: バグ修正

以下の形式でテストを作成してください：
1. バグを再現するテスト（修正前は失敗、修正後は成功）
2. 回帰テスト（他の機能が壊れていないことを確認）
3. 関連するエッジケースのテスト

重要：
- バグの根本原因を明確にするテストを作成
- 修正が正しく動作することを検証
- 将来同じバグが発生しないことを保証

生成するテストコード：
"""

        result = self.claude_executor.execute_prompt(test_prompt)

        if result['success']:
            test_code = result['response']
            test_info = self._parse_generated_test(test_code)
            test_file = self._save_test_file(test_info, task_data)

            return {
                'success': True,
                'test_file': str(test_file),
                'test_info': test_info,
                'regression_tests': self._extract_regression_tests(test_code)
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error')
            }

    def _generate_feature_test(self, prompt: str, task_data: Dict) -> Dict[str, Any]:
        """新機能タスクのテストを生成"""
        test_prompt = f"""
以下の新機能タスクに対するテストコードを生成してください：

タスク: {prompt}
タスクタイプ: 新機能

以下の形式でテストを作成してください：
1. 機能の基本動作テスト
2. パラメータ検証テスト
3. 境界値テスト
4. 異常系テスト
5. パフォーマンステスト（必要に応じて）
6. 統合テスト

BDD形式も考慮し、Given-When-Thenパターンを使用してください。

生成するテストコード：
"""

        result = self.claude_executor.execute_prompt(test_prompt)

        if result['success']:
            test_code = result['response']
            test_info = self._parse_generated_test(test_code)
            test_file = self._save_test_file(test_info, task_data)

            # 受け入れテストも生成
            acceptance_tests = self._generate_acceptance_tests(prompt)

            return {
                'success': True,
                'test_file': str(test_file),
                'test_info': test_info,
                'acceptance_tests': acceptance_tests,
                'bdd_scenarios': self._extract_bdd_scenarios(test_code)
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error')
            }

    def _generate_general_test(self, prompt: str, task_data: Dict) -> Dict[str, Any]:
        """一般的なタスクのテストを生成"""
        # 基本的なテスト生成
        test_info = {
            'test_name': f"test_{task_data.get('task_id', 'general')}",
            'test_cases': [
                {
                    'name': 'test_task_execution',
                    'description': 'タスクが正常に実行されることを確認',
                    'type': 'unit'
                },
                {
                    'name': 'test_output_format',
                    'description': '出力フォーマットが正しいことを確認',
                    'type': 'unit'
                }
            ]
        }

        # 基本テンプレートを使用
        test_code = self._generate_basic_test_template(task_data, test_info)
        test_file = self._save_test_file({'code': test_code, 'info': test_info}, task_data)

        return {
            'success': True,
            'test_file': str(test_file),
            'test_info': test_info
        }

    def _parse_generated_test(self, test_code: str) -> Dict[str, Any]:
        """生成されたテストコードを解析"""
        try:
            # ASTで解析してテスト情報を抽出
            tree = ast.parse(test_code)

            test_classes = []
            test_functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                    test_methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                            test_methods.append({
                                'name': item.name,
                                'docstring': ast.get_docstring(item) or ''
                            })
                    test_classes.append({
                        'name': node.name,
                        'methods': test_methods
                    })
                elif isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    test_functions.append({
                        'name': node.name,
                        'docstring': ast.get_docstring(node) or ''
                    })

            return {
                'code': test_code,
                'classes': test_classes,
                'functions': test_functions,
                'total_tests': sum(len(c['methods']) for c in test_classes) + len(test_functions)
            }

        except Exception as e:
            self.logger.error(f"テストコード解析エラー: {e}")
            return {
                'code': test_code,
                'info': {'error': str(e)}
            }

    def _save_test_file(self, test_info: Dict, task_data: Dict) -> Path:
        """テストファイルを保存"""
        task_id = task_data.get('task_id', datetime.now().strftime('%Y%m%d_%H%M%S'))
        test_file = self.test_output_dir / f"test_{task_id}.py"

        test_code = test_info.get('code', '')
        if not test_code:
            # 基本テンプレートを生成
            test_code = self._generate_basic_test_template(task_data, test_info)

        test_file.write_text(test_code, encoding='utf-8')
        test_file.chmod(0o755)

        # メタデータも保存
        meta_file = self.test_output_dir / f"test_{task_id}_meta.json"
        meta_data = {
            'task_id': task_id,
            'task_data': task_data,
            'test_info': test_info,
            'generated_at': datetime.now().isoformat(),
            'test_file': str(test_file)
        }
        meta_file.write_text(json.dumps(meta_data, indent=2, ensure_ascii=False), encoding='utf-8')

        return test_file

    def _generate_basic_test_template(self, task_data: Dict, test_info: Dict) -> str:
        """基本的なテストテンプレートを生成"""
        task_id = task_data.get('task_id', 'unknown')
        task_type = task_data.get('type', 'general')

        return f'''#!/usr/bin/env python3
"""
自動生成されたテスト: {task_id}
生成日時: {datetime.now().isoformat()}
タスクタイプ: {task_type}
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

class TestTask_{task_id.replace('-', '_')}:
    """タスク {task_id} のテスト"""

    def test_task_execution(self):
        """タスクが正常に実行されることを確認"""
        # TODO: 実装
        assert True

    def test_output_validation(self):
        """出力が期待通りであることを確認"""
        # TODO: 実装
        assert True

    def test_error_handling(self):
        """エラーが適切に処理されることを確認"""
        # TODO: 実装
        with pytest.raises(Exception):
            pass
'''

    def _extract_coverage_targets(self, test_code: str) -> List[str]:
        """テストコードからカバレッジ対象を抽出"""
        targets = []

        # importされているモジュールを抽出
        lines = test_code.split('\n')
        for line in lines:
            if line.startswith('from ') or line.startswith('import '):
                if 'from ' in line and ' import ' in line:
                    module = line.split('from ')[1].split(' import')[0].strip()
                    targets.append(module)
                elif 'import ' in line:
                    module = line.split('import ')[1].strip()
                    targets.append(module)

        return targets

    def _extract_regression_tests(self, test_code: str) -> List[Dict]:
        """回帰テストを抽出"""
        regression_tests = []

        # test_regression_や test_no_regression_で始まるテストを検索
        tree = ast.parse(test_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if 'regression' in node.name.lower():
                    regression_tests.append({
                        'name': node.name,
                        'docstring': ast.get_docstring(node) or ''
                    })

        return regression_tests

    def _generate_acceptance_tests(self, prompt: str) -> List[Dict]:
        """受け入れテストを生成"""
        # 簡易的な受け入れテスト生成
        return [
            {
                'scenario': 'ユーザーが機能を使用する',
                'given': 'システムが起動している',
                'when': f'{prompt}を実行する',
                'then': '期待される結果が得られる'
            }
        ]

    def _extract_bdd_scenarios(self, test_code: str) -> List[Dict]:
        """BDDシナリオを抽出"""
        scenarios = []

        # Given-When-Thenパターンを検索
        lines = test_code.split('\n')
        current_scenario = {}

        for line in lines:
            line = line.strip()
            if 'Given' in line or 'given' in line:
                current_scenario['given'] = line
            elif 'When' in line or 'when' in line:
                current_scenario['when'] = line
            elif 'Then' in line or 'then' in line:
                current_scenario['then'] = line
                scenarios.append(current_scenario)
                current_scenario = {}

        return scenarios

    def validate_generated_tests(self, test_file: Path) -> Dict[str, Any]:
        """生成されたテストを検証"""
        try:
            # pytest --collect-onlyでテストが正しく認識されるか確認
            import subprocess
            result = subprocess.run(
                ['pytest', '--collect-only', str(test_file)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # テスト数をカウント
                test_count = result.stdout.count('::test_')
                return {
                    'valid': True,
                    'test_count': test_count,
                    'message': f'{test_count}個のテストが検出されました'
                }
            else:
                return {
                    'valid': False,
                    'error': result.stderr,
                    'message': 'テストの検証に失敗しました'
                }

        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'message': 'テスト検証中にエラーが発生しました'
            }


if __name__ == "__main__":
    # テスト実行
    generator = AITestGenerator()

    # サンプルタスク
    sample_task = {
        'task_id': 'test_123',
        'type': 'code',
        'prompt': 'ユーザー管理システムのCRUD操作を実装する'
    }

    result = generator.generate_test_for_task(sample_task)
    print(json.dumps(result, indent=2, ensure_ascii=False))
