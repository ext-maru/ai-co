"""
Database Model Generator Template for Elders Guild
SQLAlchemy モデル、マイグレーション、CRUD操作を生成
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

class DatabaseModelTemplate:
    """データベースモデルテンプレート"""
    
    def __init__(self):
        self.template_info = {
            "name": "Database Model",
            "version": "1.0.0", 
            "description": "Generate SQLAlchemy models with CRUD operations",
            "author": "Elders Guild",
            "parameters": {
                "model_name": {
                    "type": "str",
                    "required": True,
                    "description": "Name of the model (e.g., 'User', 'Product')"
                },
                "fields": {
                    "type": "dict",
                    "required": True,
                    "description": "Field definitions {name: type}"
                },
                "relationships": {
                    "type": "list",
                    "default": [],
                    "description": "Relationship definitions"
                },
                "indexes": {
                    "type": "list",
                    "default": [],
                    "description": "Index definitions"
                },
                "soft_delete": {
                    "type": "bool",
                    "default": True,
                    "description": "Include soft delete functionality"
                }
            }
        }
    
    def generate_model(self, params: Dict[str, Any]) -> str:
        """SQLAlchemy モデルを生成"""
        model_name = params["model_name"]
        fields = params["fields"]
        relationships = params.get("relationships", [])
        indexes = params.get("indexes", [])
        soft_delete = params.get("soft_delete", True)
        
        content = f'''"""
{model_name} database model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index, Text, Float
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

from ..database import Base

class {model_name}(Base):
    """
    {model_name} model
    """
    __tablename__ = "{model_name.lower()}s"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Fields
'''
        
        # Add fields
        for field_name, field_type in fields.items():
            if field_type == "string":
                content += f"    {field_name} = Column(String(255), nullable=False)\n"
            elif field_type == "text":
                content += f"    {field_name} = Column(Text, nullable=True)\n"
            elif field_type == "integer":
                content += f"    {field_name} = Column(Integer, nullable=False)\n"
            elif field_type == "float":
                content += f"    {field_name} = Column(Float, nullable=False)\n"
            elif field_type == "boolean":
                content += f"    {field_name} = Column(Boolean, default=False)\n"
            elif field_type == "datetime":
                content += f"    {field_name} = Column(DateTime, nullable=True)\n"
            elif field_type.startswith("foreign_key:"):
                ref_table = field_type.split(":")[1]
                content += f"    {field_name} = Column(Integer, ForeignKey('{ref_table}.id'), nullable=True)\n"
        
        content += '''    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
'''
        
        if soft_delete:
            content += '''    
    # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
'''
        
        # Add relationships
        if relationships:
            content += "\n    # Relationships\n"
            for rel in relationships:
                rel_type = rel.get("type", "one-to-many")
                target = rel.get("target")
                back_populates = rel.get("back_populates", f"{model_name.lower()}s")
                
                if rel_type == "one-to-many":
                    content += f"    {target.lower()}s = relationship('{target}', back_populates='{model_name.lower()}')\n"
                elif rel_type == "many-to-one":
                    content += f"    {target.lower()} = relationship('{target}', back_populates='{model_name.lower()}s')\n"
        
        # Add indexes
        if indexes:
            content += "\n    # Indexes\n"
            for idx, index_fields in enumerate(indexes):
                index_name = f"idx_{model_name.lower()}_{'_'.join(index_fields)}"
                content += f"    __table_args__ = (Index('{index_name}', {', '.join(repr(f) for f in index_fields)}),)\n"
        
        # Add validation
        if any(f == "email" for f in fields.keys()):
            content += '''
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format"""
        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")
        return email.lower()
'''
        
        # Add string representation
        content += f'''
    def __repr__(self):
        return f"<{model_name}(id={{self.id}})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {{
            "id": self.id,
'''
        for field_name in fields.keys():
            content += f'            "{field_name}": self.{field_name},\n'
        
        content += '''            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
'''
        
        if soft_delete:
            content += '''            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
'''
        
        content += '''        }
'''
        
        return content
    
    def generate_crud(self, params: Dict[str, Any]) -> str:
        """CRUD操作を生成"""
        model_name = params["model_name"]
        soft_delete = params.get("soft_delete", True)
        
        content = f'''"""
CRUD operations for {model_name}
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from ..models.{model_name.lower()} import {model_name}

