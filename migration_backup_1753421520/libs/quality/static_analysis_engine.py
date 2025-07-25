"""
StaticAnalysisEngine - 静的解析完全自動化エンジン

Issue #309: 自動化品質パイプライン実装
担当サーバント: 🧝‍♂️ QualityWatcher

目的: フロー違反完全排除・人的ミス撲滅
方針: Execute & Judge パターン
"""

import asyncio
import subprocess
import time
import logging
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor


@dataclass
class FormattingResult:
    """フォーマット結果"""
    changes_made: bool
    output: str
    errors: List[str] = field(default_factory=list)


@dataclass
class ImportResult:
    """import整理結果"""
    changes_made: bool
    output: str
    errors: List[str] = field(default_factory=list)


@dataclass
class TypeCheckResult:
    """型チェック結果"""
    errors: List[str]
    auto_fixable_errors: List[str] = field(default_factory=list)
    output: str = ""


@dataclass
class PylintResult:
    """Pylint解析結果"""
    score: float
    issues: List[Dict[str, Any]]
    auto_fixable_issues: List[Dict[str, Any]] = field(default_factory=list)
    output: str = ""


@dataclass
class StaticAnalysisResult:
    """静的解析完全結果"""
    status: str  # "COMPLETED" | "MAX_ITERATIONS_EXCEEDED" | "ERROR"
    iterations: int
    formatting_applied: bool
    imports_organized: bool
    type_errors: List[str]
    pylint_score: float
    pylint_issues: List[Dict[str, Any]]
    auto_fixes_applied: int
    execution_time: float
    summary: Dict[str, Any] = field(default_factory=dict)


