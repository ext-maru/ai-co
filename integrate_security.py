#!/usr/bin/env python3
"""
Integrate Security Features into GitHub APIs
Iron Will 95% Compliance
"""

import os
import re
from pathlib import Path
from typing import List, Dict

class SecurityIntegrator:
    """
    Integrates security features into existing GitHub API implementations
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.api_implementations_path = self.project_root / "libs/integrations/github/api_implementations"
        self.security_import = """from libs.integrations.github.security import get_security_manager, SecurityViolationError
"""
        self.integrated_count = 0
    
    def add_security_to_file(self, file_path: Path) -> bool:
        """Add security features to a single API file"""
        try:
            if not file_path.exists() or file_path.suffix != '.py':
                return False
            
            content = file_path.read_text()
            original_content = content
            
            # Skip if already has security import
            if 'get_security_manager' in content:
                print(f"⏭️  {file_path.name} already has security integration")
                return False
            
            # Add security import after existing imports
            import_match = re.search(r'(import .*\n)+', content)
            if import_match:
                insert_pos = import_match.end()
                content = content[:insert_pos] + "\n" + self.security_import + content[insert_pos:]
            
            # Add security manager initialization in __init__ methods
            init_pattern = r'(def __init__\(self[^)]*\)[^:]*:\s*\n(?:\s*"""[^"]*"""\s*\n)?)'
            init_matches = list(re.finditer(init_pattern, content))
            
            for match in reversed(init_matches):
                init_end = match.end()
                # Find the indentation
                lines_after = content[init_end:].split('\n')
                if lines_after and lines_after[0].strip():
                    indent_match = re.match(r'^(\s+)', lines_after[0])
                    if indent_match:
                        indent = indent_match.group(1)
                        security_init = f"{indent}self.security_manager = get_security_manager()\n"
                        content = content[:init_end] + security_init + content[init_end:]
            
            # Add input validation to key methods
            # Find methods that accept string parameters
            method_pattern = r'(async def|def) (create_|update_|merge_|list_|get_)([^(]+)\([^)]*\):'
            method_matches = list(re.finditer(method_pattern, content))
            
            for match in reversed(method_matches):
                method_name = match.group(2) + match.group(3)
                method_start = match.end()
                
                # Find method body indentation
                lines_after = content[method_start:].split('\n')
                if len(lines_after) > 1:
                    body_line = next((line for line in lines_after[1:] if line.strip()), None)
                    if body_line:
                        indent_match = re.match(r'^(\s+)', body_line)
                        if indent_match:
                            indent = indent_match.group(1)
                            
                            # Add security validation for common parameters
                            security_checks = []
                            
                            # Check method signature for common parameters
                            method_sig = content[match.start():match.end()]
                            
                            if 'repo' in method_sig:
                                security_checks.append(f"{indent}if 'repo' in locals():\n{indent}    repo = self.security_manager.validate_and_sanitize_input(repo, 'repo_name')")
                            if 'owner' in method_sig:
                                security_checks.append(f"{indent}if 'owner' in locals():\n{indent}    owner = self.security_manager.validate_and_sanitize_input(owner, 'username')")
                            if 'title' in method_sig:
                                security_checks.append(f"{indent}if 'title' in locals():\n{indent}    title = self.security_manager.validate_and_sanitize_input(title, 'title')")
                            if 'body' in method_sig:
                                security_checks.append(f"{indent}if 'body' in locals():\n{indent}    body = self.security_manager.validate_and_sanitize_input(body, 'body')")
                            if 'branch' in method_sig:
                                security_checks.append(f"{indent}if 'branch' in locals():\n{indent}    branch = self.security_manager.validate_and_sanitize_input(branch, 'branch_name')")
                            
                            if security_checks:
                                # Find where to insert (after docstring if exists)
                                insert_pos = method_start
                                docstring_match = re.search(r'\n\s+"""[^"]*"""\s*\n', content[method_start:method_start+1000])
                                if docstring_match:
                                    insert_pos = method_start + docstring_match.end()
                                else:
                                    insert_pos = method_start + 1
                                
                                security_block = "\n" + "\n".join(security_checks) + "\n"
                                content = content[:insert_pos] + security_block + content[insert_pos:]
            
            # Add HTTPS enforcement to URL validation
            https_pattern = r'(if not .*\.startswith\(["\']https://["\']\):)'
            if not re.search(https_pattern, content):
                # Find base_url validation
                url_pattern = r'(self\.base_url = base_url)'
                url_match = re.search(url_pattern, content)
                if url_match:
                    insert_pos = url_match.end()
                    # Find indentation
                    line_start = content.rfind('\n', 0, url_match.start()) + 1
                    line = content[line_start:url_match.end()]
                    indent_match = re.match(r'^(\s+)', line)
                    if indent_match:
                        indent = indent_match.group(1)
                        https_check = f'\n{indent}if not self.base_url.startswith("https://"):\n{indent}    raise SecurityViolationError("Only HTTPS URLs are allowed")'
                        content = content[:insert_pos] + https_check + content[insert_pos:]
            
            if content != original_content:
                file_path.write_text(content)
                self.integrated_count += 1
                print(f"✅ Security integrated into {file_path.name}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error integrating security into {file_path}: {str(e)}")
            return False
    
    def run(self):
        """Run security integration"""
        print("🔒 Integrating Security Features into GitHub APIs")
        print("=" * 60)
        
        # Get all API implementation files
        api_files = list(self.api_implementations_path.glob("*.py"))
        
        # Skip __init__.py
        api_files = [f for f in api_files if f.name != "__init__.py"]
        
        print(f"Found {len(api_files)} API implementation files")
        
        for api_file in api_files:
            self.add_security_to_file(api_file)
        
        print(f"\n✅ Security integrated into {self.integrated_count} files")
        print("🔒 Security integration complete!")

if __name__ == "__main__":
    integrator = SecurityIntegrator()
    integrator.run()