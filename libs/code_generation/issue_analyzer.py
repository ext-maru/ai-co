#!/usr/bin/env python3
"""
Issue分析エンジン
Issue #184 Phase 2: より高度なIssue理解システム
NLP依存を最小限にし、パターンマッチングベースで実装
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class IssueSection:
    """Issue内のセクション"""
    title: str
    content: str
    section_type: str  # requirements, examples, constraints, description


@dataclass
class RequirementItem:
    """要件アイテム"""
    type: str  # functional, non_functional, api, data_model
    description: str
    details: Dict[str, Any]
    priority: str  # high, medium, low


class IssueAnalyzer:
    """Issue内容を分析し、構造化された情報を抽出"""
    
    def __init__(self):
        """初期化メソッド"""
        # セクションを識別するパターン
        self.section_patterns = {
            'requirements': r'(?i)(requirements?|needs?|should|must|features?):?\s*\n',
            'api': r'(?i)(api|endpoints?|routes?):?\s*\n',
            'examples': r'(?i)(examples?|samples?|usage):?\s*\n',
            'constraints': r'(?i)(constraints?|limitations?|performance|security):?\s*\n',
            'data_model': r'(?i)(data\s*models?|schemas?|database):?\s*\n',
        }
        
        # API仕様を抽出するパターン
        self.api_patterns = {
            'endpoint': r'(?i)(?:GET|POST|PUT|DELETE|PATCH)\s+([/\w\{\}]+)',
            'rest_endpoint': r'(?i)([/\w\{\}]+)\s*[-–]\s*(?:GET|POST|PUT|DELETE|PATCH)',
            'endpoint_with_desc': r'(?i)(?:GET|POST|PUT|DELETE|PATCH)\s+([/\w\{\}]+)\s*[-–:]?\s*(.+)',
        }
        
        # 技術要件を識別するパターン
        self.tech_patterns = {
            'framework': {
                'flask': r'(?i)\b(flask)\b',
                'django': r'(?i)\b(django)\b',
                'fastapi': r'(?i)\b(fastapi)\b',
                'express': r'(?i)\b(express)\b',
            },
            'database': {
                'postgresql': r'(?i)\b(postgres(?:ql)?)\b',
                'mysql': r'(?i)\b(mysql)\b',
                'mongodb': r'(?i)\b(mongodb?)\b',
                'redis': r'(?i)\b(redis)\b',
                'sqlite': r'(?i)\b(sqlite)\b',
            },
            'auth': {
                'jwt': r'(?i)\b(jwt|json\s*web\s*tokens?)\b',
                'oauth': r'(?i)\b(oauth2?)\b',
                'basic': r'(?i)\b(basic\s*auth(?:entication)?)\b',
            },
            'cloud': {
                'aws': r'(?i)\b(aws|amazon\s*web\s*services?)\b',
                's3': r'(?i)\b(s3|simple\s*storage)\b',
                'ec2': r'(?i)\b(ec2|elastic\s*compute)\b',
                'lambda': r'(?i)\b(lambda)\b',
            }
        }
        
        # 制約条件パターン
        self.constraint_patterns = {
            'performance': {
                'requests_per_second': r'(?i)(\d+)\s*(?:requests?/s(?:ec)?|req/s)',
                'response_time': r'(?i)(?:response\s*time|latency)\s*[<>]?\s*(\d+)\s*ms',
                'concurrent_users': r'(?i)(\d+)\s*(?:concurrent|simultaneous)\s*users?',
                'uptime': r'(?i)(\d+(?:\.\d+)?)\s*%\s*uptime',
            },
            'rate_limit': r'(?i)(\d+)\s*(?:requests?)\s*(?:per|/)\s*(minute|hour|day)',
            'data_size': r'(?i)(\d+)\s*(?:MB|GB|TB)',
        }
        
        # 優先度キーワード
        self.priority_keywords = {
            'high': ['must', 'required', 'critical', 'essential', 'mandatory'],
            'medium': ['should', 'recommended', 'preferred', 'important'],
            'low': ['could', 'optional', 'nice to have', 'future']
        }
    
    def analyze(self, issue_title: str, issue_body: str) -> Dict[str, Any]:
        """
        Issue を分析して構造化された情報を返す
        
        Args:
            issue_title: Issue のタイトル
            issue_body: Issue の本文
            
        Returns:
            分析結果
        """
        # セクションを抽出
        sections = self._extract_sections(issue_body)
        
        # 要件を抽出
        requirements = self._extract_requirements(sections, issue_body)
        
        # API仕様を抽出
        api_specs = self._extract_api_specs(sections, issue_body)
        
        # 技術スタックを検出
        tech_stack = self._detect_tech_stack(issue_title + " " + issue_body)
        
        # 制約条件を抽出
        constraints = self._extract_constraints(sections, issue_body)
        
        # Issueの意図を分類
        intent = self._classify_intent(issue_title, issue_body)
        
        # 複雑度を評価
        complexity = self._evaluate_complexity(requirements, api_specs, constraints)
        
        return {
            'sections': sections,
            'requirements': requirements,
            'api_specs': api_specs,
            'tech_stack': tech_stack,
            'constraints': constraints,
            'intent': intent,
            'complexity': complexity,
            'structured_context': self._create_structured_context(
                requirements, api_specs, tech_stack, constraints
            )
        }
    
    def _extract_sections(self, issue_body: str) -> List[IssueSection]:
        """Issue本文をセクションに分割"""
        sections = []
        lines = issue_body.split('\n')
        
        current_section = None
        current_content = []
        
        for line in lines:
            # セクションヘッダーをチェック
            section_found = False
            for section_type, pattern in self.section_patterns.items():
                if re.match(pattern, line):
                    # 前のセクションを保存
                    if current_section:
                        sections.append(IssueSection(
                            title=current_section['title'],
                            content='\n'.join(current_content).strip(),
                            section_type=current_section['type']
                        ))
                    
                    # 新しいセクション開始
                    current_section = {
                        'title': line.strip(),
                        'type': section_type
                    }
                    current_content = []
                    section_found = True
                    break
            
            if not section_found and current_section:
                current_content.append(line)
        
        # 最後のセクションを保存
        if current_section:
            sections.append(IssueSection(
                title=current_section['title'],
                content='\n'.join(current_content).strip(),
                section_type=current_section['type']
            ))
        
        # セクションが見つからない場合、全体を1つのセクションとして扱う
        if not sections:
            sections.append(IssueSection(
                title='Description',
                content=issue_body,
                section_type='description'
            ))
        
        return sections
    
    def _extract_requirements(
        self,
        sections: List[IssueSection],
        full_text: str
    ) -> List[RequirementItem]:
        """要件を抽出"""
        requirements = []
        
        # 番号付きリストのパターン
        numbered_pattern = r'^\s*(?:\d+\.|[-*])\s+(.+)$'
        
        # セクションから要件を抽出
        for section in sections:
            if section.section_type in ['requirements', 'description']:
                lines = section.content.split('\n')
                for line in lines:
                    match = re.match(numbered_pattern, line)
                    if match:
                        req_text = match.group(1).strip()
                        req_item = self._parse_requirement(req_text)
                        if not (req_item):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if req_item:
                            requirements.append(req_item)
        
        # 全文から「must」「should」などのキーワードで要件を抽出
        requirement_patterns = [
            r'(?i)(?:must|should|shall|need\s+to)\s+(.+?)(?:\.|$)',
            r'(?i)(?:implement|create|add|build)\s+(.+?)(?:\.|$)',
        ]
        
        for pattern in requirement_patterns:
        # 繰り返し処理
            matches = re.findall(pattern, full_text)
            for match in matches:
                req_item = self._parse_requirement(match)
                if req_item and not self._is_duplicate_requirement(req_item, requirements):
                    requirements.append(req_item)
        
        return requirements
    
    def _parse_requirement(self, text: str) -> Optional[RequirementItem]:
        """テキストから要件を解析"""
        # API要件のチェック
        api_keywords = ['endpoint', 'api', 'route', 'GET', 'POST', 'PUT', 'DELETE']
        if any(keyword in text.upper() for keyword in api_keywords):
            return RequirementItem(
                type='api',
                description=text,
                details=self._extract_api_details(text),
                priority=self._determine_priority(text)
            )
        
        # データモデル要件のチェック
        data_keywords = ['model', 'schema', 'table', 'field', 'column']
        if any(keyword in text.lower() for keyword in data_keywords):
            return RequirementItem(
                type='data_model',
                description=text,
                details={},
                priority=self._determine_priority(text)
            )
        
        # 非機能要件のチェック
        nonfunc_keywords = ['performance', 'security', 'scalability', 'reliability']
        if any(keyword in text.lower() for keyword in nonfunc_keywords):
            return RequirementItem(
                type='non_functional',
                description=text,
                details={},
                priority='high'  # 非機能要件は通常高優先度
            )
        
        # その他は機能要件
        return RequirementItem(
            type='functional',
            description=text,
            details={},
            priority=self._determine_priority(text)
        )
    
    def _extract_api_details(self, text: str) -> Dict[str, Any]:
        """APIの詳細を抽出"""
        details = {}
        
        # HTTPメソッドを検出
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        for method in methods:
            if method in text.upper():
                details['method'] = method
                break
        
        # エンドポイントを検出
        endpoint_match = re.search(r'[/][\w/\{\}]+', text)
        if endpoint_match:
            details['endpoint'] = endpoint_match.group(0)
        
        return details
    
    def _is_duplicate_requirement(
        self,
        req: RequirementItem,
        existing: List[RequirementItem]
    ) -> bool:
        """重複要件かチェック"""
        for existing_req in existing:
            # 説明文の類似度をチェック（簡易版）
            if req.description.lower() in existing_req.description.lower() or \
               existing_req.description.lower() in req.description.lower():
                return True
        return False
    
    def _extract_api_specs(
        self,
        sections: List[IssueSection],
        full_text: str
    ) -> List[Dict[str, Any]]:
        """API仕様を抽出"""
        api_specs = []
        
        # すべてのパターンで API を探す
        for pattern_name, pattern in self.api_patterns.items():
            matches = re.findall(pattern, full_text, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    endpoint = match[0]
                    description = match[1] if len(match) > 1 else ''
                else:
                    endpoint = match
                    description = ''
                
                # HTTPメソッドを検出
                method_match = re.search(r'(GET|POST|PUT|DELETE|PATCH)', 
                                       full_text[max(
                                           0,
                                           full_text.find(endpoint)-20):full_text.find(endpoint)+20]
                                       )
                method = method_match.group(1) if method_match else 'GET'
                
                api_spec = {
                    'method': method,
                    'endpoint': endpoint,
                    'description': description.strip(),
                    'parameters': self._extract_parameters(endpoint)
                }
                
                # 重複チェック
                if not any(spec['endpoint'] == api_spec['endpoint'] and 
                          spec['method'] == api_spec['method'] for spec in api_specs):
                    api_specs.append(api_spec)
        
        return api_specs
    
    def _extract_parameters(self, endpoint: str) -> List[Dict[str, str]]:
        """エンドポイントからパラメータを抽出"""
        params = []
        # {id} や {user_id} などのパターンを検出
        param_matches = re.findall(r'\{(\w+)\}', endpoint)
        for param in param_matches:
            params.append({
                'name': param,
                'type': 'string',  # デフォルト
                'required': True
            })
        return params
    
    def _detect_tech_stack(self, text: str) -> Dict[str, List[str]]:
        """技術スタックを検出"""
        detected_stack = {}
        
        # 繰り返し処理
        for category, patterns in self.tech_patterns.items():
            detected_stack[category] = []
            for tech, pattern in patterns.items():
                if re.search(pattern, text):
                    detected_stack[category].append(tech)
        
        # 空のカテゴリを削除
        detected_stack = {k: v for k, v in detected_stack.items() if v}
        
        return detected_stack
    
    def _extract_constraints(self, sections: List[IssueSection], full_text: str) -> Dict[str, Any]:
        """制約条件を抽出"""
        constraints = {}
        
        # パフォーマンス制約
        perf_constraints = {}
        for constraint_type, pattern in self.constraint_patterns['performance'].items():
            match = re.search(pattern, full_text)
            if match:
                perf_constraints[constraint_type] = match.group(1)
        
        if perf_constraints:
            constraints['performance'] = perf_constraints
        
        # レート制限
        rate_match = re.search(self.constraint_patterns['rate_limit'], full_text)
        if rate_match:
            constraints['rate_limit'] = {
                'limit': int(rate_match.group(1)),
                'period': rate_match.group(2)
            }
        
        # データサイズ制限
        size_match = re.search(self.constraint_patterns['data_size'], full_text)
        if size_match:
            constraints['data_size'] = size_match.group(0)
        
        return constraints
    
    def _classify_intent(self, title: str, body: str) -> Dict[str, str]:
        """Issueの意図を分類"""
        text = (title + " " + body).lower()
        
        # プライマリ意図の判定
        if any(word in text for word in ['bug', 'fix', 'error', 'issue', 'problem']):
            primary = 'bug_fix'
        elif any(word in text for word in ['feature', 'implement', 'add', 'create', 'new']):
            primary = 'feature_implementation'
        elif any(word in text for word in ['improve', 'optimize', 'enhance', 'refactor']):
            primary = 'improvement'
        elif any(word in text for word in ['document', 'docs', 'readme']):
            primary = 'documentation'
        else:
            primary = 'other'
        
        # カテゴリの判定
        if any(word in text for word in ['api', 'endpoint', 'rest', 'graphql']):
            category = 'api'
        elif any(word in text for word in ['ui', 'frontend', 'interface', 'view']):
            category = 'ui'
        elif any(word in text for word in ['database', 'model', 'schema']):
            category = 'data'
        elif any(word in text for word in ['integration', 'connect', 'third-party']):
            category = 'integration'
        else:
            category = 'general'
        
        return {
            'primary': primary,
            'category': category
        }
    
    def _evaluate_complexity(self, requirements: List[RequirementItem], 
                           api_specs: List[Dict], constraints: Dict) -> str:
        """複雑度を評価"""
        score = 0
        
        # 要件数による評価
        score += len(requirements) * 2
        
        # API数による評価
        score += len(api_specs) * 3
        
        # 制約条件による評価
        score += len(constraints) * 5
        
        # 高優先度要件による評価
        high_priority_count = sum(1 for req in requirements if req.priority == 'high')
        score += high_priority_count * 3
        
        # スコアに基づいて複雑度を判定
        if score >= 30:
            return 'high'
        elif score >= 15:
            return 'medium'
        else:
            return 'low'
    
    def _determine_priority(self, text: str) -> str:
        """テキストから優先度を判定"""
        text_lower = text.lower()
        
        for priority, keywords in self.priority_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return priority
        
        return 'medium'  # デフォルト
    
    def _create_structured_context(self, requirements: List[RequirementItem],
                                 api_specs: List[Dict], tech_stack: Dict,
                                 constraints: Dict) -> Dict[str, Any]:
        """構造化されたコンテキストを作成"""
        return {
            'functional_requirements': [
                req for req in requirements if req.type == 'functional'
            ],
            'api_requirements': [
                req for req in requirements if req.type == 'api'
            ] + api_specs,
            'non_functional_requirements': [
                req for req in requirements if req.type == 'non_functional'
            ],
            'technology_stack': tech_stack,
            'constraints': constraints,
            'priority_summary': {
                'high': sum(1 for req in requirements if req.priority == 'high'),
                'medium': sum(1 for req in requirements if req.priority == 'medium'),
                'low': sum(1 for req in requirements if req.priority == 'low')
            }
        }