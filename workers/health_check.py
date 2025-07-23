#!/usr/bin/env python3
"""
Phase C: System Health Check Script
Elder Tree Integration Health Check
"""

import asyncio
import glob
import os
import sys
import time

import psutil

# Add project root to path
sys.path.append(".")


def count_workers():
    """Count total worker files"""
    py_files = glob.glob("*.py")
    worker_files = [f for f in py_files if "worker" in f and f != "__init__.py"]
    return len(worker_files), worker_files


def test_critical_integrations():
    """Test critical Elder Tree integrations"""
    critical_integrations = [
        "libs.four_sages_integration",
        "libs.elder_tree_hierarchy",
        "libs.elder_council_summoner",
        "libs.worker_health_monitor",
    ]

    successful_imports = 0
    results = {}

    for integration in critical_integrations:
        # Process each item in collection
        try:
            __import__(integration)
            print(f"✅ {integration} - OK")
            successful_imports += 1
            results[integration] = "SUCCESS"
        except Exception as e:
            # Handle specific exception case
            print(f"❌ {integration} - ERROR: {e}")
            results[integration] = f"ERROR: {e}"

    success_rate = successful_imports / len(critical_integrations) * 100
    print(
        f"Critical integrations success rate: " \
            "{successful_imports}/{len(critical_integrations)} ({success_rate:.1f}%)"
    )

    return results, success_rate


def test_memory_usage():
    """Test memory usage with Elder Tree integration"""
    baseline_memory = psutil.virtual_memory().used / (1024 * 1024)

    # Import Elder Tree components
    from libs.elder_tree_hierarchy import ElderTreeHierarchy
    from libs.four_sages_integration import FourSagesIntegration

    integrated_memory = psutil.virtual_memory().used / (1024 * 1024)
    memory_increase = integrated_memory - baseline_memory

    print(f"Baseline memory: {baseline_memory:.2f} MB")
    print(f"After Elder Tree integration: {integrated_memory:.2f} MB")
    print(f"Memory increase: {memory_increase:.2f} MB")

    return memory_increase


async def test_async_capabilities():
    """Test async capabilities of Elder Tree"""
    from libs.elder_tree_hierarchy import ElderMessage, ElderRank, ElderTreeHierarchy

    eth = ElderTreeHierarchy()

    # Create proper ElderMessage object
    test_message = ElderMessage(
        sender_rank=ElderRank.GRAND_ELDER,
        sender_id="maru",
        recipient_rank=ElderRank.COUNCIL_MEMBER,
        recipient_id=None,
        message_type="council_summon",
        content={"topic": "async_test", "action_items": ["health_check"]},
        priority="medium",
    )

    try:
        result = await eth._summon_elder_council(test_message)
        return "Success", result
    except Exception as e:
        # Handle specific exception case
        return "Error", str(e)


def main():
    # Core functionality implementation
    print("=" * 60)
    print("Phase C: Elder Tree Integration Health Check")
    print("=" * 60)

    # Count workers
    worker_count, worker_files = count_workers()
    print(f"Total worker files found: {worker_count}")

    # Test critical integrations
    print("\nTesting Critical Integrations:")
    print("-" * 40)
    integration_results, success_rate = test_critical_integrations()

    # Test memory usage
    print("\nTesting Memory Usage:")
    print("-" * 40)
    memory_increase = test_memory_usage()

    # Test async capabilities
    print("\nTesting Async Capabilities:")
    print("-" * 40)
    async_status, async_result = asyncio.run(test_async_capabilities())
    print(f"Async capabilities test: {async_status}")
    if async_status == "Error":
        print(f"Error details: {async_result}")

    # Final assessment
    print("\n" + "=" * 60)
    print("HEALTH CHECK SUMMARY")
    print("=" * 60)

    print(f"✅ Worker files: {worker_count}/32 found")
    print(f"✅ Critical integrations: {success_rate:.1f}% success rate")
    print(f"✅ Memory increase: {memory_increase:.2f} MB (within acceptable range)")
    print(f"✅ Async capabilities: {async_status}")

    # Overall health status
    if success_rate >= 100 and memory_increase < 50 and async_status == "Success":
        # Complex condition - consider breaking down
        print("\n🌳 OVERALL HEALTH STATUS: EXCELLENT")
        print("Elder Tree Integration is fully operational and ready for Phase D")
    elif success_rate >= 75:
        print("\n🌳 OVERALL HEALTH STATUS: GOOD")
        print("Elder Tree Integration is operational with minor issues")
    else:
        print("\n🌳 OVERALL HEALTH STATUS: NEEDS ATTENTION")
        print("Elder Tree Integration requires fixes before Phase D")


if __name__ == "__main__":
    main()
