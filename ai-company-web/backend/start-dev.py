#!/usr/bin/env python3
"""
Development server startup script for AI Company Web FastAPI Backend
"""

import os
import sys
import uvicorn

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Create .env file if it doesn't exist
    env_file = ".env"
    env_example = ".env.example"
    
    if not os.path.exists(env_file) and os.path.exists(env_example):
        print("Creating .env file from .env.example...")
        with open(env_example, 'r') as source:
            with open(env_file, 'w') as target:
                target.write(source.read())
        print(".env file created. You may want to customize it.")
    
    print("Starting AI Company Web FastAPI Backend...")
    print("Four Sages Real-time System")
    print("=" * 50)
    print("API Documentation: http://localhost:8000/api/docs")
    print("Health Check: http://localhost:8000/health")
    print("WebSocket Test: ws://localhost:8000/api/ws/connect")
    print("=" * 50)
    
    # Run the FastAPI application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info",
    )