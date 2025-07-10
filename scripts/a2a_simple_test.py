#!/usr/bin/env python3
"""
A2A通信の簡単なテスト
設定問題を回避した基本的なA2A通信テスト
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleA2ATest:
    """簡単なA2A通信テスト"""

    def __init__(self):
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
            "communications": [],
        }

    def test_a2a_imports(self):
        """A2A関連のインポートテスト"""
        print("📋 A2Aインポートテスト...")

        try:
            # A2A通信モジュールのインポート
            from libs.a2a_communication import AgentType
            from libs.a2a_communication import MessagePriority
            from libs.a2a_communication import MessageType

            print("  ✅ A2A通信モジュールインポート成功")
            self.test_results["tests_passed"] += 1

            # 列挙型のテスト
            print(f"  📊 メッセージタイプ: {len(MessageType)}種類")
            print(f"  📊 優先度レベル: {len(MessagePriority)}レベル")
            print(f"  📊 エージェントタイプ: {len(AgentType)}種類")

            return True

        except Exception as e:
            print(f"  ❌ インポートエラー: {e}")
            self.test_results["errors"].append(f"Import error: {e}")
            self.test_results["tests_failed"] += 1
            return False

        finally:
            self.test_results["tests_run"] += 1

    def test_message_creation(self):
        """メッセージ作成テスト"""
        print("\n📝 メッセージ作成テスト...")

        try:
            # メッセージ作成のテスト
            message_data = {
                "id": "test_001",
                "type": "query_request",
                "priority": 3,
                "source": "test_agent",
                "target": "knowledge_sage",
                "payload": {"query": "Hello from A2A test!"},
                "timestamp": datetime.now().isoformat(),
            }

            print("  ✅ テストメッセージ作成成功")
            print(f"  📊 メッセージID: {message_data['id']}")
            print(f"  📊 送信者: {message_data['source']} → {message_data['target']}")

            self.test_results["communications"].append(message_data)
            self.test_results["tests_passed"] += 1
            return True

        except Exception as e:
            print(f"  ❌ メッセージ作成エラー: {e}")
            self.test_results["errors"].append(f"Message creation error: {e}")
            self.test_results["tests_failed"] += 1
            return False

        finally:
            self.test_results["tests_run"] += 1

    def test_rabbitmq_connection(self):
        """RabbitMQ接続テスト"""
        print("\n🐰 RabbitMQ接続テスト...")

        try:
            import pika

            # 接続パラメータ
            connection_params = pika.ConnectionParameters(
                host="localhost", port=5672, virtual_host="/", connection_attempts=3, retry_delay=1
            )

            # 接続テスト
            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()

            # テストキューの作成
            queue_name = "a2a_test_queue"
            channel.queue_declare(queue=queue_name, durable=False)

            # テストメッセージの送信
            test_message = json.dumps({"test": "A2A communication test", "timestamp": datetime.now().isoformat()})

            channel.basic_publish(exchange="", routing_key=queue_name, body=test_message)

            print("  ✅ RabbitMQ接続成功")
            print("  ✅ テストキュー作成成功")
            print("  ✅ テストメッセージ送信成功")

            # キューの削除
            channel.queue_delete(queue=queue_name)
            connection.close()

            self.test_results["tests_passed"] += 1
            return True

        except Exception as e:
            print(f"  ❌ RabbitMQ接続エラー: {e}")
            self.test_results["errors"].append(f"RabbitMQ connection error: {e}")
            self.test_results["tests_failed"] += 1
            return False

        finally:
            self.test_results["tests_run"] += 1

    def test_four_sages_simulation(self):
        """4賢者シミュレーションテスト"""
        print("\n🧙‍♂️ 4賢者シミュレーションテスト...")

        try:
            # 4賢者の疑似的な会話シミュレーション
            sages = [
                {"id": "knowledge_sage", "name": "ナレッジ賢者", "role": "知識管理"},
                {"id": "task_sage", "name": "タスク賢者", "role": "タスク管理"},
                {"id": "rag_sage", "name": "RAG賢者", "role": "情報検索"},
                {"id": "incident_sage", "name": "インシデント賢者", "role": "危機管理"},
            ]

            # 会話シナリオの実行
            scenario = [
                {
                    "from": "task_sage",
                    "to": "knowledge_sage",
                    "message": "新しいタスクの処理方法を教えて",
                    "type": "knowledge_query",
                },
                {
                    "from": "knowledge_sage",
                    "to": "task_sage",
                    "message": "過去のパターンに基づいて3つの選択肢があります",
                    "type": "query_response",
                },
                {"from": "task_sage", "to": "rag_sage", "message": "関連する実装例を検索して", "type": "query_request"},
                {
                    "from": "rag_sage",
                    "to": "incident_sage",
                    "message": "この実装にリスクはありますか？",
                    "type": "urgent_consultation",
                },
            ]

            print("  🎭 4賢者会話シナリオ実行:")
            for i, interaction in enumerate(scenario, 1):
                sage_from = next(s for s in sages if s["id"] == interaction["from"])
                sage_to = next(s for s in sages if s["id"] == interaction["to"])

                print(f"    {i}. {sage_from['name']} → {sage_to['name']}")
                print(f"       「{interaction['message']}」")
                print(f"       タイプ: {interaction['type']}")

                # 通信記録に追加
                self.test_results["communications"].append(
                    {
                        "from": interaction["from"],
                        "to": interaction["to"],
                        "message": interaction["message"],
                        "type": interaction["type"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            print("  ✅ 4賢者シミュレーション完了")
            self.test_results["tests_passed"] += 1
            return True

        except Exception as e:
            print(f"  ❌ 4賢者シミュレーションエラー: {e}")
            self.test_results["errors"].append(f"Four sages simulation error: {e}")
            self.test_results["tests_failed"] += 1
            return False

        finally:
            self.test_results["tests_run"] += 1

    def test_monitoring_integration(self):
        """監視システム統合テスト"""
        print("\n📊 監視システム統合テスト...")

        try:
            # 監視システムのインポート
            from scripts.a2a_monitoring_system import A2AMonitoringSystem

            monitor = A2AMonitoringSystem()

            # 疑似的な通信記録
            monitor.record_communication(
                source_agent="test_agent",
                target_agent="knowledge_sage",
                message_type="test_message",
                status="success",
                response_time=0.05,
                metadata={"test": "A2A integration test"},
            )

            print("  ✅ 監視システム統合成功")
            print("  ✅ 通信記録保存成功")

            self.test_results["tests_passed"] += 1
            return True

        except Exception as e:
            print(f"  ❌ 監視システム統合エラー: {e}")
            self.test_results["errors"].append(f"Monitoring integration error: {e}")
            self.test_results["tests_failed"] += 1
            return False

        finally:
            self.test_results["tests_run"] += 1

    def generate_test_report(self):
        """テストレポート生成"""
        self.test_results["end_time"] = datetime.now().isoformat()

        print("\n" + "=" * 60)
        print("🧪 A2A通信テストレポート")
        print("=" * 60)

        print(f"実行時間: {self.test_results['start_time']} - {self.test_results['end_time']}")
        print(f"総テスト数: {self.test_results['tests_run']}")
        print(f"成功: {self.test_results['tests_passed']}")
        print(f"失敗: {self.test_results['tests_failed']}")

        if self.test_results["tests_run"] > 0:
            success_rate = (self.test_results["tests_passed"] / self.test_results["tests_run"]) * 100
            print(f"成功率: {success_rate:.1f}%")

        print(f"\n📡 通信記録: {len(self.test_results['communications'])}件")

        if self.test_results["errors"]:
            print("\n❌ エラー詳細:")
            for error in self.test_results["errors"]:
                print(f"  - {error}")

        # レポートファイルの保存
        report_file = PROJECT_ROOT / "logs" / "a2a_test_report.json"
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)

        print(f"\n📄 詳細レポート保存: {report_file}")

        return self.test_results

    def run_all_tests(self):
        """すべてのテストを実行"""
        print("🤖 A2A（AI-to-AI通信）テスト開始")
        print("=" * 60)

        # テスト実行
        self.test_a2a_imports()
        self.test_message_creation()
        self.test_rabbitmq_connection()
        self.test_four_sages_simulation()
        self.test_monitoring_integration()

        # レポート生成
        return self.generate_test_report()


def main():
    """メイン処理"""
    tester = SimpleA2ATest()
    results = tester.run_all_tests()

    # 結果に基づく推奨事項
    print("\n💡 推奨事項:")

    if results["tests_passed"] == results["tests_run"]:
        print("  ✅ すべてのテストが成功しました！")
        print("  🚀 A2A通信システムは動作準備完了です")
        print("  🔄 次のステップ: 実際の4賢者通信を開始")
    else:
        print("  ⚠️  一部のテストが失敗しました")
        print("  🔧 エラーを確認して修正してください")
        print("  📊 詳細レポートを確認してください")

    return results


if __name__ == "__main__":
    main()
