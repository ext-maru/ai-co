"""
Code Generation Template Registry for AI Company
すべてのコード生成テンプレートを管理
"""

import importlib
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

class TemplateRegistry:
    """テンプレートレジストリ"""
    
    def __init__(self):
        self.templates = {}
        self.template_dir = Path(__file__).parent
        self._load_templates()
    
    def _load_templates(self):
        """テンプレートを自動ロード"""
        # Import templates
        from .rest_api_template import RestApiTemplate
        from .database_model_template import DatabaseModelTemplate
        from .cli_command_template import CliCommandTemplate
        
        # Register templates
        self.register("rest_api", RestApiTemplate())
        self.register("database_model", DatabaseModelTemplate())
        self.register("cli_command", CliCommandTemplate())
    
    def register(self, name: str, template: Any):
        """テンプレートを登録"""
        self.templates[name] = template
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """利用可能なテンプレートをリスト"""
        templates = []
        for name, template in self.templates.items():
            info = template.template_info.copy()
            info["key"] = name
            templates.append(info)
        return templates
    
    def get_template(self, name: str) -> Optional[Any]:
        """テンプレートを取得"""
        return self.templates.get(name)
    
    def generate(self, template_name: str, params: Dict[str, Any]) -> Dict[str, str]:
        """テンプレートからコードを生成"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        # Validate parameters
        self._validate_params(template, params)
        
        # Generate code
        return template.generate(params)
    
    def _validate_params(self, template: Any, params: Dict[str, Any]):
        """パラメータを検証"""
        template_params = template.template_info.get("parameters", {})
        
        # Check required parameters
        for param_name, param_info in template_params.items():
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
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """テンプレートの情報を取得"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        return template.template_info
    
    def save_generated_code(self, output_dir: str, files: Dict[str, str]):
        """生成されたコードを保存"""
        output_path = Path(output_dir)
        
        for filepath, content in files.items():
            full_path = output_path / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Generated: {full_path}")

# CLI interface
def main():
    """CLI インターフェース"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='AI Company Code Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available templates')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate code from template')
    gen_parser.add_argument('template', help='Template name')
    gen_parser.add_argument('--params', '-p', type=str, 
                           help='Parameters as JSON string or file path')
    gen_parser.add_argument('--output', '-o', default='./generated',
                           help='Output directory')
    gen_parser.add_argument('--interactive', '-i', action='store_true',
                           help='Interactive mode')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show template information')
    info_parser.add_argument('template', help='Template name')
    
    args = parser.parse_args()
    
    registry = TemplateRegistry()
    
    if args.command == 'list':
        templates = registry.list_templates()
        print("📋 Available Templates:")
        print("=" * 60)
        for tmpl in templates:
            print(f"\n🔧 {tmpl['key']}")
            print(f"   Name: {tmpl['name']}")
            print(f"   Version: {tmpl['version']}")
            print(f"   Description: {tmpl['description']}")
    
    elif args.command == 'generate':
        # Load parameters
        params = {}
        if args.params:
            if args.params.startswith('{'):
                # JSON string
                params = json.loads(args.params)
            elif os.path.exists(args.params):
                # JSON file
                with open(args.params, 'r') as f:
                    params = json.load(f)
            else:
                print(f"❌ Invalid params: {args.params}")
                return
        
        # Interactive mode
        if args.interactive:
            template_info = registry.get_template_info(args.template)
            print(f"🔧 Generating {template_info['name']}")
            print("Please provide parameters:")
            
            for param_name, param_info in template_info['parameters'].items():
                if param_info.get('required', False):
                    value = input(f"  {param_name} ({param_info['description']}): ")
                    params[param_name] = value
        
        try:
            # Generate code
            files = registry.generate(args.template, params)
            
            # Save files
            registry.save_generated_code(args.output, files)
            
            print(f"\n✅ Code generated successfully in {args.output}")
            
        except Exception as e:
            print(f"❌ Generation failed: {e}")
    
    elif args.command == 'info':
        try:
            info = registry.get_template_info(args.template)
            print(f"📋 Template: {info['name']}")
            print(f"Version: {info['version']}")
            print(f"Description: {info['description']}")
            print(f"Author: {info['author']}")
            print("\nParameters:")
            
            for param_name, param_info in info['parameters'].items():
                required = "Required" if param_info.get('required', False) else "Optional"
                print(f"\n  {param_name} ({required})")
                print(f"    Type: {param_info['type']}")
                print(f"    Description: {param_info['description']}")
                if 'default' in param_info:
                    print(f"    Default: {param_info['default']}")
                if 'choices' in param_info:
                    print(f"    Choices: {param_info['choices']}")
        
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()