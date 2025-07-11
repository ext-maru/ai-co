"""
nWo Library Update Strategy System
Think it, Rule it, Own it - 開発界新世界秩序のライブラリアップデート戦略

エルダーズギルド評議会承認済み - 2025年7月11日
"""

import asyncio
import json
import logging
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, asdict
try:
    import semver
except ImportError:
    # Fallback for semver functionality
    class semver:
        @staticmethod
        def parse(ver):
            parts = ver.split('.')
            return {
                'major': int(parts[0]) if len(parts) > 0 else 0,
                'minor': int(parts[1]) if len(parts) > 1 else 0,
                'patch': int(parts[2]) if len(parts) > 2 else 0
            }

try:
    import requests
except ImportError:
    # Mock requests for testing
    class requests:
        @staticmethod
        def get(url, timeout=10):
            raise Exception("requests not available")

try:
    from packaging import version
except ImportError:
    # Fallback version comparison
    class version:
        @staticmethod
        def parse(ver):
            return SimpleVersion(ver)

    class SimpleVersion:
        def __init__(self, ver):
            self.version = ver
            self.parts = [int(x) for x in ver.split('.')]

        def __gt__(self, other):
            return self.parts > other.parts

        def __lt__(self, other):
            return self.parts < other.parts

        def __eq__(self, other):
            return self.parts == other.parts

        @property
        def major(self):
            return self.parts[0] if len(self.parts) > 0 else 0

        @property
        def minor(self):
            return self.parts[1] if len(self.parts) > 1 else 0

        @property
        def patch(self):
            return self.parts[2] if len(self.parts) > 2 else 0


class UpdatePriority(Enum):
    """アップデート優先度 - nWo階層準拠"""
    SECURITY_CRITICAL = "security_critical"    # 即座対応
    NWO_STRATEGIC = "nwo_strategic"           # nWo戦略的重要度
    ELDER_COUNCIL = "elder_council"           # エルダー評議会承認
    COMPATIBILITY = "compatibility"           # 互換性維持
    ENHANCEMENT = "enhancement"               # 機能強化
    ROUTINE = "routine"                       # 定期メンテナンス


class UpdateStatus(Enum):
    """アップデート状況"""
    PENDING = "pending"
    TESTING = "testing"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    ROLLBACK = "rollback"
    FAILED = "failed"


@dataclass
class LibraryInfo:
    """ライブラリ情報"""
    name: str
    current_version: str
    latest_version: str
    update_available: bool
    security_update: bool
    priority: UpdatePriority
    dependencies: List[str]
    breaking_changes: bool
    changelog_url: str
    update_notes: str


@dataclass
class UpdatePlan:
    """アップデート計画"""
    library: LibraryInfo
    scheduled_date: datetime
    test_requirements: List[str]
    rollback_plan: str
    approval_required: bool
    nwo_impact_score: int  # 1-100, nWoへの影響度


