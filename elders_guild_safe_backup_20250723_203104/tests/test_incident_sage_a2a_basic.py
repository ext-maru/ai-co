#!/usr/bin/env python3
"""
🚨 Incident Sage A2A Agent - 基本テストスイート
=======================================

Elder Loop Phase 3: Knowledge Sageパターン適用
Incident Sage A2A Agent基本機能テスト

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
from incident_sage.a2a_agent import IncidentSageAgent

# Test framework imports
from python_a2a import Message, TextContent, MessageRole


class TestIncidentSageA2ABasic:


"""Incident Sage A2A Agent基本テスト"""
        self.test_results = {}
        self.logger = logging.getLogger("incident_sage_basic_test")
    
    async def run_basic_tests(self) -> Dict[str, Any]:

        """基本テスト実行"""
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
        
        print(f"\\n📊 基本テスト結果サマリー")
        print("=" * 70)
        print(f"合格テスト: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"総実行時間: {total_duration:.3f}秒")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "test_results": self.test_results
        }
    
    async def test_business_logic_basic(self) -> bool:

        """ビジネスロジック基本テスト"""
            # IncidentProcessor初期化
            processor = IncidentProcessor()
            
            # 基本機能テスト: インシデント検知
            anomaly_data = {
                "anomaly_data": {
                    "component": "test_service",
                    "metric": "error_rate",
                    "value": 15.5,
                    "threshold": 10.0,
                    "severity": "high",
                    "confidence": 0.9
                }
            }
            
            result = await processor.process_action("detect_incident", anomaly_data)
            
            # 結果検証
            if not result.get("success"):
                print(f"     ❌ インシデント検知失敗: {result.get('error')}")
                return False
            
            incident_data = result.get("data", {})
            if not incident_data.get("incident_id"):
                print(f"     ❌ インシデントID生成失敗")
                return False
            
            print(f"     ✅ インシデント検知成功: {incident_data['incident_id']}")
            return True
            
        except Exception as e:
            print(f"     💥 ビジネスロジックテストエラー: {e}")
            return False
    
    async def test_a2a_agent_basic(self) -> bool:

            """A2Aエージェント基本テスト"""
            # IncidentSageAgent初期化
            agent = IncidentSageAgent()
            init_result = await agent.initialize()
            
            if not init_result:
                print(f"     ❌ エージェント初期化失敗")
                return False
            
            # スキル情報確認
            skills_info = agent.get_skills_info()
            expected_skills = 16
            
            if skills_info["total_skills"] != expected_skills:
                print(f"     ❌ スキル数不一致: {skills_info['total_skills']} != {expected_skills}")
                return False
            
            # クリーンアップ
            await agent.shutdown()
            
            print(f"     ✅ A2Aエージェント初期化成功: {expected_skills}スキル")
            return True
            
        except Exception as e:
            print(f"     💥 A2Aエージェントテストエラー: {e}")
            return False
    
    async def test_incident_detection(self) -> bool:

            """インシデント検知テスト"""
            agent = IncidentSageAgent()
            await agent.initialize()
            
            # テストメッセージ作成
            test_data = {
                "anomaly_data": {
                    "component": "payment_service",
                    "metric": "response_time",
                    "value": 5000,
                    "threshold": 1000,
                    "severity": "critical"
                }
            }
            
            message = Message(
                role=MessageRole.USER,
                content=TextContent(text=json.dumps(test_data))
            )
            
            # スキル実行
            response = await agent.detect_incident_skill(message)
            
            # レスポンス解析
            response_data = json.loads(response.content.text)
            
            if not response_data.get("success"):
                print(f"     ❌ インシデント検知スキル失敗: {response_data.get('error')}")
                return False
            
            incident_info = response_data.get("data", {})
            if not incident_info.get("incident_id"):
                print(f"     ❌ インシデントID生成失敗")
                return False
            
            await agent.shutdown()
            print(f"     ✅ インシデント検知スキル成功: {incident_info['severity']}")
            return True
            
        except Exception as e:
            print(f"     💥 インシデント検知テストエラー: {e}")
            return False
    
    async def test_quality_assessment(self) -> bool:

            """品質評価テスト"""
            agent = IncidentSageAgent()
            await agent.initialize()
            
            # デフォルト品質基準でテスト
            test_data = {
                "standard_id": "elder_guild_quality_standard_" + datetime.now().strftime("%Y%m%d%H%M%S"),
                "component": "test_component",
                "metrics": {
                    "test_coverage": 85.0,
                    "iron_will_compliance": 100.0,
                    "code_quality_score": 88.5
                }
            }
            
            # まず品質基準を確認（デフォルトが存在するはず）
            processor = agent.incident_processor
            if not processor.quality_standards:
                print(f"     ❌ デフォルト品質基準が存在しない")
                return False
            
            # デフォルト品質基準IDを取得
            default_standard_id = list(processor.quality_standards.keys())[0]
            test_data["standard_id"] = default_standard_id
            
            message = Message(
                role=MessageRole.USER,
                content=TextContent(text=json.dumps(test_data))
            )
            
            # 品質評価スキル実行
            response = await agent.assess_quality_skill(message)
            response_data = json.loads(response.content.text)
            
            if not response_data.get("success"):
                print(f"     ❌ 品質評価スキル失敗: {response_data.get('error')}")
                return False
            
            assessment_info = response_data.get("data", {})
            if "overall_score" not in assessment_info:
                print(f"     ❌ 品質スコア計算失敗")
                return False
            
            await agent.shutdown()
            print(f"     ✅ 品質評価スキル成功: {assessment_info['overall_score']:.1f}%")
            return True
            
        except Exception as e:
            print(f"     💥 品質評価テストエラー: {e}")
            return False
    
    async def test_alert_management(self) -> bool:

            """アラート管理テスト"""
            agent = IncidentSageAgent()
            await agent.initialize()
            
            # アラートルール作成テスト
            alert_data = {
                "alert_rule": {
                    "name": "Test Alert Rule",
                    "description": "テスト用アラートルール",
                    "condition_expression": "error_rate > 5.0",
                    "severity": "medium",
                    "enabled": True
                }
            }
            
            message = Message(
                role=MessageRole.USER,
                content=TextContent(text=json.dumps(alert_data))
            )
            
            # アラートルール作成スキル実行
            response = await agent.create_alert_rule_skill(message)
            response_data = json.loads(response.content.text)
            
            if not response_data.get("success"):
                print(f"     ❌ アラートルール作成失敗: {response_data.get('error')}")
                return False
            
            rule_info = response_data.get("data", {})
            if not rule_info.get("rule_id"):
                print(f"     ❌ アラートルールID生成失敗")
                return False
            
            # アラートルール評価テスト
            eval_data = {
                "metrics": {
                    "error_rate": 7.5  # 閾値5.0を超過
                }
            }
            
            eval_message = Message(
                role=MessageRole.USER,
                content=TextContent(text=json.dumps(eval_data))
            )
            
            eval_response = await agent.evaluate_alert_rules_skill(eval_message)
            eval_response_data = json.loads(eval_response.content.text)
            
            if not eval_response_data.get("success"):
                print(f"     ❌ アラートルール評価失敗: {eval_response_data.get('error')}")
                return False
            
            await agent.shutdown()
            print(f"     ✅ アラート管理スキル成功: ルール作成・評価完了")
            return True
            
        except Exception as e:
            print(f"     💥 アラート管理テストエラー: {e}")
            return False
    
    async def test_monitoring_basic(self) -> bool:

            """監視機能基本テスト"""
            agent = IncidentSageAgent()
            await agent.initialize()
            
            # 監視対象登録テスト
            target_data = {
                "target": {
                    "name": "Test Service",
                    "type": "web_service",
                    "endpoint_url": "http://test-service:8080",
                    "health_check_enabled": True
                }
            }
            
            message = Message(
                role=MessageRole.USER,
                content=TextContent(text=json.dumps(target_data))
            )
            
            # 監視対象登録スキル実行
            response = await agent.register_monitoring_target_skill(message)
            response_data = json.loads(response.content.text)
            
            if not response_data.get("success"):
                print(f"     ❌ 監視対象登録失敗: {response_data.get('error')}")
                return False
            
            target_info = response_data.get("data", {})
            target_id = target_info.get("target_id")
            
            if not target_id:
                print(f"     ❌ 監視対象ID生成失敗")
                return False
            
            # ヘルスチェックテスト
            health_data = {"target_id": target_id}
            health_message = Message(
                role=MessageRole.USER,
                content=TextContent(text=json.dumps(health_data))
            )
            
            health_response = await agent.check_target_health_skill(health_message)
            health_response_data = json.loads(health_response.content.text)
            
            if not health_response_data.get("success"):
                print(f"     ❌ ヘルスチェック失敗: {health_response_data.get('error')}")
                return False
            
            await agent.shutdown()
            print(f"     ✅ 監視機能基本テスト成功: 登録・ヘルスチェック完了")
            return True
            
        except Exception as e:
            print(f"     💥 監視機能テストエラー: {e}")
            return False
    
    async def test_pattern_learning(self) -> bool:

            """パターン学習テスト"""
            agent = IncidentSageAgent()
            await agent.initialize()
            
            # 複数インシデントを作成してパターン学習
            incidents_data = [
                {
                    "anomaly_data": {
                        "component": "payment_service",
                        "metric": "error_rate",
                        "severity": "high",
                        "category": "performance"
                    }
                },
                {
                    "anomaly_data": {
                        "component": "payment_service", 
                        "metric": "response_time",
                        "severity": "medium",
                        "category": "performance"
                    }
                }
            ]
            
            # インシデント作成
            for incident_data in incidents_data:
                message = Message(
                    role=MessageRole.USER,
                    content=TextContent(text=json.dumps(incident_data))
                )
                await agent.detect_incident_skill(message)
            
            # パターン学習実行
            learn_message = Message(
                role=MessageRole.USER,
                content=TextContent(text="{}")
            )
            
            response = await agent.learn_incident_patterns_skill(learn_message)
            response_data = json.loads(response.content.text)
            
            if not response_data.get("success"):
                print(f"     ❌ パターン学習失敗: {response_data.get('error')}")
                return False
            
            learning_info = response_data.get("data", {})
            patterns_learned = learning_info.get("patterns_learned", 0)
            
            if patterns_learned == 0:
                print(f"     ⚠️ パターン学習: パターン検出なし（正常、少数データのため）")
            else:
                print(f"     ✅ パターン学習成功: {patterns_learned}パターン学習")
            
            await agent.shutdown()
            return True
            
        except Exception as e:
            print(f"     💥 パターン学習テストエラー: {e}")
            return False
    
    async def test_statistics_basic(self) -> bool:

            """統計機能基本テスト"""
            agent = IncidentSageAgent()
            await agent.initialize()
            
            # 統計情報取得テスト
            message = Message(
                role=MessageRole.USER,
                content=TextContent(text="{}")
            )
            
            response = await agent.get_statistics_skill(message)
            response_data = json.loads(response.content.text)
            
            if not response_data.get("success"):
                print(f"     ❌ 統計情報取得失敗: {response_data.get('error')}")
                return False
            
            stats_info = response_data.get("data", {})
            required_sections = ["incident_statistics", "quality_statistics", "operational_metrics"]
            
            for section in required_sections:
                if section not in stats_info:
                    print(f"     ❌ 統計セクション不足: {section}")
                    return False
            
            # 運用メトリクス取得テスト
            metrics_response = await agent.get_operational_metrics_skill(message)
            metrics_data = json.loads(metrics_response.content.text)
            
            if not metrics_data.get("success"):
                print(f"     ❌ 運用メトリクス取得失敗: {metrics_data.get('error')}")
                return False
            
            await agent.shutdown()
            print(f"     ✅ 統計機能基本テスト成功: 統計・メトリクス取得完了")
            return True
            
        except Exception as e:
            print(f"     💥 統計機能テストエラー: {e}")
            return False
    
    async def test_health_check(self) -> bool:

            """ヘルスチェックテスト"""
            agent = IncidentSageAgent()
            
            # 初期化前ヘルスチェック
            message = Message(
                role=MessageRole.USER,
                content=TextContent(text="{}")
            )
            
            response = await agent.health_check_skill(message)
            response_data = json.loads(response.content.text)
            
            if not response_data.get("success"):
                print(f"     ❌ 初期化前ヘルスチェック失敗: {response_data.get('error')}")
                return False
            
            health_info = response_data.get("data", {})
            if health_info.get("status") != "initializing":
                print(f"     ❌ 初期化前ステータス不正: {health_info.get('status')}")
                return False
            
            # 初期化後ヘルスチェック
            await agent.initialize()
            
            response = await agent.health_check_skill(message)
            response_data = json.loads(response.content.text)
            
            if not response_data.get("success"):
                print(f"     ❌ 初期化後ヘルスチェック失敗: {response_data.get('error')}")
                return False
            
            health_info = response_data.get("data", {})
            if health_info.get("status") != "healthy":
                print(f"     ❌ 初期化後ステータス不正: {health_info.get('status')}")
                return False
            
            await agent.shutdown()
            print(f"     ✅ ヘルスチェックテスト成功: 初期化前後の状態確認完了")
            return True
            
        except Exception as e:
            print(f"     💥 ヘルスチェックテストエラー: {e}")
            return False
    
    async def test_error_handling_basic(self) -> bool:

            """エラーハンドリング基本テスト"""
            agent = IncidentSageAgent()
            await agent.initialize()
            
            # 不正なデータでテスト
            test_cases = [
                {
                    "name": "無効なインシデントデータ",
                    "skill": agent.detect_incident_skill,
                    "data": {"invalid": "data"}
                },
                {
                    "name": "存在しない品質基準",
                    "skill": agent.assess_quality_skill,
                    "data": {
                        "standard_id": "non_existent_standard",
                        "component": "test",
                        "metrics": {}
                    }
                },
                {
                    "name": "存在しないインシデント対応",
                    "skill": agent.respond_to_incident_skill,
                    "data": {"incident_id": "non_existent_incident"}
                }
            ]
            
            for test_case in test_cases:
                message = Message(
                    role=MessageRole.USER,
                    content=TextContent(text=json.dumps(test_case["data"]))
                )
                
                response = await test_case["skill"](message)
                response_data = json.loads(response.content.text)
                
                # エラーが適切に処理されているかチェック
                if response_data.get("success"):
                    print(f"     ❌ {test_case['name']}: エラーが検出されなかった")
                    return False
                
                if "error" not in response_data:
                    print(f"     ❌ {test_case['name']}: エラーメッセージがない")
                    return False
            
            await agent.shutdown()
            print(f"     ✅ エラーハンドリング基本テスト成功: 全エラーケース適切処理")
            return True
            
        except Exception as e:
            print(f"     💥 エラーハンドリングテストエラー: {e}")
            return False


async def main():

            """メイン実行"""
        print(f"\\n🎉 Incident Sage基本テスト成功！")
        print(f"   成功率: {results['success_rate']:.1f}%")
        print(f"   実行時間: {results['total_duration']:.3f}秒")
        print(f"   🚨 Elder Loop Phase 3完了準備")
        return True
    else:
        print(f"\\n🔧 Incident Sage基本テストで調整が必要")
        print(f"   成功率: {results['success_rate']:.1f}% (80%未満)")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)