class StaticAnalysisEngine:
    """
    静的解析完全自動化エンジン
    
    機能:
    - Black自動フォーマット（完了まで反復）
    - isort import整理（完了まで反復）
    - MyPy型チェック + 自動修正
    - Pylint静的解析（9.5点以上まで反復）
    - 自動修正機能
    - 完了判定ロジック
    """
    
    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
        self.logger = self._setup_logger()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Tool configurations
        self.black_config = {
            "line_length": 88,
            "target_version": ["py312"],
            "extend_exclude": r"/(migrations|__pycache__|\.git|\.venv|venv)/"
        }
        
        self.isort_config = {
            "profile": "black",
            "multi_line_output": 3,
            "line_length": 88,
            "known_first_party": ["libs", "core", "commands"],
        }
        
        self.mypy_config = {
            "python_version": "3.12",
            "warn_return_any": True,
            "warn_unused_configs": True,
            "disallow_untyped_defs": False,  # Gradual typing
        }
        
        self.pylint_config = {
            "max_line_length": 88,
            "good_names": ["i", "j", "k", "ex", "Run", "_", "id", "pk"],
            "disable": ["C0114", "C0116"],  # Missing docstrings for now
        }
    
    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("static_analysis_engine")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def execute_full_pipeline(self, target_path: str) -> StaticAnalysisResult:
        """
        完全自動化パイプライン実行
        
        Args:
            target_path: 解析対象ファイル/ディレクトリパス
            
        Returns:
            StaticAnalysisResult: 完全解析結果
        """
        start_time = time.time()
        self.logger.info(f"🚀 Starting static analysis pipeline for: {target_path}")
        
        result = StaticAnalysisResult(
            status="IN_PROGRESS",
            iterations=0,
            formatting_applied=False,
            imports_organized=False,
            type_errors=[],
            pylint_score=0.0,
            pylint_issues=[],
            auto_fixes_applied=0,
            execution_time=0.0
        )
        
        try:
            for iteration in range(self.max_iterations):
                self.logger.info(f"🔄 Iteration {iteration + 1}/{self.max_iterations}")
                result.iterations = iteration + 1
                
                # Step 1: Black Auto-formatting
                format_result = await self._run_black_formatting(target_path)
                if format_result.changes_made:
                    result.formatting_applied = True
                    self.logger.info("✅ Black formatting applied")
                
                # Step 2: isort Import Ordering
                import_result = await self._run_isort_organizing(target_path)
                if import_result.changes_made:
                    result.imports_organized = True
                    self.logger.info("✅ Import ordering applied")
                
                # Step 3: MyPy Type Checking
                type_result = await self._run_mypy_checking(target_path)
                result.type_errors = type_result.errors
                
                if type_result.auto_fixable_errors:
                    fixes_applied = await self._auto_fix_type_issues(
                        target_path, type_result.auto_fixable_errors
                    )
                    result.auto_fixes_applied += fixes_applied
                    self.logger.info(f"🔧 Applied {fixes_applied} type fixes")
                
                # Step 4: Pylint Static Analysis
                pylint_result = await self._run_pylint_analysis(target_path)
                result.pylint_score = pylint_result.score
                result.pylint_issues = pylint_result.issues
                
                if pylint_result.auto_fixable_issues:
                    fixes_applied = await self._auto_fix_pylint_issues(
                        target_path, pylint_result.auto_fixable_issues
                    )
                    result.auto_fixes_applied += fixes_applied
                    self.logger.info(f"🔧 Applied {fixes_applied} pylint fixes")
                
                # 完了判定: Iron Will基準
                completion_check = self._check_completion_criteria(
                    format_result, import_result, type_result, pylint_result
                )
                
                if completion_check["completed"]:
                    result.status = "COMPLETED"
                    self.logger.info(f"🎉 Pipeline completed in {iteration + 1} iterations")
                    break
                
                self.logger.info(f"⏳ Criteria not met: {completion_check['reasons']}")
                
                # 追加待機時間（ツール間の競合回避）
                await asyncio.sleep(0.5)
            
            else:
                result.status = "MAX_ITERATIONS_EXCEEDED"
                self.logger.warning(f"⚠️ Max iterations ({self.max_iterations}) exceeded")
        
        except Exception as e:
            result.status = "ERROR"
            self.logger.error(f"❌ Pipeline error: {e}", exc_info=True)
        
        finally:
            result.execution_time = time.time() - start_time
            result.summary = self._generate_summary(result)
            self.logger.info(f"📊 Pipeline finished in {result.execution_time:.2f}s")
        
        return result
    
    async def _run_black_formatting(self, target_path: str) -> FormattingResult:
        """Black自動フォーマット実行"""
        try:
            cmd = [
                "black",
                "--line-length", str(self.black_config["line_length"]),
                "--target-version", "py312",
                "--diff",  # Show changes
                "--check",  # Don't modify, just check
                target_path
            ]
            
            # First check if changes needed
            check_result = await self._run_subprocess(cmd)
            changes_needed = check_result.returncode != 0
            
            if changes_needed:
                # Apply formatting
                apply_cmd = cmd[:-2] + [target_path]  # Remove --diff --check
                apply_result = await self._run_subprocess(apply_cmd)
                
                return FormattingResult(
                    changes_made=True,
                    output=apply_result.stdout,
                    errors=[apply_result.stderr] if apply_result.stderr else []
                )
            else:
                return FormattingResult(
                    changes_made=False,
                    output="Already formatted",
                    errors=[]
                )
        
        except Exception as e:
            self.logger.error(f"Black formatting error: {e}")
            return FormattingResult(
                changes_made=False,
                output="",
                errors=[str(e)]
            )
    
    async def _run_isort_organizing(self, target_path: str) -> ImportResult:
        """isort import整理実行"""
        try:
            cmd = [
                "isort",
                "--profile", "black",
                "--line-length", str(self.isort_config["line_length"]),
                "--multi-line", "3",
                "--diff",  # Show changes
                "--check-only",  # Don't modify, just check
                target_path
            ]
            
            # Check if changes needed
            check_result = await self._run_subprocess(cmd)
            changes_needed = check_result.returncode != 0
            
            if changes_needed:
                # Apply import organizing
                apply_cmd = [c for c in cmd if c not in ["--diff", "--check-only"]]
                apply_result = await self._run_subprocess(apply_cmd)
                
                return ImportResult(
                    changes_made=True,
                    output=apply_result.stdout,
                    errors=[apply_result.stderr] if apply_result.stderr else []
                )
            else:
                return ImportResult(
                    changes_made=False,
                    output="Imports already organized",
                    errors=[]
                )
        
        except Exception as e:
            self.logger.error(f"isort organizing error: {e}")
            return ImportResult(
                changes_made=False,
                output="",
                errors=[str(e)]
            )
    
    async def _run_mypy_checking(self, target_path: str) -> TypeCheckResult:
        """MyPy型チェック実行"""
        try:
            cmd = [
                "mypy",
                "--python-version", self.mypy_config["python_version"],
                "--show-error-codes",
                "--no-error-summary",
                target_path
            ]
            
            result = await self._run_subprocess(cmd)
            errors = []
            auto_fixable = []
            
            if result.stdout:
                error_lines = result.stdout.strip().split('\n')
                for line in error_lines:
                    if line.strip():
                        errors.append(line)
                        # Simple auto-fixable error detection
                        if "Need type annotation" in line or "missing return type" in line:
                            auto_fixable.append(line)
            
            return TypeCheckResult(
                errors=errors,
                auto_fixable_errors=auto_fixable,
                output=result.stdout
            )
        
        except Exception as e:
            self.logger.error(f"MyPy checking error: {e}")
            return TypeCheckResult(
                errors=[str(e)],
                auto_fixable_errors=[],
                output=""
            )
    
    async def _run_pylint_analysis(self, target_path: str) -> PylintResult:
        """Pylint静的解析実行"""
        try:
            cmd = [
                "pylint",
                "--max-line-length", str(self.pylint_config["max_line_length"]),
                "--good-names", ",".join(self.pylint_config["good_names"]),
                "--disable", ",".join(self.pylint_config["disable"]),
                "--output-format", "json",
                "--score", "yes",
                target_path
            ]
            
            result = await self._run_subprocess(cmd)
            
            # Parse JSON output
            issues = []
            auto_fixable = []
            score = 0.0
            
            try:
                if result.stdout:
                    # Pylint outputs score at the end, JSON before that
                    lines = result.stdout.strip().split('\n')
                    json_lines = []
                    score_line = ""
                    
                    for line in lines:
                        if line.startswith('[') or line.startswith('{'):
                            json_lines.append(line)
                        elif "rated at" in line:
                            score_line = line
                    
                    # Parse JSON issues
                    if json_lines:
                        json_str = '\n'.join(json_lines)
                        if json_str.strip():
                            issues = json.loads(json_str)
                    
                    # Parse score
                    if score_line:
                        score_match = re.search(r'rated at ([\d.]+)/10', score_line)
                        if score_match:
                            score = float(score_match.group(1))
                    
                    # Identify auto-fixable issues
                    for issue in issues:
                        if issue.get('type') in ['convention', 'refactor']:
                            if issue.get('message-id') in ['C0326', 'C0330', 'W0611']:
                                auto_fixable.append(issue)
            
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(f"Pylint output parsing error: {e}")
                # Fallback: extract score from stderr
                if result.stderr and "rated at" in result.stderr:
                    score_match = re.search(r'rated at ([\d.]+)/10', result.stderr)
                    if score_match:
                        score = float(score_match.group(1))
            
            return PylintResult(
                score=score,
                issues=issues,
                auto_fixable_issues=auto_fixable,
                output=result.stdout
            )
        
        except Exception as e:
            self.logger.error(f"Pylint analysis error: {e}")
            return PylintResult(
                score=0.0,
                issues=[],
                auto_fixable_issues=[],
                output=""
            )
    
    async def _auto_fix_type_issues(self, target_path: str, type_errors: List[str]) -> int:
        """型エラー自動修正"""
        # Simplified auto-fix implementation
        # In production, this would use AST manipulation
        fixes_applied = 0
        
        try:
            file_path = Path(target_path)
            if file_path.is_file() and file_path.suffix == '.py':
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Simple fixes for common type issues
                for error in type_errors:
                    if "Need type annotation" in error and "-> None:" not in content:
                        # Add return type annotation for functions
                        content = re.sub(
                            r'def (\w+)\([^)]*\):',
                            r'def \1(\g<0>) -> None:',
                            content
                        )
                        if content != original_content:
                            fixes_applied += 1
                            original_content = content
                
                if fixes_applied > 0:
                    file_path.write_text(content, encoding='utf-8')
                    self.logger.info(f"Applied {fixes_applied} type fixes to {target_path}")
        
        except Exception as e:
            self.logger.error(f"Auto-fix type issues error: {e}")
        
        return fixes_applied
    
    async def _auto_fix_pylint_issues(self, target_path: str, pylint_issues: List[Dict]) -> int:
        """Pylint問題自動修正"""
        # Simplified auto-fix implementation
        fixes_applied = 0
        
        try:
            file_path = Path(target_path)
            if file_path.is_file() and file_path.suffix == '.py':
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                for issue in pylint_issues:
                    message_id = issue.get('message-id', '')
                    
                    # Fix unused imports
                    if message_id == 'W0611':
                        # This would require more sophisticated AST analysis
                        pass
                    
                    # Fix whitespace issues
                    elif message_id in ['C0326', 'C0330']:
                        # Black should handle most of these
                        pass
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    fixes_applied = len(pylint_issues)
                    self.logger.info(f"Applied {fixes_applied} pylint fixes to {target_path}")
        
        except Exception as e:
            self.logger.error(f"Auto-fix pylint issues error: {e}")
        
        return fixes_applied
    
    def _check_completion_criteria(
        self,
        format_result: FormattingResult,
        import_result: ImportResult,
        type_result: TypeCheckResult,
        pylint_result: PylintResult
    ) -> Dict[str, Any]:
        """完了基準チェック - Iron Will基準"""
        reasons = []
        
        # Criterion 1: No formatting changes needed
        if format_result.changes_made:
            reasons.append("Formatting changes still needed")
        
        # Criterion 2: No import organizing changes needed
        if import_result.changes_made:
            reasons.append("Import organizing still needed")
        
        # Criterion 3: No type errors (relaxed for gradual typing)
        if len(type_result.errors) > 0:
            reasons.append(f"{len(type_result.errors)} type errors remaining")
        
        # Criterion 4: Pylint score >= 9.5 (Iron Will standard)
        if pylint_result.score < 9.5:
            reasons.append(f"Pylint score {pylint_result.score:.1f} < 9.5")
        
        completed = len(reasons) == 0
        
        return {
            "completed": completed,
            "reasons": reasons,
            "criteria_met": {
                "formatting": not format_result.changes_made,
                "imports": not import_result.changes_made,
                "types": len(type_result.errors) == 0,
                "pylint": pylint_result.score >= 9.5
            }
        }
    
    def _generate_summary(self, result: StaticAnalysisResult) -> Dict[str, Any]:
        """結果サマリー生成"""
        return {
            "pipeline_status": result.status,
            "total_iterations": result.iterations,
            "execution_time_seconds": result.execution_time,
            "quality_metrics": {
                "pylint_score": result.pylint_score,
                "type_errors_count": len(result.type_errors),
                "pylint_issues_count": len(result.pylint_issues),
                "auto_fixes_applied": result.auto_fixes_applied
            },
            "improvements_applied": {
                "formatting": result.formatting_applied,
                "import_organization": result.imports_organized,
                "automatic_fixes": result.auto_fixes_applied > 0
            },
            "iron_will_compliance": {
                "formatting_perfect": not result.formatting_applied,
                "imports_perfect": not result.imports_organized,
                "type_safety": len(result.type_errors) == 0,
                "pylint_excellence": result.pylint_score >= 9.5
            }
        }
    
    async def _run_subprocess(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """サブプロセス実行（非同期）"""
        loop = asyncio.get_event_loop()
        
        def run_sync():
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
                cwd=str(Path.cwd())
            )
        
        return await loop.run_in_executor(self.executor, run_sync)
    
    def __del__(self):
        """クリーンアップ"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)