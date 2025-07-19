#!/usr/bin/env python3
"""
System Recovery Orchestrator - システム基本機能完全回復オーケストレーター
API Integration Knight と Worker Stabilization Knight を連携させて完全回復を実行
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# プロジェクトパス追加
sys.path.append(str(Path(__file__).parent.parent))

from libs.api_integration_knight import APIIntegrationKnight
from libs.worker_stabilization_knight import WorkerStabilizationKnight

logger = logging.getLogger(__name__)


class SystemRecoveryOrchestrator:
    """
    System Recovery Orchestrator - システム回復オーケストレーター

    機能:
    - 2つの専門騎士を連携させたシステム回復
    - 修復作業の順序制御と依存関係管理
    - 修復進捗の監視と報告
    - 回復検証とパフォーマンス測定
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.api_knight = APIIntegrationKnight()
        self.worker_knight = WorkerStabilizationKnight()

        # 回復状況追跡
        self.recovery_session = {
            "session_id": f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": datetime.now(),
            "phases": {
                "api_integration": {"status": "pending", "issues": 0, "fixed": 0},
                "worker_stabilization": {"status": "pending", "issues": 0, "fixed": 0},
                "system_verification": {"status": "pending", "tests": 0, "passed": 0},
            },
            "total_issues": 0,
            "total_fixed": 0,
            "success_rate": 0.0,
        }

        # 報告ディレクトリ作成
        self.reports_dir = self.project_root / "data" / "recovery_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        logger.info("🎭 System Recovery Orchestrator 初期化完了")

    async def execute_full_recovery(self) -> Dict[str, Any]:
        """システム完全回復の実行"""
        logger.info("🚀 システム完全回復開始")

        try:
            # Phase 1: API統合修復
            await self._execute_api_integration_phase()

            # Phase 2: ワーカーシステム安定化
            await self._execute_worker_stabilization_phase()

            # Phase 3: システム検証
            await self._execute_system_verification_phase()

            # 最終報告生成
            final_report = await self._generate_final_report()

            return final_report

        except Exception as e:
            logger.error(f"システム回復実行エラー: {e}")
            return await self._generate_error_report(str(e))

    async def _execute_api_integration_phase(self):
        """Phase 1: API統合修復フェーズ"""
        logger.info("🔑 Phase 1: API統合修復開始")
        self.recovery_session["phases"]["api_integration"]["status"] = "in_progress"

        try:
            # API問題の検出
            api_issues = await self.api_knight.patrol()
            self.recovery_session["phases"]["api_integration"]["issues"] = len(
                api_issues
            )
            self.recovery_session["total_issues"] += len(api_issues)

            logger.info(f"🔍 API統合問題検出: {len(api_issues)}件")

            # 各問題の修復実行
            fixed_count = 0
            for issue in api_issues:
                try:
                    # 問題調査
                    diagnosis = await self.api_knight.investigate(issue)

                    # 修復実行
                    resolution = await self.api_knight.resolve(diagnosis)

                    if resolution.success:
                        fixed_count += 1
                        logger.info(f"✅ API問題修復成功: {issue.title}")
                    else:
                        logger.warning(f"❌ API問題修復失敗: {issue.title}")

                except Exception as e:
                    logger.error(f"API問題修復エラー {issue.id}: {e}")

            self.recovery_session["phases"]["api_integration"]["fixed"] = fixed_count
            self.recovery_session["phases"]["api_integration"]["status"] = "completed"
            self.recovery_session["total_fixed"] += fixed_count

            logger.info(f"🎯 API統合フェーズ完了: {fixed_count}/{len(api_issues)} 修復")

        except Exception as e:
            logger.error(f"API統合フェーズエラー: {e}")
            self.recovery_session["phases"]["api_integration"]["status"] = "failed"

    async def _execute_worker_stabilization_phase(self):
        """Phase 2: ワーカーシステム安定化フェーズ"""
        logger.info("⚙️ Phase 2: ワーカーシステム安定化開始")
        self.recovery_session["phases"]["worker_stabilization"][
            "status"
        ] = "in_progress"

        try:
            # ワーカー問題の検出
            worker_issues = await self.worker_knight.patrol()
            self.recovery_session["phases"]["worker_stabilization"]["issues"] = len(
                worker_issues
            )
            self.recovery_session["total_issues"] += len(worker_issues)

            logger.info(f"🔍 ワーカー問題検出: {len(worker_issues)}件")

            # 重要度順に修復実行
            sorted_issues = sorted(
                worker_issues,
                key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[
                    x.severity.value
                ],
            )

            fixed_count = 0
            for issue in sorted_issues:
                try:
                    # 問題調査
                    diagnosis = await self.worker_knight.investigate(issue)

                    # 修復実行
                    resolution = await self.worker_knight.resolve(diagnosis)

                    if resolution.success:
                        fixed_count += 1
                        logger.info(f"✅ ワーカー問題修復成功: {issue.title}")
                    else:
                        logger.warning(f"❌ ワーカー問題修復失敗: {issue.title}")

                    # 修復間隔（負荷軽減）
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"ワーカー問題修復エラー {issue.id}: {e}")

            self.recovery_session["phases"]["worker_stabilization"][
                "fixed"
            ] = fixed_count
            self.recovery_session["phases"]["worker_stabilization"][
                "status"
            ] = "completed"
            self.recovery_session["total_fixed"] += fixed_count

            logger.info(f"🎯 ワーカー安定化フェーズ完了: {fixed_count}/{len(worker_issues)} 修復")

        except Exception as e:
            logger.error(f"ワーカー安定化フェーズエラー: {e}")
            self.recovery_session["phases"]["worker_stabilization"]["status"] = "failed"

    async def _execute_system_verification_phase(self):
        """Phase 3: システム検証フェーズ"""
        logger.info("🔬 Phase 3: システム検証開始")
        self.recovery_session["phases"]["system_verification"]["status"] = "in_progress"

        try:
            verification_tests = [
                ("API接続テスト", self._verify_api_connectivity),
                ("ワーカー起動テスト", self._verify_worker_status),
                ("設定ファイル整合性", self._verify_configurations),
                ("ログシステム", self._verify_logging_system),
                ("リソース使用量", self._verify_resource_usage),
            ]

            passed_tests = 0
            total_tests = len(verification_tests)

            for test_name, test_func in verification_tests:
                try:
                    result = await test_func()
                    if result:
                        passed_tests += 1
                        logger.info(f"✅ 検証成功: {test_name}")
                    else:
                        logger.warning(f"❌ 検証失敗: {test_name}")

                except Exception as e:
                    logger.error(f"検証エラー {test_name}: {e}")

            self.recovery_session["phases"]["system_verification"][
                "tests"
            ] = total_tests
            self.recovery_session["phases"]["system_verification"][
                "passed"
            ] = passed_tests
            self.recovery_session["phases"]["system_verification"][
                "status"
            ] = "completed"

            logger.info(f"🎯 システム検証完了: {passed_tests}/{total_tests} テスト通過")

        except Exception as e:
            logger.error(f"システム検証エラー: {e}")
            self.recovery_session["phases"]["system_verification"]["status"] = "failed"

    async def _verify_api_connectivity(self) -> bool:
        """API接続性の検証"""
        try:
            # .envファイルの存在確認
            env_file = self.project_root / ".env"
            if not env_file.exists():
                return False

            # API設定の基本確認
            with open(env_file) as f:
                content = f.read()

            return "ANTHROPIC_API_KEY" in content

        except Exception:
            return False

    async def _verify_worker_status(self) -> bool:
        """ワーカー状態の検証"""
        try:
            # 必要なワーカーファイルの存在確認
            required_workers = [
                "workers/enhanced_task_worker.py",
                "workers/task_worker.py",
            ]

            for worker_file in required_workers:
                worker_path = self.project_root / worker_file
                if not worker_path.exists():
                    return False

            return True

        except Exception:
            return False

    async def _verify_configurations(self) -> bool:
        """設定ファイル整合性の検証"""
        try:
            # 設定ディレクトリの確認
            config_dir = self.project_root / "config"
            if not config_dir.exists():
                return False

            # 基本設定ファイルの確認
            config_files = ["worker_config.json", "claude_api.json"]
            existing_files = sum(1 for f in config_files if (config_dir / f).exists())

            return existing_files >= 1  # 最低1つの設定ファイルが存在

        except Exception:
            return False

    async def _verify_logging_system(self) -> bool:
        """ログシステムの検証"""
        try:
            # ログディレクトリの確認
            log_dir = self.project_root / "logs"
            log_dir.mkdir(exist_ok=True)

            # テストログファイル作成
            test_log = log_dir / "recovery_test.log"
            with open(test_log, "w") as f:
                f.write(f"Recovery test: {datetime.now().isoformat()}\n")

            return test_log.exists()

        except Exception:
            return False

    async def _verify_resource_usage(self) -> bool:
        """リソース使用量の検証"""
        try:
            import psutil

            # リソース使用量が健全な範囲内かチェック
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # CPU < 95%, Memory < 90% なら健全
            return cpu_percent < 95 and memory.percent < 90

        except Exception:
            return False

    async def _generate_final_report(self) -> Dict[str, Any]:
        """最終回復報告の生成"""
        end_time = datetime.now()
        duration = (end_time - self.recovery_session["start_time"]).total_seconds()

        # 成功率計算
        if self.recovery_session["total_issues"] > 0:
            self.recovery_session["success_rate"] = (
                self.recovery_session["total_fixed"]
                / self.recovery_session["total_issues"]
            )

        # 最終報告データ
        final_report = {
            "recovery_session": self.recovery_session,
            "summary": {
                "duration_seconds": duration,
                "total_issues_found": self.recovery_session["total_issues"],
                "total_issues_fixed": self.recovery_session["total_fixed"],
                "success_rate": self.recovery_session["success_rate"],
                "overall_status": "success"
                if self.recovery_session["success_rate"] > 0.7
                else "partial",
            },
            "phase_results": self.recovery_session["phases"],
            "recommendations": await self._generate_recommendations(),
            "next_steps": await self._generate_next_steps(),
            "generated_at": end_time.isoformat(),
        }

        # 報告ファイル保存
        report_file = (
            self.reports_dir
            / f"{self.recovery_session['session_id']}_final_report.json"
        )
        with open(report_file, "w") as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)

        logger.info(f"📋 最終報告生成完了: {report_file}")
        return final_report

    async def _generate_error_report(self, error_message: str) -> Dict[str, Any]:
        """エラー報告の生成"""
        error_report = {
            "recovery_session": self.recovery_session,
            "error": {
                "message": error_message,
                "occurred_at": datetime.now().isoformat(),
            },
            "status": "failed",
            "recovery_incomplete": True,
        }

        # エラー報告ファイル保存
        error_file = (
            self.reports_dir
            / f"{self.recovery_session['session_id']}_error_report.json"
        )
        with open(error_file, "w") as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False)

        return error_report

    async def _generate_recommendations(self) -> List[str]:
        """推奨事項の生成"""
        recommendations = []

        # API統合の結果に基づく推奨
        api_phase = self.recovery_session["phases"]["api_integration"]
        if (
            api_phase["status"] == "completed"
            and api_phase["fixed"] < api_phase["issues"]
        ):
            recommendations.append("APIキーの手動設定確認が必要です")

        # ワーカー安定化の結果に基づく推奨
        worker_phase = self.recovery_session["phases"]["worker_stabilization"]
        if (
            worker_phase["status"] == "completed"
            and worker_phase["fixed"] < worker_phase["issues"]
        ):
            recommendations.append("ワーカーの手動再起動を推奨します")

        # システム検証の結果に基づく推奨
        verify_phase = self.recovery_session["phases"]["system_verification"]
        if verify_phase["passed"] < verify_phase["tests"]:
            recommendations.append("システム設定の詳細確認が必要です")

        # 全体的な推奨
        if self.recovery_session["success_rate"] < 0.5:
            recommendations.append("手動による詳細調査を強く推奨します")
        elif self.recovery_session["success_rate"] < 0.8:
            recommendations.append("定期的な監視を継続してください")

        return recommendations if recommendations else ["システム回復が完了しました"]

    async def _generate_next_steps(self) -> List[str]:
        """次のステップの生成"""
        next_steps = []

        # 成功率に応じたステップ
        if self.recovery_session["success_rate"] >= 0.9:
            next_steps.extend(["継続的監視システムの有効化", "パフォーマンス最適化の実行", "自動バックアップの設定"])
        elif self.recovery_session["success_rate"] >= 0.7:
            next_steps.extend(["残存問題の手動確認", "システム安定性の24時間監視", "ログ分析による根本原因調査"])
        else:
            next_steps.extend(["緊急：手動システム診断の実行", "専門技術者による詳細調査", "システム設定の全面見直し"])

        return next_steps

    def print_recovery_summary(self, report: Dict[str, Any]):
        """回復結果のサマリー表示"""
        print("\n🎭 === システム完全回復結果 ===")
        print(f"📊 実行時間: {report['summary']['duration_seconds']:.1f}秒")
        print(f"🔍 検出問題: {report['summary']['total_issues_found']}件")
        print(f"✅ 修復完了: {report['summary']['total_issues_fixed']}件")
        print(f"📈 成功率: {report['summary']['success_rate']:.1%}")
        print(f"🎯 総合結果: {report['summary']['overall_status'].upper()}")

        print(f"\n📋 フェーズ別結果:")
        for phase_name, phase_data in report["phase_results"].items():
            status_icon = (
                "✅"
                if phase_data["status"] == "completed"
                else "❌"
                if phase_data["status"] == "failed"
                else "⏳"
            )
            print(f"  {status_icon} {phase_name}: {phase_data['status']}")

        print(f"\n💡 推奨事項:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")

        print(f"\n🚀 次のステップ:")
        for i, step in enumerate(report["next_steps"], 1):
            print(f"  {i}. {step}")


if __name__ == "__main__":

    async def main():
        orchestrator = SystemRecoveryOrchestrator()

        print("🎭 Elders Guild システム完全回復開始...")
        report = await orchestrator.execute_full_recovery()

        # 結果表示
        orchestrator.print_recovery_summary(report)

        return report

    # 実行
    recovery_result = asyncio.run(main())
