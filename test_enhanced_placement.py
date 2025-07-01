#!/usr/bin/env python3
"""
Test script for enhanced SelfEvolutionManager placement functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.self_evolution_manager import SelfEvolutionManager
import json

def test_enhanced_placement():
    """Test the enhanced ML-based placement system"""
    manager = SelfEvolutionManager()
    
    # Test cases with different types of content
    test_cases = [
        {
            'name': 'Worker Script',
            'content': '''#!/usr/bin/env python3
import pika
import asyncio
from threading import Thread

class TaskWorker:
    def __init__(self):
        self.connection = None
        
    async def process_task(self, task_data):
        """Process background task"""
        print(f"Processing task: {task_data}")
        
    def start_worker(self):
        """Start the worker process"""
        pass
''',
            'expected_dir': 'workers/'
        },
        {
            'name': 'Manager Class',
            'content': '''#!/usr/bin/env python3
import sqlite3
import logging
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
    def create_connection(self):
        """Create database connection"""
        return sqlite3.connect(self.db_path)
        
    def execute_query(self, query, params=None):
        """Execute database query"""
        pass
''',
            'expected_dir': 'libs/'
        },
        {
            'name': 'Web API',
            'content': '''#!/usr/bin/env python3
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify({'status': 'ok'})
    
@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create new task"""
    data = request.get_json()
    return jsonify({'task_id': 123})

if __name__ == '__main__':
    app.run(debug=True)
''',
            'expected_dir': 'web/'
        },
        {
            'name': 'Setup Script',
            'content': '''#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Setup development environment"""
    print("Setting up environment...")
    
def install_dependencies():
    """Install required packages"""
    subprocess.run(['pip', 'install', '-r', 'requirements.txt'])
    
def create_directories():
    """Create necessary directories"""
    dirs = ['logs', 'data', 'config']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)

if __name__ == '__main__':
    setup_environment()
    install_dependencies()
    create_directories()
    print("Setup complete!")
''',
            'expected_dir': 'scripts/'
        }
    ]
    
    print("🧪 Testing Enhanced SelfEvolutionManager Placement")
    print("="*60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        print("-" * 40)
        
        # Test the enhanced placement
        result = manager.test_enhanced_placement(test_case['content'])
        
        print(f"Selected placement: {result['selected_placement']}")
        print(f"Expected placement: {test_case['expected_dir']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Filename: {result['filename']}")
        
        # Check if prediction matches expected
        is_correct = result['selected_placement'] == test_case['expected_dir']
        status = "✅ CORRECT" if is_correct else "❌ INCORRECT"
        print(f"Result: {status}")
        
        # Show top candidates
        print("Top candidates:")
        for j, candidate in enumerate(result['candidates'][:3], 1):
            method_short = candidate['method'].replace('enhanced_', '').replace('_', ' ')
            print(f"  {j}. {candidate['dir']} (score: {candidate['score']:.3f}, method: {method_short})")
        
        # Show analysis methods used
        methods = result['analysis_methods']
        active_methods = [k for k, v in methods.items() if v > 0]
        print(f"Analysis methods: {', '.join(active_methods)}")
        
        print()
    
    print("="*60)
    print("🎯 Enhanced Placement Test Complete")
    
    # Test placement analytics if database exists
    analytics = manager.get_placement_analytics()
    if 'error' not in analytics:
        print(f"\n📊 Learning Database Stats:")
        print(f"Total placements: {analytics['total_placements']}")
        print(f"Database size: {analytics['learning_db_size']} bytes")

if __name__ == '__main__':
    test_enhanced_placement()