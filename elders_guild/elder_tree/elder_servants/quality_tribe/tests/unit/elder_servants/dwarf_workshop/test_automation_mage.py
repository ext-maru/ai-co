"""
AutomationMage (D16) のテストケース

TDD方式で自動化魔術師の各機能をテストします。
包括的な自動化ソリューション機能の品質を保証。
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# テスト対象のインポート
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from elders_guild.elder_tree.elder_servants.dwarf_workshop.automation_mage import (
    AutomationMage,
    AutomationMageRequest,
    AutomationMageResponse,
    WorkflowDefinition,
    AutomationTask,
    ExecutionResult,
    WorkflowExecution,
    AutomationType,
    TriggerType,
)


class TestAutomationMage:
    """AutomationMage (D16) テストスイート"""

    @pytest.fixture
    def automation_mage(self):
        """AutomationMageインスタンスを作成"""
        return AutomationMage()

    @pytest.fixture
    def basic_request(self):
        """基本的なリクエストを作成"""
        return AutomationMageRequest(
            action="create_workflow",
            workflow_name="test_ci_cd_workflow",
            parameters={
                "template": "basic_ci_cd",
                "description": "Test CI/CD workflow",
                "project_name": "test_project",
                "repository": "https://github.com/test/repo.git",
                "environment": "development",
            }
        )

    def test_automation_mage_initialization(self, automation_mage):
        """🔴 AutomationMageの初期化テスト"""
        assert automation_mage.servant_id == "D16"
        assert automation_mage.name == "AutomationMage"
        assert automation_mage.automation_engines is not None
        assert "jenkins" in automation_mage.automation_engines
        assert "github_actions" in automation_mage.automation_engines
        assert "terraform" in automation_mage.automation_engines

    def test_automation_mage_capabilities(self, automation_mage):
        """🔴 AutomationMageの能力一覧テスト"""
        capabilities = automation_mage.get_capabilities()
        
        assert "ワークフロー自動化" in capabilities
        assert "CI/CDパイプライン構築" in capabilities
        assert "インフラストラクチャ自動化" in capabilities
        assert "デプロイメント自動化" in capabilities
        assert "依存関係管理" in capabilities
        assert len(capabilities) >= 8

    @pytest.mark.asyncio
    async def test_validate_request_valid(self, automation_mage, basic_request):
        """🔴 有効なリクエストの検証テスト"""
        is_valid = await automation_mage.validate_request(basic_request)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_request_invalid_action(self, automation_mage):
        """🔴 無効なアクションのリクエスト検証テスト"""
        invalid_request = AutomationMageRequest(action="invalid_action")
        is_valid = await automation_mage.validate_request(invalid_request)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_create_workflow_success(self, automation_mage, basic_request):
        """🟢 ワークフロー作成成功テスト"""
        response = await automation_mage.process_request(basic_request)
        
        assert response.success is True
        assert response.workflow_definition is not None
        assert response.workflow_definition.name == "test_ci_cd_workflow"
        assert len(response.workflow_definition.tasks) > 0
        assert response.recommendations is not None

    @pytest.mark.asyncio
    async def test_workflow_tasks_generation(self, automation_mage, basic_request):
        """🟢 ワークフロータスク生成テスト"""
        response = await automation_mage.process_request(basic_request)
        
        assert response.success is True
        
        # タスクの確認
        tasks = response.workflow_definition.tasks
        task_names = [task.name for task in tasks]
        
        # CI/CDパイプラインの基本タスクが含まれることを確認
        assert "checkout_code" in task_names
        assert "build_application" in task_names
        assert "run_tests" in task_names
        assert "security_scan" in task_names

    @pytest.mark.asyncio
    async def test_dependencies_definition(self, automation_mage, basic_request):
        """🟢 依存関係定義テスト"""
        response = await automation_mage.process_request(basic_request)
        
        assert response.success is True
        
        # 依存関係の確認
        dependencies = response.workflow_definition.dependencies
        
        # ビルドタスクがチェックアウトタスクに依存することを確認
        if "build_application" in dependencies:
            assert "checkout_code" in dependencies["build_application"]

    @pytest.mark.asyncio
    async def test_global_variables_definition(self, automation_mage, basic_request):
        """🟢 グローバル変数定義テスト"""
        response = await automation_mage.process_request(basic_request)
        
        assert response.success is True
        
        # グローバル変数の確認
        global_vars = response.workflow_definition.global_variables
        
        assert "project_name" in global_vars
        assert "environment" in global_vars
        assert "build_number" in global_vars
        assert global_vars["project_name"] == "test_project"

    @pytest.mark.asyncio
    async def test_error_handling_definition(self, automation_mage, basic_request):
        """🟢 エラーハンドリング定義テスト"""
        response = await automation_mage.process_request(basic_request)
        
        assert response.success is True
        
        # エラーハンドリング設定の確認
        error_handling = response.workflow_definition.error_handling
        
        assert "on_failure" in error_handling
        assert "timeout_handling" in error_handling
        assert "rollback" in error_handling
        assert error_handling["on_failure"]["strategy"] == "fail_fast"

    @pytest.mark.asyncio
    async def test_notifications_definition(self, automation_mage, basic_request):
        """🟢 通知設定定義テスト"""
        response = await automation_mage.process_request(basic_request)
        
        assert response.success is True
        
        # 通知設定の確認
        notifications = response.workflow_definition.notifications
        
        assert "channels" in notifications
        assert "templates" in notifications
        assert "slack" in notifications["channels"]

    @pytest.mark.asyncio
    async def test_workflow_validation(self, automation_mage, basic_request):
        """🟢 ワークフロー検証テスト"""
        response = await automation_mage.process_request(basic_request)
        
        assert response.success is True
        
        # ワークフローが正常に検証されることを確認
        workflow = response.workflow_definition
        
        # タスク名の重複がないことを確認
        task_names = [task.name for task in workflow.tasks]
        assert len(task_names) == len(set(task_names))

    @pytest.mark.asyncio
    async def test_microservices_workflow(self, automation_mage):
        """🟢 マイクロサービスワークフローテスト"""
        request = AutomationMageRequest(
            action="create_workflow",
            workflow_name="microservices_pipeline",
            parameters={
                "template": "microservices_pipeline",
                "project_name": "micro_app",
            }
        )
        
        response = await automation_mage.process_request(request)
        
        assert response.success is True
        assert response.workflow_definition.name == "microservices_pipeline"

    @pytest.mark.asyncio
    async def test_infrastructure_workflow(self, automation_mage):
        """🟢 インフラストラクチャワークフローテスト"""
        request = AutomationMageRequest(
            action="create_workflow",
            workflow_name="infra_deployment",
            parameters={
                "template": "infrastructure_deployment",
                "project_name": "infra_project",
            }
        )
        
        response = await automation_mage.process_request(request)
        
        assert response.success is True
        assert response.workflow_definition.name == "infra_deployment"

    @pytest.mark.asyncio
    async def test_custom_tasks_support(self, automation_mage):
        """🟢 カスタムタスクサポートテスト"""
        request = AutomationMageRequest(
            action="create_workflow",
            workflow_name="custom_workflow",
            parameters={
                "custom_tasks": [
                    {
                        "name": "custom_validation",
                        "description": "Custom validation task",
                        "type": "workflow",
                        "actions": [{"type": "validate", "script": "validate.sh"}],
                        "tags": ["custom", "validation"]
                    }
                ]
            }
        )
        
        response = await automation_mage.process_request(request)
        
        assert response.success is True
        
        # カスタムタスクが含まれることを確認
        tasks = response.workflow_definition.tasks
        task_names = [task.name for task in tasks]
        assert "custom_validation" in task_names

    @pytest.mark.asyncio
    async def test_jenkins_config(self, automation_mage):
        """🟢 Jenkins設定テスト"""
        jenkins_config = automation_mage._get_jenkins_config()
        
        assert jenkins_config["name"] == "jenkins"
        assert "url" in jenkins_config
        assert "pipeline_format" in jenkins_config
        assert jenkins_config["pipeline_format"] == "Jenkinsfile"

    @pytest.mark.asyncio
    async def test_github_actions_config(self, automation_mage):
        """🟢 GitHub Actions設定テスト"""
        ga_config = automation_mage._get_github_actions_config()
        
        assert ga_config["name"] == "github_actions"
        assert "workflow_path" in ga_config
        assert "file_format" in ga_config
        assert ga_config["workflow_path"] == ".github/workflows"

    @pytest.mark.asyncio
    async def test_gitlab_ci_config(self, automation_mage):
        """🟢 GitLab CI設定テスト"""
        gitlab_config = automation_mage._get_gitlab_ci_config()
        
        assert gitlab_config["name"] == "gitlab_ci"
        assert "config_file" in gitlab_config
        assert gitlab_config["config_file"] == ".gitlab-ci.yml"

    @pytest.mark.asyncio
    async def test_terraform_config(self, automation_mage):
        """🟢 Terraform設定テスト"""
        terraform_config = automation_mage._get_terraform_config()
        
        assert terraform_config["name"] == "terraform"
        assert "version" in terraform_config
        assert "state_backend" in terraform_config

    @pytest.mark.asyncio
    async def test_workflow_templates_loading(self, automation_mage):
        """🟢 ワークフローテンプレート読み込みテスト"""
        templates = automation_mage.workflow_templates
        
        assert "basic_ci_cd" in templates
        assert "infrastructure_deployment" in templates
        assert "microservices_pipeline" in templates
        
        # テンプレート構造の確認
        basic_template = templates["basic_ci_cd"]
        assert "source_control" in basic_template
        assert "build" in basic_template
        assert "testing" in basic_template

    @pytest.mark.asyncio
    async def test_automation_patterns_loading(self, automation_mage):
        """🟢 自動化パターン読み込みテスト"""
        patterns = automation_mage.automation_patterns
        
        assert "daily_backup" in patterns
        assert "health_check" in patterns
        assert "log_rotation" in patterns
        
        # パターン構造の確認
        backup_pattern = patterns["daily_backup"]
        assert backup_pattern["type"] == "backup"
        assert backup_pattern["schedule"] == "0 2 * * *"

    @pytest.mark.asyncio
    async def test_scheduler_config_loading(self, automation_mage):
        """🟢 スケジューラー設定読み込みテスト"""
        scheduler_config = automation_mage.scheduler_config
        
        assert "engine" in scheduler_config
        assert "timezone" in scheduler_config
        assert "max_concurrent" in scheduler_config
        assert scheduler_config["engine"] == "cron"

    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self, automation_mage):
        """🟢 循環依存検出テスト"""
        # 循環依存のテスト
        dependencies = {
            "task_a": ["task_b"],
            "task_b": ["task_c"],
            "task_c": ["task_a"]  # 循環依存
        }
        
        has_circular = automation_mage._has_circular_dependencies(dependencies)
        assert has_circular is True
        
        # 正常な依存関係のテスト
        normal_dependencies = {
            "task_a": ["task_b"],
            "task_b": ["task_c"],
            "task_c": []
        }
        
        has_circular = automation_mage._has_circular_dependencies(normal_dependencies)
        assert has_circular is False

    @pytest.mark.asyncio
    async def test_workflow_recommendations(self, automation_mage, basic_request):
        """🟢 ワークフロー推奨事項テスト"""
        response = await automation_mage.process_request(basic_request)
        
        assert response.success is True
        assert len(response.recommendations) > 0
        
        # 一般的な推奨事項が含まれることを確認
        recommendations_text = " ".join(response.recommendations)
        assert "セキュリティ" in recommendations_text or "テスト" in recommendations_text

    @pytest.mark.asyncio
    async def test_unsupported_action(self, automation_mage):
        """🔴 サポートされていないアクションテスト"""
        request = AutomationMageRequest(action="unsupported_action")
        response = await automation_mage.process_request(request)
        
        assert response.success is False
        assert "サポートされていないアクション" in response.error_message

    @pytest.mark.asyncio
    async def test_metrics_retrieval(self, automation_mage):
        """🟢 品質メトリクス取得テスト"""
        metrics = await automation_mage.get_metrics()
        
        assert isinstance(metrics, dict)
        assert "root_cause_resolution" in metrics
        assert "test_coverage" in metrics
        assert "security_score" in metrics
        
        # Iron Will基準の確認
        assert metrics["root_cause_resolution"] >= 95.0
        assert metrics["test_coverage"] >= 95.0
        assert metrics["security_score"] >= 90.0

    @pytest.mark.asyncio
    async def test_error_handling(self, automation_mage):
        """🔴 エラーハンドリングテスト"""
        # 不正なリクエストでエラーが適切に処理されることを確認
        with patch.object(automation_mage, '_create_workflow', side_effect=Exception("Test error")):
            request = AutomationMageRequest(action="create_workflow")
            response = await automation_mage.process_request(request)
            
            assert response.success is False
            assert "処理エラー" in response.error_message

    def test_automation_task_creation(self):
        """🟢 AutomationTaskデータクラステスト"""
        task = AutomationTask(
            name="test_task",
            description="Test automation task",
            automation_type=AutomationType.CI_CD,
            trigger={"type": "manual"},
            actions=[{"type": "build", "command": "make"}],
            timeout_seconds=1800,
            tags=["build", "test"]
        )
        
        assert task.name == "test_task"
        assert task.automation_type == AutomationType.CI_CD
        assert task.timeout_seconds == 1800
        assert "build" in task.tags
        assert task.enabled is True  # デフォルト値

    def test_workflow_definition_creation(self):
        """🟢 WorkflowDefinitionデータクラステスト"""
        from datetime import datetime
        
        tasks = [
            AutomationTask(
                name="test_task",
                description="Test task",
                automation_type=AutomationType.CI_CD,
                trigger={"type": "manual"},
                actions=[]
            )
        ]
        
        workflow = WorkflowDefinition(
            name="test_workflow",
            description="Test workflow",
            tasks=tasks,
            dependencies={"test_task": []},
            global_variables={"env": "test"},
            error_handling={},
            notifications={},
            created_at=datetime.now(),
            version="1.0.0"
        )
        
        assert workflow.name == "test_workflow"
        assert len(workflow.tasks) == 1
        assert workflow.version == "1.0.0"
        assert workflow.global_variables["env"] == "test"

    def test_execution_result_creation(self):
        """🟢 ExecutionResultデータクラステスト"""
        from datetime import datetime
        
        result = ExecutionResult(
            task_name="test_task",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=30.5,
            output={"message": "Task completed"},
            error_message=None
        )
        
        assert result.task_name == "test_task"
        assert result.status == "success"
        assert result.duration_seconds == 30.5
        assert result.output["message"] == "Task completed"

    @pytest.mark.asyncio
    async def test_automation_types(self):
        """🟢 自動化タイプテスト"""
        # すべての自動化タイプが定義されていることを確認
        automation_types = list(AutomationType)
        type_values = [at.value for at in automation_types]
        
        assert "ci_cd" in type_values
        assert "infrastructure" in type_values
        assert "deployment" in type_values
        assert "monitoring" in type_values
        assert "testing" in type_values

    @pytest.mark.asyncio
    async def test_trigger_types(self):
        """🟢 トリガータイプテスト"""
        # すべてのトリガータイプが定義されていることを確認
        trigger_types = list(TriggerType)
        type_values = [tt.value for tt in trigger_types]
        
        assert "schedule" in type_values
        assert "event" in type_values
        assert "manual" in type_values
        assert "threshold" in type_values
        assert "dependency" in type_values

    @pytest.mark.asyncio
    async def test_workflow_with_schedule(self, automation_mage):
        """🟢 スケジュール付きワークフローテスト"""
        request = AutomationMageRequest(
            action="create_workflow",
            workflow_name="scheduled_workflow",
            schedule={"cron": "0 2 * * *", "timezone": "UTC"},
            parameters={"template": "basic_ci_cd"}
        )
        
        response = await automation_mage.process_request(request)
        
        assert response.success is True
        assert response.workflow_definition is not None

    @pytest.mark.asyncio
    async def test_workflow_with_parameters(self, automation_mage):
        """🟢 パラメータ付きワークフローテスト"""
        request = AutomationMageRequest(
            action="create_workflow",
            workflow_name="parametrized_workflow",
            parameters={
                "template": "basic_ci_cd",
                "global_variables": {"CUSTOM_VAR": "custom_value"},
                "notification_channels": ["slack", "email"],
                "retry_count": 5,
                "default_timeout": 7200
            }
        )
        
        response = await automation_mage.process_request(request)
        
        assert response.success is True
        
        # カスタムパラメータが反映されることを確認
        global_vars = response.workflow_definition.global_variables
        assert "CUSTOM_VAR" in global_vars

    @pytest.mark.asyncio
    async def test_concurrent_workflow_creation(self, automation_mage):
        """🔵 並行ワークフロー作成テスト（リファクタリング品質確認）"""
        # 複数のワークフロー作成を並行実行
        requests = [
            AutomationMageRequest(
                action="create_workflow",
                workflow_name=f"workflow_{i}",
                parameters={"template": "basic_ci_cd", "project_name": f"project_{i}"}
            )
            for i in range(3)
        ]
        
        # 並行実行
        responses = await asyncio.gather(*[
            automation_mage.process_request(req) for req in requests
        ])
        
        # すべてのレスポンスが成功することを確認
        for i, response in enumerate(responses):
            assert response.success is True
            assert response.workflow_definition is not None
            assert response.workflow_definition.name == f"workflow_{i}"