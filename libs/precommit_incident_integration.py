#!/usr/bin/env python3
"""
Pre-commit Incident Integration
pre-commitフックとインシデント予測システムの統合

コミット前に以下を自動実行：
1. インポートエラー予測
2. テスト失敗予測
3. コード品質チェック
4. インシデント リスク評価
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import tempfile

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from libs.development_incident_predictor import DevelopmentIncidentPredictor
    from libs.test_execution_monitor import TestExecutionMonitor
except ImportError as e:
    logging.error(f"Failed to import incident prediction modules: {e}")
    DevelopmentIncidentPredictor = None
    TestExecutionMonitor = None

logger = logging.getLogger(__name__)

@dataclass
class PreCommitResult:
    """pre-commit結果"""
    success: bool
    risk_score: float
    issues_found: List[str]
    recommendations: List[str]
    execution_time: float
    details: Dict[str, Any]

@dataclass
class HookConfig:
    """フック設定"""
    enable_import_check: bool = True
    enable_test_prediction: bool = True
    enable_quick_tests: bool = True
    risk_threshold: float = 0.7  # この値以上でコミット拒否
    timeout_seconds: int = 60
    verbose: bool = False

class GitFileAnalyzer:
    """Git変更ファイル分析器"""
    
    def __init__(self):
        pass
    
    def get_staged_files(self) -> List[Path]:
        """ステージングされたファイル取得"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=AM'],
                capture_output=True, text=True, cwd=PROJECT_ROOT
            )
            
            if result.returncode != 0:
                logger.error(f"Git command failed: {result.stderr}")
                return []
            
            files = []
            for line in result.stdout.strip().split('\n'):
                if line and line.endswith('.py'):
                    file_path = PROJECT_ROOT / line
                    if file_path.exists():
                        files.append(file_path)
            
            return files
        except Exception as e:
            logger.error(f"Failed to get staged files: {e}")
            return []
    
    def get_modified_files(self) -> List[Path]:
        """変更されたファイル取得（ステージング + ワーキング）"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', '--diff-filter=AM', 'HEAD'],
                capture_output=True, text=True, cwd=PROJECT_ROOT
            )
            
            if result.returncode != 0:
                logger.warning(f"Git HEAD diff failed, using staged files only")
                return self.get_staged_files()
            
            files = []
            for line in result.stdout.strip().split('\n'):
                if line and line.endswith('.py'):
                    file_path = PROJECT_ROOT / line
                    if file_path.exists():
                        files.append(file_path)
            
            return files
        except Exception as e:
            logger.error(f"Failed to get modified files: {e}")
            return self.get_staged_files()
    
    def get_commit_message(self) -> Optional[str]:
        """コミットメッセージ取得（準備中の場合）"""
        try:
            commit_msg_file = PROJECT_ROOT / '.git' / 'COMMIT_EDITMSG'
            if commit_msg_file.exists():
                with open(commit_msg_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception as e:
            logger.debug(f"Could not read commit message: {e}")
        return None

class QuickTestRunner:
    """クイックテスト実行器"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def run_quick_tests(self, target_files: List[Path]) -> Dict[str, Any]:
        """関連テストの高速実行"""
        test_files = self._find_related_tests(target_files)
        
        if not test_files:
            return {
                'success': True,
                'tests_run': 0,
                'test_files': [],
                'message': 'No related tests found'
            }
        
        try:
            # pytestを高速モードで実行
            cmd = [
                'python', '-m', 'pytest',
                '--tb=short',
                '--quiet',
                '--disable-warnings',
                '--maxfail=5',  # 5回失敗で停止
                f'--timeout={self.timeout}',
                *[str(f) for f in test_files]
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                timeout=self.timeout + 10
            )
            
            return {
                'success': result.returncode == 0,
                'tests_run': len(test_files),
                'test_files': [str(f) for f in test_files],
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'tests_run': len(test_files),
                'test_files': [str(f) for f in test_files],
                'error': f'Tests timed out after {self.timeout}s',
                'return_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'tests_run': len(test_files),
                'test_files': [str(f) for f in test_files],
                'error': str(e),
                'return_code': -1
            }
    
    def _find_related_tests(self, target_files: List[Path]) -> List[Path]:
        """関連テストファイル検索"""
        test_files = []
        
        for target_file in target_files:
            # 直接対応するテストファイル
            test_file = self._find_direct_test_file(target_file)
            if test_file and test_file not in test_files:
                test_files.append(test_file)
            
            # インポートベースの関連テスト
            related_tests = self._find_import_related_tests(target_file)
            for test_file in related_tests:
                if test_file not in test_files:
                    test_files.append(test_file)
        
        return test_files[:10]  # 最大10ファイルに制限
    
    def _find_direct_test_file(self, target_file: Path) -> Optional[Path]:
        """直接対応するテストファイル検索"""
        # test_*.py パターン
        test_name = f"test_{target_file.stem}.py"
        
        # 複数の可能性をチェック
        candidates = [
            PROJECT_ROOT / 'tests' / test_name,
            PROJECT_ROOT / 'tests' / 'unit' / test_name,
            PROJECT_ROOT / 'tests' / 'integration' / test_name,
            target_file.parent / test_name,
            PROJECT_ROOT / test_name
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        return None
    
    def _find_import_related_tests(self, target_file: Path) -> List[Path]:
        """インポートベースの関連テスト検索"""
        related_tests = []
        
        try:
            # ターゲットファイルのモジュール名を取得
            rel_path = target_file.relative_to(PROJECT_ROOT)
            module_name = str(rel_path.with_suffix('')).replace('/', '.')
            
            # テストディレクトリを検索
            test_dirs = [
                PROJECT_ROOT / 'tests',
                PROJECT_ROOT / 'tests' / 'unit',
                PROJECT_ROOT / 'tests' / 'integration'
            ]
            
            for test_dir in test_dirs:
                if test_dir.exists():
                    for test_file in test_dir.rglob('test_*.py'):
                        if self._test_imports_module(test_file, module_name):
                            related_tests.append(test_file)
            
        except Exception as e:
            logger.debug(f"Error finding import-related tests: {e}")
        
        return related_tests[:5]  # 最大5ファイル
    
    def _test_imports_module(self, test_file: Path, module_name: str) -> bool:
        """テストファイルが指定モジュールをインポートするかチェック"""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 簡易的なインポートチェック
            import_patterns = [
                f'import {module_name}',
                f'from {module_name}',
                module_name.split('.')[-1]  # 最後の部分だけでもチェック
            ]
            
            return any(pattern in content for pattern in import_patterns)
        except Exception:
            return False

class PreCommitIncidentIntegration:
    """pre-commitインシデント統合メインクラス"""
    
    def __init__(self, config: Optional[HookConfig] = None):
        self.config = config or HookConfig()
        self.git_analyzer = GitFileAnalyzer()
        self.quick_test_runner = QuickTestRunner(timeout=self.config.timeout_seconds)
        
        # インシデント予測器（利用可能な場合のみ）
        if DevelopmentIncidentPredictor:
            self.incident_predictor = DevelopmentIncidentPredictor(PROJECT_ROOT)
        else:
            self.incident_predictor = None
            logger.warning("Development incident predictor not available")
    
    def run_precommit_check(self) -> PreCommitResult:
        """pre-commitチェック実行"""
        start_time = datetime.now()
        issues = []
        recommendations = []
        risk_score = 0.0
        details = {}
        
        try:
            # 変更ファイル取得
            staged_files = self.git_analyzer.get_staged_files()
            if not staged_files:
                return PreCommitResult(
                    success=True,
                    risk_score=0.0,
                    issues_found=['No Python files staged for commit'],
                    recommendations=['Stage some Python files to commit'],
                    execution_time=0.0,
                    details={'staged_files': []}
                )
            
            details['staged_files'] = [str(f) for f in staged_files]
            
            if self.config.verbose:
                print(f"📁 Analyzing {len(staged_files)} staged files...")
            
            # インシデント予測実行
            if self.config.enable_import_check and self.incident_predictor:
                prediction_result = self.incident_predictor.predict_development_risks(staged_files)
                risk_score = prediction_result['overall_risk_score']
                details['incident_prediction'] = prediction_result
                
                # 重要な問題を抽出
                critical_imports = [i for i in prediction_result['import_issues'] if i.severity == 'critical']
                if critical_imports:
                    issues.extend([f"Critical import error: {i.suggested_fix}" for i in critical_imports[:3]])
                
                recommendations.extend(prediction_result['recommendations'][:5])
            
            # クイックテスト実行
            if self.config.enable_quick_tests:
                test_result = self.quick_test_runner.run_quick_tests(staged_files)
                details['quick_tests'] = test_result
                
                if not test_result['success']:
                    issues.append(f"Quick tests failed ({test_result['tests_run']} tests)")
                    risk_score += 0.3
                    recommendations.append("Fix failing tests before committing")
            
            # テスト予測（利用可能な場合）
            if self.config.enable_test_prediction and self.incident_predictor:
                # staged_filesからテストファイルを抽出
                test_files = [f for f in staged_files if f.name.startswith('test_')]
                if test_files and hasattr(self.incident_predictor, 'test_predictor'):
                    test_predictions = self.incident_predictor.test_predictor.predict_test_results(test_files)
                    
                    failing_predictions = [p for p in test_predictions if p.predicted_result in ['fail', 'error']]
                    if failing_predictions:
                        issues.append(f"{len(failing_predictions)} tests predicted to fail")
                        risk_score += 0.2
                        recommendations.append("Review tests predicted to fail")
                    
                    details['test_predictions'] = len(test_predictions)
            
            # リスク評価
            success = risk_score < self.config.risk_threshold
            
            if not success:
                issues.append(f"Risk score {risk_score:.2f} exceeds threshold {self.config.risk_threshold}")
                recommendations.append("Address high-risk issues before committing")
            
        except Exception as e:
            logger.error(f"Pre-commit check failed: {e}")
            return PreCommitResult(
                success=False,
                risk_score=1.0,
                issues_found=[f"Pre-commit check error: {str(e)}"],
                recommendations=["Fix the pre-commit check error"],
                execution_time=(datetime.now() - start_time).total_seconds(),
                details={'error': str(e)}
            )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return PreCommitResult(
            success=success,
            risk_score=risk_score,
            issues_found=issues,
            recommendations=recommendations,
            execution_time=execution_time,
            details=details
        )
    
    def format_result_message(self, result: PreCommitResult) -> str:
        """結果メッセージのフォーマット"""
        lines = []
        
        # ヘッダー
        status = "✅ PASSED" if result.success else "❌ FAILED"
        lines.append(f"\n🔍 AI Company Pre-commit Check: {status}")
        lines.append(f"⏱️  Execution time: {result.execution_time:.2f}s")
        lines.append(f"📊 Risk score: {result.risk_score:.2f}")
        
        # 問題
        if result.issues_found:
            lines.append(f"\n⚠️  Issues found ({len(result.issues_found)}):")
            for issue in result.issues_found:
                lines.append(f"   • {issue}")
        
        # 推奨事項
        if result.recommendations:
            lines.append(f"\n💡 Recommendations ({len(result.recommendations)}):")
            for rec in result.recommendations[:5]:  # 最大5件
                lines.append(f"   • {rec}")
        
        # 詳細情報（verbose時）
        if self.config.verbose and result.details:
            lines.append(f"\n📋 Details:")
            if 'staged_files' in result.details:
                lines.append(f"   Staged files: {len(result.details['staged_files'])}")
            if 'quick_tests' in result.details:
                test_info = result.details['quick_tests']
                lines.append(f"   Quick tests: {test_info['tests_run']} files")
        
        if not result.success:
            lines.append(f"\n🚨 Commit blocked due to high risk (>{self.config.risk_threshold:.1f})")
            lines.append("   Address the issues above and try again.")
        else:
            lines.append(f"\n🎉 Commit approved - proceed with confidence!")
        
        return '\n'.join(lines)
    
    def save_result_log(self, result: PreCommitResult):
        """結果ログ保存"""
        log_dir = PROJECT_ROOT / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / 'precommit_checks.json'
        
        # 既存ログ読み込み
        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except Exception:
                logs = []
        
        # 新しいエントリ追加
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'success': result.success,
            'risk_score': result.risk_score,
            'execution_time': result.execution_time,
            'issues_count': len(result.issues_found),
            'details': result.details
        }
        
        logs.append(log_entry)
        
        # 最新100件のみ保持
        logs = logs[-100:]
        
        # 保存
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

