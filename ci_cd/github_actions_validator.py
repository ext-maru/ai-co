#!/usr/bin/env python3
"""
GitHub Actions ワークフロー設定バリデーター
"""
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path


class GitHubActionsValidator:
    """GitHub Actions ワークフロー設定の検証クラス"""
    
    def __init__(self):
        """バリデーターの初期化"""
        self.required_fields = ['name', 'on', 'jobs']
        self.security_best_practices = {
            'permissions': 'ワークフローの権限を最小限に設定',
            'actions_version': 'アクションのバージョンを固定',
            'secrets_usage': 'シークレットの適切な使用'
        }
    
    def validate_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """ワークフロー設定の検証"""
        errors = []
        
        # 必須フィールドの確認
        for field in self.required_fields:
            if field not in workflow_data:
                errors.append(f"必須フィールド '{field}' が不足しています")
        
        # on フィールドの詳細チェック
        if 'on' in workflow_data:
            on_triggers = workflow_data['on']
            if not isinstance(on_triggers, dict):
                errors.append("'on' フィールドは辞書形式である必要があります")
            else:
                # push または pull_request のいずれかが必要
                if 'push' not in on_triggers and 'pull_request' not in on_triggers:
                    errors.append("'push' または 'pull_request' トリガーが必要です")
        
        # jobs フィールドの詳細チェック
        if 'jobs' in workflow_data:
            jobs = workflow_data['jobs']
            if not isinstance(jobs, dict) or len(jobs) == 0:
                errors.append("少なくとも1つのジョブが必要です")
            else:
                for job_name, job_config in jobs.items():
                    if 'runs-on' not in job_config:
                        errors.append(f"ジョブ '{job_name}' に 'runs-on' が定義されていません")
                    if 'steps' not in job_config:
                        errors.append(f"ジョブ '{job_name}' に 'steps' が定義されていません")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_security(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティベストプラクティスの検証"""
        recommendations = []
        security_issues = []
        
        # 権限設定の確認
        self._validate_permissions(workflow_data, recommendations, security_issues)
        
        # アクションのバージョン固定チェック
        self._validate_action_versions(workflow_data, security_issues)
        
        # シークレットの使用チェック
        self._validate_secrets_usage(workflow_data, recommendations, security_issues)
        
        return {
            'secure': len(security_issues) == 0,
            'security_issues': security_issues,
            'recommendations': recommendations
        }
    
    def _validate_permissions(self, workflow_data: Dict[str, Any], recommendations: List[str], security_issues: List[str]) -> None:
        """権限設定の検証"""
        if 'permissions' in workflow_data:
            permissions = workflow_data['permissions']
            if isinstance(permissions, dict):
                # 最小権限の原則をチェック
                if 'write' in str(permissions).lower():
                    recommendations.append("書き込み権限は必要最小限に設定してください")
            recommendations.append("permissions フィールドが適切に設定されています")
        else:
            security_issues.append("permissions フィールドを設定して最小権限を定義してください")
    
    def _validate_action_versions(self, workflow_data: Dict[str, Any], security_issues: List[str]) -> None:
        """アクションのバージョン固定チェック"""
        if 'jobs' in workflow_data:
            for job_name, job_config in workflow_data['jobs'].items():
                if 'steps' in job_config:
                    for step in job_config['steps']:
                        if 'uses' in step:
                            uses = step['uses']
                            if '@' not in uses:
                                security_issues.append(f"アクション '{uses}' にバージョンを指定してください")
    
    def _validate_secrets_usage(self, workflow_data: Dict[str, Any], recommendations: List[str], security_issues: List[str]) -> None:
        """シークレットの使用チェック"""
        workflow_str = str(workflow_data)
        if 'secrets.' in workflow_str:
            recommendations.append("シークレットが適切に使用されています")
        
        # 環境変数での機密情報チェック
        if 'env' in workflow_data:
            env_vars = workflow_data['env']
            for key, value in env_vars.items():
                if isinstance(value, str) and any(keyword in value.lower() for keyword in ['password', 'token', 'key', 'secret']):
                    if not value.startswith('${{'):
                        security_issues.append(f"環境変数 '{key}' にハードコードされた機密情報が含まれる可能性があります")
    
    def validate_workflow_file(self, file_path: Path) -> Dict[str, Any]:
        """ワークフローファイルの検証"""
        if not file_path.exists():
            return {
                'valid': False,
                'errors': [f"ワークフローファイル '{file_path}' が見つかりません"]
            }
        
        try:
            with open(file_path, 'r') as f:
                workflow_data = yaml.safe_load(f)
            
            # 基本検証
            basic_validation = self.validate_workflow(workflow_data)
            
            # セキュリティ検証
            security_validation = self.validate_security(workflow_data)
            
            return {
                'valid': basic_validation['valid'],
                'errors': basic_validation['errors'],
                'security': security_validation
            }
            
        except yaml.YAMLError as e:
            return {
                'valid': False,
                'errors': [f"YAML解析エラー: {str(e)}"]
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"ファイル読み込みエラー: {str(e)}"]
            }