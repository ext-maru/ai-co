#!/usr/bin/env python3
"""
Elders Guild 設定検証システム
設定ファイルの整合性チェックと自動修正
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

@dataclass
class ConfigValidationResult:
    """設定検証結果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    missing_keys: List[str]
    fixed_issues: List[str]

class ConfigValidator:
    """設定ファイル検証・自動修正システム"""
    
    def __init__(self):
        self.project_root = Path("/home/aicompany/ai_co")
        self.env_file = self.project_root / ".env"
        self.logger = logging.getLogger(__name__)
        
        # 必須設定項目の定義
        self.required_configs = {
            "RABBITMQ_HOST": "localhost",
            "RABBITMQ_PORT": "5672", 
            "RABBITMQ_USER": "guest",
            "RABBITMQ_PASS": "guest",
            "AI_COMPANY_HOME": "/home/aicompany/ai_co",
            "PYTHONPATH": "/home/aicompany/ai_co",
            "WORKER_DEV_MODE": "true",
            "WORKER_TIMEOUT": "600"
        }
        
        # 設定の依存関係
        self.config_dependencies = {
            "RABBITMQ_HOST": ["RABBITMQ_PORT", "RABBITMQ_USER", "RABBITMQ_PASS"],
            "AI_COMPANY_HOME": ["PYTHONPATH"],
            "WORKER_DEV_MODE": ["WORKER_TIMEOUT"]
        }
    
    def validate_env_file(self) -> ConfigValidationResult:
        """環境変数ファイルの検証"""
        errors = []
        warnings = []
        missing_keys = []
        fixed_issues = []
        
        # .envファイルの存在確認
        if not self.env_file.exists():
            errors.append(f".env file not found: {self.env_file}")
            return ConfigValidationResult(False, errors, warnings, missing_keys, fixed_issues)
        
        # 現在の設定を読み込み
        current_config = self._load_env_file()
        
        # 必須項目のチェック
        for key, default_value in self.required_configs.items():
            if key not in current_config:
                missing_keys.append(key)
                self.logger.warning(f"Missing required config: {key}")
            elif not current_config[key]:
                warnings.append(f"Empty value for {key}")
        
        # 依存関係のチェック
        for main_key, dependent_keys in self.config_dependencies.items():
            if main_key in current_config:
                for dep_key in dependent_keys:
                    if dep_key not in current_config:
                        warnings.append(f"{main_key} requires {dep_key}")
        
        # パス存在チェック
        if "AI_COMPANY_HOME" in current_config:
            home_path = Path(current_config["AI_COMPANY_HOME"])
            if not home_path.exists():
                errors.append(f"AI_COMPANY_HOME path does not exist: {home_path}")
        
        # RabbitMQ接続チェック
        if self._has_rabbitmq_config(current_config):
            if not self._test_rabbitmq_connection(current_config):
                warnings.append("RabbitMQ connection test failed")
        
        is_valid = len(errors) == 0 and len(missing_keys) == 0
        return ConfigValidationResult(is_valid, errors, warnings, missing_keys, fixed_issues)
    
    def auto_fix_config(self) -> ConfigValidationResult:
        """設定の自動修正"""
        result = self.validate_env_file()
        fixed_issues = []
        
        if result.missing_keys:
            current_config = self._load_env_file()
            
            # 不足している設定を追加
            with open(self.env_file, 'a') as f:
                f.write('\n# Auto-generated missing configurations\n')
                for key in result.missing_keys:
                    default_value = self.required_configs[key]
                    f.write(f'{key}={default_value}\n')
                    fixed_issues.append(f"Added missing config: {key}={default_value}")
                    self.logger.info(f"Auto-fixed: {key}={default_value}")
        
        # 再検証
        final_result = self.validate_env_file()
        final_result.fixed_issues = fixed_issues
        
        return final_result
    
    def validate_worker_configs(self) -> List[ConfigValidationResult]:
        """ワーカー設定ファイルの検証"""
        results = []
        config_dir = self.project_root / "config"
        
        if not config_dir.exists():
            return results
        
        for config_file in config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # JSON形式の検証
                errors = []
                warnings = []
                
                # 共通項目のチェック
                if 'worker' in config_data:
                    worker_config = config_data['worker']
                    if 'timeout' not in worker_config:
                        warnings.append("Worker timeout not specified")
                    if 'max_retries' not in worker_config:
                        warnings.append("Worker max_retries not specified")
                
                is_valid = len(errors) == 0
                result = ConfigValidationResult(is_valid, errors, warnings, [], [])
                results.append(result)
                
            except json.JSONDecodeError as e:
                errors = [f"Invalid JSON in {config_file}: {e}"]
                result = ConfigValidationResult(False, errors, [], [], [])
                results.append(result)
                
        return results
    
    def generate_config_report(self) -> str:
        """設定検証レポートの生成"""
        env_result = self.validate_env_file()
        worker_results = self.validate_worker_configs()
        
        report = "🔧 Elders Guild 設定検証レポート\n"
        report += "=" * 50 + "\n\n"
        
        # .env ファイル検証結果
        report += "📄 .env ファイル検証結果:\n"
        if env_result.is_valid:
            report += "  ✅ 正常\n"
        else:
            report += "  ❌ 問題あり\n"
            for error in env_result.errors:
                report += f"    - エラー: {error}\n"
            for warning in env_result.warnings:
                report += f"    - 警告: {warning}\n"
            for missing in env_result.missing_keys:
                report += f"    - 不足: {missing}\n"
        
        # ワーカー設定検証結果
        report += f"\n⚙️ ワーカー設定検証結果: {len(worker_results)}ファイル\n"
        valid_count = sum(1 for r in worker_results if r.is_valid)
        report += f"  ✅ 正常: {valid_count}ファイル\n"
        report += f"  ❌ 問題: {len(worker_results) - valid_count}ファイル\n"
        
        return report
    
    def _load_env_file(self) -> Dict[str, str]:
        """環境変数ファイルの読み込み"""
        env_vars = {}
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        return env_vars
    
    def _has_rabbitmq_config(self, config: Dict[str, str]) -> bool:
        """RabbitMQ設定の存在確認"""
        rabbitmq_keys = ["RABBITMQ_HOST", "RABBITMQ_PORT", "RABBITMQ_USER", "RABBITMQ_PASS"]
        return all(key in config for key in rabbitmq_keys)
    
    def _test_rabbitmq_connection(self, config: Dict[str, str]) -> bool:
        """RabbitMQ接続テスト"""
        try:
            import pika
            connection_params = pika.ConnectionParameters(
                host=config.get("RABBITMQ_HOST", "localhost"),
                port=int(config.get("RABBITMQ_PORT", "5672")),
                credentials=pika.PlainCredentials(
                    config.get("RABBITMQ_USER", "guest"),
                    config.get("RABBITMQ_PASS", "guest")
                )
            )
            connection = pika.BlockingConnection(connection_params)
            connection.close()
            return True
        except Exception:
            return False

if __name__ == "__main__":
    validator = ConfigValidator()
    
    # 検証実行
    print("🔧 設定検証開始...")
    result = validator.auto_fix_config()
    
    # レポート生成
    report = validator.generate_config_report()
    print(report)
    
    if result.fixed_issues:
        print("\n🛠️ 自動修正された項目:")
        for fix in result.fixed_issues:
            print(f"  - {fix}")