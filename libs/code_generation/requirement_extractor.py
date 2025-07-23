#!/usr/bin/env python3
"""
要件抽出システム
Issue #184 Phase 2: より詳細な要件抽出と構造化
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class APIEndpoint:
    """API エンドポイント仕様"""
    method: str
    path: str
    description: str
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    auth_required: bool = True


@dataclass
class DataModel:
    """データモデル仕様"""
    name: str
    fields: List[Dict[str, Any]]
    relationships: List[Dict[str, str]]
    constraints: List[str]


@dataclass
class TechnicalRequirement:
    """技術要件"""
    category: str  # performance, security, scalability, etc.
    requirement: str
    metrics: Dict[str, Any]
    priority: str


class RequirementExtractor:
    """Issue から詳細な要件を抽出"""
    
    def __init__(self):
        # データ型のパターン
        self.data_type_patterns = {
            'string': r'(?i)\b(string|text|varchar|char)\b',
            'integer': r'(?i)\b(int(?:eger)?|number|numeric|bigint)\b',
            'boolean': r'(?i)\b(bool(?:ean)?|true|false)\b',
            'datetime': r'(?i)\b(date(?:time)?|timestamp|time)\b',
            'float': r'(?i)\b(float|double|decimal|real)\b',
            'uuid': r'(?i)\b(uuid|guid)\b',
            'json': r'(?i)\b(json|jsonb|object)\b',
            'array': r'(?i)\b(array|list|\[\])\b',
        }
        
        # フィールド属性のパターン
        self.field_attribute_patterns = {
            'required': r'(?i)\b(required|mandatory|must\s+have)\b',
            'optional': r'(?i)\b(optional|nullable|can\s+be\s+null)\b',
            'unique': r'(?i)\b(unique|distinct)\b',
            'primary_key': r'(?i)\b(primary\s+key|pk|id)\b',
            'foreign_key': r'(?i)\b(foreign\s+key|fk|references?)\b',
        }
        
        # HTTPステータスコードのマッピング
        self.status_code_mapping = {
            'success': 200,
            'created': 201,
            'accepted': 202,
            'no content': 204,
            'bad request': 400,
            'unauthorized': 401,
            'forbidden': 403,
            'not found': 404,
            'conflict': 409,
            'server error': 500,
        }
        
        # 認証タイプのパターン
        self.auth_patterns = {
            'jwt': r'(?i)\b(jwt|json\s*web\s*token)\b',
            'oauth': r'(?i)\b(oauth2?)\b',
            'api_key': r'(?i)\b(api[\s_-]?key)\b',
            'basic': r'(?i)\b(basic\s+auth(?:entication)?)\b',
            'bearer': r'(?i)\b(bearer\s+token)\b',
        }
    
    def extract_requirements(self, analyzed_issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析済みのIssueから詳細な要件を抽出
        
        Args:
            analyzed_issue: IssueAnalyzer の出力
            
        Returns:
            構造化された要件
        """
        # API仕様を詳細化
        api_endpoints = self._extract_detailed_api_specs(
            analyzed_issue.get('api_specs', []),
            analyzed_issue.get('sections', []),
            analyzed_issue.get('requirements', [])
        )
        
        # データモデルを抽出
        data_models = self._extract_data_models(
            analyzed_issue.get('sections', []),
            analyzed_issue.get('requirements', [])
        )
        
        # 技術要件を構造化
        technical_requirements = self._extract_technical_requirements(
            analyzed_issue.get('constraints', {}),
            analyzed_issue.get('requirements', [])
        )
        
        # 認証要件を抽出
        auth_requirements = self._extract_auth_requirements(
            analyzed_issue.get('tech_stack', {}),
            analyzed_issue.get('sections', [])
        )
        
        # ビジネスルールを抽出
        business_rules = self._extract_business_rules(
            analyzed_issue.get('requirements', [])
        )
        
        return {
            'api_endpoints': api_endpoints,
            'data_models': data_models,
            'technical_requirements': technical_requirements,
            'auth_requirements': auth_requirements,
            'business_rules': business_rules,
            'implementation_notes': self._generate_implementation_notes(
                api_endpoints, data_models, technical_requirements
            )
        }
    
    def _extract_detailed_api_specs(self, api_specs: List[Dict], 
                                   sections: List[Any], 
                                   requirements: List[Any]) -> List[APIEndpoint]:
        """詳細なAPI仕様を抽出"""
        detailed_endpoints = []
        
        for spec in api_specs:
            endpoint = APIEndpoint(
                method=spec.get('method', 'GET'),
                path=spec.get('endpoint', ''),
                description=spec.get('description', ''),
                parameters=self._extract_api_parameters(spec, sections),
                request_body=self._extract_request_body(spec, sections),
                response=self._extract_response_format(spec, sections),
                auth_required=self._determine_auth_requirement(spec, requirements)
            )
            detailed_endpoints.append(endpoint)
        
        return detailed_endpoints
    
    def _extract_api_parameters(self, api_spec: Dict, sections: List[Any]) -> List[Dict[str, Any]]:
        """APIパラメータを抽出"""
        parameters = []
        
        # パスパラメータ
        path_params = api_spec.get('parameters', [])
        for param in path_params:
            parameters.append({
                'name': param['name'],
                'in': 'path',
                'type': param.get('type', 'string'),
                'required': param.get('required', True),
                'description': f"Path parameter {param['name']}"
            })
        
        # クエリパラメータを文脈から推測
        endpoint_path = api_spec.get('endpoint', '')
        if 'list' in endpoint_path.lower() or 'search' in endpoint_path.lower():
            # ページネーション
            parameters.extend([
                {
                    'name': 'page',
                    'in': 'query',
                    'type': 'integer',
                    'required': False,
                    'description': 'Page number for pagination',
                    'default': 1
                },
                {
                    'name': 'limit',
                    'in': 'query',
                    'type': 'integer',
                    'required': False,
                    'description': 'Number of items per page',
                    'default': 20
                }
            ])
            
            # フィルタリング
            if 'search' in endpoint_path.lower():
                parameters.append({
                    'name': 'q',
                    'in': 'query',
                    'type': 'string',
                    'required': False,
                    'description': 'Search query'
                })
        
        return parameters
    
    def _extract_request_body(
        self,
        api_spec: Dict,
        sections: List[Any]
    ) -> Optional[Dict[str, Any]]:
        """リクエストボディの仕様を抽出"""
        method = api_spec.get('method', 'GET')
        
        if method in ['POST', 'PUT', 'PATCH']:
            # エンドポイント名から推測
            endpoint = api_spec.get('endpoint', '')
            
            if 'user' in endpoint.lower():
                return {
                    'content_type': 'application/json',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'username': {'type': 'string', 'required': True},
                            'email': {'type': 'string', 'format': 'email', 'required': True},
                            'password': {'type': 'string', 'minLength': 8, 'required': True}
                        }
                    }
                }
            elif 'auth' in endpoint.lower() or 'login' in endpoint.lower():
                return {
                    'content_type': 'application/json',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'username': {'type': 'string', 'required': True},
                            'password': {'type': 'string', 'required': True}
                        }
                    }
                }
        
        return None
    
    def _extract_response_format(self, api_spec: Dict, sections: List[Any]) -> Dict[str, Any]:
        """レスポンス形式を抽出"""
        endpoint = api_spec.get('endpoint', '')
        method = api_spec.get('method', 'GET')
        
        # 成功レスポンス
        success_response = {
            'status_code': 200 if method == 'GET' else 201 if method == 'POST' else 200,
            'content_type': 'application/json',
            'schema': {}
        }
        
        # エンドポイントに基づいてスキーマを推測
        if 'user' in endpoint.lower():
            if method == 'GET' and '{' in endpoint:  # 単一リソース
                success_response['schema'] = {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'string'},
                        'username': {'type': 'string'},
                        'email': {'type': 'string'},
                        'created_at': {'type': 'string', 'format': 'datetime'}
                    }
                }
            elif method == 'GET':  # リスト
                success_response['schema'] = {
                    'type': 'object',
                    'properties': {
                        'data': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'id': {'type': 'string'},
                                    'username': {'type': 'string'},
                                    'email': {'type': 'string'}
                                }
                            }
                        },
                        'pagination': {
                            'type': 'object',
                            'properties': {
                                'page': {'type': 'integer'},
                                'limit': {'type': 'integer'},
                                'total': {'type': 'integer'}
                            }
                        }
                    }
                }
        
        return success_response
    
    def _determine_auth_requirement(self, api_spec: Dict, requirements: List[Any]) -> bool:
        """認証が必要かどうかを判定"""
        endpoint = api_spec.get('endpoint', '').lower()
        
        # 公開エンドポイントのパターン
        public_patterns = ['login', 'register', 'signup', 'health', 'status']
        
        return not any(pattern in endpoint for pattern in public_patterns)
    
    def _extract_data_models(self, sections: List[Any], requirements: List[Any]) -> List[DataModel]:
        """データモデルを抽出"""
        models = []
        
        # セクションからデータモデル情報を探す
        for section in sections:
            if hasattr(section, 'section_type') and section.section_type == 'data_model':
                # データモデルの記述をパース
                model_info = self._parse_data_model_description(section.content)
                if model_info:
                    models.append(model_info)
        
        # 要件からもデータモデルを推測
        for req in requirements:
            if hasattr(req, 'type') and req.type == 'data_model':
                model_info = self._infer_data_model_from_requirement(req.description)
                if model_info and not any(m.name == model_info.name for m in models):
                    models.append(model_info)
        
        # デフォルトのユーザーモデル（多くのケースで必要）
        if not any(m.name.lower() == 'user' for m in models):
            models.append(self._create_default_user_model())
        
        return models
    
    def _parse_data_model_description(self, content: str) -> Optional[DataModel]:
        """データモデルの記述をパース"""
        # テーブル定義のパターン
        table_pattern = r'(?i)(?:table|model|entity)\s+(\w+)'
        table_match = re.search(table_pattern, content)
        
        if not table_match:
            return None
        
        model_name = table_match.group(1)
        fields = []
        
        # フィールド定義のパターン
        field_pattern = r'(?i)(\w+)\s*[:]\s*(\w+)(?:\s*\(([^)]+)\))?'
        
        for match in re.finditer(field_pattern, content):
            field_name = match.group(1)
            field_type = match.group(2)
            attributes = match.group(3) or ''
            
            field = {
                'name': field_name,
                'type': self._normalize_data_type(field_type),
                'required': 'required' in attributes.lower() or 'not null' in attributes.lower(),
                'unique': 'unique' in attributes.lower(),
                'primary_key': field_name.lower() == 'id' or 'primary' in attributes.lower()
            }
            
            fields.append(field)
        
        return DataModel(
            name=model_name,
            fields=fields,
            relationships=[],
            constraints=[]
        )
    
    def _infer_data_model_from_requirement(self, description: str) -> Optional[DataModel]:
        """要件からデータモデルを推測"""
        # 基本的なモデル名の抽出
        model_pattern = r'(?i)(?:create|implement|design)\s+(?:a\s+)?(\w+)\s+(?:model|schema|table)'
        match = re.search(model_pattern, description)
        
        if not match:
            return None
        
        model_name = match.group(1)
        
        # 一般的なフィールドを推測
        fields = [
            {'name': 'id', 'type': 'uuid', 'required': True, 'primary_key': True},
            {'name': 'created_at', 'type': 'datetime', 'required': True},
            {'name': 'updated_at', 'type': 'datetime', 'required': True}
        ]
        
        # モデル名に基づいて追加フィールドを推測
        if 'user' in model_name.lower():
            fields.extend([
                {'name': 'username', 'type': 'string', 'required': True, 'unique': True},
                {'name': 'email', 'type': 'string', 'required': True, 'unique': True},
                {'name': 'password_hash', 'type': 'string', 'required': True}
            ])
        elif 'product' in model_name.lower():
            fields.extend([
                {'name': 'name', 'type': 'string', 'required': True},
                {'name': 'description', 'type': 'string', 'required': False},
                {'name': 'price', 'type': 'float', 'required': True}
            ])
        
        return DataModel(
            name=model_name,
            fields=fields,
            relationships=[],
            constraints=[]
        )
    
    def _create_default_user_model(self) -> DataModel:
        """デフォルトのユーザーモデルを作成"""
        return DataModel(
            name='User',
            fields=[
                {'name': 'id', 'type': 'uuid', 'required': True, 'primary_key': True},
                {'name': 'username', 'type': 'string', 'required': True, 'unique': True, 'max_length': 50},
                {'name': 'email', 'type': 'string', 'required': True, 'unique': True, 'format': 'email'},
                {'name': 'password_hash', 'type': 'string', 'required': True},
                {'name': 'is_active', 'type': 'boolean', 'required': True, 'default': True},
                {'name': 'created_at', 'type': 'datetime', 'required': True},
                {'name': 'updated_at', 'type': 'datetime', 'required': True}
            ],
            relationships=[],
            constraints=['email must be valid', 'username must be unique']
        )
    
    def _normalize_data_type(self, type_str: str) -> str:
        """データ型を正規化"""
        type_lower = type_str.lower()
        
        for normalized_type, pattern in self.data_type_patterns.items():
            if re.search(pattern, type_lower):
                return normalized_type
        
        return 'string'  # デフォルト
    
    def _extract_technical_requirements(self, constraints: Dict[str, Any], 
                                      requirements: List[Any]) -> List[TechnicalRequirement]:
        """技術要件を抽出"""
        tech_requirements = []
        
        # パフォーマンス要件
        if 'performance' in constraints:
            perf = constraints['performance']
            
            if 'response_time' in perf:
                tech_requirements.append(TechnicalRequirement(
                    category='performance',
                    requirement=f"Response time must be less than {perf['response_time']}ms",
                    metrics={'response_time_ms': int(perf['response_time'])},
                    priority='high'
                ))
            
            if 'concurrent_users' in perf:
                tech_requirements.append(TechnicalRequirement(
                    category='scalability',
                    requirement=f"Support {perf['concurrent_users']} concurrent users",
                    metrics={'concurrent_users': int(perf['concurrent_users'])},
                    priority='high'
                ))
        
        # レート制限
        if 'rate_limit' in constraints:
            rate_limit = constraints['rate_limit']
            tech_requirements.append(TechnicalRequirement(
                category='security',
                requirement=f"Rate limiting: {rate_limit['limit']} requests per {rate_limit['period']}",
                metrics={
                    'rate_limit': rate_limit['limit'],
                    'period': rate_limit['period']
                },
                priority='medium'
            ))
        
        return tech_requirements
    
    def _extract_auth_requirements(self, tech_stack: Dict[str, List[str]], 
                                 sections: List[Any]) -> Dict[str, Any]:
        """認証要件を抽出"""
        auth_req = {
            'type': 'none',
            'mechanisms': [],
            'token_lifetime': None,
            'refresh_enabled': False
        }
        
        # 技術スタックから認証タイプを検出
        if 'auth' in tech_stack:
            auth_types = tech_stack['auth']
            if 'jwt' in auth_types:
                auth_req['type'] = 'jwt'
                auth_req['token_lifetime'] = '1h'  # デフォルト
                auth_req['refresh_enabled'] = True
            elif 'oauth' in auth_types:
                auth_req['type'] = 'oauth2'
                auth_req['mechanisms'] = ['authorization_code', 'client_credentials']
        
        return auth_req
    
    def _extract_business_rules(self, requirements: List[Any]) -> List[Dict[str, str]]:
        """ビジネスルールを抽出"""
        rules = []
        
        # ルールを示すキーワード
        rule_keywords = ['must', 'should', 'cannot', 'only', 'require', 'limit']
        
        for req in requirements:
            if hasattr(req, 'description'):
                desc_lower = req.description.lower()
                if any(keyword in desc_lower for keyword in rule_keywords):
                    rules.append({
                        'rule': req.description,
                        'type': 'validation' if 'valid' in desc_lower else 'business_logic',
                        'priority': req.priority if hasattr(req, 'priority') else 'medium'
                    })
        
        return rules
    
    def _generate_implementation_notes(self, api_endpoints: List[APIEndpoint],
                                     data_models: List[DataModel],
                                     tech_requirements: List[TechnicalRequirement]) -> List[str]:
        """実装上の注意点を生成"""
        notes = []
        
        # API関連の注意点
        if api_endpoints:
            notes.append("Implement proper input validation for all API endpoints")
            notes.append("Use consistent error response format across all endpoints")
            
            # 認証が必要なエンドポイントがある場合
            if any(ep.auth_required for ep in api_endpoints):
                notes.append("Implement authentication middleware for protected endpoints")
        
        # データモデル関連の注意点
        if data_models:
            notes.append("Create database migrations for all data models")
            notes.append("Implement proper indexing for unique and frequently queried fields")
        
        # 技術要件関連の注意点
        for req in tech_requirements:
            if req.category == 'performance':
                notes.append("Consider implementing caching for improved performance")
            elif req.category == 'security':
                notes.append("Implement rate limiting and request throttling")
        
        return notes