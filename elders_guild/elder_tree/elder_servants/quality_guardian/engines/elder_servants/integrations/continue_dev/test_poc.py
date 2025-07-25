#!/usr/bin/env python3
"""
Continue.dev Integration POC Test
Tests the integration between Continue.dev and Elder Servants
"""

import asyncio
import sys
import os
import requests
import time
import subprocess
import signal
from typing import Optional

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.abspath('./../../..'))))

class ContinueDevPOC:
    """POC test for Continue.dev integration"""
    
    def __init__(self):
        """初期化メソッド"""
        self.base_url = "http://localhost:8000"
        self.server_process: Optional[subprocess.Popen] = None
        
    def start_server(self):
        """Start the Continue.dev adapter server"""
        try:
            # Start server in background
            env = os.environ.copy()
            env['PYTHONPATH'] = '/home/aicompany/ai_co'
            
            self.server_process = subprocess.Popen([
                'venv_continue_dev/bin/python', 
                'elder_servant_adapter.py'
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            for i in range(30):  # Wait up to 30 seconds
                try:
                    # Security: Validate URL before making request
                    response = requests.get(f"{self.base_url}/")
                    if response.status_code == 200:
                        print("✅ Server started successfully")
                        return True
                except requests.exceptions.ConnectionError:
                    time.sleep(1)
                    
            print("❌ Server failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    def stop_server(self):
        """Stop the server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            print("🛑 Server stopped")
    
    def test_health_check(self):
        """Test basic health check"""
        try:
            # Security: Validate URL before making request
            response = requests.get(f"{self.base_url}/")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            print("✅ Health check passed")
            return True
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def test_list_servants(self):
        """Test listing Elder Servants"""
        try:
            # Security: Validate URL before making request
            response = requests.get(f"{self.base_url}/elder/servants/list")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            print(f"✅ Listed {data['total']} servants")
            return True
        except Exception as e:
            print(f"❌ List servants failed: {e}")
            return False
    
    def test_sage_consultation(self):
        """Test 4 Sages consultation"""
        try:
            payload = {
                "question": "What are the best practices for Python code quality?",
                "context": {"language": "python"}
            }
            response = requests.post(f"{self.base_url}/elder/sages/consult", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Sage consultation successful")
                print(f"📜 Advice: {data['advice'][:100]}...")
                return True
            else:
                print(f"❌ Sage consultation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Sage consultation error: {e}")
            return False
    
    def test_quality_check(self):
        """Test Iron Will quality check"""
        try:
            test_code = '''
def hello_world():
    """A simple hello world function"""
    return "Hello, World!"
            '''
            
            payload = {
                "file_path": "test.py",
                "content": test_code
            }
            response = requests.post(f"{self.base_url}/elder/quality/iron-will", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Quality check: {data['score']}% (Iron Will: {data['passes_iron_will']})")
                return True
            else:
                print(f"❌ Quality check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Quality check error: {e}")
            return False
    
    def test_knowledge_search(self):
        """Test knowledge base search"""
        try:
            payload = {
                "query": "TDD best practices",
                "limit": 3
            }
            response = requests.post(f"{self.base_url}/elder/knowledge/search", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Knowledge search: Found {data['total']} items")
                return True
            else:
                print(f"❌ Knowledge search failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Knowledge search error: {e}")
            return False
    
    def run_poc_tests(self):
        """Run all POC tests"""
        print("🚀 Starting Continue.dev Integration POC")
        print("=" * 50)
        
        # Start server
        if not self.start_server():
            return False
        
        try:
            tests = [
                ("Health Check", self.test_health_check),
                ("List Servants", self.test_list_servants),
                ("Sage Consultation", self.test_sage_consultation),
                ("Quality Check", self.test_quality_check),
                ("Knowledge Search", self.test_knowledge_search)
            ]
            
            results = []
            for test_name, test_func in tests:
                print(f"\n🧪 Running: {test_name}")
                result = test_func()
                results.append((test_name, result))
                time.sleep(1)  # Brief pause between tests
            
            # Summary
            print("\n" + "=" * 50)
            print("📊 POC Test Results:")
            passed = sum(1 for _, result in results if result)
            total = len(results)
            
            for test_name, result in results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  {status} {test_name}")
            
            print(f"\n🎯 Overall: {passed}/{total} tests passed")
            
            if passed == total:
                print("🎉 POC successful! Continue.dev integration is working.")
                return True
            else:
                print("⚠️ POC partially successful. Some issues need attention.")
                return False
                
        finally:
            self.stop_server()

def main():
    """Main entry point"""
    poc = ContinueDevPOC()
    success = poc.run_poc_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())