#!/usr/bin/env python3
"""
Verification script for worker RAG migration
Tests that all workers properly integrate with the new RagGrimoireIntegration system
"""

import asyncio
import importlib
import inspect
import logging
import sys
from pathlib import Path
from typing import Any
from typing import Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.rag_grimoire_integration import RagGrimoireConfig
from libs.rag_grimoire_integration import RagGrimoireIntegration

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class WorkerRAGMigrationVerifier:
    """Verifies that workers have been properly migrated to use RagGrimoireIntegration"""

    def __init__(self):
        self.results = {"verified_workers": [], "failed_workers": [], "skipped_workers": [], "issues": []}

        # Workers that should have RAG integration
        self.target_workers = [
            "enhanced_task_worker",
            "async_enhanced_task_worker",
            "rag_wizards_worker",
            "dialog_task_worker",
            "knowledge_scheduler_worker",
        ]

    async def verify_all_workers(self) -> Dict[str, Any]:
        """Verify all target workers for RAG integration"""
        logger.info("🔍 Starting worker RAG migration verification...")

        for worker_name in self.target_workers:
            try:
                await self._verify_worker(worker_name)
            except Exception as e:
                logger.error(f"❌ Failed to verify worker {worker_name}: {e}")
                self.results["failed_workers"].append({"worker": worker_name, "error": str(e)})

        return self._generate_report()

    async def _verify_worker(self, worker_name: str):
        """Verify a specific worker for RAG integration"""
        logger.info(f"📋 Verifying worker: {worker_name}")

        try:
            # Import the worker module
            module = importlib.import_module(f"workers.{worker_name}")

            # Check for RagGrimoireIntegration import
            if not self._check_import(module, worker_name):
                return

            # Check worker class for RAG integration attributes
            worker_class = self._find_worker_class(module, worker_name)
            if not worker_class:
                self.results["issues"].append(f"No worker class found in {worker_name}")
                return

            # Verify RAG integration implementation
            verification_result = await self._verify_rag_implementation(worker_class, worker_name)

            if verification_result["success"]:
                self.results["verified_workers"].append(
                    {"worker": worker_name, "class": worker_class.__name__, "features": verification_result["features"]}
                )
                logger.info(f"✅ Worker {worker_name} verification passed")
            else:
                self.results["failed_workers"].append({"worker": worker_name, "issues": verification_result["issues"]})
                logger.warning(f"⚠️  Worker {worker_name} has issues: {verification_result['issues']}")

        except ImportError as e:
            logger.error(f"❌ Cannot import worker {worker_name}: {e}")
            self.results["failed_workers"].append({"worker": worker_name, "error": f"Import error: {e}"})
        except Exception as e:
            logger.error(f"❌ Unexpected error verifying {worker_name}: {e}")
            self.results["failed_workers"].append({"worker": worker_name, "error": f"Unexpected error: {e}"})

    def _check_import(self, module, worker_name: str) -> bool:
        """Check if the module imports RagGrimoireIntegration"""
        source_file = inspect.getfile(module)

        try:
            with open(source_file, "r", encoding="utf-8") as f:
                content = f.read()

            if "RagGrimoireIntegration" not in content:
                self.results["issues"].append(f"{worker_name} does not import RagGrimoireIntegration")
                return False

            if "RagGrimoireConfig" not in content:
                self.results["issues"].append(f"{worker_name} does not import RagGrimoireConfig")
                return False

            return True

        except Exception as e:
            self.results["issues"].append(f"Cannot read source file for {worker_name}: {e}")
            return False

    def _find_worker_class(self, module, worker_name: str):
        """Find the main worker class in the module"""
        # Common worker class name patterns
        class_patterns = [
            # Enhanced Task Worker -> EnhancedTaskWorker
            "".join(word.capitalize() for word in worker_name.split("_")),
            # enhanced_task_worker -> EnhancedTaskWorker
            worker_name.replace("_", " ").title().replace(" ", ""),
            # RAGWizardsWorker for rag_wizards_worker
            "RAGWizardsWorker" if "rag_wizards" in worker_name else None,
            # DialogTaskWorker for dialog_task_worker
            "DialogTaskWorker" if "dialog" in worker_name else None,
            # KnowledgeManagementScheduler for knowledge_scheduler_worker
            "KnowledgeManagementScheduler" if "knowledge_scheduler" in worker_name else None,
        ]

        for pattern in class_patterns:
            if pattern and hasattr(module, pattern):
                return getattr(module, pattern)

        # If no pattern matches, find classes that might be workers
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if "Worker" in name or "Scheduler" in name:
                return obj

        return None

    async def _verify_rag_implementation(self, worker_class, worker_name: str) -> Dict[str, Any]:
        """Verify that the worker class properly implements RAG integration"""
        issues = []
        features = []

        # Check if class has RAG-related attributes in __init__
        init_source = self._get_method_source(worker_class, "__init__")
        if init_source:
            if "rag_integration" in init_source:
                features.append("RAG integration attribute")
            else:
                issues.append("Missing rag_integration attribute in __init__")

            if "rag_config" in init_source or "RagGrimoireConfig" in init_source:
                features.append("RAG configuration setup")
            else:
                issues.append("Missing RAG configuration setup")

        # Check for RAG initialization method
        if hasattr(worker_class, "_initialize_rag_integration"):
            features.append("RAG initialization method")
        else:
            issues.append("Missing _initialize_rag_integration method")

        # Check for cleanup method with RAG cleanup
        cleanup_source = self._get_method_source(worker_class, "cleanup")
        if cleanup_source and "rag_integration" in cleanup_source:
            features.append("RAG cleanup in cleanup method")
        else:
            issues.append("Missing RAG cleanup in cleanup method")

        # Check for async workers
        if "async" in worker_name.lower():
            if hasattr(worker_class, "start"):
                start_source = self._get_method_source(worker_class, "start")
                if start_source and "rag_integration" in start_source:
                    features.append("Async RAG initialization in start method")
                else:
                    issues.append("Missing async RAG initialization in start method")

        # Check for RAG usage in processing methods
        processing_methods = ["process_message", "_process_rag_query", "_get_rag_context"]
        for method_name in processing_methods:
            if hasattr(worker_class, method_name):
                method_source = self._get_method_source(worker_class, method_name)
                if method_source and ("search_unified" in method_source or "add_knowledge_unified" in method_source):
                    features.append(f"RAG usage in {method_name}")
                    break

        return {"success": len(issues) == 0, "issues": issues, "features": features}

    def _get_method_source(self, worker_class, method_name: str) -> str:
        """Get source code of a method"""
        try:
            if hasattr(worker_class, method_name):
                method = getattr(worker_class, method_name)
                return inspect.getsource(method)
        except Exception:
            pass
        return ""

    def _generate_report(self) -> Dict[str, Any]:
        """Generate verification report"""
        total_workers = len(self.target_workers)
        verified_count = len(self.results["verified_workers"])
        failed_count = len(self.results["failed_workers"])

        report = {
            "summary": {
                "total_workers": total_workers,
                "verified_workers": verified_count,
                "failed_workers": failed_count,
                "success_rate": f"{(verified_count / total_workers * 100):.1f}%",
            },
            "details": self.results,
        }

        return report


