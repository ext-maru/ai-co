#!/usr/bin/env python3
"""
Generate comprehensive test coverage report
Final step in the Elder Servants mission
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class CoverageReporter:
    """Generate and analyze test coverage"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_coverage(self):
        """Run pytest with coverage"""
        print("🧪 RUNNING TEST COVERAGE ANALYSIS")
        print("=" * 80)
        
        # Prepare coverage command
        cmd = [
            sys.executable, '-m', 'pytest',
            '--cov=.',
            '--cov-report=term-missing',
            '--cov-report=html',
            '--cov-report=json',
            '--no-cov-on-fail',
            '-q',
            '--tb=short',
            '--maxfail=1000',  # Continue even with many failures
            'tests/'
        ]
        
        # Set environment variables
        env = os.environ.copy()
        env['TESTING'] = 'true'
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        
        try:
            # Run coverage
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                env=env,
                timeout=600  # 10 minutes timeout
            )
            
            # Print output
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
                
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏱️ Coverage analysis timed out")
            return False
        except Exception as e:
            print(f"❌ Error running coverage: {e}")
            return False
    
    def analyze_coverage(self):
        """Analyze coverage results"""
        coverage_file = self.project_root / 'coverage.json'
        
        if not coverage_file.exists():
            print("❌ No coverage.json file found")
            return None
            
        try:
            with open(coverage_file, 'r') as f:
                data = json.load(f)
                
            totals = data.get('totals', {})
            percent_covered = totals.get('percent_covered', 0)
            
            print("\n" + "=" * 80)
            print("📊 COVERAGE SUMMARY")
            print("=" * 80)
            print(f"Total Coverage: {percent_covered:.2f}%")
            print(f"Lines Covered: {totals.get('covered_lines', 0)}")
            print(f"Lines Missing: {totals.get('missing_lines', 0)}")
            print(f"Total Lines: {totals.get('num_statements', 0)}")
            
            return percent_covered
            
        except Exception as e:
            print(f"❌ Error analyzing coverage: {e}")
            return None
    
    def generate_report(self):
        """Generate final coverage report"""
        print("\n" + "=" * 80)
        print("📋 ELDER SERVANTS COVERAGE MISSION REPORT")
        print("=" * 80)
        print(f"Timestamp: {datetime.now()}")
        print(f"Project: AI Company")
        print()
        
        # Count test files
        test_files = list(Path(self.project_root / 'tests').rglob('test_*.py'))
        print(f"Test Files Generated: {len(test_files)}")
        
        # Run coverage
        success = self.run_coverage()
        
        # Analyze results
        coverage_percent = self.analyze_coverage()
        
        print("\n" + "=" * 80)
        print("🎯 MISSION STATUS")
        print("=" * 80)
        
        if coverage_percent is not None:
            if coverage_percent >= 60:
                print(f"✅ MISSION ACCOMPLISHED! Coverage: {coverage_percent:.2f}%")
                print("🎉 Target of 60% coverage ACHIEVED!")
            else:
                print(f"📈 Current Coverage: {coverage_percent:.2f}%")
                print(f"📊 Gap to Target: {60 - coverage_percent:.2f}%")
                print("\nNext Steps:")
                print("- Fix failing tests")
                print("- Add missing test implementations")
                print("- Run Elf Forest for auto-healing")
        else:
            print("⚠️ Could not determine coverage percentage")
            print("Check error messages above for details")
        
        print("\n" + "=" * 80)
        print("📁 Coverage Reports Generated:")
        print(f"- HTML Report: {self.project_root}/htmlcov/index.html")
        print(f"- JSON Report: {self.project_root}/coverage.json")
        print("=" * 80)
        
        return coverage_percent


if __name__ == '__main__':
    reporter = CoverageReporter()
    coverage = reporter.generate_report()
    
    # Exit with appropriate code
    if coverage is not None and coverage >= 60:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Need more work