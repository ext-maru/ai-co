"""
FastAPI Framework Wrapper
"""

try:
    from fastapi import FastAPI, HTTPException, Depends, Request, Response
    from fastapi.responses import JSONResponse, HTMLResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
except ImportError:
    # フォールバック実装
    class MockFastAPI:
        def __init__(self):
            pass
        def get(self, path): return lambda f: f
        def post(self, path): return lambda f: f
        def put(self, path): return lambda f: f
        def delete(self, path): return lambda f: f
    
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
    Jinja2Templates = object
