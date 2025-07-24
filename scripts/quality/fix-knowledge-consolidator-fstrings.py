#!/usr/bin/env python3
"""Fix f-string syntax errors in knowledge_consolidator.py"""

import re

file_path = "libs/knowledge_consolidator.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the position of the HTML generation section
html_start = content.find('{"".join(')
if html_start != -1:
    # Find the complete _generate_html_report method
    method_start = content.rfind('def _generate_html_report', 0, html_start)
    method_end = content.find('\n\n    def ', html_start)
    if method_end == -1:
        method_end = content.find('\n\nif __name__', html_start)
    
    if method_start != -1 and method_end != -1:
        # Extract the method
        method_content = content[method_start:method_end]
        
        # Fix the malformed f-string in Workers table
        method_content = method_content.replace(
            '''{"".join(
                (
                    f"f"<tr><td>{name}</td><td>{', '.join(info.get('classes', []))}</td><td>"
                    f"{len(info.get('functions', []))}</td><td>{info.get('lines', 0)}</td></tr>" for name,"
                )
                info in data['implementations']['workers'].items()
            )}''',
            '''{"".join(
                f"<tr><td>{name}</td><td>{', '.join(info.get('classes', []))}</td><td>"
                f"{len(info.get('functions', []))}</td><td>{info.get('lines', 0)}</td></tr>"
                for name, info in data['implementations']['workers'].items()
            )}'''
        )
        
        # Fix the malformed f-string in Managers table
        method_content = method_content.replace(
            '''{"".join(
                (
                    f"f"<tr><td>{name}</td><td>{', '.join(info.get('classes', []))}</td><td>"
                    f"{len(info.get('functions', []))}</td><td>{info.get('lines', 0)}</td></tr>" for name,"
                )
                info in data['implementations']['managers'].items()
            )}''',
            '''{"".join(
                f"<tr><td>{name}</td><td>{', '.join(info.get('classes', []))}</td><td>"
                f"{len(info.get('functions', []))}</td><td>{info.get('lines', 0)}</td></tr>"
                for name, info in data['implementations']['managers'].items()
            )}'''
        )
        
        # Fix the Knowledge Base table
        method_content = method_content.replace(
            '''                        { \\
                "".join(f"<tr><td>{f['filename']}</td><td>{f['lines']}<" \\
                    f"/td><td>{f['modified']}</td></tr>" for f in data['knowledge']['files'])}''',
            '''            {"".join(
                f"<tr><td>{f['filename']}</td><td>{f['lines']}</td><td>{f['modified']}</td></tr>"
                for f in data['knowledge']['files']
            )}'''
        )
        
        # Close the missing div tag in stats
        method_content = method_content.replace(
            '''            </div>
        </div>

        <h2>🏗️ Architecture</h2>''',
            '''            </div>
        </div>

        <h2>🏗️ Architecture</h2>'''
        )
        
        # Replace the method in the content
        content = content[:method_start] + method_content + content[method_end:]

# Save the fixed content
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed f-string syntax errors in knowledge_consolidator.py")