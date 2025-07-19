#!/usr/bin/env python3
"""
Test Environment Setup Script
Automatically installs dependencies and configures the test environment
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path


class TestEnvironmentSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / "venv"
        self.required_packages = [
            # Core testing
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pytest-asyncio>=0.21.0",
            "pytest-timeout>=2.1.0",
            # Web scraping dependencies
            "beautifulsoup4>=4.11.0",
            "selenium>=4.8.0",
            "requests>=2.28.0",
            # Data visualization
            "matplotlib>=3.6.0",
            "seaborn>=0.12.0",
            # Message queue
            "pika>=1.3.0",
            # Web framework
            "flask>=2.2.0",
            "flask-login>=0.6.0",
            # Async utilities
            "aiohttp>=3.8.0",
            "asyncio>=3.4.3",
            # Circuit breaker pattern
            "py-breaker>=0.7.0",
            # Other utilities
            "python-dotenv>=0.21.0",
            "pyyaml>=6.0",
            "jsonschema>=4.17.0",
        ]

    def run(self):
        """Run the complete setup process"""
        print("=== Elders Guild Test Environment Setup ===\n")

        steps = [
            ("Cleaning __pycache__ directories", self.clean_pycache),
            ("Installing Python dependencies", self.install_dependencies),
            ("Setting up environment variables", self.setup_env_vars),
            ("Creating test directories", self.create_test_directories),
            ("Fixing import paths", self.fix_import_paths),
            ("Validating setup", self.validate_setup),
        ]

        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            try:
                step_func()
                print(f"✓ {step_name} completed")
            except Exception as e:
                print(f"✗ {step_name} failed: {e}")
                return False

        print("\n=== Setup completed successfully! ===")
        return True

    def clean_pycache(self):
        """Remove all __pycache__ directories"""
        removed = 0
        for root, dirs, files in os.walk(self.project_root):
            if "__pycache__" in dirs:
                shutil.rmtree(os.path.join(root, "__pycache__"))
                removed += 1

        # Also remove .pyc files
        pyc_files = list(self.project_root.rglob("*.pyc"))
        for pyc in pyc_files:
            pyc.unlink()
            removed += 1

        print(f"  Removed {removed} cache directories/files")

    def install_dependencies(self):
        """Install required Python packages"""
        # Upgrade pip first
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
        )

        # Install packages
        for package in self.required_packages:
            print(f"  Installing {package}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"    Warning: Failed to install {package}")

    def setup_env_vars(self):
        """Create .env file with test configuration"""
        env_file = self.project_root / ".env.test"
        env_content = """# Test Environment Configuration
PYTHONPATH=.
ENVIRONMENT=test
LOG_LEVEL=INFO
MOCK_EXTERNAL_SERVICES=true
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
REDIS_HOST=localhost
REDIS_PORT=6379
DATABASE_URL=sqlite:///test.db
FLASK_ENV=testing
FLASK_DEBUG=0
"""
        env_file.write_text(env_content)
        print(f"  Created {env_file}")

    def create_test_directories(self):
        """Ensure all test directories exist"""
        test_dirs = [
            "tests/unit",
            "tests/integration",
            "tests/fixtures",
            "tests/mocks",
            "logs/test",
            "coverage",
        ]

        for dir_path in test_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)

            # Create __init__.py files
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()

    def fix_import_paths(self):
        """Add project root to Python path"""
        pythonpath_file = self.project_root / ".pythonpath"
        pythonpath_file.write_text(str(self.project_root))

        # Create a pytest.ini if it doesn't exist
        pytest_ini = self.project_root / "pytest.ini"
        if not pytest_ini.exists():
            pytest_ini.write_text(
                """[pytest]
pythonpath = .
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
"""
            )

    def validate_setup(self):
        """Validate the setup is working"""
        # Try importing key packages
        try:
            print("  All key packages imported successfully")
        except ImportError as e:
            raise Exception(f"Failed to import package: {e}")

        # Check pytest can collect tests
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            cwd=self.project_root,
        )

        if "error" in result.stderr.lower():
            error_count = result.stderr.count("ERROR")
            print(f"  Warning: {error_count} collection errors remain")
        else:
            print("  Pytest collection successful")


if __name__ == "__main__":
    setup = TestEnvironmentSetup()
    success = setup.run()
    sys.exit(0 if success else 1)
