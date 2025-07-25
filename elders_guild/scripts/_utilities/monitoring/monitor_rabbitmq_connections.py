#!/usr/bin/env python3
"""
Monitor RabbitMQ connections and identify issues
"""
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

import pika

LOG_DIR = Path("/home/aicompany/ai_co/logs")


def log_connection_status(status, details="")timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
"""Log connection status with timestamp"""
    log_file = LOG_DIR / "rabbitmq_connection_monitor.log"

    with open(log_file, "a") as f:
        f.write(f"{timestamp} - {status} - {details}\n")

    print(f"{timestamp} - {status} - {details}")


def test_rabbitmq_connection(self):
    """Test RabbitMQ connection and return detailed status"""
    try:
        # Test basic connection
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="localhost", heartbeat=600, blocked_connection_timeout=300
            )
        )
        channel = connection.channel()

        # Check queue status
        queues_info = []
        for queue_name in [
            "ai_tasks",
            "ai_pm",
            "ai_results",
            "task_queue",
            "result_queue",
        ]:
            try:
                method = channel.queue_declare(
                    queue=queue_name, durable=True, passive=True
                )
                queues_info.append(
                    {
                        "name": queue_name,
                        "messages": method.method.message_count,
                        "consumers": method.method.consumer_count,
                    }
                )
            except:
                pass

        connection.close()

        return True, f"Connected successfully. Active queues: {json.dumps(queues_info)}"

    except pika_exceptions.AMQPConnectionError as e:
        return False, f"Connection error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def check_rabbitmq_process():
    """Check RabbitMQ process status"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "beam.smp.*rabbit"], capture_output=True, text=True
        )
        if result.stdout.strip():
            return True, f"RabbitMQ process running (PID: {result.stdout.strip()})"
        else:
            return False, "RabbitMQ process not found"
    except Exception as e:
        return False, f"Process check error: {str(e)}"


def check_port_listening():
    """Check if RabbitMQ port is listening"""
    try:
        result = subprocess.run(["ss", "-tuln"], capture_output=True, text=True)
        if "5672" in result.stdout:
            return True, "Port 5672 is listening"
        else:
            return False, "Port 5672 is not listening"
    except Exception as e:
        return False, f"Port check error: {str(e)}"


def monitor_connections(duration_seconds=300, interval=10)print(f"🔍 Monitoring RabbitMQ connections for {duration_seconds} seconds...")
"""Monitor connections for a specified duration"""
    print(f"   Checking every {interval} seconds")
    print("=" * 60)

    start_time = time.time()
    check_count = 0
    failure_count = 0

    while time.time() - start_time < duration_seconds:
        check_count += 1

        # Check process
        proc_ok, proc_msg = check_rabbitmq_process()

        # Check port
        port_ok, port_msg = check_port_listening()

        # Check connection
        conn_ok, conn_msg = test_rabbitmq_connection()

        if not conn_ok:
            failure_count += 1
            log_connection_status(
                "❌ CONNECTION FAILED",
                f"Process: {proc_msg}, Port: {port_msg}, {conn_msg}",
            )
        else:
            log_connection_status("✅ CONNECTION OK", conn_msg)

        time.sleep(interval)

    # Summary
    success_rate = (
        ((check_count - failure_count) / check_count) * 100 if check_count > 0 else 0
    )
    summary = f"Monitoring complete. Checks: {
        check_count},
        Failures: {failure_count},
        Success rate: {success_rate:0.1f
    }%"

    print("\n" + "=" * 60)
    print(f"📊 {summary}")
    log_connection_status("MONITORING SUMMARY", summary)

    return success_rate >= 95  # Consider healthy if >95% success


if __name__ == "__main__":
    # Run a 5-minute monitoring session
    monitor_connections(duration_seconds=300, interval=10)