class nWoLibraryUpdateStrategy:
    """nWo Library Update Strategy System"""

    def __init__(self, config_path: str = "config/nwo_update_config.json"):
        self.config_path = Path(config_path)
        self.logger = self._setup_logger()
        self.config = self._load_config()
        self.requirements_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "pyproject.toml",
            "setup.py"
        ]

    def _setup_logger(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger("nwo_library_update")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - nWo Library Update - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _load_config(self) -> Dict[str, Any]:
        """設定ロード"""
        default_config = {
            "update_schedule": {
                "security_critical": "immediate",
                "nwo_strategic": "within_24h",
                "elder_council": "within_week",
                "compatibility": "monthly",
                "enhancement": "quarterly",
                "routine": "biannual"
            },
            "test_requirements": {
                "security_critical": ["security_scan", "smoke_test"],
                "nwo_strategic": ["unit_test", "integration_test", "performance_test"],
                "elder_council": ["full_test_suite", "elder_review"],
                "compatibility": ["compatibility_test", "regression_test"],
                "enhancement": ["feature_test", "performance_test"],
                "routine": ["basic_test"]
            },
            "auto_approve_thresholds": {
                "patch_version": True,
                "minor_version": False,
                "major_version": False,
                "security_patches": True
            },
            "nwo_strategic_libraries": [
                "fastapi", "sqlalchemy", "asyncio", "pydantic",
                "pytest", "uvicorn", "redis", "celery",
                "transformers", "torch", "numpy", "pandas"
            ],
            "elder_council_libraries": [
                "django", "flask", "postgresql", "elasticsearch",
                "kubernetes", "docker", "terraform"
            ]
        }

        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # デフォルト設定とマージ
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config

        return default_config

    async def analyze_library_updates(self) -> List[LibraryInfo]:
        """ライブラリアップデート分析"""
        self.logger.info("🔍 ライブラリアップデート分析開始")

        libraries = []

        # requirements.txtから現在のライブラリを取得
        current_libs = self._get_current_libraries()

        # 各ライブラリの最新バージョンを確認
        for lib_name, current_version in current_libs.items():
            try:
                lib_info = await self._analyze_single_library(lib_name, current_version)
                libraries.append(lib_info)
            except Exception as e:
                self.logger.error(f"❌ {lib_name} 分析失敗: {e}")

        self.logger.info(f"✅ {len(libraries)} ライブラリ分析完了")
        return libraries

    def _get_current_libraries(self) -> Dict[str, str]:
        """現在のライブラリ一覧取得"""
        libraries = {}

        # pip freezeで現在のライブラリを取得
        try:
            result = subprocess.run(
                ["pip", "freeze"],
                capture_output=True,
                text=True,
                check=True
            )

            for line in result.stdout.strip().split('\n'):
                if '==' in line:
                    name, version = line.split('==')
                    libraries[name.lower()] = version
        except subprocess.CalledProcessError as e:
            self.logger.error(f"pip freeze 失敗: {e}")

        return libraries

    async def _analyze_single_library(self, lib_name: str, current_version: str) -> LibraryInfo:
        """単一ライブラリ分析"""
        # PyPI APIから最新バージョン取得
        latest_version = await self._get_latest_version(lib_name)

        # アップデート可能かチェック
        update_available = self._is_update_available(current_version, latest_version)

        # セキュリティアップデートかチェック
        security_update = await self._is_security_update(lib_name, current_version, latest_version)

        # 優先度決定
        priority = self._determine_priority(lib_name, security_update, current_version, latest_version)

        # 依存関係取得
        dependencies = await self._get_dependencies(lib_name)

        # 破壊的変更チェック
        breaking_changes = self._has_breaking_changes(current_version, latest_version)

        # 更新情報取得
        changelog_url = f"https://pypi.org/project/{lib_name}/"
        update_notes = await self._get_update_notes(lib_name, latest_version)

        return LibraryInfo(
            name=lib_name,
            current_version=current_version,
            latest_version=latest_version,
            update_available=update_available,
            security_update=security_update,
            priority=priority,
            dependencies=dependencies,
            breaking_changes=breaking_changes,
            changelog_url=changelog_url,
            update_notes=update_notes
        )

    async def _get_latest_version(self, lib_name: str) -> str:
        """最新バージョン取得"""
        try:
            response = requests.get(f"https://pypi.org/pypi/{lib_name}/json", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data['info']['version']
        except Exception as e:
            self.logger.warning(f"⚠️ {lib_name} 最新バージョン取得失敗: {e}")
            return "unknown"

    def _is_update_available(self, current: str, latest: str) -> bool:
        """アップデート可能かチェック"""
        try:
            return version.parse(latest) > version.parse(current)
        except Exception:
            return False

    async def _is_security_update(self, lib_name: str, current: str, latest: str) -> bool:
        """セキュリティアップデートかチェック"""
        # 簡易実装 - 実際はセキュリティデータベースと連携
        security_keywords = ["security", "vulnerability", "cve", "exploit"]

        try:
            update_notes = await self._get_update_notes(lib_name, latest)
            return any(keyword in update_notes.lower() for keyword in security_keywords)
        except Exception:
            return False

    def _determine_priority(self, lib_name: str, security_update: bool, current: str, latest: str) -> UpdatePriority:
        """優先度決定"""
        if security_update:
            return UpdatePriority.SECURITY_CRITICAL

        if lib_name in self.config["nwo_strategic_libraries"]:
            return UpdatePriority.NWO_STRATEGIC

        if lib_name in self.config["elder_council_libraries"]:
            return UpdatePriority.ELDER_COUNCIL

        # バージョン差分で判定
        try:
            current_ver = version.parse(current)
            latest_ver = version.parse(latest)

            if latest_ver.major > current_ver.major:
                return UpdatePriority.ELDER_COUNCIL
            elif latest_ver.minor > current_ver.minor:
                return UpdatePriority.COMPATIBILITY
            else:
                return UpdatePriority.ROUTINE
        except Exception:
            return UpdatePriority.ROUTINE

    async def _get_dependencies(self, lib_name: str) -> List[str]:
        """依存関係取得"""
        try:
            response = requests.get(f"https://pypi.org/pypi/{lib_name}/json", timeout=10)
            response.raise_for_status()
            data = response.json()

            requires_dist = data['info'].get('requires_dist', [])
            if requires_dist:
                return [dep.split()[0] for dep in requires_dist if dep]
            return []
        except Exception:
            return []

    def _has_breaking_changes(self, current: str, latest: str) -> bool:
        """破壊的変更チェック"""
        try:
            current_ver = version.parse(current)
            latest_ver = version.parse(latest)
            return latest_ver.major > current_ver.major
        except Exception:
            return False

    async def _get_update_notes(self, lib_name: str, version: str) -> str:
        """アップデート情報取得"""
        try:
            response = requests.get(f"https://pypi.org/pypi/{lib_name}/json", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data['info'].get('description', '')[:500]  # 最初の500文字
        except Exception:
            return "更新情報の取得に失敗しました"

    async def create_update_plan(self, libraries: List[LibraryInfo]) -> List[UpdatePlan]:
        """アップデート計画作成"""
        self.logger.info("📋 アップデート計画作成開始")

        plans = []

        for lib in libraries:
            if not lib.update_available:
                continue

            # スケジュール決定
            scheduled_date = self._calculate_schedule_date(lib.priority)

            # テスト要件決定
            test_requirements = self.config["test_requirements"][lib.priority.value]

            # ロールバック計画
            rollback_plan = self._create_rollback_plan(lib)

            # 承認要否
            approval_required = self._requires_approval(lib)

            # nWo影響度スコア
            nwo_impact_score = self._calculate_nwo_impact(lib)

            plan = UpdatePlan(
                library=lib,
                scheduled_date=scheduled_date,
                test_requirements=test_requirements,
                rollback_plan=rollback_plan,
                approval_required=approval_required,
                nwo_impact_score=nwo_impact_score
            )

            plans.append(plan)

        # 優先度順でソート
        plans.sort(key=lambda x: (x.library.priority.value, x.nwo_impact_score), reverse=True)

        self.logger.info(f"✅ {len(plans)} 件のアップデート計画作成完了")
        return plans

    def _calculate_schedule_date(self, priority: UpdatePriority) -> datetime:
        """スケジュール日付計算"""
        now = datetime.now()

        schedule_map = {
            UpdatePriority.SECURITY_CRITICAL: now,  # 即座
            UpdatePriority.NWO_STRATEGIC: now + timedelta(hours=24),  # 24時間以内
            UpdatePriority.ELDER_COUNCIL: now + timedelta(days=7),  # 1週間以内
            UpdatePriority.COMPATIBILITY: now + timedelta(days=30),  # 1ヶ月以内
            UpdatePriority.ENHANCEMENT: now + timedelta(days=90),  # 3ヶ月以内
            UpdatePriority.ROUTINE: now + timedelta(days=180)  # 6ヶ月以内
        }

        return schedule_map.get(priority, now + timedelta(days=30))

    def _create_rollback_plan(self, lib: LibraryInfo) -> str:
        """ロールバック計画作成"""
        return f"""
        Rollback Plan for {lib.name}:
        1. pip install {lib.name}=={lib.current_version}
        2. Run test suite: pytest tests/
        3. Check system health: python -m health_check
        4. Verify nWo services: ./scripts/nwo_service_check.sh
        5. Document incident: knowledge_base/incidents/
        """

    def _requires_approval(self, lib: LibraryInfo) -> bool:
        """承認要否判定"""
        if lib.priority in [UpdatePriority.SECURITY_CRITICAL]:
            return False  # セキュリティは自動承認

        if lib.breaking_changes:
            return True  # 破壊的変更は承認必要

        if lib.priority in [UpdatePriority.NWO_STRATEGIC, UpdatePriority.ELDER_COUNCIL]:
            return True  # 戦略的重要度は承認必要

        return False

    def _calculate_nwo_impact(self, lib: LibraryInfo) -> int:
        """nWo影響度スコア計算"""
        score = 0

        # 基本スコア
        priority_scores = {
            UpdatePriority.SECURITY_CRITICAL: 100,
            UpdatePriority.NWO_STRATEGIC: 80,
            UpdatePriority.ELDER_COUNCIL: 60,
            UpdatePriority.COMPATIBILITY: 40,
            UpdatePriority.ENHANCEMENT: 20,
            UpdatePriority.ROUTINE: 10
        }

        score += priority_scores.get(lib.priority, 0)

        # 破壊的変更があれば+20
        if lib.breaking_changes:
            score += 20

        # 依存関係が多ければ+10
        if len(lib.dependencies) > 10:
            score += 10

        # nWo戦略ライブラリなら+30
        if lib.name in self.config["nwo_strategic_libraries"]:
            score += 30

        return min(score, 100)  # 最大100

    async def execute_update_plan(self, plans: List[UpdatePlan]) -> Dict[str, Any]:
        """アップデート計画実行"""
        self.logger.info("🚀 アップデート計画実行開始")

        results = {
            "executed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }

        for plan in plans:
            try:
                result = await self._execute_single_update(plan)
                results["details"].append(result)
                results["executed"] += 1

                if result["status"] == "success":
                    results["succeeded"] += 1
                elif result["status"] == "failed":
                    results["failed"] += 1
                else:
                    results["skipped"] += 1

            except Exception as e:
                self.logger.error(f"❌ {plan.library.name} アップデート失敗: {e}")
                results["failed"] += 1
                results["details"].append({
                    "library": plan.library.name,
                    "status": "failed",
                    "error": str(e)
                })

        self.logger.info(f"✅ アップデート実行完了: {results['succeeded']} 成功, {results['failed']} 失敗")
        return results

    async def _execute_single_update(self, plan: UpdatePlan) -> Dict[str, Any]:
        """単一アップデート実行"""
        lib = plan.library

        # 承認チェック
        if plan.approval_required:
            self.logger.info(f"⏳ {lib.name} 承認待ち (エルダー評議会承認必要)")
            return {
                "library": lib.name,
                "status": "pending_approval",
                "message": "Elder Council approval required"
            }

        # 即座実行でない場合はスケジュール確認
        if plan.scheduled_date > datetime.now():
            self.logger.info(f"⏰ {lib.name} スケジュール待ち ({plan.scheduled_date})")
            return {
                "library": lib.name,
                "status": "scheduled",
                "scheduled_date": plan.scheduled_date.isoformat()
            }

        try:
            # アップデート実行
            self.logger.info(f"🔄 {lib.name} アップデート実行: {lib.current_version} → {lib.latest_version}")

            # pip install
            result = subprocess.run(
                ["pip", "install", f"{lib.name}=={lib.latest_version}"],
                capture_output=True,
                text=True,
                check=True
            )

            # テスト実行
            test_results = await self._run_tests(plan.test_requirements)

            if not test_results["passed"]:
                # テスト失敗時はロールバック
                self.logger.warning(f"⚠️ {lib.name} テスト失敗, ロールバック実行")
                await self._rollback_update(lib)
                return {
                    "library": lib.name,
                    "status": "failed",
                    "reason": "test_failed",
                    "test_results": test_results
                }

            self.logger.info(f"✅ {lib.name} アップデート成功")
            return {
                "library": lib.name,
                "status": "success",
                "old_version": lib.current_version,
                "new_version": lib.latest_version,
                "test_results": test_results
            }

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ {lib.name} アップデート失敗: {e}")
            return {
                "library": lib.name,
                "status": "failed",
                "reason": "install_failed",
                "error": str(e)
            }

    async def _run_tests(self, test_requirements: List[str]) -> Dict[str, Any]:
        """テスト実行"""
        test_results = {
            "passed": True,
            "details": {}
        }

        for test_type in test_requirements:
            try:
                if test_type == "unit_test":
                    result = subprocess.run(["pytest", "tests/unit/"], capture_output=True, text=True)
                elif test_type == "integration_test":
                    result = subprocess.run(["pytest", "tests/integration/"], capture_output=True, text=True)
                elif test_type == "security_scan":
                    result = subprocess.run(["safety", "check"], capture_output=True, text=True)
                elif test_type == "smoke_test":
                    result = subprocess.run(["python", "-m", "smoke_test"], capture_output=True, text=True)
                else:
                    continue

                test_results["details"][test_type] = {
                    "passed": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr
                }

                if result.returncode != 0:
                    test_results["passed"] = False

            except Exception as e:
                test_results["passed"] = False
                test_results["details"][test_type] = {
                    "passed": False,
                    "error": str(e)
                }

        return test_results

    async def _rollback_update(self, lib: LibraryInfo):
        """アップデートロールバック"""
        try:
            subprocess.run(
                ["pip", "install", f"{lib.name}=={lib.current_version}"],
                capture_output=True,
                text=True,
                check=True
            )
            self.logger.info(f"🔄 {lib.name} ロールバック完了")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ {lib.name} ロールバック失敗: {e}")

    async def generate_update_report(self, libraries: List[LibraryInfo], plans: List[UpdatePlan]) -> str:
        """アップデートレポート生成"""
        report = f"""
# nWo Library Update Strategy Report
## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 📊 Overview
- Total Libraries Analyzed: {len(libraries)}
- Updates Available: {len([lib for lib in libraries if lib.update_available])}
- Security Critical: {len([lib for lib in libraries if lib.priority == UpdatePriority.SECURITY_CRITICAL])}
- nWo Strategic: {len([lib for lib in libraries if lib.priority == UpdatePriority.NWO_STRATEGIC])}
- Elder Council: {len([lib for lib in libraries if lib.priority == UpdatePriority.ELDER_COUNCIL])}

### 🚨 Security Critical Updates
"""

        security_updates = [lib for lib in libraries if lib.priority == UpdatePriority.SECURITY_CRITICAL]
        for lib in security_updates:
            report += f"- **{lib.name}**: {lib.current_version} → {lib.latest_version}\n"

        report += f"""
### 🎯 nWo Strategic Updates
"""

        nwo_updates = [lib for lib in libraries if lib.priority == UpdatePriority.NWO_STRATEGIC]
        for lib in nwo_updates:
            report += f"- **{lib.name}**: {lib.current_version} → {lib.latest_version}\n"

        report += f"""
### 🏛️ Elder Council Updates
"""

        elder_updates = [lib for lib in libraries if lib.priority == UpdatePriority.ELDER_COUNCIL]
        for lib in elder_updates:
            report += f"- **{lib.name}**: {lib.current_version} → {lib.latest_version}\n"

        report += f"""
### 📋 Update Plans
"""

        for plan in plans[:10]:  # 上位10件
            report += f"""
#### {plan.library.name}
- **Priority**: {plan.library.priority.value}
- **nWo Impact Score**: {plan.nwo_impact_score}/100
- **Scheduled**: {plan.scheduled_date.strftime('%Y-%m-%d %H:%M')}
- **Tests Required**: {', '.join(plan.test_requirements)}
- **Approval Required**: {'Yes' if plan.approval_required else 'No'}
- **Breaking Changes**: {'Yes' if plan.library.breaking_changes else 'No'}
"""

        return report

    async def run_nwo_update_cycle(self) -> Dict[str, Any]:
        """nWoアップデートサイクル実行"""
        self.logger.info("🌟 nWo Library Update Cycle Starting")

        try:
            # 1. ライブラリ分析
            libraries = await self.analyze_library_updates()

            # 2. アップデート計画作成
            plans = await self.create_update_plan(libraries)

            # 3. 即座実行対象の実行
            immediate_plans = [p for p in plans if p.scheduled_date <= datetime.now()]
            execution_results = await self.execute_update_plan(immediate_plans)

            # 4. レポート生成
            report = await self.generate_update_report(libraries, plans)

            # 5. 結果保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = f"knowledge_base/nwo_reports/library_update_{timestamp}.md"
            Path(report_path).parent.mkdir(parents=True, exist_ok=True)

            with open(report_path, 'w') as f:
                f.write(report)

            self.logger.info(f"📄 レポート保存: {report_path}")

            return {
                "libraries_analyzed": len(libraries),
                "plans_created": len(plans),
                "immediate_executions": len(immediate_plans),
                "execution_results": execution_results,
                "report_path": report_path
            }

        except Exception as e:
            self.logger.error(f"❌ nWoアップデートサイクル失敗: {e}")
            raise


# CLI実行
async def main():
    """メイン実行"""
    strategy = nWoLibraryUpdateStrategy()

    # アップデートサイクル実行
    results = await strategy.run_nwo_update_cycle()

    print("🌟 nWo Library Update Strategy Results:")
    print(f"📊 Libraries Analyzed: {results['libraries_analyzed']}")
    print(f"📋 Plans Created: {results['plans_created']}")
    print(f"⚡ Immediate Executions: {results['immediate_executions']}")
    print(f"📄 Report: {results['report_path']}")

    execution_results = results['execution_results']
    print(f"✅ Succeeded: {execution_results['succeeded']}")
    print(f"❌ Failed: {execution_results['failed']}")
    print(f"⏭️ Skipped: {execution_results['skipped']}")


if __name__ == "__main__":
    asyncio.run(main())
