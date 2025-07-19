#!/usr/bin/env python3
"""
Automated Security Audit System
"""
import subprocess
import json
from datetime import datetime
from pathlib import Path


class SecurityAuditor:
    def __init__(self):
        self.audit_results = {}

    def audit_file_permissions(self):
        """ファイル権限監査"""
        try:
            # 重要ファイルの権限チェック
            important_files = [
                "/etc/passwd",
                "/etc/shadow",
                "config/",
                "scripts/",
                ".env",
            ]

            permission_issues = []

            for file_path in important_files:
                if Path(file_path).exists():
                    # ls -la でファイル権限取得
                    result = subprocess.run(
                        ["ls", "-la", file_path], capture_output=True, text=True
                    )

                    if "777" in result.stdout:
                        permission_issues.append(
                            {
                                "file": file_path,
                                "issue": "overly_permissive",
                                "permissions": "777",
                            }
                        )

            return {
                "audit_type": "file_permissions",
                "issues_found": len(permission_issues),
                "details": permission_issues,
            }

        except Exception as e:
            return {"error": str(e)}

    def audit_network_security(self):
        """ネットワークセキュリティ監査"""
        try:
            # 開いているポートチェック
            result = subprocess.run(
                ["netstat", "-tuln"], capture_output=True, text=True
            )

            open_ports = []
            lines = result.stdout.split("\n")

            for line in lines:
                if "LISTEN" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        port_info = parts[3]
                        open_ports.append(port_info)

            return {
                "audit_type": "network_security",
                "open_ports": len(open_ports),
                "details": open_ports[:10],  # 最初の10個
            }

        except Exception as e:
            return {"error": str(e)}

    def generate_full_audit_report(self):
        """完全監査レポート生成"""
        file_audit = self.audit_file_permissions()
        network_audit = self.audit_network_security()

        report = {
            "audit_timestamp": datetime.now().isoformat(),
            "audits_performed": [file_audit, network_audit],
            "overall_security_score": 85,  # デモ値
            "recommendations": [
                "ファイル権限の最小権限原則適用",
                "不要ポートの閉鎖検討",
                "定期的なセキュリティパッチ適用",
            ],
        }

        return report


if __name__ == "__main__":
    auditor = SecurityAuditor()
    audit_report = auditor.generate_full_audit_report()
    print("🔍 Security Audit Report:")
    print(json.dumps(audit_report, indent=2))
