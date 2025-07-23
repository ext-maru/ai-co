#!/usr/bin/env python3
"""
Elder Flow Quality Gate V2
Phase 3強化版: 実装系Issueに対する厳格な品質基準

主な強化点:
1. 最低品質スコア: 85点（実装系）、70点（設計系）
2. Iron Will違反: 即座不合格
3. セキュリティリスク: レベル3以下必須
4. Issue種別に応じた品質基準の自動調整
"""

import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging
import json

# Phase 2で実装したIssue分類器
from libs.elder_system.issue_classifier_v2 import (
    IssueTypeClassifierV2, IssueCategory, IssueType
)

# 既存の強化品質基準
from libs.enhanced_quality_standards import (
    EnhancedQualityConfig, EnhancedQualityEvaluator,
    StrictIronWillValidator, EnhancedSecurityValidator,
    QualityViolation
)

logger = logging.getLogger(__name__)


class AdaptiveQualityConfig(EnhancedQualityConfig):
    """Issue種別に応じて適応する品質設定"""
    
    def __init__(self, issue_category: IssueCategory = IssueCategory.UNKNOWN):
        """初期化メソッド"""
        super().__init__()
        self.issue_category = issue_category
        self._apply_category_specific_config()
    
    def _apply_category_specific_config(self):
        """Issue種別に応じた品質基準の調整"""
        if self.issue_category == IssueCategory.IMPLEMENTATION_ORIENTED:
            # 実装系: 最も厳格な基準
            self.minimum_quality_score = 85.0
            self.iron_will_compliance_rate = 1.0  # 100%必須
            self.maximum_security_risk_level = 3
            self.critical_issues_limit = 0
            self.complexity_threshold = 8
            self.maintainability_minimum = 60
            self.test_coverage_minimum = 90.0
            self.documentation_coverage_minimum = 80.0
            
        elif self.issue_category == IssueCategory.DESIGN_ORIENTED:
            # 設計系: 標準基準
            self.minimum_quality_score = 70.0
            self.iron_will_compliance_rate = 1.0  # Iron Willは必須
            self.maximum_security_risk_level = 5
            self.critical_issues_limit = 0
            self.complexity_threshold = 15  # 設計文書は複雑でもOK
            self.maintainability_minimum = 50
            self.test_coverage_minimum = 80.0
            self.documentation_coverage_minimum = 90.0  # 設計系は文書重視
            
        elif self.issue_category == IssueCategory.MAINTENANCE_ORIENTED:
            # 保守系: 中間基準
            self.minimum_quality_score = 80.0
            self.iron_will_compliance_rate = 1.0
            self.maximum_security_risk_level = 4
            self.critical_issues_limit = 0
            self.complexity_threshold = 10
            self.maintainability_minimum = 55
            self.test_coverage_minimum = 85.0
            self.documentation_coverage_minimum = 75.0


