#!/usr/bin/env python3
"""
🛠️ Practical Auto System Generator
Elder Flow理論を実用的な自動システム作成に応用（実装版）
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import re

@dataclass
class SystemRequirement:
    """システム要件"""
    requirement_id: str
    description: str
    priority: int  # 1-10
    complexity: float  # 0.0-1.0
    dependencies: List[str]
    technical_category: str
    estimated_effort: float

@dataclass
class GeneratedComponent:
    """生成されたシステムコンポーネント"""
    component_id: str
    name: str
    type: str
    technology_stack: List[str]
    configuration: Dict[str, Any]
    deployment_config: Dict[str, Any]
    dependencies: List[str]
    estimated_resources: Dict[str, float]
    code_template: str

class PracticalAutoSystemGenerator:
    """実用的な自動システム生成器"""

    def __init__(self):
        self.tech_patterns = {
            "todo_app": {
                "frontend": ["React", "TypeScript", "Tailwind CSS"],
                "backend": ["FastAPI", "Python", "SQLAlchemy"],
                "database": ["PostgreSQL", "Redis"],
                "auth": ["JWT", "bcrypt"],
                "realtime": ["WebSocket", "Socket.IO"]
            },
            "e_commerce": {
                "frontend": ["Next.js", "TypeScript", "Stripe"],
                "backend": ["Node.js", "Express", "Prisma"],
                "database": ["PostgreSQL", "Redis"],
                "payment": ["Stripe", "PayPal"],
                "inventory": ["Redis", "PostgreSQL"]
            },
            "dashboard": {
                "frontend": ["React", "D3.js", "Chart.js"],
                "backend": ["Python", "FastAPI", "Pandas"],
                "database": ["PostgreSQL", "InfluxDB"],
                "analytics": ["Pandas", "NumPy"],
                "realtime": ["WebSocket", "Server-Sent Events"]
            }
        }

        self.code_templates = {
            "fastapi_backend": '''
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import {model_name}
from schemas import {schema_name}

app = FastAPI(title="{app_name}")

@app.get("/")
async def root():
    return {{"message": "Welcome to {app_name}"}}

@app.get("/{endpoint}")
async def get_items(db: Session = Depends(get_db)):
    items = db.query({model_name}).all()
    return items

@app.post("/{endpoint}")
async def create_item(item: {schema_name}, db: Session = Depends(get_db)):
    db_item = {model_name}(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
''',
            "react_frontend": '''
import React, {{ useState, useEffect }} from 'react';
import axios from 'axios';

const {component_name} = () => {{
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {{
        fetchItems();
    }}, []);

    const fetchItems = async () => {{
        try {{
            const response = await axios.get('/api/{endpoint}');
            setItems(response.data);
        }} catch (error) {{
            console.error('Error fetching items:', error);
        }} finally {{
            setLoading(false);
        }}
    }};

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-2xl font-bold mb-4">{component_name}</h1>
            {{loading ? (
                <div>Loading...</div>
            ) : (
                <div className="grid gap-4">
                    {{items.map(item => (
                        <div key={{item.id}} className="border p-4 rounded">
                            {{JSON.stringify(item)}}
                        </div>
                    ))}}
                </div>
            )}}
        </div>
    );
}};

export default {component_name};
''',
            "docker_compose": '''
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://backend:8000

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - database
    environment:
      - DATABASE_URL=postgresql://user:password@database:5432/mydb

  database:
    image: postgres:13
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
'''
        }

        self.generated_systems = {}

    def analyze_requirements(self, user_description: str) -> List[SystemRequirement]:
        """要件分析 - キーワードベースの実装"""

        requirements = []
        desc_lower = user_description.lower()

        # パターン認識
        system_type = None
        if any(word in desc_lower for word in ['todo', 'task', 'list']):
            system_type = "todo_app"
        elif any(word in desc_lower for word in ['ecommerce', 'e-commerce', 'shop', 'store']):
            system_type = "e_commerce"
        elif any(word in desc_lower for word in ['dashboard', 'analytics', 'chart']):
            system_type = "dashboard"

        # 基本要件生成
        if 'app' in desc_lower or 'web' in desc_lower:
            requirements.append(SystemRequirement(
                requirement_id=f"req_{uuid.uuid4().hex[:8]}",
                description="Frontend application",
                priority=8,
                complexity=0.6,
                dependencies=[],
                technical_category="frontend",
                estimated_effort=40.0
            ))

        if any(word in desc_lower for word in ['api', 'backend', 'server']):
            requirements.append(SystemRequirement(
                requirement_id=f"req_{uuid.uuid4().hex[:8]}",
                description="Backend API service",
                priority=9,
                complexity=0.7,
                dependencies=[],
                technical_category="backend",
                estimated_effort=60.0
            ))

        if any(word in desc_lower for word in ['database', 'data', 'store']):
            requirements.append(SystemRequirement(
                requirement_id=f"req_{uuid.uuid4().hex[:8]}",
                description="Database system",
                priority=9,
                complexity=0.5,
                dependencies=[],
                technical_category="database",
                estimated_effort=20.0
            ))

        if any(word in desc_lower for word in ['auth', 'login', 'user']):
            requirements.append(SystemRequirement(
                requirement_id=f"req_{uuid.uuid4().hex[:8]}",
                description="Authentication system",
                priority=8,
                complexity=0.8,
                dependencies=[],
                technical_category="auth",
                estimated_effort=35.0
            ))

        if any(word in desc_lower for word in ['realtime', 'real-time', 'live']):
            requirements.append(SystemRequirement(
                requirement_id=f"req_{uuid.uuid4().hex[:8]}",
                description="Real-time communication",
                priority=7,
                complexity=0.9,
                dependencies=[],
                technical_category="realtime",
                estimated_effort=45.0
            ))

        return requirements

    def establish_dependency_order(self, requirements: List[SystemRequirement]) -> List[str]:
        """依存関係に基づく最適なビルド順序"""

        # 依存関係の優先順位
        category_priority = {
            "database": 1,
            "backend": 2,
            "auth": 3,
            "realtime": 4,
            "frontend": 5
        }

        # 優先度とカテゴリ優先度でソート
        sorted_reqs = sorted(requirements,
                           key=lambda x: (category_priority.get(x.technical_category, 10),
                                        -x.priority))

        return [req.requirement_id for req in sorted_reqs]

    def generate_system_components(self, requirements: List[SystemRequirement],
                                 description: str) -> List[GeneratedComponent]:
        """並列的にシステムコンポーネントを生成"""

        components = []

        # システムタイプ判定
        system_type = self._detect_system_type(description)
        tech_stack = self.tech_patterns.get(system_type, self.tech_patterns["todo_app"])

        for req in requirements:
            component = self._generate_component_for_requirement(req, tech_stack, description)
            components.append(component)

        return components

    def _detect_system_type(self, description: str) -> str:
        """システムタイプ検出"""
        desc_lower = description.lower()

        if any(word in desc_lower for word in ['todo', 'task']):
            return "todo_app"
        elif any(word in desc_lower for word in ['shop', 'store', 'ecommerce']):
            return "e_commerce"
        elif any(word in desc_lower for word in ['dashboard', 'analytics']):
            return "dashboard"
        else:
            return "todo_app"  # デフォルト

    def _generate_component_for_requirement(self, req: SystemRequirement,
                                          tech_stack: Dict, description: str) -> GeneratedComponent:
        """要件に基づくコンポーネント生成"""

        component_id = f"comp_{uuid.uuid4().hex[:8]}"
        category = req.technical_category

        # カテゴリ別の技術スタック選択
        if category == "frontend":
            stack = tech_stack.get("frontend", ["React", "TypeScript"])
            deployment = {"type": "static", "platform": "Vercel"}
            resources = {"cpu": 0.1, "memory": 0.5, "storage": 1.0}
            code = self._generate_frontend_code(description)

        elif category == "backend":
            stack = tech_stack.get("backend", ["FastAPI", "Python"])
            deployment = {"type": "container", "platform": "Docker"}
            resources = {"cpu": 1.0, "memory": 2.0, "storage": 10.0}
            code = self._generate_backend_code(description)

        elif category == "database":
            stack = tech_stack.get("database", ["PostgreSQL"])
            deployment = {"type": "managed", "platform": "AWS RDS"}
            resources = {"cpu": 0.5, "memory": 4.0, "storage": 100.0}
            code = self._generate_database_code()

        elif category == "auth":
            stack = tech_stack.get("auth", ["JWT", "bcrypt"])
            deployment = {"type": "integrated", "platform": "Backend"}
            resources = {"cpu": 0.2, "memory": 0.5, "storage": 1.0}
            code = self._generate_auth_code()

        elif category == "realtime":
            stack = tech_stack.get("realtime", ["WebSocket"])
            deployment = {"type": "integrated", "platform": "Backend"}
            resources = {"cpu": 0.3, "memory": 1.0, "storage": 2.0}
            code = self._generate_realtime_code()

        else:
            stack = ["Docker", "Python"]
            deployment = {"type": "container", "platform": "Kubernetes"}
            resources = {"cpu": 0.5, "memory": 1.0, "storage": 10.0}
            code = "# Generic component code"

        return GeneratedComponent(
            component_id=component_id,
            name=f"{category}_{req.requirement_id}",
            type=category,
            technology_stack=stack,
            configuration={
                "environment": "production",
                "scaling": "auto",
                "monitoring": True
            },
            deployment_config=deployment,
            dependencies=req.dependencies,
            estimated_resources=resources,
            code_template=code
        )

    def _generate_frontend_code(self, description: str) -> str:
        """フロントエンドコード生成"""
        return self.code_templates["react_frontend"].format(
            component_name="MainApp",
            endpoint="items"
        )

    def _generate_backend_code(self, description: str) -> str:
        """バックエンドコード生成"""
        return self.code_templates["fastapi_backend"].format(
            app_name="Auto Generated API",
            model_name="Item",
            schema_name="ItemCreate",
            endpoint="items"
        )

    def _generate_database_code(self) -> str:
        """データベースコード生成"""
        return '''
-- Auto-generated database schema
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_items_completed ON items(completed);
'''

    def _generate_auth_code(self) -> str:
        """認証コード生成"""
        return '''
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
'''

    def _generate_realtime_code(self) -> str:
        """リアルタイムコード生成"""
        return '''
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
'''

    async def auto_generate_system(self, user_description: str) -> Dict[str, Any]:
        """自動システム生成のメインフロー"""

        print(f"🛠️ Generating system for: '{user_description}'")

        # 1. 要件分析
        print("📋 Analyzing requirements...")
        requirements = self.analyze_requirements(user_description)
        print(f"✅ Identified {len(requirements)} requirements")

        # 2. 依存関係確立
        print("🔗 Establishing build order...")
        build_order = self.establish_dependency_order(requirements)
        print(f"✅ Build order: {' → '.join([req.technical_category for req in requirements])}")

        # 3. 並列コンポーネント生成
        print("⚡ Generating components...")
        components = self.generate_system_components(requirements, user_description)
        print(f"✅ Generated {len(components)} components")

        # 4. Docker Compose生成
        print("🐳 Generating deployment configuration...")
        docker_compose = self._generate_docker_compose(components)

        # 5. システム統合
        system_architecture = {
            "system_id": f"sys_{uuid.uuid4().hex[:8]}",
            "description": user_description,
            "requirements": [asdict(req) for req in requirements],
            "components": [asdict(comp) for comp in components],
            "build_order": build_order,
            "estimated_total_resources": self._calculate_total_resources(components),
            "deployment_config": docker_compose,
            "generated_at": datetime.now().isoformat(),
            "estimated_completion_time": sum(req.estimated_effort for req in requirements)
        }

        self.generated_systems[system_architecture["system_id"]] = system_architecture
        return system_architecture

    def _generate_docker_compose(self, components: List[GeneratedComponent]) -> str:
        """Docker Compose設定生成"""
        return self.code_templates["docker_compose"]

    def _calculate_total_resources(self, components: List[GeneratedComponent]) -> Dict[str, float]:
        """総リソース計算"""
        total = {"cpu": 0, "memory": 0, "storage": 0}

        for comp in components:
            for resource, amount in comp.estimated_resources.items():
                total[resource] = total.get(resource, 0) + amount

        return total

    def generate_project_files(self, system_id: str) -> Dict[str, str]:
        """プロジェクトファイル生成"""

        if system_id not in self.generated_systems:
            raise ValueError(f"System {system_id} not found")

        system = self.generated_systems[system_id]
        files = {}

        # 各コンポーネントのコードファイル
        for comp_data in system["components"]:
            comp_type = comp_data["type"]
            code = comp_data["code_template"]

            if comp_type == "frontend":
                files[f"frontend/src/App.tsx"] = code
            elif comp_type == "backend":
                files[f"backend/main.py"] = code
            elif comp_type == "database":
                files[f"database/schema.sql"] = code
            elif comp_type == "auth":
                files[f"backend/auth.py"] = code
            elif comp_type == "realtime":
                files[f"backend/websocket.py"] = code

        # Docker Compose
        files["docker-compose.yml"] = system["deployment_config"]

        # README
        files["README.md"] = self._generate_readme(system)

        return files

    def _generate_readme(self, system: Dict) -> str:
        """README生成"""
        return f'''
# {system["description"]}

Auto-generated system with Elder Flow technology.

## System ID
{system["system_id"]}

## Components
{chr(10).join(f"- {comp['name']}: {comp['type']} ({', '.join(comp['technology_stack'])})" for comp in system["components"])}

## Quick Start

```bash
# Build and run the system
docker-compose up -d

# Access the application
Frontend: http://localhost:3000
Backend API: http://localhost:8000
```

## Estimated Resources
- CPU: {system["estimated_total_resources"]["cpu"]} cores
- Memory: {system["estimated_total_resources"]["memory"]} GB
- Storage: {system["estimated_total_resources"]["storage"]} GB

## Estimated Development Time
{system["estimated_completion_time"]} hours

Generated at: {system["generated_at"]}
'''

# デモ実行
async def practical_demo():
    """実用的な自動システム生成デモ"""
    print("🛠️ Practical Auto System Generator Demo")
    print("=" * 70)

    generator = PracticalAutoSystemGenerator()

    # テストケース
    test_cases = [
        "Create a todo app with user authentication and real-time updates",
        "Build an e-commerce API with payment processing",
        "Develop a data analytics dashboard with real-time charts"
    ]

    for i, description in enumerate(test_cases, 1):
        print(f"\n🎯 Test Case {i}: {description}")
        print("-" * 50)

        # システム生成
        result = await generator.auto_generate_system(description)

        print(f"✅ System generated successfully!")
        print(f"System ID: {result['system_id']}")
        print(f"Components: {len(result['components'])}")
        print(f"Total Development Time: {result['estimated_completion_time']} hours")
        print(f"Total Resources: CPU={result['estimated_total_resources']['cpu']}, Memory={result['estimated_total_resources']['memory']}GB")

        # プロジェクトファイル生成
        files = generator.generate_project_files(result['system_id'])
        print(f"Generated {len(files)} project files:")
        for filename in sorted(files.keys()):
            print(f"  📄 {filename}")

    print(f"\n🎉 Demo completed! Generated {len(generator.generated_systems)} systems.")

if __name__ == "__main__":
    asyncio.run(practical_demo())
