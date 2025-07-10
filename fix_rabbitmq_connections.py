#!/usr/bin/env python3
"""
Fix common RabbitMQ connection issues in Elders Guild system
"""
import sys
import subprocess
import time
from pathlib import Path
import pika

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def ensure_rabbitmq_running():
    """Ensure RabbitMQ service is running"""
    print("1️⃣ Checking RabbitMQ service...")
    
    try:
        # Check if service is active
        result = subprocess.run(['systemctl', 'is-active', 'rabbitmq-server'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip() != 'active':
            print("  ⚠️ RabbitMQ is not active. Starting service...")
            subprocess.run(['sudo', 'systemctl', 'start', 'rabbitmq-server'], check=True)
            time.sleep(5)  # Wait for service to start
            print("  ✅ RabbitMQ service started")
        else:
            print("  ✅ RabbitMQ service is already running")
        
        return True
    except Exception as e:
        print(f"  ❌ Failed to ensure RabbitMQ service: {e}")
        return False

def create_required_queues():
    """Create all required queues for Elders Guild"""
    print("\n2️⃣ Creating required queues...")
    
    required_queues = [
        # Core queues
        ('ai_tasks', True),
        ('ai_results', True),
        ('ai_pm', True),
        ('ai_dialog', True),
        ('ai_todo', True),
        ('ai_command', True),
        ('ai_error', True),
        # Slack queues
        ('ai_slack_events', True),
        ('ai_slack_messages', True),
        ('ai_slack_pm_events', True),
        ('ai_slack_pm_messages', True),
        # Legacy queues for compatibility
        ('task_queue', True),
        ('result_queue', True),
        ('pm_queue', True)
    ]
    
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost')
        )
        channel = connection.channel()
        
        for queue_name, durable in required_queues:
            try:
                channel.queue_declare(queue=queue_name, durable=durable)
                print(f"  ✅ Queue '{queue_name}' created/verified")
            except Exception as e:
                print(f"  ❌ Failed to create queue '{queue_name}': {e}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to connect to RabbitMQ: {e}")
        return False

def update_worker_configs():
    """Update worker configurations to use correct connection parameters"""
    print("\n3️⃣ Updating worker configurations...")
    
    # Check if .env file exists
    env_file = PROJECT_ROOT / '.env'
    if not env_file.exists():
        print("  ⚠️ .env file not found. Creating with RabbitMQ defaults...")
        
        rabbitmq_config = """
# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
"""
        
        with open(env_file, 'a') as f:
            f.write(rabbitmq_config)
        
        print("  ✅ Added RabbitMQ configuration to .env file")
    else:
        # Check if RabbitMQ config exists in .env
        content = env_file.read_text()
        if 'RABBITMQ_HOST' not in content:
            print("  ⚠️ RabbitMQ configuration missing from .env. Adding...")
            
            rabbitmq_config = """
# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
"""
            
            with open(env_file, 'a') as f:
                f.write(rabbitmq_config)
            
            print("  ✅ Added RabbitMQ configuration to .env file")
        else:
            print("  ✅ RabbitMQ configuration already exists in .env")
    
    return True

def restart_workers():
    """Restart all workers to apply fixes"""
    print("\n4️⃣ Restarting workers...")
    
    worker_scripts = [
        'workers/enhanced_task_worker.py',
        'workers/simple_task_worker.py',
        'workers/intelligent_pm_worker_simple.py',
        'workers/async_result_worker_simple.py'
    ]
    
    # First, stop existing workers
    print("  Stopping existing workers...")
    for script in worker_scripts:
        subprocess.run(['pkill', '-f', script], capture_output=True)
    
    time.sleep(2)  # Wait for processes to stop
    
    # Start workers
    print("  Starting workers...")
    started = 0
    for script in worker_scripts:
        script_path = PROJECT_ROOT / script
        if script_path.exists():
            try:
                subprocess.Popen(['python3', str(script_path)], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                print(f"  ✅ Started {script}")
                started += 1
                time.sleep(1)  # Small delay between starts
            except Exception as e:
                print(f"  ❌ Failed to start {script}: {e}")
        else:
            print(f"  ⚠️ Script not found: {script}")
    
    print(f"  Started {started} workers")
    return started > 0

def verify_connections():
    """Verify all connections are working"""
    print("\n5️⃣ Verifying connections...")
    
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost')
        )
        channel = connection.channel()
        
        # Check main queues
        active_queues = []
        for queue in ['ai_tasks', 'ai_pm', 'ai_results']:
            try:
                method = channel.queue_declare(queue=queue, durable=True, passive=True)
                if method.method.consumer_count > 0:
                    active_queues.append(queue)
            except:
                pass
        
        connection.close()
        
        if active_queues:
            print(f"  ✅ Active queues with consumers: {', '.join(active_queues)}")
            return True
        else:
            print("  ⚠️ No active consumers found on queues")
            return False
            
    except Exception as e:
        print(f"  ❌ Connection verification failed: {e}")
        return False

def main():
    """Main function to fix RabbitMQ connection issues"""
    print("🔧 Elders Guild RabbitMQ Connection Fixer")
    print("=" * 50)
    
    success = True
    
    # Step 1: Ensure RabbitMQ is running
    if not ensure_rabbitmq_running():
        success = False
    
    # Step 2: Create required queues
    if not create_required_queues():
        success = False
    
    # Step 3: Update configurations
    if not update_worker_configs():
        success = False
    
    # Step 4: Restart workers
    if not restart_workers():
        success = False
    
    # Step 5: Verify connections
    time.sleep(5)  # Wait for workers to connect
    if not verify_connections():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ RabbitMQ connection issues resolved successfully!")
        print("📝 All workers should now be able to connect to RabbitMQ")
    else:
        print("⚠️ Some issues could not be resolved automatically")
        print("📝 Please check the logs for more details")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())