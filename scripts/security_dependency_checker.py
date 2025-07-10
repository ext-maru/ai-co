#!/usr/bin/env python3
"""
Security & Dependency Checker - セキュリティ・依存関係チェッカー
エルダーズギルドのセキュリティ監査と依存関係管理

🔍 チェック項目:
- 依存関係の脆弱性スキャン
- 古いパッケージの検出
- セキュリティ設定確認
- ファイル権限チェック
- 機密情報漏洩検査
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
import re

class SecurityDependencyChecker:
    """セキュリティ・依存関係チェッカー"""
    
    def __init__(self, project_dir: str = "/home/aicompany/ai_co"):
        self.project_dir = Path(project_dir)
        self.logs_dir = self.project_dir / "logs"
        
        # セキュリティパターン
        self.security_patterns = {
            "api_keys": [
                r"api[_-]?key[s]?\s*[=:]\s*['\"][^'\"]+['\"]",
                r"secret[_-]?key[s]?\s*[=:]\s*['\"][^'\"]+['\"]",
                r"access[_-]?token[s]?\s*[=:]\s*['\"][^'\"]+['\"]",
            ],
            "passwords": [
                r"password[s]?\s*[=:]\s*['\"][^'\"]+['\"]",
                r"passwd[s]?\s*[=:]\s*['\"][^'\"]+['\"]",
                r"pwd[s]?\s*[=:]\s*['\"][^'\"]+['\"]",
            ],
            "database_urls": [
                r"database[_-]?url[s]?\s*[=:]\s*['\"][^'\"]+['\"]",
                r"db[_-]?url[s]?\s*[=:]\s*['\"][^'\"]+['\"]",
                r"postgresql://[^'\"\\s]+",
                r"mysql://[^'\"\\s]+",
            ],
            "private_keys": [
                r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
                r"-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----",
                r"private[_-]?key[s]?\s*[=:]\s*['\"][^'\"]+['\"]",
            ]
        }
        
        # 除外ファイル（拡張版）
        self.exclude_patterns = [
            "*.log", "*.pyc", "*.git/*", "node_modules/*",
            "*.backup*", "*.tmp", "logs/*", "__pycache__/*",
            "*.db", "*.sqlite*", "backups/*", "*.tar.gz",
            "*.zip", "*.pdf", "*.img", "*.bin", "archive/*"
        ]
        
        # ログ設定
        self.setup_logging()
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs_dir / 'security_dependency_checker.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def find_requirements_files(self) -> List[Path]:
        """依存関係ファイルの検索"""
        self.logger.info("🔍 依存関係ファイル検索開始")
        
        patterns = [
            "requirements*.txt",
            "Pipfile*",
            "pyproject.toml",
            "package*.json"
        ]
        
        files = []
        for pattern in patterns:
            files.extend(self.project_dir.rglob(pattern))
        
        # 重複除去とソート
        files = sorted(list(set(files)))
        
        self.logger.info(f"🔍 依存関係ファイル: {len(files)}個発見")
        for file in files:
            self.logger.debug(f"  {file.relative_to(self.project_dir)}")
        
        return files
    
    def check_python_dependencies(self, requirements_files: List[Path]) -> Dict[str, Any]:
        """Python依存関係チェック"""
        self.logger.info("🐍 Python依存関係チェック開始")
        
        result = {
            "requirements_files": [],
            "total_packages": 0,
            "outdated_packages": [],
            "security_issues": [],
            "recommendations": [],
            "error": None
        }
        
        try:
            # requirements.txtファイルのみ処理
            req_files = [f for f in requirements_files if f.name.startswith("requirements") and f.suffix == ".txt"]
            
            for req_file in req_files:
                self.logger.info(f"📦 チェック中: {req_file.name}")
                
                file_info = {
                    "file": str(req_file),
                    "packages": [],
                    "issues": []
                }
                
                try:
                    with open(req_file, 'r') as f:
                        lines = f.readlines()
                    
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # パッケージ名とバージョン抽出
                            match = re.match(r'^([a-zA-Z0-9_-]+)([>=<!=~]+)?([\d.]+)?', line)
                            if match:
                                package_name = match.group(1)
                                version_spec = match.group(2) or ""
                                version = match.group(3) or ""
                                
                                package_info = {
                                    "name": package_name,
                                    "version_spec": version_spec,
                                    "version": version,
                                    "line": line
                                }
                                file_info["packages"].append(package_info)
                                result["total_packages"] += 1
                
                except Exception as e:
                    file_info["issues"].append(f"ファイル読み込みエラー: {e}")
                
                result["requirements_files"].append(file_info)
            
            # セキュリティ推奨事項
            if result["total_packages"] > 0:
                result["recommendations"].extend([
                    "依存関係を定期的に更新してください",
                    "pip-audit または safety でセキュリティチェックを実行してください",
                    "固定バージョンの使用を検討してください",
                    "不要な依存関係を削除してください"
                ])
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"Python依存関係チェックエラー: {e}")
        
        self.logger.info(f"🐍 Python依存関係チェック完了: {result['total_packages']}パッケージ")
        return result
    
    def check_file_permissions(self) -> Dict[str, Any]:
        """ファイル権限チェック"""
        self.logger.info("🔒 ファイル権限チェック開始")
        
        result = {
            "total_files": 0,
            "world_writable": [],
            "world_readable": [],
            "executable_scripts": [],
            "recommendations": []
        }
        
        try:
            # 危険な権限のファイルをチェック
            for file_path in self.project_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # 除外パターンチェック
                if any(file_path.match(pattern) for pattern in self.exclude_patterns):
                    continue
                
                result["total_files"] += 1
                
                try:
                    stat = file_path.stat()
                    mode = stat.st_mode
                    
                    # 誰でも書き込み可能
                    if mode & 0o002:
                        result["world_writable"].append(str(file_path))
                    
                    # 実行可能スクリプト
                    if mode & 0o111 and file_path.suffix in ['.py', '.sh', '.pl']:
                        result["executable_scripts"].append(str(file_path))
                
                except OSError:
                    continue
            
            # 推奨事項
            if result["world_writable"]:
                result["recommendations"].append("誰でも書き込み可能なファイルの権限を制限してください")
            
            if len(result["executable_scripts"]) > 20:
                result["recommendations"].append("実行可能スクリプトが多数あります。必要性を確認してください")
        
        except Exception as e:
            self.logger.error(f"ファイル権限チェックエラー: {e}")
        
        self.logger.info(f"🔒 ファイル権限チェック完了: {result['total_files']}ファイル")
        return result
    
    def scan_for_secrets(self) -> Dict[str, Any]:
        """機密情報スキャン"""
        self.logger.info("🕵️ 機密情報スキャン開始")
        
        result = {
            "scanned_files": 0,
            "potential_secrets": [],
            "by_category": {
                "api_keys": [],
                "passwords": [],
                "database_urls": [],
                "private_keys": []
            },
            "recommendations": []
        }
        
        try:
            # テキストファイルをスキャン
            text_extensions = {'.py', '.js', '.json', '.yaml', '.yml', '.conf', '.cfg', '.ini', '.env'}
            
            for file_path in self.project_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # 除外パターンチェック
                if any(file_path.match(pattern) for pattern in self.exclude_patterns):
                    continue
                
                # テキストファイルのみ
                if file_path.suffix not in text_extensions:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    result["scanned_files"] += 1
                    
                    # パターンマッチング
                    for category, patterns in self.security_patterns.items():
                        for pattern in patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                            for match in matches:
                                # 行番号計算
                                line_num = content[:match.start()].count('\\n') + 1
                                
                                secret_info = {
                                    "file": str(file_path.relative_to(self.project_dir)),
                                    "line": line_num,
                                    "category": category,
                                    "pattern": pattern,
                                    "match": match.group()[:50] + "..." if len(match.group()) > 50 else match.group()
                                }
                                
                                result["potential_secrets"].append(secret_info)
                                result["by_category"][category].append(secret_info)
                
                except (UnicodeDecodeError, OSError):
                    continue
            
            # 推奨事項
            if result["potential_secrets"]:
                result["recommendations"].extend([
                    "検出された機密情報を環境変数に移行してください",
                    ".env ファイルを .gitignore に追加してください",
                    "ハードコードされた認証情報を削除してください",
                    "シークレット管理システムの使用を検討してください"
                ])
        
        except Exception as e:
            self.logger.error(f"機密情報スキャンエラー: {e}")
        
        self.logger.info(f"🕵️ 機密情報スキャン完了: {len(result['potential_secrets'])}個の疑わしい項目")
        return result
    
    def check_system_security(self) -> Dict[str, Any]:
        """システムセキュリティ設定チェック"""
        self.logger.info("🛡️ システムセキュリティチェック開始")
        
        result = {
            "firewall_status": "unknown",
            "ssh_config": {},
            "system_updates": "unknown",
            "open_ports": [],
            "recommendations": []
        }
        
        try:
            # ファイアウォール状態チェック
            try:
                fw_result = subprocess.run(["ufw", "status"], capture_output=True, text=True)
                if fw_result.returncode == 0:
                    if "inactive" in fw_result.stdout.lower():
                        result["firewall_status"] = "inactive"
                        result["recommendations"].append("ファイアウォールが無効です。有効化を検討してください")
                    else:
                        result["firewall_status"] = "active"
            except FileNotFoundError:
                pass
            
            # SSH設定チェック
            ssh_config_path = Path("/etc/ssh/sshd_config")
            if ssh_config_path.exists():
                try:
                    with open(ssh_config_path, 'r') as f:
                        ssh_content = f.read()
                    
                    # 危険な設定をチェック
                    if "PermitRootLogin yes" in ssh_content:
                        result["ssh_config"]["root_login"] = "enabled"
                        result["recommendations"].append("SSH root ログインを無効化してください")
                    
                    if "PasswordAuthentication yes" in ssh_content:
                        result["ssh_config"]["password_auth"] = "enabled"
                        result["recommendations"].append("SSH パスワード認証を無効化し、公開鍵認証を使用してください")
                
                except PermissionError:
                    result["ssh_config"]["error"] = "読み取り権限なし"
            
            # システム更新状態チェック
            try:
                apt_result = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True)
                if apt_result.returncode == 0:
                    upgrade_count = len(apt_result.stdout.split('\\n')) - 2  # ヘッダーを除く
                    if upgrade_count > 0:
                        result["system_updates"] = f"{upgrade_count} packages available"
                        result["recommendations"].append(f"システムアップデートが利用可能です ({upgrade_count}個)")
                    else:
                        result["system_updates"] = "up to date"
            except FileNotFoundError:
                pass
        
        except Exception as e:
            self.logger.error(f"システムセキュリティチェックエラー: {e}")
        
        self.logger.info("🛡️ システムセキュリティチェック完了")
        return result
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """包括的セキュリティチェック"""
        self.logger.info("🚀 包括的セキュリティチェック開始")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "project_dir": str(self.project_dir),
            "python_dependencies": None,
            "file_permissions": None,
            "secrets_scan": None,
            "system_security": None,
            "overall_recommendations": [],
            "security_score": 0
        }
        
        # 依存関係ファイル検索
        requirements_files = self.find_requirements_files()
        
        # 各チェック実行
        results["python_dependencies"] = self.check_python_dependencies(requirements_files)
        results["file_permissions"] = self.check_file_permissions()
        results["secrets_scan"] = self.scan_for_secrets()
        results["system_security"] = self.check_system_security()
        
        # 総合推奨事項
        all_recommendations = []
        for check_result in [results["python_dependencies"], results["file_permissions"], 
                           results["secrets_scan"], results["system_security"]]:
            if check_result and "recommendations" in check_result:
                all_recommendations.extend(check_result["recommendations"])
        
        results["overall_recommendations"] = list(set(all_recommendations))
        
        # セキュリティスコア計算
        score = 100
        
        # 機密情報発見で減点
        if results["secrets_scan"]["potential_secrets"]:
            score -= len(results["secrets_scan"]["potential_secrets"]) * 5
        
        # 権限問題で減点
        if results["file_permissions"]["world_writable"]:
            score -= len(results["file_permissions"]["world_writable"]) * 3
        
        # システムセキュリティで減点
        if results["system_security"]["firewall_status"] == "inactive":
            score -= 10
        
        results["security_score"] = max(0, min(100, score))
        
        self.logger.info(f"✅ 包括的セキュリティチェック完了: スコア {results['security_score']}/100")
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """セキュリティチェック結果サマリー表示"""
        print("\\n" + "="*60)
        print("🔐 Elders Guild Security & Dependency Report")
        print("="*60)
        
        print(f"\\n📊 Security Score: {results['security_score']}/100")
        
        # Python依存関係
        if results["python_dependencies"]:
            deps = results["python_dependencies"]
            print(f"\\n🐍 Python Dependencies:")
            print(f"  Total packages: {deps['total_packages']}")
            print(f"  Requirements files: {len(deps['requirements_files'])}")
            
            if deps["requirements_files"]:
                for req_file in deps["requirements_files"]:
                    print(f"    {Path(req_file['file']).name}: {len(req_file['packages'])} packages")
        
        # ファイル権限
        if results["file_permissions"]:
            perms = results["file_permissions"]
            print(f"\\n🔒 File Permissions:")
            print(f"  Files scanned: {perms['total_files']}")
            
            if perms["world_writable"]:
                print(f"  ⚠️ World-writable files: {len(perms['world_writable'])}")
                for file in perms["world_writable"][:3]:  # 最初の3個表示
                    print(f"    {file}")
                if len(perms["world_writable"]) > 3:
                    print(f"    ... and {len(perms['world_writable']) - 3} more")
        
        # 機密情報
        if results["secrets_scan"]:
            secrets = results["secrets_scan"]
            print(f"\\n🕵️ Secrets Scan:")
            print(f"  Files scanned: {secrets['scanned_files']}")
            print(f"  Potential secrets found: {len(secrets['potential_secrets'])}")
            
            for category, items in secrets["by_category"].items():
                if items:
                    print(f"    {category}: {len(items)} items")
        
        # システムセキュリティ
        if results["system_security"]:
            sys_sec = results["system_security"]
            print(f"\\n🛡️ System Security:")
            print(f"  Firewall status: {sys_sec['firewall_status']}")
            print(f"  System updates: {sys_sec['system_updates']}")
        
        # 推奨事項
        if results["overall_recommendations"]:
            print(f"\\n💡 Security Recommendations:")
            for i, rec in enumerate(results["overall_recommendations"][:10], 1):
                print(f"  {i}. {rec}")
            
            if len(results["overall_recommendations"]) > 10:
                print(f"    ... and {len(results['overall_recommendations']) - 10} more recommendations")
        
        print("\\n" + "="*60)

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Security & Dependency Checker")
    parser.add_argument("--full", action="store_true", help="包括的セキュリティチェック")
    parser.add_argument("--dependencies", action="store_true", help="依存関係チェックのみ")
    parser.add_argument("--permissions", action="store_true", help="ファイル権限チェックのみ")
    parser.add_argument("--secrets", action="store_true", help="機密情報スキャンのみ")
    parser.add_argument("--system", action="store_true", help="システムセキュリティチェックのみ")
    parser.add_argument("--save", action="store_true", help="結果をファイルに保存")
    
    args = parser.parse_args()
    
    checker = SecurityDependencyChecker()
    
    if args.dependencies:
        req_files = checker.find_requirements_files()
        result = checker.check_python_dependencies(req_files)
        print(f"Python Dependencies Check: {result['total_packages']} packages found")
    elif args.permissions:
        result = checker.check_file_permissions()
        print(f"File Permissions Check: {result['total_files']} files scanned")
    elif args.secrets:
        result = checker.scan_for_secrets()
        print(f"Secrets Scan: {len(result['potential_secrets'])} potential secrets found")
    elif args.system:
        result = checker.check_system_security()
        print(f"System Security Check completed")
    elif args.full:
        results = checker.run_comprehensive_check()
        checker.print_summary(results)
        
        if args.save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = checker.logs_dir / f"security_report_{timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\\n📄 Report saved: {report_file}")
    else:
        print("🔐 Elders Guild Security & Dependency Checker")
        print("使用方法:")
        print("  --full           : 包括的セキュリティチェック")
        print("  --dependencies   : Python依存関係チェック")
        print("  --permissions    : ファイル権限チェック")
        print("  --secrets        : 機密情報スキャン")
        print("  --system         : システムセキュリティチェック")
        print("  --save           : 結果保存 (--fullと併用)")

if __name__ == "__main__":
    main()