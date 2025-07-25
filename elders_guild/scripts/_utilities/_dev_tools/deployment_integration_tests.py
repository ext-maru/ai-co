"""
🧪 デプロイメント統合システム テスト
"""

import os
import shutil
import sys

import unittest
from pathlib import Path

# パスを追加
sys.path.append(str(Path(__file__).parent.parent))

from libs.deployment_integration import (
    DeploymentIntegration,
    get_deployment_integration,
)
from libs.project_deployment_config import ProjectDeploymentManager

class TestDeploymentIntegration(unittest.TestCase):
    """デプロイメント統合のテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.integration = DeploymentIntegration()
        self.test_project = "test-integration-project"

        # テスト用プロジェクト設定を作成
        self.config_manager = ProjectDeploymentManager()
        self.config_manager.create_project_config(self.test_project, "web-app")

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # テストプロジェクトの設定を削除
        project_dir = Path("deployment-configs/projects") / self.test_project
        if project_dir.exists():
            shutil.rmtree(project_dir)

    def test_set_project_context(self):
        """プロジェクトコンテキスト設定のテスト"""
        self.integration.set_project_context(self.test_project, "production")

        self.assertEqual(self.integration.current_project, self.test_project)
        self.assertEqual(self.integration.current_environment, "production")

    def test_get_deployment_method(self):
        """デプロイメント方法取得のテスト"""
        # コンテキストなしの場合
        method = self.integration.get_deployment_method()
        self.assertEqual(method, "github_actions")  # デフォルト

        # コンテキストありの場合
        self.integration.set_project_context(self.test_project)
        method = self.integration.get_deployment_method()
        self.assertIn(method, ["github_actions", "ssh", "hybrid"])

    def test_should_use_github_actions(self):
        """GitHub Actions使用判定のテスト"""
        self.integration.set_project_context(self.test_project)

        # GitHub Actionsに設定
        self.config_manager.set_deployment_method(
            self.test_project, "development", "github_actions"
        )
        self.assertTrue(self.integration.should_use_github_actions())
        self.assertFalse(self.integration.should_use_ssh())

    def test_should_use_ssh(self):
        """SSH使用判定のテスト"""
        self.integration.set_project_context(self.test_project)

        # SSHに設定
        self.config_manager.set_deployment_method(
            self.test_project, "development", "ssh"
        )
        self.assertTrue(self.integration.should_use_ssh())
        self.assertFalse(self.integration.should_use_github_actions())

    def test_hybrid_deployment(self):
        """ハイブリッドデプロイのテスト"""
        self.integration.set_project_context(self.test_project)

        # ハイブリッドに設定
        self.config_manager.set_deployment_method(
            self.test_project, "development", "hybrid"
        )
        self.assertTrue(self.integration.should_use_github_actions())
        self.assertTrue(self.integration.should_use_ssh())

    def test_get_deployment_config(self):
        """デプロイメント設定取得のテスト"""
        self.integration.set_project_context(self.test_project)

        config = self.integration.get_deployment_config()
        self.assertIsNotNone(config)
        self.assertEqual(config.project_name, self.test_project)

    def test_execute_deployment(self):
        """デプロイメント実行のテスト"""
        # コンテキストなしの場合
        result = self.integration.execute_deployment()
        self.assertFalse(result["success"])
        self.assertIn("error", result)

        # コンテキストありの場合
        self.integration.set_project_context(self.test_project)
        result = self.integration.execute_deployment()
        self.assertTrue(result["success"])
        self.assertEqual(result["project"], self.test_project)
        self.assertEqual(result["environment"], "development")
        self.assertIn("method", result)
        self.assertTrue(result["four_sages_approval"])

    def test_auto_detect_project(self):
        """プロジェクト自動検出のテスト"""
        # 一時ディレクトリでテスト

            # package.jsonを作成
            test_dir = Path(tmpdir) / "test-auto-detect"
            test_dir.mkdir()
            (test_dir / "package.json").write_text('{"name": "test"}')

            # 現在のディレクトリを保存
            original_cwd = os.getcwd()
            try:
                # テストディレクトリに移動
                os.chdir(test_dir)

                # 自動検出（新規プロジェクトなのでNone）
                detected = self.integration.auto_detect_project()
                # 既存のプロジェクトのみ検出するため、Noneが期待値
                self.assertIsNone(detected)
            finally:
                # 元のディレクトリに戻る
                os.chdir(original_cwd)

    def test_integrate_with_command(self):
        """コマンド統合のテスト"""
        # デプロイコマンド
        result = self.integration.integrate_with_command(
            "deploy", {"project": self.test_project, "environment": "staging"}
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["environment"], "staging")

        # ビルドコマンド
        result = self.integration.integrate_with_command(
            "build", {"project": self.test_project}
        )
        self.assertIn("build_command", result)

        # テストコマンド
        result = self.integration.integrate_with_command(
            "test", {"project": self.test_project}
        )
        self.assertIn("test_command", result)

    def test_singleton_pattern(self):
        """シングルトンパターンのテスト"""
        integration1 = get_deployment_integration()
        integration2 = get_deployment_integration()

        # 同じインスタンスであることを確認
        self.assertIs(integration1, integration2)

    def test_deployment_method_override(self):
        """デプロイメント方法のオーバーライドテスト"""
        self.integration.set_project_context(self.test_project)

        # 通常のデプロイ
        result = self.integration.integrate_with_command("deploy", {})
        original_method = result["method"]

        # SSH強制
        result = self.integration.integrate_with_command("deploy", {"use_ssh": True})
        self.assertEqual(result["method"], "ssh")

        # GitHub Actions強制
        result = self.integration.integrate_with_command(
            "deploy", {"use_github_actions": True}
        )
        self.assertEqual(result["method"], "github_actions")

class TestDeploymentIntegrationEdgeCases(unittest.TestCase):
    """エッジケースのテスト"""

    def setUp(self):
        self.integration = DeploymentIntegration()

    def test_no_config_directory(self):
        """設定ディレクトリがない場合のテスト"""
        # 一時的な設定ディレクトリ名を使用
        import uuid

        try:
            # 新しいインスタンスを作成（存在しないディレクトリを指定）
            from libs.project_deployment_config import ProjectDeploymentManager

            integration = DeploymentIntegration()
            integration.config_manager = manager

            # デフォルト値が返ることを確認
            method = integration.get_deployment_method()
            self.assertEqual(method, "github_actions")

            # プロジェクト一覧は空であることを確認
            projects = manager.list_projects()
            self.assertEqual(projects, [])
        finally:
            # テスト用ディレクトリをクリーンアップ

    def test_invalid_project_name(self):
        """無効なプロジェクト名のテスト"""
        self.integration.set_project_context("non-existent-project")

        config = self.integration.get_deployment_config()
        self.assertIsNone(config)

        method = self.integration.get_deployment_method()
        self.assertEqual(method, "github_actions")  # デフォルト

if __name__ == "__main__":
    unittest.main()
