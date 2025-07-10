"""
REST API Endpoint Generator Template for Elders Guild
生成されるエンドポイントは FastAPI または Flask をサポート
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class RestApiTemplate:
    """REST APIエンドポイントテンプレート"""
    
    def __init__(self):
        self.template_info = {
            "name": "REST API Endpoint",
            "version": "1.0.0",
            "description": "Generate REST API endpoints with validation and tests",
            "author": "Elders Guild",
            "parameters": {
                "framework": {
                    "type": "str",
                    "choices": ["fastapi", "flask"],
                    "default": "fastapi",
                    "description": "Web framework to use"
                },
                "resource_name": {
                    "type": "str",
                    "required": True,
                    "description": "Name of the resource (e.g., 'user', 'product')"
                },
                "operations": {
                    "type": "list",
                    "choices": ["list", "get", "create", "update", "delete"],
                    "default": ["list", "get", "create", "update", "delete"],
                    "description": "CRUD operations to generate"
                },
                "auth_required": {
                    "type": "bool",
                    "default": True,
                    "description": "Whether authentication is required"
                },
                "validation": {
                    "type": "bool",
                    "default": True,
                    "description": "Include request validation"
                }
            }
        }
    
    def generate_fastapi(self, params: Dict[str, Any]) -> Dict[str, str]:
        """FastAPI エンドポイントを生成"""
        resource = params["resource_name"]
        operations = params.get("operations", ["list", "get", "create", "update", "delete"])
        auth = params.get("auth_required", True)
        
        # Model file
        model_content = f'''"""
{resource.capitalize()} models for API
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class {resource.capitalize()}Base(BaseModel):
    """Base {resource} model"""
    name: str = Field(..., description="Name of the {resource}")
    description: Optional[str] = Field(None, description="Description")

class {resource.capitalize()}Create({resource.capitalize()}Base):
    """Create {resource} model"""
    pass

class {resource.capitalize()}Update({resource.capitalize()}Base):
    """Update {resource} model"""
    name: Optional[str] = Field(None, description="Name of the {resource}")

class {resource.capitalize()}InDB({resource.capitalize()}Base):
    """Database {resource} model"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class {resource.capitalize()}Response({resource.capitalize()}InDB):
    """Response {resource} model"""
    pass
'''
        
        # Router file
        router_content = f'''"""
{resource.capitalize()} API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional
from sqlalchemy.orm import Session

from .models import (
    {resource.capitalize()}Create,
    {resource.capitalize()}Update,
    {resource.capitalize()}Response
)
from ..database import get_db
{"from ..auth import get_current_user" if auth else ""}

router = APIRouter(
    prefix="/{resource}s",
    tags=["{resource}s"],
    responses={{404: {{"description": "Not found"}}}}
)
'''
        
        if "list" in operations:
            router_content += f'''
@router.get("/", response_model=List[{resource.capitalize()}Response])
async def list_{resource}s(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    db: Session = Depends(get_db){"," if auth else ""}
    {f"current_user = Depends(get_current_user)" if auth else ""}
):
    """List all {resource}s with pagination"""
    # TODO: Implement database query
    return []
'''
        
        if "get" in operations:
            router_content += f'''
@router.get("/{{{resource}_id}}", response_model={resource.capitalize()}Response)
async def get_{resource}(
    {resource}_id: int = Path(..., description="{resource.capitalize()} ID"),
    db: Session = Depends(get_db){"," if auth else ""}
    {f"current_user = Depends(get_current_user)" if auth else ""}
):
    """Get a specific {resource} by ID"""
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="{resource.capitalize()} not found")
'''
        
        if "create" in operations:
            router_content += f'''