def create_precommit_hook():
    """pre-commitフック作成"""
    hook_content = '''#!/bin/bash
# AI Company Pre-commit Hook
# Auto-generated incident prediction integration

cd "$(git rev-parse --show-toplevel)"

# Python環境確認
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

# インシデント予測実行
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

try:
    from libs.precommit_incident_integration import PreCommitIncidentIntegration, HookConfig
    
    # 設定（必要に応じて調整）
    config = HookConfig(
        enable_import_check=True,
        enable_test_prediction=True, 
        enable_quick_tests=True,
        risk_threshold=0.7,
        timeout_seconds=60,
        verbose=False
    )
    
    integration = PreCommitIncidentIntegration(config)
    result = integration.run_precommit_check()
    
    print(integration.format_result_message(result))
    integration.save_result_log(result)
    
    sys.exit(0 if result.success else 1)
    
except Exception as e:
    print(f'❌ Pre-commit check error: {e}')
    sys.exit(1)
"
'''
    
    hook_file = PROJECT_ROOT / '.git' / 'hooks' / 'pre-commit'
    hook_file.parent.mkdir(exist_ok=True)
    
    with open(hook_file, 'w') as f:
        f.write(hook_content)
    
    # 実行可能にする
    hook_file.chmod(0o755)
    
    print(f"✅ Pre-commit hook created: {hook_file}")

