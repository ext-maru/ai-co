#!/usr/bin/env python3
"""
🧪 D01 - CodeCrafter テストスイート

Python実装専門サーバントのTDDテストケース
Issue #70: ドワーフ工房前半実装
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from elders_guild.elder_tree.elder_servants.base.specialized_servants import DwarfServant
from elders_guild.elder_tree.elder_servants.base.elder_servant import (
    ServantCapability, ServantRequest, ServantResponse, 
    TaskStatus, TaskPriority, TaskResult
)
from elders_guild.elder_tree.core.elders_legacy import enforce_boundary


class TestCodeCrafter:
    """D01 - CodeCrafter テストスイート"""
    
    @pytest.fixture
    def code_crafter(self):
        """CodeCrafter実装のフィクスチャ"""
        # 実装クラスはまだ存在しないため、モック実装を作成
        from elders_guild.elder_tree.elder_servants.dwarf_workshop.code_crafter import CodeCrafter
        return CodeCrafter()
    
    @pytest.fixture
    def sample_code_request(self):
        """Python実装リクエストのサンプル"""
        return ServantRequest(
            task_id="code_001",
            task_type="python_implementation",
            priority=TaskPriority.HIGH,
            payload={
                "function_name": "calculate_fibonacci",
                "description": "フィボナッチ数列のn番目を計算する関数",
                "parameters": [
                    {"name": "n", "type": "int", "description": "計算したい位置"}
                ],
                "return_type": "int",
                "requirements": [
                    "再帰ではなく反復的に実装する",
                    "0以下の値に対してはValueErrorを発生させる",
                    "型ヒントを含める"
                ]
            },
            context={"user": "test_user", "project": "math_utils"}
        )
    
    # ========== 基本機能テスト ==========
    
    def test_code_crafter_inheritance(self, code_crafter):
        """CodeCrafterがDwarfServantを継承していることを確認"""
        assert isinstance(code_crafter, DwarfServant)
        assert code_crafter.category.value == "dwarf"
        assert code_crafter.specialization == "python_implementation"
    
    def test_code_crafter_capabilities(self, code_crafter):
        """CodeCrafterの専門能力を確認"""
        capabilities = code_crafter.get_capabilities()
        
        # 期待される能力
        expected_capabilities = [
            "function_generation",
            "class_generation", 
            "module_generation",
            "type_annotation",
            "docstring_generation",
            "code_refactoring"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
    
    @pytest.mark.asyncio
    async def test_function_generation_success(self, code_crafter, sample_code_request):
        """関数生成の成功ケース"""
        response = await code_crafter.execute_with_quality_gate(sample_code_request)
        
        assert response.status == TaskStatus.COMPLETED
        assert response.quality_score >= 95.0  # Iron Will基準
        
        # 生成されたコードの検証
        generated_code = response.result_data.get("code")
        assert generated_code is not None
        assert "def calculate_fibonacci" in generated_code
        assert "-> int:" in generated_code  # 型ヒント
        
        # CodeCrafterの実際の出力に基づく検証
        assert response.result_data.get("name") == "calculate_fibonacci"
        assert response.result_data.get("type") == "function"
        assert response.result_data.get("line_count", 0) > 0
    
    @pytest.mark.asyncio
    async def test_class_generation(self, code_crafter):
        """クラス生成テスト"""
        class_request = ServantRequest(
            task_id="code_002",
            task_type="class_generation",
            priority=TaskPriority.HIGH,
            payload={
                "class_name": "MathCalculator",
                "description": "数学計算を行うクラス",
                "methods": [
                    {
                        "name": "add",
                        "parameters": [{"name": "a", "type": "float"}, {"name": "b", "type": "float"}],
                        "return_type": "float",
                        "description": "二つの数値を加算"
                    },
                    {
                        "name": "multiply", 
                        "parameters": [{"name": "a", "type": "float"}, {"name": "b", "type": "float"}],
                        "return_type": "float",
                        "description": "二つの数値を乗算"
                    }
                ],
                "inheritance": None,
                "attributes": [
                    {"name": "precision", "type": "int", "default": "2"}
                ]
            }
        )
        
        response = await code_crafter.execute_with_quality_gate(class_request)
        
        assert response.status == TaskStatus.COMPLETED
        assert response.quality_score >= 95.0
        
        generated_code = response.result_data.get("code")
        assert "class MathCalculator:" in generated_code
        assert "def add(" in generated_code
        assert "def multiply(" in generated_code
        assert "self.precision" in generated_code
    
    @pytest.mark.asyncio
    async def test_module_generation(self, code_crafter):
        """モジュール生成テスト"""
        module_request = ServantRequest(
            task_id="code_003",
            task_type="module_generation",
            priority=TaskPriority.MEDIUM,
            payload={
                "module_name": "string_utils",
                "description": "文字列操作ユーティリティモジュール",
                "functions": [
                    {
                        "name": "reverse_string",
                        "parameters": [{"name": "text", "type": "str"}],
                        "return_type": "str",
                        "description": "文字列を逆順にする"
                    },
                    {
                        "name": "count_words",
                        "parameters": [{"name": "text", "type": "str"}],
                        "return_type": "int", 
                        "description": "単語数をカウント"
                    }
                ],
                "imports": ["re", "typing"],
                "constants": [
                    {"name": "DEFAULT_SEPARATOR", "value": " ", "type": "str"}
                ]
            }
        )
        
        response = await code_crafter.execute_with_quality_gate(module_request)
        
        assert response.status == TaskStatus.COMPLETED
        generated_code = response.result_data.get("code")
        
        assert "import re" in generated_code
        assert "import typing" in generated_code
        assert "DEFAULT_SEPARATOR" in generated_code
        assert "def reverse_string" in generated_code
        assert "def count_words" in generated_code
    
    # ========== エラーハンドリングテスト ==========
    
    @pytest.mark.asyncio
    async def test_invalid_request_validation(self, code_crafter):
        """無効なリクエストのバリデーション"""
        invalid_request = ServantRequest(
            task_id="",  # 無効なタスクID
            task_type="python_implementation",
            priority=TaskPriority.HIGH,
            payload={}  # 空のペイロード
        )
        
        with pytest.raises(ValueError, match="Invalid request"):
            await code_crafter.execute_with_quality_gate(invalid_request)
    
    @pytest.mark.asyncio
    async def test_unsupported_task_type(self, code_crafter):
        """サポートされていないタスクタイプ"""
        unsupported_request = ServantRequest(
            task_id="code_004",
            task_type="unsupported_type",
            priority=TaskPriority.HIGH,
            payload={"some": "data"}
        )
        
        response = await code_crafter.execute_with_quality_gate(unsupported_request)
        assert response.status == TaskStatus.FAILED
        assert "unsupported" in response.error_message.lower()
    
    # ========== 品質・パフォーマンステスト ==========
    
    @pytest.mark.asyncio
    async def test_code_quality_validation(self, code_crafter, sample_code_request):
        """生成コードの品質検証"""
        response = await code_crafter.execute_with_quality_gate(sample_code_request)
        
        # 品質メトリクス確認
        quality_metrics = response.result_data.get("quality_metrics", {})
        
        assert quality_metrics.get("syntax_valid", False) is True
        assert quality_metrics.get("has_type_hints", False) is True
        assert quality_metrics.get("has_docstring", False) is True
        assert quality_metrics.get("complexity_score", 0) <= 10  # 複雑度制限
    
    @pytest.mark.asyncio
    async def test_performance_requirements(self, code_crafter, sample_code_request):
        """パフォーマンス要件テスト"""
        import time
        
        start_time = time.time()
        response = await code_crafter.execute_with_quality_gate(sample_code_request)
        execution_time = (time.time() - start_time) * 1000
        
        # ドワーフ工房の生産性基準
        assert execution_time < 5000  # 5秒以内
        assert response.execution_time_ms < 5000
        
        # 品質基準確認
        assert response.quality_score >= 95.0
    
    @pytest.mark.asyncio
    async def test_concurrent_code_generation(self, code_crafter):
        """並行コード生成テスト"""
        requests = [
            ServantRequest(
                task_id=f"concurrent_{i}",
                task_type="function_generation",
                priority=TaskPriority.MEDIUM,
                payload={
                    "function_name": f"test_function_{i}",
                    "description": f"Test function {i}",
                    "parameters": [],
                    "return_type": "str"
                }
            )
            for i in range(3)
        ]
        
        # 並行実行
        responses = await asyncio.gather(*[
            code_crafter.execute_with_quality_gate(req) for req in requests
        ])
        
        # 全て成功
        assert len(responses) == 3
        assert all(resp.status == TaskStatus.COMPLETED for resp in responses)
        assert all(resp.quality_score >= 95.0 for resp in responses)
        
        # 生成されたコードがそれぞれ異なることを確認
        generated_codes = [resp.result_data.get("code") for resp in responses]
        assert len(set(generated_codes)) == 3  # 全て異なる
    
    # ========== 4賢者連携テスト ==========
    
    @pytest.mark.asyncio
    async def test_sage_collaboration(self, code_crafter, sample_code_request):
        """4賢者との連携テスト"""
        # ナレッジ賢者から過去の実装例を取得
        knowledge_result = await code_crafter.collaborate_with_sages(
            "knowledge", 
            {"query": "fibonacci implementation best practices"}
        )
        assert knowledge_result["success"] is True
        
        # インシデント賢者にセキュリティチェックを依頼
        incident_result = await code_crafter.collaborate_with_sages(
            "incident",
            {"code": "sample code", "check_type": "security_scan"}
        )
        assert incident_result["success"] is True
    
    # ========== 統合テスト ==========
    
    @pytest.mark.asyncio
    async def test_end_to_end_implementation_flow(self, code_crafter):
        """エンドツーエンドの実装フロー"""
        # 1.0 要件分析
        analysis_request = ServantRequest(
            task_id="e2e_001",
            task_type="requirement_analysis",
            priority=TaskPriority.HIGH,
            payload={
                "user_story": "ユーザーとして、パスワードの強度をチェックしたい",
                "acceptance_criteria": [
                    "8文字以上",
                    "大文字小文字数字特殊文字を含む",
                    "強度スコアを0-100で返す"
                ]
            }
        )
        
        analysis_response = await code_crafter.execute_with_quality_gate(analysis_request)
        assert analysis_response.status == TaskStatus.COMPLETED
        
        # 2.0 関数生成
        implementation_request = ServantRequest(
            task_id="e2e_002",
            task_type="function_generation",
            priority=TaskPriority.HIGH,
            payload={
                "function_name": "check_password_strength",
                "description": "パスワード強度をチェックする関数",
                "parameters": [
                    {"name": "password", "type": "str", "description": "チェック対象パスワード"}
                ],
                "return_type": "Dict[str, Any]",
                "requirements": analysis_response.result_data.get("technical_requirements", [])
            }
        )
        
        impl_response = await code_crafter.execute_with_quality_gate(implementation_request)
        assert impl_response.status == TaskStatus.COMPLETED
        
        # 3.0 生成されたコードの検証
        generated_code = impl_response.result_data.get("code")
        assert "def check_password_strength" in generated_code
        assert "Dict[str, Any]" in generated_code
        assert len(generated_code.split('\n')) >= 10  # 適切な長さ


if __name__ == "__main__":
    pytest.main([__file__, "-v"])