@router.post("/", response_model={resource.capitalize()}Response, status_code=201)
async def create_{resource}(
    {resource}: {resource.capitalize()}Create,
    db: Session = Depends(get_db){"," if auth else ""}
    {f"current_user = Depends(get_current_user)" if auth else ""}
):
    """Create a new {resource}"""
    # TODO: Implement database creation
    return {{{resource}.model_dump(), "id": 1, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"}}
'''
        
        if "update" in operations:
            router_content += f'''
@router.put("/{{{resource}_id}}", response_model={resource.capitalize()}Response)
async def update_{resource}(
    {resource}_id: int = Path(..., description="{resource.capitalize()} ID"),
    {resource}: {resource.capitalize()}Update,
    db: Session = Depends(get_db){"," if auth else ""}
    {f"current_user = Depends(get_current_user)" if auth else ""}
):
    """Update a {resource}"""
    # TODO: Implement database update
    raise HTTPException(status_code=404, detail="{resource.capitalize()} not found")
'''
        
        if "delete" in operations:
            router_content += f'''
@router.delete("/{{{resource}_id}}", status_code=204)
async def delete_{resource}(
    {resource}_id: int = Path(..., description="{resource.capitalize()} ID"),
    db: Session = Depends(get_db){"," if auth else ""}
    {f"current_user = Depends(get_current_user)" if auth else ""}
):
    """Delete a {resource}"""
    # TODO: Implement database deletion
    raise HTTPException(status_code=404, detail="{resource.capitalize()} not found")
'''
        
        # Test file
        test_content = f'''"""
Tests for {resource} API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from main import app

client = TestClient(app)

class Test{resource.capitalize()}API:
    """Test {resource} API endpoints"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        with patch("api.database.get_db") as mock:
            yield mock
    '''
        
        if auth:
            test_content += f'''
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {{"Authorization": "Bearer test-token"}}
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        with patch("api.auth.get_current_user") as mock:
            mock.return_value = {{"id": 1, "username": "testuser"}}
            yield mock
'''
        
        if "list" in operations:
            test_content += f'''
    def test_list_{resource}s(self, mock_db{", mock_user, auth_headers" if auth else ""}):
        """Test listing {resource}s"""
        response = client.get("/{resource}s/"{", headers=auth_headers" if auth else ""})
        assert response.status_code == 200
        assert isinstance(response.json(), list)
'''
        
        if "create" in operations:
            test_content += f'''
    def test_create_{resource}(self, mock_db{", mock_user, auth_headers" if auth else ""}):
        """Test creating a {resource}"""
        data = {{"name": "Test {resource}", "description": "Test description"}}
        response = client.post("/{resource}s/", json=data{", headers=auth_headers" if auth else ""})
        assert response.status_code == 201
        assert response.json()["name"] == data["name"]
'''
        
        return {
            f"models/{resource}.py": model_content,
            f"routers/{resource}.py": router_content,
            f"tests/test_{resource}.py": test_content
        }
    
    def generate_flask(self, params: Dict[str, Any]) -> Dict[str, str]:
        """Flask エンドポイントを生成"""
        resource = params["resource_name"]
        operations = params.get("operations", ["list", "get", "create", "update", "delete"])
        
        blueprint_content = f'''"""
{resource.capitalize()} API Blueprint
"""
from flask import Blueprint, request, jsonify
from flask_restful import Resource, Api, reqparse
from marshmallow import Schema, fields, ValidationError
{f"from ..auth import auth_required" if params.get("auth_required", True) else ""}

{resource}_bp = Blueprint('{resource}', __name__, url_prefix='/api/{resource}s')
api = Api({resource}_bp)

# Schemas
class {resource.capitalize()}Schema(Schema):
    """Validation schema for {resource}"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(missing="")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

{resource}_schema = {resource.capitalize()}Schema()
{resource}s_schema = {resource.capitalize()}Schema(many=True)

# Parser
parser = reqparse.RequestParser()
parser.add_argument('name', type=str, required=True, help='Name is required')
parser.add_argument('description', type=str)
'''
        
        if "list" in operations or "create" in operations:
            blueprint_content += f'''
class {resource.capitalize()}List(Resource):
    """List and create {resource}s"""
    '''
            if "list" in operations:
                blueprint_content += f'''
    {"@auth_required" if params.get("auth_required", True) else ""}
    def get(self):
        """List all {resource}s"""
        # TODO: Implement database query
        return {{"data": [], "total": 0}}
    '''
            
            if "create" in operations:
                blueprint_content += f'''
    {"@auth_required" if params.get("auth_required", True) else ""}
    def post(self):
        """Create a new {resource}"""
        try:
            data = {resource}_schema.load(request.get_json())
        except ValidationError as err:
            return {{"errors": err.messages}}, 400
        
        # TODO: Implement database creation
        return {resource}_schema.dump(data), 201
'''
        
        if any(op in operations for op in ["get", "update", "delete"]):
            blueprint_content += f'''
class {resource.capitalize()}Detail(Resource):
    """Get, update and delete {resource}"""
    '''
            if "get" in operations:
                blueprint_content += f'''
    {"@auth_required" if params.get("auth_required", True) else ""}
    def get(self, {resource}_id):
        """Get a specific {resource}"""
        # TODO: Implement database query
        return {{"error": "{resource.capitalize()} not found"}}, 404
    '''
            
            if "update" in operations:
                blueprint_content += f'''
    {"@auth_required" if params.get("auth_required", True) else ""}
    def put(self, {resource}_id):
        """Update a {resource}"""
        try:
            data = {resource}_schema.load(request.get_json(), partial=True)
        except ValidationError as err:
            return {{"errors": err.messages}}, 400
        
        # TODO: Implement database update
        return {{"error": "{resource.capitalize()} not found"}}, 404
    '''
            
            if "delete" in operations:
                blueprint_content += f'''
    {"@auth_required" if params.get("auth_required", True) else ""}
    def delete(self, {resource}_id):
        """Delete a {resource}"""
        # TODO: Implement database deletion
        return '', 204
'''
        
        blueprint_content += f'''
# Register resources
api.add_resource({resource.capitalize()}List, '/')
api.add_resource({resource.capitalize()}Detail, '/<int:{resource}_id>')
'''
        
        return {
            f"blueprints/{resource}.py": blueprint_content
        }
    
    def generate(self, params: Dict[str, Any]) -> Dict[str, str]:
        """テンプレートからコードを生成"""
        framework = params.get("framework", "fastapi")
        
        if framework == "fastapi":
            return self.generate_fastapi(params)
        elif framework == "flask":
            return self.generate_flask(params)
        else:
            raise ValueError(f"Unsupported framework: {framework}")

# Usage example
if __name__ == "__main__":
    template = RestApiTemplate()
    
    # Example parameters
    params = {
        "framework": "fastapi",
        "resource_name": "product",
        "operations": ["list", "get", "create", "update", "delete"],
        "auth_required": True,
        "validation": True
    }
    
    files = template.generate(params)
    for filename, content in files.items():
        print(f"=== {filename} ===")
        print(content)
        print()