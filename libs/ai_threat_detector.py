#!/usr/bin/env python3
"""
AI Threat Detection System
"""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


class AIThreatDetector:
    def __init__(self):
        self.threat_patterns = [
            r"rm\s+-rf\s+/",
            r"chmod\s+777",
            r"passwd.*root",
            r"sudo\s+su\s+-",
            r"eval\(",
            r"exec\(",
            r"system\(",
            r"__import__\(",
        ]
        self.suspicious_activities = []

    def scan_code(self, file_path):
        """コードスキャン"""
        threats_found = []

        try:
            with open(file_path, "r") as f:
                content = f.read()

            for pattern in self.threat_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    threats_found.append(
                        {
                            "pattern": pattern,
                            "matches": matches,
                            "severity": (
                                "high" if pattern.startswith("rm") else "medium"
                            ),
                        }
                    )

        except Exception as e:
            return {"error": str(e)}

        return {
            "file": str(file_path),
            "threats_found": len(threats_found),
            "details": threats_found,
        }

    def monitor_process_activity(self):
        """プロセス監視"""
        try:
            import psutil

            suspicious_processes = []
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = " ".join(proc.info["cmdline"] or [])

                    # 怪しいコマンドパターンチェック
                    for pattern in self.threat_patterns:
                        if re.search(pattern, cmdline, re.IGNORECASE):
                            suspicious_processes.append(
                                {
                                    "pid": proc.info["pid"],
                                    "name": proc.info["name"],
                                    "cmdline": cmdline,
                                    "threat_pattern": pattern,
                                }
                            )

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return {
                "scan_time": datetime.now().isoformat(),
                "suspicious_processes": len(suspicious_processes),
                "details": suspicious_processes,
            }

        except ImportError:
            return {"status": "process monitoring unavailable"}

    def generate_security_report(self):
        """セキュリティレポート生成"""
        process_scan = self.monitor_process_activity()

        report = {
            "report_time": datetime.now().isoformat(),
            "security_status": (
                "secure"
                if process_scan.get("suspicious_processes", 0) == 0
                else "threats_detected"
            ),
            "process_scan": process_scan,
            "recommendations": [
                "定期的なコードスキャンを実施",
                "プロセス監視を継続",
                "セキュリティパッチの適用確認",
            ],
        }

        return report


# ゼロトラスト認証システム
class ZeroTrustAuth:
    def __init__(self):
        self.verified_entities = {}
        self.access_logs = []

    def verify_entity(self, entity_id, credentials):
        """エンティティ検証"""
        # ハッシュベース検証（デモ）
        credential_hash = hashlib.sha256(credentials.encode()).hexdigest()

        verification_result = {
            "entity_id": entity_id,
            "verified": True,  # デモでは常にTrue
            "verification_time": datetime.now().isoformat(),
            "access_level": "authenticated",
        }

        self.verified_entities[entity_id] = verification_result
        self.access_logs.append(verification_result)

        return verification_result

    def check_access_permission(self, entity_id, resource):
        """アクセス権限チェック"""
        if entity_id not in self.verified_entities:
            return {"access": "denied", "reason": "not_verified"}

        # 基本的なアクセス制御
        return {
            "access": "granted",
            "entity_id": entity_id,
            "resource": resource,
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    # 脅威検知デモ
    detector = AIThreatDetector()
    security_report = detector.generate_security_report()
    print("🛡️ Security Report:")
    print(json.dumps(security_report, indent=2))

    # ゼロトラスト認証デモ
    auth = ZeroTrustAuth()
    verification = auth.verify_entity("elder_system", "secure_credentials")
    print("\n🔐 Authentication:")
    print(json.dumps(verification, indent=2))
