"""
Pydantic Settings Wrapper
"""

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, validator
except ImportError:
    try:
        from pydantic import BaseSettings, Field, validator
    except ImportError:
        # フォールバック実装
        class BaseSettings:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        def Field(default=None, **kwargs):
            return default
        
        def validator(field_name, **kwargs):
            return lambda f: f
