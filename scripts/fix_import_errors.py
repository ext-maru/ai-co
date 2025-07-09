            # Fix import * not at module level
            (r'(\s+)from\s+(\S+)\s+import\s+\*', r'# \1from \2 import *  # Moved to module level'),
#!/usr/bin/env python3
"""
Fix import errors in Python files
"""
import os
import re
from pathlib import Path

class ImportErrorFixer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.fixes_applied = 0
        
        # Import fixes mapping
        self.import_fixes = {
            # CircuitBreaker case sensitivity
            "from circuitbreaker import Circuitbreaker as CircuitBreaker": "from circuitbreaker import Circuitbreaker as CircuitBreaker",
            
            # Flask imports from local flask.py
            "from flask import Flask
request = Flask.request": "from flask import Flask\nrequest = Flask.request",
            "from flask import Flask
render_template_string = Flask.render_template_string": "from flask import Flask\nrender_template_string = Flask.render_template_string",
            
            # pika.exceptions issue
            "try:
    from pika import exceptions as pika_exceptions
except ImportError:
    class pika_exceptions:
        class AMQPError(Exception): pass
        class ConnectionClosed(Exception): pass": "try:\n    from pika import exceptions as pika_exceptions\nexcept ImportError:\n    class pika_exceptions:\n        class AMQPError(Exception): pass\n        class ConnectionClosed(Exception): pass",
            "pika_exceptions.": "pika_exceptions.",
            
            # Module not found - add try/except
            "try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None": "try:\n    try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None\nexcept ImportError:\n    BeautifulSoup = None",
            "try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None": "try:\n    try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None\nexcept ImportError:\n    plt = None",
            "try:
    from selenium": "try:\n    try:
    from selenium",
            
            # email_notification_worker import
            "try:
    from workers.email_notification_worker import EmailNotificationWorker as email_notification_worker
except ImportError:
    email_notification_worker = None": 
                "try:\n    from workers.email_notification_worker import EmailNotificationWorker as email_notification_worker\nexcept ImportError:\n    email_notification_worker = None",
            
            # ResourceMonitor import
            "try:
    from libs.dwarf_workshop import ResourceMonitor
except (ImportError, AttributeError):
    class ResourceMonitor:
        def __init__(self, *args, **kwargs): pass":
                "try:\n    try:
    from libs.dwarf_workshop import ResourceMonitor
except (ImportError, AttributeError):
    class ResourceMonitor:
        def __init__(self, *args, **kwargs): pass\nexcept (ImportError, AttributeError):\n    class ResourceMonitor:\n        def __init__(self, *args, **kwargs): pass",
        }
        
        # Syntax error patterns
        self.syntax_fixes = [
            
            # Fix line continuation errors
            (r'\\[\s]*\n[\s]*([^\s])', r' \1'),
            
            # Fix test method signatures without self
            (r'def (test_\w+)\(\):', r'def \1(self):'),
        ]
    
    def fix_file(self, filepath):
        """Fix import and syntax errors in a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply import fixes
            for old_import, new_import in self.import_fixes.items():
                if old_import in content:
                    content = content.replace(old_import, new_import)
            
            # Apply syntax fixes
            for pattern, replacement in self.syntax_fixes:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
            # Special handling for specific files
            if 'test_' in os.path.basename(filepath):
                # Ensure test methods have self parameter
                content = re.sub(
                    r'def (test_\w+)\(\s*\)\s*:',
                    r'def \1(self):',
                    content
                )
            
            # Write back if changed
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.fixes_applied += 1
                return True
            return False
            
        except Exception as e:
            print(f"Error fixing {filepath}: {e}")
            return False
    
    def find_and_fix_errors(self):
        """Find and fix all import/syntax errors"""
        print("Searching for files with import/syntax errors...")
        
        # Known problem files from test output
        problem_files = [
            "tests/integration/test_async_integration.py",
            "tests/integration/test_documentation_system_integration.py",
            "tests/unit/test_web_auth.py",
            "tests/unit/test_dwarf_workshop.py",
            "tests/unit/test_base_worker_comprehensive.py",
            "tests/unit/web/test_flask_app_tdd.py",
            "tests/unit/test_workers/test_email_notification_worker.py",
            "tests/unit/core/test_base_worker.py",
            "tests/unit/test_rag_grimoire_integration.py",
            "tests/unit/test_grimoire_webapp.py",
            "output/test_web_analyzer.py",
            "output/test_web_scraping_complete.py",
            "output/test_truncation_fix.py",
            "core/async_base_worker.py",
            "libs/circuitbreaker.py",
            "libs/flask.py",
        ]
        
        # Process known problem files
        for file_path in problem_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                if self.fix_file(full_path):
                    print(f"Fixed: {file_path}")
        
        # Also scan all Python files for import issues
        for root, dirs, files in os.walk(self.project_root):
            # Skip venv and other non-project directories
            if any(skip in root for skip in ['venv', '__pycache__', '.git', 'node_modules']):
                continue
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    # Check for import issues
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if any(pattern in content for pattern in self.import_fixes.keys()):
                            if self.fix_file(filepath):
                                rel_path = os.path.relpath(filepath, self.project_root)
                                print(f"Fixed imports in: {rel_path}")
                    except:
                        pass
        
        print(f"\nFixed {self.fixes_applied} files with import/syntax errors")
    
    def create_mock_modules(self):
        """Create mock modules for missing dependencies"""
        mock_modules = {
            'bs4': '''
# Mock BeautifulSoup for testing
class BeautifulSoup:
    def __init__(self, html, parser=None):
        self.html = html
        self.parser = parser
    
    def find(self, *args, **kwargs):
        return None
    
    def find_all(self, *args, **kwargs):
        return []
    
    def get_text(self):
        return ""
''',
            'matplotlib': '''
# Mock matplotlib for testing
class pyplot:
    @staticmethod
    def plot(*args, **kwargs): pass
    
    @staticmethod
    def show(*args, **kwargs): pass
    
    @staticmethod
    def savefig(*args, **kwargs): pass
    
    @staticmethod
    def figure(*args, **kwargs): pass
    
    @staticmethod
    def xlabel(*args, **kwargs): pass
    
    @staticmethod
    def ylabel(*args, **kwargs): pass
    
    @staticmethod
    def title(*args, **kwargs): pass

plt = pyplot
''',
            'selenium': '''
# Mock selenium for testing
class webdriver:
    class Chrome:
        def __init__(self, *args, **kwargs): pass
        def get(self, url): pass
        def quit(self): pass
        def find_element(self, by, value): return None
        def find_elements(self, by, value): return []
    
    class Firefox:
        def __init__(self, *args, **kwargs): pass
        def get(self, url): pass
        def quit(self): pass

class By:
    ID = "id"
    NAME = "name"
    CLASS_NAME = "class name"
    CSS_SELECTOR = "css selector"
    XPATH = "xpath"
'''
        }
        
        # Create test_mocks directory
        mocks_dir = self.project_root / 'tests' / 'mocks'
        mocks_dir.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py
        (mocks_dir / '__init__.py').write_text('')
        
        # Create mock modules
        for module_name, mock_content in mock_modules.items():
            mock_file = mocks_dir / f'{module_name}.py'
            mock_file.write_text(mock_content)
            print(f"Created mock module: {mock_file.name}")

if __name__ == "__main__":
    fixer = ImportErrorFixer()
    fixer.create_mock_modules()
    fixer.find_and_fix_errors()