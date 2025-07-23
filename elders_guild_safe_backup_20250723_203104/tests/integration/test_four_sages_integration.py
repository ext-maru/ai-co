#!/usr/bin/env python3
"""
🧪 4賢者統合テストスイート
=========================

Elder Loop開発手法に基づく4賢者システムの統合テスト。
賢者間の連携、データフロー、エンドツーエンドシナリオを検証。

Author: Claude Elder
Created: 2025-07-23
"""

import asyncio
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import sys

# プロジェクトパス設定
import os
current_file = os.path.abspath(__file__)
tests_dir = os.path.dirname(current_file)
integration_dir = os.path.dirname(tests_dir)
elders_guild_path = os.path.dirname(integration_dir)

# ビジネスロジックの直接インポート
import importlib.util

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# 各ビジネスロジックモジュールをロード
knowledge_module = load_module("knowledge_bl", os.path.join(elders_guild_path, "knowledge_sage", "business_logic.py"))
task_module = load_module("task_bl", os.path.join(elders_guild_path, "task_sage", "business_logic.py"))
incident_module = load_module("incident_bl", os.path.join(elders_guild_path, "incident_sage", "business_logic.py"))
rag_module = load_module("rag_bl", os.path.join(elders_guild_path, "rag_sage", "business_logic.py"))

KnowledgeProcessor = knowledge_module.KnowledgeProcessor
TaskProcessor = task_module.TaskProcessor
IncidentProcessor = incident_module.IncidentProcessor
RAGProcessor = rag_module.RAGProcessor


