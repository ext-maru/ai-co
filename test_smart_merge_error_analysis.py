#!/usr/bin/env python3
"""
🚨 Smart Merge Retry エラーハンドリング・レジリエンス分析テスト
詳細なエラーシナリオとストレステストを実行
"""

import asyncio
import logging
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch

# パスを追加
sys.path.append('/home/aicompany/ai_co/libs/integrations/github')

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ErrorAnalysisTestSuite:
    """Smart Merge Retry エラー分析テストスイート"""
    
    def __init__(self):
        self.test_results = []
        self.error_patterns = {}
        self.resilience_scores = {}
        
    async def run_all_tests(self):
        """全テストを実行"""
        print("🚨 Smart Merge Retry エラーハンドリング・レジリエンス分析開始\n")
        
        # 1.0 エラーハンドリングパターン分析
        await self._test_error_handling_patterns()
        
        # 2.0 レジリエンス機能評価
        await self._test_resilience_features()
        
        # 3.0 障害シナリオテスト
        await self._test_failure_scenarios()
        
        # 4.0 実際のストレステスト
        await self._test_stress_conditions()
        
        # 分析結果レポート
        self._generate_analysis_report()
        
    async def _test_error_handling_patterns(self):
        """エラーハンドリングパターン分析"""
        print("🔍 1.0 エラーハンドリングパターン分析")
        
        from smart_merge_retry import SmartMergeRetryEngine, RetryConfig, MergeableState
        
        # テストケース: 例外捕捉の網羅性
        patterns_tested = {
            'network_errors': False,
            'api_errors': False,
            'timeout_errors': False,
            'merge_errors': False,
            'unexpected_errors': False
        }
        
        try:
            # モックAPIクライアント
            mock_client = Mock()
            
            # 1.1 ネットワークエラー処理
            print("   📡 1.1 ネットワークエラー処理テスト")
            mock_client._get_pull_request = Mock(side_effect=ConnectionError("Network error"))
            mock_client._enable_auto_merge = Mock(return_value={"success": True})
            
            engine = SmartMergeRetryEngine(mock_client)
            result = await engine.attempt_smart_merge(1)
            
            if not result.get('success') and 'unexpected_error' in result.get('reason', ''):
                patterns_tested['network_errors'] = True
                print("   ✅ ネットワークエラーが適切にキャッチされています")
            else:
                print("   ❌ ネットワークエラー処理に問題があります")
            
            # 1.2 API エラー処理
            print("   🔧 1.2 API エラー処理テスト")
            mock_client._get_pull_request = Mock(return_value={
                'success': False, 
                'error': 'API rate limit exceeded'
            })
            
            engine2 = SmartMergeRetryEngine(mock_client)
            result2 = await engine2.attempt_smart_merge(2)
            
            if result2.get('success') is False:
                patterns_tested['api_errors'] = True
                print("   ✅ API エラーが適切に処理されています")
            else:
                print("   ❌ API エラー処理に問題があります")
            
            # 1.3 予期しない例外処理
            print("   💥 1.3 予期しない例外処理テスト")
            mock_client._get_pull_request = Mock(side_effect=ValueError("Unexpected value error"))
            
            engine3 = SmartMergeRetryEngine(mock_client)
            result3 = await engine3.attempt_smart_merge(3)
            
            if 'unexpected_error' in result3.get('reason', '') or 'error' in result3:
                patterns_tested['unexpected_errors'] = True
                print("   ✅ 予期しない例外が適切に処理されています")
            else:
                print("   ❌ 予期しない例外処理に問題があります")
                
        except Exception as e:
            print(f"   ❌ エラーハンドリングパターンテスト中にエラー: {e}")
        
        self.error_patterns = patterns_tested
        print(f"   📊 エラーハンドリング網羅率: {sum(patterns_tested.values())}/{len(patterns_tested)}\n")
        
    async def _test_resilience_features(self):
        """レジリエンス機能評価"""
        print("🛡️ 2.0 レジリエンス機能評価")
        
        try:
            from smart_merge_retry import SmartMergeRetryEngine, RetryConfig, MergeableState
            
            # 2.1 リトライ機構テスト
            print("   🔄 2.1 リトライ機構テスト")
            
            call_count = 0
            def mock_get_pr_with_retry(pr_number):
                nonlocal call_count
                call_count += 1
                """mock_get_pr_with_retryの値を取得"""
                
                if call_count <= 2:  # 最初の2回は失敗
                    return {
                        'success': True,
                        'pull_request': {
                            'mergeable': None,
                            'mergeable_state': 'unstable',
                            'draft': False,
                            'state': 'open'
                        }
                    }
                else:  # 3回目で成功
                    return {
                        'success': True,
                        'pull_request': {
                            'mergeable': True,
                            'mergeable_state': 'clean',
                            'draft': False,
                            'state': 'open'
                        }
                    }
            
            mock_client = Mock()
            mock_client._get_pull_request = Mock(side_effect=mock_get_pr_with_retry)
            mock_client._enable_auto_merge = Mock(return_value={"success": True})
            
            # 短い間隔でテスト
            config = {
                MergeableState.UNSTABLE: RetryConfig(
                    max_retries=5, base_delay=0.1, max_delay=0.5, timeout=10
                )
            }
            
            engine = SmartMergeRetryEngine(mock_client)
            start_time = time.time()
            result = await engine.attempt_smart_merge(10, custom_config=config)
            end_time = time.time()
            
            retry_history = engine.get_retry_history(10)
            
            resilience_score = 0
            if result.get('success'):
                resilience_score += 30
                print(f"   ✅ リトライ成功: {result.get('attempts')}回試行")
            
            if len(retry_history) >= 2:
                resilience_score += 20
                print(f"   ✅ リトライ履歴記録: {len(retry_history)}回")
            
            if end_time - start_time < 5:  # 適切な時間内
                resilience_score += 15
                print(f"   ✅ 実行時間適切: {end_time - start_time:0.2f}秒")
            
            # 2.2 バックオフ機構テスト  
            print("   ⏰ 2.2 指数バックオフ機構テスト")
            from smart_merge_retry import RetryStrategy
            
            config_backoff = RetryConfig(
                max_retries=3,
                base_delay=1,
                backoff_factor=2.0,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF
            )
            
            engine_test = SmartMergeRetryEngine(Mock())
            delays = []
            for attempt in range(3):
                delay = engine_test._calculate_delay(attempt, config_backoff)
                delays.append(delay)
            
            # 指数的増加をチェック
            if delays[0] < delays[1] < delays[2]:
                resilience_score += 20
                print(f"   ✅ 指数バックオフ動作確認: {delays}")
            else:
                print(f"   ❌ 指数バックオフに問題: {delays}")
            
            # 2.3 タイムアウト管理テスト
            print("   ⏳ 2.3 タイムアウト管理テスト")
            
            # タイムアウト設定を極端に短くして動作確認
            timeout_config = {
                MergeableState.UNSTABLE: RetryConfig(
                    max_retries=10, base_delay=0.1, timeout=0.5  # 0.5秒でタイムアウト
                )
            }
            
            mock_slow_client = Mock()
            mock_slow_client._get_pull_request = Mock(return_value={
                'success': True,
                'pull_request': {'mergeable': None, 'mergeable_state': 'unstable', 'draft': False}
            })
            
            engine_timeout = SmartMergeRetryEngine(mock_slow_client)
            timeout_result = await engine_timeout.attempt_smart_merge(20, custom_config=timeout_config)
            
            if timeout_result.get('reason') == 'timeout':
                resilience_score += 15
                print("   ✅ タイムアウト管理が適切に動作")
            else:
                print(f"   ❌ タイムアウト管理に問題: {timeout_result.get('reason')}")
            
            self.resilience_scores['basic'] = resilience_score
            print(f"   📊 レジリエンス基本スコア: {resilience_score}/100\n")
                
        except Exception as e:
            print(f"   ❌ レジリエンス機能評価中にエラー: {e}\n")
    
    async def _test_failure_scenarios(self):
        """障害シナリオテスト"""
        print("💣 3.0 障害シナリオテスト")
        
        scenarios_tested = {
            'github_api_failure': False,
            'memory_pressure': False,
            'concurrent_execution': False,
            'malformed_response': False
        }
        
        try:
            from smart_merge_retry import SmartMergeRetryEngine, MergeableState
            
            # 3.1 GitHub API障害対応
            print("   🐙 3.1 GitHub API障害対応テスト")
            
            api_failure_responses = [
                {'success': False, 'error': 'Service temporarily unavailable'},
                {'success': False, 'error': 'Rate limit exceeded'},
                ConnectionError('GitHub API unreachable'),
                {'success': True, 'pull_request': {'mergeable': True, 'mergeable_state': 'clean', 'draft': False}}
            ]
            
            response_index = 0
            def mock_api_failure(pr_number):
                nonlocal response_index
                """mock_api_failureメソッド"""
                response = api_failure_responses[response_index % len(api_failure_responses)]
                response_index += 1
                
                if isinstance(response, Exception):
                    raise response
                return response
            
            mock_client = Mock()
            mock_client._get_pull_request = Mock(side_effect=mock_api_failure)
            mock_client._enable_auto_merge = Mock(return_value={"success": True})
            
            config = {
                MergeableState.UNKNOWN: RetryConfig(
                    max_retries=5, base_delay=0.1, timeout=10
                )
            }
            
            engine = SmartMergeRetryEngine(mock_client)
            result = await engine.attempt_smart_merge(30, custom_config=config)
            
            if result.get('success') or 'error' in result:
                scenarios_tested['github_api_failure'] = True
                print("   ✅ GitHub API障害に適切に対応")
            else:
                print("   ❌ GitHub API障害対応に問題")
            
            # 3.2 同時実行時のエラー処理
            print("   ⚡ 3.2 同時実行エラー処理テスト")
            
            concurrent_tasks = []
            
            for i in range(5):  # 5つの同時実行
                mock_concurrent_client = Mock()
                mock_concurrent_client._get_pull_request = Mock(return_value={
                    'success': True,
                    'pull_request': {'mergeable': True, 'mergeable_state': 'clean', 'draft': False}
                })
                mock_concurrent_client._enable_auto_merge = Mock(return_value={"success": True})
                
                engine_concurrent = SmartMergeRetryEngine(mock_concurrent_client)
                task = asyncio.create_task(engine_concurrent.attempt_smart_merge(40 + i))
                concurrent_tasks.append(task)
            
            concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            
            successful_tasks = sum(1 for r in concurrent_results if isinstance(r, dict) and r.get('success'))
            if successful_tasks >= 4:  # 5つ中4つ以上成功
                scenarios_tested['concurrent_execution'] = True
                print(f"   ✅ 同時実行処理成功: {successful_tasks}/5")
            else:
                print(f"   ❌ 同時実行処理に問題: {successful_tasks}/5成功")
            
            # 3.3 不正なレスポンス処理
            print("   🔧 3.3 不正なレスポンス処理テスト")
            
            malformed_client = Mock()
            malformed_client._get_pull_request = Mock(return_value={
                'success': True,
                'pull_request': {
                    # 不正な値
                    'mergeable': 'invalid_value',  # boolean期待
                    'mergeable_state': None,       # 文字列期待 
                    'draft': 'not_boolean'         # boolean期待
                }
            })
            
            engine_malformed = SmartMergeRetryEngine(malformed_client)
            malformed_result = await engine_malformed.attempt_smart_merge(50)
            
            # エラーなく処理されることを確認
            if 'error' in malformed_result or malformed_result.get('success') is False:
                scenarios_tested['malformed_response'] = True
                print("   ✅ 不正なレスポンスが適切に処理")
            else:
                print("   ❌ 不正なレスポンス処理に問題")
                
        except Exception as e:
            print(f"   ❌ 障害シナリオテスト中にエラー: {e}")
        
        scenario_success_rate = sum(scenarios_tested.values()) / len(scenarios_tested)
        self.resilience_scores['scenarios'] = scenario_success_rate * 100
        print(f"   📊 障害シナリオ対応率: {scenario_success_rate*100:0.1f}%\n")
    
    async def _test_stress_conditions(self):
        """実際のストレステスト"""
        print("💪 4.0 ストレステスト")
        
        stress_results = {
            'high_error_rate': 0,
            'long_running': 0,
            'resource_efficiency': 0
        }
        
        try:
            from smart_merge_retry import SmartMergeRetryEngine, RetryConfig, MergeableState
            
            # 4.1 大量エラー発生時のテスト
            print("   🔥 4.1 大量エラー発生時の安定性テスト")
            
            error_count = 0
            def high_error_rate_mock(pr_number):
                """high_error_rate_mockメソッド"""
                nonlocal error_count
                error_count += 1
                
                # 80%の確率でエラー
                if error_count % 5 != 0:
                    if error_count % 3 == 0:
                        raise ConnectionError("Network error")
                    elif error_count % 3 == 1:
                        return {'success': False, 'error': 'API error'}
                    else:
                        return {
                            'success': True,
                            'pull_request': {'mergeable': None, 'mergeable_state': 'unstable', 'draft': False}
                        }
                else:
                    return {
                        'success': True,
                        'pull_request': {'mergeable': True, 'mergeable_state': 'clean', 'draft': False}
                    }
            
            high_error_client = Mock()
            high_error_client._get_pull_request = Mock(side_effect=high_error_rate_mock)
            high_error_client._enable_auto_merge = Mock(return_value={"success": True})
            
            config_stress = {
                MergeableState.UNSTABLE: RetryConfig(
                    max_retries=10, base_delay=0.5, max_delay=0.2, timeout=5
                ),
                MergeableState.UNKNOWN: RetryConfig(
                    max_retries=5, base_delay=0.5, max_delay=0.1, timeout=3
                )
            }
            
            engine_stress = SmartMergeRetryEngine(high_error_client)
            
            stress_tasks = []
            for i in range(10):  # 10個のPRを並行処理
                task = asyncio.create_task(
                    engine_stress.attempt_smart_merge(60 + i, custom_config=config_stress)
                )
                stress_tasks.append(task)
            
            start_stress_time = time.time()
            stress_results_list = await asyncio.gather(*stress_tasks, return_exceptions=True)
            end_stress_time = time.time()
            
            successful_stress = sum(
                1 for r in stress_results_list 
                if isinstance(r, dict) and r.get('success')
            )
            
            if successful_stress >= 7:  # 70%以上成功
                stress_results['high_error_rate'] = 80
                print(f"   ✅ 高エラー率環境で {successful_stress}/10 成功")
            elif successful_stress >= 5:
                stress_results['high_error_rate'] = 60
                print(f"   ⚠️ 高エラー率環境で {successful_stress}/10 成功 (改善余地あり)")
            else:
                stress_results['high_error_rate'] = 30
                print(f"   ❌ 高エラー率環境で {successful_stress}/10 成功 (問題あり)")
            
            # 4.2 実行時間効率性
            execution_time = end_stress_time - start_stress_time
            if execution_time < 10:  # 10秒以内
                stress_results['resource_efficiency'] = 90
                print(f"   ✅ 実行時間効率: {execution_time:0.2f}秒")
            elif execution_time < 20:
                stress_results['resource_efficiency'] = 70
                print(f"   ⚠️ 実行時間: {execution_time:0.2f}秒 (改善可能)")
            else:
                stress_results['resource_efficiency'] = 40
                print(f"   ❌ 実行時間: {execution_time:0.2f}秒 (非効率)")
            
            # 4.3 統計・監視機能テスト
            print("   📊 4.3 統計・監視機能テスト")
            
            stats = engine_stress.get_statistics()
            
            expected_stats = ['total_prs', 'successful_prs', 'success_rate', 'average_attempts', 'total_attempts']
            stats_available = sum(1 for stat in expected_stats if stat in stats)
            
            if stats_available >= 4:
                stress_results['long_running'] = 85
                print(f"   ✅ 統計機能充実: {stats_available}/{len(expected_stats)}項目")
                print(f"   📈 統計データ: {stats}")
            else:
                stress_results['long_running'] = 50
                print(f"   ⚠️ 統計機能不十分: {stats_available}/{len(expected_stats)}項目")
                
        except Exception as e:
            print(f"   ❌ ストレステスト中にエラー: {e}")
            stress_results = {'high_error_rate': 20, 'long_running': 20, 'resource_efficiency': 20}
        
        avg_stress_score = sum(stress_results.values()) / len(stress_results)
        self.resilience_scores['stress'] = avg_stress_score
        print(f"   📊 ストレステストスコア: {avg_stress_score:0.1f}/100\n")
    
    def _generate_analysis_report(self):
        """分析結果レポート生成"""
        print("📋 === Smart Merge Retry エラーハンドリング・レジリエンス分析レポート ===\n")
        
        # 1.0 エラーハンドリング分析結果
        print("🔍 1.0 エラーハンドリングパターン分析結果:")
        for pattern, tested in self.error_patterns.items():
            status = "✅ 適切" if tested else "❌ 問題あり"
            print(f"   - {pattern}: {status}")
        
        error_coverage = sum(self.error_patterns.values()) / len(self.error_patterns) * 100
        print(f"   📊 エラー処理網羅率: {error_coverage:0.1f}%")
        
        # 2.0 レジリエンス評価結果
        print(f"\n🛡️ 2.0 レジリエンス機能評価結果:")
        print(f"   - 基本機能スコア: {self.resilience_scores.get('basic', 0):0.1f}/100")
        print(f"   - 障害シナリオ対応: {self.resilience_scores.get('scenarios', 0):0.1f}/100") 
        print(f"   - ストレステスト: {self.resilience_scores.get('stress', 0):0.1f}/100")
        
        overall_resilience = sum(self.resilience_scores.values()) / len(self.resilience_scores)
        print(f"   📊 総合レジリエンススコア: {overall_resilience:0.1f}/100")
        
        # 3.0 改善提案
        print(f"\n💡 3.0 改善提案:")
        
        if error_coverage < 80:
            print("   🔧 エラーハンドリング改善が必要:")
            print("      - より具体的な例外処理の実装")
            print("      - エラーメッセージの詳細化")
            print("      - ログ出力レベルの最適化")
        
        if self.resilience_scores.get('basic', 0) < 70:
            print("   ⚡ リトライ機構改善が必要:")
            print("      - サーキットブレーカーパターンの実装")
            print("      - 適応的バックオフ戦略の改良")
            print("      - デッドロック防止機構の追加")
        
        if self.resilience_scores.get('stress', 0) < 70:
            print("   💪 パフォーマンス改善が必要:")
            print("      - 非同期処理の最適化")
            print("      - メモリ使用量の削減")
            print("      - 並行実行時の競合状態対策")
        
        # 4.0 推奨アクション
        print(f"\n🎯 4.0 推奨アクション:")
        
        if overall_resilience >= 80:
            print("   ✅ 優秀: 現在のシステムは十分に堅牢です")
        elif overall_resilience >= 60:
            print("   ⚠️ 良好: いくつかの改善で更なる向上が期待できます")
            print("      1.0 エラーログの構造化")
            print("      2.0 メトリクス収集の強化")
            print("      3.0 アラート機構の実装")
        else:
            print("   ❌ 要改善: システムの安定性に問題があります")
            print("      1.0 基本的なエラーハンドリングの見直し")
            print("      2.0 リトライロジックの再設計")
            print("      3.0 障害回復機能の強化")
            print("      4.0 包括的なテストスイートの作成")
        
        # 結果をファイルに保存
        analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'error_patterns': self.error_patterns,
            'resilience_scores': self.resilience_scores,
            'overall_score': overall_resilience,
            'recommendations': self._get_recommendations(overall_resilience)
        }
        
        with open('/home/aicompany/ai_co/smart_merge_analysis_result.json', 'w') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 詳細な分析結果は smart_merge_analysis_result.json に保存されました")
    
    def _get_recommendations(self, overall_score: float) -> List[str]:
        """スコアに基づく推奨事項を取得"""
        recommendations = []
        
        if overall_score < 60:
            recommendations.extend([
                "基本的なエラーハンドリングの全面見直し",
                "リトライロジックの再設計",
                "例外処理の網羅性確認",
                "ログ出力の構造化"
            ])
        elif overall_score < 80:
            recommendations.extend([
                "サーキットブレーカーパターンの実装",
                "アダプティブバックオフ戦略の導入",
                "メトリクス収集機能の強化",
                "アラート機構の実装"
            ])
        else:
            recommendations.extend([
                "現在のシステムは良好に動作しています",
                "定期的な監視とメンテナンスを継続してください",
                "負荷テストの定期実行を推奨します"
            ])
            
        return recommendations


# メイン実行
async def main():
    """メイン実行関数"""
    test_suite = ErrorAnalysisTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())