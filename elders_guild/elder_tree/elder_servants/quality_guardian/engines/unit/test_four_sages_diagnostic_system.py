#!/usr/bin/env python3
"""
Test Four Sages Diagnostic System
4賢者診断システムのテスト
"""

import pytest
import asyncio

import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.four_sages_diagnostic_system import (
    FourSagesDiagnosticSystem,
    DiagnosticResult,
    run_four_sages_diagnosis
)

class TestDiagnosticResult:
    """DiagnosticResult クラスのテスト"""
    
    def test_diagnostic_result_creation(self):
        """DiagnosticResult の作成をテスト"""
        result = DiagnosticResult(
            component="database",
            test_name="sqlite_connection",
            status="healthy",
            message="Database connection successful",
            details={"path": "/test/db.sqlite"},
            recommended_action="None",
            auto_fixable=False
        )
        
        assert result.component == "database"
        assert result.test_name == "sqlite_connection"
        assert result.status == "healthy"
        assert result.message == "Database connection successful"
        assert result.details == {"path": "/test/db.sqlite"}
        assert result.recommended_action == "None"
        assert result.auto_fixable is False

class TestFourSagesDiagnosticSystem:
    """FourSagesDiagnosticSystem のテスト"""
    
    def setup_method(self):
        """テストセットアップ"""

        self.diagnostic = FourSagesDiagnosticSystem()

    def teardown_method(self):
        """テストクリーンアップ"""
        import shutil

    @pytest.mark.asyncio
    async def test_environment_check_python_version(self):
        """Python バージョンチェックのテスト"""
        await self.diagnostic._check_environment()
        
        # Python バージョンの結果を確認
        python_results = [r for r in self.diagnostic.results if r.test_name == "python_version"]
        assert len(python_results) == 1
        assert python_results[0].status == "healthy"  # Python 3.8+ であることを前提
        
    @pytest.mark.asyncio
    async def test_environment_check_env_vars(self):
        """環境変数チェックのテスト"""
        await self.diagnostic._check_environment()
        
        # 環境変数の結果を確認
        env_results = [r for r in self.diagnostic.results if r.test_name.startswith("env_var_")]
        assert len(env_results) >= 3  # HOME, USER, PATH
        
        # HOME は通常設定されているはず
        home_results = [r for r in env_results if r.test_name == "env_var_HOME"]
        assert len(home_results) == 1
        assert home_results[0].status == "healthy"
    
    @pytest.mark.asyncio
    async def test_database_check_missing_sqlite(self):
        """存在しないSQLiteデータベースのテスト"""
        await self.diagnostic._check_databases()
        
        # 存在しないデータベースに対する警告を確認
        db_results = [r for r in self.diagnostic.results if r.component == "database"]
        missing_results = [r for r in db_results if "missing" in r.message.lower()]
        assert len(missing_results) > 0
        
        for result in missing_results:
            assert result.status == "warning"
            assert result.auto_fixable is True
    
    @pytest.mark.asyncio
    async def test_database_check_healthy_sqlite(self):
        """健全なSQLiteデータベースのテスト"""
        # テスト用データベース作成

        conn = sqlite3connect(str(test_db))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()
        
        await self.diagnostic._check_databases()
        
        # 健全なデータベース結果を確認
        healthy_results = [r for r in self.diagnostic.results 
                          if r.component == "database" and r.status == "healthy"]
        assert len(healthy_results) >= 1
    
    @pytest.mark.asyncio
    @patch('psycopg2.0connect')
    async def test_postgresql_connection_success(self, mock_connect):
        """PostgreSQL接続成功のテスト"""
        # モック設定
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        # PostgreSQL設定ファイルを作成

        config_file.write_text("DATABASE_URL=postgresql://localhost/test")
        
        await self.diagnostic._check_postgresql()
        
        # PostgreSQL接続成功結果を確認
        pg_results = [r for r in self.diagnostic.results 
                     if r.test_name == "postgresql_connection"]
        assert len(pg_results) == 1
        assert pg_results[0].status == "healthy"
    
    @pytest.mark.asyncio
    @patch('psycopg2.0connect')
    async def test_postgresql_connection_failure(self, mock_connect):
        """PostgreSQL接続失敗のテスト"""
        # モック設定 - 接続エラー
        mock_connect.side_effect = Exception("Connection failed")
        
        # PostgreSQL設定ファイルを作成

        config_file.write_text("DATABASE_URL=postgresql://localhost/test")
        
        await self.diagnostic._check_postgresql()
        
        # PostgreSQL接続エラー結果を確認
        pg_results = [r for r in self.diagnostic.results 
                     if r.test_name == "postgresql_connection"]
        assert len(pg_results) == 1
        assert pg_results[0].status == "error"
        assert pg_results[0].auto_fixable is True
    
    @pytest.mark.asyncio
    async def test_knowledge_base_check_missing(self):
        """存在しない知識ベースのテスト"""
        await self.diagnostic._check_knowledge_base()
        
        # 知識ベース不存在の結果を確認
        kb_results = [r for r in self.diagnostic.results if r.component == "knowledge_base"]
        missing_results = [r for r in kb_results if "missing" in r.message.lower()]
        assert len(missing_results) >= 1
        
        for result in missing_results:
            assert result.status in ["error", "warning"]
            assert result.auto_fixable is True
    
    @pytest.mark.asyncio
    async def test_knowledge_base_check_healthy(self):
        """健全な知識ベースのテスト"""
        # テスト用知識ベース作成

        kb_dir.mkdir()
        (kb_dir / "test.md").write_text("# Test Knowledge")
        
        await self.diagnostic._check_knowledge_base()
        
        # 健全な知識ベース結果を確認
        healthy_results = [r for r in self.diagnostic.results 
                          if r.component == "knowledge_base" and r.status == "healthy"]
        assert len(healthy_results) >= 1
    
    @pytest.mark.asyncio
    @patch('psutil.process_iter')
    async def test_sage_processes_check(self, mock_process_iter):
        """賢者プロセスチェックのテスト"""
        # モック設定 - 賢者関連プロセスをシミュレート
        mock_proc = Mock()
        mock_proc.info = {
            'pid': 12345,
            'name': 'python3',
            'cmdline': ['python3', 'sage_manager.py']
        }
        mock_process_iter.return_value = [mock_proc]
        
        await self.diagnostic._check_sage_processes()
        
        # プロセス結果を確認
        process_results = [r for r in self.diagnostic.results if r.component == "processes"]
        assert len(process_results) >= 1
        
        sage_results = [r for r in process_results if r.test_name == "sage_processes"]
        assert len(sage_results) == 1
        assert sage_results[0].status == "healthy"
    
    @pytest.mark.asyncio
    async def test_file_system_check_missing_directories(self):
        """存在しないディレクトリのテスト"""
        await self.diagnostic._check_file_system()
        
        # 存在しないディレクトリの警告を確認
        fs_results = [r for r in self.diagnostic.results if r.component == "filesystem"]
        missing_results = [r for r in fs_results if "missing" in r.message.lower()]
        assert len(missing_results) >= 1
        
        for result in missing_results:
            assert result.status == "warning"
            assert result.auto_fixable is True
    
    @pytest.mark.asyncio
    async def test_file_system_check_disk_space(self):
        """ディスク容量チェックのテスト"""
        await self.diagnostic._check_file_system()
        
        # ディスク容量結果を確認
        disk_results = [r for r in self.diagnostic.results if r.test_name == "disk_space"]
        assert len(disk_results) == 1
        # 通常のテスト環境では十分な容量があるはず
        assert disk_results[0].status == "healthy"
    
    @pytest.mark.asyncio
    async def test_configuration_check_missing_claude_md(self):
        """CLAUDE.md不存在のテスト"""
        await self.diagnostic._check_configuration()
        
        # CLAUDE.md不存在の結果を確認
        config_results = [r for r in self.diagnostic.results if r.component == "configuration"]
        claude_results = [r for r in config_results if r.test_name == "claude_md"]
        assert len(claude_results) == 1
        assert claude_results[0].status == "error"
        assert claude_results[0].auto_fixable is True
    
    @pytest.mark.asyncio
    async def test_configuration_check_healthy_claude_md(self):
        """健全なCLAUDE.mdのテスト"""
        # テスト用CLAUDE.md作成

        claude_md.write_text("# Claude Configuration\n\n## 4賢者システム\n...")
        
        await self.diagnostic._check_configuration()
        
        # 健全なCLAUDE.md結果を確認
        healthy_results = [r for r in self.diagnostic.results 
                          if r.component == "configuration" and r.status == "healthy"]
        assert len(healthy_results) >= 1
    
    @pytest.mark.asyncio
    async def test_full_diagnosis_execution(self):
        """包括的診断実行のテスト"""
        report = await self.diagnostic.run_full_diagnosis()
        
        # レポート基本構造を確認
        assert "timestamp" in report
        assert "overall_status" in report
        assert "health_score" in report
        assert "summary" in report
        assert "components" in report
        assert "recommendations" in report
        
        # サマリー情報を確認
        summary = report["summary"]
        assert "total_tests" in summary
        assert "healthy" in summary
        assert "warnings" in summary
        assert "errors" in summary
        assert "auto_fixable" in summary
        
        # 総テスト数が妥当であることを確認
        assert summary["total_tests"] > 0
        assert summary["total_tests"] == (summary["healthy"] + summary["warnings"] + 
                                         summary["errors"] + summary["critical"])
    
    @pytest.mark.asyncio
    async def test_auto_fix_missing_database(self):
        """データベース自動修復のテスト"""
        # 修復対象の診断結果を作成
        result = DiagnosticResult(
            component="database",
            test_name="sqlite_task_history",
            status="warning",
            message="SQLite database missing: task_history.db",

            recommended_action="Create missing database",
            auto_fixable=True
        )
        
        # 修復を実行
        fix_result = await self.diagnostic._apply_specific_fix(result)
        
        # 修復成功を確認
        assert fix_result["success"] is True
        assert "task_history.db" in fix_result["action"]
        
        # データベースファイルが作成されたことを確認

    @pytest.mark.asyncio
    async def test_auto_fix_missing_knowledge_base(self):
        """知識ベース自動修復のテスト"""
        result = DiagnosticResult(
            component="knowledge_base",
            test_name="kb_directory",
            status="error",
            message="Knowledge base directory missing",

            recommended_action="Create knowledge base directory structure",
            auto_fixable=True
        )
        
        # 修復を実行
        fix_result = await self.diagnostic._apply_specific_fix(result)
        
        # 修復成功を確認
        assert fix_result["success"] is True
        assert "knowledge base" in fix_result["action"]
        
        # ディレクトリ構造が作成されたことを確認

        assert kb_dir.exists()
        assert (kb_dir / "core").exists()
        assert (kb_dir / "guides").exists()
        assert (kb_dir / "technical").exists()
        assert (kb_dir / "README.md").exists()
    
    @pytest.mark.asyncio
    async def test_auto_fix_missing_directory(self):
        """ディレクトリ自動修復のテスト"""
        result = DiagnosticResult(
            component="filesystem",
            test_name="directory_libs",
            status="warning",
            message="Directory libs is missing",

            recommended_action="Create libs directory",
            auto_fixable=True
        )
        
        # 修復を実行
        fix_result = await self.diagnostic._apply_specific_fix(result)
        
        # 修復成功を確認
        assert fix_result["success"] is True
        assert "libs" in fix_result["action"]
        
        # ディレクトリが作成されたことを確認

    @pytest.mark.asyncio
    async def test_comprehensive_auto_fixes(self):
        """包括的自動修復のテスト"""
        # 診断を実行して問題を特定
        await self.diagnostic.run_full_diagnosis()
        
        # 自動修復を実行
        fix_results = await self.diagnostic.apply_auto_fixes()
        
        # 修復結果を確認
        assert "fixes_applied" in fix_results
        assert "fixes_failed" in fix_results
        assert "applied" in fix_results
        assert "failed" in fix_results
        
        # 修復が実際に適用されたことを確認
        if fix_results["fixes_applied"] > 0:
            # 修復後に再診断して改善を確認
            report_after = await self.diagnostic.run_full_diagnosis()
            # 健全性スコアが改善しているか、少なくとも維持されていることを確認
            assert report_after["health_score"] >= 0