class TestFourSagesIntegration:

    """4賢者統合テストクラス"""
        self.test_results = {}
        self.temp_dir = None
        
    async def setup(self):

        """テスト環境セットアップ""" {self.temp_dir}")
        
        # 各賢者を初期化（テストモード）
        self.knowledge_sage = KnowledgeProcessor(test_mode=True)
        self.task_sage = TaskProcessor(test_mode=True) 
        self.incident_sage = IncidentProcessor(test_mode=True)
        self.rag_sage = RAGProcessor(f"{self.temp_dir}/rag.db")
        
        # テストデータリセット
        self.knowledge_sage.reset_for_testing()
        self.task_sage.reset_for_testing()
        self.incident_sage.reset_for_testing()
        
    async def teardown(self):

        
        """テスト環境クリーンアップ"""
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        print("🧹 テスト環境クリーンアップ完了")
        
    async def test_knowledge_to_rag_flow(self) -> bool:

            """Knowledge Sage → RAG Sage データフローテスト"""
            # 1. Knowledge Sageに知識を保存
            knowledge_data = {
                "title": "Elder Loop開発手法",
                "content": "Elder Loopは品質を重視した反復的開発手法です。7つのフェーズで構成されています。",
                "category": "development_methodology",
                "tags": ["elder-loop", "quality", "methodology"],
                "metadata": {
                    "author": "Claude Elder",
                    "importance": "high"
                }
            }
            
            store_result = await self.knowledge_sage.process_action("store_knowledge", {
                "knowledge": knowledge_data
            })
            
            if not store_result.get("success"):
                print(f"   ❌ 知識保存失敗: {store_result.get('error')}")
                return False
                
            knowledge_id = store_result["data"]["id"]
            print(f"   ✅ 知識保存成功: {knowledge_id}")
            
            # 2. RAG Sageでインデックス
            index_result = await self.rag_sage.process_action("index_document", {
                "document": {
                    "id": knowledge_id,
                    "content": knowledge_data["content"],
                    "source": "knowledge_sage",
                    "title": knowledge_data["title"],
                    "category": knowledge_data["category"],
                    "tags": knowledge_data["tags"]
                }
            })
            
            if not index_result.get("success"):
                print(f"   ❌ RAGインデックス失敗: {index_result.get('error')}")
                return False
                
            print("   ✅ RAGインデックス成功")
            
            # 3. RAG Sageで検索
            search_result = await self.rag_sage.process_action("search_knowledge", {
                "query": "Elder Loop",
                "limit": 5
            })
            
            if not search_result.get("success"):
                print(f"   ❌ RAG検索失敗: {search_result.get('error')}")
                return False
                
            results = search_result["data"]["results"]
            if len(results) == 0:
                print("   ❌ 検索結果なし")
                return False
                
            # 検索結果確認
            found = any(r["document_id"] == knowledge_id for r in results)
            if not found:
                print(f"   ❌ 保存した知識が検索結果に含まれない")
                return False
                
            print(f"   ✅ 検索成功: {len(results)}件ヒット")
            return True
            
        except Exception as e:
            print(f"   💥 エラー: {e}")
            return False
            
    async def test_task_to_incident_flow(self) -> bool:

            """Task Sage → Incident Sage エラーフローテスト"""
            # 1. Task Sageでタスク作成
            task_data = {
                "title": "重要なデプロイメントタスク",
                "description": "本番環境への重要なデプロイメント",
                "priority": "high",
                "tags": ["deployment", "production"]
            }
            
            create_result = await self.task_sage.process_action("create_task", {
                "task": task_data
            })
            
            if not create_result.get("success"):
                print(f"   ❌ タスク作成失敗: {create_result.get('error')}")
                return False
                
            task_id = create_result["data"]["task_id"]
            print(f"   ✅ タスク作成成功: {task_id}")
            
            # 2. タスク実行中にエラーが発生したと仮定
            # Incident Sageでインシデント検知
            incident_result = await self.incident_sage.process_action("detect_incident", {
                "anomaly_data": {
                    "component": f"task_execution_{task_id}",
                    "metric": "deployment_failure",
                    "value": 1.0,
                    "threshold": 0.0,
                    "severity": "critical",
                    "confidence": 0.95,
                    "related_task_id": task_id
                }
            })
            
            if not incident_result.get("success"):
                print(f"   ❌ インシデント検知失敗: {incident_result.get('error')}")
                return False
                
            incident_id = incident_result["data"]["incident_id"]
            print(f"   ✅ インシデント検知成功: {incident_id}")
            
            # 3. Task Sageでタスクステータス更新（失敗）
            update_result = await self.task_sage.process_action("update_task", {
                "task_id": task_id,
                "updates": {
                    "status": "failed",
                    "error_details": f"Deployment failed. Incident: {incident_id}"
                }
            })
            
            if not update_result.get("success"):
                print(f"   ❌ タスクステータス更新失敗: {update_result.get('error')}")
                return False
                
            print("   ✅ タスクステータス更新成功（failed）")
            
            # 4. インシデント対応
            response_result = await self.incident_sage.process_action("respond_to_incident", {
                "incident_id": incident_id
            })
            
            if not response_result.get("success"):
                print(f"   ❌ インシデント対応失敗: {response_result.get('error')}")
                return False
                
            print("   ✅ インシデント対応成功")
            return True
            
        except Exception as e:
            print(f"   💥 エラー: {e}")
            return False
            
    async def test_full_workflow_scenario(self) -> bool:

            """完全なワークフローシナリオテスト"""
            # 1. Knowledge Sageで開発ガイドライン保存
            guidelines_result = await self.knowledge_sage.process_action("store_knowledge", {
                "knowledge": {
                    "title": "エルダーズギルド開発ガイドライン",
                    "content": "1. TDD必須\n2. Elder Loop準拠\n3. 品質スコア90以上",
                    "category": "guidelines",
                    "tags": ["development", "quality", "tdd"]
                }
            })
            
            if not guidelines_result.get("success"):
                return False
                
            print("   ✅ Step 1: ガイドライン保存")
            
            # 2. Task Sageでワークフロー作成
            workflow_result = await self.task_sage.process_action("create_workflow", {
                "workflow": {
                    "name": "新機能開発フロー",
                    "description": "Elder Loop準拠の開発フロー",
                    "tasks": [
                        {
                            "title": "要件定義",
                            "description": "機能要件の明確化",
                            "estimated_hours": 2
                        },
                        {
                            "title": "TDDテスト作成",
                            "description": "Red Phaseテスト実装",
                            "estimated_hours": 3
                        },
                        {
                            "title": "実装",
                            "description": "Green Phase実装",
                            "estimated_hours": 5
                        }
                    ]
                }
            })
            
            if not workflow_result.get("success"):
                return False
                
            workflow_id = workflow_result["data"]["workflow_id"]
            print(f"   ✅ Step 2: ワークフロー作成: {workflow_id}")
            
            # 3. RAG Sageでガイドライン検索とインデックス
            rag_index_result = await self.rag_sage.process_action("index_document", {
                "document": {
                    "id": guidelines_result["data"]["id"],
                    "content": "TDD必須、Elder Loop準拠、品質スコア90以上",
                    "source": "knowledge_sage",
                    "title": "開発ガイドライン"
                }
            })
            
            if not rag_index_result.get("success"):
                return False
                
            print("   ✅ Step 3: ガイドラインインデックス")
            
            # 4. Incident Sageで品質基準登録
            quality_result = await self.incident_sage.process_action("register_quality_standard", {
                "standard": {
                    "name": "Elder Loop品質基準",
                    "description": "エルダーループ開発の品質基準",
                    "category": "development",
                    "metrics": {
                        "test_coverage": {
                            "name": "テストカバレッジ",
                            "target_value": 90.0,
                            "threshold_min": 80.0,
                            "unit": "%"
                        },
                        "quality_score": {
                            "name": "品質スコア",
                            "target_value": 95.0,
                            "threshold_min": 90.0,
                            "unit": "points"
                        }
                    },
                    "compliance_threshold": 90.0
                }
            })
            
            if not quality_result.get("success"):
                return False
                
            print("   ✅ Step 4: 品質基準登録")
            
            # 5. ワークフロー実行
            execute_result = await self.task_sage.process_action("execute_workflow", {
                "workflow_id": workflow_id
            })
            
            if not execute_result.get("success"):
                return False
                
            print("   ✅ Step 5: ワークフロー実行開始")
            
            # 6. 品質評価
            assessment_result = await self.incident_sage.process_action("assess_quality", {
                "standard_id": quality_result["data"]["standard_id"],
                "component": workflow_id,
                "metrics": {
                    "test_coverage": 92.0,
                    "quality_score": 94.0
                }
            })
            
            if not assessment_result.get("success"):
                return False
                
            compliance = assessment_result["data"]["overall_compliance"]
            print(f"   ✅ Step 6: 品質評価完了（適合率: {compliance}%）")
            
            return compliance >= 90.0
            
        except Exception as e:
            print(f"   💥 エラー: {e}")
            return False
            
    async def test_performance_integration(self) -> bool:

            """パフォーマンス統合テスト"""
            start_time = time.time()
            operations = []
            
            # 並行して複数の操作を実行
            tasks = []
            
            # Knowledge Sage: 10個の知識を並行保存
            for i in range(10):
                task = self.knowledge_sage.process_action("store_knowledge", {
                    "knowledge": {
                        "title": f"Performance Test Knowledge {i}",
                        "content": f"パフォーマンステスト用知識 {i}",
                        "category": "test"
                    }
                })
                tasks.append(task)
                
            # Task Sage: 10個のタスクを並行作成
            for i in range(10):
                task = self.task_sage.process_action("create_task", {
                    "task": {
                        "title": f"Performance Test Task {i}",
                        "description": f"パフォーマンステスト用タスク {i}",
                        "priority": "medium"
                    }
                })
                tasks.append(task)
                
            # RAG Sage: 10個のドキュメントを並行インデックス
            for i in range(10):
                task = self.rag_sage.process_action("index_document", {
                    "document": {
                        "id": f"perf_doc_{i}",
                        "content": f"パフォーマンステスト用ドキュメント {i}",
                        "source": "performance_test"
                    }
                })
                tasks.append(task)
                
            # すべての操作を並行実行
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 成功率計算
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            total = len(results)
            success_rate = (successful / total) * 100
            
            print(f"   📊 実行統計:")
            print(f"      - 総操作数: {total}")
            print(f"      - 成功数: {successful}")
            print(f"      - 成功率: {success_rate:.1f}%")
            print(f"      - 総実行時間: {total_time:.2f}秒")
            print(f"      - 平均処理時間: {(total_time / total):.3f}秒/操作")
            
            # 成功率90%以上かつ平均処理時間が0.5秒以下であること
            return success_rate >= 90 and (total_time / total) <= 0.5
            
        except Exception as e:
            print(f"   💥 エラー: {e}")
            return False
            
    async def test_error_recovery_flow(self) -> bool:

            """エラー回復フローテスト"""
            # 1. わざと不正なデータでエラーを発生させる
            error_results = []
            
            # Knowledge Sage: 空のデータ
            result = await self.knowledge_sage.process_action("store_knowledge", {})
            error_results.append(("Knowledge空データ", result))
            
            # Task Sage: 無効な優先度
            result = await self.task_sage.process_action("create_task", {
                "task": {
                    "title": "Invalid Priority Task",
                    "priority": "super-ultra-high"  # 無効な値
                }
            })
            error_results.append(("Task無効優先度", result))
            
            # RAG Sage: 巨大クエリ
            result = await self.rag_sage.process_action("search_knowledge", {
                "query": "x" * 20000  # 20KB
            })
            error_results.append(("RAG巨大クエリ", result))
            
            # Incident Sage: 不正な重要度
            result = await self.incident_sage.process_action("detect_incident", {
                "anomaly_data": {
                    "severity": "mega-critical"  # 無効な値
                }
            })
            error_results.append(("Incident不正重要度", result))
            
            # エラーハンドリング確認
            all_handled = True
            for name, result in error_results:
                if result.get("success", True):
                    print(f"   ❌ {name}: エラーが期待されたが成功した")
                    all_handled = False
                else:
                    error_msg = result.get("error", "")
                    if error_msg:
                        print(f"   ✅ {name}: 適切にエラー処理（{error_msg[:50]}...）")
                    else:
                        print(f"   ⚠️ {name}: エラーメッセージなし")
                        all_handled = False
                        
            return all_handled
            
        except Exception as e:
            print(f"   💥 予期しないエラー: {e}")
            return False
            
    async def run_all_tests(self) -> Dict[str, Any]:

            """すべての統合テストを実行"""
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
                    print(f"\n✅ {test_name} 成功 ({end_time - start_time:.2f}秒)")
                else:
                    print(f"\n❌ {test_name} 失敗")
                    
            except Exception as e:
                print(f"\n💥 {test_name} エラー: {e}")
                self.test_results[test_name] = {
                    "passed": False,
                    "error": str(e)
                }
                
        await self.teardown()
        
        # 総合結果
        success_rate = (passed_tests / total_tests) * 100
        total_duration = sum(r.get("duration", 0) for r in self.test_results.values())
        
        print("\n" + "=" * 70)
        print("📊 統合テスト結果サマリー")
        print("=" * 70)
        print(f"合格テスト: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"総実行時間: {total_duration:.2f}秒")
        
        # Elder Loop基準（80%以上）
        if success_rate >= 80:
            print(f"\n🎉 Elder Loop Quality Gate PASSED! ({success_rate:.1f}%)")
        else:
            print(f"\n❌ Elder Loop Quality Gate FAILED! ({success_rate:.1f}% < 80%)")
            
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": total_tests - passed_tests,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "details": self.test_results
        }


async def main():

        """メイン実行"""
    asyncio.run(main())