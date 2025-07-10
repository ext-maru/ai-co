#!/usr/bin/env python3
"""
🏛️ エルダーズギルド プロジェクト別デプロイメント設定管理コマンド
作成者: クロードエルダー（Claude Elder）
日付: 2025年7月10日

Usage:
    ai-deploy-config list
    ai-deploy-config show <project>
    ai-deploy-config create <project> --template <template>
    ai-deploy-config update <project> --file <config_file>
    ai-deploy-config method <project> <env> <method>
    ai-deploy-config validate <project>
    ai-deploy-config sages-optimize <project>
"""

import sys
import argparse
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List

# パスを追加
sys.path.append(str(Path(__file__).parent.parent))

from libs.project_deployment_config import ProjectDeploymentManager, DeploymentConfig
from libs.four_sages_integration import FourSagesIntegration
from commands.base_command import BaseCommand

class DeployConfigCommand(BaseCommand):
    """プロジェクト別デプロイメント設定管理コマンド"""
    
    def __init__(self):
        super().__init__(name='deploy-config', description='プロジェクト別デプロイメント設定管理')
        self.manager = ProjectDeploymentManager()
        self.sages = FourSagesIntegration()
    
    def execute(self, args: List[str]) -> int:
        """コマンド実行"""
        try:
            parser = self._create_parser()
            parsed_args = parser.parse_args(args)
            
            if parsed_args.command == 'list':
                return self._list_projects()
            elif parsed_args.command == 'show':
                return self._show_project(parsed_args.project, parsed_args.environment)
            elif parsed_args.command == 'create':
                return self._create_project(parsed_args.project, parsed_args.template, parsed_args.type)
            elif parsed_args.command == 'update':
                return self._update_project(parsed_args.project, parsed_args.file)
            elif parsed_args.command == 'method':
                return self._set_deployment_method(parsed_args.project, parsed_args.environment, parsed_args.method)
            elif parsed_args.command == 'validate':
                return self._validate_project(parsed_args.project, parsed_args.environment)
            elif parsed_args.command == 'dry-run':
                return self._dry_run_deployment(parsed_args.project, parsed_args.environment)
            elif parsed_args.command == 'sages-optimize':
                return self._sages_optimize(parsed_args.project)
            elif parsed_args.command == 'sages-recommend':
                return self._sages_recommend(parsed_args.project)
            elif parsed_args.command == 'sages-analyze':
                return self._sages_analyze(parsed_args.project)
            else:
                parser.print_help()
                return 1
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            return 1
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """引数パーサー作成"""
        parser = argparse.ArgumentParser(
            description='🏛️ エルダーズギルド プロジェクト別デプロイメント設定管理',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest='command', help='利用可能なコマンド')
        
        # list コマンド
        list_parser = subparsers.add_parser('list', help='プロジェクト一覧表示')
        
        # show コマンド
        show_parser = subparsers.add_parser('show', help='プロジェクト設定表示')
        show_parser.add_argument('project', help='プロジェクト名')
        show_parser.add_argument('--environment', '-e', default='development', help='環境名')
        
        # create コマンド
        create_parser = subparsers.add_parser('create', help='新規プロジェクト作成')
        create_parser.add_argument('project', help='プロジェクト名')
        create_parser.add_argument('--template', '-t', default='web-app', 
                                 choices=['web-app', 'microservice', 'background-job'],
                                 help='プロジェクトテンプレート')
        create_parser.add_argument('--type', default='web-app', help='プロジェクトタイプ')
        
        # update コマンド
        update_parser = subparsers.add_parser('update', help='プロジェクト設定更新')
        update_parser.add_argument('project', help='プロジェクト名')
        update_parser.add_argument('--file', '-f', required=True, help='設定ファイル')
        
        # method コマンド
        method_parser = subparsers.add_parser('method', help='デプロイ方法設定')
        method_parser.add_argument('project', help='プロジェクト名')
        method_parser.add_argument('environment', help='環境名')
        method_parser.add_argument('method', choices=['github_actions', 'ssh', 'hybrid'], 
                                 help='デプロイ方法')
        
        # validate コマンド
        validate_parser = subparsers.add_parser('validate', help='設定検証')
        validate_parser.add_argument('project', help='プロジェクト名')
        validate_parser.add_argument('--environment', '-e', default='development', help='環境名')
        
        # dry-run コマンド
        dry_run_parser = subparsers.add_parser('dry-run', help='デプロイドライラン')
        dry_run_parser.add_argument('project', help='プロジェクト名')
        dry_run_parser.add_argument('environment', help='環境名')
        
        # sages-optimize コマンド
        sages_optimize_parser = subparsers.add_parser('sages-optimize', help='4賢者による最適化')
        sages_optimize_parser.add_argument('project', help='プロジェクト名')
        
        # sages-recommend コマンド
        sages_recommend_parser = subparsers.add_parser('sages-recommend', help='4賢者による推奨')
        sages_recommend_parser.add_argument('project', help='プロジェクト名')
        
        # sages-analyze コマンド
        sages_analyze_parser = subparsers.add_parser('sages-analyze', help='4賢者による分析')
        sages_analyze_parser.add_argument('project', help='プロジェクト名')
        
        return parser
    
    def _list_projects(self) -> int:
        """プロジェクト一覧表示"""
        try:
            projects = self.manager.list_projects()
            
            print("🏛️ エルダーズギルド プロジェクト一覧")
            print("=" * 40)
            
            if not projects:
                print("📋 プロジェクトがありません")
                return 0
            
            for project in projects:
                # プロジェクト情報取得
                try:
                    config = self.manager.get_project_config(project, 'development')
                    environments = self.manager.get_project_environments(project)
                    
                    print(f"📁 {project}")
                    print(f"   🚀 デプロイ方法: {config.deployment_method}")
                    print(f"   🌍 環境: {', '.join(environments)}")
                    print(f"   📊 最終更新: {config.metadata.get('last_updated', 'N/A')}")
                except Exception as e:
                    print(f"📁 {project} (設定読み込みエラー: {e})")
                print()
            
            return 0
        except Exception as e:
            print(f"❌ プロジェクト一覧取得エラー: {e}")
            return 1
    
    def _show_project(self, project: str, environment: str) -> int:
        """プロジェクト設定表示"""
        try:
            config = self.manager.get_project_config(project, environment)
            
            print(f"🏛️ プロジェクト設定: {project} ({environment})")
            print("=" * 50)
            
            # 基本情報
            print("📋 基本情報:")
            print(f"   プロジェクト名: {config.project_name}")
            print(f"   デプロイ方法: {config.deployment_method}")
            print(f"   環境: {environment}")
            print()
            
            # 環境設定
            if environment in config.environments:
                env_config = config.environments[environment]
                print("🌍 環境設定:")
                for key, value in env_config.items():
                    print(f"   {key}: {value}")
                print()
            
            # 4賢者設定
            if config.four_sages_config:
                print("🧙‍♂️ 4賢者設定:")
                for sage, sage_config in config.four_sages_config.items():
                    print(f"   {sage}: {sage_config}")
                print()
            
            # 騎士団設定
            if config.knights_config:
                print("🛡️ 騎士団設定:")
                for key, value in config.knights_config.items():
                    print(f"   {key}: {value}")
                print()
            
            # メタデータ
            if config.metadata:
                print("📊 メタデータ:")
                for key, value in config.metadata.items():
                    print(f"   {key}: {value}")
            
            return 0
        except Exception as e:
            print(f"❌ プロジェクト設定表示エラー: {e}")
            return 1
    
    def _create_project(self, project: str, template: str, project_type: str) -> int:
        """新規プロジェクト作成"""
        try:
            print(f"🏛️ 新規プロジェクト作成: {project}")
            print(f"📋 テンプレート: {template}")
            print(f"🎯 タイプ: {project_type}")
            print()
            
            if self.manager.create_project_config(project, template, project_type):
                print("✅ プロジェクト作成成功")
                print()
                
                # 4賢者による初期最適化
                print("🧙‍♂️ 4賢者による初期最適化中...")
                try:
                    self.manager.update_project_config(project, {})
                    print("✅ 初期最適化完了")
                except Exception as e:
                    print(f"⚠️ 初期最適化エラー: {e}")
                
                # 作成された設定を表示
                return self._show_project(project, 'development')
            else:
                print("❌ プロジェクト作成失敗")
                return 1
        except Exception as e:
            print(f"❌ プロジェクト作成エラー: {e}")
            return 1
    
    def _update_project(self, project: str, config_file: str) -> int:
        """プロジェクト設定更新"""
        try:
            print(f"🏛️ プロジェクト設定更新: {project}")
            print(f"📁 設定ファイル: {config_file}")
            print()
            
            # 設定ファイル読み込み
            config_path = Path(config_file)
            if not config_path.exists():
                print(f"❌ 設定ファイルが見つかりません: {config_file}")
                return 1
            
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix == '.json':
                    config_updates = json.load(f)
                elif config_path.suffix in ['.yml', '.yaml']:
                    config_updates = yaml.safe_load(f)
                else:
                    print(f"❌ サポートされていないファイル形式: {config_path.suffix}")
                    return 1
            
            # 設定更新
            if self.manager.update_project_config(project, config_updates):
                print("✅ プロジェクト設定更新成功")
                return 0
            else:
                print("❌ プロジェクト設定更新失敗")
                return 1
        except Exception as e:
            print(f"❌ プロジェクト設定更新エラー: {e}")
            return 1
    
    def _set_deployment_method(self, project: str, environment: str, method: str) -> int:
        """デプロイ方法設定"""
        try:
            print(f"🏛️ デプロイ方法設定: {project} ({environment})")
            print(f"🚀 新しいデプロイ方法: {method}")
            print()
            
            if self.manager.set_deployment_method(project, environment, method):
                print("✅ デプロイ方法設定成功")
                
                # 設定後の状態を表示
                config = self.manager.get_project_config(project, environment)
                print(f"📋 現在の設定: {config.deployment_method}")
                return 0
            else:
                print("❌ デプロイ方法設定失敗")
                return 1
        except Exception as e:
            print(f"❌ デプロイ方法設定エラー: {e}")
            return 1
    
    def _validate_project(self, project: str, environment: str) -> int:
        """設定検証"""
        try:
            print(f"🏛️ 設定検証: {project} ({environment})")
            print("=" * 40)
            
            is_valid, errors = self.manager.validate_config(project, environment)
            
            if is_valid:
                print("✅ 設定検証成功")
                print("🏛️ 全ての設定が正常です")
                
                # 4賢者による追加分析
                print("\n🧙‍♂️ 4賢者による設定分析:")
                try:
                    config = self.manager.get_project_config(project, environment)
                    analysis = self.sages.analyze_deployment_config(config.to_dict())
                    
                    for sage, result in analysis.items():
                        print(f"   {sage}: {result}")
                except Exception as e:
                    print(f"   ⚠️ 4賢者分析エラー: {e}")
                
                return 0
            else:
                print("❌ 設定検証失敗")
                print("\n🚨 検証エラー:")
                for error in errors:
                    print(f"   • {error}")
                return 1
        except Exception as e:
            print(f"❌ 設定検証エラー: {e}")
            return 1
    
    def _dry_run_deployment(self, project: str, environment: str) -> int:
        """デプロイドライラン"""
        try:
            print(f"🏛️ デプロイドライラン: {project} ({environment})")
            print("=" * 40)
            
            result = self.manager.dry_run_deployment(project, environment)
            
            if 'error' in result:
                print(f"❌ ドライランエラー: {result['error']}")
                return 1
            
            print("📋 デプロイ計画:")
            print(f"   プロジェクト: {result['project_name']}")
            print(f"   環境: {result['environment']}")
            print(f"   デプロイ方法: {result['deployment_method']}")
            print(f"   推定時間: {result['estimated_duration']}")
            print(f"   リスク評価: {result['risk_assessment']}")
            print()
            
            # 検証結果
            is_valid, errors = result['validation_result']
            if is_valid:
                print("✅ 設定検証: 成功")
            else:
                print("❌ 設定検証: 失敗")
                for error in errors:
                    print(f"   • {error}")
            print()
            
            # 4賢者分析
            if 'four_sages_analysis' in result:
                print("🧙‍♂️ 4賢者分析:")
                for sage, analysis in result['four_sages_analysis'].items():
                    print(f"   {sage}: {analysis}")
            
            return 0
        except Exception as e:
            print(f"❌ デプロイドライランエラー: {e}")
            return 1
    
    def _sages_optimize(self, project: str) -> int:
        """4賢者による最適化"""
        try:
            print(f"🏛️ 4賢者による最適化: {project}")
            print("=" * 40)
            
            print("🧙‍♂️ 4賢者会議開始...")
            
            # 最適化実行
            if self.manager.update_project_config(project, {}):
                print("✅ 4賢者による最適化完了")
                
                # 最適化後の設定を表示
                config = self.manager.get_project_config(project, 'development')
                print("\n📋 最適化後の設定:")
                print(f"   デプロイ方法: {config.deployment_method}")
                print(f"   最適化日時: {config.metadata.get('last_updated', 'N/A')}")
                
                return 0
            else:
                print("❌ 4賢者による最適化失敗")
                return 1
        except Exception as e:
            print(f"❌ 4賢者最適化エラー: {e}")
            return 1
    
    def _sages_recommend(self, project: str) -> int:
        """4賢者による推奨"""
        try:
            print(f"🏛️ 4賢者による推奨: {project}")
            print("=" * 40)
            
            config = self.manager.get_project_config(project, 'development')
            recommendations = self.sages.generate_deployment_recommendations(config.to_dict())
            
            print("🧙‍♂️ 4賢者からの推奨事項:")
            for sage, recommendation in recommendations.items():
                print(f"\n{sage}:")
                if isinstance(recommendation, dict):
                    for key, value in recommendation.items():
                        print(f"   {key}: {value}")
                else:
                    print(f"   {recommendation}")
            
            return 0
        except Exception as e:
            print(f"❌ 4賢者推奨エラー: {e}")
            return 1
    
    def _sages_analyze(self, project: str) -> int:
        """4賢者による分析"""
        try:
            print(f"🏛️ 4賢者による分析: {project}")
            print("=" * 40)
            
            report = self.manager.generate_deployment_report(project, 'development')
            
            if 'error' in report:
                print(f"❌ 分析エラー: {report['error']}")
                return 1
            
            print("📊 デプロイメント分析レポート:")
            print(f"   プロジェクト: {report['project_name']}")
            print(f"   環境: {report['environment']}")
            print(f"   分析時刻: {report['timestamp']}")
            print()
            
            # 検証結果
            validation = report['validation']
            if validation['valid']:
                print("✅ 設定検証: 成功")
            else:
                print("❌ 設定検証: 失敗")
                for error in validation['errors']:
                    print(f"   • {error}")
            print()
            
            # 4賢者分析
            if 'four_sages_analysis' in report:
                print("🧙‍♂️ 4賢者分析:")
                for sage, analysis in report['four_sages_analysis'].items():
                    print(f"   {sage}: {analysis}")
            print()
            
            # 推奨事項
            if 'recommendations' in report:
                print("💡 推奨事項:")
                for sage, recommendation in report['recommendations'].items():
                    print(f"   {sage}: {recommendation}")
            
            return 0
        except Exception as e:
            print(f"❌ 4賢者分析エラー: {e}")
            return 1

def main():
    """メイン関数"""
    command = DeployConfigCommand()
    return command.execute(sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main())