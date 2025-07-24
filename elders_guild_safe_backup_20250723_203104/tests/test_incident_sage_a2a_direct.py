#!/usr/bin/env python3
"""
🚨 Incident Sage A2A Agent - 直接テストスイート（A2A依存なし）
==================================================

Elder Loop Phase 3: A2A依存を避けた直接ビジネスロジックテスト
Knowledge Sageパターン適用：段階的テスト戦略

Author: Claude Elder
Created: 2025-07-23
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

# Incident Sage imports
import sys
sys.path.append("/home/aicompany/ai_co/elders_guild")
from incident_sage.business_logic import IncidentProcessor


class TestIncidentSageA2ADirect:
    pass


"""Incident Sage A2A Direct Test（A2A依存なし）"""
        self.test_results = {}
        self.logger = logging.getLogger("incident_sage_direct_test")
    
    async def run_direct_tests(self) -> Dict[str, Any]:
        pass

        """直接テスト実行"""
            print(f"\\n🧪 {test_name.replace('_', ' ').title()} 実行中...")
            try:
                start_time = time.time()
                result = await test_method()
                end_time = time.time()
                
                self.test_results[test_name] = {
                    "passed": result,
                    "duration": end_time - start_time
                }
                
                if result:
                    passed_tests += 1
                    print(f"   ✅ {test_name} 成功 ({self.test_results[test_name]['duration']:0.3f}s)")
                else:
                    print(f"   ❌ {test_name} 失敗")
                    
            except Exception as e:
                print(f"   💥 {test_name} エラー: {e}")
                self.test_results[test_name] = {
                    "passed": False,
                    "error": str(e),
                    "duration": 0
                }
        
        # 総合結果
        success_rate = (passed_tests / total_tests) * 100
        total_duration = sum(r.get("duration", 0) for r in self.test_results.values())
        
        print(f"\\n📊 直接テスト結果サマリー")
        print("=" * 70)
        print(f"合格テスト: {passed_tests}/{total_tests} ({success_rate:0.1f}%)")
        print(f"総実行時間: {total_duration:0.3f}秒")
        print(f"平均テスト時間: {total_duration/total_tests:0.3f}秒")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "test_results": self.test_results
        }
    
    async def test_processor_initialization(self) -> bool:
        pass

        """プロセッサ初期化テスト"""
            # IncidentProcessor初期化
            processor = IncidentProcessor()
            
            # 初期化確認
            if not processor.quality_standards:
                print(f"     ❌ デフォルト品質基準が初期化されていない")
                return False
            
            if "elder_guild_quality_standard" not in str(processor.quality_standards):
                print(f"     ❌ Elder Guild品質基準が見つからない")
                return False
            
            # データベース確認
            if not processor.db_path.exists():
                print(f"     ❌ データベースファイルが作成されていない")
                return False
            
            print(f"     ✅ プロセッサ初期化成功: {len(processor.quality_standards)}品質基準")
            return True
            
        except Exception as e:
            print(f"     💥 プロセッサ初期化エラー: {e}")
            return False
    
    async def test_incident_detection(self) -> bool:
        pass

            """インシデント検知テスト"""
            processor = IncidentProcessor()
            
            # 異常データでインシデント検知
            test_data = {
                "anomaly_data": {
                    "component": "payment_service",
                    "metric": "error_rate",
                    "value": 15.5,
                    "threshold": 10.0,
                    "severity": "critical",
                    "confidence": 0.95
                }
            }
            
            result = await processor.process_action("detect_incident", test_data)
            
            # 結果検証
            if not result.get("success"):
                print(f"     ❌ インシデント検知失敗: {result.get('error')}")
                return False
            
            incident_data = result.get("data", {})
            
            # 必須フィールド確認
            required_fields = ["incident_id", "title", "severity", "category", "status"]
            for field in required_fields:
                if field not in incident_data:
                    print(f"     ❌ 必須フィールド不足: {field}")
                    return False
            
            # 自動対応トリガー確認
            if incident_data["severity"] == "critical" and not incident_data.get("auto_response_triggered"):
                print(f"     ❌ Critical重要度で自動対応がトリガーされていない")
                return False
            
            print(f"     ✅ インシデント検知成功: {incident_data['incident_id']} ({incident_data['severity']})")
            return True
            
        except Exception as e:
            print(f"     💥 インシデント検知テストエラー: {e}")
            return False
    
    async def test_incident_response(self) -> bool:
        pass

            """インシデント対応テスト"""
            processor = IncidentProcessor()
            
            # インシデント作成
            detection_data = {
                "anomaly_data": {
                    "component": "database_service",
                    "metric": "connection_failure",
                    "severity": "high"
                }
            }
            
            detection_result = await processor.process_action("detect_incident", detection_data)
            incident_id = detection_result["data"]["incident_id"]
            
            # インシデント対応実行
            response_data = {"incident_id": incident_id}
            response_result = await processor.process_action("respond_to_incident", response_data)
            
            if not response_result.get("success"):
                print(f"     ❌ インシデント対応失敗: {response_result.get('error')}")
                return False
            
            response_info = response_result.get("data", {})
            
            # 対応結果確認
            required_fields = ["response_status", "effectiveness_score", "execution_steps"]
            for field in required_fields:
                if field not in response_info:
                    print(f"     ❌ 対応結果フィールド不足: {field}")
                    return False
            
            if not response_info["execution_steps"]:
                print(f"     ❌ 実行ステップが空")
                return False
            
            print(f"     ✅ インシデント対応成功: {response_info['response_status']} "
                  f"(効果: {response_info['effectiveness_score']:0.1f})")
            return True
            
        except Exception as e:
            print(f"     💥 インシデント対応テストエラー: {e}")
            return False
    
    async def test_quality_assessment(self) -> bool:
        pass

            """品質評価テスト"""
            processor = IncidentProcessor()
            
            # デフォルト品質基準取得
            default_standard_id = list(processor.quality_standards.keys())[0]
            
            # 品質評価実行
            assessment_data = {
                "standard_id": default_standard_id,
                "component": "payment_api",
                "metrics": {
                    "test_coverage": 88.5,
                    "iron_will_compliance": 100.0,
                    "code_quality_score": 85.2
                }
            }
            
            result = await processor.process_action("assess_quality", assessment_data)
            
            if not result.get("success"):
                print(f"     ❌ 品質評価失敗: {result.get('error')}")
                return False
            
            assessment_info = result.get("data", {})
            
            # 評価結果確認
            required_fields = ["assessment_id", "overall_score", "compliance_score", "is_compliant"]
            for field in required_fields:
                if field not in assessment_info:
                    print(f"     ❌ 評価結果フィールド不足: {field}")
                    return False
            
            # スコア範囲確認
            overall_score = assessment_info["overall_score"]
            if not (0 <= overall_score <= 100):
                print(f"     ❌ 総合スコア範囲外: {overall_score}")
                return False
            
            print(f"     ✅ 品質評価成功: {overall_score:0.1f}% "
                  f"(コンプライアンス: {assessment_info['is_compliant']})")
            return True
            
        except Exception as e:
            print(f"     💥 品質評価テストエラー: {e}")
            return False
    
    async def test_alert_management(self) -> bool:
        pass

            """アラート管理テスト"""
            processor = IncidentProcessor()
            
            # アラートルール作成
            rule_data = {
                "alert_rule": {
                    "name": "CPU Usage Alert",
                    "description": "CPU使用率監視アラート",
                    "condition_expression": "cpu_usage > 85.0",
                    "severity": "high",
                    "enabled": True
                }
            }
            
            create_result = await processor.process_action("create_alert_rule", rule_data)
            
            if not create_result.get("success"):
                print(f"     ❌ アラートルール作成失敗: {create_result.get('error')}")
                return False
            
            rule_info = create_result.get("data", {})
            rule_id = rule_info.get("rule_id")
            
            if not rule_id:
                print(f"     ❌ アラートルールID生成失敗")
                return False
            
            # アラートルール評価
            eval_data = {
                "metrics": {
                    "cpu_usage": 90.5  # 閾値85.0を超過
                }
            }
            
            eval_result = await processor.process_action("evaluate_alert_rules", eval_data)
            
            if not eval_result.get("success"):
                print(f"     ❌ アラートルール評価失敗: {eval_result.get('error')}")
                return False
            
            eval_info = eval_result.get("data", {})
            triggered_alerts = eval_info.get("triggered_alerts", [])
            
            # トリガーされたアラート確認
            if not triggered_alerts:
                print(f"     ❌ 閾値超過でアラートがトリガーされなかった")
                return False
            
            print(f"     ✅ アラート管理成功: ルール作成・評価完了 ({len(triggered_alerts)}アラート)")
            return True
            
        except Exception as e:
            print(f"     💥 アラート管理テストエラー: {e}")
            return False
    
    async def test_monitoring_management(self) -> bool:
        pass

            """監視管理テスト"""
            processor = IncidentProcessor()
            
            # 監視対象登録
            target_data = {
                "target": {
                    "name": "API Gateway",
                    "type": "api_service",
                    "endpoint_url": "https://api.example.com",
                    "health_check_enabled": True
                }
            }
            
            register_result = await processor.process_action("register_monitoring_target", target_data)
            
            if not register_result.get("success"):
                print(f"     ❌ 監視対象登録失敗: {register_result.get('error')}")
                return False
            
            target_info = register_result.get("data", {})
            target_id = target_info.get("target_id")
            
            if not target_id:
                print(f"     ❌ 監視対象ID生成失敗")
                return False
            
            # ヘルスチェック実行
            health_data = {"target_id": target_id}
            health_result = await processor.process_action("check_target_health", health_data)
            
            if not health_result.get("success"):
                print(f"     ❌ ヘルスチェック失敗: {health_result.get('error')}")
                return False
            
            health_info = health_result.get("data", {})
            
            # ヘルス結果確認
            required_fields = ["target_id", "status", "response_time_ms", "uptime_percentage"]
            for field in required_fields:
                if field not in health_info:
                    print(f"     ❌ ヘルス結果フィールド不足: {field}")
                    return False
            
            print(f"     ✅ 監視管理成功: 登録・ヘルスチェック完了 ({health_info['status']})")
            return True
            
        except Exception as e:
            print(f"     💥 監視管理テストエラー: {e}")
            return False
    
    async def test_pattern_learning(self) -> bool:
        pass

            """パターン学習テスト"""
            processor = IncidentProcessor()
            
            # 複数のインシデントを作成（同じカテゴリ）
            incidents_data = [
                {
                    "anomaly_data": {
                        "component": "auth_service",
                        "metric": "login_failure_rate",
                        "severity": "medium",
                        "category": "security"
                    }
                },
                {
                    "anomaly_data": {
                        "component": "auth_service",
                        "metric": "token_validation_error",
                        "severity": "high", 
                        "category": "security"
                    }
                }
            ]
            
            # インシデント作成
            for incident_data in incidents_data:
                await processor.process_action("detect_incident", incident_data)
            
            # パターン学習実行
            learning_result = await processor.process_action("learn_incident_patterns", {})
            
            if not learning_result.get("success"):
                print(f"     ❌ パターン学習失敗: {learning_result.get('error')}")
                return False
            
            learning_info = learning_result.get("data", {})
            patterns_learned = learning_info.get("patterns_learned", 0)
            total_incidents = learning_info.get("total_incidents_analyzed", 0)
            
            # 学習結果確認
            if total_incidents == 0:
                print(f"     ❌ インシデント分析数が0")
                return False
            
            # パターンが学習されなくても正常（少数データのため）
            print(f"     ✅ パターン学習成功: {patterns_learned}パターン学習 ({total_incidents}インシデント分析)")
            return True
            
        except Exception as e:
            print(f"     💥 パターン学習テストエラー: {e}")
            return False
    
    async def test_correlation_analysis(self) -> bool:
        pass

            """相関分析テスト"""
            processor = IncidentProcessor()
            
            # 時間的に近接したインシデントを作成
            incidents_data = [
                {
                    "anomaly_data": {
                        "component": "frontend_app",
                        "metric": "page_load_time",
                        "severity": "medium"
                    }
                },
                {
                    "anomaly_data": {
                        "component": "backend_api",
                        "metric": "response_time",
                        "severity": "medium"
                    }
                }
            ]
            
            # インシデント作成
            for incident_data in incidents_data:
                await processor.process_action("detect_incident", incident_data)
            
            # 相関分析実行
            correlation_result = await processor.process_action("analyze_correlations", {})
            
            if not correlation_result.get("success"):
                print(f"     ❌ 相関分析失敗: {correlation_result.get('error')}")
                return False
            
            correlation_info = correlation_result.get("data", {})
            correlations = correlation_info.get("correlations", [])
            analyzed_incidents = correlation_info.get("analyzed_incidents", 0)
            
            # 分析結果確認
            if analyzed_incidents == 0:
                print(f"     ❌ 分析インシデント数が0")
                return False
            
            print(f"     ✅ 相関分析成功: {len(correlations)}相関検出 ({analyzed_incidents}インシデント分析)")
            return True
            
        except Exception as e:
            print(f"     💥 相関分析テストエラー: {e}")
            return False
    
    async def test_automated_remediation(self) -> bool:
        pass

            """自動修復テスト"""
            processor = IncidentProcessor()
            
            # インシデント作成
            detection_data = {
                "anomaly_data": {
                    "component": "cache_service",
                    "metric": "memory_usage",
                    "severity": "high",
                    "category": "performance"
                }
            }
            
            detection_result = await processor.process_action("detect_incident", detection_data)
            incident_id = detection_result["data"]["incident_id"]
            
            # 自動修復試行
            remediation_data = {"incident_id": incident_id}
            remediation_result = await processor.process_action("attempt_automated_remediation", remediation_data)
            
            if not remediation_result.get("success"):
                print(f"     ❌ 自動修復失敗: {remediation_result.get('error')}")
                return False
            
            remediation_info = remediation_result.get("data", {})
            
            # 修復結果確認
            required_fields = ["status", "incident_id"]
            for field in required_fields:
                if field not in remediation_info:
                    print(f"     ❌ 修復結果フィールド不足: {field}")
                    return False
            
            remediation_status = remediation_info["status"]
            if remediation_status not in ["success", "failed", "no_action"]:
                print(f"     ❌ 修復ステータス不正: {remediation_status}")
                return False
            
            print(f"     ✅ 自動修復成功: {remediation_status}")
            return True
            
        except Exception as e:
            print(f"     💥 自動修復テストエラー: {e}")
            return False
    
    async def test_similar_incidents_search(self) -> bool:
        pass

            """類似インシデント検索テスト"""
            processor = IncidentProcessor()
            
            # 検索対象インシデント作成
            incidents_data = [
                {
                    "anomaly_data": {
                        "component": "search_service",
                        "metric": "query_timeout",
                        "severity": "medium"
                    }
                },
                {
                    "anomaly_data": {
                        "component": "search_index",
                        "metric": "indexing_error",
                        "severity": "low"
                    }
                }
            ]
            
            # インシデント作成
            for incident_data in incidents_data:
                await processor.process_action("detect_incident", incident_data)
            
            # 類似検索実行
            search_data = {"query": "search service timeout"}
            search_result = await processor.process_action("search_similar_incidents", search_data)
            
            if not search_result.get("success"):
                print(f"     ❌ 類似インシデント検索失敗: {search_result.get('error')}")
                return False
            
            search_info = search_result.get("data", {})
            similar_incidents = search_info.get("similar_incidents", [])
            total_matches = search_info.get("total_matches", 0)
            
            # 検索結果確認
            if total_matches != len(similar_incidents):
                print(f"     ❌ 検索結果数不一致: {total_matches} != {len(similar_incidents)}")
                return False
            
            # 類似度確認
            for incident in similar_incidents:
                if "similarity" not in incident:
                    print(f"     ❌ 類似度フィールドなし")
                    return False
                
                if not (0 <= incident["similarity"] <= 1):
                    print(f"     ❌ 類似度範囲外: {incident['similarity']}")
                    return False
            
            print(f"     ✅ 類似インシデント検索成功: {total_matches}件マッチ")
            return True
            
        except Exception as e:
            print(f"     💥 類似インシデント検索テストエラー: {e}")
            return False
    
    async def test_statistics_comprehensive(self) -> bool:
        pass

            """統計情報包括テスト"""
            processor = IncidentProcessor()
            
            # いくつかのデータを作成
            await processor.process_action("detect_incident", {
                "anomaly_data": {"component": "test", "severity": "medium"}
            })
            
            # 統計情報取得
            stats_result = await processor.process_action("get_statistics", {})
            
            if not stats_result.get("success"):
                print(f"     ❌ 統計情報取得失敗: {stats_result.get('error')}")
                return False
            
            stats_info = stats_result.get("data", {})
            
            # 必須統計セクション確認
            required_sections = [
                "incident_statistics", "quality_statistics", 
                "alert_statistics", "monitoring_statistics", "operational_metrics"
            ]
            
            for section in required_sections:
                if section not in stats_info:
                    print(f"     ❌ 統計セクション不足: {section}")
                    return False
            
            # インシデント統計詳細確認
            incident_stats = stats_info["incident_statistics"]
            required_incident_fields = [
                "total_incidents", "incidents_by_status", "incidents_by_severity", 
                "resolution_rate", "average_resolution_time_minutes"
            ]
            
            for field in required_incident_fields:
                if field not in incident_stats:
                    print(f"     ❌ インシデント統計フィールド不足: {field}")
                    return False
            
            # 運用メトリクス取得
            metrics_result = await processor.process_action("get_operational_metrics", {})
            
            if not metrics_result.get("success"):
                print(f"     ❌ 運用メトリクス取得失敗: {metrics_result.get('error')}")
                return False
            
            print(f"     ✅ 統計情報包括テスト成功: 全セクション確認完了")
            return True
            
        except Exception as e:
            print(f"     💥 統計情報テストエラー: {e}")
            return False
    
    async def test_health_check(self) -> bool:
        pass

            """ヘルスチェックテスト"""
            processor = IncidentProcessor()
            
            # ヘルスチェック実行
            health_result = await processor.process_action("health_check", {})
            
            if not health_result.get("success"):
                print(f"     ❌ ヘルスチェック失敗: {health_result.get('error')}")
                return False
            
            health_info = health_result.get("data", {})
            
            # ヘルス情報確認
            required_fields = ["status", "agent_name", "incidents_managed"]
            for field in required_fields:
                if field not in health_info:
                    print(f"     ❌ ヘルス情報フィールド不足: {field}")
                    return False
            
            if health_info["status"] != "healthy":
                print(f"     ❌ ヘルスステータス異常: {health_info['status']}")
                return False
            
            print(f"     ✅ ヘルスチェック成功: {health_info['status']}")
            return True
            
        except Exception as e:
            print(f"     💥 ヘルスチェックテストエラー: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        pass

            """エラーハンドリングテスト"""
            processor = IncidentProcessor()
            
            # エラーケーステスト
            error_test_cases = [
                {
                    "name": "無効なアクション",
                    "action": "invalid_action",
                    "data": {}
                },
                {
                    "name": "存在しないインシデント対応",
                    "action": "respond_to_incident",
                    "data": {"incident_id": "non_existent_incident"}
                },
                {
                    "name": "存在しない品質基準評価",
                    "action": "assess_quality",
                    "data": {
                        "standard_id": "non_existent_standard",
                        "component": "test"
                    }
                },
                {
                    "name": "存在しない監視対象ヘルスチェック",
                    "action": "check_target_health",
                    "data": {"target_id": "non_existent_target"}
                }
            ]
            
            for test_case in error_test_cases:
                result = await processor.process_action(test_case["action"], test_case["data"])
                
                # エラーが適切に処理されているかチェック
                if result.get("success"):
                    print(f"     ❌ {test_case['name']}: エラーが検出されなかった")
                    return False
                
                if "error" not in result:
                    print(f"     ❌ {test_case['name']}: エラーメッセージがない")
                    return False
            
            print(f"     ✅ エラーハンドリング成功: 全エラーケース適切処理")
            return True
            
        except Exception as e:
            print(f"     💥 エラーハンドリングテストエラー: {e}")
            return False
    
    async def test_performance_basic(self) -> bool:
        pass

            """基本パフォーマンステスト"""
            processor = IncidentProcessor()
            
            # パフォーマンステスト
            test_operations = [
                ("detect_incident", {
                    "anomaly_data": {"component": "perf_test", "severity": "low"}
                }),
                ("get_statistics", {}),
                ("health_check", {}),
                ("learn_incident_patterns", {}),
                ("analyze_correlations", {})
            ]
            
            performance_results = []
            
            for operation, data in test_operations:
                start_time = time.time()
                result = await processor.process_action(operation, data)
                end_time = time.time()
                
                execution_time = end_time - start_time
                performance_results.append({
                    "operation": operation,
                    "execution_time": execution_time,
                    "success": result.get("success", False)
                })
                
                # 基本的なパフォーマンス閾値チェック（1秒）
                if execution_time > 1.0:
                    print(f"     ⚠️ {operation}: 実行時間が長い ({execution_time:0.3f}s)")
            
            # 全操作の成功確認
            failed_operations = [r for r in performance_results if not r["success"]]
            if failed_operations:
                print(f"     ❌ 失敗した操作: {[r['operation'] for r in failed_operations]}")
                return False
            
            avg_time = sum(r["execution_time"] for r in performance_results) / len(performance_results)
            
            print(f"     ✅ パフォーマンステスト成功: 平均実行時間 {avg_time:0.3f}秒")
            return True
            
        except Exception as e:
            print(f"     💥 パフォーマンステストエラー: {e}")
            return False


async def main():
    pass

            """メイン実行"""
        print(f"\\n🎉 Incident Sage直接テスト成功！")
        print(f"   成功率: {results['success_rate']:0.1f}%")
        print(f"   実行時間: {results['total_duration']:0.3f}秒")
        print(f"   平均テスト時間: {results['total_duration']/results['total_tests']:0.3f}秒")
        print(f"   🚨 Elder Loop Phase 3完了準備")
        return True
    else:
        print(f"\\n🔧 Incident Sage直接テストで調整が必要")
        print(f"   成功率: {results['success_rate']:0.1f}% (80%未満)")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)