def demo_precommit_integration():
    """pre-commit統合のデモンストレーション"""
    print("🔗 Pre-commit Incident Integration Demo")
    print("=" * 60)
    
    config = HookConfig(
        enable_import_check=True,
        enable_test_prediction=True,
        enable_quick_tests=False,  # デモでは無効
        risk_threshold=0.5,
        verbose=True
    )
    
    integration = PreCommitIncidentIntegration(config)
    result = integration.run_precommit_check()
    
    print(integration.format_result_message(result))
    integration.save_result_log(result)
    
    print(f"\n🎯 Demo Result: {'SUCCESS' if result.success else 'BLOCKED'}")
    print("\n✅ Demo completed successfully!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Company Pre-commit Integration')
    parser.add_argument('--demo', action='store_true', help='Run demo')
    parser.add_argument('--install-hook', action='store_true', help='Install pre-commit hook')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    
    if args.install_hook:
        create_precommit_hook()
    elif args.demo:
        demo_precommit_integration()
    else:
        # 通常のpre-commitチェック実行
        config = HookConfig(verbose=args.verbose)
        integration = PreCommitIncidentIntegration(config)
        result = integration.run_precommit_check()
        
        print(integration.format_result_message(result))
        integration.save_result_log(result)
        
        sys.exit(0 if result.success else 1)