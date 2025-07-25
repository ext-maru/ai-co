"""
FastAPI Framework Wrapper
"""

try:
    from fastapi import FastAPI, HTTPException, Depends, Request, Response
    from fastapi.responses import JSONResponse, HTMLResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.staticfiles import StaticFiles

except ImportError:
    # フォールバック実装
    class MockFastAPI:
        """MockFastAPIクラス"""
        def __init__(self):
            """初期化メソッド"""
            pass
        def get(self, path):
            """getメソッド"""
        return lambda f: f
        def post(self, path):
            """postメソッド"""
        return lambda f: f
        def put(self, path):
            """putメソッド"""
        return lambda f: f
        def delete(self, path):
            """deleteメソッド"""
        return lambda f: f
    
    FastAPI = MockFastAPI
    HTTPException = Exception
    Depends = lambda x: x
    Request = dict
    Response = dict
    JSONResponse = dict
    HTMLResponse = str
    CORSMiddleware = object
    HTTPBearer = object
    HTTPAuthorizationCredentials = dict
    StaticFiles = object

