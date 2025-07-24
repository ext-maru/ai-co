#!/usr/bin/env python3
"""
Debug the failing tests
"""

import asyncio
import sys
sys.path.append("/home/aicompany/ai_co/elders_guild")
from task_sage.business_logic import TaskProcessor

async def debug_error_handling():
    """Debug error handling test"""
    print("🔍 Debugging Error Handling Test...")
    
    processor = TaskProcessor()
    
    # Test 1: Invalid task ID (should fail)
    print("Test 1: Invalid task ID")
    result = await processor.process_action("get_task", {"task_id": "invalid-id"})
    print(f"  Success: {result['success']} (should be False)")
    
    # Test 2: Missing title (should fail)
    print("Test 2: Missing title")
    result = await processor.process_action("create_task", {"description": "No title"})
    print(f"  Success: {result['success']} (should be False)")
    
    # Test 3: Create valid task then invalid status update
    print("Test 3: Invalid status update")
    task_result = await processor.process_action("create_task", {
        "title": "Test Task",
        "estimated_hours": 1.0
    })
    print(f"  Task creation success: {task_result['success']}")
    
    if task_result["success"]:
        task_id = task_result["data"]["task_id"]
        
        # Invalid status update
        result = await processor.process_action("update_task", {
            "task_id": task_id,
            "updates": {"status": "invalid_status"}
        })
        print(f"  Invalid status update success: {result['success']} (should be False)")
    
    # Test 4: Circular dependency
    print("Test 4: Circular dependency")
    task1_result = await processor.process_action("create_task", {
        "title": "Task 1",
        "estimated_hours": 1.0
    })
    task2_result = await processor.process_action("create_task", {
        "title": "Task 2", 
        "estimated_hours": 1.0
    })
    
    if task1_result["success"] and task2_result["success"]:
        task1_id = task1_result["data"]["task_id"]
        task2_id = task2_result["data"]["task_id"]
        
        # Create circular dependency
        await processor.process_action("update_task", {
            "task_id": task1_id,
            "updates": {"dependencies": [task2_id]}
        })
        await processor.process_action("update_task", {
            "task_id": task2_id,
            "updates": {"dependencies": [task1_id]}
        })
        
        # Try to resolve
        result = await processor.process_action("resolve_dependencies", {
            "task_ids": [task1_id, task2_id]
        })
        print(f"  Circular dependency resolution success: {result['success']} (should be False)")
    
    # Test 5: Invalid action
    print("Test 5: Invalid action")
    result = await processor.process_action("invalid_action", {})
    print(f"  Invalid action success: {result['success']} (should be False)")

async def debug_effort_estimation():
    """Debug effort estimation test"""
    print("\n🔍 Debugging Effort Estimation Test...")
    
    processor = TaskProcessor()
    
    # Test cases from the comprehensive test
    estimation_cases = [
        {
            "name": "Simple Task",
            "complexity_factors": {
                "lines_of_code": 100,
                "complexity": "low",
                "dependencies": []
            },
            "expected_range": (1, 10)
        },
        {
            "name": "Medium Task", 
            "complexity_factors": {
                "lines_of_code": 1000,
                "complexity": "medium",
                "dependencies": ["task1", "task2"]
            },
            "expected_range": (10, 50)
        },
        {
            "name": "Complex Task",
            "complexity_factors": {
                "lines_of_code": 5000,
                "complexity": "high",
                "dependencies": ["task1", "task2", "task3", "task4"]
            },
            "expected_range": (50, 200)
        },
        {
            "name": "Critical Task",
            "complexity_factors": {
                "lines_of_code": 10000,
                "complexity": "critical",
                "dependencies": ["task1", "task2", "task3", "task4", "task5", "task6"]
            },
            "expected_range": (100, 500)
        }
    ]
    
    for case in estimation_cases:
        print(f"\nTesting: {case['name']}")
        
        estimate_result = await processor.process_action("estimate_effort", {
            "complexity_factors": case["complexity_factors"]
        })
        
        print(f"  Success: {estimate_result['success']}")
        
        if estimate_result["success"]:
            estimated_hours = estimate_result["data"]["estimated_hours"]
            confidence = estimate_result["data"]["confidence"]
            breakdown = estimate_result["data"]["breakdown"]
            
            min_hours, max_hours = case["expected_range"]
            hours_in_range = min_hours <= estimated_hours <= max_hours
            confidence_valid = 0.3 <= confidence <= 0.95
            
            print(f"  Estimated hours: {estimated_hours:0.2f} (range: {min_hours}-{max_hours}) - {'✅' if hours_in_range else '❌'}")
            print(f"  Confidence: {confidence:0.2f} (range: 0.3-0.95) - {'✅' if confidence_valid else '❌'}")
            print(f"  Breakdown keys: {list(breakdown.keys())}")
            
            # Check breakdown calculation
            required_phases = ["implementation", "analysis", "testing", "documentation", "review", "total"]
            has_required_phases = all(phase in breakdown for phase in required_phases)
            print(f"  Has required phases: {'✅' if has_required_phases else '❌'}")
            
            if has_required_phases:
                calculated_total = sum(breakdown[phase] for phase in required_phases[:-1])  # exclude total
                total_matches = abs(breakdown["total"] - calculated_total) < 0.01
                hours_match_total = abs(estimated_hours - breakdown["total"]) < 0.01
                
                print(f"  Total calculation matches: {'✅' if total_matches else '❌'}")
                print(f"  Hours match total: {'✅' if hours_match_total else '❌'}")
        else:
            print(f"  Error: {estimate_result.get('error', 'Unknown error')}")

async def main():
    await debug_error_handling()
    await debug_effort_estimation()

if __name__ == "__main__":
    asyncio.run(main())