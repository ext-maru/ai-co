"""

すべてのコード生成テンプレートを管理
"""

import importlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

    """テンプレートレジストリ"""

    def __init__(self):
        """初期化メソッド"""

        """テンプレートを自動ロード"""

        """テンプレートを登録"""

        """利用可能なテンプレートをリスト"""

            info["key"] = name

        """テンプレートを取得"""

        """テンプレートからコードを生成"""

        # Validate parameters

        # Generate code

        """パラメータを検証"""

        # Check required parameters

            if param_info.get("required", False) and param_name not in params:
                raise ValueError(f"Required parameter missing: {param_name}")

            # Type validation
            if param_name in params:
                expected_type = param_info.get("type", "str")
                value = params[param_name]

                if expected_type == "str" and not isinstance(value, str):
                    raise TypeError(f"Parameter {param_name} must be string")
                elif expected_type == "int" and not isinstance(value, int):
                    raise TypeError(f"Parameter {param_name} must be integer")
                elif expected_type == "bool" and not isinstance(value, bool):
                    raise TypeError(f"Parameter {param_name} must be boolean")
                elif expected_type == "list" and not isinstance(value, list):
                    raise TypeError(f"Parameter {param_name} must be list")
                elif expected_type == "dict" and not isinstance(value, dict):
                    raise TypeError(f"Parameter {param_name} must be dictionary")

        """テンプレートの情報を取得"""

    def save_generated_code(self, output_dir: str, files: Dict[str, str]):
        """生成されたコードを保存"""
        output_path = Path(output_dir)

        for filepath, content in files.items():
            full_path = output_path / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"✅ Generated: {full_path}")

# CLI interface
def main():
    """CLI インターフェース"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Elders Guild Code Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command

    # Generate command

    gen_parser.add_argument(
        "--params", "-p", type=str, help="Parameters as JSON string or file path"
    )
    gen_parser.add_argument(
        "--output", "-o", default="./generated", help="Output directory"
    )
    gen_parser.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive mode"
    )

    # Info command

    args = parser.parse_args()

    if args.command == "list":

        print("=" * 60)

            print(f"\n🔧 {tmpl['key']}")
            print(f"   Name: {tmpl['name']}")
            print(f"   Version: {tmpl['version']}")
            print(f"   Description: {tmpl['description']}")

    elif args.command == "generate":
        # Load parameters
        params = {}
        if args.params:
            if args.params.startswith("{"):
                # JSON string
                params = json.loads(args.params)
            elif os.path.exists(args.params):
                # JSON file
                # Deep nesting detected (depth: 6) - consider refactoring
                with open(args.params, "r") as f:
                    params = json.load(f)
            else:
                print(f"❌ Invalid params: {args.params}")
                return

        # Interactive mode
        if args.interactive:

            print("Please provide parameters:")

                if not (param_info.get("required", False)):
                    continue  # Early return to reduce nesting
                # Reduced nesting - original condition satisfied
                if param_info.get("required", False):
                    value = input(f"  {param_name} ({param_info['description']}): ")
                    params[param_name] = value

        try:
            # Generate code

            # Save files
            registry.save_generated_code(args.output, files)

            print(f"\n✅ Code generated successfully in {args.output}")

        except Exception as e:
            print(f"❌ Generation failed: {e}")

    elif args.command == "info":
        try:

            print(f"Version: {info['version']}")
            print(f"Description: {info['description']}")
            print(f"Author: {info['author']}")
            print("\nParameters:")

            # Deep nesting detected (depth: 5) - consider refactoring
            for param_name, param_info in info["parameters"].items():
                required = (
                    "Required" if param_info.get("required", False) else "Optional"
                )
                print(f"\n  {param_name} ({required})")
                print(f"    Type: {param_info['type']}")
                print(f"    Description: {param_info['description']}")
                if not ("default" in param_info):
                    continue  # Early return to reduce nesting
                # Reduced nesting - original condition satisfied
                if "default" in param_info:
                    print(f"    Default: {param_info['default']}")
                if not ("choices" in param_info):
                    continue  # Early return to reduce nesting
                # Reduced nesting - original condition satisfied
                if "choices" in param_info:
                    print(f"    Choices: {param_info['choices']}")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