async def test_rag_integration_functionality():
    """Test that RAG integration actually works"""
    logger.info("🧪 Testing RAG integration functionality...")

    try:
        # Create test RAG integration
        config = RagGrimoireConfig(
            database_url="postgresql://localhost/grimoire_test", search_threshold=0.7, max_search_results=5
        )

        integration = RagGrimoireIntegration(config)

        # Test initialization
        await integration.initialize()
        logger.info("✅ RAG integration initialization successful")

        # Test adding knowledge
        spell_id = await integration.add_knowledge_unified(
            spell_name="verification_test_spell",
            content="This is a test spell created during worker verification.",
            metadata={"verification": True},
            category="verification_test",
        )
        logger.info(f"✅ Knowledge addition successful: {spell_id}")

        # Test searching
        results = await integration.search_unified(query="verification test spell", limit=3)
        logger.info(f"✅ Knowledge search successful: {len(results)} results")

        # Test status
        status = await integration.get_integration_status()
        logger.info(f"✅ Status check successful: {status['integration_active']}")

        # Cleanup
        await integration.cleanup()
        logger.info("✅ RAG integration cleanup successful")

        return True

    except Exception as e:
        logger.error(f"❌ RAG integration test failed: {e}")
        return False


async def main():
    """Main verification function"""
    print("🚀 Worker RAG Migration Verification")
    print("=" * 50)

    # Test RAG integration functionality first
    rag_test_success = await test_rag_integration_functionality()
    if not rag_test_success:
        print("\n❌ RAG integration basic functionality test failed!")
        print("Please ensure PostgreSQL is running and grimoire database is set up.")
        return 1

    print("\n✅ RAG integration basic functionality test passed!")

    # Verify worker migrations
    verifier = WorkerRAGMigrationVerifier()
    report = await verifier.verify_all_workers()

    # Print report
    print("\n📊 Verification Report")
    print("-" * 30)
    print(f"Total workers checked: {report['summary']['total_workers']}")
    print(f"Successfully verified: {report['summary']['verified_workers']}")
    print(f"Failed verification: {report['summary']['failed_workers']}")
    print(f"Success rate: {report['summary']['success_rate']}")

    if report["details"]["verified_workers"]:
        print("\n✅ Verified Workers:")
        for worker in report["details"]["verified_workers"]:
            print(f"  • {worker['worker']} ({worker['class']})")
            for feature in worker["features"]:
                print(f"    - {feature}")

    if report["details"]["failed_workers"]:
        print("\n❌ Failed Workers:")
        for worker in report["details"]["failed_workers"]:
            print(f"  • {worker['worker']}")
            if "issues" in worker:
                for issue in worker["issues"]:
                    print(f"    - {issue}")
            if "error" in worker:
                print(f"    - Error: {worker['error']}")

    if report["details"]["issues"]:
        print("\n⚠️  General Issues:")
        for issue in report["details"]["issues"]:
            print(f"  • {issue}")

    # Return success/failure
    return 0 if report["summary"]["failed_workers"] == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
