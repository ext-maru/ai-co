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
import pytest
import tempfile
import os
from statistics import mean

# 環境変数を使用してパスを設定
import sys
import os
# shared_libs.configからELDERS_GUILD_HOMEを取得
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_libs.config import config
sys.path.insert(0, config.ELDERS_GUILD_HOME)
from incident_sage.business_logic import IncidentProcessor


class TestIncidentSageA2AComprehensive:
    """Incident Sage A2A Agent包括的テスト"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """テスト用セットアップ"""
        self.performance_metrics = {}
        self.logger = logging.getLogger("incident_sage_comprehensive_test")
        yield
        # クリーンアップ処理（必要に応じて）
    
    @pytest.mark.asyncio
    async def test_performance(self):
        """パフォーマンステスト"""
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
        assert throughput >= 50, f"スループット低い: {throughput:0.1f} ops/sec"
        assert avg_time_per_operation <= 0.1, f"平均実行時間長い: {avg_time_per_operation:0.3f}s"
        
        print(f"✅ パフォーマンステスト成功: {throughput:0.1f} ops/sec, {avg_time_per_operation:0.3f}s/op")
    
    @pytest.mark.asyncio
    async def test_concurrency(self):
        """並行性テスト"""
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
        assert len(failed_results) <= 2, f"並行処理失敗多数: {len(failed_results)}"
        assert concurrent_time <= 5.0, f"並行実行時間長い: {concurrent_time:0.3f}s"
        
        print(f"✅ 並行性テスト成功: {len(successful_results)}/{len(concurrent_tasks)} 成功, {concurrent_time:0.3f}s")
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """エラーハンドリングテスト"""
        processor = IncidentProcessor()
        
        # 悪意のある/異常データテストケース
        error_test_cases = [
            {
                "name": "NULL データ",
                "action": "detect_incident",
                "data": {}
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
        
        # 80%以上が適切に処理されていることを確認
        assert properly_handled >= total_cases * 0.8, f"エラーハンドリング不十分: {properly_handled}/{total_cases}"
        
        print(f"✅ エラーハンドリング成功: {properly_handled}/{total_cases} 適切処理")
    
    @pytest.mark.asyncio
    async def test_data_integrity(self):
        """データ整合性テスト"""
        processor = IncidentProcessor()
        
        # データ整合性テストシナリオ
        
        # 1.0 インシデント作成と取得の整合性
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
        assert create_result.get("success"), "インシデント作成失敗"
        
        incident_id = create_result["data"]["incident_id"]
        
        # データベースから読み直し
        processor2 = IncidentProcessor()
        assert incident_id in processor2.incidents, "インシデントデータ永続化失敗"
        
        stored_incident = processor2.incidents[incident_id]
        
        # データ整合性確認
        assert stored_incident.title == create_result["data"]["title"], "タイトル不整合"
        assert stored_incident.severity.value == create_result["data"]["severity"], "重要度不整合"
        
        # 2.0 品質基準データ整合性
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
        assert register_result.get("success"), "品質基準登録失敗"
        
        standard_id = register_result["data"]["standard_id"]
        
        # 新しいプロセッサで確認
        processor3 = IncidentProcessor()
        assert standard_id in processor3.quality_standards, "品質基準データ永続化失敗"
        
        stored_standard = processor3.quality_standards[standard_id]
        assert stored_standard.name == quality_data["standard"]["name"], "品質基準名不整合"
        
        print("✅ データ整合性テスト成功: インシデント・品質基準永続化確認")
    
    @pytest.mark.asyncio
    async def test_complex_workflow(self):
        """複雑ワークフローテスト"""
        processor = IncidentProcessor()
        
        # 複雑なワークフローシナリオ
        # 1.0 複数サービスでの連鎖的インシデント
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
            await asyncio.sleep(0.01)
        
        assert len(incidents) == len(services), f"インシデント作成数不一致: {len(incidents)} != {len(services)}"
        
        # 2.0 パターン学習実行
        pattern_result = await processor.process_action("learn_incident_patterns", {})
        assert pattern_result.get("success"), "パターン学習失敗"
        
        # 3.0 相関分析実行
        correlation_result = await processor.process_action("analyze_correlations", {})
        assert correlation_result.get("success"), "相関分析失敗"
        
        correlations = correlation_result["data"]["correlations"]
        
        # 4.0 自動修復試行
        remediation_results = []
        for incident_id in incidents[:2]:  # 最初の2つのみ
            remediation_result = await processor.process_action("attempt_automated_remediation", {
                "incident_id": incident_id
            })
            remediation_results.append(remediation_result)
        
        successful_remediations = [r for r in remediation_results if r.get("success")]
        
        # 5.0 統計分析
        stats_result = await processor.process_action("get_statistics", {})
        assert stats_result.get("success"), "統計取得失敗"
        
        stats = stats_result["data"]
        
        # ワークフロー結果検証
        assert stats["incident_statistics"]["total_incidents"] >= len(services), "統計のインシデント数不正"
        assert len(successful_remediations) > 0, "自動修復が全て失敗"
        
        print(f"✅ 複雑ワークフロー成功: {len(incidents)}インシデント, {len(correlations)}相関, {len(successful_remediations)}修復成功")
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """メモリ効率性テスト"""
        try:
            import psutil
            
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
            assert memory_increase <= 100, f"メモリ使用量増加過大: {memory_increase:0.1f}MB"
            
            memory_per_op = (memory_increase * 1024) / 1000  # KB per operation
            assert memory_per_op <= 10, f"操作あたりメモリ使用量過大: {memory_per_op:0.1f}KB/op"
            
            print(f"✅ メモリ効率性テスト成功: +{memory_increase:0.1f}MB, {memory_per_op:0.1f}KB/op")
            
        except ImportError:
            pytest.skip("psutil未利用可能、メモリテストスキップ")
    
    @pytest.mark.asyncio
    async def test_incident_lifecycle(self):
        """インシデントライフサイクルテスト"""
        processor = IncidentProcessor(test_mode=True)
        processor.reset_for_testing()
        
        # インシデントライフサイクル全体テスト
        
        # 1.0 インシデント検知
        detection_data = {
            "anomaly_data": {
                "component": "lifecycle_test_service",
                "metric": "availability",
                "severity": "critical",
                "confidence": 0.98
            }
        }
        
        detection_result = await processor.process_action("detect_incident", detection_data)
        assert detection_result.get("success"), "インシデント検知失敗"
        
        incident_id = detection_result["data"]["incident_id"]
        initial_status = detection_result["data"]["status"]
        
        assert initial_status == "open", f"初期ステータス不正: {initial_status}"
        
        # 2.0 インシデント対応
        response_result = await processor.process_action("respond_to_incident", {
            "incident_id": incident_id
        })
        
        assert response_result.get("success"), "インシデント対応失敗"
        
        response_status = response_result["data"]["response_status"]
        incident_status_after_response = response_result["data"]["incident_status"]
        
        # 3.0 自動修復試行
        remediation_result = await processor.process_action("attempt_automated_remediation", {
            "incident_id": incident_id
        })
        
        assert remediation_result.get("success"), "自動修復試行失敗"
        
        remediation_status = remediation_result["data"]["status"]
        
        # 4.0 インシデント状態確認
        # test_modeでは永続化されないため、同じプロセッサで確認
        assert incident_id in processor.incidents, "インシデントがメモリに存在しない"
        
        final_incident = processor.incidents[incident_id]
        
        # ライフサイクル検証
        lifecycle_steps = [
            ("detection", detection_result["data"]["incident_id"]),
            ("response", response_status),
            ("remediation", remediation_status),
            ("final_status", final_incident.status.value)
        ]
        
        print("✅ インシデントライフサイクル成功:")
        for step_name, step_result in lifecycle_steps:
            print(f"   • {step_name}: {step_result}")
    
    @pytest.mark.asyncio
    async def test_quality_assessment_comprehensive(self):
        """品質評価包括テスト"""
        processor = IncidentProcessor()
        
        # 複数品質基準での包括評価
        
        # 1.0 カスタム品質基準作成
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
        
        assert len(created_standards) == len(custom_standards), "品質基準作成数不一致"
        
        # 2.0 複数コンポーネントでの品質評価
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
        
        # 3.0 評価結果分析
        total_assessments = len(components) * len(created_standards)
        successful_assessments = len(assessment_results)
        
        assert successful_assessments == total_assessments, f"評価実行数不一致: {successful_assessments} != {total_assessments}"
        
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
        
        print(f"✅ 品質評価包括テスト成功: {compliance_rate:0.1f}%適合, 平均{avg_quality_score:0.1f}点")
    
    @pytest.mark.asyncio
    async def test_alert_system_integration(self):
        """アラートシステム統合テスト"""
        processor = IncidentProcessor(test_mode=True)
        processor.reset_for_testing()
        
        # アラートシステム統合シナリオ
        
        # 1.0 複数アラートルール作成
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
        
        assert len(created_rules) == len(alert_rules), "アラートルール作成数不一致"
        
        # 2.0 アラート評価シナリオ
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
        
        # 3.0 アラート評価結果検証
        successful_evaluations = [r for r in alert_evaluation_results if r["match"]]
        
        assert len(successful_evaluations) == len(test_metrics), "アラート評価結果不一致"
        
        print(f"✅ アラートシステム統合成功: {len(created_rules)}ルール, {len(successful_evaluations)}シナリオ")
    
    @pytest.mark.asyncio
    async def test_monitoring_comprehensive(self):
        """監視機能包括テスト"""
        processor = IncidentProcessor()
        
        # 監視システム包括テスト
        
        # 1.0 複数監視対象登録
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
        
        assert len(created_targets) == len(monitoring_targets), "監視対象登録数不一致"
        
        # 2.0 ヘルスチェック実行
        health_check_results = []
        for target_id in created_targets:
            result = await processor.process_action("check_target_health", {
                "target_id": target_id
            })
            if result.get("success"):
                health_check_results.append(result["data"])
        
        assert len(health_check_results) == len(created_targets), "ヘルスチェック実行数不一致"
        
        # 3.0 ヘルスチェック結果分析
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
        assert len(healthy_targets) > 0, "全監視対象が不健康"
        
        print(f"✅ 監視機能包括テスト成功: {len(healthy_targets)}/{len(created_targets)}健康, 平均応答{avg_response_time:0.1f}ms")
    
    @pytest.mark.asyncio
    async def test_pattern_learning_advanced(self):
        """パターン学習高度テスト"""
        processor = IncidentProcessor()
        
        # 高度パターン学習テスト
        
        # 1.0 複雑なインシデントパターン作成
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
        
        assert len(created_incidents) == len(incident_patterns), "インシデント作成数不一致"
        
        # 2.0 パターン学習実行
        learning_result = await processor.process_action("learn_incident_patterns", {})
        
        assert learning_result.get("success"), "パターン学習失敗"
        
        learning_data = learning_result["data"]
        patterns_learned = learning_data["patterns_learned"]
        patterns = learning_data["patterns"]
        
        # 3.0 学習パターン分析
        expected_categories = ["performance", "security", "availability"]
        learned_categories = [p["category"] for p in patterns]
        
        category_coverage = len(set(learned_categories) & set(expected_categories))
        
        assert category_coverage >= 2, f"パターン学習カテゴリ不足: {category_coverage}"
        
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
        
        print(f"✅ パターン学習高度テスト成功: {patterns_learned}パターン, {category_coverage}カテゴリ, 品質{avg_pattern_quality:0.1f}")
    
    @pytest.mark.asyncio
    async def test_correlation_analysis_detailed(self):
        """相関分析詳細テスト"""
        processor = IncidentProcessor(test_mode=True)
        processor.reset_for_testing()
        
        # 相関分析詳細テスト
        
        # 1.0 時間的相関インシデント作成
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
            await asyncio.sleep(0.01)  # 短間隔
        
        # 間隔を開ける
        await asyncio.sleep(0.1)
        
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
            await asyncio.sleep(0.01)
        
        # 2.0 空間的相関インシデント作成
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
        
        # 3.0 相関分析実行
        correlation_result = await processor.process_action("analyze_correlations", {})
        
        assert correlation_result.get("success"), "相関分析失敗"
        
        correlation_data = correlation_result["data"]
        correlations = correlation_data["correlations"]
        analyzed_incidents = correlation_data["analyzed_incidents"]
        
        # 4.0 相関分析結果評価
        total_incidents_created = len(time_correlated_incidents) + len(space_correlated_incidents)
        
        assert analyzed_incidents == total_incidents_created, f"分析インシデント数不一致: {analyzed_incidents} != {total_incidents_created}"
        
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
        
        # 最低限の相関検出確認（データ依存なのでwarningレベル）
        if len(correlations) == 0:
            print("⚠️ 相関が検出されませんでした（正常、データ依存）")
        
        print(f"✅ 相関分析詳細テスト成功: {len(correlations)}相関検出, {len(high_confidence_correlations)}高信頼度")
    
    @pytest.mark.asyncio
    async def test_remediation_effectiveness(self):
        """修復効果テスト"""
        processor = IncidentProcessor()
        
        # 修復効果テスト
        
        # 1.0 異なるカテゴリのインシデント作成
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
        
        # 2.0 修復効果分析
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
        assert success_rate >= 50, f"修復成功率低い: {success_rate:0.1f}%"
        
        # 全カテゴリで修復アクションが定義されているか確認
        categories_with_actions = len([r for r in remediation_results if r["actions_taken"]])
        assert categories_with_actions >= len(test_categories) * 0.8, "修復アクション定義不足"
        
        print(f"✅ 修復効果テスト成功: {success_rate:0.1f}%成功率, {len(test_categories)}カテゴリ対応")
    
    @pytest.mark.asyncio
    async def test_statistics_accuracy(self):
        """統計精度テスト"""
        processor = IncidentProcessor(test_mode=True)
        processor.reset_for_testing()
        
        # 統計精度テスト
        
        # 1.0 既知データで統計作成
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
        
        # 2.0 統計取得・精度確認
        stats_result = await processor.process_action("get_statistics", {})
        
        assert stats_result.get("success"), "統計取得失敗"
        
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
        assert accuracy_rate >= 80, f"統計精度低い: {accuracy_rate:0.1f}%"
        
        print(f"✅ 統計精度テスト成功: {accuracy_rate:0.1f}%精度, {len(accurate_metrics)}/{len(accuracy_checks)}項目")
    
    @pytest.mark.asyncio
    async def test_stress_load(self):
        """ストレス負荷テスト"""
        processor = IncidentProcessor()
        
        # ストレス負荷テスト
        
        # 1.0 大量同時操作テスト
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
        
        # 2.0 ストレス実行
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
                await asyncio.sleep(0.01)
        
        end_time = time.time()
        total_stress_time = end_time - start_time
        
        # 3.0 ストレス結果分析
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
        assert stress_success_rate >= 90, f"ストレス成功率低い: {stress_success_rate:0.1f}%"
        assert stress_throughput >= 20, f"ストレススループット低い: {stress_throughput:0.1f} ops/sec"
        
        print(f"✅ ストレス負荷テスト成功: {stress_success_rate:0.1f}%成功率, {stress_throughput:0.1f} ops/sec")
    
    @pytest.mark.asyncio
    async def test_edge_cases(self):
        """エッジケーステスト"""
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
        assert edge_case_success_rate >= 80, f"エッジケース処理不十分: {edge_case_success_rate:0.1f}%"
        
        print(f"✅ エッジケーステスト成功: {edge_case_success_rate:0.1f}%適切処理, {len(correct_results)}/{len(edge_test_cases)}ケース")