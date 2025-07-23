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
            """BaseSettingsクラス"""
            def __init__(self, **kwargs):
                """初期化メソッド"""
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        def Field(default=None, **kwargs):
            """Fieldメソッド"""
            return default
        
        def validator(field_name, **kwargs):
            """validatorメソッド"""
            return lambda f: f
