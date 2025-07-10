#!/usr/bin/env python3
"""
Claude Elder Rule Enforcement System 初期化スクリプト
エルダーズギルドのルール遵守システムを初期化・設定します
"""

import sys
import json
import logging
from pathlib import Path
import subprocess
import asyncio

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.claude_elder_rule_enforcement_system import get_rule_enforcement_system
from scripts.github_flow_hooks import GitHubFlowHooks

logger = logging.getLogger(__name__)

class RuleEnforcementInitializer:
    """ルール遵守システム初期化クラス"""
    
    def __init__(self):
        self.project_dir = PROJECT_ROOT
        self.config_dir = self.project_dir / "config"
        self.logs_dir = self.project_dir / "logs"
        self.setup_logging()
    
    def setup_logging(self):
        """ログ設定"""
        self.logs_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs_dir / 'rule_enforcement_init.log'),
                logging.StreamHandler()
            ]
        )
    
    def initialize_system(self):
        """システム初期化"""
        logger.info("🛡️ Claude Elder Rule Enforcement System 初期化開始")
        
        try:
            # 1. ディレクトリ構造の確認・作成
            self._ensure_directory_structure()
            
            # 2. 設定ファイルの検証
            self._validate_configuration()
            
            # 3. Git Hooksの設置
            self._setup_git_hooks()
            
            # 4. ルール遵守システムの初期化
            self._initialize_rule_system()
            
            # 5. 4賢者システムとの統合確認
            self._verify_four_sages_integration()
            
            # 6. 監視システムの起動
            self._start_monitoring_system()
            
            logger.info("✅ Claude Elder Rule Enforcement System 初期化完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ 初期化エラー: {e}")
            return False
    
    def _ensure_directory_structure(self):
        """ディレクトリ構造の確認・作成"""
        logger.info("📁 ディレクトリ構造を確認中...")
        
        required_dirs = [
            self.config_dir,
            self.logs_dir,
            self.project_dir / "knowledge_base" / "failures",
            self.project_dir / "knowledge_base" / "rule_violations",
            self.project_dir / ".git" / "hooks"
        ]
        
        for dir_path in required_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 ディレクトリ確認: {dir_path}")
    
    def _validate_configuration(self):
        """設定ファイルの検証"""
        logger.info("⚙️ 設定ファイルを検証中...")
        
        config_file = self.config_dir / "elder_rules.json"
        
        if not config_file.exists():
            logger.error(f"❌ 設定ファイルが見つかりません: {config_file}")
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # 必須項目の確認
            required_keys = [
                "rule_enforcement_config",
                "rules",
                "four_sages_integration",
                "notification_settings"
            ]
            
            for key in required_keys:
                if key not in config:
                    raise KeyError(f"Missing required configuration key: {key}")
            
            logger.info("✅ 設定ファイル検証完了")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ 設定ファイルの形式が不正です: {e}")
            raise
        except KeyError as e:
            logger.error(f"❌ 設定ファイルに必須項目がありません: {e}")
            raise
    
    def _setup_git_hooks(self):
        """Git Hooksの設置"""
        logger.info("🔗 Git Hooksを設置中...")
        
        try:
            hooks_system = GitHubFlowHooks(str(self.project_dir))
            
            if hooks_system.install_hooks():
                logger.info("✅ Git Hooks設置完了")
            else:
                logger.warning("⚠️ Git Hooks設置に一部失敗しました")
                
        except Exception as e:
            logger.error(f"❌ Git Hooks設置エラー: {e}")
            raise
    
    def _initialize_rule_system(self):
        """ルール遵守システムの初期化"""
        logger.info("🛡️ ルール遵守システムを初期化中...")
        
        try:
            rule_system = get_rule_enforcement_system()
            
            # システムの健全性チェック
            active_rules = rule_system.get_active_rules()
            logger.info(f"📋 アクティブなルール数: {len(active_rules)}")
            
            for rule_id in active_rules:
                logger.info(f"   - {rule_id}: {rule_system.rules[rule_id].name}")
            
            logger.info("✅ ルール遵守システム初期化完了")
            
        except Exception as e:
            logger.error(f"❌ ルール遵守システム初期化エラー: {e}")
            raise
    
    def _verify_four_sages_integration(self):
        """4賢者システムとの統合確認"""
        logger.info("🧙‍♂️ 4賢者システムとの統合を確認中...")
        
        try:
            # 各賢者との接続確認
            sage_systems = [
                ("Claude Task Tracker", "libs.claude_task_tracker"),
                ("GitHub Flow Manager", "libs.github_flow_manager"),
                ("Incident Integration", "libs.claude_elder_incident_integration"),
                ("Error Wrapper", "libs.claude_elder_error_wrapper")
            ]
            
            for sage_name, module_name in sage_systems:
                try:
                    __import__(module_name)
                    logger.info(f"✅ {sage_name} 統合確認完了")
                except ImportError as e:
                    logger.warning(f"⚠️ {sage_name} 統合に問題があります: {e}")
            
            logger.info("✅ 4賢者システム統合確認完了")
            
        except Exception as e:
            logger.error(f"❌ 4賢者システム統合確認エラー: {e}")
            raise
    
    def _start_monitoring_system(self):
        """監視システムの起動"""
        logger.info("👁️ 監視システムを起動中...")
        
        try:
            rule_system = get_rule_enforcement_system()
            
            # 監視開始
            rule_system.start_monitoring()
            
            # 初期状態レポート
            summary = rule_system.get_violation_summary()
            logger.info(f"📊 初期状態: {summary}")
            
            logger.info("✅ 監視システム起動完了")
            
        except Exception as e:
            logger.error(f"❌ 監視システム起動エラー: {e}")
            raise
    
    def create_systemd_service(self):
        """systemdサービスファイルの作成"""
        logger.info("🔧 systemdサービスファイルを作成中...")
        
        service_content = f"""[Unit]
Description=Claude Elder Rule Enforcement System
After=network.target

[Service]
Type=simple
User={self.project_dir.owner()}
WorkingDirectory={self.project_dir}
ExecStart=/usr/bin/python3 {self.project_dir}/scripts/rule_enforcement_daemon.py
Restart=always
RestartSec=5
Environment=PYTHONPATH={self.project_dir}

[Install]
WantedBy=multi-user.target
"""
        
        service_file = self.project_dir / "config" / "claude-elder-rules.service"
        
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        logger.info(f"✅ systemdサービスファイル作成: {service_file}")
        logger.info("📋 インストール手順:")
        logger.info(f"   sudo cp {service_file} /etc/systemd/system/")
        logger.info("   sudo systemctl daemon-reload")
        logger.info("   sudo systemctl enable claude-elder-rules")
        logger.info("   sudo systemctl start claude-elder-rules")
    
    def run_diagnostics(self):
        """診断・テストの実行"""
        logger.info("🔍 システム診断を実行中...")
        
        try:
            # Gitリポジトリの確認
            result = subprocess.run(
                ["git", "status"],
                capture_output=True, text=True, cwd=self.project_dir
            )
            
            if result.returncode == 0:
                logger.info("✅ Git リポジトリ確認完了")
            else:
                logger.warning("⚠️ Git リポジトリに問題があります")
            
            # Python環境の確認
            required_modules = [
                "asyncio",
                "json",
                "logging",
                "pathlib",
                "subprocess"
            ]
            
            for module in required_modules:
                try:
                    __import__(module)
                    logger.info(f"✅ {module} モジュール確認完了")
                except ImportError:
                    logger.error(f"❌ {module} モジュールが見つかりません")
            
            logger.info("✅ システム診断完了")
            
        except Exception as e:
            logger.error(f"❌ システム診断エラー: {e}")
            raise

def main():
    """メイン実行関数"""
    print("🛡️ Claude Elder Rule Enforcement System 初期化")
    print("=" * 50)
    
    initializer = RuleEnforcementInitializer()
    
    try:
        # システム初期化
        if initializer.initialize_system():
            print("\n✅ 初期化成功!")
            
            # オプション: systemdサービス作成
            create_service = input("\nsystemdサービスを作成しますか? (y/N): ")
            if create_service.lower() == 'y':
                initializer.create_systemd_service()
            
            # 診断実行
            run_diagnostics = input("\nシステム診断を実行しますか? (Y/n): ")
            if run_diagnostics.lower() != 'n':
                initializer.run_diagnostics()
            
            print("\n🎉 Claude Elder Rule Enforcement System の準備が完了しました!")
            print("\n📋 次のステップ:")
            print("   1. 設定ファイルをカスタマイズ: config/elder_rules.json")
            print("   2. 監視ログを確認: logs/rule_violations.json")
            print("   3. システムの稼働状況を確認: logs/rule_enforcement_init.log")
            
        else:
            print("\n❌ 初期化に失敗しました。ログを確認してください。")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 初期化が中断されました")
        return 1
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())