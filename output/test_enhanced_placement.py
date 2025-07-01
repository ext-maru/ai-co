#!/usr/bin/env python3
"""
Enhanced SelfEvolutionManager test script
Test the new ML-based intelligent placement features
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from libs.self_evolution_manager import SelfEvolutionManager

def test_enhanced_placement():
    """Test enhanced placement functionality"""
    manager = SelfEvolutionManager()
    
    # Test case 1: Worker class
    worker_content = '''
import pika
import logging

class TaskProcessor:
    def __init__(self):
        self.connection = None
    
    def process_task(self, task_data):
        print(f"Processing task: {task_data}")
        return True

if __name__ == "__main__":
    processor = TaskProcessor()
    '''
    
    # Test case 2: Manager class  
    manager_content = '''
import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        
    def create_tables(self):
        conn = sqlite3.connect(self.db_path)
        # Database setup code
        conn.close()
        
    def get_stats(self):
        return {"total": 100}
    '''
    
    # Test case 3: Script
    script_content = '''
#!/usr/bin/env python3
import argparse

def send_notification(message):
    print(f"Sending: {message}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", required=True)
    args = parser.parse_args()
    send_notification(args.message)
    '''
    
    print("=== Enhanced SelfEvolutionManager Test ===\n")
    
    # Test 1: Worker placement
    print("1. Testing Worker class placement:")
    result1 = manager.get_placement_preview(worker_content, "task_processor.py")
    print(f"   Predicted: {result1['target_dir']}")
    print(f"   Full path: {result1['relative_path']}")
    print()
    
    # Test 2: Manager placement
    print("2. Testing Manager class placement:")
    result2 = manager.get_placement_preview(manager_content, "database_manager.py")
    print(f"   Predicted: {result2['target_dir']}")
    print(f"   Full path: {result2['relative_path']}")
    print()
    
    # Test 3: Script placement
    print("3. Testing Script placement:")
    result3 = manager.get_placement_preview(script_content, "send_notification.py")
    print(f"   Predicted: {result3['target_dir']}")
    print(f"   Full path: {result3['relative_path']}")
    print()
    
    # Test actual placement (will create learning data)
    print("4. Testing actual placement with learning:")
    placement_result = manager.auto_place_file(
        worker_content, 
        "test_worker.py", 
        task_id="test_001"
    )
    
    if placement_result["success"]:
        print(f"   ✓ Successfully placed: {placement_result['relative_path']}")
        print(f"   ✓ Confidence: {placement_result['placement_confidence']:.2f}")
        print(f"   ✓ Alternatives: {placement_result['alternatives']}")
    else:
        print(f"   ✗ Placement failed: {placement_result['error']}")
    
    print()
    
    # Test analytics
    print("5. Testing placement analytics:")
    analytics = manager.get_placement_analytics()
    if 'error' not in analytics:
        print(f"   Total placements: {analytics['total_placements']}")
        print(f"   Directory stats: {analytics['directory_stats']}")
        print(f"   Learning DB size: {analytics['learning_db_size']} bytes")
    else:
        print(f"   Analytics error: {analytics['error']}")

if __name__ == "__main__":
    test_enhanced_placement()