class {model_name}CRUD:
    """CRUD operations for {model_name}"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, **kwargs) -> {model_name}:
        """Create a new {model_name}"""
        db_{model_name.lower()} = {model_name}(**kwargs)
        self.db.add(db_{model_name.lower()})
        self.db.commit()
        self.db.refresh(db_{model_name.lower()})
        return db_{model_name.lower()}
    
    def get(self, {model_name.lower()}_id: int) -> Optional[{model_name}]:
        """Get a {model_name} by ID"""
        query = self.db.query({model_name}).filter({model_name}.id == {model_name.lower()}_id)
'''
        
        if soft_delete:
            content += f"        query = query.filter({model_name}.is_deleted == False)\n"
        
        content += f'''        return query.first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[{model_name}]:
        """Get all {model_name}s with pagination"""
        query = self.db.query({model_name})
'''
        
        if soft_delete:
            content += f"        query = query.filter({model_name}.is_deleted == False)\n"
        
        content += f'''        return query.offset(skip).limit(limit).all()
    
    def update(self, {model_name.lower()}_id: int, **kwargs) -> Optional[{model_name}]:
        """Update a {model_name}"""
        db_{model_name.lower()} = self.get({model_name.lower()}_id)
        if db_{model_name.lower()}:
            for key, value in kwargs.items():
                setattr(db_{model_name.lower()}, key, value)
            self.db.commit()
            self.db.refresh(db_{model_name.lower()})
        return db_{model_name.lower()}
    
    def delete(self, {model_name.lower()}_id: int) -> bool:
        """Delete a {model_name}"""
        db_{model_name.lower()} = self.get({model_name.lower()}_id)
        if db_{model_name.lower()}:
'''
        
        if soft_delete:
            content += f'''            db_{model_name.lower()}.is_deleted = True
            db_{model_name.lower()}.deleted_at = datetime.now()
            self.db.commit()
'''
        else:
            content += f'''            self.db.delete(db_{model_name.lower()})
            self.db.commit()
'''
        
        content += '''            return True
        return False
    
    def search(self, **filters) -> List[{model_name}]:
        """Search {model_name}s with filters"""
        query = self.db.query({model_name})
'''
        
        if soft_delete:
            content += f"        query = query.filter({model_name}.is_deleted == False)\n"
        
        content += '''        
        for key, value in filters.items():
            if hasattr({model_name}, key) and value is not None:
                query = query.filter(getattr({model_name}, key) == value)
        
        return query.all()
'''
        
        return content
    
    def generate_migration(self, params: Dict[str, Any]) -> str:
        """Alembic マイグレーションを生成"""
        model_name = params["model_name"]
        fields = params["fields"]
        soft_delete = params.get("soft_delete", True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        content = f'''"""create {model_name.lower()} table

Revision ID: {timestamp[:8]}
Revises: 
Create Date: {datetime.now().isoformat()}

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '{timestamp[:8]}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Create {model_name} table"""
    op.create_table(
        '{model_name.lower()}s',
        sa.Column('id', sa.Integer(), nullable=False),
'''
        
        # Add fields
        for field_name, field_type in fields.items():
            if field_type == "string":
                content += f"        sa.Column('{field_name}', sa.String(255), nullable=False),\n"
            elif field_type == "text":
                content += f"        sa.Column('{field_name}', sa.Text(), nullable=True),\n"
            elif field_type == "integer":
                content += f"        sa.Column('{field_name}', sa.Integer(), nullable=False),\n"
            elif field_type == "float":
                content += f"        sa.Column('{field_name}', sa.Float(), nullable=False),\n"
            elif field_type == "boolean":
                content += f"        sa.Column('{field_name}', sa.Boolean(), nullable=False),\n"
            elif field_type == "datetime":
                content += f"        sa.Column('{field_name}', sa.DateTime(), nullable=True),\n"
        
        content += '''        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
'''
        
        if soft_delete:
            content += '''        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
'''
        
        content += f'''        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_{model_name.lower()}s_id'), '{model_name.lower()}s', ['id'], unique=False)

def downgrade():
    """Drop {model_name} table"""
    op.drop_index(op.f('ix_{model_name.lower()}s_id'), table_name='{model_name.lower()}s')
    op.drop_table('{model_name.lower()}s')
'''
        
        return content
    
    def generate(self, params: Dict[str, Any]) -> Dict[str, str]:
        """テンプレートからコードを生成"""
        model_name = params["model_name"]
        
        return {
            f"models/{model_name.lower()}.py": self.generate_model(params),
            f"crud/{model_name.lower()}_crud.py": self.generate_crud(params),
            f"migrations/{datetime.now().strftime('%Y%m%d_%H%M%S')}_create_{model_name.lower()}.py": self.generate_migration(params)
        }

# Usage example
if __name__ == "__main__":
    template = DatabaseModelTemplate()
    
    # Example parameters
    params = {
        "model_name": "Product",
        "fields": {
            "name": "string",
            "description": "text",
            "price": "float",
            "stock": "integer",
            "is_active": "boolean",
            "category_id": "foreign_key:categories"
        },
        "relationships": [
            {"type": "many-to-one", "target": "Category"}
        ],
        "indexes": [["name"], ["category_id", "is_active"]],
        "soft_delete": True
    }
    
    files = template.generate(params)
    for filename, content in files.items():
        print(f"=== {filename} ===")
        print(content)
        print()