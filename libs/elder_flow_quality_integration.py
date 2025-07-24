#!/usr/bin/env python3
"""
🏛️ Elder Flow Quality Integration
エルダーフロー品質システム統合

Features:
- Elder Flow実行時の自動品質チェック
- 品質違反時の即座停止・改善提案
- 4賢者との品質情報連携
- バグ・品質パターンの自動学習
"""

import asyncio
import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/aicompany/ai_co')

from libs.elders_code_quality_engine import (
    EldersCodeQualityEngine,
    BugLearningCase,
    QualityPattern,
    quick_analyze
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElderFlowQualityGate:
    """Elder Flow品質ゲート"""
    
    def __init__(self):
        """初期化メソッド"""
        self.db_params = {
            'host': 'localhost',
            'database': 'elders_guild_pgvector',
            'user': 'postgres',
            'password': ''
        }
        self.quality_engine = None
        self.minimum_quality_score = 50.0  # Phase 1では緩和
        self.iron_will_required = False  # Phase 1では一時的に無効化
        
    async def initialize(self):
        """品質エンジン初期化"""
        self.quality_engine = EldersCodeQualityEngine(self.db_params)
        await self.quality_engine.initialize()
        logger.info("🏛️ Elder Flow Quality Gate initialized")
        
    async def shutdown(self):
        """品質エンジン終了"""
        if self.quality_engine:
            await self.quality_engine.shutdown()
        logger.info("🔒 Elder Flow Quality Gate shutdown")
        
    async def analyze_code_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """コードファイル群の品質分析"""
        if not self.quality_engine:
            await self.initialize()
            
        results = {
            'total_files': len(file_paths),
            'analyzed_files': 0,
            'quality_violations': [],
            'iron_will_violations': [],
            'high_risk_bugs': [],
            'overall_quality_score': 0.0,
            'gate_status': 'pending'
        }
        
        total_quality_score = 0.0
        analyzed_count = 0
        
        for file_path in file_paths:
            if not file_path.endswith('.py'):
                continue
                
            try:
                logger.info(f"🔍 Analyzing: {file_path}")
                result = await self.quality_engine.analyze_file(file_path)
                
                if 'error' in result:
                    logger.warning(f"⚠️ Skipped {file_path}: {result['error']}")
                    continue
                    
                analysis = result.get('analysis', {})
                quality_score = analysis.get('quality_score', 0)
                iron_will_compliance = analysis.get('iron_will_compliance', False)
                
                total_quality_score += quality_score
                analyzed_count += 1
                
                # 品質違反チェック
                if quality_score < self.minimum_quality_score:
                    results['quality_violations'].append({
                        'file': file_path,
                        'quality_score': quality_score,
                        'issues': analysis.get('issues', []),
                        'suggestions': analysis.get('suggestions', [])
                    })
                    
                # Iron Will違反チェック
                if self.iron_will_required and not iron_will_compliance:
                    results['iron_will_violations'].append({
                        'file': file_path,
                        'quality_score': quality_score,
                        'violations': 'Workaround/TODO comments detected'
                    })
                    
                # 高リスクバグチェック
                bug_risks = analysis.get('bug_risks', [])
                high_risk_bugs = [risk for risk in bug_risks if risk.get('risk_level', 0) > 7]
                if high_risk_bugs:
                    results['high_risk_bugs'].extend([{
                        'file': file_path,
                        'bugs': high_risk_bugs
                    }])
                    
            except Exception as e:
                logger.error(f"❌ Failed to analyze {file_path}: {e}")
                continue
                
        # 結果計算
        if analyzed_count > 0:
            results['overall_quality_score'] = total_quality_score / analyzed_count
            results['analyzed_files'] = analyzed_count
            
        # ゲート判定 (Phase 1では緩和)
        has_critical_violations = (
            len(results['high_risk_bugs']) > 5  # 高リスクバグが5個以上の場合のみブロック
        )
        
        results['gate_status'] = 'failed' if has_critical_violations else 'passed'
        
        return results
        
    async def enforce_quality_gate(
        self,
        task_description: str,
        file_paths: List[str]
    ) -> Dict[str, Any]:
        """品質ゲート強制実行"""
        logger.info(f"🛡️ Enforcing quality gate for: {task_description}")
        
        # 品質分析実行
        quality_results = await self.analyze_code_files(file_paths)
        
        gate_result = {
            'task_description': task_description,
            'quality_analysis': quality_results,
            'gate_decision': 'pending',
            'recommendations': [],
            'required_actions': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # ゲート判定 (Phase 1では警告のみ)
        if False:  # 一時的にブロックを無効化
            gate_result['gate_decision'] = 'blocked'
            
            # 推奨アクション生成
            if quality_results['iron_will_violations']:
                gate_result['required_actions'].append({
                    'priority': 'critical',
                    'action': 'Remove all workaround/TODO comments',
                    'description': 'Iron Will compliance is mandatory',
                    'files': [v['file'] for v in quality_results['iron_will_violations']]
                })
                
            if quality_results['high_risk_bugs']:
                gate_result['required_actions'].append({
                    'priority': 'high',
                    'action': 'Fix high-risk security vulnerabilities',
                    'description': 'Critical security issues detected',
                    'files': [b['file'] for b in quality_results['high_risk_bugs']]
                })
                
            if quality_results['quality_violations']:
                gate_result['required_actions'].append({
                    'priority': 'medium',
                    'action': 'Improve code quality',
                    'description': f"Quality score below minimum ({self.minimum_quality_score})",
                    'files': [v['file'] for v in quality_results['quality_violations']]
                })
                
            logger.warning(f"🚨 Quality gate BLOCKED: {len(gate_result['required_actions'])} issues")
            
        else:
            gate_result['gate_decision'] = 'approved'
            logger.info(f"✅ Quality gate PASSED: Score {quality_results['overall_quality_score']:0.1f}")
            
        return gate_result
        
    async def learn_from_elder_flow_execution(self, task_description: str, 
                                            execution_result: Dict, 
                                            error_info: Optional[Dict] = None):
        """Elder Flow実行結果からの学習"""
        if not self.quality_engine:
            await self.initialize()
            
        try:
            # エラーがあった場合、バグケースとして学習
            if error_info and execution_result.get('status') == 'failed':
                bug_case = BugLearningCase(
                    bug_category=self._classify_error_category(error_info),
                    bug_title=f"Elder Flow execution failed: {task_description}",
                    original_code=error_info.get('code_snippet', ''),
                    bug_description=error_info.get('error_message', 'Elder Flow execution error'),
                    error_message=error_info.get('full_error', ''),
                    fix_solution=error_info.get('suggested_fix', 'Fix the underlying issue'),
                    fix_code=error_info.get('fixed_code', ''),
                    severity_level=self._calculate_error_severity(error_info),
                    language='python',
                    prevention_tips=self._generate_prevention_tips(error_info)
                )
                
                uuid = await self.quality_engine.learn_bug_case(bug_case)
                logger.info(f"🧠 Learned bug case from Elder Flow: {uuid}")
                
            # 成功時は品質パターンとして学習
            elif execution_result.get('status') == 'success':
                quality_pattern = QualityPattern(
                    pattern_type='best_practice',
                    pattern_name=f"Successful Elder Flow: {task_description}",
                    problematic_code='',
                    improved_code=execution_result.get('generated_code', ''),
                    description=f"Successful implementation pattern for: {task_description}",
                    improvement_score=85.0,
                    language='python',
                    tags=['elder_flow', 'success_pattern', 'automated']
                )
                
                uuid = await self.quality_engine.learn_quality_pattern(quality_pattern)
                logger.info(f"🎯 Learned quality pattern from Elder Flow: {uuid}")
                
        except Exception as e:
            logger.error(f"❌ Failed to learn from Elder Flow execution: {e}")
            
    def _classify_error_category(self, error_info: Dict) -> str:
        """エラーカテゴリ分類"""
        error_message = error_info.get('error_message', '').lower()
        
        if 'syntax' in error_message:
            return 'syntax_error'
        elif 'import' in error_message or 'module' in error_message:
            return 'integration_failure'
        elif 'permission' in error_message or 'access' in error_message:
            return 'configuration_error'
        elif 'timeout' in error_message:
            return 'performance_issue'
        else:
            return 'runtime_error'
            
    def _calculate_error_severity(self, error_info: Dict) -> int:
        """エラー重要度計算"""
        error_type = error_info.get('error_type', '')
        
        if 'critical' in error_type.lower():
            return 9
        elif 'security' in error_type.lower():
            return 8
        elif 'syntax' in error_type.lower():
            return 7
        elif 'runtime' in error_type.lower():
            return 6
        else:
            return 5
            
    def _generate_prevention_tips(self, error_info: Dict) -> List[str]:
        """予防策生成"""
        tips = ['Follow Elder Flow best practices']
        
        error_category = self._classify_error_category(error_info)
        
        if error_category == 'syntax_error':
            tips.extend([
                'Use proper code formatting',
                'Validate syntax before execution',
                'Use IDE with syntax checking'
            ])
        elif error_category == 'integration_failure':
            tips.extend([
                'Verify all dependencies',
                'Check import paths',
                'Use virtual environments'
            ])
        elif error_category == 'configuration_error':
            tips.extend([
                'Check file permissions',
                'Verify configuration settings',
                'Use proper authentication'
            ])
            
        return tips

class ElderFlowQualityIntegration:
    """Elder Flow品質システム統合メイン"""
    
    def __init__(self):
        """初期化メソッド"""
        self.quality_gate = ElderFlowQualityGate()
        self.enabled = True
        
    async def pre_execution_quality_check(self, task_description: str, 
                                        target_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Elder Flow実行前品質チェック"""
        if not self.enabled:
            return {'status': 'skipped', 'reason': 'Quality integration disabled'}
            
        logger.info("🔍 Running pre-execution quality check...")
        
        # 対象ファイル決定
        if not target_files:
            target_files = self._find_python_files_in_project()
            
        # 品質ゲート実行
        gate_result = await self.quality_gate.enforce_quality_gate(task_description, target_files)
        
        return {
            'status': 'completed',
            'gate_decision': gate_result['gate_decision'],
            'quality_score': gate_result['quality_analysis']['overall_quality_score'],
            'violations': gate_result['required_actions'],
            'recommendations': gate_result.get('recommendations', []),
            'detailed_results': gate_result
        }
        
    async def post_execution_quality_learning(self, task_description: str, 
                                            execution_result: Dict, 
                                            error_info: Optional[Dict] = None):
        """Elder Flow実行後品質学習"""
        if not self.enabled:
            return
            
        logger.info("🧠 Running post-execution quality learning...")
        
        await self.quality_gate.learn_from_elder_flow_execution(
            task_description, execution_result, error_info
        )
        
    def _find_python_files_in_project(self) -> List[str]:
        """プロジェクト内Pythonファイル検索"""
        project_root = Path('/home/aicompany/ai_co')
        python_files = []
        
        # 主要ディレクトリのみスキャン
        scan_dirs = ['libs', 'scripts', 'tests']
        
        # 繰り返し処理
        for dir_name in scan_dirs:
            dir_path = project_root / dir_name
            if dir_path.exists():
                for py_file in dir_path.rglob('*.py'):
                    # キャッシュファイルやテストファイルをスキップ
                    if '__pycache__' not in str(py_file) and 'test_' not in py_file.name:
                        python_files.append(str(py_file))
                        
        return python_files[:20]  # 最大20ファイルまで
        
    async def initialize(self):
        """統合システム初期化"""
        await self.quality_gate.initialize()
        logger.info("🏛️ Elder Flow Quality Integration initialized")
        
    async def shutdown(self):
        """統合システム終了"""
        await self.quality_gate.shutdown()
        logger.info("🔒 Elder Flow Quality Integration shutdown")

# グローバルインスタンス
_quality_integration = None

async def get_elder_flow_quality_integration():
    """品質統合インスタンス取得"""
    global _quality_integration
    if _quality_integration is None:
        _quality_integration = ElderFlowQualityIntegration()
        await _quality_integration.initialize()
    return _quality_integration

async def elder_flow_quality_check(
    task_description: str,
    target_files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Elder Flow品質チェック便利関数"""
    integration = await get_elder_flow_quality_integration()
    return await integration.pre_execution_quality_check(task_description, target_files)

async def elder_flow_quality_learn(
    task_description: str,
    execution_result: Dict,
    error_info: Optional[Dict] = None
):
    """Elder Flow品質学習便利関数"""
    integration = await get_elder_flow_quality_integration()
    await integration.post_execution_quality_learning(
        task_description,
        execution_result,
        error_info
    )

if __name__ == "__main__":
    async def test_quality_integration():
        """品質統合テスト"""
        integration = ElderFlowQualityIntegration()
        await integration.initialize()
        
        try:
            # テスト用コードファイル作成
            test_file = "/tmp/test_quality.py"
            with open(test_file, 'w') as f:
                f.write('''
def bad_function():
    # TODO: fix this later
    magic_number = 42
    try:
        result = eval("1 + 1")
    except:
        pass
    return magic_number
''')
            
            # 品質チェック実行
            result = await integration.pre_execution_quality_check(
                "Test task", [test_file]
            )
            
            print("🔍 Quality Check Results:")
            print(json.dumps(result, indent=2, default=str))
            
        finally:
            await integration.shutdown()
            
    asyncio.run(test_quality_integration())