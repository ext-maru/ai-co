"""
Test script for Continue.dev integration
Tests the HTTP adapter endpoints to ensure Elder Servants are accessible
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.abspath('./../../..'))))

BASE_URL = "http://localhost:8000"

async def test_health_check():
    """Test health check endpoint"""
    print("🏥 Testing health check...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/") as response:
            data = await response.json()
            print(f"✅ Health check: {data['status']}")
            print(f"   Servants count: {data['servants_count']}")
            return response.status == 200

async def test_list_servants():
    """Test listing all servants"""
    print("\n📋 Testing list servants...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/elder/servants/list") as response:
            data = await response.json()
            print(f"✅ Found {data['total']} servants:")
            for servant in data['servants']:
                print(f"   - {servant['name']} ({servant['category']}): {servant['status']}")
            return response.status == 200

async def test_code_generation():
    """Test code generation with Code Craftsman"""
    print("\n🔨 Testing Code Craftsman...")
    async with aiohttp.ClientSession() as session:
        payload = {
            "type": "execute_task",
            "task": {
                "type": "code_generation",
                "prompt": "Create a simple Python function to calculate fibonacci",
                "language": "python"
            }
        }
        async with session.post(
            f"{BASE_URL}/elder/servants/code-craftsman/execute",
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Code generation successful")
                print("Generated code preview:")
                code = data.get('result', {}).get('result_data', {}).get('code', 'No code')
                print(code[:200] + "..." if len(code) > 200 else code)
                return True
            else:
                print(f"❌ Code generation failed: {response.status}")
                return False

async def test_sage_consultation():
    """Test 4 Sages consultation"""
    print("\n🧙‍♂️ Testing 4 Sages consultation...")
    async with aiohttp.ClientSession() as session:
        payload = {
            "question": "What's the best way to implement user authentication?",
            "context": {
                "project_type": "web_api",
                "language": "python"
            }
        }
        async with session.post(
            f"{BASE_URL}/elder/sages/consult",
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Sage consultation successful")
                print("Sage advice preview:")
                advice = data.get('advice', 'No advice')
                print(advice[:300] + "..." if len(advice) > 300 else advice)
                return True
            else:
                print(f"❌ Sage consultation failed: {response.status}")
                return False

async def test_quality_check():
    """Test Iron Will quality check"""
    print("\n🗡️ Testing Iron Will quality check...")
    async with aiohttp.ClientSession() as session:
        payload = {
            "file_path": "test.py",
            "content": """
def calculate_sum(a, b):
    '''Calculate sum of two numbers'''
    return a + b

def test_calculate_sum():
    assert calculate_sum(2, 3) == 5
    assert calculate_sum(-1, 1) == 0
"""
        }
        async with session.post(
            f"{BASE_URL}/elder/quality/iron-will",
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Quality check complete: {data['score']}%")
                print(f"   Passes Iron Will: {data['passes_iron_will']}")
                print(f"   Details: {data['details']}")
                return True
            else:
                print(f"❌ Quality check failed: {response.status}")
                return False

async def test_elder_flow():
    """Test Elder Flow execution"""
    print("\n🌊 Testing Elder Flow...")
    async with aiohttp.ClientSession() as session:
        payload = {
            "query": "Add error handling to the fibonacci function",
            "context": {
                "files": ["test.py"],
                "priority": "high"
            }
        }
        async with session.post(
            f"{BASE_URL}/elder/flow/execute",
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Elder Flow executed successfully")
                print(f"   Task ID: {data.get('task_id', 'N/A')}")
                print(f"   Quality Score: {data.get('quality_score', 0)}%")
                return True
            else:
                print(f"❌ Elder Flow failed: {response.status}")
                error_text = await response.text()
                print(f"   Error: {error_text}")
                return False

async def test_continue_dev_scenario():
    """Test a complete Continue.dev usage scenario"""
    print("\n🎯 Testing Complete Continue.dev Scenario...")
    
    # Simulate Continue.dev workflow
    success = True
    
    # 1. User asks for code generation
    print("1️⃣ User requests code generation via Continue.dev...")
    success &= await test_code_generation()
    
    # 2. Check quality of generated code
    print("\n2️⃣ Continue.dev checks code quality...")
    success &= await test_quality_check()
    
    # 3. Consult sages for best practices
    print("\n3️⃣ Continue.dev consults sages for improvements...")
    success &= await test_sage_consultation()
    
    return success

async def run_all_tests():
    """Run all integration tests"""
    print("🚀 Starting Elder Servants Continue.dev Integration Tests\n")
    
    results = {
        "Health Check": await test_health_check(),
        "List Servants": await test_list_servants(),
        "Code Generation": await test_code_generation(),
        "Sage Consultation": await test_sage_consultation(),
        "Quality Check": await test_quality_check(),
        "Elder Flow": await test_elder_flow(),
        "Complete Scenario": await test_continue_dev_scenario()
    }
    
    print("\n📊 Test Results Summary:")
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Total: {passed}/{len(results)} tests passed")
    
    return passed == len(results)

async def test_adapter_startup():
    """Quick test to see if adapter is running"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/",
                timeout=aiohttp.ClientTimeout(total=2)
            ) as response:
                return response.status == 200
    except:
        return False

if __name__ == "__main__":
    # First check if adapter is running
    print("🔍 Checking if Elder Servant Adapter is running...")
    
    loop = asyncio.get_event_loop()
    adapter_running = loop.run_until_complete(test_adapter_startup())
    
    if not adapter_running:
        print("❌ Elder Servant Adapter is not running!")
        print("💡 Start it with: python elder_servant_adapter.py")
        print("   or: uvicorn elder_servant_adapter:app --reload")
        sys.exit(1)
    
    print("✅ Adapter is running!\n")
    
    # Run all tests
    all_passed = loop.run_until_complete(run_all_tests())
    
    if all_passed:
        print("\n🎉 All tests passed! Continue.dev integration is ready.")
    else:
        print("\n⚠️  Some tests failed. Please check the adapter logs.")
        sys.exit(1)