class ElderFlowQualityGateV2:
    """Phase 3強化版品質ゲート"""
    
    def __init__(self):
        """初期化メソッド"""
        self.issue_classifier = IssueTypeClassifierV2()
        self.iron_will_validator = StrictIronWillValidator()
        self.security_validator = EnhancedSecurityValidator()
        self.feedback_history = []
    
    async def check_quality(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """品質チェックの実行（Issue種別対応）"""
        try:
            # Issueコンテキストから分類情報を取得
            issue_info = self._extract_issue_info(context)
            
            # Issue種別を判定（Phase 2の分類器使用）
            classification_result = None
            if issue_info:
                classification_result = self.issue_classifier.classify(issue_info)
                logger.info(f"Issue classified as: {classification_result.issue_type.value} "
                          f"(Category: {classification_result.category.value})")
            
            # Issue種別に応じた品質設定を適用
            config = AdaptiveQualityConfig(
                classification_result.category if classification_result 
                else IssueCategory.UNKNOWN
            )
            
            # 評価器を設定付きで初期化
            evaluator = EnhancedQualityEvaluator(config)
            
            # 品質チェック実行
            quality_results = await self._run_quality_checks(
                context, evaluator, classification_result
            )
            
            # フィードバック生成
            feedback = self._generate_feedback(
                quality_results, classification_result, config
            )
            
            # 履歴に記録（学習用）
            self._record_feedback(quality_results, feedback, classification_result)
            
            return quality_results
            
        except Exception as e:
            logger.error(f"Quality gate error: {e}")
            return {
                'passed': False,
                'quality_score': 0,
                'violations': [{
                    'type': 'quality_gate_error',
                    'severity': 'critical',
                    'message': f'Quality gate failed: {str(e)}'
                }],
                'error': str(e)
            }
    
    def _extract_issue_info(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """コンテキストからIssue情報を抽出"""
        # Elder Flowコンテキストから情報を取得
        task_name = context.get('task_name', '')
        
        # Issue番号を抽出
        issue_match = re.search(r'#(\d+)', task_name)
        issue_number = issue_match.group(1) if issue_match else None
        
        # 実際のIssue情報があれば使用
        if 'issue' in context:
            return context['issue']
        
        # なければタスク名から推測
        return {
            'title': task_name,
            'body': context.get('task_description', ''),
            'labels': context.get('labels', []),
            'number': issue_number
        }
    
    async def _run_quality_checks(self, context: Dict[str, Any], 
                                 evaluator: EnhancedQualityEvaluator,
                                 classification: Any) -> Dict[str, Any]:
        """品質チェックの実行"""
        all_violations = []
        file_results = []
        total_score = 0
        files_analyzed = 0
        
        # コンテキストからファイルパスを取得
        files_to_check = self._get_files_to_check(context)
        
        for file_path in files_to_check:
            if not file_path.endswith('.py'):
                continue
            
            # ファイル品質評価
            result = evaluator.evaluate_file_quality(file_path)
            
            file_results.append({
                'file': file_path,
                'score': result['quality_score'],
                'compliant': result['elder_guild_compliant'],
                'violations': result['violations']
            })
            
            all_violations.extend(result['violations'])
            total_score += result['quality_score']
            files_analyzed += 1
        
        # 平均スコア計算
        average_score = total_score / max(1, files_analyzed) if files_analyzed > 0 else 0
        
        # Iron Will違反の特別チェック
        iron_will_violations = [v for v in all_violations 
                               if v.get('violation_type') == 'iron_will_violation']
        
        # 最終判定
        passed = self._determine_gate_passed(
            average_score, all_violations, classification, evaluator.config
        )
        
        return {
            'passed': passed,
            'quality_score': average_score,
            'files_analyzed': files_analyzed,
            'file_results': file_results,
            'violations': all_violations,
            'iron_will_violations': len(iron_will_violations),
            'critical_violations': len([v for v in all_violations 
                                      if v.get('severity') == 'critical']),
            'issue_category': classification.category.value if classification else 'unknown',
            'issue_type': classification.issue_type.value if classification else 'unknown',
            'applied_standards': {
                'minimum_score': evaluator.config.minimum_quality_score,
                'iron_will_required': True,
                'max_security_risk': evaluator.config.maximum_security_risk_level,
                'complexity_threshold': evaluator.config.complexity_threshold
            }
        }
    
    def _get_files_to_check(self, context: Dict[str, Any]) -> List[str]:
        """チェック対象ファイルの取得"""
        files = []
        
        # 生成されたファイル
        if 'generated_files' in context:
            files.extend(context['generated_files'])
        
        # 実装されたファイル
        if 'implementation' in context:
            # 実装内容からファイルパスを推測
            impl_content = context['implementation']
            # 一時ファイルに保存してチェック
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(impl_content)
                files.append(f.name)
        
        # Elder Servantの出力
        if 'servant_outputs' in context:
            for servant, output in context['servant_outputs'].items():
                if 'files' in output:
                    files.extend(output['files'])
        
        return files
    
    def _determine_gate_passed(self, average_score: float, 
                              violations: List[Dict],
                              classification: Any,
                              config: AdaptiveQualityConfig) -> bool:
        """品質ゲート通過判定"""
        # Iron Will違反は即座に不合格
        if any(v.get('violation_type') == 'iron_will_violation' for v in violations):
            logger.warning("Quality gate failed: Iron Will violation detected")
            return False
        
        # Critical違反も即座に不合格
        if any(v.get('severity') == 'critical' for v in violations):
            logger.warning("Quality gate failed: Critical violations detected")
            return False
        
        # スコアが基準未満
        if average_score < config.minimum_quality_score:
            logger.warning(f"Quality gate failed: Score {average_score:.1f} < {config.minimum_quality_score}")
            return False
        
        # 実装系の追加チェック
        if classification and classification.category == IssueCategory.IMPLEMENTATION_ORIENTED:
            # セキュリティリスクチェック
            security_violations = [v for v in violations 
                                 if v.get('violation_type') == 'security_violation']
            if security_violations:
                logger.warning("Quality gate failed: Security violations in implementation")
                return False
        
        return True
    
    def _generate_feedback(self, results: Dict[str, Any], 
                          classification: Any,
                          config: AdaptiveQualityConfig) -> Dict[str, Any]:
        """詳細なフィードバック生成"""
        feedback = {
            'summary': '',
            'violations_by_type': {},
            'improvement_suggestions': [],
            'positive_points': [],
            'next_actions': []
        }
        
        # サマリー生成
        if results['passed']:
            feedback['summary'] = f"✅ 品質ゲート通過（スコア: {results['quality_score']:.1f}/100）"
        else:
            feedback['summary'] = f"❌ 品質ゲート不合格（スコア: {results['quality_score']:.1f}/100）"
        
        # 違反の分類
        for violation in results['violations']:
            v_type = violation.get('violation_type', 'unknown')
            if v_type not in feedback['violations_by_type']:
                feedback['violations_by_type'][v_type] = []
            feedback['violations_by_type'][v_type].append(violation)
        
        # 改善提案
        if results['iron_will_violations'] > 0:
            feedback['improvement_suggestions'].append({
                'priority': 'critical',
                'suggestion': 'TODO/FIXMEコメントを削除し、完全な実装を行ってください',
                'affected_files': list(set(v['file_path'] for v in results['violations'] 
                                         if v.get('violation_type') == 'iron_will_violation'))
            })
        
        if results['quality_score'] < config.minimum_quality_score:
            feedback['improvement_suggestions'].append({
                'priority': 'high',
                'suggestion': f'品質スコアを{config.minimum_quality_score}点以上に改善してください',
                'current_score': results['quality_score']
            })
        
        # ポジティブな点
        if results['quality_score'] >= 90:
            feedback['positive_points'].append('優れた品質スコア')
        if results['iron_will_violations'] == 0:
            feedback['positive_points'].append('Iron Will完全遵守')
        
        # 次のアクション
        if not results['passed']:
            feedback['next_actions'].append('品質違反を修正してください')
            if classification and classification.category == IssueCategory.IMPLEMENTATION_ORIENTED:
                feedback['next_actions'].append('実装系Issueは特に厳格な基準が適用されます')
        
        return feedback
    
    def _record_feedback(self, results: Dict[str, Any], 
                        feedback: Dict[str, Any],
                        classification: Any):
        """フィードバックを履歴に記録（学習用）"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'quality_score': results['quality_score'],
            'passed': results['passed'],
            'issue_category': classification.category.value if classification else 'unknown',
            'issue_type': classification.issue_type.value if classification else 'unknown',
            'violations_count': len(results['violations']),
            'iron_will_violations': results['iron_will_violations'],
            'feedback': feedback
        }
        
        self.feedback_history.append(record)
        
        # 履歴をファイルに保存（最大100件）
        history_file = Path('data/quality_gate_feedback_history.json')
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if history_file.exists():
                with open(history_file, 'r') as f:
                    all_history = json.load(f)
            else:
                all_history = []
            
            all_history.append(record)
            
            # 最新100件のみ保持
            if len(all_history) > 100:
                all_history = all_history[-100:]
            
            with open(history_file, 'w') as f:
                json.dump(all_history, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to save feedback history: {e}")
    
    async def get_quality_trends(self) -> Dict[str, Any]:
        """品質トレンドの取得（学習データから）"""
        history_file = Path('data/quality_gate_feedback_history.json')
        
        if not history_file.exists():
            return {'error': 'No history available'}
        
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            # トレンド分析
            implementation_scores = [h['quality_score'] for h in history 
                                   if h.get('issue_category') == 'implementation_oriented']
            design_scores = [h['quality_score'] for h in history 
                               if h.get('issue_category') == 'design_oriented']
            
            trends = {
                'total_checks': len(history),
                'pass_rate': sum(1 for h in history if h['passed']) / len(history) * 100,
                'average_score': sum(h['quality_score'] for h in history) / len(history),
                'implementation_average': sum(implementation_scores) / len(implementation_scores) \
                    if implementation_scores \
                    else 0,
                'design_average': sum(design_scores) / len(design_scores) if design_scores else 0,
                'iron_will_violation_rate': sum(h['iron_will_violations'] > 0 for h in history) / len(history) * 100,
                'recent_improvements': self._calculate_recent_improvements(history)
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to analyze trends: {e}")
            return {'error': str(e)}
    
    def _calculate_recent_improvements(self, history: List[Dict]) -> Dict[str, float]:
        """最近の改善傾向を計算"""
        if len(history) < 10:
            return {'insufficient_data': True}
        
        # 最新10件と前の10件を比較
        recent = history[-10:]
        previous = history[-20:-10] if len(history) >= 20 else history[:10]
        
        recent_avg = sum(h['quality_score'] for h in recent) / len(recent)
        previous_avg = sum(h['quality_score'] for h in previous) / len(previous)
        
        return {
            'score_improvement': recent_avg - previous_avg,
            'pass_rate_improvement': (
                sum(1 for h in recent if h['passed']) / len(recent) -
                sum(1 for h in previous if h['passed']) / len(previous)
            ) * 100
        }


# Integration with Elder Flow
class ElderFlowQualityIntegrationV2:
    """Elder Flowとの統合インターフェース"""
    
    def __init__(self):
        """初期化メソッド"""
        self.quality_gate = ElderFlowQualityGateV2()
    
    async def run_quality_gate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Elder Flowから呼び出される品質ゲート実行"""
        logger.info("🏛️ Elder Flow Quality Gate V2 - Starting quality check")
        
        # 品質チェック実行
        results = await self.quality_gate.check_quality(context)
        
        # 結果のフォーマット（Elder Flow互換）
        formatted_results = {
            'passed': results['passed'],
            'score': results['quality_score'],
            'details': {
                'files_analyzed': results['files_analyzed'],
                'violations': results['violations'],
                'iron_will_compliant': results['iron_will_violations'] == 0,
                'issue_category': results.get('issue_category', 'unknown'),
                'applied_standards': results.get('applied_standards', {})
            },
            'feedback': results.get('feedback', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        if results['passed']:
            logger.info(f"✅ Quality gate PASSED (Score: {results['quality_score']:.1f}/100)")
        else:
            logger.warning(f"❌ Quality gate FAILED (Score: {results['quality_score']:.1f}/100)")
            logger.warning(f"   Violations: {len(results['violations'])}")
            logger.warning(f"   Iron Will violations: {results['iron_will_violations']}")
        
        return formatted_results


# Export for Elder Flow integration
quality_gate_v2 = ElderFlowQualityIntegrationV2()


# CLI Testing
if __name__ == "__main__":
    import sys
    
    async def test_quality_gate():
        """Test the quality gate with sample context"""
        test_context = {
            'task_name': 'Implement OAuth2.0 authentication #123',
            'task_description': 'Add OAuth2.0 authentication with JWT tokens',
            'labels': ['enhancement', 'security'],
            'generated_files': sys.argv[1:] if len(sys.argv) > 1 else []
        }
        
        gate = ElderFlowQualityGateV2()
        results = await gate.check_quality(test_context)
        
        print("🏛️ Elder Flow Quality Gate V2 Test Results")
        print("=" * 50)
        print(f"Passed: {results['passed']}")
        print(f"Quality Score: {results['quality_score']:.1f}/100")
        print(f"Issue Category: {results.get('issue_category', 'unknown')}")
        print(f"Files Analyzed: {results['files_analyzed']}")
        print(f"Violations: {len(results['violations'])}")
        print(f"Iron Will Violations: {results['iron_will_violations']}")
        print(f"Applied Standards: {json.dumps(results.get('applied_standards', {}), indent=2)}")
        
        if not results['passed']:
            print("\n❌ Violations:")
            for v in results['violations'][:5]:  # Show first 5
                print(f"  - [{v.get('severity')}] {v.get('message')}")
    
    asyncio.run(test_quality_gate())