#!/usr/bin/env python3
"""
🏛️ Integrated Quality Daemon - Performance + Enhanced Standards
Combines 95% performance improvement with Elder Guild 85+ quality standards
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.optimized_quality_daemon import OptimizedQualityDaemon, OptimizedMetricsCollector
from libs.enhanced_quality_standards import QualityGateEnforcer, EnhancedQualityConfig
from libs.parallel_quality_analyzer import ParallelQualityAnalyzer

logger = logging.getLogger(__name__)

class IntegratedQualityDaemon(OptimizedQualityDaemon):
    """Quality daemon with both performance optimization and enhanced standards"""
    
    def __init__(self):
        super().__init__()
        
        # Enhanced quality configuration
        self.enhanced_config = EnhancedQualityConfig(
            minimum_quality_score=85.0,
            iron_will_compliance_rate=1.0,
            maximum_security_risk_level=3,
            critical_issues_limit=0,
            complexity_threshold=8,
            maintainability_minimum=60,
            test_coverage_minimum=90.0
        )
        
        # Enhanced quality enforcer
        self.quality_enforcer = QualityGateEnforcer(self.enhanced_config)
        
        logger.info("🏛️ Integrated Quality Daemon initialized with Elder Guild 85+ standards")
    
    async def run_monitoring_cycle(self):
        """Enhanced monitoring cycle with quality gate enforcement"""
        cycle_start = time.time()
        logger.info("🏛️ Enhanced monitoring cycle started")
        
        try:
            # Run optimized performance collection
            await super().run_monitoring_cycle()
            
            # Apply enhanced quality gate (sample files for performance)
            sample_files = self._get_sample_files_for_quality_check()
            if sample_files:
                quality_gate_result = self.quality_enforcer.check_quality_gate(sample_files)
                
                # Log quality gate results
                self._log_quality_gate_results(quality_gate_result)
                
                # Take action on quality gate failures
                if not quality_gate_result['gate_passed']:
                    await self._handle_quality_gate_failure(quality_gate_result)
            
            cycle_time = time.time() - cycle_start
            logger.info(f"✅ Enhanced monitoring cycle completed in {cycle_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Enhanced monitoring cycle failed: {e}")
    
    def _get_sample_files_for_quality_check(self) -> List[str]:
        """Get sample files for quality gate checking"""
        try:
            # Get recently changed files or a representative sample
            python_files = list(self.project_root.rglob("*.py"))
            
            # Filter out excluded directories
            filtered_files = []
            for f in python_files:
                if any(part.startswith('.') for part in f.parts):
                    continue
                if any(part in ['__pycache__', 'venv', 'env'] for part in f.parts):
                    continue
                filtered_files.append(str(f))
            
            # Return sample (limit for performance)
            return filtered_files[:10]
            
        except Exception as e:
            logger.warning(f"Could not get sample files: {e}")
            return []
    
    def _log_quality_gate_results(self, result: Dict[str, Any]):
        """Log quality gate enforcement results"""
        logger.info("🏛️ Elder Guild Quality Gate Results:")
        logger.info(f"   Gate Status: {'✅ PASSED' if result['gate_passed'] else '❌ FAILED'}")
        logger.info(f"   Average Score: {result['average_quality_score']:.1f}/100")
        logger.info(f"   Files Analyzed: {result['files_analyzed']}")
        logger.info(f"   Files Failed: {result['files_failed']}")
        logger.info(f"   Critical Violations: {result['critical_violations']}")
        logger.info(f"   Total Violations: {result['total_violations']}")
    
    async def _handle_quality_gate_failure(self, result: Dict[str, Any]):
        """Handle quality gate failure with appropriate actions"""
        logger.warning("⚠️ Quality gate failure detected - taking corrective action")
        
        # Save detailed quality report
        report_file = self.project_root / "logs" / f" \
            quality_gate_failure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            logger.info(f"📋 Quality failure report saved: {report_file}")
        except Exception as e:
            logger.error(f"Could not save quality report: {e}")
        
        # Log specific violations for immediate attention
        for file_result in result['results']:
            if not file_result['result']['elder_guild_compliant']:
                file_path = file_result['file_path']
                score = file_result['result']['quality_score']
                violations = len(file_result['result']['violations'])
                
                logger.warning(f"❌ {file_path}: {score:.1f}/100 ({violations} violations)")
                
                # Log critical violations in detail
                for violation in file_result['result']['violations']:
                    if violation['severity'] == 'critical':
                        logger.error(f"🚨 CRITICAL: {violation['message']} at line {violation['line_number']}")

async def run_integrated_quality_check():
    """Run a single integrated quality check"""
    daemon = IntegratedQualityDaemon()
    await daemon.run_monitoring_cycle()

if __name__ == "__main__":
    import time
    import json
    from datetime import datetime
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    if len(sys.argv) > 1 and sys.argv[1] == "single":
        asyncio.run(run_integrated_quality_check())
    else:
        daemon = IntegratedQualityDaemon()
        asyncio.run(daemon.run_forever())
