#!/usr/bin/env python3
"""
🔧 環境変数自動補完騎士
必要な環境変数を検出して自動設定
"""

import os
import sys
from pathlib import Path
from typing import List

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class EnvAutoSetup:
    """環境変数自動セットアップ"""

    def __init__(self):
        self.env_file = PROJECT_ROOT / ".env"
        self.added_vars = []

        # 必須環境変数とデフォルト値
        self.required_vars = {
            # 基本設定
            "WORKER_DEV_MODE": "true",
            "INCIDENT_KNIGHTS_ENABLED": "true",
            "AUTO_FIX_ENABLED": "true",
            "SLACK_NOTIFICATIONS": "false",
            # RabbitMQ設定
            "RABBITMQ_HOST": "localhost",
            "RABBITMQ_PORT": "5672",
            "RABBITMQ_USER": "guest",
            "RABBITMQ_PASS": "guest",
            "RABBITMQ_VHOST": "/",
            # Redis設定
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_DB": "0",
            # ログ設定
            "LOG_LEVEL": "INFO",
            "LOG_FORMAT": "json",
            "LOG_DIR": "logs",
            # エルダーズギルド設定
            "ELDERS_GUILD_MODE": "true",
            "FOUR_SAGES_ENABLED": "true",
            "KNIGHTS_AUTO_DEPLOY": "true",
            # API設定（プレースホルダー）
            "ANTHROPIC_API_KEY": "your_anthropic_api_key_here",
            "OPENAI_API_KEY": "your_openai_api_key_here",
            "SLACK_WEBHOOK_URL": "",
            "GITHUB_TOKEN": "",
            # データベース設定
            "DATABASE_URL": "sqlite:///elder_dashboard.db",
            "TASK_DB_PATH": "task_history.db",
            # セキュリティ設定
            "SECRET_KEY": "dev_secret_key_change_in_production",
            "JWT_SECRET": "dev_jwt_secret_change_in_production",
            "ENCRYPTION_KEY": "dev_encryption_key_change_in_production",
            # パフォーマンス設定
            "MAX_WORKERS": "10",
            "WORKER_TIMEOUT": "300",
            "BATCH_SIZE": "100",
            "CACHE_TTL": "3600",
            # 開発設定
            "DEBUG": "false",
            "TESTING": "false",
            "PROFILE": "false",
            "COVERAGE": "false",
        }

    def setup_env(self) -> bool:
        """環境変数をセットアップ"""
        print("🔧 環境変数自動補完開始")
        print("=" * 50)

        # .envファイルが存在しない場合は作成
        if not self.env_file.exists():
            print("📝 .envファイルを新規作成")
            self._create_env_file()
        else:
            print("📋 既存の.envファイルをチェック")
            self._update_env_file()

        # 結果表示
        if self.added_vars:
            print(f"\n✅ {len(self.added_vars)}個の環境変数を追加:")
            for var in self.added_vars[:10]:  # 最初の10個だけ表示
                print(f"   - {var}")
            if len(self.added_vars) > 10:
                print(f"   ... 他{len(self.added_vars) - 10}個")
        else:
            print("\n✅ すべての環境変数が設定済み")

        return True

    def _create_env_file(self):
        """新規.envファイルを作成"""
        content = """# エルダーズギルド環境変数
# 自動生成日時: {}
# ⚠️ 本番環境では適切な値に変更してください

""".format(
            os.popen("date").read().strip()
        )

        # カテゴリごとに環境変数を追加
        categories = {
            "基本設定": [
                "WORKER_DEV_MODE",
                "INCIDENT_KNIGHTS_ENABLED",
                "AUTO_FIX_ENABLED",
                "SLACK_NOTIFICATIONS",
            ],
            "RabbitMQ設定": [
                "RABBITMQ_HOST",
                "RABBITMQ_PORT",
                "RABBITMQ_USER",
                "RABBITMQ_PASS",
                "RABBITMQ_VHOST",
            ],
            "Redis設定": ["REDIS_HOST", "REDIS_PORT", "REDIS_DB"],
            "ログ設定": ["LOG_LEVEL", "LOG_FORMAT", "LOG_DIR"],
            "エルダーズギルド設定": [
                "ELDERS_GUILD_MODE",
                "FOUR_SAGES_ENABLED",
                "KNIGHTS_AUTO_DEPLOY",
            ],
            "API設定": [
                "ANTHROPIC_API_KEY",
                "OPENAI_API_KEY",
                "SLACK_WEBHOOK_URL",
                "GITHUB_TOKEN",
            ],
            "データベース設定": ["DATABASE_URL", "TASK_DB_PATH"],
            "セキュリティ設定": ["SECRET_KEY", "JWT_SECRET", "ENCRYPTION_KEY"],
            "パフォーマンス設定": [
                "MAX_WORKERS",
                "WORKER_TIMEOUT",
                "BATCH_SIZE",
                "CACHE_TTL",
            ],
            "開発設定": ["DEBUG", "TESTING", "PROFILE", "COVERAGE"],
        }

        for category, vars_list in categories.items():
            content += f"\n# {category}\n"
            for var in vars_list:
                if var in self.required_vars:
                    content += f"{var}={self.required_vars[var]}\n"
                    self.added_vars.append(var)

        # ファイルに書き込み
        with open(self.env_file, "w") as f:
            f.write(content)

    def _update_env_file(self):
        """既存の.envファイルを更新"""
        # 既存の内容を読み込み
        with open(self.env_file, "r") as f:
            content = f.read()

        # 既存の変数を抽出
        existing_vars = set()
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    var_name = line.split("=")[0].strip()
                    existing_vars.add(var_name)

        # 不足している変数を検出
        missing_vars = []
        for var, default_value in self.required_vars.items():
            if var not in existing_vars:
                missing_vars.append((var, default_value))

        # 不足している変数を追加
        if missing_vars:
            # 追加内容を作成
            additions = "\n\n# 自動追加された環境変数 ({})\n".format(
                os.popen("date").read().strip()
            )

            for var, value in missing_vars:
                additions += f"{var}={value}\n"
                self.added_vars.append(var)

            # ファイルに追記
            with open(self.env_file, "a") as f:
                f.write(additions)

    def validate_env(self) -> List[str]:
        """環境変数の妥当性をチェック"""
        issues = []

        # APIキーのチェック
        api_keys = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
        for key in api_keys:
            value = os.getenv(key, "")
            if value.startswith("your_") or value == "":
                issues.append(f"⚠️ {key} が設定されていません")

        # 本番環境でのデバッグモードチェック
        if os.getenv("DEBUG", "false").lower() == "true":
            if not os.getenv("WORKER_DEV_MODE", "true").lower() == "true":
                issues.append("⚠️ 本番環境でDEBUGが有効になっています")

        return issues


def main():
    """メイン実行関数"""
    setup = EnvAutoSetup()

    # 環境変数セットアップ
    success = setup.setup_env()

    # 妥当性チェック
    issues = setup.validate_env()
    if issues:
        print("\n⚠️ 環境変数の警告:")
        for issue in issues:
            print(f"   {issue}")

    print("\n" + "=" * 50)

    if success and not issues:
        print("✅ 環境変数セットアップ完了")
        sys.exit(0)
    elif success and issues:
        print("⚠️ 環境変数セットアップ完了（警告あり）")
        sys.exit(0)
    else:
        print("❌ 環境変数セットアップ失敗")
        sys.exit(1)


if __name__ == "__main__":
    main()