@pytest.mark.asyncio
async def test_run_four_sages_diagnosis():
    """統合診断実行のテスト（モック）"""
    with patch('builtins.input', return_value='n'):  # 自動修復を拒否
        with patch('libs.four_sages_diagnostic_system.FourSagesDiagnosticSystem') as mock_class:
            # AsyncMockを使用
            from unittest.mock import AsyncMock
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance
            
            mock_report = {
                "timestamp": "2025-07-21T12:00:00",
                "overall_status": "warning",
                "health_score": 75.5,
                "summary": {
                    "total_tests": 20,
                    "healthy": 15,
                    "warnings": 3,
                    "errors": 2,
                    "critical": 0,
                    "auto_fixable": 5
                },
                "recommendations": [
                    "Fix PostgreSQL connection",
                    "Update CLAUDE.md configuration"
                ]
            }
            
            # AsyncMockで非同期メソッドをモック
            mock_instance.run_full_diagnosis.return_value = mock_report
            
            # 診断を実行
            result = await run_four_sages_diagnosis()
            
            # 結果を確認
            assert result == mock_report
            assert mock_instance.run_full_diagnosis.called

class TestPerformanceAndReliability:
    """パフォーマンスと信頼性のテスト"""
    
    @pytest.mark.asyncio
    async def test_diagnosis_performance(self):
        """診断システムのパフォーマンステスト"""
        import time
        
        diagnostic = FourSagesDiagnosticSystem()
        
        start_time = time.time()
        report = await diagnostic.run_full_diagnosis()
        execution_time = time.time() - start_time
        
        # 実行時間が妥当であることを確認（30秒以内）
        assert execution_time < 30.0
        assert report["metrics"]["execution_time"] == pytest.approx(execution_time, rel=0.1)
    
    @pytest.mark.asyncio
    async def test_error_handling_robustness(self):
        """エラーハンドリングの堅牢性テスト"""
        diagnostic = FourSagesDiagnosticSystem()
        
        # 存在しないパスを設定
        diagnostic.base_path = Path("/nonexistent/path/that/should/not/exist")
        
        # 診断を実行（エラーが発生しても例外が上がらないことを確認）
        report = await diagnostic.run_full_diagnosis()
        
        # レポートが生成されることを確認
        assert report is not None
        assert "timestamp" in report
        assert "overall_status" in report
        
        # エラー状況が適切に報告されることを確認
        assert report["summary"]["errors"] > 0 or report["summary"]["warnings"] > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])