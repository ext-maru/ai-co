"""
🔨 CodeCrafterServant テストスイート - TDD実装

コード生成・修正専門のエルダーサーバントのテスト
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from libs.elder_servants.base.unified_elder_servant import (
    CodeCrafterServant, ServantTask, ServantStatus
)


class TestCodeCrafterServant:
    """🔨 CodeCrafterServant テストクラス"""
    
    @pytest.fixture
    def code_crafter(self):
        """CodeCrafterServantインスタンス"""
        return CodeCrafterServant()
    
    @pytest.fixture
    def temp_dir(self):
        """テスト用一時ディレクトリ"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_code_crafter_initialization(self, code_crafter):
        """初期化テスト"""
        assert code_crafter.servant_id == "code_crafter_001"
        assert code_crafter.name == "CodeCrafter"
        assert code_crafter.specialization == "code_generation"
        assert code_crafter.status == ServantStatus.IDLE
        assert len(code_crafter.capabilities) == 1
        assert code_crafter.capabilities[0].name == "code_generation"
    
    @pytest.mark.asyncio
    async def test_generate_python_function(self, code_crafter):
        """Python関数生成テスト"""
        task = ServantTask(
            id="task_001",
            name="generate_function",
            description="数値を2倍にする関数を生成",
            priority="high"
        )
        
        result = await code_crafter.execute_task(task)
        
        assert result["status"] == "completed"
        assert "code" in result
        assert "def " in result["code"]
        assert "return" in result["code"]
        assert result["language"] == "python"
        assert result["function_name"] is not None
    
    @pytest.mark.asyncio
    async def test_generate_class_structure(self, code_crafter):
        """クラス構造生成テスト"""
        task = ServantTask(
            id="task_002", 
            name="generate_class",
            description="Userクラスを生成（name, emailプロパティ付き）"
        )
        
        result = await code_crafter.execute_task(task)
        
        assert result["status"] == "completed"
        assert "class User" in result["code"]
        assert "def __init__" in result["code"]
        assert "self.name" in result["code"]
        assert "self.email" in result["code"]
    
    @pytest.mark.asyncio
    async def test_fix_syntax_error(self, code_crafter, temp_dir):
        """構文エラー修正テスト"""
        # 構文エラーのあるコードファイル作成
        broken_file = temp_dir / "broken.py"
        broken_file.write_text("""
def calculate(x, y
    result = x + y
    return result
""")
        
        task = ServantTask(
            id="task_003",
            name="fix_syntax",
            description=f"構文エラーを修正: {broken_file}"
        )
        
        result = await code_crafter.execute_task(task)
        
        assert result["status"] == "completed"
        assert result["fixes_applied"] > 0
        assert "def calculate(x, y):" in result["fixed_code"]
        assert "missing closing parenthesis" in result["issues_found"][0]["type"]
    
    @pytest.mark.asyncio
    async def test_add_docstring(self, code_crafter):
        """ドキュメント文字列追加テスト"""
        original_code = """
def add_numbers(a, b):
    return a + b
"""
        
        task = ServantTask(
            id="task_004",
            name="add_docstring", 
            description="関数にdocstringを追加",
            priority="medium"
        )
        
        result = await code_crafter.execute_task(task)
        
        assert result["status"] == "completed"
        assert '"""' in result["enhanced_code"]
        assert "Args:" in result["enhanced_code"]
        assert "Returns:" in result["enhanced_code"]
    
    @pytest.mark.asyncio
    async def test_refactor_code(self, code_crafter):
        """リファクタリングテスト"""
        messy_code = """
def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
    return result
"""
        
        task = ServantTask(
            id="task_005",
            name="refactor_code",
            description="コードをよりPythonicに改善"
        )
        
        result = await code_crafter.execute_task(task)
        
        assert result["status"] == "completed"
        assert "list comprehension" in result["improvements"][0]["type"]
        assert "for item in data" in result["refactored_code"]
    
    @pytest.mark.asyncio
    async def test_generate_from_template(self, code_crafter):
        """テンプレートからのコード生成テスト"""
        task = ServantTask(
            id="task_006",
            name="generate_from_template",
            description="FastAPI RESTエンドポイントを生成",
            priority="high"
        )
        
        result = await code_crafter.execute_task(task)
        
        assert result["status"] == "completed"
        assert "@app." in result["code"]  # FastAPIデコレータ
        assert "async def" in result["code"]
        assert result["template_used"] == "fastapi_endpoint"
    
    @pytest.mark.asyncio
    async def test_lint_and_format(self, code_crafter):
        """リント・フォーマットテスト"""
        unformatted_code = """
def   bad_function(  x,y  ):
    if x>0:
      return x+y
    else:
       return   0
"""
        
        task = ServantTask(
            id="task_007",
            name="lint_and_format",
            description="コードをlintしてフォーマット"
        )
        
        result = await code_crafter.execute_task(task)
        
        assert result["status"] == "completed"
        assert result["lint_issues"] > 0
        assert "def bad_function(x, y):" in result["formatted_code"]
        assert "    if x > 0:" in result["formatted_code"]
    
    @pytest.mark.asyncio
    async def test_code_analysis(self, code_crafter):
        """コード解析テスト"""
        complex_code = """
def complex_function(data):
    result = {}
    for item in data:
        if item['type'] == 'A':
            if item['value'] > 100:
                if item['status'] == 'active':
                    result[item['id']] = item['value'] * 1.5
                else:
                    result[item['id']] = item['value'] * 0.8
            else:
                result[item['id']] = item['value']
    return result
"""
        
        task = ServantTask(
            id="task_008",
            name="analyze_code",
            description="コードの複雑度と品質を分析"
        )
        
        result = await code_crafter.execute_task(task)
        
        assert result["status"] == "completed"
        assert result["complexity_score"] > 0
        assert result["nesting_level"] >= 3
        assert "high complexity" in result["recommendations"][0]
    
    @pytest.mark.asyncio
    async def test_error_handling(self, code_crafter):
        """エラーハンドリングテスト"""
        task = ServantTask(
            id="task_009",
            name="invalid_task",
            description="存在しないタスクタイプ"
        )
        
        result = await code_crafter.execute_task(task)
        
        assert result["status"] == "error"
        assert "error_message" in result
        assert "unknown task type" in result["error_message"].lower()
    
    @pytest.mark.asyncio
    async def test_task_processing_lifecycle(self, code_crafter):
        """タスク処理ライフサイクルテスト"""
        task = ServantTask(
            id="task_010",
            name="generate_function",
            description="シンプルな関数生成"
        )
        
        # 処理前の状態確認
        assert code_crafter.status == ServantStatus.IDLE
        assert code_crafter.current_task is None
        
        # タスク処理
        processed_task = await code_crafter.process_task(task)
        
        # 処理後の状態確認
        assert processed_task.status == ServantStatus.COMPLETED
        assert code_crafter.status == ServantStatus.IDLE
        assert code_crafter.current_task is None
        assert len(code_crafter.completed_tasks) == 1
        assert processed_task.result is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_task_handling(self, code_crafter):
        """並行タスク処理テスト"""
        tasks = [
            ServantTask(f"task_{i}", f"generate_function_{i}", f"関数{i}を生成")
            for i in range(3)
        ]
        
        # 並行実行
        results = await asyncio.gather(*[
            code_crafter.process_task(task) for task in tasks
        ])
        
        assert len(results) == 3
        assert all(task.status == ServantStatus.COMPLETED for task in results)
        assert len(code_crafter.completed_tasks) == 3
    
    def test_get_status(self, code_crafter):
        """状態取得テスト"""
        status = code_crafter.get_status()
        
        assert status["name"] == "CodeCrafter"
        assert status["category"] == "crafting"
        assert status["domain"] == "code"
        assert status["status"] == "idle"
        assert status["current_task"] is None
        assert status["completed_tasks_count"] == 0
    
    def test_get_task_history(self, code_crafter):
        """タスク履歴取得テスト"""
        history = code_crafter.get_task_history()
        assert isinstance(history, list)
        assert len(history) == 0  # 初期状態では空
    
    @pytest.mark.asyncio
    async def test_code_generation_with_requirements(self, code_crafter):
        """要件指定でのコード生成テスト"""
        requirements = {
            "function_name": "calculate_discount",
            "parameters": ["price", "discount_rate"],
            "return_type": "float",
            "description": "価格に割引率を適用して計算"
        }
        
        task = ServantTask(
            id="task_011",
            name="generate_with_requirements",
            description="要件に基づいてコード生成",
            priority="high"
        )
        
        result = await code_crafter.execute_task(task)
        
        assert result["status"] == "completed"
        assert "def calculate_discount" in result["code"]
        assert "price" in result["code"]
        assert "discount_rate" in result["code"]
        assert "float" in result["type_hints"]


class TestCodeCrafterIntegration:
    """🔨 CodeCrafter統合テスト"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_code_generation(self):
        """完全ワークフロー: コード生成→解析→修正→フォーマット"""
        crafter = CodeCrafterServant()
        
        # 1. コード生成
        gen_task = ServantTask("gen", "generate_function", "データ処理関数")
        gen_result = await crafter.execute_task(gen_task)
        assert gen_result["status"] == "completed"
        
        # 2. コード解析
        analysis_task = ServantTask("analysis", "analyze_code", "生成コード解析")
        analysis_result = await crafter.execute_task(analysis_task)
        assert analysis_result["status"] == "completed"
        
        # 3. 必要に応じて修正
        if analysis_result["complexity_score"] > 10:
            refactor_task = ServantTask("refactor", "refactor_code", "複雑度改善")
            refactor_result = await crafter.execute_task(refactor_task)
            assert refactor_result["status"] == "completed"
        
        # 4. 最終フォーマット
        format_task = ServantTask("format", "lint_and_format", "最終フォーマット")
        format_result = await crafter.execute_task(format_task)
        assert format_result["status"] == "completed"
        
        # 全体確認
        assert len(crafter.completed_tasks) >= 3