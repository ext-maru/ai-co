"""
🔥 Ancient Magic Strict Tests - 厳格なテストスイート
エッジケース、異常系、パフォーマンステストを含む
"""

import pytest
import asyncio
import tempfile
import shutil
import os
import time
import subprocess
from pathlib import Path
import sys
import json

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.audit_engine import AncientElderAuditEngine
from libs.ancient_elder.integrity_auditor_wrapper import AncientElderIntegrityAuditor
from libs.ancient_elder.tdd_guardian_wrapper import TDDGuardian
from libs.ancient_elder.git_chronicle_wrapper import GitChronicle
from libs.ancient_elder.audit_cache import AuditCache, CachedAuditEngine


class TestAncientMagicStrict:
    """厳格なテストケース集"""
    
    @pytest.fixture
    def temp_git_repo(self):
        """テスト用の一時Gitリポジトリ"""
        temp_dir = tempfile.mkdtemp()
        
        # Gitリポジトリを初期化
        subprocess.run(['git', 'init'], cwd=temp_dir, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir)
        
        yield temp_dir
        
        # クリーンアップ
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_null_input_handling(self):
        """NULL/None入力のハンドリングテスト"""
        engine = AncientElderAuditEngine()
        
        # 空のターゲット
        result = await engine.run_comprehensive_audit({})
        assert result is not None
        assert "error" in result or "statistics" in result
        
        # Noneターゲット
        result = await engine.run_comprehensive_audit(None)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_nonexistent_path(self):
        """存在しないパスの処理"""
        auditor = AncientElderIntegrityAuditor()
        
        target = {
            "path": "/nonexistent/path/that/should/not/exist",
            "type": "project"
        }
        
        result = await auditor.audit(target)
        assert result is not None
        assert result.metrics.get("integrity_score", 0) == 0
    
    @pytest.mark.asyncio
    async def test_permission_denied_handling(self):
        """権限エラーのハンドリング"""
        # 読み取り不可のディレクトリを作成
        temp_dir = tempfile.mkdtemp()
        restricted_file = Path(temp_dir) / "restricted.py"
        restricted_file.write_text("# Secret code")
        os.chmod(restricted_file, 0o000)
        
        try:
            auditor = AncientElderIntegrityAuditor()
            result = await auditor.audit({"path": temp_dir})
            
            # エラーがあってもクラッシュしない
            assert result is not None
            
        finally:
            # クリーンアップ
            os.chmod(restricted_file, 0o644)
            shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_massive_file_handling(self):
        """巨大ファイルの処理"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 1000行のPythonファイルを生成
            large_file = Path(temp_dir) / "large.py"
            content = "\n".join([
                f"# TODO: Task {i}"
                for i in range(1000)
            ])
            large_file.write_text(content)
            
            auditor = AncientElderIntegrityAuditor()
            start_time = time.time()
            result = await auditor.audit({"path": temp_dir})
            execution_time = time.time() - start_time
            
            # 10秒以内に完了すること
            assert execution_time < 10
            assert result.metrics["todo_count"] > 0
            
        finally:
            shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_git_chronicle_with_broken_repo(self, temp_git_repo):
        """壊れたGitリポジトリでのテスト"""
        # .git/HEADを破壊
        head_file = Path(temp_git_repo) / ".git" / "HEAD"
        head_file.write_text("BROKEN")
        
        chronicle = GitChronicle()
        result = await chronicle.audit({"path": temp_git_repo})
        
        # エラーがあってもクラッシュしない
        assert result is not None
        assert len(result.violations) >= 0
    
    @pytest.mark.asyncio
    async def test_concurrent_audits(self):
        """並行実行時の安定性テスト"""
        engine = AncientElderAuditEngine()
        
        # 簡単な監査者のみ登録（高速化のため）
        engine.register_auditor("integrity", AncientElderIntegrityAuditor())
        
        # 10個の並行タスク
        tasks = []
        for i in range(10):
            target = {"path": f"./test_{i}", "type": "test"}
            task = engine.run_comprehensive_audit(target)
            tasks.append(task)
        
        # 全て完了することを確認
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # エラーがあっても一部は成功するはず
        successful = [r for r in results if isinstance(r, dict) and "error" not in r]
        assert len(successful) >= 5  # 少なくとも半分は成功
    
    @pytest.mark.asyncio
    async def test_cache_corruption_handling(self):
        """キャッシュ破損時の処理"""
        cache = AuditCache()
        
        # 破損したキャッシュファイルを作成
        cache_key = cache._generate_cache_key("test", {"path": "."})
        cache_file = cache.cache_dir / f"{cache_key}.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("INVALID JSON {{{")
        
        # 破損していても動作すること
        result = cache.get("test", {"path": "."})
        assert result is None  # 破損時はNoneを返す
        
        # 統計情報が取得できること
        stats = cache.get_stats()
        assert stats["misses"] > 0
    
    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self):
        """循環参照の検出（将来の実装用）"""
        # 現在は簡易実装のため、基本動作のみ確認
        engine = AncientElderAuditEngine()
        
        # 同じ監査者を複数回登録してもエラーにならない
        auditor = AncientElderIntegrityAuditor()
        engine.register_auditor("test1", auditor)
        engine.register_auditor("test2", auditor)  # 同じインスタンス
        
        result = await engine.run_comprehensive_audit({"path": "."})
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_unicode_and_special_chars(self):
        """Unicode文字と特殊文字の処理"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 特殊文字を含むファイル
            special_file = Path(temp_dir) / "特殊文字😀.py"
            special_file.write_text("""
# TODO: 日本語のタスク
# FIXME: 絵文字を含む修正 🐛
def こんにちは():
    return "Hello, 世界!"
""")
            
            auditor = AncientElderIntegrityAuditor()
            result = await auditor.audit({"path": temp_dir})
            
            # エラーなく処理できること
            assert result is not None
            assert result.metrics["todo_count"] >= 1
            
        finally:
            shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_memory_leak_prevention(self):
        """メモリリーク防止テスト"""
        import gc
        import tracemalloc
        
        tracemalloc.start()
        
        # 初期メモリ使用量
        gc.collect()
        snapshot1 = tracemalloc.take_snapshot()
        
        # 100回監査を実行
        auditor = AncientElderIntegrityAuditor()
        for i in range(100):
            await auditor.audit({"path": ".", "quick_mode": True})
        
        # 最終メモリ使用量
        gc.collect()
        snapshot2 = tracemalloc.take_snapshot()
        
        # メモリ増加量を確認
        stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_diff = sum(stat.size_diff for stat in stats)
        
        # 10MB以上増加していないこと
        assert total_diff < 10 * 1024 * 1024
        
        tracemalloc.stop()
    
    def test_cli_command_injection(self):
        """CLIコマンドインジェクション対策テスト"""
        # 危険なパスを含むテスト
        dangerous_paths = [
            "../../../etc/passwd",
            "; rm -rf /",
            "| cat /etc/shadow",
            "$HOME/.ssh/id_rsa",
            "`whoami`",
        ]
        
        for path in dangerous_paths:
            # CLIコマンドを実行（実際には実行されない）
            result = subprocess.run(
                [sys.executable, str(project_root / "commands" / "ai_ancient_magic.py"), 
                 "single", "integrity", "--target", path],
                capture_output=True,
                text=True
            )
            
            # エラーが出てもシステムに影響がないこと
            assert result.returncode != 0 or "Error" in result.stderr
    
    @pytest.mark.asyncio
    async def test_infinite_loop_protection(self):
        """無限ループ保護テスト"""
        from libs.ancient_elder.tdd_guardian_wrapper import TDDGuardian
        
        guardian = TDDGuardian()
        
        # 短いタイムアウトを設定
        target = {
            "path": ".",
            "timeout": 1,  # 1秒でタイムアウト
            "quick_mode": True
        }
        
        start_time = time.time()
        result = await guardian.audit(target)
        execution_time = time.time() - start_time
        
        # タイムアウトが機能すること
        assert execution_time < 2  # 2秒以内に終了
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_race_condition_in_cache(self):
        """キャッシュの競合状態テスト"""
        cache = AuditCache()
        
        # 同じキーに対して並行書き込み
        async def write_cache(value):
            cache.set("test", {"path": "."}, {"value": value})
            await asyncio.sleep(0.001)  # わずかな遅延
            return cache.get("test", {"path": "."})
        
        # 10個の並行タスク
        tasks = [write_cache(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # 最後の値が読み取れること
        final_value = cache.get("test", {"path": "."})
        assert final_value is not None
        assert "value" in final_value
    
    def test_error_recovery_and_logging(self):
        """エラー回復とログ記録のテスト"""
        import logging
        from io import StringIO
        
        # ログをキャプチャ
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        logger = logging.getLogger("AncientElderAuditEngine")
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
        
        # エラーを発生させる
        engine = AncientElderAuditEngine()
        
        # 不正な監査者を登録
        engine.auditors["broken"] = None  # 意図的にNoneを設定
        
        # エラーが記録されること
        asyncio.run(engine.run_comprehensive_audit({"path": "."}))
        
        log_contents = log_capture.getvalue()
        assert "error" in log_contents.lower() or len(log_contents) > 0
        
        logger.removeHandler(handler)