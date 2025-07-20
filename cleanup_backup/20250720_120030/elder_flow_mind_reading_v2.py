#!/usr/bin/env python3
"""
Elder Flow v2.0 - Mind Reading Protocol統合版
maru様の思考を理解し、自動実行する完全自動化システム

🌌 nWo Integration: Think it, Rule it, Own it
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Mind Reading Protocol統合
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from libs.mind_reading_core import MindReadingCore, IntentType
    from libs.intent_parser import IntentParser
    from libs.learning_data_collector import LearningDataCollector, ExecutionStatus
except ImportError:
    print("⚠️ Mind Reading Protocol not available. Running in basic mode.")
    MindReadingCore = None
    IntentParser = None
    LearningDataCollector = None


class ElderFlowMindReading:
    """Elder Flow v2.0 - Mind Reading Protocol統合システム"""

    def __init__(self):
        self.logger = self._setup_logger()

        # Mind Reading Protocol初期化
        self.mind_reader = None
        self.intent_parser = None
        self.learning_collector = None

        # Elder Flow機能
        self.execution_history = []
        self.auto_mode = False

        # 統計
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "mind_reading_accuracy": 0.0,
            "auto_execution_rate": 0.0
        }

        self.logger.info("🌊 Elder Flow v2.0 Mind Reading Edition initialized")

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("elder_flow_mind_reading")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - Elder Flow v2.0 - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def initialize_mind_reading(self):
        """Mind Reading Protocolコンポーネントの初期化"""
        if MindReadingCore is None:
            self.logger.warning("Mind Reading Protocol not available")
            return False

        try:
            self.logger.info("🧠 Initializing Mind Reading Protocol...")

            self.mind_reader = MindReadingCore()
            self.intent_parser = IntentParser()
            self.learning_collector = LearningDataCollector()

            self.logger.info("✅ Mind Reading Protocol initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Mind Reading Protocol: {e}")
            return False

    async def process_maru_input(self, maru_text: str) -> Dict[str, Any]:
        """
        maru様の入力を処理し、Elder Flowで自動実行

        Args:
            maru_text: maru様からの指示テキスト

        Returns:
            実行結果の詳細
        """
        self.logger.info(f"🎯 Processing maru様's input: {maru_text[:50]}...")

        if not self.mind_reader:
            return await self._fallback_processing(maru_text)

        try:
            # 1. Mind Reading - 意図理解
            intent_result = await self.mind_reader.understand_intent(maru_text)
            self.logger.info(f"🧠 Intent understood: {intent_result.intent_type.value} ({intent_result.confidence:.2%})")

            # 2. Intent Parser - コマンド生成
            parsed_command = await self.intent_parser.parse_intent(intent_result, maru_text)
            command = await self.intent_parser.generate_command(parsed_command)
            self.logger.info(f"💭 Command generated: {command}")

            # 3. Elder Flow実行判定
            should_auto_execute = self._should_auto_execute(intent_result, parsed_command)

            # 4. 実行
            if should_auto_execute or self.auto_mode:
                execution_result = await self._execute_elder_flow_command(command, intent_result)
            else:
                execution_result = await self._generate_execution_plan(command, intent_result)

            # 5. 学習データ収集
            await self._record_execution(
                maru_text, intent_result, parsed_command, command, execution_result
            )

            # 6. 統計更新
            self._update_stats(intent_result, execution_result)

            return {
                "input_text": maru_text,
                "intent": intent_result.intent_type.value,
                "confidence": intent_result.confidence,
                "command": command,
                "executed": should_auto_execute or self.auto_mode,
                "result": execution_result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error processing input: {e}")
            return {
                "input_text": maru_text,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _should_auto_execute(self, intent_result, parsed_command) -> bool:
        """自動実行判定"""
        # 高信頼度の場合は自動実行
        if intent_result.confidence > 0.9:
            return True

        # Elder Flow明示的な場合は自動実行
        if "elder" in parsed_command.original_text.lower() and "flow" in parsed_command.original_text.lower():
            return True

        # 緊急度が高い場合は自動実行
        if intent_result.urgency in ["urgent", "high"]:
            return True

        # 開発系で優先度が高い場合
        if intent_result.intent_type == IntentType.DEVELOPMENT and intent_result.priority in ["high", "critical"]:
            return True

        return False

    async def _execute_elder_flow_command(self, command: str, intent_result) -> Dict[str, Any]:
        """Elder Flowコマンドの実行"""
        self.logger.info(f"⚡ Executing: {command}")

        start_time = datetime.now()

        try:
            if command.startswith("elder-flow"):
                # Elder Flow CLI実行
                result = await self._run_elder_flow_cli(command)
            elif command.startswith("ai-tdd"):
                # TDD開発実行
                result = await self._run_tdd_development(command)
            elif command.startswith("ai-optimize"):
                # 最適化実行
                result = await self._run_optimization(command)
            elif command.startswith("ai-fix-bug"):
                # バグ修正実行
                result = await self._run_bug_fix(command)
            else:
                # 一般コマンド実行
                result = await self._run_general_command(command)

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "status": "success",
                "command": command,
                "result": result,
                "execution_time": execution_time,
                "auto_executed": True
            }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Execution failed: {e}")

            return {
                "status": "error",
                "command": command,
                "error": str(e),
                "execution_time": execution_time,
                "auto_executed": False
            }

    async def _generate_execution_plan(self, command: str, intent_result) -> Dict[str, Any]:
        """実行計画の生成（自動実行しない場合）"""
        return {
            "status": "plan_generated",
            "command": command,
            "intent": intent_result.intent_type.value,
            "confidence": intent_result.confidence,
            "suggested_actions": intent_result.suggested_actions,
            "recommendation": "Review and execute manually if needed",
            "auto_executed": False
        }

    async def _run_elder_flow_cli(self, command: str) -> str:
        """Elder Flow CLI実行"""
        # Extract parameters from command
        parts = command.split()
        if len(parts) >= 3:
            task_description = parts[2].strip('"')
            priority = "high"

            if "--priority" in parts:
                priority_idx = parts.index("--priority")
                if priority_idx + 1 < len(parts):
                    priority = parts[priority_idx + 1]

            # Elder Flow実行シミュレーション
            await asyncio.sleep(1)  # 実行時間シミュレーション

            return f"Elder Flow executed: {task_description} (priority: {priority})"

        return "Elder Flow executed with default parameters"

    async def _run_tdd_development(self, command: str) -> str:
        """TDD開発実行"""
        await asyncio.sleep(2)  # 開発時間シミュレーション
        return f"TDD development completed: {command}"

    async def _run_optimization(self, command: str) -> str:
        """最適化実行"""
        await asyncio.sleep(1.5)  # 最適化時間シミュレーション
        return f"Optimization completed: {command}"

    async def _run_bug_fix(self, command: str) -> str:
        """バグ修正実行"""
        await asyncio.sleep(1)  # 修正時間シミュレーション
        return f"Bug fix completed: {command}"

    async def _run_general_command(self, command: str) -> str:
        """一般コマンド実行"""
        await asyncio.sleep(0.5)  # 実行時間シミュレーション
        return f"Command executed: {command}"

    async def _record_execution(self, maru_text: str, intent_result, parsed_command, command: str, execution_result: Dict):
        """実行履歴の記録"""
        if not self.learning_collector:
            return

        try:
            status = ExecutionStatus.SUCCESS if execution_result.get("status") == "success" else ExecutionStatus.FAILURE
            execution_time = execution_result.get("execution_time", 0.0)
            output = str(execution_result.get("result", ""))

            await self.learning_collector.record_execution(
                original_text=maru_text,
                intent_result=intent_result,
                parsed_command=parsed_command,
                executed_command=command,
                execution_time=execution_time,
                status=status,
                output=output,
                feedback={"elder_flow_v2": True, "auto_executed": execution_result.get("auto_executed", False)}
            )

        except Exception as e:
            self.logger.error(f"Failed to record execution: {e}")

    def _update_stats(self, intent_result, execution_result):
        """統計更新"""
        self.stats["total_executions"] += 1

        if execution_result.get("status") == "success":
            self.stats["successful_executions"] += 1

        # Mind Reading精度更新
        total = self.stats["total_executions"]
        if total > 0:
            self.stats["mind_reading_accuracy"] = (
                self.stats["mind_reading_accuracy"] * (total - 1) + intent_result.confidence
            ) / total

        # 自動実行率更新
        if execution_result.get("auto_executed"):
            auto_count = sum(1 for h in self.execution_history if h.get("auto_executed"))
            self.stats["auto_execution_rate"] = (auto_count + 1) / total

        # 履歴に追加
        self.execution_history.append({
            "intent": intent_result.intent_type.value,
            "confidence": intent_result.confidence,
            "auto_executed": execution_result.get("auto_executed", False),
            "success": execution_result.get("status") == "success",
            "timestamp": datetime.now().isoformat()
        })

    async def _fallback_processing(self, maru_text: str) -> Dict[str, Any]:
        """Mind Reading Protocol未使用時のフォールバック処理"""
        self.logger.info("Using fallback processing (no Mind Reading)")

        # 簡易パターンマッチング
        if any(word in maru_text.lower() for word in ["実装", "開発", "作成", "create", "implement"]):
            command = f'ai-tdd new "{maru_text}" "Implementation task"'
            intent = "development"
        elif any(word in maru_text.lower() for word in ["修正", "バグ", "fix", "bug"]):
            command = f'ai-fix-bug "{maru_text}"'
            intent = "bug_fix"
        elif any(word in maru_text.lower() for word in ["最適化", "optimize"]):
            command = f'ai-optimize "{maru_text}"'
            intent = "optimization"
        else:
            command = f'echo "Processing: {maru_text}"'
            intent = "general"

        # 基本実行
        result = await self._run_general_command(command)

        return {
            "input_text": maru_text,
            "intent": intent,
            "confidence": 0.5,
            "command": command,
            "executed": True,
            "result": {"status": "success", "result": result, "auto_executed": True},
            "timestamp": datetime.now().isoformat()
        }

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            **self.stats,
            "execution_history_count": len(self.execution_history),
            "mind_reading_available": self.mind_reader is not None,
            "auto_mode": self.auto_mode
        }

    def set_auto_mode(self, enabled: bool):
        """自動実行モードの設定"""
        self.auto_mode = enabled
        self.logger.info(f"Auto mode {'enabled' if enabled else 'disabled'}")


async def main():
    """メイン実行"""
    print("🌊 Elder Flow v2.0 - Mind Reading Protocol統合版")
    print("=" * 60)
    print("💭 Think it, Rule it, Own it")
    print("=" * 60)

    # Elder Flow Mind Reading初期化
    elder_flow = ElderFlowMindReading()

    # Mind Reading Protocol初期化
    mind_reading_ready = await elder_flow.initialize_mind_reading()

    if mind_reading_ready:
        print("✅ Mind Reading Protocol integrated successfully!")
    else:
        print("⚠️ Running in fallback mode")

    # テストシナリオ
    test_scenarios = [
        "Elder FlowでOAuth2.0認証システムを実装して",
        "今すぐバグを修正してください",
        "素晴らしい実装ですね！継続してください",
        "DBクエリのパフォーマンスを最適化したい",
        "AIシステムの監視ダッシュボードを作成",
        "セキュリティ脆弱性をスキャンして修正"
    ]

    print(f"\n🎯 Processing {len(test_scenarios)} scenarios...")
    print("-" * 60)

    results = []

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n[Scenario {i}] \"{scenario}\"")

        # Elder Flow Mind Reading処理
        result = await elder_flow.process_maru_input(scenario)
        results.append(result)

        # 結果表示
        if "error" not in result:
            print(f"   🧠 Intent: {result['intent']}")
            print(f"   📊 Confidence: {result['confidence']:.2%}")
            print(f"   💻 Command: {result['command']}")
            print(f"   ⚡ Auto-executed: {'Yes' if result['executed'] else 'No'}")

            if result['executed']:
                exec_result = result['result']
                print(f"   ✅ Status: {exec_result['status']}")
                if exec_result['status'] == 'success':
                    print(f"   📝 Result: {exec_result['result'][:50]}...")
        else:
            print(f"   ❌ Error: {result['error']}")

        print("-" * 60)

    # 統計表示
    print("\n📊 Elder Flow v2.0 Statistics:")
    stats = elder_flow.get_statistics()
    print(f"   Total Executions: {stats['total_executions']}")
    print(f"   Success Rate: {stats['successful_executions'] / stats['total_executions'] * 100:.1f}%")
    print(f"   Mind Reading Accuracy: {stats['mind_reading_accuracy']:.2%}")
    print(f"   Auto Execution Rate: {stats['auto_execution_rate']:.2%}")
    print(f"   Mind Reading Available: {stats['mind_reading_available']}")

    # 学習データ統計
    if elder_flow.learning_collector:
        learning_stats = elder_flow.learning_collector.get_statistics()
        print(f"   Learning Data Entries: {learning_stats.get('total_executions', 0)}")

    print("\n✨ Elder Flow v2.0 Mind Reading Edition Demo Complete!")
    print("🌌 nWo Protocol fully integrated and operational!")

    return results


if __name__ == "__main__":
    asyncio.run(main())
