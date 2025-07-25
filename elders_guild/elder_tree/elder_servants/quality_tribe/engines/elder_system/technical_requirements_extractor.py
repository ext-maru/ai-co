#!/usr/bin/env python3
"""
Technical Requirements Extractor
Phase 4: 実装系Issueから技術要件を自動抽出

主な機能:
1.0 技術スタック識別（言語、フレームワーク、ライブラリ）
2.0 API/インターフェース要件抽出
3.0 パフォーマンス要件識別
4.0 セキュリティ要件抽出
5.0 テスト要件生成
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class RequirementType(Enum):
    """要件タイプ"""
    FUNCTIONAL = "functional"           # 機能要件
    TECHNICAL = "technical"            # 技術要件
    PERFORMANCE = "performance"        # パフォーマンス要件
    SECURITY = "security"              # セキュリティ要件
    INTERFACE = "interface"            # インターフェース要件
    TESTING = "testing"                # テスト要件
    INTEGRATION = "integration"        # 統合要件
    DATA = "data"                      # データ要件


@dataclass
class TechnicalRequirement:
    """技術要件"""
    requirement_type: RequirementType
    category: str
    description: str
    priority: str  # high, medium, low
    specifications: Dict[str, Any]
    constraints: List[str]
    acceptance_criteria: List[str]
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        result = asdict(self)
        result['requirement_type'] = self.requirement_type.value
        return result


@dataclass
class TechnicalStack:
    """技術スタック"""
    languages: List[str]
    frameworks: List[str]
    libraries: List[str]
    databases: List[str]
    services: List[str]
    tools: List[str]
    
    def is_empty(self) -> bool:
        """空かどうか確認"""
        return not any([
            self.languages, self.frameworks, self.libraries,
            self.databases, self.services, self.tools
        ])


@dataclass
class ExtractionResult:
    """抽出結果"""
    technical_stack: TechnicalStack
    requirements: List[TechnicalRequirement]
    implementation_steps: List[Dict[str, Any]]
    estimated_complexity: str  # low, medium, high, very_high
    risk_factors: List[Dict[str, str]]
    dependencies: List[str]
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            'technical_stack': asdict(self.technical_stack),
            'requirements': [req.to_dict() for req in self.requirements],
            'implementation_steps': self.implementation_steps,
            'estimated_complexity': self.estimated_complexity,
            'risk_factors': self.risk_factors,
            'dependencies': self.dependencies
        }


class TechnicalRequirementsExtractor:
    """技術要件抽出エンジン"""
    
    def __init__(self):
        """初期化メソッド"""
        # 技術キーワードデータベース
        self.tech_keywords = {
            'languages': {
                'python': ['python', 'py', 'pip', 'conda', 'venv'],
                'javascript': ['javascript', 'js', 'node', 'npm', 'yarn'],
                'typescript': ['typescript', 'ts', 'tsc'],
                'go': ['go', 'golang', 'go mod'],
                'rust': ['rust', 'cargo', 'rustc'],
                'java': ['java', 'jvm', 'maven', 'gradle'],
            },
            'frameworks': {
                'fastapi': ['fastapi', 'fast api', 'starlette'],
                'django': ['django', 'django rest'],
                'flask': ['flask', 'werkzeug'],
                'react': ['react', 'jsx', 'hooks'],
                'vue': ['vue', 'vuex', 'vue router'],
                'angular': ['angular', 'ng'],
                'express': ['express', 'express.js'],
            },
            'databases': {
                'postgresql': ['postgresql', 'postgres', 'pg', 'psql'],
                'mysql': ['mysql', 'mariadb'],
                'mongodb': ['mongodb', 'mongo', 'mongoose'],
                'redis': ['redis', 'redis cache'],
                'elasticsearch': ['elasticsearch', 'elastic', 'es'],
            },
            'services': {
                'docker': ['docker', 'dockerfile', 'container'],
                'kubernetes': ['kubernetes', 'k8s', 'kubectl'],
                'aws': ['aws', 'amazon web services', 's3', 'ec2', 'lambda'],
                'gcp': ['gcp', 'google cloud', 'bigquery'],
                'azure': ['azure', 'microsoft azure'],
            }
        }
        
        # パフォーマンス要件パターン
        self.performance_patterns = [
            (r'(\d+)\s*(ms|milliseconds?)\s*(response|latency|for)', 'response_time'),
            (r'under\s+(\d+)\s*(ms|milliseconds?)', 'response_time'),
            (r'(\d+)\s*(req|requests?)/s(ec)?', 'throughput'),
            (r'(\d+)\s*%\s*(cpu|memory|ram)', 'resource_usage'),
            (r'(\d+)\s*(gb|mb|kb)\s*(memory|ram|storage)', 'memory_limit'),
            (r'scale\s+to\s+(\d+)\s*(users?|connections?)', 'scalability'),
            (r'(\d+)\s*concurrent\s*(users?|connections?)', 'concurrency'),
        ]
        
        # セキュリティ要件パターン
        self.security_patterns = [
            'authentication', 'authorization', 'oauth', 'jwt', 'token',
            'encryption', 'ssl', 'tls', 'https', 'secure',
            'password', 'hash', 'salt', 'bcrypt', 'argon2',
            'permission', 'role', 'rbac', 'access control',
            'vulnerability', 'security scan', 'penetration test',
            'xss', 'csrf', 'sql injection', 'security headers'
        ]
        
    def extract_requirements(self, issue_data: Dict[str, Any]) -> ExtractionResult:
        """Issueから技術要件を抽出"""
        try:
            # 基本情報を取得
            title = issue_data.get('title', '')
            body = issue_data.get('body', '')
            
            # labelsの処理 - GitHub APIではlabelsは文字列または辞書の配列
            raw_labels = issue_data.get('labels', [])
            labels = []
            for label in raw_labels:
                if isinstance(label, str):
                    labels.append(label)
                elif isinstance(label, dict) and 'name' in label:
                    labels.append(label['name'])
            
            # 全テキストを結合
            full_text = f"{title}\n{body}".lower()
            
            # 技術スタックを抽出
            tech_stack = self._extract_technical_stack(full_text, labels)
            
            # 各種要件を抽出
            requirements = []
            
            # 機能要件
            func_reqs = self._extract_functional_requirements(full_text)
            requirements.extend(func_reqs)
            
            # パフォーマンス要件
            perf_reqs = self._extract_performance_requirements(full_text)
            requirements.extend(perf_reqs)
            
            # セキュリティ要件
            sec_reqs = self._extract_security_requirements(full_text)
            requirements.extend(sec_reqs)
            
            # インターフェース要件
            interface_reqs = self._extract_interface_requirements(full_text)
            requirements.extend(interface_reqs)
            
            # テスト要件
            test_reqs = self._extract_testing_requirements(full_text)
            requirements.extend(test_reqs)
            
            # 実装ステップを生成
            implementation_steps = self._generate_implementation_steps(
                requirements, tech_stack
            )
            
            # 複雑度を推定
            complexity = self._estimate_complexity(requirements, tech_stack)
            
            # リスク要因を識別
            risk_factors = self._identify_risk_factors(requirements, tech_stack)
            
            # 依存関係を抽出
            dependencies = self._extract_dependencies(full_text, tech_stack)
            
            return ExtractionResult(
                technical_stack=tech_stack,
                requirements=requirements,
                implementation_steps=implementation_steps,
                estimated_complexity=complexity,
                risk_factors=risk_factors,
                dependencies=dependencies
            )
            
        except Exception as e:
            logger.error(f"Failed to extract requirements: {e}")
            # 最小限の結果を返す
            return ExtractionResult(
                technical_stack=TechnicalStack([], [], [], [], [], []),
                requirements=[],
                implementation_steps=[],
                estimated_complexity='unknown',
                risk_factors=[{'type': 'extraction_error', 'description': str(e)}],
                dependencies=[]
            )
    
    def _extract_technical_stack(self, text: str, labels: List[str]) -> TechnicalStack:
        """技術スタックを抽出"""
        stack = TechnicalStack(
            languages=[], frameworks=[], libraries=[],
            databases=[], services=[], tools=[]
        )
        
        # ラベルからも抽出
        label_text = ' '.join(labels).lower()
        combined_text = f"{text} {label_text}"
        
        # 言語を検出
        for lang, keywords in self.tech_keywords['languages'].items():
            if any(kw in combined_text for kw in keywords):
                if lang not in stack.languages:
                    stack.languages.append(lang)
        
        # フレームワークを検出
        for fw, keywords in self.tech_keywords['frameworks'].items():
            if any(kw in combined_text for kw in keywords):
                if fw not in stack.frameworks:
                    stack.frameworks.append(fw)
        
        # データベースを検出
        for db, keywords in self.tech_keywords['databases'].items():
            if any(kw in combined_text for kw in keywords):
                if db not in stack.databases:
                    stack.databases.append(db)
        
        # サービスを検出
        for svc, keywords in self.tech_keywords['services'].items():
            if any(kw in combined_text for kw in keywords):
                if svc not in stack.services:
                    stack.services.append(svc)
        
        # 特定のライブラリパターンを検出
        library_patterns = [
            r'import\s+(\w+)',
            r'require\s*\(\s*[\'"](\w+)[\'"]\s*\)',
            r'from\s+(\w+)\s+import',
            r'use\s+(\w+)',
        ]
        
        for pattern in library_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in stack.libraries and len(match) > 2:
                    stack.libraries.append(match)
        
        # ツールを検出
        tool_keywords = ['pytest', 'jest', 'mocha', 'webpack', 'babel', 'eslint', 'prettier']
        for tool in tool_keywords:
            if tool in combined_text:
                if tool not in stack.tools:
                    stack.tools.append(tool)
        
        return stack
    
    def _extract_functional_requirements(self, text: str) -> List[TechnicalRequirement]:
        """機能要件を抽出"""
        requirements = []
        
        # 機能要件のパターン
        patterns = [
            r'(?:should|must|need to|have to)\s+([^.]+)',
            r'(?:implement|create|add|build)\s+([^.]+)',
            r'(?:feature|functionality):\s*([^.]+)',
            r'(?:as a user,?\s*i want to)\s+([^.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                req = TechnicalRequirement(
                    requirement_type=RequirementType.FUNCTIONAL,
                    category='feature',
                    description=match.strip(),
                    priority=self._determine_priority(match),
                    specifications={},
                    constraints=[],
                    acceptance_criteria=[]
                )
                requirements.append(req)
        
        return requirements
    
    def _extract_performance_requirements(self, text: str) -> List[TechnicalRequirement]:
        """パフォーマンス要件を抽出"""
        requirements = []
        
        for pattern, metric_type in self.performance_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match[0] if isinstance(match, tuple) else match
                
                req = TechnicalRequirement(
                    requirement_type=RequirementType.PERFORMANCE,
                    category=metric_type,
                    description=f"{metric_type}: {value}",
                    priority='high',
                    specifications={
                        'metric': metric_type,
                        'value': value,
                        'unit': match[1] if isinstance(match, tuple) and len(match) > 1 else ''
                    },
                    constraints=[f"Must achieve {value} {metric_type}"],
                    acceptance_criteria=[f"{metric_type} measurement meets target"]
                )
                requirements.append(req)
        
        return requirements
    
    def _extract_security_requirements(self, text: str) -> List[TechnicalRequirement]:
        """セキュリティ要件を抽出"""
        requirements = []
        found_security_aspects = []
        
        for keyword in self.security_patterns:
            if keyword in text:
                found_security_aspects.append(keyword)
        
        if found_security_aspects:
            req = TechnicalRequirement(
                requirement_type=RequirementType.SECURITY,
                category='security',
                description=f"Security requirements: {', '.join(found_security_aspects)}",
                priority='high',
                specifications={
                    'aspects': found_security_aspects
                },
                constraints=['Must follow security best practices'],
                acceptance_criteria=['Pass security audit', 'No known vulnerabilities']
            )
            requirements.append(req)
        
        return requirements
    
    def _extract_interface_requirements(self, text: str) -> List[TechnicalRequirement]:
        """インターフェース要件を抽出"""
        requirements = []
        
        # API関連のパターン
        api_patterns = [
            r'(?:rest|restful)\s+api',
            r'graphql\s+(?:api|endpoint)',
            r'grpc\s+(?:service|api)',
            r'websocket\s+(?:connection|api)',
            r'endpoint:\s*([^\n]+)',
            r'api\s+(?:route|path):\s*([^\n]+)',
        ]
        
        for pattern in api_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                req = TechnicalRequirement(
                    requirement_type=RequirementType.INTERFACE,
                    category='api',
                    description=f"API interface requirement",
                    priority='high',
                    specifications={
                        'type': 'api',
                        'pattern': pattern
                    },
                    constraints=['Must follow RESTful principles', 'Must be documented'],
                    acceptance_criteria=['API tests pass', 'Documentation complete']
                )
                requirements.append(req)
                break
        
        return requirements
    
    def _extract_testing_requirements(self, text: str) -> List[TechnicalRequirement]:
        """テスト要件を抽出"""
        requirements = []
        
        # テスト関連のキーワード
        test_keywords = ['unit test', 'integration test', 'e2e test', 'test coverage', 'tdd']
        coverage_match = re.search(r'(\d+)%?\s*(?:test\s*)?coverage', text)
        
        if any(kw in text for kw in test_keywords) or coverage_match:
            coverage_target = coverage_match.group(1) if coverage_match else '80'
            
            req = TechnicalRequirement(
                requirement_type=RequirementType.TESTING,
                category='testing',
                description=f"Testing requirements with {coverage_target}% coverage",
                priority='high',
                specifications={
                    'coverage_target': int(coverage_target),
                    'test_types': [kw for kw in test_keywords if kw in text]
                },
                constraints=[f'Minimum {coverage_target}% test coverage'],
                acceptance_criteria=['All tests pass', 'Coverage target met']
            )
            requirements.append(req)
        
        return requirements
    
    def _generate_implementation_steps(self, requirements: List[TechnicalRequirement], 
                                     tech_stack: TechnicalStack) -> List[Dict[str, Any]]:
        """実装ステップを生成"""
        steps = []
        
        # 1.0 環境セットアップ
        if not tech_stack.is_empty():
            steps.append({
                'order': 1,
                'phase': 'setup',
                'description': 'Set up development environment',
                'tasks': [
                    f"Install {lang.capitalize()} environment" for lang in tech_stack.languages
                ] + [
                    f"Set up {fw} framework" for fw in tech_stack.frameworks
                ]
            })
        
        # 2.0 基本実装
        func_reqs = [r for r in requirements if r.requirement_type == RequirementType.FUNCTIONAL]
        if func_reqs:
            steps.append({
                'order': 2,
                'phase': 'implementation',
                'description': 'Implement core functionality',
                'tasks': [req.description for req in func_reqs[:5]]  # 最初の5つ
            })
        
        # 3.0 インターフェース実装
        interface_reqs = [r for r in requirements if r.requirement_type == RequirementType.INTERFACE]
        if interface_reqs:
            steps.append({
                'order': 3,
                'phase': 'interface',
                'description': 'Implement interfaces and APIs',
                'tasks': ['Create API endpoints', 'Define data models', 'Add validation']
            })
        
        # 4.0 セキュリティ実装
        sec_reqs = [r for r in requirements if r.requirement_type == RequirementType.SECURITY]
        if sec_reqs:
            steps.append({
                'order': 4,
                'phase': 'security',
                'description': 'Implement security features',
                'tasks': ['Add authentication', 'Implement authorization', 'Enable encryption']
            })
        
        # 5.0 パフォーマンス最適化
        perf_reqs = [r for r in requirements if r.requirement_type == RequirementType.PERFORMANCE]
        if perf_reqs:
            steps.append({
                'order': 5,
                'phase': 'optimization',
                'description': 'Optimize performance',
                'tasks': ['Add caching', 'Optimize queries', 'Implement connection pooling']
            })
        
        # 6.0 テスト実装
        test_reqs = [r for r in requirements if r.requirement_type == RequirementType.TESTING]
        if test_reqs or len(requirements) > 0:
            steps.append({
                'order': 6,
                'phase': 'testing',
                'description': 'Implement comprehensive tests',
                'tasks': ['Write unit tests', 'Add integration tests', 'Ensure coverage target']
            })
        
        return steps
    
    def _estimate_complexity(self, requirements: List[TechnicalRequirement], 
                           tech_stack: TechnicalStack) -> str:
        """複雑度を推定"""
        score = 0
        
        # 要件数による複雑度
        score += len(requirements) * 2
        
        # 技術スタックの多様性
        score += len(tech_stack.languages) * 3
        score += len(tech_stack.frameworks) * 2
        score += len(tech_stack.databases) * 2
        
        # セキュリティ要件がある場合
        if any(r.requirement_type == RequirementType.SECURITY for r in requirements):
            score += 5
        
        # パフォーマンス要件がある場合
        if any(r.requirement_type == RequirementType.PERFORMANCE for r in requirements):
            score += 4
        
        # 複雑度レベルを決定
        if score < 10:
            return 'low'
        elif score < 20:
            return 'medium'
        elif score < 30:
            return 'high'
        else:
            return 'very_high'
    
    def _identify_risk_factors(self, requirements: List[TechnicalRequirement], 
                             tech_stack: TechnicalStack) -> List[Dict[str, str]]:
        """リスク要因を識別"""
        risks = []
        
        # セキュリティ要件がない場合
        if not any(r.requirement_type == RequirementType.SECURITY for r in requirements):
            risks.append({
                'type': 'security',
                'description': 'No explicit security requirements defined',
                'mitigation': 'Add security requirements and implement best practices'
            })
        
        # 複数の言語/フレームワーク
        if len(tech_stack.languages) > 2:
            risks.append({
                'type': 'complexity',
                'description': 'Multiple programming languages increase complexity',
                'mitigation': 'Ensure team has expertise in all languages'
            })
        
        # パフォーマンス要件が厳しい場合
        perf_reqs = [r for r in requirements if r.requirement_type == RequirementType.PERFORMANCE]
        if perf_reqs:
            risks.append({
                'type': 'performance',
                'description': 'Strict performance requirements may be challenging',
                'mitigation': 'Plan for performance testing and optimization early'
            })
        
        # テスト要件がない場合
        if not any(r.requirement_type == RequirementType.TESTING for r in requirements):
            risks.append({
                'type': 'quality',
                'description': 'No explicit testing requirements',
                'mitigation': 'Define testing strategy and coverage targets'
            })
        
        return risks
    
    def _extract_dependencies(self, text: str, tech_stack: TechnicalStack) -> List[str]:
        """依存関係を抽出"""
        dependencies = []
        
        # package.json, requirements.txt などのパターン
        dep_patterns = [
            r'"([^"]+)"\s*:\s*"[^"]+"',  # package.json style
            r'([a-zA-Z0-9_-]+)==[0-9.0]+',  # requirements.txt style
            r'([a-zA-Z0-9_-]+)>=?[0-9.0]+',  # requirements.txt with >= 
            r'gem\s+[\'"]([^\'"])+[\'"]',  # Ruby gems
            r'compile\s+[\'"]([^:]+):',  # Gradle/Maven
        ]
        
        for pattern in dep_patterns:
            matches = re.findall(pattern, text)
            dependencies.extend(matches)
        
        # 技術スタックからも推測
        if 'python' in tech_stack.languages:
            if 'fastapi' in tech_stack.frameworks:
                dependencies.extend(['fastapi', 'uvicorn', 'pydantic'])
            if 'django' in tech_stack.frameworks:
                dependencies.extend(['django', 'djangorestframework'])
        
        if 'javascript' in tech_stack.languages or 'typescript' in tech_stack.languages:
            if 'react' in tech_stack.frameworks:
                dependencies.extend(['react', 'react-dom'])
            if 'express' in tech_stack.frameworks:
                dependencies.extend(['express', 'body-parser'])
        
        # 重複を除去
        return list(set(dependencies))
    
    def _determine_priority(self, text: str) -> str:
        """優先度を判定"""
        high_keywords = ['critical', 'urgent', 'asap', 'immediately', 'blocker', 'required']
        low_keywords = ['nice to have', 'optional', 'future', 'someday', 'maybe']
        
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in high_keywords):
            return 'high'
        elif any(kw in text_lower for kw in low_keywords):
            return 'low'
        else:
            return 'medium'
    
    def generate_implementation_prompt(self, extraction_result: ExtractionResult) -> str:
        """実装用のプロンプトを生成"""
        prompt_parts = []
        
        # 技術スタック
        if not extraction_result.technical_stack.is_empty():
            prompt_parts.append("## Technical Stack")
            stack = extraction_result.technical_stack
            if stack.languages:
                prompt_parts.append(f"- Languages: {', '.join(stack.languages)}")
            if stack.frameworks:
                prompt_parts.append(f"- Frameworks: {', '.join(stack.frameworks)}")
            if stack.databases:
                prompt_parts.append(f"- Databases: {', '.join([db.capitalize() if db " \
                    "in ['redis', 'mongodb', 'postgresql', 'mysql'] else db for db in stack.databases])}")
            prompt_parts.append("")
        
        # 要件
        if extraction_result.requirements:
            prompt_parts.append("## Requirements")
            for req in extraction_result.requirements:
                prompt_parts.append(f"- [{req.requirement_type.value}] {req.description}")
            prompt_parts.append("")
        
        # 実装ステップ
        if extraction_result.implementation_steps:
            prompt_parts.append("## Implementation Steps")
            for step in extraction_result.implementation_steps:
                prompt_parts.append(f"{step['order']}. {step['description']}")
                for task in step['tasks']:
                    prompt_parts.append(f"   - {task}")
            prompt_parts.append("")
        
        # リスク
        if extraction_result.risk_factors:
            prompt_parts.append("## Risk Factors")
            for risk in extraction_result.risk_factors:
                prompt_parts.append(f"- {risk['type']}: {risk['description']}")
        
        return "\n".join(prompt_parts)


# テスト用メイン
if __name__ == "__main__":
    # テストデータ
    test_issue = {
        'title': '⚡ Performance optimization #83 - Implement caching layer',
        'body': '''## Description
We need to implement a Redis-based caching layer for our FastAPI application.

## Requirements
- Response time should be under 100ms for cached requests
- Support for 10000 concurrent users
- 90% test coverage required
- Use Redis for caching
- Implement cache invalidation strategy
- Add monitoring and metrics

## Technical Details
- Python 3.11+
- FastAPI framework
- PostgreSQL database
- Docker deployment

## Security
- Ensure all cached data is encrypted
- Implement proper authentication for cache access
''',
        'labels': ['enhancement', 'performance', 'backend']
    }
    
    extractor = TechnicalRequirementsExtractor()
    result = extractor.extract_requirements(test_issue)
    
    print("🔍 Extraction Results:")
    print(json.dumps(result.to_dict(), indent=2))
    
    print("\n📝 Implementation Prompt:")
    print(extractor.generate_implementation_prompt(result))