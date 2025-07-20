"""
Uvicorn ASGI Server Wrapper  
"""

try:
    import uvicorn
    from uvicorn import Config, Server
except ImportError:
    # フォールバック実装
    class MockUvicorn:
        @staticmethod
        def run(app, host='127.0.0.1', port=8000, **kwargs):
            print(f'Mock server running on {host}:{port}')
    
    uvicorn = MockUvicorn()
    Config = dict
    Server = object
