#!/usr/bin/env python3
"""Diagnose RabbitMQ connection issues"""
import socket
import subprocess
import sys
from pathlib import Path

import pika


def check_rabbitmq_service():
    """Check if RabbitMQ service is running"""
    print("1️⃣ Checking RabbitMQ service status...")
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "rabbitmq-server"],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip() == "active":
            print("✅ RabbitMQ service is active")
            return True
        else:
            print(f"❌ RabbitMQ service status: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"⚠️ Could not check service status: {e}")
        return None


def check_port_connectivity():
    """Check if port 5672 is accessible"""
    print("\n2️⃣ Checking port connectivity...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(("localhost", 5672))
        sock.close()

        if result == 0:
            print("✅ Port 5672 is accessible")
            return True
        else:
            print(f"❌ Port 5672 is not accessible (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Port check failed: {e}")
        return False


def test_connection_variations():
    """Test different connection parameter variations"""
    print("\n3️⃣ Testing connection variations...")

    variations = [
        {"name": "Default (no params)", "params": {}},
        {
            "name": "Localhost with heartbeat",
            "params": {
                "host": "localhost",
                "heartbeat": 600,
                "blocked_connection_timeout": 300,
            },
        },
        {
            "name": "127.0.0.1 with heartbeat",
            "params": {
                "host": "127.0.0.1",
                "heartbeat": 600,
                "blocked_connection_timeout": 300,
            },
        },
        {
            "name": "With credentials",
            "params": {
                "host": "localhost",
                "credentials": pika.PlainCredentials("guest", "guest"),
            },
        },
    ]

    for var in variations:
        try:
            print(f"\n  Testing: {var['name']}")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(**var["params"])
            )
            print(f"  ✅ Success with {var['name']}")
            connection.close()
        except Exception as e:
            print(f"  ❌ Failed with {var['name']}: {str(e)[:100]}")


def check_permissions():
    """Check file permissions and user context"""
    print("\n4️⃣ Checking permissions and context...")
    print(
        f"  Current user: {subprocess.run(['whoami'], capture_output=True, text=True).stdout.strip()}"
    )
    print(
        f"  User groups: {subprocess.run(['groups'], capture_output=True, text=True).stdout.strip()}"
    )

    # Check if RabbitMQ directories are accessible
    rabbitmq_dirs = ["/var/lib/rabbitmq", "/var/log/rabbitmq"]
    for dir_path in rabbitmq_dirs:
        if Path(dir_path).exists():
            try:
                subprocess.run(
                    ["ls", "-la", dir_path], capture_output=True, check=False
                )
                print(f"  ✅ Can access {dir_path}")
            except:
                print(f"  ❌ Cannot access {dir_path}")


def check_env_variables():
    """Check environment variables that might affect connection"""
    print("\n5️⃣ Checking environment variables...")
    import os

    relevant_vars = ["RABBITMQ_HOST", "RABBITMQ_PORT", "RABBITMQ_USER", "RABBITMQ_PASS"]
    for var in relevant_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}: {value}")
        else:
            print(f"  {var}: Not set")


def main():
    """mainメソッド"""
    print("🔍 RabbitMQ Connection Diagnostics")
    print("=" * 50)

    check_rabbitmq_service()
    check_port_connectivity()
    test_connection_variations()
    check_permissions()
    check_env_variables()

    print("\n" + "=" * 50)
    print("📊 Diagnosis complete")


if __name__ == "__main__":
    main()
