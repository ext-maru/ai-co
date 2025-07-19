"""
CLI Command Generator Template for Elders Guild
Click ベースのコマンドラインツールを生成
"""

from typing import Any, Dict, List, Optional


class CliCommandTemplate:
    """CLIコマンドテンプレート"""

    def __init__(self):
        self.template_info = {
            "name": "CLI Command",
            "version": "1.0.0",
            "description": "Generate Click-based CLI commands with proper structure",
            "author": "Elders Guild",
            "parameters": {
                "command_name": {
                    "type": "str",
                    "required": True,
                    "description": "Name of the command (e.g., 'deploy', 'backup')",
                },
                "description": {
                    "type": "str",
                    "required": True,
                    "description": "Command description",
                },
                "arguments": {
                    "type": "list",
                    "default": [],
                    "description": "List of positional arguments",
                },
                "options": {
                    "type": "list",
                    "default": [],
                    "description": "List of command options",
                },
                "subcommands": {
                    "type": "list",
                    "default": [],
                    "description": "List of subcommands",
                },
                "confirmation": {
                    "type": "bool",
                    "default": False,
                    "description": "Require confirmation before execution",
                },
                "async_command": {
                    "type": "bool",
                    "default": False,
                    "description": "Generate async command",
                },
            },
        }

    def generate_main_command(self, params: Dict[str, Any]) -> str:
        """メインコマンドファイルを生成"""
        command_name = params["command_name"]
        description = params["description"]
        arguments = params.get("arguments", [])
        options = params.get("options", [])
        subcommands = params.get("subcommands", [])
        is_async = params.get("async_command", False)

        content = f'''#!/usr/bin/env python3
"""
{command_name.upper()} CLI - {description}
"""
import click
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import json
from datetime import datetime
{"import asyncio" if is_async else ""}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('{command_name}')

# Version
__version__ = '1.0.0'

# Context settings
CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    max_content_width=120
)

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name='{command_name}')
@click.option('--config', '-c',
              type=click.Path(exists=True),
              help='Configuration file path')
@click.option('--verbose', '-v',
              is_flag=True,
              help='Enable verbose output')
@click.option('--quiet', '-q',
              is_flag=True,
              help='Suppress all output except errors')
@click.pass_context
def cli(ctx, config, verbose, quiet):
    """
    {description}

    Examples:
        {command_name} --help
        {command_name} --version
        {command_name} [COMMAND] --help
    """
    # Setup context
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet

    # Configure logging
    if quiet:
        logger.setLevel(logging.ERROR)
    elif verbose:
        logger.setLevel(logging.DEBUG)

    # Load configuration
    if config:
        try:
            with open(config, 'r') as f:
                ctx.obj['config_data'] = json.load(f)
            logger.debug(f"Loaded configuration from {{config}}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {{e}}")
            sys.exit(1)
'''

        # Add subcommands
        if subcommands:
            for subcmd in subcommands:
                content += self._generate_subcommand(subcmd, is_async)
        else:
            # Single command mode
            content += self._generate_single_command(params)

        content += """
if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo('\\nOperation cancelled by user', err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if logger.level == logging.DEBUG:
            import traceback
            traceback.print_exc()
        sys.exit(1)
"""

        return content

    def _generate_subcommand(
        self, subcmd: Dict[str, Any], is_async: bool = False
    ) -> str:
        """サブコマンドを生成"""
        name = subcmd.get("name", "subcommand")
        desc = subcmd.get("description", "Subcommand")
        args = subcmd.get("arguments", [])
        opts = subcmd.get("options", [])
        confirmation = subcmd.get("confirmation", False)

        decorator = (
            "cli.command()" if not is_async else "cli.command()\n@click.coroutine"
        )

        content = f"""
@{decorator}
"""

        # Add arguments
        for arg in args:
            arg_name = arg.get("name", "arg")
            arg_type = arg.get("type", "str")
            arg_help = arg.get("help", "")
            arg_required = arg.get("required", True)

            click_type = self._get_click_type(arg_type)

            if arg_required:
                content += f"@click.argument('{arg_name}', type={click_type})\n"
            else:
                content += f"@click.argument('{arg_name}', type={click_type}, required=False)\n"

        # Add options
        for opt in opts:
            content += self._generate_option(opt)

        content += f"""@click.pass_context
{"async " if is_async else ""}def {name}(ctx, """

        # Add parameter names
        param_names = [arg.get("name", "arg") for arg in args]
        param_names.extend([opt.get("name", "opt").replace("-", "_") for opt in opts])
        content += ", ".join(param_names)

        content += f'''):
    """
    {desc}
    """
    logger = logging.getLogger('{name}')
    config = ctx.obj.get('config_data', {{}})

'''

        if confirmation:
            content += """    # Confirmation prompt
    if not click.confirm('Are you sure you want to continue?'):
        click.echo('Operation cancelled')
        return

"""

        content += f"""    try:
        # Validate inputs
        logger.debug("Validating inputs...")

        # TODO: Add validation logic here

        # Execute command
        click.echo(f"Executing {name}...")

        # TODO: Add command implementation here
        {"await execute_async_task()" if is_async else "execute_task()"}

        click.secho("✅ Command completed successfully!", fg='green')

    except ValueError as e:
        click.secho(f"❌ Validation error: {{e}}", fg='red', err=True)
        ctx.exit(1)
    except Exception as e:
        logger.error(f"Command failed: {{e}}")
        click.secho(f"❌ Command failed: {{e}}", fg='red', err=True)
        ctx.exit(1)
"""

        return content

    def _generate_single_command(self, params: Dict[str, Any]) -> str:
        """単一コマンドモードを生成"""
        arguments = params.get("arguments", [])
        options = params.get("options", [])
        confirmation = params.get("confirmation", False)

        content = """
@cli.command()
"""

        # Add arguments and options
        for arg in arguments:
            content += self._generate_argument(arg)

        for opt in options:
            content += self._generate_option(opt)

        content += """@click.pass_context
def run(ctx, """

        # Parameter names
        param_names = [arg.get("name", "arg") for arg in arguments]
        param_names.extend(
            [opt.get("name", "opt").replace("-", "_") for opt in options]
        )
        content += ", ".join(param_names)

        content += '''):
    """Execute the command"""
    # Implementation here
    pass
'''

        return content

    def _generate_option(self, opt: Dict[str, Any]) -> str:
        """オプションを生成"""
        name = opt.get("name", "option")
        short = opt.get("short", name[0])
        opt_type = opt.get("type", "str")
        default = opt.get("default", None)
        help_text = opt.get("help", "")
        is_flag = opt.get("is_flag", False)
        multiple = opt.get("multiple", False)

        click_type = self._get_click_type(opt_type)

        decorator = f"@click.option('--{name}', '-{short}'"

        if is_flag:
            decorator += ", is_flag=True"
        else:
            decorator += f", type={click_type}"

        if default is not None:
            decorator += f", default={repr(default)}"

        if multiple:
            decorator += ", multiple=True"

        if help_text:
            decorator += f", help='{help_text}'"

        decorator += ")\n"

        return decorator

    def _generate_argument(self, arg: Dict[str, Any]) -> str:
        """引数を生成"""
        name = arg.get("name", "arg")
        arg_type = arg.get("type", "str")
        required = arg.get("required", True)

        click_type = self._get_click_type(arg_type)

        decorator = f"@click.argument('{name}', type={click_type}"

        if not required:
            decorator += ", required=False"

        decorator += ")\n"

        return decorator

    def _get_click_type(self, type_name: str) -> str:
        """Python型をClick型に変換"""
        type_map = {
            "str": "click.STRING",
            "int": "click.INT",
            "float": "click.FLOAT",
            "bool": "click.BOOL",
            "path": "click.Path()",
            "file": "click.File('r')",
            "choice": "click.Choice([])",  # Needs to be filled
            "uuid": "click.UUID",
        }
        return type_map.get(type_name, "click.STRING")

    def generate_setup(self, params: Dict[str, Any]) -> str:
        """setup.py を生成"""
        command_name = params["command_name"]
        description = params["description"]

        content = f'''"""
Setup script for {command_name} CLI
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="{command_name}",
    version="1.0.0",
    author="Elders Guild",
    author_email="support@aicompany.com",
    description="{description}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aicompany/{command_name}",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "colorama>=0.4.4",
        "python-dotenv>=0.19.0",
    ],
    entry_points={{
        "console_scripts": [
            "{command_name}={command_name}.cli:cli",
        ],
    }},
    include_package_data=True,
)
'''

        return content

    def generate_tests(self, params: Dict[str, Any]) -> str:
        """テストファイルを生成"""
        command_name = params["command_name"]
        subcommands = params.get("subcommands", [])

        content = f'''"""
Tests for {command_name} CLI
"""
import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os

from {command_name}.cli import cli

class TestCLI:
    """Test CLI commands"""

    @pytest.fixture
    def runner(self):
        """Create CLI runner"""
        return CliRunner()

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {{
                "setting1": "value1",
                "setting2": "value2"
            }}
            json.dump(config, f)
            yield f.name
        os.unlink(f.name)

    def test_cli_help(self, runner):
        """Test help command"""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert '{command_name}' in result.output

    def test_cli_version(self, runner):
        """Test version command"""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output

    def test_cli_with_config(self, runner, temp_config):
        """Test CLI with config file"""
        result = runner.invoke(cli, ['--config', temp_config, '--help'])
        assert result.exit_code == 0

    def test_verbose_mode(self, runner):
        """Test verbose mode"""
        result = runner.invoke(cli, ['--verbose', '--help'])
        assert result.exit_code == 0

    def test_quiet_mode(self, runner):
        """Test quiet mode"""
        result = runner.invoke(cli, ['--quiet', '--help'])
        assert result.exit_code == 0
'''

        # Add tests for subcommands
        for subcmd in subcommands:
            name = subcmd.get("name", "subcommand")
            content += f'''
    def test_{name}_command(self, runner):
        """Test {name} command"""
        result = runner.invoke(cli, ['{name}', '--help'])
        assert result.exit_code == 0
        assert '{name}' in result.output

    @patch('{command_name}.cli.execute_task')
    def test_{name}_execution(self, mock_execute, runner):
        """Test {name} execution"""
        mock_execute.return_value = None

        # Test with required arguments
        result = runner.invoke(cli, ['{name}', 'test_arg'])

        # Assertions depend on implementation
        # assert result.exit_code == 0
        # mock_execute.assert_called_once()
'''

        content += '''
    def test_keyboard_interrupt(self, runner):
        """Test keyboard interrupt handling"""
        with patch('{command_name}.cli.cli', side_effect=KeyboardInterrupt):
            result = runner.invoke(cli, [])
            assert result.exit_code == 1

    def test_unexpected_error(self, runner):
        """Test unexpected error handling"""
        with patch('{command_name}.cli.cli', side_effect=Exception("Test error")):
            result = runner.invoke(cli, [])
            assert result.exit_code == 1
'''

        return content

    def generate(self, params: Dict[str, Any]) -> Dict[str, str]:
        """テンプレートからコードを生成"""
        command_name = params["command_name"]

        files = {
            f"{command_name}/cli.py": self.generate_main_command(params),
            f"{command_name}/__init__.py": f'"""\\n{command_name} CLI package\\n"""\\n\\n__version__ = "1.0.0"\\n',
            f"setup.py": self.generate_setup(params),
            f"tests/test_{command_name}_cli.py": self.generate_tests(params),
            f"README.md": self._generate_readme(params),
        }

        # Add example config if needed
        if any(opt.get("name") == "config" for opt in params.get("options", [])):
            files["config.example.json"] = self._generate_example_config(params)

        return files

    def _generate_readme(self, params: Dict[str, Any]) -> str:
        """README.md を生成"""
        command_name = params["command_name"]
        description = params["description"]

        content = f"""# {command_name}

{description}

## Installation

```bash
pip install -e .
```

## Usage

```bash
{command_name} --help
```

## Commands

"""

        for subcmd in params.get("subcommands", []):
            name = subcmd.get("name", "subcommand")
            desc = subcmd.get("description", "")
            content += f"- `{name}`: {desc}\\n"

        content += """
## Configuration

Create a configuration file (see `config.example.json`):

```json
{
    "setting1": "value1",
    "setting2": "value2"
}
```

Use with: `{command_name} --config config.json`

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov={command_name}
```

## License

MIT License
"""

        return content

    def _generate_example_config(self, params: Dict[str, Any]) -> str:
        """設定ファイルの例を生成"""
        config = {
            "version": "1.0.0",
            "settings": {"debug": False, "timeout": 30, "max_retries": 3},
            "paths": {"data": "./data", "logs": "./logs"},
        }

        return json.dumps(config, indent=2)


# Usage example
if __name__ == "__main__":
    template = CliCommandTemplate()

    # Example parameters
    params = {
        "command_name": "aictl",
        "description": "Elders Guild Control CLI",
        "subcommands": [
            {
                "name": "deploy",
                "description": "Deploy AI models",
                "arguments": [{"name": "model", "type": "str", "help": "Model name"}],
                "options": [
                    {
                        "name": "environment",
                        "short": "e",
                        "type": "str",
                        "default": "production",
                        "help": "Target environment",
                    },
                    {
                        "name": "force",
                        "short": "f",
                        "is_flag": True,
                        "help": "Force deployment",
                    },
                ],
                "confirmation": True,
            },
            {
                "name": "status",
                "description": "Check system status",
                "options": [
                    {
                        "name": "format",
                        "short": "f",
                        "type": "str",
                        "default": "table",
                        "help": "Output format (table/json)",
                    }
                ],
            },
        ],
        "options": [
            {
                "name": "config",
                "short": "c",
                "type": "path",
                "help": "Configuration file",
            }
        ],
    }

    files = template.generate(params)
    for filename, content in files.items():
        print(f"=== {filename} ===")
        print(content[:500] + "...\\n")  # Show first 500 chars
