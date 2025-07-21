#!/usr/bin/env python3
"""
Issue Lock Manager セキュリティ監査ツール
ファイルベースロックシステムの脆弱性分析と改善提案
"""

import os
import stat
import json
import hashlib
import hmac
import secrets
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging


class SecurityAuditReport:
    """セキュリティ監査レポート"""
    
    def __init__(self):
        self.vulnerabilities = []
        self.warnings = []
        self.recommendations = []
        self.passed_checks = []
        
    def add_vulnerability(self, severity: str, issue: str, details: str, mitigation: str):
        """脆弱性を追加"""
        self.vulnerabilities.append({
            'severity': severity,  # CRITICAL, HIGH, MEDIUM, LOW
            'issue': issue,
            'details': details,
            'mitigation': mitigation,
            'timestamp': datetime.now().isoformat()
        })
        
    def add_warning(self, issue: str, details: str):
        """警告を追加"""
        self.warnings.append({
            'issue': issue,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    def add_recommendation(self, category: str, recommendation: str):
        """推奨事項を追加"""
        self.recommendations.append({
            'category': category,
            'recommendation': recommendation
        })
        
    def add_passed_check(self, check: str):
        """合格したチェックを追加"""
        self.passed_checks.append(check)
        
    def get_severity_score(self) -> int:
        """深刻度スコアを計算（0-100、100が最も安全）"""
        severity_weights = {
            'CRITICAL': 25,
            'HIGH': 15,
            'MEDIUM': 10,
            'LOW': 5
        }
        
        total_deduction = 0
        for vuln in self.vulnerabilities:
            total_deduction += severity_weights.get(vuln['severity'], 0)
            
        return max(0, 100 - total_deduction)
        
    def to_markdown(self) -> str:
        """Markdown形式でレポートを生成"""
        report = "# Issue Lock Manager Security Audit Report\n\n"
        report += f"**Generated**: {datetime.now().isoformat()}\n"
        report += f"**Security Score**: {self.get_severity_score()}/100\n\n"
        
        if self.vulnerabilities:
            report += "## 🚨 Vulnerabilities Found\n\n"
            for vuln in sorted(self.vulnerabilities, key=lambda x: x['severity']):
                report += f"### [{vuln['severity']}] {vuln['issue']}\n"
                report += f"**Details**: {vuln['details']}\n"
                report += f"**Mitigation**: {vuln['mitigation']}\n\n"
                
        if self.warnings:
            report += "## ⚠️ Warnings\n\n"
            for warning in self.warnings:
                report += f"- **{warning['issue']}**: {warning['details']}\n"
                
        if self.passed_checks:
            report += "\n## ✅ Passed Checks\n\n"
            for check in self.passed_checks:
                report += f"- {check}\n"
                
        if self.recommendations:
            report += "\n## 💡 Recommendations\n\n"
            for rec in self.recommendations:
                report += f"### {rec['category']}\n{rec['recommendation']}\n\n"
                
        return report


class IssueLockSecurityAuditor:
    """Issue Lock Managerのセキュリティ監査"""
    
    def __init__(self, lock_dir: str = ".issue_locks"):
        self.lock_dir = Path(lock_dir)
        self.logger = logging.getLogger(__name__)
        
    def audit_file_permissions(self) -> List[Dict]:
        """ファイル権限の監査"""
        issues = []
        
        if not self.lock_dir.exists():
            return issues
            
        # ディレクトリ権限チェック
        dir_stat = os.stat(self.lock_dir)
        dir_mode = dir_stat.st_mode
        
        # World-writableチェック
        if dir_mode & stat.S_IWOTH:
            issues.append({
                'type': 'directory_world_writable',
                'severity': 'CRITICAL',
                'path': str(self.lock_dir),
                'mode': oct(dir_mode & 0o777)
            })
            
        # ロックファイルの権限チェック
        for lock_file in self.lock_dir.glob("*.lock"):
            file_stat = os.stat(lock_file)
            file_mode = file_stat.st_mode
            
            # Other-readableチェック
            if file_mode & stat.S_IROTH:
                issues.append({
                    'type': 'file_world_readable',
                    'severity': 'MEDIUM',
                    'path': str(lock_file),
                    'mode': oct(file_mode & 0o777)
                })
                
            # Other-writableチェック
            if file_mode & stat.S_IWOTH:
                issues.append({
                    'type': 'file_world_writable',
                    'severity': 'HIGH',
                    'path': str(lock_file),
                    'mode': oct(file_mode & 0o777)
                })
                
        return issues
        
    def audit_lock_file_integrity(self) -> List[Dict]:
        """ロックファイルの整合性監査"""
        issues = []
        
        for lock_file in self.lock_dir.glob("*.lock"):
            try:
                with open(lock_file, 'r') as f:
                    lock_data = json.load(f)
                    
                # 必須フィールドチェック
                required_fields = ['processor_id', 'locked_at', 'pid']
                missing_fields = [field for field in required_fields if field not in lock_data]
                
                if missing_fields:
                    issues.append({
                        'type': 'incomplete_lock_data',
                        'severity': 'MEDIUM',
                        'file': str(lock_file),
                        'missing_fields': missing_fields
                    })
                    
                # タイムスタンプの妥当性チェック
                if 'locked_at' in lock_data:
                    try:
                        locked_time = datetime.fromisoformat(lock_data['locked_at'])
                        age = datetime.now() - locked_time
                        
                        # 24時間以上古いロック
                        if age.total_seconds() > 86400:
                            issues.append({
                                'type': 'stale_lock',
                                'severity': 'LOW',
                                'file': str(lock_file),
                                'age_hours': age.total_seconds() / 3600
                            })
                    except ValueError:
                        issues.append({
                            'type': 'invalid_timestamp',
                            'severity': 'MEDIUM',
                            'file': str(lock_file),
                            'timestamp': lock_data.get('locked_at')
                        })
                        
            except json.JSONDecodeError:
                issues.append({
                    'type': 'corrupted_lock_file',
                    'severity': 'HIGH',
                    'file': str(lock_file)
                })
            except Exception as e:
                issues.append({
                    'type': 'lock_file_read_error',
                    'severity': 'MEDIUM',
                    'file': str(lock_file),
                    'error': str(e)
                })
                
        return issues
        
    def audit_race_conditions(self) -> List[Dict]:
        """潜在的なレースコンディションの監査"""
        warnings = []
        
        # テンポラリファイルの存在チェック
        temp_files = list(self.lock_dir.glob("*.tmp"))
        if temp_files:
            warnings.append({
                'type': 'orphaned_temp_files',
                'count': len(temp_files),
                'files': [str(f) for f in temp_files[:5]]  # 最初の5個
            })
            
        # 同一プロセッサーIDの重複チェック
        processor_counts = {}
        for lock_file in self.lock_dir.glob("*.lock"):
            try:
                with open(lock_file, 'r') as f:
                    lock_data = json.load(f)
                    processor_id = lock_data.get('processor_id', 'unknown')
                    processor_counts[processor_id] = processor_counts.get(processor_id, 0) + 1
            except:
                pass
                
        duplicates = {pid: count for pid, count in processor_counts.items() if count > 1}
        if duplicates:
            warnings.append({
                'type': 'duplicate_processor_ids',
                'duplicates': duplicates
            })
            
        return warnings
        
    def suggest_security_improvements(self) -> Dict[str, List[str]]:
        """セキュリティ改善提案"""
        improvements = {
            'file_permissions': [
                "Set lock directory permissions to 0700 (owner only)",
                "Set lock file permissions to 0600 (owner read/write only)",
                "Use umask(0077) before creating lock files"
            ],
            'data_integrity': [
                "Add HMAC signatures to lock files for tamper detection",
                "Include hostname and username in lock data",
                "Add file format version for compatibility"
            ],
            'race_condition_prevention': [
                "Use fcntl.flock() for additional file locking",
                "Implement double-check locking pattern",
                "Add random jitter to retry delays"
            ],
            'monitoring': [
                "Log all lock acquisitions and releases",
                "Implement lock acquisition metrics",
                "Add alerting for long-held locks"
            ],
            'cryptographic': [
                "Use secure random for processor IDs",
                "Encrypt sensitive data in lock files",
                "Implement lock file signing"
            ]
        }
        
        return improvements
        
    def generate_secure_lock_manager_code(self) -> str:
        """セキュアなロックマネージャーの実装例を生成"""
        return '''#!/usr/bin/env python3
"""
Secure File Lock Manager - セキュリティ強化版
"""

import os
import json
import fcntl
import hashlib
import hmac
import secrets
from pathlib import Path
from datetime import datetime


class SecureFileLockManager:
    """セキュリティ強化版ファイルロックマネージャー"""
    
    def __init__(self, lock_dir: str = ".secure_locks", secret_key: bytes = None):
        self.lock_dir = Path(lock_dir)
        self.secret_key = secret_key or secrets.token_bytes(32)
        
        # セキュアなディレクトリ作成
        old_umask = os.umask(0o077)  # 新規ファイルは0600
        try:
            self.lock_dir.mkdir(mode=0o700, exist_ok=True)
        finally:
            os.umask(old_umask)
            
    def _generate_hmac(self, data: dict) -> str:
        """データのHMACを生成"""
        json_data = json.dumps(data, sort_keys=True)
        return hmac.new(
            self.secret_key,
            json_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
    def acquire_lock(self, resource_id: int, processor_id: str) -> bool:
        """セキュアなロック取得"""
        lock_file = self.lock_dir / f"resource_{resource_id}.lock"
        temp_file = lock_file.with_suffix('.tmp')
        
        # ロックデータ作成
        lock_data = {
            'processor_id': processor_id,
            'locked_at': datetime.now().isoformat(),
            'pid': os.getpid(),
            'hostname': os.uname().nodename,
            'username': os.environ.get('USER', 'unknown'),
            'nonce': secrets.token_hex(16)
        }
        
        # HMAC追加
        lock_data['hmac'] = self._generate_hmac(lock_data)
        
        # セキュアな書き込み
        old_umask = os.umask(0o077)
        try:
            with open(temp_file, 'w') as f:
                # ファイルロックを取得
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                json.dump(lock_data, f)
                f.flush()
                os.fsync(f.fileno())
                
            # アトミックな移動
            temp_file.rename(lock_file)
            return True
            
        except (OSError, IOError):
            # ロック取得失敗
            if temp_file.exists():
                temp_file.unlink()
            return False
        finally:
            os.umask(old_umask)
            
    def verify_lock_integrity(self, resource_id: int) -> bool:
        """ロックファイルの整合性を検証"""
        lock_file = self.lock_dir / f"resource_{resource_id}.lock"
        
        if not lock_file.exists():
            return True  # ロックなし
            
        try:
            with open(lock_file, 'r') as f:
                lock_data = json.load(f)
                
            # HMAC検証
            stored_hmac = lock_data.pop('hmac', None)
            calculated_hmac = self._generate_hmac(lock_data)
            
            return stored_hmac == calculated_hmac
            
        except Exception:
            return False  # 検証失敗
'''
        
    def run_full_audit(self) -> SecurityAuditReport:
        """完全なセキュリティ監査を実行"""
        report = SecurityAuditReport()
        
        # ファイル権限監査
        permission_issues = self.audit_file_permissions()
        for issue in permission_issues:
            if issue['type'] == 'directory_world_writable':
                report.add_vulnerability(
                    'CRITICAL',
                    'World-writable lock directory',
                    f"Directory {issue['path']} has mode {issue['mode']}",
                    "Set directory permissions to 0700"
                )
            elif issue['type'] == 'file_world_readable':
                report.add_vulnerability(
                    'MEDIUM',
                    'World-readable lock file',
                    f"File {issue['path']} has mode {issue['mode']}",
                    "Set file permissions to 0600"
                )
            elif issue['type'] == 'file_world_writable':
                report.add_vulnerability(
                    'HIGH',
                    'World-writable lock file',
                    f"File {issue['path']} has mode {issue['mode']}",
                    "Set file permissions to 0600"
                )
        
        if not permission_issues:
            report.add_passed_check("File permissions audit")
            
        # ロックファイル整合性監査
        integrity_issues = self.audit_lock_file_integrity()
        for issue in integrity_issues:
            if issue['type'] == 'corrupted_lock_file':
                report.add_vulnerability(
                    'HIGH',
                    'Corrupted lock file',
                    f"File {issue['file']} is corrupted",
                    "Implement HMAC verification"
                )
            elif issue['type'] == 'stale_lock':
                report.add_warning(
                    'Stale lock detected',
                    f"Lock {issue['file']} is {issue['age_hours']:.1f} hours old"
                )
                
        if not integrity_issues:
            report.add_passed_check("Lock file integrity audit")
            
        # レースコンディション監査
        race_warnings = self.audit_race_conditions()
        for warning in race_warnings:
            if warning['type'] == 'orphaned_temp_files':
                report.add_warning(
                    'Orphaned temporary files',
                    f"Found {warning['count']} orphaned .tmp files"
                )
            elif warning['type'] == 'duplicate_processor_ids':
                report.add_warning(
                    'Duplicate processor IDs',
                    f"Processors with multiple locks: {warning['duplicates']}"
                )
                
        if not race_warnings:
            report.add_passed_check("Race condition audit")
            
        # セキュリティ改善提案
        improvements = self.suggest_security_improvements()
        for category, suggestions in improvements.items():
            report.add_recommendation(
                category.replace('_', ' ').title(),
                '\n'.join(f"- {s}" for s in suggestions)
            )
            
        return report


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Issue Lock Manager Security Audit")
    parser.add_argument(
        '--lock-dir',
        default='.issue_locks',
        help='Lock directory to audit'
    )
    parser.add_argument(
        '--output',
        default='security_audit_report.md',
        help='Output file for report'
    )
    parser.add_argument(
        '--generate-secure-code',
        action='store_true',
        help='Generate secure implementation example'
    )
    
    args = parser.parse_args()
    
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    auditor = IssueLockSecurityAuditor(args.lock_dir)
    
    if args.generate_secure_code:
        # セキュアな実装例を生成
        secure_code = auditor.generate_secure_lock_manager_code()
        output_file = 'secure_file_lock_manager.py'
        with open(output_file, 'w') as f:
            f.write(secure_code)
        print(f"Secure implementation generated: {output_file}")
        return
        
    # セキュリティ監査実行
    print(f"Running security audit on: {args.lock_dir}")
    report = auditor.run_full_audit()
    
    # レポート保存
    with open(args.output, 'w') as f:
        f.write(report.to_markdown())
        
    print(f"\nSecurity Score: {report.get_severity_score()}/100")
    print(f"Vulnerabilities: {len(report.vulnerabilities)}")
    print(f"Warnings: {len(report.warnings)}")
    print(f"Report saved to: {args.output}")
    
    # 深刻な脆弱性がある場合は終了コード1
    if any(v['severity'] == 'CRITICAL' for v in report.vulnerabilities):
        return 1
        
    return 0


if __name__ == "__main__":
    exit(main())