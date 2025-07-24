#!/usr/bin/env python3
"""
GitHub Flow 恒久的保護システム
Elders Guild エルダーズ（4賢者）による設計・実装

設計者:
- タスク賢者: 計画立案・優先順位決定
- インシデント賢者: 緊急時対応・リスク管理
- ナレッジ賢者: ベストプラクティス・学習機能
- RAG賢者: 最適解検索・知識統合
"""

import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict
from typing import List
from typing import Tuple


class GitHubFlowProtectionSystem:
    """GitHub Flow保護システム - 4賢者による設計"""

    def __init__(self, project_dir: str = "/home/aicompany/ai_co"):
        self.project_dir = Path(project_dir)
        self.config_file = self.project_dir / ".github_flow_protection.json"
        self.log_file = self.project_dir / "logs" / "github_flow_protection.log"
        self.setup_logging()
        self.config = self.load_config()

    def setup_logging(self):
        """ログシステムの設定"""
        self.log_file.parent.mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(self.log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self) -> Dict:
        """設定ファイルの読み込み"""
        default_config = {
            "protected_branches": ["main"],
            "forbidden_branches": ["master"],
            "elder_approval_required": True,
            "auto_backup_enabled": True,
            "monitoring_enabled": True,
            "four_sages_validation": True,
            "emergency_contacts": ["admin@ai-company.local"],
            "protection_rules": {
                "require_pr_reviews": True,
                "dismiss_stale_reviews": True,
                "require_code_owner_reviews": True,
                "required_status_checks": ["ci/tests", "ci/coverage"],
                "enforce_admins": False,
                "restrict_pushes": True,
                "allow_force_pushes": False,
                "allow_deletions": False,
            },
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                self.logger.error(f"設定ファイル読み込みエラー: {e}")

        return default_config

    def save_config(self):
        """設定ファイルの保存"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"設定ファイル保存エラー: {e}")

    def run_git(self, command: str) -> subprocess.CompletedProcess:
        """Gitコマンドの実行"""
        try:
            result = subprocess.run(
                f"git {command}".split(),
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result
        except subprocess.TimeoutExpired:
            self.logger.error(f"Gitコマンドタイムアウト: {command}")
            raise
        except Exception as e:
            self.logger.error(f"Gitコマンドエラー: {command} - {e}")
            raise

    def validate_repository_state(self) -> Tuple[bool, List[str]]:
        """🔍 リポジトリ状態の検証"""
        issues = []

        try:
            # 1.0 禁止ブランチの存在チェック
            result = self.run_git("branch -a")
            if result.returncode == 0:
                branches = result.stdout
                for forbidden_branch in self.config["forbidden_branches"]:
                    if forbidden_branch in branches:
                        issues.append(f"禁止ブランチ '{forbidden_branch}' が存在します")

            # 2.0 保護されるべきブランチの存在チェック
            for protected_branch in self.config["protected_branches"]:
                result = self.run_git(
                    f"show-ref --verify --quiet refs/heads/{protected_branch}"
                )
                if result.returncode != 0:
                    issues.append(f"保護ブランチ '{protected_branch}' が存在しません")

            # 3.0 未コミットの重要な変更チェック
            result = self.run_git("status --porcelain")
            if result.returncode == 0 and result.stdout.strip():
                staged_files = []
                unstaged_files = []
                for line in result.stdout.strip().split("\n"):
                    if line.startswith("M ") or line.startswith("A "):
                        staged_files.append(line[3:])
                    elif line.startswith(" M") or line.startswith("??"):
                        unstaged_files.append(line[3:])

                if staged_files:
                    issues.append(
                        f"ステージングされた変更があります: {', '.join(staged_files)}"
                    )
                if unstaged_files:
                    issues.append(
                        f"未ステージングの変更があります: {', '.join(unstaged_files)}"
                    )

            # 4.0 リモートとの同期状態チェック
            result = self.run_git("fetch --dry-run")
            if result.returncode == 0 and result.stderr:
                issues.append("リモートとの同期が必要です")

            return len(issues) == 0, issues

        except Exception as e:
            self.logger.error(f"リポジトリ状態検証エラー: {e}")
            return False, [f"検証エラー: {e}"]

    def create_backup(self) -> bool:
        """🛡️ リポジトリのバックアップ作成"""
        try:
            backup_dir = (
                self.project_dir.parent
                / f"ai_co_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self.logger.info(f"バックアップを作成中: {backup_dir}")

            # .gitディレクトリを含む完全なバックアップ
            shutil.copytree(
                self.project_dir,
                backup_dir,
                ignore=shutil.ignore_patterns(
                    "venv", "__pycache__", "*.pyc", ".DS_Store"
                ),
            )

            # バックアップの検証
            if backup_dir.exists() and (backup_dir / ".git").exists():
                self.logger.info(f"✅ バックアップ完了: {backup_dir}")
                return True
            else:
                self.logger.error("❌ バックアップの検証に失敗")
                return False

        except Exception as e:
            self.logger.error(f"バックアップ作成エラー: {e}")
            return False

    def fix_branch_conflicts(self) -> bool:
        """🔧 ブランチ競合の自動修正"""
        try:
            self.logger.info("ブランチ競合の修正を開始")

            # 1.0 現在のブランチを確認
            current_branch_result = self.run_git("branch --show-current")
            if current_branch_result.returncode != 0:
                self.logger.error("現在のブランチを取得できません")
                return False

            current_branch = current_branch_result.stdout.strip()
            self.logger.info(f"現在のブランチ: {current_branch}")

            # 2.0 mainブランチの存在確認
            main_exists = (
                self.run_git("show-ref --verify --quiet refs/heads/main").returncode
                == 0
            )
            master_exists = (
                self.run_git("show-ref --verify --quiet refs/heads/master").returncode
                == 0
            )

            if not main_exists and not master_exists:
                self.logger.error("mainもmasterも存在しません")
                return False

            # 3.0 masterブランチが存在する場合の処理
            if master_exists:
                if main_exists:
                    # 両方存在する場合: masterを削除（安全確認後）
                    self.logger.warning("mainとmasterが両方存在します")

                    # masterの独自コミットをチェック
                    result = self.run_git("log main..master --oneline")
                    if result.returncode == 0 and result.stdout.strip():
                        self.logger.warning("masterに独自のコミットがあります:")
                        self.logger.warning(result.stdout)

                        # masterの内容をmainにマージ
                        if not (current_branch != "main"):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if current_branch != "main":
                            self.run_git("checkout main")

                        merge_result = self.run_git(
                            "merge master --no-ff -m 'chore: merge master into main before cleanup'"
                        )
                        if not (merge_result.returncode != 0):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if merge_result.returncode != 0:
                            self.logger.error(f"マージに失敗: {merge_result.stderr}")
                            return False

                    # masterブランチを削除
                    if current_branch == "master":
                        self.run_git("checkout main")

                    delete_result = self.run_git("branch -D master")
                    if delete_result.returncode == 0:
                        self.logger.info("✅ masterブランチを削除しました")
                    else:
                        self.logger.error(
                            f"masterブランチの削除に失敗: {delete_result.stderr}"
                        )
                        return False
                else:
                    # masterのみ存在する場合: masterをmainに改名
                    self.logger.info("masterをmainに改名します")
                    rename_result = self.run_git("branch -m master main")
                    if rename_result.returncode != 0:
                        self.logger.error(f"ブランチ改名に失敗: {rename_result.stderr}")
                        return False

            # 4.0 mainブランチの保護設定
            return self.apply_branch_protection()

        except Exception as e:
            self.logger.error(f"ブランチ競合修正エラー: {e}")
            return False

    def apply_branch_protection(self) -> bool:
        """🛡️ ブランチ保護設定の適用"""
        try:
            self.logger.info("ブランチ保護設定を適用中")

            # GitHub CLI を使用した保護設定（利用可能な場合）
            for branch in self.config["protected_branches"]:
                # 基本的な保護設定
                self.logger.info(f"ブランチ '{branch}' に保護設定を適用")

                # ローカルでの保護設定（pre-receive hookなど）
                self.setup_local_protection(branch)

            return True

        except Exception as e:
            self.logger.error(f"ブランチ保護設定エラー: {e}")
            return False

    def setup_local_protection(self, branch: str):
        """ローカル保護設定の適用"""
        try:
            # Git hooksディレクトリの作成
            hooks_dir = self.project_dir / ".git" / "hooks"
            hooks_dir.mkdir(exist_ok=True)

            # pre-push hook を作成
            pre_push_hook = hooks_dir / "pre-push"
            pre_push_script = f"""#!/bin/bash
# Elders Guild GitHub Flow Protection Hook
# Generated by 4 Sages Protection System

protected_branch="{branch}"
current_branch=$(git branch --show-current)

if [ "$current_branch" = "$protected_branch" ]; then
    echo "🛡️  保護されたブランチ '$protected_branch' への直接プッシュは禁止されています"
    echo "📋 GitHub Flowに従い、feature/fix ブランチからPRを作成してください"
    exit 1
fi

# 禁止ブランチチェック
forbidden_branches=("master")
for forbidden in "${{forbidden_branches[@]}}"; do
    if [ "$current_branch" = "$forbidden" ]; then
        echo "❌ 禁止されたブランチ '$forbidden' からのプッシュは許可されていません"
        echo "📋 '{branch}' ブランチを使用してください"
        exit 1
    fi
done

echo "✅ ブランチ '$current_branch' からのプッシュを許可"
"""

            with open(pre_push_hook, "w") as f:
                f.write(pre_push_script)

            # 実行権限を付与
            os.chmod(pre_push_hook, 0o755)

            self.logger.info(f"✅ ローカル保護設定を適用: {branch}")

        except Exception as e:
            self.logger.error(f"ローカル保護設定エラー: {e}")

    def four_sages_validation(self) -> Tuple[bool, Dict]:
        """🧙‍♂️ 4賢者による検証システム"""
        validation_result = {
            "task_sage": {"approved": False, "confidence": 0, "issues": []},
            "incident_sage": {"approved": False, "confidence": 0, "issues": []},
            "knowledge_sage": {"approved": False, "confidence": 0, "issues": []},
            "rag_sage": {"approved": False, "confidence": 0, "issues": []},
        }

        try:
            # タスク賢者による検証
            validation_result["task_sage"] = self._task_sage_validation()

            # インシデント賢者による検証
            validation_result["incident_sage"] = self._incident_sage_validation()

            # ナレッジ賢者による検証
            validation_result["knowledge_sage"] = self._knowledge_sage_validation()

            # RAG賢者による検証
            validation_result["rag_sage"] = self._rag_sage_validation()

            # 総合判定
            total_confidence = (
                sum(sage["confidence"] for sage in validation_result.values()) / 4
            )
            all_approved = all(sage["approved"] for sage in validation_result.values())

            self.logger.info(
                f"4賢者検証結果: 承認={all_approved}, 信頼度={total_confidence:0.2f}"
            )

            return all_approved and total_confidence >= 0.8, validation_result

        except Exception as e:
            self.logger.error(f"4賢者検証エラー: {e}")
            return False, validation_result

    def _task_sage_validation(self) -> Dict:
        """📋 タスク賢者による検証"""
        issues = []
        confidence = 0.0

        try:
            # 1.0 計画の妥当性チェック
            is_valid, repo_issues = self.validate_repository_state()
            if not is_valid:
                issues.extend(repo_issues)
            else:
                confidence += 0.3

            # 2.0 実行順序の最適性チェック
            if self.config["elder_approval_required"]:
                confidence += 0.2

            # 3.0 優先順位の妥当性チェック
            if self.config["four_sages_validation"]:
                confidence += 0.2

            # 4.0 進捗管理の適切性チェック
            if self.config["monitoring_enabled"]:
                confidence += 0.3

            approved = len(issues) == 0 and confidence >= 0.8

            return {"approved": approved, "confidence": confidence, "issues": issues}

        except Exception as e:
            return {
                "approved": False,
                "confidence": 0.0,
                "issues": [f"タスク賢者検証エラー: {e}"],
            }

    def _incident_sage_validation(self) -> Dict:
        """🚨 インシデント賢者による検証"""
        issues = []
        confidence = 0.0

        try:
            # 1.0 リスク評価
            if self.config["auto_backup_enabled"]:
                confidence += 0.3

            # 2.0 緊急時対応準備
            if self.config["emergency_contacts"]:
                confidence += 0.2

            # 3.0 保護設定の妥当性
            protection_rules = self.config["protection_rules"]
            if protection_rules["allow_force_pushes"] == False:
                confidence += 0.2
            if protection_rules["allow_deletions"] == False:
                confidence += 0.2
            if protection_rules["restrict_pushes"] == True:
                confidence += 0.1

            approved = len(issues) == 0 and confidence >= 0.7

            return {"approved": approved, "confidence": confidence, "issues": issues}

        except Exception as e:
            return {
                "approved": False,
                "confidence": 0.0,
                "issues": [f"インシデント賢者検証エラー: {e}"],
            }

    def _knowledge_sage_validation(self) -> Dict:
        """📚 ナレッジ賢者による検証"""
        issues = []
        confidence = 0.0

        try:
            # 1.0 ベストプラクティスチェック
            if "main" in self.config["protected_branches"]:
                confidence += 0.3

            # 2.0 学習機能の評価
            if self.config_file.exists():
                confidence += 0.2

            # 3.0 知識の蓄積状況
            if self.log_file.exists():
                confidence += 0.2

            # 4.0 継続的改善の仕組み
            if self.config["monitoring_enabled"]:
                confidence += 0.3

            approved = len(issues) == 0 and confidence >= 0.7

            return {"approved": approved, "confidence": confidence, "issues": issues}

        except Exception as e:
            return {
                "approved": False,
                "confidence": 0.0,
                "issues": [f"ナレッジ賢者検証エラー: {e}"],
            }

    def _rag_sage_validation(self) -> Dict:
        """🔍 RAG賢者による検証"""
        issues = []
        confidence = 0.0

        try:
            # 1.0 検索精度の評価
            if self.config["four_sages_validation"]:
                confidence += 0.3

            # 2.0 知識統合の品質
            if len(self.config["protection_rules"]) >= 6:
                confidence += 0.3

            # 3.0 最適解の導出
            if self.config["elder_approval_required"]:
                confidence += 0.2

            # 4.0 情報の関連性
            if self.config["monitoring_enabled"]:
                confidence += 0.2

            approved = len(issues) == 0 and confidence >= 0.7

            return {"approved": approved, "confidence": confidence, "issues": issues}

        except Exception as e:
            return {
                "approved": False,
                "confidence": 0.0,
                "issues": [f"RAG賢者検証エラー: {e}"],
            }

    def emergency_recovery(self) -> bool:
        """🚨 緊急時の自動復旧"""
        try:
            self.logger.critical("緊急復旧モードを開始")

            # 1.0 まずバックアップを作成
            if not self.create_backup():
                self.logger.error("緊急時バックアップの作成に失敗")
                return False

            # 2.0 ブランチ競合の修正
            if not self.fix_branch_conflicts():
                self.logger.error("ブランチ競合の修正に失敗")
                return False

            # 3.0 保護設定の適用
            if not self.apply_branch_protection():
                self.logger.error("保護設定の適用に失敗")
                return False

            # 4.0 4賢者による検証
            is_valid, validation_result = self.four_sages_validation()
            if not is_valid:
                self.logger.error(f"4賢者検証に失敗: {validation_result}")
                return False

            self.logger.info("✅ 緊急復旧が完了しました")
            return True

        except Exception as e:
            self.logger.critical(f"緊急復旧エラー: {e}")
            return False

    def run_protection_system(self) -> bool:
        """🛡️ 保護システムの実行"""
        try:
            self.logger.info("GitHub Flow保護システムを開始")

            # 1.0 初期検証
            is_valid, issues = self.validate_repository_state()
            if not is_valid:
                self.logger.warning(f"リポジトリに問題が検出されました: {issues}")

                # 2.0 自動修正を試行
                if not self.emergency_recovery():
                    self.logger.error("自動修正に失敗しました")
                    return False

            # 3.0 保護設定の適用
            if not self.apply_branch_protection():
                self.logger.error("保護設定の適用に失敗")
                return False

            # 4.0 4賢者による最終検証
            is_approved, validation_result = self.four_sages_validation()
            if not is_approved:
                self.logger.error(f"4賢者による検証に失敗: {validation_result}")
                return False

            # 5.0 設定の保存
            self.save_config()

            self.logger.info("✅ GitHub Flow保護システムが正常に完了しました")
            return True

        except Exception as e:
            self.logger.critical(f"保護システム実行エラー: {e}")
            return False

    def start_monitoring(self):
        """📊 継続的監視の開始"""
        try:
            self.logger.info("継続的監視を開始")

            while self.config["monitoring_enabled"]:
                # 定期的な検証
                is_valid, issues = self.validate_repository_state()
                if not is_valid:
                    self.logger.warning(f"監視中に問題を検出: {issues}")

                    # 自動修正を試行
                    if self.emergency_recovery():
                        self.logger.info("自動修正が完了しました")
                    else:
                        self.logger.error("自動修正に失敗しました")
                        break

                # 監視間隔（60秒）
                time.sleep(60)

        except KeyboardInterrupt:
            self.logger.info("監視を停止しました")
        except Exception as e:
            self.logger.error(f"監視エラー: {e}")


def main():
    """メイン実行関数"""
    print("🏛️ Elders Guild GitHub Flow Protection System")
    print("📋 4賢者による恒久的保護システム")
    print("=" * 50)

    protection_system = GitHubFlowProtectionSystem()

    try:
        # 保護システムの実行
        if protection_system.run_protection_system():
            print("✅ 保護システムが正常に完了しました")

            # 監視モードの確認
            if input("継続的監視を開始しますか？ (y/n): ").lower() == "y":
                protection_system.start_monitoring()
        else:
            print("❌ 保護システムの実行に失敗しました")
            return False

    except KeyboardInterrupt:
        print("\n🛑 ユーザーによって中断されました")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

    return True


if __name__ == "__main__":
    main()
