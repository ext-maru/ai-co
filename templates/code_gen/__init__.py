"""
Elders Guild Code Generation Templates

This module provides templates for generating various types of code:
- REST API endpoints (FastAPI/Flask)
- Database models (SQLAlchemy)
- CLI commands (Click)

Usage:
    from templates.code_gen import TemplateRegistry
    
    registry = TemplateRegistry()
    
    # List available templates
    templates = registry.list_templates()
    
    # Generate code
    files = registry.generate('rest_api', {
        'framework': 'fastapi',
        'resource_name': 'user',
        'operations': ['list', 'get', 'create', 'update', 'delete']
    })
"""

from .template_registry import TemplateRegistry
from .rest_api_template import RestApiTemplate
from .database_model_template import DatabaseModelTemplate
from .cli_command_template import CliCommandTemplate

__all__ = [
    'TemplateRegistry',
    'RestApiTemplate',
    'DatabaseModelTemplate',
    'CliCommandTemplate'
]

__version__ = '1.0.0'