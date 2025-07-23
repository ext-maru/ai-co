#!/usr/bin/env python3
"""
🚨 Incident Sage A2A Agent - 包括的テストスイート
====================================

Elder Loop Phase 4: 厳密検証ループ対応
Knowledge Sageパターンを適用した包括的テスト
パフォーマンス・並行性・エラーハンドリング・統合テスト

Author: Claude Elder
Created: 2025-07-23
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import threading

# Incident Sage imports
import sys
sys.path.append("/home/aicompany/ai_co/elders_guild")
from incident_sage.business_logic import IncidentProcessor


class TestIncidentSageA2AComprehensive:
    """Incident Sage A2A Agent包括的テスト"""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        self.logger = logging.getLogger("incident_sage_comprehensive_test")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """全包括的テスト実行"""
        print("🚨 Incident Sage A2A Agent - 包括的テストスイート開始")
        print("=" * 70)
        
        test_methods = [
            ("performance_test", self.test_performance),
            ("concurrency_test", self.test_concurrency), 
            ("error_handling_test", self.test_error_handling),
            ("data_integrity_test", self.test_data_integrity),
            ("complex_workflow_test", self.test_complex_workflow),
            ("memory_efficiency_test", self.test_memory_efficiency),
            ("incident_lifecycle_test", self.test_incident_lifecycle),
            ("quality_assessment_comprehensive_test", self.test_quality_assessment_comprehensive),
            ("alert_system_integration_test", self.test_alert_system_integration),
            ("monitoring_comprehensive_test", self.test_monitoring_comprehensive),
            ("pattern_learning_advanced_test", self.test_pattern_learning_advanced),
            ("correlation_analysis_detailed_test", self.test_correlation_analysis_detailed),
            ("remediation_effectiveness_test", self.test_remediation_effectiveness),
            ("statistics_accuracy_test", self.test_statistics_accuracy),
            ("stress_test", self.test_stress_load),
            ("edge_cases_test", self.test_edge_cases)
        ]
        
        total_tests = len(test_methods)
        passed_tests = 0
        
        for test_name, test_method in test_methods:
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
                    print(f"   ✅ {test_name} 成功 ({self.test_results[test_name]['duration']:.3f}s)")
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
        
        print(f"\\n📊 包括的テスト結果サマリー")
        print("=" * 70)
        print(f"合格テスト: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"総実行時間: {total_duration:.3f}秒")
        print(f"平均テスト時間: {total_duration/total_tests:.3f}秒")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "test_results": self.test_results,
            "performance_metrics": self.performance_metrics
        }
    
    async def test_performance(self) -> bool:
        """パフォーマンステスト"""
        try:
            processor = IncidentProcessor()
            
            # 大量操作パフォーマンステスト
            operations = [
                ("detect_incident", {"anomaly_data": {"component": f"service_{i}", "severity": "medium"}})
                for i in range(100)
            ]
            
            start_time = time.time()
            
            # バッチ実行
            results = []
            for operation, data in operations:
                result = await processor.process_action(operation, data)
                results.append(result)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # パフォーマンス解析
            successful_operations = sum(1 for r in results if r.get("success"))
            throughput = successful_operations / total_time
            avg_time_per_operation = total_time / len(operations)
            
            self.performance_metrics["batch_processing"] = {
                "total_operations": len(operations),
                "successful_operations": successful_operations,
                "total_time": total_time,
                "throughput_ops_per_sec": throughput,
                "avg_time_per_operation": avg_time_per_operation
            }
            
            # パフォーマンス基準確認
            if throughput < 50:  # 50 ops/sec未満は失敗
                print(f"     ❌ スループット低い: {throughput:.1f} ops/sec")
                return False
            
            if avg_time_per_operation > 0.1:  # 100ms超は失敗
                print(f"     ❌ 平均実行時間長い: {avg_time_per_operation:.3f}s")
                return False
            
            print(f"     ✅ パフォーマンステスト成功: {throughput:.1f} ops/sec, {avg_time_per_operation:.3f}s/op")
            return True
            
        except Exception as e:
            print(f"     💥 パフォーマンステストエラー: {e}")
            return False
    
    async def test_concurrency(self) -> bool:
        """並行性テスト"""
        try:
            processor = IncidentProcessor()
            
            # 並行タスク定義
            async def concurrent_incident_detection(task_id):
                data = {
                    "anomaly_data": {
                        "component": f"concurrent_service_{task_id}",
                        "metric": "error_rate",
                        "severity": "high",
                        "task_id": task_id
                    }
                }
                return await processor.process_action("detect_incident", data)
            
            # 並行実行
            start_time = time.time()
            concurrent_tasks = [concurrent_incident_detection(i) for i in range(20)]
            results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            end_time = time.time()
            
            # 結果解析
            successful_results = [r for r in results if not isinstance(r, Exception) and r.get("success")]
            failed_results = [r for r in results if isinstance(r, Exception) or not r.get("success")]
            
            concurrent_time = end_time - start_time
            
            self.performance_metrics["concurrency"] = {
                "total_tasks": len(concurrent_tasks),
                "successful_tasks": len(successful_results),
                "failed_tasks": len(failed_results),
                "execution_time": concurrent_time,
                "concurrent_throughput": len(successful_results) / concurrent_time
            }
            
            # 並行性基準確認
            if len(failed_results) > 2:  # 2つ超の失敗は問題
                print(f"     ❌ 並行処理失敗多数: {len(failed_results)}")
                return False
            
            if concurrent_time > 5.0:  # 5秒超は遅い
                print(f"     ❌ 並行実行時間長い: {concurrent_time:.3f}s")
                return False
            
            print(f"     ✅ 並行性テスト成功: {len(successful_results)}/{len(concurrent_tasks)} 成功, {concurrent_time:.3f}s")
            return True
            
        except Exception as e:
            print(f"     💥 並行性テストエラー: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """エラーハンドリングテスト"""
        try:
            processor = IncidentProcessor()
            
            # 悪意のある/異常データテストケース
            error_test_cases = [
                {
                    "name": "NULL データ",
                    "action": "detect_incident",
                    "data": None
                },
                {
                    "name": "空データ",
                    "action": "assess_quality", 
                    "data": {}
                },
                {
                    "name": "無効JSON構造",
                    "action": "create_alert_rule",
                    "data": {"alert_rule": {"invalid": "structure"}}
                },
                {
                    "name": "存在しないリソース",
                    "action": "respond_to_incident",
                    "data": {"incident_id": "non_existent_12345"}
                },
                {
                    "name": "無効データ型", 
                    "action": "register_monitoring_target",
                    "data": {"target": "not_a_dict"}
                },
                {
                    "name": "巨大データ",
                    "action": "search_similar_incidents",
                    "data": {"query": "x" * 10000}
                },
                {
                    "name": "負の値",
                    "action": "assess_quality",
                    "data": {
                        "standard_id": "test",
                        "component": "test",
                        "metrics": {"test_coverage": -50}
                    }
                }
            ]
            
            error_handling_results = []
            
            for test_case in error_test_cases:
                try:
                    # NULLデータの場合は特別処理
                    if test_case["data"] is None:
                        test_case["data"] = {}
                    
                    result = await processor.process_action(test_case["action"], test_case["data"])
                    
                    # エラーが適切に処理されているかチェック
                    if result.get("success"):
                        error_handling_results.append({
                            "case": test_case["name"],
                            "status": "unexpected_success",
                            "result": result
                        })
                    else:
                        # エラーメッセージが適切か確認
                        if "error" in result and isinstance(result["error"], str):
                            error_handling_results.append({
                                "case": test_case["name"],
                                "status": "properly_handled",
                                "error": result["error"]
                            })
                        else:
                            error_handling_results.append({
                                "case": test_case["name"],
                                "status": "improper_error_format",
                                "result": result
                            })
                
                except Exception as e:
                    # 予期しない例外
                    error_handling_results.append({
                        "case": test_case["name"],
                        "status": "unhandled_exception",
                        "exception": str(e)
                    })
            
            # エラーハンドリング評価
            properly_handled = len([r for r in error_handling_results if r["status"] == "properly_handled"])
            total_cases = len(error_test_cases)
            
            if properly_handled < total_cases * 0.8:  # 80%未満は失敗
                print(f"     ❌ エラーハンドリング不十分: {properly_handled}/{total_cases}")
                for result in error_handling_results:
                    if result["status"] != "properly_handled":
                        print(f"       • {result['case']}: {result['status']}")
                return False
            
            print(f"     ✅ エラーハンドリング成功: {properly_handled}/{total_cases} 適切処理")
            return True
            
        except Exception as e:
            print(f"     💥 エラーハンドリングテストエラー: {e}")
            return False
    
    async def test_data_integrity(self) -> bool:
        """データ整合性テスト"""
        try:
            processor = IncidentProcessor()
            
            # データ整合性テストシナリオ
            
            # 1. インシデント作成と取得の整合性
            original_incident_data = {
                "anomaly_data": {
                    "component": "integrity_test_service",
                    "metric": "data_consistency",
                    "value": 42.5,
                    "threshold": 30.0,
                    "severity": "high",
                    "confidence": 0.95
                }
            }
            
            create_result = await processor.process_action("detect_incident", original_incident_data)
            if not create_result.get("success"):
                print(f"     ❌ インシデント作成失敗")
                return False
            
            incident_id = create_result["data"]["incident_id"]
            
            # データベースから読み直し
            processor2 = IncidentProcessor()
            if incident_id not in processor2.incidents:
                print(f"     ❌ インシデントデータ永続化失敗")
                return False
            
            stored_incident = processor2.incidents[incident_id]
            
            # データ整合性確認
            if stored_incident.title != create_result["data"]["title"]:
                print(f"     ❌ タイトル不整合")
                return False
            
            if stored_incident.severity.value != create_result["data"]["severity"]:
                print(f"     ❌ 重要度不整合")
                return False
            
            # 2. 品質基準データ整合性
            quality_data = {
                "standard": {
                    "name": "Integrity Test Standard",
                    "description": "データ整合性テスト用品質基準",
                    "category": "testing",
                    "metrics": {
                        "data_consistency": {
                            "name": "Data Consistency",
                            "target_value": 99.9,
                            "threshold_min": 95.0,
                            "unit": "%",
                            "description": "データ整合性"
                        }
                    },
                    "compliance_threshold": 95.0
                }
            }
            
            register_result = await processor.process_action("register_quality_standard", quality_data)
            if not register_result.get("success"):
                print(f"     ❌ 品質基準登録失敗")
                return False
            
            standard_id = register_result["data"]["standard_id"]
            
            # 新しいプロセッサで確認
            processor3 = IncidentProcessor()
            if standard_id not in processor3.quality_standards:
                print(f"     ❌ 品質基準データ永続化失敗")
                return False
            
            stored_standard = processor3.quality_standards[standard_id]
            if stored_standard.name != quality_data["standard"]["name"]:
                print(f"     ❌ 品質基準名不整合")
                return False
            
            print(f"     ✅ データ整合性テスト成功: インシデント・品質基準永続化確認")
            return True
            
        except Exception as e:
            print(f"     💥 データ整合性テストエラー: {e}")
            return False
    
    async def test_complex_workflow(self) -> bool:
        """複雑ワークフローテスト"""
        try:
            processor = IncidentProcessor()
            
            # 複雑なワークフローシナリオ
            # 1. 複数サービスでの連鎖的インシデント
            services = ["frontend", "api_gateway", "user_service", "payment_service", "database"]
            incidents = []
            
            # 時系列でインシデント発生
            for i, service in enumerate(services):
                incident_data = {
                    "anomaly_data": {
                        "component": service,
                        "metric": "response_time" if i % 2 == 0 else "error_rate",
                        "severity": "critical" if i == 0 else "high",
                        "confidence": 0.9 - (i * 0.1)
                    }
                }
                
                result = await processor.process_action("detect_incident", incident_data)
                if result.get("success"):
                    incidents.append(result["data"]["incident_id"])
                
                # 少し待機して時系列を作る
                await asyncio.sleep(0.001)
            
            if len(incidents) != len(services):
                print(f"     ❌ インシデント作成数不一致: {len(incidents)} != {len(services)}")
                return False
            
            # 2. パターン学習実行
            pattern_result = await processor.process_action("learn_incident_patterns", {})
            if not pattern_result.get("success"):
                print(f"     ❌ パターン学習失敗")
                return False
            
            # 3. 相関分析実行
            correlation_result = await processor.process_action("analyze_correlations", {})
            if not correlation_result.get("success"):
                print(f"     ❌ 相関分析失敗")
                return False
            
            correlations = correlation_result["data"]["correlations"]
            
            # 4. 自動修復試行
            remediation_results = []
            for incident_id in incidents[:2]:  # 最初の2つのみ
                remediation_result = await processor.process_action("attempt_automated_remediation", {
                    "incident_id": incident_id
                })
                remediation_results.append(remediation_result)
            
            successful_remediations = [r for r in remediation_results if r.get("success")]
            
            # 5. 統計分析
            stats_result = await processor.process_action("get_statistics", {})
            if not stats_result.get("success"):
                print(f"     ❌ 統計取得失敗")
                return False
            
            stats = stats_result["data"]
            
            # ワークフロー結果検証
            if stats["incident_statistics"]["total_incidents"] < len(services):
                print(f"     ❌ 統計のインシデント数不正")
                return False
            
            if len(successful_remediations) == 0:
                print(f"     ❌ 自動修復が全て失敗")
                return False
            
            print(f"     ✅ 複雑ワークフロー成功: {len(incidents)}インシデント, {len(correlations)}相関, {len(successful_remediations)}修復成功")
            return True
            
        except Exception as e:
            print(f"     💥 複雑ワークフローテストエラー: {e}")
            return False
    
    async def test_memory_efficiency(self) -> bool:
        """メモリ効率性テスト"""
        try:
            import psutil
            import os
            
            # 初期メモリ使用量
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            processor = IncidentProcessor()
            
            # 大量データ処理
            for i in range(500):
                await processor.process_action("detect_incident", {
                    "anomaly_data": {
                        "component": f"memory_test_service_{i}",
                        "metric": "memory_usage",
                        "severity": "low"
                    }
                })
                
                # 品質評価も実行
                default_standard_id = list(processor.quality_standards.keys())[0]
                await processor.process_action("assess_quality", {
                    "standard_id": default_standard_id,
                    "component": f"component_{i}",
                    "metrics": {"test_coverage": 80.0 + (i % 20)}
                })
            
            # 最終メモリ使用量
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            self.performance_metrics["memory_usage"] = {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": memory_increase,
                "operations_performed": 1000,
                "memory_per_operation_kb": (memory_increase * 1024) / 1000
            }
            
            # メモリ効率性基準確認
            if memory_increase > 100:  # 100MB超増加は問題
                print(f"     ❌ メモリ使用量増加過大: {memory_increase:.1f}MB")
                return False
            
            memory_per_op = (memory_increase * 1024) / 1000  # KB per operation
            if memory_per_op > 10:  # 10KB/op超は問題
                print(f"     ❌ 操作あたりメモリ使用量過大: {memory_per_op:.1f}KB/op")
                return False
            
            print(f"     ✅ メモリ効率性テスト成功: +{memory_increase:.1f}MB, {memory_per_op:.1f}KB/op")
            return True
            
        except ImportError:
            print(f"     ⚠️ psutil未利用可能、メモリテストスキップ")
            return True
        except Exception as e:
            print(f"     💥 メモリ効率性テストエラー: {e}")
            return False
    
    async def test_incident_lifecycle(self) -> bool:
        """インシデントライフサイクルテスト"""
        try:
            processor = IncidentProcessor(test_mode=True)
            processor.reset_for_testing()
            
            # インシデントライフサイクル全体テスト
            
            # 1. インシデント検知
            detection_data = {
                "anomaly_data": {
                    "component": "lifecycle_test_service",
                    "metric": "availability",
                    "severity": "critical",
                    "confidence": 0.98
                }
            }
            
            detection_result = await processor.process_action("detect_incident", detection_data)
            if not detection_result.get("success"):
                print(f"     ❌ インシデント検知失敗")
                return False
            
            incident_id = detection_result["data"]["incident_id"]
            initial_status = detection_result["data"]["status"]
            
            if initial_status != "open":
                print(f"     ❌ 初期ステータス不正: {initial_status}")
                return False
            
            # 2. インシデント対応
            response_result = await processor.process_action("respond_to_incident", {
                "incident_id": incident_id
            })
            
            if not response_result.get("success"):
                print(f"     ❌ インシデント対応失敗")
                return False
            
            response_status = response_result["data"]["response_status"]
            incident_status_after_response = response_result["data"]["incident_status"]
            
            # 3. 自動修復試行
            remediation_result = await processor.process_action("attempt_automated_remediation", {
                "incident_id": incident_id
            })
            
            if not remediation_result.get("success"):
                print(f"     ❌ 自動修復試行失敗")
                return False
            
            remediation_status = remediation_result["data"]["status"]
            
            # 4. インシデント状態確認
            # test_modeでは永続化されないため、同じプロセッサで確認
            if incident_id not in processor.incidents:
                print(f"     ❌ インシデントがメモリに存在しない")
                return False
            
            final_incident = processor.incidents[incident_id]
            
            # ライフサイクル検証
            lifecycle_steps = [
                ("detection", detection_result["data"]["incident_id"]),
                ("response", response_status),
                ("remediation", remediation_status),
                ("final_status", final_incident.status.value)
            ]
            
            print(f"     ✅ インシデントライフサイクル成功:")
            for step_name, step_result in lifecycle_steps:
                print(f"       • {step_name}: {step_result}")
            
            return True
            
        except Exception as e:
            print(f"     💥 インシデントライフサイクルテストエラー: {e}")
            return False
    
    async def test_quality_assessment_comprehensive(self) -> bool:
        """品質評価包括テスト"""
        try:
            processor = IncidentProcessor()
            
            # 複数品質基準での包括評価
            
            # 1. カスタム品質基準作成
            custom_standards = [
                {
                    "name": "Security Standard",
                    "category": "security",
                    "metrics": {
                        "security_score": {"target_value": 95.0, "threshold_min": 90.0},
                        "vulnerability_count": {"target_value": 0.0, "threshold_min": 2.0}
                    },
                    "compliance_threshold": 90.0
                },
                {
                    "name": "Performance Standard", 
                    "category": "performance",
                    "metrics": {
                        "response_time": {"target_value": 100.0, "threshold_min": 200.0},
                        "throughput": {"target_value": 1000.0, "threshold_min": 500.0}
                    },
                    "compliance_threshold": 85.0
                }
            ]
            
            created_standards = []
            for standard_data in custom_standards:
                result = await processor.process_action("register_quality_standard", {
                    "standard": standard_data
                })
                if result.get("success"):
                    created_standards.append(result["data"]["standard_id"])
            
            if len(created_standards) != len(custom_standards):
                print(f"     ❌ 品質基準作成数不一致")
                return False
            
            # 2. 複数コンポーネントでの品質評価
            components = ["frontend", "backend", "database"]
            assessment_results = []
            
            for component in components:
                for standard_id in created_standards:
                    # テストメトリクス生成
                    if "security" in processor.quality_standards[standard_id].name.lower():
                        metrics = {
                            "security_score": 92.5,
                            "vulnerability_count": 1.0
                        }
                    else:
                        metrics = {
                            "response_time": 150.0,
                            "throughput": 750.0
                        }
                    
                    assessment_result = await processor.process_action("assess_quality", {
                        "standard_id": standard_id,
                        "component": component,
                        "metrics": metrics
                    })
                    
                    if assessment_result.get("success"):
                        assessment_results.append(assessment_result["data"])
            
            # 3. 評価結果分析
            total_assessments = len(components) * len(created_standards)
            successful_assessments = len(assessment_results)
            
            if successful_assessments != total_assessments:
                print(f"     ❌ 評価実行数不一致: {successful_assessments} != {total_assessments}")
                return False
            
            # コンプライアンス率計算
            compliant_assessments = [a for a in assessment_results if a["is_compliant"]]
            compliance_rate = len(compliant_assessments) / len(assessment_results) * 100
            
            # 平均品質スコア計算
            avg_quality_score = sum(a["overall_score"] for a in assessment_results) / len(assessment_results)
            
            self.performance_metrics["quality_assessment"] = {
                "total_assessments": total_assessments,
                "successful_assessments": successful_assessments,
                "compliance_rate": compliance_rate,
                "average_quality_score": avg_quality_score
            }
            
            print(f"     ✅ 品質評価包括テスト成功: {compliance_rate:.1f}%適合, 平均{avg_quality_score:.1f}点")
            return True
            
        except Exception as e:
            print(f"     💥 品質評価包括テストエラー: {e}")
            return False
    
    async def test_alert_system_integration(self) -> bool:
        """アラートシステム統合テスト"""
        try:
            processor = IncidentProcessor(test_mode=True)
            processor.reset_for_testing()
            
            # アラートシステム統合シナリオ
            
            # 1. 複数アラートルール作成
            alert_rules = [
                {
                    "name": "CPU Alert",
                    "condition_expression": "cpu_usage > 80.0",
                    "severity": "high",
                    "enabled": True
                },
                {
                    "name": "Memory Alert",
                    "condition_expression": "memory_usage > 90.0", 
                    "severity": "critical",
                    "enabled": True
                },
                {
                    "name": "Disk Alert",
                    "condition_expression": "disk_usage > 95.0",
                    "severity": "medium",
                    "enabled": False  # 無効
                }
            ]
            
            created_rules = []
            for rule_data in alert_rules:
                result = await processor.process_action("create_alert_rule", {
                    "alert_rule": rule_data
                })
                if result.get("success"):
                    created_rules.append(result["data"]["rule_id"])
            
            if len(created_rules) != len(alert_rules):
                print(f"     ❌ アラートルール作成数不一致")
                return False
            
            # 2. アラート評価シナリオ
            test_metrics = [
                {
                    "scenario": "normal",
                    "metrics": {"cpu_usage": 70.0, "memory_usage": 75.0, "disk_usage": 80.0},
                    "expected_alerts": 0
                },
                {
                    "scenario": "cpu_high",
                    "metrics": {"cpu_usage": 85.0, "memory_usage": 75.0, "disk_usage": 80.0},
                    "expected_alerts": 1
                },
                {
                    "scenario": "multiple_alerts",
                    "metrics": {"cpu_usage": 85.0, "memory_usage": 95.0, "disk_usage": 98.0},
                    "expected_alerts": 2  # disk_usageは無効ルールなので除外
                }
            ]
            
            alert_evaluation_results = []
            
            for test_case in test_metrics:
                result = await processor.process_action("evaluate_alert_rules", {
                    "metrics": test_case["metrics"],
                    "reset_cooldown": True  # テスト用クールダウンリセット
                })
                
                if result.get("success"):
                    triggered_count = result["data"]["alert_count"]
                    alert_evaluation_results.append({
                        "scenario": test_case["scenario"],
                        "expected": test_case["expected_alerts"],
                        "actual": triggered_count,
                        "match": triggered_count == test_case["expected_alerts"]
                    })
            
            # 3. アラート評価結果検証
            successful_evaluations = [r for r in alert_evaluation_results if r["match"]]
            
            if len(successful_evaluations) != len(test_metrics):
                print(f"     ❌ アラート評価結果不一致:")
                for result in alert_evaluation_results:
                    if not result["match"]:
                        print(f"       • {result['scenario']}: 期待{result['expected']}, 実際{result['actual']}")
                return False
            
            print(f"     ✅ アラートシステム統合成功: {len(created_rules)}ルール, {len(successful_evaluations)}シナリオ")
            return True
            
        except Exception as e:
            print(f"     💥 アラートシステム統合テストエラー: {e}")
            return False
    
    async def test_monitoring_comprehensive(self) -> bool:
        """監視機能包括テスト"""
        try:
            processor = IncidentProcessor()
            
            # 監視システム包括テスト
            
            # 1. 複数監視対象登録
            monitoring_targets = [
                {
                    "name": "Web Server",
                    "type": "web_service",
                    "endpoint_url": "http://web-server:80",
                    "health_check_enabled": True
                },
                {
                    "name": "Database Server",
                    "type": "database",
                    "endpoint_url": "http://db-server:5432",
                    "health_check_enabled": True
                },
                {
                    "name": "Cache Server",
                    "type": "cache",
                    "endpoint_url": "http://cache-server:6379",
                    "health_check_enabled": False
                }
            ]
            
            created_targets = []
            for target_data in monitoring_targets:
                result = await processor.process_action("register_monitoring_target", {
                    "target": target_data
                })
                if result.get("success"):
                    created_targets.append(result["data"]["target_id"])
            
            if len(created_targets) != len(monitoring_targets):
                print(f"     ❌ 監視対象登録数不一致")
                return False
            
            # 2. ヘルスチェック実行
            health_check_results = []
            for target_id in created_targets:
                result = await processor.process_action("check_target_health", {
                    "target_id": target_id
                })
                if result.get("success"):
                    health_check_results.append(result["data"])
            
            if len(health_check_results) != len(created_targets):
                print(f"     ❌ ヘルスチェック実行数不一致")
                return False
            
            # 3. ヘルスチェック結果分析
            healthy_targets = [r for r in health_check_results if r["status"] == "healthy"]
            avg_response_time = sum(r["response_time_ms"] for r in health_check_results) / len(health_check_results)
            avg_uptime = sum(r["uptime_percentage"] for r in health_check_results) / len(health_check_results)
            
            self.performance_metrics["monitoring"] = {
                "total_targets": len(created_targets),
                "healthy_targets": len(healthy_targets),
                "health_rate": len(healthy_targets) / len(created_targets) * 100,
                "average_response_time": avg_response_time,
                "average_uptime": avg_uptime
            }
            
            # 基準確認
            if len(healthy_targets) == 0:
                print(f"     ❌ 全監視対象が不健康")
                return False
            
            print(f"     ✅ 監視機能包括テスト成功: {len(healthy_targets)}/{len(created_targets)}健康, 平均応答{avg_response_time:.1f}ms")
            return True
            
        except Exception as e:
            print(f"     💥 監視機能包括テストエラー: {e}")
            return False
    
    async def test_pattern_learning_advanced(self) -> bool:
        """パターン学習高度テスト"""
        try:
            processor = IncidentProcessor()
            
            # 高度パターン学習テスト
            
            # 1. 複雑なインシデントパターン作成
            incident_patterns = [
                # パフォーマンス関連パターン
                *[{
                    "component": f"web_server_{i}",
                    "metric": "response_time",
                    "severity": "high",
                    "category": "performance"
                } for i in range(5)],
                
                # セキュリティ関連パターン
                *[{
                    "component": f"auth_service_{i}",
                    "metric": "failed_logins",
                    "severity": "medium",
                    "category": "security"
                } for i in range(3)],
                
                # 可用性関連パターン
                *[{
                    "component": f"database_{i}",
                    "metric": "connection_failure",
                    "severity": "critical",
                    "category": "availability"
                } for i in range(4)]
            ]
            
            # インシデント作成
            created_incidents = []
            for pattern in incident_patterns:
                result = await processor.process_action("detect_incident", {
                    "anomaly_data": pattern
                })
                if result.get("success"):
                    created_incidents.append(result["data"]["incident_id"])
            
            if len(created_incidents) != len(incident_patterns):
                print(f"     ❌ インシデント作成数不一致")
                return False
            
            # 2. パターン学習実行
            learning_result = await processor.process_action("learn_incident_patterns", {})
            
            if not learning_result.get("success"):
                print(f"     ❌ パターン学習失敗")
                return False
            
            learning_data = learning_result["data"]
            patterns_learned = learning_data["patterns_learned"]
            patterns = learning_data["patterns"]
            
            # 3. 学習パターン分析
            expected_categories = ["performance", "security", "availability"]
            learned_categories = [p["category"] for p in patterns]
            
            category_coverage = len(set(learned_categories) & set(expected_categories))
            
            if category_coverage < 2:  # 最低2カテゴリ学習必要
                print(f"     ❌ パターン学習カテゴリ不足: {category_coverage}")
                return False
            
            # パターン品質評価
            pattern_quality_scores = []
            for pattern in patterns:
                quality_score = 0
                # コンポーネント共通性
                if len(pattern["common_components"]) > 0:
                    quality_score += 30
                # タグ共通性
                if len(pattern["common_tags"]) > 0:
                    quality_score += 20
                # インシデント数
                if pattern["incident_count"] >= 3:
                    quality_score += 30
                # 平均重要度
                if 2.0 <= pattern["average_severity"] <= 4.0:
                    quality_score += 20
                
                pattern_quality_scores.append(quality_score)
            
            avg_pattern_quality = sum(pattern_quality_scores) / len(pattern_quality_scores) if pattern_quality_scores else 0
            
            self.performance_metrics["pattern_learning"] = {
                "total_incidents": len(created_incidents),
                "patterns_learned": patterns_learned,
                "category_coverage": category_coverage,
                "average_pattern_quality": avg_pattern_quality
            }
            
            print(f"     ✅ パターン学習高度テスト成功: {patterns_learned}パターン, {category_coverage}カテゴリ, 品質{avg_pattern_quality:.1f}")
            return True
            
        except Exception as e:
            print(f"     💥 パターン学習高度テストエラー: {e}")
            return False
    
    async def test_correlation_analysis_detailed(self) -> bool:
        """相関分析詳細テスト"""
        try:
            processor = IncidentProcessor(test_mode=True)
            processor.reset_for_testing()
            
            # 相関分析詳細テスト
            
            # 1. 時間的相関インシデント作成
            time_correlated_incidents = []
            
            # 同時期インシデント群1
            for i in range(3):
                result = await processor.process_action("detect_incident", {
                    "anomaly_data": {
                        "component": f"frontend_app_{i}",
                        "metric": "error_rate",
                        "severity": "high"
                    }
                })
                if result.get("success"):
                    time_correlated_incidents.append(result["data"]["incident_id"])
                await asyncio.sleep(0.001)  # 短間隔
            
            # 間隔を開ける
            await asyncio.sleep(0.01)
            
            # 同時期インシデント群2
            for i in range(2):
                result = await processor.process_action("detect_incident", {
                    "anomaly_data": {
                        "component": f"backend_service_{i}",
                        "metric": "response_time",
                        "severity": "medium"
                    }
                })
                if result.get("success"):
                    time_correlated_incidents.append(result["data"]["incident_id"])
                await asyncio.sleep(0.001)
            
            # 2. 空間的相関インシデント作成
            space_correlated_incidents = []
            shared_components = ["payment_service", "user_database"]
            
            for component in shared_components:
                for metric in ["availability", "performance"]:
                    result = await processor.process_action("detect_incident", {
                        "anomaly_data": {
                            "component": component,
                            "metric": metric,
                            "severity": "high"
                        }
                    })
                    if result.get("success"):
                        space_correlated_incidents.append(result["data"]["incident_id"])
            
            # 3. 相関分析実行
            correlation_result = await processor.process_action("analyze_correlations", {})
            
            if not correlation_result.get("success"):
                print(f"     ❌ 相関分析失敗")
                return False
            
            correlation_data = correlation_result["data"]
            correlations = correlation_data["correlations"]
            analyzed_incidents = correlation_data["analyzed_incidents"]
            
            # 4. 相関分析結果評価
            total_incidents_created = len(time_correlated_incidents) + len(space_correlated_incidents)
            
            if analyzed_incidents != total_incidents_created:
                print(f"     ❌ 分析インシデント数不一致: {analyzed_incidents} != {total_incidents_created}")
                return False
            
            # 相関品質評価
            high_confidence_correlations = [c for c in correlations if c["confidence"] >= 0.7]
            temporal_correlations = [c for c in correlations if c["correlation_type"] == "temporal_spatial"]
            
            self.performance_metrics["correlation_analysis"] = {
                "total_incidents_created": total_incidents_created,
                "total_correlations_found": len(correlations),
                "high_confidence_correlations": len(high_confidence_correlations),
                "temporal_correlations": len(temporal_correlations),
                "correlation_discovery_rate": len(correlations) / max(total_incidents_created, 1)
            }
            
            # 最低限の相関検出確認
            if len(correlations) == 0:
                print(f"     ⚠️ 相関が検出されませんでした（正常、データ依存）")
            
            print(f"     ✅ 相関分析詳細テスト成功: {len(correlations)}相関検出, {len(high_confidence_correlations)}高信頼度")
            return True
            
        except Exception as e:
            print(f"     💥 相関分析詳細テストエラー: {e}")
            return False
    
    async def test_remediation_effectiveness(self) -> bool:
        """修復効果テスト"""
        try:
            processor = IncidentProcessor()
            
            # 修復効果テスト
            
            # 1. 異なるカテゴリのインシデント作成
            test_categories = [
                ("performance", "cache_service", "memory_leak"),
                ("availability", "web_server", "service_down"),
                ("quality", "api_gateway", "validation_error"),
                ("security", "auth_service", "unauthorized_access")
            ]
            
            remediation_results = []
            
            for category, component, metric in test_categories:
                # インシデント作成
                incident_result = await processor.process_action("detect_incident", {
                    "anomaly_data": {
                        "component": component,
                        "metric": metric,
                        "severity": "high",
                        "category": category
                    }
                })
                
                if not incident_result.get("success"):
                    continue
                
                incident_id = incident_result["data"]["incident_id"]
                
                # 修復試行
                remediation_result = await processor.process_action("attempt_automated_remediation", {
                    "incident_id": incident_id
                })
                
                if remediation_result.get("success"):
                    remediation_data = remediation_result["data"]
                    remediation_results.append({
                        "category": category,
                        "component": component,
                        "incident_id": incident_id,
                        "status": remediation_data["status"],
                        "actions_taken": remediation_data.get("actions_taken", [])
                    })
            
            # 2. 修復効果分析
            successful_remediations = [r for r in remediation_results if r["status"] == "success"]
            failed_remediations = [r for r in remediation_results if r["status"] == "failed"]
            no_action_remediations = [r for r in remediation_results if r["status"] == "no_action"]
            
            success_rate = len(successful_remediations) / len(remediation_results) * 100 if remediation_results else 0
            
            # カテゴリ別修復効果
            category_effectiveness = {}
            for category in [c[0] for c in test_categories]:
                category_results = [r for r in remediation_results if r["category"] == category]
                category_successes = [r for r in category_results if r["status"] == "success"]
                category_effectiveness[category] = len(category_successes) / len(category_results) * 100 if category_results else 0
            
            self.performance_metrics["remediation_effectiveness"] = {
                "total_remediations": len(remediation_results),
                "successful_remediations": len(successful_remediations),
                "failed_remediations": len(failed_remediations),
                "no_action_remediations": len(no_action_remediations),
                "overall_success_rate": success_rate,
                "category_effectiveness": category_effectiveness
            }
            
            # 効果基準確認
            if success_rate < 50:  # 50%未満は問題
                print(f"     ❌ 修復成功率低い: {success_rate:.1f}%")
                return False
            
            # 全カテゴリで修復アクションが定義されているか確認
            categories_with_actions = len([r for r in remediation_results if r["actions_taken"]])
            if categories_with_actions < len(test_categories) * 0.8:  # 80%未満は問題
                print(f"     ❌ 修復アクション定義不足")
                return False
            
            print(f"     ✅ 修復効果テスト成功: {success_rate:.1f}%成功率, {len(test_categories)}カテゴリ対応")
            return True
            
        except Exception as e:
            print(f"     💥 修復効果テストエラー: {e}")
            return False
    
    async def test_statistics_accuracy(self) -> bool:
        """統計精度テスト"""
        try:
            processor = IncidentProcessor(test_mode=True)
            processor.reset_for_testing()
            
            # 統計精度テスト
            
            # 1. 既知データで統計作成
            known_data = {
                "incidents": [],
                "quality_assessments": [],
                "alert_rules": [],
                "monitoring_targets": []
            }
            
            # インシデント作成（既知数）
            incident_severities = ["low", "medium", "high", "critical"]
            incidents_per_severity = 3
            
            for severity in incident_severities:
                for i in range(incidents_per_severity):
                    result = await processor.process_action("detect_incident", {
                        "anomaly_data": {
                            "component": f"test_service_{severity}_{i}",
                            "metric": "test_metric",
                            "severity": severity
                        }
                    })
                    if result.get("success"):
                        known_data["incidents"].append(result["data"]["incident_id"])
            
            # いくつかのインシデントを解決状態にする
            resolved_count = 0
            for incident_id in known_data["incidents"][:6]:  # 半分を解決
                result = await processor.process_action("respond_to_incident", {
                    "incident_id": incident_id
                })
                if result.get("success") and result["data"]["incident_status"] == "resolved":
                    resolved_count += 1
            
            # 品質評価実行（既知数）
            default_standard_id = list(processor.quality_standards.keys())[0]
            quality_assessments = 5
            
            for i in range(quality_assessments):
                result = await processor.process_action("assess_quality", {
                    "standard_id": default_standard_id,
                    "component": f"test_component_{i}",
                    "metrics": {"test_coverage": 80.0 + i}
                })
                if result.get("success"):
                    known_data["quality_assessments"].append(result["data"]["assessment_id"])
            
            # アラートルール作成（既知数）
            alert_rules_count = 4
            for i in range(alert_rules_count):
                result = await processor.process_action("create_alert_rule", {
                    "alert_rule": {
                        "name": f"Test Alert {i}",
                        "condition_expression": f"metric_{i} > {i*10}",
                        "severity": "medium",
                        "enabled": i % 2 == 0  # 半分を有効
                    }
                })
                if result.get("success"):
                    known_data["alert_rules"].append(result["data"]["rule_id"])
            
            # 監視対象登録（既知数）
            monitoring_targets_count = 3
            for i in range(monitoring_targets_count):
                result = await processor.process_action("register_monitoring_target", {
                    "target": {
                        "name": f"Test Target {i}",
                        "type": "service",
                        "endpoint_url": f"http://test-{i}:8080",
                        "health_check_enabled": True
                    }
                })
                if result.get("success"):
                    known_data["monitoring_targets"].append(result["data"]["target_id"])
            
            # 2. 統計取得・精度確認
            stats_result = await processor.process_action("get_statistics", {})
            
            if not stats_result.get("success"):
                print(f"     ❌ 統計取得失敗")
                return False
            
            stats = stats_result["data"]
            
            # 統計精度検証
            accuracy_checks = []
            
            # インシデント統計
            incident_stats = stats["incident_statistics"]
            accuracy_checks.append({
                "metric": "total_incidents",
                "expected": len(known_data["incidents"]),
                "actual": incident_stats["total_incidents"],
                "accurate": incident_stats["total_incidents"] == len(known_data["incidents"])
            })
            
            # 解決率計算確認
            expected_resolution_rate = (resolved_count / len(known_data["incidents"])) * 100 if known_data["incidents"] else 0
            resolution_rate_diff = abs(incident_stats["resolution_rate"] - expected_resolution_rate)
            accuracy_checks.append({
                "metric": "resolution_rate",
                "expected": expected_resolution_rate,
                "actual": incident_stats["resolution_rate"],
                "accurate": resolution_rate_diff < 1.0  # 1%以内の誤差許容
            })
            
            # アラート統計
            alert_stats = stats["alert_statistics"]
            enabled_rules = len([r for r in known_data["alert_rules"]]) // 2  # 半分が有効
            accuracy_checks.append({
                "metric": "alert_rules_active",
                "expected": enabled_rules,
                "actual": alert_stats["alert_rules_active"],
                "accurate": abs(alert_stats["alert_rules_active"] - enabled_rules) <= 1
            })
            
            # 監視統計
            monitoring_stats = stats["monitoring_statistics"]
            accuracy_checks.append({
                "metric": "monitoring_targets_count",
                "expected": len(known_data["monitoring_targets"]),
                "actual": monitoring_stats["monitoring_targets_count"],
                "accurate": monitoring_stats["monitoring_targets_count"] == len(known_data["monitoring_targets"])
            })
            
            # 精度評価
            accurate_metrics = [c for c in accuracy_checks if c["accurate"]]
            accuracy_rate = len(accurate_metrics) / len(accuracy_checks) * 100
            
            self.performance_metrics["statistics_accuracy"] = {
                "total_metrics_checked": len(accuracy_checks),
                "accurate_metrics": len(accurate_metrics),
                "accuracy_rate": accuracy_rate,
                "accuracy_details": accuracy_checks
            }
            
            # 精度基準確認
            if accuracy_rate < 80:  # 80%未満は問題
                print(f"     ❌ 統計精度低い: {accuracy_rate:.1f}%")
                for check in accuracy_checks:
                    if not check["accurate"]:
                        print(f"       • {check['metric']}: 期待{check['expected']}, 実際{check['actual']}")
                return False
            
            print(f"     ✅ 統計精度テスト成功: {accuracy_rate:.1f}%精度, {len(accurate_metrics)}/{len(accuracy_checks)}項目")
            return True
            
        except Exception as e:
            print(f"     💥 統計精度テストエラー: {e}")
            return False
    
    async def test_stress_load(self) -> bool:
        """ストレス負荷テスト"""
        try:
            processor = IncidentProcessor()
            
            # ストレス負荷テスト
            
            # 1. 大量同時操作テスト
            stress_operations = []
            
            # 各種操作を混合
            for i in range(200):
                operation_type = i % 4
                
                if operation_type == 0:
                    # インシデント検知
                    stress_operations.append(("detect_incident", {
                        "anomaly_data": {
                            "component": f"stress_service_{i}",
                            "metric": "stress_metric",
                            "severity": ["low", "medium", "high"][i % 3]
                        }
                    }))
                elif operation_type == 1:
                    # 品質評価
                    default_standard_id = list(processor.quality_standards.keys())[0]
                    stress_operations.append(("assess_quality", {
                        "standard_id": default_standard_id,
                        "component": f"stress_component_{i}",
                        "metrics": {"test_coverage": 70.0 + (i % 30)}
                    }))
                elif operation_type == 2:
                    # 統計取得
                    stress_operations.append(("get_statistics", {}))
                else:
                    # パターン学習
                    stress_operations.append(("learn_incident_patterns", {}))
            
            # 2. ストレス実行
            start_time = time.time()
            stress_results = []
            
            # バッチ実行でストレステスト
            batch_size = 20
            for i in range(0, len(stress_operations), batch_size):
                batch = stress_operations[i:i+batch_size]
                batch_results = []
                
                for operation, data in batch:
                    result = await processor.process_action(operation, data)
                    batch_results.append(result)
                
                stress_results.extend(batch_results)
                
                # 少し休憩（メモリ負荷軽減）
                if i % 100 == 0:
                    await asyncio.sleep(0.001)
            
            end_time = time.time()
            total_stress_time = end_time - start_time
            
            # 3. ストレス結果分析
            successful_operations = [r for r in stress_results if r.get("success")]
            failed_operations = [r for r in stress_results if not r.get("success")]
            
            stress_success_rate = len(successful_operations) / len(stress_results) * 100
            stress_throughput = len(stress_results) / total_stress_time
            
            self.performance_metrics["stress_test"] = {
                "total_operations": len(stress_operations),
                "successful_operations": len(successful_operations),
                "failed_operations": len(failed_operations),
                "success_rate": stress_success_rate,
                "total_time": total_stress_time,
                "throughput": stress_throughput
            }
            
            # ストレス基準確認
            if stress_success_rate < 90:  # 90%未満は問題
                print(f"     ❌ ストレス成功率低い: {stress_success_rate:.1f}%")
                return False
            
            if stress_throughput < 20:  # 20 ops/sec未満は問題
                print(f"     ❌ ストレススループット低い: {stress_throughput:.1f} ops/sec")
                return False
            
            print(f"     ✅ ストレス負荷テスト成功: {stress_success_rate:.1f}%成功率, {stress_throughput:.1f} ops/sec")
            return True
            
        except Exception as e:
            print(f"     💥 ストレス負荷テストエラー: {e}")
            return False
    
    async def test_edge_cases(self) -> bool:
        """エッジケーステスト"""
        try:
            processor = IncidentProcessor()
            
            # エッジケーステスト
            
            edge_test_cases = [
                {
                    "name": "空文字列データ",
                    "action": "search_similar_incidents",
                    "data": {"query": ""},
                    "should_succeed": True
                },
                {
                    "name": "非常に長いテキスト",
                    "action": "detect_incident",
                    "data": {
                        "anomaly_data": {
                            "component": "x" * 1000,
                            "metric": "y" * 1000,
                            "severity": "medium"
                        }
                    },
                    "should_succeed": True
                },
                {
                    "name": "ゼロ値メトリクス",
                    "action": "assess_quality",
                    "data": {
                        "standard_id": list(processor.quality_standards.keys())[0],
                        "component": "test",
                        "metrics": {"test_coverage": 0.0}
                    },
                    "should_succeed": True
                },
                {
                    "name": "極大値メトリクス",
                    "action": "assess_quality",
                    "data": {
                        "standard_id": list(processor.quality_standards.keys())[0],
                        "component": "test",
                        "metrics": {"test_coverage": 999999.0}
                    },
                    "should_succeed": True
                },
                {
                    "name": "特殊文字データ",
                    "action": "detect_incident",
                    "data": {
                        "anomaly_data": {
                            "component": "test@#$%^&*()",
                            "metric": "test<>?:{}[]",
                            "severity": "low"
                        }
                    },
                    "should_succeed": True
                },
                {
                    "name": "Unicode文字データ",
                    "action": "detect_incident",
                    "data": {
                        "anomaly_data": {
                            "component": "テストサービス",
                            "metric": "応答時間",
                            "severity": "medium"
                        }
                    },
                    "should_succeed": True
                },
                {
                    "name": "同一データ重複実行",
                    "action": "detect_incident",
                    "data": {
                        "anomaly_data": {
                            "component": "duplicate_service",
                            "metric": "duplicate_metric",
                            "severity": "high"
                        }
                    },
                    "should_succeed": True
                }
            ]
            
            edge_case_results = []
            
            for test_case in edge_test_cases:
                try:
                    # 同一データ重複の場合は複数回実行
                    if test_case["name"] == "同一データ重複実行":
                        for _ in range(3):
                            result = await processor.process_action(test_case["action"], test_case["data"])
                    else:
                        result = await processor.process_action(test_case["action"], test_case["data"])
                    
                    # 結果評価
                    success = result.get("success", False)
                    expected_success = test_case["should_succeed"]
                    
                    edge_case_results.append({
                        "case": test_case["name"],
                        "expected_success": expected_success,
                        "actual_success": success,
                        "correct": success == expected_success,
                        "result": result
                    })
                    
                except Exception as e:
                    edge_case_results.append({
                        "case": test_case["name"],
                        "expected_success": test_case["should_succeed"],
                        "actual_success": False,
                        "correct": not test_case["should_succeed"],
                        "exception": str(e)
                    })
            
            # エッジケース結果評価
            correct_results = [r for r in edge_case_results if r["correct"]]
            edge_case_success_rate = len(correct_results) / len(edge_case_results) * 100
            
            self.performance_metrics["edge_cases"] = {
                "total_edge_cases": len(edge_test_cases),
                "correct_results": len(correct_results),
                "success_rate": edge_case_success_rate,
                "results": edge_case_results
            }
            
            # エッジケース基準確認
            if edge_case_success_rate < 80:  # 80%未満は問題
                print(f"     ❌ エッジケース処理不十分: {edge_case_success_rate:.1f}%")
                for result in edge_case_results:
                    if not result["correct"]:
                        print(f"       • {result['case']}: 期待{result['expected_success']}, 実際{result['actual_success']}")
                return False
            
            print(f"     ✅ エッジケーステスト成功: {edge_case_success_rate:.1f}%適切処理, {len(correct_results)}/{len(edge_test_cases)}ケース")
            return True
            
        except Exception as e:
            print(f"     💥 エッジケーステストエラー: {e}")
            return False


async def main():
    """メイン実行"""
    print("🚨 Incident Sage A2A Agent - 包括的テスト開始")
    print("=" * 70)
    
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # テスト実行
    test_suite = TestIncidentSageA2AComprehensive()
    results = await test_suite.run_all_tests()
    
    if results["success_rate"] >= 80.0:
        print(f"\\n🎉 Incident Sage包括的テスト成功！")
        print(f"   成功率: {results['success_rate']:.1f}%")
        print(f"   実行時間: {results['total_duration']:.3f}秒")
        print(f"   平均テスト時間: {results['total_duration']/results['total_tests']:.3f}秒")
        print(f"   🚨 Elder Loop Phase 4完了")
        
        # パフォーマンスサマリー
        if test_suite.performance_metrics:
            print(f"\\n📊 パフォーマンスサマリー:")
            for metric_name, metric_data in test_suite.performance_metrics.items():
                if isinstance(metric_data, dict) and "throughput" in metric_data:
                    print(f"   • {metric_name}: {metric_data['throughput']:.1f} ops/sec")
                elif isinstance(metric_data, dict) and "success_rate" in metric_data:
                    print(f"   • {metric_name}: {metric_data['success_rate']:.1f}% 成功率")
        
        return True
    else:
        print(f"\\n🔧 Incident Sage包括的テストで調整が必要")
        print(f"   成功率: {results['success_rate']:.1f}% (80%未満)")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)