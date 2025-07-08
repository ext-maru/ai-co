#!/usr/bin/env python3
"""
Fix for ai-tasks command
"""

import subprocess
import sys
from pathlib import Path

def fix_ai_tasks():
    """Fix the ai-tasks command issue"""
    print("🔧 Checking ai-tasks command...")
    
    # Find the ai-tasks script
    result = subprocess.run(['which', 'ai-tasks'], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ ai-tasks command not found")
        return
    
    ai_tasks_path = result.stdout.strip()
    print(f"📍 Found ai-tasks at: {ai_tasks_path}")
    
    # Check if it's a Python script
    with open(ai_tasks_path, 'r') as f:
        content = f.read()
    
    if 'add_option' in content and 'AITasksCommand' in content:
        print("🔍 Found the issue: 'add_option' method call")
        print("ℹ️  This might be due to an outdated argparse/click usage")
        
        # Provide fix suggestion
        print("\n📋 Suggested fixes:")
        print("1. Update the command implementation to use argparse.add_argument instead of add_option")
        print("2. Or switch to click library if using that framework")
        print("3. Check if AITasksCommand inherits from the correct base class")
    
    print("\n💡 Alternative: Use direct Python scripts instead:")
    print("   python3 scripts/send_task.py \"your task\" code")
    print("   python3 scripts/list_tasks.py")

if __name__ == "__main__":
    fix_ai_tasks()
