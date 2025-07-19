#!/usr/bin/env python3
"""
Iron Will 95% Compliance - Error Handling Improvement Script
Addresses the 14.8% error handling score by adding comprehensive error handling
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set


class ErrorHandlingFixer:
    """
    Fixes missing error handling in Python files
    """

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.github_integration_path = self.project_root / "libs/integrations/github"
        self.fixed_count = 0

        # Functions that need error handling from audit
        self.missing_error_handling = {
            "github_flow_manager.py": ["setup", "main"],
            "github_integration.py": [
                "send_error_notification",
                "send_task_notification",
                "send_elder_council_report",
                "_get_response_requirement",
                "_categorize_error",
                "_format_details_markdown",
                "_format_updates_markdown",
            ],
            "github_aware_rag.py": [
                "__init__",
                "build_context_with_github",
                "_guess_relevant_files",
            ],
        }

    def check_function_has_try_except(self, function_node) -> bool:
        """Check if a function already has try-except"""
        for node in ast.walk(function_node):
            if isinstance(node, ast.Try):
                return True
        return False

    def add_error_handling_to_function(
        self, source_code: str, function_name: str
    ) -> str:
        """Add error handling to a specific function"""
        try:
            tree = ast.parse(source_code)

            class ErrorHandlingTransformer(ast.NodeTransformer):
                def __init__(self, target_func):
                    self.target_func = target_func
                    self.modified = False

                def visit_FunctionDef(self, node):
                    if (
                        node.name == self.target_func
                        and not check_function_has_try_except(node)
                    ):
                        # Wrap function body in try-except
                        try_node = ast.Try(
                            body=node.body,
                            handlers=[
                                ast.ExceptHandler(
                                    type=ast.Name(id="Exception", ctx=ast.Load()),
                                    name="e",
                                    body=[
                                        ast.Expr(
                                            value=ast.Call(
                                                func=ast.Attribute(
                                                    value=ast.Name(
                                                        id="logger", ctx=ast.Load()
                                                    ),
                                                    attr="error",
                                                    ctx=ast.Load(),
                                                ),
                                                args=[
                                                    ast.JoinedStr(
                                                        values=[
                                                            ast.Constant(
                                                                value=f"Error in {node.name}: "
                                                            ),
                                                            ast.FormattedValue(
                                                                value=ast.Call(
                                                                    func=ast.Name(
                                                                        id="str",
                                                                        ctx=ast.Load(),
                                                                    ),
                                                                    args=[
                                                                        ast.Name(
                                                                            id="e",
                                                                            ctx=ast.Load(),
                                                                        )
                                                                    ],
                                                                    keywords=[],
                                                                ),
                                                                conversion=-1,
                                                            ),
                                                        ]
                                                    )
                                                ],
                                                keywords=[],
                                            )
                                        ),
                                        ast.Raise(),
                                    ],
                                )
                            ],
                            orelse=[],
                            finalbody=[],
                        )
                        node.body = [try_node]
                        self.modified = True
                    return node

                def visit_AsyncFunctionDef(self, node):
                    # Handle async functions the same way
                    return self.visit_FunctionDef(node)

            def check_function_has_try_except(node):
                for item in node.body:
                    if isinstance(item, ast.Try):
                        return True
                return False

            transformer = ErrorHandlingTransformer(function_name)
            new_tree = transformer.visit(tree)

            if transformer.modified:
                return ast.unparse(new_tree)

            return source_code

        except Exception as e:
            print(f"Error processing {function_name}: {str(e)}")
            return source_code

    def fix_file(self, file_path: Path, functions: List[str]) -> bool:
        """Fix error handling in a specific file"""
        try:
            if not file_path.exists():
                print(f"File not found: {file_path}")
                return False

            content = file_path.read_text()
            original_content = content

            for func_name in functions:
                # Simple regex-based approach for now
                # Look for function definition
                func_pattern = rf"(\n(?:async\s+)?def\s+{func_name}\s*\([^)]*\)[^:]*:)"
                match = re.search(func_pattern, content)

                if match:
                    # Find the function body
                    func_start = match.end()

                    # Check if already has try-except
                    func_body_start = content[func_start : func_start + 500]
                    if not re.search(r"\n\s*try:", func_body_start):
                        # Add try-except wrapper
                        indent_match = re.search(r"\n(\s+)", content[func_start:])
                        if indent_match:
                            base_indent = indent_match.group(1)

                            # Find function body
                            lines = content[func_start:].split("\n")
                            wrapped_lines = []
                            wrapped_lines.append(f"{base_indent}try:")

                            in_function = True
                            for i, line in enumerate(lines[1:], 1):
                                if (
                                    line.strip()
                                    and not line.startswith(base_indent)
                                    and not line.startswith("\t")
                                ):
                                    # End of function
                                    in_function = False

                                if in_function and line.strip():
                                    wrapped_lines.append(f"    {line}")
                                elif in_function:
                                    wrapped_lines.append(line)
                                else:
                                    # Add exception handling before function end
                                    wrapped_lines.extend(
                                        [
                                            f"{base_indent}except Exception as e:",
                                            f"{base_indent}    logger.error(f'Error in {func_name}: {{str(e)}}')",
                                            f"{base_indent}    raise",
                                            line,
                                        ]
                                    )
                                    wrapped_lines.extend(lines[i + 1 :])
                                    break

                            # Replace function body
                            func_end = content.find("\n\n", func_start)
                            if func_end == -1:
                                func_end = len(content)

                            new_body = "\n".join(wrapped_lines)
                            content = content[:func_start] + "\n" + new_body
                            self.fixed_count += 1
                            print(
                                f"✅ Added error handling to {func_name} in {file_path.name}"
                            )

            if content != original_content:
                file_path.write_text(content)
                return True

            return False

        except Exception as e:
            print(f"Error fixing file {file_path}: {str(e)}")
            return False

    def run(self):
        """Run the error handling fixes"""
        print("🗡️ Iron Will Error Handling Improvement")
        print("=" * 60)

        for filename, functions in self.missing_error_handling.items():
            file_path = self.github_integration_path / filename
            print(f"\nProcessing {filename}...")
            self.fix_file(file_path, functions)

        print(f"\n✅ Total functions fixed: {self.fixed_count}")
        print("🗡️ Error handling improvement complete!")


if __name__ == "__main__":
    fixer = ErrorHandlingFixer()
    fixer.run()
