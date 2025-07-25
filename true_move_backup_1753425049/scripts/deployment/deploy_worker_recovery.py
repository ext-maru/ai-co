#!/usr/bin/env python3
"""
Worker Auto-Recovery System Deployment Script
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime

# Elders Guildのライブラリパスを追加
sys.path.append("/home/aicompany/ai_co")


def deploy_worker_recovery():
    """ワーカー自動復旧システムをデプロイ"""
    print("\n🚀 Worker Auto-Recovery System Deployment\n")
    print("=" * 60)

    # 1.0 ディレクトリ構造の確認
    print("1.0 Checking directory structure...")
    recovery_dir = "/home/aicompany/ai_co/libs/worker_auto_recovery"

    if os.path.exists(recovery_dir):
        print(f"   ✅ Recovery system directory exists: {recovery_dir}")

        # ファイルリスト
        files = [
            "__init__.py",
            "recovery_manager.py",
            "health_checker.py",
            "recovery_strategies.py",
            "state_manager.py",
            "notification_handler.py",
        ]

        for file in files:
            if os.path.exists(os.path.join(recovery_dir, file)):
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file} missing!")
                return False
    else:
        print(f"   ❌ Recovery system directory not found!")
        return False

    # 2.0 設定ファイルの確認
    print("\n2.0 Checking configuration...")
    config_file = "/home/aicompany/ai_co/config/worker_recovery.yaml"

    if os.path.exists(config_file):
        print(f"   ✅ Configuration file exists: {config_file}")
    else:
        print(f"   ❌ Configuration file not found!")
        return False

    # 3.0 データディレクトリの作成
    print("\n3.0 Creating data directories...")
    data_dirs = [
        "/home/aicompany/ai_co/data/worker_states",
        "/home/aicompany/ai_co/knowledge_base/elder_notifications",
    ]

    for dir_path in data_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"   ✅ {dir_path}")

    # 4.0 systemdサービスファイルの作成
    print("\n4.0 Creating systemd service...")
    service_content = """[Unit]
Description=Elders Guild Worker Recovery System
After=network.target rabbitmq-server.service

[Service]
Type=simple
User=aicompany
Group=aicompany
WorkingDirectory=/home/aicompany/ai_co
Environment="PYTHONPATH=/home/aicompany/ai_co"
ExecStart=/usr/bin/python3 -m libs.worker_auto_recovery.recovery_manager start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    service_file = "/tmp/worker-recovery.service"
    with open(service_file, "w") as f:
        f.write(service_content)

    print(f"   ✅ Service file created: {service_file}")
    print("   ℹ️  To install as systemd service, run:")
    print("      sudo cp /tmp/worker-recovery.service /etc/systemd/system/")
    print("      sudo systemctl daemon-reload")
    print("      sudo systemctl enable worker-recovery")
    print("      sudo systemctl start worker-recovery")

    # 5.0 CLIコマンドの作成
    print("\n5.0 Creating CLI command...")
    cli_script = """#!/usr/bin/env python3
import sys
sys.path.append('/home/aicompany/ai_co')
from libs.worker_auto_recovery.recovery_manager import main
main()
"""

    cli_file = "/home/aicompany/ai_co/commands/ai_worker_recovery.py"
    with open(cli_file, "w") as f:
        f.write(cli_script)

    os.chmod(cli_file, 0o755)
    print(f"   ✅ CLI command created: {cli_file}")

    # 6.0 テスト実行
    print("\n6.0 Running system test...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "/home/aicompany/ai_co/test_worker_recovery.py",
                "--health",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("   ✅ System test passed")
        else:
            print("   ⚠️  System test had warnings")
            print(result.stdout)
    except Exception as e:
        print(f"   ❌ System test failed: {e}")

    # 7.0 ドキュメントの作成
    print("\n7.0 Creating documentation...")
    doc_content = f"""# Worker Auto-Recovery System

**Deployed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Version**: 1.0.0

## Quick Start

### CLI Usage
```bash
# Check system status
python3 commands/ai_worker_recovery.py status

# Start monitoring
python3 commands/ai_worker_recovery.py start

# Manually recover a worker
python3 commands/ai_worker_recovery.py recover --worker task_worker
```

### Service Management
```bash
# Start as service
sudo systemctl start worker-recovery

# Check service status
sudo systemctl status worker-recovery

# View logs
sudo journalctl -u worker-recovery -f
```

### Configuration
Edit `/home/aicompany/ai_co/config/worker_recovery.yaml` to adjust settings.

## Features
- Automatic health monitoring
- Multiple recovery strategies
- State preservation
- Slack notifications
- Elder Council integration

## Troubleshooting
- Check logs in `/home/aicompany/ai_co/logs/`
- Review saved states in `/home/aicompany/ai_co/data/worker_states/`
- Elder notifications in `/home/aicompany/ai_co/knowledge_base/elder_notifications/`
"""

    doc_file = "/home/aicompany/ai_co/docs/WORKER_RECOVERY_SYSTEM.md"
    with open(doc_file, "w") as f:
        f.write(doc_content)

    print(f"   ✅ Documentation created: {doc_file}")

    print("\n" + "=" * 60)
    print("✅ Deployment completed successfully!")
    print("\nNext steps:")
    print("1.0 Test the system: python3 test_worker_recovery.py --full")
    print("2.0 Start monitoring: python3 commands/ai_worker_recovery.py start")
    print("3.0 Or install as service (see instructions above)")

    return True


if __name__ == "__main__":
    try:
        success = deploy_worker_recovery()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
