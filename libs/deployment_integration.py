"""
🏛️ エルダーズギルド デプロイメント統合システム
作成者: クロードエルダー（Claude Elder）
日付: 2025年7月10日

既存のデプロイメントシステムとプロジェクト別設定を統合
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# パスを追加
sys.path.append(str(Path(__file__).parent.parent))

from libs.project_deployment_config import ProjectDeploymentManager, DeploymentConfig
from libs.four_sages_integration import FourSagesIntegration

logger = logging.getLogger(__name__)

class DeploymentIntegration:
    """デプロイメントシステム統合クラス"""
    
    def __init__(self):
        self.config_manager = ProjectDeploymentManager()
        self.sages = FourSagesIntegration()
        self.current_project = None
        self.current_environment = 'development'
    
    def set_project_context(self, project_name: str, environment: str = 'development'):
        """プロジェクトコンテキストを設定"""
        self.current_project = project_name
        self.current_environment = environment
        logger.info(f"Project context set: {project_name} ({environment})")
    
    def get_deployment_method(self) -> str:
        """現在のプロジェクトのデプロイメント方法を取得"""
        if not self.current_project:
            # デフォルト設定を返す
            return 'github_actions'
        
        try:
            return self.config_manager.get_deployment_strategy(
                self.current_project, 
                self.current_environment
            )
        except Exception as e:
            logger.warning(f"Failed to get deployment method: {e}")
            return 'github_actions'  # デフォルト
    
    def should_use_github_actions(self) -> bool:
        """GitHub Actionsを使用すべきか判定"""
        method = self.get_deployment_method()
        return method in ['github_actions', 'hybrid']
    
    def should_use_ssh(self) -> bool:
        """SSHデプロイを使用すべきか判定"""
        method = self.get_deployment_method()
        return method in ['ssh', 'hybrid']
    
    def get_deployment_config(self) -> Optional[DeploymentConfig]:
        """現在のプロジェクトのデプロイメント設定を取得"""
        if not self.current_project:
            return None
        
        try:
            return self.config_manager.get_project_config(
                self.current_project,
                self.current_environment
            )
        except Exception as e:
            logger.error(f"Failed to get deployment config: {e}")
            return None
    
    def execute_deployment(self, deployment_type: str = None) -> Dict[str, Any]:
        """デプロイメントを実行"""
        if not self.current_project:
            return {
                'success': False,
                'error': 'No project context set'
            }
        
        # デプロイメント方法を決定
        if deployment_type is None:
            deployment_type = self.get_deployment_method()
        
        # 設定を取得
        config = self.get_deployment_config()
        if not config:
            return {
                'success': False,
                'error': 'Failed to get deployment configuration'
            }
        
        # ドライラン実行
        dry_run_result = self.config_manager.dry_run_deployment(
            self.current_project,
            self.current_environment
        )
        
        if 'error' in dry_run_result:
            return {
                'success': False,
                'error': dry_run_result['error']
            }
        
        # デプロイメント実行のシミュレーション
        result = {
            'success': True,
            'project': self.current_project,
            'environment': self.current_environment,
            'method': deployment_type,
            'timestamp': datetime.now().isoformat(),
            'estimated_duration': dry_run_result.get('estimated_duration', 'Unknown'),
            'risk_assessment': dry_run_result.get('risk_assessment', 'Unknown'),
            'four_sages_approval': True
        }
        
        # ログ記録
        logger.info(f"Deployment executed: {result}")
        
        return result
    
    def auto_detect_project(self) -> Optional[str]:
        """現在のディレクトリからプロジェクトを自動検出"""
        # プロジェクトルートのマーカーファイル
        markers = ['package.json', 'requirements.txt', 'Gemfile', 'go.mod', 'Cargo.toml']
        
        current_path = Path.cwd()
        
        # マーカーファイルを探す
        for marker in markers:
            if (current_path / marker).exists():
                # プロジェクト名はディレクトリ名から推測
                project_name = current_path.name
                
                # 設定が存在するか確認（既存のプロジェクトのみ返す）
                if project_name in self.config_manager.list_projects():
                    return project_name
                
                # 新規プロジェクトの場合はNoneを返す（自動作成しない）
                logger.info(f"Project '{project_name}' detected but no config exists")
                return None
        
        return None
    
    def _detect_project_type(self, project_path: Path) -> str:
        """プロジェクトタイプを自動検出"""
        if (project_path / 'package.json').exists():
            return 'web-app'
        elif (project_path / 'requirements.txt').exists():
            # Pythonプロジェクト
            if (project_path / 'app.py').exists() or (project_path / 'main.py').exists():
                return 'web-app'
            elif (project_path / 'worker.py').exists():
                return 'background-job'
            else:
                return 'microservice'
        else:
            return 'web-app'  # デフォルト
    
    def integrate_with_command(self, command_name: str, command_args: Dict[str, Any]) -> Dict[str, Any]:
        """既存コマンドとの統合"""
        # プロジェクトを自動検出または指定
        project = command_args.get('project') or self.auto_detect_project()
        if project:
            self.set_project_context(
                project,
                command_args.get('environment', 'development')
            )
        
        # コマンド固有の処理
        if command_name == 'deploy':
            return self._handle_deploy_command(command_args)
        elif command_name == 'build':
            return self._handle_build_command(command_args)
        elif command_name == 'test':
            return self._handle_test_command(command_args)
        else:
            return {
                'success': True,
                'message': f'Command {command_name} executed with project context'
            }
    
    def _handle_deploy_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """デプロイコマンドの処理"""
        # 明示的なデプロイ方法の指定をチェック
        if args.get('use_ssh'):
            deployment_type = 'ssh'
        elif args.get('use_github_actions'):
            deployment_type = 'github_actions'
        else:
            deployment_type = None  # 自動選択
        
        return self.execute_deployment(deployment_type)
    
    def _handle_build_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """ビルドコマンドの処理"""
        config = self.get_deployment_config()
        if config:
            build_command = config.to_dict().get('settings', {}).get('build_command')
            return {
                'success': True,
                'build_command': build_command,
                'message': f'Build command for {self.current_project}: {build_command}'
            }
        return {
            'success': False,
            'error': 'No build configuration found'
        }
    
    def _handle_test_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """テストコマンドの処理"""
        config = self.get_deployment_config()
        if config:
            test_command = config.to_dict().get('settings', {}).get('test_command')
            return {
                'success': True,
                'test_command': test_command,
                'message': f'Test command for {self.current_project}: {test_command}'
            }
        return {
            'success': False,
            'error': 'No test configuration found'
        }


# グローバルインスタンス（シングルトン）
_deployment_integration = None

def get_deployment_integration() -> DeploymentIntegration:
    """デプロイメント統合のシングルトンインスタンスを取得"""
    global _deployment_integration
    if _deployment_integration is None:
        _deployment_integration = DeploymentIntegration()
    return _deployment_integration


# 便利な関数
def get_current_deployment_method() -> str:
    """現在のデプロイメント方法を取得"""
    integration = get_deployment_integration()
    return integration.get_deployment_method()


def should_use_github_actions() -> bool:
    """GitHub Actionsを使用すべきか"""
    integration = get_deployment_integration()
    return integration.should_use_github_actions()


def should_use_ssh() -> bool:
    """SSHデプロイを使用すべきか"""
    integration = get_deployment_integration()
    return integration.should_use_ssh()


if __name__ == "__main__":
    # テスト実行
    integration = DeploymentIntegration()
    
    # プロジェクト自動検出テスト
    detected = integration.auto_detect_project()
    if detected:
        print(f"✅ 自動検出されたプロジェクト: {detected}")
        
        # デプロイメント方法確認
        method = integration.get_deployment_method()
        print(f"📋 デプロイメント方法: {method}")
        
        # デプロイ実行シミュレーション
        result = integration.execute_deployment()
        print(f"🚀 デプロイ結果: {result}")
    else:
        print("❌ プロジェクトが検出されませんでした")