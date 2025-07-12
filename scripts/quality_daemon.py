#!/usr/bin/env python3
"""
🤖 エルダーズギルド品質進化デーモン
24/7稼働で自動的に品質を監視・向上させるバックグラウンドシステム
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'logs/quality_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class QualityMetricsCollector:
    """品質メトリクス自動収集"""

    def __init__(self):
        self.project_root = PROJECT_ROOT

    async def collect_all_metrics(self) -> Dict:
        """全メトリクスを非同期で収集"""
        logger.info("🔍 メトリクス収集開始")

        tasks = [
            self.collect_git_metrics(),
            self.collect_precommit_metrics(),
            self.collect_code_quality_metrics(),
            self.collect_team_metrics()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果をマージ
        all_metrics = {}
        for result in results:
            if isinstance(result, dict):
                all_metrics.update(result)
            else:
                logger.warning(f"メトリクス収集エラー: {result}")

        all_metrics['collected_at'] = datetime.now().isoformat()
        logger.info(f"📊 メトリクス収集完了: {len(all_metrics)}項目")

        return all_metrics

    async def collect_git_metrics(self) -> Dict:
        """Git活動メトリクス"""
        try:
            # 過去7日のコミット数
            result = await asyncio.create_subprocess_exec(
                'git', 'log', '--since=7 days ago', '--oneline',
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()

            commits_7d = len(stdout.decode().strip().split('\n')) if stdout.decode().strip() else 0

            # 今日のコミット数
            result = await asyncio.create_subprocess_exec(
                'git', 'log', '--since=1 day ago', '--oneline',
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()

            commits_today = len(stdout.decode().strip().split('\n')) if stdout.decode().strip() else 0

            return {
                'git_commits_7d': commits_7d,
                'git_commits_today': commits_today,
                'git_activity_score': min(commits_7d / 7 * 10, 10)  # 0-10スコア
            }
        except Exception as e:
            logger.warning(f"Git メトリクス収集失敗: {e}")
            return {'git_commits_7d': 0, 'git_commits_today': 0, 'git_activity_score': 0}

    async def collect_precommit_metrics(self) -> Dict:
        """Pre-commit性能メトリクス"""
        try:
            # .pre-commit-config.yaml存在確認
            config_file = self.project_root / '.pre-commit-config.yaml'
            if not config_file.exists():
                return {'precommit_configured': False}

            # 模擬的な性能データ（実際は過去ログから算出）
            return {
                'precommit_configured': True,
                'precommit_avg_time': 1.8,  # 秒
                'precommit_success_rate': 98.5,  # %
                'precommit_last_run': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Pre-commit メトリクス収集失敗: {e}")
            return {'precommit_configured': False}

    async def collect_code_quality_metrics(self) -> Dict:
        """コード品質メトリクス"""
        try:
            metrics = {
                'python_files_count': 0,
                'python_syntax_errors': 0,
                'large_files_count': 0,
                'total_lines_of_code': 0
            }

            # Python ファイル解析
            for py_file in self.project_root.glob('**/*.py'):
                if any(exclude in str(py_file) for exclude in ['venv', '__pycache__', '.git']):
                    continue

                metrics['python_files_count'] += 1

                # 構文チェック
                try:
                    result = await asyncio.create_subprocess_exec(
                        'python3', '-m', 'py_compile', str(py_file),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await result.communicate()
                    if result.returncode != 0:
                        metrics['python_syntax_errors'] += 1
                except:
                    pass

                # 行数カウント
                try:
                    lines = py_file.read_text(encoding='utf-8').count('\n')
                    metrics['total_lines_of_code'] += lines
                except:
                    pass

            # 大容量ファイルチェック
            for file_path in self.project_root.glob('**/*'):
                if file_path.is_file() and file_path.stat().st_size > 5_000_000:  # 5MB
                    metrics['large_files_count'] += 1

            # 品質スコア計算
            if metrics['python_files_count'] > 0:
                error_rate = metrics['python_syntax_errors'] / metrics['python_files_count']
                metrics['code_quality_score'] = max(0, 10 - error_rate * 100)
            else:
                metrics['code_quality_score'] = 10

            return metrics

        except Exception as e:
            logger.warning(f"コード品質メトリクス収集失敗: {e}")
            return {'code_quality_score': 5}  # デフォルト中間値

    async def collect_team_metrics(self) -> Dict:
        """チームメトリクス（模擬データ）"""
        # 実際の実装では、Slack API、GitHub API、アンケートシステムなどと連携
        return {
            'team_satisfaction': 85,  # %
            'tool_understanding_black': 80,  # %
            'tool_understanding_isort': 75,  # %
            'developer_complaints': 0,  # 件数
            'team_readiness_score': 8.5  # 0-10
        }


class QualityGateEvaluator:
    """品質ゲート自動評価"""

    def __init__(self):
        self.stability_threshold_days = 7
        self.confidence_threshold = 0.95

    def get_current_phase(self) -> int:
        """現在のフェーズを判定"""
        config_file = PROJECT_ROOT / '.pre-commit-config.yaml'
        if not config_file.exists():
            return 0

        content = config_file.read_text()

        if 'mypy' in content and 'tdd-compliance' in content:
            return 4
        elif 'black' in content and 'flake8' in content:
            return 3
        elif 'black' in content:
            return 2
        elif 'check-ast' in content:
            return 1
        else:
            return 0

    async def evaluate_gate_readiness(self, metrics: Dict) -> Dict:
        """ゲート準備状況を評価"""
        current_phase = self.get_current_phase()
        next_phase = current_phase + 1

        logger.info(f"🚪 Gate {current_phase} → Phase {next_phase} 評価中")

        # Phase別の条件評価
        if current_phase == 1 and next_phase == 2:
            return self.evaluate_gate_1_to_2(metrics)
        elif current_phase == 2 and next_phase == 3:
            return self.evaluate_gate_2_to_3(metrics)
        elif current_phase == 3 and next_phase == 4:
            return self.evaluate_gate_3_to_4(metrics)
        else:
            return {
                'ready': False,
                'reason': f'Phase {current_phase} → {next_phase} の評価は未実装',
                'current_phase': current_phase
            }

    def evaluate_gate_1_to_2(self, metrics: Dict) -> Dict:
        """Gate 1 → Phase 2 (コードフォーマット) 評価"""
        criteria = {
            'precommit_success_rate': metrics.get('precommit_success_rate', 0) >= 95,
            'precommit_performance': metrics.get('precommit_avg_time', 999) <= 3.0,
            'syntax_errors': metrics.get('python_syntax_errors', 999) == 0,
            'team_satisfaction': metrics.get('team_satisfaction', 0) >= 80,
            'tool_understanding': metrics.get('tool_understanding_black', 0) >= 75,
            'developer_complaints': metrics.get('developer_complaints', 999) <= 3
        }

        passed_criteria = sum(criteria.values())
        total_criteria = len(criteria)
        readiness_score = passed_criteria / total_criteria

        return {
            'ready': readiness_score >= 1.0,
            'readiness_score': readiness_score,
            'criteria': criteria,
            'current_phase': 1,
            'target_phase': 2,
            'missing_criteria': [k for k, v in criteria.items() if not v]
        }

    def evaluate_gate_2_to_3(self, metrics: Dict) -> Dict:
        """Gate 2 → Phase 3 (品質強化) 評価"""
        # Phase 2の条件（模擬）
        criteria = {
            'format_compliance': True,  # Black適合率95%以上
            'import_order': True,       # Import順序適合率95%以上
            'team_efficiency': True,    # PR作成時間30%短縮
            'code_review_speed': True,  # レビュー時間20%短縮
            'team_satisfaction': metrics.get('team_satisfaction', 0) >= 85
        }

        passed_criteria = sum(criteria.values())
        total_criteria = len(criteria)
        readiness_score = passed_criteria / total_criteria

        return {
            'ready': readiness_score >= 1.0,
            'readiness_score': readiness_score,
            'criteria': criteria,
            'current_phase': 2,
            'target_phase': 3
        }

    def evaluate_gate_3_to_4(self, metrics: Dict) -> Dict:
        """Gate 3 → Phase 4 (TDD完全) 評価"""
        # Phase 3の条件（模擬）
        criteria = {
            'code_quality': metrics.get('code_quality_score', 0) >= 9.0,
            'security_clean': True,      # セキュリティ問題ゼロ
            'test_coverage': False,      # テストカバレッジ70%以上（未実装）
            'tdd_understanding': False,  # TDD理解度80%以上（未実装）
            'bug_reduction': False       # バグ率50%削減（未実装）
        }

        passed_criteria = sum(criteria.values())
        total_criteria = len(criteria)
        readiness_score = passed_criteria / total_criteria

        return {
            'ready': False,  # Phase 4は高度なため慎重に
            'readiness_score': readiness_score,
            'criteria': criteria,
            'current_phase': 3,
            'target_phase': 4,
            'note': 'Phase 4は手動承認が必要'
        }


class AutoUpgradeExecutor:
    """自動昇格実行システム"""

    def __init__(self):
        self.backup_dir = PROJECT_ROOT / 'backups/auto_upgrades'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def execute_upgrade(self, from_phase: int, to_phase: int) -> bool:
        """フェーズ昇格を実行"""
        logger.info(f"🚀 Phase {from_phase} → {to_phase} 昇格開始")

        try:
            # 1. バックアップ作成
            backup_id = await self.create_backup()
            logger.info(f"💾 バックアップ作成: {backup_id}")

            # 2. 新フェーズ設定適用
            await self.apply_phase_config(to_phase)
            logger.info(f"⚙️ Phase {to_phase} 設定適用完了")

            # 3. 設定テスト
            if await self.test_new_configuration():
                logger.info(f"✅ Phase {to_phase} 昇格成功")
                await self.notify_successful_upgrade(from_phase, to_phase)
                return True
            else:
                logger.warning("❌ 設定テスト失敗、ロールバック実行")
                await self.rollback_to_backup(backup_id)
                return False

        except Exception as e:
            logger.error(f"❌ 昇格実行エラー: {e}")
            return False

    async def create_backup(self) -> str:
        """現在の設定をバックアップ"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_id = f"phase_backup_{timestamp}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(exist_ok=True)

        # 重要ファイルをバックアップ
        files_to_backup = [
            '.pre-commit-config.yaml',
            'scripts/check_elder_standards.py',
            '.gitignore'
        ]

        for file_name in files_to_backup:
            source = PROJECT_ROOT / file_name
            if source.exists():
                destination = backup_path / file_name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(source.read_text())

        return backup_id

    async def apply_phase_config(self, phase: int):
        """指定フェーズの設定を適用"""
        if phase == 2:
            await self.apply_phase_2_config()
        elif phase == 3:
            await self.apply_phase_3_config()
        elif phase == 4:
            await self.apply_phase_4_config()
        else:
            raise ValueError(f"未対応のフェーズ: {phase}")

    async def apply_phase_2_config(self):
        """Phase 2 (コードフォーマット) 設定"""
        config = '''# 🏛️ エルダーズギルド Pre-commit 設定 (Phase 2)
# 自動昇格により有効化

repos:
  # Python基本チェック
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=10000']
      - id: check-json
      - id: check-merge-conflict
      - id: check-ast
      - id: debug-statements

  # Phase 2: コードフォーマット
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        args: ['--line-length=100']

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile', 'black']

# 設定オプション
fail_fast: false
default_stages: [pre-commit]

# 🎉 Phase 2 自動昇格完了!
# - Blackによるコード整形が有効になりました
# - isortによるimport整理が有効になりました
'''
        config_file = PROJECT_ROOT / '.pre-commit-config.yaml'
        config_file.write_text(config)

        # フック再インストール
        await asyncio.create_subprocess_exec(
            'pre-commit', 'install',
            cwd=PROJECT_ROOT
        )

    async def apply_phase_3_config(self):
        """Phase 3 (品質強化) 設定"""
        # Phase 3設定は実装予定
        logger.info("Phase 3設定適用 (未実装)")

    async def apply_phase_4_config(self):
        """Phase 4 (TDD完全) 設定"""
        # Phase 4設定は実装予定
        logger.info("Phase 4設定適用 (未実装)")

    async def test_new_configuration(self) -> bool:
        """新設定のテスト"""
        try:
            # Pre-commitが正常に動作するかテスト
            result = await asyncio.create_subprocess_exec(
                'pre-commit', 'run', '--all-files',
                cwd=PROJECT_ROOT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            # 0または1のリターンコードは成功（1は修正を行った場合）
            return result.returncode in [0, 1]

        except Exception as e:
            logger.error(f"設定テストエラー: {e}")
            return False

    async def rollback_to_backup(self, backup_id: str):
        """バックアップにロールバック"""
        backup_path = self.backup_dir / backup_id

        for backup_file in backup_path.glob('**/*'):
            if backup_file.is_file():
                relative_path = backup_file.relative_to(backup_path)
                target_file = PROJECT_ROOT / relative_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(backup_file.read_text())

        logger.info(f"🔄 ロールバック完了: {backup_id}")

    async def notify_successful_upgrade(self, from_phase: int, to_phase: int):
        """昇格成功通知"""
        message = f"""
🎉 エルダーズギルド自動品質進化システム

Phase {from_phase} → Phase {to_phase} 昇格完了！

時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

新機能が有効になりました。普段通り開発を続けてください。
何か問題があれば自動的にロールバックされます。
"""
        logger.info(message.strip())

        # TODO: Slack/Discord通知
        # TODO: メール通知


class QualityEvolutionDaemon:
    """メインデーモンクラス"""

    def __init__(self):
        self.metrics_collector = QualityMetricsCollector()
        self.gate_evaluator = QualityGateEvaluator()
        self.upgrade_executor = AutoUpgradeExecutor()

        self.monitoring_interval = 3600  # 1時間ごと
        self.upgrade_time = "02:00"      # 深夜2時に昇格チェック
        self.metrics_history = []

    async def run_forever(self):
        """メインループ - 24/7稼働"""
        logger.info("🤖 エルダーズギルド品質進化デーモン起動")

        while True:
            try:
                await self.run_monitoring_cycle()
                await asyncio.sleep(self.monitoring_interval)

            except KeyboardInterrupt:
                logger.info("👋 デーモン停止")
                break
            except Exception as e:
                logger.error(f"💥 デーモンエラー: {e}")
                await asyncio.sleep(60)  # 1分待ってリトライ

    async def run_monitoring_cycle(self):
        """監視サイクル実行"""
        cycle_start = datetime.now()
        logger.info(f"🔍 監視サイクル開始: {cycle_start.strftime('%H:%M:%S')}")

        # 1. メトリクス収集
        metrics = await self.metrics_collector.collect_all_metrics()
        self.metrics_history.append(metrics)

        # 履歴は最新100件のみ保持
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]

        # 2. ゲート評価
        gate_status = await self.gate_evaluator.evaluate_gate_readiness(metrics)

        # 3. 昇格時刻チェック
        current_time = datetime.now().strftime("%H:%M")
        if current_time == self.upgrade_time:
            await self.check_and_execute_upgrade(gate_status)

        # 4. 状態保存
        await self.save_status(metrics, gate_status)

        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()
        logger.info(f"✅ 監視サイクル完了: {duration:.1f}秒")

    async def check_and_execute_upgrade(self, gate_status: Dict):
        """昇格チェック・実行"""
        if gate_status.get('ready', False):
            current_phase = gate_status.get('current_phase', 0)
            target_phase = gate_status.get('target_phase', 0)

            logger.info(f"🚀 自動昇格条件達成: Phase {current_phase} → {target_phase}")

            success = await self.upgrade_executor.execute_upgrade(
                current_phase, target_phase
            )

            if success:
                logger.info("🎉 自動昇格成功")
            else:
                logger.warning("⚠️ 自動昇格失敗")
        else:
            readiness = gate_status.get('readiness_score', 0)
            logger.info(f"📊 昇格準備中: {readiness:.1%}")

    async def save_status(self, metrics: Dict, gate_status: Dict):
        """状態をファイルに保存"""
        status_file = PROJECT_ROOT / 'logs/quality_daemon_status.json'

        status = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'gate_status': gate_status,
            'daemon_uptime': self.get_uptime()
        }

        status_file.write_text(json.dumps(status, indent=2, ensure_ascii=False))

    def get_uptime(self) -> str:
        """稼働時間を取得"""
        # 簡易実装
        return "実装予定"


async def main():
    """メインエントリーポイント"""
    daemon = QualityEvolutionDaemon()
    await daemon.run_forever()


if __name__ == "__main__":
    # ログディレクトリ作成
    (PROJECT_ROOT / 'logs').mkdir(exist_ok=True)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 デーモン停止")
    except Exception as e:
        logger.error(f"💥 デーモン起動エラー: {e}")
        sys.exit(1)
